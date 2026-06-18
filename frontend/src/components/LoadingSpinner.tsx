export default function LoadingSpinner({ text = '加载中...' }: { text?: string }) {
  return (
    <div style={{ display: 'flex', justifyContent: 'center', alignItems: 'center', padding: 60 }}>
      <div style={{ textAlign: 'center' }}>
        <div className="spinner" />
        <p style={{ marginTop: 12, color: '#666' }}>{text}</p>
      </div>
    </div>
  );
}
