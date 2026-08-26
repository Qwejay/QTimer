import copy
import ctypes
import json
import math
import os
import platform
import subprocess
import sys
import threading
import time
from dataclasses import asdict, dataclass
from functools import lru_cache, partial

from PySide6.QtCore import *
from PySide6.QtGui import *
from PySide6.QtSvg import QSvgRenderer
from PySide6.QtWidgets import *

__app_name__ = "QTimer"
__version__ = "1.4.0"
__author__ = "QwejayHuang"
__company__ = "QwejayHuang"
__description__ = "一款极简风格计时器"

try:
    import keyboard
    HAS_KEYBOARD = True
except ImportError:
    HAS_KEYBOARD = False
    print("💡 提示：推荐执行 'pip install keyboard' 以启用真正的全局热键支持。")

def get_app_dir() -> str:
    if getattr(sys, 'frozen', False):
        return os.path.dirname(sys.executable)
    return os.path.dirname(os.path.abspath(__file__))

def get_config_path() -> str:
    loc = QStandardPaths.writableLocation(QStandardPaths.StandardLocation.AppConfigLocation)
    if not loc:
        loc = os.path.join(os.path.expanduser("~"), f".{__app_name__.lower()}")
    else:
        loc = os.path.join(loc, __app_name__)
    os.makedirs(loc, exist_ok=True)
    return os.path.join(loc, "config.json")

CONFIG_PATH = get_config_path()
WNDENUMPROC_TYPE = ctypes.WINFUNCTYPE(ctypes.c_bool, ctypes.c_void_p, ctypes.c_void_p)

def is_ppt_slideshow_active() -> bool:
    if platform.system() != "Windows":
        return False
    try:
        PPT_CLASSES = {
            "screenclass", "paneclassdc", "mso_subwindow_class",
            "kslideshow", "wps_slideshow", "wpp_slideshow_class"
        }
        
        buf_cls = ctypes.create_unicode_buffer(256)
        
        def check_hwnd(hwnd: int) -> bool:
            if not ctypes.windll.user32.IsWindowVisible(hwnd):
                return False
            ctypes.windll.user32.GetClassNameW(hwnd, buf_cls, 256)
            cls = buf_cls.value.lower()
            return any(p in cls for p in PPT_CLASSES)

        fg_hwnd = ctypes.windll.user32.GetForegroundWindow()
        if fg_hwnd and check_hwnd(fg_hwnd):
            return True

        active = [False]
        def enum_cb(hwnd, lparam):
            if check_hwnd(hwnd):
                active[0] = True
                return False 
            return True
            
        ctypes.windll.user32.EnumWindows(WNDENUMPROC_TYPE(enum_cb), 0)
        return active[0]
    except Exception as e:
        print(f"PPT检测异常: {e}")
        return False

def play_alert_sound(file_path: str = "", duration_ms: int = 200) -> None:
    if file_path and os.path.exists(file_path):
        sys_name = platform.system()
        if sys_name == "Windows":
            def _play_win():
                try:
                    import winsound
                    winsound.PlaySound(file_path, winsound.SND_FILENAME | winsound.SND_ASYNC)
                except Exception:
                    pass
            threading.Thread(target=_play_win, daemon=True).start()
            return
        elif sys_name == "Darwin":
            def _play_mac():
                try:
                    subprocess.call(['afplay', file_path])
                except Exception:
                    pass
            threading.Thread(target=_play_mac, daemon=True).start()
            return

    sys_name = platform.system()
    if sys_name == "Windows":
        def _beep():
            try:
                import winsound
                winsound.Beep(1500, duration_ms)
            except Exception:
                pass
        threading.Thread(target=_beep, daemon=True).start()
    elif sys_name == "Darwin":
        def _mac_beep():
            try:
                subprocess.call(['afplay', '/System/Library/Sounds/Glass.aiff'])
            except Exception:
                pass
        threading.Thread(target=_mac_beep, daemon=True).start()
    else:
        QApplication.beep()

def get_rgba_color(hex_color: str, alpha_pct: int) -> str:
    col = QColor(hex_color)
    return f"rgba({col.red()}, {col.green()}, {col.blue()}, {alpha_pct / 100:.2f})"

SVG_ICONS: dict[str, str] = {
    "play":     '<svg viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg"><polygon points="6,4 20,12 6,20" fill="{color}"/></svg>',
    "pause":    '<svg viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg"><rect x="5" y="4" width="4" height="16" rx="1" fill="{color}"/><rect x="15" y="4" width="4" height="16" rx="1" fill="{color}"/></svg>',
    "restart":  '<svg viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg"><path d="M12 5V1L7 6l5 5V7c3.31 0 6 2.69 6 6s-2.69 6-6 6-6-2.69-6-6H4c0 4.42 3.58 8 8 8s8-3.58 8-8-3.58-8-8-8z" fill="{color}"/></svg>',
    "prev":     '<svg viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg"><polygon points="19,4 7,12 19,20" fill="{color}"/><rect x="3" y="4" width="3" height="16" rx="1" fill="{color}"/></svg>',
    "next":     '<svg viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg"><polygon points="5,4 17,12 5,20" fill="{color}"/><rect x="18" y="4" width="3" height="16" rx="1" fill="{color}"/></svg>',
    "settings": '<svg viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg"><path d="M19.14 12.94c.04-.3.06-.61.06-.94s-.02-.64-.07-.94l2.03-1.58c.18-.14.23-.41.12-.61l-1.92-3.32c-.12-.22-.37-.29-.59-.22l-2.39.96c-.5-.38-1.03-.7-1.62-.94l-.36-2.54c-.04-.24-.24-.41-.48-.41h-3.84c-.24 0-.43.17-.47.41l-.36 2.54c-.59.24-1.13.57-1.62.94l-2.39-.96c-.22-.08-.47 0-.59.22L2.74 8.87c-.12.21-.08.47.12.61l2.03 1.58c-.05.3-.09.63-.09.94s.02.64.07.94l-2.03 1.58c-.18.14-.23.41-.12.61l1.92 3.32c.12.22.37.29.59.22l2.39-.96c.5.38 1.03.7 1.62.94l.36 2.54c.05.24.24.41.48.41h3.84c.24 0 .44-.17.47-.41l.36-2.54c.59-.24 1.13-.56 1.62-.94l2.39.96c.22.08.47 0 .59-.22l1.92-3.32c.12-.22.07-.47-.12-.61l-2.01-1.58zM12 15.6c-1.98 0-3.6-1.62-3.6-3.6s1.62-3.6 3.6-3.6 3.6 1.62 3.6 3.6-1.62 3.6-3.6 3.6z" fill="{color}"/></svg>',
    "close":    '<svg viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg"><line x1="4" y1="4" x2="20" y2="20" stroke="{color}" stroke-width="2.5" stroke-linecap="round"/><line x1="20" y1="4" x2="4" y2="20" stroke="{color}" stroke-width="2.5" stroke-linecap="round"/></svg>',
    "up":       '<svg viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg"><path d="M7.41 15.41L12 10.83l4.59 4.58L18 14l-6-6-6 6z" fill="{color}"/></svg>',
    "down":     '<svg viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg"><path d="M7.41 8.59L12 13.17l4.59-4.58L18 10l-6 6-6-6z" fill="{color}"/></svg>',
    "trash":    '<svg viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg"><path d="M6 19c0 1.1.9 2 2 2h8c1.1 0 2-.9 2-2V7H6v12zM19 4h-3.5l-1-1h-5l-1 1H5v2h14V4z" fill="{color}"/></svg>',
}

@lru_cache(maxsize=128)
def _render_svg_icon(name: str, size: int, color: str, dpr: float) -> QIcon:
    svg_str = SVG_ICONS.get(name, "").replace("{color}", color)
    if not svg_str:
        return QIcon()
    renderer = QSvgRenderer(svg_str.encode("utf-8"))
    physical_size = int(size * dpr)
    physical_size = max(physical_size, 1)
    pixmap = QPixmap(physical_size, physical_size)
    pixmap.fill(Qt.GlobalColor.transparent)
    painter = QPainter(pixmap)
    painter.setRenderHints(QPainter.RenderHint.Antialiasing | QPainter.RenderHint.SmoothPixmapTransform)
    renderer.render(painter, QRectF(0, 0, physical_size, physical_size))
    painter.end()
    pixmap.setDevicePixelRatio(dpr)
    return QIcon(pixmap)

def get_svg_icon(name: str, size: int, color: str = "white") -> QIcon:
    app = QApplication.instance()
    widget = app.activeWindow() or (app.topLevelWidgets()[0] if app.topLevelWidgets() else None)
    dpr = widget.devicePixelRatioF() if widget else 1.0
    return _render_svg_icon(name, size, color, dpr)

@dataclass
class Stage:
    label: str = "说课时间"
    duration: int = 5
    unit: str = "分"
    count_up: bool = False

    @property
    def seconds(self) -> int:
        return self.duration * 60 if self.unit == "分" else self.duration

    @classmethod
    def from_dict(cls, d: dict) -> 'Stage':
        if "minutes" in d and "duration" not in d:
            return cls(label=d.get("label", ""), duration=d["minutes"], unit="分", count_up=d.get("count_up", False))
        return cls(label=d.get("label", ""), duration=d.get("duration", 5), unit=d.get("unit", "分"), count_up=d.get("count_up", False))

@dataclass
class Alert:
    seconds: int = 30
    color: str = "#ffaa00"
    play_sound: bool = True

    @classmethod
    def from_dict(cls, d: dict) -> 'Alert':
        return cls(seconds=d.get("seconds", 30), color=d.get("color", "#ffaa00"), play_sound=d.get("play_sound", True))

