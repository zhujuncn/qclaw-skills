#!/usr/bin/env python3
"""
FlashScore 比赛数据解析器

将 FlashScore 页面提取的纯文本解析为结构化数据。
"""

import re
import sys
import json
import argparse
from datetime import datetime, timezone, timedelta
from collections import defaultdict


def parse_flashscore_text(text: str, timezone_offset: int = 3) -> list[dict]:
    """
    解析 FlashScore 页面提取的文本。

    Args:
        text: 从 #live-table 提取的 innerText
        timezone_offset: UTC 偏移小时数（默认 +3 = Bucharest）

    Returns:
        比赛字典列表，每个包含 league, country, time, home, away, score1, score2
    """
    lines = text.strip().split('\n')
    matches = []
    current_league = ""
    current_country = ""

    i = 0
    while i < len(lines):
        line = lines[i].strip()

        # 跳过标题和按钮
        if line in ('ALL', 'LIVE', 'ODDS', 'FINISHED', 'SCHEDULED', 'Standings',
                     'PREVIEW', 'Draw', 'Go to News', 'display matches', ''):
            i += 1
            continue

        # 日期行 "24/04 FR"
        if re.match(r'^\d{1,2}/\d{2}\s+[A-Z]{2}$', line):
            i += 1
            continue

        # 跳过 Flashscore News
        if line.startswith('Flashscore News') or line.startswith('Why Chelsea') or \
           line.startswith('Abdul Mumin') or line.startswith('Stuttgart strike'):
            i += 1
            continue

        # 国家行: 以冒号结尾
        if re.match(r'^[A-Z][A-Za-z\s&]+:\s*$', line) and not line.startswith('Standings'):
            current_country = line.strip().rstrip(':')
            i += 1
            continue

        # 联赛名（下一行是国家: 或 Standings）
        if i + 1 < len(lines):
            next_line = lines[i + 1].strip() if i + 1 < len(lines) else ''

            # 如果下一行是国家:，这是联赛名
            if next_line.endswith(':') and not next_line.startswith('Standings'):
                current_league = line
                current_country = next_line.rstrip(':')
                i += 2
                continue
            elif next_line == 'Standings':
                current_league = line
                i += 2
                continue

        # 时间行: HH:MM 或 "Finished" 或 "After Pen." 或 FRO
        if re.match(r'^(\d{1,2}:\d{2}|Finished|After Pen\.|FRO|To finish)$', line):
            time_raw = line if line not in ('FRO', 'To finish') else 'TBD'

            # 转换时间为本地时区
            time_local = time_raw
            if re.match(r'^\d{1,2}:\d{2}$', time_raw):
                try:
                    h, m = map(int, time_raw.split(':'))
                    local_h = (h + timezone_offset) % 24
                    time_local = f"{local_h:02d}:{m:02d}"
                    if local_h < h:  # 跨天
                        time_local += " (+1d)"
                except:
                    pass

            # 提取主队
            if i + 1 < len(lines):
                home_team = lines[i + 1].strip()
                if re.match(r'^(\d{1,2}:\d{2}|Finished|After Pen\.|FRO)$', home_team):
                    i += 1
                    continue

                # 提取客队
                if i + 2 < len(lines):
                    away_team = lines[i + 2].strip()

                    # 提取比分
                    score1 = ''
                    score2 = ''
                    if i + 4 < len(lines):
                        s1 = lines[i + 3].strip()
                        s2 = lines[i + 4].strip()
                        if re.match(r'^\d+$', s1) and re.match(r'^\d+$', s2):
                            score1 = s1
                            score2 = s2

                    if home_team and away_team:
                        matches.append({
                            'league': current_league,
                            'country': current_country,
                            'time': time_local,
                            'time_utc': time_raw,
                            'home': home_team,
                            'away': away_team,
                            'score1': score1,
                            'score2': score2,
                            'status': 'finished' if line == 'Finished' else 'scheduled'
                        })
                        i += 5 if score1 else 3
                        continue

        i += 1

    return matches


