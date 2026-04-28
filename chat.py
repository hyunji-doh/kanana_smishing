"""
Kanana-o 채팅 UI
실행: python chat.py  →  http://localhost:8001
"""
from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse, StreamingResponse
from pydantic import BaseModel
import kanana_client
import json

app = FastAPI()


class ChatRequest(BaseModel):
    messages: list[dict]


@app.post("/api/chat")
async def api_chat(req: ChatRequest):
    reply = kanana_client.chat(req.messages, temperature=0.7)
    return {"reply": reply}


@app.get("/", response_class=HTMLResponse)
async def index():
    return r"""<!DOCTYPE html>
<html lang="ko">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Kanana-o Chat</title>
<style>
  * { box-sizing: border-box; margin: 0; padding: 0; }
  body {
    font-family: 'Segoe UI', sans-serif;
    background: #f0f2f5;
    height: 100vh;
    display: flex;
    flex-direction: column;
    align-items: center;
  }
  .topbar {
    width: 100%;
    background: #3A1C8A;
    color: white;
    padding: 14px 24px;
    font-size: 16px;
    font-weight: 600;
    display: flex;
    align-items: center;
    gap: 10px;
  }
  .topbar span { opacity: 0.75; font-size: 12px; font-weight: 400; }
  .chat-wrap {
    width: 100%;
    max-width: 760px;
    flex: 1;
    display: flex;
    flex-direction: column;
    padding: 16px;
    gap: 0;
    overflow: hidden;
  }
  #messages {
    flex: 1;
    overflow-y: auto;
    display: flex;
    flex-direction: column;
    gap: 12px;
    padding-bottom: 8px;
  }
  .msg {
    display: flex;
    flex-direction: column;
    max-width: 72%;
  }
  .msg.user { align-self: flex-end; align-items: flex-end; }
  .msg.assistant { align-self: flex-start; align-items: flex-start; }
  .bubble {
    padding: 11px 15px;
    border-radius: 18px;
    font-size: 14px;
    line-height: 1.65;
    white-space: pre-wrap;
    word-break: break-word;
  }
  .msg.user .bubble {
    background: #3A1C8A;
    color: white;
    border-bottom-right-radius: 4px;
  }
  .msg.assistant .bubble {
    background: white;
    color: #222;
    border-bottom-left-radius: 4px;
    box-shadow: 0 1px 4px rgba(0,0,0,0.08);
  }
  .msg-time {
    font-size: 11px;
    color: #aaa;
    margin-top: 3px;
    padding: 0 4px;
  }
  .typing .bubble {
    background: white;
    box-shadow: 0 1px 4px rgba(0,0,0,0.08);
    border-bottom-left-radius: 4px;
  }
  .dots { display: inline-flex; gap: 4px; align-items: center; height: 20px; }
  .dot {
    width: 7px; height: 7px;
    background: #bbb; border-radius: 50%;
    animation: bounce 1.2s infinite;
  }
  .dot:nth-child(2) { animation-delay: 0.2s; }
  .dot:nth-child(3) { animation-delay: 0.4s; }
  @keyframes bounce {
    0%, 60%, 100% { transform: translateY(0); }
    30% { transform: translateY(-5px); }
  }
  .input-row {
    display: flex;
    gap: 8px;
    margin-top: 12px;
    background: white;
    border-radius: 28px;
    padding: 6px 6px 6px 18px;
    box-shadow: 0 2px 10px rgba(0,0,0,0.1);
  }
  #userInput {
    flex: 1;
    border: none;
    outline: none;
    font-size: 14px;
    font-family: inherit;
    background: transparent;
    resize: none;
    max-height: 120px;
    line-height: 1.5;
    padding: 6px 0;
  }
  #sendBtn {
    width: 40px; height: 40px;
    background: #3A1C8A;
    border: none;
    border-radius: 50%;
    cursor: pointer;
    display: flex; align-items: center; justify-content: center;
    flex-shrink: 0;
    transition: background 0.15s;
    align-self: flex-end;
  }
  #sendBtn:hover { background: #2d1570; }
  #sendBtn:disabled { background: #ccc; cursor: not-allowed; }
  #sendBtn svg { fill: white; }
  .clear-btn {
    align-self: flex-end;
    background: none;
    border: 1px solid #ddd;
    border-radius: 12px;
    padding: 4px 12px;
    font-size: 12px;
    color: #888;
    cursor: pointer;
    margin-bottom: 6px;
  }
  .clear-btn:hover { color: #e74c3c; border-color: #e74c3c; }
</style>
</head>
<body>

<div class="topbar">
  Kanana-o
  <span>멀티모달 AI · 카카오</span>
</div>

<div class="chat-wrap">
  <button class="clear-btn" onclick="clearChat()">대화 초기화</button>
  <div id="messages"></div>
  <div class="input-row">
    <textarea id="userInput" rows="1" placeholder="메시지를 입력하세요…" oninput="autoResize(this)"></textarea>
    <button id="sendBtn" onclick="send()">
      <svg width="18" height="18" viewBox="0 0 24 24"><path d="M2 21l21-9L2 3v7l15 2-15 2z"/></svg>
    </button>
  </div>
</div>

<script>
let history = [];

function autoResize(el) {
  el.style.height = 'auto';
  el.style.height = Math.min(el.scrollHeight, 120) + 'px';
}

function now() {
  return new Date().toLocaleTimeString('ko-KR', { hour: '2-digit', minute: '2-digit' });
}

function addMessage(role, text) {
  const wrap = document.getElementById('messages');
  const div = document.createElement('div');
  div.className = `msg ${role}`;
  div.innerHTML = `<div class="bubble">${escHtml(text)}</div><div class="msg-time">${now()}</div>`;
  wrap.appendChild(div);
  wrap.scrollTop = wrap.scrollHeight;
  return div;
}

function showTyping() {
  const wrap = document.getElementById('messages');
  const div = document.createElement('div');
  div.className = 'msg assistant typing';
  div.id = 'typing';
  div.innerHTML = `<div class="bubble"><div class="dots"><div class="dot"></div><div class="dot"></div><div class="dot"></div></div></div>`;
  wrap.appendChild(div);
  wrap.scrollTop = wrap.scrollHeight;
}

function removeTyping() {
  const t = document.getElementById('typing');
  if (t) t.remove();
}

function escHtml(s) {
  return s.replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;').replace(/\n/g,'<br>');
}

async function send() {
  const input = document.getElementById('userInput');
  const text = input.value.trim();
  if (!text) return;

  input.value = '';
  input.style.height = 'auto';
  document.getElementById('sendBtn').disabled = true;

  addMessage('user', text);
  history.push({ role: 'user', content: text });

  showTyping();

  try {
    const res = await fetch('/api/chat', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ messages: history }),
    });
    const data = await res.json();
    removeTyping();
    addMessage('assistant', data.reply);
    history.push({ role: 'assistant', content: data.reply });
  } catch (e) {
    removeTyping();
    addMessage('assistant', '오류가 발생했습니다: ' + e.message);
  }

  document.getElementById('sendBtn').disabled = false;
  document.getElementById('userInput').focus();
}

function clearChat() {
  history = [];
  document.getElementById('messages').innerHTML = '';
}

document.getElementById('userInput').addEventListener('keydown', e => {
  if (e.key === 'Enter' && !e.shiftKey) { e.preventDefault(); send(); }
});
</script>
</body>
</html>
"""


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("chat:app", host="0.0.0.0", port=8001, reload=True)
