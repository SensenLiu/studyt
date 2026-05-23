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
/* ── bottom nav ── */
#nav{display:flex;border-top:1px solid #e0e0e0;background:#fff;flex-shrink:0}
.nav-btn{flex:1;padding:10px 0 6px;border:none;background:none;cursor:pointer;
         font-size:11px;color:#888;display:flex;flex-direction:column;align-items:center;gap:2px}
.nav-btn .icon{font-size:22px;line-height:1}
.nav-btn.active{color:#4f46e5}
.nav-btn .badge{background:#ef4444;color:#fff;border-radius:10px;padding:1px 5px;
                font-size:10px;position:absolute;margin-left:14px;margin-top:-2px}
/* ── pages ── */
.page{display:none;flex:1;flex-direction:column;overflow:hidden}
.page.active{display:flex}
/* ── setup form ── */
#setup{padding:16px;overflow-y:auto;flex:1}
#setup h1{font-size:18px;margin-bottom:12px;color:#1a1a2e}
#setup label{display:block;font-size:13px;color:#555;margin-top:10px;margin-bottom:3px}
#setup input,#setup select,#setup textarea{width:100%;padding:8px 10px;border:1px solid #ccc;
  border-radius:8px;font-size:15px;font-family:inherit}
#setup textarea{height:80px;resize:vertical}
#start-btn{margin-top:14px;width:100%;padding:12px;background:#4f46e5;color:#fff;
  border:none;border-radius:10px;font-size:16px;font-weight:600;cursor:pointer}
#start-btn:disabled{background:#a5b4fc}
/* ── chat area ── */
#chat{flex:1;overflow-y:auto;padding:12px;flex-direction:column;gap:10px}
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
/* ── mistake book page ── */
#mistakes-page{padding:0;overflow:hidden}
#mistakes-header{padding:14px 16px;border-bottom:1px solid #e0e0e0;
                 display:flex;justify-content:space-between;align-items:center}
#mistakes-header h2{font-size:17px;color:#1a1a2e}
#mistakes-filter{display:flex;gap:6px;padding:10px 16px;border-bottom:1px solid #e8e8e8}
#mistakes-filter button{padding:5px 12px;border-radius:16px;border:1px solid #ccc;
  background:#fff;font-size:13px;cursor:pointer}
