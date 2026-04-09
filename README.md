# ⏱️ QTimer V1.0.1 - 极简流线型桌面悬浮计时器

![Python Version](https://img.shields.io/badge/Python-3.7+-blue.svg)
![PyQt5](https://img.shields.io/badge/PyQt5-Supported-brightgreen.svg)
![Platform](https://img.shields.io/badge/Platform-Windows%20%7C%20macOS-lightgrey.svg)

**QTimer** 是一款专为**说课、答辩、演讲、会议**等场景打造的桌面悬浮倒计时工具。它采用极简的无边框半透明设计，平时安静地悬浮在屏幕角落，鼠标悬停时如丝滑拉开的抽屉般展示控制面板。

<img width="562" height="126" alt="image" src="https://github.com/user-attachments/assets/c7ec2962-6943-4dfb-9cba-52c817beefcc" />
<img width="1855" height="1048" alt="image" src="https://github.com/user-attachments/assets/94877e2e-cfbc-4038-a7ad-e3bc5330e76f" />

---
## 🆕 最新更新日志 (V1.0.2)

- 🛡️ **修复“抢夺焦点”打断打字的问题**：引入 `Qt.WA_ShowWithoutActivating` 属性，计时器在变色闪烁、自动切换环节时，**绝对处于静默状态**，再也不会打断您在 Word/PPT 等其他软件中的正常输入工作流。
- 🎨 **首创“画布隔离”架构解决文字遮挡**：彻底解除环节名称字数限制。无论输入多长，悬浮条都会智能拉伸。采用“抽屉式裁切”动画取代“强行挤压”，彻底杜绝文字与时间数字重叠的 Bug。
- ⚡ **渲染精度提升**：引入 `style().polish()` 强刷机制，消除 CSS 字重带来的尺寸计算误差。
---

## ✨ 核心特性

- 🎯 **无误差精准计时 (Drift-Free Engine)**
  - 彻底抛弃传统的“累加扣减”计时法。底层采用**绝对系统时间戳锚定**技术，即使你的电脑瞬间卡顿或 UI 线程阻塞，倒计时也绝对不会产生哪怕 1 秒的误差。
- 🎨 **自适应防挤压 UI (Canvas Masking)**
  - 无论你输入的环节名称有多长（哪怕是一首诗），首创的“底层画布隔离”机制确保文字与倒计时数字绝对不会发生重叠或挤压。配合 QPropertyAnimation 带来极致丝滑的折叠/展开动画。
- 🔄 **多阶段无缝流转**
  - 支持自定义多个流程（如：说课 5 分钟 ➔ 答辩 2 分钟）。可开启**自动流转**模式，倒计时结束自动无缝衔接下一个环节。
- 🔔 **多线程智能提醒**
  - **原生系统音效**：支持 Windows (`winsound`) 和 macOS (`afplay`)，采用独立守护线程异步播放声音，绝对不卡主界面。
  - **动态变色闪烁**：可自定义时间节点（如剩余 30 秒变黄，剩余 10 秒变红并伴随最后 10 秒倒数滴答声）。
- ⚙️ **高度可定制化**
  - 自定义文字颜色、背景颜色、透明度、字体风格及时间字号。
  - 配置自动保存至本地 (`~/.qtimer_config.json`)，下一次打开保留所有习惯。
- ⌨️ **快捷键支持**
  - 支持自定义全局快捷键（播放/暂停、重置、上一阶段、下一阶段）。*(注：需窗口处于焦点时生效)*

---

## 🚀 快速开始

### 1. 环境依赖

确保您的电脑已安装 Python 3.7 或更高版本。

安装必须的依赖库 PyQt5：
```bash
pip install PyQt5
