# 日本麻将点数计算程序 - 项目分析文档

## 1. 项目概述

**仓库**: https://github.com/baochi4/mahjong  
**语言**: Python 3  
**核心文件**: `app.py`（Web 服务）、`mahjong_scoring.py`（计算引擎）  
**功能**: 根据役种、番数、符数、位次等计算日本麻将（日麻）点数

### 核心能力

| 功能 | 描述 |
|------|------|
| 基本点计算 | 基于番数×符数公式计算基本点 |
| 满贯及以上判定 | 满贯(5番)、跳满(6-7番)、倍满(8-10番)、三倍满(11-12番)、役满(13番+) |
| 亲家/子家区分 | 亲家1.5倍、子家1倍的不同支付倍率 |
| 自摸/荣和区分 | 自摸分摊支付 vs 荣和一人全额支付 |
| 役满/多重役满 | 单倍~N倍役满的基本点计算 |
| 符数计算器 | 底符+面子符+雀头符+待ち符+自摸符的完整符数计算 |
| 顺位马计算 | ウマ/オカ顺位点与最终得点计算 |
| 速查表 | 常见番符组合的点数一览表 |
| 交互模式 | 命令行交互式输入计算 |

---

## 2. 项目结构

项目根目录（已推送到 GitHub：**https://github.com/baochi4/mahjong**）：

```
mahjong/
├── app.py                 # Flask Web 服务（API 路由 + 静态页面托管）
├── mahjong_scoring.py     # 核心计算引擎（役种枚举 / 符数 / 点数 / 顺位马）
├── static/
│   └── index.html         # 单页前端（算点 / 役种算番 / 符数计算 / 训练出题）
├── test_api.py            # 接口与规则校准测试（python3 test_api.py 全绿）
├── run_demo.py            # 命令行演示脚本
├── requirements.txt       # 依赖：flask, flask-cors
├── Procfile               # Web 进程：python app.py
├── runtime.txt            # Python 3.11
├── render.yaml            # Render 云部署配置（自动识别）
├── .gitignore
└── README.md
```

### 核心模块组成（mahjong_scoring.py）

- 枚举：`Wind` / `WinType` / `PlayerPosition` / `Yaku`（役种，含番数与役满标记）
- 满贯表：`MANGAN_TABLE` + `get_mangan_base()`
- 基本点：`calculate_base_point()`（符×2^(番+2)，切上满贯）
- 支付点数：`calculate_payment()`（亲/子 × 自摸/荣和 四种支付）
- 符数计算：`FuCalculator.calculate()`（底符 / 门清荣和+10 / 自摸+2 / 平和型自摸20符 / 副露荣和最低30符）
- 顺位马：`calculate_rank_bonus()`（ウマ/オカ 最终得点）
- 综合入口：`calculate_score()` / `calculate_from_yaku()`（役种复合 + 门清限定役不计 + 副露减番）

---

## 3. 核心算法详解

### 3.1 基本点计算公式

日麻点数计算的核心公式：

```
基本点 = 符数 × 2^(番数+2)
```

然后将基本点**向上取整到百位**（切り上げ）。

**示例**: 3番30符 → 30 × 2^5 = 30 × 32 = 960 → 切上 → 1000

### 3.2 满贯切上规则

当1~4番的计算基本点 ≥ 2000 时，自动升为满贯：

| 条件 | 结果 |
|------|------|
| 4番30符以上 | 满贯(切上) |
| 3番60符以上 | 满贯(切上) |

### 3.3 满贯及以上点数表

| 名称 | 番数范围 | 基本点 |
|------|----------|--------|
| 通常 | 1~4番 | 符×2^(番+2) |
| 满贯 | 5番 | 2000 |
| 跳满 | 6~7番 | 3000 |
| 倍满 | 8~10番 | 4000 |
| 三倍满 | 11~12番 | 6000 |
| 役满 | 13番+ | 8000 |
| N倍役满 | 役满×N | 8000×N |

### 3.4 支付点数规则

#### 荣和（放铳者一人全额支付）

| 角色 | 支付 |
|------|------|
| **亲家荣和** | 放铳者支付: 基本点 × 6 (即 基本点×3 再向上取整到百位) |
| **子家荣和** | 放铳者支付: 基本点 × 4 (向上取整到百位) |

