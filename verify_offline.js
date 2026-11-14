/* verify_offline.js —— 对照已知正确值验证 JS 引擎（node verify_offline.js） */
const MJ = require('./static/offline_engine.js');

let pass = 0, fail = 0;
function check(name, cond, extra) {
  if (cond) { pass++; console.log('  ✓ ' + name); }
  else { fail++; console.log('  ✗ ' + name + (extra ? '  -> ' + JSON.stringify(extra) : '')); }
}

// 1. 基础点数
let r = MJ.calculate_payment(3, 30, false, 'ron', false, 0, 0);
check('子家3番30符荣和 total=4000', r.total === 4000 && r.ron_payment === 4000, r);
let r2 = MJ.calculate_payment(3, 30, false, 'tsumo', false, 0, 0);
check('子家3番30符自摸: 亲付2000/子付1000/total4000',
  r2.total === 4000 && r2.dealer_payment === 2000 && r2.child_payment === 1000, r2);
let r3 = MJ.calculate_payment(5, 0, false, 'ron', false, 0, 0);
check('5番满贯子荣=8000', r3.total === 8000 && r3.ron_payment === 8000, r3);
let r4 = MJ.calculate_payment(0, 30, false, 'ron', true, 1, 0);
check('役满子荣=32000', r4.total === 32000, r4);

// 2. 符数
const shuntsu4 = [{ type: 'shuntsu' }, { type: 'shuntsu' }, { type: 'shuntsu' }, { type: 'shuntsu' }];
check('门清荣和平和型=30符', MJ.FuCalculator.calculate('ron', true, 'ryanmen', 'none', shuntsu4) === 30);
check('门清自摸平和型=20符', MJ.FuCalculator.calculate('tsumo', true, 'ryanmen', 'none', shuntsu4) === 20);
check('副露荣和平和型=30符(最低)', MJ.FuCalculator.calculate('ron', false, 'ryanmen', 'none', shuntsu4) === 30);
check('副露自摸平和型=20符', MJ.FuCalculator.calculate('tsumo', false, 'ryanmen', 'none', shuntsu4) === 20);
const mid = [{ type: 'shuntsu' }, { type: 'shuntsu' }, { type: 'shuntsu' }, { type: 'koutsu', is_yaochu: false, is_ankan: false }];
check('副露自摸中张明刻=30符', MJ.FuCalculator.calculate('tsumo', false, 'ryanmen', 'none', mid) === 30);
check('七对子固定25符', MJ.FuCalculator.calculate('ron', true, 'tanki', 'none', [], true) === 25);

// 3. 役种复合 + 副露规则（dora 必须传 0）
let y = MJ.calculate_from_yaku(['平和', '立直'], 0, 0, 30, false, 'ron', true);
check('平和+立直门清=2番', y.han === 2, y);
y = MJ.calculate_from_yaku(['平和', '立直'], 0, 0, 30, false, 'ron', false);
check('平和+立直副露=0番(门清限定不计)', y.han === 0 && y.total === 0, y);
y = MJ.calculate_from_yaku(['门前清自摸和'], 0, 0, 30, false, 'ron', false);
check('门前清自摸和副露无役', y.total === 0, y);
y = MJ.calculate_from_yaku(['断幺九'], 0, 0, 30, false, 'ron', false);
check('断幺九副露=1番(不减番)', y.han === 1, y);
y = MJ.calculate_from_yaku(['纯全带幺九'], 0, 0, 30, false, 'ron', false);
check('纯全带幺九副露=2番', y.han === 2, y);
y = MJ.calculate_from_yaku(['清一色'], 0, 0, 30, false, 'ron', false);
check('清一色副露=5番', y.han === 5, y);
y = MJ.calculate_from_yaku(['三色同顺', '一气通贯'], 0, 0, 30, false, 'ron', false);
check('三色同顺+一气通贯副露=2番', y.han === 2, y);
y = MJ.calculate_from_yaku(['天和'], 0, 0, 30, false, 'ron', true);
check('天和=役满 total=32000', y.is_yakuman && y.total === 32000, y);
y = MJ.calculate_from_yaku(['流局满贯'], 0, 0, 30, false, 'ron', true);
check('流局满贯=满贯 total=8000', y.total === 8000, y);
// 宝牌加番
y = MJ.calculate_from_yaku(['断幺九'], 2, 1, 30, false, 'ron', false);
check('断幺九+表2里1(dora=3)=4番', y.han === 4, y);

// 4. localApi 端点
let a = MJ.localApi('/calculate', { han: 3, fu: 30, is_dealer: false, win_type: 'ron' });
check('localApi /calculate', a.success && a.result.total === 4000, a);
let b = MJ.localApi('/yaku_score', { selected_yaku: ['平和', '立直'], is_menzen: false, win_type: 'ron' });
check('localApi /yaku_score 副露无役', b.success && b.result.total === 0, b);
let c = MJ.localApi('/quick_reference');
check('localApi /quick_reference 有表', c.success && c.table.length === 24, c);
let d = MJ.localApi('/yaku_list');
check('localApi /yaku_list 49种', d.success && d.yaku_list.length === 49, 'len=' + d.yaku_list.length);
let e = MJ.localApi('/fu_calculate', { win_type: 'ron', is_menzen: true, wait_type: 'ryanmen', pair_type: 'none', mianzi: shuntsu4 });
check('localApi /fu_calculate=30', e.success && e.fu === 30, e);
let f = MJ.localApi('/rank_bonus', { scores: [45000, 30000, 20000, 5000] });
check('localApi /rank_bonus 4位', f.success && f.results.length === 4, f);

console.log('\n结果: ' + pass + ' 通过, ' + fail + ' 失败');
process.exit(fail ? 1 : 0);
