import sys
import json
import os
import platform
import threading
import subprocess
import time
import math
import ctypes
import copy
from dataclasses import dataclass, asdict
from functools import partial
from typing import Dict, List, Optional

from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
from PyQt5.QtGui import *
from PyQt5.QtSvg import QSvgRenderer

APP_NAME = "QTimer"
APP_VERSION = "1.3.0"

def get_app_dir() -> str:
    if getattr(sys, 'frozen', False):
        return os.path.dirname(sys.executable)
    return os.path.dirname(os.path.abspath(__file__))

def get_config_path() -> str:
    local_path = os.path.join(get_app_dir(), f".{APP_NAME.lower()}_config.json")
    try:
        if not os.path.exists(local_path):
            with open(local_path, 'w', encoding="utf-8") as f:
                f.write("{}")
        else:
            with open(local_path, 'r+', encoding="utf-8") as f:
                pass
        return local_path
    except (PermissionError, IOError):
        user_path = os.path.join(os.path.expanduser("~"), f".{APP_NAME.lower()}_config.json")
        if not os.path.exists(user_path):
            try:
                with open(user_path, 'w', encoding="utf-8") as f:
                    f.write("{}")
            except Exception:
                pass
        return user_path

CONFIG_PATH = get_config_path()

def is_ppt_slideshow_active() -> bool:
    if platform.system() != "Windows":
        return False
    try:
        active = False
        def check_hwnd(hwnd):
            if not ctypes.windll.user32.IsWindowVisible(hwnd):
                return False
            buf_cls = ctypes.create_unicode_buffer(256)
            ctypes.windll.user32.GetClassNameW(hwnd, buf_cls, 256)
            cls = buf_cls.value.lower()
            buf_t = ctypes.create_unicode_buffer(512)
            ctypes.windll.user32.GetWindowTextW(hwnd, buf_t, 512)
            title = buf_t.value.lower()
            if "screenclass" in cls:
                return True
            if "幻灯片放映" in title and ("wps" in title or "演示" in title):
                return True
            return False
        def enum_cb(hwnd, lparam):
            nonlocal active
            if check_hwnd(hwnd):
                active = True
                return False
            return True
        WNDENUMPROC = ctypes.WINFUNCTYPE(ctypes.c_bool, ctypes.c_void_p, ctypes.c_void_p)
        ctypes.windll.user32.EnumWindows(WNDENUMPROC(enum_cb), 0)
        return active
    except Exception:
        return False

def play_alert_sound(duration_ms: int = 200) -> None:
    sys_name = platform.system()
    if sys_name == "Windows":
        def _beep():
            try:
                import winsound
                winsound.Beep(1500, duration_ms)
            except Exception:
                pass
        t = threading.Thread(target=_beep, daemon=True)
        t.start()
    elif sys_name == "Darwin":
        def _mac_beep():
            try:
                subprocess.call(['afplay', '/System/Library/Sounds/Glass.aiff'])
            except Exception:
                pass
        t = threading.Thread(target=_mac_beep, daemon=True)
        t.start()
    else:
        QApplication.beep()

def get_rgba_color(hex_color: str, alpha_pct: int) -> str:
    col = QColor(hex_color)
    return f"rgba({col.red()}, {col.green()}, {col.blue()}, {alpha_pct / 100:.2f})"

