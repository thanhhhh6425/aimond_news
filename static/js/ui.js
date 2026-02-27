/**
 * static/js/ui.js
 * Shared UI utilities: Toast, Skeleton, Search Overlay, Formatters
 */

const UI = (() => {

  // ── TOAST ───────────────────────────────────────────────
  let _toastContainer = null;

  function _ensureToastContainer() {
    if (!_toastContainer) {
      _toastContainer = document.createElement('div');
      _toastContainer.className = 'toast-container';
      document.body.appendChild(_toastContainer);
    }
    return _toastContainer;
  }

  function toast(message, type = 'info', duration = 3500) {
    const container = _ensureToastContainer();
    const el = document.createElement('div');
    const icons = { success: '✓', error: '✕', info: 'ℹ' };
    el.className = `toast toast-${type}`;
    el.innerHTML = `<span>${icons[type] || '•'}</span><span>${message}</span>`;
    container.appendChild(el);
    setTimeout(() => {
      el.style.transition = 'opacity 0.3s, transform 0.3s';
      el.style.opacity = '0';
      el.style.transform = 'translateX(20px)';
      setTimeout(() => el.remove(), 300);
    }, duration);
  }

  // ── SKELETON ────────────────────────────────────────────
  function skeleton(lines = 3, height = '18px') {
    return Array(lines).fill(0).map((_, i) => `
      <div class="skeleton" style="height:${height};width:${i === lines - 1 ? '70%' : '100%'};margin-bottom:10px;"></div>
    `).join('');
  }

  function skeletonCard() {
    return `
      <div class="card" style="padding:16px">
        <div class="skeleton" style="height:140px;margin-bottom:12px;"></div>
        ${skeleton(2, '16px')}
      </div>`;
  }

  // ── SEARCH OVERLAY ──────────────────────────────────────
  let _searchOverlay = null;
  let _searchDebounce = null;

  function initSearch() {
    _searchOverlay = document.getElementById('search-overlay');
    if (!_searchOverlay) return;

    const input   = _searchOverlay.querySelector('.search-overlay-input');
    const results = _searchOverlay.querySelector('.search-results');
    const closeBtn = _searchOverlay.querySelector('.search-overlay-close');

    // Open
    document.querySelectorAll('[data-search-open]').forEach(btn => {
      btn.addEventListener('click', () => openSearch());
    });

    // Close
    closeBtn?.addEventListener('click', closeSearch);
    _searchOverlay.addEventListener('click', e => {
      if (e.target === _searchOverlay) closeSearch();
    });
    document.addEventListener('keydown', e => {
      if (e.key === 'Escape') closeSearch();
      if ((e.ctrlKey || e.metaKey) && e.key === 'k') { e.preventDefault(); openSearch(); }
    });

    // Search input
    input?.addEventListener('input', () => {
      clearTimeout(_searchDebounce);
      const q = input.value.trim();
      if (q.length < 2) { results.innerHTML = ''; return; }
      results.innerHTML = `<div style="padding:12px;color:var(--color-text-muted);font-size:.85rem">Đang tìm...</div>`;
      _searchDebounce = setTimeout(() => _doSearch(q, results), 350);
    });
  }

  function openSearch() {
    if (!_searchOverlay) return;
    _searchOverlay.classList.add('open');
    setTimeout(() => _searchOverlay.querySelector('input')?.focus(), 50);
  }

  function closeSearch() {
    if (!_searchOverlay) return;
    _searchOverlay.classList.remove('open');
    const input = _searchOverlay.querySelector('input');
    if (input) input.value = '';
    const results = _searchOverlay.querySelector('.search-results');
    if (results) results.innerHTML = '';
  }

  async function _doSearch(q, container) {
    const result = await API.search(q);
    const all = [
      ...result.news.map(n    => ({ type:'Tin tức', text: n.title, url:`/news/${n.id}` })),
      ...result.players.map(p => ({ type:'Cầu thủ', text: `${p.name} — ${p.club_name||''}`, url:`/players/${p.id}` })),
      ...result.clubs.map(c   => ({ type:'CLB', text: c.name, url:`/clubs/${c.id}` })),
    ];

    if (!all.length) {
      container.innerHTML = `<div style="padding:12px;color:var(--color-text-muted);font-size:.85rem">Không tìm thấy kết quả nào cho "<strong>${escapeHtml(q)}</strong>"</div>`;
      return;
    }

    container.innerHTML = all.slice(0, 8).map(r => `
      <a href="${r.url}" class="search-result-item" onclick="UI.closeSearch()">
        <span class="search-result-type">${r.type}</span>
        <span style="font-size:.9rem">${escapeHtml(r.text)}</span>
      </a>
    `).join('');
  }

  // ── HAMBURGER MENU ──────────────────────────────────────
  function initHamburger() {
    const btn = document.querySelector('.header-hamburger');
    const nav = document.querySelector('.header-nav');
    if (!btn || !nav) return;
    btn.addEventListener('click', () => {
      nav.classList.toggle('open');
      btn.classList.toggle('open');
      document.body.style.overflow = nav.classList.contains('open') ? 'hidden' : '';
    });
  }

  // ── FORMATTERS ──────────────────────────────────────────
  function formatDate(isoStr, opts = {}) {
    if (!isoStr) return '';
    const d = new Date(isoStr);
    return d.toLocaleDateString('vi-VN', {
      day: '2-digit', month: '2-digit', year: 'numeric', ...opts
    });
  }

  function formatDateTime(isoStr) {
    if (!isoStr) return '';
    const d = new Date(isoStr);
    return d.toLocaleDateString('vi-VN', {
      day: '2-digit', month: '2-digit',
      hour: '2-digit', minute: '2-digit',
    });
  }

  function timeAgo(isoStr) {
    if (!isoStr) return '';
    const diff = (Date.now() - new Date(isoStr)) / 1000;
    if (diff < 60)     return 'Vừa xong';
    if (diff < 3600)   return `${Math.floor(diff/60)} phút trước`;
    if (diff < 86400)  return `${Math.floor(diff/3600)} giờ trước`;
    if (diff < 604800) return `${Math.floor(diff/86400)} ngày trước`;
    return formatDate(isoStr);
  }

  function escapeHtml(str) {
    return String(str)
      .replace(/&/g,'&amp;').replace(/</g,'&lt;')
      .replace(/>/g,'&gt;').replace(/"/g,'&quot;');
  }

  function formatScore(home, away) {
    if (home == null || away == null) return '— : —';
    return `${home} : ${away}`;
  }

  function positionLabel(pos) {
    const map = { GK:'Thủ môn', DEF:'Hậu vệ', MID:'Tiền vệ', FWD:'Tiền đạo' };
    return map[pos] || pos || '';
  }

  // ── RENDER HELPERS ───────────────────────────────────────
  function renderFormBadges(form = '') {
    return [...(form || '')].slice(-5).map(r =>
      `<span class="form-badge form-${r}">${r}</span>`
    ).join('');
  }

  function renderBadgeFallback(name, size = 32) {
    // Fallback badge khi không có ảnh
    const initials = (name || '?').slice(0, 2).toUpperCase();
    return `<div style="width:${size}px;height:${size}px;border-radius:50%;background:var(--color-surface-3);display:flex;align-items:center;justify-content:center;font-family:var(--font-display);font-weight:900;font-size:${size/3}px;color:var(--color-accent)">${initials}</div>`;
  }

  // ── INFINITE SCROLL ──────────────────────────────────────
  function onScrollBottom(callback, threshold = 200) {
    let called = false;
    window.addEventListener('scroll', () => {
      const nearBottom = document.documentElement.scrollHeight - window.scrollY - window.innerHeight < threshold;
      if (nearBottom && !called) {
        called = true;
        Promise.resolve(callback()).finally(() => { called = false; });
      }
    });
  }

  // ── INIT ────────────────────────────────────────────────
  function init() {
    initSearch();
    initHamburger();
  }

  return {
    init, toast, skeleton, skeletonCard,
    openSearch, closeSearch,
    formatDate, formatDateTime, timeAgo, escapeHtml, formatScore, positionLabel,
    renderFormBadges, renderBadgeFallback, onScrollBottom,
  };
})();

document.addEventListener('DOMContentLoaded', () => UI.init());
window.UI = UI;