> ⚠️ 注意：亲家荣和的正确公式是 `ceil_100(基本点 × 3)`，代码中当前实现为 `ceil_100(base * 3)`，对于满贯及以上情况，亲家荣和 = 2000×3=6000, 3000×3=9000 等，符合规则。

#### 自摸（三家分摊支付）

| 角色 | 亲家支付 | 子家支付 |
|------|----------|----------|
| **亲家自摸** | — | 每人: ceil_100(基本点 / 3) |
| **子家自摸** | ceil_100(基本点 / 2) | 每人: ceil_100(基本点 / 4) |

### 3.5 符数计算

符数由以下部分累加后向上取整到十位：

| 组成部分 | 符数 |
|----------|------|
| **底符** | 20（门前荣和/自摸）、30（副露荣和） |
| **门前自摸** | +2 |
| **顺子** | +0 |
| **刻子（中张/明）** | +2 |
| **刻子（中张/暗）** | +4 |
| **刻子（幺九/明）** | +4 |
| **刻子（幺九/暗）** | +8 |
| **杠子（中张/明）** | +8 |
| **杠子（中张/暗）** | +16 |
| **杠子（幺九/明）** | +16 |
| **杠子（幺九/暗）** | +32 |
| **雀头（役牌）** | +2 |
| **雀头（自风兼场风）** | +4 |
| **待ち（嵌张/边张/单骑）** | +2 |
| **待ち（两面/双碰）** | +0 |

> 特殊：七对子固定25符

### 3.6 顺位马（ウマ/オカ）计算

```
最终得点 = (得点 - 返点) + 顺位马 + 一位赏(仅1位)
```

默认配置：
- **顺位马**: [20, 10, -10, -20]（×1000转为点数）
- **一位赏(オカ)**: 20000
- **返点**: 30000

---

## 4. 役种一览

共 **49 个役种枚举**（含 4 个双倍役满变体）。副露规则分两类：**门清限定役**——副露时直接不计；**减番役**——副露时各 −1 番（减到 0 则该役不计）。

### 一番役（15 种）

| 役种 | 番数 | 属性 | 代码常量 |
|------|------|------|----------|
| 立直 | 1 | 门清限定 | `RIICHI` |
| 一发 | 1 | 门清限定 | `IPPATSU` |
| 门前清自摸和 | 1 | 门清限定 | `TSUMO` |
| 平和 | 1 | 门清限定 | `PINFU` |
| 一杯口 | 1 | 门清限定 | `IIPEIKOU` |
| 断幺九 | 1 | 无限制 | `TANYAO` |
| 场风 | 1 | 无限制 | `HONBA` |
| 自风 | 1 | 无限制 | `JIKAZE` |
| 三元牌 白 | 1 | 无限制 | `SANGEN_HAKU` |
| 三元牌 发 | 1 | 无限制 | `SANGEN_HATSU` |
| 三元牌 中 | 1 | 无限制 | `SANGEN_CHUN` |
| 枪杠 | 1 | 无限制 | `CHANKAN` |
| 岭上开花 | 1 | 无限制 | `RINSHAN` |
| 海底捞月 | 1 | 无限制 | `HAITEI` |
| 河底捞鱼 | 1 | 无限制 | `HOUTEI` |

### 二番役（10 种）

| 役种 | 番数 | 属性 | 代码常量 |
|------|------|------|----------|
| 七对子 | 2 | 门清限定 | `CHIITOITSU` |
| 两立直 | 2 | 门清限定 | `DOUBLE_RIICHI` |
| 混全带幺九 | 2 | 副露 −1番 | `CHANTA` |
| 混老头 | 2 | 无限制 | `HONROUTOU` |
| 三色同顺 | 2 | 副露 −1番 | `SANSHOKU_DOUJUN` |
| 三色同刻 | 2 | 无限制 | `SANSHOKU_DOUKOU` |
| 一气通贯 | 2 | 副露 −1番 | `IKKITSUKAN` |
| 三杠子 | 2 | 无限制 | `SANKANTSU` |
| 对对和 | 2 | 无限制 | `TOITOI` |
| 三暗刻 | 2 | 无限制 | `SANANKOU` |

