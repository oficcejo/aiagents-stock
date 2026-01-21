# -*- coding: utf-8 -*-
"""
申请开通QMT请添加微信咨询gjquant，获取更多资料访问https://miniqmt.com/
此代码脚本仅用于软件测试，不能用于实盘交易，以此代码进行交易本人不承担任何损失
"""
import sys
import os
import subprocess
import importlib

# ================================
# 第一步：检查并安装必需的第三方包
# ================================

REQUIRED_PACKAGES = ['psutil', 'xtquant']

def ensure_packages_installed():
    """检查并安装所需的第三方包"""
    for package in REQUIRED_PACKAGES:
        try:
            importlib.import_module(package)
            print(f"✅ {package} 已安装")
        except ImportError:
            print(f"⚠️ 未找到 {package}，正在安装...")
            try:
                subprocess.check_call([
                    sys.executable, "-m", "pip", "install", package
                ])
                print(f"✅ {package} 安装成功")
            except subprocess.CalledProcessError as e:
                print(f"❌ 安装 {package} 失败，请手动执行: pip install {package}")
                sys.exit(1)

# --- 在导入其他模块前先确保依赖存在 ---
print(" 🔍 正在检查依赖环境...\n","📘 更多资料访问miniqmt.com")
ensure_packages_installed()

# === 现在可以安全导入第三方库 ===
import psutil
import ctypes
from ctypes import wintypes

# -----------------------------
# 1. 检查 xtquant 模块
# -----------------------------
def check_xtquant():
    """检查 xtquant 模块是否安装并获取版本"""
    try:
        xtquant = importlib.import_module('xtquant')
        print("xtquant: ✅ 已安装")
        
        # 尝试获取版本信息
        version = "未知版本"
        try:
            # 尝试通过importlib.metadata获取
            from importlib.metadata import version as md_version
            version = md_version('xtquant')
        except ImportError:
            # 回退到模块属性
            if hasattr(xtquant, '__version__'):
                version = xtquant.__version__
            else:
                # 尝试获取文件版本信息
                try:
                    version = get_module_file_version(xtquant)
                except Exception:
                    pass
        
        print(f"xtquant 版本: {version}")
        return True
    except ImportError as e:
        print(f"xtquant: ❌ 未安装 ({e})")
        return False

def get_module_file_version(module):
    """尝试从模块文件属性获取版本信息"""
    file_path = module.__file__
    if file_path.endswith('.pyc'):
        file_path = file_path[:-1]  # 转换为.py文件
    
    if os.path.exists(file_path):
        # 读取文件内容查找版本信息
        with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
            for line in f:
                if '__version__' in line:
                    parts = line.split('=')
                    if len(parts) > 1:
                        return parts[1].strip().strip("'\"")
    
    # 尝试获取文件修改时间作为替代
    mtime = os.path.getmtime(file_path)
    from datetime import datetime
    return f"文件修改时间: {datetime.fromtimestamp(mtime).strftime('%Y-%m-%d')}"

# -----------------------------
# 2. Windows API：获取指定 PID 的窗口标题
# -----------------------------
user32 = ctypes.WinDLL('user32', use_last_error=True)

user32.GetWindowThreadProcessId.argtypes = (wintypes.HWND, ctypes.POINTER(wintypes.DWORD))
user32.GetWindowTextLengthW.argtypes = (wintypes.HWND,)
user32.GetWindowTextW.argtypes = (wintypes.HWND, wintypes.LPWSTR, ctypes.c_int)
user32.EnumWindows.argtypes = (ctypes.WINFUNCTYPE(ctypes.c_bool, wintypes.HWND, wintypes.LPARAM), wintypes.LPARAM)

def get_window_title_by_pid(pid):
    """枚举所有窗口，找到属于指定 PID 的主窗口标题"""
    titles = []

    def callback(hwnd, lParam):
        pid_ptr = wintypes.DWORD()
        user32.GetWindowThreadProcessId(hwnd, ctypes.byref(pid_ptr))
        if pid_ptr.value == pid:
            length = user32.GetWindowTextLengthW(hwnd)
            if length > 0:
                buffer = ctypes.create_unicode_buffer(length + 1)
                user32.GetWindowTextW(hwnd, buffer, length + 1)
                title = buffer.value.strip()
                if title:
                    titles.append(title)
        return True

    WNDENUMPROC = ctypes.WINFUNCTYPE(ctypes.c_bool, wintypes.HWND, wintypes.LPARAM)
    user32.EnumWindows(WNDENUMPROC(callback), 0)
    return titles[0] if titles else None

