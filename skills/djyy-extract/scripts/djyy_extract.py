#!/usr/bin/env python3
"""
DJYY Data 策略提取脚本
用法: python3 djyy_extract.py "策略名称"
示例: python3 djyy_extract.py "Double chance X2 strategy"
"""

import subprocess
import sys
import os

def get_browser_session():
    """启动独立浏览器会话并返回 targetId"""
    import json
    
    result = subprocess.run(
        ['curl', '-s', 'http://127.0.0.1:28800/json/new', '-X', 'POST'],
        capture_output=True, text=True
    )
    if result.returncode == 0:
        try:
            data = json.loads(result.stdout)
            return data.get('id'), data.get('webSocketDebuggerUrl')
        except:
            pass
    return None, None

def run():
    if len(sys.argv) < 2:
        strategy = "Double chance X2 strategy"
    else:
        strategy = sys.argv[1]
    
    print(f"正在提取策略: {strategy}")
    print("请使用浏览器自动化方式执行完整流程")
    print(f"提示: 告知我 '提取 {strategy}' 即可自动执行")

if __name__ == "__main__":
    run()