### 三番役 / 六番役 / 满贯役

| 役种 | 番数 | 属性 | 代码常量 |
|------|------|------|----------|
| 混一色 | 3 | 副露 −1番 | `HONITSU` |
| 纯全带幺九 | 3 | 副露 −1番 | `JUNCHAN` |
| 二盃口 | 3 | 门清限定 | `RYANPEIKOU` |
| 清一色 | 6 | 副露 −1番 | `CHINITSU` |
| 流局满贯 | 5（满贯） | 无限制 | `RYUUKYOKU_MANGAN` |

### 役满（15 种）与双倍役满（4 种）

| 役种 | 番数 | 备注 | 代码常量 |
|------|------|------|----------|
| 国士无双 | 13 | 役满 | `KOKUSHI` |
| 四暗刻 | 13 | 役满 | `SUUANKOU` |
| 四暗刻单骑 | 13 | 役满 | `SUUANKOU_TANKI` |
| 国士无双十三面 | 13 | 役满（双倍） | `KOKUSHI_13` |
| 九莲宝灯 | 13 | 役满 | `CHUREN` |
| 纯正九莲宝灯 | 13 | 役满（双倍） | `CHUREN_9` |
| 大三元 | 13 | 役满（双倍） | `DAISANGEN` |
| 小四喜 | 13 | 役满 | `SHOUSUUSHII` |
| 大四喜 | 13 | 役满（双倍） | `DAISUUSHII` |
| 字一色 | 13 | 役满 | `TSUUIISOU` |
| 绿一色 | 13 | 役满 | `RYUUIISOU` |
| 清老头 | 13 | 役满 | `CHINROUTOU` |
| 四杠子 | 13 | 役满（双倍） | `SUUKANTSU` |
| 天和 | 13 | 役满 | `TENHOU` |
| 地和 | 13 | 役满 | `CHIIHOU` |

> 双倍役满：大三元、大四喜、四杠子、纯正九莲宝灯 四者另有 **26 番（双倍）** 变体（`*_DOUBLE` 常量，如 `DAISANGEN_DOUBLE`），与上方 13 番基础役合计计入 49 个枚举成员。

---

## 5. 运行示例

### 示例1: 子家 3番30符 荣和
```
基本点 = 30 × 2^5 = 960 → 切上 → 1000
子家荣和 = 1000 × 4 = 4000
→ 放铳者支付: 4000点
```

### 示例2: 亲家 满贯 自摸
```
基本点 = 2000 (满贯)
亲家自摸 = 每子家 ceil_100(2000/3) = 700
→ 总计获得: 700 × 3 = 2100点
```

### 示例3: 子家 役满 荣和
```
基本点 = 8000 (役满)
子家荣和 = 8000 × 4 = 32000
→ 放铳者支付: 32000点
```

### 示例4: 亲家 双倍役满 自摸
```
基本点 = 16000 (双倍役满)
亲家自摸 = 每子家 ceil_100(16000/3) = 5400
→ 总计获得: 5400 × 3 = 16200点
```

### 示例5: 子家 1番40符 自摸
```
基本点 = 40 × 2^3 = 320 → 切上 → 400
子家自摸: 亲家 = ceil_100(400/2) = 200, 子家 = ceil_100(400/4) = 100
→ 总计获得: 200 + 100 × 2 = 400点
```

### 示例6: 顺位马计算
```
位次  得点    顺位马    最终
1位   45000   +20000   +55000
2位   30000   +10000   +10000
3位   20000   -10000   -20000
4位   5000    -20000   -45000
```

---

## 6. API 参考

### `calculate_score(han, fu, is_dealer, win_type, is_yakuman, yakuman_count, verbose)`

综合点数计算入口。

| 参数 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| `han` | int | 必填 | 番数 |
| `fu` | int | 20 | 符数 |
| `is_dealer` | bool | False | 是否亲家 |
| `win_type` | WinType | WinType.RON | 和牌方式 |
| `is_yakuman` | bool | False | 是否役满 |
| `yakuman_count` | int | 0 | 役满倍数 |
| `verbose` | bool | True | 是否打印详情 |

