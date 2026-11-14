#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
日本麻将点数计算程序
根据役种、番数、符数、位次等计算日麻点数

支持功能:
1. 基本点计算（番数×符数）
2. 满贯及以上特殊点数（满贯、跳满、倍满、三倍满、役满、多重役满）
3. 亲家/子家区分
4. 自摸/荣和区分
5. 一发、里宝牌等额外加番
6. 支付点数分配（自摸时各家分摊）
7. 顺位马（顺位点）计算
"""

from enum import Enum
from typing import Optional, Tuple, Dict, List
import random


# ============================================================
#   枚举定义
# ============================================================

class Wind(Enum):
    """风位（自风）"""
    EAST = "东"    # 亲家
    SOUTH = "南"
    WEST = "西"
    NORTH = "北"


class WinType(Enum):
    """和牌方式"""
    TSUMO = "自摸"
    RON = "荣和"


class PlayerPosition(Enum):
    """位次（1st~4th）"""
    FIRST = 1
    SECOND = 2
    THIRD = 3
    FOURTH = 4


# ============================================================
#   役种定义（含番数）
# ============================================================

class Yaku:
    """
    役种定义
    每个役包含: 名称, 基础番数, 是否为役满, 是否有门前清限定等
    """

    # ---- 一番役 ----
    RIICHI = ("立直", 1, False)
    IPPATSU = ("一发", 1, False)
    TSUMO = ("门前清自摸和", 1, False)
    PINFU = ("平和", 1, False)
    IIPEIKOU = ("一杯口", 1, False)
    HONBA = ("场风", 1, False)
    JIKAZE = ("自风", 1, False)
    SANGEN_HAKU = ("三元牌 白", 1, False)
    SANGEN_HATSU = ("三元牌 发", 1, False)
    SANGEN_CHUN = ("三元牌 中", 1, False)
    CHANKAN = ("枪杠", 1, False)
    RINSHAN = ("岭上开花", 1, False)
    HAITEI = ("海底捞月", 1, False)
    HOUTEI = ("河底捞鱼", 1, False)
    TANYAO = ("断幺九", 1, False)
    CHIITOITSU = ("七对子", 2, False)

    # ---- 二番役 ----
    CHANTA = ("混全带幺九", 2, False)
    HONROUTOU = ("混老头", 2, False)
    SANSHOKU_DOUJUN = ("三色同顺", 2, False)
    SANSHOKU_DOUKOU = ("三色同刻", 2, False)
    IKKITSUKAN = ("一气通贯", 2, False)
    SANKANTSU = ("三杠子", 2, False)
    TOITOI = ("对对和", 2, False)
    SANANKOU = ("三暗刻", 2, False)
    DOUBLE_RIICHI = ("两立直", 2, False)

    # ---- 三番役 ----
    HONITSU = ("混一色", 3, False)
    JUNCHAN = ("纯全带幺九", 3, False)
    RYANPEIKOU = ("二盃口", 3, False)

    # ---- 六番役 ----
    CHINITSU = ("清一色", 6, False)

    # ---- 满贯役（按满贯 5 番结算） ----
    RYUUKYOKU_MANGAN = ("流局满贯", 5, False)

    # ---- 役满 ----
    KOKUSHI = ("国士无双", 13, True)
    SUUANKOU = ("四暗刻", 13, True)
    DAISANGEN = ("大三元", 13, True)
    SHOUSUUSHII = ("小四喜", 13, True)
    DAISUUSHII = ("大四喜", 13, True)
    TSUUIISOU = ("字一色", 13, True)
    CHINROUTOU = ("清老头", 13, True)
    RYUUIISOU = ("绿一色", 13, True)
    SUUKANTSU = ("四杠子", 13, True)
    CHUREN = ("九莲宝灯", 13, True)
    SUUANKOU_TANKI = ("四暗刻单骑", 13, True)
    KOKUSHI_13 = ("国士无双十三面", 13, True)
    CHUREN_9 = ("纯正九莲宝灯", 13, True)
    TENHOU = ("天和", 13, True)
    CHIIHOU = ("地和", 13, True)

    # ---- 双倍役满 ----
    DAISANGEN_DOUBLE = ("大三元(双倍)", 26, True)
    DAISUUSHII_DOUBLE = ("大四喜(双倍)", 26, True)
    SUUKANTSU_DOUBLE = ("四杠子(双倍)", 26, True)
    CHUREN_DOUBLE = ("纯正九莲宝灯(双倍)", 26, True)

    @classmethod
    def get_info(cls, yaku_name: str) -> Tuple[str, int, bool]:
        """根据役名获取信息"""
        for attr in dir(cls):
            if attr.startswith('_'):
                continue
            val = getattr(cls, attr)
            if isinstance(val, tuple) and val[0] == yaku_name:
                return val
        raise ValueError(f"未知的役种: {yaku_name}")


# ============================================================
#   满贯及以上特殊点数表
# ============================================================

# (番数下限, 番数上限, 名称, 基本点)
MANGAN_TABLE = [
    (1, 4,   "通常",        None),    # 1~4番: 用符数计算
    (5, 5,   "满贯",        2000),
    (6, 7,   "跳满",        3000),
    (8, 10,  "倍满",        4000),
    (11, 12, "三倍满",      6000),
    (13, 999, "役满",       8000),    # 13番以上或役满
]


def get_mangan_base(han: int, is_yakuman: bool = False, yakuman_count: int = 0) -> Optional[int]:
    """
    获取满贯以上的基本点
    返回None表示需要用符数计算
    """
    if is_yakuman:
        return 8000 * yakuman_count

    for low, high, name, base in MANGAN_TABLE:
        if low <= han <= high:
            return base
    return None


# ============================================================
#   基本点计算
# ============================================================

def calculate_base_point(han: int, fu: int, is_yakuman: bool = False, yakuman_count: int = 0) -> Tuple[int, str]:
    """
    计算基本点

    参数:
        han: 番数
        fu: 符数
        is_yakuman: 是否为役满
        yakuman_count: 役满倍数 (1=单倍役满, 2=双倍役满...)

    返回:
        (基本点, 点数名称)
    """
    # 役满判定
    if is_yakuman:
        base = 8000 * yakuman_count
        if yakuman_count == 1:
            return base, "役满"
        elif yakuman_count == 2:
            return base, "双倍役满"
        elif yakuman_count == 3:
            return base, "三倍役满"
        elif yakuman_count == 4:
            return base, "四倍役满"
        else:
            return base, f"{yakuman_count}倍役满"

    # 满贯以上判定
    if han >= 13:
        return 8000, "役满"
    elif han >= 11:
        return 6000, "三倍满"
    elif han >= 8:
        return 4000, "倍满"
    elif han >= 6:
        return 3000, "跳满"
    elif han == 5:
        return 2000, "满贯"
    elif han <= 0:
        raise ValueError("番数必须大于0")

    # 1~4番: 用符数计算
    # 基本点 = 符数 × 2^(番数+2)
    base = fu * (2 ** (han + 2))

    # 切り上げ（向上取整到百位）
    base = ((base + 99) // 100) * 100

    # 切上满贯: 1~4番的基本点达到2000即升级为满贯
    if base >= 2000:
        return 2000, "满贯(切上)"

    return base, f"{han}番{fu}符"


# ============================================================
#   支付点数计算
# ============================================================

def ceil_to_100(value: int) -> int:
    """向上取整到百位"""
    return ((value + 99) // 100) * 100


def calculate_payment(
    han: int,
    fu: int,
    is_dealer: bool,
    win_type: WinType,
    is_yakuman: bool = False,
    yakuman_count: int = 0,
    dora: int = 0,
) -> Dict[str, int]:
    """
    计算支付点数

    参数:
        han: 番数
        fu: 符数
        is_dealer: 是否为亲家（庄家）
        win_type: 和牌方式（自摸/荣和）
        is_yakuman: 是否为役满
        yakuman_count: 役满倍数

    返回:
        dict: {
            'base': 基本点,
            'name': 点数名称,
            'total': 总获得点数,
            'dealer_payment': 亲家支付（自摸时）,
            'child_payment': 子家支付（自摸时）,
            'ron_payment': 荣和支付点数,
            'win_type': 和牌方式,
            'is_dealer': 是否亲家,
        }
    """
    # 宝牌加番（役满不计宝牌加番，按多重役满另行处理）
    if not is_yakuman:
        han += dora

    base, name = calculate_base_point(han, fu, is_yakuman, yakuman_count)

    result = {
        'base': base,
        'name': name,
        'total': 0,
        'dealer_payment': 0,
        'child_payment': 0,
        'ron_payment': 0,
        'win_type': win_type.value,
        'is_dealer': is_dealer,
    }

    if win_type == WinType.TSUMO:
        # 自摸和（基本点 base 已是百位整数）
        #   子家自摸: 亲家支付 base×2，其他子家各支付 base×1（总计 base×4）
        #   亲家自摸: 每个子家各支付 base×2（总计 base×6）
        if is_dealer:
            per_child = ceil_to_100(base * 2)
            result['child_payment'] = per_child
            result['dealer_payment'] = 0
            result['total'] = per_child * 3
        else:
            dealer_pay = ceil_to_100(base * 2)
            child_pay = ceil_to_100(base)
            result['dealer_payment'] = dealer_pay
            result['child_payment'] = child_pay
            result['total'] = dealer_pay + child_pay * 2

    elif win_type == WinType.RON:
        # 荣和
        if is_dealer:
            # 亲家荣和: 放铳者支付 base×6（向上取整到百位）
            payment = ceil_to_100(base * 6)
            result['ron_payment'] = payment
            result['total'] = payment
        else:
            # 子家荣和: 放铳者支付 base×4（向上取整到百位）
            payment = ceil_to_100(base * 4)
            result['ron_payment'] = payment
            result['total'] = payment

    return result


# ============================================================
#   符数计算
# ============================================================

class FuCalculator:
    """
    符数计算器
    符数 = 底符 + 面子符 + 雀头符 + 待ち符 + 自摸符
    """

    BASE_FU_TSUMO = 20   # 自摸底符
    BASE_FU_RON = 20     # 荣和底符（门前）
    BASE_FU_OPEN = 20    # 副露底符

    @staticmethod
    def calculate(
        win_type: WinType,
        is_menzen: bool,
        wait_type: str,           # 'shanpon' | 'kanchan' | 'penchan' | 'tanki' | 'ryanmen'
        pair_type: str,           # 雀头类型: 'none' | 'yakuhai' | 'jikaze' | 'bakaze' | 'sangen'
        mianzi: List[Dict],       # 面子列表: [{'type': 'shuntsu'/'koutsu'/'kantsu', 'tile': 'm'/'p'/'s'/'字', 'is_yaochu': bool, 'is_ankan': bool}]
        is_chiitoitsu: bool = False,  # 七对子: 固定25符
    ) -> int:
        """
        计算符数

        参数:
            win_type: 自摸或荣和
            is_menzen: 是否门前清
            wait_type: 听牌型
                - 'ryanmen': 两面听（0符）
                - 'kanchan': 嵌张听（2符）
                - 'penchan': 边张听（2符）
                - 'tanki': 单骑听（2符）
                - 'shanpon': 双碰听（0符）
            pair_type: 雀头类型
                - 'none': 无役牌雀头（0符）
                - 'yakuhai': 役牌雀头（2符）
                - 'sangen': 三元牌雀头（2符）
                - 'jikaze': 自风雀头（2符）
                - 'bakaze': 场风雀头（2符）
                - 'jikaze_bakaze': 自风兼场风（4符）
            mianzi: 面子列表

        返回:
            符数（向上取整到十位）
        """
        # 七对子固定25符
        if is_chiitoitsu:
            return 25

        # 平和型（全顺子+两面听+无役牌雀头）自摸固定 20符
        # （含「门前平和自摸」「副露平和型自摸」两个特例）
        is_pinfu_shape = (
            all(m.get('type') == 'shuntsu' for m in mianzi)
            and wait_type == 'ryanmen'
            and pair_type == 'none'
        )
        if win_type == WinType.TSUMO and is_pinfu_shape:
            return 20

        fu = 20  # 底符

        # 门前清荣和 +10符
        if is_menzen and win_type == WinType.RON:
            fu += 10

        # 自摸 +2符（门清/副露通用）
        if win_type == WinType.TSUMO:
            fu += 2

        # 面子符
        for mz in mianzi:
            mz_type = mz.get('type', '')
            is_yaochu = mz.get('is_yaochu', False)
            is_ankan = mz.get('is_ankan', False)

            if mz_type == 'koutsu':
                # 刻子
                if is_yaochu:
                    fu += 8 if is_ankan else 4  # 幺九牌
                else:
                    fu += 4 if is_ankan else 2  # 中张牌
            elif mz_type == 'kantsu':
                # 杠子
                if is_yaochu:
                    fu += 32 if is_ankan else 16  # 幺九牌
                else:
                    fu += 16 if is_ankan else 8   # 中张牌
            # 顺子: 0符

        # 雀头符
        pair_fu_map = {
            'none': 0,
            'yakuhai': 2,
            'sangen': 2,
            'jikaze': 2,
            'bakaze': 2,
            'jikaze_bakaze': 4,
        }
        fu += pair_fu_map.get(pair_type, 0)

        # 待ち符
        wait_fu_map = {
            'ryanmen': 0,
            'shanpon': 0,
            'kanchan': 2,
            'penchan': 2,
            'tanki': 2,
        }
        fu += wait_fu_map.get(wait_type, 0)

        # 向上取整到十位
        fu = ((fu + 9) // 10) * 10

        # 副露荣和最低 30符
        if not is_menzen and win_type == WinType.RON and fu < 30:
            fu = 30

        return fu


# ============================================================
#   顺位马（オカ/ウマ）计算
# ============================================================

def calculate_rank_bonus(
    positions: List[Tuple[PlayerPosition, int]],  # [(位次, 得点), ...]
    uma: List[int] = None,  # 顺位马，默认 [20, 10, -10, -20]
    oka: int = 20000,       # 一位赏，默认20000
    return_point: int = 30000,  # 返点
) -> List[Tuple[PlayerPosition, int, int, int]]:
    """
    计算顺位马（最终得点）

    参数:
        positions: [(位次, 得点), ...] 按位次排序
        uma: 顺位马 [1st, 2nd, 3rd, 4th]
        oka: 一位赏
        return_point: 返点

    返回:
        [(位次, 得点, uma_bonus, final_score), ...]
    """
    if uma is None:
        uma = [20, 10, -10, -20]

    results = []
    total_score = sum(p[1] for p in positions)
    oka_total = oka  # 一位赏总额

    for i, (pos, score) in enumerate(positions):
        # 顺位马
        uma_bonus = uma[i] * 1000  # 转换为点数

        # 一位赏（仅1st）
        oka_bonus = 0
        if i == 0:
            oka_bonus = oka_total

        # 返点差
        return_diff = score - return_point

        # 最终得点 = 返点差 + 顺位马 + 一位赏
        final = return_diff + uma_bonus + oka_bonus

        results.append((pos, score, uma_bonus, final))

    return results


# ============================================================
#   综合计算入口
# ============================================================

def calculate_score(
    han: int,
    fu: int = 20,
    is_dealer: bool = False,
    win_type: WinType = WinType.RON,
    is_yakuman: bool = False,
    yakuman_count: int = 0,
    dora: int = 0,
    verbose: bool = True,
) -> Dict:
    """
    综合点数计算

    参数:
        han: 番数
        fu: 符数（默认20符）
        is_dealer: 是否亲家
        win_type: 和牌方式
        is_yakuman: 是否役满
        yakuman_count: 役满倍数
        verbose: 是否打印详细信息

    返回:
        计算结果字典
    """
    result = calculate_payment(han, fu, is_dealer, win_type, is_yakuman, yakuman_count, dora)

    if verbose:
        role = "亲家" if is_dealer else "子家"
        print(f"{'='*50}")
        print(f"  {role} {win_type.value}")
        print(f"  番数: {han}番", end="")
        if not is_yakuman:
            print(f"  符数: {fu}符")
        else:
            print(f"  (役满×{yakuman_count})")
        print(f"  点数名称: {result['name']}")
        print(f"  基本点: {result['base']}")
        print(f"{'='*50}")

        if win_type == WinType.TSUMO:
            if is_dealer:
                print(f"  → 子家每人支付: {result['child_payment']}点")
                print(f"  → 总计获得: {result['total']}点")
            else:
                print(f"  → 亲家支付: {result['dealer_payment']}点")
                print(f"  → 子家每人支付: {result['child_payment']}点")
                print(f"  → 总计获得: {result['total']}点")
        else:
            print(f"  → 放铳者支付: {result['ron_payment']}点")
        print(f"{'='*50}")

    return result


# ============================================================
#   役种复合判定
# ============================================================

# 门清限定役：仅在门前清时成立，副露时直接不成立（不计）
MENZEN_ONLY = {
    "立直", "一发", "门前清自摸和", "平和", "一杯口", "七对子",
    "两立直", "二盃口",
}

# 副露减番役种：门清成立，副露（非门前清）时各减 1 番（减到 0 则该役不计）
FULOU_REDUCIBLE = {
    "三色同顺", "一气通贯",
    "混全带幺九", "混一色", "清一色", "纯全带幺九",
}


def calculate_from_yaku(
    selected_yaku: List[str],
    dora: int = 0,
    ura_dora: int = 0,
    fu: int = 20,
    is_dealer: bool = False,
    win_type: WinType = WinType.RON,
    is_menzen: bool = True,
) -> Dict:
    """
    根据勾选的役种列表自动复合判定，计算总番数/符数/点数

    参数:
        selected_yaku: 役种中文名列表（需与 Yaku 枚举名称一致）
        dora: 表宝牌数量（每个 +1翻）
        ura_dora: 里宝牌数量（每个 +1翻）
        fu: 符数（七对子请传 25）
        is_dealer: 是否亲家
        win_type: 和牌方式
        is_menzen: 是否门前清（副露时部分役种减 1 番）

    返回:
        dict: 含 han/符/役满信息/各支付点数/明细
    """
    total_han = 0
    yakuman_count = 0
    yakuman_names = []
    normal_breakdown = []

    for name in selected_yaku:
        yname, yhan, yis_yk = Yaku.get_info(name)
        if yis_yk:
            # 役满：单倍=13翻、双倍=26翻… 按翻数折算役满倍数
            yakuman_count += yhan // 13
            yakuman_names.append(yname)
        else:
            han = yhan
            if not is_menzen:
                if yname in MENZEN_ONLY:
                    continue  # 门清限定役：副露时直接不成立
                if yname in FULOU_REDUCIBLE:
                    han -= 1  # 减番役：副露 -1 番
                    if han <= 0:
                        continue
            total_han += han
            normal_breakdown.append((yname, han))

    is_yakuman = yakuman_count > 0

    # 七对子固定 25 符（勾选时自动锁定，且七对子必门清）
    if '七对子' in selected_yaku and fu < 25:
        fu = 25

    # 役满成立时宝牌不计（标准规则）
    if not is_yakuman:
        total_han += dora + ura_dora

    if is_yakuman:
        result = calculate_payment(
            0, fu, is_dealer, win_type,
            is_yakuman=True, yakuman_count=yakuman_count,
        )
    elif total_han <= 0:
        # 无役（如副露后所有门清限定役均不成立）
        result = {
            'base': 0, 'name': '无役(0番)', 'total': 0,
            'dealer_payment': 0, 'child_payment': 0, 'ron_payment': 0,
        }
    else:
        result = calculate_payment(total_han, fu, is_dealer, win_type, dora=0)

    result = dict(result)
    result['han'] = 0 if is_yakuman else total_han
    result['dora'] = dora
    result['ura_dora'] = ura_dora
    result['is_menzen'] = is_menzen
    result['is_yakuman'] = is_yakuman
    result['yakuman_count'] = yakuman_count
    result['yakuman_names'] = yakuman_names
    result['normal_breakdown'] = [{'name': n, 'han': h} for n, h in normal_breakdown]
    return result


# ============================================================
#   常见点数速查表
# ============================================================

def print_quick_reference():
    """打印常见点数速查表"""
    print("\n" + "=" * 60)
    print("           日麻点数速查表")
    print("=" * 60)

    header = f"{'番·符':<12} {'子家荣和':<10} {'子家自摸':<16} {'亲家荣和':<10} {'亲家自摸':<16}"
    print(header)
    print("-" * 60)

    # 常见组合
    cases = [
        (1, 30), (1, 40), (1, 50),
        (2, 25), (2, 30), (2, 40), (2, 50),
        (3, 20), (3, 25), (3, 30), (3, 40), (3, 60),
        (4, 20), (4, 25), (4, 30),
        (5, 0),   # 满贯
        (6, 0),   # 跳满
        (7, 0),   # 跳满
        (8, 0),   # 倍满
        (9, 0),
        (10, 0),
        (11, 0),  # 三倍满
        (12, 0),
        (13, 0),  # 役满
    ]

    for han, fu in cases:
        if han >= 5:
            label = f"{han}番"
            fu_val = 0
        else:
            label = f"{han}番{fu}符"
            fu_val = fu

        # 子家荣和
        r_child = calculate_payment(han, fu_val, False, WinType.RON)
        # 子家自摸
        t_child = calculate_payment(han, fu_val, False, WinType.TSUMO)
        # 亲家荣和
        r_dealer = calculate_payment(han, fu_val, True, WinType.RON)
        # 亲家自摸
        t_dealer = calculate_payment(han, fu_val, True, WinType.TSUMO)

        t_child_str = f"{t_child['dealer_payment']}/{t_child['child_payment']}"
        t_dealer_str = f"-/{t_dealer['child_payment']}"

        print(f"{label:<12} {r_child['ron_payment']:<10} {t_child_str:<16} {r_dealer['ron_payment']:<10} {t_dealer_str:<16}")

    print("=" * 60)
    print("注: 自摸格式为 '亲家支付/子家支付'")
    print("    满贯=2000  跳满=3000  倍满=4000  三倍满=6000  役满=8000")
    print("=" * 60)


# ============================================================
#   交互式输入
# ============================================================

def interactive_mode():
    """交互式点数计算"""
    print("\n" + "=" * 50)
    print("  日麻点数计算器（交互模式）")
    print("=" * 50)

    while True:
        print()
        # 役满选择
        yakuman_input = input("是否为役满？(y/n, 默认n): ").strip().lower()
        is_yakuman = yakuman_input == 'y'

        if is_yakuman:
            yakuman_count = int(input("役满倍数 (1=单倍, 2=双倍, 3=三倍, 默认1): ") or "1")
            han = 13
            fu = 0
        else:
            yakuman_count = 0
            han = int(input("请输入番数 (1-12): "))
            if han < 5:
                fu = int(input("请输入符数 (20/25/30/40/50/60/70/80/90/100/110): "))
            else:
                fu = 0

        # 亲家/子家
        dealer_input = input("是否为亲家？(y/n, 默认n): ").strip().lower()
        is_dealer = dealer_input == 'y'

        # 和牌方式
        win_input = input("和牌方式 (1=自摸, 2=荣和, 默认2): ").strip() or "2"
        win_type = WinType.TSUMO if win_input == "1" else WinType.RON

        # 计算
        calculate_score(
            han=han, fu=fu, is_dealer=is_dealer,
            win_type=win_type, is_yakuman=is_yakuman,
            yakuman_count=yakuman_count
        )

        # 继续？
        cont = input("\n继续计算？(y/n, 默认n): ").strip().lower()
        if cont != 'y':
            break

    print("\n感谢使用！")


# ============================================================
#   主函数
# ============================================================

def main():
    """主函数 - 演示各种计算"""

    print("=" * 60)
    print("       日本麻将点数计算程序")
    print("=" * 60)

    # 示例1: 子家 3番30符 荣和
    print("\n【示例1】子家 3番30符 荣和")
    calculate_score(han=3, fu=30, is_dealer=False, win_type=WinType.RON)

    # 示例2: 亲家 满贯 自摸
    print("\n【示例2】亲家 5番 满贯 自摸")
    calculate_score(han=5, fu=0, is_dealer=True, win_type=WinType.TSUMO)

    # 示例3: 子家 役满 荣和
    print("\n【示例3】子家 役满 荣和")
    calculate_score(han=13, fu=0, is_dealer=False, win_type=WinType.RON,
                    is_yakuman=True, yakuman_count=1)

    # 示例4: 亲家 双倍役满 自摸
    print("\n【示例4】亲家 双倍役满 自摸")
    calculate_score(han=13, fu=0, is_dealer=True, win_type=WinType.TSUMO,
                    is_yakuman=True, yakuman_count=2)

    # 示例5: 子家 1番40符 自摸
    print("\n【示例5】子家 1番40符 自摸")
    calculate_score(han=1, fu=40, is_dealer=False, win_type=WinType.TSUMO)

    # 示例6: 亲家 4番25符 荣和
    print("\n【示例6】亲家 4番25符 荣和")
    calculate_score(han=4, fu=25, is_dealer=True, win_type=WinType.RON)

    # 打印速查表
    print()
    print_quick_reference()

    # 顺位马示例
    print("\n【顺位马计算示例】")
    print("-" * 50)
    positions = [
        (PlayerPosition.FIRST, 45000),
        (PlayerPosition.SECOND, 30000),
        (PlayerPosition.THIRD, 20000),
        (PlayerPosition.FOURTH, 5000),
    ]
    results = calculate_rank_bonus(positions, uma=[20, 10, -10, -20], oka=20000, return_point=30000)
    print(f"{'位次':<8} {'得点':<10} {'顺位马':<10} {'最终':<10}")
    print("-" * 40)
    for pos, score, uma_bonus, final in results:
        print(f"  {pos.value}位    {score:<10} {uma_bonus:+<10} {final:+}")

    # 交互模式
    print("\n")
    choice = input("是否进入交互模式？(y/n, 默认n): ").strip().lower()
    if choice == 'y':
        interactive_mode()


def generate_train_question(difficulty: str = 'basic') -> Dict:
    """
    生成一道训练题目（仅返回题目参数，不含答案，避免前端作弊）

    参数:
        difficulty: 'basic' | 'advanced'
            - basic: 1~4番，常见符数组合
            - advanced: 在 basic 基础上加入满贯以上(5~12番)与役满/多重役满

    返回:
        dict: {han, fu, is_dealer, win_type, is_yakuman, yakuman_count}
            win_type 为字符串 'tsumo' / 'ron'
    """
    if difficulty == 'advanced' and random.random() < 0.15:
        # 役满 / 多重役满
        yakuman_count = random.choice([1, 1, 1, 2])
        return {
            'han': 13, 'fu': 0,
            'is_dealer': random.choice([True, False]),
            'win_type': random.choice(['tsumo', 'ron']),
            'is_yakuman': True, 'yakuman_count': yakuman_count,
        }

    if difficulty == 'advanced' and random.random() < 0.5:
        # 满贯以上（非役满）：5~12番，符数不参与
        han = random.choice([5, 6, 7, 8, 9, 10, 11, 12])
        fu = 0
    else:
        # 通常：1~4番，常见符数
        han = random.randint(1, 4)
        fu = random.choice([20, 25, 30, 40, 50, 60, 70, 80, 100, 110])

    return {
        'han': han, 'fu': fu,
        'is_dealer': random.choice([True, False]),
        'win_type': random.choice(['tsumo', 'ron']),
        'is_yakuman': False, 'yakuman_count': 0,
    }


if __name__ == '__main__':
    main()
