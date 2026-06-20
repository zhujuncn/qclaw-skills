# 可用规则目录

规则文件路径：`C:\Users\zhuju\AppData\Roaming\Bet Angel\Bet Angel Professional\Automation\`

## 命名规则

- `_1RON` — 下注规则（stake = 1 RON），需要满足触发条件才下注
- `_10RON` — 下注规则（stake = 10 RON）
- `_SIGNAL` — 信号扫描器，不直接下注，用于写入 Stored Values
- `_CS_Check` / `_CS_Score_Scanner` — 比分扫描器

## 完整列表（截至 2026-06-20）

### 下注规则 (_1RON)
BAF002, BAF004, BAF005, BAF006, BAF011, BAF014, BAF016, BAF017,
BAF020~BAF034, BAF041, BAF049~BAF052, BAF059, BAF061~BAF115

### 下注规则 (_10RON)
BAF002_10RON

### 信号扫描器 (_SIGNAL)
BAF001, BAF003, BAF007~BAF010, BAF012~BAF013, BAF015, BAF018~BAF019,
BAF035~BAF037, BAF040, BAF042~BAF048, BAF053~BAF057, BAF060,
BAF081~BAF082, BAF089, BAF096~BAF099, BAF104~BAF107

### 测试规则
CODEX_Test_Signal_Goals, CODEX_Test_Signal_Goals_OU

## 规则与市场类型映射（已知）

| 规则 | 市场类型 | 说明 |
|------|----------|------|
| BAF005_1RON | OVER_UNDER_25 | Back O2.5，需要 Stored Values homefav/awayfav + 比分 0-1/1-0 |
| BAF002_1RON | OVER_UNDER_25 | 1RON 下注 |
| BAF002_10RON | OVER_UNDER_25 | 10RON 下注 |
| BAF004_1RON | OVER_UNDER_25 | 1RON 下注 |

> 完整规则逻辑见各 .baf 文件内容或论坛帖子。
