import React from 'react';
import { Link, useNavigate } from 'react-router-dom';
import ApiClient from '../utils/ApiClient';

function Navbar() {
  const navigate = useNavigate();
  const user = ApiClient.getUser();

  const handleLogout = async () => {
    try {
      await ApiClient.post('/auth/logout');
    } catch (e) { /* ignore */ }
    ApiClient.clearToken();
    navigate('/');
  };

  return (
    <nav className="navbar navbar-expand-lg navbar-dark px-4">
      <Link className="navbar-brand fw-bold" to="/dashboard">
        <i className="bi bi-cloud-arrow-up me-2"></i>FileShare
      </Link>
      <div className="navbar-nav me-auto">
        <Link className="nav-link" to="/dashboard">
          <i className="bi bi-folder me-1"></i>Folders
        </Link>
        {user?.role === 'admin' && (
          <>
            <Link className="nav-link" to="/users">
              <i className="bi bi-people me-1"></i>Users
            </Link>
            <Link className="nav-link" to="/folders/manage">
              <i className="bi bi-gear me-1"></i>Manage Folders
            </Link>
          </>
        )}
      </div>
      <div className="navbar-nav">
        <span className="nav-link text-light opacity-75">
          <i className="bi bi-person-circle me-1"></i>
          {user?.username} <span className="badge bg-secondary ms-1">{user?.role}</span>
        </span>
        <button className="btn btn-outline-light btn-sm ms-2" onClick={handleLogout}>
          <i className="bi bi-box-arrow-right me-1"></i>Logout
        </button>
      </div>
    </nav>
  );
}

export default Navbar;
