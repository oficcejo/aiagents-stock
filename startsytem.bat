@echo off
chcp 65001 >nul
setlocal

set VENV_PATH=%~dp0TradEnv
set PYTHON_EXE="%VENV_PATH%\python.exe"

if not exist %PYTHON_EXE% (
    echo [错误] 未找到Python解释器: %PYTHON_EXE%
    echo 请确保TradEnv目录存在
    pause
    exit /b 1
)

echo [INFO] 启动智能盯盘系统...
echo [INFO] 工作目录: %cd%
echo [INFO] Python路径: %PYTHON_EXE%

%PYTHON_EXE% -m streamlit run "%~dp0app.py"

if errorlevel 1 (
    echo [错误] 系统启动失败
    pause
    exit /b 1
)

endlocal
pause