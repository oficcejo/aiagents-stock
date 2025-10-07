# 1. 删除带 \r 的旧文件
rm -f /www/wwwroot/aiagents-stock/stm /www/wwwroot/aiagents-stock/stm.py

# 2. 重新写入（纯 Unix 换行）
cat > /www/wwwroot/aiagents-stock/stm << 'EOF'
#!/usr/bin/env python3
import os, time, signal, subprocess, psutil

APP_NAME  = "app.py"
VENV_PATH = "/www/wwwroot/aiagents-stock/venv"
APP_PATH  = "/www/wwwroot/aiagents-stock"
PORT      = 8501
STR = os.path.join(VENV_PATH, "bin", "streamlit")
LOG = os.path.join(APP_PATH, "app.log")

def is_run():
    for p in psutil.process_iter(['cmdline']):
        if p.info['cmdline'] and 'streamlit' in ' '.join(p.info['cmdline']) and 'run' in p.info['cmdline']:
            return p.pid
    return None

def start():
    if is_run():
        print("⚠️  已在运行"); return
    os.chdir(APP_PATH)
    with open(LOG, "a") as f:
        subprocess.Popen(["nohup", STR, "run", APP_NAME,
                          "--server.port", str(PORT),
                          "--server.address", "0.0.0.0",
                          "--server.headless", "true"],
                         stdout=f, stderr=f, preexec_fn=os.setsid)
    time.sleep(3)
    print("✅ 启动成功 | http://服务器IP:8501")

def stop():
    pid = is_run()
    if not pid:
        print("⚠️  未运行"); return
    os.kill(pid, signal.SIGTERM)
    time.sleep(2)
    if is_run():
        os.kill(pid, signal.SIGKILL)
    print("✅ 已停止")

menu = """1) 启动  2) 停止  3) 重启  4) 状态  5) 日志  0) 退出"""
def main():
    while True:
        print(menu)
        c = input("选 > ").strip()
        if c == '1': start()
        elif c == '2': stop()
        elif c == '3': stop(); time.sleep(2); start()
        elif c == '4':
            pid = is_run()
            print("✅ 运行中" if pid else "❌ 未运行")
        elif c == '5': os.system("tail -n 50 " + LOG)
        elif c == '0': break
        else: print("无效")
        input("\n回车继续 …")

if __name__ == "__main__": main()
EOF

# 3. 赋可执行权限
chmod +x /www/wwwroot/aiagents-stock/stm

# 4. 确保 PATH 包含当前目录（已加可忽略）
echo 'export PATH="/www/wwwroot/aiagents-stock:$PATH"' >> ~/.bashrc
source ~/.bashrc

# 5. 运行
stm