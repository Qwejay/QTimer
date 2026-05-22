# ⏱️ QTimer - 极简专业桌面悬浮计时器

![Python Version](https://img.shields.io/badge/Python-3.7%2B-blue.svg)
![PyQt5](https://img.shields.io/badge/PyQt5-5.15+-brightgreen.svg)
![Platform](https://img.shields.io/badge/Platform-Windows%20%7C%20macOS-lightgrey.svg)
![License](https://img.shields.io/badge/License-MIT-green.svg)
![Downloads](https://img.shields.io/github/downloads/Qwejay/QTimer/total.svg)
![Stars](https://img.shields.io/github/stars/Qwejay/QTimer.svg)

**QTimer** 是一款专为**说课、答辩、演讲、会议**打造的**极简悬浮桌面计时器**。  
采用无边框半透明设计，平时安静悬浮在屏幕角落，鼠标悬停时丝滑展开控制面板，绝不干扰你的演示。

---

## ✨ 核心特性

- **🎨 独立字体设置**（V1.2.0 新增）  
  环节名称与时间数字可**完全独立**设置字体和大小（支持行楷、微软雅黑等任意系统字体）。

- **🪄 PPT 智能自动启动**  
  自动检测 PowerPoint / WPS 全屏放映模式，瞬间自动开始计时（智能防误触）。

- **⏱️ 正/倒计时混合编排**  
  每个环节可独立选择正计时或倒计时，底层使用绝对时间戳锚定，零漂移。

- **🖥️ 窗口行为优化**  
  支持始终置顶 + 防止移出屏幕 + 一键隐藏环节名称（极简无字模式）。

- **🔔 多维度智能提醒**  
  自定义时间节点高亮闪烁 + 原生系统提示音（Windows/macOS 完美适配）。

- **⚡ 极致流畅体验**  
  丝滑动画、单例锁、焦点防抢夺、高 DPI 支持、便携模式。

---

## 🆕 最新更新 (V1.2.0)

- **重大升级**：环节名称与时间独立字体/大小设置
- 设置界面全面美化（卡片式、专业留白）
- 优化配置保存逻辑与兼容性
- 打包体验优化（Nuitka 推荐）

---

## 🚀 快速开始

### 1. 安装依赖
```bash
pip install PyQt5
