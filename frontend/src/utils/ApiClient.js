const API_BASE_URL = process.env.REACT_APP_API_URL || '';

class ApiClient {
  static getToken() {
    return sessionStorage.getItem('token');
  }

  static setToken(token) {
    sessionStorage.setItem('token', token);
  }

  static clearToken() {
    sessionStorage.removeItem('token');
    sessionStorage.removeItem('user');
  }

  static getUser() {
    const u = sessionStorage.getItem('user');
    return u ? JSON.parse(u) : null;
  }

  static setUser(user) {
    sessionStorage.setItem('user', JSON.stringify(user));
  }

  static async request(method, path, body = null) {
    const headers = { 'Content-Type': 'application/json' };
    const token = this.getToken();
    if (token) headers['Authorization'] = token;

    const opts = { method, headers };
    if (body) opts.body = JSON.stringify(body);

    const resp = await fetch(`${API_BASE_URL}${path}`, opts);
    const data = await resp.json().catch(() => ({}));

    if (resp.status === 401) {
      this.clearToken();
      window.location.href = '/';
      throw new Error('Unauthorized');
    }

    return { status: resp.status, data };
  }

  static get(path) { return this.request('GET', path); }
  static post(path, body) { return this.request('POST', path, body); }
  static put(path, body) { return this.request('PUT', path, body); }
  static del(path) { return this.request('DELETE', path); }
}

export default ApiClient;
