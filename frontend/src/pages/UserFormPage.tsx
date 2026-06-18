import { useState, useEffect, type FormEvent } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { createUser, getUser, updateUser } from '../api/users';
import LoadingSpinner from '../components/LoadingSpinner';

export default function UserFormPage() {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const isEdit = !!id;

  const [form, setForm] = useState({ username: '', email: '', password: '', role: 'user' });
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);
  const [fetching, setFetching] = useState(isEdit);

  useEffect(() => {
    if (!isEdit) return;
    (async () => {
      try {
        const u = await getUser(Number(id));
        setForm({ username: u.username, email: u.email, password: '', role: u.role });
      } catch {
        setError('用户不存在');
      } finally {
        setFetching(false);
      }
    })();
  }, [id, isEdit]);

  const update = (field: string) => (e: React.ChangeEvent<HTMLInputElement | HTMLSelectElement>) =>
    setForm((f) => ({ ...f, [field]: e.target.value }));

  const handleSubmit = async (e: FormEvent) => {
    e.preventDefault();
    setError('');

    if (!form.username.trim() || form.username.trim().length < 2) { setError('用户名至少 2 个字符'); return; }
    if (!form.email.trim() || !form.email.includes('@')) { setError('请输入有效的邮箱'); return; }
    if (!isEdit && (!form.password || form.password.length < 6)) { setError('密码至少 6 个字符'); return; }

    setLoading(true);
    try {
      if (isEdit) {
        await updateUser(Number(id), {
          username: form.username.trim(),
          email: form.email.trim(),
          ...(form.password ? { password: form.password } : {}),
          role: form.role,
        });
      } else {
        await createUser({
          username: form.username.trim(),
          email: form.email.trim(),
          password: form.password,
          role: form.role,
        });
      }
      navigate('/users');
    } catch (err: unknown) {
      if (err && typeof err === 'object' && 'response' in err) {
        const axiosErr = err as { response?: { data?: { detail?: string } } };
        setError(axiosErr.response?.data?.detail || '操作失败');
      } else {
        setError('网络错误');
      }
    } finally {
      setLoading(false);
    }
  };

  if (fetching) return <LoadingSpinner />;

  return (
    <div>
      <div className="page-header">
        <h1>{isEdit ? '编辑用户' : '创建用户'}</h1>
        <button className="btn btn-secondary" onClick={() => navigate('/users')}>返回列表</button>
      </div>

      <div className="card" style={{ maxWidth: 560 }}>
        {error && <div className="alert alert-error">{error}</div>}

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
            <label>密码{isEdit ? '（留空则不修改）' : ''}</label>
            <input type="password" value={form.password} onChange={update('password')} placeholder={isEdit ? '留空则不改密码' : '至少 6 个字符'} />
          </div>
          <div className="form-group">
            <label>角色</label>
            <select value={form.role} onChange={update('role')}>
              <option value="user">用户</option>
              <option value="admin">管理员</option>
            </select>
          </div>
          <div className="form-actions">
            <button type="submit" className="btn btn-primary" disabled={loading}>
              {loading ? '保存中...' : '保存'}
            </button>
            <button type="button" className="btn btn-secondary" onClick={() => navigate('/users')}>取消</button>
          </div>
        </form>
      </div>
    </div>
  );
}
