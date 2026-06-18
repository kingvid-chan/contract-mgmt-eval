import { useState, useEffect, useCallback } from 'react';
import { Link } from 'react-router-dom';
import { listUsers, toggleUserStatus } from '../api/users';
import type { User } from '../types';
import SearchBar from '../components/SearchBar';
import Pagination from '../components/Pagination';
import ConfirmDialog from '../components/ConfirmDialog';
import LoadingSpinner from '../components/LoadingSpinner';

const ROLE_FILTERS = [
  { label: '管理员', value: 'admin' },
  { label: '用户', value: 'user' },
];

export default function UserListPage() {
  const [users, setUsers] = useState<User[]>([]);
  const [total, setTotal] = useState(0);
  const [page, setPage] = useState(1);
  const [search, setSearch] = useState<string | undefined>();
  const [roleFilter, setRoleFilter] = useState<string | undefined>();
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [toggleTarget, setToggleTarget] = useState<User | null>(null);

  const fetch = useCallback(async () => {
    setLoading(true);
    setError('');
    try {
      const res = await listUsers({ search, role: roleFilter, page, page_size: 20 });
      setUsers(res.items);
      setTotal(res.total);
    } catch {
      setError('加载用户列表失败');
    } finally {
      setLoading(false);
    }
  }, [search, roleFilter, page]);

  useEffect(() => { fetch(); }, [fetch]);

  const handleToggle = async () => {
    if (!toggleTarget) return;
    const newStatus = toggleTarget.status === 'active' ? 'disabled' : 'active';
    try {
      await toggleUserStatus(toggleTarget.id, newStatus);
      setToggleTarget(null);
      fetch();
    } catch {
      setError('操作失败');
    }
  };

  const handleSearch = (q: string, role?: string) => {
    setSearch(q || undefined);
    setRoleFilter(role || undefined);
    setPage(1);
  };

  return (
    <div>
      <div className="page-header">
        <h1>用户管理</h1>
        <Link to="/users/new" className="btn btn-primary">+ 创建用户</Link>
      </div>

      <div className="card">
        <SearchBar
          placeholder="搜索用户名或邮箱..."
          filters={ROLE_FILTERS}
          activeFilter={roleFilter}
          onSearch={handleSearch}
        />

        {error && <div className="alert alert-error">{error}</div>}

        {loading ? (
          <LoadingSpinner />
        ) : users.length === 0 ? (
          <div className="empty-state"><p>暂无用户数据</p></div>
        ) : (
          <>
            <div className="table-container">
              <table>
                <thead>
                  <tr>
                    <th>ID</th>
                    <th>用户名</th>
                    <th>邮箱</th>
                    <th>角色</th>
                    <th>状态</th>
                    <th>操作</th>
                  </tr>
                </thead>
                <tbody>
                  {users.map((u) => (
                    <tr key={u.id}>
                      <td>{u.id}</td>
                      <td>{u.username}</td>
                      <td>{u.email}</td>
                      <td>
                        <span className={`tag ${u.role === 'admin' ? 'tag-admin' : 'tag-user'}`}>
                          {u.role === 'admin' ? '管理员' : '用户'}
                        </span>
                      </td>
                      <td>
                        <span className={`tag ${u.status === 'active' ? 'tag-active-user' : 'tag-disabled'}`}>
                          {u.status === 'active' ? '正常' : '禁用'}
                        </span>
                      </td>
                      <td style={{ display: 'flex', gap: 4 }}>
                        <Link to={`/users/${u.id}/edit`} className="btn btn-sm">编辑</Link>
                        <button
                          className={`btn btn-sm ${u.status === 'active' ? 'btn-danger' : 'btn-success'}`}
                          onClick={() => setToggleTarget(u)}
                        >
                          {u.status === 'active' ? '禁用' : '启用'}
                        </button>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
            <Pagination page={page} pageSize={20} total={total} onPageChange={setPage} />
          </>
        )}
      </div>

      <ConfirmDialog
        open={!!toggleTarget}
        title={toggleTarget?.status === 'active' ? '禁用用户' : '启用用户'}
        message={`确定要${toggleTarget?.status === 'active' ? '禁用' : '启用'}用户 "${toggleTarget?.username}" 吗？`}
        confirmText={toggleTarget?.status === 'active' ? '禁用' : '启用'}
        onConfirm={handleToggle}
        onCancel={() => setToggleTarget(null)}
      />
    </div>
  );
}
