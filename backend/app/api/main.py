"""FastAPI application entry point."""
from __future__ import annotations
from pathlib import Path

from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.responses import HTMLResponse

load_dotenv(Path(__file__).resolve().parents[2] / ".env")

from app.api.routes import router  # noqa: E402  (import after load_dotenv)

app = FastAPI(title="Study Assistant — Socratic Tutor")
app.include_router(router)

_HTML = """<!DOCTYPE html>
<html lang="zh">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>AI 学习助手</title>
<style>
*{box-sizing:border-box;margin:0;padding:0}
body{font-family:-apple-system,sans-serif;background:#f0f2f5;display:flex;
     justify-content:center;min-height:100vh}
#app{width:100%;max-width:480px;display:flex;flex-direction:column;
     min-height:100vh;background:#fff}
/* ── setup form ── */
#setup{padding:16px;border-bottom:1px solid #e0e0e0}
#setup h1{font-size:18px;margin-bottom:12px;color:#1a1a2e}
#setup label{display:block;font-size:13px;color:#555;margin-top:10px;margin-bottom:3px}
#setup input,#setup select,#setup textarea{width:100%;padding:8px 10px;border:1px solid #ccc;
  border-radius:8px;font-size:15px;font-family:inherit}
#setup textarea{height:80px;resize:vertical}
#start-btn{margin-top:14px;width:100%;padding:12px;background:#4f46e5;color:#fff;
  border:none;border-radius:10px;font-size:16px;font-weight:600;cursor:pointer}
#start-btn:disabled{background:#a5b4fc}
/* ── chat area ── */
#chat{flex:1;overflow-y:auto;padding:12px;display:none;flex-direction:column;gap:10px}
.bubble{max-width:82%;padding:10px 13px;border-radius:16px;font-size:15px;
        line-height:1.55;word-break:break-word;white-space:pre-wrap}
.tutor{align-self:flex-start;background:#f3f4f6;border-bottom-left-radius:4px}
.student{align-self:flex-end;background:#4f46e5;color:#fff;border-bottom-right-radius:4px}
.tutor.hint{background:#fef9c3}
.tutor.done{background:#dcfce7}
/* ── input bar ── */
#input-bar{padding:10px 12px;border-top:1px solid #e0e0e0;display:none;
           flex-direction:row;gap:8px;align-items:flex-end}
#msg{flex:1;padding:9px 12px;border:1px solid #ccc;border-radius:20px;
     font-size:15px;font-family:inherit;resize:none;max-height:120px;overflow-y:auto}
#mic-btn{padding:9px 12px;background:#f3f4f6;border:1px solid #ccc;border-radius:20px;
         font-size:18px;cursor:pointer;flex-shrink:0;transition:background 0.2s}
#mic-btn.recording{background:#fee2e2;border-color:#f87171;animation:pulse 1s infinite}
@keyframes pulse{0%,100%{opacity:1}50%{opacity:0.6}}
#send-btn{padding:9px 16px;background:#4f46e5;color:#fff;border:none;
          border-radius:20px;font-size:15px;cursor:pointer;white-space:nowrap}
#send-btn:disabled{background:#a5b4fc}
#status{font-size:13px;color:#888;padding:4px 12px 8px;text-align:center;display:none}
</style>
</head>
<body>
<div id="app">
  <!-- 题目录入 -->
  <div id="setup">
    <h1>📚 AI 苏格拉底家教</h1>
    <label>科目</label>
    <select id="subject">
      <option value="math">数学</option>
      <option value="physics">物理</option>
    </select>
    <label>年级</label>
    <select id="grade">
      <option value="primary_4">小学四年级</option>
      <option value="primary_5">小学五年级</option>
      <option value="primary_6">小学六年级</option>
      <option value="junior_1">初中一年级</option>
      <option value="junior_2">初中二年级</option>
      <option value="junior_3">初中三年级</option>
      <option value="senior_1">高中一年级</option>
      <option value="senior_2">高中二年级</option>
      <option value="senior_3">高中三年级</option>
    </select>
    <label>题目</label>
    <textarea id="statement" placeholder="在这里输入题目，例如：某数加 5 等于 12，求该数。"></textarea>
    <label>参考答案（AI 内部使用，不会直接告诉你）</label>
    <input id="answer" type="text" placeholder="例如：7">
    <button id="start-btn" onclick="startSession()">开始答题</button>
  </div>
  <!-- 对话区 -->
  <div id="chat"></div>
  <div id="status"></div>
  <!-- 输入栏 -->
  <div id="input-bar">
    <textarea id="msg" placeholder="输入你的想法…" rows="1"
      oninput="autoResize(this)" onkeydown="handleKey(event)"></textarea>
    <button id="mic-btn" onclick="toggleRecording()" title="按住说话">🎤</button>
    <button id="send-btn" onclick="sendTurn()">发送</button>
  </div>
</div>
<script>
let sessionId = null;
let mediaRecorder = null;
let audioChunks = [];

function autoResize(el){
  el.style.height='auto';
  el.style.height=Math.min(el.scrollHeight,120)+'px';
}

function handleKey(e){
  if(e.key==='Enter'&&!e.shiftKey){e.preventDefault();sendTurn();}
}

function addBubble(text, role, tool){
  const chat=document.getElementById('chat');
  const d=document.createElement('div');
  d.className='bubble '+role;
  if(tool==='hint') d.classList.add('hint');
  if(tool==='summarize_at_end') d.classList.add('done');
  d.textContent=text;
  chat.appendChild(d);
  chat.scrollTop=chat.scrollHeight;
}

function setStatus(msg){
  const s=document.getElementById('status');
  s.style.display=msg?'block':'none';
  s.textContent=msg;
}

async function startSession(){
  const subject=document.getElementById('subject').value;
  const grade=document.getElementById('grade').value;
  const statement=document.getElementById('statement').value.trim();
  const answer=document.getElementById('answer').value.trim();
  if(!statement||!answer){alert('请填写题目和参考答案');return;}

  document.getElementById('start-btn').disabled=true;
  setStatus('AI 老师正在准备第一个问题…');
  try{
    const res=await fetch('/api/session/start',{
      method:'POST',
      headers:{'Content-Type':'application/json'},
      body:JSON.stringify({subject,grade,statement,reference_answer:answer,knowledge_points:[]})
    });
    if(!res.ok) throw new Error(await res.text());
    const data=await res.json();
    sessionId=data.session_id;

    document.getElementById('setup').style.display='none';
    const chat=document.getElementById('chat');
    chat.style.display='flex';
    document.getElementById('input-bar').style.display='flex';
    setStatus('');

    addBubble(data.turn.display_text,'tutor',data.turn.tool);
    if(data.turn.completed) finishSession();
  }catch(e){
    setStatus('启动失败：'+e.message);
    document.getElementById('start-btn').disabled=false;
  }
}

async function sendTurn(){
  const msgEl=document.getElementById('msg');
  const text=msgEl.value.trim();
  if(!text||!sessionId) return;
  msgEl.value='';
  msgEl.style.height='auto';
  document.getElementById('send-btn').disabled=true;

  addBubble(text,'student',null);
  setStatus('AI 老师思考中…');

  try{
    const res=await fetch('/api/session/turn',{
      method:'POST',
      headers:{'Content-Type':'application/json'},
      body:JSON.stringify({session_id:sessionId,message:text})
    });
    if(!res.ok) throw new Error(await res.text());
    const data=await res.json();
    setStatus('');
    addBubble(data.display_text,'tutor',data.tool);
    if(data.completed) finishSession();
  }catch(e){
    setStatus('出错了：'+e.message);
  }finally{
    document.getElementById('send-btn').disabled=false;
    document.getElementById('msg').focus();
  }
}

function finishSession(){
  document.getElementById('msg').disabled=true;
  document.getElementById('send-btn').disabled=true;
  document.getElementById('mic-btn').disabled=true;
  setStatus('✅ 这道题完成了！刷新页面可以换一道题。');
}

async function toggleRecording(){
  const btn=document.getElementById('mic-btn');
  if(mediaRecorder && mediaRecorder.state==='recording'){
    mediaRecorder.stop();
    return;
  }
  // start recording
  let stream;
  try{
    stream=await navigator.mediaDevices.getUserMedia({audio:true});
  }catch(e){
    setStatus('无法访问麦克风：'+e.message);
    return;
  }
  // prefer ogg-opus (aliyun NLS native); fallback to webm-opus
  const mimeType = MediaRecorder.isTypeSupported('audio/ogg;codecs=opus')
    ? 'audio/ogg;codecs=opus'
    : MediaRecorder.isTypeSupported('audio/webm;codecs=opus')
      ? 'audio/webm;codecs=opus' : 'audio/webm';
  audioChunks=[];
  mediaRecorder=new MediaRecorder(stream,{mimeType});
  mediaRecorder.ondataavailable=e=>{ if(e.data.size>0) audioChunks.push(e.data); };
  mediaRecorder.onstop=async()=>{
    btn.classList.remove('recording');
    btn.textContent='🎤';
    stream.getTracks().forEach(t=>t.stop());
    setStatus('识别中…');
    const blob=new Blob(audioChunks,{type:mimeType});
    const fd=new FormData();
    fd.append('file', blob, 'audio.webm');
    try{
      const res=await fetch('/api/asr',{method:'POST',body:fd});
      if(!res.ok) throw new Error(await res.text());
      const data=await res.json();
      setStatus('');
      if(data.text){
        document.getElementById('msg').value=data.text;
        autoResize(document.getElementById('msg'));
      } else {
        setStatus('未能识别到内容，请重试');
      }
    }catch(e){
      setStatus('识别失败：'+e.message);
    }
  };
  mediaRecorder.start();
  btn.classList.add('recording');
  btn.textContent='⏹';
  setStatus('录音中… 说完后点击停止');
}
</script>
</body>
</html>"""


@app.get("/", response_class=HTMLResponse)
async def index() -> str:
    return _HTML
