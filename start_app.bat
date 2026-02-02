@echo off
REM AI股票分析系统启动批处理脚本
REM 适用于Windows 11环境

echo 🚀 正在启动AI股票分析系统...
echo ==================================================

REM 检查是否在虚拟环境中
if "%VIRTUAL_ENV%"=="" (
    echo 📦 正在激活Python虚拟环境...
    call venv\Scripts\activate.bat
) else (
    echo ✅ 已在虚拟环境中
)

REM 检查app.py是否存在
if not exist app.py (
    echo ❌ 错误: app.py 文件不存在！
    pause
    exit /b 1
)

echo 🌐 正在启动Streamlit应用...
echo 📝 访问地址: http://localhost:8503
echo ⏹️  按 Ctrl+C 停止服务
echo ==================================================

REM 启动Streamlit应用
streamlit run app.py --server.port 8503 --server.address 127.0.0.1

REM 如果出错，暂停以便查看错误信息
if errorlevel 1 (
    echo.
    echo ❌ 启动失败，请检查错误信息
    pause
)

echo.
echo 👋 感谢使用AI股票分析系统！
pause