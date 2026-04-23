# ⏱️ QTimer V1.0.3 - 极简流线型桌面悬浮计时器 (Final Release)

![Python Version](https://img.shields.io/badge/Python-3.7+-blue.svg)
![PyQt5](https://img.shields.io/badge/PyQt5-Supported-brightgreen.svg)
![Platform](https://img.shields.io/badge/Platform-Windows%20%7C%20macOS-lightgrey.svg)
![High DPI](https://img.shields.io/badge/High%20DPI-4K%2F2K%20Ready-ff69b4.svg)
![Portable](https://img.shields.io/badge/Portable-Supported-orange.svg)

**QTimer** 是一款专为**说课、答辩、演讲、会议**等场景打造的桌面悬浮倒计时工具。它采用极简的无边框半透明设计，平时安静地悬浮在屏幕角落，鼠标悬停时如丝滑拉开的抽屉般展示控制面板。

<img width="562" height="126" alt="image" src="https://github.com/user-attachments/assets/c7ec2962-6943-4dfb-9cba-52c817beefcc" />
<img width="1855" height="1048" alt="image" src="https://github.com/user-attachments/assets/94877e2e-cfbc-4038-a7ad-e3bc5330e76f" />

---

## 🆕 最新更新日志 (Final Release V1.0.3)

- 🔒 **工业级程序单例锁 (Single Instance Lock)**：引入 `QSharedMemory` 共享内存技术，彻底阻止程序多开导致的悬浮条重叠和快捷键冲突问题，重复启动会自动静默退出。
- 💾 **原子化保存与便携模式 (Portable & Atomic Save)**：配置默认保存在程序同级目录，方便打包放进 U 盘带走！加入**原子级写入**防断电损毁机制，并具备**权限智能降级**功能（在 C 盘系统目录无权限时，自动降级保存至 User 目录，杜绝崩溃）。
- 🖥️ **原生高分屏完美适配 (High DPI Ready)**：全面启用 Qt 高抗锯齿与缩放引擎，在 4K/2K 显示器下，无论字号多大，文字与图标依然如剃刀般锐利，拒绝发虚与比例错位。
- ⚡ **SVG 图标内存缓存池**：大幅优化底层渲染逻辑，相同的 SVG 图标尺寸和颜色只渲染一次并常驻内存，彻底消除高频重绘带来的 CPU 开销，悬浮伸缩动画如丝般顺滑。
- 🛡️ **焦点防抢夺机制**：引入 `Qt.WA_ShowWithoutActivating` 属性，计时器在变色闪烁、自动切换环节时，**绝对处于静默状态**，再也不会打断您在 Word/PPT 等软件中的打字流。
- 🎨 **首创“画布隔离”架构解决文字遮挡**：解除环节名称字数限制。采用“抽屉式裁切”动画取代“强行挤压”，绝对杜绝文字与时间数字重叠 Bug。

---

## ✨ 核心特性

- 🎯 **无误差精准计时 (Drift-Free Engine)**
  - 彻底抛弃传统的“累加扣减”计时法。底层采用**绝对系统时间戳锚定**技术，即使你的电脑瞬间卡顿或 UI 线程阻塞，倒计时也绝对不会产生哪怕 1 秒的误差。
- 🎨 **自适应防挤压 UI (Canvas Masking)**
  - 无论你输入的环节名称有多长（哪怕是一首诗），首创的“底层画布隔离”机制确保文字与倒计时数字绝对不会发生重叠。配合 `QPropertyAnimation` 带来极致丝滑的折叠/展开动画。
- 🔄 **多阶段无缝流转**
  - 支持自定义多个流程（如：说课 5 分钟 ➔ 答辩 2 分钟）。可开启**自动流转**模式，倒计时结束自动无缝衔接下一个环节。
- 🔔 **多线程智能提醒**
  - **原生系统音效**：支持 Windows (`winsound`) 和 macOS (`afplay`)，采用独立守护线程异步播放声音，绝对不卡主界面。支持全局声音一键总控。
  - **动态变色闪烁**：可自定义时间节点（如剩余 30 秒变黄，剩余 10 秒变红并伴随最后 10 秒倒数滴答声）。
- ⚙️ **高度可定制化**
  - 自定义文字颜色、背景颜色、透明度、字体风格及时间字号。
  - 实时预览色彩与排版，退出程序绝对无僵尸进程残留。
- ⌨️ **快捷键支持**
  - 支持自定义全局快捷键（播放/暂停、重置、上一阶段、下一阶段）。*(注：受系统级安全限制，需鼠标点击激活面板时生效)*

---

## 🚀 快速开始

### 1. 环境依赖

确保您的电脑已安装 Python 3.7 或更高版本。

安装必须的依赖库 PyQt5：
```bash
pip install PyQt5
