/* node_integration.js —— 端到端验证 offline.html 内联引擎 + fetch 拦截 */
const fs = require('fs');
const vm = require('vm');

const html = fs.readFileSync('offline.html', 'utf8');
// 提取首个 <script>（即 build 注入到 <head> 的引擎）
const m = html.match(/<script>([\s\S]*?)<\/script>/);
if (!m) { console.error('未找到内联脚本'); process.exit(1); }
const engineCode = m[1];

let ok = true;
const sandbox = {
  console, Math, JSON, Promise, setTimeout,
  Response: class { constructor(b, o) { this.body = b; this.ok = true; this.status = (o && o.status) || 200; } },
};
sandbox.window = sandbox;
sandbox.globalThis = sandbox;
// 提供原始 fetch 占位，让 setupOffline 能触发覆盖（/api 之外的调用会抛错）
sandbox.fetch = function () { throw new Error('原始 fetch 不应被 /api 调用'); };
sandbox.window.fetch = sandbox.fetch;

vm.createContext(sandbox);
vm.runInContext(engineCode, sandbox);

const MJ = sandbox.MJ;
console.log('1. 引擎加载:', !!MJ ? '✓' : '✗'); ok = ok && !!MJ;

const r = MJ.localApi('/calculate', { han: 3, fu: 30, is_dealer: false, win_type: 'ron' });
console.log('2. localApi total =', r.result.total, r.result.total === 4000 ? '✓' : '✗'); ok = ok && r.result.total === 4000;

sandbox.fetch('/calculate', { method: 'POST', body: JSON.stringify({ han: 3, fu: 30, is_dealer: false, win_type: 'ron' }) })
  .then((resp) => {
    const data = JSON.parse(resp.body);
    console.log('3. fetch 拦截 /calculate total =', data.result.total, data.result.total === 4000 ? '✓' : '✗'); ok = ok && data.result.total === 4000;
    return sandbox.fetch('/yaku_score', { method: 'POST', body: JSON.stringify({ selected_yaku: ['平和', '立直'], is_menzen: false, win_type: 'ron' }) });
  })
  .then((resp2) => {
    const d2 = JSON.parse(resp2.body);
    console.log('4. fetch 拦截 /yaku_score 副露无役 total =', d2.result.total, d2.result.total === 0 ? '✓' : '✗'); ok = ok && d2.result.total === 0;
    return sandbox.fetch('/quick_reference', { method: 'POST', body: '{}' });
  })
  .then((resp3) => {
    const d3 = JSON.parse(resp3.body);
    console.log('5. fetch 拦截 /quick_reference 表行数 =', d3.table.length, d3.table.length === 24 ? '✓' : '✗'); ok = ok && d3.table.length === 24;
    console.log(ok ? '\n✅ offline.html 端到端验证全部通过' : '\n❌ 存在失败');
    process.exit(ok ? 0 : 1);
  })
  .catch((e) => { console.error('失败:', e); process.exit(1); });