**返回**: `Dict` - 包含 base, name, total, dealer_payment, child_payment, ron_payment 等字段

### `calculate_base_point(han, fu, is_yakuman, yakuman_count)`

计算基本点。

**返回**: `Tuple[int, str]` - (基本点, 点数名称)

### `calculate_payment(han, fu, is_dealer, win_type, is_yakuman, yakuman_count)`

计算支付点数分配。

**返回**: `Dict[str, int]` - 各方支付详情

### `FuCalculator.calculate(win_type, is_menzen, wait_type, pair_type, mianzi)`

符数计算器。

**返回**: `int` - 符数（向上取整到十位）

### `calculate_rank_bonus(positions, uma, oka, return_point)`

顺位马计算。

**返回**: `List[Tuple[PlayerPosition, int, int, int]]` - [(位次, 得点, 顺位马, 最终得点), ...]

### `print_quick_reference()`

打印常见点数速查表。

### `interactive_mode()`

命令行交互式计算模式。

---

## 7. 使用方式

### 方式一: 直接运行（演示+交互）
```bash
python3 mahjong_scoring.py
```

### 方式二: 作为模块导入
```python
from mahjong_scoring import calculate_score, WinType

# 子家 3番30符 荣和
result = calculate_score(han=3, fu=30, is_dealer=False, win_type=WinType.RON)
print(result["ron_payment"])  # 4000

# 亲家 役满 自摸
result = calculate_score(han=13, fu=0, is_dealer=True, win_type=WinType.TSUMO,
                         is_yakuman=True, yakuman_count=1)
print(result["child_payment"])  # 每子家支付
```

### 方式三: 使用符数计算器
```python
from mahjong_scoring import FuCalculator, WinType

fu = FuCalculator.calculate(
    win_type=WinType.RON,
    is_menzen=True,
    wait_type="ryanmen",   # 两面听
    pair_type="sangen",    # 三元牌雀头
    mianzi=[
        {"type": "koutsu", "is_yaochu": True, "is_ankan": True},   # 暗刻幺九
        {"type": "shuntsu", "is_yaochu": False, "is_ankan": False},
    ]
)
print(fu)  # 符数
```

---

## 8. 已知限制与改进方向

### 已修复 / 已支持（本项目）
1. **亲家荣和倍率**：已修正为 `基本点 × 6`（如满贯亲家荣和 = 12000 点，役满亲家荣和 = 48000 点）。
2. **自摸支付**：已修正为基于基本点的标准倍数（子家自摸 亲家×2/子家×1，亲家自摸 子家各×2），与荣和总额一致。
3. **七对子**：`FuCalculator.calculate(..., is_chiitoitsu=True)` 直返固定 25 符。
4. **宝牌加番**：`calculate_payment` / `calculate_score` 新增可选 `dora` 参数，非役满时并入番数（如 `4番30符 + dora=1` → 5番满贯）。
5. **切上满贯**：`calculate_base_point` 清理冗余分支，1~4番基本点 ≥2000 即升满贯（如 4番30符、3番60符 → 切上满贯）。
6. **役种复合判定**：`calculate_from_yaku` 支持勾选役种 + 表/里宝牌自动算番；含役满/多重役满叠加；副露处理分两类——**门清限定役**（立直/一发/门前清自摸和/平和/一杯口/七对子/两立直/二盃口）副露直接不计，**减番役**（三色同顺/一气通贯/混全带幺九/混一色/清一色/纯全带幺九）副露各 −1 番；副露后总番为 0 时返回「无役(0番)」。
7. **役种表校准**：对照《日本麻雀役種表(v1.0)》补齐 断幺九(1翻)/三暗刻(2翻)/两立直(2翻)/流局满贯(满贯5番)/天和/地和；另保留标准役 二盃口(3翻,门清限定)；役种总数 49。
8. **符数计算修正**：对照《日本麻雀點數計算(v1.0)》符数表——门清荣和 +10符、自摸 +2符（门清/副露通用）、平和型自摸固定 20符、副露荣和最低 30符。

### 仍待完善（改进方向）
1. 里宝牌/追加宝牌的独立计数 UI（后端已支持，前端可进一步拆分展示）

---

## 9. Web 界面

### 功能概览

