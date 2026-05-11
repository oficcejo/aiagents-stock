@echo off
chcp 65001 >nul
echo ========================================
echo   TDX股票数据查询系统 - Docker版
echo ========================================
echo.

REM 检查Docker是否安装
docker --version >nul 2>&1
if errorlevel 1 (
    echo [错误] 未检测到Docker，请先安装Docker Desktop
    echo.
    echo 下载地址: https://www.docker.com/products/docker-desktop/
    echo.
    pause
    exit /b 1
)

echo [√] Docker已安装
echo.

REM 检查Docker是否运行
docker ps >nul 2>&1
if errorlevel 1 (
    echo [错误] Docker未运行，请先启动Docker Desktop
    echo.
    pause
    exit /b 1
)

echo [√] Docker正在运行
echo.

REM 检查docker-compose是否可用
docker-compose --version >nul 2>&1
if errorlevel 1 (
    echo [错误] docker-compose不可用
    echo.
    pause
    exit /b 1
)

echo [√] docker-compose可用
echo.

echo ----------------------------------------
echo 正在构建并启动服务...
echo ----------------------------------------
echo.

REM 启动服务
docker-compose up -d

if errorlevel 1 (
    echo.
    echo [错误] 启动失败，请查看上面的错误信息
    echo.
    pause
    exit /b 1
)

echo.
echo ========================================
echo   启动成功！
echo ========================================
echo.
echo 访问地址: http://localhost:8080
echo.
echo 常用命令:
echo   查看日志: docker-compose logs -f
echo   停止服务: docker-compose stop
echo   重启服务: docker-compose restart
echo   完全清理: docker-compose down
echo.
echo ----------------------------------------

REM 等待3秒
timeout /t 3 /nobreak >nul

REM 自动打开浏览器
start http://localhost:8080

echo.
echo 浏览器已打开，请稍候...
echo.
pause

