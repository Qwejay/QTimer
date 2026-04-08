import sys
import json
import os
import time
import math

from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
from PyQt5.QtGui import *

CONFIG_PATH = "ppt_timer_config.json"

# ==========================================
# 辅助函数：根据背景颜色深浅，返回合适的文字颜色(黑/白)
# ==========================================
def get_contrast_color(hex_color):
    hex_color = hex_color.lstrip('#')
    if len(hex_color) == 6:
        r, g, b = int(hex_color[0:2], 16), int(hex_color[2:4], 16), int(hex_color[4:6], 16)
        luminance = (0.299 * r + 0.587 * g + 0.114 * b) / 255
        return "#000000" if luminance > 0.5 else "#ffffff"
    return "#000000"

# ==========================================
# 辅助函数：HEX颜色转RGBA格式字符串
# ==========================================
def hex_to_rgba(hex_color, opacity):
    hex_color = hex_color.lstrip('#')
    if len(hex_color) == 6:
        r, g, b = int(hex_color[0:2], 16), int(hex_color[2:4], 16), int(hex_color[4:6], 16)
        return f"rgba({r}, {g}, {b}, {opacity})"
    return f"rgba(25, 25, 28, {opacity})"

# ==========================================
# 纯代码绘制的扁平化矢量按钮
# ==========================================
class VectorBtn(QPushButton):
    def __init__(self, icon_type, tooltip=""):
        super().__init__()
        self.icon_type = icon_type
        self.setToolTip(tooltip)
        self.setFixedSize(42, 42) 
        self.setCursor(Qt.PointingHandCursor)
        self.is_hover = False
        self.is_pressed = False
        self.is_playing = False
        self.base_color = QColor(255, 255, 255)

    def set_base_color(self, hex_color):
        self.base_color = QColor(hex_color)
        self.update()

    def set_toggle_state(self, is_playing):
        self.is_playing = is_playing
        self.update()

    def enterEvent(self, e):
        self.is_hover = True
        self.update()
        super().enterEvent(e)

    def leaveEvent(self, e):
        self.is_hover = False
        self.update()
        super().leaveEvent(e)

    def mousePressEvent(self, e):
        self.is_pressed = True
        self.update()
        super().mousePressEvent(e)

    def mouseReleaseEvent(self, e):
        self.is_pressed = False
        self.update()
        super().mouseReleaseEvent(e)

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)

        bg_color = Qt.transparent
        hover_alpha = 40 if self.base_color.lightness() < 128 else 60
        press_alpha = 60 if self.base_color.lightness() < 128 else 30

        if self.is_pressed:
            bg_color = QColor(self.base_color.red(), self.base_color.green(), self.base_color.blue(), press_alpha)
        elif self.is_hover:
            bg_color = QColor(self.base_color.red(), self.base_color.green(), self.base_color.blue(), hover_alpha)

        if self.icon_type == "trash" and self.is_hover:
            bg_color = QColor(245, 108, 108, 200)

        painter.setBrush(bg_color)
        painter.setPen(Qt.NoPen)
        painter.drawRoundedRect(self.rect(), 21, 21)

        icon_color = self.base_color
        if not self.is_hover and self.icon_type != "trash":
            icon_color.setAlpha(180)

        if self.icon_type == "trash":
            icon_color = QColor(255, 255, 255) if self.is_hover else QColor(150, 150, 150)
            
        painter.setBrush(icon_color)
        painter.setPen(Qt.NoPen)

        cx, cy = self.width() / 2, self.height() / 2
        s = 16 
        painter.translate(cx, cy)

        if self.icon_type == "toggle":
            if not self.is_playing:
                path = QPainterPath()
                path.moveTo(-s/2.5, -s/1.8)
                path.lineTo(s/1.5, 0)
                path.lineTo(-s/2.5, s/1.8)
                painter.drawPath(path)
            else:
                painter.drawRoundedRect(QRectF(-s/2, -s/1.8, s/3, s*1.1), 1, 1)
                painter.drawRoundedRect(QRectF(s/6, -s/1.8, s/3, s*1.1), 1, 1)

        elif self.icon_type == "restart":
            pen = QPen(icon_color, 2.5, Qt.SolidLine, Qt.RoundCap)
            painter.setPen(pen)
            painter.setBrush(Qt.transparent)
            r = s / 1.2
            painter.drawArc(QRectF(-r, -r, 2*r, 2*r), 16 * 60, 16 * 270)
            painter.setPen(Qt.NoPen)
            painter.setBrush(icon_color)
            path = QPainterPath()
            tip_x = r * math.cos(math.radians(-60))
            tip_y = -r * math.sin(math.radians(-60))
            painter.translate(tip_x, tip_y)
            painter.rotate(30)
            path.moveTo(0, -5)
            path.lineTo(9, 0)
            path.lineTo(0, 5)
            painter.drawPath(path)

        elif self.icon_type == "next":
            path = QPainterPath()
            path.moveTo(-s/2, -s/1.8)
            path.lineTo(s/6, 0)
            path.lineTo(-s/2, s/1.8)
            painter.drawPath(path)
            painter.drawRoundedRect(QRectF(s/4, -s/1.8, s/5, s*1.1), 1, 1)

        elif self.icon_type == "setting":
            painter.setPen(Qt.NoPen)
            painter.setBrush(icon_color)
            for i in range(8):
                painter.drawRoundedRect(QRectF(-2.5, -s/1.3, 5, s/1.3*2), 1, 1)
                painter.rotate(45)
            painter.drawEllipse(QPointF(0,0), s/1.5, s/1.5)
            painter.setCompositionMode(QPainter.CompositionMode_Clear)
            painter.drawEllipse(QPointF(0,0), s/3.5, s/3.5)
            painter.setCompositionMode(QPainter.CompositionMode_SourceOver)
            
        elif self.icon_type == "trash":
            pen = QPen(icon_color, 1.8, Qt.SolidLine, Qt.RoundCap, Qt.MiterJoin)
            painter.setPen(pen)
            painter.setBrush(Qt.transparent)
            painter.drawRoundedRect(QRectF(-s/2.5, -s/3, s/1.25, s*1.1), 1, 1)
            painter.drawLine(QPointF(-s/1.8, -s/3), QPointF(s/1.8, -s/3))
            painter.drawLine(QPointF(-s/4, -s/3), QPointF(-s/4, -s/1.8))
            painter.drawLine(QPointF(s/4, -s/3), QPointF(s/4, -s/1.8))
            painter.drawLine(QPointF(-s/4, -s/1.8), QPointF(s/4, -s/1.8))

        painter.translate(-cx, -cy)