#mistakes-filter button.active{background:#4f46e5;color:#fff;border-color:#4f46e5}
#mistakes-list{flex:1;overflow-y:auto;padding:8px 0}
.mistake-card{padding:12px 16px;border-bottom:1px solid #f0f0f0}
.mistake-card .stmt{font-size:14px;color:#222;margin-bottom:6px;line-height:1.5}
.mistake-card .meta{font-size:12px;color:#888;margin-bottom:8px}
.mistake-card .actions{display:flex;gap:8px}
.mistake-card .actions button{padding:4px 10px;border-radius:6px;border:none;
  font-size:12px;cursor:pointer}
.btn-review{background:#4f46e5;color:#fff}
.btn-practice{background:#f3f4f6;color:#333}
.btn-del{background:#fee2e2;color:#ef4444}
#add-mistake-btn{padding:8px 14px;background:#4f46e5;color:#fff;border:none;
  border-radius:8px;font-size:13px;cursor:pointer}
/* ── photo upload for mistake book ── */
#photo-add-bar{padding:10px 16px;border-top:1px solid #e0e0e0;display:flex;gap:8px;align-items:center}
</style>
</head>
<body>
<div id="app">
  <!-- ══ 答题页 ══ -->
  <div id="page-practice" class="page active" style="flex-direction:column">
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
      <div style="display:flex;gap:8px;margin-top:12px">
        <button onclick="pickRandom()" id="random-btn"
          style="flex:1;padding:9px;background:#f3f4f6;border:1px solid #ccc;
                 border-radius:8px;font-size:14px;cursor:pointer">
          🎲 随机出题
        </button>
        <label style="flex:1;padding:9px;background:#f3f4f6;border:1px solid #ccc;
                      border-radius:8px;font-size:14px;cursor:pointer;text-align:center">
          📷 拍题识别
          <input type="file" id="ocr-input" accept="image/*" capture="environment"
            style="display:none" onchange="handleOcrImage(this)">
        </label>
      </div>
      <div id="ocr-status" style="font-size:12px;margin-top:6px;display:none"></div>
      <label style="margin-top:10px">题目</label>
      <textarea id="statement" placeholder="随机出题或拍照后自动填入，也可手动输入" rows="3"></textarea>
      <button id="start-btn" onclick="startSession()" style="margin-top:14px">开始答题</button>
    </div>
    <!-- 对话区 -->
    <div id="chat" style="flex:1;overflow-y:auto;padding:12px;flex-direction:column;gap:10px"></div>
    <div id="status"></div>
    <!-- 加入错题集按钮（答题中显示） -->
    <div id="add-to-mistakes-bar" style="display:none;padding:8px 12px;border-top:1px solid #e0e0e0">
      <button onclick="addCurrentToMistakes()"
        style="width:100%;padding:8px;background:#fff;border:1px solid #f87171;
               color:#ef4444;border-radius:8px;font-size:13px;cursor:pointer">
        ➕ 加入错题集
      </button>
    </div>
    <!-- 输入栏 -->
    <div id="input-bar">
    <textarea id="msg" placeholder="输入你的想法…" rows="1"
      oninput="autoResize(this)" onkeydown="handleKey(event)"></textarea>
    <button id="mic-btn" onclick="toggleRecording()" title="按住说话">🎤</button>
    <button id="send-btn" onclick="sendTurn()">发送</button>
  </div>
  </div><!-- end page-practice -->

  <!-- ══ 错题集页 ══ -->
  <div id="page-mistakes" class="page" style="flex-direction:column;overflow:hidden">
    <div id="mistakes-header">
      <h2>📒 错题集</h2>
      <label id="add-mistake-btn">
        📷 拍题加入
        <input type="file" id="mistake-photo-input" accept="image/*" capture="environment"
          style="display:none" onchange="addMistakeFromPhoto(this)">
      </label>
    </div>
    <div id="mistakes-filter">
      <button class="active" onclick="loadMistakes(false, this)">全部</button>
      <button onclick="loadMistakes(true, this)">待复习</button>
    </div>
    <div id="mistakes-list" style="flex:1;overflow-y:auto;padding:8px 0"></div>
  </div>

  <!-- ══ 底部导航 ══ -->
  <div id="nav">
    <button class="nav-btn active" onclick="showPage('practice', this)">
      <span class="icon">✏️</span>答题
    </button>
    <button class="nav-btn" onclick="showPage('mistakes', this)" id="nav-mistakes">
      <span class="icon">📒</span>错题集
    </button>
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

async function pickRandom(){
  const subject = document.getElementById('subject').value;
  const grade = document.getElementById('grade').value;
  const btn = document.getElementById('random-btn');
  btn.disabled = true;
  btn.textContent = '⏳ 出题中…';
  const ocrStatus = document.getElementById('ocr-status');
  ocrStatus.style.display = 'none';
  try{
    const res = await fetch(`/api/questions/random?subject=${subject}&grade=${grade}`);
    if(!res.ok){
      const err = await res.json();
      throw new Error(err.detail || '无题目');
    }
    const q = await res.json();
    document.getElementById('statement').value = q.statement;
    autoResize(document.getElementById('statement'));
    ocrStatus.style.display = 'block';
    ocrStatus.style.color = '#16a34a';
    ocrStatus.textContent = `✅ 已出题（${q.knowledge_points.join('、')}）`;
  }catch(e){
    ocrStatus.style.display = 'block';
    ocrStatus.style.color = '#dc2626';
    ocrStatus.textContent = '❌ ' + e.message;
  }finally{
    btn.disabled = false;
    btn.textContent = '🎲 随机出题';
  }
}

async function handleOcrImage(input){
  const file = input.files[0];
  if(!file) return;
  const ocrStatus = document.getElementById('ocr-status');
  ocrStatus.style.display='block';
  ocrStatus.textContent='📷 识别中，请稍候…';
  document.getElementById('start-btn').disabled=true;
  const fd = new FormData();
  fd.append('file', file);
  try{
    const subject = document.getElementById('subject').value;
    const grade = document.getElementById('grade').value;
    const res = await fetch(`/api/ocr?subject=${subject}&grade=${grade}`, {method:'POST', body:fd});
    if(!res.ok) throw new Error(await res.text());
    const data = await res.json();
    document.getElementById('statement').value = data.statement;
    autoResize(document.getElementById('statement'));
    ocrStatus.style.color = data.needs_confirmation ? '#d97706' : '#16a34a';
    ocrStatus.textContent = data.needs_confirmation
      ? '⚠️ 识别结果还需确认，请先检查或修改题目再开始答题'
      : '✅ 识别完成，请确认题目后开始答题';
  }catch(e){
    ocrStatus.textContent = '❌ 识别失败：' + e.message;
    ocrStatus.style.color = '#dc2626';
  }finally{
    document.getElementById('start-btn').disabled=false;
    input.value='';
  }
}

async function startSession(){
  const subject=document.getElementById('subject').value;
  const grade=document.getElementById('grade').value;
  const statement=document.getElementById('statement').value.trim();
  if(!statement){alert('请填写题目');return;}

  document.getElementById('start-btn').disabled=true;
  setStatus('AI 老师正在准备第一个问题…');
  try{
    const res=await fetch('/api/session/start',{
      method:'POST',
      headers:{'Content-Type':'application/json'},
      body:JSON.stringify({subject,grade,statement,knowledge_points:[]})
    });
    if(!res.ok) throw new Error(await res.text());
    const data=await res.json();
    sessionId=data.session_id;

    document.getElementById('setup').style.display='none';
    const chat=document.getElementById('chat');
    chat.style.display='flex';
    document.getElementById('input-bar').style.display='flex';
    document.getElementById('add-to-mistakes-bar').style.display='block';
    setStatus('');
    updateDueBadge();

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
  setStatus('✅ 这道题完成了！点下方「答题」可换一道题。');
}

// ── 页面切换 ──
function showPage(name, btn){
  document.querySelectorAll('.page').forEach(p=>p.classList.remove('active'));
  document.querySelectorAll('.nav-btn').forEach(b=>b.classList.remove('active'));
  document.getElementById('page-'+name).classList.add('active');
  btn.classList.add('active');
  if(name==='mistakes') loadMistakes(false, document.querySelector('#mistakes-filter button'));
  if(name==='practice' && !sessionId){
    // reset to setup form
    document.getElementById('setup').style.display='';
    document.getElementById('chat').style.display='none';
    document.getElementById('input-bar').style.display='none';
    document.getElementById('add-to-mistakes-bar').style.display='none';
  }
}

// ── 错题集 ──
async function loadMistakes(dueOnly, btn){
  if(btn){
    document.querySelectorAll('#mistakes-filter button').forEach(b=>b.classList.remove('active'));
    btn.classList.add('active');
  }
  const res = await fetch('/api/mistakes' + (dueOnly ? '?due_only=true' : ''));
  const items = await res.json();
  const list = document.getElementById('mistakes-list');
  if(!items.length){
    list.innerHTML='<div style="padding:24px;text-align:center;color:#aaa">'+(dueOnly?'没有待复习的题 🎉':'还没有错题')+' </div>';
    return;
  }
  const gradeMap={'primary_4':'小四','primary_5':'小五','primary_6':'小六',
    'junior_1':'初一','junior_2':'初二','junior_3':'初三',
    'senior_1':'高一','senior_2':'高二','senior_3':'高三'};
  const subjMap={'math':'数学','physics':'物理'};
  list.innerHTML = items.map(m=>`
    <div class="mistake-card" id="mc-${m.id}">
      <div class="stmt">${m.statement}</div>
      <div class="meta">${subjMap[m.subject]||m.subject} · ${gradeMap[m.grade]||m.grade} · 复习${m.review_count}次 · 下次 ${m.next_review}</div>
      <div class="actions">
        <button class="btn-review" onclick="markReviewed(${m.id})">✅ 已复习</button>
        <button class="btn-practice" onclick="practiceFromMistake(${m.id})">▶ 重新练习</button>
        <button class="btn-del" onclick="deleteMistake(${m.id})">🗑</button>
      </div>
    </div>`).join('');
  // update badge
  const due = items.filter(m=>m.next_review<=new Date().toISOString().slice(0,10)).length;
  updateDueBadge(due);
}

async function markReviewed(id){
  await fetch('/api/mistakes/'+id+'/reviewed', {method:'PUT'});
  loadMistakes(false, null);
}

async function deleteMistake(id){
  if(!confirm('确认删除这道错题？')) return;
  await fetch('/api/mistakes/'+id, {method:'DELETE'});
  document.getElementById('mc-'+id)?.remove();
}

function practiceFromMistake(id){
  // switch to practice page and load that mistake
  fetch('/api/mistakes').then(r=>r.json()).then(items=>{
    const m = items.find(x=>x.id===id);
    if(!m) return;
    showPage('practice', document.querySelector('#nav .nav-btn'));
    document.getElementById('subject').value = m.subject;
    document.getElementById('grade').value = m.grade;
    document.getElementById('statement').value = m.statement;
    autoResize(document.getElementById('statement'));
    // reset chat
    sessionId=null;
    document.getElementById('chat').innerHTML='';
    document.getElementById('chat').style.display='none';
    document.getElementById('input-bar').style.display='none';
    document.getElementById('setup').style.display='';
    document.getElementById('add-to-mistakes-bar').style.display='none';
    setStatus('');
  });
}

async function addCurrentToMistakes(){
  if(!sessionId) return;
  const res = await fetch('/api/mistakes/from-session/add-from-session?session_id='+sessionId, {method:'POST'});
  if(res.ok){
    document.getElementById('add-to-mistakes-bar').style.display='none';
    setStatus('✅ 已加入错题集');
    updateDueBadge();
  }
}

async function addMistakeFromPhoto(input){
  const file = input.files[0];
  if(!file) return;
  const subject = document.getElementById('subject')?.value || 'math';
  const grade = document.getElementById('grade')?.value || 'junior_1';
  const list = document.getElementById('mistakes-list');
  list.innerHTML='<div style="padding:16px;text-align:center;color:#888">📷 识别中…</div>';
  const fd = new FormData();
  fd.append('file', file);
  try{
    const res = await fetch(`/api/mistakes/from-photo?subject=${subject}&grade=${grade}`, {method:'POST', body:fd});
    if(!res.ok) throw new Error(await res.text());
    await loadMistakes(false, null);
    updateDueBadge();
  }catch(e){
    list.innerHTML='<div style="padding:16px;color:#dc2626">❌ '+e.message+'</div>';
  }
  input.value='';
}

async function updateDueBadge(count){
  if(count===undefined){
    const r = await fetch('/api/mistakes/due-count');
    const d = await r.json();
    count = d.due;
  }
  const btn = document.getElementById('nav-mistakes');
  const existing = btn.querySelector('.badge');
  if(existing) existing.remove();
  if(count>0){
    const b=document.createElement('span');
    b.className='badge'; b.textContent=count;
    btn.querySelector('.icon').appendChild(b);
  }
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
