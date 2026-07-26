import React, { useState } from 'react';
import axios from 'axios';
import { ShieldAlert, Send, Bot, User, Activity } from 'lucide-react';

function App() {
  const [messages, setMessages] = useState([
    {
      sender: 'bot',
      text: 'LSTM Sequence Engine Online. Paste a raw access log (JSON format) to analyze for anomalies.',
      isInitial: true
    }
  ]);
  
  // A default anomalous log to test with
  const [inputLog, setInputLog] = useState(
    '{\n  "entity_type": "user",\n  "source_ip": "192.168.1.99",\n  "geo_location": "Moscow",\n  "resource_accessed": "port:22",\n  "auth_method": "password",\n  "session_duration": 0.0,\n  "command_sequence": "FAILED_AUTH",\n  "device_fingerprint": "unknown-mac-address"\n}'
  );
  const [loading, setLoading] = useState(false);

  const handleAnalyze = async () => {
    if (!inputLog.trim()) return;

    const newMessages = [...messages, { sender: 'user', text: inputLog }];
    setMessages(newMessages);
    setLoading(true);

    try {
      const logJson = JSON.parse(inputLog);
      const response = await axios.post('http://localhost:5000/api/analyze', logJson);
      
      if (response.data.status === 'success') {
        const { prediction, confidence, explanation } = response.data;
        const isAnomaly = prediction.toLowerCase() !== 'normal';
        
        setMessages(prev => [...prev, {
          sender: 'bot',
          prediction,
          confidence,
          explanation,
          isAnomaly
        }]);
      } else {
        setMessages(prev => [...prev, { sender: 'bot', text: `API Error: ${response.data.message}` }]);
      }
    } catch (err) {
      setMessages(prev => [...prev, { sender: 'bot', text: "Invalid JSON format. Please check your syntax." }]);
    }
    
    setLoading(false);
    setInputLog('');
  };

  return (
    <div style={{ display: 'flex', flexDirection: 'column', height: '100vh', backgroundColor: '#f1f5f9', fontFamily: 'system-ui, sans-serif' }}>
      
      <header style={{ backgroundColor: '#0f172a', padding: '16px 24px', color: 'white', display: 'flex', alignItems: 'center', gap: '12px', boxShadow: '0 4px 6px -1px rgba(0,0,0,0.1)' }}>
        <ShieldAlert size={28} color="#38bdf8" />
        <h1 style={{ margin: 0, fontSize: '20px', fontWeight: '600' }}>ThreatVision | AI Log Analyzer</h1>
        <div style={{ marginLeft: 'auto', display: 'flex', alignItems: 'center', gap: '6px', fontSize: '14px', color: '#10b981' }}>
          <Activity size={16} /> LSTM Engine Active
        </div>
      </header>

      <main style={{ flex: 1, overflowY: 'auto', padding: '24px', display: 'flex', flexDirection: 'column', gap: '16px' }}>
        {messages.map((msg, idx) => (
          <div key={idx} style={{ 
            display: 'flex', gap: '12px', alignSelf: msg.sender === 'user' ? 'flex-end' : 'flex-start', maxWidth: '75%'
          }}>
            {msg.sender === 'bot' && <div style={{ backgroundColor: '#e2e8f0', borderRadius: '50%', padding: '8px', height: 'fit-content' }}><Bot size={20} color="#0f172a"/></div>}
            
            <div style={{ 
              backgroundColor: msg.sender === 'user' ? '#3b82f6' : 'white', 
              color: msg.sender === 'user' ? 'white' : '#0f172a',
              padding: '16px', borderRadius: '12px',
              border: msg.sender === 'bot' ? '1px solid #cbd5e1' : 'none',
              boxShadow: '0 1px 2px rgba(0,0,0,0.05)'
            }}>
              {msg.isInitial || msg.sender === 'user' ? (
                <pre style={{ margin: 0, whiteSpace: 'pre-wrap', fontFamily: msg.sender === 'user' ? 'monospace' : 'inherit', fontSize: '14px' }}>
                  {msg.text}
                </pre>
              ) : (
                <div>
                  <h4 style={{ margin: '0 0 12px 0', display: 'flex', alignItems: 'center', gap: '8px', color: msg.isAnomaly ? '#ef4444' : '#10b981' }}>
                    {msg.isAnomaly ? <ShieldAlert size={20}/> : <Activity size={20}/>}
                    {msg.isAnomaly ? 'Threat Detected' : 'Behavior Normal'}
                  </h4>
                  <div style={{ marginBottom: '8px', fontSize: '15px' }}><strong>Classification:</strong> {msg.prediction}</div>
                  <div style={{ marginBottom: '8px', fontSize: '15px' }}>
                    <strong>Confidence Score:</strong> 
                    <span style={{ marginLeft: '8px', padding: '4px 8px', borderRadius: '4px', backgroundColor: '#f1f5f9', fontWeight: 'bold' }}>
                      {msg.confidence}%
                    </span>
                  </div>
                  <div style={{ color: '#475569', fontSize: '14px', marginTop: '16px', borderTop: '1px solid #e2e8f0', paddingTop: '12px', lineHeight: '1.5' }}>
                    <strong>Explainability Layer:</strong> {msg.explanation}
                  </div>
                </div>
              )}
            </div>

            {msg.sender === 'user' && <div style={{ backgroundColor: '#3b82f6', borderRadius: '50%', padding: '8px', height: 'fit-content' }}><User size={20} color="white"/></div>}
          </div>
        ))}
        {loading && <div style={{ color: '#64748b', fontSize: '14px', marginLeft: '48px', fontStyle: 'italic' }}>LSTM Engine is analyzing sequence...</div>}
      </main>

      <footer style={{ padding: '20px', backgroundColor: 'white', borderTop: '1px solid #e2e8f0' }}>
        <div style={{ display: 'flex', gap: '12px', maxWidth: '1000px', margin: '0 auto' }}>
          <textarea 
            value={inputLog}
            onChange={(e) => setInputLog(e.target.value)}
            placeholder="Paste JSON access log here..."
            style={{ flex: 1, height: '120px', padding: '12px', borderRadius: '8px', border: '1px solid #cbd5e1', fontFamily: 'monospace', resize: 'none', outline: 'none' }}
          />
          <button 
            onClick={handleAnalyze}
            disabled={loading}
            style={{ 
              backgroundColor: '#0f172a', color: 'white', border: 'none', borderRadius: '8px', padding: '0 32px', 
              cursor: loading ? 'not-allowed' : 'pointer', display: 'flex', alignItems: 'center', gap: '8px', fontWeight: '600' 
            }}
          >
            <Send size={18} /> Analyze Log
          </button>
        </div>
      </footer>
    </div>
  );
}

export default App;