import { useState, useEffect, useCallback } from 'react';
import { listAuditLogs } from '../api/auditLogs';
import type { AuditLog, AuditLogFilter } from '../types';
import Pagination from '../components/Pagination';
import LoadingSpinner from '../components/LoadingSpinner';

const ACTION_OPTIONS = [
  { label: '全部', value: '' },
  { label: '用户登录', value: 'user.login' },
  { label: '用户登出', value: 'user.logout' },
  { label: '用户注册', value: 'user.register' },
  { label: '密码重置', value: 'user.password_reset' },
  { label: '创建用户', value: 'user.create' },
  { label: '编辑用户', value: 'user.update' },
  { label: '用户状态变更', value: 'user.status_change' },
  { label: '创建合同', value: 'contract.create' },
  { label: '编辑合同', value: 'contract.update' },
  { label: '删除合同', value: 'contract.delete' },
  { label: '合同状态变更', value: 'contract.status_change' },
  { label: '上传附件', value: 'attachment.upload' },
  { label: '删除附件', value: 'attachment.delete' },
];

const ACTION_LABELS: Record<string, string> = Object.fromEntries(
  ACTION_OPTIONS.filter((o) => o.value).map((o) => [o.value, o.label])
);

function formatDateTime(iso: string): string {
  const d = new Date(iso);
  return d.toLocaleString('zh-CN', {
    year: 'numeric',
    month: '2-digit',
    day: '2-digit',
    hour: '2-digit',
    minute: '2-digit',
    second: '2-digit',
  });
}

export default function AuditLogPage() {
  const [logs, setLogs] = useState<AuditLog[]>([]);
  const [total, setTotal] = useState(0);
  const [page, setPage] = useState(1);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  // Filters
  const [action, setAction] = useState('');
  const [userSearch, setUserSearch] = useState('');
  const [startDate, setStartDate] = useState('');
  const [endDate, setEndDate] = useState('');

  const fetch = useCallback(async () => {
    setLoading(true);
    setError('');
    try {
      const params: AuditLogFilter = {
        page,
        page_size: 20,
      };
      if (action) params.action = action;
      if (userSearch) params.user_search = userSearch;
      if (startDate) params.start_date = new Date(startDate).toISOString();
      if (endDate) {
        // End date should include the full day
        const end = new Date(endDate);
        end.setHours(23, 59, 59, 999);
        params.end_date = end.toISOString();
      }
      const res = await listAuditLogs(params);
      setLogs(res.items);
      setTotal(res.total);
    } catch {
      setError('加载审计日志失败');
    } finally {
      setLoading(false);
    }
  }, [page, action, userSearch, startDate, endDate]);

  useEffect(() => {
    fetch();
  }, [fetch]);

  const handleSearch = () => {
    setPage(1);
    fetch();
  };

  const handleReset = () => {
    setAction('');
    setUserSearch('');
    setStartDate('');
    setEndDate('');
    setPage(1);
  };

  return (
    <div className="audit-log-page">
      <div className="page-header">
        <h1>操作审计日志</h1>
      </div>

      <div className="card">
        <div className="audit-filter-bar">
          <div className="filter-group">
            <label>起始日期</label>
            <input
              type="date"
              value={startDate}
              onChange={(e) => setStartDate(e.target.value)}
            />
          </div>
          <div className="filter-group">
            <label>结束日期</label>
            <input
              type="date"
              value={endDate}
              onChange={(e) => setEndDate(e.target.value)}
            />
          </div>
          <div className="filter-group">
            <label>操作类型</label>
            <select value={action} onChange={(e) => setAction(e.target.value)}>
              {ACTION_OPTIONS.map((opt) => (
                <option key={opt.value} value={opt.value}>
                  {opt.label}
                </option>
              ))}
            </select>
          </div>
          <div className="filter-group">
            <label>操作用户</label>
            <input
              type="text"
              placeholder="搜索用户名..."
              value={userSearch}
              onChange={(e) => setUserSearch(e.target.value)}
              onKeyDown={(e) => {
                if (e.key === 'Enter') handleSearch();
              }}
            />
          </div>
          <div className="filter-group filter-actions">
            <button className="btn btn-primary" onClick={handleSearch}>
              查询
            </button>
            <button className="btn btn-secondary reset-btn" onClick={handleReset}>
              重置
            </button>
          </div>
        </div>

        {error && <div className="alert alert-error">{error}</div>}

        {loading ? (
          <LoadingSpinner />
        ) : logs.length === 0 ? (
          <div className="empty-state">
            <p>暂无审计日志记录</p>
          </div>
        ) : (
          <>
            <div className="table-wrapper">
              <table className="audit-table">
                <thead>
                  <tr>
                    <th>时间</th>
                    <th>操作人</th>
                    <th>操作类型</th>
                    <th>操作对象</th>
                    <th>IP 地址</th>
                    <th>详情</th>
                  </tr>
                </thead>
                <tbody>
                  {logs.map((log) => (
                    <tr key={log.id}>
                      <td className="cell-time">{formatDateTime(log.created_at)}</td>
                      <td>{log.username}</td>
                      <td>
                        <span className={`action-badge action-${log.action.replace('.', '-')}`}>
                          {ACTION_LABELS[log.action] || log.action}
                        </span>
                      </td>
                      <td>
                        {log.target_type && log.target_id
                          ? `${log.target_type} #${log.target_id}`
                          : '-'}
                      </td>
                      <td className="cell-ip">{log.ip_address || '-'}</td>
                      <td className="cell-detail" title={log.detail || ''}>
                        {log.detail || '-'}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
            <Pagination
              page={page}
              pageSize={20}
              total={total}
              onPageChange={setPage}
            />
          </>
        )}
      </div>
    </div>
  );
}
