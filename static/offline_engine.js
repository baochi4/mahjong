/*
 * offline_engine.js
 * 日本麻将算点引擎（纯前端版）—— 由 mahjong_scoring.py 翻译而来
 * 供 offline.html 内联使用，也可在 Node 中 require 进行单元测试。
 */
(function (global) {
  'use strict';

  // ---- 役种枚举（49 个，含 4 个双倍役满变体） ----
  const YAKU_LIST = [
    // 一番役（15）
    { code: 'RIICHI', name: '立直', han: 1, yk: false },
    { code: 'IPPATSU', name: '一发', han: 1, yk: false },
    { code: 'TSUMO', name: '门前清自摸和', han: 1, yk: false },
    { code: 'PINFU', name: '平和', han: 1, yk: false },
    { code: 'IIPEIKOU', name: '一杯口', han: 1, yk: false },
    { code: 'TANYAO', name: '断幺九', han: 1, yk: false },
    { code: 'HONBA', name: '场风', han: 1, yk: false },
    { code: 'JIKAZE', name: '自风', han: 1, yk: false },
    { code: 'SANGEN_HAKU', name: '三元牌 白', han: 1, yk: false },
    { code: 'SANGEN_HATSU', name: '三元牌 发', han: 1, yk: false },
    { code: 'SANGEN_CHUN', name: '三元牌 中', han: 1, yk: false },
    { code: 'CHANKAN', name: '枪杠', han: 1, yk: false },
    { code: 'RINSHAN', name: '岭上开花', han: 1, yk: false },
    { code: 'HAITEI', name: '海底捞月', han: 1, yk: false },
    { code: 'HOUTEI', name: '河底捞鱼', han: 1, yk: false },
    // 二番役（10）
    { code: 'CHIITOITSU', name: '七对子', han: 2, yk: false },
    { code: 'DOUBLE_RIICHI', name: '两立直', han: 2, yk: false },
    { code: 'CHANTA', name: '混全带幺九', han: 2, yk: false },
    { code: 'HONROUTOU', name: '混老头', han: 2, yk: false },
    { code: 'SANSHOKU_DOUJUN', name: '三色同顺', han: 2, yk: false },
    { code: 'SANSHOKU_DOUKOU', name: '三色同刻', han: 2, yk: false },
    { code: 'IKKITSUKAN', name: '一气通贯', han: 2, yk: false },
    { code: 'SANKANTSU', name: '三杠子', han: 2, yk: false },
    { code: 'TOITOI', name: '对对和', han: 2, yk: false },
    { code: 'SANANKOU', name: '三暗刻', han: 2, yk: false },
    // 三番役（3）
    { code: 'HONITSU', name: '混一色', han: 3, yk: false },
    { code: 'JUNCHAN', name: '纯全带幺九', han: 3, yk: false },
    { code: 'RYANPEIKOU', name: '二盃口', han: 3, yk: false },
    // 六番役（1）
    { code: 'CHINITSU', name: '清一色', han: 6, yk: false },
    // 满贯役（1）
    { code: 'RYUUKYOKU_MANGAN', name: '流局满贯', han: 5, yk: false },
    // 役满（15）
    { code: 'KOKUSHI', name: '国士无双', han: 13, yk: true },
    { code: 'SUUANKOU', name: '四暗刻', han: 13, yk: true },
    { code: 'SUUANKOU_TANKI', name: '四暗刻单骑', han: 13, yk: true },
    { code: 'KOKUSHI_13', name: '国士无双十三面', han: 13, yk: true },
    { code: 'CHUREN', name: '九莲宝灯', han: 13, yk: true },
    { code: 'CHUREN_9', name: '纯正九莲宝灯', han: 13, yk: true },
    { code: 'DAISANGEN', name: '大三元', han: 13, yk: true },
    { code: 'SHOUSUUSHII', name: '小四喜', han: 13, yk: true },
    { code: 'DAISUUSHII', name: '大四喜', han: 13, yk: true },
    { code: 'TSUUIISOU', name: '字一色', han: 13, yk: true },
    { code: 'RYUUIISOU', name: '绿一色', han: 13, yk: true },
    { code: 'CHINROUTOU', name: '清老头', han: 13, yk: true },
    { code: 'SUUKANTSU', name: '四杠子', han: 13, yk: true },
    { code: 'TENHOU', name: '天和', han: 13, yk: true },
    { code: 'CHIIHOU', name: '地和', han: 13, yk: true },
    // 双倍役满变体（4）
    { code: 'DAISANGEN_DOUBLE', name: '大三元(双倍)', han: 26, yk: true },
    { code: 'DAISUUSHII_DOUBLE', name: '大四喜(双倍)', han: 26, yk: true },
    { code: 'SUUKANTSU_DOUBLE', name: '四杠子(双倍)', han: 26, yk: true },
    { code: 'CHUREN_DOUBLE', name: '纯正九莲宝灯(双倍)', han: 26, yk: true },
  ];

  const YAKU_MAP = {};
  YAKU_LIST.forEach((y) => { YAKU_MAP[y.name] = { han: y.han, yk: y.yk }; });

  // 门清限定役：副露时直接不计
  const MENZEN_ONLY = new Set(['立直', '一发', '门前清自摸和', '平和', '一杯口', '七对子', '两立直', '二盃口']);
  // 副露减番役种：副露各 −1 番
  const FULOU_REDUCIBLE = new Set(['三色同顺', '一气通贯', '混全带幺九', '混一色', '清一色', '纯全带幺九']);

  const MANGAN_TABLE = [
    [1, 4, '通常', null],
    [5, 5, '满贯', 2000],
    [6, 7, '跳满', 3000],
    [8, 10, '倍满', 4000],
    [11, 12, '三倍满', 6000],
    [13, 999, '役满', 8000],
  ];

  function get_mangan_base(han, is_yakuman, yakuman_count) {
    if (is_yakuman) return 8000 * yakuman_count;
    for (const [low, high, name, base] of MANGAN_TABLE) {
      if (han >= low && han <= high) return base;
    }
    return null;
  }

  function calculate_base_point(han, fu, is_yakuman, yakuman_count) {
    if (is_yakuman) {
      const base = 8000 * yakuman_count;
      let name;
      if (yakuman_count === 1) name = '役满';
      else if (yakuman_count === 2) name = '双倍役满';
      else if (yakuman_count === 3) name = '三倍役满';
      else if (yakuman_count === 4) name = '四倍役满';
      else name = yakuman_count + '倍役满';
      return [base, name];
    }
    if (han >= 13) return [8000, '役满'];
    else if (han >= 11) return [6000, '三倍满'];
    else if (han >= 8) return [4000, '倍满'];
    else if (han >= 6) return [3000, '跳满'];
    else if (han === 5) return [2000, '满贯'];
    else if (han <= 0) throw new Error('番数必须大于0');

    let base = fu * Math.pow(2, han + 2);
    base = Math.floor((base + 99) / 100) * 100;
    if (base >= 2000) return [2000, '满贯(切上)'];
    return [base, han + '番' + fu + '符'];
  }

  function ceil_to_100(v) { return Math.floor((v + 99) / 100) * 100; }

  function calculate_payment(han, fu, is_dealer, win_type, is_yakuman, yakuman_count, dora) {
    is_yakuman = !!is_yakuman;
    yakuman_count = yakuman_count || 0;
    dora = dora || 0;
    if (!is_yakuman) han += dora;

    const [base, name] = calculate_base_point(han, fu, is_yakuman, yakuman_count);
    const result = {
      base: base, name: name, total: 0,
      dealer_payment: 0, child_payment: 0, ron_payment: 0,
      win_type: win_type, is_dealer: is_dealer,
    };

    if (win_type === 'tsumo') {
      if (is_dealer) {
        const per = ceil_to_100(base * 2);
        result.child_payment = per;
        result.total = per * 3;
      } else {
        const dp = ceil_to_100(base * 2);
        const cp = ceil_to_100(base);
        result.dealer_payment = dp;
        result.child_payment = cp;
        result.total = dp + cp * 2;
      }
    } else {
      if (is_dealer) {
        const p = ceil_to_100(base * 6);
        result.ron_payment = p;
        result.total = p;
      } else {
        const p = ceil_to_100(base * 4);
        result.ron_payment = p;
        result.total = p;
      }
    }
    return result;
  }

  const FuCalculator = {
    calculate(win_type, is_menzen, wait_type, pair_type, mianzi, is_chiitoitsu) {
      is_chiitoitsu = !!is_chiitoitsu;
      if (is_chiitoitsu) return 25;

      const pinfu_shape = mianzi.length > 0 &&
        mianzi.every((m) => m.type === 'shuntsu') &&
        wait_type === 'ryanmen' && pair_type === 'none';
      if (win_type === 'tsumo' && pinfu_shape) return 20;

      let fu = 20;
      if (is_menzen && win_type === 'ron') fu += 10;
      if (win_type === 'tsumo') fu += 2;

      for (const mz of mianzi) {
        const t = mz.type;
        const yao = !!mz.is_yaochu;
        const ankan = !!mz.is_ankan;
        if (t === 'koutsu') {
          fu += yao ? (ankan ? 8 : 4) : (ankan ? 4 : 2);
        } else if (t === 'kantsu') {
          fu += yao ? (ankan ? 32 : 16) : (ankan ? 16 : 8);
        }
      }

      const pair_map = { none: 0, yakuhai: 2, sangen: 2, jikaze: 2, bakaze: 2, jikaze_bakaze: 4 };
      fu += pair_map[pair_type] || 0;
      const wait_map = { ryanmen: 0, shanpon: 0, kanchan: 2, penchan: 2, tanki: 2 };
      fu += wait_map[wait_type] || 0;

      fu = Math.floor((fu + 9) / 10) * 10;
      if (!is_menzen && win_type === 'ron' && fu < 30) fu = 30;
      return fu;
    },
  };

  function calculate_rank_bonus(positions, uma, oka, return_point) {
    if (!uma) uma = [20, 10, -10, -20];
    oka = oka == null ? 20000 : oka;
    return_point = return_point == null ? 30000 : return_point;
    const results = [];
    for (let i = 0; i < positions.length; i++) {
      const [pos, score] = positions[i];
      const uma_bonus = uma[i] * 1000;
      let oka_bonus = 0;
      if (i === 0) oka_bonus = oka;
      const return_diff = score - return_point;
      const final = return_diff + uma_bonus + oka_bonus;
      results.push({ pos: pos, score: score, uma_bonus: uma_bonus, final: final });
    }
    return results;
  }

  function calculate_from_yaku(selected_yaku, dora, ura_dora, fu, is_dealer, win_type, is_menzen) {
    dora = dora || 0; ura_dora = ura_dora || 0;
    fu = fu == null ? 20 : fu;
    is_dealer = !!is_dealer;
    win_type = win_type || 'ron';
    is_menzen = is_menzen == null ? true : is_menzen;

    let total_han = 0, yakuman_count = 0;
    const yakuman_names = [];
    const normal_breakdown = [];

    for (const name of selected_yaku) {
      const info = YAKU_MAP[name];
      if (!info) continue;
      const yhan = info.han, yis_yk = info.yk;
      if (yis_yk) {
        yakuman_count += Math.floor(yhan / 13);
        yakuman_names.push(name);
      } else {
        let han = yhan;
        if (!is_menzen) {
          if (MENZEN_ONLY.has(name)) continue;
          if (FULOU_REDUCIBLE.has(name)) {
            han -= 1;
            if (han <= 0) continue;
          }
        }
        total_han += han;
        normal_breakdown.push({ name: name, han: han });
      }
    }

    const is_yakuman = yakuman_count > 0;
    if (selected_yaku.indexOf('七对子') >= 0 && fu < 25) fu = 25;
    if (!is_yakuman) total_han += dora + ura_dora;

    let result;
    if (is_yakuman) {
      result = calculate_payment(0, fu, is_dealer, win_type, true, yakuman_count, 0);
    } else if (total_han <= 0) {
      result = { base: 0, name: '无役(0番)', total: 0, dealer_payment: 0, child_payment: 0, ron_payment: 0 };
    } else {
      result = calculate_payment(total_han, fu, is_dealer, win_type, false, 0, 0);
    }

    result = Object.assign({}, result);
    result.han = is_yakuman ? 0 : total_han;
    result.dora = dora;
    result.ura_dora = ura_dora;
    result.is_menzen = is_menzen;
    result.is_yakuman = is_yakuman;
    result.yakuman_count = yakuman_count;
    result.yakuman_names = yakuman_names;
    result.normal_breakdown = normal_breakdown;
    return result;
  }

  function generate_train_question(difficulty) {
    difficulty = difficulty || 'basic';
    if (difficulty === 'advanced' && Math.random() < 0.15) {
      const yc = [1, 1, 1, 2];
      return {
        han: 13, fu: 0,
        is_dealer: Math.random() < 0.5,
        win_type: Math.random() < 0.5 ? 'tsumo' : 'ron',
        is_yakuman: true,
        yakuman_count: yc[Math.floor(Math.random() * yc.length)],
      };
    }
    let han, fu;
    if (difficulty === 'advanced' && Math.random() < 0.5) {
      const arr = [5, 6, 7, 8, 9, 10, 11, 12];
      han = arr[Math.floor(Math.random() * arr.length)];
      fu = 0;
    } else {
      han = 1 + Math.floor(Math.random() * 4);
      const arr = [20, 25, 30, 40, 50, 60, 70, 80, 100, 110];
      fu = arr[Math.floor(Math.random() * arr.length)];
    }
    return {
      han: han, fu: fu,
      is_dealer: Math.random() < 0.5,
      win_type: Math.random() < 0.5 ? 'tsumo' : 'ron',
      is_yakuman: false, yakuman_count: 0,
    };
  }

  // ---- 端点响应（结构与原 Flask 后端一致） ----
  function fmt(n) { return Number(n).toLocaleString(); }

  function resp_calculate(data) {
    const han = parseInt(data.han, 10) || 1;
    const fu = parseInt(data.fu, 10) || 20;
    const is_dealer = !!data.is_dealer;
    const wt = data.win_type === 'tsumo' ? 'tsumo' : 'ron';
    const is_yakuman = !!data.is_yakuman;
    const yc = parseInt(data.yakuman_count, 10) || 0;
    const is_menzen = data.is_menzen == null ? true : !!data.is_menzen;

    const result = calculate_payment(han, fu, is_dealer, wt, is_yakuman, yc, 0);
    const role = is_dealer ? '亲家' : '子家';
    const input = {
      han: han, fu: fu, is_dealer: is_dealer, role: role,
      win_type: wt, is_yakuman: is_yakuman, yakuman_count: yc, is_menzen: is_menzen,
    };
    const descs = [];
    if (wt === 'tsumo') {
      if (is_dealer) {
        descs.push(`亲家自摸 ${result.name}`);
        descs.push(`子家每人支付: ${fmt(result.child_payment)}点`);
        descs.push(`总计获得: ${fmt(result.total)}点`);
      } else {
        descs.push(`子家自摸 ${result.name}`);
        descs.push(`亲家支付: ${fmt(result.dealer_payment)}点`);
        descs.push(`子家每人支付: ${fmt(result.child_payment)}点`);
        descs.push(`总计获得: ${fmt(result.total)}点`);
      }
    } else {
      if (is_dealer) {
        descs.push(`亲家荣和 ${result.name}`);
        descs.push(`放铳者支付: ${fmt(result.ron_payment)}点`);
      } else {
        descs.push(`子家荣和 ${result.name}`);
        descs.push(`放铳者支付: ${fmt(result.ron_payment)}点`);
      }
    }
    return { success: true, input: input, result: result, descriptions: descs };
  }

  function resp_fu(data) {
    const wt = data.win_type === 'tsumo' ? 'tsumo' : 'ron';
    const is_menzen = !!data.is_menzen;
    const wait_type = data.wait_type || 'ryanmen';
    const pair_type = data.pair_type || 'none';
    const mianzi = data.mianzi || [];
    const fu = FuCalculator.calculate(wt, is_menzen, wait_type, pair_type, mianzi, !!data.is_chiitoitsu);
    return { success: true, fu: fu, win_type: wt, is_menzen: is_menzen, wait_type: wait_type, pair_type: pair_type };
  }

  function resp_rank(data) {
    const scores = data.scores || [30000, 30000, 30000, 30000];
    const uma = data.uma || [20, 10, -10, -20];
    const oka = parseInt(data.oka, 10) || 20000;
    const rp = parseInt(data.return_point, 10) || 30000;
    const POS = ['一位', '二位', '三位', '四位'];
    const positions = POS.map((p, i) => [p, scores[i]]);
    const res = calculate_rank_bonus(positions, uma, oka, rp);
    const results = res.map((r) => ({ position: r.pos, score: r.score, uma_bonus: r.uma_bonus, final: r.final }));
    return { success: true, results: results, uma: uma, oka: oka, return_point: rp };
  }

  function build_quick_reference() {
    const cases = [
      [1, 30], [1, 40], [1, 50],
      [2, 25], [2, 30], [2, 40], [2, 50],
      [3, 20], [3, 25], [3, 30], [3, 40], [3, 60],
      [4, 20], [4, 25], [4, 30],
      [5, 0], [6, 0], [7, 0], [8, 0], [9, 0], [10, 0], [11, 0], [12, 0], [13, 0],
    ];
    const table = [];
    for (const [han, fu] of cases) {
      let label, fu_val;
      if (han >= 5) { label = han + '番'; fu_val = 0; }
      else { label = han + '番' + fu + '符'; fu_val = fu; }
      const rc = calculate_payment(han, fu_val, false, 'ron', false, 0, 0);
      const tc = calculate_payment(han, fu_val, false, 'tsumo', false, 0, 0);
      const rd = calculate_payment(han, fu_val, true, 'ron', false, 0, 0);
      const td = calculate_payment(han, fu_val, true, 'tsumo', false, 0, 0);
      table.push({
        label: label, han: han, fu: fu_val,
        child_ron: rc.ron_payment,
        child_tsumo_dealer: tc.dealer_payment,
        child_tsumo_child: tc.child_payment,
        dealer_ron: rd.ron_payment,
        dealer_tsumo_child: td.child_payment,
        name: rc.name,
      });
    }
    return { success: true, table: table };
  }

  function resp_yaku_list() { return { success: true, yaku_list: YAKU_LIST }; }

  function resp_train(data) {
    return { success: true, question: generate_train_question(data.difficulty || 'basic') };
  }

  function resp_yaku_score(data) {
    const selected = data.selected_yaku || [];
    const dora = parseInt(data.dora, 10) || 0;
    const ura = parseInt(data.ura_dora, 10) || 0;
    const fu = parseInt(data.fu, 10) || 20;
    const is_dealer = !!data.is_dealer;
    const is_menzen = data.is_menzen == null ? true : !!data.is_menzen;
    const wt = data.win_type === 'tsumo' ? 'tsumo' : 'ron';

    const result = calculate_from_yaku(selected, dora, ura, fu, is_dealer, wt, is_menzen);
    const descs = [];
    if (selected.length) descs.push('役种: ' + selected.join('、'));
    if (result.is_yakuman) descs.push(`役满 ×${result.yakuman_count}`);
    else {
      const dt = dora + ura;
      descs.push(`总番数: ${result.han}番` + (dt ? `（含宝牌+${dt}）` : ''));
    }
    descs.push('状态: ' + (is_menzen ? '门清' : '副露（可减番役种各-1番）'));
    descs.push(`符数: ${fu}符`);
    if (wt === 'tsumo') {
      if (is_dealer) descs.push(`子家每人支付: ${fmt(result.child_payment)}点`);
      else {
        descs.push(`亲家支付: ${fmt(result.dealer_payment)}点`);
        descs.push(`子家每人支付: ${fmt(result.child_payment)}点`);
      }
    } else {
      descs.push(`放铳者支付: ${fmt(result.ron_payment)}点`);
    }
    descs.push(`总计获得: ${fmt(result.total)}点`);
    return { success: true, result: result, descriptions: descs };
  }

  function localApi(endpoint, data) {
    data = data || {};
    switch (endpoint) {
      case '/calculate': return resp_calculate(data);
      case '/fu_calculate': return resp_fu(data);
      case '/rank_bonus': return resp_rank(data);
      case '/quick_reference': return build_quick_reference();
      case '/yaku_list': return resp_yaku_list();
      case '/train/generate': return resp_train(data);
      case '/yaku_score': return resp_yaku_score(data);
      default: return { success: false, error: 'unknown endpoint ' + endpoint };
    }
  }

  // 覆盖浏览器 fetch，拦截 /api/* 调用（前端 apiCall 无需改动）
  function setupOffline() {
    if (typeof window === 'undefined' || !window.fetch) return;
    const orig = window.fetch.bind(window);
    window.fetch = function (url, opts) {
      const u = String(url);
      const m = u.match(/\/(calculate|fu_calculate|rank_bonus|quick_reference|yaku_list|train\/generate|yaku_score)(?:[?#]|$)/);
      if (m) {
        const endpoint = '/' + m[1];
        let body = {};
        if (opts && opts.body) {
          try { body = JSON.parse(opts.body); } catch (e) { /* ignore */ }
        }
        const out = localApi(endpoint, body);
        return Promise.resolve(new Response(JSON.stringify(out), {
          status: 200,
          headers: { 'Content-Type': 'application/json' },
        }));
      }
      return orig(url, opts);
    };
  }

  const MJ = {
    YAKU_LIST, YAKU_MAP, calculate_payment, FuCalculator,
    calculate_from_yaku, calculate_rank_bonus, generate_train_question,
    localApi, setupOffline,
  };

  if (typeof module !== 'undefined' && module.exports) module.exports = MJ;
  global.MJ = MJ;

  // 浏览器中加载即生效
  if (typeof window !== 'undefined') { try { setupOffline(); } catch (e) { /* ignore */ } }
})(typeof window !== 'undefined' ? window : globalThis);
