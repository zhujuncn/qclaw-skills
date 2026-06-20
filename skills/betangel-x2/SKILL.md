version: 7.0.1
last_updated: 2026-05-07
status: active
depends_on:
  - football-council  # NameResolver v3 shared infra
parent_skills: [football-council, cgmbet26-strategies]
---

# Bet Angel X2 流水线 v7.0.1 — 多策略框架（概率校准版）

> 更新: 2026-05-07 | 余额: ~6,000 RON | 账户: Betfair Exchange (RON)

## ⭐ 自动下单成功模式 (2026-05-07 验证)

### 完整自动化流程（已验证 4/4 成功）

```python
# 1. 从候选文件读取
import json
with open('_may6_final.json') as f:
    candidates = json.load(f)

# 2. 下单
import requests
BA_BASE = 'http://localhost:9000'

for c in candidates:
    payload = {
        'marketId': c['market_id'],
        'async': False,
        'globalSettings': {'accountId': 'DEFAULT'},
        'betsToPlace': [{
            'type': c['bet_type'],  # 'BACK' or 'LAY'
            'price': c['bet_price'],
            'stake': 1.0,
            'selectionId': int(c['sel_id'])  # 关键：转 int
        }]
    }
    r = requests.post(f'{BA_BASE}/api/betting/v1.0/placeBets', json=payload)
    bets = r.json().get('result', {}).get('bets', [])
    if bets and bets[0].get('status') == 'OK':
        print(f"✅ {c['home']} vs {c['away']} betRef={bets[0].get('betRef')}")
```

### 关键经验
| # | 经验 | 说明 |
|---|------|------|
| 1 | **selectionId 必须 int** | API 返回字符串，下注需 `int(sel_id)` |
| 2 | **Sel ID 非固定** | 58805 不总是 Draw，按位置获取 |
| 3 | **响应路径** | `result.bets[0]` 不是 `result.results` |
| 4 | **成功检查** | `bets[0].status == 'OK'` + `betRef` 存在 |
| 5 | **Market ID** | 用 Betfair Market ID（1.xxxxx） |

---

## ⚠️ 核心修正 v7.0（2026-05-02 重大变更）

### ❌ 旧方法论：循环论证（导致 87 笔全败）
### DJYY → BA 名称匹配

**Name Resolver v3** 是所有足球技能的统一底层组件，位于：
```
C:/Users/zhuju/.qclaw/skills/football-council/scripts/name_resolver.py
别名库: C:/Users/zhuju/.qclaw/skills/football-council/data/team_aliases.json (578条)
```

所有技能统一使用以下导入方式：
```python
import sys
sys.path.insert(0, 'C:/Users/zhuju/.qclaw/skills/football-council/scripts')
from name_resolver import NameResolver

nr = NameResolver()
nr.register_ba_markets(ba_markets_dict)  # {market_name: market_id}

result = nr.find_match('Bayern Munchen', 'Mainz 05')
# → {'ba_name': 'Bayern Munich v Mainz 05', 'score': 0.75, 'method': 'fuzzy'}

# v3 新增：一句话下单
result = nr.find_and_bet(home='Bodo Glimt', away='Molde',
                         side='BACK', max_price=1.5, stake=1.0)
```

#### Name Resolver v3 关键改进
- **匹配策略 5 层**: CGM_SHORTEN → DJYY_ALIASES (300+) → team_aliases.json (578条) → EXPANSIONS → fuzzy
- **CGM 缩写硬编码**: az→Az Alkmaar, fh→Hafnarfjordur, ibv→IBV, shamrock→Shamrock
- **去变音**: Genclerbirligi, Brondby, Malmo
- **性别过滤**: 男足≠女足，二队默认过滤
- **BA API 端点**: /api/betting/v1.0/placeBets | Price: back1.prc / lay1.prc
- **selectionId**: 必须是 INT，不是字符串

#### 关键别名映射（2026-05-03 验证）
| 外部名 | BA 队名 | 来源 |
|--------|---------|------|
| Paris | Paris St-G | DJYY |
| Koln | FC Koln | DJYY |
| AZ | Az Alkmaar | CGM |
| FH | Hafnarfjordur | CGM |
| Hearts | Heart of Midlothian | DJYY |
| Bodo Glimt | Bodo Glimt | DJYY |
| Shamrock | Shamrock | CGM |
| IBV | IBV | CGM |
| Flamengo | Flamengo | DJYY |
| Vasco da Gama | Vasco | DJYY |
| Duisburg | Duisburg | CGM |
| Cottbus | Cottbus | CGM |
| Rio Ave | Rio Ave | DJYY |
| Gil Vicente | Gil Vicente | DJYY |
| FC Twente | Twente | CGM |
| Mjallby | Mjallby | CGM |
| Brommapojkarna | Brommapojkarna | CGM |

---

### 7️⃣ DJYY 数据获取

| # | 经验 | 根因 | 日期 |
|---|------|------|------|
| 7.1 | DJYY 是 SPA 应用，`web_fetch` 只拿到空壳 HTML | React/Vue 渲染，无 SSR | 04-20 |
| 7.2 | **SSRF 策略阻止访问 djyydata.com** — browser/web_fetch 均被拦截 | OpenClaw 安全策略 | 04-16 |
| 7.3 | **0 picks = 立即停止**，不进入 Guardian 扫描 | v4.4 规则：DJYY 是唯一输入源 | 04-13 |
| 7.4 | 用户需手动登录 DJYY 提供 picks | 无法自动化 DJYY 访问 | 04-16 |

