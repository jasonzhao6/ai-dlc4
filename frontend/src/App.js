import React from 'react';
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import LoginPage from './pages/LoginPage';
import DashboardPage from './pages/DashboardPage';
import UserManagementPage from './pages/UserManagementPage';
import FolderManagementPage from './pages/FolderManagementPage';
import FolderDetailPage from './pages/FolderDetailPage';
import ApiClient from './utils/ApiClient';

function ProtectedRoute({ children, adminOnly = false }) {
  const token = ApiClient.getToken();
  const user = ApiClient.getUser();
  if (!token) return <Navigate to="/" />;
  if (adminOnly && user?.role !== 'admin') return <Navigate to="/dashboard" />;
  return children;
}

function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/" element={<LoginPage />} />
        <Route path="/dashboard" element={<ProtectedRoute><DashboardPage /></ProtectedRoute>} />
        <Route path="/users" element={<ProtectedRoute adminOnly><UserManagementPage /></ProtectedRoute>} />
        <Route path="/folders/manage" element={<ProtectedRoute adminOnly><FolderManagementPage /></ProtectedRoute>} />
        <Route path="/folders/:folderName" element={<ProtectedRoute><FolderDetailPage /></ProtectedRoute>} />
      </Routes>
    </BrowserRouter>
  );
}

export default App;
