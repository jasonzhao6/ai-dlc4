import React, { useState, useEffect } from 'react';
import Navbar from '../components/Navbar';
import ApiClient from '../utils/ApiClient';

function UserManagementPage() {
  const [users, setUsers] = useState([]);
  const [folders, setFolders] = useState([]);
  const [loading, setLoading] = useState(true);
  const [showForm, setShowForm] = useState(false);
  const [editUser, setEditUser] = useState(null);
  const [form, setForm] = useState({ username: '', password: '', role: 'viewer', folder_names: [] });
  const [error, setError] = useState('');

  useEffect(() => { loadData(); }, []);

  const loadData = async () => {
    try {
      const [usersResp, foldersResp] = await Promise.all([
        ApiClient.get('/users'),
        ApiClient.get('/folders'),
      ]);
      if (usersResp.status === 200) setUsers(usersResp.data.users || []);
      if (foldersResp.status === 200) setFolders(foldersResp.data.folders || []);
    } catch (e) { /* handled */ }
    setLoading(false);
  };

  const resetForm = () => {
    setForm({ username: '', password: '', role: 'viewer', folder_names: [] });
    setEditUser(null);
    setShowForm(false);
    setError('');
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError('');
    try {
      if (editUser) {
        const { status, data } = await ApiClient.put(`/users/${editUser}`, {
          role: form.role,
          folder_names: form.folder_names,
        });
        if (status !== 200) { setError(data.error || 'Update failed'); return; }
      } else {
        const { status, data } = await ApiClient.post('/users', form);
        if (status !== 200) { setError(data.error || 'Create failed'); return; }
      }
      resetForm();
      loadData();
    } catch (err) { setError('Connection error'); }
  };

  const handleEdit = (u) => {
    setForm({ username: u.username, password: '', role: u.role, folder_names: u.folder_names || [] });
    setEditUser(u.username);
    setShowForm(true);
  };

  const handleDelete = async (username) => {
    if (!window.confirm(`Delete user "${username}"?`)) return;
    await ApiClient.del(`/users/${username}`);
    loadData();
  };

  const toggleFolder = (fn) => {
    setForm(prev => ({
      ...prev,
      folder_names: prev.folder_names.includes(fn)
        ? prev.folder_names.filter(f => f !== fn)
        : [...prev.folder_names, fn],
    }));
  };

  const roleBadge = (role) => {
    const colors = { admin: 'danger', uploader: 'primary', reader: 'info', viewer: 'secondary' };
    return <span className={`badge bg-${colors[role] || 'secondary'} badge-role`}>{role}</span>;
  };

  return (
    <div>
      <Navbar />
      <div className="container py-4">
        <div className="d-flex justify-content-between align-items-center page-header">
          <h4 className="mb-0"><i className="bi bi-people me-2"></i>User Management</h4>
          <button className="btn btn-primary btn-sm" onClick={() => { resetForm(); setShowForm(true); }}>
            <i className="bi bi-plus-lg me-1"></i>Add User
          </button>
        </div>

        {showForm && (
          <div className="card p-4 mb-4">
            <h6>{editUser ? `Edit ${editUser}` : 'New User'}</h6>
            {error && <div className="alert alert-danger py-2">{error}</div>}
            <form onSubmit={handleSubmit}>
              {!editUser && (
                <>
                  <div className="mb-3">
                    <label className="form-label small text-muted">Username</label>
                    <input className="form-control" value={form.username}
                      onChange={e => setForm({ ...form, username: e.target.value })} required />
                  </div>
                  <div className="mb-3">
                    <label className="form-label small text-muted">Password</label>
                    <input type="password" className="form-control" value={form.password}
                      onChange={e => setForm({ ...form, password: e.target.value })} required />
                  </div>
                </>
              )}
              <div className="mb-3">
                <label className="form-label small text-muted">Role</label>
                <select className="form-select" value={form.role}
                  onChange={e => setForm({ ...form, role: e.target.value })}>
                  <option value="admin">Admin</option>
                  <option value="uploader">Uploader</option>
                  <option value="reader">Reader</option>
                  <option value="viewer">Viewer</option>
                </select>
              </div>
              <div className="mb-3">
                <label className="form-label small text-muted">Folder Access</label>
                <div className="d-flex flex-wrap gap-2">
                  {folders.map(f => (
                    <button key={f.folder_name} type="button"
                      className={`btn btn-sm ${form.folder_names.includes(f.folder_name) ? 'btn-primary' : 'btn-outline-primary'}`}
                      onClick={() => toggleFolder(f.folder_name)}>
                      <i className="bi bi-folder me-1"></i>{f.folder_name}
                    </button>
                  ))}
                  {folders.length === 0 && <span className="text-muted small">No folders created yet</span>}
                </div>
              </div>
              <div className="d-flex gap-2">
                <button type="submit" className="btn btn-primary btn-sm">
                  {editUser ? 'Update' : 'Create'}
                </button>
                <button type="button" className="btn btn-outline-secondary btn-sm" onClick={resetForm}>Cancel</button>
              </div>
            </form>
          </div>
        )}

        {loading ? (
          <div className="text-center py-5"><div className="spinner-border" style={{ color: 'var(--primary)' }}></div></div>
        ) : (
          <div className="card">
            <table className="table table-hover mb-0">
              <thead>
                <tr>
                  <th>Username</th>
                  <th>Role</th>
                  <th>Folders</th>
                  <th style={{ width: '120px' }}>Actions</th>
                </tr>
              </thead>
              <tbody>
                {users.map(u => (
                  <tr key={u.username}>
                    <td className="fw-semibold">{u.username}</td>
                    <td>{roleBadge(u.role)}</td>
                    <td>
                      {(u.folder_names || []).map(fn => (
                        <span key={fn} className="badge bg-light text-dark me-1 border">{fn}</span>
                      ))}
                    </td>
                    <td>
                      <button className="btn btn-sm btn-outline-primary me-1" onClick={() => handleEdit(u)}>
                        <i className="bi bi-pencil"></i>
                      </button>
                      <button className="btn btn-sm btn-outline-danger" onClick={() => handleDelete(u.username)}>
                        <i className="bi bi-trash"></i>
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </div>
  );
}

export default UserManagementPage;
