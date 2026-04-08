import sys
import json
import os
import platform
import threading
import subprocess
import time
import math
from dataclasses import dataclass, asdict
from functools import partial

from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
from PyQt5.QtGui import *
from PyQt5.QtSvg import QSvgRenderer

APP_NAME = "QTimer V1.0.0"
CONFIG_PATH = os.path.join(os.path.expanduser("~"), f".{APP_NAME.lower()}_config.json")

# ================================================================
#  原生声音播放器 (多线程异步，支持持续时长，绝对不卡界面)
# ================================================================
def play_alert_sound(duration_ms=200):
    sys_name = platform.system()
    if sys_name == "Windows":
        def _beep():
            try:
                import winsound
                # 发出 1500 Hz 的清脆声，根据 duration_ms 决定是短滴还是长鸣
                winsound.Beep(1500, duration_ms)
            except Exception:
                pass
        threading.Thread(target=_beep, daemon=True).start()
    elif sys_name == "Darwin":  # macOS
        def _mac_beep():
            try:
                if duration_ms > 1000:
                    # 对于超过 1 秒的长鸣，连续播放三次系统声效模拟长提示
                    for _ in range(3):
                        subprocess.call(['afplay', '/System/Library/Sounds/Glass.aiff'])
                else:
                    subprocess.Popen(['afplay', '/System/Library/Sounds/Tink.aiff'])
            except Exception:
                pass
        threading.Thread(target=_mac_beep, daemon=True).start()
    else:
        QApplication.beep()

# ================================================================
#  SVG 图标工厂
# ================================================================
SVG_ICONS = {
    "play":     '<svg viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg"><polygon points="6,4 20,12 6,20" fill="{color}"/></svg>',
    "pause":    '<svg viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg"><rect x="5" y="4" width="4" height="16" rx="1" fill="{color}"/><rect x="15" y="4" width="4" height="16" rx="1" fill="{color}"/></svg>',
    "restart":  '<svg viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg"><path d="M12 5V1L7 6l5 5V7c3.31 0 6 2.69 6 6s-2.69 6-6 6-6-2.69-6-6H4c0 4.42 3.58 8 8 8s8-3.58 8-8-3.58-8-8-8z" fill="{color}"/></svg>',
    "prev":     '<svg viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg"><polygon points="19,4 7,12 19,20" fill="{color}"/><rect x="3" y="4" width="3" height="16" rx="1" fill="{color}"/></svg>',
    "next":     '<svg viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg"><polygon points="5,4 17,12 5,20" fill="{color}"/><rect x="18" y="4" width="3" height="16" rx="1" fill="{color}"/></svg>',
    "settings": '<svg viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg"><path d="M19.14 12.94c.04-.3.06-.61.06-.94s-.02-.64-.07-.94l2.03-1.58c.18-.14.23-.41.12-.61l-1.92-3.32c-.12-.22-.37-.29-.59-.22l-2.39.96c-.5-.38-1.03-.7-1.62-.94l-.36-2.54c-.04-.24-.24-.41-.48-.41h-3.84c-.24 0-.43.17-.47.41l-.36 2.54c-.59.24-1.13.57-1.62.94l-2.39-.96c-.22-.08-.47 0-.59.22L2.74 8.87c-.12.21-.08.47.12.61l2.03 1.58c-.05.3-.09.63-.09.94s.02.64.07.94l-2.03 1.58c-.18.14-.23.41-.12.61l1.92 3.32c.12.22.37.29.59.22l2.39-.96c.5.38 1.03.7 1.62.94l.36 2.54c.05.24.24.41.48.41h3.84c.24 0 .44-.17.47-.41l.36-2.54c.59-.24 1.13-.56 1.62-.94l2.39.96c.22.08.47 0 .59-.22l1.92-3.32c.12-.22.07-.47-.12-.61l-2.01-1.58zM12 15.6c-1.98 0-3.6-1.62-3.6-3.6s1.62-3.6 3.6-3.6 3.6 1.62 3.6 3.6-1.62 3.6-3.6 3.6z" fill="{color}"/></svg>',
    "close":    '<svg viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg"><line x1="4" y1="4" x2="20" y2="20" stroke="{color}" stroke-width="2.5" stroke-linecap="round"/><line x1="20" y1="4" x2="4" y2="20" stroke="{color}" stroke-width="2.5" stroke-linecap="round"/></svg>',
}

def make_svg_icon(name: str, size: int, color: str = "white") -> QIcon:
    svg_str = SVG_ICONS[name].replace("{color}", color)
    renderer = QSvgRenderer(svg_str.encode("utf-8"))
    pixmap = QPixmap(size, size)
    pixmap.fill(Qt.transparent)
    painter = QPainter(pixmap)
    renderer.render(painter)
    painter.end()
    return QIcon(pixmap)


# ================================================================
#  数据模型
# ================================================================
@dataclass
class Stage:
    label: str = "说课时间"
    duration: int = 5
    unit: str = "分"

    @property
    def seconds(self) -> int:
        return self.duration * 60 if self.unit == "分" else self.duration

    @classmethod
    def from_dict(cls, d: dict):
        if "minutes" in d and "duration" not in d:
            return cls(label=d["label"], duration=d["minutes"], unit="分")
        return cls(label=d["label"], duration=d.get("duration", 5), unit=d.get("unit", "分"))

