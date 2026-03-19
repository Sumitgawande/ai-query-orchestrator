import React, { useState, useEffect } from 'react';
import './App.css';
import QueryForm from './components/QueryForm';
import ResponseDisplay from './components/ResponseDisplay';
import LoadingSpinner from './components/LoadingSpinner';

function App() {
  const [response, setResponse] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [apiHealth, setApiHealth] = useState(false);

  // Check API health on component mount
  useEffect(() => {
    checkAPIHealth();
    const interval = setInterval(checkAPIHealth, 30000); // Check every 30 seconds
    return () => clearInterval(interval);
  }, []);

  const checkAPIHealth = async () => {
    try {
      const response = await fetch('http://localhost:8000/health');
      if (response.ok) {
        setApiHealth(true);
        setError(null);
      } else {
        setApiHealth(false);
      }
    } catch (err) {
      setApiHealth(false);
    }
  };

  const handleQuery = async (query, topK, useStreaming = false) => {
    setLoading(true);
    setError(null);
    setResponse(null);

    try {
      const apiResponse = await fetch('http://localhost:8000/query', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          query: query,
          top_k: topK,
          stream: useStreaming,
          compression: 'gzip',
        }),
      });

      if (!apiResponse.ok) {
        throw new Error(`API error: ${apiResponse.status} ${apiResponse.statusText}`);
      }

      if (useStreaming) {
        // Handle streaming response
        const reader = apiResponse.body.getReader();
        const decoder = new TextDecoder();
        let streamedContent = '';

        while (true) {
          const { done, value } = await reader.read();
          if (done) break;

          streamedContent += decoder.decode(value, { stream: true });
          
          // Parse JSON lines and update state
          const lines = streamedContent.split('\n');
          for (let i = 0; i < lines.length - 1; i++) {
            try {
              const chunk = JSON.parse(lines[i]);
              if (chunk.type === 'metadata') {
                setResponse({
                  query: chunk.query,
                  sources: chunk.sources,
                  confidence: chunk.confidence,
                  answer: '',
                  search_strategy: 'streaming',
                  routing_type: 'stream',
                  latency_ms: 0,
                });
              } else if (chunk.type === 'content') {
                setResponse(prev => prev ? {
                  ...prev,
                  answer: (prev.answer || '') + chunk.chunk,
                } : null);
              }
            } catch (e) {
              // Skip parsing errors
            }
          }
          streamedContent = lines[lines.length - 1];
        }
      } else {
        // Handle regular response
        const data = await apiResponse.json();
        setResponse(data);
      }
    } catch (err) {
      setError(err.message || 'Failed to process query. Is the backend running?');
      console.error('Error:', err);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="app">
      <header className="app-header">
        <div className="header-content">
          <h1>🤖 Insurance Portal AI</h1>
          <p>Intelligent Query Assistant powered by RAG</p>
          <div className={`api-status ${apiHealth ? 'healthy' : 'unhealthy'}`}>
            <span className="status-indicator"></span>
            {apiHealth ? 'Backend Connected' : 'Backend Disconnected'}
          </div>
        </div>
      </header>

      <main className="app-main">
        <div className="container">
          <section className="query-section">
            <QueryForm onSubmit={handleQuery} disabled={!apiHealth || loading} />
          </section>

          {loading && <LoadingSpinner />}

          {error && (
            <div className="error-message">
              <strong>Error:</strong> {error}
            </div>
          )}

          {response && <ResponseDisplay response={response} />}

          {!response && !loading && !error && (
            <div className="empty-state">
              <h2>Welcome to Insurance Portal AI</h2>
              <p>Ask any questions about insurance coverage, policies, claims, and more.</p>
              <div className="example-queries">
                <h3>Example Queries:</h3>
                <ul>
                  <li>What insurance plans do you offer?</li>
                  <li>How do I file a claim?</li>
                  <li>What is covered under health insurance?</li>
                  <li>How much does life insurance cost?</li>
                </ul>
              </div>
            </div>
          )}
        </div>
      </main>

      <footer className="app-footer">
        <p>&copy; 2026 Insurance Portal. Powered by FastAPI + RAG.</p>
      </footer>
    </div>
  );
}

export default App;
