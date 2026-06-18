import { useState, useEffect, useCallback } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { listContracts, deleteContract } from '../api/contracts';
import type { Contract } from '../types';
import SearchBar from '../components/SearchBar';
import Pagination from '../components/Pagination';
import ConfirmDialog from '../components/ConfirmDialog';
import LoadingSpinner from '../components/LoadingSpinner';

const STATUS_FILTERS = [
  { label: '草稿', value: 'draft' },
  { label: '生效', value: 'active' },
  { label: '终止', value: 'terminated' },
  { label: '到期', value: 'expired' },
];

const STATUS_LABELS: Record<string, string> = {
  draft: '草稿', active: '生效', terminated: '终止', expired: '到期',
};

export default function ContractListPage() {
  const navigate = useNavigate();
  const [contracts, setContracts] = useState<Contract[]>([]);
  const [total, setTotal] = useState(0);
  const [page, setPage] = useState(1);
  const [search, setSearch] = useState<string | undefined>();
  const [statusFilter, setStatusFilter] = useState<string | undefined>();
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [deleteTarget, setDeleteTarget] = useState<Contract | null>(null);

  const fetch = useCallback(async () => {
    setLoading(true);
    setError('');
    try {
      const res = await listContracts({
        search, status: statusFilter, page, page_size: 20, sort_by: 'id', sort_order: 'desc',
      });
      setContracts(res.items);
      setTotal(res.total);
    } catch {
      setError('加载合同列表失败');
    } finally {
      setLoading(false);
    }
  }, [search, statusFilter, page]);

  useEffect(() => { fetch(); }, [fetch]);

  const handleDelete = async () => {
    if (!deleteTarget) return;
    try {
      await deleteContract(deleteTarget.id);
      setDeleteTarget(null);
      fetch();
    } catch (err: unknown) {
      if (err && typeof err === 'object' && 'response' in err) {
        const axiosErr = err as { response?: { data?: { detail?: string } } };
        setError(axiosErr.response?.data?.detail || '删除失败');
      }
    }
  };

  const handleSearch = (q: string, status?: string) => {
    setSearch(q || undefined);
    setStatusFilter(status || undefined);
    setPage(1);
  };

  return (
    <div>
      <div className="page-header">
        <h1>合同管理</h1>
        <Link to="/contracts/new" className="btn btn-primary">+ 新建合同</Link>
      </div>

      <div className="card">
        <SearchBar
          placeholder="搜索合同编号、标题、甲乙方..."
          filters={STATUS_FILTERS}
          activeFilter={statusFilter}
          onSearch={handleSearch}
        />

        {error && <div className="alert alert-error">{error}</div>}

        {loading ? (
          <LoadingSpinner />
        ) : contracts.length === 0 ? (
          <div className="empty-state"><p>暂无合同数据</p></div>
        ) : (
          <>
            <div className="contract-list">
              {contracts.map((c) => (
                <div key={c.id} className="contract-card" onClick={() => navigate(`/contracts/${c.id}`)}>
                  <div>
                    <div className="contract-card-title">{c.title}</div>
                    <div className="contract-card-meta">
                      {c.contract_no} | {c.party_a} ↔ {c.party_b}
                      {c.amount ? ` | ¥${c.amount.toLocaleString()}` : ''}
                    </div>
                  </div>
                  <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
                    <span className={`tag tag-${c.status}`}>{STATUS_LABELS[c.status] || c.status}</span>
                    {c.attachment_count > 0 && <span style={{ fontSize: 13, color: '#999' }}>📎 {c.attachment_count}</span>}
                    {c.status === 'draft' && (
                      <button
                        className="btn btn-sm btn-danger"
                        onClick={(e) => { e.stopPropagation(); setDeleteTarget(c); }}
                      >
                        删除
                      </button>
                    )}
                  </div>
                </div>
              ))}
            </div>
            <Pagination page={page} pageSize={20} total={total} onPageChange={setPage} />
          </>
        )}
      </div>

      <ConfirmDialog
        open={!!deleteTarget}
        title="删除合同"
        message={`确定要删除合同 "${deleteTarget?.contract_no}" 吗？此操作不可撤销。`}
        confirmText="删除"
        onConfirm={handleDelete}
        onCancel={() => setDeleteTarget(null)}
      />
    </div>
  );
}
