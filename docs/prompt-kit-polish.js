(function(){
'use strict';
var copyToastTimer=null;
var PROMPT_KIT_SHORTCUT_STORAGE_KEY='promptKit.promptShortcuts.v1';
var PROMPT_KIT_SHORTCUT_SCHEMA='prompt-kit-shortcuts/v1';
var PROMPT_KIT_SHORTCUT_SEQUENCE_TIMEOUT_MS=1200;
var promptShortcutBindings=loadPromptShortcutBindings();
var sharedPromptShortcutBindings=computeSharedPromptShortcutBindings();
var promptShortcutBuffer='';
var promptShortcutBufferTimer=null;

function ensurePromptKitPolishStyles(){
  if(document.getElementById('prompt-kit-polish-styles'))return;
  var style=document.createElement('style');
  style.id='prompt-kit-polish-styles';
  style.textContent='.prompt-card .prompt-header{padding-right:176px;min-height:34px}.prompt-card-actions{position:absolute;top:12px;right:12px;display:flex;align-items:center;justify-content:flex-end;gap:6px;z-index:3;max-width:168px}.prompt-card-actions .prompt-favorite-btn,.prompt-card-actions .prompt-open-btn,.prompt-card-actions .prompt-copy-btn{position:static!important;top:auto!important;right:auto!important;margin:0!important;opacity:1!important;display:inline-flex;align-items:center;justify-content:center;min-height:30px;box-sizing:border-box}.prompt-card-actions .prompt-favorite-btn{width:30px;min-width:30px}.prompt-card-actions .prompt-open-btn,.prompt-card-actions .prompt-copy-btn{padding:4px 8px;white-space:nowrap}.prompt-card.copy-confirmed{animation:prompt-copy-confirm 800ms ease-out}.prompt-card.copy-confirmed .glow-bar{background:var(--success)!important;box-shadow:0 0 12px rgba(34,197,94,.9),0 0 28px rgba(34,197,94,.45)!important}.toast.success{border-color:var(--success);background:linear-gradient(135deg,rgba(20,83,45,.96),rgba(17,24,39,.98));color:#dcfce7;box-shadow:0 0 0 1px rgba(34,197,94,.2),0 0 24px rgba(34,197,94,.42),0 10px 34px rgba(0,0,0,.42)}.toast.success.show{animation:prompt-toast-success 1.7s ease both}.header-top{display:grid;grid-template-columns:minmax(0,1fr) auto minmax(280px,400px);align-items:center;gap:12px 16px}.header-top>.logo{grid-column:1;min-width:0}.filter-panel-toggle{grid-column:2;display:inline-flex;align-items:center;justify-content:center;justify-self:end;min-height:34px;padding:6px 10px;border:1px solid var(--border);border-radius:7px;background:var(--bg-surface);color:var(--text-secondary);font-size:11px;font-weight:600;cursor:pointer;white-space:nowrap;transition:all .2s}.header-top>.search-container{grid-column:3;min-width:0;width:100%;max-width:none}.header-top>.header-controls{grid-column:1/-1;min-width:0;width:100%;justify-self:stretch;justify-content:flex-end;flex-wrap:wrap}.filter-panel-toggle:hover,.filter-panel-toggle:focus-visible{outline:none;border-color:var(--accent);color:var(--text-primary);box-shadow:0 0 0 2px var(--accent-glow)}.header.filters-collapsed{padding-bottom:8px}.header.filters-collapsed .search-container,.header.filters-collapsed .header-controls,.header.filters-collapsed .sections-nav,.header.filters-collapsed .type-nav{display:none!important}.header.filters-collapsed .header-top{padding-bottom:0}.header.filters-collapsed .filter-panel-toggle{justify-self:end;margin-left:0}.mobile-favorites-quick{display:none;align-items:center;justify-content:center;min-height:44px;padding:8px 12px;border:1px solid rgba(245,158,11,.45);border-radius:8px;background:rgba(245,158,11,.08);color:#fbbf24;font-size:12px;font-weight:800;letter-spacing:.02em;cursor:pointer;touch-action:manipulation}.mobile-favorites-quick:hover,.mobile-favorites-quick:focus-visible{outline:none;border-color:#f59e0b;box-shadow:0 0 0 2px rgba(245,158,11,.18)}@keyframes prompt-copy-confirm{0%{border-color:var(--success);box-shadow:0 0 0 1px rgba(34,197,94,.7),0 0 30px rgba(34,197,94,.42);transform:translateY(-1px) scale(1.006)}45%{border-color:rgba(34,197,94,.78);box-shadow:0 0 22px rgba(34,197,94,.3)}100%{border-color:var(--border);box-shadow:none;transform:none}}@keyframes prompt-toast-success{0%{opacity:0;transform:translate(-50%,12px) scale(.96)}12%{opacity:1;transform:translate(-50%,0) scale(1.03)}24%,82%{opacity:1;transform:translate(-50%,0) scale(1)}100%{opacity:0;transform:translate(-50%,-4px) scale(.99)}}@media(max-width:980px){.header-top{grid-template-columns:minmax(0,1fr) auto}.header-top>.logo{grid-column:1}.filter-panel-toggle{grid-column:2}.header-top>.search-container{grid-column:1/-1;max-width:none}.header-top>.header-controls{grid-column:1/-1}}@media(max-width:760px){.prompt-card .prompt-header{padding-right:0;min-height:0}.prompt-card-actions{position:static;max-width:none;width:100%;display:grid;grid-template-columns:44px minmax(72px,1fr) minmax(72px,1fr);gap:8px;margin-top:12px}.prompt-card-actions .prompt-favorite-btn,.prompt-card-actions .prompt-open-btn,.prompt-card-actions .prompt-copy-btn{width:100%;min-height:42px;margin:0!important}.header{padding-left:12px;padding-right:12px}.header-top{grid-template-columns:minmax(0,1fr) auto;gap:8px}.filter-panel-toggle{min-height:40px;justify-self:end}.header-top>.search-container{grid-column:1/-1;width:100%}.header-top>.header-controls{grid-column:1/-1;display:grid;grid-template-columns:minmax(0,1fr);width:100%;justify-items:stretch;gap:8px}.header-top>.header-controls .cat-tabs{max-width:100%;overflow-x:auto;-webkit-overflow-scrolling:touch;scrollbar-width:none}.header-top>.header-controls .cat-tabs::-webkit-scrollbar{display:none}.header-top>.header-controls .cat-tab{min-height:42px}.header-top>.header-controls .add-prompt-btn{justify-content:center;min-height:42px}.header-top>.header-controls .stats{justify-content:center}.header-top>.mobile-favorites-quick{display:inline-flex;width:100%;grid-column:1/-1}.header.filters-collapsed .header-top{grid-template-columns:minmax(0,1fr) auto}}@media(prefers-reduced-motion:reduce){.prompt-card.copy-confirmed,.toast.success.show{animation:none}.toast.success.show{opacity:1}}';
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


var MOBILE_QUICK_GESTURE_THRESHOLD=38;
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
    var ref=document.getElementById('refBtn');
    if(ref){ref.click();return true}
    return false
  }
  if(action==='top'){scrollPromptKitTo('top');return true}
  if(action==='bottom'){scrollPromptKitTo('bottom');return true}
  return false
}

function installMobileQuickHandleGestures(toggle){
  if(!toggle||toggle.__mobileQuickGesturesInstalled)return;
  toggle.__mobileQuickGesturesInstalled=true;
  var start=null;
  toggle.addEventListener('pointerdown',function(e){
    if(!window.matchMedia||!window.matchMedia('(max-width:760px)').matches)return;
    if(e.pointerType&&e.pointerType!=='touch'&&e.pointerType!=='pen')return;
    start={id:e.pointerId,x:e.clientX,y:e.clientY};
    try{toggle.setPointerCapture(e.pointerId)}catch(ignore){}
  });
  toggle.addEventListener('pointercancel',function(){start=null});
  toggle.addEventListener('pointerup',function(e){
    if(!start||start.id!==e.pointerId){start=null;return}
    var dx=e.clientX-start.x,dy=e.clientY-start.y;
    start=null;
    var ax=Math.abs(dx),ay=Math.abs(dy),action=null;
    if(ay>=MOBILE_QUICK_GESTURE_THRESHOLD&&ay>ax*1.2)action=dy<0?'find':'filters';
    else if(ax>=MOBILE_QUICK_GESTURE_THRESHOLD&&ax>ay*1.2)action=dx<0?'profile-prev':'profile-next';
    if(!action)return;
    e.preventDefault();e.stopPropagation();
    toggle.__mobileQuickGestureConsumed=true;
    var status=document.getElementById('mobileQuickGestureStatus');
    if(status)status.textContent=action==='find'?'Find Prompt opened':action==='filters'?'Filters toggled':action==='profile-prev'?'Previous profile selected':'Next profile selected';
    performMobileQuickAction(action,toggle);
    setTimeout(function(){toggle.__mobileQuickGestureConsumed=false},450)
  })
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
    if(promptId)bindings[promptId.toLowerCase()]=promptId
  });
  return bindings
}