# ==========================================
# 数据模型与配置管理
# ==========================================
class ConfigManager:
    def __init__(self):
        self.stages = [{"label": "讲解时间", "minutes": 5}, {"label": "问答时间", "minutes": 2}]
        self.alerts = [{"seconds": 30, "color": "#ffaa00"}, {"seconds": 10, "color": "#ff0000"}]
        self.color = "#ffffff"
        self.bg_color = "#19191c"  
        self.font = "Microsoft YaHei UI"
        self.size = 36
        self.opacity = 0.90
        self.auto_hide = True # 新增：控制栏是否自动隐藏
        self.load()

    def load(self):
        if os.path.exists(CONFIG_PATH):
            try:
                with open(CONFIG_PATH, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    self.stages = data.get("stages", self.stages)
                    self.alerts = data.get("alerts", self.alerts)
                    self.color = data.get("color", self.color)
                    self.bg_color = data.get("bg_color", self.bg_color)
                    self.font = data.get("font", self.font)
                    self.size = data.get("size", self.size)
                    self.opacity = data.get("opacity", self.opacity)
                    self.auto_hide = data.get("auto_hide", self.auto_hide)
            except Exception:
                pass

    def save(self):
        data = {
            "stages": self.stages, "alerts": self.alerts, 
            "color": self.color, "bg_color": self.bg_color,
            "font": self.font, "size": self.size, 
            "opacity": self.opacity, "auto_hide": self.auto_hide
        }
        with open(CONFIG_PATH, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=4)

# ==========================================
# 严格捕捉鼠标区域的胶囊体
# ==========================================
class CapsuleWidget(QWidget):
    hover_entered = pyqtSignal()
    hover_left = pyqtSignal()

    def enterEvent(self, e):
        self.hover_entered.emit()
        super().enterEvent(e)

    def leaveEvent(self, e):
        self.hover_left.emit()
        super().leaveEvent(e)

# ==========================================
# 现代化的悬浮倒计时条
# ==========================================
class ModernFloatBar(QMainWindow):
    request_setting = pyqtSignal()

    def __init__(self, config: ConfigManager):
        super().__init__()
        self.config = config
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint | Qt.Tool)
        self.setAttribute(Qt.WA_TranslucentBackground)
        
        self.draggable = True
        self.offset = None
        self.current_flash_color = None

        self.init_ui()
        self.setup_animations()
        self.apply_config()

    def init_ui(self):
        self.root_widget = QWidget()
        self.setCentralWidget(self.root_widget)
        self.root_layout = QVBoxLayout(self.root_widget)
        self.root_layout.setContentsMargins(15, 15, 15, 15) 

        self.capsule = CapsuleWidget()
        self.capsule.setObjectName("capsuleWidget")
        self.capsule_layout = QHBoxLayout(self.capsule)
        self.capsule_layout.setContentsMargins(25, 8, 20, 8)
        self.capsule_layout.setSpacing(20)

        shadow = QGraphicsDropShadowEffect(self)
        shadow.setBlurRadius(20)
        shadow.setColor(QColor(0, 0, 0, 100))
        shadow.setOffset(0, 5)
        self.capsule.setGraphicsEffect(shadow)
        self.root_layout.addWidget(self.capsule)

        self.text_container = QWidget()
        text_layout = QHBoxLayout(self.text_container)
        text_layout.setContentsMargins(0, 0, 0, 0)
        text_layout.setSpacing(15) 
        
        self.stage_label = QLabel("准备就绪")
        self.time_label = QLabel("00:00")
        self.stage_label.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        self.time_label.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)
        
        text_layout.addWidget(self.stage_label)
        text_layout.addWidget(self.time_label)

        # ------------------------------------------
        # 重构：工具栏包装器（用于统一做透明度动画，解决位移问题）
        # ------------------------------------------
        self.toolbar_wrapper = QWidget()
        toolbar_layout = QHBoxLayout(self.toolbar_wrapper)
        toolbar_layout.setContentsMargins(0, 0, 0, 0)
        toolbar_layout.setSpacing(20)

        self.separator = QFrame()
        self.separator.setFrameShape(QFrame.VLine)
        self.separator.setStyleSheet("QFrame { border: 1px solid rgba(150, 150, 150, 0.3); }")
        self.separator.setFixedWidth(2)

        self.control_container = QWidget()
        control_layout = QHBoxLayout(self.control_container)
        control_layout.setContentsMargins(0, 0, 0, 0)
        control_layout.setSpacing(8)

        self.btn_toggle = VectorBtn("toggle", "开始 / 暂停")
        self.btn_restart = VectorBtn("restart", "重新开始")
        self.btn_next = VectorBtn("next", "下一阶段")
        self.btn_setting = VectorBtn("setting", "设置")

        self.btn_setting.clicked.connect(self.request_setting.emit)

        self.buttons = [self.btn_toggle, self.btn_restart, self.btn_next, self.btn_setting]
        for btn in self.buttons:
            control_layout.addWidget(btn)

        toolbar_layout.addWidget(self.separator)
        toolbar_layout.addWidget(self.control_container)

        self.capsule_layout.addWidget(self.text_container)
        self.capsule_layout.addWidget(self.toolbar_wrapper) # 统一放入Wrapper

        self.setContextMenuPolicy(Qt.CustomContextMenu)
        self.customContextMenuRequested.connect(self.show_context_menu)

    def setup_animations(self):
        # 动画作用于完整的包装器，不再使用 hide()/show()
        self.opacity_effect = QGraphicsOpacityEffect(self.toolbar_wrapper)
        self.opacity_effect.setOpacity(0.0)
        self.toolbar_wrapper.setGraphicsEffect(self.opacity_effect)
        
        # 初始不可见时鼠标穿透
        self.toolbar_wrapper.setAttribute(Qt.WA_TransparentForMouseEvents, True)
        
        self.anim = QPropertyAnimation(self.opacity_effect, b"opacity")
        self.anim.setDuration(200)

        self.capsule.hover_entered.connect(lambda: self.fade_controls(1.0))
        self.capsule.hover_left.connect(lambda: self.fade_controls(0.0))

        self.flash_timer = QTimer(self)
        self.flash_timer.timeout.connect(self.toggle_flash)
        self.flash_state = False

    def apply_config(self):
        rgba_bg = hex_to_rgba(self.config.bg_color, self.config.opacity)
        self.capsule.setStyleSheet(f"""
            QWidget#capsuleWidget {{
                background-color: {rgba_bg};
                border-radius: 22px;
            }}
        """)

        for btn in self.buttons:
            btn.set_base_color(self.config.color)

        stage_font_size = max(18, int(self.config.size * 0.55)) 
        c = QColor(self.config.color)
        stage_color_rgba = f"rgba({c.red()}, {c.green()}, {c.blue()}, 0.85)"

        self.stage_label.setStyleSheet(f"""
            color: {stage_color_rgba}; 
            font-family: "{self.config.font}";
            font-size: {stage_font_size}px; 
            font-weight: bold; 
            background: transparent;
        """)
        self.time_label.setStyleSheet(f"""
            color: {self.config.color}; 
            font-family: "{self.config.font}";
            font-size: {self.config.size}px; 
            font-weight: 900; 
            background: transparent;
        """)
        
        # 初始化是否显示控制栏
        if self.config.auto_hide:
            if not self.capsule.underMouse():
                self.fade_controls(0.0)
            else:
                self.fade_controls(1.0)
        else:
            self.fade_controls(1.0)

        self.capsule.adjustSize()
        self.adjustSize()

    def fade_controls(self, target_opacity: float):
        # 如果不自动隐藏，阻止淡出操作
        if not self.config.auto_hide and target_opacity == 0.0:
            return

        if target_opacity > 0:
            self.toolbar_wrapper.setAttribute(Qt.WA_TransparentForMouseEvents, False)
        else:
            self.toolbar_wrapper.setAttribute(Qt.WA_TransparentForMouseEvents, True)

        self.anim.stop()
        self.anim.setStartValue(self.opacity_effect.opacity())
        self.anim.setEndValue(target_opacity)
        self.anim.start()

    def update_display(self, stage: str, time_str: str):
        self.stage_label.setText(stage)
        self.time_label.setText(time_str)

    def start_flash(self, color: str):
        self.current_flash_color = color
        self.flash_timer.start(500)

    def stop_flash(self):
        self.flash_timer.stop()
        self.flash_state = False
        self.apply_config()

    def toggle_flash(self):
        self.flash_state = not self.flash_state
        color = self.current_flash_color if self.flash_state else self.config.color
        self.time_label.setStyleSheet(f"""
            color: {color}; font-family: "{self.config.font}";
            font-size: {self.config.size}px; font-weight: 900; background: transparent;
        """)

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton and self.draggable:
            self.offset = event.globalPos() - self.pos()

    def mouseMoveEvent(self, event):
        if self.offset and event.buttons() == Qt.LeftButton:
            self.move(event.globalPos() - self.offset)

    def show_context_menu(self, pos):
        menu = QMenu()
        menu.setStyleSheet("""
            QMenu { background: #2b2b2b; color: white; border: 1px solid #444; border-radius: 8px; }
            QMenu::item { padding: 10px 25px; margin: 2px 5px; border-radius: 4px; font-size: 14px;}
            QMenu::item:selected { background: #409EFF; }
            QMenu::separator { background: #444; height: 1px; margin: 5px 15px; }
        """)
        menu.addAction("▶ 开始 / ⏸ 暂停").triggered.connect(self.btn_toggle.click)
        menu.addAction("🔄 重新开始").triggered.connect(self.btn_restart.click)
        menu.addAction("⏭ 下一阶段").triggered.connect(self.btn_next.click)
        menu.addSeparator()
        menu.addAction("⚙️ 打开设置").triggered.connect(self.request_setting.emit)
        menu.addAction("❌ 退出程序").triggered.connect(QApplication.quit)
        menu.exec_(self.mapToGlobal(pos))

