(function(){
'use strict';
var copyToastTimer=null;
var PROMPT_KIT_SHORTCUT_STORAGE_KEY='promptKit.promptShortcuts.v1';
var PROMPT_KIT_SHORTCUT_SCHEMA='prompt-kit-shortcuts/v1';
var PROMPT_KIT_SHORTCUT_SEQUENCE_TIMEOUT_MS=1200;
var promptShortcutBindings=loadPromptShortcutBindings();
var promptShortcutBuffer='';
var promptShortcutBufferTimer=null;

function ensurePromptKitPolishStyles(){
  if(document.getElementById('prompt-kit-polish-styles'))return;
  var style=document.createElement('style');
  style.id='prompt-kit-polish-styles';
  style.textContent='.prompt-card .prompt-header{padding-right:176px;min-height:34px}.prompt-card-actions{position:absolute;top:12px;right:12px;display:flex;align-items:center;justify-content:flex-end;gap:6px;z-index:3;max-width:168px}.prompt-card-actions .prompt-favorite-btn,.prompt-card-actions .prompt-open-btn,.prompt-card-actions .prompt-copy-btn{position:static!important;top:auto!important;right:auto!important;margin:0!important;opacity:1!important;display:inline-flex;align-items:center;justify-content:center;min-height:30px;box-sizing:border-box}.prompt-card-actions .prompt-favorite-btn{width:30px;min-width:30px}.prompt-card-actions .prompt-open-btn,.prompt-card-actions .prompt-copy-btn{padding:4px 8px;white-space:nowrap}.prompt-card.copy-confirmed{animation:prompt-copy-confirm 800ms ease-out}.prompt-card.copy-confirmed .glow-bar{background:var(--success)!important;box-shadow:0 0 12px rgba(34,197,94,.9),0 0 28px rgba(34,197,94,.45)!important}.toast.success{border-color:var(--success);background:linear-gradient(135deg,rgba(20,83,45,.96),rgba(17,24,39,.98));color:#dcfce7;box-shadow:0 0 0 1px rgba(34,197,94,.2),0 0 24px rgba(34,197,94,.42),0 10px 34px rgba(0,0,0,.42)}.toast.success.show{animation:prompt-toast-success 1.7s ease both}.header-top{display:grid;grid-template-columns:minmax(0,1fr) auto minmax(280px,400px);align-items:center;gap:12px 16px}.header-top>.logo{grid-column:1;min-width:0}.filter-panel-toggle{grid-column:2;display:inline-flex;align-items:center;justify-content:center;justify-self:end;min-height:34px;padding:6px 10px;border:1px solid var(--border);border-radius:7px;background:var(--bg-surface);color:var(--text-secondary);font-size:11px;font-weight:600;cursor:pointer;white-space:nowrap;transition:all .2s}.header-top>.search-container{grid-column:3;min-width:0;width:100%;max-width:none}.header-top>.header-controls{grid-column:1/-1;min-width:0;width:100%;justify-self:stretch;justify-content:flex-end;flex-wrap:wrap}.filter-panel-toggle:hover,.filter-panel-toggle:focus-visible{outline:none;border-color:var(--accent);color:var(--text-primary);box-shadow:0 0 0 2px var(--accent-glow)}.header.filters-collapsed{padding-bottom:8px}.header.filters-collapsed .search-container,.header.filters-collapsed .header-controls,.header.filters-collapsed .sections-nav,.header.filters-collapsed .type-nav{display:none!important}.header.filters-collapsed .header-top{padding-bottom:0}.header.filters-collapsed .filter-panel-toggle{justify-self:end;margin-left:0}@keyframes prompt-copy-confirm{0%{border-color:var(--success);box-shadow:0 0 0 1px rgba(34,197,94,.7),0 0 30px rgba(34,197,94,.42);transform:translateY(-1px) scale(1.006)}45%{border-color:rgba(34,197,94,.78);box-shadow:0 0 22px rgba(34,197,94,.3)}100%{border-color:var(--border);box-shadow:none;transform:none}}@keyframes prompt-toast-success{0%{opacity:0;transform:translate(-50%,12px) scale(.96)}12%{opacity:1;transform:translate(-50%,0) scale(1.03)}24%,82%{opacity:1;transform:translate(-50%,0) scale(1)}100%{opacity:0;transform:translate(-50%,-4px) scale(.99)}}@media(max-width:980px){.header-top{grid-template-columns:minmax(0,1fr) auto}.header-top>.logo{grid-column:1}.filter-panel-toggle{grid-column:2}.header-top>.search-container{grid-column:1/-1;max-width:none}.header-top>.header-controls{grid-column:1/-1}}@media(max-width:760px){.prompt-card .prompt-header{padding-right:0;min-height:0}.prompt-card-actions{position:static;max-width:none;width:100%;display:grid;grid-template-columns:44px minmax(72px,1fr) minmax(72px,1fr);gap:8px;margin-top:12px}.prompt-card-actions .prompt-favorite-btn,.prompt-card-actions .prompt-open-btn,.prompt-card-actions .prompt-copy-btn{width:100%;min-height:42px;margin:0!important}.header{padding-left:12px;padding-right:12px}.header-top{grid-template-columns:minmax(0,1fr) auto;gap:8px}.filter-panel-toggle{min-height:40px;justify-self:end}.header-top>.search-container{grid-column:1/-1;width:100%}.header-top>.header-controls{grid-column:1/-1;display:grid;grid-template-columns:minmax(0,1fr);width:100%;justify-items:stretch;gap:8px}.header-top>.header-controls .cat-tabs{max-width:100%;overflow-x:auto;-webkit-overflow-scrolling:touch;scrollbar-width:none}.header-top>.header-controls .cat-tabs::-webkit-scrollbar{display:none}.header-top>.header-controls .cat-tab{min-height:42px}.header-top>.header-controls .add-prompt-btn{justify-content:center;min-height:42px}.header-top>.header-controls .stats{justify-content:center}.header.filters-collapsed .header-top{grid-template-columns:minmax(0,1fr) auto}}@media(prefers-reduced-motion:reduce){.prompt-card.copy-confirmed,.toast.success.show{animation:none}.toast.success.show{opacity:1}}';
  document.head.appendChild(style)
}

window.showToast=function(msg,tone){
  var t=document.getElementById('toast');
  if(!t)return;
  if(copyToastTimer){clearTimeout(copyToastTimer);copyToastTimer=null}
  t.textContent=msg;
  t.classList.remove('success');
  if(tone)t.classList.add(tone);
  t.classList.add('show');
  copyToastTimer=setTimeout(function(){t.classList.remove('show');t.classList.remove('success');copyToastTimer=null},1800)
};

function fallbackClipboard(text,onSuccess){
  var ta=document.createElement('textarea');
  ta.value=text;ta.style.position='fixed';ta.style.opacity='0';ta.setAttribute('readonly','');
  document.body.appendChild(ta);ta.select();
  var copied=false;
  try{copied=document.execCommand('copy')}catch(e){copied=false}
  document.body.removeChild(ta);
  if(copied&&onSuccess)onSuccess();
  if(!copied)showToast('Copy failed — use the Copy button again')
}

window.copyToClipboard=function(text,onSuccess){
  if(navigator.clipboard&&navigator.clipboard.writeText){
    navigator.clipboard.writeText(text).then(function(){if(onSuccess)onSuccess()}).catch(function(){fallbackClipboard(text,onSuccess)})
  }else fallbackClipboard(text,onSuccess)
};

window.showCopyConfirmation=function(id){
  showToast('✓ Copied to clipboard','success');
  var selector='[data-prompt-id="'+String(id||'').replace(/"/g,'')+'"]';
  document.querySelectorAll(selector).forEach(function(card){card.classList.remove('copy-confirmed');void card.offsetWidth;card.classList.add('copy-confirmed');setTimeout(function(){card.classList.remove('copy-confirmed')},850)})
};

window.copyPrompt=function(id){
  var p=PROMPTS.find(function(x){return x.id===id});
  if(p&&p.copyContent)copyToClipboard(p.copyContent,function(){showCopyConfirmation(id)})
};

function clearTransientPromptFilters(){
  activeType=null;
  activeColor=null;
  collapsedSections={};
  var search=document.getElementById('search');
  if(search)search.value='';
  var clear=document.getElementById('searchClear');
  if(clear)clear.style.display='none';
  document.querySelectorAll('.type-chip').forEach(function(button){button.classList.toggle('active',button.dataset.type==='__all__')})
}

function activateAllPromptsView(){
  resetPromptKitView();
}

function activateFavoritesView(){
  activeCat='all';
  activeSection='__favorites__';
  clearTransientPromptFilters();
  document.querySelectorAll('.cat-tab').forEach(function(button){button.classList.toggle('active',button.id==='favoritesShortcut')});
  document.querySelectorAll('.section-tab').forEach(function(button){button.classList.toggle('active',button.dataset.section==='__favorites__')});
  render();
}

function ensureCompactBrowsingControls(){
  var header=document.querySelector('.header');
  var headerTop=document.querySelector('.header-top');
  var search=document.querySelector('.search-container');
  var catTabs=document.querySelector('.cat-tabs');
  if(!header||!headerTop||!catTabs)return;

  var doctrineButton=catTabs.querySelector('.cat-tab[data-cat="doctrine"]');
  if(doctrineButton){
    var doctrineKbd=doctrineButton.querySelector('.kbd');
    if(doctrineKbd)doctrineKbd.textContent='5';
  }

  if(!document.getElementById('favoritesShortcut')){
    var favoritesButton=document.createElement('button');
    favoritesButton.className='cat-tab';
    favoritesButton.id='favoritesShortcut';
    favoritesButton.type='button';
    favoritesButton.setAttribute('data-view','favorites');
    favoritesButton.setAttribute('aria-label','Show saved favorite prompts');
    favoritesButton.innerHTML='<span class="tab-icon">★</span>Favorites<span class="kbd">4</span>';
    favoritesButton.addEventListener('click',function(e){e.preventDefault();e.stopPropagation();activateFavoritesView()});
    if(doctrineButton)catTabs.insertBefore(favoritesButton,doctrineButton);else catTabs.appendChild(favoritesButton)
  }

  if(!document.getElementById('filterPanelToggle')){
    var toggle=document.createElement('button');
    toggle.className='filter-panel-toggle';
    toggle.id='filterPanelToggle';
    toggle.type='button';
    toggle.setAttribute('aria-expanded','true');
    toggle.setAttribute('aria-controls','search sectionsNav typeNav');
    toggle.setAttribute('aria-keyshortcuts','F');
    toggle.setAttribute('title','Hide filters to maximize prompt browsing space (F)');
    toggle.textContent='Hide filters ↑';
    toggle.addEventListener('click',function(){toggleCompactFilters()});
    if(search)headerTop.insertBefore(toggle,search);else headerTop.appendChild(toggle)
  }
}

function installCompactBrowsingViewSwitches(){
  document.addEventListener('click',function(e){
    var target=e.target;
    if(!target||typeof target.closest!=='function')return;
    var allButton=target.closest('.cat-tab[data-cat="all"]');
    if(!allButton)return;
    e.preventDefault();
    e.stopImmediatePropagation();
    activateAllPromptsView();
  },true)
}

var PROMPT_KIT_SHORTCUTS=[
  {key:'`',label:'Show / hide Hotkeys'},
  {key:'1',label:'All prompts'},
  {key:'2',label:'Standard prompts'},
  {key:'3',label:'GNHF prompts'},
  {key:'4',label:'Favorites'},
  {key:'5',label:'Doctrine'},
  {key:'/',label:'Focus search'},
  {key:'R',label:'Reference panel'},
  {key:'F',label:'Show / hide filters'},
  {key:'[',label:'Hide filters'},
  {key:']',label:'Show filters'},
  {key:'T',label:'Scroll to top'},
  {key:'B',label:'Scroll to bottom'},
  {key:'Esc',label:'Close / clear active surface'}
];

function hotkeyScrollBehavior(){
  try{return window.matchMedia&&window.matchMedia('(prefers-reduced-motion: reduce)').matches?'auto':'smooth'}catch(e){return 'auto'}
}

function scrollPromptKitTo(edge){
  var anchor=document.getElementById(edge==='top'?'page-top':'page-bottom');
  var behavior=hotkeyScrollBehavior();
  if(anchor&&typeof anchor.scrollIntoView==='function'){
    try{anchor.scrollIntoView({behavior:behavior,block:edge==='top'?'start':'end'});return}catch(e){}
  }
  var height=Math.max(document.documentElement?document.documentElement.scrollHeight:0,document.body?document.body.scrollHeight:0);
  var top=edge==='top'?0:height;
  try{window.scrollTo({top:top,behavior:behavior})}catch(e){window.scrollTo(0,top)}
}

function setCompactFiltersVisible(visible){
  var header=document.querySelector('.header');
  var toggle=document.getElementById('filterPanelToggle');
  if(!header||!toggle)return false;
  var collapsed=!visible;
  header.classList.toggle('filters-collapsed',collapsed);
  toggle.setAttribute('aria-expanded',collapsed?'false':'true');
  toggle.setAttribute('title',collapsed?'Show Prompt Kit filters (F)':'Hide filters to maximize prompt browsing space (F)');
  toggle.textContent=collapsed?'Show filters ↓':'Hide filters ↑';
  return !collapsed
}

function showCompactFilters(){return setCompactFiltersVisible(true)}
function hideCompactFilters(){return setCompactFiltersVisible(false)}
function toggleCompactFilters(){
  var header=document.querySelector('.header');
  if(!header)return false;
  return setCompactFiltersVisible(header.classList.contains('filters-collapsed'))
}

function normalizePromptShortcutId(raw){
  var value=String(raw||'').trim().toUpperCase();
  return /^P\d+$/.test(value)?value:null
}

function clonePromptShortcutBindings(source){
  var copy={};
  Object.keys(source||{}).forEach(function(gesture){copy[gesture]=source[gesture]});
  return copy
}

function loadPromptShortcutBindings(){
  var bindings={};
  try{
    if(!window.localStorage)return bindings;
    var raw=window.localStorage.getItem(PROMPT_KIT_SHORTCUT_STORAGE_KEY);
    if(!raw)return bindings;
    var payload=JSON.parse(raw);
    if(!payload||payload.schema!==PROMPT_KIT_SHORTCUT_SCHEMA||!Array.isArray(payload.bindings))return bindings;
    payload.bindings.forEach(function(item){
      if(!item||typeof item.promptId!=='string')return;
      var promptId=normalizePromptShortcutId(item.promptId);
      if(promptId)bindings[promptId.toLowerCase()]=promptId
    })
  }catch(e){}
  return bindings
}

function persistPromptShortcutBindings(candidate){
  try{
    if(!window.localStorage)throw new Error('localStorage unavailable');
    var payload={schema:PROMPT_KIT_SHORTCUT_SCHEMA,bindings:Object.keys(candidate).sort().map(function(gesture){return{gesture:gesture,promptId:candidate[gesture]}})};
    window.localStorage.setItem(PROMPT_KIT_SHORTCUT_STORAGE_KEY,JSON.stringify(payload));
    return true
  }catch(e){
    showToast('Prompt shortcut save failed');
    return false
  }
}

function configuredPromptShortcutIds(){
  return Object.keys(promptShortcutBindings).sort(function(a,b){return Number(a.slice(1))-Number(b.slice(1))}).map(function(gesture){return promptShortcutBindings[gesture]})
}

function configurePromptShortcut(rawPromptId){
  var promptId=normalizePromptShortcutId(rawPromptId);
  if(!promptId){showToast('Use a prompt ID such as P95');return false}
  var prompt=PROMPTS.find(function(item){return item.id===promptId});
  if(!prompt){showToast(promptId+' is not in this Prompt Kit');return false}
  if(!isFavoritePrompt(promptId)){showToast('Favorite '+promptId+' before assigning its shortcut');return false}
  var candidate=clonePromptShortcutBindings(promptShortcutBindings);
  candidate[promptId.toLowerCase()]=promptId;
  if(!persistPromptShortcutBindings(candidate))return false;
  promptShortcutBindings=candidate;
  renderPromptShortcutBindings();
  showToast('Shortcut '+promptId.toLowerCase()+' saved','success');
  return true
}

function removePromptShortcut(rawPromptId){
  var promptId=normalizePromptShortcutId(rawPromptId);
  if(!promptId)return false;
  var gesture=promptId.toLowerCase();
  if(!promptShortcutBindings[gesture])return false;
  var candidate=clonePromptShortcutBindings(promptShortcutBindings);
  delete candidate[gesture];
  if(!persistPromptShortcutBindings(candidate))return false;
  promptShortcutBindings=candidate;
  renderPromptShortcutBindings();
  showToast('Removed shortcut '+gesture);
  return true
}

function renderPromptShortcutBindings(){
  var host=document.getElementById('promptShortcutBindings');
  if(!host)return;
  host.innerHTML='';
  var ids=configuredPromptShortcutIds();
  if(!ids.length){var empty=document.createElement('span');empty.className='hotkey-shortcut-empty';empty.textContent='No favorite prompt shortcuts configured.';host.appendChild(empty);return}
  ids.forEach(function(promptId){
    var row=document.createElement('div');row.className='hotkey-shortcut-row';
    var key=document.createElement('kbd');key.textContent=promptId.toLowerCase();
    var label=document.createElement('span');label.textContent='Copy '+promptId;
    var remove=document.createElement('button');remove.type='button';remove.className='hotkey-shortcut-remove';remove.setAttribute('aria-label','Remove '+promptId+' keyboard shortcut');remove.textContent='Remove';
    remove.addEventListener('click',function(){removePromptShortcut(promptId)});
    row.appendChild(key);row.appendChild(label);row.appendChild(remove);host.appendChild(row)
  })
}

function resetPromptShortcutBuffer(){
  promptShortcutBuffer='';
  if(promptShortcutBufferTimer){clearTimeout(promptShortcutBufferTimer);promptShortcutBufferTimer=null}
}

function schedulePromptShortcutBufferReset(){
  if(promptShortcutBufferTimer)clearTimeout(promptShortcutBufferTimer);
  promptShortcutBufferTimer=setTimeout(resetPromptShortcutBuffer,PROMPT_KIT_SHORTCUT_SEQUENCE_TIMEOUT_MS)
}

function openPromptShortcutTarget(promptId){
  var prompt=PROMPTS.find(function(item){return item.id===promptId});
  if(!prompt)return false;
  if(!isFavoritePrompt(promptId)){showToast(promptId+' is no longer a Favorite');return false}
  copyPrompt(promptId);
  return true
}

function handleConfiguredPromptShortcutKey(e,key){
  if(!/^[a-z0-9]$/.test(key)){resetPromptShortcutBuffer();return false}
  var gestures=Object.keys(promptShortcutBindings);
  if(!gestures.length){resetPromptShortcutBuffer();return false}
  var candidate=promptShortcutBuffer+key;
  var exact=promptShortcutBindings[candidate];
  if(exact){e.preventDefault();e.stopImmediatePropagation();resetPromptShortcutBuffer();openPromptShortcutTarget(exact);return true}
  var prefix=gestures.some(function(gesture){return gesture.indexOf(candidate)===0});
  if(prefix){e.preventDefault();e.stopImmediatePropagation();promptShortcutBuffer=candidate;schedulePromptShortcutBufferReset();return true}
  resetPromptShortcutBuffer();
  candidate=key;
  exact=promptShortcutBindings[candidate];
  if(exact){e.preventDefault();e.stopImmediatePropagation();openPromptShortcutTarget(exact);return true}
  prefix=gestures.some(function(gesture){return gesture.indexOf(candidate)===0});
  if(prefix){e.preventDefault();e.stopImmediatePropagation();promptShortcutBuffer=candidate;schedulePromptShortcutBufferReset();return true}
  return false
}

function setHotkeyHelpOpen(open,restoreFocus){
  var panel=document.getElementById('hotkeyHelpPanel');
  var toggle=document.getElementById('hotkeyHelpToggle');
  if(!panel||!toggle)return;
  panel.hidden=!open;
  toggle.setAttribute('aria-expanded',open?'true':'false');
  if(open){
    var close=panel.querySelector('.hotkey-help-close');
    if(close){try{close.focus({preventScroll:true})}catch(e){close.focus()}}
    return;
  }
  if(restoreFocus){try{toggle.focus({preventScroll:true})}catch(e){toggle.focus()}}
}

function ensureHotkeyHelp(){
  if(document.getElementById('hotkeyHelp'))return;
  if(!document.getElementById('prompt-kit-hotkey-help-styles')){
    var style=document.createElement('style');
    style.id='prompt-kit-hotkey-help-styles';
    style.textContent='.hotkey-help{position:fixed;right:80px;bottom:16px;z-index:45;font-family:inherit}.hotkey-help-toggle{display:inline-flex;align-items:center;gap:7px;min-height:40px;padding:8px 11px;border:1px solid rgba(56,189,248,.62);border-radius:999px;background:linear-gradient(135deg,rgba(14,116,144,.92),rgba(15,23,42,.96));color:var(--text-primary);font-size:11px;font-weight:800;letter-spacing:.03em;cursor:pointer;box-shadow:0 0 0 1px rgba(56,189,248,.14),0 0 18px rgba(56,189,248,.32),0 8px 24px rgba(0,0,0,.28);animation:hotkey-help-glow 2.8s ease-in-out infinite}.hotkey-help-toggle:hover,.hotkey-help-toggle:focus-visible{outline:none;border-color:var(--accent);box-shadow:0 0 0 3px var(--accent-glow),0 0 26px rgba(56,189,248,.46)}.hotkey-help-icon{font-size:15px;line-height:1}.hotkey-help-panel{position:absolute;right:0;bottom:calc(100% + 10px);width:min(292px,calc(100vw - 24px));max-height:min(520px,70vh);overflow:auto;padding:12px;border:1px solid rgba(56,189,248,.42);border-radius:12px;background:rgba(15,23,42,.98);box-shadow:0 0 0 1px rgba(56,189,248,.12),0 0 28px rgba(56,189,248,.22),0 18px 48px rgba(0,0,0,.46);backdrop-filter:blur(12px)}.hotkey-help-panel[hidden]{display:none}.hotkey-help-head{display:flex;align-items:center;justify-content:space-between;gap:10px;margin-bottom:8px;color:var(--text-primary);font-size:12px}.hotkey-help-close{display:inline-flex;align-items:center;justify-content:center;width:30px;height:30px;border:1px solid var(--border);border-radius:7px;background:var(--bg-surface);color:var(--text-secondary);cursor:pointer}.hotkey-help-close:hover,.hotkey-help-close:focus-visible{outline:none;border-color:var(--accent);color:var(--text-primary);box-shadow:0 0 0 2px var(--accent-glow)}.hotkey-help-list{display:grid;grid-template-columns:auto 1fr;gap:6px 10px;align-items:center}.hotkey-help-list kbd{min-width:28px;padding:3px 6px;border:1px solid var(--border);border-bottom-color:rgba(148,163,184,.65);border-radius:6px;background:var(--bg-surface);color:var(--accent);font:700 10px/1.3 ui-monospace,SFMono-Regular,Consolas,monospace;text-align:center}.hotkey-help-list span{color:var(--text-secondary);font-size:11px;line-height:1.35}@keyframes hotkey-help-glow{0%,100%{box-shadow:0 0 0 1px rgba(56,189,248,.12),0 0 14px rgba(56,189,248,.24),0 8px 24px rgba(0,0,0,.28)}50%{box-shadow:0 0 0 1px rgba(56,189,248,.24),0 0 24px rgba(56,189,248,.46),0 8px 28px rgba(0,0,0,.34)}}@media(max-width:760px){.hotkey-help{right:78px;bottom:16px}.hotkey-help-toggle{min-height:44px;padding:9px 12px}.hotkey-help-panel{position:fixed;right:12px;bottom:72px;width:calc(100vw - 24px);max-height:60vh}}@media(prefers-reduced-motion:reduce){.hotkey-help-toggle{animation:none}}';
    document.head.appendChild(style)
  }
  var shell=document.createElement('div');
  shell.className='hotkey-help';
  shell.id='hotkeyHelp';

  var toggle=document.createElement('button');
  toggle.className='hotkey-help-toggle';
  toggle.id='hotkeyHelpToggle';
  toggle.type='button';
  toggle.setAttribute('aria-expanded','false');
  toggle.setAttribute('aria-controls','hotkeyHelpPanel');
  toggle.setAttribute('aria-label','Open keyboard shortcut help');
  toggle.setAttribute('aria-keyshortcuts','`');
  toggle.innerHTML='<span class="hotkey-help-icon" aria-hidden="true">⌨</span><span>Hotkeys</span>';
  shell.appendChild(toggle);

  var panel=document.createElement('div');
  panel.className='hotkey-help-panel';
  panel.id='hotkeyHelpPanel';
  panel.hidden=true;
  panel.setAttribute('role','dialog');
  panel.setAttribute('aria-label','Keyboard shortcuts');

  var head=document.createElement('div');
  head.className='hotkey-help-head';
  var title=document.createElement('strong');
  title.textContent='Keyboard shortcuts';
  var close=document.createElement('button');
  close.className='hotkey-help-close';
  close.type='button';
  close.setAttribute('aria-label','Close keyboard shortcut help');
  close.textContent='×';
  head.appendChild(title);
  head.appendChild(close);
  panel.appendChild(head);

  var list=document.createElement('div');
  list.className='hotkey-help-list';
  PROMPT_KIT_SHORTCUTS.forEach(function(shortcut){
    var key=document.createElement('kbd');
    key.textContent=shortcut.key;
    var label=document.createElement('span');
    label.textContent=shortcut.label;
    list.appendChild(key);
    list.appendChild(label)
  });
  panel.appendChild(list);

  var config=document.createElement('div');
  config.className='hotkey-shortcut-config';
  var configTitle=document.createElement('strong');
  configTitle.textContent='Favorite prompt shortcuts';
  var configHint=document.createElement('span');
  configHint.className='hotkey-shortcut-hint';
  configHint.textContent='Favorite a prompt, enter its ID, then type that ID anywhere outside editable fields to copy it immediately.';
  var configControls=document.createElement('div');
  configControls.className='hotkey-shortcut-controls';
  var promptInput=document.createElement('input');
  promptInput.id='promptShortcutPromptId';
  promptInput.type='text';
  promptInput.inputMode='text';
  promptInput.autocomplete='off';
  promptInput.placeholder='P95';
  promptInput.setAttribute('aria-label','Favorite prompt ID for keyboard shortcut');
  var saveShortcut=document.createElement('button');
  saveShortcut.type='button';
  saveShortcut.textContent='Save';
  saveShortcut.setAttribute('aria-label','Save favorite prompt keyboard shortcut');
  configControls.appendChild(promptInput);configControls.appendChild(saveShortcut);
  var bindings=document.createElement('div');
  bindings.id='promptShortcutBindings';
  bindings.className='hotkey-shortcut-bindings';
  config.appendChild(configTitle);config.appendChild(configHint);config.appendChild(configControls);config.appendChild(bindings);
  panel.appendChild(config);
  shell.appendChild(panel);
  document.body.appendChild(shell);

  toggle.addEventListener('click',function(){setHotkeyHelpOpen(panel.hidden)});
  close.addEventListener('click',function(){setHotkeyHelpOpen(false,true)});
  saveShortcut.addEventListener('click',function(){if(configurePromptShortcut(promptInput.value))promptInput.value=''});
  promptInput.addEventListener('keydown',function(e){if(e.key==='Enter'){e.preventDefault();if(configurePromptShortcut(promptInput.value))promptInput.value=''}});
  document.addEventListener('click',function(e){if(!panel.hidden&&!shell.contains(e.target))setHotkeyHelpOpen(false,false)});
  if(!document.getElementById('prompt-kit-hotkey-config-styles')){
    var configStyle=document.createElement('style');configStyle.id='prompt-kit-hotkey-config-styles';
    configStyle.textContent='.hotkey-shortcut-config{margin-top:12px;padding-top:10px;border-top:1px solid var(--border);display:grid;gap:7px}.hotkey-shortcut-hint,.hotkey-shortcut-empty{color:var(--text-muted);font-size:10px;line-height:1.4}.hotkey-shortcut-controls{display:grid;grid-template-columns:minmax(0,1fr) auto;gap:6px}.hotkey-shortcut-controls input,.hotkey-shortcut-controls button,.hotkey-shortcut-remove{min-height:32px;border:1px solid var(--border);border-radius:6px;background:var(--bg-surface);color:var(--text-primary);font:inherit}.hotkey-shortcut-controls input{padding:5px 7px}.hotkey-shortcut-controls button,.hotkey-shortcut-remove{padding:5px 8px;cursor:pointer}.hotkey-shortcut-bindings{display:grid;gap:5px}.hotkey-shortcut-row{display:grid;grid-template-columns:auto minmax(0,1fr) auto;align-items:center;gap:7px;color:var(--text-secondary);font-size:10px}.hotkey-shortcut-row kbd{padding:3px 6px;border:1px solid var(--border);border-radius:6px;color:var(--accent);font:700 10px/1.3 ui-monospace,SFMono-Regular,Consolas,monospace}.hotkey-shortcut-remove{min-height:28px;font-size:9px}';
    document.head.appendChild(configStyle)
  }
  renderPromptShortcutBindings()
}

function installCompactBrowsingHotkeys(){
  document.addEventListener('keydown',function(e){
    var key=String(e.key||'').toLowerCase();
    var target=e.target;
    var editable=!!(target&&(target.tagName==='INPUT'||target.tagName==='TEXTAREA'||target.tagName==='SELECT'||target.isContentEditable));
    if(e.defaultPrevented||e.altKey||e.metaKey||e.ctrlKey)return;
    if(editable)return;
    if(key==='`'){
      e.preventDefault();e.stopImmediatePropagation();
      var helpPanel=document.getElementById('hotkeyHelpPanel');
      setHotkeyHelpOpen(helpPanel?helpPanel.hidden:true,false);
      resetPromptShortcutBuffer();
      return
    }
    if(key==='escape')resetPromptShortcutBuffer();
    var escapeHelpPanel=document.getElementById('hotkeyHelpPanel');
    if(key==='escape'&&escapeHelpPanel&&!escapeHelpPanel.hidden){
      e.preventDefault();e.stopImmediatePropagation();setHotkeyHelpOpen(false,true);return
    }
    if(promptShortcutBuffer&&handleConfiguredPromptShortcutKey(e,key))return;
    if(key==='1'){e.preventDefault();e.stopImmediatePropagation();activateAllPromptsView();return}
    if(key==='4'){e.preventDefault();e.stopImmediatePropagation();activateFavoritesView();return}
    if(key==='5'){
      var doctrine=document.querySelector('.cat-tab[data-cat="doctrine"]');
      if(doctrine){e.preventDefault();e.stopImmediatePropagation();doctrine.click()}
      return
    }
    if(key==='f'){e.preventDefault();e.stopImmediatePropagation();toggleCompactFilters();return}
    if(key==='['){e.preventDefault();e.stopImmediatePropagation();hideCompactFilters();return}
    if(key===']'){e.preventDefault();e.stopImmediatePropagation();showCompactFilters();return}
    if(key==='t'){e.preventDefault();e.stopImmediatePropagation();scrollPromptKitTo('top');return}
    if(key==='b'){e.preventDefault();e.stopImmediatePropagation();scrollPromptKitTo('bottom');return}
    handleConfiguredPromptShortcutKey(e,key)
  },true)
}

window.appendPromptCard=function(grid,p){
  var hex=COLORS[p.color.toLowerCase()]||'#64748b';
  var isGnhf=p.category==='gnhf';
  var safeId=escapePromptHtml(p.id),safeName=escapePromptHtml(p.name),safeType=escapePromptHtml(p.type),safeColor=escapePromptHtml(p.color),safeUseWhen=escapePromptHtml(p.useWhen),safeSprintRole=escapePromptHtml(p.sprintRole),safeProofGate=escapePromptHtml(p.proofGate);
  var card=document.createElement('div');
  card.className='prompt-card'+(isGnhf?' gnhf':'');
  card.tabIndex=0;
  card.setAttribute('role','group');
  card.setAttribute('data-prompt-id',p.id);
  card.setAttribute('aria-label',p.id+' '+p.name+'. Click or tap to copy. Double-click or press Enter to expand. Touch users may use Open.');
  card.innerHTML='<div class="glow-bar" style="background:'+hex+'"></div><div class="prompt-header"><span class="prompt-id">'+safeId+'</span>'+(isGnhf?'<span class="gnhf-badge">☾ GNHF</span>':'')+'<span class="prompt-name">'+safeName+'</span></div><div class="prompt-type">'+safeType+' · '+safeColor+'</div><div class="prompt-desc">'+safeUseWhen+'</div><div class="prompt-meta"><span class="prompt-badge">'+safeSprintRole+'</span><span class="prompt-badge">'+safeProofGate+'</span></div>';
  card.onclick=function(){cancelPromptCardCopy(card);card._copyTimer=setTimeout(function(){copyPrompt(p.id);card._copyTimer=null},300)};
  card.ondblclick=function(e){cancelPromptCardCopy(card);e.preventDefault();showPromptDetail(p.id,card)};
  card.onkeydown=function(e){if(e.target!==card)return;if(e.key==='Enter'){cancelPromptCardCopy(card);e.preventDefault();e.stopPropagation();showPromptDetail(p.id,card)}else if(e.key===' '){cancelPromptCardCopy(card);e.preventDefault();e.stopPropagation();copyPrompt(p.id)}};

  var actions=document.createElement('div');
  actions.className='prompt-card-actions';
  actions.setAttribute('aria-label',p.id+' prompt actions');

  var favBtn=document.createElement('button');
  favBtn.className='prompt-favorite-btn'+(isFavoritePrompt(p.id)?' active':'');
  favBtn.textContent=isFavoritePrompt(p.id)?'★':'☆';
  favBtn.setAttribute('aria-label',(isFavoritePrompt(p.id)?'Remove ':'Add ')+p.id+(isFavoritePrompt(p.id)?' from Favorites':' to Favorites'));
  favBtn.setAttribute('aria-pressed',isFavoritePrompt(p.id)?'true':'false');
  favBtn.title=isFavoritePrompt(p.id)?'Remove from Favorites':'Save to Favorites';
  favBtn.onclick=function(e){cancelPromptCardCopy(card);e.preventDefault();e.stopPropagation();toggleFavoritePrompt(p.id)};
  actions.appendChild(favBtn);

  var openBtn=document.createElement('button');
  openBtn.className='prompt-open-btn';
  openBtn.textContent='Open';
  openBtn.setAttribute('aria-label','Open '+p.id+' prompt detail');
  openBtn.onclick=function(e){cancelPromptCardCopy(card);e.stopPropagation();showPromptDetail(p.id,card)};
  actions.appendChild(openBtn);

  var copyBtn=document.createElement('button');
  copyBtn.className='prompt-copy-btn';
  copyBtn.textContent='Copy';
  copyBtn.setAttribute('aria-label','Copy '+p.id+' prompt');
  copyBtn.onclick=function(e){e.stopPropagation();copyPrompt(p.id);copyBtn.classList.add('copied');copyBtn.textContent='Copied!';setTimeout(function(){copyBtn.classList.remove('copied');copyBtn.textContent='Copy'},1500)};
  actions.appendChild(copyBtn);

  card.appendChild(actions);
  grid.appendChild(card)
};

ensurePromptKitPolishStyles();
ensureCompactBrowsingControls();
ensureHotkeyHelp();
installCompactBrowsingViewSwitches();
installCompactBrowsingHotkeys();
render();
})();
