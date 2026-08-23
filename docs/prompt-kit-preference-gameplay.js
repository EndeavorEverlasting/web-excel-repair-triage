(function(root){
'use strict';

var STORAGE_KEY='promptKit.usage.v1';
var SCHEMA='prompt-kit-usage/v1';
var LEVEL_SIZE=5;
var state=loadState();

function emptyState(){return{schema:SCHEMA,totalCopies:0,byPrompt:{},recent:[]}}
function normalizedCount(value){var number=Number(value);return Number.isFinite(number)&&number>0?Math.floor(number):0}
function loadState(){
  var next=emptyState();
  try{
    if(!root.localStorage)return next;
    var raw=root.localStorage.getItem(STORAGE_KEY);
    if(!raw)return next;
    var parsed=JSON.parse(raw);
    if(!parsed||parsed.schema!==SCHEMA)return next;
    next.totalCopies=normalizedCount(parsed.totalCopies);
    next.recent=Array.isArray(parsed.recent)?parsed.recent.filter(function(id){return /^P\d+$/.test(String(id||''))}).slice(0,12):[];
    if(parsed.byPrompt&&typeof parsed.byPrompt==='object'){
      Object.keys(parsed.byPrompt).forEach(function(id){
        if(!/^P\d+$/.test(id))return;
        var item=parsed.byPrompt[id]||{};
        var count=normalizedCount(item.count);
        if(count)next.byPrompt[id]={count:count,lastCopiedAt:item.lastCopiedAt||null}
      })
    }
  }catch(error){}
  return next
}
function saveState(){try{if(root.localStorage)root.localStorage.setItem(STORAGE_KEY,JSON.stringify(state));return true}catch(error){return false}}
function promptById(id){return(root.PROMPTS||[]).find(function(prompt){return prompt.id===id})}
function recordSuccessfulCopy(id,now){
  if(!promptById(id))return false;
  state=loadState();
  var current=state.byPrompt[id]||{count:0,lastCopiedAt:null};
  current.count+=1;
  current.lastCopiedAt=now||new Date().toISOString();
  state.byPrompt[id]=current;
  state.totalCopies+=1;
  state.recent=[id].concat(state.recent.filter(function(item){return item!==id})).slice(0,12);
  saveState();
  renderDashboard();
  return true
}
function rows(){
  return Object.keys(state.byPrompt).map(function(id){var prompt=promptById(id);return prompt?{prompt:prompt,count:state.byPrompt[id].count}:null})
    .filter(Boolean).sort(function(a,b){return b.count-a.count||Number(a.prompt.seq)-Number(b.prompt.seq)})
}
function level(){
  var complete=Math.floor(state.totalCopies/LEVEL_SIZE);
  var progress=state.totalCopies%LEVEL_SIZE;
  return{number:complete+1,progress:progress,remaining:LEVEL_SIZE-progress,percent:Math.round(progress/LEVEL_SIZE*100)}
}
function favoriteIds(){return(root.PROMPTS||[]).filter(function(prompt){return typeof root.isFavoritePrompt==='function'&&root.isFavoritePrompt(prompt.id)}).map(function(prompt){return prompt.id})}
function signals(){
  var buckets={};
  rows().forEach(function(row){var label=String(row.prompt.type||row.prompt.class||'Other');buckets[label]=(buckets[label]||0)+row.count});
  return Object.keys(buckets).map(function(label){return{label:label,count:buckets[label]}}).sort(function(a,b){return b.count-a.count||a.label.localeCompare(b.label)}).slice(0,4)
}
function escapeHtml(value){return String(value==null?'':value).replace(/[&<>\"]/g,function(ch){return{'&':'&amp;','<':'&lt;','>':'&gt;','\"':'&quot;'}[ch]})}
function ensureStyles(){
  if(typeof document==='undefined'||document.getElementById('prompt-kit-preference-gameplay-styles'))return;
  var style=document.createElement('style');style.id='prompt-kit-preference-gameplay-styles';
  style.textContent='.prompt-dashboard-toggle{min-height:32px;padding:6px 10px;border:1px solid rgba(168,85,247,.45);border-radius:7px;background:linear-gradient(135deg,rgba(88,28,135,.82),rgba(30,41,59,.96));color:#f3e8ff;font-size:11px;font-weight:800;cursor:pointer;box-shadow:0 0 14px rgba(168,85,247,.18)}.prompt-dashboard-toggle:hover,.prompt-dashboard-toggle:focus-visible{outline:none;border-color:#c084fc;box-shadow:0 0 0 2px rgba(192,132,252,.18),0 0 22px rgba(168,85,247,.3)}.prompt-game-dashboard{position:fixed;inset:0;z-index:340;display:grid;place-items:center;padding:18px;background:rgba(2,6,23,.76);backdrop-filter:blur(8px)}.prompt-game-dashboard[hidden]{display:none}.prompt-game-panel{width:min(820px,96vw);max-height:88vh;overflow:auto;border:1px solid rgba(168,85,247,.42);border-radius:18px;background:linear-gradient(145deg,#111827,#171426 58%,#0f172a);box-shadow:0 28px 80px rgba(0,0,0,.55),0 0 36px rgba(168,85,247,.2);padding:18px}.prompt-game-head{display:flex;align-items:flex-start;justify-content:space-between;gap:12px}.prompt-game-kicker{font-size:10px;text-transform:uppercase;letter-spacing:.14em;color:#c084fc;font-weight:800}.prompt-game-head h2{margin:2px 0 3px;font-size:22px}.prompt-game-subtitle{font-size:11px;color:var(--text-muted)}.prompt-game-close{width:36px;height:36px;border:1px solid var(--border);border-radius:9px;background:var(--bg-surface);color:var(--text-secondary);font-size:20px;cursor:pointer}.prompt-game-stats{display:grid;grid-template-columns:repeat(4,minmax(0,1fr));gap:9px;margin:16px 0}.prompt-game-stat{padding:12px;border:1px solid var(--border);border-radius:12px;background:rgba(15,23,42,.75)}.prompt-game-stat strong{display:block;font-size:21px;color:#e9d5ff}.prompt-game-stat span{font-size:9px;color:var(--text-muted);text-transform:uppercase;letter-spacing:.08em}.prompt-level-card{padding:13px;border:1px solid rgba(168,85,247,.35);border-radius:13px;background:linear-gradient(135deg,rgba(88,28,135,.28),rgba(15,23,42,.76));margin-bottom:14px}.prompt-level-row{display:flex;justify-content:space-between;gap:10px;font-size:11px}.prompt-level-row strong{color:#d8b4fe}.prompt-level-track{height:9px;margin-top:8px;border-radius:999px;background:#1e293b;overflow:hidden}.prompt-level-fill{height:100%;border-radius:inherit;background:linear-gradient(90deg,#8b5cf6,#c084fc,#22d3ee);box-shadow:0 0 14px rgba(192,132,252,.45)}.prompt-game-grid{display:grid;grid-template-columns:1.2fr .8fr;gap:12px}.prompt-game-section{border:1px solid var(--border);border-radius:13px;background:rgba(15,23,42,.62);padding:12px}.prompt-game-section h3{font-size:12px;margin:0 0 9px}.prompt-game-empty{font-size:11px;color:var(--text-muted);line-height:1.5}.prompt-game-list{display:grid;gap:7px}.prompt-game-row{display:grid;grid-template-columns:auto minmax(0,1fr) auto;gap:8px;align-items:center;padding:8px;border:1px solid rgba(51,65,85,.82);border-radius:9px;background:rgba(15,23,42,.78)}.prompt-game-row button{border:0;background:none;color:var(--accent);font:800 10px ui-monospace,SFMono-Regular,Consolas,monospace;cursor:pointer}.prompt-game-row .name{min-width:0;overflow:hidden;text-overflow:ellipsis;white-space:nowrap;font-size:10px;color:var(--text-secondary)}.prompt-game-row .count{font-size:10px;color:#e9d5ff;font-weight:800}.prompt-signal{display:flex;align-items:center;justify-content:space-between;gap:8px;padding:7px 0;border-bottom:1px solid rgba(51,65,85,.55);font-size:10px}.prompt-signal:last-child{border-bottom:0}.prompt-signal strong{color:#c4b5fd}.prompt-loadout{display:flex;gap:6px;flex-wrap:wrap;margin-top:8px}.prompt-loadout button{padding:5px 7px;border:1px solid rgba(245,158,11,.3);border-radius:8px;background:rgba(120,53,15,.18);color:#fbbf24;font:700 10px ui-monospace,SFMono-Regular,Consolas,monospace;cursor:pointer}@media(max-width:760px){.prompt-game-stats{grid-template-columns:repeat(2,minmax(0,1fr))}.prompt-game-grid{grid-template-columns:1fr}.prompt-dashboard-toggle{min-height:42px}}';
  document.head.appendChild(style)
}
function renderDashboard(){
  if(typeof document==='undefined')return;
  var shell=document.getElementById('promptGameDashboard');if(!shell)return;
  var body=shell.querySelector('.prompt-game-body');if(!body)return;
  var usage=rows(),gameLevel=level(),favoriteList=favoriteIds(),configured=typeof root.configuredPromptShortcutIds==='function'?root.configuredPromptShortcutIds():[];
  var top=usage.slice(0,6).map(function(row){return'<div class="prompt-game-row"><button type="button" data-dashboard-copy="'+escapeHtml(row.prompt.id)+'">'+escapeHtml(row.prompt.id)+'</button><span class="name">'+escapeHtml(row.prompt.name)+'</span><span class="count">'+row.count+'×</span></div>'}).join('');
  var preference=signals().map(function(item){return'<div class="prompt-signal"><span>'+escapeHtml(item.label)+'</span><strong>'+item.count+' copies</strong></div>'}).join('');
  var loadout=favoriteList.slice(0,12).map(function(id){var shortcut=configured.indexOf(id)>=0?' · '+id.toLowerCase():'';return'<button type="button" data-dashboard-copy="'+escapeHtml(id)+'">★ '+escapeHtml(id+shortcut)+'</button>'}).join('');
  body.innerHTML='<div class="prompt-game-stats"><div class="prompt-game-stat"><strong>'+state.totalCopies+'</strong><span>Successful copies</span></div><div class="prompt-game-stat"><strong>'+usage.length+'</strong><span>Prompts explored</span></div><div class="prompt-game-stat"><strong>'+favoriteList.length+'</strong><span>Favorites</span></div><div class="prompt-game-stat"><strong>'+gameLevel.number+'</strong><span>Prompt level</span></div></div><div class="prompt-level-card"><div class="prompt-level-row"><strong>Level '+gameLevel.number+'</strong><span>'+gameLevel.remaining+' successful '+(gameLevel.remaining===1?'copy':'copies')+' to Level '+(gameLevel.number+1)+'</span></div><div class="prompt-level-track"><div class="prompt-level-fill" style="width:'+gameLevel.percent+'%"></div></div></div><div class="prompt-game-grid"><section class="prompt-game-section"><h3>Most used prompts</h3>'+(top?'<div class="prompt-game-list">'+top+'</div>':'<div class="prompt-game-empty">Copy a prompt to start revealing your play style. Only successful clipboard writes earn progress.</div>')+'</section><section class="prompt-game-section"><h3>Preference signals</h3>'+(preference||'<div class="prompt-game-empty">Your preferred prompt types will appear here as you use them.</div>')+'<h3 style="margin-top:14px">Favorite loadout</h3>'+(loadout?'<div class="prompt-loadout">'+loadout+'</div>':'<div class="prompt-game-empty">Star prompts to build a reusable loadout. Favorite shortcuts copy immediately.</div>')+'</section></div>';
  body.querySelectorAll('[data-dashboard-copy]').forEach(function(button){button.addEventListener('click',function(){root.copyPrompt(button.getAttribute('data-dashboard-copy'))})})
}
function setOpen(open){var shell=typeof document!=='undefined'?document.getElementById('promptGameDashboard'):null;if(!shell)return;shell.hidden=!open;if(open){renderDashboard();var close=shell.querySelector('.prompt-game-close');if(close)close.focus()}}
function initializeDashboard(){
  if(typeof document==='undefined')return;
  ensureStyles();
  if(!document.getElementById('promptGameDashboardToggle')){
    var controls=document.querySelector('.header-controls'),addPrompt=document.getElementById('addPromptBtn');
    if(controls){var toggle=document.createElement('button');toggle.type='button';toggle.id='promptGameDashboardToggle';toggle.className='prompt-dashboard-toggle';toggle.textContent='Dashboard';toggle.setAttribute('aria-haspopup','dialog');toggle.setAttribute('aria-controls','promptGameDashboard');toggle.addEventListener('click',function(){setOpen(true)});if(addPrompt&&addPrompt.parentNode===controls)controls.insertBefore(toggle,addPrompt);else controls.appendChild(toggle)}
  }
  if(!document.getElementById('promptGameDashboard')){
    var shell=document.createElement('div');shell.id='promptGameDashboard';shell.className='prompt-game-dashboard';shell.hidden=true;shell.setAttribute('role','dialog');shell.setAttribute('aria-modal','true');shell.setAttribute('aria-label','Prompt preference dashboard');shell.innerHTML='<div class="prompt-game-panel"><div class="prompt-game-head"><div><div class="prompt-game-kicker">Prompt Playbook</div><h2>Preference Dashboard</h2><div class="prompt-game-subtitle">Every successful copy earns progress and sharpens your local preference signals.</div></div><button type="button" class="prompt-game-close" aria-label="Close preference dashboard">×</button></div><div class="prompt-game-body"></div></div>';shell.querySelector('.prompt-game-close').addEventListener('click',function(){setOpen(false)});shell.addEventListener('click',function(event){if(event.target===shell)setOpen(false)});document.addEventListener('keydown',function(event){if(event.key==='Escape'&&!shell.hidden)setOpen(false)});document.body.appendChild(shell)
  }
  renderDashboard()
}

var previousCopyPrompt=root.copyPrompt;
root.copyPrompt=function(id){
  var prompt=promptById(id);
  if(!prompt||!prompt.copyContent)return previousCopyPrompt?previousCopyPrompt(id):undefined;
  var recorded=false;
  root.copyToClipboard(prompt.copyContent,function(){if(recorded)return;recorded=true;recordSuccessfulCopy(id);root.showCopyConfirmation(id)})
};
root.PromptKitPreferenceGameplay={schema:SCHEMA,storage_key:STORAGE_KEY,recordSuccessfulCopy:recordSuccessfulCopy,getState:function(){return JSON.parse(JSON.stringify(state))},getLevel:level,render:renderDashboard,open:function(){setOpen(true)}};
initializeDashboard()
})(typeof globalThis!=='undefined'?globalThis:this);
