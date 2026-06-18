import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import { AuthProvider } from './contexts/AuthContext';
import ProtectedRoute from './components/ProtectedRoute';
import AdminRoute from './components/AdminRoute';
import Layout from './components/Layout';
import NotFoundPage from './pages/NotFoundPage';

// Lazy-loaded pages (placeholder — filled in T8-T11)
import LoginPage from './pages/LoginPage';
import RegisterPage from './pages/RegisterPage';
import PasswordResetPage from './pages/PasswordResetPage';
import UserListPage from './pages/UserListPage';
import UserFormPage from './pages/UserFormPage';
import ContractListPage from './pages/ContractListPage';
import ContractDetailPage from './pages/ContractDetailPage';
import ContractFormPage from './pages/ContractFormPage';
import AuditLogPage from './pages/AuditLogPage';

function App() {
  return (
    <BrowserRouter basename="/projects/contract-mgmt-eval">
      <AuthProvider>
        <Routes>
          {/* Public routes */}
          <Route path="/login" element={<LoginPage />} />
          <Route path="/register" element={<RegisterPage />} />
          <Route path="/reset-password" element={<PasswordResetPage />} />

          {/* Protected routes */}
          <Route element={<ProtectedRoute />}>
            <Route element={<Layout />}>
              <Route path="/" element={<Navigate to="/contracts" replace />} />

              {/* Admin routes */}
              <Route element={<AdminRoute />}>
                <Route path="/users" element={<UserListPage />} />
                <Route path="/users/new" element={<UserFormPage />} />
                <Route path="/users/:id/edit" element={<UserFormPage />} />
                <Route path="/audit-logs" element={<AuditLogPage />} />
              </Route>

              {/* Contract routes */}
              <Route path="/contracts" element={<ContractListPage />} />
              <Route path="/contracts/new" element={<ContractFormPage />} />
              <Route path="/contracts/:id" element={<ContractDetailPage />} />
              <Route path="/contracts/:id/edit" element={<ContractFormPage />} />
            </Route>
          </Route>

          {/* 404 */}
          <Route path="*" element={<NotFoundPage />} />
        </Routes>
      </AuthProvider>
    </BrowserRouter>
  );
}

export default App;
