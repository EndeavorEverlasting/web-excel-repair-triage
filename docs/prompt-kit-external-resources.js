(function(){
'use strict';
var OPERANT_EXTERNAL_RESOURCE_SCHEMA='operant-external-resources/v1';
var OPERANT_EXTERNAL_RESOURCE_INDEX='resources.v1.json';
var OPERANT_EXTERNAL_RESOURCE_PAGE_SIZE=40;
var externalResourceIndex=null;
var externalResourceQuery='';
var externalResourcePage=0;
var externalResourceLoadPromise=null;
try{
  Object.defineProperty(window,'externalResourceIndex',{get:function(){return externalResourceIndex},set:function(v){externalResourceIndex=v},configurable:true});
  Object.defineProperty(window,'externalResourcePage',{get:function(){return externalResourcePage},set:function(v){externalResourcePage=v},configurable:true});
}catch(e){}

function ensureExternalResourceStyles(){
  if(document.getElementById('operant-external-resource-styles'))return;
  var style=document.createElement('style');
  style.id='operant-external-resource-styles';
  style.textContent='.operant-resource-button{min-height:34px;padding:6px 10px;border:1px solid var(--border);border-radius:7px;background:var(--bg-surface);color:var(--text-secondary);font:600 11px/1.2 inherit;cursor:pointer}.operant-resource-button:hover,.operant-resource-button:focus-visible{outline:none;border-color:var(--accent);color:var(--text-primary)}.operant-resource-backdrop{position:fixed;inset:0;z-index:70;background:rgba(0,0,0,.58);display:flex;align-items:flex-start;justify-content:center;padding:7vh 16px}.operant-resource-backdrop[hidden]{display:none!important}.operant-resource-panel{width:min(860px,100%);max-height:86vh;overflow:hidden;display:grid;grid-template-rows:auto auto auto minmax(0,1fr) auto;gap:10px;padding:16px;border:1px solid var(--border);border-radius:12px;background:var(--bg-surface);box-shadow:0 20px 60px rgba(0,0,0,.45)}.operant-resource-head{display:flex;align-items:center;justify-content:space-between;gap:12px}.operant-resource-head h2{margin:0;font-size:16px}.operant-resource-close{border:0;background:transparent;color:var(--text-secondary);font-size:22px;cursor:pointer}.operant-resource-search{width:100%;box-sizing:border-box;min-height:40px;padding:8px 10px;border:1px solid var(--border);border-radius:7px;background:var(--bg);color:var(--text-primary)}.operant-resource-sources{display:grid;grid-template-columns:repeat(3,minmax(0,1fr));gap:8px}.operant-resource-source{display:grid;gap:4px;padding:9px;border:1px solid var(--border);border-radius:8px;background:var(--bg)}.operant-resource-source strong{font-size:10px;color:var(--text-primary);overflow-wrap:anywhere}.operant-resource-source span{font-size:9px;color:var(--text-muted)}.operant-resource-source a{font-size:9px;color:var(--accent);text-decoration:none}.operant-resource-list{overflow:auto;display:grid;gap:8px;align-content:start}.operant-resource-row{display:grid;grid-template-columns:minmax(0,1fr) auto;gap:8px 12px;padding:10px;border:1px solid var(--border);border-radius:8px}.operant-resource-title{font-weight:700;color:var(--text-primary)}.operant-resource-meta{margin-top:3px;color:var(--text-muted);font-size:10px}.operant-resource-actions{display:flex;align-items:center;gap:6px}.operant-resource-actions a,.operant-resource-actions button{min-height:30px;padding:5px 8px;border:1px solid var(--border);border-radius:6px;background:var(--bg);color:var(--text-secondary);font:600 10px/1.2 inherit;text-decoration:none;cursor:pointer}.operant-resource-actions a:hover,.operant-resource-actions button:hover{border-color:var(--accent);color:var(--text-primary)}.operant-resource-foot{display:flex;align-items:center;justify-content:space-between;gap:8px;color:var(--text-muted);font-size:10px}.operant-resource-page-actions{display:flex;gap:6px}.operant-resource-page{min-height:30px;padding:5px 9px;border:1px solid var(--border);border-radius:6px;background:var(--bg);color:var(--text-secondary);cursor:pointer}.operant-resource-empty{padding:18px 8px;color:var(--text-muted);text-align:center}@media(max-width:640px){.operant-resource-sources{grid-template-columns:1fr}.operant-resource-backdrop{padding:3vh 8px}.operant-resource-panel{max-height:94vh;padding:12px}.operant-resource-row{grid-template-columns:1fr}.operant-resource-actions{justify-content:flex-start;flex-wrap:wrap}}';
  document.head.appendChild(style)
}

function ensureExternalResourceSurface(){
  ensureExternalResourceStyles();
  var controls=document.querySelector('.header-controls');
  if(controls&&!document.getElementById('externalResourcesButton')){
    var button=document.createElement('button');
    button.id='externalResourcesButton';
    button.type='button';
    button.className='operant-resource-button';
    button.textContent='Resources';
    button.setAttribute('aria-haspopup','dialog');
    button.setAttribute('aria-controls','operantExternalResources');
    button.addEventListener('click',openExternalResources);
    controls.appendChild(button)
  }
  if(document.getElementById('operantExternalResources'))return;
  var backdrop=document.createElement('div');
  backdrop.className='operant-resource-backdrop';
  backdrop.id='operantExternalResources';
  backdrop.hidden=true;
  backdrop.innerHTML='<section class="operant-resource-panel" role="dialog" aria-modal="true" aria-labelledby="operantResourceTitle"><div class="operant-resource-head"><h2 id="operantResourceTitle">Open resources</h2><button type="button" class="operant-resource-close" aria-label="Close resources">×</button></div><input class="operant-resource-search" type="search" placeholder="Search external skills and existing Operant coverage" aria-label="Search external resources"><div class="operant-resource-sources" aria-label="Registered external source libraries"></div><div class="operant-resource-list" aria-live="polite"></div><div class="operant-resource-foot"><span class="operant-resource-count">Catalog loads only when opened.</span><span class="operant-resource-page-actions"><button type="button" class="operant-resource-page operant-resource-prev" hidden>Previous</button><button type="button" class="operant-resource-page operant-resource-next" hidden>Next</button></span></div></section>';
  backdrop.addEventListener('click',function(event){if(event.target===backdrop)closeExternalResources()});
  backdrop.querySelector('.operant-resource-close').addEventListener('click',closeExternalResources);
  backdrop.querySelector('.operant-resource-search').addEventListener('input',function(event){externalResourceQuery=String(event.target.value||'').trim().toLowerCase();externalResourcePage=0;renderExternalResourcePage()});
  backdrop.querySelector('.operant-resource-prev').addEventListener('click',function(){if(externalResourcePage>0){externalResourcePage-=1;renderExternalResourcePage()}});
  backdrop.querySelector('.operant-resource-next').addEventListener('click',function(){externalResourcePage+=1;renderExternalResourcePage()});
  document.body.appendChild(backdrop)
}

function loadExternalResources(){
  if(externalResourceIndex)return Promise.resolve(externalResourceIndex);
  if(externalResourceLoadPromise)return externalResourceLoadPromise;
  externalResourceLoadPromise=window.fetch(OPERANT_EXTERNAL_RESOURCE_INDEX,{cache:'no-cache',credentials:'same-origin'}).then(function(response){
    if(!response.ok)throw new Error('resource index HTTP '+response.status);
    return response.json()
  }).then(function(payload){
    if(!payload||payload.schema_version!=='operant-external-resource-index/v1'||!Array.isArray(payload.resources))throw new Error('resource index schema mismatch');
    externalResourceIndex=payload;
    return payload
  }).finally(function(){externalResourceLoadPromise=null});
  return externalResourceLoadPromise
}

function resourceMatches(item){
  if(!externalResourceQuery)return true;
  var coverage=item.coverage||{};
  var haystack=[item.title,item.slug,item.source_id,item.source_repo,coverage.target_id,coverage.target_title].concat(item.search_terms||[]).join(' ').toLowerCase();
  return externalResourceQuery.split(/\s+/).filter(Boolean).every(function(term){return haystack.indexOf(term)!==-1})
}

function focusExistingPrompt(promptId){
  closeExternalResources();
  var search=document.getElementById('search');
  if(!search)return;
  search.value=promptId;
  search.dispatchEvent(new Event('input',{bubbles:true}));
  search.focus()
}

function sourceRepositoryUrl(floor){var repository=String(floor&&floor.repository||'').trim();return repository?'https://github.com/'+repository:'#'}
function renderExternalSourceChoices(){var surface=document.getElementById('operantExternalResources');if(!surface||!externalResourceIndex)return;var host=surface.querySelector('.operant-resource-sources');if(!host)return;var filtered=externalResourceIndex.resources.filter(resourceMatches);var floors=(externalResourceIndex.source_floor||[]).map(function(floor,index){var matchCount=filtered.filter(function(item){return item.source_id===floor.id}).length;var catalogBonus=floor.search_mode==='on_demand'&&externalResourceQuery?1:0;return {floor:floor,index:index,matchCount:matchCount,catalogBonus:catalogBonus}}).sort(function(a,b){return b.matchCount-a.matchCount||b.catalogBonus-a.catalogBonus||a.index-b.index});host.innerHTML='';floors.forEach(function(entry){var floor=entry.floor,card=document.createElement('article');card.className='operant-resource-source';card.setAttribute('data-source-id',String(floor.id||''));var title=document.createElement('strong');title.textContent=String(floor.repository||floor.id||'External source');var meta=document.createElement('span');if(floor.enumeration==='catalog_csv')meta.textContent=String(floor.catalog_entry_count||0)+' catalog prompts · on-demand';else meta.textContent=String(floor.resource_count||0)+' indexed skills'+(entry.matchCount?' · '+entry.matchCount+' matching':'');var link=document.createElement('a');link.href=sourceRepositoryUrl(floor);link.target='_blank';link.rel='noopener noreferrer';link.textContent='Open source library';card.appendChild(title);card.appendChild(meta);card.appendChild(link);host.appendChild(card)})}

function renderExternalResourcePage(){
  var surface=document.getElementById('operantExternalResources');
  if(!surface)return;
  var list=surface.querySelector('.operant-resource-list');
  var count=surface.querySelector('.operant-resource-count');
  var previous=surface.querySelector('.operant-resource-prev');
  var next=surface.querySelector('.operant-resource-next');
  if(!externalResourceIndex){list.innerHTML='<div class="operant-resource-empty">Loading current resource index…</div>';count.textContent='Fetching metadata only…';previous.hidden=true;next.hidden=true;return}
  renderExternalSourceChoices();
  var filtered=externalResourceIndex.resources.filter(resourceMatches);
  var pageCount=Math.max(1,Math.ceil(filtered.length/OPERANT_EXTERNAL_RESOURCE_PAGE_SIZE));
  externalResourcePage=Math.min(externalResourcePage,pageCount-1);
  var start=externalResourcePage*OPERANT_EXTERNAL_RESOURCE_PAGE_SIZE;
  var end=start+OPERANT_EXTERNAL_RESOURCE_PAGE_SIZE;
  var visible=filtered.slice(start,end);
  list.innerHTML='';
  visible.forEach(function(item){
    var coverage=item.coverage||{};
    var row=document.createElement('article');row.className='operant-resource-row';
    var detail=document.createElement('div');
    var title=document.createElement('div');title.className='operant-resource-title';title.textContent=item.title;
    var meta=document.createElement('div');meta.className='operant-resource-meta';
    var coverageLabel=coverage.disposition==='POINT_TO_EXISTING_PROMPT'?'Already covered by '+coverage.target_id:coverage.disposition==='POINT_TO_EXISTING_SKILL'?'Local skill: '+coverage.target_title:'External resource · prompt gap under review';
    meta.textContent=item.source_id+' · '+coverageLabel;
    detail.appendChild(title);detail.appendChild(meta);
    var actions=document.createElement('div');actions.className='operant-resource-actions';
    if(coverage.disposition==='POINT_TO_EXISTING_PROMPT'&&coverage.target_id){var use=document.createElement('button');use.type='button';use.textContent='Use '+coverage.target_id;use.addEventListener('click',function(){focusExistingPrompt(coverage.target_id)});actions.appendChild(use)}
    var open=document.createElement('a');open.href=item.url;open.target='_blank';open.rel='noopener noreferrer';open.textContent='Open source';actions.appendChild(open);
    row.appendChild(detail);row.appendChild(actions);list.appendChild(row)
  });
  if(!visible.length)list.innerHTML='<div class="operant-resource-empty">No resources match this search.</div>';
  count.textContent=filtered.length+' matching · '+externalResourceIndex.summary.resource_count+' indexed · page '+(externalResourcePage+1)+'/'+pageCount+' · metadata only';
  previous.hidden=externalResourcePage===0;
  next.hidden=end>=filtered.length
}

function openExternalResources(){
  var request=arguments.length?arguments[0]:null;
  ensureExternalResourceSurface();
  var surface=document.getElementById('operantExternalResources');
  var input=surface.querySelector('.operant-resource-search');
  var requestedQuery='';
  if(typeof request==='string')requestedQuery=request;else if(request&&typeof request.query==='string')requestedQuery=request.query;
  externalResourceQuery=String(requestedQuery||'').trim().toLowerCase();
  input.value=String(requestedQuery||'');
  surface.hidden=false;
  externalResourcePage=0;
  renderExternalResourcePage();
  loadExternalResources().then(function(){renderExternalResourcePage();input.focus()}).catch(function(error){var list=surface.querySelector('.operant-resource-list');list.innerHTML='<div class="operant-resource-empty">Resource catalog unavailable. Existing prompts remain fully usable.</div>';surface.querySelector('.operant-resource-count').textContent=String(error&&error.message||'Resource load failed')})
}
function openExternalResourcesForUseCase(query,origin){openExternalResources({query:query,origin:origin||null})}

function closeExternalResources(){var surface=document.getElementById('operantExternalResources');if(surface)surface.hidden=true}

document.addEventListener('keydown',function(event){if(event.key==='Escape'){var surface=document.getElementById('operantExternalResources');if(surface&&!surface.hidden){event.preventDefault();closeExternalResources()}}});

if(document.readyState==='loading')document.addEventListener('DOMContentLoaded',ensureExternalResourceSurface,{once:true});else ensureExternalResourceSurface();
window.OperantExternalResources={schema:OPERANT_EXTERNAL_RESOURCE_SCHEMA,open:openExternalResources,openForUseCase:openExternalResourcesForUseCase,close:closeExternalResources,load:loadExternalResources,render:renderExternalResourcePage};
})();
