import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import Navbar from '../components/Navbar';
import ApiClient from '../utils/ApiClient';

function DashboardPage() {
  const navigate = useNavigate();
  const [folders, setFolders] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    loadFolders();
  }, []);

  const loadFolders = async () => {
    try {
      const { status, data } = await ApiClient.get('/folders');
      if (status === 200) setFolders(data.folders || []);
    } catch (e) { /* handled by ApiClient */ }
    setLoading(false);
  };

  return (
    <div>
      <Navbar />
      <div className="container py-4">
        <h4 className="page-header">
          <i className="bi bi-folder2-open me-2"></i>My Folders
        </h4>

        {loading ? (
          <div className="text-center py-5">
            <div className="spinner-border" style={{ color: 'var(--primary)' }}></div>
          </div>
        ) : folders.length === 0 ? (
          <div className="text-center py-5 text-muted">
            <i className="bi bi-folder-x" style={{ fontSize: '3rem' }}></i>
            <p className="mt-2">No folders available</p>
          </div>
        ) : (
          <div className="row g-3">
            {folders.map(f => (
              <div key={f.folder_name} className="col-md-4 col-lg-3">
                <div className="card folder-card p-3"
                  onClick={() => navigate(`/folders/${encodeURIComponent(f.folder_name)}`)}>
                  <div className="d-flex align-items-center">
                    <i className="bi bi-folder-fill me-3" style={{ fontSize: '1.5rem', color: 'var(--primary)' }}></i>
                    <div>
                      <div className="fw-semibold">{f.folder_name}</div>
                      <small className="text-muted">
                        {f.created_at ? new Date(f.created_at * 1000).toLocaleDateString() : ''}
                      </small>
                    </div>
                  </div>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}

export default DashboardPage;
