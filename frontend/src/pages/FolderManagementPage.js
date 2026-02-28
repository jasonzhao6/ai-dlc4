import React, { useState, useEffect } from 'react';
import Navbar from '../components/Navbar';
import ApiClient from '../utils/ApiClient';

function FolderManagementPage() {
  const [folders, setFolders] = useState([]);
  const [loading, setLoading] = useState(true);
  const [newName, setNewName] = useState('');
  const [renaming, setRenaming] = useState(null);
  const [renameValue, setRenameValue] = useState('');
  const [error, setError] = useState('');

  useEffect(() => { loadFolders(); }, []);

  const loadFolders = async () => {
    try {
      const { status, data } = await ApiClient.get('/folders');
      if (status === 200) setFolders(data.folders || []);
    } catch (e) { /* handled */ }
    setLoading(false);
  };

  const handleCreate = async (e) => {
    e.preventDefault();
    setError('');
    if (!newName.trim()) return;
    const { status, data } = await ApiClient.post('/folders', { folder_name: newName.trim() });
    if (status !== 200) { setError(data.error || 'Create failed'); return; }
    setNewName('');
    loadFolders();
  };

  const handleRename = async (oldName) => {
    setError('');
    if (!renameValue.trim()) return;
    const { status, data } = await ApiClient.put(`/folders/${encodeURIComponent(oldName)}`, { new_name: renameValue.trim() });
    if (status !== 200) { setError(data.error || 'Rename failed'); return; }
    setRenaming(null);
    loadFolders();
  };

  const handleDelete = async (folderName) => {
    if (!window.confirm(`Delete folder "${folderName}" and all its files?`)) return;
    await ApiClient.del(`/folders/${encodeURIComponent(folderName)}`);
    loadFolders();
  };

  return (
    <div>
      <Navbar />
      <div className="container py-4">
        <h4 className="page-header"><i className="bi bi-gear me-2"></i>Folder Management</h4>

        {error && <div className="alert alert-danger py-2">{error}</div>}

        <form className="d-flex gap-2 mb-4" onSubmit={handleCreate}>
          <div className="input-group" style={{ maxWidth: '400px' }}>
            <span className="input-group-text"><i className="bi bi-folder-plus"></i></span>
            <input className="form-control" placeholder="New folder name" value={newName}
              onChange={e => setNewName(e.target.value)} />
          </div>
          <button type="submit" className="btn btn-primary btn-sm">Create</button>
        </form>

        {loading ? (
          <div className="text-center py-5"><div className="spinner-border" style={{ color: 'var(--primary)' }}></div></div>
        ) : folders.length === 0 ? (
          <div className="text-center py-5 text-muted">
            <i className="bi bi-folder-x" style={{ fontSize: '3rem' }}></i>
            <p className="mt-2">No folders yet</p>
          </div>
        ) : (
          <div className="card">
            <table className="table table-hover mb-0">
              <thead>
                <tr>
                  <th>Folder Name</th>
                  <th>Created</th>
                  <th style={{ width: '200px' }}>Actions</th>
                </tr>
              </thead>
              <tbody>
                {folders.map(f => (
                  <tr key={f.folder_name}>
                    <td>
                      {renaming === f.folder_name ? (
                        <div className="d-flex gap-2">
                          <input className="form-control form-control-sm" value={renameValue}
                            onChange={e => setRenameValue(e.target.value)}
                            onKeyDown={e => e.key === 'Enter' && handleRename(f.folder_name)} autoFocus />
                          <button className="btn btn-sm btn-primary" onClick={() => handleRename(f.folder_name)}>
                            <i className="bi bi-check"></i>
                          </button>
                          <button className="btn btn-sm btn-outline-secondary" onClick={() => setRenaming(null)}>
                            <i className="bi bi-x"></i>
                          </button>
                        </div>
                      ) : (
                        <span className="fw-semibold"><i className="bi bi-folder-fill me-2" style={{ color: 'var(--primary)' }}></i>{f.folder_name}</span>
                      )}
                    </td>
                    <td className="text-muted">{f.created_at ? new Date(f.created_at * 1000).toLocaleDateString() : ''}</td>
                    <td>
                      {renaming !== f.folder_name && (
                        <>
                          <button className="btn btn-sm btn-outline-primary me-1"
                            onClick={() => { setRenaming(f.folder_name); setRenameValue(f.folder_name); }}>
                            <i className="bi bi-pencil"></i>
                          </button>
                          <button className="btn btn-sm btn-outline-danger" onClick={() => handleDelete(f.folder_name)}>
                            <i className="bi bi-trash"></i>
                          </button>
                        </>
                      )}
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

export default FolderManagementPage;
