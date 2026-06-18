import { useState, useEffect, type FormEvent } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { createTemplate, getTemplate, updateTemplate } from '../api/templates';
import LoadingSpinner from '../components/LoadingSpinner';

const EMPTY_FORM = {
  name: '',
  category: '',
  party_a_default: '',
  party_b_default: '',
  content: '',
  amount_min: '',
  amount_max: '',
};

const PLACEHOLDER_HINTS = ['{{甲方}}', '{{乙方}}', '{{金额}}', '{{日期}}', '{{合同编号}}'];

export default function TemplateFormPage() {
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
        const t = await getTemplate(Number(id));
        setForm({
          name: t.name,
          category: t.category || '',
          party_a_default: t.party_a_default || '',
          party_b_default: t.party_b_default || '',
          content: t.content || '',
          amount_min: t.amount_min?.toString() || '',
          amount_max: t.amount_max?.toString() || '',
        });
      } catch {
        setError('模板不存在');
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

    if (!form.name.trim()) { setError('请输入模板名称'); return; }

    setLoading(true);
    try {
      const data = {
        name: form.name.trim(),
        category: form.category.trim() || undefined,
        party_a_default: form.party_a_default.trim() || undefined,
        party_b_default: form.party_b_default.trim() || undefined,
        content: form.content,
        amount_min: form.amount_min ? parseFloat(form.amount_min) : undefined,
        amount_max: form.amount_max ? parseFloat(form.amount_max) : undefined,
      };

      if (isEdit) {
        await updateTemplate(Number(id), data);
      } else {
        await createTemplate(data);
      }
      navigate('/templates');
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
        <h1>{isEdit ? '编辑模板' : '创建模板'}</h1>
        <button className="btn btn-secondary" onClick={() => navigate('/templates')}>返回列表</button>
      </div>

      <div className="card" style={{ maxWidth: 720 }}>
        {error && <div className="alert alert-error">{error}</div>}

        <form onSubmit={handleSubmit}>
          <div className="form-row">
            <div className="form-group">
              <label>模板名称 *</label>
              <input type="text" value={form.name} onChange={update('name')} placeholder="如：标准采购合同模板" autoFocus />
            </div>
            <div className="form-group">
              <label>分类标签</label>
              <input type="text" value={form.category} onChange={update('category')} placeholder="如：采购合同、服务合同" />
            </div>
          </div>
          <div className="form-row">
            <div className="form-group">
              <label>甲方默认值</label>
              <input type="text" value={form.party_a_default} onChange={update('party_a_default')} placeholder="默认甲方公司名称" />
            </div>
            <div className="form-group">
              <label>乙方默认值</label>
              <input type="text" value={form.party_b_default} onChange={update('party_b_default')} placeholder="默认乙方公司名称" />
            </div>
          </div>
          <div className="form-row">
            <div className="form-group">
              <label>金额下限</label>
              <input type="number" value={form.amount_min} onChange={update('amount_min')} placeholder="0.00" step="0.01" />
            </div>
            <div className="form-group">
              <label>金额上限</label>
              <input type="number" value={form.amount_max} onChange={update('amount_max')} placeholder="0.00" step="0.01" />
            </div>
          </div>
          <div className="form-group">
            <label>
              合同正文模板
              <span style={{ fontSize: '0.85em', color: '#666', marginLeft: 8 }}>
                可用占位符: {PLACEHOLDER_HINTS.join(', ')}
              </span>
            </label>
            <textarea
              value={form.content}
              onChange={update('content')}
              placeholder={`合同正文模板，使用占位符填充动态内容...\n\n示例：\n本合同由{{甲方}}与{{乙方}}于{{日期}}签订，合同金额为{{金额}}元，合同编号：{{合同编号}}。`}
              rows={8}
            />
          </div>
          <div className="form-actions">
            <button type="submit" className="btn btn-primary" disabled={loading}>
              {loading ? '保存中...' : (isEdit ? '保存修改' : '创建模板')}
            </button>
            <button type="button" className="btn btn-secondary" onClick={() => navigate('/templates')}>取消</button>
          </div>
        </form>
      </div>
    </div>
  );
}