@dataclass
class Alert:
    seconds: int = 30
    color: str = "#ffaa00"
    play_sound: bool = True

    @classmethod
    def from_dict(cls, d: dict):
        return cls(seconds=d["seconds"], color=d["color"], play_sound=d.get("play_sound", True))

class Config:
    def __init__(self):
        self.auto_advance = False        
        self.global_sound = True          # 全局声音主控开关
        self.countdown_10s_sound = True  

        self.stages = [Stage("说课时间", 5, "分"), Stage("答辩时间", 2, "分")]
        self.alerts = [Alert(30, "#ffaa00", True), Alert(10, "#ff4444", True)]
        
        self.color = "#ffffff"
        self.font = "微软雅黑"
        self.font_size = 32
        self.opacity = 0.95
        self.bg_color = "#141414"
        self.bg_opacity = 82

        self.shortcut_toggle = "Ctrl+Space"
        self.shortcut_reset = "Ctrl+Return"
        self.shortcut_prev = "Ctrl+Left"
        self.shortcut_next = "Ctrl+Right"

    def save(self):
        data = {
            "auto_advance": self.auto_advance,
            "global_sound": self.global_sound,
            "countdown_10s_sound": self.countdown_10s_sound,
            "stages": [asdict(s) for s in self.stages],
            "alerts": [asdict(a) for a in self.alerts],
            "color": self.color, "font": self.font,
            "font_size": self.font_size, "opacity": self.opacity,
            "bg_color": self.bg_color, "bg_opacity": self.bg_opacity,
            "shortcut_toggle": self.shortcut_toggle, "shortcut_reset": self.shortcut_reset,
            "shortcut_prev": self.shortcut_prev, "shortcut_next": self.shortcut_next,
        }
        with open(CONFIG_PATH, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

    def load(self):
        if not os.path.exists(CONFIG_PATH):
            return
        try:
            with open(CONFIG_PATH, encoding="utf-8") as f:
                d = json.load(f)
            self.auto_advance = d.get("auto_advance", self.auto_advance)
            self.global_sound = d.get("global_sound", self.global_sound)
            self.countdown_10s_sound = d.get("countdown_10s_sound", self.countdown_10s_sound)
            self.stages = [Stage.from_dict(s) for s in d.get("stages", [])] or self.stages
            self.alerts = [Alert.from_dict(a) for a in d.get("alerts", [])] or self.alerts
            
            self.color = d.get("color", self.color)
            self.font = d.get("font", self.font)
            self.font_size = d.get("font_size", self.font_size)
            self.opacity = d.get("opacity", self.opacity)
            self.bg_color = d.get("bg_color", self.bg_color)
            self.bg_opacity = d.get("bg_opacity", self.bg_opacity)

            self.shortcut_toggle = d.get("shortcut_toggle", self.shortcut_toggle)
            self.shortcut_reset = d.get("shortcut_reset", self.shortcut_reset)
            self.shortcut_prev = d.get("shortcut_prev", self.shortcut_prev)
            self.shortcut_next = d.get("shortcut_next", self.shortcut_next)
        except Exception:
            pass

    def bg_qcolor(self) -> QColor:
        c = QColor(self.bg_color)
        c.setAlpha(int(self.bg_opacity / 100 * 255))
        return c


# ================================================================
#  无误差精确计时控制器 (Drift-Free Engine)
# ================================================================
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
        self._timer.setInterval(200) # 更高频率刷新UI防止卡顿，核心逻辑依据时间戳
        self._timer.timeout.connect(self._tick)
        
        self.running = False
        self.paused = True 
        
        self._stage_idx = 0
        self._remaining_float = 0.0   # 记录精确剩余小数秒
        self._target_time = 0.0       # 锚定系统时间，防止漂移
        self._last_displayed = -1
        
        self._triggered = set()
        self._zero_triggered = False

    def toggle_pause(self):
        if self._remaining_float <= 0:
            return
        
        if not self.running:
            self.running = True
            
        self.paused = not self.paused
        if not self.paused:
            # 恢复时，根据剩余精确时间重新推算目标时间戳
            self._target_time = time.time() + self._remaining_float
            self._timer.start()
        else:
            self._timer.stop()
            # 停止时，_remaining_float 已经在 _tick 中保存为了精确小数
            
        self.state_changed.emit(not self.paused)

    def restart_stage(self):
        self._load_stage()
        self._stop_and_wait()

    def prev_stage(self):
        self._stage_idx = (self._stage_idx - 1) % len(self.config.stages)
        self._load_stage()
        self._stop_and_wait()

    def next_stage(self):
        self._advance_idx()
        self._load_stage()
        self._stop_and_wait()

    def stop(self):
        self._stage_idx = 0
        self._load_stage()
        self._stop_and_wait()
        self.running = False

    def _stop_and_wait(self):
        self._timer.stop()
        self.paused = True
        self.state_changed.emit(False)

    def _load_stage(self):
        st = self.config.stages[self._stage_idx]
        self._remaining_float = float(st.seconds)
        self._last_displayed = st.seconds
        
        self._triggered.clear()
        self._zero_triggered = False
        
        self.stage_changed.emit(self._stage_idx, st.label)
        self.tick.emit(st.label, st.seconds)

    def _tick(self):
        if self.paused:
            return

        now = time.time()
        self._remaining_float = self._target_time - now
        
        # 向上取整满足倒计时的标准人类视觉习惯 (5.1秒显示为 6 秒)
        display_sec = int(math.ceil(self._remaining_float))
        if display_sec < 0:
            display_sec = 0

        # 如果时间跨秒了才更新，降低 UI 刷新率负担
        if display_sec != self._last_displayed:
            self._last_displayed = display_sec
            self.tick.emit(self.config.stages[self._stage_idx].label, display_sec)

            # --- 全局声音总控 ---
            if self.config.global_sound:
                # 最后十秒短音
                if self.config.countdown_10s_sound and 0 < display_sec <= 10:
                    play_alert_sound(200)

                # 节点触发音与变色闪烁
                for a in self.config.alerts:
                    if display_sec == a.seconds and a.seconds not in self._triggered:
                        self._triggered.add(a.seconds)
                        self.alert_triggered.emit(a.color)
                        if a.play_sound:
                            play_alert_sound(200)

        # 时间彻底耗尽的处理
        if self._remaining_float <= 0 and not self._zero_triggered:
            self._zero_triggered = True
            self._remaining_float = 0.0
            
            # 长鸣 2 秒
            if self.config.global_sound:
                play_alert_sound(2000)

            if self.config.auto_advance:
                self._advance_idx()
                self._load_stage()
                # 自动模式下重新锚定新环节的系统时间，实现无缝衔接
                self._target_time = time.time() + self._remaining_float 
            else:
                self._stop_and_wait()

    def _advance_idx(self):
        self._stage_idx += 1
        if self._stage_idx >= len(self.config.stages):
            self._stage_idx = 0
            self.loop_restarted.emit()


# ================================================================
#  浮动计时条 (视觉对称修复版)
# ================================================================
class FloatBar(QWidget):
    request_settings = pyqtSignal()
    request_exit = pyqtSignal()

    ICON_SIZE = 34

    def __init__(self):
        super().__init__()
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint | Qt.Tool)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setAttribute(Qt.WA_Hover)
        self.setFocusPolicy(Qt.ClickFocus)

        self._drag_pos = None
        self._text_color = "#ffffff"
        self._font_family = "微软雅黑"
        self._font_size = 32
        self._bg_color = QColor(20, 20, 20, 210)
        
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
    def bar_width(self):
        return self.width()

    @bar_width.setter
    def bar_width(self, w):
        self.setFixedWidth(w)

    def _build_ui(self):
        self._layout = QHBoxLayout(self)
        self._layout.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)
        
        # 精确数学计算保证绝对对称：左边距锁定为 18 像素
        self._layout.setContentsMargins(18, 0, 0, 0)
        self._layout.setSpacing(0)

        self.lbl_stage = QLabel("环节名称")
        self.lbl_stage.setAlignment(Qt.AlignCenter)
        
        self.lbl_time = QLabel("00:00")
        self.lbl_time.setAlignment(Qt.AlignCenter)

        self._layout.addWidget(self.lbl_stage)
        self._layout.addSpacing(12)  # 文字之间的间距
        self._layout.addWidget(self.lbl_time)
        self._layout.addSpacing(18)  # 文字到按钮之间的间距 (将化身为折叠状态时的精准右留白)

        self._btn_container = QWidget()
        btn_lay = QHBoxLayout(self._btn_container)
        btn_lay.setContentsMargins(0, 0, 0, 0)
        btn_lay.setSpacing(2)

        self.btn_toggle = self._make_icon_btn("play", "开始/暂停")
        self.btn_restart = self._make_icon_btn("restart", "重置当前环节")
        self.btn_prev = self._make_icon_btn("prev", "上一阶段")
        self.btn_next = self._make_icon_btn("next", "下一阶段")
        self.btn_settings = self._make_icon_btn("settings", "设置")
        self.btn_close = self._make_icon_btn("close", "退出")

        for b in (self.btn_toggle, self.btn_restart, self.btn_prev, self.btn_next,
                  self.btn_settings, self.btn_close):
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
        b.setIcon(make_svg_icon(icon_name, self.ICON_SIZE - 8))
        b.setIconSize(QSize(self.ICON_SIZE - 8, self.ICON_SIZE - 8))
        b.setStyleSheet("""
            QPushButton { background: rgba(255,255,255,15); border: none; border-radius: 7px; }
            QPushButton:hover { background: rgba(255,255,255,40); }
        """)
        return b

    def apply_style(self, color, font, size, opacity, bg_color: QColor):
        self._text_color = color
        self._font_family = font
        self._font_size = size
        self._bg_color = bg_color
        self.setWindowOpacity(opacity)
        self._refresh_labels()
        self._update_size()
        self.update()

    def _refresh_labels(self, stage_color=None, time_color=None):
        sc = stage_color or self._text_color
        tc = time_color or self._text_color
        stage_size = max(13, int(self._font_size * 0.65))
        self.lbl_stage.setStyleSheet(
            f"color:{sc}; font-family:'{self._font_family}'; "
            f"font-size:{stage_size}px; font-weight:600; background:transparent;")
        self.lbl_time.setStyleSheet(
            f"color:{tc}; font-family:'{self._font_family}'; "
            f"font-size:{self._font_size}px; font-weight:900; background:transparent;")

    def _update_size(self):
        stage_size = max(13, int(self._font_size * 0.65))
        fm_stage = QFontMetrics(QFont(self._font_family, stage_size, QFont.Bold))
        fm_time = QFontMetrics(QFont(self._font_family, self._font_size, QFont.Black))
        
        text = self.lbl_stage.text()
        if not text or text == "环节名称": text = "说课时间"
        
        stage_w = fm_stage.horizontalAdvance(text) + 4
        time_w = fm_time.horizontalAdvance("00:00") + 4
        
        self.lbl_stage.setFixedWidth(stage_w)
        self.lbl_time.setFixedWidth(time_w)

        btn_w = (self.ICON_SIZE + 2) * 6
        self._btn_container.setFixedWidth(btn_w)

        # 绝对精准的视觉对称： 折叠宽度 = 左留白18 + 阶段字宽 + 字间距12 + 时间字宽 + 右留白18
        self._text_width = 18 + stage_w + 12 + time_w + 18
        # 展开宽度 = 折叠宽度 + 按钮宽 + 展开后的右侧保护留白16
        self._full_width = self._text_width + btn_w + 16

        h = max(self._font_size + 20, 50)
        self.setFixedHeight(h)

        if self.underMouse():
            self.setFixedWidth(self._full_width)
            self._btn_opacity.setOpacity(1.0)
        else:
            self.setFixedWidth(self._text_width)
            self._btn_opacity.setOpacity(0.0)

    def update_display(self, stage: str, remaining: int):
        mm, ss = divmod(remaining, 60)
        if self.lbl_stage.text() != stage:
            self.lbl_stage.setText(stage)
            self._update_size()
        self.lbl_time.setText(f"{mm:02d}:{ss:02d}")

    def set_running(self, running: bool):
        self.btn_toggle.setIcon(make_svg_icon("pause" if running else "play", self.ICON_SIZE - 8))

    def start_flash(self, color: str, auto_stop_ms=3000):
        self._flash_color = color
        self._flash_state = False
        self._flash_timer.start(400)
        if auto_stop_ms > 0:
            QTimer.singleShot(auto_stop_ms, self.stop_flash)

    def stop_flash(self):
        self._flash_timer.stop()
        self._refresh_labels()

    def _do_flash(self):
        self._flash_state = not self._flash_state
        c = self._flash_color if self._flash_state else self._text_color
        self._refresh_labels(stage_color=c, time_color=c)

    def enterEvent(self, e):
        self._anim_group.stop()
        self._width_anim.setStartValue(self.width())
        self._width_anim.setEndValue(self._full_width)
        self._btn_anim.setStartValue(self._btn_opacity.opacity())
        self._btn_anim.setEndValue(1.0)
        self._anim_group.start()
        super().enterEvent(e)

    def leaveEvent(self, e):
        self._anim_group.stop()
        self._width_anim.setStartValue(self.width())
        self._width_anim.setEndValue(self._text_width)
        self._btn_anim.setStartValue(self._btn_opacity.opacity())
        self._btn_anim.setEndValue(0.0)
        self._anim_group.start()
        super().leaveEvent(e)

    def _show_ctx_menu(self, pos):
        m = QMenu(self)
        m.setStyleSheet("""
            QMenu { background:#2a2a2a; color:#eee; border:1px solid #444; border-radius:6px; padding:4px; }
            QMenu::item { padding:6px 20px; border-radius:4px; }
            QMenu::item:selected { background:#3d3d3d; }
            QMenu::separator { background:#444; height:1px; margin:4px 8px; }
        """)
        m.addAction("开始 / 暂停").triggered.connect(self.btn_toggle.click)
        m.addAction("重置本环节").triggered.connect(self.btn_restart.click)
        m.addAction("上一阶段").triggered.connect(self.btn_prev.click)
        m.addAction("下一阶段").triggered.connect(self.btn_next.click)
        m.addSeparator()
        m.addAction("设置").triggered.connect(self.request_settings.emit)
        m.addAction("退出").triggered.connect(self.request_exit.emit)
        m.exec_(self.mapToGlobal(pos))

    def paintEvent(self, e):
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing)
        p.setBrush(self._bg_color)
        p.setPen(Qt.NoPen)
        p.drawRoundedRect(self.rect(), 12, 12)

    def mousePressEvent(self, e):
        if e.button() == Qt.LeftButton:
            self._drag_pos = e.globalPos() - self.pos()

    def mouseMoveEvent(self, e):
        if self._drag_pos and e.buttons() == Qt.LeftButton:
            self.move(e.globalPos() - self._drag_pos)

    def mouseReleaseEvent(self, e):
        self._drag_pos = None


