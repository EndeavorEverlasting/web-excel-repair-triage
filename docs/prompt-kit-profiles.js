(function(root,factory){
'use strict';
var api=factory();
if(typeof module!=='undefined'&&module.exports)module.exports=api;
if(root){
  root.PromptKitProfiles=api;
  if(root.document)api.install(root);
}
})(typeof window!=='undefined'?window:null,function(){
'use strict';

var IMPORT_SCHEMA='prompt-kit-profile-import/v1';
var SLOT_SCHEMA='prompt-kit-profile-slots/v1';
var STORAGE_KEYS={
  slots:'promptKit.profileSlots.v1',
  active:'promptKit.activeProfileSlot.v1',
  imports:'promptKit.profilePacks.v1'
};
var LIMITS=Object.freeze({
  importBytes:32768,
  packsPerImport:32,
  installedImportedPacks:64,
  ruleNodesPerPack:64,
  ruleDepth:4,
  stringLength:120,
  packIdLength:40,
  packLabelLength:64,
  packsPerSlot:12,
  slotNameLength:32,
  ruleListLength:16
});
var SLOT_KEYS=['A','B','C','D','E'];
var MODES=['all','standard','favorites','doctrine','packs'];

function ProfileError(code,message){
  this.name='PromptKitProfileError';
  this.code=code;
  this.message=message;
  if(Error.captureStackTrace)Error.captureStackTrace(this,ProfileError)
}
ProfileError.prototype=Object.create(Error.prototype);
ProfileError.prototype.constructor=ProfileError;

function clone(value){return JSON.parse(JSON.stringify(value))}
function isObject(value){return !!value&&typeof value==='object'&&!Array.isArray(value)}
function byteLength(value){
  var text=String(value==null?'':value);
  if(typeof TextEncoder!=='undefined')return new TextEncoder().encode(text).length;
  try{return unescape(encodeURIComponent(text)).length}catch(e){return text.length}
}
function boundedString(value,label,max){
  if(typeof value!=='string')throw new ProfileError('INVALID_STRING',label+' must be a string');
  var text=value.trim();
  if(!text)throw new ProfileError('EMPTY_STRING',label+' must not be empty');
  if(text.length>max)throw new ProfileError('STRING_TOO_LONG',label+' exceeds '+max+' characters');
  return text
}
function normalizePackId(value){
  var id=boundedString(value,'pack id',LIMITS.packIdLength).toUpperCase().replace(/[\s-]+/g,'_');
  if(!/^[A-Z][A-Z0-9_]{0,39}$/.test(id))throw new ProfileError('INVALID_PACK_ID','pack id must use A-Z, 0-9, and underscores');
  return id
}
function promptText(prompt){
  var keys=['id','name','type','class','sprintRole','progress','useWhen','inspectFirst','expectedOutput','nextStep','proofGate','color','category','keywords','profile'];
  return keys.map(function(key){
    var value=prompt&&prompt[key];
    if(Array.isArray(value))return value.join(' ');
    if(value==null)return '';
    return String(value)
  }).join(' ').toLowerCase()
}

function validateRule(rule,state,depth){
  state=state||{nodes:0};
  depth=depth||0;
  if(depth>LIMITS.ruleDepth)throw new ProfileError('RULE_DEPTH','profile rule nesting exceeds '+LIMITS.ruleDepth);
  if(!isObject(rule))throw new ProfileError('INVALID_RULE','profile rule must be an object');
  state.nodes+=1;
  if(state.nodes>LIMITS.ruleNodesPerPack)throw new ProfileError('RULE_NODES','profile rule exceeds '+LIMITS.ruleNodesPerPack+' nodes');
  var op=boundedString(rule.op,'rule op',24);
  if(op==='all')return{op:'all'};
  if(op==='id'){
    var promptId=boundedString(rule.value,'prompt id',16).toUpperCase();
    if(!/^P\d+$/.test(promptId))throw new ProfileError('INVALID_PROMPT_ID','id rule must target a P-number prompt');
    return{op:'id',value:promptId}
  }
  if(op==='category'||op==='type'||op==='keyword'||op==='text'){
    return{op:op,value:boundedString(rule.value,op+' value',LIMITS.stringLength).toLowerCase()}
  }
  if(op==='not'){
    return{op:'not',rule:validateRule(rule.rule,state,depth+1)}
  }
  if(op==='any'||op==='every'){
    if(!Array.isArray(rule.rules)||!rule.rules.length)throw new ProfileError('INVALID_RULE_LIST',op+' requires a non-empty rules array');
    if(rule.rules.length>LIMITS.ruleListLength)throw new ProfileError('RULE_LIST_TOO_LONG',op+' exceeds '+LIMITS.ruleListLength+' child rules');
    return{op:op,rules:rule.rules.map(function(child){return validateRule(child,state,depth+1)})}
  }
  throw new ProfileError('UNKNOWN_RULE_OP','unsupported profile rule op: '+op)
}

function compileNormalizedRule(rule){
  if(rule.op==='all')return function(){return true};
  if(rule.op==='id')return function(prompt){return String(prompt&&prompt.id||'').toUpperCase()===rule.value};
  if(rule.op==='category')return function(prompt){return String(prompt&&prompt.category||'').toLowerCase()===rule.value};
  if(rule.op==='type')return function(prompt){return String(prompt&&prompt.type||'').toLowerCase()===rule.value};
  if(rule.op==='keyword'||rule.op==='text')return function(prompt){return promptText(prompt).indexOf(rule.value)!==-1};
  if(rule.op==='not'){
    var inner=compileNormalizedRule(rule.rule);
    return function(prompt){return !inner(prompt)}
  }
  if(rule.op==='any'){
    var anyRules=rule.rules.map(compileNormalizedRule);
    return function(prompt){return anyRules.some(function(test){return test(prompt)})}
  }
  if(rule.op==='every'){
    var everyRules=rule.rules.map(compileNormalizedRule);
    return function(prompt){return everyRules.every(function(test){return test(prompt)})}
  }
  throw new ProfileError('UNKNOWN_RULE_OP','unsupported normalized profile rule op: '+rule.op)
}
function compileRule(rule){
  var normalized=validateRule(rule,{nodes:0},0);
  return compileNormalizedRule(normalized)
}
function anyKeywords(values){
  return{op:'any',rules:values.map(function(value){return{op:'keyword',value:value}})}
}

var PREDEFINED_PACKS={
  TRIAGE:{id:'TRIAGE',label:'TRIAGE',rule:anyKeywords(['triage','repair','diagnose','diagnostic','recovery'])},
  FUN:{id:'FUN',label:'FUN',rule:anyKeywords(['fun','creative','game','play','brainstorm'])},
  PM:{id:'PM',label:'PM',rule:anyKeywords(['project manager','project management','stakeholder','sprint','planning','coordination'])},
  CYBERSEC:{id:'CYBERSEC',label:'CYBERSEC',rule:anyKeywords(['cyber','security','threat','vulnerability','hardening'])},
  AGENTIC_LOOPING:{id:'AGENTIC_LOOPING',label:'AGENTIC LOOPING',rule:anyKeywords(['agentic','autonomy','night shift','loop','iteration'])},
  SAS:{id:'SAS',label:'SAS',rule:anyKeywords(['sysadminsuite','sysadmin suite','network probe','powershell','windows administration',' sas '])},
  GARDENING:{id:'GARDENING',label:'Gardening',rule:anyKeywords(['garden','gardening','greenhouse','plant','watering'])},
  H_AND_H:{id:'H_AND_H',label:'H&H',rule:anyKeywords(['h&h','health and hospital','health & hospital','hospital'])},
  FUTURE_PROJECTS:{id:'FUTURE_PROJECTS',label:'Future Projects',rule:anyKeywords(['future project','roadmap','backlog'])},
  GNHF:{id:'GNHF',label:'GNHF',rule:{op:'category',value:'gnhf'}}
};
Object.keys(PREDEFINED_PACKS).forEach(function(id){
  PREDEFINED_PACKS[id].rule=validateRule(PREDEFINED_PACKS[id].rule,{nodes:0},0)
});

var DEFAULT_SLOTS=[
  {key:'A',name:'All',mode:'all',packIds:[]},
  {key:'B',name:'Standard',mode:'standard',packIds:[]},
  {key:'C',name:'Favorites',mode:'favorites',packIds:[]},
  {key:'D',name:'SAS',mode:'packs',packIds:['SAS']},
  {key:'E',name:'PM',mode:'packs',packIds:['PM','FUN','TRIAGE','H_AND_H']}
];

function normalizePackRecord(pack){
  if(!isObject(pack))throw new ProfileError('INVALID_PACK','profile pack must be an object');
  var id=normalizePackId(pack.id);
  var label=boundedString(pack.label||pack.id,'pack label',LIMITS.packLabelLength);
  var rule=validateRule(pack.rule,{nodes:0},0);
  return{id:id,label:label,rule:rule}
}
function validateImport(raw,existingCount){
  if(typeof raw!=='string')throw new ProfileError('IMPORT_TYPE','profile import must be JSON text');
  if(byteLength(raw)>LIMITS.importBytes)throw new ProfileError('IMPORT_TOO_LARGE','profile import exceeds '+LIMITS.importBytes+' bytes');
  var payload;
  try{payload=JSON.parse(raw)}catch(e){throw new ProfileError('IMPORT_JSON','profile import is not valid JSON')}
  if(!isObject(payload)||payload.schema!==IMPORT_SCHEMA)throw new ProfileError('IMPORT_SCHEMA','profile import schema must be '+IMPORT_SCHEMA);
  if(!Array.isArray(payload.packs)||!payload.packs.length)throw new ProfileError('IMPORT_PACKS','profile import must contain at least one pack');
  if(payload.packs.length>LIMITS.packsPerImport)throw new ProfileError('IMPORT_PACK_COUNT','profile import exceeds '+LIMITS.packsPerImport+' packs');
  var seen={};
  var packs=payload.packs.map(function(pack){
    var normalized=normalizePackRecord(pack);
    if(PREDEFINED_PACKS[normalized.id])throw new ProfileError('RESERVED_PACK_ID',normalized.id+' is a predefined pack id');
    if(seen[normalized.id])throw new ProfileError('DUPLICATE_PACK_ID','duplicate imported pack id '+normalized.id);
    seen[normalized.id]=true;
    return normalized
  });
  var installed=Math.max(0,Number(existingCount)||0);
  if(installed+packs.length>LIMITS.installedImportedPacks)throw new ProfileError('INSTALLED_PACK_LIMIT','installed imports would exceed '+LIMITS.installedImportedPacks+' packs');
  return{schema:IMPORT_SCHEMA,packs:packs}
}
function packMap(importedPacks){
  var map={};
  Object.keys(PREDEFINED_PACKS).forEach(function(id){map[id]=PREDEFINED_PACKS[id]});
  (importedPacks||[]).forEach(function(pack){map[pack.id]=pack});
  return map
}
function normalizeSlot(slot,index,available){
  if(!isObject(slot))throw new ProfileError('INVALID_SLOT','slot '+SLOT_KEYS[index]+' must be an object');
  var key=SLOT_KEYS[index];
  var name=boundedString(slot.name||key,'slot '+key+' name',LIMITS.slotNameLength);
  var mode=String(slot.mode||'packs').toLowerCase();
  if(MODES.indexOf(mode)===-1)throw new ProfileError('INVALID_SLOT_MODE','slot '+key+' has unsupported mode '+mode);
  var ids=Array.isArray(slot.packIds)?slot.packIds:[];
  if(ids.length>LIMITS.packsPerSlot)throw new ProfileError('SLOT_PACK_LIMIT','slot '+key+' exceeds '+LIMITS.packsPerSlot+' packs');
  var normalizedIds=[];
  var seen={};
  ids.forEach(function(value){
    var id=normalizePackId(value);
    if(!available[id])throw new ProfileError('UNKNOWN_PACK','slot '+key+' references unknown pack '+id);
    if(!seen[id]){seen[id]=true;normalizedIds.push(id)}
  });
  if(mode==='packs'&&!normalizedIds.length)throw new ProfileError('EMPTY_PACK_SLOT','custom slot '+key+' must select at least one pack');
  return{key:key,name:name,mode:mode,packIds:normalizedIds}
}
function normalizeSlots(slots,available){
  if(!Array.isArray(slots)||slots.length!==5)throw new ProfileError('SLOT_COUNT','exactly five profile tabs are required');
  return slots.map(function(slot,index){return normalizeSlot(slot,index,available)})
}
function defaultSlots(){return clone(DEFAULT_SLOTS)}

function install(root){
  if(root.__promptKitProfilesInstalled)return root.PromptKitProfiles;
  root.__promptKitProfilesInstalled=true;
  var doc=root.document;
  var storage=null;
  try{storage=root.localStorage}catch(e){storage=null}
  var imported=[];
  var slots=defaultSlots();
  var activeKey='A';
  var compiled={};

  function toast(message,tone){
    if(typeof root.showToast==='function')root.showToast(message,tone);
  }
  function readJson(key,fallback){
    try{
      if(!storage)return fallback;
      var raw=storage.getItem(key);
      return raw?JSON.parse(raw):fallback
    }catch(e){return fallback}
  }
  function writeJson(key,value){
    if(!storage)throw new ProfileError('STORAGE_UNAVAILABLE','localStorage unavailable');
    storage.setItem(key,JSON.stringify(value))
  }
  function loadImported(){
    var payload=readJson(STORAGE_KEYS.imports,{schema:IMPORT_SCHEMA,packs:[]});
    if(!payload||payload.schema!==IMPORT_SCHEMA||!Array.isArray(payload.packs))return[];
    var safe=[];
    payload.packs.slice(0,LIMITS.installedImportedPacks).forEach(function(pack){
      try{
        var normalized=normalizePackRecord(pack);
        if(!PREDEFINED_PACKS[normalized.id])safe.push(normalized)
      }catch(e){}
    });
    return safe
  }
  function availablePacks(){return packMap(imported)}
  function rebuildCompiled(){
    compiled={};
    var available=availablePacks();
    Object.keys(available).forEach(function(id){compiled[id]=compileNormalizedRule(available[id].rule)})
  }
  function loadSlots(){
    var available=availablePacks();
    var payload=readJson(STORAGE_KEYS.slots,null);
    if(!payload||payload.schema!==SLOT_SCHEMA||!Array.isArray(payload.slots))return defaultSlots();
    try{return normalizeSlots(payload.slots,available)}catch(e){return defaultSlots()}
  }
  function saveSlots(candidate){
    var normalized=normalizeSlots(candidate,availablePacks());
    writeJson(STORAGE_KEYS.slots,{schema:SLOT_SCHEMA,slots:normalized});
    slots=normalized;
    return slots
  }
  function loadActive(){
    try{
      if(!storage)return'A';
      var key=String(storage.getItem(STORAGE_KEYS.active)||'A').toUpperCase();
      return SLOT_KEYS.indexOf(key)!==-1?key:'A'
    }catch(e){return'A'}
  }
  function persistActive(key){
    if(storage)storage.setItem(STORAGE_KEYS.active,key)
  }
  function currentSlot(){
    return slots[SLOT_KEYS.indexOf(activeKey)]||slots[0]
  }
  function matchesSlot(prompt,slot){
    if(!slot||slot.mode!=='packs')return true;
    return slot.packIds.some(function(id){var test=compiled[id];return !!(test&&test(prompt))})
  }
  function projectCall(fn,args){
    var slot=currentSlot();
    if(slot.mode!=='packs'||typeof fn!=='function')return fn&&fn.apply(root,args||[]);
    var original=root.PROMPTS;
    if(!Array.isArray(original))return fn.apply(root,args||[]);
    root.PROMPTS=original.filter(function(prompt){return matchesSlot(prompt,slot)});
    try{return fn.apply(root,args||[])}
    finally{root.PROMPTS=original}
  }

  imported=loadImported();
  rebuildCompiled();
  slots=loadSlots();
  activeKey=loadActive();

  var baseRender=root.render;
  var baseRenderTypes=root.renderTypes;
  var baseRenderSections=root.renderSections;
  if(typeof baseRender==='function')root.render=function(){return projectCall(baseRender,arguments)};
  if(typeof baseRenderTypes==='function')root.renderTypes=function(){return projectCall(baseRenderTypes,arguments)};
  if(typeof baseRenderSections==='function')root.renderSections=function(){return projectCall(baseRenderSections,arguments)};
  var baseResetPromptKitView=root.resetPromptKitView;
  if(typeof baseResetPromptKitView==='function')root.resetPromptKitView=function(){
    activeKey='A';
    try{persistActive('A')}catch(e){}
    var result=baseResetPromptKitView.apply(root,arguments);
    refreshHeader();
    updateEditor();
    return result
  };

  function clearTransientBrowserFilters(){
    if(typeof root.activeType!=='undefined')root.activeType=null;
    if(typeof root.activeColor!=='undefined')root.activeColor=null;
    if(typeof root.collapsedSections!=='undefined')root.collapsedSections={};
    var search=doc.getElementById('search');
    if(search)search.value='';
    var clear=doc.getElementById('searchClear');
    if(clear)clear.style.display='none'
  }
  function setBuiltinView(slot){
    clearTransientBrowserFilters();
    if(slot.mode==='all'){
      root.activeCat='all';
      root.activeSection=null
    }else if(slot.mode==='standard'){
      root.activeCat='standard';
      root.activeSection=null
    }else if(slot.mode==='favorites'){
      root.activeCat='all';
      root.activeSection='__favorites__'
    }else if(slot.mode==='doctrine'){
      root.activeCat='doctrine';
      root.activeSection=null
    }else{
      root.activeCat='all';
      root.activeSection=null
    }
  }
  function refreshHeader(){
    var host=doc.querySelector('.cat-tabs');
    if(!host)return;
    host.innerHTML='';
    slots.forEach(function(slot){
      var button=doc.createElement('button');
      button.className='cat-tab profile-slot'+(slot.key===activeKey?' active':'');
      button.type='button';
      button.dataset.profileSlot=slot.key;
      if(slot.key==='A')button.dataset.cat='all';
      if(slot.key==='B')button.dataset.cat='standard';
      if(slot.key==='C'){button.id='favoritesShortcut';button.dataset.view='favorites'}
      button.setAttribute('aria-keyshortcuts',slot.key);
      button.setAttribute('aria-pressed',slot.key===activeKey?'true':'false');
      button.setAttribute('title',slot.name+' ('+slot.key+')');
      button.innerHTML='<span class="profile-slot-label"></span><span class="kbd">'+slot.key+'</span>';
      button.querySelector('.profile-slot-label').textContent=slot.name;
      host.appendChild(button)
    })
  }
  function renderAll(){
    if(typeof root.renderSections==='function')root.renderSections();
    if(typeof root.renderTypes==='function')root.renderTypes();
    if(typeof root.render==='function')root.render()
  }
  function activateSlot(key,quiet){
    key=String(key||'').toUpperCase();
    if(SLOT_KEYS.indexOf(key)===-1)return false;
    activeKey=key;
    try{persistActive(key)}catch(e){}
    var slot=currentSlot();
    setBuiltinView(slot);
    refreshHeader();
    renderAll();
    updateEditor();
    if(!quiet)toast(slot.name+' active','success');
    return true
  }
  function configureSlots(candidate){
    saveSlots(candidate);
    setBuiltinView(currentSlot());
    refreshHeader();
    renderAll();
    updateEditor();
    toast('Profile tabs saved','success');
    return clone(slots)
  }
  function importPackSet(raw){
    var validated=validateImport(raw,imported.length);
    var existing={};
    imported.forEach(function(pack){existing[pack.id]=true});
    validated.packs.forEach(function(pack){
      if(existing[pack.id])throw new ProfileError('DUPLICATE_INSTALLED_PACK','pack '+pack.id+' is already installed')
    });
    var candidate=imported.concat(validated.packs);
    writeJson(STORAGE_KEYS.imports,{schema:IMPORT_SCHEMA,packs:candidate});
    imported=candidate;
    rebuildCompiled();
    updateEditor();
    toast('Imported '+validated.packs.length+' profile pack'+(validated.packs.length===1?'':'s'),'success');
    return clone(validated)
  }

  function ensureStyles(){
    if(doc.getElementById('prompt-kit-profile-styles'))return;
    var style=doc.createElement('style');
    style.id='prompt-kit-profile-styles';
    style.textContent='.cat-tabs .profile-slot{gap:7px}.profile-slot-label{max-width:150px;overflow:hidden;text-overflow:ellipsis;white-space:nowrap}.prompt-profile-editor{margin-top:12px;padding-top:10px;border-top:1px solid var(--border);display:grid;gap:9px}.prompt-profile-editor h4{margin:0;color:var(--text-primary);font-size:11px}.prompt-profile-editor-note,.prompt-profile-status{font-size:10px;line-height:1.45;color:var(--text-muted)}.prompt-profile-slot-row{display:grid;grid-template-columns:24px minmax(80px,1fr) minmax(100px,1fr);gap:6px;align-items:start}.prompt-profile-slot-key{display:flex;align-items:center;justify-content:center;min-height:34px;border:1px solid var(--border);border-radius:6px;color:var(--accent);font:700 11px ui-monospace,SFMono-Regular,Consolas,monospace}.prompt-profile-slot-row input,.prompt-profile-slot-row select,.prompt-profile-import textarea,.prompt-profile-editor button{width:100%;box-sizing:border-box;min-height:34px;border:1px solid var(--border);border-radius:6px;background:var(--bg-surface);color:var(--text-primary);font:inherit;font-size:10px}.prompt-profile-slot-row input,.prompt-profile-slot-row select{padding:5px 7px}.prompt-profile-pack-select{grid-column:2/4;min-height:82px!important}.prompt-profile-editor-actions{display:flex;gap:6px}.prompt-profile-editor button{width:auto;padding:6px 9px;cursor:pointer}.prompt-profile-import{display:grid;gap:6px;padding-top:8px;border-top:1px solid var(--border)}.prompt-profile-import textarea{min-height:86px;padding:7px;resize:vertical;font-family:ui-monospace,SFMono-Regular,Consolas,monospace}.prompt-profile-status.error{color:#fca5a5}.prompt-profile-status.success{color:#86efac}@media(max-width:760px){.prompt-profile-slot-row{grid-template-columns:28px minmax(0,1fr)}.prompt-profile-slot-row select{grid-column:2}.prompt-profile-pack-select{grid-column:2}.profile-slot-label{max-width:110px}}';
    doc.head.appendChild(style)
  }
  function helpPanel(){
    return doc.getElementById('hotkeyHelpPanel')
  }
  function updateHotkeyHelp(){
    var panel=helpPanel();
    if(!panel)return;
    var list=panel.querySelector('.hotkey-help-list');
    if(!list)return;
    var extras=[
      ['`','Show / hide Hotkeys'],
      ['/','Focus search'],
      ['R','Reference panel'],
      ['F','Show / hide filters'],
      ['[','Hide filters'],
      [']','Show filters'],
      ['Home','Scroll to top'],
      ['End','Scroll to bottom'],
      ['Esc','Close / clear active surface']
    ];
    list.innerHTML='';
    slots.forEach(function(slot){
      var key=doc.createElement('kbd');key.textContent=slot.key;
      var label=doc.createElement('span');label.textContent=slot.name;
      list.appendChild(key);list.appendChild(label)
    });
    extras.forEach(function(item){
      var key=doc.createElement('kbd');key.textContent=item[0];
      var label=doc.createElement('span');label.textContent=item[1];
      list.appendChild(key);list.appendChild(label)
    })
  }
  function editorHost(){
    var panel=helpPanel();
    if(!panel)return null;
    var existing=panel.querySelector('.prompt-profile-editor');
    if(existing)return existing;
    var editor=doc.createElement('section');
    editor.className='prompt-profile-editor';
    editor.setAttribute('aria-label','Profile tab configuration');
    editor.innerHTML='<h4>Profile tabs A–E</h4><div class="prompt-profile-editor-note">Rename any tab. All, Standard, Favorites, and Doctrine are built-in views; Custom composes one or more safe profile packs.</div><div class="prompt-profile-slot-list"></div><div class="prompt-profile-editor-actions"><button type="button" data-profile-save>Save tabs</button><button type="button" data-profile-reset>Reset defaults</button></div><div class="prompt-profile-import"><strong>Import profile packs</strong><span class="prompt-profile-editor-note">JSON only. Max 32 KB, 32 packs/import, 64 installed packs, 64 rule nodes/pack, depth 4. Imported data is validated and compiled without eval.</span><textarea data-profile-import-text placeholder=\'{"schema":"prompt-kit-profile-import/v1","packs":[{"id":"MY_PACK","label":"My Pack","rule":{"op":"keyword","value":"example"}}]}\'></textarea><button type="button" data-profile-import>Import validated pack set</button></div><div class="prompt-profile-status" role="status" aria-live="polite"></div>';
    panel.appendChild(editor);
    editor.querySelector('[data-profile-save]').addEventListener('click',function(){
      try{
        var rows=Array.prototype.slice.call(editor.querySelectorAll('.prompt-profile-slot-row'));
        var candidate=rows.map(function(row){
          var selected=Array.prototype.slice.call(row.querySelector('.prompt-profile-pack-select').selectedOptions||[]).map(function(option){return option.value});
          return{key:row.dataset.key,name:row.querySelector('[data-slot-name]').value,mode:row.querySelector('[data-slot-mode]').value,packIds:selected}
        });
        configureSlots(candidate);
        setStatus('Saved five profile tabs.','success')
      }catch(e){setStatus(e.message||String(e),'error')}
    });
    editor.querySelector('[data-profile-reset]').addEventListener('click',function(){
      try{slots=normalizeSlots(defaultSlots(),availablePacks());writeJson(STORAGE_KEYS.slots,{schema:SLOT_SCHEMA,slots:slots});activeKey='A';persistActive('A');refreshHeader();renderAll();updateEditor();setStatus('Restored default All / Standard / Favorites / SAS / PM tabs.','success')}catch(e){setStatus(e.message||String(e),'error')}
    });
    editor.querySelector('[data-profile-import]').addEventListener('click',function(){
      var raw=editor.querySelector('[data-profile-import-text]').value;
      try{var result=importPackSet(raw);editor.querySelector('[data-profile-import-text]').value='';setStatus('Imported '+result.packs.length+' validated pack(s).','success')}catch(e){setStatus((e.code?e.code+': ':'')+(e.message||String(e)),'error')}
    });
    return editor
  }
  function setStatus(message,tone){
    var editor=editorHost();if(!editor)return;
    var status=editor.querySelector('.prompt-profile-status');if(!status)return;
    status.className='prompt-profile-status '+(tone||'');status.textContent=message
  }
  function updateEditor(){
    var editor=editorHost();
    if(!editor)return;
    var list=editor.querySelector('.prompt-profile-slot-list');
    if(!list)return;
    var available=availablePacks();
    var packIds=Object.keys(available).sort(function(a,b){return available[a].label.localeCompare(available[b].label)});
    list.innerHTML='';
    slots.forEach(function(slot){
      var row=doc.createElement('div');row.className='prompt-profile-slot-row';row.dataset.key=slot.key;
      var key=doc.createElement('span');key.className='prompt-profile-slot-key';key.textContent=slot.key;
      var name=doc.createElement('input');name.type='text';name.value=slot.name;name.maxLength=LIMITS.slotNameLength;name.dataset.slotName='';name.setAttribute('aria-label','Tab '+slot.key+' name');
      var mode=doc.createElement('select');mode.dataset.slotMode='';mode.setAttribute('aria-label','Tab '+slot.key+' mode');
      [['all','All prompts'],['standard','Standard prompts'],['favorites','Favorites'],['doctrine','Doctrine'],['packs','Custom profile packs']].forEach(function(item){var option=doc.createElement('option');option.value=item[0];option.textContent=item[1];option.selected=slot.mode===item[0];mode.appendChild(option)});
      var packs=doc.createElement('select');packs.multiple=true;packs.className='prompt-profile-pack-select';packs.setAttribute('aria-label','Tab '+slot.key+' profile packs');
      packIds.forEach(function(id){var option=doc.createElement('option');option.value=id;option.textContent=available[id].label+' · '+id;option.selected=slot.packIds.indexOf(id)!==-1;packs.appendChild(option)});
      row.appendChild(key);row.appendChild(name);row.appendChild(mode);row.appendChild(packs);list.appendChild(row)
    });
    updateHotkeyHelp()
  }
  function installEditorWhenReady(){
    if(helpPanel()){updateEditor();return}
    if(typeof root.MutationObserver==='function'){
      var observer=new root.MutationObserver(function(){if(helpPanel()){observer.disconnect();updateEditor()}});
      observer.observe(doc.body,{childList:true,subtree:true})
    }else root.setTimeout(updateEditor,0)
  }

  ensureStyles();
  refreshHeader();
  doc.addEventListener('click',function(event){
    var target=event.target;
    if(!target||typeof target.closest!=='function')return;
    var button=target.closest('.profile-slot[data-profile-slot]');
    if(!button)return;
    event.preventDefault();event.stopImmediatePropagation();
    activateSlot(button.dataset.profileSlot)
  },true);
  // A-E keydown ownership lives in prompt-kit-polish.js so prompt-ID sequences settle before profile navigation.
  installEditorWhenReady();
  activateSlot(activeKey,true);

  var browserApi={
    limits:LIMITS,
    predefinedPacks:clone(PREDEFINED_PACKS),
    defaultSlots:defaultSlots,
    getState:function(){return{activeKey:activeKey,slots:clone(slots),importedPacks:clone(imported)}},
    activateSlot:activateSlot,
    configureSlots:configureSlots,
    importPackSet:importPackSet,
    refreshHeader:refreshHeader
  };
  Object.keys(browserApi).forEach(function(key){api[key]=browserApi[key]});
  return api
}

var api={
  IMPORT_SCHEMA:IMPORT_SCHEMA,
  SLOT_SCHEMA:SLOT_SCHEMA,
  STORAGE_KEYS:clone(STORAGE_KEYS),
  LIMITS:LIMITS,
  SLOT_KEYS:SLOT_KEYS.slice(),
  MODES:MODES.slice(),
  PREDEFINED_PACKS:clone(PREDEFINED_PACKS),
  DEFAULT_SLOTS:defaultSlots(),
  ProfileError:ProfileError,
  byteLength:byteLength,
  validateRule:validateRule,
  compileRule:compileRule,
  normalizePackRecord:normalizePackRecord,
  validateImport:validateImport,
  packMap:packMap,
  normalizeSlots:normalizeSlots,
  defaultSlots:defaultSlots,
  install:install
};
return api
});
