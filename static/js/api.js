/**
 * static/js/api.js
 * API client - gọi Flask backend từ frontend
 * Tự động gắn league + season từ Theme.getLeague()
 */

const API = (() => {
  const BASE = '/api';

  // ── Core fetch wrapper ────────────────────────────────────
  async function request(path, opts = {}) {
    try {
      const res = await fetch(BASE + path, {
        headers: { 'Content-Type': 'application/json', ...opts.headers },
        ...opts,
      });
      const data = await res.json();
      if (!res.ok) throw new Error(data.error || `HTTP ${res.status}`);
      return { ok: true, data };
    } catch (err) {
      console.error(`[API] ${path}:`, err.message);
      return { ok: false, error: err.message };
    }
  }

  function _league() {
    return window.Theme?.getLeague() || 'PL';
  }

  function _qs(params = {}) {
    const all = { league: _league(), season: '2025', ...params };
    return '?' + new URLSearchParams(
      Object.fromEntries(Object.entries(all).filter(([, v]) => v != null))
    ).toString();
  }

  // ── NEWS ─────────────────────────────────────────────────
  const news = {
    list:    (p={}) => request(`/news/${_qs(p)}`),
    detail:  (id)   => request(`/news/${id}`),
    latest:  (p={}) => request(`/news/latest${_qs(p)}`),
    search:  (q, p={}) => request(`/news/search${_qs({q,...p})}`),
  };

  // ── MATCHES ──────────────────────────────────────────────
  const matches = {
    list:     (p={}) => request(`/matches/${_qs(p)}`),
    live:     (p={}) => request(`/matches/live${_qs(p)}`),
    upcoming: (p={}) => request(`/matches/upcoming${_qs(p)}`),
    results:  (p={}) => request(`/matches/results${_qs(p)}`),
    detail:   (id)   => request(`/matches/${id}`),
  };

  // ── STANDINGS ────────────────────────────────────────────
  const standings = {
    list:   (p={}) => request(`/standings/${_qs(p)}`),
    groups: (p={}) => request(`/standings/groups${_qs(p)}`),
  };

  // ── PLAYERS ──────────────────────────────────────────────
  const players = {
    list:   (p={}) => request(`/players/${_qs(p)}`),
    detail: (id)   => request(`/players/${id}`),
    top:    (p={}) => request(`/players/top${_qs(p)}`),
    search: (q,p={}) => request(`/players/search${_qs({q,...p})}`),
  };

  // ── CLUBS ────────────────────────────────────────────────
  const clubs = {
    list:   (p={}) => request(`/clubs/${_qs(p)}`),
    detail: (id,p={}) => request(`/clubs/${id}${_qs(p)}`),
    search: (q,p={}) => request(`/clubs/search${_qs({q,...p})}`),
  };

  // ── STATISTICS ───────────────────────────────────────────
  const stats = {
    players: (p={}) => request(`/statistics/players${_qs(p)}`),
    teams:   (p={}) => request(`/statistics/teams${_qs(p)}`),
  };

  // ── AUTH ─────────────────────────────────────────────────
  const auth = {
    login:    (body) => request('/auth/login',    { method:'POST', body: JSON.stringify(body) }),
    register: (body) => request('/auth/register', { method:'POST', body: JSON.stringify(body) }),
    logout:   ()     => request('/auth/logout',   { method:'POST' }),
    me:       ()     => request('/auth/me'),
    update:   (body) => request('/auth/me',       { method:'PATCH', body: JSON.stringify(body) }),
  };

  // ── CHATBOT ──────────────────────────────────────────────
  const chatbot = {
    message: (msg) => request('/chatbot/message', {
      method: 'POST',
      body: JSON.stringify({ message: msg, league: _league() }),
    }),
  };

  // ── SEARCH (unified) ─────────────────────────────────────
  async function search(q) {
    if (!q || q.length < 2) return { news: [], players: [], clubs: [] };
    const league = _league();
    const [n, p, c] = await Promise.all([
      news.search(q, { league }),
      players.search(q, { league }),
      clubs.search(q, { league }),
    ]);
    return {
      news:    n.ok ? n.data.items || [] : [],
      players: p.ok ? p.data.items || [] : [],
      clubs:   c.ok ? c.data.items || [] : [],
    };
  }

  return { news, matches, standings, players, clubs, stats, auth, chatbot, search };
})();

window.API = API;