# ================================================================
#  设置窗口 (包含全局声音总控)
# ================================================================
class SettingsWindow(QDialog):
    _SS = """
    QDialog { background: #f0f2f5; }
    QLabel { color: #333; font-size: 13px; }
    QCheckBox { color: #333; font-size: 13px; }
    
    QListWidget {
        background: #ffffff;
        border: none;
        border-right: 1px solid #dcdde1;
        outline: none;
    }
    QListWidget::item {
        padding: 14px 18px;
        color: #555;
        font-size: 14px;
        border-bottom: 1px solid #f5f6fa;
    }
    QListWidget::item:selected {
        background: #f0f7ff;
        color: #1a73e8;
        font-weight: bold;
        border-left: 4px solid #1a73e8;
    }
    QListWidget::item:hover:!selected {
        background: #f8f9fa;
    }

    QLineEdit, QSpinBox, QFontComboBox, QComboBox, QKeySequenceEdit {
        background: #fff; color: #222; border: 1px solid #ccc;
        border-radius: 4px; padding: 6px 8px; font-size: 13px; min-height: 20px;
    }
    QLineEdit:focus, QKeySequenceEdit:focus { border-color: #1a73e8; }
    
    QPushButton {
        background: #fff; color: #333; border: 1px solid #ccc;
        border-radius: 4px; padding: 6px 14px; font-size: 13px;
    }
    QPushButton:hover { background: #f8f9fa; border-color: #aaa; }
    QPushButton:pressed { background: #e5e5e5; }
    
    QScrollArea { border: none; background: transparent; }
    QScrollBar:vertical { background: #f0f0f0; width: 6px; }
    QScrollBar::handle:vertical { background: #bbb; border-radius: 3px; min-height: 24px; }
    QSlider::groove:horizontal { background: #ddd; height: 4px; border-radius: 2px; }
    QSlider::handle:horizontal { background: #1a73e8; width: 16px; height: 16px; margin: -6px 0; border-radius: 8px; }
    """

    def __init__(self, config: Config, parent=None):
        super().__init__(parent)
        self.config = config
        self.setWindowTitle(f"{APP_NAME}  - QwejayHuang")
        self.resize(720, 520) 
        self.setStyleSheet(self._SS)
        self.setWindowFlags(self.windowFlags() & ~Qt.WindowContextHelpButtonHint)
        
        self._stage_rows = []
        self._alert_rows = []
        
        self._build_ui()
        self._populate()

    def _build_ui(self):
        root_lay = QVBoxLayout(self)
        root_lay.setContentsMargins(0, 0, 0, 0)
        root_lay.setSpacing(0)

        main_widget = QWidget()
        main_lay = QHBoxLayout(main_widget)
        main_lay.setContentsMargins(0, 0, 0, 0)
        main_lay.setSpacing(0)

        self.nav_list = QListWidget()
        self.nav_list.setFixedWidth(160)
        items = ["📑 环节与流程", "🔔 提醒与声音", "🎨 外观与样式", "⌨️ 快捷键设置"]
        for txt in items:
            self.nav_list.addItem(txt)
        main_lay.addWidget(self.nav_list)

        self.stack = QStackedWidget()
        self.stack.setStyleSheet("background: #fcfcfd;")
        
        self.stack.addWidget(self._build_page_stages())
        self.stack.addWidget(self._build_page_alerts())
        self.stack.addWidget(self._build_page_appearance())
        self.stack.addWidget(self._build_page_shortcuts())
        
        main_lay.addWidget(self.stack)
        root_lay.addWidget(main_widget)

        self.nav_list.currentRowChanged.connect(self.stack.setCurrentIndex)
        self.nav_list.setCurrentRow(0)

        bottom_bar = QWidget()
        bottom_bar.setStyleSheet("background: #ffffff; border-top: 1px solid #ddd;")
        btn_lay = QHBoxLayout(bottom_bar)
        btn_lay.setContentsMargins(20, 12, 20, 12)
        
        self.btn_save = QPushButton("✓  保存并应用")
        self.btn_save.setStyleSheet("background:#1a73e8; color:#fff; border:none; font-weight:bold; padding: 8px 24px;")
        self.btn_save.setCursor(Qt.PointingHandCursor)
        
        self.btn_cancel = QPushButton("取消")
        self.btn_cancel.setCursor(Qt.PointingHandCursor)
        self.btn_cancel.clicked.connect(self.reject)
        
        btn_lay.addStretch()
        btn_lay.addWidget(self.btn_cancel)
        btn_lay.addWidget(self.btn_save)
        root_lay.addWidget(bottom_bar)

    def _create_page_wrap(self, title: str, desc: str) -> (QWidget, QVBoxLayout):
        w = QWidget()
        lay = QVBoxLayout(w)
        lay.setContentsMargins(30, 24, 30, 20)
        lay.setSpacing(16)
        
        lbl_title = QLabel(title)
        lbl_title.setStyleSheet("font-size: 18px; font-weight: bold; color: #222;")
        lbl_desc = QLabel(desc)
        lbl_desc.setStyleSheet("color: #666; margin-bottom: 10px;")
        
        lay.addWidget(lbl_title)
        lay.addWidget(lbl_desc)
        return w, lay

    def _build_page_stages(self):
        w, lay = self._create_page_wrap("环节配置", "配置演示的不同阶段（如：说课 5 分、答辩 2 分）。")
        
        self.chk_auto_advance = QCheckBox("当前阶段结束后，自动进入并开始下一阶段 (自动模式)")
        self.chk_auto_advance.setStyleSheet("font-weight: bold; color: #1a73e8;")
        lay.addWidget(self.chk_auto_advance)
        
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        content = QWidget()
        self._stage_vlay = QVBoxLayout(content)
        self._stage_vlay.setContentsMargins(0, 0, 0, 0)
        self._stage_vlay.setAlignment(Qt.AlignTop)
        scroll.setWidget(content)
        lay.addWidget(scroll)

        btn_add = QPushButton("＋ 新增阶段")
        btn_add.setCursor(Qt.PointingHandCursor)
        btn_add.clicked.connect(lambda: self._add_stage_row())
        lay.addWidget(btn_add, alignment=Qt.AlignCenter)
        return w

    def _build_page_alerts(self):
        w, lay = self._create_page_wrap("提醒与声音", "配置时间快到时产生的闪烁与系统提示音。")
        
        self.chk_global_sound = QCheckBox("🔊 开启声音")
        self.chk_global_sound.setStyleSheet("font-weight: bold; color: #d35400; font-size: 14px;")
        lay.addWidget(self.chk_global_sound)
        
        self.chk_10s_sound = QCheckBox("最后10秒播放提示音")
        lay.addWidget(self.chk_10s_sound)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        content = QWidget()
        self._alert_vlay = QVBoxLayout(content)
        self._alert_vlay.setContentsMargins(0, 0, 0, 0)
        self._alert_vlay.setAlignment(Qt.AlignTop)
        scroll.setWidget(content)
        lay.addWidget(scroll)

        btn_add = QPushButton("＋ 新增提醒节点")
        btn_add.setCursor(Qt.PointingHandCursor)
        btn_add.clicked.connect(lambda: self._add_alert_row())
        lay.addWidget(btn_add, alignment=Qt.AlignCenter)
        return w

    def _build_page_appearance(self):
        w, lay = self._create_page_wrap("外观样式", "自定义悬浮计时器的色彩、透明度与排版风格。")
        
        form = QFormLayout()
        form.setContentsMargins(10, 10, 10, 10)
        form.setSpacing(20)

        color_row = QHBoxLayout()
        self._color_preview = QLabel()
        self._color_preview.setFixedSize(24, 24)
        c_btn = QPushButton("选择色彩")
        c_btn.clicked.connect(self._pick_color)
        color_row.addWidget(self._color_preview)
        color_row.addWidget(c_btn)
        color_row.addStretch()
        form.addRow("文字颜色：", color_row)

        bg_row = QHBoxLayout()
        self._bg_color_preview = QLabel()
        self._bg_color_preview.setFixedSize(24, 24)
        bg_btn = QPushButton("选择色彩")
        bg_btn.clicked.connect(self._pick_bg_color)
        bg_row.addWidget(self._bg_color_preview)
        bg_row.addWidget(bg_btn)
        bg_row.addStretch()
        form.addRow("背景颜色：", bg_row)

        bg_op_row = QHBoxLayout()
        self._bg_op_slider = QSlider(Qt.Horizontal)
        self._bg_op_slider.setRange(10, 100)
        self._bg_op_lbl = QLabel()
        self._bg_op_lbl.setFixedWidth(40)
        self._bg_op_slider.valueChanged.connect(lambda v: self._bg_op_lbl.setText(f"{v}%"))
        bg_op_row.addWidget(self._bg_op_slider)
        bg_op_row.addWidget(self._bg_op_lbl)
        form.addRow("背景透明度：", bg_op_row)

        self._font_cmb = QFontComboBox()
        self._font_cmb.setFontFilters(QFontComboBox.ScalableFonts)
        form.addRow("字体风格：", self._font_cmb)

        sz_row = QHBoxLayout()
        self._size_slider = QSlider(Qt.Horizontal)
        self._size_slider.setRange(16, 72)
        self._size_lbl = QLabel()
        self._size_lbl.setFixedWidth(40)
        self._size_slider.valueChanged.connect(lambda v: self._size_lbl.setText(f"{v} px"))
        sz_row.addWidget(self._size_slider)
        sz_row.addWidget(self._size_lbl)
        form.addRow("时间字号：", sz_row)

        op_row = QHBoxLayout()
        self._op_slider = QSlider(Qt.Horizontal)
        self._op_slider.setRange(20, 100)
        self._op_lbl = QLabel()
        self._op_lbl.setFixedWidth(40)
        self._op_slider.valueChanged.connect(lambda v: self._op_lbl.setText(f"{v}%"))
        op_row.addWidget(self._op_slider)
        op_row.addWidget(self._op_lbl)
        form.addRow("整体透明度：", op_row)

        lay.addLayout(form)
        lay.addStretch()
        return w

    def _build_page_shortcuts(self):
        w, lay = self._create_page_wrap("快捷键配置", "为核心操作分配全局快捷键。\n(⚠️注意：由于系统级限制，快捷键仅在您鼠标点击激活计时器面板时生效)")
        
        form = QFormLayout()
        form.setContentsMargins(10, 10, 10, 10)
        form.setSpacing(24)

        self.ks_toggle = QKeySequenceEdit()
        self.ks_reset = QKeySequenceEdit()
        self.ks_prev = QKeySequenceEdit()
        self.ks_next = QKeySequenceEdit()

        form.addRow("▶️ 播放 / 暂停：", self.ks_toggle)
        form.addRow("🔄 重置当前环节：", self.ks_reset)
        form.addRow("⏮️ 上一个环节：", self.ks_prev)
        form.addRow("⏭️ 下一个环节：", self.ks_next)

        lay.addLayout(form)
        lay.addStretch()
        return w

    def _populate(self):
        self.chk_auto_advance.setChecked(self.config.auto_advance)
        for s in self.config.stages:
            self._add_stage_row(s.label, s.duration, s.unit)
        
        self.chk_global_sound.setChecked(self.config.global_sound)
        self.chk_10s_sound.setChecked(self.config.countdown_10s_sound)
        for a in self.config.alerts:
            self._add_alert_row(a.seconds, a.color, a.play_sound)
        
        self._cur_color = self.config.color
        self._set_color_preview(self._color_preview, self._cur_color)
        self._cur_bg_color = self.config.bg_color
        self._set_color_preview(self._bg_color_preview, self._cur_bg_color)
        self._bg_op_slider.setValue(self.config.bg_opacity)
        self._font_cmb.setCurrentFont(QFont(self.config.font))
        self._size_slider.setValue(self.config.font_size)
        self._op_slider.setValue(int(self.config.opacity * 100))

        self.ks_toggle.setKeySequence(QKeySequence(self.config.shortcut_toggle))
        self.ks_reset.setKeySequence(QKeySequence(self.config.shortcut_reset))
        self.ks_prev.setKeySequence(QKeySequence(self.config.shortcut_prev))
        self.ks_next.setKeySequence(QKeySequence(self.config.shortcut_next))

    def _add_stage_row(self, label="新阶段", duration=3, unit="分"):
        row_widget = QWidget()
        h = QHBoxLayout(row_widget)
        h.setContentsMargins(0, 6, 0, 6)
        
        name = QLineEdit(label)
        name.setPlaceholderText("阶段名称")
        h.addWidget(name, 2)
        
        spin = QSpinBox()
        spin.setRange(1, 9999)
        spin.setValue(duration)
        spin.setFixedWidth(70)
        h.addWidget(spin)
        
        unit_cmb = QComboBox()
        unit_cmb.addItems(["分", "秒"])
        unit_cmb.setCurrentText(unit)
        unit_cmb.setFixedWidth(50)
        h.addWidget(unit_cmb)

        row = {"widget": row_widget, "name": name, "spin": spin, "unit_cmb": unit_cmb}
        self._add_row_controls(h, self._stage_rows, row, self._rebuild_stage_rows)
        self._stage_rows.append(row)
        self._stage_vlay.addWidget(row_widget)

    def _rebuild_stage_rows(self):
        self._rebuild_rows(self._stage_vlay, self._stage_rows,
                           lambda r: self._add_stage_row(r["name"].text(), r["spin"].value(), r["unit_cmb"].currentText()))

    def _add_alert_row(self, seconds=20, color="#ffaa00", play_sound=True):
        row_widget = QWidget()
        h = QHBoxLayout(row_widget)
        h.setContentsMargins(0, 6, 0, 6)
        
        lbl = QLabel("剩余：")
        h.addWidget(lbl)
        
        spin = QSpinBox()
        spin.setRange(1, 9999)
        spin.setSuffix(" 秒")
        spin.setValue(seconds)
        spin.setFixedWidth(90)
        h.addWidget(spin)
        
        cbtn = QPushButton()
        cbtn.setFixedSize(24, 24)
        cbtn.setCursor(Qt.PointingHandCursor)
        cbtn.setStyleSheet(f"background:{color}; border:1px solid #bbb; border-radius:4px;")
        
        chk_sound = QCheckBox("触发声音")
        chk_sound.setChecked(play_sound)

        row = {"widget": row_widget, "spin": spin, "color": color, "cbtn": cbtn, "chk_sound": chk_sound}
        cbtn.clicked.connect(partial(self._pick_alert_color, row))
        
        h.addSpacing(10)
        h.addWidget(QLabel("闪烁色:"))
        h.addWidget(cbtn)
        h.addSpacing(10)
        h.addWidget(chk_sound)
        h.addStretch()

        self._add_row_controls(h, self._alert_rows, row, self._rebuild_alert_rows)
        self._alert_rows.append(row)
        self._alert_vlay.addWidget(row_widget)

    def _pick_alert_color(self, row: dict):
        c = QColorDialog.getColor(QColor(row["color"]), self)
        if c.isValid():
            row["color"] = c.name()
            row["cbtn"].setStyleSheet(f"background:{c.name()}; border:1px solid #bbb; border-radius:4px;")

    def _rebuild_alert_rows(self):
        self._rebuild_rows(self._alert_vlay, self._alert_rows,
                           lambda r: self._add_alert_row(r["spin"].value(), r["color"], r["chk_sound"].isChecked()))

    def _add_row_controls(self, layout, rows, row, rebuild_fn):
        btn_style = "background:#f5f6fa; color:#444; border:1px solid #dcdde1; border-radius:4px; font-size:12px; padding:0;"
        for icon, tip, delta in (("↑", "上移", -1), ("↓", "下移", 1)):
            b = QPushButton(icon)
            b.setFixedSize(24, 24)
            b.setToolTip(tip)
            b.setCursor(Qt.PointingHandCursor)
            b.setStyleSheet(btn_style)
            b.clicked.connect(partial(self._move_row, rows, row, delta, rebuild_fn))
            layout.addWidget(b)
            
        btn_del = QPushButton("✕")
        btn_del.setFixedSize(24, 24)
        btn_del.setToolTip("删除")
        btn_del.setCursor(Qt.PointingHandCursor)
        btn_del.setStyleSheet("background:#ffe0e0; color:#c0392b; border:1px solid #ffbbbb; border-radius:4px;")
        btn_del.clicked.connect(partial(self._delete_row, rows, row, rebuild_fn))
        layout.addWidget(btn_del)

    def _move_row(self, rows: list, row: dict, delta: int, rebuild_fn):
        idx = rows.index(row)
        new_idx = idx + delta
        if 0 <= new_idx < len(rows):
            rows[idx], rows[new_idx] = rows[new_idx], rows[idx]
            rebuild_fn()

    def _delete_row(self, rows: list, row: dict, rebuild_fn):
        if len(rows) > 1:
            rows.remove(row)
            rebuild_fn()

    def _rebuild_rows(self, layout: QLayout, rows: list, add_fn):
        saved = list(rows)
        rows.clear()
        while layout.count():
            w = layout.takeAt(0).widget()
            if w: w.deleteLater()
        for r in saved: add_fn(r)

    def _pick_color(self):
        c = QColorDialog.getColor(QColor(self._cur_color), self)
        if c.isValid():
            self._cur_color = c.name()
            self._set_color_preview(self._color_preview, c.name())

    def _pick_bg_color(self):
        c = QColorDialog.getColor(QColor(self._cur_bg_color), self)
        if c.isValid():
            self._cur_bg_color = c.name()
            self._set_color_preview(self._bg_color_preview, c.name())

    def _set_color_preview(self, label: QLabel, color: str):
        label.setStyleSheet(f"background:{color}; border:1px solid #bbb; border-radius:4px;")

    def get_config(self) -> Config:
        self.config.auto_advance = self.chk_auto_advance.isChecked()
        self.config.global_sound = self.chk_global_sound.isChecked()
        self.config.countdown_10s_sound = self.chk_10s_sound.isChecked()
        
        self.config.stages = [Stage(r["name"].text(), r["spin"].value(), r["unit_cmb"].currentText()) for r in self._stage_rows]
        self.config.alerts = [Alert(r["spin"].value(), r["color"], r["chk_sound"].isChecked()) for r in self._alert_rows]
        
        self.config.color = self._cur_color
        self.config.bg_color = self._cur_bg_color
        self.config.bg_opacity = self._bg_op_slider.value()
        self.config.font = self._font_cmb.currentFont().family()
        self.config.font_size = self._size_slider.value()
        self.config.opacity = self._op_slider.value() / 100

        self.config.shortcut_toggle = self.ks_toggle.keySequence().toString()
        self.config.shortcut_reset = self.ks_reset.keySequence().toString()
        self.config.shortcut_prev = self.ks_prev.keySequence().toString()
        self.config.shortcut_next = self.ks_next.keySequence().toString()
        
        return self.config


