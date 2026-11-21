class Gt {
  /**
   * The registered events.
   * 
   * @protected
   */
  events = [];
  /**
   * Emit an event.
   * 
   * @public
  */
  emit(e, ...n) {
    for (const i of this.events)
      i.key === e && i.fn(...n);
  }
  /**
   * Listen for an event. This returns a function to unwatch the event.
   * 
   * @public
   */
  on(e, n) {
    const i = () => {
      const o = this.events.findIndex((s) => s.key === e && s.fn === n);
      this.events.splice(o, 1);
    };
    return this.events.push({ key: e, fn: n, unwatch: i }), i;
  }
  /**
   * Listen for an event once.
   * 
   * @public
   */
  once(e, n) {
    const i = this.on(e, (...o) => {
      n(...o), i();
    });
    return i;
  }
  off(e, n) {
    for (const i of this.events)
      i.key === e && (!n || n === i.fn) && i.unwatch();
  }
  /**
   * Reset the event bus and remove all watchers.
   * 
   * @public
   */
  reset() {
    this.events = [];
  }
}
function Un() {
  return new Gt();
}
const we = !1, ve = (t, e) => t === e, Ae = Symbol("solid-track"), it = {
  equals: ve
};
let Xt = ne;
const L = 1, rt = 2, Qt = {
  owned: null,
  cleanups: null,
  context: null,
  owner: null
};
var S = null;
let gt = null, Se = null, A = null, M = null, T = null, ft = 0;
function q(t, e) {
  const n = A, i = S, o = t.length === 0, s = e === void 0 ? i : e, r = o ? Qt : {
    owned: null,
    cleanups: null,
    context: s ? s.context : null,
    owner: s
  }, a = o ? t : () => t(() => V(() => Q(r)));
  S = r, A = null;
  try {
    return tt(a, !0);
  } finally {
    A = n, S = i;
  }
}
function P(t, e) {
  e = e ? Object.assign({}, it, e) : it;
  const n = {
    value: t,
    observers: null,
    observerSlots: null,
    comparator: e.equals || void 0
  }, i = (o) => (typeof o == "function" && (o = o(n.value)), ee(n, o));
  return [te.bind(n), i];
}
function W(t, e, n) {
  const i = $t(t, e, !1, L);
  Z(i);
}
function Zt(t, e, n) {
  Xt = ke;
  const i = $t(t, e, !1, L);
  i.user = !0, T ? T.push(i) : Z(i);
}
function $(t, e, n) {
  n = n ? Object.assign({}, it, n) : it;
  const i = $t(t, e, !0, 0);
  return i.observers = null, i.observerSlots = null, i.comparator = n.equals || void 0, Z(i), te.bind(i);
}
function V(t) {
  if (A === null) return t();
  const e = A;
  A = null;
  try {
    return t();
  } finally {
    A = e;
  }
}
function xe(t) {
  return S === null || (S.cleanups === null ? S.cleanups = [t] : S.cleanups.push(t)), t;
}
const [Jn, Kn] = /* @__PURE__ */ P(!1);
function Me(t) {
  const e = $(t), n = $(() => wt(e()));
  return n.toArray = () => {
    const i = n();
    return Array.isArray(i) ? i : i != null ? [i] : [];
  }, n;
}
function te() {
  if (this.sources && this.state)
    if (this.state === L) Z(this);
    else {
      const t = M;
      M = null, tt(() => ot(this), !1), M = t;
    }
  if (A) {
    const t = this.observers ? this.observers.length : 0;
    A.sources ? (A.sources.push(this), A.sourceSlots.push(t)) : (A.sources = [this], A.sourceSlots = [t]), this.observers ? (this.observers.push(A), this.observerSlots.push(A.sources.length - 1)) : (this.observers = [A], this.observerSlots = [A.sources.length - 1]);
  }
  return this.value;
}
function ee(t, e, n) {
  let i = t.value;
  return (!t.comparator || !t.comparator(i, e)) && (t.value = e, t.observers && t.observers.length && tt(() => {
    for (let o = 0; o < t.observers.length; o += 1) {
      const s = t.observers[o], r = gt && gt.running;
      r && gt.disposed.has(s), (r ? !s.tState : !s.state) && (s.pure ? M.push(s) : T.push(s), s.observers && ie(s)), r || (s.state = L);
    }
    if (M.length > 1e6)
      throw M = [], new Error();
  }, !1)), e;
}
function Z(t) {
  if (!t.fn) return;
  Q(t);
  const e = ft;
  De(t, t.value, e);
}
function De(t, e, n) {
  let i;
  const o = S, s = A;
  A = S = t;
  try {
    i = t.fn(e);
  } catch (r) {
    return t.pure && (t.state = L, t.owned && t.owned.forEach(Q), t.owned = null), t.updatedAt = n + 1, re(r);
  } finally {
    A = s, S = o;
  }
  (!t.updatedAt || t.updatedAt <= n) && (t.updatedAt != null && "observers" in t ? ee(t, i) : t.value = i, t.updatedAt = n);
}
function $t(t, e, n, i = L, o) {
  const s = {
    fn: t,
    state: i,
    updatedAt: null,
    owned: null,
    sources: null,
    sourceSlots: null,
    cleanups: null,
    value: e,
    owner: S,
    context: S ? S.context : null,
    pure: n
  };
  return S === null || S !== Qt && (S.owned ? S.owned.push(s) : S.owned = [s]), s;
}
function st(t) {
  if (t.state === 0) return;
  if (t.state === rt) return ot(t);
  if (t.suspense && V(t.suspense.inFallback)) return t.suspense.effects.push(t);
  const e = [t];
  for (; (t = t.owner) && (!t.updatedAt || t.updatedAt < ft); )
    t.state && e.push(t);
  for (let n = e.length - 1; n >= 0; n--)
    if (t = e[n], t.state === L)
      Z(t);
    else if (t.state === rt) {
      const i = M;
      M = null, tt(() => ot(t, e[0]), !1), M = i;
    }
}
function tt(t, e) {
  if (M) return t();
  let n = !1;
  e || (M = []), T ? n = !0 : T = [], ft++;
  try {
    const i = t();
    return $e(n), i;
  } catch (i) {
    n || (T = null), M = null, re(i);
  }
}
function $e(t) {
  if (M && (ne(M), M = null), t) return;
  const e = T;
  T = null, e.length && tt(() => Xt(e), !1);
}
function ne(t) {
  for (let e = 0; e < t.length; e++) st(t[e]);
}
function ke(t) {
  let e, n = 0;
  for (e = 0; e < t.length; e++) {
    const i = t[e];
    i.user ? t[n++] = i : st(i);
  }
  for (e = 0; e < n; e++) st(t[e]);
}
function ot(t, e) {
  t.state = 0;
  for (let n = 0; n < t.sources.length; n += 1) {
    const i = t.sources[n];
    if (i.sources) {
      const o = i.state;
      o === L ? i !== e && (!i.updatedAt || i.updatedAt < ft) && st(i) : o === rt && ot(i, e);
    }
  }
}
function ie(t) {
  for (let e = 0; e < t.observers.length; e += 1) {
    const n = t.observers[e];
    n.state || (n.state = rt, n.pure ? M.push(n) : T.push(n), n.observers && ie(n));
  }
}
function Q(t) {
  let e;
  if (t.sources)
    for (; t.sources.length; ) {
      const n = t.sources.pop(), i = t.sourceSlots.pop(), o = n.observers;
      if (o && o.length) {
        const s = o.pop(), r = n.observerSlots.pop();
        i < o.length && (s.sourceSlots[r] = i, o[i] = s, n.observerSlots[i] = r);
      }
    }
  if (t.tOwned) {
    for (e = t.tOwned.length - 1; e >= 0; e--) Q(t.tOwned[e]);
    delete t.tOwned;
  }
  if (t.owned) {
    for (e = t.owned.length - 1; e >= 0; e--) Q(t.owned[e]);
    t.owned = null;
  }
  if (t.cleanups) {
    for (e = t.cleanups.length - 1; e >= 0; e--) t.cleanups[e]();
    t.cleanups = null;
  }
  t.state = 0;
}
function Ce(t) {
  return t instanceof Error ? t : new Error(typeof t == "string" ? t : "Unknown error", {
    cause: t
  });
}
function re(t, e = S) {
  throw Ce(t);
}
function wt(t) {
  if (typeof t == "function" && !t.length) return wt(t());
  if (Array.isArray(t)) {
    const e = [];
    for (let n = 0; n < t.length; n++) {
      const i = wt(t[n]);
      Array.isArray(i) ? e.push.apply(e, i) : e.push(i);
    }
    return e;
  }
  return t;
}
const _t = Symbol("fallback");
function Lt(t) {
  for (let e = 0; e < t.length; e++) t[e]();
}
function Fe(t, e, n = {}) {
  let i = [], o = [], s = [], r = [], a = 0, l;
  return xe(() => Lt(s)), () => {
    const c = t() || [], f = c.length;
    return c[Ae], V(() => {
      if (f === 0)
        return a !== 0 && (Lt(s), s = [], i = [], o = [], a = 0, r = []), n.fallback && (i = [_t], o[0] = q((h) => (s[0] = h, n.fallback())), a = 1), o;
      for (i[0] === _t && (s[0](), s = [], i = [], o = [], a = 0), l = 0; l < f; l++)
        l < i.length && i[l] !== c[l] ? r[l](() => c[l]) : l >= i.length && (o[l] = q(d));
      for (; l < i.length; l++)
        s[l]();
      return a = r.length = s.length = f, i = c.slice(0), o = o.slice(0, a);
    });
    function d(h) {
      s[l] = h;
      const [u, b] = P(c[l]);
      return r[l] = b, e(u, l);
    }
  };
}
function k(t, e) {
  return V(() => t(e || {}));
}
const se = (t) => `Stale read from <${t}>.`;
function Ee(t) {
  const e = "fallback" in t && {
    fallback: () => t.fallback
  };
  return $(Fe(() => t.each, t.children, e || void 0));
}
function Oe(t) {
  const e = t.keyed, n = $(() => t.when, void 0, void 0), i = e ? n : $(n, void 0, {
    equals: (o, s) => !o == !s
  });
  return $(() => {
    const o = i();
    if (o) {
      const s = t.children;
      return typeof s == "function" && s.length > 0 ? V(() => s(e ? o : () => {
        if (!V(i)) throw se("Show");
        return n();
      })) : s;
    }
    return t.fallback;
  }, void 0, void 0);
}
function Ie(t) {
  const e = Me(() => t.children), n = $(() => {
    const i = e(), o = Array.isArray(i) ? i : [i];
    let s = () => {
    };
    for (let r = 0; r < o.length; r++) {
      const a = r, l = o[r], c = s, f = $(() => c() ? void 0 : l.when, void 0, void 0), d = l.keyed ? f : $(f, void 0, {
        equals: (h, u) => !h == !u
      });
      s = () => c() || (d() ? [a, f, l] : void 0);
    }
    return s;
  });
  return $(() => {
    const i = n()();
    if (!i) return t.fallback;
    const [o, s, r] = i, a = r.children;
    return typeof a == "function" && a.length > 0 ? V(() => a(r.keyed ? s() : () => {
      if (V(n)()?.[0] !== o) throw se("Match");
      return s();
    })) : a;
  }, void 0, void 0);
}
function mt(t) {
  return t;
}
class Nt extends SyntaxError {
  constructor(e, n, i, o) {
    super(e), this.expected = n, this.found = i, this.location = o, this.name = "SyntaxError";
  }
  format(e) {
    let n = "Error: " + this.message;
    if (this.location) {
      let i = null;
      const o = e.find((l) => l.source === this.location.source);
      o && (i = o.text.split(/\r\n|\n|\r/g));
      const s = this.location.start, r = this.location.source && typeof this.location.source.offset == "function" ? this.location.source.offset(s) : s, a = this.location.source + ":" + r.line + ":" + r.column;
      if (i) {
        const l = this.location.end, c = "".padEnd(r.line.toString().length, " "), f = i[s.line - 1], h = (s.line === l.line ? l.column : f.length + 1) - s.column || 1;
        n += `
 --> ` + a + `
` + c + ` |
` + r.line + " | " + f + `
` + c + " | " + "".padEnd(s.column - 1, " ") + "".padEnd(h, "^");
      } else
        n += `
 at ` + a;
    }
    return n;
  }
  static buildMessage(e, n) {
    function i(h) {
      return h.codePointAt(0).toString(16).toUpperCase();
    }
    const o = Object.prototype.hasOwnProperty.call(RegExp.prototype, "unicode") ? new RegExp("[\\p{C}\\p{Mn}\\p{Mc}]", "gu") : null;
    function s(h) {
      return o ? h.replace(o, (u) => "\\u{" + i(u) + "}") : h;
    }
    function r(h) {
      return s(h.replace(/\\/g, "\\\\").replace(/"/g, '\\"').replace(/\0/g, "\\0").replace(/\t/g, "\\t").replace(/\n/g, "\\n").replace(/\r/g, "\\r").replace(/[\x00-\x0F]/g, (u) => "\\x0" + i(u)).replace(/[\x10-\x1F\x7F-\x9F]/g, (u) => "\\x" + i(u)));
    }
    function a(h) {
      return s(h.replace(/\\/g, "\\\\").replace(/\]/g, "\\]").replace(/\^/g, "\\^").replace(/-/g, "\\-").replace(/\0/g, "\\0").replace(/\t/g, "\\t").replace(/\n/g, "\\n").replace(/\r/g, "\\r").replace(/[\x00-\x0F]/g, (u) => "\\x0" + i(u)).replace(/[\x10-\x1F\x7F-\x9F]/g, (u) => "\\x" + i(u)));
    }
    const l = {
      literal(h) {
        return '"' + r(h.text) + '"';
      },
      class(h) {
        const u = h.parts.map(
          (b) => Array.isArray(b) ? a(b[0]) + "-" + a(b[1]) : a(b)
        );
        return "[" + (h.inverted ? "^" : "") + u.join("") + "]" + (h.unicode ? "u" : "");
      },
      any() {
        return "any character";
      },
      end() {
        return "end of input";
      },
      other(h) {
        return h.description;
      }
    };
    function c(h) {
      return l[h.type](h);
    }
    function f(h) {
      const u = h.map(c);
      if (u.sort(), u.length > 0) {
        let b = 1;
        for (let w = 1; w < u.length; w++)
          u[w - 1] !== u[w] && (u[b] = u[w], b++);
        u.length = b;
      }
      switch (u.length) {
        case 1:
          return u[0];
        case 2:
          return u[0] + " or " + u[1];
        default:
          return u.slice(0, -1).join(", ") + ", or " + u[u.length - 1];
      }
    }
    function d(h) {
      return h ? '"' + r(h) + '"' : "end of input";
    }
    return "Expected " + f(e) + " but " + d(n) + " found.";
  }
}
function Te(t, e) {
  e = e !== void 0 ? e : {};
  const n = {}, i = e.grammarSource, o = {
    array: nt
  };
  let s = nt;
  const r = "[", a = "]", l = /^[[\]]/, c = Ft("[", !1), f = Ft("]", !1), d = me(["[", "]"], !1, !1, !1), h = pe();
  function u(y) {
    return () => y;
  }
  function b(y) {
    return y;
  }
  function w(y) {
    for (const g of y)
      typeof g == "function" && y.splice(y.indexOf(g), 1, ...g());
    return y;
  }
  function x(y) {
    return y.flat(1).filter(Boolean);
  }
  let m = e.peg$currPos | 0;
  const N = [{ line: 1, column: 1 }];
  let C = m, et = e.peg$maxFailExpected || [], _ = e.peg$silentFails | 0, G;
  if (e.startRule) {
    if (!(e.startRule in o))
      throw new Error(`Can't start parsing from rule "` + e.startRule + '".');
    s = o[e.startRule];
  }
  function ge(y = m) {
    const g = t.codePointAt(y);
    return g === void 0 ? "" : String.fromCodePoint(g);
  }
  function Ft(y, g) {
    return { type: "literal", text: y, ignoreCase: g };
  }
  function me(y, g, p, v) {
    return { type: "class", parts: y, inverted: g, ignoreCase: p, unicode: v };
  }
  function pe() {
    return { type: "any" };
  }
  function ye() {
    return { type: "end" };
  }
  function Et(y) {
    let g = N[y], p;
    if (g)
      return g;
    if (y >= N.length)
      p = N.length - 1;
    else
      for (p = y; !N[--p]; )
        ;
    for (g = N[p], g = {
      line: g.line,
      column: g.column
    }; p < y; )
      t.charCodeAt(p) === 10 ? (g.line++, g.column = 1) : g.column++, p++;
    return N[y] = g, g;
  }
  function Ot(y, g, p) {
    const v = Et(y), R = Et(g);
    return {
      source: i,
      start: {
        offset: y,
        line: v.line,
        column: v.column
      },
      end: {
        offset: g,
        line: R.line,
        column: R.column
      }
    };
  }
  function j(y) {
    m < C || (m > C && (C = m, et = []), et.push(y));
  }
  function be(y, g, p) {
    return new Nt(
      Nt.buildMessage(y, g),
      y,
      g,
      p
    );
  }
  function nt() {
    let y, g, p, v, R, Y;
    for (y = m, g = [], p = m, v = It(), v !== n && (v = u(v)), p = v, p === n && (p = m, t.charCodeAt(m) === 91 ? (v = r, m++) : (v = n, _ === 0 && j(c)), v !== n ? (R = nt(), t.charCodeAt(m) === 93 ? (Y = a, m++) : (Y = n, _ === 0 && j(f)), Y !== n ? p = R : (m = p, p = n)) : (m = p, p = n)); p !== n; )
      g.push(p), p = m, v = It(), v !== n && (v = u(v)), p = v, p === n && (p = m, t.charCodeAt(m) === 91 ? (v = r, m++) : (v = n, _ === 0 && j(c)), v !== n ? (R = nt(), t.charCodeAt(m) === 93 ? (Y = a, m++) : (Y = n, _ === 0 && j(f)), Y !== n ? p = R : (m = p, p = n)) : (m = p, p = n));
    return g = w(g), y = g, y;
  }
  function It() {
    let y, g, p;
    if (y = m, g = [], p = Tt(), p !== n)
      for (; p !== n; )
        g.push(p), p = Tt();
    else
      g = n;
    return g !== n && (g = x(g)), y = g, y;
  }
  function Tt() {
    let y, g, p;
    return y = m, g = m, _++, p = t.charAt(m), l.test(p) ? m++ : (p = n, _ === 0 && j(d)), _--, p === n ? g = void 0 : (m = g, g = n), g !== n ? (t.length > m ? (p = t.charAt(m), m++) : (p = n, _ === 0 && j(h)), p !== n ? (g = [g, p], y = g) : (m = y, y = n)) : (m = y, y = n), y;
  }
  G = s();
  const dt = G !== n && m === t.length;
  function Vt() {
    throw G !== n && m < t.length && j(ye()), be(
      et,
      C < t.length ? ge(C) : null,
      C < t.length ? Ot(C, C + 1) : Ot(C, C)
    );
  }
  if (e.peg$library)
    return (
      /** @type {any} */
      {
        peg$result: G,
        peg$currPos: m,
        peg$FAILED: n,
        peg$maxFailExpected: et,
        peg$maxFailPos: C,
        peg$success: dt,
        peg$throw: dt ? void 0 : Vt
      }
    );
  if (dt)
    return G;
  Vt();
}
const Gn = [
  "array"
], Ve = " ";
function _e() {
  function t(n) {
    if (n === void 0)
      return [];
    if (typeof n == "string")
      return n.match(/\[|\]/) ? Te(n) : Array.from(n);
    if (typeof n == "number")
      return Array.from(n.toString());
    for (const i of n) {
      const o = n.indexOf(i), s = t(i);
      typeof i == "string" ? n.splice(o, 1, ...s) : n.splice(o, 1, s);
    }
    return n.filter(Boolean);
  }
  function e(n) {
    if (!Array.isArray(n))
      return !1;
    for (const i in n)
      if (!(typeof n[i] == "string" && n[i].length === 1)) {
        if (Array.isArray(n[i])) {
          if (!n[i].length)
            continue;
        } else return !1;
        if (!e(n[i]))
          return !1;
      }
    return !0;
  }
  return {
    digitize: t,
    isDigitized: e
  };
}
function jt(t, e, n, i) {
  typeof n == "function" ? (i = n, n = {}) : n || (n = {});
  const o = !n.backwards;
  function s(r, a) {
    if (at(a)) {
      r = Ne(r);
      const l = Math.max(a.length, r.length);
      for (let c = o ? 0 : l - 1; o ? c < l : c >= 0; o ? c++ : c--) {
        const f = r[c] ? s(r[c], a[c]) : s([], a[c]);
        r[c] ? r[c] = f : r.push(f);
      }
      for (let c = 0; c < r.length; c++)
        r[c] === void 0 && r.splice(c, 1);
      return r;
    }
    if (Array.isArray(a) && !at(a)) {
      r = Le(r);
      let l = 0;
      for (; l < r.length; ) {
        const c = o ? l : r.length - 1 - l, f = o ? l : a.length - 1 - l;
        r[c] = s(
          r[c],
          a[f]
        ), r[c] === void 0 ? r.splice(c, 1) : l++;
      }
      for (let c = o ? r.length : a.length - 1; o ? c < a.length : c >= r.length; o ? c++ : c--) {
        const f = s(void 0, a[c]);
        if (f === void 0)
          break;
        r.push(f);
      }
      return r;
    }
    return i ? i(vt(r), a) : vt(r);
  }
  return s(t, e);
}
function vt(t) {
  return Array.isArray(t) ? vt(t[0]) : t;
}
function Le(t) {
  return at(t) ? t.flat(1 / 0) : Array.isArray(t) ? t : t === void 0 ? [] : [t];
}
function Ne(t) {
  return at(t) ? t : Array.isArray(t) ? [t] : t === void 0 ? [[]] : [[t]];
}
function at(t) {
  if (!Array.isArray(t) || !t.length)
    return !1;
  for (const e in t)
    if (Array.isArray(t[e]))
      return !0;
  return !1;
}
function At(t) {
  function e(n, i = 0) {
    for (const o of n)
      Array.isArray(o) ? i += e(o) : i += o.length;
    return i;
  }
  return e(t);
}
function je() {
  return { stop: !0 };
}
function Re(t) {
  const e = [];
  return (...n) => {
    const [i] = n, o = typeof i == "object" || Array.isArray(i) ? JSON.stringify(i) : i, s = t(e, ...n);
    if (s && typeof s == "object" && "stop" in s)
      return i;
    const r = s, a = typeof r == "object" || Array.isArray(r) ? JSON.stringify(r) : r;
    return o !== a && e.push({
      from: i,
      to: r
    }), r;
  };
}
function St(t, e) {
  return Re((n, ...i) => t(n, ...i) ? e(...i) : je());
}
function Xn(t, e) {
  return St((n, ...i) => n.length < t, e);
}
class kt {
  /**
   * Parameters that are passed to the digiter.
   * 
   * @public
   */
  digitizer;
  /**
   * The face's value.
   * 
   * @protected
   */
  $value;
  /**
   * The face's digits.
   * 
   * @protected
   */
  $digits;
  /**
   * Instantiate the face value.
   * 
   * @public
   */
  constructor(e, n) {
    this.digitizer = n?.digitizer || _e(), this.$value = P(e), this.$digits = P(n?.digits ?? this.digitizer.digitize(e));
  }
  /**
   * The digitized value.
   * 
   * @public
   */
  get digits() {
    return this.$digits[0]();
  }
  /**
   * Set the digits from a `DigitizedValues`.
   * 
   * @public
   */
  set digits(e) {
    this.$digits[1](e);
  }
  /**
   * Get the length of the flattened digitized array.
   * 
   * @public
   */
  get length() {
    return At(this.$digits[0]());
  }
  /**
   * Get the value.
   * 
   * @public
   */
  get value() {
    return this.$value[0]();
  }
  /**
   * Set the value.
   * 
   * @public
   */
  set value(e) {
    this.$value[1](e), this.$digits[1](this.digitizer.digitize(e));
  }
  /**
   * Compare the face value with the given subject.
   * 
   * @public
   */
  compare(e) {
    return JSON.stringify(this.digits) === JSON.stringify(e?.digits);
  }
  /**
   * Create a new instance with the given value.
   * 
   * @public
   */
  copy() {
    return new kt(this.value, {
      digits: this.digits,
      digitizer: this.digitizer
    });
  }
}
function J(t, e) {
  return new kt(t, e);
}
function Ye(t = 0, e) {
  return Array.from(Array(e).keys()).map((n) => n + t);
}
function pt(t, e) {
  return Ye(
    t.charCodeAt(0),
    e.charCodeAt(0) + 1 - t.charCodeAt(0)
  ).map((i) => String.fromCharCode(i));
}
function ze(t) {
  const e = [];
  for (; t.length; ) {
    const n = Math.floor(
      Math.random() * t.length
    );
    e.push(...t.splice(n, 1));
  }
  return e;
}
function He() {
  return [
    ...pt("a", "z"),
    ...pt("A", "Z"),
    ...pt("0", "9"),
    '"',
    "'",
    ":",
    "-",
    ".",
    ",",
    "!",
    "?"
  ];
}
function Pe(t) {
  const e = t?.blacklist ?? [], n = t?.whitelist ?? [], i = t?.emptyChar ?? Ve, o = typeof t?.shuffle == "function" ? t.shuffle : t?.shuffle ? ze : void 0;
  function s() {
    const u = t?.charset || He;
    return o ? o(u()) : u();
  }
  const r = s();
  function a(u) {
    const b = u.charCodeAt(0), w = r.map((x) => x.charCodeAt(0));
    return String.fromCharCode(
      w.reduce((x, m) => Math.abs(m - b) < Math.abs(x - b) ? m : x)
    );
  }
  function l(u, b = 1) {
    let w = [i, ...r, i, ...r];
    b < 0 && (w = w.reverse());
    let x = 1;
    u === void 0 ? u = i : w.includes(u) || (u = i, x = 0);
    const m = w.indexOf(u);
    return w.slice(
      m + x,
      w.indexOf(u, m + 1) + x
    ).splice(0, Math.abs(b));
  }
  function c(u, b, w = 1) {
    if (b === void 0 && u === i)
      return;
    if (typeof b == "string" && !r.includes(b))
      return b;
    if (u && (h(u) || b === u))
      return u;
    if (u && d(u))
      return a(u);
    const x = l(u, w);
    if (typeof b == "string" && x.includes(b))
      return b;
    const m = x[w - 1];
    if (!(b === void 0 && u && m && r.indexOf(m) < r.indexOf(u)))
      return x[w - 1];
  }
  function f(u, b, w = 1) {
    if (b === void 0 && u === i)
      return;
    if (typeof b == "string" && !r.includes(b))
      return b;
    if (u && (h(u) || b === u))
      return u;
    if (u && d(u))
      return a(u);
    const x = l(u, -w);
    if (typeof b == "string" && x.includes(b))
      return b;
    const m = x[w - 1];
    if (!(b === void 0 && u && m && r.indexOf(m) > r.indexOf(u)))
      return x[w - 1];
  }
  function d(u) {
    return e.includes(u);
  }
  function h(u) {
    return n.includes(u);
  }
  return {
    charset: r,
    chunk: l,
    emptyChar: i,
    isBlacklisted: d,
    isWhitelisted: h,
    next: c,
    prev: f
  };
}
let qe = { data: "" }, We = (t) => typeof window == "object" ? ((t ? t.querySelector("#_goober") : window._goober) || Object.assign((t || document.head).appendChild(document.createElement("style")), { innerHTML: " ", id: "_goober" })).firstChild : t || qe, Be = /(?:([\u0080-\uFFFF\w-%@]+) *:? *([^{;]+?);|([^;}{]*?) *{)|(}\s*)/g, Ue = /\/\*[^]*?\*\/|  +/g, Rt = /\n+/g, H = (t, e) => {
  let n = "", i = "", o = "";
  for (let s in t) {
    let r = t[s];
    s[0] == "@" ? s[1] == "i" ? n = s + " " + r + ";" : i += s[1] == "f" ? H(r, s) : s + "{" + H(r, s[1] == "k" ? "" : e) + "}" : typeof r == "object" ? i += H(r, e ? e.replace(/([^,])+/g, (a) => s.replace(/([^,]*:\S+\([^)]*\))|([^,])+/g, (l) => /&/.test(l) ? l.replace(/&/g, a) : a ? a + " " + l : l)) : s) : r != null && (s = /^--/.test(s) ? s : s.replace(/[A-Z]/g, "-$&").toLowerCase(), o += H.p ? H.p(s, r) : s + ":" + r + ";");
  }
  return n + (e && o ? e + "{" + o + "}" : o) + i;
}, I = {}, oe = (t) => {
  if (typeof t == "object") {
    let e = "";
    for (let n in t) e += n + oe(t[n]);
    return e;
  }
  return t;
}, Je = (t, e, n, i, o) => {
  let s = oe(t), r = I[s] || (I[s] = ((l) => {
    let c = 0, f = 11;
    for (; c < l.length; ) f = 101 * f + l.charCodeAt(c++) >>> 0;
    return "go" + f;
  })(s));
  if (!I[r]) {
    let l = s !== t ? t : ((c) => {
      let f, d, h = [{}];
      for (; f = Be.exec(c.replace(Ue, "")); ) f[4] ? h.shift() : f[3] ? (d = f[3].replace(Rt, " ").trim(), h.unshift(h[0][d] = h[0][d] || {})) : h[0][f[1]] = f[2].replace(Rt, " ").trim();
      return h[0];
    })(t);
    I[r] = H(o ? { ["@keyframes " + r]: l } : l, n ? "" : "." + r);
  }
  let a = n && I.g ? I.g : null;
  return n && (I.g = I[r]), ((l, c, f, d) => {
    d ? c.data = c.data.replace(d, l) : c.data.indexOf(l) === -1 && (c.data = f ? l + c.data : c.data + l);
  })(I[r], e, i, a), r;
}, Ke = (t, e, n) => t.reduce((i, o, s) => {
  let r = e[s];
  if (r && r.call) {
    let a = r(n), l = a && a.props && a.props.className || /^go/.test(a) && a;
    r = l ? "." + l : a && typeof a == "object" ? a.props ? "" : H(a, "") : a === !1 ? "" : a;
  }
  return i + o + (r ?? "");
}, "");
function Ct(t) {
  let e = this || {}, n = t.call ? t(e.p) : t;
  return Je(n.unshift ? n.raw ? Ke(n, [].slice.call(arguments, 1), e.p) : n.reduce((i, o) => Object.assign(i, o && o.call ? o(e.p) : o), {}) : n, We(e.target), e.g, e.o, e.k);
}
Ct.bind({ g: 1 });
Ct.bind({ k: 1 });
function yt(t) {
  return typeof t == "object" && t !== null && !Array.isArray(t);
}
function lt(t, e) {
  for (const n in e) {
    const i = e[n], o = t[n];
    yt(o) && yt(i) ? t[n] = lt(o, i) : yt(i) ? t[n] = lt({}, i) : t[n] = i;
  }
  return t;
}
function ae(t) {
  const e = [];
  function n(...s) {
    const r = e.reduce((a, l) => lt(a, l(...s)), t(...s));
    return {
      css: r,
      toString() {
        return Ct(r);
      }
    };
  }
  function i(s) {
    return e.push(s), n;
  }
  function o(s) {
    return ae((...r) => lt(n(...r).css, s(...r)));
  }
  return n.merge = i, n.extend = o, n;
}
function le(t) {
  const e = new Map(Array.isArray(t) ? t : Object.entries(t));
  function n(o, s) {
    if (typeof o == "string" && s !== void 0)
      e.set(o, s);
    else if (Array.isArray(o))
      for (const [r, a] of o)
        e.set(r, a);
    else if (typeof o == "object")
      for (const [r, a] of Object.entries(o))
        e.set(r, a);
  }
  function i(o) {
    if (Array.isArray(o))
      for (const s of o)
        e.delete(s);
    else
      e.delete(o);
  }
  return {
    map: e,
    define: n,
    unset: i
  };
}
function Qn(t) {
  const { map: e, define: n, unset: i } = le(
    Array.isArray(t) ? t : Object.entries(t)
  );
  function o(s, r) {
    const a = e.get(s);
    return typeof a == "function" ? a(s) : a !== void 0 ? a : r !== void 0 ? r : s;
  }
  return {
    map: e,
    define: n,
    translate: o,
    unset: i
  };
}
const Zn = 7, ti = 864e5, ei = 36e5, ni = 6e4, Ge = [
  "Sunday",
  "Monday",
  "Tuesday",
  "Wednesday",
  "Thursday",
  "Friday",
  "Saturday"
], Xe = [
  "Sun",
  "Mon",
  "Tue",
  "Wed",
  "Thu",
  "Fri",
  "Sat",
  "Sun"
], Qe = [
  "January",
  "February",
  "March",
  "April",
  "May",
  "June",
  "July",
  "August",
  "September",
  "October",
  "November",
  "December"
], Ze = [
  "Jan",
  "Feb",
  "Mar",
  "Apr",
  "May",
  "Jun",
  "Jul",
  "Aug",
  "Sep",
  "Oct",
  "Nov",
  "Dec"
];
function Yt(t) {
  const { map: e, define: n, unset: i } = le({
    A: (r) => r.getHours() < 12 ? "AM" : "PM",
    a: (r) => r.getHours() < 12 ? "am" : "pm",
    Q: (r) => Math.ceil((r.getMonth() + 1) / 3).toString(),
    YYYY: (r) => r.getFullYear().toString(),
    YY: (r) => F(r.getFullYear().toString().slice(2), 2),
    MMMM: (r) => String(Qe[r.getMonth()]),
    MMM: (r) => String(Ze[r.getMonth()]),
    MM: (r) => F(r.getMonth() + 1, 2),
    M: (r) => String(r.getMonth() + 1),
    DDDD: (r) => String(Ge[r.getDay()]),
    DDD: (r) => String(Xe[r.getDay()]),
    DD: (r) => F(r.getDate(), 2),
    D: (r) => String(r.getDate()),
    HH: (r) => F(r.getHours(), 2),
    H: (r) => String(r.getHours()),
    hh: (r) => F(zt(r), 2),
    h: (r) => zt(r),
    mm: (r) => F(r.getMinutes(), 2),
    m: (r) => String(r.getMinutes()),
    ss: (r) => F(r.getSeconds(), 2),
    s: (r) => String(r.getSeconds()),
    vvvv: (r) => F(r.getMilliseconds(), 4),
    vvv: (r) => F(r.getMilliseconds(), 3),
    vv: (r) => F(r.getMilliseconds(), 2),
    v: (r) => String(r.getMilliseconds()),
    ...t?.formats
  }), o = typeof t?.translate == "function" ? t.translate : t?.translate?.translate;
  function s(r, a) {
    const l = new RegExp([...tn(e)].join("|"), "g");
    return a.replace(l, (c) => {
      const f = e.get(c)(r);
      return o?.(f) ?? f;
    });
  }
  return { map: e, define: n, format: s, unset: i };
}
function tn(t) {
  return Array.from(t.keys()).sort((e, n) => e.length < n.length ? 1 : e.length > n.length ? -1 : 0);
}
function F(t, e) {
  return t === void 0 ? "" : (typeof t == "number" && (t = t.toString()), e < t.length ? t : Array(e - t.length + 1).join("0") + t);
}
function zt(t) {
  const e = t.getHours() % 12;
  return String(e === 0 ? 12 : e);
}
const en = 864e5, nn = 6e4, rn = 36e5, Ht = Symbol.for("constructDateFrom");
function O(t, e) {
  return typeof t == "function" ? t(e) : t && typeof t == "object" && Ht in t ? t[Ht](e) : t instanceof Date ? new t.constructor(e) : new Date(e);
}
function D(t, e) {
  return O(e || t, t);
}
function ce(t, e, n) {
  const i = D(t, n?.in);
  return isNaN(e) ? O(n?.in || t, NaN) : (e && i.setDate(i.getDate() + e), i);
}
function ue(t, e, n) {
  const i = D(t, n?.in);
  if (isNaN(e)) return O(n?.in || t, NaN);
  if (!e)
    return i;
  const o = i.getDate(), s = O(n?.in || t, i.getTime());
  s.setMonth(i.getMonth() + e + 1, 0);
  const r = s.getDate();
  return o >= r ? s : (i.setFullYear(
    s.getFullYear(),
    s.getMonth(),
    o
  ), i);
}
function z(t, e, n) {
  const {
    years: i = 0,
    months: o = 0,
    weeks: s = 0,
    days: r = 0,
    hours: a = 0,
    minutes: l = 0,
    seconds: c = 0
  } = e, f = D(t, n?.in), d = o || i ? ue(f, o + i * 12) : f, h = r || s ? ce(d, r + s * 7) : d, u = l + a * 60, w = (c + u * 60) * 1e3;
  return O(n?.in || t, +h + w);
}
function Pt(t) {
  const e = D(t), n = new Date(
    Date.UTC(
      e.getFullYear(),
      e.getMonth(),
      e.getDate(),
      e.getHours(),
      e.getMinutes(),
      e.getSeconds(),
      e.getMilliseconds()
    )
  );
  return n.setUTCFullYear(e.getFullYear()), +t - +n;
}
function B(t, ...e) {
  const n = O.bind(
    null,
    t || e.find((i) => typeof i == "object")
  );
  return e.map(n);
}
function qt(t, e) {
  const n = D(t, e?.in);
  return n.setHours(0, 0, 0, 0), n;
}
function sn(t, e, n) {
  const [i, o] = B(
    n?.in,
    t,
    e
  ), s = qt(i), r = qt(o), a = +s - Pt(s), l = +r - Pt(r);
  return Math.round((a - l) / en);
}
function X(t, e) {
  const n = +D(t) - +D(e);
  return n < 0 ? -1 : n > 0 ? 1 : n;
}
function on(t, e, n) {
  const [i, o] = B(
    n?.in,
    t,
    e
  ), s = i.getFullYear() - o.getFullYear(), r = i.getMonth() - o.getMonth();
  return s * 12 + r;
}
function an(t, e, n) {
  const [i, o] = B(
    n?.in,
    t,
    e
  );
  return i.getFullYear() - o.getFullYear();
}
function fe(t, e, n) {
  const [i, o] = B(
    n?.in,
    t,
    e
  ), s = Wt(i, o), r = Math.abs(
    sn(i, o)
  );
  i.setDate(i.getDate() - s * r);
  const a = +(Wt(i, o) === -s), l = s * (r - a);
  return l === 0 ? 0 : l;
}
function Wt(t, e) {
  const n = t.getFullYear() - e.getFullYear() || t.getMonth() - e.getMonth() || t.getDate() - e.getDate() || t.getHours() - e.getHours() || t.getMinutes() - e.getMinutes() || t.getSeconds() - e.getSeconds() || t.getMilliseconds() - e.getMilliseconds();
  return n < 0 ? -1 : n > 0 ? 1 : n;
}
function ht(t) {
  return (e) => {
    const i = (t ? Math[t] : Math.trunc)(e);
    return i === 0 ? 0 : i;
  };
}
function ln(t, e, n) {
  const [i, o] = B(
    n?.in,
    t,
    e
  ), s = (+i - +o) / rn;
  return ht(n?.roundingMethod)(s);
}
function ct(t, e) {
  return +D(t) - +D(e);
}
function cn(t, e, n) {
  const i = ct(t, e) / nn;
  return ht(n?.roundingMethod)(i);
}
function un(t, e) {
  const n = D(t, e?.in);
  return n.setHours(23, 59, 59, 999), n;
}
function fn(t, e) {
  const n = D(t, e?.in), i = n.getMonth();
  return n.setFullYear(n.getFullYear(), i + 1, 0), n.setHours(23, 59, 59, 999), n;
}
function hn(t, e) {
  const n = D(t, e?.in);
  return +un(n, e) == +fn(n, e);
}
function dn(t, e, n) {
  const [i, o, s] = B(
    n?.in,
    t,
    t,
    e
  ), r = X(o, s), a = Math.abs(
    on(o, s)
  );
  if (a < 1) return 0;
  o.getMonth() === 1 && o.getDate() > 27 && o.setDate(30), o.setMonth(o.getMonth() - r * a);
  let l = X(o, s) === -r;
  hn(i) && a === 1 && X(i, s) === 1 && (l = !1);
  const c = r * (a - +l);
  return c === 0 ? 0 : c;
}
function gn(t, e, n) {
  const i = ct(t, e) / 1e3;
  return ht(n?.roundingMethod)(i);
}
function mn(t, e, n) {
  const i = fe(t, e, n) / 7;
  return ht(n?.roundingMethod)(i);
}
function pn(t, e, n) {
  const [i, o] = B(
    n?.in,
    t,
    e
  ), s = X(i, o), r = Math.abs(an(i, o));
  i.setFullYear(1584), o.setFullYear(1584);
  const a = X(i, o) === -s, l = s * (r - +a);
  return l === 0 ? 0 : l;
}
function yn(t, e) {
  const n = D(t, e?.in), i = n.getFullYear(), o = n.getMonth(), s = O(n, 0);
  return s.setFullYear(i, o + 1, 0), s.setHours(0, 0, 0, 0), s.getDate();
}
function bn(t, e, n) {
  return ce(t, -e, n);
}
function wn(t, e, n) {
  const i = D(t, n?.in), o = i.getFullYear(), s = i.getDate(), r = O(t, 0);
  r.setFullYear(o, e, 15), r.setHours(0, 0, 0, 0);
  const a = yn(r);
  return i.setMonth(e, Math.min(s, a)), i;
}
function Bt(t, e, n) {
  let i = D(t, n?.in);
  return isNaN(+i) ? O(t, NaN) : (e.year != null && i.setFullYear(e.year), e.month != null && (i = wn(i, e.month)), e.date != null && i.setDate(e.date), e.hours != null && i.setHours(e.hours), e.minutes != null && i.setMinutes(e.minutes), e.seconds != null && i.setSeconds(e.seconds), e.milliseconds != null && i.setMilliseconds(e.milliseconds), i);
}
function vn(t, e, n) {
  return ue(t, -e, n);
}
function ii(t, e, n) {
  const {
    years: i = 0,
    months: o = 0,
    weeks: s = 0,
    days: r = 0,
    hours: a = 0,
    minutes: l = 0,
    seconds: c = 0
  } = e, f = vn(t, o + i * 12, n), d = bn(f, r + s * 7, n), h = l + a * 60, b = (c + h * 60) * 1e3;
  return O(n?.in || t, +d - b);
}
const bt = {
  years: pn,
  months: dn,
  weeks: mn,
  days: fe,
  hours: ln,
  minutes: cn,
  seconds: gn
}, An = {
  years: (t, e) => z(t, { years: e }),
  months: (t, e) => z(t, { months: e }),
  weeks: (t, e) => z(t, { weeks: e }),
  days: (t, e) => z(t, { days: e }),
  hours: (t, e) => z(t, { hours: e }),
  minutes: (t, e) => z(t, { minutes: e }),
  seconds: (t, e) => z(t, { seconds: e })
};
function Sn(t, e, n) {
  return n.sort((i, o) => Object.keys(bt).indexOf(i) - Object.keys(bt).indexOf(o)).reduce((i, o) => {
    const s = bt[o], r = An[o], a = s(i.end, i.start);
    return {
      ...i,
      result: { ...i.result, [o]: a },
      start: r(i.start, a)
    };
  }, {
    result: {},
    start: new Date(t),
    end: new Date(e)
  }).result;
}
function xn() {
  const t = {
    years: "Y",
    months: "M",
    weeks: "W",
    days: "D",
    hours: "h",
    minutes: "m",
    seconds: "s"
  };
  function e(n, i, o) {
    const s = new RegExp(
      Object.values(t).map((c) => `${c}+`).join("|"),
      "g"
    ), r = o.match(s)?.map((c) => c[0]).filter((c, f, d) => d.indexOf(c) === f).reduce((c, f) => {
      const d = Object.keys(t).find(
        (h) => t[h] === f
      );
      return [...c, d];
    }, []), a = Sn(
      Bt(new Date(n), { milliseconds: 0 }),
      Bt(new Date(i), { milliseconds: 0 }),
      r
    );
    return Object.entries(a).reduce((c, [f, d]) => {
      const h = new RegExp(`${t[f]}+`, "g");
      return c.replace(h, (u) => F(Math.abs(d), u.length));
    }, o);
  }
  return {
    format: e
  };
}
function Mn(t) {
  const e = t?.trim().split(",")[0]?.match(/^([+-]?(?:\d+\.?\d*|\.\d+))\s*(ms|s|m|h)$/i);
  if (!e)
    return 0;
  const [, n, i] = e;
  return parseFloat(n) * {
    ms: 1,
    s: 1e3,
    m: 6e4,
    h: 36e5
  }[i.toLowerCase()];
}
function Dn(t) {
  return Mn(
    getComputedStyle(t).getPropertyValue("--animation-duration")
  );
}
function $n(t) {
  const { charset: e, next: n, prev: i } = t?.charset && "next" in t.charset ? t.charset : Pe(t?.charset);
  function o(r, a, l = 1, c = !1) {
    const f = {
      backwards: c,
      ...t?.matchArray
    };
    return r.digits = jt(
      r.digits,
      a.digits,
      f,
      St((d, h, u) => t?.stopWhen ? t.stopWhen(d, h, u) : t?.stopAfterChanges ? d.length < t.stopAfterChanges : !0, (d, h) => d === h ? d : i(d ?? "", h, l))
    ), r;
  }
  function s(r, a, l = 1, c = !1) {
    const f = {
      ...t?.matchArray,
      backwards: c
    };
    return r.digits = jt(
      r.digits,
      a.digits,
      f,
      St((d, h, u) => t?.stopWhen ? t.stopWhen(d, h, u) : t?.stopAfterChanges ? d.length < t.stopAfterChanges : !0, (d, h) => d === h ? d : n(d, h, l))
    ), r;
  }
  return {
    charset: e,
    decrement: o,
    increment: s
  };
}
class kn {
  /**
   * The sequencer method.
   * 
   * @public
   */
  method = "increment";
  /**
   * The flip direction. If auto, the direction is automatically determined
   * based on the current value and target value.
   * 
   * @public
   */
  direction = "auto";
  /**
   * Override how digits are sequenced.
   * 
   * @public
   */
  sequencer;
  /**
   * The number of characters to skip during the incrementing/decrementing.
   * 
   * @public
   */
  skipChars;
  /**
   * The face's current value.
   * 
   * @public
   */
  value;
  /**
   * The face's target value.
   * 
   * @public
   */
  targetValue;
  /**
   * The face's current value.
   * 
   * @protected
   */
  currentValue;
  /**
   * Construct the clock face.
   * 
   * @public
   */
  constructor(e) {
    e.skipChars && (this.skipChars = e.skipChars), e.direction && (this.direction = e.direction), e.method && (this.method = e.method), this.sequencer = e.sequencer && "increment" in e.sequencer ? e.sequencer : $n(e.sequencer), this.value = e.value, this.targetValue = e.targetValue ?? this.value.copy(), this.currentValue = J(this.value.digits);
  }
  /**
   * The sequencer method to call.
   * 
   * @public
   */
  get backwards() {
    return this.direction === "backwards" ? !0 : this.direction === "forwards" ? !1 : At(this.value.digits) > At(this.targetValue.digits);
  }
  /**
   * The face's current value.
   * 
   * @public
   */
  faceValue() {
    return this.currentValue;
  }
  /**
   * This method is called with every interval, or every time the clock
   * should change, and handles the actual incrementing and decrementing the
   * clock's `FaceValue`.
   * 
   * @public
   */
  interval(e) {
    this[this.method](), this.currentValue.compare(this.targetValue) && e.stop();
  }
  /**
   * Increment the value to the next sequence.
   * 
   * @public
   */
  increment() {
    this.sequencer.increment(
      this.value,
      this.targetValue,
      this.skipChars,
      this.backwards
    ), this.currentValue.value = this.value.digits;
  }
  /**
   * Decrement the value to the next sequence.
   * 
   * @public
   */
  decrement() {
    this.sequencer.decrement(
      this.value,
      this.targetValue,
      this.skipChars,
      this.backwards
    ), this.currentValue.value = this.value.digits;
  }
}
function ri(t) {
  return new kn(t);
}
class Cn {
  /**
   * The starting date on the clock. If no date is set, the current time
   * will be used.
   * 
   * @public
   */
  date;
  /**
   * The current formatted value.
   * 
   * @public
   */
  value;
  /**
   * The format string.
   * 
   * @public
   */
  format = "[hh]:[mm]:[ss][A]";
  /**
   * The duration formatter.
   * 
   * @public
   */
  formatter;
  /**
   * Instantiate the clock face.
   * 
   * @public
   */
  constructor(e) {
    this.date = e?.date ?? /* @__PURE__ */ new Date(), e?.format && (this.format = e.format), e?.formatter === void 0 ? this.formatter = Yt() : "format" in e.formatter ? this.formatter = e.formatter : this.formatter = Yt(e.formatter), this.value = q(() => J(this.formatter.format(this.date, this.format)));
  }
  /**
   * The face's current value.
   * 
   * @public
   */
  faceValue() {
    return this.value;
  }
  /**
   * Format the face value to the current date/time.
   * 
   * @public
   */
  interval(e) {
    this.value.value = this.formatter.format(
      new Date(this.date.getTime() + e.timer.elapsed),
      this.format
    );
  }
}
function si(t) {
  return new Cn(t);
}
class Fn {
  /**
   * Should the face count down instead of up.
   * 
   * @public
   */
  countdown = !1;
  /**
   * The number to increment/decrement in the interval.
   * 
   * @public
   */
  step = 1;
  /**
   * The formatted face value to display on the clock.
   * 
   * @protected
   */
  formattedValue;
  /**
   * The target value determines when the counter should stop.
   * 
   * @public
   */
  targetValue;
  /**
   * The current face value.
   * 
   * @public
   */
  value;
  /**
   * A format callback. If the `formatter` is defined, this prop is ignored.
   * 
   * @public
   */
  format;
  /**
   * An `Intl.NumberFormat` instance used to format the number into a string.
   * 
   * @public
   */
  formatter;
  /**
   * Construct the clock face.
   * 
   * @public
   */
  constructor(e) {
    this.value = typeof e?.value == "number" || e?.value === void 0 ? J(e?.value ?? 0) : e.value, this.targetValue = typeof e?.targetValue == "number" ? J(e.targetValue) : e?.targetValue, this.format = e?.format, this.formatter = e?.formatter, this.formattedValue = q(() => {
      const n = J(this.formattedString);
      return Zt(() => {
        n.value = this.formattedString;
      }), n;
    }), typeof e?.countdown == "boolean" && (this.countdown = e.countdown), typeof e?.step == "number" && (this.step = e.step);
  }
  /**
   * Get the number as a formatted string.
   * 
   * @public
   */
  get formattedString() {
    return this.formatter ? this.formatter.format(this.value.value) : this.format ? this.format(this.value.value) : this.value.value.toString();
  }
  /**
   * The face's current value.
   * 
   * @public
   */
  faceValue() {
    return this.formattedValue;
  }
  /**
   * This method is called with every interval, or every time the clock
   * should change, and handles the actual incrementing and decrementing the
   * clock's `FaceValue`.
   * 
   * @public
   */
  interval(e) {
    this.countdown ? this.decrement(this.step) : this.increment(this.step), this.value.compare(this.targetValue) && e.stop();
  }
  /**
   * Substract the face value by the given value.
   * 
   * @public
   */
  decrement(e) {
    this.value.value = this.value.value - (e ?? this.step);
  }
  /**
   * Add to the face value by the given value.
   * 
   * @public
   */
  increment(e) {
    this.value.value = this.value.value + (e ?? this.step);
  }
}
function oi(t) {
  return new Fn(t);
}
class En {
  /**
   * The date used to calculate the current.
   * 
   * @protected
   */
  start;
  /**
   * The date used to calculate the current.
   * 
   * @protected
   */
  current;
  /**
   * The "from" date used to calculate the elsapsed time.
   * 
   * @public
   */
  from;
  /**
   * The "to" date used to calculate the elsapsed time.
   * 
   * @public
   */
  to;
  /**
   * The format string.
   * 
   * @public
   */
  format = "[mm]:[ss]";
  /**
   * The duration formatter.
   * 
   * @public
   */
  formatter;
  /**
   * The current face value.
   * 
   * @public
   */
  value;
  /**
   * Construct the clock face.
   * 
   * @public
   */
  constructor(e) {
    this.from = e?.from, this.to = e?.to, this.start = /* @__PURE__ */ new Date(), this.current = new Date(this.start), e?.format && (this.format = e.format), e?.formatter ? this.formatter = e.formatter : this.formatter = xn(), this.value = q(() => J(this.formattedString));
  }
  /**
   * Get the elapsed time as a formatted string.
   * 
   * @public
   */
  get formattedString() {
    return this.from ? this.formatter.format(
      this.from,
      this.current,
      this.format
    ) : this.to ? this.formatter.format(
      this.to,
      this.current,
      this.format
    ) : this.formatter.format(
      this.start,
      this.current,
      this.format
    );
  }
  /**
   * The face's current value.
   * 
   * @public
   */
  faceValue() {
    return this.value;
  }
  /**
   * Format the value with the new elapsed time.
   * 
   * @public
   */
  interval(e) {
    this.shouldStop() ? e.stop() : (this.current.setTime(e.timer.lastLoop), this.value.value = this.formattedString);
  }
  /**
   * Set the dates before the clock starts.
   * 
   * @public
   */
  beforeStart() {
    this.start = /* @__PURE__ */ new Date(), this.current = new Date(this.start);
  }
  /**
   * Determines if the clock should be stopped.
   * 
   * @public
   */
  shouldStop() {
    return this.from && this.from > this.start ? ct(this.from, this.current) <= 0 : this.to ? ct(this.to, this.current) <= 0 : !1;
  }
}
function ai(t) {
  return new En(t);
}
class xt {
  /**
   * The count increments with each interval.
   * 
   * @protected
   */
  $count = 0;
  /**
   * The requestAnimationFrame handle number.
   * 
   * @protected
   */
  $handle;
  /**
   * The number of milliseconds that define an interval.
   * 
   * @public
   */
  interval;
  /**
   * The timestamp of the last loop.
   * 
   * @protected
   */
  $lastLoop;
  /**
   * The date the timer starts.
   * 
   * @protected
   */
  $startDate;
  /**
   * Construct the timer.
   * 
   * @public
   */
  constructor(e = 1e3) {
    this.interval = e;
  }
  /**
   * Get the number of times the timer has ticked.
   * 
   * @public
   */
  get count() {
    return this.$count;
  }
  /**
   * The `elapsed` attribute.
   * 
   * @public
   */
  get elapsed() {
    return this.$startDate ? Math.max(0, Date.now() - this.$startDate.getTime()) : 0;
  }
  /**
   * The `elapsedSinceLastLoop` attribute.
   * 
   * @public
   */
  get elapsedSinceLastLoop() {
    return this.lastLoop ? Date.now() - this.lastLoop : 0;
  }
  /**
   * Determines if the Timer is currently running.
   * 
   * @public
   */
  get isRunning() {
    return this.$handle !== void 0;
  }
  /**
   * Determines if the Timer is currently stopped.
   * 
   * @public
   */
  get isStopped() {
    return !this.isRunning;
  }
  /**
   * Get the last timestamp the timer looped.
   * 
   * @public
   */
  get lastLoop() {
    return this.$lastLoop || 0;
  }
  /**
   * Set the last timestamp the timer looped.
   * 
   * @public
   */
  set lastLoop(e) {
    this.$lastLoop = e;
  }
  /**
   * Get the date object when the timer started.
   * 
   * @public
   */
  get started() {
    return this.$startDate;
  }
  /**
   * Resets the timer. If a callback is provided, re-start the clock.
   * 
   * @public
   */
  reset(e) {
    return this.stop(() => {
      this.$count = 0, this.$lastLoop = 0, this.start(e);
    }), this;
  }
  /**
   * Starts the timer.
   * 
   * @public
   */
  start(e) {
    this.$startDate = /* @__PURE__ */ new Date(), this.$lastLoop = this.$startDate.getTime();
    const n = () => (Date.now() - this.lastLoop >= this.interval && (typeof e == "function" && e(this), this.$lastLoop = Date.now(), this.$count++), this.$handle = requestAnimationFrame(n), this);
    return n();
  }
  /**
   * Stops the timer.
   * 
   * @public
   */
  stop(e) {
    return this.isRunning && this.$handle && (window.cancelAnimationFrame(this.$handle), this.$lastLoop = 0, this.$handle = void 0, typeof e == "function" && e(this)), this;
  }
}
function li(t = 1e3) {
  return new xt(t);
}
class On extends Gt {
  /**
   * Determines if the clock should automatically start when it is mounted.
   * 
   * @public
   */
  autoStart = !0;
  /**
   * The parent element to which the clock is mounted.
   * 
   * @public
   */
  parent;
  /**
   * The clock element.
   * 
   * @public
   */
  el;
  /**
   * The face used to display the clock.
   * 
   * @public
   */
  face;
  /**
   * The face used to display the clock.
   * 
   * @public
   */
  theme;
  /**
   * The face value displayed on the clock.
   * 
   * @public
   */
  timer;
  /**
   * Dispose of the clock.
   * 
   * @private
   */
  dispose;
  /**
   * Construct the FlipClock.
   * 
   * @public
   */
  constructor(e) {
    super(), this.face = e.face, this.theme = e.theme, typeof e.autoStart == "boolean" && (this.autoStart = e.autoStart), this.timer = e.timer instanceof xt ? e.timer : new xt(e.timer), this.hook("afterCreate", this), e.parent && this.mount(e.parent);
  }
  /**
   * Get the animation rate of the clock.
   * 
   * @public
   */
  get animationRate() {
    return this.el ? Dn(this.el) : 0;
  }
  /**
   * Mount the clock instance to the DOM.
   * 
   * @public
   */
  mount(e) {
    this.hook("beforeMount", this), this.parent = e;
    const [n, i] = this.theme.render(this.parent, this);
    return this.el = n, this.dispose = i, this.hook("afterMount", this), this.autoStart && this.timer.isStopped && requestAnimationFrame(() => this.start()), this;
  }
  /**
   * Start the clock instance.
   * 
   * @public
   */
  start(e) {
    return this.hook("beforeStart", this), this.timer.start(() => {
      requestAnimationFrame(() => {
        this.hook("beforeInterval", this), this.face.interval(this), this.hook("afterInterval", this), typeof e == "function" && e(this), this.hook("afterStart", this);
      });
    }), this;
  }
  /**
   * Stop the clock instance.
   * 
   * @public
   */
  stop(e) {
    return this.hook("beforeStop", this), this.timer.stop(() => {
      typeof e == "function" && e(this), this.hook("afterStop", this);
    }), this;
  }
  /**
   * Toggle starting/stopping the clock instance.
   * 
   * @public
   */
  toggle(e) {
    return this.timer.isStopped ? this.start(e) : this.stop(e), this;
  }
  /**
   * Unmount the clock instance from the DOM.
   * 
   * @public
   */
  unmount() {
    return this.hook("beforeUnmount", this), this.timer.stop(), this.el?.remove(), this.dispose?.(), this.hook("afterUnmount", this), this;
  }
  /**
   * Dispatch the event and call the method that corresponds to given hook.
   * 
   * @protected
   */
  hook(e, ...n) {
    if (e in this.face && typeof this.face[e] == "function" && this.face[e].apply(this.face, n), e in this.theme && typeof this.theme[e] == "function") {
      const i = this.theme[e];
      i(...n);
    }
    this.emit(e, ...n);
  }
}
function ci(t) {
  return new On(t);
}
const In = (t) => $(() => t());
function Tn(t, e, n) {
  let i = n.length, o = e.length, s = i, r = 0, a = 0, l = e[o - 1].nextSibling, c = null;
  for (; r < o || a < s; ) {
    if (e[r] === n[a]) {
      r++, a++;
      continue;
    }
    for (; e[o - 1] === n[s - 1]; )
      o--, s--;
    if (o === r) {
      const f = s < i ? a ? n[a - 1].nextSibling : n[s - a] : l;
      for (; a < s; ) t.insertBefore(n[a++], f);
    } else if (s === a)
      for (; r < o; )
        (!c || !c.has(e[r])) && e[r].remove(), r++;
    else if (e[r] === n[s - 1] && n[a] === e[o - 1]) {
      const f = e[--o].nextSibling;
      t.insertBefore(n[a++], e[r++].nextSibling), t.insertBefore(n[--s], f), e[o] = n[s];
    } else {
      if (!c) {
        c = /* @__PURE__ */ new Map();
        let d = a;
        for (; d < s; ) c.set(n[d], d++);
      }
      const f = c.get(e[r]);
      if (f != null)
        if (a < f && f < s) {
          let d = r, h = 1, u;
          for (; ++d < o && d < s && !((u = c.get(e[d])) == null || u !== f + h); )
            h++;
          if (h > f - a) {
            const b = e[r];
            for (; a < f; ) t.insertBefore(n[a++], b);
          } else t.replaceChild(n[a++], e[r++]);
        } else r++;
      else e[r++].remove();
    }
  }
}
function Vn(t, e, n, i = {}) {
  let o;
  return q((s) => {
    o = s, e === document ? t() : E(e, t(), e.firstChild ? null : void 0, n);
  }, i.owner), () => {
    o(), e.textContent = "";
  };
}
function K(t, e, n, i) {
  let o;
  const s = () => {
    const a = document.createElement("template");
    return a.innerHTML = t, a.content.firstChild;
  }, r = () => (o || (o = s())).cloneNode(!0);
  return r.cloneNode = r, r;
}
function Mt(t, e, n) {
  n == null ? t.removeAttribute(e) : t.setAttribute(e, n);
}
function _n(t, e, n, i) {
  if (Array.isArray(n)) {
    const o = n[0];
    t.addEventListener(e, n[0] = (s) => o.call(t, n[1], s));
  } else t.addEventListener(e, n, typeof n != "function" && n);
}
function he(t, e, n = {}) {
  const i = Object.keys(e || {}), o = Object.keys(n);
  let s, r;
  for (s = 0, r = o.length; s < r; s++) {
    const a = o[s];
    !a || a === "undefined" || e[a] || (Ut(t, a, !1), delete n[a]);
  }
  for (s = 0, r = i.length; s < r; s++) {
    const a = i[s], l = !!e[a];
    !a || a === "undefined" || n[a] === l || !l || (Ut(t, a, !0), n[a] = l);
  }
  return n;
}
function Ln(t, e, n) {
  return V(() => t(e, n));
}
function E(t, e, n, i) {
  if (n !== void 0 && !i && (i = []), typeof e != "function") return ut(t, e, i, n);
  W((o) => ut(t, e(), o, n), i);
}
function Ut(t, e, n) {
  const i = e.trim().split(/\s+/);
  for (let o = 0, s = i.length; o < s; o++) t.classList.toggle(i[o], n);
}
function ut(t, e, n, i, o) {
  for (; typeof n == "function"; ) n = n();
  if (e === n) return n;
  const s = typeof e, r = i !== void 0;
  if (t = r && n[0] && n[0].parentNode || t, s === "string" || s === "number") {
    if (s === "number" && (e = e.toString(), e === n))
      return n;
    if (r) {
      let a = n[0];
      a && a.nodeType === 3 ? a.data !== e && (a.data = e) : a = document.createTextNode(e), n = U(t, n, i, a);
    } else
      n !== "" && typeof n == "string" ? n = t.firstChild.data = e : n = t.textContent = e;
  } else if (e == null || s === "boolean")
    n = U(t, n, i);
  else {
    if (s === "function")
      return W(() => {
        let a = e();
        for (; typeof a == "function"; ) a = a();
        n = ut(t, a, n, i);
      }), () => n;
    if (Array.isArray(e)) {
      const a = [], l = n && Array.isArray(n);
      if (Dt(a, e, n, o))
        return W(() => n = ut(t, a, n, i, !0)), () => n;
      if (a.length === 0) {
        if (n = U(t, n, i), r) return n;
      } else l ? n.length === 0 ? Jt(t, a, i) : Tn(t, n, a) : (n && U(t), Jt(t, a));
      n = a;
    } else if (e.nodeType) {
      if (Array.isArray(n)) {
        if (r) return n = U(t, n, i, e);
        U(t, n, null, e);
      } else n == null || n === "" || !t.firstChild ? t.appendChild(e) : t.replaceChild(e, t.firstChild);
      n = e;
    }
  }
  return n;
}
function Dt(t, e, n, i) {
  let o = !1;
  for (let s = 0, r = e.length; s < r; s++) {
    let a = e[s], l = n && n[t.length], c;
    if (!(a == null || a === !0 || a === !1)) if ((c = typeof a) == "object" && a.nodeType)
      t.push(a);
    else if (Array.isArray(a))
      o = Dt(t, a, l) || o;
    else if (c === "function")
      if (i) {
        for (; typeof a == "function"; ) a = a();
        o = Dt(t, Array.isArray(a) ? a : [a], Array.isArray(l) ? l : [l]) || o;
      } else
        t.push(a), o = !0;
    else {
      const f = String(a);
      l && l.nodeType === 3 && l.data === f ? t.push(l) : t.push(document.createTextNode(f));
    }
  }
  return o;
}
function Jt(t, e, n = null) {
  for (let i = 0, o = e.length; i < o; i++) t.insertBefore(e[i], n);
}
function U(t, e, n, i) {
  if (n === void 0) return t.textContent = "";
  const o = i || document.createTextNode("");
  if (e.length) {
    let s = !1;
    for (let r = e.length - 1; r >= 0; r--) {
      const a = e[r];
      if (o !== a) {
        const l = a.parentNode === t;
        !s && !r ? l ? t.replaceChild(o, a) : t.insertBefore(o, n) : l && a.remove();
      } else s = !0;
    }
  } else t.insertBefore(o, n);
  return [o];
}
var Nn = /* @__PURE__ */ K("<div class=flip-clock>"), jn = /* @__PURE__ */ K("<div class=flip-clock-label>"), Rn = /* @__PURE__ */ K("<div class=flip-clock-group><div class=flip-clock-group-items>"), Yn = /* @__PURE__ */ K("<div class=flip-clock-card>"), zn = /* @__PURE__ */ K("<div class=flip-clock-card-item><div class=flip-clock-card-item-inner><div class=top></div><div class=bottom>"), Hn = /* @__PURE__ */ K("<div class=flip-clock-divider><div class=flip-clock-divider-inner>");
function ui(t) {
  return {
    render(e, n) {
      return q((i) => {
        let o;
        const s = $(() => (Array.isArray(t?.css) ? t.css : [t?.css]).filter(Boolean).map((r) => String(r)).join(" "));
        return Vn(() => (() => {
          var r = Nn();
          return Ln((a) => o = a, r), E(r, k(de, {
            get digits() {
              return n.face.faceValue().digits;
            },
            get dividers() {
              return t?.dividers;
            },
            get labels() {
              return In(() => !!t?.labels)() ? [...t.labels] : void 0;
            }
          })), W((a) => he(r, {
            [s()]: !0
          }, a)), r;
        })(), e), [o, i];
      });
    }
  };
}
function Pn(t) {
  if (t !== void 0)
    return t instanceof RegExp ? t : new RegExp(`[${(Array.isArray(t) ? t : [t]).join("|")}]`);
}
function qn(t, e) {
  const n = Pn(e);
  return n ? !!t.match(n)?.length : !1;
}
function de(t) {
  const e = t.labels?.shift();
  let n = 0;
  return (() => {
    var i = Rn(), o = i.firstChild;
    return E(i, k(Oe, {
      when: typeof e == "string",
      get children() {
        var s = jn();
        return E(s, e), s;
      }
    }), o), E(o, k(Ee, {
      get each() {
        return t.digits;
      },
      children: (s) => {
        const r = $(() => {
          const a = s();
          return Array.isArray(a) ? "group" : qn(a, t.dividers) ? "divider" : "card";
        });
        return k(Ie, {
          get children() {
            return [k(mt, {
              get when() {
                return r() === "group";
              },
              get children() {
                return (() => {
                  const a = Array.isArray(t.labels?.[n]) ? t.labels[n++] : void 0;
                  return k(de, {
                    get digits() {
                      return s();
                    },
                    get dividers() {
                      return t.dividers;
                    },
                    labels: a
                  });
                })();
              }
            }), k(mt, {
              get when() {
                return r() === "divider";
              },
              get children() {
                return k(Bn, {
                  get value() {
                    return s();
                  }
                });
              }
            }), k(mt, {
              get when() {
                return r() === "card";
              },
              get children() {
                return k(Wn, {
                  get value() {
                    return s();
                  }
                });
              }
            })];
          }
        });
      }
    })), i;
  })();
}
function Wn(t) {
  const [e, n] = P(t.value), [i, o] = P(t.value), [s, r] = P(!1);
  return o(t.value), n(t.value), Zt(() => {
    const a = t.value;
    r(!1), requestAnimationFrame(() => {
      o(e()), n(a), a !== i() && r(!0);
    });
  }), (() => {
    var a = Yn();
    return E(a, k(Kt, {
      get value() {
        return e();
      },
      classList: {
        active: !0
      }
    }), null), E(a, k(Kt, {
      get value() {
        return i();
      },
      classList: {
        before: !0
      }
    }), null), W((l) => {
      var c = e(), f = i(), d = !!s();
      return c !== l.e && Mt(a, "data-value", l.e = c), f !== l.t && Mt(a, "data-before-value", l.t = f), d !== l.a && a.classList.toggle("animate", l.a = d), l;
    }, {
      e: void 0,
      t: void 0,
      a: void 0
    }), a;
  })();
}
function Kt(t) {
  return (() => {
    var e = zn(), n = e.firstChild, i = n.firstChild, o = i.nextSibling;
    return _n(e, "animationend", t.onAnimationEnd), E(i, () => t.value), E(o, () => t.value), W((s) => he(e, t.classList, s)), e;
  })();
}
function Bn(t) {
  return (() => {
    var e = Hn(), n = e.firstChild;
    return E(n, () => t.value), W(() => Mt(e, "data-value", t.value)), e;
  })();
}
const fi = ae((t) => ({
  "&": {
    "--border-radius": t?.borderRadius ?? ".15em",
    "--font-size": t?.fontSize ?? "4.5em",
    "--font-family": t?.fontFamily ?? '"Helvetica Neue", Helvetica, sans-serif',
    "--width": t?.width ?? "1em",
    "--height": t?.height ?? "1.45em",
    "--animation-duration": t?.animationDuration ?? "250ms",
    "--animation-delay": t?.animationDelay ?? "var(--animation-duration)",
    fontFamily: "var(--font-family)",
    fontSize: "var(--font-size)",
    userSelect: "none",
    textAlign: "center",
    position: "relative",
    width: "100%",
    display: "inline-flex",
    boxSizing: "border-box",
    alignItems: "flex-end",
    gap: ".25rem"
  },
  ".flip-clock-label": {
    fontSize: "1rem",
    marginBottom: ".5rem"
  },
  ".flip-clock-meridium": {
    lineHeight: "1em",
    top: "50%",
    left: "100%",
    flex: "0",
    width: "auto",
    textTransform: "uppercase",
    fontWeight: "200",
    transform: "translate(.5em, -50%)"
  },
  ".flip-clock-divider": {
    position: "relative",
    display: "flex",
    alignItems: "center",
    justifyContent: "center",
    fontFamily: "serif",
    color: "#333",
    height: "var(--height)",
    ".flip-clock-divider-inner": {
      fontSize: "1.25em"
    },
    '&[data-value=" "]': {
      minWidth: "1rem"
    },
    ".dark &": {
      color: "#ccc"
    }
  },
  ".flip-clock-group": {
    display: "flex",
    flexDirection: "column",
    "+ .flip-clock-group": {
      marginLeft: "1rem"
    },
    ".flip-clock-group-items": {
      display: "flex",
      alignItems: "end",
      gap: ".25rem"
    }
  },
  ".flip-clock-card": {
    width: "var(--width)",
    height: "var(--height)",
    position: "relative",
    borderRadius: "var(--border-radius)",
    boxShadow: "0 1.5px 3px rgba(0, 0, 0, 0.24), 0 3px 8px rgba(0, 0, 0, 0.05)",
    fontWeight: "bold",
    color: "#ccc",
    flexShrink: 0,
    "&:not(.animate)": {
      ".active .flip-clock-card-item-inner": {
        zIndex: "4"
      },
      ".flip-clock-card-item-inner": {
        ".top, .bottom": {
          "&:after": {
            display: "none"
          }
        }
      }
    },
    ".flip-clock-card-item": {},
    ".flip-clock-card-item-inner": {
      position: "absolute",
      width: "100%",
      height: "100%",
      "&:first-child": {
        zIndex: "2"
      },
      ".top, .bottom": {
        width: "100%",
        height: "50%",
        overflow: "hidden",
        position: "relative",
        fontSize: "1em",
        background: "#333",
        boxShadow: "inset 0 0 .2em rgba(0,0,0,.5)",
        "&:after": {
          content: '" "',
          display: "block",
          position: "absolute",
          top: "0",
          right: "0",
          bottom: "0",
          left: "0",
          overflow: "hidden"
        },
        "&:before": {
          content: '" "',
          display: "block",
          width: "100%",
          height: "1px",
          position: "absolute"
        }
      },
      ".top": {
        borderRadius: "var(--border-radius) var(--border-radius) 0 0",
        lineHeight: "var(--height)",
        "&:after": {
          borderRadius: "var(--border-radius) var(--border-radius) 0 0"
        },
        "&:before": {
          background: "#333",
          opacity: ".4",
          bottom: "0"
        }
      },
      ".bottom": {
        borderRadius: "0 0 var(--border-radius) var(--border-radius)",
        lineHeight: "0",
        "&:after": {
          borderRadius: "0 0 var(--border-radius) var(--border-radius)"
        },
        "&:before": {
          background: "#ccc",
          opacity: ".1"
        }
      }
    },
    "&.animate": {
      animationDuration: "var(--animation-duration)",
      animationDelay: "var(--animation-delay)",
      ".flip-clock-card-item-inner": {
        perspective: "15em"
      },
      ".top, .bottom, .active, .active > div, .before, .before > div": {
        animationDelay: "inherit",
        animationFillMode: "forwards",
        animationDuration: "inherit",
        animationTimingFunction: "inherit",
        "&:after": {
          animationDuration: "inherit",
          animationFillMode: "inherit"
        }
      },
      ".before": {
        animationDelay: "0s",
        animationTimingFunction: "ease-in",
        ".top": {
          animationName: "flip-clock-top"
        },
        ".top:after, .bottom:after": {
          animationName: "flip-clock-show-shadow"
        }
      },
      ".active": {
        animationTimingFunction: "ease-out",
        "& > div": {
          animationName: "flip-clock-indexing"
        },
        ".top:after, .bottom:after": {
          animationName: "flip-clock-hide-shadow"
        },
        ".bottom": {
          animationName: "flip-clock-bottom"
        }
      }
    },
    ".active": {
      zIndex: "2",
      ".bottom": {
        zIndex: "2",
        transformOrigin: "top center"
      }
    },
    ".before": {
      zIndex: "3",
      ".top": {
        zIndex: "2",
        transformOrigin: "bottom center",
        "&:after": {
          background: "linear-gradient(to bottom, rgba(0,0,0,.1) 0%, rgba(0,0,0,1) 100%)"
        }
      },
      ".bottom": {
        "&:after": {
          background: "linear-gradient(to bottom, rgba(0,0,0,1) 0%, rgba(0,0,0,.1) 100%)"
        }
      }
    }
  },
  "@keyframes flip-clock-indexing": {
    "0%": {
      zIndex: "2"
    },
    "1%": {
      zIndex: "3"
    },
    "100%": {
      zIndex: "4"
    }
  },
  "@keyframes flip-clock-bottom": {
    "0%": {
      transform: "rotateX(90deg)"
    },
    "100%": {
      transform: "rotateX(0)"
    }
  },
  "@keyframes flip-clock-top": {
    "0%": {
      transform: "rotateX(0)"
    },
    "100%": {
      transform: "rotateX(-90deg)"
    }
  },
  "@keyframes flip-clock-show-shadow": {
    "0%": {
      opacity: "0"
    },
    "100%": {
      opacity: "1"
    }
  },
  "@keyframes flip-clock-hide-shadow": {
    "0%": {
      opacity: "1"
    },
    "100%": {
      opacity: "0"
    }
  }
}));
export {
  kn as Alphanumeric,
  Cn as Clock,
  Fn as Counter,
  Ve as EMPTY_CHAR,
  En as ElapsedTime,
  Gt as EventEmitter,
  kt as FaceValue,
  On as FlipClock,
  Gn as StartRules,
  Nt as SyntaxError,
  xt as Timer,
  z as add,
  ri as alphanumeric,
  Ne as castDigitizedGroup,
  vt as castDigitizedString,
  Le as castDigitizedValues,
  pt as characterRange,
  si as clock,
  At as count,
  oi as counter,
  fi as css,
  Xe as dayAbbreviations,
  Ge as days,
  Zn as daysInWeek,
  He as defaultCharset,
  ai as elapsedTime,
  Un as eventEmitter,
  J as faceValue,
  ze as fisherYatesShuffle,
  ci as flipClock,
  Dn as getAnimationRate,
  Sn as getFilteredDuration,
  zt as getTwelveHourFormat,
  at as isDigitizedGroup,
  jt as matchArrayStructure,
  lt as mergeCss,
  ti as millisecondsInDay,
  ei as millisecondsInHour,
  ni as millisecondsInMinute,
  Ze as monthAbbreviations,
  Qe as months,
  F as pad,
  Te as parse,
  Mn as parseDuration,
  Ye as range,
  tn as sort,
  je as stop,
  Xn as stopAfterChanges,
  St as stopWhen,
  ii as sub,
  ui as theme,
  li as timer,
  Re as trackChanges,
  Pe as useCharset,
  ae as useCss,
  Yt as useDateFormats,
  le as useDefinitionMap,
  Qn as useDictionary,
  _e as useDigitizer,
  xn as useDurationFormats,
  $n as useSequencer
};
//# sourceMappingURL=FlipClock.es.js.map