**凭证**：从本机安全配置读取；不要在 skill 文件中写入明文账号或密码。

---

### 8️⃣ Cron 定时任务

| # | 经验 | 根因 | 日期 |
|---|------|------|------|
| 8.1 | **必须指定 `model: "modelroute"`** | tc-code-latest 模型会拒绝博彩任务 | 04-16 |
| 8.2 | 300s timeout 不够 DJYY 登录流程 | DJYY 登录 + 页面加载 + 提取 > 5 分钟 | 04-20 |
| 8.3 | 无 DJYY 模式下扫描 125+ 场候选不安全 | 缺乏策略筛选 = 随机下注 | 04-20 |

---

### 9️⃣ 环境与 GUI 限制

| # | 经验 | 根因 | 日期 |
|---|------|------|------|
| 9.1 | Bet Angel GUI 是 **DirectX 自定义渲染**，Win32/UIA/pywinauto 全部失败 | 非 WPF/WinForms 标准控件 | 04-11 |
| 9.2 | 键盘自动化被 **UIPI** (User Interface Privilege Isolation) 拦截 | 进程权限不足 | 04-11 |
| 9.3 | 俄超联赛**不在 FT Coupon** 中，需特定 coupon 或手动添加 | 联赛覆盖有限 | 04-19 |
| 9.4 | MLS / 丹麦超等联赛可能需要特定 coupon | FT coupon 非全球覆盖 | 04-19 |
| 9.5 | BACK↔LAY 赔率换算：LAY price ≈ BACK price + 1（快速心算） | 下注逻辑互为镜像 | 04-10 |
| 9.6 | CGMBet MatchId 格式：`LLSSMMMMMM`（LL=联赛前2位，SS=赛季，M=序号） | CGMBet 内部编码 | 04-16 |
| **9.7** | **CGMBet `StatusCode=0` 表示已完成**（❌ 不是 1），`Teams.Id` 是 TEXT 需引号 | Schema 与直觉相反 | **04-23** |

---

### 🔢 速查表

| 操作 | API 端点 | 关键参数 | marketId 类型 |
|------|---------|---------|--------------|
| 查余额 | `POST /api/markets/v1.0/getBalance` | `{}` | — |
| 加载市场 | `POST /api/guardian/v1.0/applyCoupon` | `{couponName, clearOption, watchListNumber}` | — |
| 获取市场 | `POST /api/markets/v1.0/getMarkets` | `{dataRequired: [SELECTION_IDS, SELECTION_NAMES, ...]}` | — |
| 获取价格 | `POST /api/markets/v1.0/getMarketPrices` | `{marketId, dataRequired: [BEST_PRICE_ONLY]}` | Guardian ID |
| **下注** | `POST /api/betting/v1.0/placeBets` | `{marketId, betsToPlace: [{selectionId, type, price, stake}]}` | **Betfair Market ID** |
| 取消下注 | `POST /api/betting/v1.0/cancelBets` | `{betsToCancel: [bet_ref]}` | — |
| 全部平仓 | `POST /api/betting/v1.0/greenAllSelections` | `{marketId, priceOption}` | Betfair Market ID |
| 显示市场 | `POST /api/guardian/v1.0/displayMarket` | `{marketId, displayChoice, activateWindow}` | Guardian ID |

---

## Evolver 学习记录 (2026-04-24)

### Value 筛选阈值 (73场实单验证)

| Value | 信号 | 动作 |
|-------|------|------|
| ≥20% | BLUE++ | KEEP，标准仓位 |
| 15-20% | BLUE+ | KEEP |
| 10-15% | BLUE | KEEP |
| 5-10% | BLUE- | MARGINAL |
| -5%~5% | GRAY | CANCEL |
| <-15% | PINK++ | 立即取消 |

### 赔率范围规则

| 赔率范围 | 评级 | 动作 |
|---------|------|------|
| < 2.0 | ❌ 陷阱 | 一律取消 (Kelly 必为负) |
| 2.0-4.0 | ✅ 最佳 | 标准操作区间 |
| 4.0-8.0 | ✅ 良好 | 标准/高 Value 区域 |
| 8.0-10.0 | ⚠️ 谨慎 | 减半仓位 |
| > 10.0 | ⚠️ 彩票 | 极小比例或不参与 |

### 风控规则

- 每场限 **1 笔注**，禁止同方向叠加
- 单批次总暴露 ≤ 银行余额 **10%**
- **Kelly < 0 → 立即取消**
- 连续 3 次失败 → 暂停重新评估

### 低赔率陷阱案例

| 比赛 | 赔率 | Kelly | Value | 结果 |
|------|------|-------|-------|------|
| Getafe v Barcelona | 1.65 | -1.2% | -22.2% | 取消 |
| Betis v Real Madrid | 1.93 | -1.0% | -19.8% | 取消 |

### Draw 信号特征

当双方 15 场平局率均 > 60% 时，Draw 价值极高:
- Sogndal v Asane: Draw @4.20, Value=+68.9%
- Bray v Cork City: Draw @3.80, Value=+65.0%
- 适用联赛: 挪威/瑞典/爱尔兰/苏格兰低级别