function effectivePromptShortcutBindings(){
  var merged={};
  Object.keys(sharedPromptShortcutBindings).forEach(function(gesture){merged[gesture]=sharedPromptShortcutBindings[gesture]});
  Object.keys(promptShortcutBindings).forEach(function(gesture){merged[gesture]=promptShortcutBindings[gesture]});
  return merged
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

function sharedPromptShortcutIds(){
  return Object.keys(sharedPromptShortcutBindings).sort(function(a,b){return Number(a.slice(1))-Number(b.slice(1))}).map(function(gesture){return sharedPromptShortcutBindings[gesture]})
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
  var sharedIds=sharedPromptShortcutIds().filter(function(promptId){return !promptShortcutBindings[promptId.toLowerCase()]});
  var ids=configuredPromptShortcutIds();
  if(!ids.length&&!sharedIds.length){var empty=document.createElement('span');empty.className='hotkey-shortcut-empty';empty.textContent='No favorite prompt shortcuts configured.';host.appendChild(empty);return}
  sharedIds.forEach(function(promptId){
    var row=document.createElement('div');row.className='hotkey-shortcut-row';
    var key=document.createElement('kbd');key.textContent=promptId.toLowerCase();
    var label=document.createElement('span');label.textContent='Copy + reveal '+promptId;
    var shared=document.createElement('span');shared.className='hotkey-shortcut-shared';shared.textContent='Recommended';
    row.appendChild(key);row.appendChild(label);row.appendChild(shared);host.appendChild(row)
  });
  ids.forEach(function(promptId){
    var row=document.createElement('div');row.className='hotkey-shortcut-row';
    var key=document.createElement('kbd');key.textContent=promptId.toLowerCase();
    var label=document.createElement('span');label.textContent='Copy + reveal '+promptId;
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
  promptShortcutBufferTimer=setTimeout(function(){
    var exact=effectivePromptShortcutBindings()[promptShortcutBuffer];
    resetPromptShortcutBuffer();
    if(exact)activatePromptShortcutTarget(exact)
  },PROMPT_KIT_SHORTCUT_SEQUENCE_TIMEOUT_MS)
}

function promptShortcutHasLongerPrefix(candidate,gestures){
  return gestures.some(function(gesture){return gesture!==candidate&&gesture.indexOf(candidate)===0})
}

function revealPromptShortcutTarget(promptId){
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
  var selector='[data-prompt-id="'+String(promptId||'').replace(/"/g,'')+'"]';
  var card=document.querySelector(selector);
  if(!card)return false;
  try{card.scrollIntoView({behavior:hotkeyScrollBehavior(),block:'center',inline:'nearest'})}catch(e){try{card.scrollIntoView()}catch(ignore){}}
  return true
}

function activatePromptShortcutTarget(promptId){
  var prompt=PROMPTS.find(function(item){return item.id===promptId});
  if(!prompt)return false;
  if(!sharedPromptShortcutBindings[String(promptId).toLowerCase()]&&!isFavoritePrompt(promptId)){showToast(promptId+' is no longer a Favorite');return false}
  if(!revealPromptShortcutTarget(promptId)){showToast(promptId+' could not be revealed');return false}
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

function focusFavoritePromptShortcutInput(panel){
  var promptInput=document.getElementById('promptShortcutPromptId');
  if(!panel||!promptInput||!panel.contains(promptInput))return false;
  try{promptInput.focus()}catch(e){return false}
  try{promptInput.scrollIntoView({block:'nearest',inline:'nearest'})}catch(e){try{promptInput.scrollIntoView()}catch(ignore){}}
  return document.activeElement===promptInput
}

function mobileQuickControlsActive(){
  return !!(window.matchMedia&&window.matchMedia('(max-width:760px)').matches)
}

function setHotkeyHelpOpen(open,restoreFocus){
  var panel=document.getElementById('hotkeyHelpPanel');
  var toggle=document.getElementById('hotkeyHelpToggle');
  if(!panel||!toggle)return;
  panel.hidden=!open;
  toggle.setAttribute('aria-expanded',open?'true':'false');
  if(open){
    if(!mobileQuickControlsActive()&&focusFavoritePromptShortcutInput(panel))return;
    var target=mobileQuickControlsActive()?panel.querySelector('[data-mobile-quick-action="find"]'):panel.querySelector('.hotkey-help-close');
    if(target){try{target.focus({preventScroll:true})}catch(e){target.focus()}}
    return;
  }
  if(restoreFocus){try{toggle.focus({preventScroll:true})}catch(e){toggle.focus()}}
}

function ensureHotkeyHelp(){
  if(document.getElementById('hotkeyHelp'))return;
  if(!document.getElementById('prompt-kit-hotkey-help-styles')){
    var style=document.createElement('style');
    style.id='prompt-kit-hotkey-help-styles';
    style.textContent='.hotkey-help{position:fixed;right:80px;bottom:16px;z-index:45;font-family:inherit}.hotkey-help-toggle{display:inline-flex;align-items:center;gap:7px;min-height:40px;padding:8px 11px;border:1px solid rgba(56,189,248,.62);border-radius:999px;background:linear-gradient(135deg,rgba(14,116,144,.92),rgba(15,23,42,.96));color:var(--text-primary);font-size:11px;font-weight:800;letter-spacing:.03em;cursor:pointer;box-shadow:0 0 0 1px rgba(56,189,248,.14),0 0 18px rgba(56,189,248,.32),0 8px 24px rgba(0,0,0,.28);animation:hotkey-help-glow 2.8s ease-in-out infinite}.hotkey-help-toggle:hover,.hotkey-help-toggle:focus-visible{outline:none;border-color:var(--accent);box-shadow:0 0 0 3px var(--accent-glow),0 0 26px rgba(56,189,248,.46)}.hotkey-help-icon{font-size:15px;line-height:1}.mobile-quick-label{display:none}.mobile-quick-controls{display:none;gap:10px;padding:2px 0 12px;margin-bottom:10px;border-bottom:1px solid var(--border)}.mobile-quick-gesture-guide{display:none;padding:9px 10px;border:1px solid rgba(56,189,248,.25);border-radius:9px;background:rgba(14,116,144,.08);color:var(--text-secondary);font-size:10px;line-height:1.45;text-align:center}.mobile-quick-grid{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:8px}.mobile-quick-action{min-height:44px;padding:9px 10px;border:1px solid var(--border);border-radius:8px;background:var(--bg-surface);color:var(--text-primary);font:inherit;font-size:11px;font-weight:750;text-align:left;cursor:pointer;touch-action:manipulation}.mobile-quick-action:hover,.mobile-quick-action:focus-visible{outline:none;border-color:var(--accent);box-shadow:0 0 0 2px var(--accent-glow)}.mobile-quick-heading{color:var(--text-primary);font-size:12px}.hotkey-help-panel{position:absolute;right:0;bottom:calc(100% + 10px);width:min(292px,calc(100vw - 24px));max-height:min(520px,70vh);overflow:auto;padding:12px;border:1px solid rgba(56,189,248,.42);border-radius:12px;background:rgba(15,23,42,.98);box-shadow:0 0 0 1px rgba(56,189,248,.12),0 0 28px rgba(56,189,248,.22),0 18px 48px rgba(0,0,0,.46);backdrop-filter:blur(12px)}.hotkey-help-panel[hidden]{display:none}.hotkey-help-head{display:flex;align-items:center;justify-content:space-between;gap:10px;margin-bottom:8px;color:var(--text-primary);font-size:12px}.hotkey-help-close{display:inline-flex;align-items:center;justify-content:center;width:30px;height:30px;border:1px solid var(--border);border-radius:7px;background:var(--bg-surface);color:var(--text-secondary);cursor:pointer}.hotkey-help-close:hover,.hotkey-help-close:focus-visible{outline:none;border-color:var(--accent);color:var(--text-primary);box-shadow:0 0 0 2px var(--accent-glow)}.hotkey-help-list{display:grid;grid-template-columns:auto 1fr;gap:6px 10px;align-items:center}.hotkey-help-list kbd{min-width:28px;padding:3px 6px;border:1px solid var(--border);border-bottom-color:rgba(148,163,184,.65);border-radius:6px;background:var(--bg-surface);color:var(--accent);font:700 10px/1.3 ui-monospace,SFMono-Regular,Consolas,monospace;text-align:center}.hotkey-help-list span{color:var(--text-secondary);font-size:11px;line-height:1.35}@keyframes hotkey-help-glow{0%,100%{box-shadow:0 0 0 1px rgba(56,189,248,.12),0 0 14px rgba(56,189,248,.24),0 8px 24px rgba(0,0,0,.28)}50%{box-shadow:0 0 0 1px rgba(56,189,248,.24),0 0 24px rgba(56,189,248,.46),0 8px 28px rgba(0,0,0,.34)}}@media(max-width:760px){.ref-toggle{display:none!important}.hotkey-help{right:16px;bottom:16px}.hotkey-help-toggle{min-height:48px;padding:10px 14px;touch-action:none}.hotkey-desktop-label{display:none}.mobile-quick-label{display:inline}.hotkey-help-panel{position:fixed;right:12px;bottom:76px;width:calc(100vw - 24px);max-height:72vh}.mobile-quick-controls{display:grid}.mobile-quick-gesture-guide{display:block}}@media(prefers-reduced-motion:reduce){.hotkey-help-toggle{animation:none}}';
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
  toggle.setAttribute('aria-label','Open Hotkeys on desktop or Quick Controls on touch devices');
  toggle.setAttribute('aria-keyshortcuts','`');
  toggle.innerHTML='<span class="hotkey-help-icon" aria-hidden="true">◎</span><span class="hotkey-desktop-label">Hotkeys</span><span class="mobile-quick-label">Quick Controls</span>';
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
  title.textContent='Quick controls & hotkeys';
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
  quickHeading.textContent='Touch shortcuts';
  mobileQuick.appendChild(quickHeading);
  var gestureGuide=document.createElement('div');
  gestureGuide.className='mobile-quick-gesture-guide';
  gestureGuide.textContent='Swipe the Quick Controls handle: ↑ Find · ← previous profile · → next profile · ↓ filters. Tap the handle for these labeled controls.';
  mobileQuick.appendChild(gestureGuide);
  var quickGrid=document.createElement('div');
  quickGrid.className='mobile-quick-grid';
  [
    ['find','✦ Find Prompt'],
    ['search','⌕ Search'],
    ['profile-prev','← Previous profile'],
    ['profile-next','Next profile →'],
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
  var gestureStatus=document.createElement('div');
  gestureStatus.id='mobileQuickGestureStatus';
  gestureStatus.setAttribute('role','status');
  gestureStatus.setAttribute('aria-live','polite');
  gestureStatus.style.position='absolute';
  gestureStatus.style.width='1px';
  gestureStatus.style.height='1px';
  gestureStatus.style.overflow='hidden';
  gestureStatus.style.clip='rect(0 0 0 0)';
  mobileQuick.appendChild(gestureStatus);
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
  configTitle.textContent='Favorite prompt shortcuts';
  var configHint=document.createElement('span');
  configHint.className='hotkey-shortcut-hint';
  configHint.textContent='Favorite a prompt, enter its ID, then type that ID anywhere outside editable fields.';
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

  toggle.addEventListener('click',function(e){if(toggle.__mobileQuickGestureConsumed){e.preventDefault();e.stopImmediatePropagation();return}setHotkeyHelpOpen(panel.hidden)});
  installMobileQuickHandleGestures(toggle);
  close.addEventListener('click',function(){setHotkeyHelpOpen(false,true)});
  saveShortcut.addEventListener('click',function(){if(configurePromptShortcut(promptInput.value))promptInput.value=''});
  promptInput.addEventListener('keydown',function(e){if(e.key==='Enter'){e.preventDefault();if(configurePromptShortcut(promptInput.value))promptInput.value=''}});
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
ensureFavoritesGroupJumpStyles();
ensureFavoritesJourneyStyles();
ensureCompactBrowsingControls();
ensureHotkeyHelp();
installCompactBrowsingViewSwitches();
installCompactBrowsingHotkeys();
installFavoritesGroupJumpNavigation();
render();
})();
