import sys
import json
import os
import platform
import threading
import subprocess
import time
import math
import ctypes
from dataclasses import dataclass, asdict
from functools import partial
from typing import Dict, List, Optional

from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
from PyQt5.QtGui import *
from PyQt5.QtSvg import QSvgRenderer

APP_NAME = "QTimer"
APP_VERSION = "Final Release V1.2.1"

def get_app_dir() -> str:
    if getattr(sys, 'frozen', False):
        return os.path.dirname(sys.executable)
    return os.path.dirname(os.path.abspath(__file__))

def get_config_path() -> str:
    local_path = os.path.join(get_app_dir(), f".{APP_NAME.lower()}_config.json")
    try:
        with open(local_path, 'a', encoding="utf-8"):
            pass
        return local_path
    except PermissionError:
        return os.path.join(os.path.expanduser("~"), f".{APP_NAME.lower()}_config.json")

CONFIG_PATH = get_config_path()


def is_ppt_slideshow_active() -> bool:
    if platform.system() != "Windows":
        return False
    try:
        hwnd = ctypes.windll.user32.GetForegroundWindow()
        if not hwnd:
            return False
        buf = ctypes.create_unicode_buffer(256)
        ctypes.windll.user32.GetClassNameW(hwnd, buf, 256)
        cls_name = buf.value.lower()
        return "screenclass" in cls_name or "wpp_screen" in cls_name or "wpp_slide_show" in cls_name
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


SVG_ICONS: Dict[str, str] = {
    "play":     '<svg viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg"><polygon points="6,4 20,12 6,20" fill="{color}"/></svg>',
    "pause":    '<svg viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg"><rect x="5" y="4" width="4" height="16" rx="1" fill="{color}"/><rect x="15" y="4" width="4" height="16" rx="1" fill="{color}"/></svg>',
    "restart":  '<svg viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg"><path d="M12 5V1L7 6l5 5V7c3.31 0 6 2.69 6 6s-2.69 6-6 6-6-2.69-6-6H4c0 4.42 3.58 8 8 8s8-3.58 8-8-3.58-8-8-8z" fill="{color}"/></svg>',
    "prev":     '<svg viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg"><polygon points="19,4 7,12 19,20" fill="{color}"/><rect x="3" y="4" width="3" height="16" rx="1" fill="{color}"/></svg>',
    "next":     '<svg viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg"><polygon points="5,4 17,12 5,20" fill="{color}"/><rect x="18" y="4" width="3" height="16" rx="1" fill="{color}"/></svg>',
    "settings": '<svg viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg"><path d="M19.14 12.94c.04-.3.06-.61.06-.94s-.02-.64-.07-.94l2.03-1.58c.18-.14.23-.41.12-.61l-1.92-3.32c-.12-.22-.37-.29-.59-.22l-2.39.96c-.5-.38-1.03-.7-1.62-.94l-.36-2.54c-.04-.24-.24-.41-.48-.41h-3.84c-.24 0-.43.17-.47.41l-.36 2.54c-.59.24-1.13.57-1.62.94l-2.39-.96c-.22-.08-.47 0-.59.22L2.74 8.87c-.12.21-.08.47.12.61l2.03 1.58c-.05.3-.09.63-.09.94s.02.64.07.94l-2.03 1.58c-.18.14-.23.41-.12.61l1.92 3.32c.12.22.37.29.59.22l2.39-.96c.5.38 1.03.7 1.62.94l.36 2.54c.05.24.24.41.48.41h3.84c.24 0 .44-.17.47-.41l.36-2.54c.59-.24 1.13-.56 1.62-.94l2.39.96c.22.08.47 0 .59-.22l1.92-3.32c.12-.22.07-.47-.12-.61l-2.01-1.58zM12 15.6c-1.98 0-3.6-1.62-3.6-3.6s1.62-3.6 3.6-3.6 3.6 1.62 3.6 3.6-1.62 3.6-3.6 3.6z" fill="{color}"/></svg>',
    "close":    '<svg viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg"><line x1="4" y1="4" x2="20" y2="20" stroke="{color}" stroke-width="2.5" stroke-linecap="round"/><line x1="20" y1="4" x2="4" y2="20" stroke="{color}" stroke-width="2.5" stroke-linecap="round"/></svg>',
}

_ICON_CACHE: Dict[str, QIcon] = {}

