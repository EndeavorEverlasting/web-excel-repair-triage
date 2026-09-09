(function(){
'use strict';
var copyToastTimer=null;
var PROMPT_KIT_SHORTCUT_SEQUENCE_TIMEOUT_MS=1200;
var PROMPT_KIT_COPY_CONFIRMATION_PREVIEW_CHARS=420;
var PROMPT_KIT_COPY_CONFIRMATION_TOAST_MS=4200;
var sharedPromptShortcutBindings=computeSharedPromptShortcutBindings();
var promptShortcutBuffer='';
var promptShortcutBufferTimer=null;

function ensurePromptKitPolishStyles(){
  if(document.getElementById('prompt-kit-polish-styles'))return;
  var style=document.createElement('style');
  style.id='prompt-kit-polish-styles';
  style.textContent='.prompt-card .prompt-header{padding-right:176px;min-height:34px}.prompt-card-actions{position:absolute;top:12px;right:12px;display:flex;align-items:center;justify-content:flex-end;gap:6px;z-index:3;max-width:168px}.prompt-card-actions .prompt-favorite-btn,.prompt-card-actions .prompt-open-btn,.prompt-card-actions .prompt-copy-btn{position:static!important;top:auto!important;right:auto!important;margin:0!important;opacity:1!important;display:inline-flex;align-items:center;justify-content:center;min-height:30px;box-sizing:border-box}.prompt-card-actions .prompt-favorite-btn{width:30px;min-width:30px}.prompt-card-actions .prompt-open-btn,.prompt-card-actions .prompt-copy-btn{padding:4px 8px;white-space:nowrap}.prompt-card.copy-confirmed{animation:prompt-copy-confirm 800ms ease-out}.prompt-card.copy-confirmed .glow-bar{background:var(--success)!important;box-shadow:0 0 12px rgba(34,197,94,.9),0 0 28px rgba(34,197,94,.45)!important}.toast.success{border-color:var(--success);background:linear-gradient(135deg,rgba(20,83,45,.96),rgba(17,24,39,.98));color:#dcfce7;box-shadow:0 0 0 1px rgba(34,197,94,.2),0 0 24px rgba(34,197,94,.42),0 10px 34px rgba(0,0,0,.42)}.toast.success.copy-confirmation{max-width:min(720px,92vw);white-space:normal;display:flex;flex-direction:column;gap:6px;align-items:stretch;padding:10px 14px}.toast-copy-label{font-weight:700;color:#dcfce7;font-size:12px;line-height:1.35}.toast-copy-preview{margin:0;max-height:9.5em;overflow:auto;white-space:pre-wrap;word-break:break-word;font:11px/1.45 ui-monospace,SFMono-Regular,Menlo,Consolas,monospace;color:#bbf7d0;opacity:.95}.toast.success.show{animation:prompt-toast-success 1.7s ease both}.toast.success.copy-confirmation.show{animation:prompt-toast-copy-confirmation 4.2s ease both}.header-top{display:grid;grid-template-columns:minmax(0,1fr) auto minmax(280px,400px);align-items:center;gap:12px 16px}.header-top>.logo{grid-column:1;min-width:0}.filter-panel-toggle{grid-column:2;display:inline-flex;align-items:center;justify-content:center;justify-self:end;min-height:34px;padding:6px 10px;border:1px solid var(--border);border-radius:7px;background:var(--bg-surface);color:var(--text-secondary);font-size:11px;font-weight:600;cursor:pointer;white-space:nowrap;transition:all .2s}.header-top>.search-container{grid-column:3;min-width:0;width:100%;max-width:none}.header-top>.header-controls{grid-column:1/-1;min-width:0;width:100%;justify-self:stretch;justify-content:flex-end;flex-wrap:wrap}.filter-panel-toggle:hover,.filter-panel-toggle:focus-visible{outline:none;border-color:var(--accent);color:var(--text-primary);box-shadow:0 0 0 2px var(--accent-glow)}.header.filters-collapsed{padding-bottom:8px}.header.filters-collapsed .search-container,.header.filters-collapsed .header-controls,.header.filters-collapsed .sections-nav,.header.filters-collapsed .type-nav{display:none!important}.header.filters-collapsed .header-top{padding-bottom:0}.header.filters-collapsed .filter-panel-toggle{justify-self:end;margin-left:0}.mobile-favorites-quick{display:none;align-items:center;justify-content:center;min-height:44px;padding:8px 12px;border:1px solid rgba(245,158,11,.45);border-radius:8px;background:rgba(245,158,11,.08);color:#fbbf24;font-size:12px;font-weight:800;letter-spacing:.02em;cursor:pointer;touch-action:manipulation}.mobile-favorites-quick:hover,.mobile-favorites-quick:focus-visible{outline:none;border-color:#f59e0b;box-shadow:0 0 0 2px rgba(245,158,11,.18)}@keyframes prompt-copy-confirm{0%{border-color:var(--success);box-shadow:0 0 0 1px rgba(34,197,94,.7),0 0 30px rgba(34,197,94,.42);transform:translateY(-1px) scale(1.006)}45%{border-color:rgba(34,197,94,.78);box-shadow:0 0 22px rgba(34,197,94,.3)}100%{border-color:var(--border);box-shadow:none;transform:none}}@keyframes prompt-toast-success{0%{opacity:0;transform:translate(-50%,12px) scale(.96)}12%{opacity:1;transform:translate(-50%,0) scale(1.03)}24%,82%{opacity:1;transform:translate(-50%,0) scale(1)}100%{opacity:0;transform:translate(-50%,-4px) scale(.99)}}@keyframes prompt-toast-copy-confirmation{0%{opacity:0;transform:translate(-50%,12px) scale(.96)}8%{opacity:1;transform:translate(-50%,0) scale(1.02)}16%,88%{opacity:1;transform:translate(-50%,0) scale(1)}100%{opacity:0;transform:translate(-50%,-4px) scale(.99)}}@media(max-width:980px){.header-top{grid-template-columns:minmax(0,1fr) auto}.header-top>.logo{grid-column:1}.filter-panel-toggle{grid-column:2}.header-top>.search-container{grid-column:1/-1;max-width:none}.header-top>.header-controls{grid-column:1/-1}}@media(max-width:760px){.prompt-card .prompt-header{padding-right:0;min-height:0}.prompt-card-actions{position:static;max-width:none;width:100%;display:grid;grid-template-columns:44px minmax(72px,1fr) minmax(72px,1fr);gap:8px;margin-top:12px}.prompt-card-actions .prompt-favorite-btn,.prompt-card-actions .prompt-open-btn,.prompt-card-actions .prompt-copy-btn{width:100%;min-height:42px;margin:0!important}.header{padding-left:12px;padding-right:12px}.header-top{grid-template-columns:minmax(0,1fr) auto;gap:8px}.filter-panel-toggle{min-height:40px;justify-self:end}.header-top>.search-container{grid-column:1/-1;width:100%}.header-top>.header-controls{grid-column:1/-1;display:grid;grid-template-columns:minmax(0,1fr);width:100%;justify-items:stretch;gap:8px}.header-top>.header-controls .cat-tabs{max-width:100%;overflow-x:auto;-webkit-overflow-scrolling:touch;scrollbar-width:none}.header-top>.header-controls .cat-tabs::-webkit-scrollbar{display:none}.header-top>.header-controls .cat-tab{min-height:42px}.header-top>.header-controls .add-prompt-btn{justify-content:center;min-height:42px}.header-top>.header-controls .stats{justify-content:center}.header-top>.mobile-favorites-quick{display:inline-flex;width:100%;grid-column:1/-1}.header.filters-collapsed .header-top{grid-template-columns:minmax(0,1fr) auto}}@media(prefers-reduced-motion:reduce){.prompt-card.copy-confirmed,.toast.success.show,.toast.success.copy-confirmation.show{animation:none}.toast.success.show,.toast.success.copy-confirmation.show{opacity:1}}';
  document.head.appendChild(style)
}

function clearToastCopyConfirmationState(toastEl){
  if(!toastEl)return;
  toastEl.classList.remove('copy-confirmation');
  toastEl.removeAttribute('data-copy-confirmation');
  toastEl.removeAttribute('data-prompt-id');
  toastEl.removeAttribute('data-copy-preview');
}

function formatCopyConfirmationPreview(copyContent,limit){
  var text=String(copyContent==null?'':copyContent).replace(/\r\n/g,'\n');
  var max=typeof limit==='number'?limit:PROMPT_KIT_COPY_CONFIRMATION_PREVIEW_CHARS;
  if(!text)return '';
  if(text.length<=max)return text;
  var sliced=text.slice(0,Math.max(0,max-1));
  var boundary=sliced.lastIndexOf('\n');
  if(boundary<Math.floor(max*0.55))boundary=sliced.lastIndexOf(' ');
  if(boundary>=Math.floor(max*0.4))sliced=sliced.slice(0,boundary);
  return sliced.replace(/\s+$/,'')+'…';
}

function buildCopyConfirmationToastModel(promptId,copyContent){
  var id=String(promptId||'');
  var preview=formatCopyConfirmationPreview(copyContent);
  return {
    promptId:id,
    label:id?'✓ Copied to clipboard · '+id:'✓ Copied to clipboard',
    preview:preview,
    copyContent:String(copyContent==null?'':copyContent)
  };
}

function renderCopyConfirmationToast(toastEl,model){
  if(!toastEl||!model)return false;
  clearToastCopyConfirmationState(toastEl);
  toastEl.textContent='';
  toastEl.setAttribute('data-copy-confirmation','1');
  toastEl.setAttribute('data-prompt-id',model.promptId||'');
  toastEl.setAttribute('data-copy-preview',model.preview||'');
  toastEl.classList.add('copy-confirmation');
  var label=document.createElement('div');
  label.className='toast-copy-label';
  label.textContent=model.label;
  toastEl.appendChild(label);
  if(model.preview){
    var preview=document.createElement('pre');
    preview.className='toast-copy-preview';
    preview.setAttribute('aria-label','Copied prompt preview');
    preview.textContent=model.preview;
    toastEl.appendChild(preview);
  }
  return true;
}

window.formatCopyConfirmationPreview=formatCopyConfirmationPreview;
window.buildCopyConfirmationToastModel=buildCopyConfirmationToastModel;
window.renderCopyConfirmationToast=renderCopyConfirmationToast;

window.showToast=function(msg,tone){
  var t=document.getElementById('toast');
  if(!t)return;
  if(copyToastTimer){clearTimeout(copyToastTimer);copyToastTimer=null}
  clearToastCopyConfirmationState(t);
  t.textContent=msg;
  t.classList.remove('success');
  if(tone)t.classList.add(tone);
  t.classList.add('show');
  copyToastTimer=setTimeout(function(){t.classList.remove('show');t.classList.remove('success');clearToastCopyConfirmationState(t);copyToastTimer=null},1800)
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
  var promptId=String(id||'');
  var catalog=typeof PROMPTS!=='undefined'&&Array.isArray(PROMPTS)?PROMPTS:[];
  var prompt=catalog.find(function(item){return item&&item.id===promptId});
  var copyContent=prompt&&prompt.copyContent?prompt.copyContent:'';
  var model=buildCopyConfirmationToastModel(promptId,copyContent);
  var toast=document.getElementById('toast');
  if(toast){
    if(copyToastTimer){clearTimeout(copyToastTimer);copyToastTimer=null}
    renderCopyConfirmationToast(toast,model);
    toast.classList.remove('success');
    toast.classList.add('success','show');
    copyToastTimer=setTimeout(function(){
      toast.classList.remove('show');
      toast.classList.remove('success');
      clearToastCopyConfirmationState(toast);
      toast.textContent='';
      copyToastTimer=null;
    },PROMPT_KIT_COPY_CONFIRMATION_TOAST_MS);
  }
  var selector='[data-prompt-id="'+promptId.replace(/"/g,'')+'"]';
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

function ensureFavoritesGroupJumpStyles(){
  if(document.getElementById('favorites-group-jump-styles'))return;
  var style=document.createElement('style');
  style.id='favorites-group-jump-styles';
  style.textContent='.favorites-group-jump-nav{grid-column:1/-1;display:flex;align-items:center;gap:8px;max-width:100%;overflow-x:auto;-webkit-overflow-scrolling:touch;scrollbar-width:none;padding:4px 0 10px}.favorites-group-jump-nav::-webkit-scrollbar{display:none}.favorites-group-jump-label{flex:0 0 auto;color:var(--text-muted);font-size:10px;font-weight:800;letter-spacing:.06em;text-transform:uppercase}.favorite-group-jump{display:inline-flex;align-items:center;justify-content:center;flex:0 0 auto;min-height:38px;padding:7px 10px;border:1px solid var(--border);border-radius:999px;background:var(--bg-surface);color:var(--text-secondary);font-size:11px;font-weight:700;text-decoration:none;touch-action:manipulation}.favorite-group-jump:hover,.favorite-group-jump:focus-visible{outline:none;border-color:#f59e0b;color:#fbbf24;box-shadow:0 0 0 2px rgba(245,158,11,.16)}.section-divider.favorite-group-jump-target{scroll-margin-top:12px}@media(max-width:760px){.favorites-group-jump-nav{padding:2px 0 8px}.favorite-group-jump{min-height:44px;padding:8px 12px}}';
  document.head.appendChild(style)
}

function ensureFavoritesJourneyStyles(){
  if(document.getElementById('favorites-journey-styles'))return;
  var style=document.createElement('style');
  style.id='favorites-journey-styles';
  style.textContent='.favorites-empty-state{grid-column:1/-1;display:flex;flex-direction:column;align-items:center;justify-content:center;gap:10px;min-height:220px;padding:28px 20px;border:1px dashed var(--border);border-radius:12px;background:var(--bg-surface);text-align:center}.favorites-empty-icon{font-size:30px;line-height:1;color:#fbbf24}.favorites-empty-title{margin:0;color:var(--text-primary);font-size:18px}.favorites-empty-copy{max-width:520px;margin:0;color:var(--text-secondary);font-size:12px;line-height:1.55}.favorites-empty-action{display:inline-flex;align-items:center;justify-content:center;min-height:42px;padding:8px 14px;border:1px solid var(--accent);border-radius:8px;background:var(--accent-glow);color:var(--text-primary);font-size:12px;font-weight:800;cursor:pointer;touch-action:manipulation}.favorites-empty-action:hover,.favorites-empty-action:focus-visible{outline:none;box-shadow:0 0 0 2px var(--accent-glow)}@media(max-width:760px){.favorites-empty-state{min-height:190px;padding:24px 16px}.favorites-empty-action{width:100%;min-height:48px}}';
  document.head.appendChild(style)
}

function storedFavoritePromptCount(){
  return Object.keys(favoritePromptIds||{}).filter(function(id){return favoritePromptIds[id]===true}).length
}

function currentFavoritePromptCount(){
  var catalog=typeof PROMPTS!=='undefined'&&Array.isArray(PROMPTS)?PROMPTS:[];
  return catalog.filter(function(prompt){return prompt&&isFavoritePrompt(prompt.id)}).length
}

function renderFavoritesEmptyState(grid){
  if(!grid||activeSection!=='__favorites__')return false;
  var storedCount=storedFavoritePromptCount();
  var savedCount=currentFavoritePromptCount();
  var state=document.createElement('section');
  state.id='favoritesEmptyState';
  state.className='favorites-empty-state';
  state.setAttribute('role','status');
  state.setAttribute('aria-live','polite');
  var icon=document.createElement('div');
  icon.className='favorites-empty-icon';
  icon.setAttribute('aria-hidden','true');
  icon.textContent='★';
  var title=document.createElement('h2');
  title.className='favorites-empty-title';
  var copy=document.createElement('p');
  copy.className='favorites-empty-copy';
  var action=document.createElement('button');
  action.className='favorites-empty-action';
  action.type='button';
  if(storedCount===0){
    state.setAttribute('data-empty-kind','none-saved');
    title.textContent='No Favorites yet';
    copy.textContent='Star any prompt to save it here. Your Favorites stay in this browser for quick return visits.';
    action.textContent='Browse all prompts';
    action.setAttribute('aria-label','Browse all prompts');
    action.addEventListener('click',function(){activateAllPromptsView()})
  }else if(savedCount===0){
    state.setAttribute('data-empty-kind','unavailable');
    title.textContent='Saved Favorites unavailable in this version';
    copy.textContent='This browser still remembers saved prompt IDs, but none exist in the current Prompt Kit registry. Your saved IDs are preserved for portability.';
    action.textContent='Browse current prompts';
    action.setAttribute('aria-label','Browse current prompts');
    action.addEventListener('click',function(){activateAllPromptsView()})
  }else{
    state.setAttribute('data-empty-kind','filtered');
    title.textContent='No Favorites match these filters';
    copy.textContent='You still have saved Favorites available in this version. Clear the current search and prompt filters to show them again.';
    action.textContent='Clear Favorites filters';
    action.setAttribute('aria-label','Clear Favorites filters');
    action.addEventListener('click',function(){clearTransientPromptFilters();renderTypes();render()})
  }
  state.appendChild(icon);
  state.appendChild(title);
  state.appendChild(copy);
  state.appendChild(action);
  grid.appendChild(state);
  return true
}

function favoriteGroupJumpId(name,index){
  var slug=String(name||'group').toLowerCase().replace(/[^a-z0-9]+/g,'-').replace(/^-+|-+$/g,'')||'group';
  return 'favorite-group-'+String(index+1)+'-'+slug
}

function renderFavoritesGroupJumpNavigation(){
  var grid=document.getElementById('grid');
  if(!grid)return;
  var existing=document.getElementById('favoritesGroupJumpNav');
  if(existing&&existing.parentNode)existing.parentNode.removeChild(existing);
  var existingEmpty=document.getElementById('favoritesEmptyState');
  if(existingEmpty&&existingEmpty.parentNode)existingEmpty.parentNode.removeChild(existingEmpty);
  grid.querySelectorAll('.section-divider.favorite-group-jump-target').forEach(function(divider){divider.classList.remove('favorite-group-jump-target');divider.removeAttribute('id')});
  if(activeSection!=='__favorites__')return;
  var dividers=Array.prototype.slice.call(grid.querySelectorAll('.section-divider[data-category]'));
  if(!dividers.length){renderFavoritesEmptyState(grid);return}
  var nav=document.createElement('nav');
  nav.id='favoritesGroupJumpNav';
  nav.className='favorites-group-jump-nav';
  nav.setAttribute('aria-label','Saved favorite groups');
  var label=document.createElement('span');
  label.className='favorites-group-jump-label';
  label.textContent='Saved groups';
  nav.appendChild(label);
  dividers.forEach(function(divider,index){
    var name=divider.getAttribute('data-category')||'Group';
    var countNode=divider.querySelector('.sd-count');
    var countText=countNode?String(countNode.textContent||'').trim():'';
    var id=favoriteGroupJumpId(name,index);
    divider.id=id;
    divider.classList.add('favorite-group-jump-target');
    var link=document.createElement('a');
    link.className='favorite-group-jump';
    link.href='#'+id;
    link.setAttribute('data-favorite-group',name);
    link.setAttribute('aria-label','Jump to saved favorite group '+name+(countText?' · '+countText:''));
    link.textContent=name+(countText?' · '+countText:'');
    link.addEventListener('click',function(e){
      e.preventDefault();
      var target=document.getElementById(id);
      if(!target)return;
      try{target.scrollIntoView({block:'start',behavior:hotkeyScrollBehavior()})}catch(err){target.scrollIntoView(true)}
      var toggle=target.querySelector('.section-toggle');
      if(toggle){try{toggle.focus({preventScroll:true})}catch(err){toggle.focus()}}
    });
    nav.appendChild(link)
  });
  grid.insertBefore(nav,grid.firstChild)
}

function installFavoritesGroupJumpNavigation(){
  var baseRender=window.render;
  if(typeof baseRender!=='function'||baseRender.__favoritesGroupJumpWrapped)return false;
  var wrapped=function(){baseRender();renderFavoritesGroupJumpNavigation()};
  wrapped.__favoritesGroupJumpWrapped=true;
  window.render=wrapped;
  return true
}

function ensureCompactBrowsingControls(){
  var header=document.querySelector('.header');
  var headerTop=document.querySelector('.header-top');
  var search=document.querySelector('.search-container');
  var catTabs=document.querySelector('.cat-tabs');
  if(!header||!headerTop||!catTabs)return;

  if(!document.getElementById('mobileFavoritesQuick')){
    var mobileFavoritesQuick=document.createElement('button');
    mobileFavoritesQuick.className='mobile-favorites-quick';
    mobileFavoritesQuick.id='mobileFavoritesQuick';
    mobileFavoritesQuick.type='button';
    mobileFavoritesQuick.setAttribute('data-view','favorites');
    mobileFavoritesQuick.setAttribute('aria-label','Open saved favorite prompts');
    mobileFavoritesQuick.textContent='★ Favorites';
    mobileFavoritesQuick.addEventListener('click',function(e){e.preventDefault();e.stopPropagation();activateFavoritesView()});
    if(search)headerTop.insertBefore(mobileFavoritesQuick,search);else headerTop.appendChild(mobileFavoritesQuick)
  }

  if(!document.getElementById('favoritesShortcut')){
    var favoritesButton=document.createElement('button');
    favoritesButton.className='cat-tab profile-slot';
    favoritesButton.id='favoritesShortcut';
    favoritesButton.type='button';
    favoritesButton.dataset.profileSlot='C';
    favoritesButton.setAttribute('data-view','favorites');
    favoritesButton.setAttribute('aria-label','Show saved favorite prompts');
    favoritesButton.setAttribute('aria-keyshortcuts','C');
    favoritesButton.innerHTML='<span class="tab-icon">★</span>Favorites<span class="kbd">C</span>';
    favoritesButton.addEventListener('click',function(e){e.preventDefault();e.stopPropagation();activateFavoritesView()});
    catTabs.appendChild(favoritesButton)
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
  {key:'126',label:'Prompt number → copy + snap to P126'},
  {key:'A',label:'All'},
  {key:'B',label:'Standard'},
  {key:'C',label:'Favorites'},
  {key:'D',label:'SAS'},
  {key:'E',label:'PM'},
  {key:'/',label:'Focus search'},
  {key:'R',label:'Reference panel'},
  {key:'F',label:'Show / hide filters'},
  {key:'[',label:'Hide filters'},
  {key:']',label:'Show filters'},
  {key:'Home',label:'Scroll to top'},
  {key:'End',label:'Scroll to bottom'},
  {key:'Esc',label:'Close / clear active surface'}
];

function hotkeyScrollBehavior(){
  try{return window.matchMedia&&window.matchMedia('(prefers-reduced-motion: reduce)').matches?'auto':'smooth'}catch(e){return 'auto'}
}

function scrollPromptKitTo(edge){
  var behavior=hotkeyScrollBehavior();
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


var MOBILE_QUICK_PROFILE_KEYS=['A','B','C','D','E'];

function mobileQuickCurrentProfileKey(){
  try{
    if(window.PromptKitProfiles&&typeof window.PromptKitProfiles.getState==='function'){
      var state=window.PromptKitProfiles.getState();
      if(state&&MOBILE_QUICK_PROFILE_KEYS.indexOf(state.activeKey)>=0)return state.activeKey
    }
  }catch(e){}
  var active=document.querySelector('.cat-tab.profile-slot.active[data-profile-slot]');
  var key=active&&active.getAttribute('data-profile-slot');
  return MOBILE_QUICK_PROFILE_KEYS.indexOf(key)>=0?key:'A'
}

function mobileQuickCycleProfile(delta){
  if(!window.PromptKitProfiles||typeof window.PromptKitProfiles.activateSlot!=='function')return false;
  var current=mobileQuickCurrentProfileKey();
  var index=MOBILE_QUICK_PROFILE_KEYS.indexOf(current);
  var next=(index+delta+MOBILE_QUICK_PROFILE_KEYS.length)%MOBILE_QUICK_PROFILE_KEYS.length;
  window.PromptKitProfiles.activateSlot(MOBILE_QUICK_PROFILE_KEYS[next]);
  return true
}

function mobileQuickFocusSearch(){
  showCompactFilters();
  var search=document.getElementById('search');
  if(!search)return false;
  try{search.focus()}catch(e){return false}
  try{search.scrollIntoView({block:'center',inline:'nearest'})}catch(e){}
  return true
}

function performMobileQuickAction(action,origin){
  if(action!=='panel')setHotkeyHelpOpen(false,false);
  if(action==='find'){
    if(typeof window.openPromptFinder==='function'){
      window.openPromptFinder(origin||document.getElementById('hotkeyHelpToggle'));
      return true
    }
    return mobileQuickFocusSearch()
  }
  if(action==='search')return mobileQuickFocusSearch();
  if(action==='profile-prev')return mobileQuickCycleProfile(-1);
  if(action==='profile-next')return mobileQuickCycleProfile(1);
  if(action==='favorites'){activateFavoritesView();return true}
  if(action==='filters'){toggleCompactFilters();return true}
  if(action==='reference'){
    if(typeof toggleRef==='function'){toggleRef();return true}
    return false
  }
  if(action==='top'){scrollPromptKitTo('top');return true}
  if(action==='bottom'){scrollPromptKitTo('bottom');return true}
  return false
}

function mobilePromptJumpDigits(raw){
  return String(raw||'').replace(/\D+/g,'').slice(0,6)
}

function mobilePromptJumpPrompt(promptId){
  var catalog=typeof PROMPTS!=='undefined'&&Array.isArray(PROMPTS)?PROMPTS:[];
  return catalog.find(function(item){return item&&item.id===promptId})||null
}

function mobilePromptJumpHasPrefix(promptId){
  var catalog=typeof PROMPTS!=='undefined'&&Array.isArray(PROMPTS)?PROMPTS:[];
  return catalog.some(function(item){return item&&typeof item.id==='string'&&item.id!==promptId&&item.id.indexOf(promptId)===0})
}

function setMobilePromptJumpSubmitState(promptId,exact,longer){
  var go=document.querySelector('#mobilePromptJumpForm .mobile-prompt-jump-go');
  if(!go)return;
  if(exact){
    go.disabled=false;
    go.textContent=longer?'Go to '+promptId:'Go';
    go.setAttribute('aria-label',longer?'Go to exact '+promptId:'Go to exact prompt ID')
  }else{
    go.disabled=true;
    go.textContent='Go';
    go.setAttribute('aria-label','Go to exact prompt ID')
  }
}

function setMobilePromptJumpOpen(open,restoreFocus){
  var form=document.getElementById('mobilePromptJumpForm');
  var toggle=document.getElementById('mobilePromptJumpToggle');
  var input=document.getElementById('mobilePromptJumpInput');
  if(!form||!toggle)return false;
  form.hidden=!open;
  toggle.setAttribute('aria-expanded',open?'true':'false');
  if(open&&input){
    input.value='';
    var status=document.getElementById('mobilePromptJumpStatus');
    if(status)status.textContent='Type the digits after P. Example: 111.';
    setMobilePromptJumpSubmitState('',false,false);
    try{input.focus({preventScroll:true})}catch(e){input.focus()}
  }else if(restoreFocus){
    try{toggle.focus({preventScroll:true})}catch(e){toggle.focus()}
  }
  return true
}

function resolveMobilePromptJump(force){
  var input=document.getElementById('mobilePromptJumpInput');
  var status=document.getElementById('mobilePromptJumpStatus');
  var toggle=document.getElementById('mobilePromptJumpToggle');
  if(!input)return false;
  var digits=mobilePromptJumpDigits(input.value);
  if(input.value!==digits)input.value=digits;
  if(!digits){setMobilePromptJumpSubmitState('',false,false);if(status)status.textContent='Type the digits after P. Example: 111.';return false}
  var promptId='P'+digits;
  var prompt=mobilePromptJumpPrompt(promptId);
  var longer=mobilePromptJumpHasPrefix(promptId);
  if(prompt&&(!longer||force)){
    setMobilePromptJumpSubmitState(promptId,true,longer);
    if(!revealPromptShortcutTarget(promptId,'instant')){
      if(status)status.textContent=promptId+' could not be centered in the prompt library.';
      return false
    }
    setMobilePromptJumpOpen(false,false);
    setHotkeyHelpOpen(false,false);
    var card=document.querySelector('[data-prompt-id="'+promptId+'"]');
    if(card){
      try{card.focus({preventScroll:true})}catch(e){try{card.focus()}catch(ignore){}}
      if(typeof showToast==='function')showToast(promptId+' ready — tap the prompt card to copy');
      return true
    }
    if(status)status.textContent='Prompt card is unavailable.';
    return false
  }
  if(prompt&&longer){
    setMobilePromptJumpSubmitState(promptId,true,true);
    if(status)status.textContent=promptId+' is exact. Press Enter or tap Go to '+promptId+', or keep typing for a longer ID.';
    return false
  }
  var catalog=typeof PROMPTS!=='undefined'&&Array.isArray(PROMPTS)?PROMPTS:[];
  var hasCandidate=catalog.some(function(item){return item&&typeof item.id==='string'&&item.id.indexOf(promptId)===0});
  setMobilePromptJumpSubmitState(promptId,false,false);
  if(status)status.textContent=hasCandidate?'Keep typing '+promptId+'…':'No prompt starts with '+promptId+'.';
  return false
}

function installMobilePromptJump(shell){
  if(!shell||document.getElementById('mobilePromptJump'))return;
  if(!document.getElementById('mobile-prompt-jump-styles')){
    var style=document.createElement('style');
    style.id='mobile-prompt-jump-styles';
    style.textContent='.mobile-prompt-jump{display:none}.mobile-prompt-jump-form[hidden]{display:none}@media(max-width:760px){.hotkey-help{display:flex;align-items:flex-end;gap:8px;right:12px;bottom:12px}.mobile-prompt-jump{display:block;position:relative}.mobile-prompt-jump-toggle,.hotkey-help-toggle{min-height:52px;border-radius:999px;touch-action:manipulation!important}.mobile-prompt-jump-toggle{display:inline-flex;align-items:center;justify-content:center;padding:8px 14px;border:1px solid rgba(56,189,248,.75);background:linear-gradient(135deg,rgba(2,132,199,.96),rgba(15,23,42,.98));color:var(--text-primary);font:800 12px/1 inherit;box-shadow:0 0 0 1px rgba(56,189,248,.14),0 0 18px rgba(56,189,248,.28),0 8px 24px rgba(0,0,0,.28)}.mobile-prompt-jump-toggle:focus-visible{outline:none;box-shadow:0 0 0 3px var(--accent-glow),0 0 24px rgba(56,189,248,.4)}.mobile-prompt-jump-form{position:fixed;right:12px;bottom:74px;width:min(300px,calc(100vw - 24px));display:grid;grid-template-columns:auto minmax(0,1fr) auto;align-items:center;gap:8px;padding:10px;border:1px solid rgba(56,189,248,.55);border-radius:12px;background:rgba(15,23,42,.99);box-shadow:0 14px 40px rgba(0,0,0,.48);z-index:47}.mobile-prompt-jump-prefix{font:900 18px/1 ui-monospace,SFMono-Regular,Consolas,monospace;color:var(--accent)}.mobile-prompt-jump-input{min-width:0;height:48px;box-sizing:border-box;padding:8px 10px;border:1px solid var(--border);border-radius:8px;background:var(--bg-surface);color:var(--text-primary);font:800 18px/1 ui-monospace,SFMono-Regular,Consolas,monospace}.mobile-prompt-jump-go{min-width:52px;height:48px;border:1px solid var(--accent);border-radius:8px;background:var(--accent-glow);color:var(--text-primary);font:800 12px/1 inherit}.mobile-prompt-jump-go:disabled{opacity:.45;cursor:not-allowed}.mobile-prompt-jump-status{grid-column:1/-1;min-height:16px;color:var(--text-secondary);font-size:10px;line-height:1.35}.mobile-quick-label{display:inline}.hotkey-panel-title{display:none}.mobile-quick-panel-title{display:inline}.hotkey-help-panel{width:min(340px,calc(100vw - 24px));max-height:min(460px,58vh)}.hotkey-help-list,.hotkey-shortcut-config,.prompt-profile-editor{display:none!important}.mobile-quick-handle-cue{display:none!important}}';
    document.head.appendChild(style)
  }
  var jump=document.createElement('div');
  jump.className='mobile-prompt-jump';
  jump.id='mobilePromptJump';
  var toggle=document.createElement('button');
  toggle.className='mobile-prompt-jump-toggle';
  toggle.id='mobilePromptJumpToggle';
  toggle.type='button';
  toggle.textContent='Go to P#';
  toggle.setAttribute('aria-expanded','false');
  toggle.setAttribute('aria-controls','mobilePromptJumpForm');
  toggle.setAttribute('aria-label','Go directly to a prompt by number');
  var form=document.createElement('form');
  form.className='mobile-prompt-jump-form';
  form.id='mobilePromptJumpForm';
  form.hidden=true;
  form.setAttribute('aria-label','Go directly to prompt ID');
  var prefix=document.createElement('span');
  prefix.className='mobile-prompt-jump-prefix';
  prefix.textContent='P';
  prefix.setAttribute('aria-hidden','true');
  var input=document.createElement('input');
  input.className='mobile-prompt-jump-input';
  input.id='mobilePromptJumpInput';
  input.type='text';
  input.inputMode='numeric';
  input.pattern='[0-9]*';
  input.enterKeyHint='go';
  input.autocomplete='off';
  input.placeholder='111';
  input.setAttribute('aria-label','Prompt number after P');
  var go=document.createElement('button');
  go.className='mobile-prompt-jump-go';
  go.type='submit';
  go.textContent='Go';
  go.disabled=true;
  go.setAttribute('aria-label','Go to exact prompt ID');
  var status=document.createElement('div');
  status.className='mobile-prompt-jump-status';
  status.id='mobilePromptJumpStatus';
  status.setAttribute('role','status');
  status.setAttribute('aria-live','polite');
  form.appendChild(prefix);form.appendChild(input);form.appendChild(go);form.appendChild(status);
  jump.appendChild(toggle);jump.appendChild(form);shell.appendChild(jump);
  toggle.addEventListener('click',function(e){e.preventDefault();e.stopPropagation();setHotkeyHelpOpen(false,false);setMobilePromptJumpOpen(form.hidden,false)});
  input.addEventListener('input',function(){resolveMobilePromptJump(false)});
  input.addEventListener('keydown',function(e){if(e.key==='Escape'){e.preventDefault();setMobilePromptJumpOpen(false,true)}});
  form.addEventListener('submit',function(e){e.preventDefault();resolveMobilePromptJump(true)});
}

function normalizePromptShortcutId(raw){
  var value=String(raw||'').trim().toUpperCase().replace(/\./g,'');
  return /^P\d+$/.test(value)?value:null
}

function computeSharedPromptShortcutBindings(){
  var bindings={};
  var catalog=typeof PROMPTS!=='undefined'&&Array.isArray(PROMPTS)?PROMPTS:[];
  catalog.forEach(function(item){
    if(!item||item.sharedShortcut!==true)return;
    var promptId=normalizePromptShortcutId(item.id);
    var digits=promptShortcutDigitGesture(promptId);
    if(digits)bindings[digits]=promptId
  });
  return bindings
}

function favoritePromptShortcutBindings(){
  var bindings={};
  var catalog=typeof PROMPTS!=='undefined'&&Array.isArray(PROMPTS)?PROMPTS:[];
  catalog.forEach(function(item){
    if(!item)return;
    var promptId=normalizePromptShortcutId(item.id);
    var digits=promptShortcutDigitGesture(promptId);
    if(digits&&isFavoritePrompt(promptId))bindings[digits]=promptId
  });
  return bindings
}

function promptShortcutDigitGesture(promptId){
  var value=String(promptId||'');
  if(!/^P\d+$/i.test(value))return '';
  return value.slice(1)
}

function catalogPromptShortcutBindings(){
  var bindings={};
  var catalog=typeof PROMPTS!=='undefined'&&Array.isArray(PROMPTS)?PROMPTS:[];
  catalog.forEach(function(item){
    if(!item)return;
    var promptId=normalizePromptShortcutId(item.id);
    var digits=promptShortcutDigitGesture(promptId);
    if(!digits)return;
    bindings[digits]=promptId;
    bindings['p'+digits]=promptId
  });
  return bindings
}

function effectivePromptShortcutBindings(){
  return catalogPromptShortcutBindings()
}

function favoritePromptShortcutIds(){
  var bindings=favoritePromptShortcutBindings();
  return Object.keys(bindings).sort(function(a,b){return Number(a)-Number(b)}).map(function(gesture){return bindings[gesture]})
}

function sharedPromptShortcutIds(){
  return Object.keys(sharedPromptShortcutBindings).sort(function(a,b){return Number(a)-Number(b)}).map(function(gesture){return sharedPromptShortcutBindings[gesture]})
}

function renderPromptShortcutBindings(){
  var host=document.getElementById('promptShortcutBindings');
  if(!host)return;
  host.innerHTML='';
  var intro=document.createElement('span');
  intro.className='hotkey-shortcut-empty';
  intro.textContent='Every prompt has a natural numeric shortcut. Example: type 126 to copy + snap to P126.';
  host.appendChild(intro);
  var favoriteIds=favoritePromptShortcutIds();
  var sharedIds=sharedPromptShortcutIds().filter(function(promptId){return favoriteIds.indexOf(promptId)<0});
  sharedIds.forEach(function(promptId){
    var row=document.createElement('div');row.className='hotkey-shortcut-row';
    var key=document.createElement('kbd');key.textContent=promptId.slice(1);
    var label=document.createElement('span');label.textContent='Copy + snap to '+promptId;
    var shared=document.createElement('span');shared.className='hotkey-shortcut-shared';shared.textContent='Recommended';
    row.appendChild(key);row.appendChild(label);row.appendChild(shared);host.appendChild(row)
  });
  favoriteIds.forEach(function(promptId){
    var row=document.createElement('div');row.className='hotkey-shortcut-row';
    var key=document.createElement('kbd');key.textContent=promptId.slice(1);
    var label=document.createElement('span');label.textContent='Copy + snap to '+promptId;
    var favorite=document.createElement('span');favorite.className='hotkey-shortcut-shared';favorite.textContent='Favorite';
    var remove=document.createElement('button');remove.type='button';remove.className='hotkey-shortcut-remove';remove.setAttribute('aria-label','Remove '+promptId+' from Favorites');remove.textContent='Unfavorite';
    remove.addEventListener('click',function(){toggleFavoritePromptAndRefreshShortcut(promptId)});
    row.appendChild(key);row.appendChild(label);row.appendChild(favorite);row.appendChild(remove);host.appendChild(row)
  })
}

function resetPromptShortcutBuffer(){
  promptShortcutBuffer='';
  if(promptShortcutBufferTimer){clearTimeout(promptShortcutBufferTimer);promptShortcutBufferTimer=null}
}

function schedulePromptShortcutBufferReset(){
  if(promptShortcutBufferTimer)clearTimeout(promptShortcutBufferTimer);
  promptShortcutBufferTimer=setTimeout(function(){
    var exact=effectivePromptShortcutBindings()[promptShortcutBuffer];
    resetPromptShortcutBuffer();
    if(exact)activatePromptShortcutTarget(exact)
  },PROMPT_KIT_SHORTCUT_SEQUENCE_TIMEOUT_MS)
}

function promptShortcutHasLongerPrefix(candidate,gestures){
  return gestures.some(function(gesture){return gesture!==candidate&&gesture.indexOf(candidate)===0})
}

function centerRenderedPromptCard(promptId,behavior){
  hideCompactFilters();
  var selector='[data-prompt-id="'+String(promptId||'').replace(/"/g,'')+'"]';
  var card=document.querySelector(selector);
  if(!card)return false;
  var scrollBehavior=behavior||hotkeyScrollBehavior();
  try{card.scrollIntoView({behavior:scrollBehavior,block:'center',inline:'nearest'})}catch(e){try{card.scrollIntoView()}catch(ignore){}}
  return true
}

function revealPromptShortcutTarget(promptId,behavior){
  if(window.PromptKitProfiles&&typeof window.PromptKitProfiles.activateSlot==='function'){
    window.PromptKitProfiles.activateSlot('A',true)
  }
  activeCat='all';
  activeSection=null;
  clearTransientPromptFilters();
  document.querySelectorAll('.cat-tab').forEach(function(button){button.classList.toggle('active',button.dataset.cat==='all')});
  document.querySelectorAll('.section-tab').forEach(function(button){button.classList.toggle('active',button.dataset.section==='__all__')});
  renderTypes();
  render();
  return centerRenderedPromptCard(promptId,behavior||hotkeyScrollBehavior())
}

function activatePromptShortcutTarget(promptId){
  var prompt=PROMPTS.find(function(item){return item.id===promptId});
  if(!prompt)return false;
  if(!revealPromptShortcutTarget(promptId,'instant')){showToast(promptId+' could not be revealed');return false}
  copyPrompt(promptId);
  return true
}

function handleConfiguredPromptShortcutKey(e,key){
  var bindings=effectivePromptShortcutBindings();
  var gestures=Object.keys(bindings);
  if(!gestures.length){resetPromptShortcutBuffer();return false}
  if(key==='.'&&promptShortcutBuffer){e.preventDefault();e.stopImmediatePropagation();schedulePromptShortcutBufferReset();return true}
  var pendingExact=bindings[promptShortcutBuffer]||null;
  if(!/^[a-z0-9]$/.test(key)){
    resetPromptShortcutBuffer();
    if(pendingExact)activatePromptShortcutTarget(pendingExact);
    return false
  }
  function acceptCandidate(candidate){
    var exact=bindings[candidate];
    var prefix=gestures.some(function(gesture){return gesture.indexOf(candidate)===0});
    if(exact&&!promptShortcutHasLongerPrefix(candidate,gestures)){e.preventDefault();e.stopImmediatePropagation();resetPromptShortcutBuffer();activatePromptShortcutTarget(exact);return true}
    if(prefix){e.preventDefault();e.stopImmediatePropagation();promptShortcutBuffer=candidate;schedulePromptShortcutBufferReset();return true}
    return false
  }
  var candidate=promptShortcutBuffer+key;
  if(acceptCandidate(candidate))return true;
  resetPromptShortcutBuffer();
  if(pendingExact){activatePromptShortcutTarget(pendingExact);return false}
  return acceptCandidate(key)
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
    style.textContent='.hotkey-help{position:fixed;right:80px;bottom:16px;z-index:45;font-family:inherit}.hotkey-help-toggle{display:inline-flex;align-items:center;gap:7px;min-height:40px;padding:8px 11px;border:1px solid rgba(56,189,248,.62);border-radius:999px;background:linear-gradient(135deg,rgba(14,116,144,.92),rgba(15,23,42,.96));color:var(--text-primary);font-size:11px;font-weight:800;letter-spacing:.03em;cursor:pointer;box-shadow:0 0 0 1px rgba(56,189,248,.14),0 0 18px rgba(56,189,248,.32),0 8px 24px rgba(0,0,0,.28);animation:hotkey-help-glow 2.8s ease-in-out infinite}.hotkey-help-toggle:hover,.hotkey-help-toggle:focus-visible{outline:none;border-color:var(--accent);box-shadow:0 0 0 3px var(--accent-glow),0 0 26px rgba(56,189,248,.46)}.hotkey-help-icon{font-size:15px;line-height:1}.mobile-quick-label{display:none}.mobile-quick-controls{display:none;gap:10px;padding:2px 0 12px;margin-bottom:10px;border-bottom:1px solid var(--border)}.mobile-quick-grid{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:8px}.mobile-quick-action{min-height:44px;padding:9px 10px;border:1px solid var(--border);border-radius:8px;background:var(--bg-surface);color:var(--text-primary);font:inherit;font-size:11px;font-weight:750;text-align:left;cursor:pointer;touch-action:manipulation}.mobile-quick-action:hover,.mobile-quick-action:focus-visible{outline:none;border-color:var(--accent);box-shadow:0 0 0 2px var(--accent-glow)}.mobile-quick-heading{color:var(--text-primary);font-size:12px}.hotkey-help-panel{position:absolute;right:0;bottom:calc(100% + 10px);width:min(292px,calc(100vw - 24px));max-height:min(520px,70vh);overflow:auto;padding:12px;border:1px solid rgba(56,189,248,.42);border-radius:12px;background:rgba(15,23,42,.98);box-shadow:0 0 0 1px rgba(56,189,248,.12),0 0 28px rgba(56,189,248,.22),0 18px 48px rgba(0,0,0,.46);backdrop-filter:blur(12px)}.hotkey-help-panel[hidden]{display:none}.hotkey-help-head{display:flex;align-items:center;justify-content:space-between;gap:10px;margin-bottom:8px;color:var(--text-primary);font-size:12px}.hotkey-help-close{display:inline-flex;align-items:center;justify-content:center;width:30px;height:30px;border:1px solid var(--border);border-radius:7px;background:var(--bg-surface);color:var(--text-secondary);cursor:pointer}.hotkey-help-close:hover,.hotkey-help-close:focus-visible{outline:none;border-color:var(--accent);color:var(--text-primary);box-shadow:0 0 0 2px var(--accent-glow)}.hotkey-help-list{display:grid;grid-template-columns:auto 1fr;gap:6px 10px;align-items:center}.hotkey-help-list kbd{min-width:28px;padding:3px 6px;border:1px solid var(--border);border-bottom-color:rgba(148,163,184,.65);border-radius:6px;background:var(--bg-surface);color:var(--accent);font:700 10px/1.3 ui-monospace,SFMono-Regular,Consolas,monospace;text-align:center}.hotkey-help-list span{color:var(--text-secondary);font-size:11px;line-height:1.35}@keyframes hotkey-help-glow{0%,100%{box-shadow:0 0 0 1px rgba(56,189,248,.12),0 0 14px rgba(56,189,248,.24),0 8px 24px rgba(0,0,0,.28)}50%{box-shadow:0 0 0 1px rgba(56,189,248,.24),0 0 24px rgba(56,189,248,.46),0 8px 28px rgba(0,0,0,.34)}}@media(max-width:760px){.ref-toggle{display:none!important}.hotkey-help{right:16px;bottom:16px}.hotkey-help-toggle{min-height:48px;padding:10px 14px;touch-action:none}.hotkey-desktop-label{display:none}.mobile-quick-label{display:inline}.hotkey-help-panel{position:fixed;right:12px;bottom:76px;width:calc(100vw - 24px);max-height:72vh}.mobile-quick-controls{display:grid}.mobile-quick-gesture-guide{display:block}}@media(prefers-reduced-motion:reduce){.hotkey-help-toggle{animation:none}}';
    document.head.appendChild(style)
  }
  var shell=document.createElement('div');
  shell.className='hotkey-help';
  shell.id='hotkeyHelp';
  installMobilePromptJump(shell);

  var toggle=document.createElement('button');
  toggle.className='hotkey-help-toggle';
  toggle.id='hotkeyHelpToggle';
  toggle.type='button';
  toggle.setAttribute('aria-expanded','false');
  toggle.setAttribute('aria-controls','hotkeyHelpPanel');
  toggle.setAttribute('aria-label','Open Hotkeys on desktop. On touch, open More controls. Use Go to P# for the fastest known prompt ID path.');
  toggle.setAttribute('aria-keyshortcuts','`');
  toggle.innerHTML='<span class="hotkey-help-icon" aria-hidden="true">◎</span><span class="hotkey-desktop-label">Hotkeys</span><span class="mobile-quick-label">More</span>';
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
  title.innerHTML='<span class="hotkey-panel-title">Hotkeys</span><span class="mobile-quick-panel-title">More controls</span>';
  var close=document.createElement('button');
  close.className='hotkey-help-close';
  close.type='button';
  close.setAttribute('aria-label','Close keyboard shortcut help');
  close.textContent='×';
  head.appendChild(title);
  head.appendChild(close);
panel.appendChild(head);

  var mobileQuick=document.createElement('section');
  mobileQuick.className='mobile-quick-controls';
  mobileQuick.id='mobileQuickControls';
  mobileQuick.setAttribute('aria-label','Mobile quick controls');
  var quickHeading=document.createElement('strong');
  quickHeading.className='mobile-quick-heading';
  quickHeading.textContent='More controls';
  mobileQuick.appendChild(quickHeading);
  var quickGrid=document.createElement('div');
  quickGrid.className='mobile-quick-grid';
  [
    ['find','✦ Find Prompt'],
    ['profile-prev','← Previous profile'],
    ['profile-next','Next profile →'],
    ['search','⌕ Search'],
    ['favorites','★ Favorites'],
    ['filters','▤ Filters'],
    ['reference','☰ Reference'],
    ['top','↑ Top'],
    ['bottom','↓ Bottom']
  ].forEach(function(item){
    var button=document.createElement('button');
    button.type='button';
    button.className='mobile-quick-action';
    button.setAttribute('data-mobile-quick-action',item[0]);
    button.textContent=item[1];
    button.addEventListener('click',function(){performMobileQuickAction(item[0],toggle)});
    quickGrid.appendChild(button)
  });
  mobileQuick.appendChild(quickGrid);
  panel.appendChild(mobileQuick);

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
  configTitle.textContent='Prompt shortcuts';
  var configHint=document.createElement('span');
  configHint.className='hotkey-shortcut-hint';
  configHint.textContent='Type the digits after P anywhere outside editable fields. Example: 126 copies P126 and snaps its card to center. p126 remains accepted for compatibility. Favorites need no shortcut setup.';
  var bindings=document.createElement('div');
  bindings.id='promptShortcutBindings';
  bindings.className='hotkey-shortcut-bindings';
  config.appendChild(configTitle);config.appendChild(configHint);config.appendChild(bindings);
  panel.appendChild(config);
  shell.appendChild(panel);
  document.body.appendChild(shell);

  toggle.addEventListener('click',function(e){e.preventDefault();e.stopPropagation();setMobilePromptJumpOpen(false,false);setHotkeyHelpOpen(panel.hidden)});
  close.addEventListener('click',function(){setHotkeyHelpOpen(false,true)});
  document.addEventListener('click',function(e){if(!panel.hidden&&!shell.contains(e.target))setHotkeyHelpOpen(false,false)});
  if(!document.getElementById('prompt-kit-hotkey-config-styles')){
    var configStyle=document.createElement('style');configStyle.id='prompt-kit-hotkey-config-styles';
    configStyle.textContent='.hotkey-shortcut-config{margin-top:12px;padding-top:10px;border-top:1px solid var(--border);display:grid;gap:7px}.hotkey-shortcut-hint,.hotkey-shortcut-empty{color:var(--text-muted);font-size:10px;line-height:1.4}.hotkey-shortcut-controls{display:grid;grid-template-columns:minmax(0,1fr) auto;gap:6px}.hotkey-shortcut-controls input,.hotkey-shortcut-controls button,.hotkey-shortcut-remove{min-height:32px;border:1px solid var(--border);border-radius:6px;background:var(--bg-surface);color:var(--text-primary);font:inherit}.hotkey-shortcut-controls input{padding:5px 7px}.hotkey-shortcut-controls button,.hotkey-shortcut-remove{padding:5px 8px;cursor:pointer}.hotkey-shortcut-bindings{display:grid;gap:5px}.hotkey-shortcut-row{display:grid;grid-template-columns:auto minmax(0,1fr) auto;align-items:center;gap:7px;color:var(--text-secondary);font-size:10px}.hotkey-shortcut-row kbd{padding:3px 6px;border:1px solid var(--border);border-radius:6px;color:var(--accent);font:700 10px/1.3 ui-monospace,SFMono-Regular,Consolas,monospace}.hotkey-shortcut-remove{min-height:28px;font-size:9px}.hotkey-shortcut-shared{display:inline-flex;align-items:center;min-height:28px;padding:0 8px;border:1px solid var(--border);border-radius:6px;color:var(--text-muted);font-size:9px}';
    document.head.appendChild(configStyle)
  }
  renderPromptShortcutBindings()
}


function exitFocusedSearch(search){
  if(!search)return false;
  var changed=search.value!=='';
  search.value='';
  var clear=document.getElementById('searchClear');
  if(clear)clear.style.display='none';
  if(changed)render();
  try{search.blur()}catch(e){}
  return true
}

function installCompactBrowsingHotkeys(){
  document.addEventListener('keydown',function(e){
    var key=String(e.key||'').toLowerCase();
    var target=e.target;
    var editable=!!(target&&(target.tagName==='INPUT'||target.tagName==='TEXTAREA'||target.tagName==='SELECT'||target.isContentEditable));
    if(e.defaultPrevented||e.altKey||e.metaKey||e.ctrlKey)return;
    var escapeHelpPanel=document.getElementById('hotkeyHelpPanel');
    if(key==='escape'&&escapeHelpPanel&&!escapeHelpPanel.hidden){
      e.preventDefault();e.stopImmediatePropagation();resetPromptShortcutBuffer();setHotkeyHelpOpen(false,true);return
    }
    var search=document.getElementById('search');
    if(key==='escape'&&search&&target===search){
      e.preventDefault();e.stopImmediatePropagation();resetPromptShortcutBuffer();exitFocusedSearch(search);return
    }
    if(editable)return;
    if(key==='`'){
      e.preventDefault();e.stopImmediatePropagation();
      var helpPanel=document.getElementById('hotkeyHelpPanel');
      setHotkeyHelpOpen(helpPanel?helpPanel.hidden:true,false);
      resetPromptShortcutBuffer();
      return
    }
    if(key==='escape')resetPromptShortcutBuffer();
    if(promptShortcutBuffer&&handleConfiguredPromptShortcutKey(e,key))return;
    if(/^[a-e]$/.test(key)&&window.PromptKitProfiles&&typeof window.PromptKitProfiles.activateSlot==='function'){
      e.preventDefault();e.stopImmediatePropagation();resetPromptShortcutBuffer();window.PromptKitProfiles.activateSlot(key.toUpperCase());return
    }
    if(key==='f'){e.preventDefault();e.stopImmediatePropagation();toggleCompactFilters();return}
    if(key==='['){e.preventDefault();e.stopImmediatePropagation();hideCompactFilters();return}
    if(key===']'){e.preventDefault();e.stopImmediatePropagation();showCompactFilters();return}
    if(key==='home'){e.preventDefault();e.stopImmediatePropagation();scrollPromptKitTo('top');return}
    if(key==='end'){e.preventDefault();e.stopImmediatePropagation();scrollPromptKitTo('bottom');return}
    handleConfiguredPromptShortcutKey(e,key)
  },true)
}

function ensurePromptDetailFavoriteStyles(){
  if(document.getElementById('prompt-detail-favorite-styles'))return;
  var style=document.createElement('style');
  style.id='prompt-detail-favorite-styles';
  style.textContent='.prompt-detail-favorite-btn{position:absolute;top:12px;right:50px;z-index:3;display:inline-flex;align-items:center;justify-content:center;gap:6px;min-height:34px;padding:6px 10px;border:1px solid rgba(245,158,11,.55);border-radius:999px;background:rgba(15,23,42,.94);color:#fbbf24;font:800 11px/1 inherit;cursor:pointer}.prompt-detail-favorite-btn:hover,.prompt-detail-favorite-btn:focus-visible{outline:none;border-color:#f59e0b;box-shadow:0 0 0 2px rgba(245,158,11,.18)}.prompt-detail-favorite-btn.active{background:rgba(245,158,11,.16);border-color:#f59e0b}@media(max-width:760px){.prompt-detail-favorite-btn{position:sticky;top:0;right:auto;float:right;margin:-4px 34px 8px 8px;min-height:44px;padding:8px 12px}}';
  document.head.appendChild(style)
}

function refreshPromptDetailFavoriteButton(button,promptId){
  if(!button)return;
  var active=isFavoritePrompt(promptId);
  button.classList.toggle('active',active);
  button.setAttribute('aria-pressed',active?'true':'false');
  button.setAttribute('aria-label',(active?'Remove ':'Add ')+promptId+(active?' from Favorites':' to Favorites'));
  button.textContent=(active?'★ ':'☆ ')+(active?'Favorited':'Favorite')
}

function toggleFavoritePromptAndRefreshShortcut(rawPromptId){
  var promptId=normalizePromptShortcutId(rawPromptId);
  if(!promptId)return false;
  var wasFavorite=isFavoritePrompt(promptId);
  toggleFavoritePrompt(promptId);
  var isFavorite=isFavoritePrompt(promptId);
  renderPromptShortcutBindings();
  var detailButton=document.querySelector('.prompt-detail-favorite-btn[data-favorite-prompt-id="'+promptId+'"]');
  refreshPromptDetailFavoriteButton(detailButton,promptId);
  if(isFavorite&&!wasFavorite)showToast('★ '+promptId+' saved · type '+promptId.slice(1)+' anytime','success');
  else if(!isFavorite&&wasFavorite)showToast('Removed '+promptId+' from Favorites · shortcut '+promptId.slice(1)+' still available');
  return isFavorite
}

function decoratePromptDetailFavorite(promptId){
  var normalized=normalizePromptShortcutId(promptId);
  var detail=document.getElementById('promptDetail');
  if(!normalized||!detail)return false;
  var existing=detail.querySelector('.prompt-detail-favorite-btn');
  if(existing&&existing.parentNode)existing.parentNode.removeChild(existing);
  var button=document.createElement('button');
  button.type='button';
  button.className='prompt-detail-favorite-btn';
  button.setAttribute('data-favorite-prompt-id',normalized);
  refreshPromptDetailFavoriteButton(button,normalized);
  button.addEventListener('click',function(e){e.preventDefault();e.stopPropagation();toggleFavoritePromptAndRefreshShortcut(normalized)});
  var close=detail.querySelector('.prompt-detail-close');
  if(close&&close.parentNode===detail)detail.insertBefore(button,close.nextSibling);else detail.insertBefore(button,detail.firstChild);
  return true
}

var baseShowPromptDetailWithFavorite=window.showPromptDetail;
if(typeof baseShowPromptDetailWithFavorite==='function'){
  window.showPromptDetail=function(id,origin){
    centerRenderedPromptCard(id,'instant');
    baseShowPromptDetailWithFavorite(id,origin);
    decoratePromptDetailFavorite(id)
  }
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
  favBtn.onclick=function(e){cancelPromptCardCopy(card);e.preventDefault();e.stopPropagation();toggleFavoritePromptAndRefreshShortcut(p.id)};
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
ensureFavoritesGroupJumpStyles();
ensureFavoritesJourneyStyles();
ensurePromptDetailFavoriteStyles();
ensureCompactBrowsingControls();
ensureHotkeyHelp();
installCompactBrowsingViewSwitches();
installCompactBrowsingHotkeys();
installFavoritesGroupJumpNavigation();
render();
})();