SVG_ICONS: Dict[str, str] = {
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

_ICON_CACHE: Dict[str, QIcon] = {}

def get_svg_icon(name: str, size: int, color: str = "white") -> QIcon:
    app = QApplication.instance()
    dpr = app.devicePixelRatio() if app else 1.0
    cache_key = f"{name}_{size}_{color}_{dpr}"
    
    if cache_key in _ICON_CACHE:
        return _ICON_CACHE[cache_key]
        
    svg_str = SVG_ICONS.get(name, "").replace("{color}", color)
    if not svg_str:
        return QIcon()
        
    renderer = QSvgRenderer(svg_str.encode("utf-8"))
    
    # 物理分辨率映射：计算真实物理像素尺寸
    physical_size = int(size * dpr)
    if physical_size < 1:
        physical_size = 1
        
    pixmap = QPixmap(physical_size, physical_size)
    pixmap.fill(Qt.transparent)
    
    # 在纯物理像素上进行绘制，避免坐标系被缩放干扰
    painter = QPainter(pixmap)
    painter.setRenderHints(QPainter.Antialiasing | QPainter.SmoothPixmapTransform)
    renderer.render(painter, QRectF(0, 0, physical_size, physical_size))
    painter.end()
    
    # 绘制完成后再设置像素比
    pixmap.setDevicePixelRatio(dpr)
    
    icon = QIcon(pixmap)
    _ICON_CACHE[cache_key] = icon
    return icon

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
        self.always_on_top: bool = True
        self.prevent_offscreen: bool = True
        self.show_stage_label: bool = True
        self.ppt_auto_start: bool = True
        self.double_click_toggle: bool = True

        self.stages: List[Stage] = [Stage("说课时间", 5, "分", False), Stage("答辩时间", 2, "分", False)]
        self.alerts: List[Alert] = [Alert(30, "#ffaa00", True), Alert(10, "#ff4444", True)]
        
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
        except Exception as e:
            print(f"配置保存异常: {e}")

    def load(self) -> None:
        if not os.path.exists(CONFIG_PATH):
            return
        try:
            with open(CONFIG_PATH, "r", encoding="utf-8") as f:
                content = f.read().strip()
                if not content:
                    return
                d = json.loads(content)
            for key in ("auto_advance", "global_sound", "countdown_10s_sound", "always_on_top",
                        "prevent_offscreen", "show_stage_label", "ppt_auto_start", "double_click_toggle",
                        "color", "font", "font_size", "stage_font", "stage_font_size", "bg_color",
                        "global_transparency", "bg_transparency", "font_transparency", 
                        "shortcut_toggle", "shortcut_reset", "shortcut_prev", "shortcut_next", "ui_scale"):
                if key in d:
                    setattr(self, key, d[key])

            if "opacity" in d and "global_transparency" not in d:
                self.global_transparency = max(0, min(70, int(round((1.0 - float(d["opacity"])) * 100))))
            if "bg_opacity" in d and "bg_transparency" not in d:
                self.bg_transparency = max(0, min(60, 100 - int(d["bg_opacity"])))
            if "font_opacity" in d and "font_transparency" not in d:
                self.font_transparency = max(0, min(100, 100 - int(d["font_opacity"])))

            if "stages" in d:
                self.stages = [Stage.from_dict(s) for s in d["stages"]]
            if "alerts" in d:
                self.alerts = [Alert.from_dict(a) for a in d["alerts"]]
        except Exception as e:
            print(f"配置加载异常: {e}")

    def bg_qcolor(self) -> QColor:
        c = QColor(self.bg_color)
        opacity_pct = max(0, min(100, 100 - self.bg_transparency))
        c.setAlpha(int(opacity_pct / 100 * 255))
        return c

class TimerController(QObject):
    tick = pyqtSignal(str, int)
    stage_changed = pyqtSignal(int, str)
    alert_triggered = pyqtSignal(str)
    loop_restarted = pyqtSignal()
    state_changed = pyqtSignal(bool)

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
                    play_alert_sound(200)
                for a in self.config.alerts:
                    if rem_sec == a.seconds and a.seconds not in self._triggered:
                        self._triggered.add(a.seconds)
                        self.alert_triggered.emit(a.color)
                        if a.play_sound:
                            play_alert_sound(200)

        if self._remaining_float <= 0 and not self._zero_triggered:
            self._zero_triggered = True
            self._remaining_float = 0.0
            if self.config.global_sound:
                play_alert_sound(2000)
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
    request_settings = pyqtSignal()
    request_exit = pyqtSignal()
    double_clicked = pyqtSignal()
    wheel_scrolled = pyqtSignal(int)

    def __init__(self):
        super().__init__()
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.Tool)
        self.setAttribute(Qt.WA_ShowWithoutActivating)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setAttribute(Qt.WA_Hover)
        self.setFocusPolicy(Qt.ClickFocus)

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
        self._width_anim.setEasingCurve(QEasingCurve.OutCubic)

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

    @pyqtProperty(int)
    def bar_width(self) -> int:
        return self.width()

    @bar_width.setter
    def bar_width(self, w: int) -> None:
        self.setFixedWidth(w)

    def _build_ui(self) -> None:
        self._canvas = QWidget(self)
        self._canvas.move(0, 0)
        self._layout = QHBoxLayout(self._canvas)
        self._layout.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)
        self._layout.setContentsMargins(18, 0, 0, 0)
        self._layout.setSpacing(0)

        self.lbl_stage = QLabel("环节名称")
        self.lbl_stage.setAlignment(Qt.AlignCenter)
        self.lbl_time = QLabel("00:00")
        self.lbl_time.setAlignment(Qt.AlignCenter)

        self._layout.addWidget(self.lbl_stage)
        self._spacing_item = QSpacerItem(12, 0, QSizePolicy.Fixed, QSizePolicy.Fixed)
        self._layout.addItem(self._spacing_item)
        self._layout.addWidget(self.lbl_time)
        self._end_spacing_item = QSpacerItem(18, 0, QSizePolicy.Fixed, QSizePolicy.Fixed)
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
        self._layout.addWidget(self._btn_container)

        self.setContextMenuPolicy(Qt.CustomContextMenu)
        self.customContextMenuRequested.connect(self._show_ctx_menu)

    def _make_icon_btn(self, icon_name: str, tip: str) -> QPushButton:
        b = QPushButton()
        b.setProperty("icon_name", icon_name)
        b.setToolTip(tip)
        b.setCursor(Qt.PointingHandCursor)
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
        self._end_spacing_item.changeSize(int(18 * scale), 0, QSizePolicy.Fixed, QSizePolicy.Fixed)
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
            flags |= Qt.WindowStaysOnTopHint
        else:
            flags &= ~Qt.WindowStaysOnTopHint
            
        if flags != self.windowFlags():
            was_visible = self.isVisible()
            pos_before = self.pos()
            self.setWindowFlags(flags)
            self.setAttribute(Qt.WA_TranslucentBackground, True)
            if was_visible:
                self.move(pos_before)
                self.show()

        self._refresh_labels()
        self._update_size()
        self.update()

    def _refresh_labels(self, stage_color: Optional[str] = None, time_color: Optional[str] = None) -> None:
        sc = stage_color or self._text_color
        tc = time_color or self._text_color
        
        opacity_pct = max(0, min(100, 100 - self._font_transparency))
        rgba_sc = get_rgba_color(sc, opacity_pct)
        rgba_tc = get_rgba_color(tc, opacity_pct)
        
        self.lbl_stage.setStyleSheet(
            f"color:{rgba_sc}; font-family:'{self._stage_font_family}'; "
            f"font-size:{self._stage_font_size}px; font-weight:600; background:transparent;")
        self.lbl_time.setStyleSheet(
            f"color:{rgba_tc}; font-family:'{self._font_family}'; "
            f"font-size:{self._font_size}px; font-weight:900; background:transparent;")
        self.lbl_stage.style().polish(self.lbl_stage)
        self.lbl_time.style().polish(self.lbl_time)

    def _update_size(self) -> None:
        if hasattr(self, '_anim_group'):
            self._anim_group.stop()
            
        scale = getattr(self, '_ui_scale', 100) / 100.0
        fm_stage = self.lbl_stage.fontMetrics()
        fm_time = self.lbl_time.fontMetrics()
        text = self._current_stage_text or "环节名称"
        
        time_w = fm_time.horizontalAdvance("88:88") + int(20 * scale)
        self.lbl_time.setFixedWidth(time_w)

        btn_w = (getattr(self, '_icon_size', 34) + int(2 * scale)) * 6
        self._btn_container.setFixedWidth(btn_w)

        base_margin = int(18 * scale)
        stage_spacing = int(12 * scale)

        if self._show_stage_label:
            self.lbl_stage.show()
            self._spacing_item.changeSize(stage_spacing, 0, QSizePolicy.Fixed, QSizePolicy.Fixed)
            stage_w = fm_stage.horizontalAdvance(text) + int(20 * scale)
            self.lbl_stage.setText(text)
            self.lbl_stage.setFixedWidth(stage_w)
            self._text_width = base_margin + stage_w + stage_spacing + time_w + base_margin
        else:
            self.lbl_stage.hide()
            self._spacing_item.changeSize(0, 0, QSizePolicy.Fixed, QSizePolicy.Fixed)
            self.lbl_stage.setFixedWidth(0)
            self._text_width = base_margin + time_w + base_margin

        self._layout.invalidate()
        self._full_width = self._text_width + btn_w + int(16 * scale)

        h = max(self._font_size + int(24 * scale), int(50 * scale))
        self._canvas.setFixedSize(self._full_width, h)
        self.setFixedHeight(h)

        if self.underMouse():
            self.setFixedWidth(self._full_width)
            self._btn_opacity.setOpacity(1.0)
        else:
            self.setFixedWidth(self._text_width)
            self._btn_opacity.setOpacity(0.0)
            
        self._ensure_onscreen()

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
        mm, ss = divmod(display_sec, 60)
        if self._current_stage_text != stage:
            self._current_stage_text = stage
            self._update_size()
        self.lbl_time.setText(f"{mm:02d}:{ss:02d}")

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
        self._refresh_labels()

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
        m.exec_(self.mapToGlobal(pos))

    def wheelEvent(self, e: QWheelEvent) -> None:
        if e.modifiers() & Qt.ControlModifier:
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
        p.setRenderHint(QPainter.Antialiasing)
        p.setBrush(self._bg_color)
        p.setPen(Qt.NoPen)
        radius = int(12 * getattr(self, '_ui_scale', 100) / 100.0)
        p.drawRoundedRect(self.rect(), radius, radius)

    def mouseDoubleClickEvent(self, e: QMouseEvent) -> None:
        if e.button() == Qt.LeftButton:
            self.double_clicked.emit()
        super().mouseDoubleClickEvent(e)

    def mousePressEvent(self, e: QMouseEvent) -> None:
        if e.button() == Qt.LeftButton:
            self._drag_pos = e.globalPos() - self.pos()
            QToolTip.showText(e.globalPos(), f"窗体透明度: {self._global_transparency}%", self)

    def mouseMoveEvent(self, e: QMouseEvent) -> None:
        if self._drag_pos and e.buttons() == Qt.LeftButton:
            new_pos = e.globalPos() - self._drag_pos
            if self._prevent_offscreen:
                screen = self.screen().availableGeometry()
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
            QToolTip.showText(e.globalPos(), f"窗体透明度: {self._global_transparency}%", self)

    def mouseReleaseEvent(self, e: QMouseEvent) -> None:
        self._drag_pos = None
        QToolTip.hideText()
        self._ensure_onscreen()

    def moveEvent(self, e: QMoveEvent) -> None:
        super().moveEvent(e)
        self.setAttribute(Qt.WA_TranslucentBackground, True)
        if hasattr(self, '_target_opacity'):
            self.setWindowOpacity(self._target_opacity)

    def resizeEvent(self, e: QResizeEvent) -> None:
        super().resizeEvent(e)
        self.setAttribute(Qt.WA_TranslucentBackground, True)
        if hasattr(self, '_target_opacity'):
            self.setWindowOpacity(self._target_opacity)

    def showEvent(self, e: QShowEvent) -> None:
        super().showEvent(e)
        self.setAttribute(Qt.WA_TranslucentBackground, True)
        if hasattr(self, '_target_opacity'):
            self.setWindowOpacity(self._target_opacity)

