var activeCat='all',activeSection=null,activeType=null,activeColor=null;
var promptDetailOrigin=null;

function showToast(msg){var t=document.getElementById('toast');t.textContent=msg;t.classList.add('show');setTimeout(function(){t.classList.remove('show')},2000)}
function toggleRef(){var s=document.getElementById('refSidebar'),o=document.getElementById('refOverlay');s.classList.toggle('open');o.classList.toggle('open')}
function closeRef(){var s=document.getElementById('refSidebar'),o=document.getElementById('refOverlay');s.classList.remove('open');o.classList.remove('open')}
function copyToClipboard(text){if(navigator.clipboard&&navigator.clipboard.writeText){navigator.clipboard.writeText(text).then(function(){showToast('Copied to clipboard')})}else{var ta=document.createElement('textarea');ta.value=text;ta.style.position='fixed';ta.style.opacity='0';document.body.appendChild(ta);ta.select();document.execCommand('copy');document.body.removeChild(ta);showToast('Copied to clipboard')}}
function copyPrompt(id){var p=PROMPTS.find(function(x){return x.id===id});if(p&&p.copyContent){copyToClipboard(p.copyContent)}}
function focusPromptOrigin(){if(promptDetailOrigin&&document.body.contains(promptDetailOrigin)){try{promptDetailOrigin.focus({preventScroll:true})}catch(e){promptDetailOrigin.focus()}}}
function showPromptDetail(id,origin){var p=PROMPTS.find(function(x){return x.id===id});if(!p)return;promptDetailOrigin=origin||null;var hex=COLORS[p.color.toLowerCase()]||'#64748b';var el=document.getElementById('promptDetail');var html='<button class="prompt-detail-close" onclick="closePromptDetail()" aria-label="Close prompt detail">&times;</button>';html+='<div class="pd-glow" style="background:'+hex+'"></div>';html+='<div class="pd-header"><span class="pd-id">'+p.id+'</span><span class="pd-name">'+p.name+'</span></div>';html+='<div class="pd-type">'+p.type+' · '+p.color+' · '+p.category+'</div>';html+='<div class="pd-badges"><span class="pd-badge">'+p.sprintRole+'</span><span class="pd-badge">'+p.proofGate+'</span><span class="pd-badge">'+p.class+'</span></div>';html+='<div class="pd-section"><h4>When To Use</h4><pre>'+p.useWhen+'</pre></div>';if(p.copyContent){html+='<div class="pd-section"><h4>Prompt Content</h4><pre>'+p.copyContent+'</pre></div>'}html+='<button class="pd-copy" onclick="copyPrompt(\''+p.id+'\');this.classList.add(\'copied\');this.textContent=\'Copied!\';setTimeout(function(){this.classList.remove(\'copied\');this.textContent=\'Copy to Clipboard\'}.bind(this),1500)">Copy to Clipboard</button>';el.innerHTML=html;document.getElementById('promptDetailOverlay').classList.add('open');var closeButton=el.querySelector('.prompt-detail-close');if(closeButton)closeButton.focus()}
function closePromptDetail(restoreFocus){document.getElementById('promptDetailOverlay').classList.remove('open');if(restoreFocus!==false)focusPromptOrigin()}
function cancelPromptCardCopy(card){if(card&&card._copyTimer){clearTimeout(card._copyTimer);card._copyTimer=null}}

function ensurePageNavigation(){
  if(!document.getElementById('page-top')){var top=document.createElement('span');top.id='page-top';top.className='page-anchor';top.setAttribute('aria-hidden','true');document.body.insertBefore(top,document.body.firstChild)}
  if(!document.getElementById('page-bottom')){var bottom=document.createElement('span');bottom.id='page-bottom';bottom.className='page-anchor';bottom.setAttribute('aria-hidden','true');document.body.appendChild(bottom)}
  if(!document.getElementById('page-navigation-styles')){var style=document.createElement('style');style.id='page-navigation-styles';style.textContent='.page-anchor{display:block;position:relative;width:0;height:0;overflow:hidden}.section-divider .page-jump{display:inline-flex;align-items:center;justify-content:center;min-width:62px;padding:4px 8px;border:1px solid var(--border);border-radius:6px;background:var(--bg-surface);color:var(--text-muted);font-size:10px;font-weight:700;letter-spacing:.04em;text-decoration:none;text-transform:uppercase;transition:all .2s}.section-divider .page-jump:hover,.section-divider .page-jump:focus{border-color:var(--accent);color:var(--accent);outline:none;box-shadow:0 0 0 2px var(--accent-glow)}';document.head.appendChild(style)}
}

