// HTML→A4 PDF と各ページのPNG（確認用）を書き出す。node build/render.js [png出力先]
const { chromium } = require('playwright');
const fs = require('fs');
const path = require('path');
(async () => {
  const dir = path.resolve(__dirname, '..');
  const src = fs.readFileSync(path.join(dir, 'kabukura_2026-11-13.html'), 'utf8');
  const shots = process.argv[2];
  const b = await chromium.launch();
  const p = await b.newPage({ viewport: { width: 900, height: 1200 }, deviceScaleFactor: 1.5 });
  await p.setContent('<!doctype html><html lang="ja"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"></head><body>' + src + '</body></html>', { waitUntil: 'networkidle' });
  await p.evaluate(() => document.fonts.ready);
  const over = await p.evaluate(() => [...document.querySelectorAll('.sheet')].map((s, i) => {
    const b = s.querySelector('.body');
    return { page: i + 1, overflow: b.scrollHeight - b.clientHeight };
  }));
  await p.waitForTimeout(500); const z = await p.evaluate(() => [...document.querySelectorAll('.sheet')].map(s => s.dataset.zoom+'/'+s.dataset.free)); console.log('zoom/free', z.join(' ')); console.log('overflow(px)', JSON.stringify(over));
  await p.pdf({ path: path.join(dir, 'kabukura_2026-11-13.pdf'), format: 'A4', printBackground: true, margin: { top: 0, bottom: 0, left: 0, right: 0 } });
  if (shots) {
    const els = await p.$$('.sheet');
    for (let i = 0; i < els.length; i++) await els[i].screenshot({ path: `${shots}/p${String(i + 1).padStart(2, '0')}.png` });
  }
  await b.close();
})();