class ToggleSwitch(QCheckBox):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedSize(42, 22)
        self.setCursor(Qt.PointingHandCursor)
        
        self._thumb_radius = 9
        self._margin = 2
        self._bg_color_off = QColor("#d1d1d6")
        self._bg_color_on = QColor("#0078d4")
        
        self._thumb_pos = self._margin
        
        self._anim = QPropertyAnimation(self, b"thumb_pos")
        self._anim.setDuration(150)
        self._anim.setEasingCurve(QEasingCurve.InOutQuad)
        self.toggled.connect(self._start_anim)

    @pyqtProperty(float)
    def thumb_pos(self):
        return self._thumb_pos

    @thumb_pos.setter
    def thumb_pos(self, pos):
        self._thumb_pos = pos
        self.update()

    def _start_anim(self, checked):
        self._anim.stop()
        end_val = self.width() - self._thumb_radius * 2 - self._margin if checked else self._margin
        self._anim.setEndValue(end_val)
        self._anim.start()

    def showEvent(self, e):
        self._thumb_pos = self.width() - self._thumb_radius * 2 - self._margin if self.isChecked() else self._margin
        super().showEvent(e)

    def paintEvent(self, e):
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing)
        
        progress = (self._thumb_pos - self._margin) / (self.width() - self._thumb_radius * 2 - self._margin * 2)
        progress = max(0.0, min(1.0, progress))
        r = int(self._bg_color_off.red() + (self._bg_color_on.red() - self._bg_color_off.red()) * progress)
        g = int(self._bg_color_off.green() + (self._bg_color_on.green() - self._bg_color_off.green()) * progress)
        b = int(self._bg_color_off.blue() + (self._bg_color_on.blue() - self._bg_color_off.blue()) * progress)
        
        p.setBrush(QColor(r, g, b))
        p.setPen(Qt.NoPen)
        p.drawRoundedRect(self.rect(), self.height() / 2, self.height() / 2)
        
        p.setBrush(Qt.white)
        p.setPen(QPen(QColor(0, 0, 0, 30), 1))
        thumb_rect = QRectF(self._thumb_pos, self._margin, self._thumb_radius * 2, self._thumb_radius * 2)
        p.drawEllipse(thumb_rect)
        p.end()

    def hitButton(self, pos):
        return self.rect().contains(pos)

