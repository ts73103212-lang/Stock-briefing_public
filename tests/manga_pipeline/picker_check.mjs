// docs/manga/picker.html を実ブラウザで動かして確かめる。使い方: node picker_check.mjs <シナリオ名> [スクリーンショットの保存先]
// 偽の db（claude.use("db")）を差し込み、時刻は page.clock.setFixedTime で固定する。失敗は終了コード 1。
import { createRequire } from 'node:module';
import path from 'node:path';
import { fileURLToPath } from 'node:url';

// ESM の import は NODE_PATH（グローバルの playwright）を見ないので、require 経由で読み込む
const { chromium } = createRequire(import.meta.url)('playwright');
const HERE = path.dirname(fileURLToPath(import.meta.url));
const PAGE = 'file://' + path.resolve(HERE, '../../docs/manga/picker.html');

const DAY = {
  date: '2026-11-27', for_date: '2026-11-30', deadline: '20:00', created_at: '2026-11-27T14:05+09:00',
  candidates: [
    { id: 'c1', kind: 'theme', difficulty: 1, title: '相場をふり返る', summary: '一週間の値動きをやさしく整理する。', hook: '月曜と金曜でどう変わった？', characters: ['corgi'] },
    { id: 'c2', kind: 'term', difficulty: 2, title: 'SOX指数ってなに', summary: '半導体株の指数の読み方を知る。', hook: '指数の名前で動きが読める', characters: ['mirai'] },
    { id: 'c3', kind: 'stock', difficulty: 3, title: 'ある銘柄の決算', summary: '決算発表のあとの動きを見る。', hook: '数字よりも見出しが先に動く', characters: ['gonda'] },
    { id: 'c4', kind: 'caution', difficulty: 2, title: '急な値上がりに注意', summary: 'うわさで上がる株の見分け方。', hook: 'ほんとうに買っていい？', characters: ['corgi', 'mirai'], caution_count_note: '今週3回目' },
  ],
};

const fail = (m) => { console.error('FAIL: ' + m); process.exit(1); };
const eq = (a, b, what) => { if (JSON.stringify(a) !== JSON.stringify(b)) fail(`${what}: ${JSON.stringify(a)} != ${JSON.stringify(b)}`); };
const ok = (c, what) => { if (!c) fail(what); };
const has = (s, sub, what) => ok(String(s).includes(sub), `${what}: ${JSON.stringify(s)} に ${JSON.stringify(sub)} が無い`);
const stripAt = (o) => { const { picked_at, ...r } = o; ok(typeof picked_at === 'string' && picked_at.length > 0, 'picked_at が無い'); return r; };

const DAY2 = { ...DAY, date: '2026-11-26', for_date: '2026-11-27', candidates: DAY.candidates.map((c) => ({ ...c, title: c.title + '（前日）' })) };
const T = (s) => new Date(s + '+09:00');
const SCENARIOS = {
  'render': { now: T('2026-11-27T15:12:00') },
  'pick-request': { now: T('2026-11-27T15:12:00') },
  'free-exclusive': { now: T('2026-11-27T15:12:00') },
  'blank-free': { now: T('2026-11-27T15:12:00') },
  'auto': { now: T('2026-11-27T15:12:00') },
  'reload': { now: T('2026-11-27T15:12:00'), picks: { '2026-11-27': { date: '2026-11-27', id: 'c3', request: 'x', free: null } } },
  'deadline': { now: T('2026-11-27T20:00:00') },
  'cross-deadline': { now: T('2026-11-27T19:59:00') },
  'no-today': { now: T('2026-11-30T10:00:00') },
  'switch-day': { now: T('2026-11-27T15:12:00'), days: [DAY, DAY2] },
  'live-update': { now: T('2026-11-27T15:12:00') },
  'no-db': { now: T('2026-11-27T15:12:00'), noDb: true },
};

const name = process.argv[2];
const shot = process.argv[3];
const sc = SCENARIOS[name];
if (!sc) fail(`未知のシナリオ: ${name}（${Object.keys(SCENARIOS).join(', ')}）`);

