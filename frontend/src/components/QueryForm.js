import React, { useState } from 'react';
import '../styles/QueryForm.css';

function QueryForm({ onSubmit, disabled }) {
  const [query, setQuery] = useState('');
  const [topK, setTopK] = useState(3);
  const [useStreaming, setUseStreaming] = useState(false);

  const handleSubmit = (e) => {
    e.preventDefault();
    if (query.trim()) {
      onSubmit(query, topK, useStreaming);
    }
  };

  return (
    <form onSubmit={handleSubmit} className="query-form">
      <div className="form-group">
        <label htmlFor="query">Ask a Question:</label>
        <textarea
          id="query"
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          placeholder="Type your insurance question here..."
          disabled={disabled}
          rows="3"
        />
      </div>

      <div className="form-group-row">
        <div className="form-group">
          <label htmlFor="topK">Context Documents (top_k):</label>
          <select
            id="topK"
            value={topK}
            onChange={(e) => setTopK(Number(e.target.value))}
            disabled={disabled}
          >
            <option value={1}>1</option>
            <option value={3}>3</option>
            <option value={5}>5</option>
            <option value={10}>10</option>
          </select>
        </div>

        <div className="form-group checkbox-group">
          <label htmlFor="streaming">
            <input
              id="streaming"
              type="checkbox"
              checked={useStreaming}
              onChange={(e) => setUseStreaming(e.target.checked)}
              disabled={disabled}
            />
            Streaming Mode
          </label>
        </div>
      </div>

      <button
        type="submit"
        disabled={disabled || !query.trim()}
        className="submit-btn"
      >
        {disabled ? 'Connecting...' : 'Get Answer'}
      </button>
    </form>
  );
}

export default QueryForm;