class SettingsWindow(QDialog):
    preview_requested = pyqtSignal()
    
    _SS = """
    QDialog { background-color: #ffffff; }
    
    QTabWidget::pane { 
        border: 1px solid #e0e0e0; 
        border-radius: 8px; 
        background-color: #ffffff; 
        top: -1px; 
    }
    QTabBar::tab {
        background: #f5f5f5;
        border: 1px solid #e0e0e0;
        border-bottom: none;
        border-top-left-radius: 6px;
        border-top-right-radius: 6px;
        padding: 8px 24px;
        font-size: 13px;
        font-weight: 600;
        color: #555555;
        margin-right: 4px;
    }
    QTabBar::tab:hover { background: #eeeeee; }
    QTabBar::tab:selected {
        background: #ffffff;
        border-color: #e0e0e0;
        border-bottom: 2px solid #0078d4;
        color: #0078d4;
    }
    
    QLineEdit, QSpinBox, QComboBox, QKeySequenceEdit { 
        background: #fdfdfd; 
        border: 1px solid #cccccc; 
        border-radius: 5px; 
        padding: 5px 8px; 
        font-size: 13px; 
        color: #242424; 
    }
    QLineEdit:focus, QSpinBox:focus, QComboBox:focus { 
        border-color: #0078d4; 
        background: #ffffff; 
    }
    
    QSlider::groove:horizontal { background: #e0e0e0; height: 4px; border-radius: 2px; }
    QSlider::sub-page:horizontal { background: #0078d4; height: 4px; border-radius: 2px; }
    QSlider::handle:horizontal { background: #ffffff; border: 1.5px solid #0078d4; width: 14px; height: 14px; margin: -5px 0; border-radius: 8px; }
    """

    def __init__(self, config: Config, parent=None):
        super().__init__(parent)
        self.config = config
        
        self._backup_attrs = {
            "color": config.color,
            "bg_color": config.bg_color,
            "font": config.font,
            "font_size": config.font_size,
            "stage_font": config.stage_font,
            "stage_font_size": config.stage_font_size,
            "always_on_top": config.always_on_top,
            "prevent_offscreen": config.prevent_offscreen,
            "show_stage_label": config.show_stage_label,
            "auto_advance": config.auto_advance,
            "ppt_auto_start": config.ppt_auto_start,
            "double_click_toggle": config.double_click_toggle,
            "global_sound": config.global_sound,
            "countdown_10s_sound": config.countdown_10s_sound,
            "global_transparency": config.global_transparency,
            "bg_transparency": config.bg_transparency,
            "font_transparency": config.font_transparency,
            "shortcut_toggle": config.shortcut_toggle,
            "shortcut_reset": config.shortcut_reset,
            "shortcut_prev": config.shortcut_prev,
            "shortcut_next": config.shortcut_next,
            "ui_scale": config.ui_scale,
            "stages": copy.deepcopy(config.stages),
            "alerts": copy.deepcopy(config.alerts),
        }

        self.setWindowTitle(f"{APP_NAME} 首选项")
        self.resize(720, 560)  
        self.setStyleSheet(self._SS)
        self.setWindowFlags(self.windowFlags() & ~Qt.WindowContextHelpButtonHint)
        
        self._stage_rows = []
        self._alert_rows = []
        
        self._build_ui()
        self._populate()
        self._connect_live_preview_triggers()

    def _build_ui(self) -> None:
        root_lay = QVBoxLayout(self)
        root_lay.setContentsMargins(20, 20, 20, 16)
        root_lay.setSpacing(16)

        self.tabs = QTabWidget()
        self.tabs.addTab(self._build_tab_stages(), "⏱️ 流程配置")
        self.tabs.addTab(self._build_tab_alerts(), "🔔 预警设置")
        self.tabs.addTab(self._build_tab_appearance(), "🎨 视觉外观")
        self.tabs.addTab(self._build_tab_shortcuts(), "⌨️ 全局热键")
        root_lay.addWidget(self.tabs)

        bottom_bar = QWidget()
        btn_lay = QHBoxLayout(bottom_bar)
        btn_lay.setContentsMargins(0, 0, 0, 0)
        
        lbl_copyright = QLabel(f'<a href="https://github.com/Qwejay/QTimer" style="color: #8a8886; text-decoration: none;">Copyright © 2026 QwejayHuang. All rights reserved.</a>')
        lbl_copyright.setOpenExternalLinks(True)
        lbl_copyright.setToolTip("点击查看最新版本")
        lbl_copyright.setStyleSheet("font-size: 11px;")
        btn_lay.addWidget(lbl_copyright)
        
        btn_lay.addStretch()

        self.btn_restore = QPushButton("恢复默认")
        self.btn_restore.setCursor(Qt.PointingHandCursor)
        self.btn_restore.setFixedSize(88, 32)
        self.btn_restore.setStyleSheet("""
            QPushButton { background: #ffffff; color: #d13438; border: 1px solid #d13438; border-radius: 4px; font-size: 12px; font-weight: 600; }
            QPushButton:hover { background: #fde7e9; }
        """)
        self.btn_restore.clicked.connect(self._restore_defaults)
        btn_lay.addWidget(self.btn_restore)
        
        self.btn_cancel = QPushButton("取消")
        self.btn_cancel.setCursor(Qt.PointingHandCursor)
        self.btn_cancel.setFixedSize(80, 32)
        self.btn_cancel.setStyleSheet("""
            QPushButton { background: #ffffff; color: #323130; border: 1px solid #8a8886; border-radius: 4px; font-size: 12px; font-weight: 600; }
            QPushButton:hover { background: #f3f2f1; }
        """)
        self.btn_cancel.clicked.connect(self.reject)
        btn_lay.addWidget(self.btn_cancel)
        
        self.btn_save = QPushButton("确定")  
        self.btn_save.setCursor(Qt.PointingHandCursor)
        self.btn_save.setFixedSize(94, 32)
        self.btn_save.setStyleSheet("""
            QPushButton { background: #0078d4; color: white; border: none; border-radius: 4px; font-size: 12px; font-weight: 600; }
            QPushButton:hover { background: #106ebe; }
        """)
        self.btn_save.clicked.connect(self.accept)
        btn_lay.addWidget(self.btn_save)
        
        root_lay.addWidget(bottom_bar)

    def _make_state_btn(self, tooltip: str) -> ToggleSwitch:
        btn = ToggleSwitch()
        btn.setToolTip(tooltip)
        return btn

    def _build_tab_stages(self) -> QWidget:
        w = QWidget()
        lay = QVBoxLayout(w)
        lay.setContentsMargins(18, 18, 18, 18)
        lay.setSpacing(14)

        auto_group = QWidget()
        auto_lay = QGridLayout(auto_group)
        auto_lay.setContentsMargins(0, 0, 0, 0)
        auto_lay.setHorizontalSpacing(24)
        auto_lay.setVerticalSpacing(10)

        self.switch_show_label = self._make_state_btn("在主面板悬浮球中同步显示各小节文本标题")
        self.switch_auto_advance = self._make_state_btn("环节到期时自动切换下个任务并继续倒数")
        self.switch_ppt_auto_start = self._make_state_btn("当微软或WPS放映幻灯片时自动运行")
        self.switch_double_click = self._make_state_btn("双击悬浮窗空白区域快速进行开始/暂停切换")

        auto_lay.addWidget(QLabel("<b>显示环节名称</b>"), 0, 0)
        auto_lay.addWidget(self.switch_show_label, 0, 1, Qt.AlignRight)
        auto_lay.addWidget(QLabel("<b>自动进入下一个环节并计时</b>"), 1, 0)
        auto_lay.addWidget(self.switch_auto_advance, 1, 1, Qt.AlignRight)
        auto_lay.addWidget(QLabel("<b>PPT全屏放映时自动计时</b>"), 2, 0)
        auto_lay.addWidget(self.switch_ppt_auto_start, 2, 1, Qt.AlignRight)
        auto_lay.addWidget(QLabel("<b>双击悬浮窗便捷播放/暂停</b>"), 3, 0)
        auto_lay.addWidget(self.switch_double_click, 3, 1, Qt.AlignRight)
        
        lay.addWidget(auto_group)
        
        sep = QFrame()
        sep.setFrameShape(QFrame.HLine)
        sep.setStyleSheet("background-color: #e0e0e0; max-height: 1px;")
        lay.addWidget(sep)

        lbl_list = QLabel("<b>计时任务序列</b> (鼠标移动至对应项目可查看提示)")
        lbl_list.setStyleSheet("font-size: 13px; color: #333;")
        lay.addWidget(lbl_list)

        scroll = QScrollArea()
        scroll.setMinimumHeight(120)
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.NoFrame)
        scroll.setStyleSheet("background: transparent;")
        
        self._stage_container = QWidget()
        self._stage_vlay = QVBoxLayout(self._stage_container)
        self._stage_vlay.setContentsMargins(0, 0, 4, 0)
        self._stage_vlay.setSpacing(8)
        scroll.setWidget(self._stage_container)
        lay.addWidget(scroll)

        btn_add = QPushButton("＋ 添加一个计时阶段")
        btn_add.setFixedHeight(36)
        btn_add.setCursor(Qt.PointingHandCursor)
        btn_add.setStyleSheet("""
            QPushButton { background: #fdfdfd; color: #0078d4; border: 1px dashed #d1d1d1; border-radius: 4px; font-weight: 600; }
            QPushButton:hover { background: #f3f3f3; border-color: #0078d4; }
        """)
        btn_add.clicked.connect(lambda: self._add_stage_row())
        lay.addWidget(btn_add)
        return w

    def _build_tab_alerts(self) -> QWidget:
        w = QWidget()
        lay = QVBoxLayout(w)
        lay.setContentsMargins(18, 18, 18, 18)
        lay.setSpacing(14)

        auto_group = QWidget()
        auto_lay = QGridLayout(auto_group)
        auto_lay.setContentsMargins(0, 0, 0, 0)
        auto_lay.setHorizontalSpacing(24)
        auto_lay.setVerticalSpacing(10)

        self.switch_global_sound = self._make_state_btn("控制全局所有提示蜂鸣音频开关")
        self.switch_10s_sound = self._make_state_btn("在临近最后10秒时，每秒触发一次微弱滴答敲击声")

        auto_lay.addWidget(QLabel("<b>启用声音提示</b>"), 0, 0)
        auto_lay.addWidget(self.switch_global_sound, 0, 1, Qt.AlignRight)
        auto_lay.addWidget(QLabel("<b>倒计时最后 10 秒倒数提示音</b>"), 1, 0)
        auto_lay.addWidget(self.switch_10s_sound, 1, 1, Qt.AlignRight)
        
        lay.addWidget(auto_group)

        sep = QFrame()
        sep.setFrameShape(QFrame.HLine)
        sep.setStyleSheet("background-color: #e0e0e0; max-height: 1px;")
        lay.addWidget(sep)

        lbl_list = QLabel("<b>警报阈值节点列表</b>")
        lbl_list.setStyleSheet("font-size: 13px; color: #333;")
        lay.addWidget(lbl_list)

        scroll = QScrollArea()
        scroll.setMinimumHeight(120)
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.NoFrame)
        scroll.setStyleSheet("background: transparent;")
        
        self._alert_container = QWidget()
        self._alert_vlay = QVBoxLayout(self._alert_container)
        self._alert_vlay.setContentsMargins(0, 0, 4, 0)
        self._alert_vlay.setSpacing(8)
        scroll.setWidget(self._alert_container)
        lay.addWidget(scroll)

        btn_add = QPushButton("＋ 新增一个时间触发阈值")
        btn_add.setFixedHeight(36)
        btn_add.setCursor(Qt.PointingHandCursor)
        btn_add.setStyleSheet("""
            QPushButton { background: #fdfdfd; color: #0078d4; border: 1px dashed #d1d1d1; border-radius: 4px; font-weight: 600; }
            QPushButton:hover { background: #f3f3f3; border-color: #0078d4; }
        """)
        btn_add.clicked.connect(lambda: self._add_alert_row())
        lay.addWidget(btn_add)
        return w

    def _create_fast_font_combobox(self, default_font: str) -> QComboBox:
        cmb = QComboBox()
        cmb.setEditable(False)
        db = QFontDatabase()
        cmb.addItems(db.families())
        self._set_combobox_font(cmb, default_font)
        return cmb

    def _set_combobox_font(self, cmb: QComboBox, font_name: str) -> None:
        idx = cmb.findText(font_name)
        if idx >= 0:
            cmb.setCurrentIndex(idx)
        else:
            cmb.addItem(font_name)
            cmb.setCurrentIndex(cmb.count() - 1)

    def _build_tab_appearance(self) -> QWidget:
        w = QWidget()
        lay = QGridLayout(w)
        lay.setContentsMargins(24, 24, 24, 24)
        lay.setHorizontalSpacing(32)
        lay.setVerticalSpacing(16)
        
        self._color_preview = QPushButton("选择色彩")
        self._color_preview.setFixedSize(110, 28)
        self._color_preview.setCursor(Qt.PointingHandCursor)
        self._color_preview.clicked.connect(lambda: self._pick_color(self._color_preview, "_cur_color"))
        
        self._bg_color_preview = QPushButton("选择色彩")
        self._bg_color_preview.setFixedSize(110, 28)
        self._bg_color_preview.setCursor(Qt.PointingHandCursor)
        self._bg_color_preview.clicked.connect(lambda: self._pick_color(self._bg_color_preview, "_cur_bg_color"))

        self.lbl_global_trans = QLabel("<b>窗体全局透明度</b>")
        self.lbl_bg_trans = QLabel("<b>底色背景透明度</b>")
        self.lbl_font_trans = QLabel("<b>字体透明度</b>")

        self._op_slider = QSlider(Qt.Horizontal)
        self._op_slider.setRange(0, 70)  
        
        self._bg_op_slider = QSlider(Qt.Horizontal)
        self._bg_op_slider.setRange(0, 60)  

        self._font_trans_slider = QSlider(Qt.Horizontal)
        self._font_trans_slider.setRange(0, 100) 

        self._font_cmb = self._create_fast_font_combobox(self.config.font)
        self._size_slider = QSlider(Qt.Horizontal)
        self._size_slider.setRange(20, 60)

        self._stage_font_cmb = self._create_fast_font_combobox(self.config.stage_font)
        self._stage_size_slider = QSlider(Qt.Horizontal)
        self._stage_size_slider.setRange(12, 36)
        
        self._ui_scale_slider = QSlider(Qt.Horizontal)
        self._ui_scale_slider.setRange(50, 300)

        self.switch_always_on_top = self._make_state_btn("强行保持在所有应用层级的上方，避免放映遮掩")
        self.switch_prevent_offscreen = self._make_state_btn("拖拽过程中如果靠近边界自动吸附，且绝不出屏")

        lay.addWidget(QLabel("<b>文字与数字颜色</b>"), 0, 0)
        lay.addWidget(self._color_preview, 0, 1, Qt.AlignLeft)
        lay.addWidget(QLabel("<b>悬浮窗背景颜色</b>"), 1, 0)
        lay.addWidget(self._bg_color_preview, 1, 1, Qt.AlignLeft)
        
        lay.addWidget(self.lbl_global_trans, 2, 0)
        lay.addWidget(self._op_slider, 2, 1)
        lay.addWidget(self.lbl_bg_trans, 3, 0)
        lay.addWidget(self._bg_op_slider, 3, 1)
        lay.addWidget(self.lbl_font_trans, 4, 0)
        lay.addWidget(self._font_trans_slider, 4, 1)
        
        lay.addWidget(QLabel("<b>始终置于顶层</b>"), 5, 0)
        lay.addWidget(self.switch_always_on_top, 5, 1, Qt.AlignLeft)
        lay.addWidget(QLabel("<b>边缘自动磁吸</b>"), 6, 0)
        lay.addWidget(self.switch_prevent_offscreen, 6, 1, Qt.AlignLeft)

        lay.addWidget(QLabel("<b>计时数字字体</b>"), 0, 2)
        lay.addWidget(self._font_cmb, 0, 3)
        lay.addWidget(QLabel("<b>计时数字尺寸</b>"), 1, 2)
        lay.addWidget(self._size_slider, 1, 3)
        lay.addWidget(QLabel("<b>环节文本字体</b>"), 2, 2)
        lay.addWidget(self._stage_font_cmb, 2, 3)
        lay.addWidget(QLabel("<b>环节文本尺寸</b>"), 3, 2)
        lay.addWidget(self._stage_size_slider, 3, 3)
        lay.addWidget(QLabel("<b>全局缩放倍率</b>"), 4, 2)
        lay.addWidget(self._ui_scale_slider, 4, 3)
        
        tip_lbl = QLabel("💡 提示：按住键盘 Ctrl 并滚动鼠标滚轮可快速调整悬浮窗全局大小。")
        tip_lbl.setStyleSheet("color: #666; font-size: 11px;")
        lay.addWidget(tip_lbl, 7, 0, 1, 4)

        lay.setColumnStretch(1, 1)
        lay.setColumnStretch(3, 1)
        return w

    def _build_tab_shortcuts(self) -> QWidget:
        w = QWidget()
        lay = QVBoxLayout(w)
        lay.setContentsMargins(24, 24, 24, 24)
        lay.setSpacing(16)

        help_banner = QLabel("💡 <b>热键设定方式</b>：单击输入框后，在键盘上直接按下您要配置的任何组合键即可。")
        help_banner.setStyleSheet("color: #0078d4; background-color: #f3f9ff; border: 1px solid #d0e7ff; border-radius: 4px; padding: 10px 14px; font-size: 12px;")
        lay.addWidget(help_banner)

        card = QWidget()
        form = QFormLayout(card)
        form.setContentsMargins(0, 0, 0, 0)
        form.setSpacing(14)

        self.ks_toggle = QKeySequenceEdit()
        self.ks_reset = QKeySequenceEdit()
        self.ks_prev = QKeySequenceEdit()
        self.ks_next = QKeySequenceEdit()

        form.addRow("<b>播放 / 暂停 计时</b>", self.ks_toggle)
        form.addRow("<b>重置当前环节</b>", self.ks_reset)
        form.addRow("<b>切入上一小节</b>", self.ks_prev)
        form.addRow("<b>跃进下一小节</b>", self.ks_next)

        lay.addWidget(card)
        lay.addStretch()
        return w

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
            QWidget#stageRow { background: #fcfcfc; border: 1px solid #e2e2e2; border-radius: 6px; }
            QWidget#stageRow:hover { border-color: #0078d4; }
        """)
        h = QHBoxLayout(row_widget)
        h.setContentsMargins(10, 6, 10, 6)
        h.setSpacing(8)
        
        name = QLineEdit(str(label))
        name.setPlaceholderText("环节名称")
        name.setMaxLength(100)
        h.addWidget(name, 2)
        
        spin = QSpinBox()
        spin.setRange(1, 9999)
        spin.setValue(duration)
        spin.setFixedWidth(70)
        h.addWidget(spin)
        
        unit_cmb = QComboBox()
        unit_cmb.addItems(["分", "秒"])
        unit_cmb.setCurrentText(str(unit))
        unit_cmb.setFixedWidth(54)
        h.addWidget(unit_cmb)

        dir_cmb = QComboBox()
        dir_cmb.addItems(["倒计时", "正计时"])
        dir_cmb.setCurrentText("正计时" if count_up else "倒计时")
        dir_cmb.setFixedWidth(82)
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
            QWidget#alertRow { background: #fcfcfc; border: 1px solid #e2e2e2; border-radius: 6px; }
            QWidget#alertRow:hover { border-color: #0078d4; }
        """)
        h = QHBoxLayout(row_widget)
        h.setContentsMargins(10, 6, 10, 6)
        h.setSpacing(8)
        
        lbl = QLabel("剩余秒数：")
        lbl.setStyleSheet("color: #666; font-size: 12px;")
        h.addWidget(lbl)
        
        spin = QSpinBox()
        spin.setRange(1, 9999)
        spin.setSuffix(" 秒")
        spin.setValue(seconds)
        spin.setFixedWidth(85)
        h.addWidget(spin)
        
        cbtn = QPushButton()
        cbtn.setFixedSize(38, 24)
        cbtn.setCursor(Qt.PointingHandCursor)
        self._set_color_preview(cbtn, color)
        
        chk_sound = QCheckBox("伴随提示音")
        chk_sound.setStyleSheet("QCheckBox { font-size:12px; }")
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
        layout.addSpacing(4)
        
        btn_up = QPushButton()
        btn_up.setFixedSize(24, 24)
        btn_up.setCursor(Qt.PointingHandCursor)
        btn_up.setIcon(get_svg_icon("up", 14, "#555555"))
        btn_up.setStyleSheet("QPushButton { background:transparent; border:none; border-radius:3px; } QPushButton:hover { background:#eaeaea; }")
        btn_up.clicked.connect(partial(self._move_row, rows, row, -1, rebuild_fn))
        layout.addWidget(btn_up)

        btn_down = QPushButton()
        btn_down.setFixedSize(24, 24)
        btn_down.setCursor(Qt.PointingHandCursor)
        btn_down.setIcon(get_svg_icon("down", 14, "#555555"))
        btn_down.setStyleSheet("QPushButton { background:transparent; border:none; border-radius:3px; } QPushButton:hover { background:#eaeaea; }")
        btn_down.clicked.connect(partial(self._move_row, rows, row, 1, rebuild_fn))
        layout.addWidget(btn_down)
            
        btn_del = QPushButton()
        btn_del.setFixedSize(24, 24)
        btn_del.setCursor(Qt.PointingHandCursor)
        btn_del.setIcon(get_svg_icon("trash", 14, "#d13438"))
        btn_del.setStyleSheet("QPushButton { background:transparent; border:none; border-radius:3px; } QPushButton:hover { background:#fde7e9; }")
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
        widget.setStyleSheet(f"""
            background: {color}; 
            border: 1px solid #ababab; 
            border-radius: 4px;
            color: {color};
        """)

    def _restore_defaults(self) -> None:
        reply = QMessageBox.question(
            self, 
            "确认重置", 
            "是否确认恢复默认配置？您原先的所有修改将被重置。",
            QMessageBox.Yes | QMessageBox.No
        )
        if reply == QMessageBox.Yes:
            self.config = Config()
            for row in list(self._stage_rows):
                if row.get("widget"): row["widget"].deleteLater()
            self._stage_rows.clear()
            for row in list(self._alert_rows):
                if row.get("widget"): row["widget"].deleteLater()
            self._alert_rows.clear()

            self._populate()
            self._trigger_live_preview()
            QMessageBox.information(self, "重置成功", "已加载出厂默认方案。点击“确定”后方可正式保存写入。")

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
                    self, 
                    "快捷键冲突", 
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

