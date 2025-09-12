const state = {
  provider: null,
  models: [],
  recognizing: false,
  lastAssistant: '',
  micReady: false,
};

function el(sel){return document.querySelector(sel)}
function addMsg(text, who){
  const m = document.createElement('div');
  m.className = `message ${who}`;
  m.textContent = text;
  el('#messages').appendChild(m);
  el('#messages').scrollTop = el('#messages').scrollHeight;
  if(who === 'assistant') state.lastAssistant = text;
}

async function loadModels(){
  try{
    const res = await fetch('/models');
    const data = await res.json();
    state.provider = data.provider;
    state.models = Array.isArray(data.allowed_models) ? data.allowed_models : [];
    const sel = el('#model');
    sel.innerHTML = '<option value="" disabled selected>Select a model…</option>';
    state.models.forEach(m=>{
      const opt = document.createElement('option');
      opt.value = m; opt.textContent = m; sel.appendChild(opt);
    });
  const provEl = el('#provider');
  if (provEl) provEl.textContent = state.provider;
  }catch(err){
    console.warn('Model load failed', err);
  }
}

async function sendChat(){
  const inp = el('#input');
  const text = inp.value.trim();
  const model = el('#model').value;
  if(!model){ inp.blur(); alert('Please select a model.'); return; }
  if(!text) return;
  addMsg(text, 'user');
  inp.value = '';
  try{
    el('#send').disabled = true; el('#send').classList.add('loading');
    const res = await fetch('/chat', {
      method:'POST', headers:{'Content-Type':'application/json'},
      body: JSON.stringify({ message:text, model })
    });
    const data = await res.json();
    if(data.status === 'success') addMsg(data.response, 'assistant');
    else addMsg(data.error || 'Error from server', 'assistant');
  }catch(err){
    addMsg('Network error', 'assistant');
  }finally{
    el('#send').disabled = false; el('#send').classList.remove('loading');
  }
}

// --- Voice: STT (mic) ---
let recognition;
async function ensureMicPermission(){
  try{
    if(state.micReady) return true;
    if(!navigator.mediaDevices || !navigator.mediaDevices.getUserMedia) return true; // not strictly required for WebSpeech
    await navigator.mediaDevices.getUserMedia({ audio:true });
    state.micReady = true;
    return true;
  }catch(err){
    alert('Microphone permission is required. Please allow access.');
    return false;
  }
}
function initSTT(){
  const SR = window.SpeechRecognition || window.webkitSpeechRecognition;
  if(!SR) return null;
  const r = new SR();
  r.continuous = false;
  r.interimResults = true;
  r.lang = navigator.language || 'en-US';
  r.onstart = ()=>{ state.recognizing = true; el('#mic').classList.add('loading'); };
  r.onerror = ()=>{ state.recognizing = false; el('#mic').classList.remove('loading'); };
  r.onend = ()=>{ state.recognizing = false; el('#mic').classList.remove('loading'); };
  r.onresult = (event)=>{
    let finalTranscript = '';
    for(let i=event.resultIndex; i<event.results.length; i++){
      const res = event.results[i];
      if(res.isFinal) finalTranscript += res[0].transcript;
    }
    if(finalTranscript){
      el('#input').value = finalTranscript.trim();
      sendChat();
    }
  };
  return r;
}

function toggleMic(){ /* removed in UI; kept for safety */
  if(!recognition){ recognition = initSTT(); }
  if(!recognition){ alert('Speech Recognition not supported in this browser.'); return; }
  if(state.recognizing){ recognition.stop(); }
  else { recognition.start(); }
}

async function startMic(){
  if(!recognition){ recognition = initSTT(); }
  if(!recognition){ alert('Speech Recognition not supported in this browser.'); return; }
  const ok = await ensureMicPermission();
  if(!ok) return;
  if(!state.recognizing){ recognition.start(); }
}

function stopMic(){
  if(recognition && state.recognizing){ recognition.stop(); }
}

// --- Voice: TTS (speaker) ---
function speak(text){
  if(!('speechSynthesis' in window)){ alert('Speech Synthesis not supported.'); return; }
  const utter = new SpeechSynthesisUtterance(text);
  utter.lang = navigator.language || 'en-US';
  window.speechSynthesis.cancel();
  window.speechSynthesis.speak(utter);
}

function handleSpeak(){
  const toRead = state.lastAssistant || 'No assistant message yet.';
  speak(toRead);
}

window.addEventListener('DOMContentLoaded', ()=>{
  loadModels();
  el('#send').addEventListener('click', sendChat);
  el('#input').addEventListener('keydown', (e)=>{ if(e.key==='Enter') sendChat(); });
  const micBtn = el('#mic');
  const speakBtn = el('#speak');
  const SR = window.SpeechRecognition || window.webkitSpeechRecognition;
  if(!SR){
    addMsg('Voice input not supported in this browser. Try Chrome on desktop/mobile.', 'assistant');
  }
  if(micBtn){
    micBtn.addEventListener('mousedown', startMic);
    micBtn.addEventListener('mouseup', stopMic);
    micBtn.addEventListener('mouseleave', stopMic);
    micBtn.addEventListener('touchstart', (e)=>{ e.preventDefault(); startMic(); }, { passive:false });
    micBtn.addEventListener('touchend', (e)=>{ e.preventDefault(); stopMic(); }, { passive:false });
  }
  if(speakBtn) speakBtn.addEventListener('click', handleSpeak);
});
