import React from 'react';
import '../styles/ResponseDisplay.css';

function ResponseDisplay({ response }) {
  return (
    <div className="response-display">
      <div className="response-section">
        <h2>Answer</h2>
        <div className="answer-content">
          <p>{response.answer}</p>
        </div>
        <div className="confidence-indicator">
          <span className="confidence-label">Confidence:</span>
          <div className="confidence-bar">
            <div
              className="confidence-fill"
              style={{
                width: `${response.confidence * 100}%`,
                backgroundColor: `rgb(${255 - response.confidence * 255}, ${response.confidence * 255}, 100)`
              }}
            ></div>
          </div>
          <span className="confidence-value">{(response.confidence * 100).toFixed(1)}%</span>
        </div>
      </div>

      {/* Metadata Section */}
      {response.latency_ms && (
        <div className="response-section metadata-section">
          <h3>Performance Metrics</h3>
          <div className="metrics-grid">
            <div className="metric">
              <span className="metric-label">Latency:</span>
              <span className="metric-value">{response.latency_ms.toFixed(0)}ms</span>
            </div>
            {response.search_strategy && (
              <div className="metric">
                <span className="metric-label">Search Strategy:</span>
                <span className="metric-value">{response.search_strategy}</span>
              </div>
            )}
            {response.routing_type && (
              <div className="metric">
                <span className="metric-label">Routing Type:</span>
                <span className="metric-value">{response.routing_type}</span>
              </div>
            )}
          </div>
        </div>
      )}

      {response.sources && response.sources.length > 0 && (
        <div className="response-section">
          <h2>Sources</h2>
          <ul className="sources-list">
            {response.sources.map((source, index) => (
              <li key={index} className="source-item">
                <span className="source-number">{index + 1}</span>
                <span className="source-text">{source}</span>
              </li>
            ))}
          </ul>
        </div>
      )}
    </div>
  );
}

export default ResponseDisplay;
