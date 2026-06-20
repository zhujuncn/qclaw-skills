---
name: maps-travel-list
description: Google Maps 旅行规划地点列表创建工具。自动为城市创建国家代码命名的地点列表，搜索主要景点并添加格式化备注。触发词：创建地点列表、旅行规划、Google Maps 列表、景点备注、城市列表。支持格式：`#序号 英文名 | 时长 | 费用`
---

# Google Maps 旅行地点列表创建

为旅行规划在 Google Maps 创建按国家代码命名的地点列表，搜索主要景点并添加格式化备注。

## 工作流程

```
输入城市 → Google Maps 新建国家代码列表 → 搜索主要景点 → 添加到列表 → 按格式添加备注
```

## 使用方法

用户输入城市名称和国家代码，技能自动：
1. 在 Google Maps 创建国家代码列表（如 SE、FI、EE）
2. 搜索城市主要景点
3. 将景点添加到列表
4. 为每个景点添加格式化备注

## 备注格式

```
#序号 英文名 | 时长 | 费用
```

示例：
- `#1 Vasa Museum | 2h | SEK190`
- `#2 Gamla Stan | 1h | free`
- `#3 City Hall | 45min | SEK150`

## 操作步骤

### 1. 创建列表

1. 打开 Google Maps
2. 点击侧边栏"已保存"
3. 点击"新建列表"
4. 输入国家代码（如 SE、FI、EE）作为列表名称
5. 点击"制作"

### 2. 添加地点

**方法 A：列表内添加（推荐）**
1. 打开目标列表
2. 点击"添加地点"
3. 在搜索框输入景点名称
4. 点击搜索结果添加

**方法 B：从地点详情添加**
1. 搜索景点名称
2. 打开地点详情页
3. 点击"保存"按钮
4. 选择目标列表

### 3. 添加备注

1. 在列表中点击地点下方的"添加备注"
2. 输入格式化备注：`#序号 英文名 | 时长 | 费用`
3. 点击下一个地点继续

## 常见城市景点参考

### 斯德哥尔摩 (SE)

| # | 地点 | 时长 | 费用 |
|---|---|---|---|
| 1 | Gamla Stan | 1h | free |
| 2 | Royal Palace | 45min | SEK200 |
| 3 | City Hall | 45min | SEK150 |
| 4 | Vasa Museum | 2h | SEK190 |
| 5 | ABBA Museum | 1.5h | SEK295 |
| 6 | Skansen | 2h | SEK225 |
| 7 | Fotografiska | 1h | SEK175 |
| 8 | Stockholm Cathedral | 20min | SEK80 |
| 9 | Monteliusvägen | 15min | free |
| 10 | Östermalms Saluhall | 1h | free |
| 11 | Moderna Museet | 1.5h | free |
| 12 | Djurgården | 1h | free |

### 赫尔辛基 (FI)

| # | 地点 | 时长 | 费用 |
|---|---|---|---|
| 1 | Helsinki Cathedral | 30min | free |
| 2 | Market Square | 1h | free |
| 3 | Suomenlinna | 3h | free |
| 4 | Temppeliaukio Church | 30min | €5 |
| 5 | Sibelius Monument | 15min | free |
| 6 | Uspenski Cathedral | 20min | free |
| 7 | Design Museum | 1h | €15 |
| 8 | National Museum | 2h | €18 |
| 9 | Oodi Library | 1h | free |
| 10 | Esplanadi | 1h | free |
| 11 | Old Market Hall | 30min | free |

### 塔林 (EE)

| # | 地点 | 时长 | 费用 |
|---|---|---|---|
| 1 | Old Town | 2h | free |
| 2 | Town Hall Square | 30min | free |
| 3 | Alexander Nevsky Cathedral | 20min | free |
| 4 | St. Olaf's Church | 30min | €5 |
| 5 | Toompea Hill | 1h | free |
| 6 | Kalamaja | 1h | free |
| 7 | Telliskivi | 1h | free |
| 8 | Kadriorg Park | 1h | free |
| 9 | Seaplane Harbour | 1.5h | €15 |
| 10 | Rotermann Quarter | 30min | free |

## 地理位置和游览效率排序

备注序号应按**最佳游览路线**排列，而非随意编号。原则：

### 排序原则

1. **机场/车站出发**：从交通枢纽开始，顺时针或单向路线
2. **地理位置相近**：同一区域的景点连续编号
3. **时间效率**：上午户外，下午室内（博物馆）
4. **步行可达**：相邻景点步行距离内
5. **可选景点靠后**：时间充裕才去的景点编号靠后

### 示例：奥斯陆一日游（机场出发）

**上午（市中心步行环线）**
| # | 地点 | 时长 | 说明 |
|---|---|---|---|
| 1 | Opera House | 45min | 机场快线→中央车站，步行5分钟，登顶看峡湾 |
| 2 | Karl Johans gate | 1h | 主街漫步，通往王宫 |
| 3 | City Hall | 30min | 诺贝尔和平奖颁发地 |
| 4 | Akershus Fortress | 1.5h | 海边城堡，俯瞰峡湾 |
| 5 | Aker Brygge | 1h | 码头午餐、购物 |

**下午（比格多半岛博物馆群）**
| # | 地点 | 时长 | 说明 |
|---|---|---|---|
| 6 | Fram Museum | 1.5h | 极地探险船，渡轮/公交30路 |
| 7 | Viking Ship Museum | 1h | 同区域，⚠️暂停营业可跳过 |
| 8 | Vigeland Park | 1h | 回市区，雕塑公园 |

**傍晚/可选**
| # | 地点 | 时长 | 说明 |
|---|---|---|---|
| 9 | National Museum | 2h | 蒙克《呐喊》在此 |
| 10 | Munch Museum | 1.5h | 新馆，可选 |
| 11 | Holmenkollen | 1h | 跳台滑雪场，较远，时间充裕再去 |

### 路线说明

- **机场→市中心**：Flytoget 快线 19 分钟到中央车站
- **上午**：中央车站周边步行可达，歌剧院→主街→市政厅→城堡→码头
- **下午**：渡轮或公交 30 路去比格多半岛，Fram + Viking Ship 同区域
- **返回**：比格多半岛→市区→Vigeland Park 或 National Museum
- **总时长**：约 8-9 小时（不含 Holmenkollen）

## 注意事项

- 列表名称使用两位国家代码（ISO 3166-1 alpha-2）
- 备注使用英文景点名称，方便国际旅行使用
- 时长使用 h（小时）或 min（分钟）
- 免费景点标注 `free`
- 收费景点使用当地货币（SEK、€、NOK 等）
- 备注添加后刷新页面验证保存成功
- **序号按游览路线排列**，而非景点重要性或字母顺序
