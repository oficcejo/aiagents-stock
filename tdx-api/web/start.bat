@echo off
chcp 65001 >nul
echo ========================================
echo   股票数据查询Web系统
echo ========================================
echo.
echo 正在启动服务器...
echo.

cd /d %~dp0
go run server.go

pause

