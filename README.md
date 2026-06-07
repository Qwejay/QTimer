# ⏱️ QTimer - 极简专业桌面悬浮计时器

![Python Version](https://img.shields.io/badge/Python-3.7%2B-blue.svg)
![PyQt5](https://img.shields.io/badge/PyQt5-5.15+-brightgreen.svg)
![Platform](https://img.shields.io/badge/Platform-Windows%20%7C%20macOS-lightgrey.svg)
![License](https://img.shields.io/badge/License-MIT-green.svg)
![Downloads](https://img.shields.io/github/downloads/Qwejay/QTimer/total.svg)
![Stars](https://img.shields.io/github/stars/Qwejay/QTimer.svg)

**QTimer** 是一款专为**说课、答辩、演讲、会议**打造的**极简悬浮桌面计时器**。  
采用无边框半透明设计，平时安静悬浮在屏幕角落，鼠标悬停时丝滑展开控制面板，绝不干扰你的演示。

<img width="249" height="56" alt="image" src="https://github.com/user-attachments/assets/a4857c73-f183-41eb-9590-dcb82608fbae" />
<img width="481" height="56" alt="image" src="https://github.com/user-attachments/assets/776f1907-7564-4124-adb1-16111bd1c302" />
<img width="849" height="637" alt="image" src="https://github.com/user-attachments/assets/1526b17a-358d-41c2-9676-e4ecedcdaf6c" />

---

## 🆕 最新更新 (V1.3.0)

本次更新聚焦于**底层性能优化**与**极致的视觉交互体验**：

- **💎 矢量级超清渲染**：重构了底层 UI 绘制逻辑，完美解决高分屏及大比例缩放下的图标模糊问题，无论放大多少倍，边缘依然极其锐利。
- **🪄 PPT 联动逻辑升级**：修复了退出放映时进度被重置的 Bug。现在按 `Esc` 退出幻灯片，计时器会自动**暂停并完美保留当前剩余时间**，再次放映无缝续播。
- **⚡ 丝滑无级缩放**：加入了 `Ctrl + 滚轮` 全局缩放的防抖熔断机制，大幅降低高频磁盘 I/O，缩放过程丝滑流畅，告别卡顿。
- **🛡️ 智能边界防溢出**：任意比例缩放悬浮窗时，系统会自动进行屏幕边界检测，强行拉回可视区域，再也不用担心面板“飞出屏幕”。
- **✨ 动画冲突修复**：解决了鼠标极速进出或切段时引起的 UI 抽搐问题，动画过渡更稳重。

---

## ✨ 核心特性

- **🖥️ 智能 PPT/WPS 联动**  
  后台自动检测全屏放映模式。开始放映自动倒数，退出放映智能暂停。防误触、免操作，让你专注于演讲本身。

- **🎨 高度自定义的视觉排版**  
  环节名称与时间数字**完全解耦**。支持独立设置不同字体（如行楷+雅黑）、字号、色彩。支持透明度无级调节与极简无字模式。

- **⏱️ 正/倒计时混合编排**  
  支持建立多个任务小节（如：说课5分钟倒数 -> 答辩2分钟正计时）。底层基于绝对时间戳锚定，无论系统多卡顿，倒计时绝对“零漂移”。

- **🔔 多维度智能预警机制**  
  支持自定义多个预警时间节点（如：剩 30 秒变黄，剩 10 秒变红）。倒计时最后 10 秒可开启心跳滴答声，倒数结束伴随系统级清脆蜂鸣。

- **🧲 优秀的桌面交互**  
  始终置顶保护，绝不被其他窗口遮挡；边缘自动磁吸停靠；支持自定义全局快捷键（播放/下一阶段/重置）。

---

## 🚀 快速开始

### 1. 下载运行
https://github.com/Qwejay/QTimer/releases

### 2. 脚本运行
确保您的电脑已安装 Python 3.7 或更高版本。
```bash
# 克隆项目到本地
git clone https://github.com/Qwejay/QTimer.git
cd QTimer

# 安装必要的依赖库
pip install PyQt5

# 运行
python main.py

## 开源协议
### GPL-3.0 license
