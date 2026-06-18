import { Link, useNavigate } from 'react-router-dom';
import { useAuth } from '../contexts/AuthContext';

export default function Navbar() {
  const { user, isAdmin, logoutAction } = useAuth();
  const navigate = useNavigate();

  const handleLogout = async () => {
    await logoutAction();
    navigate('/login');
  };

  return (
    <nav className="navbar">
      <div className="navbar-brand">
        <Link to="/">📋 合同管理系统</Link>
      </div>
      <div className="navbar-links">
        <Link to="/contracts">合同管理</Link>
        {isAdmin && <Link to="/users">用户管理</Link>}
      </div>
      <div className="navbar-user">
        <span className="navbar-username">
          {user?.username} ({user?.role === 'admin' ? '管理员' : '用户'})
        </span>
        <button className="btn btn-link" onClick={handleLogout}>
          登出
        </button>
      </div>
    </nav>
  );
}
