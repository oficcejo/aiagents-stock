@echo off
chcp 65001 >nul
setlocal

echo ============================================
echo       智能盯盘系统 - 一键启动
echo ============================================
echo.

set SERVER_EXE=d:\AI\MICC\tdx-api\web\server.exe
set MINI_QMT_EXE=d:\AI\MICC\SMT-Q\bin.x64\XtItClient.exe
set START_BAT=d:\AI\MICC\AIagentsStock\startsytem.bat

echo [步骤 1/3] 启动TDX服务器...
if exist "%SERVER_EXE%" (
    start "TDX Server" "%SERVER_EXE%"
    echo [OK] TDX服务器已启动
) else (
    echo [警告] 未找到 TDX 服务器: %SERVER_EXE%
)
echo 等待 3 秒...
ping -n 4 127.0.0.1 >nul
echo.

echo [步骤 2/3] 启动 MiniQMT 客户端...
if exist "%MINI_QMT_EXE%" (
    start "MiniQMT" "%MINI_QMT_EXE%"
    echo [OK] MiniQMT 客户端已启动
) else (
    echo [警告] 未找到 MiniQMT 客户端: %MINI_QMT_EXE%
)
echo 等待 3 秒...
ping -n 4 127.0.0.1 >nul
echo.

echo [步骤 3/3] 启动智能盯盘系统...
if exist "%START_BAT%" (
    start "Smart Monitor" cmd /c "%START_BAT%"
    echo [OK] 智能盯盘系统已启动
) else (
    echo [错误] 未找到启动脚本: %START_BAT%
)
echo.

echo ============================================
echo       所有服务已启动完成！
echo ============================================
echo.
echo 请在浏览器中访问: http://localhost:8501
echo.
echo 注意：
echo   - MiniQMT 需要登录您的交易账户
echo   - 确保 TDX 服务器正常运行
echo   - 查看浏览器中的系统状态
echo.
endlocal
pause