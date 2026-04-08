@echo off
setlocal enabledelayedexpansion
chcp 65001 >nul 2>&1

:: ================= 配置区域 =================
:: 源代码文件名 (请确保 Python 文件名为此名字)
set "SOURCE_FILE=QTimer.py"

:: 生成的 exe 名称
set "EXE_NAME=QTimer"

:: 虚拟环境文件夹名称
set "VENV_DIR=build_env"
:: ===========================================

echo ========================================================
echo        正在启动纯净构建环境 (Clean Build Env)
echo ========================================================

:: 1. 检查 Python 是否安装
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [错误] 未检测到 Python，请确保已安装 Python 并添加到 PATH 环境变量。
    pause
    exit /b
)

:: 2. 检查源文件是否存在
if not exist "%SOURCE_FILE%" (
    echo [错误] 找不到源文件: %SOURCE_FILE%
    echo 请将此脚本放在与 py 文件同一目录下，或修改脚本中的 SOURCE_FILE 变量。
    pause
    exit /b
)

:: 3. 创建/激活虚拟环境
if not exist "%VENV_DIR%" (
    echo [1/4] 正在创建隔离的虚拟环境，请稍候...
    python -m venp %VENV_DIR%
) else (
    echo [1/4] 检测到已有虚拟环境，跳过创建...
)

echo [2/4] 激活环境并安装依赖库...
call %VENV_DIR%\Scripts\activate.bat

:: 检查并使用清华源安装依赖
if exist "requirements.txt" (
    pip install -r requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple
) else (
    echo [警告] 找不到 requirements.txt，将尝试直接安装基础依赖...
    pip install pyinstaller PyQt5 -i https://pypi.tuna.tsinghua.edu.cn/simple
)

:: 4. 开始构建
echo.
echo [3/4] 开始打包 (PyInstaller)...

:: 智能检测图标：如果有 icon.ico，则加入图标参数
set "ICON_CMD="
if exist "icon.ico" (
    set "ICON_CMD=--icon=icon.ico"
    echo [提示] 检测到 icon.ico，将作为程序图标注入。
)

:: 智能检测版本文件：如果有 version.txt，则加入版本信息参数
set "VERSION_CMD="
if exist "version.txt" (
    set "VERSION_CMD=--version-file=version.txt"
    echo [提示] 检测到 version.txt，将注入右键属性详细信息。
)

:: 参数说明:
:: -F: 生成单文件 (Onefile)
:: -w: 无控制台窗口 (Windowed/Noconsole)
:: --clean: 清理缓存
:: --noconfirm: 不询问直接覆盖
:: -n: 指定生成文件名
pyinstaller -F -w --clean --noconfirm -n "%EXE_NAME%" !ICON_CMD! !VERSION_CMD! "%SOURCE_FILE%"

if %errorlevel% neq 0 (
    echo.
    echo [失败] 构建过程中出现错误。
    call %VENV_DIR%\Scripts\deactivate.bat
    pause
    exit /b
)

:: 5. 清理垃圾文件
echo.
echo [4/4] 正在清理构建垃圾与销毁虚拟环境...
call %VENV_DIR%\Scripts\deactivate.bat

:: 删除 build 文件夹
if exist build rd /s /q build
:: 删除 spec 文件
if exist "%EXE_NAME%.spec" del "%EXE_NAME%.spec"
:: 删除 __pycache__ 文件夹
for /d /r . %%d in (__pycache__) do @if exist "%%d" rd /s /q "%%d"
:: 删除 .pyc 文件
for /r . %%f in (*.pyc) do @if exist "%%f" del /f /q "%%f"
:: 删除虚拟环境，保证彻底无痕
if exist %VENV_DIR% rd /s /q %VENV_DIR%

echo.
echo ========================================================
echo              构建成功! (Build Success)
echo.
echo  可执行文件位置:  dist\%EXE_NAME%.exe
echo ========================================================
echo.

pause