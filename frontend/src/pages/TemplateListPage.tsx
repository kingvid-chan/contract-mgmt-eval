import { useState, useEffect, useCallback } from 'react';
import { Link } from 'react-router-dom';
import { listTemplates, deleteTemplate } from '../api/templates';
import type { ContractTemplate } from '../types';
import SearchBar from '../components/SearchBar';
import Pagination from '../components/Pagination';
import ConfirmDialog from '../components/ConfirmDialog';
import LoadingSpinner from '../components/LoadingSpinner';

export default function TemplateListPage() {
  const [templates, setTemplates] = useState<ContractTemplate[]>([]);
  const [total, setTotal] = useState(0);
  const [page, setPage] = useState(1);
  const [search, setSearch] = useState<string | undefined>();
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [deleteTarget, setDeleteTarget] = useState<ContractTemplate | null>(null);

  const fetch = useCallback(async () => {
    setLoading(true);
    setError('');
    try {
      const res = await listTemplates({ search, page, page_size: 20 });
      setTemplates(res.items);
      setTotal(res.total);
    } catch {
      setError('加载模板列表失败');
    } finally {
      setLoading(false);
    }
  }, [search, page]);

  useEffect(() => { fetch(); }, [fetch]);

  const handleDelete = async () => {
    if (!deleteTarget) return;
    try {
      await deleteTemplate(deleteTarget.id);
      setDeleteTarget(null);
      fetch();
    } catch {
      setError('删除模板失败');
    }
  };

  const handleSearch = (q: string) => {
    setSearch(q || undefined);
    setPage(1);
  };

  const formatDate = (iso: string) => iso?.slice(0, 10) ?? '';

  return (
    <div>
      <div className="page-header">
        <h1>模板管理</h1>
        <Link to="/templates/new" className="btn btn-primary">+ 创建模板</Link>
      </div>

      <div className="card">
        <SearchBar
          placeholder="搜索模板名称或分类..."
          onSearch={handleSearch}
        />

        {error && <div className="alert alert-error">{error}</div>}

        {loading ? (
          <LoadingSpinner />
        ) : templates.length === 0 ? (
          <div className="empty-state"><p>暂无模板数据</p></div>
        ) : (
          <>
            <div className="table-container">
              <table>
                <thead>
                  <tr>
                    <th>ID</th>
                    <th>模板名称</th>
                    <th>分类</th>
                    <th>创建者</th>
                    <th>创建时间</th>
                    <th>操作</th>
                  </tr>
                </thead>
                <tbody>
                  {templates.map((t) => (
                    <tr key={t.id}>
                      <td>{t.id}</td>
                      <td>{t.name}</td>
                      <td>
                        {t.category && (
                          <span className="tag tag-user">{t.category}</span>
                        )}
                      </td>
                      <td>{t.creator_username}</td>
                      <td>{formatDate(t.created_at)}</td>
                      <td style={{ display: 'flex', gap: 4 }}>
                        <Link to={`/templates/${t.id}/edit`} className="btn btn-sm">编辑</Link>
                        <button
                          className="btn btn-sm btn-danger"
                          onClick={() => setDeleteTarget(t)}
                        >
                          删除
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
        open={!!deleteTarget}
        title="删除模板"
        message={`确定要删除模板 "${deleteTarget?.name}" 吗？删除后不影响已通过此模板创建的合同。`}
        confirmText="删除"
        onConfirm={handleDelete}
        onCancel={() => setDeleteTarget(null)}
      />
    </div>
  );
}
