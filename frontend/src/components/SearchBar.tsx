import { useState } from 'react';

interface Props {
  placeholder?: string;
  filters?: { label: string; value: string }[];
  activeFilter?: string;
  onSearch: (query: string, filter?: string) => void;
}

export default function SearchBar({
  placeholder = '搜索...',
  filters,
  activeFilter,
  onSearch,
}: Props) {
  const [query, setQuery] = useState('');

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    onSearch(query, activeFilter);
  };

  return (
    <form className="search-bar" onSubmit={handleSubmit}>
      <input
        type="text"
        value={query}
        onChange={(e) => setQuery(e.target.value)}
        placeholder={placeholder}
      />
      {filters && (
        <select
          value={activeFilter || ''}
          onChange={(e) => onSearch(query, e.target.value || undefined)}
        >
          <option value="">全部</option>
          {filters.map((f) => (
            <option key={f.value} value={f.value}>
              {f.label}
            </option>
          ))}
        </select>
      )}
      <button type="submit" className="btn btn-primary">
        搜索
      </button>
    </form>
  );
}
