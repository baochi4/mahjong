#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
日麻点数计算器 - Web API 服务
提供 RESTful API 供前端调用
"""

from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
from mahjong_scoring import (
    calculate_score, calculate_payment, calculate_base_point,
    calculate_rank_bonus, FuCalculator, generate_train_question,
    calculate_from_yaku,
    WinType, PlayerPosition, Yaku
)

app = Flask(__name__, static_folder='static', static_url_path='')
CORS(app)


@app.route('/')
def index():
    """返回前端页面"""
    return send_from_directory('static', 'index.html')


@app.route('/api/calculate', methods=['POST'])
def api_calculate():
    """
    点数计算 API

    请求体:
    {
        "han": 3,
        "fu": 30,
        "is_dealer": false,
        "win_type": "ron",     // "ron" or "tsumo"
        "is_yakuman": false,
        "yakuman_count": 0
    }
    """
    data = request.get_json()

    try:
        han = int(data.get('han', 1))
        fu = int(data.get('fu', 20))
        is_dealer = bool(data.get('is_dealer', False))
        win_type_str = data.get('win_type', 'ron')
        is_yakuman = bool(data.get('is_yakuman', False))
        yakuman_count = int(data.get('yakuman_count', 0))
        is_menzen = bool(data.get('is_menzen', True))

        win_type = WinType.TSUMO if win_type_str == 'tsumo' else WinType.RON

        # 计算
        result = calculate_payment(
            han=han, fu=fu, is_dealer=is_dealer,
            win_type=win_type, is_yakuman=is_yakuman,
            yakuman_count=yakuman_count
        )

        # 构建响应
        role = "亲家" if is_dealer else "子家"
        response = {
            'success': True,
            'input': {
                'han': han,
                'fu': fu,
                'is_dealer': is_dealer,
                'role': role,
                'win_type': win_type.value,
                'is_yakuman': is_yakuman,
                'yakuman_count': yakuman_count,
                'is_menzen': is_menzen,
            },
            'result': {
                'base': result['base'],
                'name': result['name'],
                'total': result['total'],
                'dealer_payment': result['dealer_payment'],
                'child_payment': result['child_payment'],
                'ron_payment': result['ron_payment'],
            }
        }

        # 构建描述文字
        descriptions = []
        if win_type == WinType.TSUMO:
            if is_dealer:
                descriptions.append(f"亲家自摸 {result['name']}")
                descriptions.append(f"子家每人支付: {result['child_payment']:,}点")
                descriptions.append(f"总计获得: {result['total']:,}点")
            else:
                descriptions.append(f"子家自摸 {result['name']}")
                descriptions.append(f"亲家支付: {result['dealer_payment']:,}点")
                descriptions.append(f"子家每人支付: {result['child_payment']:,}点")
                descriptions.append(f"总计获得: {result['total']:,}点")
        else:
            if is_dealer:
                descriptions.append(f"亲家荣和 {result['name']}")
                descriptions.append(f"放铳者支付: {result['ron_payment']:,}点")
            else:
                descriptions.append(f"子家荣和 {result['name']}")
                descriptions.append(f"放铳者支付: {result['ron_payment']:,}点")

        response['descriptions'] = descriptions

        return jsonify(response)

    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 400


@app.route('/api/fu_calculate', methods=['POST'])
def api_fu_calculate():
    """
    符数计算 API

    请求体:
    {
        "win_type": "ron",
        "is_menzen": true,
        "wait_type": "ryanmen",
        "pair_type": "none",
        "mianzi": [
            {"type": "koutsu", "is_yaochu": true, "is_ankan": true}
        ]
    }
    """
    data = request.get_json()

    try:
        win_type_str = data.get('win_type', 'ron')
        win_type = WinType.TSUMO if win_type_str == 'tsumo' else WinType.RON
        is_menzen = bool(data.get('is_menzen', True))
        wait_type = data.get('wait_type', 'ryanmen')
        pair_type = data.get('pair_type', 'none')
        mianzi = data.get('mianzi', [])

        fu = FuCalculator.calculate(
            win_type=win_type,
            is_menzen=is_menzen,
            wait_type=wait_type,
            pair_type=pair_type,
            mianzi=mianzi
        )

        return jsonify({
            'success': True,
            'fu': fu,
            'win_type': win_type.value,
            'is_menzen': is_menzen,
            'wait_type': wait_type,
            'pair_type': pair_type,
        })

    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 400


@app.route('/api/rank_bonus', methods=['POST'])
def api_rank_bonus():
    """
    顺位马计算 API

    请求体:
    {
        "scores": [45000, 30000, 20000, 5000],
        "uma": [20, 10, -10, -20],
        "oka": 20000,
        "return_point": 30000
    }
    """
    data = request.get_json()

    try:
        scores = data.get('scores', [30000, 30000, 30000, 30000])
        uma = data.get('uma', [20, 10, -10, -20])
        oka = int(data.get('oka', 20000))
        return_point = int(data.get('return_point', 30000))

        positions = [
            (PlayerPosition.FIRST, scores[0]),
            (PlayerPosition.SECOND, scores[1]),
            (PlayerPosition.THIRD, scores[2]),
            (PlayerPosition.FOURTH, scores[3]),
        ]

        results = calculate_rank_bonus(positions, uma=uma, oka=oka, return_point=return_point)

        response_results = []
        for pos, score, uma_bonus, final in results:
            response_results.append({
                'position': pos.value,
                'score': score,
                'uma_bonus': uma_bonus,
                'final': final,
            })

        return jsonify({
            'success': True,
            'results': response_results,
            'uma': uma,
            'oka': oka,
            'return_point': return_point,
        })

    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 400


@app.route('/api/quick_reference', methods=['GET'])
def api_quick_reference():
    """速查表 API"""
    cases = [
        (1, 30), (1, 40), (1, 50),
        (2, 25), (2, 30), (2, 40), (2, 50),
        (3, 20), (3, 25), (3, 30), (3, 40), (3, 60),
        (4, 20), (4, 25), (4, 30),
        (5, 0), (6, 0), (7, 0), (8, 0), (9, 0), (10, 0),
        (11, 0), (12, 0), (13, 0),
    ]

    table = []
    for han, fu in cases:
        if han >= 5:
            label = f"{han}番"
            fu_val = 0
        else:
            label = f"{han}番{fu}符"
            fu_val = fu

        r_child = calculate_payment(han, fu_val, False, WinType.RON)
        t_child = calculate_payment(han, fu_val, False, WinType.TSUMO)
        r_dealer = calculate_payment(han, fu_val, True, WinType.RON)
        t_dealer = calculate_payment(han, fu_val, True, WinType.TSUMO)

        table.append({
            'label': label,
            'han': han,
            'fu': fu_val,
            'child_ron': r_child['ron_payment'],
            'child_tsumo_dealer': t_child['dealer_payment'],
            'child_tsumo_child': t_child['child_payment'],
            'dealer_ron': r_dealer['ron_payment'],
            'dealer_tsumo_child': t_dealer['child_payment'],
            'name': r_child['name'],
        })

    return jsonify({'success': True, 'table': table})


@app.route('/api/yaku_list', methods=['GET'])
def api_yaku_list():
    """役种列表 API"""
    yaku_list = []
    for attr in dir(Yaku):
        if attr.startswith('_'):
            continue
        val = getattr(Yaku, attr)
        if isinstance(val, tuple):
            yaku_list.append({
                'code': attr,
                'name': val[0],
                'han': val[1],
                'is_yakuman': val[2],
            })

    return jsonify({'success': True, 'yaku_list': yaku_list})


@app.route('/api/train/generate', methods=['POST'])
def api_train_generate():
    """训练出题接口：返回随机题目参数（不含答案，避免前端作弊）"""
    data = request.get_json(silent=True) or {}
    difficulty = data.get('difficulty', 'basic')
    if difficulty not in ('basic', 'advanced'):
        difficulty = 'basic'
    question = generate_train_question(difficulty)
    return jsonify({'success': True, 'question': question})


@app.route('/api/yaku_score', methods=['POST'])
def api_yaku_score():
    """役种复合判定 API：根据勾选役种 + 表/里宝牌自动算番与点数"""
    data = request.get_json(silent=True) or {}
    try:
        selected_yaku = data.get('selected_yaku', [])
        dora = int(data.get('dora', 0))
        ura_dora = int(data.get('ura_dora', 0))
        fu = int(data.get('fu', 20))
        is_dealer = bool(data.get('is_dealer', False))
        is_menzen = bool(data.get('is_menzen', True))
        win_type_str = data.get('win_type', 'ron')
        win_type = WinType.TSUMO if win_type_str == 'tsumo' else WinType.RON

        result = calculate_from_yaku(selected_yaku, dora, ura_dora, fu, is_dealer, win_type, is_menzen)

        descriptions = []
        if selected_yaku:
            descriptions.append("役种: " + "、".join(selected_yaku))
        if result['is_yakuman']:
            descriptions.append(f"役满 ×{result['yakuman_count']}")
        else:
            dora_total = dora + ura_dora
            descriptions.append(f"总番数: {result['han']}番" + (f"（含宝牌+{dora_total}）" if dora_total else ""))
        descriptions.append("状态: " + ("门清" if is_menzen else "副露（可减番役种各-1番）"))
        descriptions.append(f"符数: {fu}符")

        if win_type == WinType.TSUMO:
            if is_dealer:
                descriptions.append(f"子家每人支付: {result['child_payment']:,}点")
            else:
                descriptions.append(f"亲家支付: {result['dealer_payment']:,}点")
                descriptions.append(f"子家每人支付: {result['child_payment']:,}点")
        else:
            descriptions.append(f"放铳者支付: {result['ron_payment']:,}点")
        descriptions.append(f"总计获得: {result['total']:,}点")

        return jsonify({
            'success': True,
            'result': result,
            'descriptions': descriptions,
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 400


if __name__ == '__main__':
    # 获取局域网 IP，方便手机在同一 WiFi 下访问
    import socket
    try:
        _s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        _s.connect(('8.8.8.8', 80))
        lan_ip = _s.getsockname()[0]
        _s.close()
    except Exception:
        lan_ip = '127.0.0.1'

    print("=" * 50)
    print("  日麻点数计算器 Web 服务")
    print(f"  本机访问: http://localhost:5000")
    print(f"  手机访问: http://{lan_ip}:5000  (需同一 WiFi)")
    print("=" * 50)
    import os
    port = int(os.environ.get('PORT', 5000))
    debug = os.environ.get('DEBUG', '0') == '1'
    app.run(host='0.0.0.0', port=port, debug=debug)
