import { Outlet } from 'react-router-dom';
import { useAuth } from '../contexts/AuthContext';

export default function AdminRoute() {
  const { isAdmin } = useAuth();

  if (!isAdmin) {
    return (
      <div style={{ padding: 40, textAlign: 'center' }}>
        <h2>403 - 无权访问</h2>
        <p>需要管理员权限才能访问此页面</p>
      </div>
    );
  }
  return <Outlet />;
}