提供了美观的现代化 Web 界面，包含 7 个功能标签页：

| 标签页 | 功能 |
|--------|------|
| 🎲 点数计算 | 输入番数/符数/亲家子家/自摸荣和，计算支付点数 |
| 🔢 符数计算 | 根据听牌型/雀头/面子等计算符数 |
| 🏆 顺位马 | 输入四位得点，计算顺位马和最终得点 |
| 📋 速查表 | 常见番符组合的点数一览表 |
| 🎯 训练 | 随机出题、作答、自动校验、连对统计 |
| 🎴 役种一览 | 全部49种役的名称和番数 |
| 🀄 役种算番 | 勾选役种+表/里宝牌+门清/副露，自动算番数/符数/点数 |

### 启动方式

```bash
# 安装依赖
pip install -r requirements.txt

# 启动 Web 服务
python3 app.py

# 访问浏览器
# http://localhost:5001  （macOS 控制中心默认占用 5000，已改用 5001）
```

### API 接口

| 接口 | 方法 | 说明 |
|------|------|------|
| `/api/calculate` | POST | 点数计算 |
| `/api/fu_calculate` | POST | 符数计算 |
| `/api/rank_bonus` | POST | 顺位马计算 |
| `/api/quick_reference` | GET | 速查表数据 |
| `/api/train/generate` | POST | 训练出题（仅返回题目，不返回答案） |
| `/api/yaku_list` | GET | 役种列表 |
| `/api/yaku_score` | POST | 役种复合判定（勾选役种+表/里宝牌算点） |

### API 请求示例

```json
// POST /api/calculate
{
    "han": 3,
    "fu": 30,
    "is_dealer": false,
    "win_type": "ron",
    "is_yakuman": false,
    "yakuman_count": 0
}

// 响应
{
    "success": true,
    "result": {
        "base": 1000,
        "name": "3番30符",
        "total": 4000,
        "ron_payment": 4000,
        "dealer_payment": 0,
        "child_payment": 0
    },
    "descriptions": ["子家荣和 3番30符", "放铳者支付: 4,000点"]
}
```

### 训练出题接口

| 接口 | 方法 | 说明 |
|------|------|------|
| `/api/train/generate` | POST | 随机生成一道训练题目（仅返回题目参数，不含答案） |

请求体：`{"difficulty": "basic" | "advanced"}`（可选，默认 basic）。
- `basic`：1~4番 + 常见符数组合
- `advanced`：在 basic 基础上加入满贯以上(5~12番) 与 役满/多重役满

响应示例：
```json
{
    "success": true,
    "question": {
        "han": 3, "fu": 30, "is_dealer": false,
        "win_type": "ron", "is_yakuman": false, "yakuman_count": 0
    }
}
```
> ⚠️ 响应中**不含任何答案/支付数值**，前端调用 `/api/calculate` 用相同参数自行计算标准答案用于校验，避免答案泄露。

### 部署到云平台（手机 / iOS 不依赖电脑访问）

项目已上线代码仓库：**https://github.com/baochi4/mahjong**（main 分支，部署配置齐全）。

部署配置均已就位：`Procfile`、`runtime.txt`、`render.yaml`、`requirements.txt`，`app.py` 使用 `PORT` / `DEBUG` 环境变量自动适配 Render。

**Render 部署步骤（约 2 分钟）：**
1. 打开 https://render.com → 注册/登录（可用 GitHub 一键登录）。
2. **New → Web Service** → Connect GitHub → 授权后选仓库 **`baochi4/mahjong`**。
3. Render 自动读取 `render.yaml`（Python 3.11、Build `pip install -r requirements.txt`、Start `python app.py`、Free 计划、Health Check `/`），直接点 **Create Web Service**。
4. 构建完成后分配 `https://mahjong-score.onrender.com`，iOS Safari 打开即用，电脑可关机。

> 免费层有冷启动（约 15 分钟无访问后休眠），首次打开稍慢属正常；如需稳定常驻可升级付费计划。

---

## 10. 依赖

### 核心计算（无第三方依赖）
- Python 3.6+（仅使用标准库：`enum`, `typing`）

### Web 界面
- flask >= 3.0
- flask-cors >= 4.0

安装: `pip install -r requirements.txt`