function showAddPrompt(){promptDetailOrigin=null;var el=document.getElementById('promptDetail');var html='<button class="prompt-detail-close" onclick="closePromptDetail()" aria-label="Close add prompt form">&times;</button>';html+='<div class="pd-glow" style="background:var(--accent)"></div>';html+='<div class="pd-header"><span class="pd-name">Add New Prompt</span></div>';html+='<div class="pd-section"><h4>Prompt ID</h4><input id="newPromptId" style="width:100%;padding:8px;background:var(--bg-surface);border:1px solid var(--border);border-radius:6px;color:var(--text-primary);font-size:13px" placeholder="e.g. P58"></div>';html+='<div class="pd-section"><h4>Name</h4><input id="newPromptName" style="width:100%;padding:8px;background:var(--bg-surface);border:1px solid var(--border);border-radius:6px;color:var(--text-primary);font-size:13px" placeholder="Prompt name"></div>';html+='<div class="pd-section"><h4>Type</h4><input id="newPromptType" style="width:100%;padding:8px;background:var(--bg-surface);border:1px solid var(--border);border-radius:6px;color:var(--text-primary);font-size:13px" placeholder="e.g. BUILD"></div>';html+='<div class="pd-section"><h4>Color</h4><input id="newPromptColor" style="width:100%;padding:8px;background:var(--bg-surface);border:1px solid var(--border);border-radius:6px;color:var(--text-primary);font-size:13px" placeholder="e.g. sky"></div>';html+='<div class="pd-section"><h4>When To Use</h4><textarea id="newPromptUseWhen" style="width:100%;padding:8px;background:var(--bg-surface);border:1px solid var(--border);border-radius:6px;color:var(--text-primary);font-size:13px;height:80px" placeholder="Describe when to use this prompt"></textarea></div>';html+='<div class="pd-section"><h4>Prompt Content</h4><textarea id="newPromptContent" style="width:100%;padding:8px;background:var(--bg-surface);border:1px solid var(--border);border-radius:6px;color:var(--text-primary);font-size:13px;height:120px" placeholder="The prompt text to copy"></textarea></div>';html+='<button class="pd-copy" onclick="submitNewPrompt()">Add to Library</button>';el.innerHTML=html;document.getElementById('promptDetailOverlay').classList.add('open')}
function submitNewPrompt(){var id=document.getElementById('newPromptId').value.trim();var name=document.getElementById('newPromptName').value.trim();var type=document.getElementById('newPromptType').value.trim();var color=document.getElementById('newPromptColor').value.trim();var useWhen=document.getElementById('newPromptUseWhen').value.trim();var content=document.getElementById('newPromptContent').value.trim();if(!id||!name){showToast('ID and Name are required');return}var p={id:id,seq:id.replace('P',''),name:name,type:type||'BUILD',color:color||'sky',category:'standard',class:'standard',sprintRole:'implementor',proofGate:'local validation',useWhen:useWhen||'Custom prompt',copyContent:content||'',keywords:[]};PROMPTS.push(p);closePromptDetail();render();showToast('Added '+id+' - commit docs/prompts.json to save')}
function promptSequenceValue(p){var raw=String((p&&p.seq)||((p&&p.id)||''));var n=parseInt(raw.replace(/\D/g,''),10);return isNaN(n)?Number.MAX_SAFE_INTEGER:n}
function sectionForPrompt(p){for(var i=0;i<SECTIONS.length;i++){if(SECTIONS[i].types.indexOf(p.type)!==-1)return SECTIONS[i]}return null}
function groupPromptsBySection(prompts){
  var groups=[],byName={};
  SECTIONS.forEach(function(section){var group={name:section.name,glow:section.glow,prompts:[]};groups.push(group);byName[section.name]=group});
  var other={name:'Other',glow:'#64748b',prompts:[]};
  prompts.forEach(function(p){var section=sectionForPrompt(p);if(section&&byName[section.name])byName[section.name].prompts.push(p);else other.prompts.push(p)});
  groups=groups.filter(function(group){return group.prompts.length>0});
  if(other.prompts.length)groups.push(other);
  groups.forEach(function(group){group.prompts.sort(function(a,b){var delta=promptSequenceValue(a)-promptSequenceValue(b);return delta||String(a.id).localeCompare(String(b.id))})});
  return groups
}
function renderSections(){var nav=document.getElementById('sectionsNav');nav.setAttribute('aria-label','Prompt categories');nav.innerHTML='<button class="section-tab'+(activeSection===null?' active':'')+'" data-section="__all__">All Categories</button>';SECTIONS.forEach(function(s){nav.innerHTML+='<button class="section-tab'+(activeSection===s.name?' active':'')+'" data-section="'+s.name+'">'+s.name+'</button>'})}
function renderTypes(){var nav=document.getElementById('typeNav');var types={};nav.setAttribute('aria-label','Prompt types');PROMPTS.forEach(function(p){if(!types[p.type])types[p.type]={count:0,color:p.color};types[p.type].count++});nav.innerHTML='<div class="type-chip'+(activeType===null?' active':'')+'" data-type="__all__">All Types</div>';Object.keys(types).sort().forEach(function(t){var hex=COLORS[types[t].color.toLowerCase()]||'#64748b';nav.innerHTML+='<div class="type-chip'+(activeType===t?' active':'')+'" data-type="'+t+'"><span class="dot" style="background:'+hex+'"></span>'+t+' ('+types[t].count+')</div>'})}
function clearSearch(){document.getElementById('search').value='';render()}

