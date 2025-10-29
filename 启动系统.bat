@echo off
set VENV_PATH=.\TradEnv
set PYTHON_EXE="%VENV_PATH%\python.exe"
set STREAMLIT_MODULE="streamlit.cli"
cd /d ..\AIagentsStock
%PYTHON_EXE% -m streamlit run app.py
pause