(function(){
const $=s=>document.querySelector(s);
const esc=s=>String(s).replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
const story=$('#story'),chipsEl=$('#chips'),picker=$('#picker'),menu=$('#menu'),go=$('#go'),hint=$('#hint'),out=$('#results');
const state={syms:new Map(),removed:new Set(),all:[],last:null,sel:0,tab:'overview',analysed:false};
const SEV_LABEL=k=>k;
let parseT;

fetch('/api/symptoms').then(r=>r.json()).then(a=>state.all=a);

/* ---------- chips ---------- */
function renderChips(){
  chipsEl.innerHTML='';
  state.syms.forEach((label,key)=>{
    const c=document.createElement('span');c.className='chip';
    c.innerHTML=esc(label)+'<button type="button" aria-label="Remove '+esc(label)+'">×</button>';
    c.querySelector('button').onclick=()=>{state.syms.delete(key);state.removed.add(key);renderChips();if(state.analysed)analyse();};
    chipsEl.appendChild(c);
  });
  go.disabled=state.syms.size===0;
  hint.textContent=state.syms.size?state.syms.size+' symptom'+(state.syms.size>1?'s':'')+' selected.':'Add at least one symptom to begin. The more you add, the sharper the result.';
}
function addSym(key,label,rerun){
  if(state.syms.has(key))return;state.syms.set(key,label);state.removed.delete(key);renderChips();
  if(rerun&&state.analysed)analyse();
}

/* ---------- free text -> symptoms ---------- */
story.addEventListener('input',()=>{clearTimeout(parseT);parseT=setTimeout(parseNow,450);});
async function parseNow(){
  const text=story.value.trim();if(!text)return;
  try{
    const r=await fetch('/api/parse',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({text})});
    const d=await r.json();let added=false;
    d.symptoms.forEach(s=>{if(!state.syms.has(s.key)&&!state.removed.has(s.key)){state.syms.set(s.key,s.label);added=true;}});
    if(added)renderChips();
  }catch(e){}
}

/* ---------- search picker ---------- */
let hl=-1;
function showMenu(){
  const q=picker.value.trim().toLowerCase();if(!q){menu.hidden=true;return;}
  const m=state.all.filter(s=>!state.syms.has(s.key)&&s.label.toLowerCase().includes(q)).slice(0,8);
  menu.innerHTML='';hl=-1;
  m.forEach(s=>{const b=document.createElement('button');b.type='button';b.textContent=s.label;b.onmousedown=e=>{e.preventDefault();pick(s)};menu.appendChild(b);});
  menu.hidden=!m.length;
}
function pick(s){addSym(s.key,s.label,true);picker.value='';menu.hidden=true;}
picker.addEventListener('input',showMenu);
picker.addEventListener('blur',()=>setTimeout(()=>menu.hidden=true,100));
picker.addEventListener('keydown',e=>{
  const items=[...menu.children];
  if(e.key==='ArrowDown'){e.preventDefault();hl=Math.min(hl+1,items.length-1);}
  else if(e.key==='ArrowUp'){e.preventDefault();hl=Math.max(hl-1,0);}
  else if(e.key==='Enter'&&items.length){e.preventDefault();(items[hl>=0?hl:0]).dispatchEvent(new MouseEvent('mousedown'));return;}
  else return;
  items.forEach((b,i)=>b.classList.toggle('hl',i===hl));
});

/* ---------- voice ---------- */
const SR=window.SpeechRecognition||window.webkitSpeechRecognition;
if(SR){const mic=$('#mic');mic.hidden=false;let rec=null,on=false;
  mic.onclick=()=>{
    if(on){rec.stop();return;}
    rec=new SR();rec.lang='en-IN';rec.interimResults=true;rec.continuous=false;
    const base=story.value?story.value.trim()+' ':'';
    rec.onstart=()=>{on=true;mic.textContent='■ Listening…';};
    rec.onresult=e=>{story.value=base+[...e.results].map(r=>r[0].transcript).join(' ');};
    rec.onend=()=>{on=false;mic.textContent='🎙 Speak';parseNow();};
    rec.onerror=()=>{on=false;mic.textContent='🎙 Speak';};
    rec.start();
  };}

/* ---------- examples ---------- */
document.querySelectorAll('[data-ex]').forEach(b=>b.onclick=()=>{
  state.syms.clear();state.removed.clear();story.value=b.dataset.ex;parseNow().then(()=>{if(state.syms.size)analyse();});
});

/* ---------- analyse ---------- */
go.onclick=analyse;
async function analyse(){
  if(!state.syms.size)return;
  state.analysed=true;go.disabled=true;go.innerHTML='<span class="spin"></span> Analysing';
  try{
    const r=await fetch('/api/predict',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({symptoms:[...state.syms.keys()]})});
    const d=await r.json();if(!r.ok)throw new Error(d.error);
    state.last=d;state.sel=0;render();save(d);
    if(!out.dataset.seen){out.scrollIntoView({behavior:'smooth',block:'start'});out.dataset.seen=1;}
  }catch(e){out.hidden=false;out.innerHTML='<div class="card">Something went wrong: '+esc(e.message||'try again')+'</div>';}
  go.disabled=false;go.textContent='Analyse symptoms';
}