function appendSectionDivider(grid,group){
  var secGlow=group.glow||'#64748b';
  var icons={'Foundation':'⚒','Discover & Plan':'⚛','Build & Repair':'⚙','Validate & Protect':'✔','Integrate & Ship':'✈','Autonomy & Night Shift':'☾'};
  var divider=document.createElement('div');
  divider.className='section-divider';
  divider.setAttribute('data-category',group.name);
  divider.innerHTML='<a class="page-jump page-jump-top" href="#page-top" aria-label="Go to top of page">&#8593; Top</a><div class="sd-line" style="background:'+secGlow+'"></div><div class="sd-label" style="color:'+secGlow+'"><span class="sd-icon">'+(icons[group.name]||'◆')+'</span>'+group.name+'<span class="sd-count">'+group.prompts.length+' prompts</span></div><div class="sd-line" style="background:'+secGlow+'"></div><a class="page-jump page-jump-bottom" href="#page-bottom" aria-label="Go to bottom of page">Bottom &#8595;</a>';
  grid.appendChild(divider)
}
function appendPromptCard(grid,p){
  var hex=COLORS[p.color.toLowerCase()]||'#64748b';
  var isGnhf=p.category==='gnhf';
  var card=document.createElement('div');
  card.className='prompt-card'+(isGnhf?' gnhf':'');
  card.tabIndex=0;
  card.setAttribute('role','button');
  card.setAttribute('aria-label',p.id+' '+p.name+'. Click to copy. Double-click or press Enter to expand.');
  card.innerHTML='<div class="glow-bar" style="background:'+hex+'"></div><div class="prompt-header"><span class="prompt-id">'+p.id+'</span>'+(isGnhf?'<span class="gnhf-badge">☾ GNHF</span>':'')+'<span class="prompt-name">'+p.name+'</span></div><div class="prompt-type">'+p.type+' · '+p.color+'</div><div class="prompt-desc">'+p.useWhen+'</div><div class="prompt-meta"><span class="prompt-badge">'+p.sprintRole+'</span><span class="prompt-badge">'+p.proofGate+'</span></div>';
  card.onclick=function(e){cancelPromptCardCopy(card);card._copyTimer=setTimeout(function(){copyPrompt(p.id);card._copyTimer=null},300)};
  card.ondblclick=function(e){cancelPromptCardCopy(card);e.preventDefault();showPromptDetail(p.id,card)};
  card.onkeydown=function(e){if(e.target!==card)return;if(e.key==='Enter'){cancelPromptCardCopy(card);e.preventDefault();e.stopPropagation();showPromptDetail(p.id,card)}else if(e.key===' '){cancelPromptCardCopy(card);e.preventDefault();e.stopPropagation();copyPrompt(p.id)}};
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
  if(activeSection){var secTypes=[];for(var i=0;i<SECTIONS.length;i++){if(SECTIONS[i].name===activeSection){secTypes=SECTIONS[i].types;break}}f=f.filter(function(p){return secTypes.indexOf(p.type)!==-1})}
  if(activeType)f=f.filter(function(p){return p.type===activeType});
  if(activeColor)f=f.filter(function(p){return p.color&&p.color.toLowerCase()===activeColor.toLowerCase()});
  if(q){var synIds={};var qWords=q.split(/\s+/);Object.keys(SYNONYMS).forEach(function(key){if(q.indexOf(key)!==-1){SYNONYMS[key].split(' ').forEach(function(id){synIds[id.toUpperCase()]=1})}else if(qWords.length<=3&&key.split(' ').length<=3){var allMatch=qWords.every(function(w){var kw=key.split(/\s+/);return kw.some(function(k){return k.indexOf(w)!==-1||w.indexOf(k)!==-1})});if(allMatch)SYNONYMS[key].split(' ').forEach(function(id){synIds[id.toUpperCase()]=1})}});f=f.filter(function(p){if(synIds[p.id])return true;if(p.keywords){for(var ki=0;ki<p.keywords.length;ki++){if(p.keywords[ki].indexOf(q)!==-1)return true}}return p.id.toLowerCase().indexOf(q)!==-1||p.name.toLowerCase().indexOf(q)!==-1||p.type.toLowerCase().indexOf(q)!==-1||p.class.toLowerCase().indexOf(q)!==-1||p.useWhen.toLowerCase().indexOf(q)!==-1||p.sprintRole.toLowerCase().indexOf(q)!==-1||p.proofGate.toLowerCase().indexOf(q)!==-1||p.copyContent.toLowerCase().indexOf(q)!==-1})}
  var grid=document.getElementById('grid');
  var dv=document.getElementById('doctrineView');
  grid.innerHTML='';
  if(activeCat==='doctrine'){grid.style.display='none';dv.classList.add('active');renderDoctrineList();document.getElementById('showing').textContent=Object.keys(DOCTRINE).length;document.getElementById('total').textContent=PROMPTS.length;return}
  grid.style.display='grid';
  dv.classList.remove('active');
  var groups=groupPromptsBySection(f);
  groups.forEach(function(group){
    appendSectionDivider(grid,group);
    group.prompts.forEach(function(p){appendPromptCard(grid,p)})
  });
  document.getElementById('showing').textContent=f.length;
  document.getElementById('total').textContent=PROMPTS.length
}

