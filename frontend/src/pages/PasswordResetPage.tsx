import { useState, type FormEvent } from 'react';
import { Link } from 'react-router-dom';
import { passwordReset } from '../api/auth';

export default function PasswordResetPage() {
  const [email, setEmail] = useState('');
  const [error, setError] = useState('');
  const [result, setResult] = useState<{ message: string; new_password?: string } | null>(null);
  const [loading, setLoading] = useState(false);

  const handleSubmit = async (e: FormEvent) => {
    e.preventDefault();
    setError('');
    setResult(null);

    if (!email.trim() || !email.includes('@')) {
      setError('请输入有效的邮箱地址');
      return;
    }

    setLoading(true);
    try {
      const res = await passwordReset(email.trim());
      setResult(res);
    } catch (err: unknown) {
      if (err && typeof err === 'object' && 'response' in err) {
        const axiosErr = err as { response?: { data?: { detail?: string } } };
        setError(axiosErr.response?.data?.detail || '重置失败');
      } else {
        setError('网络错误，请检查后端是否启动');
      }
    } finally {
      setLoading(false);
    }
  };

  return (
    <div style={{ minHeight: '100vh', display: 'flex', alignItems: 'center', justifyContent: 'center', background: '#f0f2f5' }}>
      <div className="card" style={{ width: 400 }}>
        <h2 style={{ textAlign: 'center', marginBottom: 24 }}>重置密码</h2>
        {error && <div className="alert alert-error">{error}</div>}

        {result ? (
          <div>
            <div className="alert alert-success" style={{ marginBottom: 16 }}>{result.message}</div>
            {result.new_password && (
              <div className="alert alert-info">
                新密码：<strong>{result.new_password}</strong>
                <br />
                <span style={{ fontSize: 13 }}>请复制并妥善保存新密码。</span>
              </div>
            )}
            <Link to="/login" className="btn btn-primary" style={{ display: 'block', textAlign: 'center', marginTop: 16 }}>
              返回登录
            </Link>
          </div>
        ) : (
          <form onSubmit={handleSubmit}>
            <div className="form-group">
              <label>注册邮箱</label>
              <input
                type="email"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                placeholder="请输入注册时使用的邮箱"
                autoFocus
              />
            </div>
            <button type="submit" className="btn btn-primary" style={{ width: '100%' }} disabled={loading}>
              {loading ? '重置中...' : '重置密码'}
            </button>
          </form>
        )}

        <div style={{ textAlign: 'center', marginTop: 16, fontSize: 14, color: '#666' }}>
          <Link to="/login">返回登录</Link>
        </div>
      </div>
    </div>
  );
}