class Config:
    def __init__(self):
        self.auto_advance: bool = False
        self.global_sound: bool = True
        self.countdown_10s_sound: bool = True
        self.alert_sound_path: str = ""
        self.end_sound_path: str = ""
        self.pos_x: int = -1
        self.pos_y: int = -1
        self.always_on_top: bool = True
        self.prevent_offscreen: bool = True
        self.show_stage_label: bool = True
        self.ppt_auto_start: bool = True
        self.double_click_toggle: bool = True
        self.stages: list[Stage] = [Stage("说课时间", 5, "分", False), Stage("答辩时间", 2, "分", False)]
        self.alerts: list[Alert] = [Alert(30, "#ffaa00", True), Alert(10, "#ff4444", True)]
        self.color: str = "#ffffff"
        self.font: str = "微软雅黑"
        self.font_size: int = 32
        self.stage_font: str = "微软雅黑"
        self.stage_font_size: int = 18
        self.bg_color: str = "#141414"
        self.global_transparency: int = 5       
        self.bg_transparency: int = 18         
        self.font_transparency: int = 0         
        self.shortcut_toggle: str = "Ctrl+Space"
        self.shortcut_reset: str = "Ctrl+Return"
        self.shortcut_prev: str = "Ctrl+Left"
        self.shortcut_next: str = "Ctrl+Right"
        self.ui_scale: int = 100

    def save(self) -> None:
        data = {
            "auto_advance": self.auto_advance,
            "global_sound": self.global_sound,
            "countdown_10s_sound": self.countdown_10s_sound,
            "alert_sound_path": self.alert_sound_path,
            "end_sound_path": self.end_sound_path,
            "pos_x": self.pos_x,
            "pos_y": self.pos_y,
            "always_on_top": self.always_on_top,
            "prevent_offscreen": self.prevent_offscreen,
            "show_stage_label": self.show_stage_label,
            "ppt_auto_start": self.ppt_auto_start,
            "double_click_toggle": self.double_click_toggle,
            "stages": [asdict(s) for s in self.stages],
            "alerts": [asdict(a) for a in self.alerts],
            "color": self.color,
            "font": self.font,
            "font_size": self.font_size,
            "stage_font": self.stage_font,
            "stage_font_size": self.stage_font_size,
            "bg_color": self.bg_color,
            "global_transparency": self.global_transparency,
            "bg_transparency": self.bg_transparency,
            "font_transparency": self.font_transparency,
            "shortcut_toggle": self.shortcut_toggle,
            "shortcut_reset": self.shortcut_reset,
            "shortcut_prev": self.shortcut_prev,
            "shortcut_next": self.shortcut_next,
            "ui_scale": self.ui_scale,
        }
        try:
            tmp_path = CONFIG_PATH + ".tmp"
            with open(tmp_path, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            if os.path.exists(tmp_path):
                os.replace(tmp_path, CONFIG_PATH)
        except Exception:
            pass

    def load(self) -> None:
        if not os.path.exists(CONFIG_PATH):
            return
        try:
            with open(CONFIG_PATH, "r", encoding="utf-8") as f:
                d = json.load(f)
            if not isinstance(d, dict): return
            
            for key in self.__dict__.keys():
                if key in d and not key.startswith('_'):
                    setattr(self, key, d[key])
                    
            if "stages" in d:
                self.stages = [Stage.from_dict(s) for s in d["stages"] if isinstance(s, dict)]
            if "alerts" in d:
                self.alerts = [Alert.from_dict(a) for a in d["alerts"] if isinstance(a, dict)]
        except Exception as e:
            print(f"加载配置失败，将使用默认值: {e}")

    def bg_qcolor(self) -> QColor:
        c = QColor(self.bg_color)
        opacity_pct = max(0, min(100, 100 - self.bg_transparency))
        alpha = int(opacity_pct / 100 * 255)
        if self.bg_transparency == 100:
            alpha = 1
        c.setAlpha(alpha)
        return c

class TimerController(QObject):
    tick = Signal(str, int)
    stage_changed = Signal(int, str)
    alert_triggered = Signal(str)
    loop_restarted = Signal()
    state_changed = Signal(bool)

    def __init__(self, config: Config):
        super().__init__()
        self.config = config
        self._timer = QTimer(self)
        self._timer.setInterval(200)
        self._timer.timeout.connect(self._tick)
        self.running: bool = False
        self.paused: bool = True
        self._stage_idx: int = 0
        self._remaining_float: float = 0.0
        self._target_time: float = 0.0
        self._last_displayed: int = -1
        self._triggered = set()
        self._zero_triggered: bool = False

    def toggle_pause(self) -> None:
        if self._remaining_float <= 0:
            return
        if not self.running:
            self.running = True
        self.paused = not self.paused
        if not self.paused:
            self._target_time = time.time() + self._remaining_float
            self._timer.start()
        else:
            self._timer.stop()
        self.state_changed.emit(not self.paused)

    def restart_stage(self) -> None:
        self._load_stage()
        self._stop_and_wait()

    def prev_stage(self) -> None:
        if not self.config.stages:
            return
        self._stage_idx = (self._stage_idx - 1) % len(self.config.stages)
        self._load_stage()
        self._stop_and_wait()

    def next_stage(self) -> None:
        self._advance_idx()
        self._load_stage()
        self._stop_and_wait()

    def stop(self) -> None:
        self._timer.stop()
        self._stage_idx = 0
        self._load_stage()
        self._stop_and_wait()
        self.running = False

    def _stop_and_wait(self) -> None:
        self._timer.stop()
        self.paused = True
        self.state_changed.emit(False)

    def _load_stage(self) -> None:
        if not self.config.stages:
            return
        st = self.config.stages[self._stage_idx]
        self._remaining_float = float(st.seconds)
        self._last_displayed = st.seconds
        self._triggered.clear()
        self._zero_triggered = False
        self.stage_changed.emit(self._stage_idx, st.label)
        self.tick.emit(st.label, 0 if st.count_up else st.seconds)

    def _tick(self) -> None:
        if self.paused or not self.config.stages:
            return
        now = time.time()
        self._remaining_float = self._target_time - now
        rem_sec = max(0, int(math.ceil(self._remaining_float)))
        if rem_sec != self._last_displayed:
            self._last_displayed = rem_sec
            st = self.config.stages[self._stage_idx]
            display_sec = max(0, st.seconds - rem_sec) if st.count_up else rem_sec
            self.tick.emit(st.label, display_sec)
            if self.config.global_sound:
                if self.config.countdown_10s_sound and 0 < rem_sec <= 10:
                    play_alert_sound(self.config.alert_sound_path, 200)
                for a in self.config.alerts:
                    if rem_sec == a.seconds and a.seconds not in self._triggered:
                        self._triggered.add(a.seconds)
                        self.alert_triggered.emit(a.color)
                        if a.play_sound:
                            play_alert_sound(self.config.alert_sound_path, 200)
        if self._remaining_float <= 0 and not self._zero_triggered:
            self._zero_triggered = True
            self._remaining_float = 0.0
            if self.config.global_sound:
                play_alert_sound(self.config.end_sound_path, 2000)
            if self.config.auto_advance:
                self._advance_idx()
                self._load_stage()
                self._target_time = time.time() + self._remaining_float
            else:
                self._stop_and_wait()

    def _advance_idx(self) -> None:
        if not self.config.stages:
            return
        self._stage_idx += 1
        if self._stage_idx >= len(self.config.stages):
            self._stage_idx = 0
            self.loop_restarted.emit()

class FloatBar(QWidget):
    request_settings = Signal()
    request_exit = Signal()
    double_clicked = Signal()
    wheel_scrolled = Signal(int)
    position_changed = Signal(int, int) 

    def __init__(self):
        super().__init__()
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint | Qt.WindowType.Tool)
        self.setAttribute(Qt.WidgetAttribute.WA_ShowWithoutActivating)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setAttribute(Qt.WidgetAttribute.WA_Hover)
        self.setFocusPolicy(Qt.FocusPolicy.ClickFocus)
        self._drag_pos = None
        self._text_color = "#ffffff"
        self._font_family = "微软雅黑"
        self._font_size = 32
        self._stage_font_family = "微软雅黑"
        self._stage_font_size = 18
        self._bg_color = QColor(20, 20, 20, 210)
        self._show_stage_label = True
        self._prevent_offscreen = True
        self._font_transparency = 0
        self._target_opacity = 0.95
        self._global_transparency = 5
        self._ui_scale = 100
        self._icon_size = 34
        self._is_running = False
        self._current_stage_text = ""
        self._text_width = 150
        self._full_width = 300
        self._flash_timer = QTimer(self)
        self._flash_state = False
        self._flash_color = "#ff4444"
        self._flash_timer.timeout.connect(self._do_flash)
        self._width_anim = QPropertyAnimation(self, b"bar_width")
        self._width_anim.setDuration(220)
        self._width_anim.setEasingCurve(QEasingCurve.Type.OutCubic)
        self._btn_opacity = QGraphicsOpacityEffect()
        self._btn_anim = QPropertyAnimation(self._btn_opacity, b"opacity")
        self._btn_anim.setDuration(220)
        self._anim_group = QParallelAnimationGroup(self)
        self._anim_group.addAnimation(self._width_anim)
        self._anim_group.addAnimation(self._btn_anim)
        self._hide_timer = QTimer(self)
        self._hide_timer.setSingleShot(True)
        self._hide_timer.timeout.connect(self._do_hide_anim)
        self._build_ui()
        self._update_size()

    @Property(int)
    def bar_width(self) -> int:
        return self.width()

    @bar_width.setter
    def bar_width(self, w: int) -> None:
        self.setFixedWidth(w)

    def _build_ui(self) -> None:
        self._canvas = QWidget(self)
        self._canvas.move(0, 0)
        self._layout = QHBoxLayout(self._canvas)
        self._layout.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)
        self._layout.setContentsMargins(18, 0, 0, 0)
        self._layout.setSpacing(0)
        
        self.lbl_stage = QLabel("环节名称")
        self.lbl_stage.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.lbl_time = QLabel("00:00")
        self.lbl_time.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        self._layout.addWidget(self.lbl_stage, 0, Qt.AlignmentFlag.AlignVCenter)
        self._spacing_item = QSpacerItem(12, 0, QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed)
        self._layout.addItem(self._spacing_item)
        self._layout.addWidget(self.lbl_time, 0, Qt.AlignmentFlag.AlignVCenter)
        
        self._end_spacing_item = QSpacerItem(18, 0, QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed)
        self._layout.addItem(self._end_spacing_item)
        self._btn_container = QWidget()
        btn_lay = QHBoxLayout(self._btn_container)
        btn_lay.setContentsMargins(0, 0, 0, 0)
        btn_lay.setSpacing(2)
        self.btn_toggle = self._make_icon_btn("play", "播放 / 暂停")
        self.btn_restart = self._make_icon_btn("restart", "重置当前环节")
        self.btn_prev = self._make_icon_btn("prev", "上一环节")
        self.btn_next = self._make_icon_btn("next", "下一环节")
        self.btn_settings = self._make_icon_btn("settings", "设置")
        self.btn_close = self._make_icon_btn("close", "退出")
        for b in (self.btn_toggle, self.btn_restart, self.btn_prev, self.btn_next, self.btn_settings, self.btn_close):
            btn_lay.addWidget(b)
        self._btn_container.setGraphicsEffect(self._btn_opacity)
        self._btn_opacity.setOpacity(0.0)
        self._layout.addWidget(self._btn_container, 0, Qt.AlignmentFlag.AlignVCenter)
        self.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.customContextMenuRequested.connect(self._show_ctx_menu)
        
        shadow_stage = QGraphicsDropShadowEffect(self)
        shadow_stage.setBlurRadius(4)
        shadow_stage.setColor(QColor(0, 0, 0, 180))
        shadow_stage.setOffset(1, 1)
        self.lbl_stage.setGraphicsEffect(shadow_stage)

        shadow_time = QGraphicsDropShadowEffect(self)
        shadow_time.setBlurRadius(4)
        shadow_time.setColor(QColor(0, 0, 0, 180))
        shadow_time.setOffset(1, 1)
        self.lbl_time.setGraphicsEffect(shadow_time)

    def _make_icon_btn(self, icon_name: str, tip: str) -> QPushButton:
        b = QPushButton()
        b.setProperty("icon_name", icon_name)
        b.setToolTip(tip)
        b.setCursor(Qt.CursorShape.PointingHandCursor)
        return b

    def apply_style(self, color: str, font: str, size: int, stage_font: str, stage_size: int,
                    opacity: float, bg_color: QColor, always_on_top: bool,
                    show_stage_label: bool, prevent_offscreen: bool, font_transparency: int, ui_scale: int = 100) -> None:
        self._text_color = color
        self._font_family = font
        self._stage_font_family = stage_font
        self._bg_color = bg_color
        self._show_stage_label = show_stage_label
        self._prevent_offscreen = prevent_offscreen
        self._font_transparency = font_transparency
        self._ui_scale = ui_scale
        scale = self._ui_scale / 100.0
        self._font_size = max(10, int(size * scale))
        self._stage_font_size = max(8, int(stage_size * scale))
        self._icon_size = max(16, int(34 * scale))
        icon_inner = max(10, self._icon_size - 8)
        btn_radius = max(3, int(7 * scale))
        self._layout.setContentsMargins(int(18 * scale), 0, 0, 0)
        self._end_spacing_item.changeSize(int(18 * scale), 0, QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed)
        self._btn_container.layout().setSpacing(int(2 * scale))
        for b in (self.btn_toggle, self.btn_restart, self.btn_prev, self.btn_next, self.btn_settings, self.btn_close):
            b.setFixedSize(self._icon_size, self._icon_size)
            i_name = b.property("icon_name")
            if i_name:
                b.setIcon(get_svg_icon(i_name, icon_inner))
            b.setIconSize(QSize(icon_inner, icon_inner))
            b.setStyleSheet(f"QPushButton {{ background: rgba(255,255,255,15); border: none; border-radius: {btn_radius}px; }} "
                            f"QPushButton:hover {{ background: rgba(255,255,255,40); }}")
        self._target_opacity = opacity
        self._global_transparency = int(round((1.0 - opacity) * 100))
        self.setWindowOpacity(opacity)
        flags = self.windowFlags()
        if always_on_top:
            flags |= Qt.WindowType.WindowStaysOnTopHint
        else:
            flags &= ~Qt.WindowType.WindowStaysOnTopHint
        if flags != self.windowFlags():
            was_visible = self.isVisible()
            pos_before = self.pos()
            self.setWindowFlags(flags)
            self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, True)
            if was_visible:
                self.move(pos_before)
                self.show()
        self._refresh_labels()
        self._update_size()
        self.update()

    def _refresh_labels(self, stage_color: str = None, time_color: str = None) -> None:
        sc = stage_color or self._text_color
        tc = time_color or self._text_color
        opacity_pct = max(0, min(100, 100 - self._font_transparency))
        rgba_sc = get_rgba_color(sc, opacity_pct)
        rgba_tc = get_rgba_color(tc, opacity_pct)
        self.lbl_stage.setStyleSheet(
            f"color:{rgba_sc}; font-family:'{self._stage_font_family}'; "
            f"font-size:{self._stage_font_size}px; font-weight:600; background:transparent; padding:0px; margin:0px;")
        self.lbl_time.setStyleSheet(
            f"color:{rgba_tc}; font-family:'{self._font_family}'; "
            f"font-size:{self._font_size}px; font-weight:900; background:transparent; padding:0px; margin:0px;")
        self.lbl_stage.style().polish(self.lbl_stage)
        self.lbl_time.style().polish(self.lbl_time)

    def _update_size(self) -> None:
        if hasattr(self, '_anim_group'):
            self._anim_group.stop()
        
        scale = getattr(self, '_ui_scale', 100) / 100.0
        fm_stage = self.lbl_stage.fontMetrics()
        fm_time = self.lbl_time.fontMetrics()
        
        text = self._current_stage_text or "环节名称"
        sample_text = "88:88:88" if len(self.lbl_time.text()) > 5 else "88:88"
        time_w = fm_time.horizontalAdvance(sample_text) + int(24 * scale)
        self.lbl_time.setFixedWidth(time_w)
        
        btn_count = 6
        btn_w = (getattr(self, '_icon_size', 34) + int(2 * scale)) * btn_count
        self._btn_container.setFixedWidth(btn_w)
        
        base_margin = int(18 * scale)
        stage_spacing = int(12 * scale)
        
        if self._show_stage_label:
            self.lbl_stage.show()
            self._spacing_item.changeSize(stage_spacing, 0, QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed)
            stage_w = fm_stage.horizontalAdvance(text) + int(20 * scale)
            self.lbl_stage.setText(text)
            self.lbl_stage.setFixedWidth(stage_w)
            self._text_width = base_margin + stage_w + stage_spacing + time_w + base_margin
        else:
            self.lbl_stage.hide()
            self._spacing_item.changeSize(0, 0, QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed)
            self._text_width = base_margin + time_w + base_margin

        self._full_width = self._text_width + btn_w + int(16 * scale)
        h = max(self._font_size + int(24 * scale), int(50 * scale))
        self.lbl_stage.setFixedHeight(int(h))
        self.lbl_time.setFixedHeight(int(h))
        
        self._canvas.setFixedSize(int(self._full_width), int(h))
        self.setFixedHeight(int(h))
        
        if self.underMouse():
            self.setFixedWidth(int(self._full_width))
            self._btn_opacity.setOpacity(1.0)
        else:
            self.setFixedWidth(int(self._text_width))
            self._btn_opacity.setOpacity(0.0)
            
        QTimer.singleShot(10, self._ensure_onscreen)

    def _ensure_onscreen(self) -> None:
        if not getattr(self, '_prevent_offscreen', True):
            return
        screen = self.screen()
        if not screen:
            return
        avail_geo = screen.availableGeometry()
        geo = self.geometry()
        new_x = max(avail_geo.left(), min(geo.x(), avail_geo.right() - geo.width()))
        new_y = max(avail_geo.top(), min(geo.y(), avail_geo.bottom() - geo.height()))
        if new_x != geo.x() or new_y != geo.y():
            self.move(new_x, new_y)

    def update_display(self, stage: str, display_sec: int) -> None:
        if display_sec >= 3600:
            hh, rem = divmod(display_sec, 3600)
            mm, ss = divmod(rem, 60)
            time_text = f"{hh:02d}:{mm:02d}:{ss:02d}"
        else:
            mm, ss = divmod(display_sec, 60)
            time_text = f"{mm:02d}:{ss:02d}"
            
        if self._current_stage_text != stage or (len(time_text) != len(self.lbl_time.text())):
            self._current_stage_text = stage
            self.lbl_time.setText(time_text)
            self._update_size()
        else:
            self.lbl_time.setText(time_text)

    def set_running(self, running: bool) -> None:
        self._is_running = running
        icon_name = "pause" if running else "play"
        self.btn_toggle.setProperty("icon_name", icon_name)
        icon_inner = max(10, getattr(self, '_icon_size', 34) - 8)
        self.btn_toggle.setIcon(get_svg_icon(icon_name, icon_inner))

    def start_flash(self, color: str, auto_stop_ms: int = 3000) -> None:
        self._flash_color = color
        self._flash_state = False
        self._flash_timer.start(400)
        if auto_stop_ms > 0:
            QTimer.singleShot(auto_stop_ms, self.stop_flash)

    def stop_flash(self) -> None:
        self._flash_timer.stop()
        self._refresh_labels(stage_color=self._flash_color, time_color=self._flash_color)

    def _do_flash(self) -> None:
        self._flash_state = not self._flash_state
        c = self._flash_color if self._flash_state else self._text_color
        self._refresh_labels(stage_color=c, time_color=c)

    def enterEvent(self, e) -> None:
        self._hide_timer.stop()
        self._anim_group.stop()
        self._width_anim.setStartValue(self.width())
        self._width_anim.setEndValue(self._full_width)
        self._btn_anim.setStartValue(self._btn_opacity.opacity())
        self._btn_anim.setEndValue(1.0)
        self._anim_group.start()
        super().enterEvent(e)
        
    def leaveEvent(self, e) -> None:
        self._hide_timer.start(1000)
        super().leaveEvent(e)
        
    def _do_hide_anim(self) -> None:
        self._anim_group.stop()
        self._width_anim.setStartValue(self.width())
        self._width_anim.setEndValue(self._text_width)
        self._btn_anim.setStartValue(self._btn_opacity.opacity())
        self._btn_anim.setEndValue(0.0)
        self._anim_group.start()

    def _show_ctx_menu(self, pos: QPoint) -> None:
        m = QMenu(self)
        m.setStyleSheet("""
            QMenu { background:#2a2a2a; color:#eee; border:1px solid #444; border-radius:6px; padding:4px; }
            QMenu::item { padding:6px 20px; border-radius:4px; }
            QMenu::item:selected { background:#3d3d3d; }
            QMenu::separator { background:#444; height:1px; margin:4px 8px; }
        """)
        m.addAction("播放 / 暂停").triggered.connect(self.btn_toggle.click)
        m.addAction("重置当前环节").triggered.connect(self.btn_restart.click)
        m.addAction("上一环节").triggered.connect(self.btn_prev.click)
        m.addAction("下一环节").triggered.connect(self.btn_next.click)
        m.addSeparator()
        m.addAction("设置").triggered.connect(self.request_settings.emit)
        m.addAction("退出").triggered.connect(self.request_exit.emit)
        m.exec(self.mapToGlobal(pos))

    def wheelEvent(self, e: QWheelEvent) -> None:
        if e.modifiers() & Qt.KeyboardModifier.ControlModifier:
            delta = e.angleDelta().y()
            if delta > 0:
                self.wheel_scrolled.emit(5)
            elif delta < 0:
                self.wheel_scrolled.emit(-5)
            e.accept()
        else:
            super().wheelEvent(e)

    def paintEvent(self, e) -> None:
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        p.setBrush(self._bg_color)
        p.setPen(Qt.PenStyle.NoPen)
        radius = int(12 * getattr(self, '_ui_scale', 100) / 100.0)
        p.drawRoundedRect(self.rect(), radius, radius)

    def mouseDoubleClickEvent(self, e: QMouseEvent) -> None:
        if e.button() == Qt.MouseButton.LeftButton:
            self.double_clicked.emit()
        super().mouseDoubleClickEvent(e)

    def mousePressEvent(self, e: QMouseEvent) -> None:
        if e.button() == Qt.MouseButton.LeftButton:
            self._drag_pos = e.globalPosition().toPoint() - self.pos()
            QToolTip.showText(e.globalPosition().toPoint(), f"窗体透明度: {self._global_transparency}%", self)

    def mouseMoveEvent(self, e: QMouseEvent) -> None:
        if self._drag_pos and e.buttons() == Qt.MouseButton.LeftButton:
            new_pos = e.globalPosition().toPoint() - self._drag_pos
            if self._prevent_offscreen:
                screen_obj = QApplication.screenAt(e.globalPosition().toPoint())
                screen = screen_obj.availableGeometry() if screen_obj else self.screen().availableGeometry()
                new_x = new_pos.x()
                new_y = new_pos.y()

                snap_margin = 15
                if abs(new_x - screen.left()) < snap_margin:
                    new_x = screen.left()
                elif abs(new_x + self.width() - screen.right()) < snap_margin:
                    new_x = screen.right() - self.width()
                if abs(new_y - screen.top()) < snap_margin:
                    new_y = screen.top()
                elif abs(new_y + self.height() - screen.bottom()) < snap_margin:
                    new_y = screen.bottom() - self.height()
                new_x = max(screen.left(), min(new_x, screen.right() - self.width()))
                new_y = max(screen.top(), min(new_y, screen.bottom() - self.height()))
                new_pos = QPoint(new_x, new_y)
            self.move(new_pos)
            QToolTip.showText(e.globalPosition().toPoint(), f"窗体透明度: {self._global_transparency}%", self)

    def mouseReleaseEvent(self, e: QMouseEvent) -> None:
        self._drag_pos = None
        QToolTip.hideText()
        self._ensure_onscreen()
        self.position_changed.emit(self.x(), self.y())

    def moveEvent(self, e: QMoveEvent) -> None:
        super().moveEvent(e)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, True)
        if hasattr(self, '_target_opacity'):
            self.setWindowOpacity(self._target_opacity)

    def resizeEvent(self, e: QResizeEvent) -> None:
        super().resizeEvent(e)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, True)
        if hasattr(self, '_target_opacity'):
            self.setWindowOpacity(self._target_opacity)

    def showEvent(self, e: QShowEvent) -> None:
        super().showEvent(e)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, True)
        if hasattr(self, '_target_opacity'):
            self.setWindowOpacity(self._target_opacity)