function renderDoctrineList(){var el=document.getElementById('doctrineList');document.getElementById('doctrineDetail').classList.remove('active');el.style.display='grid';el.innerHTML='';Object.keys(DOCTRINE).forEach(function(key){var d=DOCTRINE[key];var card=document.createElement('div');card.className='doctrine-card';card.onclick=function(){document.getElementById('doctrineDetail').classList.add('active');el.style.display='none';var html='<h2 style="color:var(--accent);margin-bottom:0.25rem">'+d.title+'</h2><div style="color:var(--text-muted);margin-bottom:1.5rem">'+d.subtitle+'</div>';d.sections.forEach(function(s){html+='<div class="doctrine-section"><h4>'+s.heading+'</h4>';var lines=s.content.split('\n');var inTable=false;var tbl='';lines.forEach(function(line){if(line.match(/^\|.*\|$/)){if(!inTable){inTable=true;tbl='<table>'}if(line.match(/^\|[-\s|]+$/)){return}var cells=line.split('|').filter(function(c){return c.trim()!==''});var tag=tbl.indexOf('<th>')===-1?'th':'td';tbl+='<tr>'+cells.map(function(c){return '<'+tag+'>'+c.trim()+'</'+tag+'>'}).join('')+'</tr>'}else{if(inTable){tbl+='</table>';html+=tbl;inTable=false;tbl=''}html+='<p>'+line+'</p>'}});if(inTable){tbl+='</table>';html+=tbl}html+='<div style="margin-top:8px"><button class="pd-copy" onclick="copyToClipboard(this.closest(\'.doctrine-section\').querySelector(\'pre\').textContent);this.classList.add(\'copied\');this.textContent=\'Copied!\';setTimeout(function(){this.classList.remove(\'copied\');this.textContent=\'Copy Section\'}.bind(this),1500)">Copy Section</button></div>';html+='</div>'});document.getElementById('doctrineContent').innerHTML=html};card.innerHTML='<h3>'+d.title+'</h3><div class="subtitle">'+d.subtitle+'</div><div class="count">'+d.sections.length+' sections →</div>';el.appendChild(card)})}

