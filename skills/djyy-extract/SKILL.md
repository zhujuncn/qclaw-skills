---
name: djyy-extract
description: 从 djyydata.com 网站自动提取指定策略（strategy）的今日比赛推荐。适用场景：用户说"提取 DJYY 策略"、"获取 Double chance X2 今日推荐"、"导出 djyydata 策略"、或要求"帮我从 DJYY Data 网站下载策略推荐"时触发。支持指定策略名称，自动完成登录、导航、提取、保存全流程。
---

# DJYY Data 策略提取技能

从 djyydata.com 提取指定策略的今日比赛推荐。

## 凭证配置

首次使用需配置账号密码（已加密存储在 `~/.qclaw/.env`）：

```
DJYY_EMAIL=<your-email>
DJYY_PASSWORD=<your-password>
```

## 执行流程

### 方式一：直接指令（推荐）

告知我需要提取哪个策略，例如：
- "提取 Double chance X2 strategy"
- "导出 Balance draw strategy 的今日推荐"
- "获取 Away win strategy 的比赛"

我会自动执行以下步骤：

1. 启动浏览器并打开登录页
2. 输入邮箱 → Continue → 输入密码 → Continue
3. 进入 Strategies 页面
4. 找到对应策略卡片，点击 "N picks" 按钮
5. 从下拉菜单提取所有比赛信息
6. 筛选未开始比赛（比分 `- : -`）
7. 按格式生成文件并保存到 `~/.easyclaw/workspace/djyy_recommendations_YYYY-MM-DD.txt`

### 方式二：脚本自动化

如需完全自动化，可使用脚本：

```bash
python3 scripts/djyy_extract.py "Double chance X2 strategy"
```

## 输出格式

```
策略名称：[策略名]
日期：[YYYY-MM-DD]
比赛总数：[N] 场

主队列表（or 分隔）：
[主队1] or [主队2] or [主队3] ...

详细比赛信息（按时间从早到晚排序）：

【今天 YYYY-MM-DD】
1. [时间] | [联赛] | [主队] vs [客队] | [比分]
2. [时间] | [联赛] | [主队] vs [客队] | [比分]
...

【明天 YYYY-MM-DD】
N. [时间] | [联赛] | [主队] vs [客队] | [比分]
...
```

## 排序要求

**必须按完整时间从早到晚排序：**
- 比赛跨天时，按完整日期+时间排序（如 2026-04-04 22:00 < 2026-04-05 02:30）
- 使用 `【今天】` 和 `【明天】` 分隔不同日期的比赛
- 同一时间多场比赛，按联赛名称字母顺序排列
- 格式：`序号. 时间 | 联赛 | 主队 vs 客队 | 比分`

## 已知策略名称映射

| 策略显示名 | 内部标识 |
|-----------|---------|
| Double chance X2 strategy | x2 |
| Balance draw strategy | draw |
| Home win strategy A / B | home |
| Away win strategy | away |
| Over 2.5 strategy | over |
| Corners under 9.5 strategy | corners |

## 注意事项

- 该网站为 React SPA，curl 无法直接提取数据，必须使用浏览器自动化
- 登录时需两次点击 Continue（先邮箱，后密码）
- 部分策略的 picks 按钮可能需要等待菜单动画加载
- 输出文件默认保存至 `~/.easyclaw/workspace/`，目录不存在会自动创建
- **排序必须按完整日期+时间从早到晚**，跨天比赛要正确排序
- 文件中需用 `【今天】` 和 `【明天】` 分隔不同日期的比赛
