---
name: superbet
description: |
  Superbet.ro 罗马尼亚博彩网站自动化。支持登录、查看赔率、浏览比赛、查看余额等操作。
  当用户提到 Superbet、superbet.ro、罗马尼亚博彩、下注网站、查看赔率等时触发。
---

# Superbet.ro 自动化

通过 xbrowser 控制 Superbet.ro 网站操作。

## 前置条件

- xbrowser 已初始化（`node {baseDir}/scripts/xb.cjs init`）
- 账号凭据已保存在 Auth Vault 或由用户提供

## 登录流程

1. 打开登录页：`xb run --browser default open https://superbet.ro/login`
2. 等待加载：`xb run --browser default wait --load networkidle`
3. 获取快照：`xb run --browser default snapshot -i`
4. 填写用户名：`xb run --browser default fill "@<email-ref>" "<username>"`
5. 填写密码：`xb run --browser default fill "@<pass-ref>" "<password>"`
6. 点击登录：`xb run --browser default click "@<login-btn-ref>"`
7. 等待跳转：`xb run --browser default wait --load networkidle`
8. 验证登录成功：`xb run --browser default get url` → 应跳转到 `https://superbet.ro/`
9. 确认登录态：快照中应出现用户头像按钮（如 "JZ"）和 "Depunere"（存款）按钮

### 登录页表单元素

- 用户名输入框：`textbox "E-mail/Nume de utilizator"`
- 密码输入框：`textbox "Parolă"`
- 登录按钮：`button "Intră în cont"`
- 忘记密码：`button "Ai uitat parola?"`
- 注册按钮：`button "Fǎ-ți cont Superbet"`

### Cookie 处理

首次访问会弹出 Cookie 横幅，需先点击 `button "Acceptați toate cookie-urile"` 后再操作。

## 会话持久化

xbrowser 自动维护会话，首次登录后 Cookie 自动保存，后续无需重复登录。
如需导出/导入认证状态：`xb run state save/load <file>`。

## 网站结构（移动端视图）

### 顶部导航
- 搜索按钮、用户头像、存款按钮
- 首页(Acasă)、Live、Sport、Bilete(票据)、Casino

### 首页区域
- TOP LIVE、COTE MĂRITE（提高赔率）、SUPERPARIURI DE TOP
- COMPETIȚII DE TOP、SUPER COTA、EVENIMENTE LIVE
- TOP 10、BILETE POPULARE、ȘTIRI

### 比赛详情页
- 标签页：Chat、Cote（赔率）、Stats、H2H、Echipe、Clasament、Analize
- 赔率分类：Populare、Goluri、Statistici、Cornere、Cartonașe、Reprize、Handicap、Combos、Rapide、Bet Builder

## 注意事项

- URL 含特殊字符时用单引号包裹（PowerShell 中双引号会展开 $）
- 赔率按钮格式如 "1 1.30"、"X 4.30"、"2 12.00"
- 比赛链接包含实时比分信息，如 "Repriza 2 · 58'"
- 快照中 @ref 是临时的，DOM 变化后需重新 snapshot -i

---

## Evolver 学习记录 (2026-04-24)

### 赔率范围规则 (Betfair Exchange 实测验证)

| 赔率范围 | 评级 | 动作 |
|---------|------|------|
| < 2.0 | ❌ 陷阱 | 一律不碰 (Kelly 必为负) |
| 2.0-4.0 | ✅ 最佳 | 标准操作区间 |
| 4.0-8.0 | ✅ 良好 | 高 Value 区域 |
| 8.0-10.0 | ⚠️ 谨慎 | 减半仓位 |
| > 10.0 | ⚠️ 彩票 | 极小比例或不参与 |

### 低赔率陷阱案例

| 比赛 | 赔率 | Value | 结果 |
|------|------|-------|------|
| Getafe v Barcelona | 1.65 | -22.2% | 必须取消 |
| Betis v Real Madrid | 1.93 | -19.8% | 必须取消 |

### Value 筛选标准

- Value ≥ 10% → KEEP
- Value 5-10% → MARGINAL
- Value < 5% → CANCEL

### 风控规则

- 每场限 1 笔，禁止同方向叠加
- 单批次总暴露 ≤ 银行余额 10%
- Kelly < 0 → 立即取消