def get_svg_icon(name: str, size: int, color: str = "white") -> QIcon:
    cache_key = f"{name}_{size}_{color}"
    if cache_key in _ICON_CACHE:
        return _ICON_CACHE[cache_key]
        
    svg_str = SVG_ICONS.get(name, "").replace("{color}", color)
    renderer = QSvgRenderer(svg_str.encode("utf-8"))
    
    pixmap = QPixmap(size, size)
    pixmap.fill(Qt.transparent)
    painter = QPainter(pixmap)
    painter.setRenderHints(QPainter.Antialiasing | QPainter.SmoothPixmapTransform)
    renderer.render(painter)
    painter.end()
    
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

        self.stages: List[Stage] = [Stage("说课时间", 5, "分", False), Stage("答辩时间", 2, "分", False)]
        self.alerts: List[Alert] = [Alert(30, "#ffaa00", True), Alert(10, "#ff4444", True)]
        
        self.color: str = "#ffffff"
        self.font: str = "微软雅黑"
        self.font_size: int = 32
        self.stage_font: str = "微软雅黑"
        self.stage_font_size: int = 18
        self.opacity: float = 0.95
        self.bg_color: str = "#141414"
        self.bg_opacity: int = 82

        self.shortcut_toggle: str = "Ctrl+Space"
        self.shortcut_reset: str = "Ctrl+Return"
        self.shortcut_prev: str = "Ctrl+Left"
        self.shortcut_next: str = "Ctrl+Right"

    def save(self) -> None:
        data = {
            "auto_advance": self.auto_advance,
            "global_sound": self.global_sound,
            "countdown_10s_sound": self.countdown_10s_sound,
            "always_on_top": self.always_on_top,
            "prevent_offscreen": self.prevent_offscreen,
            "show_stage_label": self.show_stage_label,
            "ppt_auto_start": self.ppt_auto_start,
            "stages": [asdict(s) for s in self.stages],
            "alerts": [asdict(a) for a in self.alerts],
            "color": self.color,
            "font": self.font,
            "font_size": self.font_size,
            "stage_font": self.stage_font,
            "stage_font_size": self.stage_font_size,
            "opacity": self.opacity,
            "bg_color": self.bg_color,
            "bg_opacity": self.bg_opacity,
            "shortcut_toggle": self.shortcut_toggle,
            "shortcut_reset": self.shortcut_reset,
            "shortcut_prev": self.shortcut_prev,
            "shortcut_next": self.shortcut_next,
        }
        try:
            tmp_path = CONFIG_PATH + ".tmp"
            with open(tmp_path, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            os.replace(tmp_path, CONFIG_PATH)
        except Exception as e:
            print(f"配置保存异常: {e}")

    def load(self) -> None:
        if not os.path.exists(CONFIG_PATH):
            return
        try:
            with open(CONFIG_PATH, "r", encoding="utf-8") as f:
                d = json.load(f)
            for key in ("auto_advance", "global_sound", "countdown_10s_sound", "always_on_top",
                        "prevent_offscreen", "show_stage_label", "ppt_auto_start", "color", "font",
                        "font_size", "stage_font", "stage_font_size", "opacity", "bg_color",
                        "bg_opacity", "shortcut_toggle", "shortcut_reset", "shortcut_prev", "shortcut_next"):
                if key in d:
                    setattr(self, key, d[key])

            if "stages" in d:
                self.stages = [Stage.from_dict(s) for s in d["stages"]]
            if "alerts" in d:
                self.alerts = [Alert.from_dict(a) for a in d["alerts"]]
        except Exception as e:
            print(f"配置加载异常: {e}")

    def bg_qcolor(self) -> QColor:
        c = QColor(self.bg_color)
        c.setAlpha(int(self.bg_opacity / 100 * 255))
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

    ICON_SIZE = 34

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
        self._layout.addSpacing(18)

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
        b.setFixedSize(self.ICON_SIZE, self.ICON_SIZE)
        b.setToolTip(tip)
        b.setCursor(Qt.PointingHandCursor)
        b.setIcon(get_svg_icon(icon_name, self.ICON_SIZE - 8))
        b.setIconSize(QSize(self.ICON_SIZE - 8, self.ICON_SIZE - 8))
        b.setStyleSheet("""
            QPushButton { background: rgba(255,255,255,15); border: none; border-radius: 7px; }
            QPushButton:hover { background: rgba(255,255,255,40); }
        """)
        return b

    def apply_style(self, color: str, font: str, size: int, stage_font: str, stage_size: int,
                    opacity: float, bg_color: QColor, always_on_top: bool,
                    show_stage_label: bool, prevent_offscreen: bool) -> None:
        self._text_color = color
        self._font_family = font
        self._font_size = size
        self._stage_font_family = stage_font
        self._stage_font_size = stage_size
        self._bg_color = bg_color
        self._show_stage_label = show_stage_label
        self._prevent_offscreen = prevent_offscreen
        self.setWindowOpacity(opacity)
        
        flags = self.windowFlags()
        if always_on_top:
            flags |= Qt.WindowStaysOnTopHint
        else:
            flags &= ~Qt.WindowStaysOnTopHint
        if flags != self.windowFlags():
            was_visible = self.isVisible()
            self.setWindowFlags(flags)
            if was_visible:
                self.show()

        self._refresh_labels()
        self._update_size()
        self.update()

    def _refresh_labels(self, stage_color: Optional[str] = None, time_color: Optional[str] = None) -> None:
        sc = stage_color or self._text_color
        tc = time_color or self._text_color
        self.lbl_stage.setStyleSheet(
            f"color:{sc}; font-family:'{self._stage_font_family}'; "
            f"font-size:{self._stage_font_size}px; font-weight:600; background:transparent;")
        self.lbl_time.setStyleSheet(
            f"color:{tc}; font-family:'{self._font_family}'; "
            f"font-size:{self._font_size}px; font-weight:900; background:transparent;")
        self.lbl_stage.style().polish(self.lbl_stage)
        self.lbl_time.style().polish(self.lbl_time)

    def _update_size(self) -> None:
        fm_stage = self.lbl_stage.fontMetrics()
        fm_time = self.lbl_time.fontMetrics()
        text = self._current_stage_text or "环节名称"
        
        time_w = fm_time.horizontalAdvance("88:88") + 20
        self.lbl_time.setFixedWidth(time_w)

        btn_w = (self.ICON_SIZE + 2) * 6
        self._btn_container.setFixedWidth(btn_w)

        if self._show_stage_label:
            self.lbl_stage.show()
            self._spacing_item.changeSize(12, 0, QSizePolicy.Fixed, QSizePolicy.Fixed)
            stage_w = fm_stage.horizontalAdvance(text) + 20
            self.lbl_stage.setText(text)
            self.lbl_stage.setFixedWidth(stage_w)
            self._text_width = 18 + stage_w + 12 + time_w + 18
        else:
            self.lbl_stage.hide()
            self._spacing_item.changeSize(0, 0, QSizePolicy.Fixed, QSizePolicy.Fixed)
            self.lbl_stage.setFixedWidth(0)
            self._text_width = 18 + time_w + 18

        self._layout.invalidate()
        self._full_width = self._text_width + btn_w + 16

        h = max(self._font_size + 24, 50)
        self._canvas.setFixedSize(self._full_width, h)
        self.setFixedHeight(h)

        if self.underMouse():
            self.setFixedWidth(self._full_width)
            self._btn_opacity.setOpacity(1.0)
        else:
            self.setFixedWidth(self._text_width)
            self._btn_opacity.setOpacity(0.0)

    def update_display(self, stage: str, display_sec: int) -> None:
        mm, ss = divmod(display_sec, 60)
        if self._current_stage_text != stage:
            self._current_stage_text = stage
            self._update_size()
        self.lbl_time.setText(f"{mm:02d}:{ss:02d}")

    def set_running(self, running: bool) -> None:
        self.btn_toggle.setIcon(get_svg_icon("pause" if running else "play", self.ICON_SIZE - 8))

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
        self._anim_group.stop()
        self._width_anim.setStartValue(self.width())
        self._width_anim.setEndValue(self._full_width)
        self._btn_anim.setStartValue(self._btn_opacity.opacity())
        self._btn_anim.setEndValue(1.0)
        self._anim_group.start()
        super().enterEvent(e)

    def leaveEvent(self, e) -> None:
        self._anim_group.stop()
        self._width_anim.setStartValue(self.width())
        self._width_anim.setEndValue(self._text_width)
        self._btn_anim.setStartValue(self._btn_opacity.opacity())
        self._btn_anim.setEndValue(0.0)
        self._anim_group.start()
        super().leaveEvent(e)

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

    def paintEvent(self, e) -> None:
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing)
        p.setBrush(self._bg_color)
        p.setPen(Qt.NoPen)
        p.drawRoundedRect(self.rect(), 12, 12)

    def mousePressEvent(self, e: QMouseEvent) -> None:
        if e.button() == Qt.LeftButton:
            self._drag_pos = e.globalPos() - self.pos()

    def mouseMoveEvent(self, e: QMouseEvent) -> None:
        if self._drag_pos and e.buttons() == Qt.LeftButton:
            new_pos = e.globalPos() - self._drag_pos
            if self._prevent_offscreen:
                screen = QApplication.desktop().availableGeometry(self)
                new_x = max(screen.left(), min(new_pos.x(), screen.right() - self.width()))
                new_y = max(screen.top(), min(new_pos.y(), screen.bottom() - self.height()))
                new_pos = QPoint(new_x, new_y)
            self.move(new_pos)

    def mouseReleaseEvent(self, e: QMouseEvent) -> None:
        self._drag_pos = None


