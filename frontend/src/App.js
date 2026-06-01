import React from 'react';

function App() {
  return (
    <div style={{ padding: '40px', textAlign: 'center' }}>
      <h1>🛒 在线商城系统</h1>
      <p>Frontend placeholder - React app will be implemented here</p>
      <div style={{ marginTop: '20px' }}>
        <h2>API Endpoints</h2>
        <ul style={{ listStyle: 'none', padding: 0 }}>
          <li>📚 API Docs: <a href="http://localhost:8000/docs">http://localhost:8000/docs</a></li>
          <li>🔐 Auth: POST /api/auth/register, /api/auth/login</li>
          <li>📦 Products: GET /api/products</li>
          <li>🛒 Cart: GET /api/cart</li>
          <li>📋 Orders: GET /api/orders</li>
          <li>🤖 AI: POST /api/ai/recommend, /api/ai/chat</li>
        </ul>
      </div>
    </div>
  );
}

export default App;
