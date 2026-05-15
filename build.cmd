@echo off
setlocal enabledelayedexpansion
chcp 65001 >nul 2>&1

:: ================= 配置区域 =================
set "SOURCE_FILE=QTimer.py"
set "EXE_NAME=QTimer"
set "VENV_DIR=build_env"
:: ===========================================

echo ========================================================
echo        QTimer Nuitka 纯净构建 (Clean Build Env)
echo ========================================================

python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [错误] 未检测到 Python，请确保已安装并加入 PATH。
    pause
    exit /b
)

if not exist "%SOURCE_FILE%" (
    echo [错误] 找不到 %SOURCE_FILE%
    pause
    exit /b
)

if not exist "%VENV_DIR%" (
    echo [1/4] 创建纯净虚拟环境...
    python -m venv %VENV_DIR%
)

echo [2/4] 激活环境并安装依赖...
call %VENV_DIR%\Scripts\activate.bat
python -m pip install --upgrade pip
pip install nuitka ordered-set PyQt5 -i https://pypi.tuna.tsinghua.edu.cn/simple

echo [3/4] 开始 Nuitka 打包...
python -m nuitka ^
    --standalone ^
    --onefile ^
    --windows-console-mode=disable ^
    --enable-plugin=pyqt5 ^
    --include-package=PyQt5 ^
    --windows-icon-from-ico=icon.ico ^
    --product-name="QTimer" ^
    --product-version=1.1.0 ^
    --file-description="一款极简风格计时器" ^
    --copyright="QwejayHuang" ^
    --output-dir=dist ^
    --clean-cache=all ^
    --assume-yes-for-downloads ^
    %SOURCE_FILE%

if %errorlevel% == 0 (
    echo [4/4] 打包成功！
    echo 输出: dist\%EXE_NAME%.exe
    explorer dist
) else (
    echo [错误] 打包失败
)

call %VENV_DIR%\Scripts\deactivate.bat 2>nul
echo 按任意键退出...
pause