document.getElementById('doctrineBack').onclick=function(){renderDoctrineList()};
document.getElementById('addPromptBtn').addEventListener('click',showAddPrompt);
document.getElementById('searchClear').addEventListener('click',clearSearch);
document.addEventListener('click',function(e){var ct=e.target.closest('.cat-tab');if(ct){activeCat=ct.dataset.cat;document.querySelectorAll('.cat-tab').forEach(function(b){b.classList.remove('active')});ct.classList.add('active');render();return}var st=e.target.closest('.section-tab');if(st){var sn=st.dataset.section;activeSection=sn==='__all__'?null:sn;document.querySelectorAll('.section-tab').forEach(function(b){b.classList.remove('active')});st.classList.add('active');render();return}var tc=e.target.closest('.type-chip');if(tc){var tn=tc.dataset.type;activeType=tn==='__all__'?null:tn;document.querySelectorAll('.type-chip').forEach(function(b){b.classList.remove('active')});tc.classList.add('active');render();return}});
document.getElementById('search').addEventListener('input',function(){var v=this.value;document.getElementById('searchClear').style.display=v?'block':'none';render()});
document.getElementById('refBtn').addEventListener('click',toggleRef);
document.getElementById('refOverlay').addEventListener('click',toggleRef);
document.getElementById('refClose').addEventListener('click',toggleRef);
document.getElementById('promptDetailOverlay').addEventListener('click',function(e){if(e.target!==this)return;closePromptDetail(false);focusPromptOrigin()});
document.addEventListener('keydown',function(e){if(e.target.tagName==='INPUT'||e.target.tagName==='TEXTAREA')return;switch(e.key){case'1':activeCat='all';break;case'2':activeCat='standard';break;case'3':activeCat='gnhf';break;case'4':activeCat='doctrine';break;case'r':case'R':toggleRef();return;case'/':e.preventDefault();document.getElementById('search').focus();return;case'Escape':if(document.getElementById('promptDetailOverlay').classList.contains('open')){closePromptDetail();return}if(document.getElementById('refSidebar').classList.contains('open')){toggleRef();return}if(document.getElementById('search').value){clearSearch();return}if(activeType){activeType=null;render();return}if(activeSection){activeSection=null;render();return}if(activeCat!=='all'){activeCat='all';render();return}return;default:return}document.querySelectorAll('.cat-tab').forEach(function(b){b.classList.remove('active');if(b.dataset.cat===activeCat)b.classList.add('active')});render()});

(function buildRef(){var el=document.getElementById('refContent');var html='';if(REF.gnhfWorkflow){html+='<div class="ref-section"><h3>GNHF Workflow</h3>';REF.gnhfWorkflow.forEach(function(w){var pid=w.prompt||'';html+='<div class="ref-item'+(pid?' data-prompt="'+pid+'"':'')+'"><span class="label">'+pid+'</span> '+(w.useCase||w.moment||'')+'</div>'});html+='</div>'}if(REF.nightShiftRunbook){html+='<div class="ref-section"><h3>Night Shift Runbook</h3>';REF.nightShiftRunbook.forEach(function(r){if(r.scenario==='Scenario')return;html+='<div class="ref-item"><span class="label">'+r.scenario+'</span> '+r.purpose+'</div>'});html+='</div>'}if(REF.variables){html+='<div class="ref-section"><h3>Variables</h3>';REF.variables.forEach(function(v){html+='<div class="ref-item"><span class="label">'+v.name+'</span> '+v.description+'</div>'});html+='</div>'}if(REF.promptSequence){html+='<div class="ref-section"><h3>Prompt Sequence</h3>';REF.promptSequence.forEach(function(s){html+='<div class="ref-item" data-prompt="'+s.promptId+'"><span class="label">'+s.seq+'</span> '+s.promptId+': '+s.useItFor+'</div>'});html+='</div>'}el.innerHTML=html;el.querySelectorAll('.ref-item[data-prompt]').forEach(function(item){item.addEventListener('click',function(){var pid=item.getAttribute('data-prompt');if(!pid)return;closeRef();setTimeout(function(){showPromptDetail(pid)},300)})})})();

ensurePageNavigation();
renderSections();
renderTypes();
render();