# ==========================================
# 现代化的设置窗口
# ==========================================
class ModernSettingsWindow(QMainWindow):
    settings_saved = pyqtSignal()

    def __init__(self, config: ConfigManager):
        super().__init__()
        self.config = config
        self.setWindowTitle("⏱️ PPT 计时器设置")
        self.resize(580, 800)
        self.setMinimumSize(500, 600)
        self.setStyleSheet("""
            QMainWindow { background-color: #f5f7fa; }
            QGroupBox { font-weight: bold; border: 1px solid #dcdfe6; border-radius: 8px; margin-top: 12px; background: white; }
            QGroupBox::title { subcontrol-origin: margin; left: 15px; top: -8px; color: #606266; }
            QLabel { color: #303133; font-size: 13px; }
            QPushButton { background-color: #409EFF; color: white; border: none; border-radius: 6px; padding: 8px 15px; }
            QPushButton:hover { background-color: #66b1ff; }
            QPushButton#danger { background-color: #F56C6C; }
            QPushButton#danger:hover { background-color: #f78989; }
            QPushButton#success { background-color: #67C23A; font-weight: bold; }
            QPushButton#success:hover { background-color: #85ce61; }
            QSpinBox, QLineEdit, QFontComboBox { border: 1px solid #dcdfe6; border-radius: 4px; padding: 6px; background: white; }
            QCheckBox { font-size: 13px; color: #303133; }
            QScrollArea { border: none; background: transparent; }
        """)
        self.init_ui()

    def init_ui(self):
        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.setCentralWidget(self.scroll_area)

        central = QWidget()
        self.scroll_area.setWidget(central)
        
        layout = QVBoxLayout(central)
        layout.setSpacing(20)
        layout.setContentsMargins(25, 25, 25, 25)

        g_stage = QGroupBox("📌 计时阶段配置")
        v_stage = QVBoxLayout(g_stage)
        self.stage_layout = QVBoxLayout()
        v_stage.addLayout(self.stage_layout)
        
        btn_add_stage = QPushButton("+ 新增阶段")
        btn_add_stage.clicked.connect(lambda: self.add_stage_row("新阶段", 3))
        v_stage.addWidget(btn_add_stage)
        layout.addWidget(g_stage)

        g_alert = QGroupBox("🔔 倒计时提醒配置")
        v_alert = QVBoxLayout(g_alert)
        self.alert_layout = QVBoxLayout()
        v_alert.addLayout(self.alert_layout)
        
        btn_add_alert = QPushButton("+ 新增提醒")
        btn_add_alert.clicked.connect(lambda: self.add_alert_row(20, "#ffaa00"))
        v_alert.addWidget(btn_add_alert)
        layout.addWidget(g_alert)

        g_style = QGroupBox("🎨 显示样式")
        g = QGridLayout(g_style)
        g.setVerticalSpacing(15)

        self.color_btn = QPushButton("选择文字颜色")
        self.update_btn_color_style(self.color_btn, self.config.color)
        self.color_btn.clicked.connect(self.pick_text_color)
        
        self.bg_color_btn = QPushButton("选择背景颜色")
        self.update_btn_color_style(self.bg_color_btn, self.config.bg_color)
        self.bg_color_btn.clicked.connect(self.pick_bg_color)

        self.font_cmb = QFontComboBox()
        self.font_cmb.setCurrentFont(QFont(self.config.font))
        
        self.size_spin = QSpinBox()
        self.size_spin.setRange(20, 150)
        self.size_spin.setValue(self.config.size)
        
        self.op_slider = QSlider(Qt.Horizontal)
        self.op_slider.setRange(10, 100) 
        self.op_slider.setValue(int(self.config.opacity * 100))

        # 新增控制栏显隐复选框
        self.auto_hide_cb = QCheckBox("自动隐藏控制栏 (仅鼠标悬停时显示)")
        self.auto_hide_cb.setChecked(self.config.auto_hide)

        g.addWidget(QLabel("文字颜色:"), 0, 0)
        g.addWidget(self.color_btn, 0, 1)
        g.addWidget(QLabel("背景颜色:"), 1, 0)
        g.addWidget(self.bg_color_btn, 1, 1)
        g.addWidget(QLabel("背景不透明度:"), 2, 0)
        g.addWidget(self.op_slider, 2, 1)
        g.addWidget(QLabel("字体:"), 3, 0)
        g.addWidget(self.font_cmb, 3, 1)
        g.addWidget(QLabel("时间字号:"), 4, 0)
        g.addWidget(self.size_spin, 4, 1)
        g.addWidget(self.auto_hide_cb, 5, 0, 1, 2) # 跨越两列
        layout.addWidget(g_style)

        h_btn = QHBoxLayout()
        save_btn = QPushButton("✅ 保存并应用")
        save_btn.setObjectName("success")
        save_btn.setMinimumHeight(45)
        save_btn.clicked.connect(self.save_config)
        
        exit_btn = QPushButton("❌ 退出程序")
        exit_btn.setObjectName("danger")
        exit_btn.setMinimumHeight(45)
        exit_btn.clicked.connect(QApplication.quit)
        
        h_btn.addWidget(save_btn)
        h_btn.addWidget(exit_btn)
        layout.addLayout(h_btn)

        self.load_data_to_ui()

    def update_btn_color_style(self, btn, hex_color):
        text_color = get_contrast_color(hex_color)
        btn.setStyleSheet(f"background-color: {hex_color}; color: {text_color}; border: 1px solid #ccc;")

    def add_stage_row(self, name, minutes):
        w = QWidget()
        h = QHBoxLayout(w)
        h.setContentsMargins(0,0,0,0)
        
        le = QLineEdit(name)
        sb = QSpinBox()
        sb.setRange(1, 120)
        sb.setValue(minutes)
        sb.setSuffix(" 分钟")
        
        del_btn = VectorBtn("trash", "删除")
        del_btn.setFixedSize(36, 36)
        del_btn.clicked.connect(lambda: w.deleteLater())

        h.addWidget(le)
        h.addWidget(sb)
        h.addWidget(del_btn)
        self.stage_layout.addWidget(w)

    def add_alert_row(self, seconds, color):
        w = QWidget()
        h = QHBoxLayout(w)
        h.setContentsMargins(0,0,0,0)
        
        sb = QSpinBox()
        sb.setRange(1, 600)
        sb.setValue(seconds)
        sb.setPrefix("剩余 ")
        sb.setSuffix(" 秒")
        
        color_btn = QPushButton("颜色")
        color_btn.color_val = color
        self.update_btn_color_style(color_btn, color)
        
        def pick():
            c = QColorDialog.getColor(QColor(color_btn.color_val))
            if c.isValid():
                color_btn.color_val = c.name()
                self.update_btn_color_style(color_btn, c.name())
                
        color_btn.clicked.connect(pick)

        del_btn = VectorBtn("trash", "删除")
        del_btn.setFixedSize(36, 36)
        del_btn.clicked.connect(lambda: w.deleteLater())

        h.addWidget(sb)
        h.addWidget(color_btn)
        h.addWidget(del_btn)
        self.alert_layout.addWidget(w)

    def load_data_to_ui(self):
        for s in self.config.stages:
            self.add_stage_row(s["label"], s["minutes"])
        for a in self.config.alerts:
            self.add_alert_row(a["seconds"], a["color"])

    def pick_text_color(self):
        c = QColorDialog.getColor(QColor(self.config.color))
        if c.isValid():
            self.config.color = c.name()
            self.update_btn_color_style(self.color_btn, c.name())

    def pick_bg_color(self):
        c = QColorDialog.getColor(QColor(self.config.bg_color))
        if c.isValid():
            self.config.bg_color = c.name()
            self.update_btn_color_style(self.bg_color_btn, c.name())

    def save_config(self):
        stages = []
        for i in range(self.stage_layout.count()):
            w = self.stage_layout.itemAt(i).widget()
            if w:
                le, sb = w.findChildren(QLineEdit)[0], w.findChildren(QSpinBox)[0]
                stages.append({"label": le.text(), "minutes": sb.value()})
        
        alerts = []
        for i in range(self.alert_layout.count()):
            w = self.alert_layout.itemAt(i).widget()
            if w:
                sb, btn = w.findChildren(QSpinBox)[0], w.findChildren(QPushButton)[0]
                alerts.append({"seconds": sb.value(), "color": btn.color_val})

        self.config.stages = stages
        self.config.alerts = alerts
        self.config.font = self.font_cmb.currentFont().family()
        self.config.size = self.size_spin.value()
        self.config.opacity = self.op_slider.value() / 100.0
        self.config.auto_hide = self.auto_hide_cb.isChecked()

        self.config.save()
        self.settings_saved.emit()
        self.hide()