/* ---------- render ---------- */
const ICON={emergency:'🚨',urgent:'⚠️',moderate:'🩺',mild:'🏠'};
function list(a){return a&&a.length?'<ul class="clean">'+a.map(i=>'<li>'+esc(i)+'</li>').join('')+'</ul>':'<p class="muted">No data available.</p>';}
function render(){
  const d=state.last,t=d.triage,top=d.results[state.sel];out.hidden=false;
  const flags=t.red_flags.length?'<ul class="flags">'+t.red_flags.map(f=>'<li>'+esc(f)+'</li>').join('')+'</ul>':'';
  const pct=p=>Math.round(p*100);
  let h='<div class="banner '+t.level+'" role="alert"><span style="font-size:2rem" aria-hidden="true">'+ICON[t.level]+'</span><div><h2>'+esc(t.title)+'</h2><p>'+esc(t.message)+'</p>'+flags
    +(t.level==='emergency'?'<a class="call" href="tel:112">Call 112 now</a>':'')+'</div><div class="sevmeter"><b>'+t.severity_score+'</b>severity score</div></div>';
  h+='<div class="grid"><div><div class="card"><h3>Possible conditions</h3><p class="small muted" style="margin-top:-6px">'+esc(d.confidence_note)+'</p>';
  d.results.forEach((r,i)=>{h+='<button class="dx '+(i===state.sel?'sel':'')+'" data-i="'+i+'"><div class="top"><span>'+esc(r.name)+'</span><span>'+pct(r.probability)+'%</span></div><div class="bar"><i style="width:'+pct(r.probability)+'%"></i></div></button>';});
  h+='<p class="small muted" style="margin:6px 0 0">Match likelihood is a model score, not a clinical probability.</p></div>';
  if(d.follow_ups.length){h+='<div class="card followup" style="margin-top:18px"><h3>Sharpen this result</h3><p class="small muted" style="margin-top:-6px">Do you also have any of these? One tap re-runs the analysis.</p><div class="chips">'
    +d.follow_ups.map(f=>'<button class="chip add" data-k="'+esc(f.key)+'" data-l="'+esc(f.label)+'">+ '+esc(f.label)+'</button>').join('')+'</div></div>';}
  h+='</div><div class="card"><h3>'+esc(top.name)+'</h3><div class="tabs" role="tablist">'
    +[['overview','Overview'],['why','Why this match'],['care','Care plan'],['meds','Treatments'],['doctor','Who to see']].map(([k,l])=>'<button role="tab" data-t="'+k+'" class="'+(state.tab===k?'on':'')+'">'+l+'</button>').join('')+'</div>';
  const pane={
    overview:'<p>'+esc(top.description)+'</p><p class="small muted">Your symptoms: '+d.symptoms.map(s=>'<span class="tag">'+esc(s.label)+'</span>').join('')+'</p>',
    why:'<p class="small muted">Symptoms you reported that this condition typically involves:</p>'+(top.matched.map(s=>'<span class="tag">✓ '+esc(s.label)+'</span>').join('')||'<p class="muted">None</p>')
      +'<p class="small muted" style="margin-top:14px">Common signs you did <b>not</b> mention (ask yourself if you have them):</p>'+(top.unmatched_typical.map(s=>'<span class="tag miss">'+esc(s.label)+'</span>').join('')||'<p class="muted">You covered all the typical signs.</p>'),
    care:'<h3 class="small" style="margin-bottom:4px">Precautions</h3>'+list(top.precautions)+'<h3 class="small" style="margin:14px 0 4px">Diet</h3>'+list(top.diet)+'<h3 class="small" style="margin:14px 0 4px">Lifestyle</h3>'+list(top.lifestyle.slice(0,6)),
    meds:'<p class="small muted">Common treatment options a doctor may consider. Never start or stop medicines without professional advice.</p>'+list(top.medications),
    doctor:'<p><b>'+esc(top.specialist)+'</b></p><p class="small muted">Find one near you:</p><p><a class="btn ghost" style="display:inline-block;text-decoration:none" target="_blank" rel="noopener" href="https://www.google.com/maps/search/'+encodeURIComponent(top.specialist.split('/')[0].trim()+' near me')+'">Open in Google Maps</a></p>'
  };
  Object.keys(pane).forEach(k=>{h+='<div class="tabpane" data-p="'+k+'" '+(state.tab===k?'':'hidden')+'>'+pane[k]+'</div>';});
  h+='<div class="actions"><form method="post" action="/report.pdf" style="display:inline"><input type="hidden" name="symptoms" value=\''+esc(JSON.stringify([...state.syms.keys()]))+'\'><button class="btn" type="submit">Download PDF report</button></form><button class="btn ghost" id="print" type="button">Print</button><button class="btn ghost" id="share" type="button">Copy summary</button></div>'
    +'<p class="disc">Educational tool trained on a public dataset. Not a diagnosis. If you feel very unwell, seek care.</p></div></div>';
  out.innerHTML=h;
  out.querySelectorAll('.dx').forEach(b=>b.onclick=()=>{state.sel=+b.dataset.i;render();});
  out.querySelectorAll('.tabs button').forEach(b=>b.onclick=()=>{state.tab=b.dataset.t;out.querySelectorAll('.tabs button').forEach(x=>x.classList.toggle('on',x===b));out.querySelectorAll('.tabpane').forEach(p=>p.hidden=p.dataset.p!==state.tab);});
  out.querySelectorAll('.chip.add').forEach(b=>b.onclick=()=>addSym(b.dataset.k,b.dataset.l,true));
  $('#print').onclick=()=>window.print();
  $('#share').onclick=e=>{const txt='Apna Hospital: '+d.results.map(r=>r.name+' '+pct(r.probability)+'%').join(', ')+'. Triage: '+t.title+'. Symptoms: '+d.symptoms.map(s=>s.label).join(', ');
    (navigator.clipboard?navigator.clipboard.writeText(txt):Promise.reject()).then(()=>e.target.textContent='Copied ✓').catch(()=>prompt('Copy this summary',txt));};
}