# -----------------------------
# 3. 获取 miniQMT 安装/运行状态
# -----------------------------
def get_miniqmt_info():
    """检查 miniQMT 是否运行，返回安装目录和窗口标题"""
    for proc in psutil.process_iter(['name', 'exe', 'pid']):
        if proc.info['name'] == 'XtMiniQmt.exe':
            try:
                exe_path = proc.info['exe']
                pid = proc.info['pid']
                install_dir = os.path.dirname(exe_path)
                window_title = get_window_title_by_pid(pid)
                return {
                    'install_dir': install_dir,
                    'process_name': window_title or f"XtMiniQmt.exe (PID: {pid})",
                    'status': 'running'
                }
            except (psutil.NoSuchProcess, psutil.AccessDenied, OSError):
                continue

    # 快捷方式 fallback（可选）
    shortcut_name = "国金证券QMT交易端.lnk"
    desktop = os.path.expanduser("~/Desktop")
    shortcut_path = os.path.join(desktop, shortcut_name)
    
    if os.path.exists(shortcut_path):
        target = get_target_from_shortcut(shortcut_path)
        if target and os.path.exists(target):
            install_dir = os.path.dirname(target)
            return {
                'install_dir': install_dir,
                'process_name': '未运行',
                'status': 'installed'
            }

    return {
        'install_dir': '未找到',
        'process_name': '未运行',
        'status': 'not_found'
    }

# -----------------------------
# 4. 解析快捷方式目标
# -----------------------------
def get_target_from_shortcut(lnk_path):
    cmd = f'powershell -command "$s=(New-Object -ComObject WScript.Shell).CreateShortcut(\'{lnk_path}\'); $s.TargetPath"'
    try:
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=5)
        return result.stdout.strip() if result.returncode == 0 else None
    except Exception:
        return None

# -----------------------------
# 5. 提取账户名（从窗口标题）
# -----------------------------
def extract_account_from_title(title):
    """从窗口标题提取账号，例如 '55011888 - 国金QMT交易端模拟 1.0.0.36251'"""
    if title and ' - ' in title:
        account = title.split(' - ')[0].strip()
        if account.isdigit():
            return account
    return None

# -----------------------------
# 6. 保存 path.txt
# -----------------------------
def save_path_file(install_dir, account):
    """生成 path.txt，路径替换 bin.x64 -> userdata_mini"""
    try:
        base_dir = os.path.dirname(install_dir.rstrip('\\/'))
        userdata_path = os.path.join(base_dir, "userdata_mini")
        
        # 写入文件
        with open('path.txt', 'w', encoding='utf-8') as f:
            f.write(f"{userdata_path}\n")
            f.write(f"{account}\n")
        
        print(f"✅ 已生成环境配置所需文件 path.txt：\n   {userdata_path}\n   {account}")
    except Exception as e:
        print(f"❌ 保存 path.txt 失败: {e}")

# -----------------------------
# 7. 主函数
# -----------------------------
def main():
    print("=" * 50)
    print("🔍 开始检查运行环境")
    print("=" * 50)
    
    # 输出Python环境信息
    print(f"Python版本: {sys.version.split()[0]}")
    print(f"Python路径: {sys.executable}")
    print(f"运行路径: {os.getcwd()}")
    
    # 检查模块
    print("\n" + "=" * 50)
    print("📦 xtquant 模块检查")
    print("=" * 50)
    xtquant_ok = check_xtquant()

    # 获取 miniQMT 状态
    print("\n" + "=" * 50)
    print("📊 miniQMT 终端状态")
    print("=" * 50)

    miniqmt = get_miniqmt_info()
    status_map = {
        'running': '🟢 运行中',
        'installed': '🟡 已安装（未运行）',
        'not_found': '🔴 未找到'
    }

    print(f"miniQMT路径: {miniqmt['install_dir']}")
    print(f"miniQMT窗口: {miniqmt['process_name']}")
    print(f"状态: {status_map.get(miniqmt['status'], '未知')}")

    # 建议与保存逻辑
    print("\n" + "=" * 50)
    print("💡 环境检测配置")
    print("=" * 50)

    if miniqmt['status'] == 'not_found':
        print("⚠️ 未找到 miniQMT，是否登录软件？\n⚠️ 请在登录QMT终端时勾选'独立交易'。")
    elif not xtquant_ok:
        print("⚠️ xtquant 模块未安装 ")
    elif miniqmt['status'] == 'running':
        account = extract_account_from_title(miniqmt['process_name'])
        if account:
            print("✅ 环境准备就绪，可以开始使用 miniQMT 量化开发！")
            print("📘 更多资料请访问：https://miniqmt.com")
            # 保存 path.txt
            save_path_file(miniqmt['install_dir'], account)
        else:
            print("⚠️ 已运行 但未登录，请检查miniQMT终端状态是否已经登录账户。")
            print("✅ 环境正常，但未检测到登录账户，未生成环境文档 path.txt")
    else:
        print("🟡 miniQMT 已安装但未运行。")
        print("⚠️ 请先启动 miniQMT 登录交易。")

if __name__ == "__main__":
    main()