def filter_by_country(matches: list[dict], countries: list[str]) -> list[dict]:
    """按国家代码筛选比赛"""
    country_map = {
        'RO': 'ROMANIA', 'DE': 'GERMANY', 'GB': 'ENGLAND', 'FR': 'FRANCE',
        'IT': 'ITALY', 'ES': 'SPAIN', 'NL': 'NETHERLANDS', 'PT': 'PORTUGAL',
        'TR': 'TURKEY', 'PL': 'POLAND', 'BE': 'BELGIUM', 'AT': 'AUSTRIA',
        'CZ': 'CZECH', 'HU': 'HUNGARY', 'GR': 'GREECE', 'DK': 'DENMARK',
        'SE': 'SWEDEN', 'NO': 'NORWAY', 'FI': 'FINLAND', 'RU': 'RUSSIA',
        'UA': 'UKRAINE', 'CH': 'SWITZERLAND', 'AR': 'ARGENTINA', 'BR': 'BRAZIL',
        'MX': 'MEXICO', 'US': 'USA', 'AU': 'AUSTRALIA', 'JP': 'JAPAN',
        'KR': 'SOUTH KOREA', 'CN': 'CHINA', 'IN': 'INDIA', 'SA': 'SAUDI ARABIA'
    }

    allowed = [country_map.get(c.upper(), c.upper()) for c in countries]
    return [m for m in matches if any(a in m.get('country', '').upper() for a in allowed)]


def format_output(matches: list[dict], fmt: str = 'text') -> str:
    """格式化输出"""
    if fmt == 'json':
        return json.dumps(matches, ensure_ascii=False, indent=2)

    # 按联赛分组
    by_league = defaultdict(list)
    for m in matches:
        key = f"{m['country']} - {m['league']}"
        by_league[key].append(m)

    # 排序：五大联赛 + 罗马尼亚优先
    major = ['ENGLAND', 'FRANCE', 'GERMANY', 'ITALY', 'SPAIN', 'ROMANIA']
    sorted_leagues = sorted(by_league.keys(),
                            key=lambda x: (0 if any(c in x for c in major) else 1, x))

    lines = []
    lines.append("=" * 80)
    lines.append(f"足球比赛汇总 ({datetime.now().strftime('%Y-%m-%d')})")
    lines.append("=" * 80)

    for league in sorted_leagues:
        ms = by_league[league]
        lines.append(f"\n{league} ({len(ms)} 场)")
        lines.append("-" * 60)
        for m in ms:
            score = f"{m['score1']}:{m['score2']}" if m['score1'] else "-"
            status = "✓" if m['status'] == 'finished' else "○"
            lines.append(f"  {status} {m['time']:<10} {m['home']} vs {m['away']} [{score}]")

    return '\n'.join(lines)


def main():
    parser = argparse.ArgumentParser(description='解析 FlashScore 比赛数据')
    parser.add_argument('input', help='FlashScore 页面文本文件')
    parser.add_argument('--country', '-c', help='按国家筛选（逗号分隔，如 RO,DE,GB）')
    parser.add_argument('--timezone', '-tz', default='Europe/Bucharest',
                        help='输出时区（默认 Europe/Bucharest）')
    parser.add_argument('--format', '-f', choices=['text', 'json'], default='text',
                        help='输出格式')
    parser.add_argument('--output', '-o', help='输出文件（默认 stdout）')

    args = parser.parse_args()

    # 时区偏移
    tz_offsets = {
        'Europe/Bucharest': 3, 'Europe/London': 0, 'Europe/Berlin': 1,
        'Europe/Paris': 1, 'Europe/Moscow': 3, 'Asia/Shanghai': 8,
        'Asia/Tokyo': 9, 'America/New_York': -5, 'America/Los_Angeles': -8
    }
    offset = tz_offsets.get(args.timezone, 3)

    # 读取输入
    with open(args.input, 'r', encoding='utf-8') as f:
        text = f.read()

    # 解析
    matches = parse_flashscore_text(text, offset)

    # 筛选
    if args.country:
        countries = [c.strip() for c in args.country.split(',')]
        matches = filter_by_country(matches, countries)

    # 输出
    output = format_output(matches, args.format)

    if args.output:
        with open(args.output, 'w', encoding='utf-8') as f:
            f.write(output)
        print(f"已保存到 {args.output} ({len(matches)} 场比赛)")
    else:
        print(output)


if __name__ == '__main__':
    main()
