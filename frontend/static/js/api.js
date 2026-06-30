const API_BASE = '/api/v1';

const Api = {
  getToken() {
    return localStorage.getItem('mycar_token');
  },

  setTokens(access, refresh) {
    localStorage.setItem('mycar_token', access);
    localStorage.setItem('mycar_refresh', refresh);
  },

  getUser() {
    const t = this.getToken();
    if (!t) return null;
    try {
      return JSON.parse(atob(t.split('.')[1]));
    } catch {
      return null;
    }
  },

  logout() {
    localStorage.removeItem('mycar_token');
    localStorage.removeItem('mycar_refresh');
    window.location.href = '/';
  },

  requireAuth() {
    if (!this.getToken()) {
      window.location.href = '/';
    }
  },

  async fetch(path, opts = {}) {
    const token = this.getToken();
    try {
      const res = await fetch(`${API_BASE}${path}`, {
        ...opts,
        headers: {
          'Content-Type': 'application/json',
          ...(token ? { Authorization: `Bearer ${token}` } : {}),
          ...opts.headers,
        },
      });
      if (res.status === 401) {
        this.logout();
        return null;
      }
      return res;
    } catch (err) {
      console.error('API error:', err);
      return null;
    }
  },

  async get(path) {
    const res = await this.fetch(path);
    if (!res) return null;
    return res.json();
  },

  async post(path, data) {
    const res = await this.fetch(path, {
      method: 'POST',
      body: JSON.stringify(data),
    });
    if (!res) return null;
    return { ok: res.ok, status: res.status, data: await res.json() };
  },

  async put(path, data) {
    const res = await this.fetch(path, {
      method: 'PUT',
      body: JSON.stringify(data),
    });
    if (!res) return null;
    return { ok: res.ok, status: res.status, data: await res.json() };
  },

  async delete(path) {
    const res = await this.fetch(path, { method: 'DELETE' });
    return res?.ok ?? false;
  },
};

// Helpers UI
function statutBadge(statut) {
  const map = {
    VERT:   '<span class="badge badge-vert"><i class="bi bi-check-circle-fill me-1"></i>VERT</span>',
    ORANGE: '<span class="badge badge-orange"><i class="bi bi-exclamation-circle-fill me-1"></i>ORANGE</span>',
    ROUGE:  '<span class="badge badge-rouge"><i class="bi bi-x-circle-fill me-1"></i>ROUGE</span>',
  };
  return map[statut] ?? `<span class="badge bg-secondary">${statut}</span>`;
}

function formatDate(d) {
  if (!d) return '—';
  return new Date(d).toLocaleDateString('fr-FR');
}

function showToast(msg, type = 'success') {
  const container = document.getElementById('toast-container') || (() => {
    const c = document.createElement('div');
    c.id = 'toast-container';
    c.style.cssText = 'position:fixed;top:1rem;right:1rem;z-index:9999;';
    document.body.appendChild(c);
    return c;
  })();
  const el = document.createElement('div');
  el.className = `toast align-items-center text-white bg-${type === 'success' ? 'success' : 'danger'} border-0 show`;
  el.innerHTML = `<div class="d-flex"><div class="toast-body">${msg}</div>
    <button type="button" class="btn-close btn-close-white me-2 m-auto" onclick="this.closest('.toast').remove()"></button></div>`;
  container.appendChild(el);
  setTimeout(() => el.remove(), 3500);
}
