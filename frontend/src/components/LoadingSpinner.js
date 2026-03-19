import React from 'react';
import '../styles/LoadingSpinner.css';

function LoadingSpinner() {
  return (
    <div className="loading-spinner-container">
      <div className="spinner"></div>
      <p>Processing your query...</p>
    </div>
  );
}

export default LoadingSpinner;
