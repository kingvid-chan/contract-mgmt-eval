import { useState, useEffect, useCallback } from 'react';
import { useParams, useNavigate, Link } from 'react-router-dom';
import { getContract, deleteContract, updateContractStatus } from '../api/contracts';
import { listAttachments, uploadAttachment, deleteAttachment, getDownloadUrl } from '../api/attachments';
import type { Contract, Attachment } from '../types';
import ConfirmDialog from '../components/ConfirmDialog';
import LoadingSpinner from '../components/LoadingSpinner';

const STATUS_LABELS: Record<string, string> = {
  draft: '草稿', active: '生效', terminated: '终止', expired: '到期',
};

const NEXT_STATUS: Record<string, { label: string; value: string; className: string }[]> = {
  draft: [
    { label: '激活合同', value: 'active', className: 'btn-success' },
  ],
  active: [
    { label: '终止合同', value: 'terminated', className: 'btn-danger' },
    { label: '标记到期', value: 'expired', className: 'btn-secondary' },
  ],
};

export default function ContractDetailPage() {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const [contract, setContract] = useState<Contract | null>(null);
  const [attachments, setAttachments] = useState<Attachment[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [deleteTarget, setDeleteTarget] = useState<'contract' | number | null>(null);
  const [statusTarget, setStatusTarget] = useState<string | null>(null);
  const [uploading, setUploading] = useState(false);

  const fetch = useCallback(async () => {
    if (!id) return;
    setLoading(true);
    setError('');
    try {
      const [c, a] = await Promise.all([
        getContract(Number(id)),
        listAttachments(Number(id)),
      ]);
      setContract(c);
      setAttachments(a.items);
    } catch {
      setError('加载合同详情失败');
    } finally {
      setLoading(false);
    }
  }, [id]);

  useEffect(() => { fetch(); }, [fetch]);

  const handleDelete = async () => {
    if (!id || deleteTarget !== 'contract') return;
    try {
      await deleteContract(Number(id));
      navigate('/contracts');
    } catch (err: unknown) {
      if (err && typeof err === 'object' && 'response' in err) {
        const axiosErr = err as { response?: { data?: { detail?: string } } };
        setError(axiosErr.response?.data?.detail || '删除失败');
      }
      setDeleteTarget(null);
    }
  };

  const handleStatusChange = async (newStatus: string) => {
    if (!id) return;
    setStatusTarget(null);
    try {
      const updated = await updateContractStatus(Number(id), newStatus);
      setContract(updated);
    } catch (err: unknown) {
      if (err && typeof err === 'object' && 'response' in err) {
        const axiosErr = err as { response?: { data?: { detail?: string } } };
        setError(axiosErr.response?.data?.detail || '操作失败');
      }
    }
  };

  const handleUpload = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file || !id) return;

    const ext = file.name.split('.').pop()?.toLowerCase();
    if (!['pdf', 'doc', 'docx'].includes(ext || '')) {
      setError('仅支持 PDF 和 Word (.pdf, .doc, .docx) 格式');
      e.target.value = '';
      return;
    }
    if (file.size > 10 * 1024 * 1024) {
      setError('文件大小不能超过 10MB');
      e.target.value = '';
      return;
    }

    setUploading(true);
    setError('');
    try {
      await uploadAttachment(Number(id), file);
      await fetch();
    } catch {
      setError('上传失败');
    } finally {
      setUploading(false);
      e.target.value = '';
    }
  };

  const handleDeleteAttachment = async (attachmentId: number) => {
    try {
      await deleteAttachment(attachmentId);
      setDeleteTarget(null);
      fetch();
    } catch {
      setError('删除附件失败');
    }
  };

  const formatSize = (bytes: number) => {
    if (bytes < 1024) return `${bytes} B`;
    if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
    return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
  };

  if (loading) return <LoadingSpinner />;
  if (error && !contract) return <div className="alert alert-error">{error}</div>;
  if (!contract) return <div className="empty-state"><p>合同不存在</p></div>;

  const nextActions = NEXT_STATUS[contract.status] || [];

  return (
    <div>
      <div className="page-header">
        <h1>合同详情</h1>
        <div style={{ display: 'flex', gap: 8 }}>
          <Link to={`/contracts/${id}/edit`} className="btn">编辑</Link>
          {contract.status === 'draft' && (
            <button className="btn btn-danger" onClick={() => setDeleteTarget('contract')}>删除</button>
          )}
          {nextActions.map((a) => (
            <button key={a.value} className={`btn ${a.className}`} onClick={() => setStatusTarget(a.value)}>
              {a.label}
            </button>
          ))}
          <button className="btn btn-secondary" onClick={() => navigate('/contracts')}>返回</button>
        </div>
      </div>

      {error && <div className="alert alert-error">{error}</div>}

      {/* Contract Info */}
      <div className="card">
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 16 }}>
          <h2 style={{ margin: 0 }}>{contract.title}</h2>
          <span className={`tag tag-${contract.status}`}>{STATUS_LABELS[contract.status] || contract.status}</span>
        </div>
        <div className="detail-grid">
          <div className="detail-label">合同编号</div><div className="detail-value">{contract.contract_no}</div>
          <div className="detail-label">甲方</div><div className="detail-value">{contract.party_a}</div>
          <div className="detail-label">乙方</div><div className="detail-value">{contract.party_b}</div>
          <div className="detail-label">金额</div><div className="detail-value">¥{contract.amount?.toLocaleString() || '-'}</div>
          <div className="detail-label">签订日期</div><div className="detail-value">{contract.sign_date || '-'}</div>
          <div className="detail-label">到期日期</div><div className="detail-value">{contract.expiry_date || '-'}</div>
          <div className="detail-label">创建者</div><div className="detail-value">{contract.creator_username || contract.created_by}</div>
          <div className="detail-label">创建时间</div><div className="detail-value">{new Date(contract.created_at).toLocaleString()}</div>
        </div>
        {contract.content && (
          <div style={{ marginTop: 16, padding: 16, background: '#fafafa', borderRadius: 6 }}>
            <div className="detail-label" style={{ marginBottom: 8 }}>合同内容</div>
            <div style={{ whiteSpace: 'pre-wrap' }}>{contract.content}</div>
          </div>
        )}
      </div>

      {/* Attachments */}
      <div className="card">
        <div className="card-header">
          <h2>附件管理 ({attachments.length})</h2>
        </div>

        {/* Upload */}
        <div className="upload-zone" onClick={() => document.getElementById('file-upload')?.click()}>
          <input
            id="file-upload"
            type="file"
            accept=".pdf,.doc,.docx"
            onChange={handleUpload}
            style={{ display: 'none' }}
          />
          <p>{uploading ? '上传中...' : '点击上传附件 (PDF / Word，最大 10MB)'}</p>
        </div>

        {/* List */}
        {attachments.length === 0 ? (
          <div className="empty-state" style={{ padding: 24 }}><p>暂无附件</p></div>
        ) : (
          <div className="table-container">
            <table>
              <thead>
                <tr>
                  <th>文件名</th>
                  <th>类型</th>
                  <th>大小</th>
                  <th>上传者</th>
                  <th>时间</th>
                  <th>操作</th>
                </tr>
              </thead>
              <tbody>
                {attachments.map((a) => (
                  <tr key={a.id}>
                    <td>{a.original_name}</td>
                    <td><span className="tag tag-draft">{a.file_type.toUpperCase()}</span></td>
                    <td>{formatSize(a.file_size)}</td>
                    <td>{a.uploader_username || '-'}</td>
                    <td>{new Date(a.uploaded_at).toLocaleString()}</td>
                    <td style={{ display: 'flex', gap: 4 }}>
                      <a
                        href={getDownloadUrl(a.id)}
                        className="btn btn-sm"
                        target="_blank"
                        rel="noreferrer"
                      >
                        下载
                      </a>
                      <a
                        href={getDownloadUrl(a.id, true)}
                        className="btn btn-sm"
                        target="_blank"
                        rel="noreferrer"
                      >
                        预览
                      </a>
                      <button
                        className="btn btn-sm btn-danger"
                        onClick={() => setDeleteTarget(a.id)}
                      >
                        删除
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>

      {/* Delete Contract Confirm */}
      <ConfirmDialog
        open={deleteTarget === 'contract'}
        title="删除合同"
        message={`确定要删除合同 "${contract.contract_no}" 吗？此操作不可撤销。`}
        confirmText="删除"
        onConfirm={handleDelete}
        onCancel={() => setDeleteTarget(null)}
      />

      {/* Delete Attachment Confirm */}
      <ConfirmDialog
        open={typeof deleteTarget === 'number'}
        title="删除附件"
        message="确定要删除此附件吗？"
        confirmText="删除"
        onConfirm={() => deleteTarget !== null && typeof deleteTarget === 'number' && handleDeleteAttachment(deleteTarget)}
        onCancel={() => setDeleteTarget(null)}
      />

      {/* Status Change Confirm */}
      <ConfirmDialog
        open={!!statusTarget}
        title="变更合同状态"
        message={`确定要将合同状态变更为 "${STATUS_LABELS[statusTarget || ''] || statusTarget}" 吗？`}
        confirmText="确认"
        onConfirm={() => statusTarget && handleStatusChange(statusTarget)}
        onCancel={() => setStatusTarget(null)}
      />
    </div>
  );
}
