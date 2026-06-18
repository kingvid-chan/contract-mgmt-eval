interface Props {
  page: number;
  pageSize: number;
  total: number;
  onPageChange: (page: number) => void;
}

export default function Pagination({ page, pageSize, total, onPageChange }: Props) {
  const totalPages = Math.max(1, Math.ceil(total / pageSize));

  if (totalPages <= 1) return null;

  const pages: number[] = [];
  const start = Math.max(1, page - 2);
  const end = Math.min(totalPages, page + 2);
  for (let i = start; i <= end; i++) pages.push(i);

  return (
    <div className="pagination">
      <button disabled={page <= 1} onClick={() => onPageChange(page - 1)}>
        上一页
      </button>
      {start > 1 && (
        <>
          <button onClick={() => onPageChange(1)}>1</button>
          {start > 2 && <span>…</span>}
        </>
      )}
      {pages.map((p) => (
        <button key={p} className={p === page ? 'active' : ''} onClick={() => onPageChange(p)}>
          {p}
        </button>
      ))}
      {end < totalPages && (
        <>
          {end < totalPages - 1 && <span>…</span>}
          <button onClick={() => onPageChange(totalPages)}>{totalPages}</button>
        </>
      )}
      <button disabled={page >= totalPages} onClick={() => onPageChange(page + 1)}>
        下一页
      </button>
      <span className="pagination-info">共 {total} 条</span>
    </div>
  );
}