/* ---------- history ---------- */
function loadHist(){try{return JSON.parse(localStorage.getItem('ah_hist')||'[]')}catch(e){return[]}}
function save(d){try{
  const h=loadHist().filter(x=>x.k!==d.symptoms.map(s=>s.key).sort().join());
  h.unshift({k:d.symptoms.map(s=>s.key).sort().join(),s:d.symptoms,top:d.results[0].name,lvl:d.triage.level,t:Date.now()});
  localStorage.setItem('ah_hist',JSON.stringify(h.slice(0,8)));drawHist();}catch(e){}}
function drawHist(){const h=loadHist(),w=$('#history-wrap'),el=$('#hist');if(!h.length){w.hidden=true;return;}w.hidden=false;el.innerHTML='';
  h.forEach(x=>{const b=document.createElement('button');b.innerHTML='<b>'+esc(x.top)+'</b><small>'+esc(x.s.slice(0,3).map(s=>s.label).join(', '))+(x.s.length>3?'…':'')+' · '+new Date(x.t).toLocaleDateString()+'</small>';
    b.onclick=()=>{state.syms=new Map(x.s.map(s=>[s.key,s.label]));state.removed.clear();renderChips();analyse();};el.appendChild(b);});}
drawHist();

/* ---------- preset from ?symptoms= ---------- */
if(window.PRESET){const keys=window.PRESET.split(',').map(s=>s.trim().replace(/^[\[\]'" ]+|[\[\]'" ]+$/g,'')).filter(Boolean);
  fetch('/api/parse',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({text:keys.join(', ')})}).then(r=>r.json()).then(d=>{d.symptoms.forEach(s=>state.syms.set(s.key,s.label));renderChips();if(state.syms.size)analyse();});}
renderChips();
})();
