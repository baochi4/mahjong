#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
日麻点数计算器 测试套件
可直接运行: python3 test_api.py
"""
from app import app
from mahjong_scoring import (
    calculate_payment, WinType, FuCalculator, generate_train_question
)

client = app.test_client()


def check(name, cond, detail=''):
    if cond:
        print(f'  ✅ {name} {detail}')
    else:
        print(f'  ❌ {name} {detail}')
        raise AssertionError(f'测试失败: {name} {detail}')


print('=== 核心支付计算（mahjong_scoring）===')
check('子家3番30符荣和 = 4000', calculate_payment(3, 30, False, WinType.RON)['ron_payment'] == 4000)
# 亲家荣和应为 基本点×6（重要修复点）
check('亲家3番30符荣和 = 6000 (base×6)', calculate_payment(3, 30, True, WinType.RON)['ron_payment'] == 6000)
check('亲家满贯荣和 = 12000', calculate_payment(5, 0, True, WinType.RON)['ron_payment'] == 12000)
check('子家自摸3番30符 庄2000/闲1000/总4000',
      calculate_payment(3, 30, False, WinType.TSUMO)['dealer_payment'] == 2000 and
      calculate_payment(3, 30, False, WinType.TSUMO)['child_payment'] == 1000 and
      calculate_payment(3, 30, False, WinType.TSUMO)['total'] == 4000)
check('亲家自摸满贯 闲各4000/总12000',
      calculate_payment(5, 0, True, WinType.TSUMO)['child_payment'] == 4000 and
      calculate_payment(5, 0, True, WinType.TSUMO)['total'] == 12000)
check('役满(子家荣和) = 32000', calculate_payment(13, 0, False, WinType.RON,
      is_yakuman=True, yakuman_count=1)['ron_payment'] == 32000)
check('七对子符数 = 25', FuCalculator.calculate(WinType.RON, True, 'tanki', 'none', [],
      is_chiitoitsu=True) == 25)
check('宝牌: 4番30符+1dora → 满贯子家荣和8000',
      calculate_payment(4, 30, False, WinType.RON, dora=1)['ron_payment'] == 8000)
# 切上满贯
check('切上满贯: 4番30符子家荣和 = 8000', calculate_payment(4, 30, False, WinType.RON)['ron_payment'] == 8000)

print('\n=== 计算 API ===')
r = client.post('/api/calculate', json={'han': 3, 'fu': 30, 'is_dealer': False, 'win_type': 'ron'}).get_json()
check('计算API: 子家3番30符荣和 = 4000', r['result']['ron_payment'] == 4000, f"got {r['result']['ron_payment']}")

print('\n=== 训练出题 API（严禁泄露答案）===')
for diff in ['basic', 'advanced']:
    r = client.post('/api/train/generate', json={'difficulty': diff}).get_json()
    q = r['question']
    required = {'han', 'fu', 'is_dealer', 'win_type', 'is_yakuman', 'yakuman_count'}
    check(f'[{diff}] 返回必需题目字段', required.issubset(q.keys()))
    leaked = {'ron_payment', 'dealer_payment', 'child_payment', 'total', 'base', 'answer'}
    check(f'[{diff}] 不泄露答案字段', not (leaked & set(q.keys())))
    # 端到端：该题可被计算 API 处理（保证训练可校验）
    calc = client.post('/api/calculate', json={
        'han': q['han'], 'fu': q['fu'], 'is_dealer': q['is_dealer'],
        'win_type': q['win_type'], 'is_yakuman': q['is_yakuman'],
        'yakuman_count': q['yakuman_count'],
    }).get_json()
    check(f'[{diff}] 题目可被计算 API 处理', calc.get('success') and 'result' in calc)

print('\n=== 出题分布（advanced 200 题抽样）===')
import collections
cnt = collections.Counter()
for _ in range(200):
    q = client.post('/api/train/generate', json={'difficulty': 'advanced'}).get_json()['question']
    cnt['役满' if q['is_yakuman'] else ('满贯+' if q['han'] >= 5 else '通常')] += 1
print('  分布:', dict(cnt))
check('advanced 覆盖满贯以上', cnt['满贯+'] > 0)
check('advanced 覆盖役满', cnt['役满'] > 0)

# 纯函数出题可重复调用且不抛异常
for _ in range(100):
    generate_train_question('basic')
    generate_train_question('advanced')

print('\n=== 役种复合判定 ===')
from mahjong_scoring import calculate_from_yaku
# 立直+平和+纯全带幺九(3番)+宝牌1 = 6番跳满 -> 子家荣和 12000
r = calculate_from_yaku(['立直', '平和', '纯全带幺九'], dora=1, fu=30, is_dealer=False, win_type=WinType.RON)
check('立直+平和+纯全带幺九+宝牌1 = 6番跳满子荣12000', r['total'] == 12000, f"got {r['total']}")
# 大三元 -> 役满
r = calculate_from_yaku(['大三元'], is_dealer=False, win_type=WinType.RON)
check('大三元 = 役满子荣32000', r['is_yakuman'] and r['total'] == 32000)
# 大三元(双倍) -> 双倍役满
r = calculate_from_yaku(['大三元(双倍)'], is_dealer=False, win_type=WinType.RON)
check('大三元(双倍) = 双倍役满子荣64000', r['total'] == 64000 and r['yakuman_count'] == 2)
# 大三元 + 字一色 -> 双役满叠加
r = calculate_from_yaku(['大三元', '字一色'], is_dealer=False, win_type=WinType.RON)
check('大三元+字一色 = 双役满64000', r['total'] == 64000 and r['yakuman_count'] == 2)
# 役满不计宝牌
r = calculate_from_yaku(['大三元'], dora=5, is_dealer=False, win_type=WinType.RON)
check('役满不计宝牌 仍32000', r['total'] == 32000)
# 七对子固定25符
r = calculate_from_yaku(['七对子'], fu=20, is_dealer=False, win_type=WinType.RON)
check('七对子固定25符 子荣1600', r['total'] == 1600)
# 接口
y = client.post('/api/yaku_score', json={'selected_yaku': ['立直', '门前清自摸和'], 'fu': 20, 'is_dealer': False, 'win_type': 'tsumo'}).get_json()
check('/api/yaku_score 立直+自摸 子自摸总1600', y['success'] and y['result']['total'] == 1600, str(y.get('result', {}).get('total')))

# 副露：门清限定役直接不计（非减番）
r = calculate_from_yaku(['平和', '立直'], is_menzen=True)
check('平和+立直 门清=2番', r['han'] == 2)
r = calculate_from_yaku(['平和', '立直'], is_menzen=False)
check('平和+立直 副露=0番(门清限定役均不计)', r['han'] == 0 and r['total'] == 0)
r = calculate_from_yaku(['门前清自摸和'], is_menzen=False)
check('门前清自摸和 副露不计(无役)', r['han'] == 0 and r['total'] == 0)
r = calculate_from_yaku(['立直'], is_menzen=False)
check('立直 副露不计(无役)', r['han'] == 0 and r['total'] == 0)

# 副露减番役种：各 -1 番
r = calculate_from_yaku(['纯全带幺九'], is_menzen=True)
check('纯全带幺九 门清=3番', r['han'] == 3)
r = calculate_from_yaku(['纯全带幺九'], is_menzen=False)
check('纯全带幺九 副露=2番', r['han'] == 2)
r = calculate_from_yaku(['清一色'], is_menzen=False)
check('清一色 副露=5番', r['han'] == 5)
r = calculate_from_yaku(['三色同顺', '一气通贯'], is_menzen=False)
check('三色同顺+一气通贯 副露=2番(各-1)', r['han'] == 2)
y = client.post('/api/yaku_score', json={'selected_yaku': ['混一色'], 'is_menzen': False}).get_json()
check('/api/yaku_score 混一色副露=2番子荣1600', y['success'] and y['result']['han'] == 2 and y['result']['total'] == 1600, str(y.get('result')))

# === 役种表校准（对照 日本麻雀役種表 v1.0） ===
r = calculate_from_yaku(['断幺九'], is_menzen=False)
check('断幺九(1番) 副露不减番', r['han'] == 1)
r = calculate_from_yaku(['三暗刻'], is_menzen=False)
check('三暗刻(2番) 副露不减番', r['han'] == 2)
r = calculate_from_yaku(['两立直'], is_menzen=False)
check('两立直(2番门清限定) 副露不计', r['han'] == 0)
r = calculate_from_yaku(['二盃口'], is_menzen=False)
check('二盃口(3番门清限定) 副露不计', r['han'] == 0)
r = calculate_from_yaku(['天和'], is_dealer=False)
check('天和 = 役满子荣32000', r['is_yakuman'] and r['total'] == 32000)
r = calculate_from_yaku(['地和'], is_dealer=False)
check('地和 = 役满子荣32000', r['is_yakuman'] and r['total'] == 32000)
r = calculate_from_yaku(['流局满贯'], fu=30)
check('流局满贯 = 满贯子荣8000', r['total'] == 8000)

# === 符数校准（对照 日本麻雀點數計算 v1.0 符数表） ===
shuntsu4 = [{'type': 'shuntsu'}] * 4
fu = FuCalculator.calculate(WinType.RON, True, 'ryanmen', 'none', shuntsu4)
check('门清荣和平和型 = 30符(底20+门清10)', fu == 30)
fu = FuCalculator.calculate(WinType.TSUMO, True, 'ryanmen', 'none', shuntsu4)
check('门清自摸平和型 = 20符(特例)', fu == 20)
fu = FuCalculator.calculate(WinType.RON, False, 'ryanmen', 'none', shuntsu4)
check('副露荣和平和型 = 30符(最低30)', fu == 30)
fu = FuCalculator.calculate(WinType.TSUMO, False, 'ryanmen', 'none', shuntsu4)
check('副露自摸平和型 = 20符(特例)', fu == 20)
fu = FuCalculator.calculate(WinType.TSUMO, False, 'ryanmen', 'none',
    [{'type': 'shuntsu'}] * 3 + [{'type': 'koutsu', 'is_yaochu': False, 'is_ankan': False}])
check('副露自摸中张明刻 = 30符(20+2+2)', fu == 30)
fu = FuCalculator.calculate(WinType.TSUMO, True, 'ryanmen', 'none',
    [{'type': 'shuntsu'}] * 3 + [{'type': 'koutsu', 'is_yaochu': True, 'is_ankan': True}])
check('门清自摸幺九暗刻 = 30符(20+2+8)', fu == 30)
fu = FuCalculator.calculate(WinType.RON, True, 'tanki', 'sangen',
    [{'type': 'koutsu', 'is_yaochu': True, 'is_ankan': False}] * 3 + [{'type': 'shuntsu'}])
check('门清荣和幺九明刻x3+三元雀头单骑 = 50符(20+10+12+2+2)', fu == 50)

print('\n✅ 所有测试通过!')
