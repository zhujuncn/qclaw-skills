---
name: guardian-automation
version: 1.1.0
last_updated: 2026-05-02
status: active
parent_skills: [betangel-x2]
description: Guardian 自动化规则(.baf)生成解析 + API 替代方案 + Guardian GUI 设置指南。进球信号检测、Guardian 规则文件管理。
---

# Guardian Automation v1.1.0 - Bet Angel 进球信号检测技能

> Guardian 自动化规则(.baf)生成解析 + API 替代方案 + Guardian GUI 设置指南

---

## 核心能力

| 能力 | 工具 | 说明 |
|------|------|------|
| .baf 文件解析 | `baf_generator.py parse` | 解读 Guardian 规则结构 |
| .baf 文件生成 | `baf_generator.py generate` | 程序化生成信号检测规则 |
| API 进球检测 | `goal_signal_detector.py` | Python + API 实时监控赔率变动 |
| Guardian GUI 设置 | 模板 + 手动配置 | 路径 A：GUI 内完成全套流程 |

---

## ⚠️ 关键限制

**Bet Angel API 不暴露 Guardian 自动化端点**。信号和规则只能通过 GUI 操作。

**两条路径**：
- **路径 A（推荐）**：Guardian GUI 导入 .baf + 手动创建交易规则
- **路径 B**：Python API 实时监控 + 脚本执行下注

---

## 进球检测原理

足球进球时市场赔率会发生显著跳变：

| 市场 | 进球后赔率变化 | 检测方向 | 推荐阈值 |
|------|-------------|---------|---------|
| Match Odds | 领先方 BACK 赔率骤降 | LTP 下降 10+ ticks | 10 ticks |
| Match Odds | 落后方 BACK 赔率飙升 | LTP 上升 10+ ticks | 10 ticks |
| Over/Under | Over 赔率下降 | LTP 下降 15+ ticks | 15 ticks |

**信号机制**：
- `INCREMENT goal 1` → goal 计数 +1（检测到进球）
- `DECREMENT goal 1` → goal 计数 -1（区分对方进球）

---

## 路径 A：Guardian GUI 设置（推荐）

### 第一步：导入信号检测规则

1. 打开 Bet Angel → 点击 **Guardian** 按钮
2. 切换到 **Automation** 标签
3. 点击 **"Import a Rules File"** 按钮
4. 选择模板文件：
   - **Match Odds 版**：`templates/signal_goals_match_odds.baf`
     - 规则 1：LTP 65秒内上涨 >10 ticks → INCREMENT goal（对方进球）
     - 规则 2：LTP 65秒内下跌 >10 ticks → DECREMENT goal（主队进球）
   - **O/U 版**：`templates/signal_goals_over_under.baf`
     - 规则 1：Over 价格 65秒内下跌 >15 ticks → INCREMENT goal
5. 导入后规则会出现在 Automation 列表中

### 第二步：添加比赛市场

1. 在 Guardian 主界面 → **Markets** 标签
2. 点击 **"Add Market"** → 搜索比赛名称
3. 或点击 **"My Coupons"** → 选择 **"Football - Full Time"** 批量加载
4. 将需要的比赛拖入 Guardian 监控列表

### 第三步：应用信号规则到市场

1. 在 Guardian 监控列表中，右键点击比赛
2. 选择 **"Apply Automation"** → 选择导入的信号规则
3. 确认规则已绑定（Automation 列显示规则名称）

### 第四步：创建 Cash Out 规则（GUI 内）

这是路径 A 的核心优势 — 信号可直接在 Guardian 内触发交易：

1. Guardian → Automation → **"Create a New Rule"**
2. 规则名称：`Cash Out on Goal`
3. 规则类型：**"Place a Bet"**
4. **Conditions** 标签：
   - 添加条件 → **"Signal Value"**
   - 信号名称：`goal`
   - 比较方式：`Greater than`
   - 值：`0`
5. **Actions** 标签：
   - 选择 **"Back All"** 或 **"Cash Out"**
   - 设置下注参数（stake、price 等）
6. 保存规则并应用到比赛市场

