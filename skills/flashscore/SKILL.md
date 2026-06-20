---
name: flashscore
description: FlashScore 足球比赛数据抓取技能。通过 xbrowser 控制 FlashScore 网站，提取全球足球比赛的实时比分、赛程和结果。当用户提到 FlashScore、flashscore.com、今日比赛、比赛列表、足球赛程、实时比分、比分查询、比赛数据抓取、足球比赛汇总等时触发此技能。支持按联赛/国家筛选、五大联赛重点关注、罗马尼亚本地联赛优先显示。
---

# FlashScore 足球比赛数据抓取

通过 xbrowser (CfT浏览器) 从 flashscore.com 提取全球足球比赛数据。

## 工作流程

### 1. 打开 FlashScore

```
xb run --browser default open https://www.flashscore.com/football/
xb run --browser default wait --load networkidle
```

### 2. 处理隐私弹窗

首次打开会出现 Cookie 弹窗，点击 "Reject All" 或 "Accept"：
```
xb run --browser default snapshot -i -c
# 找到 Reject/Accept 按钮的 ref，然后点击
xb run --browser default click @<ref>
```

### 3. 提取比赛数据

使用 `eval` 命令提取页面文本（xb eval 有参数长度限制，用简单表达式）：

```
xb run --browser default eval "document.querySelector('#live-table').innerText"
```

返回的文本格式为：
```
联赛名
国家:
Standings
HH:MM
主队
客队
比分1
比分2
```

### 4. 解析为结构化数据

使用 `scripts/parse_flashscore.py` 解析原始文本：

```bash
python <skill_dir>/scripts/parse_flashscore.py <input.txt> [--country RO,DE,GB] [--timezone Europe/Bucharest]
```

参数：
- `input.txt` - FlashScore 页面提取的原始文本
- `--country` - 按国家代码筛选（逗号分隔），默认显示全部
- `--timezone` - 输出时区，默认 Europe/Bucharest (UTC+3)
- `--output` - 输出文件路径，默认 stdout

### 5. 关闭浏览器

```
xb run cleanup
```

## 重要技术细节

### xb eval 限制
- **参数长度限制**: 超过 ~500 字符的 JS 表达式会被截断
- **解决方案**: 用简单表达式 `innerText` 提取全文，Python 端解析
- **避免**: 不要在 eval 中写复杂的 DOM 查询 + 数据聚合

### PowerShell/Bat 转义陷阱
- `||` 在 `.bat` 文件中是管道符，会导致 JS 逻辑运算符 `||` 被误解
- 双引号嵌套: CSS 选择器中的双引号与 shell 引号冲突
- **推荐**: 用 Python `subprocess` 调用 node xb.cjs，避免 shell 层

### Python 调用示例

```python
import subprocess, json, re

js = "document.querySelector('#live-table').innerText"
node = r'C:\Program Files\QClaw\resources\openclaw\config\bin\node.cmd'
xb = r'<xb_cjs_path>'

result = subprocess.run(
    [node, xb, 'run', '--browser', 'default', 'eval', js],
    capture_output=True, text=True, timeout=30, encoding='utf-8'
)

# 解析返回的 JSON (result 字段可能含特殊字符导致 json.loads 失败)
# 使用正则提取 result 值
match = re.search(r'"result"\s*:\s*"((?:[^"\\]|\\.)*)"', result.stdout)
if match:
    text = match.group(1).replace('\\n', '\n').replace('\\t', '\t')
```

## FlashScore DOM 结构

CSS 类名参考（2024-2026 验证）:

| 元素 | CSS 类名 |
|------|----------|
| 联赛头 | `[class*="event__header"]` |
| 联赛名 | `[class*="event__titleBox"]` |
| 比赛行 | `[class*="event__match"]` |
| 开球时间 | `[class*="event__time"]` |
| 主队 | `[class*="event__homeParticipant"]` |
| 客队 | `[class*="event__awayParticipant"]` |
| 主队比分 | `[class*="event__score--home"]` |
| 客队比分 | `[class*="event__score--away"]` |
| 比赛状态 | `[class*="event__stage"]` |
| 容器 | `#live-table` |

## 页面导航

- 全部比赛: `https://www.flashscore.com/football/`
- 仅直播: `https://www.flashscore.com/football/live/`
- 已完赛: 页面上点击 FINISHED 标签
- 特定日期: 页面上点击日期标签

## 输出格式

默认输出 TSV 格式：
```
联赛    时间    主队    客队    比分
```

使用 `--format json` 输出 JSON 格式。
