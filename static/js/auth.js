/**
 * static/js/auth.js
 * Login / Register logic + User session management
 */

const Auth = (() => {
  let _user = null;

  async function init() {
    const res = await API.auth.me();
    if (res.ok && res.data.user) {
      _user = res.data.user;
      _renderLoggedIn(_user);
    } else {
      _renderLoggedOut();
    }
  }

  function getUser()        { return _user; }
  function isLoggedIn()     { return !!_user; }

  // ── Login ──────────────────────────────────────────────
  async function login(identifier, password, remember = true) {
    const res = await API.auth.login({ username: identifier, email: identifier, password, remember });
    if (res.ok) {
      _user = res.data.user;
      _renderLoggedIn(_user);
      UI.toast('Đăng nhập thành công!', 'success');
      return { ok: true };
    }
    UI.toast(res.error || 'Đăng nhập thất bại', 'error');
    return { ok: false, error: res.error };
  }

  // ── Register ───────────────────────────────────────────
  async function register(data) {
    const res = await API.auth.register(data);
    if (res.ok) {
      _user = res.data.user;
      _renderLoggedIn(_user);
      UI.toast('Đăng ký thành công!', 'success');
      return { ok: true };
    }
    UI.toast(res.error || 'Đăng ký thất bại', 'error');
    return { ok: false, error: res.error };
  }

  // ── Logout ─────────────────────────────────────────────
  async function logout() {
    await API.auth.logout();
    _user = null;
    _renderLoggedOut();
    UI.toast('Đã đăng xuất', 'info');
    window.location.href = '/';
  }

  // ── DOM updates ────────────────────────────────────────
  function _renderLoggedIn(user) {
    // Desktop and mobile auth containers
    document.querySelectorAll('.header-right .auth-logged-out').forEach(el => el.classList.add('hidden'));
    document.querySelectorAll('.header-right .auth-logged-in').forEach(el => el.classList.remove('hidden'));

    // Mobile auth containers (inside .auth-mobile)
    document.querySelectorAll('.auth-mobile .auth-logged-out').forEach(el => el.classList.add('hidden'));
    document.querySelectorAll('.auth-mobile .auth-logged-in').forEach(el => el.classList.remove('hidden'));

    // Update user info elements
    document.querySelectorAll('[data-user-name]').forEach(el => {
      el.textContent = user.full_name || user.username;
    });
    document.querySelectorAll('[data-user-avatar]').forEach(el => {
      if (user.avatar_url) {
        el.src = user.avatar_url;
        el.style.display = "";
        const span = el.parentElement?.querySelector('[data-user-name]');
        if (span) span.style.display = "none";
      } else {
        el.style.display = "none";
        const span = el.parentElement?.querySelector('[data-user-name]');
        if (span) span.style.display = "";
      }
    });
  }

  function _renderLoggedOut() {
    // Desktop
    document.querySelectorAll('.header-right .auth-logged-in').forEach(el => el.classList.add('hidden'));
    document.querySelectorAll('.header-right .auth-logged-out').forEach(el => el.classList.remove('hidden'));

    // Mobile
    document.querySelectorAll('.auth-mobile .auth-logged-in').forEach(el => el.classList.add('hidden'));
    document.querySelectorAll('.auth-mobile .auth-logged-out').forEach(el => el.classList.remove('hidden'));
  }

  // ── Form binding helpers ────────────────────────────────
  function bindLoginForm(formEl) {
    formEl.addEventListener('submit', async e => {
      e.preventDefault();
      const fd = new FormData(formEl);
      const btn = formEl.querySelector('[type=submit]');
      btn.disabled = true;
      btn.textContent = 'Đang đăng nhập...';
      const res = await login(fd.get('identifier'), fd.get('password'));
      if (res.ok) window.location.href = '/';
      else {
        btn.disabled = false;
        btn.textContent = 'Đăng nhập';
        const errEl = formEl.querySelector('.form-error');
        if (errEl) errEl.textContent = res.error;
      }
    });
  }

  function bindRegisterForm(formEl) {
    formEl.addEventListener('submit', async e => {
      e.preventDefault();
      const fd = new FormData(formEl);
      if (fd.get('password') !== fd.get('confirm_password')) {
        UI.toast('Mật khẩu xác nhận không khớp', 'error');
        return;
      }
      const btn = formEl.querySelector('[type=submit]');
      btn.disabled = true;
      btn.textContent = 'Đang tạo tài khoản...';
      const res = await register({
        username:         fd.get('username'),
        email:            fd.get('email'),
        password:         fd.get('password'),
        full_name:        fd.get('full_name'),
        preferred_league: fd.get('preferred_league') || 'PL',
      });
      if (res.ok) window.location.href = '/';
      else {
        btn.disabled = false;
        btn.textContent = 'Đăng ký';
        const errEl = formEl.querySelector('.form-error');
        if (errEl) errEl.textContent = res.error;
      }
    });
  }

  // Expose updateHeaderUI for external calls (e.g., after avatar update)
  function updateHeaderUI(user) {
    if (user) _renderLoggedIn(user);
  }

  return { init, getUser, isLoggedIn, login, register, logout, bindLoginForm, bindRegisterForm, updateHeaderUI };
})();

window.Auth = Auth;