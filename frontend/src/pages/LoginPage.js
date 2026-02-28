import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import ApiClient from '../utils/ApiClient';

function LoginPage() {
  const navigate = useNavigate();
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);

  // Password change state
  const [showChangePassword, setShowChangePassword] = useState(false);
  const [oldPassword, setOldPassword] = useState('');
  const [newPassword, setNewPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');

  const handleLogin = async (e) => {
    e.preventDefault();
    setError('');
    setLoading(true);
    try {
      const { status, data } = await ApiClient.post('/auth/login', { username, password });
      if (status !== 200) {
        setError(data.error || 'Login failed');
        return;
      }
      ApiClient.setToken(data.token);
      ApiClient.setUser({ username: data.username, role: data.role });

      if (data.force_password_change) {
        setOldPassword(password);
        setShowChangePassword(true);
      } else {
        navigate('/dashboard');
      }
    } catch (err) {
      setError('Connection error');
    } finally {
      setLoading(false);
    }
  };

  const handleChangePassword = async (e) => {
    e.preventDefault();
    setError('');
    if (newPassword !== confirmPassword) {
      setError('Passwords do not match');
      return;
    }
    if (newPassword.length < 6) {
      setError('Password must be at least 6 characters');
      return;
    }
    setLoading(true);
    try {
      const { status, data } = await ApiClient.post('/auth/change-password', {
        old_password: oldPassword,
        new_password: newPassword,
      });
      if (status !== 200) {
        setError(data.error || 'Password change failed');
        return;
      }
      navigate('/dashboard');
    } catch (err) {
      setError('Connection error');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="login-container">
      <div className="login-card">
        <div className="text-center mb-4">
          <i className="bi bi-cloud-arrow-up" style={{ fontSize: '3rem', color: 'var(--primary)' }}></i>
          <h2 className="mt-2 fw-bold">FileShare</h2>
          <p className="text-muted">
            {showChangePassword ? 'Please set a new password' : 'Sign in to your account'}
          </p>
        </div>

        {error && <div className="alert alert-danger py-2">{error}</div>}

        {!showChangePassword ? (
          <form onSubmit={handleLogin}>
            <div className="mb-3">
              <label className="form-label text-muted small">Username</label>
              <div className="input-group">
                <span className="input-group-text"><i className="bi bi-person"></i></span>
                <input type="text" className="form-control" value={username}
                  onChange={e => setUsername(e.target.value)} required autoFocus />
              </div>
            </div>
            <div className="mb-4">
              <label className="form-label text-muted small">Password</label>
              <div className="input-group">
                <span className="input-group-text"><i className="bi bi-lock"></i></span>
                <input type="password" className="form-control" value={password}
                  onChange={e => setPassword(e.target.value)} required />
              </div>
            </div>
            <button type="submit" className="btn btn-primary w-100 py-2" disabled={loading}>
              {loading ? <span className="spinner-border spinner-border-sm me-2"></span> : null}
              Sign In
            </button>
          </form>
        ) : (
          <form onSubmit={handleChangePassword}>
            <div className="mb-3">
              <label className="form-label text-muted small">New Password</label>
              <div className="input-group">
                <span className="input-group-text"><i className="bi bi-lock"></i></span>
                <input type="password" className="form-control" value={newPassword}
                  onChange={e => setNewPassword(e.target.value)} required autoFocus />
              </div>
            </div>
            <div className="mb-4">
              <label className="form-label text-muted small">Confirm New Password</label>
              <div className="input-group">
                <span className="input-group-text"><i className="bi bi-lock-fill"></i></span>
                <input type="password" className="form-control" value={confirmPassword}
                  onChange={e => setConfirmPassword(e.target.value)} required />
              </div>
            </div>
            <button type="submit" className="btn btn-primary w-100 py-2" disabled={loading}>
              {loading ? <span className="spinner-border spinner-border-sm me-2"></span> : null}
              Change Password
            </button>
          </form>
        )}
      </div>
    </div>
  );
}

export default LoginPage;