class App(QObject):
    def __init__(self):
        super().__init__()
        self.config = Config()
        self.config.load()

        self.float_bar = FloatBar()
        self.controller = TimerController(self.config)
        self._shortcuts = []

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

        screen = self.float_bar.screen().availableGeometry()
        self.float_bar.move(screen.left() + 40, screen.top() + 40)
        self.float_bar.show()

    def _check_ppt_status(self) -> None:
        if not self.config.ppt_auto_start:
            return

        is_active = is_ppt_slideshow_active()

        if is_active:
            self._ppt_stable_active_count += 1
            if self._ppt_stable_active_count >= 3 and not self._ppt_was_active:
                self._ppt_was_active = True
                self._current_ppt_session_paused_by_user = False
                if self.controller.paused and self.controller._remaining_float > 0:
                    self.controller.toggle_pause()
            elif self._ppt_stable_active_count >= 3:
                if self.controller.paused and self.controller._remaining_float > 0:
                    if not self._current_ppt_session_paused_by_user:
                        self.controller.toggle_pause()
        else:
            self._ppt_stable_active_count = 0
            if self._ppt_was_active:
                self._ppt_was_active = False
                self._current_ppt_session_paused_by_user = False
                # 退出放映时仅暂停，坚决不重置进度
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

        ctrl.tick.connect(lambda lbl, rem: fb.update_display(lbl, rem))
        ctrl.alert_triggered.connect(lambda c: fb.start_flash(c, 3000))
        ctrl.loop_restarted.connect(lambda: fb.start_flash(self.config.color, 1500))
        ctrl.state_changed.connect(fb.set_running)

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

        mapping = [
            (self.config.shortcut_toggle, self.controller.toggle_pause),
            (self.config.shortcut_reset, self.controller.restart_stage),
            (self.config.shortcut_prev, self.controller.prev_stage),
            (self.config.shortcut_next, self.controller.next_stage),
        ]
        for key_str, slot_func in mapping:
            if key_str:
                sc = QShortcut(QKeySequence(key_str), self.float_bar)
                sc.setContext(Qt.ApplicationShortcut)
                sc.activated.connect(slot_func)
                self._shortcuts.append(sc)

    def _open_settings(self) -> None:
        dlg = SettingsWindow(self.config)
        dlg.preview_requested.connect(self._apply_style)
        
        res = dlg.exec_()
        if res == QDialog.Rejected:
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
    if hasattr(Qt, 'AA_EnableHighDpiScaling'):
        QApplication.setAttribute(Qt.AA_EnableHighDpiScaling, True)
    if hasattr(Qt, 'AA_UseHighDpiPixmaps'):
        QApplication.setAttribute(Qt.AA_UseHighDpiPixmaps, True)

    app = QApplication(sys.argv)
    app.setStyle("Fusion")
    app.setApplicationName(APP_NAME)
    app.setQuitOnLastWindowClosed(False)

    translator = QTranslator()
    locale = QLocale.system().name()  
    if translator.load(f"qt_{locale}", QLibraryInfo.location(QLibraryInfo.TranslationsPath)):
        app.installTranslator(translator)

    shared_mem_key = f"{APP_NAME}_SingleInstance_MemoryLock"
    shared_mem = QSharedMemory(shared_mem_key)

    if shared_mem.attach():
        sys.exit(0)
    else:
        shared_mem.create(1)

    main = App()
    exit_code = app.exec_()
    if shared_mem.isAttached():
        shared_mem.detach()
    sys.exit(exit_code)
