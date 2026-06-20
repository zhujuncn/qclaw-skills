#!/usr/bin/env python3
"""
FlashScore 数据抓取器

通过 xbrowser 从 FlashScore 提取比赛数据并解析为结构化输出。
依赖: xbrowser skill (CfT 浏览器)
"""

import subprocess
import json
import re
import sys
import os

# 路径配置
NODE_CMD = r'C:\Program Files\QClaw\resources\openclaw\config\bin\node.cmd'
XB_PATH = os.path.join(os.path.dirname(__file__), '..', '..', 'xbrowser', 'scripts', 'xb.cjs')
if not os.path.exists(XB_PATH):
    # Fallback to managed skill path
    XB_PATH = r'C:\Users\zhuju\.qclaw\skills\xbrowser\scripts\xb.cjs'

PARSE_SCRIPT = os.path.join(os.path.dirname(__file__), 'parse_flashscore.py')


def xb_run(args: list[str], timeout: int = 30) -> dict:
    """运行 xb 命令并返回 JSON 结果"""
    cmd = [NODE_CMD, XB_PATH, 'run', '--browser', 'default'] + args
    result = subprocess.run(
        cmd, capture_output=True, text=True, timeout=timeout, encoding='utf-8'
    )
    try:
        return json.loads(result.stdout)
    except json.JSONDecodeError:
        return {'ok': False, 'error': result.stdout[:500]}


def extract_text() -> str:
    """从 FlashScore 页面提取 innerText"""
    data = xb_run(['eval', "document.querySelector('#live-table').innerText"])
    if not data.get('ok'):
        raise RuntimeError(f"提取失败: {data.get('error', 'unknown')}")

    result_str = json.dumps(data)
    # 正则提取 result 字段（可能含特殊字符导致 JSON 解析失败）
    match = re.search(r'"result"\s*:\s*"((?:[^"\\]|\\.)*)"', result_str)
    if not match:
        raise RuntimeError("无法从返回数据中提取文本")

    text = match.group(1)
    text = text.replace('\\n', '\n').replace('\\t', '\t').replace('\\"', '"')
    return text


def open_flashscore(url: str = 'https://www.flashscore.com/football/') -> None:
    """打开 FlashScore 页面"""
    xb_run(['open', url])
    xb_run(['wait', '--load', 'networkidle'])


def dismiss_cookie_banner() -> None:
    """尝试关闭 Cookie 弹窗"""
    snap = xb_run(['snapshot', '-i', '-c'])
    if not snap.get('ok'):
        return

    snap_text = json.dumps(snap)
    # 查找 Reject / Accept 按钮
    for keyword in ['Reject', 'reject', 'Accept', 'accept']:
        ref_match = re.search(rf'"{keyword}[^"]*".*?ref=(e\d+)', snap_text)
        if ref_match:
            xb_run(['click', f'@{ref_match.group(1)}'])
            break


def fetch_matches(url: str = None, country: str = None, fmt: str = 'text') -> str:
    """
    完整流程: 打开页面 -> 关闭弹窗 -> 提取数据 -> 解析输出

    Args:
        url: FlashScore URL (默认足球首页)
        country: 按国家筛选 (逗号分隔)
        fmt: 输出格式 text/json

    Returns:
        格式化后的比赛数据
    """
    url = url or 'https://www.flashscore.com/football/'

    print("正在打开 FlashScore...", file=sys.stderr)
    open_flashscore(url)

    print("检查弹窗...", file=sys.stderr)
    dismiss_cookie_banner()

    print("提取数据...", file=sys.stderr)
    text = extract_text()

    # 保存原始文本
    raw_path = os.path.join(os.path.dirname(__file__), '..', '..', 'workspace', 'fs_raw.txt')
    os.makedirs(os.path.dirname(raw_path), exist_ok=True)
    with open(raw_path, 'w', encoding='utf-8') as f:
        f.write(text)

    print(f"提取到 {len(text)} 字符", file=sys.stderr)

    # 解析
    import tempfile
    with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False, encoding='utf-8') as tf:
        tf.write(text)
        tmp_path = tf.name

    try:
        cmd = ['python', PARSE_SCRIPT, tmp_path, '-f', fmt]
        if country:
            cmd.extend(['-c', country])

        result = subprocess.run(
            cmd, capture_output=True, text=True, timeout=15, encoding='utf-8'
        )
        return result.stdout
    finally:
        os.unlink(tmp_path)


def cleanup():
    """关闭浏览器"""
    xb_run(['cleanup'])


if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser(description='FlashScore 比赛数据抓取')
    parser.add_argument('--url', default='https://www.flashscore.com/football/')
    parser.add_argument('--country', '-c', help='按国家筛选')
    parser.add_argument('--format', '-f', choices=['text', 'json'], default='text')
    parser.add_argument('--no-cleanup', action='store_true', help='不关闭浏览器')
    args = parser.parse_args()

    try:
        output = fetch_matches(url=args.url, country=args.country, fmt=args.format)
        print(output)
    finally:
        if not args.no_cleanup:
            cleanup()
