(() => {
  const SECTIONS = ["", "Basics", "Need", "Prior work", "Models", "Data", "Results", "Close"];
  const SECTION_FULL = ["", "SAR and PolSAR fundamentals", "Why calibration is required", "Previous work and objectives", "Calibration models: Ainsworth and Quegan", "Study area", "Results", "Limitations and future scope"];
  const stage = document.getElementById('stage');
  const slides = [...document.querySelectorAll('.slide')];
  const N = slides.length;
  const standalone = document.body.hasAttribute('data-slide-index');
  const slideIndex = Number(document.body.dataset.slideIndex || 0);
  const deckEntries = window.THESIS_SLIDES || [];
  function visitSlide(index, atEnd = false) {
    if (index < 0 || index >= deckEntries.length) return;
    if (window.parent !== window && new URLSearchParams(location.search).has('embedded')) {
      window.parent.postMessage({ type: 'thesis:goto', index, atEnd }, '*');
      return;
    }
    location.href = deckEntries[index].file + (atEnd ? '#end' : '');
  }
  function slideCount(i) {
    return String((standalone ? slideIndex : i) + 1).padStart(2, '0') + ' / ' + (standalone ? deckEntries.length : N);
  }
  addEventListener('message', event => {
    if (event.source !== window.parent) return;
    if (event.data?.type === 'thesis:resize') { scheduleFit(); return; }
    if (event.data?.type !== 'thesis:key') return;
    handleKey({ key: event.data.key, code: event.data.code, preventDefault() {} });
  });
  const STATIC = /static/.test(location.search);
  if (STATIC) document.documentElement.classList.add('static');

  /* merge duplicate style attrs is impossible in HTML (only first kept) so read data-d too */
  /* ---- build charts ---- */
  function el(tag, css, parent, cls) { const e = document.createElement(tag); if (css) e.style.cssText = css; if (cls) e.className = cls; parent && parent.appendChild(e); return e; }

  // RCS chart (stage 1)
  (function () {
    const host = document.getElementById('rcsChart');
    if (!host) return;
    const data = [["13",49.88,21.14],["14",50.93,25.95],["15",51.00,24.41],["16",50.93,26.06],["17",49.22,23.55],["18",48.42,24.50],["19",47.62,23.14],["20",47.59,25.84],["21",47.29,24.23],["22",45.99,25.08]];
    const max = 55, H = 430;
    [0,10,20,30,40,50].forEach(v => { const y = H - v / max * H; el('div', `position:absolute;left:40px;right:0;top:${y}px;height:1px;background:var(--line)`, host); const t = el('div', `position:absolute;left:0;top:${y-9}px;font:500 13px var(--sans);color:var(--mute)`, host); t.textContent = v; });
    const W = 1;
    data.forEach((d, i) => {
      const g = el('div', `position:absolute;left:calc(52px + ${i} * (100% - 52px) / 10);width:calc((100% - 52px) / 10);top:0;height:${H}px`, host);
      const mk = (val, css, off, step, dl) => { const wrap = el('div', `position:absolute;bottom:0;left:${off}%;width:26%;height:${val / max * 100}%`, g); if (step) { wrap.dataset.a = 'fade'; wrap.dataset.step = step; } const b = el('div', `position:absolute;inset:0;border-radius:6px 6px 0 0;${css};--d:${dl}ms`, wrap, 'gy'); return wrap; };
      mk(d[2], 'background:#BDBDBD', 10, 1, i * 60);
      const t = mk(d[1], '', 38, 1, i * 60 + 100); t.firstChild.classList.add('hatch'); t.firstChild.style.borderRadius = '6px 6px 0 0';
      mk(d[1], 'background:#000', 66, 2, i * 70);
      const lab = el('div', `position:absolute;top:${H + 10}px;left:0;right:0;text-align:center;font:600 13px var(--sans)`, g); lab.textContent = 'CR' + d[0];
    });
  })();

  // cross-talk dumbbells
  (function () {
    const host = document.getElementById('xtChart');
    if (!host) return;
    const lo = -75, hi = -15, pct = v => (v - lo) / (hi - lo) * 100;
    const rows = [["|u|",[-43.5,-34.2],[-61.3,-36.5],[-38.2,-28.2],[-51.3,-32.1]],["|v|",[-37.0,-29.7],[-69.3,-44.3],[-29.3,-20.9],[-60.7,-36.0]],["|w|",[-37.0,-29.7],[-69.3,-44.3],[-47.2,-30.8],[-60.7,-36.0]],["|z|",[-43.4,-34.2],[-61.3,-36.5],[-49.7,-28.9],[-51.3,-32.1]]];
    const plotL = 150, top = 0;
    const plot = el('div', `position:absolute;left:${plotL}px;right:0;top:0;bottom:30px`, host);
    for (let v = -70; v <= -20; v += 10) { el('div', `position:absolute;left:${pct(v)}%;top:0;bottom:0;width:1px;background:var(--line)`, plot); const t = el('div', `position:absolute;left:${pct(v)}%;bottom:-28px;transform:translateX(-50%);font:500 13px var(--sans);color:var(--mute)`, plot); t.textContent = v; }
    const blocks = [["Ainsworth", 1, 2, 0], ["Quegan", 3, 4, 1]];
    let y = 0;
    blocks.forEach(([name, bi, ai, step]) => {
      const head = el('div', `position:absolute;left:0;top:${y}px;font:600 14px var(--sans);text-transform:uppercase;letter-spacing:.06em`, host); head.textContent = name;
      if (step) { head.dataset.a = 'fade'; head.dataset.step = step; }
      y += 26;
      rows.forEach((r, k) => {
        const lab = el('div', `position:absolute;left:0;top:${y + 8}px;font:500 italic 22px var(--serif)`, host); lab.textContent = r[0];
        const line = el('div', `position:absolute;left:${plotL}px;right:0;top:${y}px;height:46px`, host);
        if (step) { line.dataset.a = 'fade'; line.dataset.step = step; lab.dataset.a = 'fade'; lab.dataset.step = step; } else { line.dataset.a = 'fade'; line.style.setProperty('--d', (300 + k * 80) + 'ms'); }
        const b = r[bi], a = r[ai];
        el('div', `position:absolute;left:${pct(b[0])}%;width:${pct(b[1]) - pct(b[0])}%;top:6px;height:12px;border-radius:9px;background:#C4C4C4;--d:${k * 90}ms`, line, 'gx');
        el('div', `position:absolute;left:${pct(a[0])}%;width:${pct(a[1]) - pct(a[0])}%;top:24px;height:12px;border-radius:9px;background:#000;--d:${k * 90 + 250}ms`, line, 'gx');
        y += 50;
      });
      y += 22;
    });
  })();

  // alpha range chart
  (function () {
    const host = document.getElementById('alphaChart');
    if (!host) return;
    const lo = -10, hi = 20, pct = v => (v - lo) / (hi - lo) * 100;
    const plot = el('div', `position:absolute;left:170px;right:20px;top:0;bottom:30px`, host);
    for (let v = -10; v <= 20; v += 5) { el('div', `position:absolute;left:${pct(v)}%;top:0;bottom:0;width:${v === 0 ? 2 : 1}px;background:${v === 0 ? 'var(--fg)' : 'var(--line)'}`, plot); const t = el('div', `position:absolute;left:${pct(v)}%;bottom:-28px;transform:translateX(-50%);font:500 13px var(--sans);color:var(--mute)`, plot); t.textContent = (v > 0 ? '+' : '') + v + ' dB'; }
    const z = el('div', `position:absolute;left:${pct(0)}%;top:-6px;transform:translateX(8px);font:600 12px var(--sans);color:var(--mute)`, plot); z.textContent = 'α = 1 (ideal)';
    const rows = [["Ainsworth", -6.25, 1.25, "−6.25 to +1.25 dB", "background:#000", 0], ["Quegan", -5.35, 18.55, "−5.35 to +18.55 dB", "", 1]];
    rows.forEach(([n, a, b, txt, css, step], i) => {
      const y = 30 + i * 80;
      const lab = el('div', `position:absolute;left:0;top:${y + 4}px;font:600 22px var(--sans)`, host); lab.textContent = n;
      const wrap = el('div', `position:absolute;left:170px;right:20px;top:${y}px;height:40px`, host);
      wrap.dataset.a = 'fade'; if (step) { wrap.dataset.step = step; lab.dataset.a = 'fade'; lab.dataset.step = step; } else wrap.style.setProperty('--d', '400ms');
      const bar = el('div', `position:absolute;left:${pct(a)}%;width:${pct(b) - pct(a)}%;top:0;height:40px;border-radius:12px;${css}`, wrap, 'gx' + (step ? ' hatch' : ''));
      const t = el('div', `position:absolute;left:calc(${pct(b)}% + 14px);top:6px;font:600 20px var(--sans);white-space:nowrap`, wrap); t.textContent = txt;
      if (step) { t.style.left = 'auto'; t.style.right = `calc(${100 - pct(a)}% + 14px)`; }
    });
  })();

  // CR amplitude chart
  (function () {
    const host = document.getElementById('crChart');
    if (!host) return;
    const data = [["23",67.72,67.80,13.01,"−80.8%"],["24",77.24,77.33,12.39,"−84.0%"],["25",82.18,82.26,13.14,"−84.0%"],["26",83.63,83.75,15.55,"−81.4%"],["27",83.49,83.56,54.08,"−35.2%"]];
    const max = 90, H = 420;
    [0,20,40,60,80].forEach(v => { const y = H - v / max * H; el('div', `position:absolute;left:36px;right:0;top:${y}px;height:1px;background:var(--line)`, host); const t = el('div', `position:absolute;left:0;top:${y-9}px;font:500 13px var(--sans);color:var(--mute)`, host); t.textContent = v; });
    data.forEach((d, i) => {
      const g = el('div', `position:absolute;left:calc(50px + ${i} * (100% - 50px) / 5);width:calc((100% - 50px) / 5);top:0;height:${H}px`, host);
      const mk = (val, css, off, step, dl, cls) => { const w = el('div', `position:absolute;bottom:0;left:${off}%;width:22%;height:${val / max * 100}%`, g); w.dataset.a = 'fade'; if (step) w.dataset.step = step; else w.style.setProperty('--d', '300ms'); el('div', `position:absolute;inset:0;border-radius:6px 6px 0 0;${css};--d:${dl}ms`, w, 'gy' + (cls ? ' ' + cls : '')); return w; };
      mk(d[1], 'background:#C4C4C4', 14, 0, i * 70);
      mk(d[2], 'background:#000', 39, 1, i * 70);
      const q = mk(d[3], '', 64, 2, i * 90, 'hatch');
      const t = el('div', `position:absolute;bottom:calc(100% + 8px);left:50%;transform:translateX(-50%);font:700 14px var(--sans);white-space:nowrap`, q); t.textContent = d[4];
      const lab = el('div', `position:absolute;top:${H + 12}px;left:0;right:0;text-align:center;font:600 14px var(--sans)`, g); lab.textContent = 'CR ' + d[0];
    });
  })();

  /* ---- title word split ---- */
  document.querySelectorAll('.title').forEach(t => {
    let i = 0;
    const walk = node => [...node.childNodes].forEach(n => {
      if (n.nodeType === 3) {
        const frag = document.createDocumentFragment();
        n.textContent.split(/(\s+)/).forEach(part => {
          if (!part) return;
          if (/^\s+$/.test(part)) { frag.appendChild(document.createTextNode(' ')); return; }
          const w = document.createElement('span'); w.className = 'w';
          const s = document.createElement('span'); s.textContent = part; s.style.setProperty('--i', i++);
          w.appendChild(s); frag.appendChild(w);
        });
        n.replaceWith(frag);
      } else if (n.nodeType === 1) {
        const w = document.createElement('span'); w.className = 'w';
        const s = document.createElement('span'); s.style.setProperty('--i', i++);
        n.replaceWith(w); s.appendChild(n); w.appendChild(s);
      }
    });
    walk(t);
  });

  /* ---- per-slide data ---- */
  const info = slides.map(s => {
    const items = [...s.querySelectorAll('[data-a]')];
    const max = items.reduce((m, e) => Math.max(m, +(e.dataset.step || 0)), 0);
    return { items, max };
  });

  /* ---- topbar tabs ---- */
  const tabs = document.getElementById('tabs');
  SECTIONS.forEach((n, i) => { if (!i) return; const t = el('span', '', tabs, 'tab'); t.textContent = n; t.dataset.i = i; });

  /* ---- counters ---- */
  function runCount(e, instant) {
    const target = parseFloat(e.dataset.count), dec = +(e.dataset.dec || 0), pre = e.dataset.prefix || '';
    const fmt = v => pre + (e.hasAttribute('data-sep') ? Math.round(v).toLocaleString('en-IN').replace(/,/g, ' ') : v.toFixed(dec));
    if (instant) { e.textContent = fmt(target); return; }
    const t0 = performance.now(), dur = 1400;
    const tick = now => { const p = Math.min(1, (now - t0) / dur), k = 1 - Math.pow(1 - p, 4); e.textContent = fmt(target * k); if (p < 1) requestAnimationFrame(tick); };
    e.textContent = fmt(0);
    setTimeout(() => requestAnimationFrame(tick), 250);
  }
  function reveal(e, instant) {
    e.classList.add('on');
    const cs = e.matches('[data-count]') ? [e] : [];
    e.querySelectorAll('[data-count]').forEach(c => { if (c.closest('[data-a]') === e) cs.push(c); });
    cs.forEach(c => runCount(c, instant));
  }

  /* ---- static (print) mode ---- */
  if (STATIC) {
    const tb = document.getElementById('topbar');
    slides.forEach((s, i) => {
      const c = tb.cloneNode(true); c.removeAttribute('id'); c.className = 'tb-clone';
      c.querySelector('.count').textContent = slideCount(i);
      c.querySelectorAll('.tab').forEach(t => t.classList.toggle('on', +t.dataset.i === +s.dataset.sec));
      if (s.classList.contains('dark')) { c.style.color = '#fff'; c.querySelectorAll('.tab.on').forEach(t => { t.style.background = '#fff'; t.style.color = '#000'; }); c.querySelector('.count').style.cssText = 'background:#1F1F1F;color:#fff'; c.querySelector('.brand b i').style.borderColor = '#000'; }
      s.appendChild(c);
      info[i].items.forEach(e => reveal(e, true));
    });
    return;
  }

  /* ---- scaling ---- */
  // Keep the authored 1600×900 canvas rigid; use one scale for both axes.
  function fit() {
    const viewport = document.documentElement;
    const width = viewport.clientWidth || innerWidth;
    const height = viewport.clientHeight || innerHeight;
    const scale = Math.min(width / 1600, height / 900);
    if (!(scale > 0)) return;
    stage.style.width = '1600px'; stage.style.height = '900px';
    stage.style.transform = `translate(-50%,-50%) scale(${scale})`;
  }
  let fitFrame = 0;
  function scheduleFit() {
    cancelAnimationFrame(fitFrame);
    fitFrame = requestAnimationFrame(fit);
  }
  addEventListener('resize', scheduleFit);
  document.addEventListener('fullscreenchange', scheduleFit);
  window.visualViewport?.addEventListener('resize', scheduleFit);
  new ResizeObserver(scheduleFit).observe(document.documentElement);
  fit();

  /* ---- navigation ---- */
  let cur = -1, step = 0, busy = false;
  const curtain = document.getElementById('curtain');

  function setStep(i, k, instant) {
    info[i].items.forEach(e => {
      const st = +(e.dataset.step || 0);
      if (st <= k) { if (!e.classList.contains('on')) reveal(e, instant); }
      else e.classList.remove('on');
    });
  }
  function chrome(i) {
    const s = slides[i];
    stage.classList.toggle('is-dark', s.classList.contains('dark'));
    document.body.classList.toggle('light', !s.classList.contains('dark'));
    document.querySelectorAll('.tab').forEach(t => t.classList.toggle('on', +t.dataset.i === +s.dataset.sec));
    document.getElementById('count').textContent = slideCount(i);
    document.getElementById('hint').style.opacity = i === 0 ? .55 : 0;
    if (!standalone) history.replaceState(null, '', '#' + (i + 1));
  }
  function show(i, dir, atEnd) {
    const prev = slides[cur], next = slides[i];
    if (prev) {
      prev.classList.remove('active'); prev.classList.add('out'); prev.classList.toggle('back', dir < 0);
      setTimeout(() => { prev.classList.remove('out', 'back'); info[slides.indexOf(prev)].items.forEach(e => e.classList.remove('on')); }, 800);
    }
    next.classList.add('instant'); next.classList.toggle('back', dir < 0);
    info[i].items.forEach(e => e.classList.remove('on'));
    void next.offsetWidth; next.classList.remove('instant');
    next.classList.add('active');
    cur = i; chrome(i);
    if (atEnd) { step = info[i].max; next.classList.add('instant'); setStep(i, step, true); void next.offsetWidth; next.classList.remove('instant'); }
    else { step = 0; setStep(i, 0); }
  }
  function go(i, dir = 1, atEnd = false) {
    if (busy) return;
    if (standalone && i !== cur) { visitSlide(slideIndex + i, atEnd); return; }
    if (i < 0 || i >= N || i === cur) return;
    const ns = +slides[i].dataset.sec, cs = cur >= 0 ? +slides[cur].dataset.sec : -1;
    if (dir > 0 && ns > 0 && ns !== cs && cur >= 0) {
      busy = true;
      curtain.querySelector('.cn').textContent = String(ns).padStart(2, '0');
      curtain.querySelector('.ct').textContent = SECTION_FULL[ns];
      curtain.querySelector('.cs').textContent = 'SECTION ' + ns + ' OF 7';
      curtain.className = ''; void curtain.offsetWidth; curtain.classList.add('cover');
      setTimeout(() => {
        slides.forEach(s => s.classList.add('instant'));
        show(i, dir, atEnd);
        slides.forEach(s => s.classList.remove('instant'));
        slides[i].classList.add('instant'); setStep(i, -1, true); void slides[i].offsetWidth; slides[i].classList.remove('instant');
        // word titles need replay
        const t = slides[i].querySelectorAll('.title .w>span'); t.forEach(x => x.style.transform = 'translateY(108%)'); void slides[i].offsetWidth;
        curtain.classList.add('leave');
        setTimeout(() => { t.forEach(x => x.style.transform = ''); setStep(i, 0); }, 200);
        setTimeout(() => { curtain.className = ''; busy = false; }, 760);
      }, 1000);
      return;
    }
    show(i, dir, atEnd);
  }
  function next() {
    if (busy) return;
    if (step < info[cur].max) { step++; setStep(cur, step); }
    else go(cur + 1, 1);
  }
  function prev() {
    if (busy) return;
    if (step > 0) { step--; setStep(cur, step); }
    else go(cur - 1, -1, true);
  }

  function handleKey(e) {
    if (e.ctrlKey || e.metaKey || e.altKey || e.target?.closest?.('input, textarea, select, [contenteditable="true"]')) return;
    const key = ({KeyF:'f', KeyM:'m', KeyO:'o'})[e.code] || e.key;
    const lower = key.length === 1 ? key.toLowerCase() : key;
    if (lower === 'f') {
      e.preventDefault();
      if (window.parent !== window && new URLSearchParams(location.search).has('embedded')) {
        window.parent.postMessage({type:'thesis:fullscreen'}, '*');
      } else {
        const operation = document.fullscreenElement ? document.exitFullscreen() : document.documentElement.requestFullscreen();
        operation?.catch(error => console.warn('Fullscreen unavailable:', error.message));
      }
      return;
    }
    if (lower === 'm' || lower === 'o') { e.preventDefault(); toggleSheet(!sheet.classList.contains('open')); return; }
    if (key === 'Escape') { e.preventDefault(); toggleSheet(false); return; }
    if (sheet.classList.contains('open')) return;
    if (['ArrowRight', 'ArrowDown', ' ', 'PageDown', 'Enter'].includes(key)) { e.preventDefault(); next(); }
    else if (['ArrowLeft', 'ArrowUp', 'PageUp', 'Backspace'].includes(key)) { e.preventDefault(); prev(); }
    else if (key === 'Home') { e.preventDefault(); standalone ? visitSlide(0) : go(0, -1); }
    else if (key === 'End') { e.preventDefault(); standalone ? visitSlide(deckEntries.length - 1, true) : go(N - 1, -1, true); }
  }
  addEventListener('keydown', handleKey);
  stage.addEventListener('click', e => {
    if (e.target.closest('#sheet, button, input, select, textarea')) return;
    const destination = e.target.closest('[data-slide-target]');
    if (destination) {
      if (!e.ctrlKey && !e.metaKey && !e.shiftKey && !e.altKey) {
        e.preventDefault();
        visitSlide(Number(destination.dataset.slideTarget) - 1);
      }
      return;
    }
    // Ordinary page clicks do not reveal builds or navigate slides.
  });
  let tx = null;
  addEventListener('touchstart', e => tx = e.touches[0].clientX, { passive: true });
  addEventListener('touchend', e => { if (tx == null) return; const dx = e.changedTouches[0].clientX - tx; if (Math.abs(dx) > 50) dx < 0 ? next() : prev(); tx = null; });

  /* ---- menu sheet ---- */
  const sheet = document.getElementById('sheet'), items = document.getElementById('items');
  (standalone ? deckEntries : slides).forEach((s, i) => {
    const it = el('div', '', items, 'it');
    const number = document.createElement('b'); number.textContent = String(i + 1).padStart(2, '0');
    it.append(number, document.createTextNode(standalone ? s.name : s.dataset.name));
    it.onclick = ev => { ev.stopPropagation(); toggleSheet(false); if (standalone) visitSlide(i); else go(i, i > cur ? 1 : -1); };
  });
  function toggleSheet(open) { sheet.classList.toggle('open', open); [...items.children].forEach((c, i) => c.classList.toggle('cur', i === (standalone ? slideIndex : cur))); }
  sheet.addEventListener('click', e => { if (e.target === sheet) { e.stopPropagation(); toggleSheet(false); } });

  const start = Math.max(0, Math.min(N - 1, (parseInt(location.hash.slice(1)) || 1) - 1));
  show(start, 1, standalone && location.hash === '#end');
  if (window.parent !== window && new URLSearchParams(location.search).has('embedded')) {
    window.parent.postMessage({type:'thesis:ready'}, '*');
  }
})();
