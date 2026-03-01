const express = require('express');
const app = express();

// CORSヘッダーを全リクエストに手動付与
app.use((req, res, next) => {
  res.header('Access-Control-Allow-Origin', '*');
  res.header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS');
  res.header('Access-Control-Allow-Headers', 'Content-Type');
  if (req.method === 'OPTIONS') return res.sendStatus(200);
  next();
});

app.use(express.json());

app.get('/health', (req, res) => res.json({ ok: true }));

app.post('/api/chat', async (req, res) => {
  const { messages, system } = req.body;
  const body = { model: 'claude-haiku-4-5-20251001', max_tokens: 1000, messages };
  if (system) body.system = system;

  try {
    const response = await fetch('https://api.anthropic.com/v1/messages', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'x-api-key': process.env.ANTHROPIC_API_KEY,
        'anthropic-version': '2023-06-01'
      },
      body: JSON.stringify(body)
    });
    const data = await response.json();
    if (!response.ok) return res.status(500).json({ error: data.error?.message || 'API error' });
    const text = (data.content || []).filter(b => b.type === 'text').map(b => b.text).join('');
    res.json({ text });
  } catch (err) {
    res.status(500).json({ error: err.message });
  }
});

const PORT = process.env.PORT || 3000;
app.listen(PORT, () => console.log('listening on ' + PORT));
