import { useState, useEffect, type FormEvent } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { createContract, getContract, updateContract } from '../api/contracts';
import LoadingSpinner from '../components/LoadingSpinner';

const EMPTY_FORM = { title: '', contract_no: '', party_a: '', party_b: '', amount: '', sign_date: '', expiry_date: '', content: '' };

export default function ContractFormPage() {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const isEdit = !!id;

  const [form, setForm] = useState(EMPTY_FORM);
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);
  const [fetching, setFetching] = useState(isEdit);

  useEffect(() => {
    if (!isEdit) return;
    (async () => {
      try {
        const c = await getContract(Number(id));
        setForm({
          title: c.title,
          contract_no: c.contract_no,
          party_a: c.party_a,
          party_b: c.party_b,
          amount: c.amount?.toString() || '',
          sign_date: c.sign_date || '',
          expiry_date: c.expiry_date || '',
          content: c.content || '',
        });
      } catch {
        setError('合同不存在');
      } finally {
        setFetching(false);
      }
    })();
  }, [id, isEdit]);

  const update = (field: string) => (e: React.ChangeEvent<HTMLInputElement | HTMLTextAreaElement>) =>
    setForm((f) => ({ ...f, [field]: e.target.value }));

  const handleSubmit = async (e: FormEvent) => {
    e.preventDefault();
    setError('');

    if (!form.title.trim()) { setError('请输入合同标题'); return; }
    if (!form.contract_no.trim()) { setError('请输入合同编号'); return; }
    if (!form.party_a.trim()) { setError('请输入甲方'); return; }
    if (!form.party_b.trim()) { setError('请输入乙方'); return; }

    setLoading(true);
    try {
      const data = {
        title: form.title.trim(),
        contract_no: form.contract_no.trim(),
        party_a: form.party_a.trim(),
        party_b: form.party_b.trim(),
        amount: form.amount ? parseFloat(form.amount) : undefined,
        sign_date: form.sign_date || undefined,
        expiry_date: form.expiry_date || undefined,
        content: form.content,
      };

      if (isEdit) {
        await updateContract(Number(id), data);
      } else {
        await createContract(data);
      }
      navigate('/contracts');
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
        <h1>{isEdit ? '编辑合同' : '新建合同'}</h1>
        <button className="btn btn-secondary" onClick={() => navigate('/contracts')}>返回列表</button>
      </div>

      <div className="card" style={{ maxWidth: 720 }}>
        {error && <div className="alert alert-error">{error}</div>}

        <form onSubmit={handleSubmit}>
          <div className="form-row">
            <div className="form-group">
              <label>合同编号 *</label>
              <input type="text" value={form.contract_no} onChange={update('contract_no')} placeholder="HT-2026-001" autoFocus />
            </div>
            <div className="form-group">
              <label>合同金额</label>
              <input type="number" value={form.amount} onChange={update('amount')} placeholder="0.00" step="0.01" />
            </div>
          </div>
          <div className="form-group">
            <label>合同标题 *</label>
            <input type="text" value={form.title} onChange={update('title')} placeholder="请输入合同标题" />
          </div>
          <div className="form-row">
            <div className="form-group">
              <label>甲方 *</label>
              <input type="text" value={form.party_a} onChange={update('party_a')} placeholder="甲方公司名称" />
            </div>
            <div className="form-group">
              <label>乙方 *</label>
              <input type="text" value={form.party_b} onChange={update('party_b')} placeholder="乙方公司名称" />
            </div>
          </div>
          <div className="form-row">
            <div className="form-group">
              <label>签订日期</label>
              <input type="date" value={form.sign_date} onChange={update('sign_date')} />
            </div>
            <div className="form-group">
              <label>到期日期</label>
              <input type="date" value={form.expiry_date} onChange={update('expiry_date')} />
            </div>
          </div>
          <div className="form-group">
            <label>合同内容</label>
            <textarea value={form.content} onChange={update('content')} placeholder="合同正文或备注信息..." rows={4} />
          </div>
          <div className="form-actions">
            <button type="submit" className="btn btn-primary" disabled={loading}>
              {loading ? '保存中...' : (isEdit ? '保存修改' : '创建合同')}
            </button>
            <button type="button" className="btn btn-secondary" onClick={() => navigate('/contracts')}>取消</button>
          </div>
        </form>
      </div>
    </div>
  );
}
