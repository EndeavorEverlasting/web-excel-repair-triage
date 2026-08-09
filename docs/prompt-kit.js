var activeCat='all',activeSection=null,activeType=null,activeColor=null;
var promptDetailOrigin=null;
var collapsedSections={};
var FAVORITES_STORAGE_KEY='promptKit.favoritePromptIds.v1';
var favoritePromptIds=loadFavoritePromptIds();
var PROMPT_NAVIGATION_INTERVAL=5;

function showToast(msg){var t=document.getElementById('toast');t.textContent=msg;t.classList.add('show');setTimeout(function(){t.classList.remove('show')},2000)}
function toggleRef(){var s=document.getElementById('refSidebar'),o=document.getElementById('refOverlay');s.classList.toggle('open');o.classList.toggle('open')}
function closeRef(){var s=document.getElementById('refSidebar'),o=document.getElementById('refOverlay');s.classList.remove('open');o.classList.remove('open')}
function copyToClipboard(text){if(navigator.clipboard&&navigator.clipboard.writeText){navigator.clipboard.writeText(text).then(function(){showToast('Copied to clipboard')})}else{var ta=document.createElement('textarea');ta.value=text;ta.style.position='fixed';ta.style.opacity='0';document.body.appendChild(ta);ta.select();document.execCommand('copy');document.body.removeChild(ta);showToast('Copied to clipboard')}}
function copyPrompt(id){var p=PROMPTS.find(function(x){return x.id===id});if(p&&p.copyContent){copyToClipboard(p.copyContent)}}
function escapePromptHtml(value){return String(value==null?'':value).replace(/[&<>"']/g,function(ch){return{'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot',"'":'&#39;'}[ch]})}
function focusPromptOrigin(){if(promptDetailOrigin&&document.body.contains(promptDetailOrigin)){try{promptDetailOrigin.focus({preventScroll:true})}catch(e){promptDetailOrigin.focus()}}}
function showPromptDetail(id,origin){var p=PROMPTS.find(function(x){return x.id===id});if(!p)return;promptDetailOrigin=origin||null;var hex=COLORS[p.color.toLowerCase()]||'#64748b';var safeId=escapePromptHtml(p.id),safeName=escapePromptHtml(p.name),safeType=escapePromptHtml(p.type),safeColor=escapePromptHtml(p.color),safeCategory=escapePromptHtml(p.category),safeSprintRole=escapePromptHtml(p.sprintRole),safeProofGate=escapePromptHtml(p.proofGate),safeClass=escapePromptHtml(p.class),safeUseWhen=escapePromptHtml(p.useWhen),safeCopyContent=escapePromptHtml(p.copyContent||'');var el=document.getElementById('promptDetail');var html='<button class="prompt-detail-close" onclick="closePromptDetail()" aria-label="Close prompt detail">&times;</button>';html+='<div class="pd-glow" style="background:'+hex+'"></div>';html+='<div class="pd-header"><span class="pd-id">'+safeId+'</span><span class="pd-name">'+safeName+'</span></div>';html+='<div class="pd-type">'+safeType+' · '+safeColor+' · '+safeCategory+'</div>';html+='<div class="pd-badges"><span class="pd-badge">'+safeSprintRole+'</span><span class="pd-badge">'+safeProofGate+'</span><span class="pd-badge">'+safeClass+'</span></div>';html+='<div class="pd-section"><h4>When To Use</h4><pre>'+safeUseWhen+'</pre></div>';if(p.copyContent){html+='<div class="pd-section"><h4>Prompt Content</h4><pre>'+safeCopyContent+'</pre></div>'}html+='<button class="pd-copy" onclick="copyPrompt(\''+safeId+'\');this.classList.add(\'copied\');this.textContent=\'Copied!\';setTimeout(function(){this.classList.remove(\'copied\');this.textContent=\'Copy to Clipboard\'}.bind(this),1500)">Copy to Clipboard</button>';el.innerHTML=html;document.getElementById('promptDetailOverlay').classList.add('open');var closeButton=el.querySelector('.prompt-detail-close');if(closeButton)closeButton.focus()}
function closePromptDetail(restoreFocus){document.getElementById('promptDetailOverlay').classList.remove('open');if(restoreFocus!==false)focusPromptOrigin()}
function cancelPromptCardCopy(card){if(card&&card._copyTimer){clearTimeout(card._copyTimer);card._copyTimer=null}}
function isSectionCollapsed(name){return collapsedSections[name]===true}
function togglePromptSection(name){if(!name)return;if(isSectionCollapsed(name)){delete collapsedSections[name]}else{collapsedSections[name]=true}render()}

function ensurePageNavigation(){
  if(!document.getElementById('page-top')){var top=document.createElement('span');top.id='page-top';top.className='page-anchor';top.setAttribute('aria-hidden','true');document.body.insertBefore(top,document.body.firstChild)}
  if(!document.getElementById('page-bottom')){var bottom=document.createElement('span');bottom.id='page-bottom';bottom.className='page-anchor';bottom.setAttribute('aria-hidden','true');document.body.appendChild(bottom)}
  if(!document.getElementById('page-navigation-styles')){var style=document.createElement('style');style.id='page-navigation-styles';style.textContent='.page-anchor{display:block;position:relative;width:0;height:0;overflow:hidden}.section-divider .page-jump,.distributed-page-navigation .page-jump{display:inline-flex;align-items:center;justify-content:center;min-width:62px;padding:4px 8px;border:1px solid var(--border);border-radius:6px;background:var(--bg-surface);color:var(--text-muted);font-size:10px;font-weight:700;letter-spacing:.04em;text-decoration:none;text-transform:uppercase;transition:all .2s}.section-divider .page-jump:hover,.section-divider .page-jump:focus,.distributed-page-navigation .page-jump:hover,.distributed-page-navigation .page-jump:focus{border-color:var(--accent);color:var(--accent);outline:none;box-shadow:0 0 0 2px var(--accent-glow)}.distributed-page-navigation{grid-column:1/-1;display:flex;align-items:center;justify-content:space-between;gap:10px;padding:8px 0 12px}.distributed-page-navigation .page-jump{min-height:40px;padding:6px 12px;touch-action:manipulation}.distributed-page-navigation-count{color:var(--text-muted);font-size:9px;letter-spacing:.04em;text-transform:uppercase;text-align:center}.section-divider .section-toggle{appearance:none;border:1px solid transparent;border-radius:7px;background:transparent;cursor:pointer;padding:5px 8px;font:inherit;text-transform:inherit;letter-spacing:inherit;transition:background .2s,border-color .2s}.section-divider .section-toggle:hover{background:var(--bg-surface);border-color:var(--border)}.section-divider .section-toggle:focus-visible{outline:none;border-color:var(--accent);box-shadow:0 0 0 2px var(--accent-glow)}.section-divider .section-chevron{display:inline-flex;width:14px;justify-content:center;color:var(--text-muted);font-size:12px;transition:transform .2s}.section-divider .section-toggle[aria-expanded="true"] .section-chevron{transform:rotate(90deg)}.section-divider.section-collapsed{padding-bottom:14px}.section-divider.section-collapsed .sd-line{opacity:.55}';document.head.appendChild(style)}
}

function ensureMobileSupport(){
  if(!document.getElementById('prompt-kit-mobile-styles')){
    var style=document.createElement('style');
    style.id='prompt-kit-mobile-styles';
    style.textContent='.logo[role="button"]{border-radius:8px;cursor:pointer;touch-action:manipulation;outline:none}.logo[role="button"]:focus-visible{box-shadow:0 0 0 3px var(--accent-glow)}.prompt-open-btn{position:absolute;top:12px;right:58px;background:var(--bg-surface);border:1px solid var(--border);border-radius:var(--radius);padding:4px 8px;font-size:10px;color:var(--text-muted);cursor:pointer;transition:all .2s;opacity:0}.prompt-card:hover .prompt-open-btn,.prompt-card:focus-within .prompt-open-btn,.prompt-card:focus-within .prompt-copy-btn{opacity:1}.prompt-open-btn:hover,.prompt-open-btn:focus{border-color:var(--accent);color:var(--accent);outline:none}@media (hover:none), (pointer:coarse){.prompt-open-btn,.prompt-copy-btn{opacity:1;min-width:64px;min-height:40px;padding:8px 12px;touch-action:manipulation}.section-divider .section-toggle{min-height:40px;touch-action:manipulation}.distributed-page-navigation .page-jump{min-height:40px;touch-action:manipulation}}@media(max-width:760px){body{overflow-x:hidden}.header{position:static;padding:10px 12px 0}.header-top{display:grid;grid-template-columns:minmax(0,1fr) auto;gap:8px;padding-bottom:8px}.logo{grid-column:1/2;min-width:0;padding:4px}.logo-icon{width:36px;height:36px;flex:0 0 auto}.logo h1{font-size:15px;line-height:1.2}.search-container{grid-column:1/-1;max-width:none;width:100%}.search-container input{min-height:44px;font-size:16px}.search-kbd{display:none}.header-controls{grid-column:1/-1;display:grid;grid-template-columns:minmax(0,1fr) auto;gap:8px;width:100%}.cat-tabs{grid-column:1/-1;display:flex;overflow-x:auto;-webkit-overflow-scrolling:touch;scrollbar-width:none}.cat-tabs::-webkit-scrollbar,.type-nav::-webkit-scrollbar{display:none}.cat-tab{min-height:40px;padding:8px 12px;flex:0 0 auto}.add-prompt-btn{min-height:40px;justify-self:start}.stats{justify-self:end}.sections-nav{padding:0 4px}.section-tab{min-height:44px;padding:10px 12px}.type-nav{padding:8px 0 10px;display:flex;flex-wrap:nowrap;overflow-x:auto;-webkit-overflow-scrolling:touch;scrollbar-width:none}.type-chip{min-height:36px;display:inline-flex;align-items:center;flex:0 0 auto;padding:6px 10px}.grid{grid-template-columns:minmax(0,1fr);gap:10px;margin:12px auto;padding:0 12px}.prompt-card{padding:14px;touch-action:manipulation}.prompt-card:hover{transform:none}.prompt-open-btn,.prompt-copy-btn{position:static;display:inline-flex;align-items:center;justify-content:center;margin:12px 8px 0 0;opacity:1}.prompt-header{padding-right:0}.section-divider{padding:16px 0 6px;gap:6px;justify-content:space-between}.section-divider .sd-line{display:none}.section-divider>button:nth-of-type(1){white-space:normal;text-align:center;justify-content:center;line-height:1.3;font-size:11px;flex:1}.section-divider .page-jump{min-width:58px;min-height:40px;padding:6px}.distributed-page-navigation{padding:6px 0 10px}.distributed-page-navigation .page-jump{min-width:72px;min-height:44px;padding:8px 12px}.distributed-page-navigation-count{font-size:8px}.prompt-detail-overlay{padding:0;align-items:stretch}.prompt-detail{max-width:none;width:100%;height:100dvh;max-height:100dvh;border-radius:0;padding:18px 14px 32px}.prompt-detail-close{position:sticky;top:0;margin-left:auto;background:var(--bg-secondary);z-index:2}.prompt-detail .pd-header{align-items:flex-start;flex-wrap:wrap;padding-right:0}.prompt-detail .pd-name{font-size:16px}.prompt-detail .pd-copy{width:100%;min-height:48px;justify-content:center}.ref-sidebar{width:100vw;max-width:100vw;right:-100vw;padding:18px 14px}.doctrine-view{padding:12px}.ref-toggle{right:16px;bottom:16px;width:52px;height:52px}.version-badge{left:12px;bottom:12px}}';
    document.head.appendChild(style)
  }
  var logo=document.querySelector('.logo');
  if(logo){logo.id='homeReset';logo.tabIndex=0;logo.setAttribute('role','button');logo.setAttribute('aria-label','Reset Prompt Kit to the original unfiltered view');logo.setAttribute('title','Reset filters and return to all prompts')}
}

function ensureDiscoverySupport(){
  if(document.getElementById('prompt-kit-discovery-styles'))return;
  var style=document.createElement('style');
  style.id='prompt-kit-discovery-styles';
  style.textContent='.section-divider .section-toggle{color:var(--text-primary)}.section-divider .section-toggle .sd-count{color:var(--text-secondary)}.section-divider[data-category="Favorites"] .section-toggle{color:#fef3c7}.prompt-favorite-btn{display:inline-flex;align-items:center;justify-content:center;flex:0 0 auto;width:30px;height:30px;margin-left:8px;border:1px solid var(--border);border-radius:7px;background:var(--bg-surface);color:var(--text-muted);font-size:17px;line-height:1;cursor:pointer;transition:all .2s;touch-action:manipulation}.prompt-favorite-btn:hover,.prompt-favorite-btn:focus-visible{outline:none;border-color:#f59e0b;color:#fbbf24;box-shadow:0 0 0 2px rgba(245,158,11,.18)}.prompt-favorite-btn.active{border-color:rgba(245,158,11,.55);background:rgba(245,158,11,.12);color:#fbbf24}@media (hover:none),(pointer:coarse){.prompt-favorite-btn{min-width:40px;min-height:40px}}';
  document.head.appendChild(style)
}

function loadFavoritePromptIds(){var ids={};try{if(!window.localStorage)return ids;var raw=window.localStorage.getItem(FAVORITES_STORAGE_KEY);var parsed=raw?JSON.parse(raw):[];if(Array.isArray(parsed)){parsed.forEach(function(id){if(typeof id==='string'&&id.trim())ids[id.trim().toUpperCase()]=true})}}catch(e){}return ids}
function saveFavoritePromptIds(){try{if(window.localStorage){var ids=Object.keys(favoritePromptIds).filter(function(id){return favoritePromptIds[id]===true}).sort();window.localStorage.setItem(FAVORITES_STORAGE_KEY,JSON.stringify(ids))}}catch(e){}}
function isFavoritePrompt(id){return favoritePromptIds[String(id||'').toUpperCase()]===true}
function toggleFavoritePrompt(id){var key=String(id||'').toUpperCase();if(!key)return;if(isFavoritePrompt(key)){delete favoritePromptIds[key];showToast('Removed '+key+' from Favorites')}else{favoritePromptIds[key]=true;showToast('Saved '+key+' to Favorites')}saveFavoritePromptIds();render()}

function syncLibraryTabs(){document.querySelectorAll('.cat-tab').forEach(function(b){b.classList.remove('active');if(b.dataset.cat==='all')b.classList.add('active')})}
function resetPromptKitView(){activeCat='all';activeSection=null;activeType=null;activeColor=null;collapsedSections={};var search=document.getElementById('search');if(search)search.value='';var clear=document.getElementById('searchClear');if(clear)clear.style.display='none';promptDetailOrigin=null;closePromptDetail(false);closeRef();var detail=document.getElementById('doctrineDetail');if(detail)detail.classList.remove('active');var list=document.getElementById('doctrineList');if(list)list.style.display='grid';syncLibraryTabs();renderSections();renderTypes();render();try{window.scrollTo({top:0,behavior:'smooth'})}catch(e){window.scrollTo(0,0)}showToast('Returned to all prompts')}

function showAddPrompt(){promptDetailOrigin=null;var el=document.getElementById('promptDetail');var html='<button class="prompt-detail-close" onclick="closePromptDetail()" aria-label="Close add prompt form">&times;</button>';html+='<div class="pd-glow" style="background:var(--accent)"></div>';html+='<div class="pd-header"><span class="pd-name">Add New Prompt</span></div>';html+='<div class="pd-section"><h4>Prompt ID</h4><input id="newPromptId" style="width:100%;padding:8px;background:var(--bg-surface);border:1px solid var(--border);border-radius:6px;color:var(--text-primary);font-size:13px" placeholder="e.g. P58"></div>';html+='<div class="pd-section"><h4>Name</h4><input id="newPromptName" style="width:100%;padding:8px;background:var(--bg-surface);border:1px solid var(--border);border-radius:6px;color:var(--text-primary);font-size:13px" placeholder="Prompt name"></div>';html+='<div class="pd-section"><h4>Type</h4><input id="newPromptType" style="width:100%;padding:8px;background:var(--bg-surface);border:1px solid var(--border);border-radius:6px;color:var(--text-primary);font-size:13px" placeholder="e.g. BUILD"></div>';html+='<div class="pd-section"><h4>Color</h4><input id="newPromptColor" style="width:100%;padding:8px;background:var(--bg-surface);border:1px solid var(--border);border-radius:6px;color:var(--text-primary);font-size:13px" placeholder="e.g. sky"></div>';html+='<div class="pd-section"><h4>When To Use</h4><textarea id="newPromptUseWhen" style="width:100%;padding:8px;background:var(--bg-surface);border:1px solid var(--border);border-radius:6px;color:var(--text-primary);font-size:13px;height:80px" placeholder="Describe when to use this prompt"></textarea></div>';html+='<div class="pd-section"><h4>Prompt Content</h4><textarea id="newPromptContent" style="width:100%;padding:8px;background:var(--bg-surface);border:1px solid var(--border);border-radius:6px;color:var(--text-primary);font-size:13px;height:120px" placeholder="The prompt text to copy"></textarea></div>';html+='<button class="pd-copy" onclick="submitNewPrompt()">Add to Library</button>';el.innerHTML=html;document.getElementById('promptDetailOverlay').classList.add('open')}
function submitNewPrompt(){var id=document.getElementById('newPromptId').value.trim();var name=document.getElementById('newPromptName').value.trim();var type=document.getElementById('newPromptType').value.trim();var color=document.getElementById('newPromptColor').value.trim();var useWhen=document.getElementById('newPromptUseWhen').value.trim();var content=document.getElementById('newPromptContent').value.trim();if(!id||!name){showToast('ID and Name are required');return}var p={id:id,seq:id.replace('P',''),name:name,type:type||'BUILD',color:color||'sky',category:'standard',class:'standard',sprintRole:'implementor',proofGate:'local validation',useWhen:useWhen||'Custom prompt',copyContent:content||'',keywords:[]};PROMPTS.push(p);closePromptDetail();render();showToast('Added '+id+' - commit docs/prompts.json to save')}

function normalizeSearchText(value){return String(value==null?'':value).toLowerCase().replace(/[^a-z0-9]+/g,' ').trim()}
function searchFieldScore(text,q,qWords,phraseScore,wordScore){var normalized=normalizeSearchText(text);if(!normalized)return 0;if(normalized===q)return phraseScore+20;if(normalized.indexOf(q)!==-1)return phraseScore;var words=normalized.split(/\s+/);var matched=qWords.every(function(queryWord){return words.some(function(word){return word===queryWord||word.indexOf(queryWord)===0||queryWord.indexOf(word)===0})});return matched?wordScore:0}
function synonymPromptIdsForQuery(q){var ids={};var normalizedQ=normalizeSearchText(q);if(!normalizedQ)return ids;var qWords=normalizedQ.split(/\s+/);Object.keys(SYNONYMS).forEach(function(rawKey){var key=normalizeSearchText(rawKey);var keyWords=key.split(/\s+/);var phraseMatch=key.indexOf(normalizedQ)!==-1||normalizedQ.indexOf(key)!==-1;var tokenMatch=qWords.length<=3&&keyWords.length<=4&&qWords.every(function(queryWord){return keyWords.some(function(keyWord){return keyWord===queryWord||keyWord.indexOf(queryWord)===0||queryWord.indexOf(keyWord)===0})});if(phraseMatch||tokenMatch){String(SYNONYMS[rawKey]).split(/\s+/).forEach(function(id){if(id)ids[id.toUpperCase()]=true})}});return ids}
function scorePromptForQuery(p,q,synIds){var normalizedQ=normalizeSearchText(q);if(!normalizedQ)return 0;var qWords=normalizedQ.split(/\s+/);var score=0;var id=normalizeSearchText(p.id);if(id===normalizedQ)score+=140;else if(id.indexOf(normalizedQ)===0)score+=100;if(synIds[String(p.id||'').toUpperCase()])score+=110;score+=searchFieldScore(p.name,normalizedQ,qWords,90,65);score+=searchFieldScore((p.keywords||[]).join(' '),normalizedQ,qWords,80,55);score+=searchFieldScore(p.type,normalizedQ,qWords,65,45);score+=searchFieldScore(p.useWhen,normalizedQ,qWords,50,35);score+=searchFieldScore(p.class,normalizedQ,qWords,35,20);score+=searchFieldScore(p.sprintRole,normalizedQ,qWords,25,15);score+=searchFieldScore(p.proofGate,normalizedQ,qWords,20,12);var body=normalizeSearchText(p.copyContent);if(body&&body.indexOf(normalizedQ)!==-1)score+=2;return score}
function filterPromptsForQuery(prompts,q){var normalizedQ=normalizeSearchText(q);if(!normalizedQ)return prompts.slice();var synIds=synonymPromptIdsForQuery(normalizedQ);var scored=prompts.map(function(prompt){return{prompt:prompt,score:scorePromptForQuery(prompt,normalizedQ,synIds)}}).filter(function(item){return item.score>0});var maxScore=scored.reduce(function(max,item){return Math.max(max,item.score)},0);var strongFloor=maxScore>=40?10:1;return scored.filter(function(item){return item.score>=strongFloor}).sort(function(a,b){var delta=b.score-a.score;if(delta)return delta;return promptSequenceValue(a.prompt)-promptSequenceValue(b.prompt)}).map(function(item){var result=Object.assign({},item.prompt);result._searchScore=item.score;return result})}

function promptSequenceValue(p){var raw=String((p&&p.seq)||((p&&p.id)||''));var n=parseInt(raw.replace(/\D/g,''),10);return isNaN(n)?Number.MAX_SAFE_INTEGER:n}
function sectionForPrompt(p){for(var i=0;i<SECTIONS.length;i++){if(SECTIONS[i].types.indexOf(p.type)!==-1)return SECTIONS[i]}return null}
function groupPromptsBySection(prompts){
  var groups=[];
  prompts.slice().sort(function(a,b){var delta=promptSequenceValue(a)-promptSequenceValue(b);return delta||String(a.id).localeCompare(String(b.id))}).forEach(function(p){
    var section=sectionForPrompt(p);
    var name=section?section.name:'Other';
    var glow=section?section.glow:'#64748b';
    var group=groups.length?groups[groups.length-1]:null;
    if(!group||group.name!==name){group={name:name,glow:glow,prompts:[]};groups.push(group)}
    group.prompts.push(p)
  });
  return groups
}
function renderSections(){var nav=document.getElementById('sectionsNav');nav.setAttribute('aria-label','Prompt categories and favorites');nav.innerHTML='<button class="section-tab'+(activeSection===null?' active':'')+'" data-section="__all__">All Categories</button><button class="section-tab'+(activeSection==='__favorites__'?' active':'')+'" data-section="__favorites__">★ Favorites</button>';SECTIONS.forEach(function(s){nav.innerHTML+='<button class="section-tab'+(activeSection===s.name?' active':'')+'" data-section="'+s.name+'">'+s.name+'</button>'})}
function renderTypes(){var nav=document.getElementById('typeNav');var types={};nav.setAttribute('aria-label','Prompt types');PROMPTS.forEach(function(p){if(!types[p.type])types[p.type]={count:0,color:p.color};types[p.type].count++});nav.innerHTML='<div class="type-chip'+(activeType===null?' active':'')+'" data-type="__all__">All Types</div>';Object.keys(types).sort().forEach(function(t){var hex=COLORS[types[t].color.toLowerCase()]||'#64748b';nav.innerHTML+='<div class="type-chip'+(activeType===t?' active':'')+'" data-type="'+t+'"><span class="dot" style="background:'+hex+'"></span>'+t+' ('+types[t].count+')</div>'})}
function clearSearch(){document.getElementById('search').value='';render()}

function appendSectionDivider(grid,group){
  var secGlow=group.glow||'#64748b';
  var icons={'Favorites':'★','Foundation':'⚒','Discover & Plan':'⚛','Build & Repair':'⚙','Validate & Protect':'✔','Integrate & Ship':'✈','Autonomy & Night Shift':'☾'};
  var collapsed=isSectionCollapsed(group.name);
  var safeGroup=escapePromptHtml(group.name);
  var divider=document.createElement('div');
  divider.className='section-divider'+(collapsed?' section-collapsed':'');
  divider.setAttribute('data-category',group.name);
  divider.innerHTML='<a class="page-jump page-jump-top" href="#page-top" aria-label="Go to top of page">&#8593; Top</a><div class="sd-line" style="background:'+secGlow+'"></div><button class="sd-label section-toggle" type="button" data-collapse-section="'+safeGroup+'" aria-expanded="'+(!collapsed)+'" aria-label="'+(collapsed?'Expand ':'Collapse ')+safeGroup+' section"><span class="section-chevron" aria-hidden="true">&#9656;</span><span class="sd-icon">'+(icons[group.name]||'◆')+'</span>'+safeGroup+'<span class="sd-count">'+group.prompts.length+' prompts</span></button><div class="sd-line" style="background:'+secGlow+'"></div><a class="page-jump page-jump-bottom" href="#page-bottom" aria-label="Go to bottom of page">Bottom &#8595;</a>';
  grid.appendChild(divider)
}
function appendDistributedPageNavigation(grid,visiblePromptIndex){
  var navigation=document.createElement('nav');
  navigation.className='distributed-page-navigation';
  navigation.setAttribute('aria-label','Prompt list navigation after '+visiblePromptIndex+' visible prompts');
  navigation.innerHTML='<a class="page-jump page-jump-top" href="#page-top" aria-label="Go to top of page">&#8593; Top</a><span class="distributed-page-navigation-count">After prompt '+visiblePromptIndex+'</span><a class="page-jump page-jump-bottom" href="#page-bottom" aria-label="Go to bottom of page">Bottom &#8595;</a>';
  grid.appendChild(navigation)
}
function appendPromptCard(grid,p){
  var hex=COLORS[p.color.toLowerCase()]||'#64748b';
  var isGnhf=p.category==='gnhf';
  var safeId=escapePromptHtml(p.id),safeName=escapePromptHtml(p.name),safeType=escapePromptHtml(p.type),safeColor=escapePromptHtml(p.color),safeUseWhen=escapePromptHtml(p.useWhen),safeSprintRole=escapePromptHtml(p.sprintRole),safeProofGate=escapePromptHtml(p.proofGate);
  var card=document.createElement('div');
  card.className='prompt-card'+(isGnhf?' gnhf':'');
  card.tabIndex=0;
  card.setAttribute('role','group');
  card.setAttribute('aria-label',p.id+' '+p.name+'. Click or tap to copy. Double-click or press Enter to expand. Touch users may use Open.');
  card.innerHTML='<div class="glow-bar" style="background:'+hex+'"></div><div class="prompt-header"><span class="prompt-id">'+safeId+'</span>'+(isGnhf?'<span class="gnhf-badge">☾ GNHF</span>':'')+'<span class="prompt-name">'+safeName+'</span></div><div class="prompt-type">'+safeType+' · '+safeColor+'</div><div class="prompt-desc">'+safeUseWhen+'</div><div class="prompt-meta"><span class="prompt-badge">'+safeSprintRole+'</span><span class="prompt-badge">'+safeProofGate+'</span></div>';
  card.onclick=function(e){cancelPromptCardCopy(card);card._copyTimer=setTimeout(function(){copyPrompt(p.id);card._copyTimer=null},300)};
  card.ondblclick=function(e){cancelPromptCardCopy(card);e.preventDefault();showPromptDetail(p.id,card)};
  card.onkeydown=function(e){if(e.target!==card)return;if(e.key==='Enter'){cancelPromptCardCopy(card);e.preventDefault();e.stopPropagation();showPromptDetail(p.id,card)}else if(e.key===' '){cancelPromptCardCopy(card);e.preventDefault();e.stopPropagation();copyPrompt(p.id)}};
  var favBtn=document.createElement('button');
  favBtn.className='prompt-favorite-btn'+(isFavoritePrompt(p.id)?' active':'');
  favBtn.textContent=isFavoritePrompt(p.id)?'★':'☆';
  favBtn.setAttribute('aria-label',(isFavoritePrompt(p.id)?'Remove ':'Add ')+p.id+(isFavoritePrompt(p.id)?' from Favorites':' to Favorites'));
  favBtn.setAttribute('aria-pressed',isFavoritePrompt(p.id)?'true':'false');
  favBtn.title=isFavoritePrompt(p.id)?'Remove from Favorites':'Save to Favorites';
  favBtn.onclick=function(e){cancelPromptCardCopy(card);e.preventDefault();e.stopPropagation();toggleFavoritePrompt(p.id)};
  card.querySelector('.prompt-header').appendChild(favBtn);
  var openBtn=document.createElement('button');
  openBtn.className='prompt-open-btn';
  openBtn.textContent='Open';
  openBtn.setAttribute('aria-label','Open '+p.id+' prompt detail');
  openBtn.onclick=function(e){cancelPromptCardCopy(card);e.stopPropagation();showPromptDetail(p.id,card)};
  card.appendChild(openBtn);
  var btn=document.createElement('button');
  btn.className='prompt-copy-btn';
  btn.textContent='Copy';
  btn.onclick=function(e){e.stopPropagation();copyPrompt(p.id);btn.classList.add('copied');btn.textContent='Copied!';setTimeout(function(){btn.classList.remove('copied');btn.textContent='Copy'},1500)};
  card.appendChild(btn);
  grid.appendChild(card)
}

function render(){
  var q=document.getElementById('search').value.toLowerCase().trim();
  var f=PROMPTS.slice();
  if(activeCat!=='all'&&activeCat!=='doctrine')f=f.filter(function(p){return p.category===activeCat});
  if(activeSection==='__favorites__')f=f.filter(function(p){return isFavoritePrompt(p.id)});else if(activeSection){var secTypes=[];for(var i=0;i<SECTIONS.length;i++){if(SECTIONS[i].name===activeSection){secTypes=SECTIONS[i].types;break}}f=f.filter(function(p){return secTypes.indexOf(p.type)!==-1})}
  if(activeType)f=f.filter(function(p){return p.type===activeType});
  if(activeColor)f=f.filter(function(p){return p.color&&p.color.toLowerCase()===activeColor.toLowerCase()});
  if(q)f=filterPromptsForQuery(f,q);
  var grid=document.getElementById('grid');
  var dv=document.getElementById('doctrineView');
  grid.innerHTML='';
  if(activeCat==='doctrine'){grid.style.display='none';dv.classList.add('active');renderDoctrineList();document.getElementById('showing').textContent=Object.keys(DOCTRINE).length;document.getElementById('total').textContent=PROMPTS.length;return}
  grid.style.display='grid';
  dv.classList.remove('active');
  var groups=groupPromptsBySection(f);
  var visiblePromptIndex=0;
  groups.forEach(function(group){
    appendSectionDivider(grid,group);
    if(!isSectionCollapsed(group.name)){group.prompts.forEach(function(p){appendPromptCard(grid,p);visiblePromptIndex++;if(visiblePromptIndex%PROMPT_NAVIGATION_INTERVAL===0)appendDistributedPageNavigation(grid,visiblePromptIndex)})}
  });
  if(visiblePromptIndex>0&&visiblePromptIndex%PROMPT_NAVIGATION_INTERVAL!==0)appendDistributedPageNavigation(grid,visiblePromptIndex);
  document.getElementById('showing').textContent=f.length;
  document.getElementById('total').textContent=PROMPTS.length
}

function renderDoctrineList(){var el=document.getElementById('doctrineList');document.getElementById('doctrineDetail').classList.remove('active');el.style.display='grid';el.innerHTML='';Object.keys(DOCTRINE).forEach(function(key){var d=DOCTRINE[key];var card=document.createElement('div');card.className='doctrine-card';card.onclick=function(){document.getElementById('doctrineDetail').classList.add('active');el.style.display='none';var html='<h2 style="color:var(--accent);margin-bottom:0.25rem">'+d.title+'</h2><div style="color:var(--text-muted);margin-bottom:1.5rem">'+d.subtitle+'</div>';d.sections.forEach(function(s){html+='<div class="doctrine-section"><h4>'+s.heading+'</h4>';var lines=s.content.split('\n');var inTable=false;var tbl='';lines.forEach(function(line){if(line.match(/^\|.*\|$/)){if(!inTable){inTable=true;tbl='<table>'}if(line.match(/^\|[-\s|]+$/)){return}var cells=line.split('|').filter(function(c){return c.trim()!==''});var tag=tbl.indexOf('<th>')===-1?'th':'td';tbl+='<tr>'+cells.map(function(c){return '<'+tag+'>'+c.trim()+'</'+tag+'>'}).join('')+'</tr>'}else{if(inTable){tbl+='</table>';html+=tbl;inTable=false;tbl=''}html+='<p>'+line+'</p>'}});if(inTable){tbl+='</table>';html+=tbl}html+='<div style="margin-top:8px"><button class="pd-copy" onclick="copyToClipboard(this.closest(\'.doctrine-section\').querySelector(\'pre\').textContent);this.classList.add(\'copied\');this.textContent=\'Copied!\';setTimeout(function(){this.classList.remove(\'copied\');this.textContent=\'Copy Section\'}.bind(this),1500)">Copy Section</button></div>';html+='</div>'});document.getElementById('doctrineContent').innerHTML=html};card.innerHTML='<h3>'+d.title+'</h3><div class="subtitle">'+d.subtitle+'</div><div class="count">'+d.sections.length+' sections →</div>';el.appendChild(card)})}

document.getElementById('doctrineBack').onclick=function(){renderDoctrineList()};
document.getElementById('addPromptBtn').addEventListener('click',showAddPrompt);
document.getElementById('searchClear').addEventListener('click',clearSearch);
document.addEventListener('click',function(e){var collapse=e.target.closest('.section-toggle');if(collapse){e.preventDefault();e.stopPropagation();togglePromptSection(collapse.getAttribute('data-collapse-section'));return}var ct=e.target.closest('.cat-tab');if(ct){activeCat=ct.dataset.cat;document.querySelectorAll('.cat-tab').forEach(function(b){b.classList.remove('active')});ct.classList.add('active');render();return}var st=e.target.closest('.section-tab');if(st){var sn=st.dataset.section;activeSection=sn==='__all__'?null:sn;document.querySelectorAll('.section-tab').forEach(function(b){b.classList.remove('active')});st.classList.add('active');render();return}var tc=e.target.closest('.type-chip');if(tc){var tn=tc.dataset.type;activeType=tn==='__all__'?null:tn;document.querySelectorAll('.type-chip').forEach(function(b){b.classList.remove('active')});tc.classList.add('active');render();return}});
document.getElementById('search').addEventListener('input',function(){var v=this.value;document.getElementById('searchClear').style.display=v?'block':'none';render()});
document.getElementById('refBtn').addEventListener('click',toggleRef);
document.getElementById('refOverlay').addEventListener('click',toggleRef);
document.getElementById('refClose').addEventListener('click',toggleRef);
document.getElementById('promptDetailOverlay').addEventListener('click',function(e){if(e.target!==this)return;closePromptDetail(false);focusPromptOrigin()});
document.addEventListener('keydown',function(e){if(e.target.tagName==='INPUT'||e.target.tagName==='TEXTAREA')return;switch(e.key){case'1':activeCat='all';break;case'2':activeCat='standard';break;case'3':activeCat='gnhf';break;case'4':activeCat='doctrine';break;case'r':case'R':toggleRef();return;case'/':e.preventDefault();document.getElementById('search').focus();return;case'Escape':if(document.getElementById('promptDetailOverlay').classList.contains('open')){closePromptDetail();return}if(document.getElementById('refSidebar').classList.contains('open')){toggleRef();return}if(document.getElementById('search').value){clearSearch();return}if(activeType){activeType=null;render();return}if(activeSection){activeSection=null;render();return}if(activeCat!=='all'){activeCat='all';render();return}return;default:return}document.querySelectorAll('.cat-tab').forEach(function(b){b.classList.remove('active');if(b.dataset.cat===activeCat)b.classList.add('active')});render()});

(function buildRef(){var el=document.getElementById('refContent');var html='';if(REF.gnhfWorkflow){html+='<div class="ref-section"><h3>GNHF Workflow</h3>';REF.gnhfWorkflow.forEach(function(w){var pid=w.prompt||'';html+='<div class="ref-item'+(pid?' data-prompt="'+pid+'"':'')+'"><span class="label">'+pid+'</span> '+(w.useCase||w.moment||'')+'</div>'});html+='</div>'}if(REF.nightShiftRunbook){html+='<div class="ref-section"><h3>Night Shift Runbook</h3>';REF.nightShiftRunbook.forEach(function(r){if(r.scenario==='Scenario')return;html+='<div class="ref-item"><span class="label">'+r.scenario+'</span> '+r.purpose+'</div>'});html+='</div>'}if(REF.variables){html+='<div class="ref-section"><h3>Variables</h3>';REF.variables.forEach(function(v){html+='<div class="ref-item"><span class="label">'+v.name+'</span> '+v.description+'</div>'});html+='</div>'}if(REF.promptSequence){html+='<div class="ref-section"><h3>Prompt Sequence</h3>';REF.promptSequence.forEach(function(s){html+='<div class="ref-item" data-prompt="'+s.promptId+'"><span class="label">'+s.seq+'</span> '+s.promptId+': '+s.useItFor+'</div>'});html+='</div>'}el.innerHTML=html;el.querySelectorAll('.ref-item[data-prompt]').forEach(function(item){item.addEventListener('click',function(){var pid=item.getAttribute('data-prompt');if(!pid)return;closeRef();setTimeout(function(){showPromptDetail(pid)},300)})})})();

ensurePageNavigation();
ensureMobileSupport();
ensureDiscoverySupport();
var homeReset=document.getElementById('homeReset');
if(homeReset){homeReset.addEventListener('click',resetPromptKitView);homeReset.addEventListener('keydown',function(e){if(e.key==='Enter'||e.key===' '){e.preventDefault();resetPromptKitView()}})}
renderSections();
renderTypes();
render();