**信号 → 动作链**：
```
进球发生 → LTP 跳变 >10 ticks
         → Signal Goal 规则 INCREMENT goal
         → goal 信号值变为 1
         → Cash Out on Goal 规则检测到 goal > 0
         → 执行 Cash Out / 下注动作
```

### 常用信号触发规则模板

在 Guardian GUI 中创建以下规则：

| 规则名 | 条件 | 动作 | 用途 |
|--------|------|------|------|
| Cash Out on Goal | goal > 0 | Cash Out | 进球后立即平仓 |
| Lay Draw on Goal | goal > 0 | LAY Draw @ 顺销 | 进球后平局赔率飙升，LAY 获利 |
| Back Over 0.5 | goal > 0 | BACK Over 0.5 | 进球确认后追 Over |
| Back Leader | goal > 0 + price<1.50 | BACK 领先方 | 进球后加仓领先方 |

### 参数调整建议

| 场景 | Match Odds ticks | O/U ticks | 守卫时间 |
|------|-----------------|-----------|---------|
| 标准（推荐） | 10 | 15 | 60s |
| 保守（防误触） | 15 | 20 | 90s |
| 激进（快速检测） | 5 | 10 | 30s |
| 强弱悬殊 | 15-20 | 20 | 60s |

**⚠️ 低赔率陷阱**：当领先方赔率 < 1.30 时，后续进球只产生 5-10 ticks 变动，可能无法触发检测。建议：
- 同时监控 O/U 市场作为备份
- 或降低 tick 阈值到 5

---

## 路径 B：Python API 监控

```bash
# 实时监控（Match Odds 市场）— verbose 模式显示 LTP 变化
python goal_signal_detector.py monitor <market_id> --market-type match_odds -v

# 测试模式（60秒后退出）
python goal_signal_detector.py test <market_id> -v

# O/U 市场
python goal_signal_detector.py monitor <market_id> --market-type over_under --tick-threshold 15 -v

# 自定义参数
python goal_signal_detector.py monitor <market_id> \
  --tick-threshold 10 --history-seconds 65 --guard-delay 60 --check-interval 3 -v

# 带回调命令（进球时触发外部脚本）
python goal_signal_detector.py monitor <market_id> --on-goal "python place_bet.py --market {market_id}"
```

**输出示例**：

```
[10:30:15] LTP init: Sel97450775=2.50 | Sel82346037=3.40 | Sel58805=3.20
[10:30:18] LTP: Sel97450775 2.50->2.35(-5) | Sel82346037 3.40->3.80(+6)
[10:31:20] GOAL! INCREMENT | Sel97450775 | 2.50 -> 2.10 (-12 ticks) | Total: 1
{"event":"goal_detected","market":"Team A v Team B","direction":"increment",...}
```

---

## .baf 文件生成/解析

```bash
# 生成 Match Odds 版信号检测
python baf_generator.py generate --type match_odds --tick-threshold 10 -o signal_goals.baf

# 生成 O/U 版信号检测
python baf_generator.py generate --type over_under --tick-threshold 15 -o signal_goals_ou.baf

# 解析任意 .baf 文件
python baf_generator.py parse "C:\path\to\file.baf"

# JSON 输出
python baf_generator.py parse "C:\path\to\file.baf" --json
```

---

## 红牌误触发

**问题**：红牌会导致赔率变动方向与进球类似。

**缓解方法**：
- 增大 tick 阈值（进球通常 >15 ticks，红牌 5-10 ticks）
- 增加时间保护（60 秒内不重复触发）
- 配合实时比分源（如 Sofascore）交叉验证

---

## 文件清单

| 文件 | 用途 |
|------|------|
| `SKILL.md` | 本文档 |
| `scripts/goal_signal_detector.py` | API 进球检测器（支持 verbose 模式） |
| `scripts/baf_generator.py` | .baf 文件生成/解析器 |
| `references/baf_format.md` | 完整 .baf 格式参考 |
| `templates/signal_goals_match_odds.baf` | Match Odds 信号检测模板 ✅ |
| `templates/signal_goals_over_under.baf` | O/U 信号检测模板 ✅ |
