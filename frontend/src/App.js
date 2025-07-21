import React, { useState } from 'react';
import './App.css';

function App() {
  const [topic, setTopic] = useState('');
  const [loading, setLoading] = useState(false);
  const [blob, setBlob] = useState(null);
  const [fileName, setFileName] = useState('');

  const handleInputChange = (e) => {
    setTopic(e.target.value);
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!topic.trim()) return;

    setLoading(true);
    setBlob(null);
    setFileName('');

    try {
      const response = await fetch('http://localhost:8000/generate-content', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/x-www-form-urlencoded',
        },
        body: new URLSearchParams({ topic }),
      });

      if (!response.ok) throw new Error('Failed to generate document');

      const responseBlob = await response.blob();

      const disposition = response.headers.get('Content-Disposition');
      let name = 'generated_document.md';
      if (disposition && disposition.includes('filename=')) {
        name = disposition.split('filename=')[1].trim().replace(/^.*[\\/]/, '').replace(/"/g, '');
      }

      setBlob(responseBlob);
      setFileName(name);
    } catch (err) {
      alert('Error: ' + err.message);
    } finally {
      setLoading(false);
    }
  };

  const handleDownload = () => {
    if (!blob) return;

    const url = window.URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = fileName || 'generated_document.md';
    document.body.appendChild(a);
    a.click();
    a.remove();
    window.URL.revokeObjectURL(url);
  };

  return (
    <div className="App" style={{ minHeight: '100vh', display: 'flex', flexDirection: 'column', justifyContent: 'center', alignItems: 'center', background: '#f5f6fa' }}>
      <h2>Agentic AI README Generator</h2>
      <form onSubmit={handleSubmit} style={{ display: 'flex', alignItems: 'center', gap: '10px', marginBottom: '20px' }}>
        <input
          type="text"
          value={topic}
          onChange={handleInputChange}
          placeholder="Enter topic"
          style={{ padding: '10px', fontSize: '16px', borderRadius: '4px', border: '1px solid #ccc', width: '300px' }}
          disabled={loading}
        />
        <button
          type="submit"
          style={{ padding: '10px 16px', fontSize: '16px', borderRadius: '4px', border: 'none', background: '#007bff', color: '#fff', cursor: 'pointer' }}
          disabled={loading}
        >
          {loading ? 'Generating...' : 'Generate'}
        </button>
      </form>
      <button
        onClick={handleDownload}
        disabled={!blob}
        style={{ padding: '10px 24px', fontSize: '16px', borderRadius: '4px', border: 'none', background: blob ? '#28a745' : '#ccc', color: '#fff', cursor: blob ? 'pointer' : 'not-allowed' }}
      >
        Download README.md
      </button>
    </div>
  );
}

export default App;
