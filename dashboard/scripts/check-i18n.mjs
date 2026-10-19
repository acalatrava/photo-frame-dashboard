// Verifies that every literal App.t('key') / data-t="key" used by the sources exists in both languages.
import { readFileSync, readdirSync, statSync } from 'node:fs';
import { join } from 'node:path';

const root = new URL('..', import.meta.url).pathname;
const src = readFileSync(join(root, 'js/i18n.js'), 'utf8');
const dicts = {};
for (const lang of ['es', 'en']) {
  const start = src.indexOf(`    ${lang}: {`);
  const end = lang === 'es' ? src.indexOf('    en: {') : src.indexOf('  App.DICT');
  dicts[lang] = new Set([...src.slice(start, end).matchAll(/^\s+|[,{]\s*([a-z0-9_]+):/gm)].map((m) => m[1]).filter(Boolean));
}

function walk(dir, out = []) {
  for (const f of readdirSync(dir)) {
    const p = join(dir, f);
    if (f === 'node_modules' || f === 'dist') continue;
    statSync(p).isDirectory() ? walk(p, out) : /\.(js|html)$/.test(f) && out.push(p);
  }
  return out;
}

const used = new Set();
const prefixes = new Set();
for (const f of [...walk(join(root, 'js')), join(root, 'index.html')]) {
  if (f.endsWith('i18n.js')) continue;
  const text = readFileSync(f, 'utf8');
  for (const m of text.matchAll(/\bt\(\s*'([a-z0-9_]+)'(\s*\+)?/g)) (m[2] ? prefixes : used).add(m[1]);
  for (const m of text.matchAll(/data-t="([a-z0-9_]+)"/g)) used.add(m[1]);
  // Keys inside ternaries such as App.t(cond ? 'a_b' : 'c_d') sit on a line that calls t( and share a known prefix.
  const known = new Set([...dicts.es].map((k) => k.split('_')[0]));
  for (const line of text.split('\n')) {
    if (!/\bt\(/.test(line)) continue;
    for (const m of line.matchAll(/[?:]\s*'([a-z]+_[a-z0-9_]+)'/g)) if (known.has(m[1].split('_')[0]) && !/_$/.test(m[1])) used.add(m[1]);
  }
}

let bad = 0;
for (const lang of Object.keys(dicts)) {
  for (const k of used) if (!dicts[lang].has(k)) { console.log(`missing [${lang}] ${k}`); bad++; }
  for (const p of prefixes) if (![...dicts[lang]].some((k) => k.startsWith(p))) { console.log(`missing prefix [${lang}] ${p}*`); bad++; }
}
for (const k of dicts.es) if (!dicts.en.has(k)) { console.log(`only in es: ${k}`); bad++; }
for (const k of dicts.en) if (!dicts.es.has(k)) { console.log(`only in en: ${k}`); bad++; }
console.log('dict sizes', dicts.es.size, dicts.en.size); console.log(`${used.size} keys, ${prefixes.size} dynamic prefixes, ${bad} problems`);
process.exit(bad ? 1 : 0);
