import React, { useState, useEffect, useCallback } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import Navbar from '../components/Navbar';
import SearchBar from '../components/SearchBar';
import SortableFileTable from '../components/SortableFileTable';
import ApiClient from '../utils/ApiClient';

function FolderDetailPage() {
  const { folderName } = useParams();
  const navigate = useNavigate();
  const user = ApiClient.getUser();
  const [files, setFiles] = useState([]);
  const [searchTerm, setSearchTerm] = useState('');
  const [loading, setLoading] = useState(true);
  const [uploading, setUploading] = useState(false);
  const [error, setError] = useState('');

  const loadFiles = useCallback(async () => {
    try {
      const { status, data } = await ApiClient.get(`/folders/${encodeURIComponent(folderName)}/files`);
      if (status === 200) setFiles(data.files || []);
      else if (status === 403) { setError('Access denied'); }
    } catch (e) { /* handled */ }
    setLoading(false);
  }, [folderName]);

  useEffect(() => { loadFiles(); }, [loadFiles]);

  const canUpload = user?.role === 'admin' || user?.role === 'uploader';
  const canDownload = user?.role === 'admin' || user?.role === 'uploader' || user?.role === 'reader';

  const handleUpload = async (e) => {
    const file = e.target.files[0];
    if (!file) return;
    setError('');
    setUploading(true);

    try {
      // Request pre-signed URL
      const { status, data } = await ApiClient.post(
        `/folders/${encodeURIComponent(folderName)}/files/upload`,
        { file_name: file.name, file_size: file.size }
      );
      if (status !== 200) { setError(data.error || 'Upload request failed'); setUploading(false); return; }

      // Upload directly to S3
      const uploadResp = await fetch(data.upload_url, { method: 'PUT', body: file });
      if (!uploadResp.ok) { setError('S3 upload failed'); setUploading(false); return; }

      // Record metadata
      await ApiClient.post(
        `/folders/${encodeURIComponent(folderName)}/files/upload/complete`,
        { file_name: file.name, file_size: file.size }
      );

      loadFiles();
    } catch (err) {
      setError('Upload error');
    }
    setUploading(false);
    e.target.value = '';
  };

  const handleDownload = async (fileName) => {
    try {
      const { status, data } = await ApiClient.post(
        `/folders/${encodeURIComponent(folderName)}/files/${encodeURIComponent(fileName)}/download`
      );
      if (status === 200 && data.download_url) {
        window.open(data.download_url, '_blank');
      }
    } catch (e) { /* handled */ }
  };

  const filteredFiles = files.filter(f =>
    f.file_name.toLowerCase().includes(searchTerm.toLowerCase())
  );

  return (
    <div>
      <Navbar />
      <div className="container py-4">
        <div className="d-flex justify-content-between align-items-center page-header">
          <h4 className="mb-0">
            <button className="btn btn-sm btn-outline-secondary me-2" onClick={() => navigate('/dashboard')}>
              <i className="bi bi-arrow-left"></i>
            </button>
            <i className="bi bi-folder-fill me-2" style={{ color: 'var(--primary)' }}></i>
            {decodeURIComponent(folderName)}
          </h4>
          {canUpload && (
            <label className="btn btn-primary btn-sm mb-0" style={{ cursor: 'pointer' }}>
              {uploading ? (
                <><span className="spinner-border spinner-border-sm me-1"></span>Uploading...</>
              ) : (
                <><i className="bi bi-cloud-arrow-up me-1"></i>Upload File</>
              )}
              <input type="file" className="d-none" onChange={handleUpload} disabled={uploading} />
            </label>
          )}
        </div>

        {error && <div className="alert alert-danger py-2">{error}</div>}

        <SearchBar searchTerm={searchTerm} onSearchChange={setSearchTerm} />

        {loading ? (
          <div className="text-center py-5"><div className="spinner-border" style={{ color: 'var(--primary)' }}></div></div>
        ) : (
          <SortableFileTable
            files={filteredFiles}
            canDownload={canDownload}
            onDownload={handleDownload}
          />
        )}
      </div>
    </div>
  );
}

export default FolderDetailPage;
