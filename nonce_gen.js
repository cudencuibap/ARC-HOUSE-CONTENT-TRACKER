// Executes the site's real obfuscated generateNonce() to produce a fresh X-Nonce.
// Usage: node nonce_gen.js "<x-client>"  -> prints nonce to stdout
const fs = require('fs');
const path = require('path');

const xclient = process.argv[2];
if (!xclient) { console.error('need x-client arg'); process.exit(1); }

const chunkPath = process.env.ARC_NONCE_CHUNK || path.join(__dirname, 'nonce_chunk.js');
const src = fs.readFileSync(chunkPath, 'utf8');

// ---- browser-ish global shims (Node 24 already has Headers, btoa, atob, TextDecoder, Buffer, crypto) ----
globalThis.self = globalThis;
globalThis.window = globalThis;
if (typeof globalThis.navigator === 'undefined') globalThis.navigator = { userAgent: 'node' };

let MODULES = null;
const chunkArr = [];
chunkArr.push = function (arg) { MODULES = Object.assign(MODULES || {}, arg[1]); };
globalThis.webpackChunk_N_E = chunkArr;
self.webpackChunk_N_E = chunkArr;

// register modules
eval(src);
if (!MODULES) { console.error('no modules captured'); process.exit(1); }

// minimal webpack require
const cache = {};
function r(id) {
  if (cache[id]) return cache[id].exports;
  const m = { exports: {} };
  cache[id] = m;
  MODULES[id].call(m.exports, m, m.exports, r);
  return m.exports;
}
r.g = globalThis;
r.n = function (m) { const g = m && m.__esModule ? () => m.default : () => m; return g; };
r.d = function (exports, defs) { for (const k in defs) if (!Object.prototype.hasOwnProperty.call(exports, k)) Object.defineProperty(exports, k, { enumerable: true, get: defs[k] }); };
r.r = function (e) { if (typeof Symbol !== 'undefined' && Symbol.toStringTag) Object.defineProperty(e, Symbol.toStringTag, { value: 'Module' }); Object.defineProperty(e, '__esModule', { value: true }); };
r.o = function (o, k) { return Object.prototype.hasOwnProperty.call(o, k); };

const mod = r(26193);                       // exports generateNonce
const nonce = mod.generateNonce(xclient);
process.stdout.write(nonce || '');