class SettingsWindow(QDialog):
    preview_requested = Signal()
    
    _SS = """
    QDialog {
        background-color: #f9f9f9;
        color: #242424;
        font-family: 'Microsoft YaHei', sans-serif;
    }

    QLabel {
        color: #242424;
    }

    QListWidget {
        background: transparent;
        border: none;
        border-right: 1px solid #e0e0e0;
        outline: none;
        padding-top: 15px;
    }

    QListWidget::item {
        height: 42px;
        padding-left: 15px;
        color: #444444;
        font-size: 13px;
        border-left: 4px solid transparent;
        border-radius: 6px;
        margin: 2px 10px;
    }

    QListWidget::item:hover {
        background: #f0f0f0;
    }

    QListWidget::item:selected {
        background: #f0f7ff;
        color: #0078d4;
        font-weight: bold;
    }

    QLineEdit,
    QSpinBox,
    QDoubleSpinBox,
    QKeySequenceEdit,
    QComboBox {
        background: #ffffff;
        color: #242424;
        selection-background-color: #0078d4;
        selection-color: #ffffff;
        border: 1px solid #d1d1d1;
        border-radius: 5px;
    }

    QComboBox QAbstractItemView {
        background: #ffffff;
        color: #242424;
        selection-background-color: #0078d4;
        selection-color: #ffffff;
    }

    QKeySequenceEdit {
        padding: 6px 10px;
        font-size: 12px;
    }

    QKeySequenceEdit:focus {
        border-color: #0078d4;
    }

    QPushButton {
        padding: 4px 12px;
        border: 1px solid #cccccc;
        border-radius: 4px;
        background: #ffffff;
        color: #242424;
    }

    QPushButton:hover {
        background: #f0f0f0;
    }

    QCheckBox {
        color: #242424;
    }

    QFrame {
        color: #242424;
    }

    QScrollArea {
        color: #242424;
    }

    QScrollBar:vertical {
        background: #f0f0f0;
        width: 10px;
        border: none;
    }

    QScrollBar::handle:vertical {
        background: #c8c8c8;
        border-radius: 5px;
        min-height: 30px;
    }

    QScrollBar::handle:vertical:hover {
        background: #aaaaaa;
    }

    QScrollBar::add-line:vertical,
    QScrollBar::sub-line:vertical {
        height: 0px;
    }

    QScrollBar:horizontal {
        background: #f0f0f0;
        height: 10px;
        border: none;
    }

    QScrollBar::handle:horizontal {
        background: #c8c8c8;
        border-radius: 5px;
        min-width: 30px;
    }

    QSlider:horizontal {
        min-height: 26px;
    }

    QSlider::groove:horizontal {
        height: 4px;
        background: #d6d6d6;
        border-radius: 2px;
    }

    QSlider::handle:horizontal {
        width: 16px;
        height: 16px;
        margin: -6px 0;
        background: #0078d4;
        border-radius: 8px;
    }

    QSlider::handle:horizontal:hover {
        background: #005a9e;
    }
    """

    def __init__(self, config: Config, parent=None):
        super().__init__(parent)
        self.config = config
        self._backup_attrs = {
            "color": config.color, "bg_color": config.bg_color,
            "alert_sound_path": config.alert_sound_path,
            "end_sound_path": config.end_sound_path,
            "font": config.font, "font_size": config.font_size,
            "stage_font": config.stage_font, "stage_font_size": config.stage_font_size,
            "always_on_top": config.always_on_top, "prevent_offscreen": config.prevent_offscreen,
            "show_stage_label": config.show_stage_label, "auto_advance": config.auto_advance,
            "ppt_auto_start": config.ppt_auto_start, "double_click_toggle": config.double_click_toggle,
            "global_sound": config.global_sound, "countdown_10s_sound": config.countdown_10s_sound,
            "global_transparency": config.global_transparency, "bg_transparency": config.bg_transparency,
            "font_transparency": config.font_transparency,
            "shortcut_toggle": config.shortcut_toggle, "shortcut_reset": config.shortcut_reset,
            "shortcut_prev": config.shortcut_prev, "shortcut_next": config.shortcut_next,
            "ui_scale": config.ui_scale,
            "stages": copy.deepcopy(config.stages), "alerts": copy.deepcopy(config.alerts),
        }
        self.setWindowTitle(f"{__app_name__} 设置")
        self.resize(780, 560)
        self.setStyleSheet(self._SS)
        self.setWindowFlags(self.windowFlags() & ~Qt.WindowType.WindowContextHelpButtonHint)
        self._stage_rows = []
        self._alert_rows = []
        self._build_ui()
        self._populate()
        self._connect_live_preview_triggers()

    def _build_ui(self) -> None:
        root_lay = QHBoxLayout(self)
        root_lay.setContentsMargins(0, 0, 0, 0)
        root_lay.setSpacing(0)
        self.sidebar = QListWidget()
        self.sidebar.setFixedWidth(160)
        self.sidebar.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        nav_items = ["⏱️ 流程配置", "🔔 预警声音", "🎨 视觉外观", "⌨️ 快捷操作"]
        self.sidebar.addItems(nav_items)
        self.sidebar.currentRowChanged.connect(self._change_page)
        root_lay.addWidget(self.sidebar)
        right_panel = QWidget()
        right_lay = QVBoxLayout(right_panel)
        right_lay.setContentsMargins(20, 20, 20, 12)
        right_lay.setSpacing(12)
        self.pages = QStackedWidget()
        self.pages.addWidget(self._build_page_stages())
        self.pages.addWidget(self._build_page_alerts())
        self.pages.addWidget(self._build_page_appearance())
        self.pages.addWidget(self._build_page_shortcuts())
        right_lay.addWidget(self.pages)
        bottom_bar = QWidget()
        btn_lay = QHBoxLayout(bottom_bar)
        btn_lay.setContentsMargins(0, 0, 0, 0)
        lbl_copyright = QLabel('<a href="https://github.com/Qwejay/QTimer" style="color: #999; text-decoration: none;">Copyright © 2026 QwejayHuang</a>')
        lbl_copyright.setOpenExternalLinks(True)
        lbl_copyright.setStyleSheet("font-size: 11px;")
        btn_lay.addWidget(lbl_copyright)
        btn_lay.addStretch()
        
        self.btn_restore = QPushButton("恢复默认")
        self.btn_restore.clicked.connect(self._restore_defaults)
        btn_lay.addWidget(self.btn_restore)
        
        self.btn_cancel = QPushButton("取消")
        self.btn_cancel.clicked.connect(self.reject)
        btn_lay.addWidget(self.btn_cancel)
        
        self.btn_save = QPushButton("保存应用")  
        self.btn_save.setStyleSheet("background-color: #0078d4; color: white; border: none;")
        self.btn_save.clicked.connect(self.accept)
        btn_lay.addWidget(self.btn_save)
        
        right_lay.addWidget(bottom_bar)
        root_lay.addWidget(right_panel)
        self.sidebar.setCurrentRow(0)

    def _change_page(self, idx: int) -> None:
        self.pages.setCurrentIndex(idx)

    def _make_setting_row(self, title: str, subtitle: str, control: QWidget) -> QWidget:
        w = QWidget()
        lay = QHBoxLayout(w)
        lay.setContentsMargins(0, 0, 0, 0)
        text_lay = QVBoxLayout()
        text_lay.setSpacing(2)
        lbl_title = QLabel(title)
        lbl_title.setStyleSheet("font-weight: bold; color: #333;")
        text_lay.addWidget(lbl_title)
        if subtitle:
            lbl_sub = QLabel(subtitle)
            lbl_sub.setStyleSheet("color: #777; font-size: 11px;")
            text_lay.addWidget(lbl_sub)
        lay.addLayout(text_lay)
        lay.addStretch()
        lay.addWidget(control)
        return w

    def _make_card(self, title: str, layout: QLayout) -> QWidget:
        card = QFrame()
        card.setStyleSheet("QFrame { background: white; border: 1px solid #e0e0e0; border-radius: 8px; }")
        vlay = QVBoxLayout(card)
        vlay.setContentsMargins(16, 16, 16, 16)
        vlay.setSpacing(12)
        if title:
            lbl = QLabel(title)
            lbl.setStyleSheet(
                "font-size: 15px; "
                "font-weight: bold; "
                "color: #242424; "
                "background: transparent; "
                "border: none;"
            )
            vlay.addWidget(lbl)
        inner = QWidget()
        inner.setStyleSheet("border: none;")
        inner.setLayout(layout)
        vlay.addWidget(inner)
        return card

    def _make_sound_picker_row(self, title: str, line_edit: QLineEdit, default_duration: int = 200) -> QWidget:
        w = QWidget()
        lay = QHBoxLayout(w)
        lay.setContentsMargins(0, 0, 0, 0)
        lay.setSpacing(8)
        
        lbl = QLabel(title)
        lbl.setStyleSheet("font-weight: bold; color: #333;")
        lbl.setFixedWidth(90)
        lay.addWidget(lbl)
        
        line_edit.setMinimumWidth(160)
        lay.addWidget(line_edit, 1)
        
        btn_browse = QPushButton("浏览...")
        btn_browse.setCursor(Qt.CursorShape.PointingHandCursor)
        def _on_browse():
            ext = "*.wav *.mp3 *.aiff" if platform.system() == "Darwin" else "*.wav"
            path, _ = QFileDialog.getOpenFileName(self, f"选择{title}文件", "", f"音频文件 ({ext});;所有文件 (*.*)")
            if path:
                line_edit.setText(path)

        btn_browse.clicked.connect(_on_browse)
        lay.addWidget(btn_browse)
        
        btn_test = QPushButton("试听")
        btn_test.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_test.clicked.connect(lambda: play_alert_sound(line_edit.text().strip(), default_duration))
        lay.addWidget(btn_test)
        
        btn_clear = QPushButton("重置")
        btn_clear.setToolTip("重置为默认蜂鸣")
        btn_clear.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_clear.clicked.connect(lambda: line_edit.clear())
        lay.addWidget(btn_clear)
        
        return w

    def _build_page_stages(self) -> QWidget:
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        scroll.setStyleSheet("QScrollArea{background: transparent; border: none;}")
        w = QWidget()
        w.setObjectName("scrollWidget")
        w.setStyleSheet("#scrollWidget{background: transparent;}")
        lay = QVBoxLayout(w)
        lay.setContentsMargins(0, 0, 0, 0)
        lay.setSpacing(12)
        self.switch_show_label = QCheckBox()
        self.switch_auto_advance = QCheckBox()
        self.switch_ppt_auto_start = QCheckBox()
        self.switch_double_click = QCheckBox()
        behav_lay = QVBoxLayout()
        behav_lay.setSpacing(12)
        behav_lay.addWidget(self._make_setting_row("显示环节名称", "在主悬浮球中同步显示各小节文本标题", self.switch_show_label))
        behav_lay.addWidget(self._make_setting_row("自动连播", "环节到期时自动切换下个任务并继续倒数", self.switch_auto_advance))
        behav_lay.addWidget(self._make_setting_row("PPT放映联动", "当检测到幻灯片全屏放映时，自动开始计时", self.switch_ppt_auto_start))
        behav_lay.addWidget(self._make_setting_row("双击快捷操作", "双击悬浮窗空白区域快速进行开始/暂停", self.switch_double_click))
        lay.addWidget(self._make_card("行为习惯", behav_lay))
        list_lay = QVBoxLayout()
        list_lay.setSpacing(10)
        self._stage_container = QWidget()
        self._stage_vlay = QVBoxLayout(self._stage_container)
        self._stage_vlay.setContentsMargins(0, 0, 0, 0)
        self._stage_vlay.setSpacing(10)
        list_lay.addWidget(self._stage_container)
        btn_add = QPushButton("＋ 添加阶段")
        btn_add.clicked.connect(lambda: self._add_stage_row())
        list_lay.addWidget(btn_add)
        lay.addWidget(self._make_card("计时序列规划", list_lay))
        lay.addStretch()
        scroll.setWidget(w)
        return scroll

    def _build_page_alerts(self) -> QWidget:
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        scroll.setStyleSheet("QScrollArea{background: transparent; border: none;}")
        w = QWidget()
        w.setObjectName("scrollWidget")
        w.setStyleSheet("#scrollWidget{background: transparent;}")
        lay = QVBoxLayout(w)
        lay.setContentsMargins(0, 0, 0, 0)
        lay.setSpacing(12)
        
        self.switch_global_sound = QCheckBox()
        self.switch_10s_sound = QCheckBox()
        snd_lay = QVBoxLayout()
        snd_lay.setSpacing(12)
        snd_lay.addWidget(self._make_setting_row("启用所有提示音", "全局控制蜂鸣与音频的播放许可", self.switch_global_sound))
        snd_lay.addWidget(self._make_setting_row("临近结束敲击音", "在倒计时最后10秒时，每秒触发一次提示", self.switch_10s_sound))
        
        self.txt_alert_sound = QLineEdit()
        self.txt_alert_sound.setReadOnly(True)
        self.txt_alert_sound.setPlaceholderText("系统默认蜂鸣音")
        snd_lay.addWidget(self._make_sound_picker_row("节点预警音效", self.txt_alert_sound, default_duration=200))
        
        self.txt_end_sound = QLineEdit()
        self.txt_end_sound.setReadOnly(True)
        self.txt_end_sound.setPlaceholderText("系统默认长蜂鸣")
        snd_lay.addWidget(self._make_sound_picker_row("环节结束音效", self.txt_end_sound, default_duration=2000))
        
        lay.addWidget(self._make_card("声音反馈", snd_lay))
        
        list_lay = QVBoxLayout()
        list_lay.setSpacing(10)
        self._alert_container = QWidget()
        self._alert_vlay = QVBoxLayout(self._alert_container)
        self._alert_vlay.setContentsMargins(0, 0, 0, 0)
        self._alert_vlay.setSpacing(10)
        list_lay.addWidget(self._alert_container)
        btn_add = QPushButton("＋ 新增时间阈值")
        btn_add.clicked.connect(lambda: self._add_alert_row())
        list_lay.addWidget(btn_add)
        lay.addWidget(self._make_card("时间节点变色/预警", list_lay))
        lay.addStretch()
        scroll.setWidget(w)
        return scroll

    def _build_page_appearance(self) -> QWidget:
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        scroll.setStyleSheet("QScrollArea{background: transparent; border: none;}")
        w = QWidget()
        w.setObjectName("scrollWidget")
        w.setStyleSheet("#scrollWidget{background: transparent;}")
        lay = QVBoxLayout(w)
        lay.setContentsMargins(0, 0, 0, 0)
        lay.setSpacing(12)
        c_lay = QGridLayout()
        c_lay.setVerticalSpacing(12)
        c_lay.setHorizontalSpacing(15)
        
        self._color_preview = QPushButton("拾取颜色")
        self._color_preview.setFixedSize(110, 32)
        self._color_preview.setCursor(Qt.CursorShape.PointingHandCursor)
        self._color_preview.clicked.connect(lambda: self._pick_color(self._color_preview, "_cur_color"))
        
        self._bg_color_preview = QPushButton("拾取颜色")
        self._bg_color_preview.setFixedSize(110, 32)
        self._bg_color_preview.setCursor(Qt.CursorShape.PointingHandCursor)
        self._bg_color_preview.clicked.connect(lambda: self._pick_color(self._bg_color_preview, "_cur_bg_color"))
        
        self._op_slider = QSlider(Qt.Orientation.Horizontal)
        self._op_slider.setRange(0, 70)  
        self._bg_op_slider = QSlider(Qt.Orientation.Horizontal)
        self._bg_op_slider.setRange(0, 100)
        self._font_trans_slider = QSlider(Qt.Orientation.Horizontal)
        self._font_trans_slider.setRange(0, 100) 
        c_lay.addWidget(QLabel("数字/文字颜色:"), 0, 0)
        c_lay.addWidget(self._color_preview, 0, 1)
        c_lay.addWidget(QLabel("窗口背景底色:"), 1, 0)
        c_lay.addWidget(self._bg_color_preview, 1, 1)
        c_lay.addWidget(QLabel("全局穿透度:"), 0, 2)
        c_lay.addWidget(self._op_slider, 0, 3)
        c_lay.addWidget(QLabel("背景通透度:"), 1, 2)
        c_lay.addWidget(self._bg_op_slider, 1, 3)
        c_lay.addWidget(QLabel("字体通透度:"), 2, 2)
        c_lay.addWidget(self._font_trans_slider, 2, 3)
        c_lay.setColumnStretch(1, 1)
        c_lay.setColumnStretch(3, 1)
        lay.addWidget(self._make_card("色彩与材质", c_lay))
        
        f_lay = QGridLayout()
        f_lay.setVerticalSpacing(12)
        f_lay.setHorizontalSpacing(15)
        self._font_cmb = self._create_fast_font_combobox(self.config.font)
        self._size_slider = QSlider(Qt.Orientation.Horizontal)
        self._size_slider.setRange(20, 60)
        self._stage_font_cmb = self._create_fast_font_combobox(self.config.stage_font)
        self._stage_size_slider = QSlider(Qt.Orientation.Horizontal)
        self._stage_size_slider.setRange(12, 36)
        self._ui_scale_slider = QSlider(Qt.Orientation.Horizontal)
        self._ui_scale_slider.setRange(50, 300)
        
        f_lay.addWidget(QLabel("数字字体族:"), 0, 0)
        f_lay.addWidget(self._font_cmb, 0, 1)
        f_lay.addWidget(QLabel("数字字号大小:"), 1, 0)
        f_lay.addWidget(self._size_slider, 1, 1)
        f_lay.addWidget(QLabel("全局缩放比例:"), 2, 0)
        f_lay.addWidget(self._ui_scale_slider, 2, 1)
        f_lay.addWidget(QLabel("小节文本字体:"), 0, 2)
        f_lay.addWidget(self._stage_font_cmb, 0, 3)
        f_lay.addWidget(QLabel("小节文本字号:"), 1, 2)
        f_lay.addWidget(self._stage_size_slider, 1, 3)
        f_lay.setColumnStretch(1, 1)
        f_lay.setColumnStretch(3, 1)
        lay.addWidget(self._make_card("排版与尺寸", f_lay))
        
        win_lay = QVBoxLayout()
        win_lay.setSpacing(12)
        self.switch_always_on_top = QCheckBox()
        self.switch_prevent_offscreen = QCheckBox()
        win_lay.addWidget(self._make_setting_row("窗口置顶显示", "强行保持在所有应用之上，避免被遮盖", self.switch_always_on_top))
        win_lay.addWidget(self._make_setting_row("边缘磁吸/防出界", "拖动时限制不出屏，靠近边界自动吸附", self.switch_prevent_offscreen))
        lay.addWidget(self._make_card("窗口行为", win_lay))
        lay.addStretch()
        scroll.setWidget(w)
        return scroll

    def _build_page_shortcuts(self) -> QWidget:
        w = QWidget()
        lay = QVBoxLayout(w)
        lay.setContentsMargins(0, 0, 0, 0)
        txt = "点击下方输入框后在键盘上直接按下组合键即可。\n如环境已安装keyboard模块，热键将支持在PPT全屏等失去焦点时盲操。"
        help_banner = QLabel(txt)
        help_banner.setStyleSheet("color: #005a9e; background-color: #f0f7ff; border: 1px solid #cce3f5; border-radius: 6px; padding: 12px; font-size: 12px; line-height: 1.4;")
        lay.addWidget(help_banner)
        lay.addSpacing(16)
        hk_lay = QFormLayout()
        hk_lay.setSpacing(20)
        hk_lay.setVerticalSpacing(16)
        hk_lay.setLabelAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)
        self.ks_toggle = QKeySequenceEdit()
        self.ks_reset = QKeySequenceEdit()
        self.ks_prev = QKeySequenceEdit()
        self.ks_next = QKeySequenceEdit()
        hk_lay.addRow(self._styled_label("播放 / 暂停 计时"), self.ks_toggle)
        hk_lay.addRow(self._styled_label("重置当前环节"), self.ks_reset)
        hk_lay.addRow(self._styled_label("切入上一小节"), self.ks_prev)
        hk_lay.addRow(self._styled_label("跃进下一小节"), self.ks_next)
        lay.addWidget(self._make_card("全局控制按键", hk_lay))
        lay.addStretch()
        return w

    def _styled_label(self, txt: str) -> QLabel:
        lbl = QLabel(txt)
        lbl.setStyleSheet(
            "font-weight: bold; "
            "color: #242424; "
            "background: transparent;"
        )
        return lbl

    def _create_fast_font_combobox(self, default_font: str) -> QComboBox:
        cmb = QComboBox()
        cmb.setMinimumWidth(100)
        cmb.addItems(QFontDatabase.families())
        self._set_combobox_font(cmb, default_font)
        return cmb

    def _set_combobox_font(self, cmb: QComboBox, font_name: str) -> None:
        idx = cmb.findText(font_name)
        if idx >= 0:
            cmb.setCurrentIndex(idx)
        else:
            cmb.addItem(font_name)
            cmb.setCurrentIndex(cmb.count() - 1)

    def _populate(self) -> None:
        self.switch_auto_advance.setChecked(self.config.auto_advance)
        self.switch_show_label.setChecked(self.config.show_stage_label)
        self.switch_ppt_auto_start.setChecked(self.config.ppt_auto_start)
        self.switch_double_click.setChecked(self.config.double_click_toggle)
        for s in self.config.stages:
            self._add_stage_row(s.label, s.duration, s.unit, s.count_up)
        if not self.config.stages:
            self._add_stage_row()
        self.switch_global_sound.setChecked(self.config.global_sound)
        self.switch_10s_sound.setChecked(self.config.countdown_10s_sound)
        self.txt_alert_sound.setText(self.config.alert_sound_path)
        self.txt_end_sound.setText(self.config.end_sound_path)
        for a in self.config.alerts:
            self._add_alert_row(a.seconds, a.color, a.play_sound)
        self.switch_always_on_top.setChecked(self.config.always_on_top)
        self.switch_prevent_offscreen.setChecked(self.config.prevent_offscreen)
        self._cur_color = self.config.color
        self._set_color_preview(self._color_preview, self._cur_color)
        self._cur_bg_color = self.config.bg_color
        self._set_color_preview(self._bg_color_preview, self._cur_bg_color)
        self._op_slider.setValue(self.config.global_transparency)
        self._bg_op_slider.setValue(self.config.bg_transparency)
        self._font_trans_slider.setValue(self.config.font_transparency)
        self._set_combobox_font(self._font_cmb, self.config.font)
        self._size_slider.setValue(self.config.font_size)
        self._set_combobox_font(self._stage_font_cmb, self.config.stage_font)
        self._stage_size_slider.setValue(self.config.stage_font_size)
        self._ui_scale_slider.setValue(self.config.ui_scale)
        self.ks_toggle.setKeySequence(QKeySequence(self.config.shortcut_toggle))
        self.ks_reset.setKeySequence(QKeySequence(self.config.shortcut_reset))
        self.ks_prev.setKeySequence(QKeySequence(self.config.shortcut_prev))
        self.ks_next.setKeySequence(QKeySequence(self.config.shortcut_next))

    def _add_stage_row(self, label: str = "新阶段", duration: int = 3, unit: str = "分", count_up: bool = False) -> None:
        row_widget = QWidget()
        row_widget.setObjectName("stageRow")
        row_widget.setStyleSheet("""
            QWidget#stageRow {
                background: #ffffff;
                color: #242424;
                border: 1px solid #eaeaea;
                border-radius: 6px;
            }

            QWidget#stageRow:hover {
                border-color: #0078d4;
            }

            QWidget#stageRow QLineEdit,
            QWidget#stageRow QSpinBox,
            QWidget#stageRow QComboBox {
                background: #ffffff;
                color: #242424;
            }
        """)
        h = QHBoxLayout(row_widget)
        h.setContentsMargins(12, 8, 12, 8)
        h.setSpacing(10)
        name = QLineEdit()
        name.setText(str(label))
        name.setPlaceholderText("环节名称")
        name.setMaxLength(100)
        h.addWidget(name, 2)
        spin = QSpinBox()
        spin.setRange(1, 9999)
        spin.setValue(duration)
        spin.setMinimumWidth(65)
        h.addWidget(spin)
        unit_cmb = QComboBox()
        unit_cmb.addItems(["分", "秒"])
        unit_cmb.setCurrentText(str(unit))
        unit_cmb.setMinimumWidth(55)
        h.addWidget(unit_cmb)
        dir_cmb = QComboBox()
        dir_cmb.addItems(["倒计时", "正计时"])
        dir_cmb.setCurrentText("正计时" if count_up else "倒计时")
        dir_cmb.setMinimumWidth(75)
        h.addWidget(dir_cmb)
        row = {"widget": row_widget, "name": name, "spin": spin, "unit_cmb": unit_cmb, "dir_cmb": dir_cmb}
        self._add_row_controls(h, self._stage_rows, row, self._rebuild_stage_rows)
        self._stage_rows.append(row)
        self._stage_vlay.addWidget(row_widget)

    def _rebuild_stage_rows(self) -> None:
        self._rebuild_rows(self._stage_vlay, self._stage_rows,
                           lambda r: self._add_stage_row(r["name"].text(), r["spin"].value(), r["unit_cmb"].currentText(), r["dir_cmb"].currentText() == "正计时"))

    def _add_alert_row(self, seconds: int = 20, color: str = "#ffaa00", play_sound: bool = True) -> None:
        row_widget = QWidget()
        row_widget.setObjectName("alertRow")
        row_widget.setStyleSheet("""
            QWidget#alertRow {
                background: #ffffff;
                color: #242424;
                border: 1px solid #eaeaea;
                border-radius: 6px;
            }

            QWidget#alertRow:hover {
                border-color: #0078d4;
            }

            QWidget#alertRow QSpinBox {
                background: #ffffff;
                color: #242424;
            }

            QWidget#alertRow QCheckBox {
                color: #242424;
            }
        """)
        h = QHBoxLayout(row_widget)
        h.setContentsMargins(12, 8, 12, 8)
        h.setSpacing(10)
        lbl = QLabel("剩余时长：")
        h.addWidget(lbl)
        spin = QSpinBox()
        spin.setRange(1, 9999)
        spin.setSuffix(" 秒")
        spin.setValue(seconds)
        spin.setMinimumWidth(85)
        h.addWidget(spin)
        cbtn = QPushButton()
        cbtn.setFixedSize(32, 32)
        cbtn.setCursor(Qt.CursorShape.PointingHandCursor)
        self._set_color_preview(cbtn, color)
        chk_sound = QCheckBox("伴随音效")
        chk_sound.setChecked(play_sound)
        row = {"widget": row_widget, "spin": spin, "color": color, "cbtn": cbtn, "chk_sound": chk_sound}
        cbtn.clicked.connect(partial(self._pick_alert_color, row))
        h.addWidget(cbtn)
        h.addWidget(chk_sound)
        h.addStretch()
        self._add_row_controls(h, self._alert_rows, row, self._rebuild_alert_rows)
        self._alert_rows.append(row)
        self._alert_vlay.addWidget(row_widget)

    def _pick_alert_color(self, row: dict) -> None:
        c = QColorDialog.getColor(QColor(row["color"]), self)
        if c.isValid():
            row["color"] = c.name()
            self._set_color_preview(row["cbtn"], c.name())

    def _rebuild_alert_rows(self) -> None:
        self._rebuild_rows(self._alert_vlay, self._alert_rows,
                           lambda r: self._add_alert_row(r["spin"].value(), r["color"], r["chk_sound"].isChecked()))

    def _add_row_controls(self, layout: QHBoxLayout, rows: list, row: dict, rebuild_fn) -> None:
        layout.addSpacing(10)
        btn_up = QPushButton()
        btn_up.setFixedSize(28, 28)
        btn_up.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_up.setIcon(get_svg_icon("up", 14, "#666666"))
        btn_up.setStyleSheet("QPushButton { background:transparent; border:none; border-radius:4px; } QPushButton:hover { background:#e1e1e1; }")
        btn_up.clicked.connect(partial(self._move_row, rows, row, -1, rebuild_fn))
        layout.addWidget(btn_up)
        btn_down = QPushButton()
        btn_down.setFixedSize(28, 28)
        btn_down.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_down.setIcon(get_svg_icon("down", 14, "#666666"))
        btn_down.setStyleSheet("QPushButton { background:transparent; border:none; border-radius:4px; } QPushButton:hover { background:#e1e1e1; }")
        btn_down.clicked.connect(partial(self._move_row, rows, row, 1, rebuild_fn))
        layout.addWidget(btn_down)
        btn_del = QPushButton()
        btn_del.setFixedSize(28, 28)
        btn_del.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_del.setIcon(get_svg_icon("trash", 14, "#d13438"))
        btn_del.setStyleSheet("QPushButton { background:transparent; border:none; border-radius:4px; } QPushButton:hover { background:#fde7e9; }")
        btn_del.clicked.connect(partial(self._delete_row, rows, row, rebuild_fn))
        layout.addWidget(btn_del)

    def _move_row(self, rows: list, row: dict, delta: int, rebuild_fn) -> None:
        idx = rows.index(row)
        new_idx = idx + delta
        if 0 <= new_idx < len(rows):
            rows[idx], rows[new_idx] = rows[new_idx], rows[idx]
            rebuild_fn()

    def _delete_row(self, rows: list, row: dict, rebuild_fn) -> None:
        if len(rows) > 1:
            rows.remove(row)
            rebuild_fn()

    def _rebuild_rows(self, layout: QVBoxLayout, rows: list, add_fn) -> None:
        saved = list(rows)
        rows.clear()
        while layout.count():
            w = layout.takeAt(0).widget()
            if w: w.deleteLater()
        for r in saved: 
            add_fn(r)

    def _pick_color(self, btn: QPushButton, attr_name: str) -> None:
        current_color = getattr(self, attr_name)
        c = QColorDialog.getColor(QColor(current_color), self)
        if c.isValid():
            setattr(self, attr_name, c.name())
            self._set_color_preview(btn, c.name())
            self._trigger_live_preview() 

    @staticmethod
    def _set_color_preview(widget: QWidget, color: str) -> None:
        if isinstance(widget, QPushButton) and widget.text() == "":
            widget.setStyleSheet(f"background: {color}; border: 1px solid #d1d1d1; border-radius: 4px;")
        else:
            widget.setStyleSheet(f"background: {color}; border: 1px solid #d1d1d1; border-radius: 4px; color: {color};")

    def _restore_defaults(self) -> None:
        reply = QMessageBox.question(
            self, "确认重置", "是否确认恢复默认配置？您的修改将被覆盖。",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        if reply == QMessageBox.StandardButton.Yes:
            self.config = Config()
            for row in list(self._stage_rows):
                if row.get("widget"): row["widget"].deleteLater()
            self._stage_rows.clear()
            for row in list(self._alert_rows):
                if row.get("widget"): row["widget"].deleteLater()
            self._alert_rows.clear()
            self._populate()
            self._trigger_live_preview()
            QMessageBox.information(self, "重置成功", "已加载默认方案。点击“保存应用”后生效。")

    def _validate_shortcuts(self) -> bool:
        mapping = {
            "【播放 / 暂停】": self.ks_toggle.keySequence().toString(),
            "【重置当前小节】": self.ks_reset.keySequence().toString(),
            "【上一环节】": self.ks_prev.keySequence().toString(),
            "【下一环节】": self.ks_next.keySequence().toString()
        }
        active_shortcuts = {name: seq for name, seq in mapping.items() if seq.strip()}
        seen = {}
        for name, seq in active_shortcuts.items():
            if seq in seen:
                QMessageBox.critical(
                    self, "快捷键冲突", 
                    f"保存失败：您的“{name}”与“{seen[seq]}”指定了同一组按键：【{seq}】。\n\n请修改不一致的按键后再行应用。"
                )
                return False
            seen[seq] = name
        return True

    def _connect_live_preview_triggers(self) -> None:
        self.switch_show_label.toggled.connect(self._trigger_live_preview)
        self.switch_always_on_top.toggled.connect(self._trigger_live_preview)
        self.switch_prevent_offscreen.toggled.connect(self._trigger_live_preview)
        self._op_slider.valueChanged.connect(self._trigger_live_preview)
        self._bg_op_slider.valueChanged.connect(self._trigger_live_preview)
        self._font_trans_slider.valueChanged.connect(self._trigger_live_preview)
        self._size_slider.valueChanged.connect(self._trigger_live_preview)
        self._stage_size_slider.valueChanged.connect(self._trigger_live_preview)
        self._ui_scale_slider.valueChanged.connect(self._trigger_live_preview)
        self._font_cmb.currentTextChanged.connect(self._trigger_live_preview)
        self._stage_font_cmb.currentTextChanged.connect(self._trigger_live_preview)

    def _trigger_live_preview(self) -> None:
        self.config.show_stage_label = self.switch_show_label.isChecked()
        self.config.always_on_top = self.switch_always_on_top.isChecked()
        self.config.prevent_offscreen = self.switch_prevent_offscreen.isChecked()
        self.config.color = self._cur_color
        self.config.bg_color = self._cur_bg_color
        self.config.global_transparency = self._op_slider.value()
        self.config.bg_transparency = self._bg_op_slider.value()
        self.config.font_transparency = self._font_trans_slider.value()
        self.config.opacity = (100 - self.config.global_transparency) / 100
        self.config.font = self._font_cmb.currentText()
        self.config.font_size = self._size_slider.value()
        self.config.stage_font = self._stage_font_cmb.currentText()
        self.config.stage_font_size = self._stage_size_slider.value()
        self.config.ui_scale = self._ui_scale_slider.value()
        self.preview_requested.emit()

    def restore_backup(self) -> None:
        for k, v in self._backup_attrs.items():
            setattr(self.config, k, v)

    def reject(self) -> None:
        self.restore_backup()
        super().reject()

    def get_config(self) -> Config:
        self.config.auto_advance = self.switch_auto_advance.isChecked()
        self.config.show_stage_label = self.switch_show_label.isChecked()
        self.config.ppt_auto_start = self.switch_ppt_auto_start.isChecked()
        self.config.double_click_toggle = self.switch_double_click.isChecked()
        self.config.global_sound = self.switch_global_sound.isChecked()
        self.config.countdown_10s_sound = self.switch_10s_sound.isChecked()
        self.config.alert_sound_path = self.txt_alert_sound.text().strip()
        self.config.end_sound_path = self.txt_end_sound.text().strip()
        self.config.always_on_top = self.switch_always_on_top.isChecked()
        self.config.prevent_offscreen = self.switch_prevent_offscreen.isChecked()
        self.config.stages = [Stage(r["name"].text(), r["spin"].value(), r["unit_cmb"].currentText(), r["dir_cmb"].currentText() == "正计时") for r in self._stage_rows]
        self.config.alerts = [Alert(r["spin"].value(), r["color"], r["chk_sound"].isChecked()) for r in self._alert_rows]
        self.config.color = self._cur_color
        self.config.bg_color = self._cur_bg_color
        self.config.global_transparency = self._op_slider.value()
        self.config.bg_transparency = self._bg_op_slider.value()
        self.config.font_transparency = self._font_trans_slider.value()
        self.config.opacity = (100 - self.config.global_transparency) / 100
        self.config.font = self._font_cmb.currentText()
        self.config.font_size = self._size_slider.value()
        self.config.stage_font = self._stage_font_cmb.currentText()
        self.config.stage_font_size = self._stage_size_slider.value()
        self.config.ui_scale = self._ui_scale_slider.value()
        self.config.shortcut_toggle = self.ks_toggle.keySequence().toString()
        self.config.shortcut_reset = self.ks_reset.keySequence().toString()
        self.config.shortcut_prev = self.ks_prev.keySequence().toString()
        self.config.shortcut_next = self.ks_next.keySequence().toString()
        return self.config

class HotkeyBridge(QObject):
    toggle = Signal()
    reset = Signal()
    prev = Signal()
    next = Signal()

class App(QObject):
    def __init__(self):
        super().__init__()
        self.config = Config()
        self.config.load()
        self.float_bar = FloatBar()
        self.controller = TimerController(self.config)
        self._shortcuts = []
        self.hotkey_bridge = HotkeyBridge()
        self.hotkey_bridge.toggle.connect(self.controller.toggle_pause)
        self.hotkey_bridge.reset.connect(self.controller.restart_stage)
        self.hotkey_bridge.prev.connect(self.controller.prev_stage)
        self.hotkey_bridge.next.connect(self.controller.next_stage)
        self._ppt_was_active = False
        self._ppt_stable_active_count = 0
        self._current_ppt_session_paused_by_user = False
        self._ppt_monitor_timer = QTimer(self)
        self._ppt_monitor_timer.timeout.connect(self._check_ppt_status)
        self._ppt_monitor_timer.start(600)
        self._save_timer = QTimer(self)
        self._save_timer.setSingleShot(True)
        self._save_timer.timeout.connect(self.config.save)
        self._connect_signals()
        self._apply_style()
        self._apply_shortcuts()
        self.controller.stop()
        
        if self.config.pos_x >= 0 and self.config.pos_y >= 0:
            self.float_bar.move(self.config.pos_x, self.config.pos_y)
        else:
            screen = self.float_bar.screen().availableGeometry()
            self.float_bar.move(screen.left() + 40, screen.top() + 40)
            
        self.float_bar.show()

    def _check_ppt_status(self) -> None:
        if not self.config.ppt_auto_start:
            return
        is_active = is_ppt_slideshow_active()
        if is_active:
            self._ppt_stable_active_count += 1
            if self._ppt_stable_active_count >= 2 and not self._ppt_was_active:
                self._ppt_was_active = True
                self._current_ppt_session_paused_by_user = False
                if self.controller.paused and self.controller._remaining_float > 0:
                    self.controller.toggle_pause()
            elif self._ppt_stable_active_count >= 2:
                if self.controller.paused and self.controller._remaining_float > 0:
                    if not self._current_ppt_session_paused_by_user:
                        self.controller.toggle_pause()
        else:
            self._ppt_stable_active_count = 0
            if self._ppt_was_active:
                self._ppt_was_active = False
                self._current_ppt_session_paused_by_user = False
                if not self.controller.paused:
                    self.controller.toggle_pause()

    def _on_user_interaction(self):
        if is_ppt_slideshow_active():
            self._current_ppt_session_paused_by_user = True

    def _connect_signals(self) -> None:
        fb = self.float_bar
        ctrl = self.controller
        for btn in (fb.btn_toggle, fb.btn_restart, fb.btn_prev, fb.btn_next):
            btn.clicked.connect(self._on_user_interaction)
        fb.btn_toggle.clicked.connect(ctrl.toggle_pause)
        fb.btn_restart.clicked.connect(ctrl.restart_stage)
        fb.btn_prev.clicked.connect(ctrl.prev_stage)
        fb.btn_next.clicked.connect(ctrl.next_stage)
        fb.btn_restart.clicked.connect(self._on_stage_reset)
        fb.btn_prev.clicked.connect(self._on_stage_reset)
        fb.btn_next.clicked.connect(self._on_stage_reset)
        fb.btn_settings.clicked.connect(self._open_settings)
        fb.btn_close.clicked.connect(self._exit)
        fb.request_settings.connect(self._open_settings)
        fb.request_exit.connect(self._exit)
        fb.double_clicked.connect(self._on_double_clicked)
        fb.wheel_scrolled.connect(self._on_wheel_scrolled)
        fb.position_changed.connect(self._on_position_changed)
        ctrl.tick.connect(lambda lbl, rem: fb.update_display(lbl, rem))
        ctrl.alert_triggered.connect(lambda c: fb.start_flash(c, 3000))
        ctrl.loop_restarted.connect(lambda: fb.start_flash(self.config.color, 1500))
        ctrl.state_changed.connect(fb.set_running)

    def _on_position_changed(self, x: int, y: int) -> None:
        self.config.pos_x = x
        self.config.pos_y = y
        self._save_timer.start(500)

    def _on_wheel_scrolled(self, delta: int) -> None:
        new_scale = max(50, min(300, self.config.ui_scale + delta))
        if new_scale != self.config.ui_scale:
            self.config.ui_scale = new_scale
            self._apply_style()
            self._save_timer.start(500) 

    def _on_double_clicked(self) -> None:
        if self.config.double_click_toggle:
            self.controller.toggle_pause()

    def _apply_style(self) -> None:
        c = self.config
        opacity_float = max(0.3, min(1.0, (100 - c.global_transparency) / 100))
        self.float_bar.apply_style(c.color, c.font, c.font_size, c.stage_font, c.stage_font_size,
                                   opacity_float, c.bg_qcolor(), c.always_on_top, c.show_stage_label, 
                                   c.prevent_offscreen, c.font_transparency, c.ui_scale)

    def _apply_shortcuts(self) -> None:
        for sc in self._shortcuts:
            sc.setEnabled(False)
            sc.deleteLater()
        self._shortcuts.clear()
        if HAS_KEYBOARD:
            keyboard.unhook_all()
            mapping = [
                (self.config.shortcut_toggle, self.hotkey_bridge.toggle),
                (self.config.shortcut_reset, self.hotkey_bridge.reset),
                (self.config.shortcut_prev, self.hotkey_bridge.prev),
                (self.config.shortcut_next, self.hotkey_bridge.next),
            ]
            for key_str, signal in mapping:
                if key_str:
                    k_str = key_str.lower().replace("return", "enter")
                    try:
                        keyboard.add_hotkey(k_str, signal.emit, suppress=False)
                    except Exception:
                        pass
        else:
            mapping_qt = [
                (self.config.shortcut_toggle, self.controller.toggle_pause),
                (self.config.shortcut_reset, self.controller.restart_stage),
                (self.config.shortcut_prev, self.controller.prev_stage),
                (self.config.shortcut_next, self.controller.next_stage),
            ]
            for key_str, slot_func in mapping_qt:
                if key_str:
                    sc = QShortcut(QKeySequence(key_str), self.float_bar)
                    sc.setContext(Qt.ShortcutContext.ApplicationShortcut)
                    sc.activated.connect(slot_func)
                    self._shortcuts.append(sc)

    def _open_settings(self) -> None:
        dlg = SettingsWindow(self.config)
        dlg.preview_requested.connect(self._apply_style)
        res = dlg.exec()
        if res == QDialog.DialogCode.Rejected:
            self._apply_style()
        else:
            self._save_settings(dlg)
        dlg.deleteLater()

    def _save_settings(self, dlg: SettingsWindow) -> None:
        if not dlg._validate_shortcuts():
            return
        dlg.get_config()
        self.config.save()
        self._apply_style()
        self._apply_shortcuts()
        self.controller.config = self.config
        self.controller.stop()

    def _exit(self) -> None:
        self.controller.stop()
        self._ppt_monitor_timer.stop()
        if HAS_KEYBOARD:
            keyboard.unhook_all()
        for sc in self._shortcuts:
            sc.setEnabled(False)
            sc.deleteLater()
        self.float_bar.close()
        QApplication.quit()

    def _on_stage_reset(self) -> None:
        self._current_ppt_session_paused_by_user = False
        if is_ppt_slideshow_active() and self.config.ppt_auto_start:
            if self.controller.paused and self.controller._remaining_float > 0:
                self.controller.toggle_pause()

if __name__ == "__main__":
    app = QApplication(sys.argv)
    app.setStyle("Fusion")
    
    app.setApplicationName(__app_name__)
    app.setQuitOnLastWindowClosed(False)
    translator = QTranslator()
    locale = QLocale.system().name()  
    if translator.load(f"qt_{locale}", QLibraryInfo.path(QLibraryInfo.LibraryPath.TranslationsPath)):
        app.installTranslator(translator)
    shared_mem_key = f"{__app_name__}_SingleInstance_MemoryLock"
    shared_mem = QSharedMemory(shared_mem_key)
    
    if not shared_mem.create(1):
        if shared_mem.attach():
            QMessageBox.warning(None, "程序已启动", f"{__app_name__} 已在运行中！")
            sys.exit(0)
        else:
            shared_mem.create(1)
            
    main = App()
    exit_code = app.exec()
    if shared_mem.isAttached():
        shared_mem.detach()
    sys.exit(exit_code)