class SettingsWindow(QDialog):
    """现代化高级风格设置界面"""
    _SS = """
    QDialog { background: #ffffff; }
    QWidget { font-family: "Segoe UI", "Microsoft YaHei", sans-serif; }
    QLabel { color: #202124; font-size: 14px; background: transparent; }
    QCheckBox { color: #3c4043; font-size: 14px; spacing: 10px; }
    QListWidget { background: transparent; border: none; outline: none; padding: 12px 8px; }
    QListWidget::item { height: 44px; padding-left: 16px; color: #4a4a4a; font-size: 15px; border-radius: 6px; margin-bottom: 4px; }
    QListWidget::item:hover { background: #ebecef; }
    QListWidget::item:selected { background: #e8f0fe; color: #1a73e8; font-weight: bold; }
    QGroupBox { font-weight: bold; border: 1px solid #e8eaed; border-radius: 8px; margin-top: 24px; padding-top: 16px; font-size: 14px; }
    QGroupBox::title { subcontrol-origin: margin; subcontrol-position: top left; left: 16px; top: 8px; color: #1a73e8; }
    QLineEdit, QSpinBox, QComboBox, QFontComboBox, QKeySequenceEdit { background: #f8f9fa; border: 1px solid #dadce0; border-radius: 6px; padding: 6px 12px; font-size: 14px; color: #202124; min-height: 22px; }
    QLineEdit:focus, QSpinBox:focus, QComboBox:focus, QFontComboBox:focus, QKeySequenceEdit:focus { border: 2px solid #1a73e8; padding: 5px 11px; background: #ffffff; }
    QSlider::groove:horizontal { background: #e8eaed; height: 6px; border-radius: 3px; }
    QSlider::sub-page:horizontal { background: #1a73e8; height: 6px; border-radius: 3px; }
    QSlider::handle:horizontal { background: white; border: 2px solid #1a73e8; width: 16px; height: 16px; margin: -6px 0; border-radius: 10px; }
    QScrollBar:vertical { border: none; background: transparent; width: 8px; }
    QScrollBar::handle:vertical { background: #dadce0; border-radius: 4px; min-height: 24px; }
    QFormLayout QLabel { background: transparent; }
    """

    def __init__(self, config: Config, parent=None):
        super().__init__(parent)
        self.config = config
        self.setWindowTitle(f"{APP_NAME} 设置")
        self.resize(920, 680)
        self.setStyleSheet(self._SS)
        self.setWindowFlags(self.windowFlags() & ~Qt.WindowContextHelpButtonHint)
        
        self._stage_rows = []
        self._alert_rows = []
        
        self._build_ui()
        self._populate()

    def _build_ui(self) -> None:
        root_lay = QVBoxLayout(self)
        root_lay.setContentsMargins(0, 0, 0, 0)
        root_lay.setSpacing(0)

        main_widget = QWidget()
        main_lay = QHBoxLayout(main_widget)
        main_lay.setContentsMargins(0, 0, 0, 0)
        main_lay.setSpacing(0)

        left_panel = QWidget()
        left_panel.setFixedWidth(220)
        left_panel.setStyleSheet("background: #f4f5f7; border-right: 1px solid #e8eaed;")
        left_lay = QVBoxLayout(left_panel)
        left_lay.setContentsMargins(0, 16, 0, 0)

        self.nav_list = QListWidget()
        self.nav_list.addItems(["流程配置", "提醒设置", "外观设置", "全局快捷键"])
        self.nav_list.setCurrentRow(0)
        left_lay.addWidget(self.nav_list)
        main_lay.addWidget(left_panel)

        self.stack = QStackedWidget()
        self.stack.setStyleSheet("background: #ffffff;")
        self.stack.addWidget(self._build_page_stages())
        self.stack.addWidget(self._build_page_alerts())
        self.stack.addWidget(self._build_page_appearance())
        self.stack.addWidget(self._build_page_shortcuts())
        main_lay.addWidget(self.stack)

        root_lay.addWidget(main_widget)
        self.nav_list.currentRowChanged.connect(self.stack.setCurrentIndex)

        bottom_bar = QWidget()
        bottom_bar.setStyleSheet("background: #ffffff; border-top: 1px solid #e8eaed;")
        btn_lay = QHBoxLayout(bottom_bar)
        btn_lay.setContentsMargins(32, 16, 32, 16)
        
        self.btn_cancel = QPushButton("取消")
        self.btn_cancel.setCursor(Qt.PointingHandCursor)
        self.btn_cancel.setFixedSize(100, 40)
        self.btn_cancel.setStyleSheet("""
            QPushButton { background: #ffffff; color: #5f6368; border: 1px solid #dadce0; border-radius: 6px; font-size: 14px; font-weight: bold; }
            QPushButton:hover { background: #f8f9fa; color: #202124; }
        """)
        self.btn_cancel.clicked.connect(self.reject)
        
        self.btn_save = QPushButton("保存设置")
        self.btn_save.setCursor(Qt.PointingHandCursor)
        self.btn_save.setFixedSize(120, 40)
        self.btn_save.setStyleSheet("""
            QPushButton { background: #1a73e8; color: white; border: none; border-radius: 6px; font-size: 14px; font-weight: bold; }
            QPushButton:hover { background: #1557b0; }
        """)
        
        btn_lay.addStretch()
        btn_lay.addWidget(self.btn_cancel)
        btn_lay.addSpacing(16)
        btn_lay.addWidget(self.btn_save)
        root_lay.addWidget(bottom_bar)

    def _create_page_wrap(self, title: str, desc: str) -> tuple:
        w = QWidget()
        lay = QVBoxLayout(w)
        lay.setContentsMargins(40, 32, 40, 32)
        lay.setSpacing(20)
        
        lbl_title = QLabel(title)
        lbl_title.setStyleSheet("font-size: 26px; font-weight: bold; color: #202124;")
        lbl_desc = QLabel(desc)
        lbl_desc.setStyleSheet("color: #5f6368; font-size: 14px;")
        lay.addWidget(lbl_title)
        lay.addWidget(lbl_desc)
        
        line = QFrame()
        line.setFrameShape(QFrame.HLine)
        line.setStyleSheet("background-color: #e8eaed; max-height: 1px;")
        lay.addWidget(line)
        return w, lay

    def _build_page_stages(self) -> QWidget:
        w, lay = self._create_page_wrap("流程配置", "管理演讲、说课或答辩的各环节与计时逻辑")
        opts = QHBoxLayout()
        self.chk_show_label = QCheckBox("在悬浮窗显示环节名称")
        self.chk_auto_advance = QCheckBox("倒计时结束自动进入下一环节")
        opts.addWidget(self.chk_show_label)
        opts.addWidget(self.chk_auto_advance)
        opts.addStretch()
        lay.addLayout(opts)
        self.chk_ppt_auto_start = QCheckBox("检测到 PPT 幻灯片放映时自动开始计时")
        lay.addWidget(self.chk_ppt_auto_start)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.NoFrame)
        content = QWidget()
        self._stage_vlay = QVBoxLayout(content)
        self._stage_vlay.setContentsMargins(0, 0, 8, 0)
        self._stage_vlay.setSpacing(8)
        scroll.setWidget(content)
        lay.addWidget(scroll)

        btn_add = QPushButton("＋ 添加环节")
        btn_add.setFixedHeight(44)
        btn_add.setStyleSheet("""
            QPushButton { background: #ffffff; color: #1a73e8; border: 2px dashed #dadce0; border-radius: 8px; font-size: 15px; font-weight: bold; }
            QPushButton:hover { background: #f8f9fa; border-color: #1a73e8; }
        """)
        btn_add.clicked.connect(self._add_stage_row)
        lay.addWidget(btn_add)
        return w

    def _build_page_alerts(self) -> QWidget:
        w, lay = self._create_page_wrap("提醒设置", "到达特定剩余时间时，触发高亮与声音提醒")
        opts = QHBoxLayout()
        self.chk_global_sound = QCheckBox("允许播放所有提示音")
        self.chk_10s_sound = QCheckBox("最后 10 秒倒数提示音")
        opts.addWidget(self.chk_global_sound)
        opts.addWidget(self.chk_10s_sound)
        opts.addStretch()
        lay.addLayout(opts)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.NoFrame)
        content = QWidget()
        self._alert_vlay = QVBoxLayout(content)
        self._alert_vlay.setContentsMargins(0, 0, 8, 0)
        self._alert_vlay.setSpacing(8)
        scroll.setWidget(content)
        lay.addWidget(scroll)

        btn_add = QPushButton("＋ 添加提醒节点")
        btn_add.setFixedHeight(44)
        btn_add.setStyleSheet("""
            QPushButton { background: #ffffff; color: #1a73e8; border: 2px dashed #dadce0; border-radius: 8px; font-size: 15px; font-weight: bold; }
            QPushButton:hover { background: #f8f9fa; border-color: #1a73e8; }
        """)
        btn_add.clicked.connect(self._add_alert_row)
        lay.addWidget(btn_add)
        return w

    def _build_page_appearance(self) -> QWidget:
        w, lay = self._create_page_wrap("外观设置", "自定义悬浮窗的视觉风格与窗口行为")

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.NoFrame)
        content = QWidget()
        c_lay = QVBoxLayout(content)
        c_lay.setContentsMargins(0, 0, 8, 0)
        c_lay.setSpacing(20)

        color_group = QGroupBox("颜色风格")
        color_lay = QGridLayout(color_group)
        color_lay.setContentsMargins(20, 20, 20, 20)
        color_lay.setSpacing(16)
        self._color_preview = QPushButton()
        self._color_preview.setFixedSize(70, 32)
        self._color_preview.setCursor(Qt.PointingHandCursor)
        self._color_preview.clicked.connect(lambda: self._pick_color(self._color_preview, "_cur_color"))
        self._bg_color_preview = QPushButton()
        self._bg_color_preview.setFixedSize(70, 32)
        self._bg_color_preview.setCursor(Qt.PointingHandCursor)
        self._bg_color_preview.clicked.connect(lambda: self._pick_color(self._bg_color_preview, "_cur_bg_color"))
        color_lay.addWidget(QLabel("文本颜色："), 0, 0)
        color_lay.addWidget(self._color_preview, 0, 1)
        color_lay.addWidget(QLabel("背景颜色："), 1, 0)
        color_lay.addWidget(self._bg_color_preview, 1, 1)
        c_lay.addWidget(color_group)

        op_group = QGroupBox("透明度")
        op_lay = QFormLayout(op_group)
        op_lay.setContentsMargins(20, 20, 20, 20)
        self._op_slider = QSlider(Qt.Horizontal)
        self._op_slider.setRange(30, 100)
        self._bg_op_slider = QSlider(Qt.Horizontal)
        self._bg_op_slider.setRange(40, 100)
        op_lay.addRow("整体透明度：", self._op_slider)
        op_lay.addRow("背景透明度：", self._bg_op_slider)
        c_lay.addWidget(op_group)

        font_group = QGroupBox("排版设置")
        f_lay = QFormLayout(font_group)
        f_lay.setContentsMargins(20, 20, 20, 20)
        self._font_cmb = QFontComboBox()
        self._size_slider = QSlider(Qt.Horizontal)
        self._size_slider.setRange(20, 60)
        self._stage_font_cmb = QFontComboBox()
        self._stage_size_slider = QSlider(Qt.Horizontal)
        self._stage_size_slider.setRange(12, 36)
        f_lay.addRow("时间字体：", self._font_cmb)
        f_lay.addRow("时间字号：", self._size_slider)
        f_lay.addRow("环节字体：", self._stage_font_cmb)
        f_lay.addRow("环节字号：", self._stage_size_slider)
        c_lay.addWidget(font_group)

        behavior = QGroupBox("窗口行为")
        b_lay = QVBoxLayout(behavior)
        b_lay.setContentsMargins(20, 20, 20, 20)
        self.chk_always_on_top = QCheckBox("始终置顶显示")
        self.chk_prevent_offscreen = QCheckBox("防止意外移出屏幕边界")
        b_lay.addWidget(self.chk_always_on_top)
        b_lay.addWidget(self.chk_prevent_offscreen)
        c_lay.addWidget(behavior)

        c_lay.addStretch()
        scroll.setWidget(content)
        lay.addWidget(scroll)
        return w

    def _build_page_shortcuts(self) -> QWidget:
        w, lay = self._create_page_wrap("全局快捷键", "设置便于盲操的快捷方式（悬浮窗需获得焦点）")
        container = QWidget()
        container.setStyleSheet("background: #f8f9fa; border: 1px solid #e8eaed; border-radius: 8px;")
        c_lay = QVBoxLayout(container)
        c_lay.setContentsMargins(32, 32, 32, 32)
        form = QFormLayout()
        form.setSpacing(24)
        self.ks_toggle = QKeySequenceEdit()
        self.ks_reset = QKeySequenceEdit()
        self.ks_prev = QKeySequenceEdit()
        self.ks_next = QKeySequenceEdit()
        form.addRow("播放 / 暂停：", self.ks_toggle)
        form.addRow("重置当前环节：", self.ks_reset)
        form.addRow("上一环节：", self.ks_prev)
        form.addRow("下一环节：", self.ks_next)
        c_lay.addLayout(form)
        lay.addWidget(container)
        lay.addStretch()
        return w

    def _populate(self) -> None:
        self.chk_auto_advance.setChecked(self.config.auto_advance)
        self.chk_show_label.setChecked(self.config.show_stage_label)
        self.chk_ppt_auto_start.setChecked(self.config.ppt_auto_start)
        
        for s in self.config.stages:
            self._add_stage_row(s.label, s.duration, s.unit, s.count_up)
        if not self.config.stages:
            self._add_stage_row()
        
        self.chk_global_sound.setChecked(self.config.global_sound)
        self.chk_10s_sound.setChecked(self.config.countdown_10s_sound)
        for a in self.config.alerts:
            self._add_alert_row(a.seconds, a.color, a.play_sound)
        
        self.chk_always_on_top.setChecked(self.config.always_on_top)
        self.chk_prevent_offscreen.setChecked(self.config.prevent_offscreen)

        self._cur_color = self.config.color
        self._set_color_preview(self._color_preview, self._cur_color)
        self._cur_bg_color = self.config.bg_color
        self._set_color_preview(self._bg_color_preview, self._cur_bg_color)
        self._bg_op_slider.setValue(self.config.bg_opacity)
        
        self._font_cmb.setCurrentFont(QFont(self.config.font))
        self._size_slider.setValue(self.config.font_size)
        
        self._stage_font_cmb.setCurrentFont(QFont(self.config.stage_font))
        self._stage_size_slider.setValue(self.config.stage_font_size)
        
        self._op_slider.setValue(int(self.config.opacity * 100))

        self.ks_toggle.setKeySequence(QKeySequence(self.config.shortcut_toggle))
        self.ks_reset.setKeySequence(QKeySequence(self.config.shortcut_reset))
        self.ks_prev.setKeySequence(QKeySequence(self.config.shortcut_prev))
        self.ks_next.setKeySequence(QKeySequence(self.config.shortcut_next))

    def _add_stage_row(self, label: str = "新阶段", duration: int = 3, unit: str = "分", count_up: bool = False) -> None:
        row_widget = QWidget()
        row_widget.setObjectName("cardRow")
        row_widget.setStyleSheet("""
            #cardRow { background: #ffffff; border: 1px solid #dadce0; border-radius: 8px; }
            #cardRow:hover { border-color: #bdc1c6; background: #f8f9fa; }
        """)
        h = QHBoxLayout(row_widget)
        h.setContentsMargins(16, 6, 16, 6)
        h.setSpacing(12)
        
        name = QLineEdit(str(label))
        name.setPlaceholderText("环节名称")
        name.setMaxLength(100)
        h.addWidget(name, 2)
        
        spin = QSpinBox()
        spin.setRange(1, 9999)
        spin.setValue(duration)
        spin.setFixedWidth(80)
        h.addWidget(spin)
        
        unit_cmb = QComboBox()
        unit_cmb.addItems(["分", "秒"])
        unit_cmb.setCurrentText(str(unit))
        unit_cmb.setFixedWidth(65)
        h.addWidget(unit_cmb)

        dir_cmb = QComboBox()
        dir_cmb.addItems(["倒计时", "正计时"])
        dir_cmb.setCurrentText("正计时" if count_up else "倒计时")
        dir_cmb.setFixedWidth(100)
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
        row_widget.setObjectName("cardRow")
        row_widget.setStyleSheet("""
            #cardRow { background: #ffffff; border: 1px solid #dadce0; border-radius: 8px; }
            #cardRow:hover { border-color: #bdc1c6; background: #f8f9fa; }
        """)
        h = QHBoxLayout(row_widget)
        h.setContentsMargins(16, 6, 16, 6)
        h.setSpacing(12)
        
        lbl = QLabel("剩余时间：")
        lbl.setStyleSheet("color: #5f6368; font-weight: bold;")
        h.addWidget(lbl)
        
        spin = QSpinBox()
        spin.setRange(1, 9999)
        spin.setSuffix(" 秒")
        spin.setValue(seconds)
        spin.setFixedWidth(110)
        h.addWidget(spin)
        
        h.addSpacing(12)
        lbl_color = QLabel("高亮色：")
        lbl_color.setStyleSheet("color: #5f6368;")
        h.addWidget(lbl_color)
        
        cbtn = QPushButton()
        cbtn.setFixedSize(48, 28)
        cbtn.setCursor(Qt.PointingHandCursor)
        self._set_color_preview(cbtn, color)
        
        chk_sound = QCheckBox("附加提示音")
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
        layout.addSpacing(8)
        for icon, tip, delta in (("↑", "上移", -1), ("↓", "下移", 1)):
            b = QPushButton(icon)
            b.setFixedSize(28, 28)
            b.setToolTip(tip)
            b.setCursor(Qt.PointingHandCursor)
            b.setStyleSheet("QPushButton { background: transparent; color: #5f6368; border: none; font-size: 15px; } QPushButton:hover { color: #1a73e8; }")
            b.clicked.connect(partial(self._move_row, rows, row, delta, rebuild_fn))
            layout.addWidget(b)
            
        btn_del = QPushButton("✕")
        btn_del.setFixedSize(28, 28)
        btn_del.setToolTip("删除")
        btn_del.setCursor(Qt.PointingHandCursor)
        btn_del.setStyleSheet("QPushButton { background: transparent; color: #d93025; border: none; font-size: 15px; } QPushButton:hover { color: #c5221f; }")
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

    @staticmethod
    def _set_color_preview(widget: QWidget, color: str) -> None:
        widget.setStyleSheet(f"""
            background: {color}; 
            border: 1px solid #dadce0; 
            border-radius: 6px;
        """)

    def get_config(self) -> Config:
        self.config.auto_advance = self.chk_auto_advance.isChecked()
        self.config.show_stage_label = self.chk_show_label.isChecked()
        self.config.ppt_auto_start = self.chk_ppt_auto_start.isChecked()
        self.config.global_sound = self.chk_global_sound.isChecked()
        self.config.countdown_10s_sound = self.chk_10s_sound.isChecked()
        self.config.always_on_top = self.chk_always_on_top.isChecked()
        self.config.prevent_offscreen = self.chk_prevent_offscreen.isChecked()
        
        self.config.stages = [Stage(r["name"].text(), r["spin"].value(), r["unit_cmb"].currentText(), r["dir_cmb"].currentText() == "正计时") for r in self._stage_rows]
        self.config.alerts = [Alert(r["spin"].value(), r["color"], r["chk_sound"].isChecked()) for r in self._alert_rows]
        
        self.config.color = self._cur_color
        self.config.bg_color = self._cur_bg_color
        self.config.bg_opacity = self._bg_op_slider.value()
        self.config.font = self._font_cmb.currentFont().family()
        self.config.font_size = self._size_slider.value()
        self.config.stage_font = self._stage_font_cmb.currentFont().family()
        self.config.stage_font_size = self._stage_size_slider.value()
        self.config.opacity = self._op_slider.value() / 100

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

        self._connect_signals()
        self._apply_style()
        self._apply_shortcuts()
        self.controller.stop()

        screen = QApplication.primaryScreen().availableGeometry()
        self.float_bar.move(screen.left() + 40, screen.top() + 40)
        self.float_bar.show()

    def _check_ppt_status(self) -> None:
        if not self.config.ppt_auto_start:
            return

        is_active = is_ppt_slideshow_active()

        if is_active:
            self._ppt_stable_active_count += 1
            if self._ppt_stable_active_count >= 3 and not self._ppt_was_active:
                self._current_ppt_session_paused_by_user = False
                if self.controller.paused and self.controller._remaining_float > 0:
                    self.controller.toggle_pause()
        else:
            self._ppt_stable_active_count = 0
            if self._ppt_was_active:
                self._current_ppt_session_paused_by_user = False

        self._ppt_was_active = is_active

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
        fb.btn_settings.clicked.connect(self._open_settings)
        fb.btn_close.clicked.connect(self._exit)
        fb.request_settings.connect(self._open_settings)
        fb.request_exit.connect(self._exit)

        ctrl.tick.connect(lambda lbl, rem: fb.update_display(lbl, rem))
        ctrl.alert_triggered.connect(lambda c: fb.start_flash(c, 3000))
        ctrl.loop_restarted.connect(lambda: fb.start_flash("#44aaff", 1500))
        ctrl.state_changed.connect(fb.set_running)

    def _apply_style(self) -> None:
        c = self.config
        self.float_bar.apply_style(c.color, c.font, c.font_size, c.stage_font, c.stage_font_size,
                                   c.opacity, c.bg_qcolor(), c.always_on_top, c.show_stage_label, c.prevent_offscreen)

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
        dlg.btn_save.clicked.connect(lambda: self._save_settings(dlg))
        fb_geo = self.float_bar.geometry()
        screen_geo = QApplication.primaryScreen().availableGeometry()
        target_y = fb_geo.bottom() + 10
        if target_y + dlg.height() > screen_geo.bottom():
            target_y = fb_geo.top() - dlg.height() - 10
        dlg.move(fb_geo.left(), target_y)
        dlg.exec_()
        dlg.deleteLater()

    def _save_settings(self, dlg: SettingsWindow) -> None:
        dlg.get_config()
        self.config.save()
        self._apply_style()
        self._apply_shortcuts()
        self.controller.config = self.config
        self.controller.stop()
        dlg.accept()

    def _exit(self) -> None:
        self.controller.stop()
        self._ppt_monitor_timer.stop()
        for sc in self._shortcuts:
            sc.setEnabled(False)
            sc.deleteLater()
        self.float_bar.close()
        QApplication.quit()


if __name__ == "__main__":
    if hasattr(Qt, 'AA_EnableHighDpiScaling'):
        QApplication.setAttribute(Qt.AA_EnableHighDpiScaling, True)
    if hasattr(Qt, 'AA_UseHighDpiPixmaps'):
        QApplication.setAttribute(Qt.AA_UseHighDpiPixmaps, True)

    app = QApplication(sys.argv)
    app.setStyle("Fusion")
    app.setApplicationName(APP_NAME)
    app.setQuitOnLastWindowClosed(False)

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
