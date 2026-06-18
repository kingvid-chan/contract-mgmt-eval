import { useState, type FormEvent } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { useAuth } from '../contexts/AuthContext';

export default function RegisterPage() {
  const { registerAction } = useAuth();
  const navigate = useNavigate();
  const [form, setForm] = useState({ username: '', email: '', password: '', confirmPassword: '' });
  const [error, setError] = useState('');
  const [success, setSuccess] = useState('');
  const [loading, setLoading] = useState(false);

  const update = (field: string) => (e: React.ChangeEvent<HTMLInputElement>) =>
    setForm((f) => ({ ...f, [field]: e.target.value }));

  const validate = (): string | null => {
    if (!form.username.trim() || form.username.trim().length < 2) return '用户名至少 2 个字符';
    if (!form.email.trim() || !form.email.includes('@')) return '请输入有效的邮箱';
    if (!form.password || form.password.length < 6) return '密码至少 6 个字符';
    if (form.password !== form.confirmPassword) return '两次密码不一致';
    return null;
  };

  const handleSubmit = async (e: FormEvent) => {
    e.preventDefault();
    setError('');
    setSuccess('');

    const msg = validate();
    if (msg) { setError(msg); return; }

    setLoading(true);
    try {
      await registerAction(form.username.trim(), form.email.trim(), form.password);
      setSuccess('注册成功！即将跳转到登录页...');
      setTimeout(() => navigate('/login'), 1500);
    } catch (err: unknown) {
      if (err && typeof err === 'object' && 'response' in err) {
        const axiosErr = err as { response?: { data?: { detail?: string } } };
        setError(axiosErr.response?.data?.detail || '注册失败');
      } else {
        setError('网络错误，请检查后端是否启动');
      }
    } finally {
      setLoading(false);
    }
  };

  return (
    <div style={{ minHeight: '100vh', display: 'flex', alignItems: 'center', justifyContent: 'center', background: '#f0f2f5' }}>
      <div className="card" style={{ width: 420 }}>
        <h2 style={{ textAlign: 'center', marginBottom: 24 }}>注册</h2>
        {error && <div className="alert alert-error">{error}</div>}
        {success && <div className="alert alert-success">{success}</div>}

        <form onSubmit={handleSubmit}>
          <div className="form-group">
            <label>用户名</label>
            <input type="text" value={form.username} onChange={update('username')} placeholder="2-50 个字符" autoFocus />
          </div>
          <div className="form-group">
            <label>邮箱</label>
            <input type="email" value={form.email} onChange={update('email')} placeholder="user@example.com" />
          </div>
          <div className="form-group">
            <label>密码</label>
            <input type="password" value={form.password} onChange={update('password')} placeholder="至少 6 个字符" />
          </div>
          <div className="form-group">
            <label>确认密码</label>
            <input type="password" value={form.confirmPassword} onChange={update('confirmPassword')} placeholder="再次输入密码" />
          </div>
          <button type="submit" className="btn btn-primary" style={{ width: '100%', marginTop: 8 }} disabled={loading}>
            {loading ? '注册中...' : '注册'}
          </button>
        </form>

        <div style={{ textAlign: 'center', marginTop: 16, fontSize: 14, color: '#666' }}>
          已有账户？<Link to="/login">返回登录</Link>
        </div>
      </div>
    </div>
  );
}