const browser = await chromium.launch();
try {
  const ctx = await browser.newContext({ viewport: { width: 390, height: 844 }, deviceScaleFactor: 1 });
  const page = await ctx.newPage();
  const errors = [];
  page.on('pageerror', (e) => errors.push(String(e)));
  await page.clock.setFixedTime(sc.now);
  await page.addInitScript(({ days, picks, noDb }) => {
    window.__sets = [];
    const store = new Map(Object.entries(picks || {}).map(([d, v]) => ['picks/' + d, v]));
    const subs = new Map();
    const later = (f) => setTimeout(f, 0);   // 本物の claude.use も onSnapshot も、同期では返らない
    const snapOf = (k) => ({ exists: store.has(k), data: () => store.get(k) });
    window.claude = {
      use: async () => {
        await new Promise((r) => later(r));
        if (noDb) return null;
        return {
          collection: () => ({
            orderBy() { return this; }, limit() { return this; },
            onSnapshot(cb) {
              const push = (ds) => cb({ docs: ds.map((d) => ({ data: () => d })) });
              window.__pushDays = push; later(() => push(days)); return () => {};
            },
          }),
          doc: (k) => ({
            onSnapshot(cb) {
              if (!subs.has(k)) subs.set(k, new Set());
              subs.get(k).add(cb); later(() => cb(snapOf(k)));
              return () => subs.get(k).delete(cb);
            },
            async set(v) {
              window.__sets.push(JSON.parse(JSON.stringify(v))); store.set(k, v);
              (subs.get(k) || []).forEach((cb) => cb(snapOf(k)));
            },
          }),
        };
      },
    };
  }, { days: sc.days || [DAY], picks: sc.picks, noDb: !!sc.noDb });
  await page.goto(PAGE);

  const text = (sel) => page.locator(sel).innerText();
  const sets = () => page.evaluate(() => window.__sets);
  const lastSet = async () => { const s = await sets(); ok(s.length > 0, 'set が呼ばれていない'); return s[s.length - 1]; };
  const noSet = async (why) => eq((await sets()).length, 0, why);
  const ready = () => page.waitForSelector('#cards .card', { timeout: 5000 });

  if (name === 'no-db') {
    await page.waitForFunction(() => document.body.innerText.includes('サインインした本人だけ'), null, { timeout: 5000 });
    has(await page.locator('body').innerText(), 'このページは、サインインした本人だけが使えます。', 'no-db');
  } else if (name === 'switch-day' || name === 'live-update') {
    await ready();
    await page.locator('input[name=pick][value=c2]').check();
    await page.fill('#request', 'PTSの時間帯も入れて');
    const underC2 = () => page.evaluate(() => { const b = document.querySelector('#request-box'); return !b.hidden && b.previousElementSibling === document.querySelector('.card[data-id=c2]'); });
    if (name === 'switch-day') {
      await page.locator('#days button', { hasText: '11/26' }).click();
      await page.waitForFunction(() => document.querySelector('#cards .title').innerText.includes('前日'));
      await page.locator('#days button', { hasText: '11/27' }).click();
      await page.waitForFunction(() => !document.querySelector('#cards .title').innerText.includes('前日'));
      ok(await page.locator('input[name=pick][value=c2]').isChecked(), '日を戻したら c2 が選ばれたまま');
    } else {
      const changed = { ...DAY, candidates: DAY.candidates.map((c) => ({ ...c, title: c.title + '（更新）' })) };
      await page.evaluate((d) => window.__pushDays([d]), changed);
      await page.waitForFunction(() => document.querySelector('#cards .title').innerText.includes('更新'));
      ok(await page.locator('input[name=pick][value=c2]').isChecked(), '更新後も c2 が選ばれたまま');
    }
    ok(await page.locator('#request').isVisible(), '要望欄が見えない');
    ok(await underC2(), '要望欄が c2 の下にない');
    eq(await page.inputValue('#request'), 'PTSの時間帯も入れて', '要望の保持');
    await page.click('#save');
    await page.waitForFunction(() => window.__sets.length > 0);
    eq(stripAt(await lastSet()), { date: '2026-11-27', id: 'c2', request: 'PTSの時間帯も入れて', free: null }, 'set の中身');
  } else if (name === 'no-today') {
    await ready();
    has(await text('#status'), '今日の候補はまだありません', 'no-today status');
    eq(await page.locator('#cards .card').count(), 4, '過去の日の候補は見られる');
    for (const sel of ['input[name=pick]', '#save', '#auto']) {
      for (const el of await page.locator(sel).all()) ok(await el.isDisabled(), `${sel} が無効でない`);
    }
    await noSet('no-today');
  } else {
    await ready();
    if (name === 'render') {
      eq(await page.locator('#cards .card').count(), 4, 'カード枚数');
      const diffs = await page.locator('#cards .card .diff').allInnerTexts();
      eq(diffs, ['☆', '☆☆', '☆☆☆', '☆☆'], '難易度の☆');
      const kinds = await page.locator('#cards .card .kind').allInnerTexts();
      eq(kinds, ['振り返り', '用語', '話題', '注意喚起'], '種類');
      const body = await page.locator('body').innerText();
      has(body, '11/30(月) 朝に掲載', 'for_date');
      has(body, '締切 20:00', '締切');
      has(await text('#cards .card[data-id=c4]'), '今週3回目', 'c4 の注意書き');
      ok(!(await text('#cards .card[data-id=c1]')).includes('今週'), 'c1 に注意書きが出ている');
      ok(!(await page.locator('#request').isVisible()), '候補を選ぶまで要望欄は非表示');
      const w = await page.evaluate(() => [document.documentElement.scrollWidth, document.documentElement.clientWidth]);
      ok(w[0] <= w[1], `横スクロールが出る: ${w}`);
      ok(await page.locator('#save').isDisabled(), '未選択では保存できない');
      if (shot) {
        await page.locator('input[name=pick][value=c2]').check();
        await page.fill('#request', 'PTSの時間帯も入れて');
        await page.screenshot({ path: shot });
      }
    } else if (name === 'pick-request') {
      await page.locator('input[name=pick][value=c2]').check();
      ok(await page.locator('#request').isVisible(), '要望欄が出ない');
      await page.fill('#request', 'PTSの時間帯も入れて');
      await page.click('#save');
      await page.waitForFunction(() => window.__sets.length > 0);
      eq(stripAt(await lastSet()), { date: '2026-11-27', id: 'c2', request: 'PTSの時間帯も入れて', free: null }, 'set の中身');
      await page.waitForFunction(() => document.querySelector('#current').innerText.includes('c2'));
      const cur = await text('#current');
      has(cur, 'c2', '#current'); has(cur, 'PTSの時間帯も入れて', '#current');
    } else if (name === 'free-exclusive') {
      await page.locator('input[name=pick][value=c1]').check();
      await page.fill('#request', '消えるはずの要望');
      await page.locator('#free-radio').check();
      await page.fill('#free', '自分で決めたネタ');
      await page.click('#save');
      await page.waitForFunction(() => window.__sets.length > 0);
      eq(stripAt(await lastSet()), { date: '2026-11-27', id: null, request: null, free: '自分で決めたネタ' }, 'set の中身');
    } else if (name === 'blank-free') {
      await page.locator('#free-radio').check();
      await page.fill('#free', '  　 ');
      ok(await page.locator('#save').isDisabled(), '空白だけで保存できてしまう');
      await page.locator('#save').click({ force: true });
      await noSet('blank-free');
    } else if (name === 'auto') {
      await page.locator('input[name=pick][value=c4]').check();
      await page.click('#auto');
      await page.waitForFunction(() => window.__sets.length > 0);
      eq(stripAt(await lastSet()), { date: '2026-11-27', id: null, request: null, free: null }, 'set の中身');
      has(await text('#current'), 'おまかせ', '#current');
    } else if (name === 'reload') {
      await page.waitForFunction(() => document.querySelector('input[name=pick][value=c3]')?.checked);
      ok(await page.locator('#request').isVisible(), '要望欄が出ていない');
      eq(await page.inputValue('#request'), 'x', '要望の復元');
      has(await text('#current'), 'c3', '#current');
    } else if (name === 'deadline') {
      has(await text('#status'), '締切済み', '#status');
      for (const sel of ['input[name=pick]', '#free', '#save', '#auto']) {
        for (const el of await page.locator(sel).all()) ok(await el.isDisabled(), `${sel} が無効でない`);
      }
      await page.locator('#save').click({ force: true });
      await page.locator('#auto').click({ force: true });
      await noSet('deadline');
    } else if (name === 'cross-deadline') {
      has(await text('#status'), '受付中', '開いた時点は受付中');
      await page.locator('input[name=pick][value=c1]').check();
      await page.clock.setFixedTime(T('2026-11-27T20:01:00'));
      ok(!(await page.locator('#save').isDisabled()), '再描画前なので保存ボタンはまだ押せるはず');
      await page.click('#save');
      await page.waitForFunction(() => document.querySelector('#msg').innerText.includes('締切'));
      await noSet('cross-deadline');
    }
  }
  if (errors.length) fail('ページのエラー: ' + errors.join(' | '));
  console.log('ok ' + name);
} finally {
  await browser.close();
}
