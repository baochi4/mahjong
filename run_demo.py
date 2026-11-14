#!/usr/bin/env python3
from mahjong_scoring import *

# 示例1: 子家 3番30符 荣和
print("【示例1】子家 3番30符 荣和")
calculate_score(han=3, fu=30, is_dealer=False, win_type=WinType.RON)

# 示例2: 亲家 满贯 自摸
print("\n【示例2】亲家 5番 满贯 自摸")
calculate_score(han=5, fu=0, is_dealer=True, win_type=WinType.TSUMO)

# 示例3: 子家 役满 荣和
print("\n【示例3】子家 役满 荣和")
calculate_score(han=13, fu=0, is_dealer=False, win_type=WinType.RON, is_yakuman=True, yakuman_count=1)

# 示例4: 亲家 双倍役满 自摸
print("\n【示例4】亲家 双倍役满 自摸")
calculate_score(han=13, fu=0, is_dealer=True, win_type=WinType.TSUMO, is_yakuman=True, yakuman_count=2)

# 示例5: 子家 1番40符 自摸
print("\n【示例5】子家 1番40符 自摸")
calculate_score(han=1, fu=40, is_dealer=False, win_type=WinType.TSUMO)

# 示例6: 亲家 4番25符 荣和
print("\n【示例6】亲家 4番25符 荣和")
calculate_score(han=4, fu=25, is_dealer=True, win_type=WinType.RON)

# 顺位马示例
print("\n【顺位马计算示例】")
positions = [
    (PlayerPosition.FIRST, 45000),
    (PlayerPosition.SECOND, 30000),
    (PlayerPosition.THIRD, 20000),
    (PlayerPosition.FOURTH, 5000),
]
results = calculate_rank_bonus(positions, uma=[20, 10, -10, -20], oka=20000, return_point=30000)
for pos, score, uma_bonus, final in results:
    print(f"  {pos.value}位: 得点={score}, 顺位马={uma_bonus:+}, 最终={final:+}")
