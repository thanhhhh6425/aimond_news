/**
 * static/js/theme.js
 * Dual-Theme Switcher: Premier League (PL) ↔ Champions League (UCL)
 * - Đổi CSS variables (màu sắc)
 * - Đổi dữ liệu qua API không reload trang
 * - Persist lựa chọn trong localStorage
 */

const Theme = (() => {
  const STORAGE_KEY = 'aimond_league';
  const DEFAULT     = 'PL';

  let currentLeague = localStorage.getItem(STORAGE_KEY) || DEFAULT;
  let callbacks     = [];   // listeners đăng ký nhận thông báo khi đổi theme

  // ── INIT ──────────────────────────────────────────────────
  function init() {
    _applyTheme(currentLeague, false);
    _bindToggleButtons();
    _setActiveNav();
  }

  // ── PUBLIC API ────────────────────────────────────────────
  function getLeague()  { return currentLeague; }
  function isPL()       { return currentLeague === 'PL'; }
  function isUCL()      { return currentLeague === 'UCL'; }

  function switchTo(league) {
    if (!['PL', 'UCL'].includes(league) || league === currentLeague) return;
    currentLeague = league;
    localStorage.setItem(STORAGE_KEY, league);
    _applyTheme(league, true);
    callbacks.forEach(fn => fn(league));
  }

  function toggle() {
    switchTo(currentLeague === 'PL' ? 'UCL' : 'PL');
  }

  /** Đăng ký callback khi đổi theme */
  function onChange(fn) {
    callbacks.push(fn);
    return () => { callbacks = callbacks.filter(f => f !== fn); };  // unsubscribe
  }

  // ── PRIVATE ───────────────────────────────────────────────
  function _applyTheme(league, animate) {
    const root = document.documentElement;

    if (animate) {
      // Flash transition khi đổi theme
      document.body.style.transition = 'none';
      const overlay = document.createElement('div');
      overlay.style.cssText = `
        position:fixed;inset:0;z-index:9998;pointer-events:none;
        background:${league === 'PL' ? '#38003c' : '#0e1e5b'};
        opacity:0;transition:opacity 0.15s ease;
      `;
      document.body.appendChild(overlay);
      requestAnimationFrame(() => {
        overlay.style.opacity = '0.25';
        setTimeout(() => {
          overlay.style.opacity = '0';
          setTimeout(() => overlay.remove(), 200);
        }, 150);
      });
    }

    root.setAttribute('data-theme', league);
    _updateToggleButtons(league);
    _updateLeagueBadges(league);
    _updatePageTitle(league);
  }

  function _bindToggleButtons() {
    document.addEventListener('click', e => {
      const btn = e.target.closest('[data-league-toggle]');
      if (!btn) return;
      const target = btn.dataset.leagueToggle;
      if (target) switchTo(target);
      else toggle();
    });
  }

  function _updateToggleButtons(league) {
    document.querySelectorAll('.league-toggle-btn').forEach(btn => {
      const isActive = btn.dataset.leagueToggle === league;
      btn.classList.toggle('active', isActive);
      btn.setAttribute('aria-pressed', isActive);
    });
  }

  function _updateLeagueBadges(league) {
    // Cập nhật text hiển thị giải đấu trên toàn trang
    document.querySelectorAll('[data-league-label]').forEach(el => {
      el.textContent = league === 'PL' ? 'Premier League' : 'Champions League';
    });
    document.querySelectorAll('[data-league-short]').forEach(el => {
      el.textContent = league;
    });
    document.querySelectorAll('[data-league-season]').forEach(el => {
      el.textContent = '2025/26';
    });
  }

  function _updatePageTitle(league) {
    const base  = document.title.replace(/ — (PL|UCL)/, '');
    document.title = `${base} — ${league}`;
  }

  function _setActiveNav() {
    const path = window.location.pathname;
    document.querySelectorAll('.header-nav-list a').forEach(a => {
      const href = a.getAttribute('href');
      const isActive = href === path || (href !== '/' && path.startsWith(href));
      a.classList.toggle('active', isActive);
    });
  }

  return { init, getLeague, isPL, isUCL, switchTo, toggle, onChange };
})();

// ── Auto-init when DOM is ready ────────────────────────────
document.addEventListener('DOMContentLoaded', () => {
  Theme.init();
  document.documentElement.style.visibility = '';
});

// Expose globally
window.Theme = Theme;