# ==========================================
# 核心逻辑控制器
# ==========================================
class TimerController(QObject):
    def __init__(self, ui: ModernFloatBar, config: ConfigManager):
        super().__init__()
        self.ui = ui
        self.config = config
        
        self.timer = QTimer()
        self.timer.timeout.connect(self.tick)
        
        self.is_running = False
        self.is_paused = False
        self.current_stage_idx = 0
        self.end_time = 0.0
        self.remaining_seconds = 0.0
        self.triggered_alerts = set()

        self.bind_signals()

    def bind_signals(self):
        self.ui.btn_toggle.clicked.connect(self.toggle)
        self.ui.btn_restart.clicked.connect(self.restart)
        self.ui.btn_next.clicked.connect(self.next_stage)

    def toggle(self):
        if not self.is_running:
            self.start_timer()
        else:
            self.is_paused = not self.is_paused
            self.ui.btn_toggle.set_toggle_state(not self.is_paused)
            if self.is_paused:
                self.timer.stop()
            else:
                self.end_time = time.time() + self.remaining_seconds
                self.timer.start(100)

    def start_timer(self):
        if not self.config.stages: return
        self.is_running = True
        self.is_paused = False
        self.current_stage_idx = 0
        self.ui.btn_toggle.set_toggle_state(True)
        self.load_stage()

    def load_stage(self):
        stage = self.config.stages[self.current_stage_idx]
        self.remaining_seconds = stage["minutes"] * 60
        self.end_time = time.time() + self.remaining_seconds
        self.triggered_alerts.clear()
        self.ui.stop_flash()
        self.timer.start(100)
        self.update_ui(stage["label"], self.remaining_seconds)

    def tick(self):
        self.remaining_seconds = self.end_time - time.time()
        stage = self.config.stages[self.current_stage_idx]
        
        if self.remaining_seconds <= 0:
            self.next_stage()
            return

        self.update_ui(stage["label"], self.remaining_seconds)
        self.check_alerts()

    def check_alerts(self):
        sec = int(self.remaining_seconds)
        for a in self.config.alerts:
            if sec == a["seconds"] and sec not in self.triggered_alerts:
                self.triggered_alerts.add(sec)
                self.ui.start_flash(a["color"])
                QApplication.beep()
                QTimer.singleShot(3000, self.ui.stop_flash)

    def update_ui(self, label, seconds):
        secs = max(0, int(seconds))
        mm, ss = divmod(secs, 60)
        self.ui.update_display(label, f"{mm:02d}:{ss:02d}")

    def next_stage(self):
        if not self.is_running: return
        self.current_stage_idx += 1
        if self.current_stage_idx < len(self.config.stages):
            self.load_stage()
        else:
            self.finish()

    def restart(self):
        if not self.is_running: return
        self.load_stage()

    def finish(self):
        self.is_running = False
        self.timer.stop()
        self.ui.update_display("已结束", "00:00")
        self.ui.start_flash("#ff0000")
        self.ui.btn_toggle.set_toggle_state(False)


# ==========================================
# 主程序入口
# ==========================================
if __name__ == "__main__":
    QApplication.setAttribute(Qt.AA_EnableHighDpiScaling, True)
    QApplication.setAttribute(Qt.AA_UseHighDpiPixmaps, True)
    
    app = QApplication(sys.argv)
    app.setStyle("Fusion")

    config = ConfigManager()
    float_bar = ModernFloatBar(config)
    settings_win = ModernSettingsWindow(config)
    controller = TimerController(float_bar, config)

    float_bar.request_setting.connect(settings_win.show)
    settings_win.settings_saved.connect(float_bar.apply_config)

    float_bar.move(100, 100)
    float_bar.show()

    if config.stages:
        float_bar.update_display(config.stages[0]["label"], f"{config.stages[0]['minutes']:02d}:00")

    sys.exit(app.exec_())