# ================================================================
#  主应用协调器
# ================================================================
class App(QObject):
    def __init__(self):
        super().__init__()
        self.config = Config()
        self.config.load()
        
        self.float_bar = FloatBar()
        self.controller = TimerController(self.config)
        self._shortcuts = []
        
        self._connect_signals()
        self._apply_style()
        self._apply_shortcuts()
        self.controller.stop()
        
        screen = QApplication.primaryScreen().availableGeometry()
        self.float_bar.move(screen.left() + 20, screen.top() + 20)
        self.float_bar.show()

    def _connect_signals(self):
        fb = self.float_bar
        ctrl = self.controller
        
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

    def _apply_style(self):
        c = self.config
        self.float_bar.apply_style(c.color, c.font, c.font_size, c.opacity, c.bg_qcolor())

    def _apply_shortcuts(self):
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

    def _open_settings(self):
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

    def _save_settings(self, dlg: SettingsWindow):
        dlg.get_config()
        self.config.save()
        self._apply_style()
        self._apply_shortcuts()
        self.controller.config = self.config
        self.controller.stop() 
        dlg.accept()

    def _exit(self):
        self.controller.stop()
        self.float_bar.close()
        QApplication.quit()


if __name__ == "__main__":
    app = QApplication(sys.argv)
    app.setStyle("Fusion")
    app.setApplicationName(APP_NAME)
    app.setQuitOnLastWindowClosed(False)
    main = App()
    sys.exit(app.exec_())