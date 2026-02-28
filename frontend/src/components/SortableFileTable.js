import React, { useState, useMemo } from 'react';

function formatSize(bytes) {
  if (!bytes) return '—';
  const units = ['B', 'KB', 'MB', 'GB'];
  let i = 0;
  let size = Number(bytes);
  while (size >= 1024 && i < units.length - 1) { size /= 1024; i++; }
  return `${size.toFixed(i === 0 ? 0 : 1)} ${units[i]}`;
}

function formatDate(ts) {
  if (!ts) return '—';
  return new Date(Number(ts) * 1000).toLocaleString();
}

function SortableFileTable({ files, canDownload, onDownload }) {
  const [sortColumn, setSortColumn] = useState('file_name');
  const [sortDir, setSortDir] = useState('asc');

  const toggleSort = (col) => {
    if (sortColumn === col) {
      setSortDir(d => d === 'asc' ? 'desc' : 'asc');
    } else {
      setSortColumn(col);
      setSortDir('asc');
    }
  };

  const sorted = useMemo(() => {
    const arr = [...files];
    arr.sort((a, b) => {
      let va = a[sortColumn];
      let vb = b[sortColumn];
      if (sortColumn === 'size' || sortColumn === 'uploaded_at') {
        va = Number(va) || 0;
        vb = Number(vb) || 0;
      } else {
        va = (va || '').toLowerCase();
        vb = (vb || '').toLowerCase();
      }
      if (va < vb) return sortDir === 'asc' ? -1 : 1;
      if (va > vb) return sortDir === 'asc' ? 1 : -1;
      return 0;
    });
    return arr;
  }, [files, sortColumn, sortDir]);

  const sortIcon = (col) => {
    if (sortColumn !== col) return <i className="bi bi-chevron-expand ms-1 opacity-25"></i>;
    return sortDir === 'asc'
      ? <i className="bi bi-chevron-up ms-1"></i>
      : <i className="bi bi-chevron-down ms-1"></i>;
  };

  if (files.length === 0) {
    return (
      <div className="text-center py-5 text-muted">
        <i className="bi bi-file-earmark-x" style={{ fontSize: '3rem' }}></i>
        <p className="mt-2">No files in this folder</p>
      </div>
    );
  }

  return (
    <div className="card">
      <table className="table table-hover mb-0">
        <thead>
          <tr>
            <th className="sortable-header" onClick={() => toggleSort('file_name')}>
              Name {sortIcon('file_name')}
            </th>
            <th className="sortable-header" onClick={() => toggleSort('size')}>
              Size {sortIcon('size')}
            </th>
            <th className="sortable-header" onClick={() => toggleSort('uploaded_at')}>
              Uploaded {sortIcon('uploaded_at')}
            </th>
            <th>By</th>
            {canDownload && <th style={{ width: '80px' }}>Action</th>}
          </tr>
        </thead>
        <tbody>
          {sorted.map(f => (
            <tr key={f.file_name}>
              <td>
                <i className="bi bi-file-earmark me-2 text-muted"></i>
                {f.file_name}
              </td>
              <td className="text-muted">{formatSize(f.size)}</td>
              <td className="text-muted">{formatDate(f.uploaded_at)}</td>
              <td className="text-muted">{f.uploaded_by || '—'}</td>
              {canDownload && (
                <td>
                  <button className="btn btn-sm btn-outline-primary" onClick={() => onDownload(f.file_name)}>
                    <i className="bi bi-download"></i>
                  </button>
                </td>
              )}
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

export default SortableFileTable;
