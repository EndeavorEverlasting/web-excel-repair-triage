(function(root,factory){
'use strict';
var api=factory();
if(typeof module!=='undefined'&&module.exports)module.exports=api;
if(root){
  root.PromptKitComputeMode=api;
  if(root.document)api.install(root);
}
})(typeof window!=='undefined'?window:null,function(){
'use strict';

var SCHEMA='prompt-kit-compute-mode/v1';
var PRODUCT_DEFAULT='exhaustive';
var VALID_PROFILES=Object.freeze({exhaustive:true,efficient:true});
var STORAGE_KEYS=Object.freeze({
  userDefault:'promptKit.computeMode.userDefault.v1',
  promptOverrides:'promptKit.computeMode.promptOverrides.v1'
});
var PROFILE_PRECEDENCE=Object.freeze([
  'explicit_run_override',
  'prompt_override',
  'user_default',
  'product_default'
]);

var sessionRunOverride=null;
var boundStorage=null;

function ComputeModeError(code,message){
  this.name='PromptKitComputeModeError';
  this.code=code;
  this.message=message;
  if(Error.captureStackTrace)Error.captureStackTrace(this,ComputeModeError)
}
ComputeModeError.prototype=Object.create(Error.prototype);
ComputeModeError.prototype.constructor=ComputeModeError;

function hasStorage(storage){
  return !!(storage&&typeof storage.getItem==='function'&&typeof storage.setItem==='function')
}
function normalizeProfile(value,label){
  var profile=String(value==null?'':value).trim().toLowerCase();
  if(!VALID_PROFILES[profile])throw new ComputeModeError('INVALID_PROFILE',(label||'profile')+' must be exhaustive or efficient');
  return profile
}
function readUserDefault(storage){
  storage=storage||boundStorage;
  if(!hasStorage(storage))return PRODUCT_DEFAULT;
  try{
    var raw=storage.getItem(STORAGE_KEYS.userDefault);
    if(!raw)return PRODUCT_DEFAULT;
    return normalizeProfile(raw,'user default')
  }catch(error){
    return PRODUCT_DEFAULT
  }
}
function writeUserDefault(storage,profile){
  storage=storage||boundStorage;
  var normalized=normalizeProfile(profile,'user default');
  if(!hasStorage(storage))throw new ComputeModeError('STORAGE_UNAVAILABLE','localStorage unavailable');
  storage.setItem(STORAGE_KEYS.userDefault,normalized);
  return normalized
}
function readPromptOverrides(storage){
  storage=storage||boundStorage;
  if(!hasStorage(storage))return{};
  try{
    var raw=storage.getItem(STORAGE_KEYS.promptOverrides);
    var parsed=raw?JSON.parse(raw):{};
    if(!parsed||typeof parsed!=='object'||Array.isArray(parsed))return{};
    var out={};
    Object.keys(parsed).forEach(function(key){
      var id=String(key||'').trim().toUpperCase();
      if(!id)return;
      try{out[id]=normalizeProfile(parsed[key],'prompt override')}catch(e){}
    });
    return out
  }catch(error){
    return{}
  }
}
function writePromptOverrides(storage,map){
  storage=storage||boundStorage;
  if(!hasStorage(storage))throw new ComputeModeError('STORAGE_UNAVAILABLE','localStorage unavailable');
  var clean={};
  Object.keys(map||{}).forEach(function(key){
    var id=String(key||'').trim().toUpperCase();
    if(!id)return;
    clean[id]=normalizeProfile(map[key],'prompt override')
  });
  storage.setItem(STORAGE_KEYS.promptOverrides,JSON.stringify(clean));
  return clean
}
function getPromptOverride(promptId,storage){
  var id=String(promptId||'').trim().toUpperCase();
  if(!id)return null;
  return readPromptOverrides(storage)[id]||null
}
function setPromptOverride(promptId,profile,storage){
  storage=storage||boundStorage;
  var map=readPromptOverrides(storage);
  var id=String(promptId||'').trim().toUpperCase();
  if(!id)throw new ComputeModeError('INVALID_PROMPT_ID','prompt id required');
  if(profile==null||profile==='')delete map[id];
  else map[id]=normalizeProfile(profile,'prompt override');
  writePromptOverrides(storage,map);
  return getPromptOverride(id,storage)
}
function setRunOverride(profile){
  sessionRunOverride=profile==null||profile===''?null:normalizeProfile(profile,'run override');
  return sessionRunOverride
}
function clearRunOverride(){sessionRunOverride=null;return null}
function getRunOverride(){return sessionRunOverride}

function resolveProfile(options){
  options=options||{};
  var productDefault=normalizeProfile(options.productDefault!=null?options.productDefault:PRODUCT_DEFAULT,'product default');
  var candidates={
    explicit_run_override:options.runOverride!=null&&String(options.runOverride).trim()?String(options.runOverride).trim().toLowerCase():null,
    prompt_override:options.promptOverride!=null&&String(options.promptOverride).trim()?String(options.promptOverride).trim().toLowerCase():null,
    user_default:options.userDefault!=null&&String(options.userDefault).trim()?String(options.userDefault).trim().toLowerCase():null,
    product_default:productDefault
  };
  var chosenSource='product_default';
  var chosenName=productDefault;
  for(var i=0;i<PROFILE_PRECEDENCE.length;i++){
    var source=PROFILE_PRECEDENCE[i];
    var value=candidates[source];
    if(typeof value==='string'&&value){
      chosenSource=source;
      chosenName=normalizeProfile(value,source);
      break
    }
  }
  return{
    schema:SCHEMA,
    profile:chosenName,
    resolvedFrom:chosenSource,
    resolved_from:chosenSource,
    precedence:PROFILE_PRECEDENCE.slice()
  }
}

function resolveCopyContent(prompt,options){
  options=options||{};
  var storage=options.storage||boundStorage;
  var promptId=String(prompt&&prompt.id||options.promptId||'').trim().toUpperCase();
  var overrides=options.promptOverrides||readPromptOverrides(storage);
  var userDefault=options.userDefault!=null?options.userDefault:readUserDefault(storage);
  var runOverride=options.runOverride!==undefined?options.runOverride:sessionRunOverride;
  var promptOverride=options.promptOverride!==undefined?options.promptOverride:(promptId?overrides[promptId]:null);
  var resolved=resolveProfile({
    promptId:promptId,
    runOverride:runOverride,
    promptOverride:promptOverride,
    userDefault:userDefault,
    productDefault:options.productDefault!=null?options.productDefault:PRODUCT_DEFAULT
  });
  var compiled=prompt&&prompt.compiledEffectivePrompts;
  if(compiled&&typeof compiled==='object'&&!Array.isArray(compiled)){
    var text=compiled[resolved.profile];
    if(typeof text==='string'&&text.trim())return text
  }
  if(prompt&&prompt.copyContent!=null){
    var canonical=String(prompt.copyContent);
    if(canonical.trim())return canonical
  }
  return ''
}

function ensureStyles(doc){
  if(!doc||doc.getElementById('promptComputeModeStyles'))return;
  var style=doc.createElement('style');
  style.id='promptComputeModeStyles';
  style.textContent=[
    '.prompt-compute-mode{display:inline-flex;align-items:center;gap:6px;margin-left:8px}',
    '.prompt-compute-mode-label{font-size:11px;font-weight:700;letter-spacing:.04em;text-transform:uppercase;color:var(--text-muted)}',
    '.prompt-compute-mode-toggle{display:inline-flex;border:1px solid var(--border);border-radius:8px;overflow:hidden;background:var(--bg-surface)}',
    '.prompt-compute-mode-toggle button{appearance:none;border:0;background:transparent;color:var(--text-secondary);font-size:11px;font-weight:700;padding:6px 10px;cursor:pointer;min-height:32px}',
    '.prompt-compute-mode-toggle button.active{background:var(--accent-glow);color:var(--text-primary)}',
    '.prompt-compute-mode-toggle button:focus-visible{outline:2px solid var(--accent);outline-offset:-2px}',
    '.prompt-compute-mode-detail{display:flex;align-items:center;gap:8px;flex-wrap:wrap;margin:0 0 14px;padding:8px;border:1px solid var(--border);border-radius:8px;background:var(--bg-surface);color:var(--text-secondary);font-size:10px}',
    '.prompt-compute-mode-source{color:var(--text-muted);font-family:ui-monospace,SFMono-Regular,Consolas,monospace}'
  ].join('');
  doc.head.appendChild(style)
}

function syncToggle(doc,profile){
  var node=doc.getElementById('promptComputeMode');
  if(!node)return;
  node.querySelectorAll('button[data-compute-mode]').forEach(function(button){
    var active=button.getAttribute('data-compute-mode')===profile;
    button.classList.toggle('active',active);
    button.setAttribute('aria-pressed',active?'true':'false')
  })
}

function refreshDetail(doc,storage,promptId){
  if(!doc)return;
  var detail=doc.getElementById('promptDetail');
  if(!detail||String(detail.getAttribute('data-prompt-id')||'').toUpperCase()!==String(promptId||'').toUpperCase())return;
  var resolution=resolveProfile({
    runOverride:sessionRunOverride,
    promptOverride:getPromptOverride(promptId,storage),
    userDefault:readUserDefault(storage),
    productDefault:PRODUCT_DEFAULT
  });
  var wrap=detail.querySelector('.prompt-compute-mode-detail');
  if(!wrap){
    wrap=doc.createElement('div');
    wrap.className='prompt-compute-mode-detail';
    wrap.setAttribute('data-prompt-detail-no-copy','');
    var badges=detail.querySelector('.pd-badges');
    if(badges&&badges.parentNode)badges.parentNode.insertBefore(wrap,badges.nextSibling);
    else detail.insertBefore(wrap,detail.firstChild)
  }
  wrap.innerHTML='';
  var label=doc.createElement('label');
  label.appendChild(doc.createTextNode('This prompt '));
  var select=doc.createElement('select');
  select.id='promptComputeOverride';
  select.setAttribute('aria-label','Compute mode override for '+promptId);
  var inherited=doc.createElement('option');
  inherited.value='';
  inherited.textContent='Inherit · '+readUserDefault(storage);
  select.appendChild(inherited);
  [['exhaustive','Exhaustive'],['efficient','Efficient']].forEach(function(item){
    var option=doc.createElement('option');
    option.value=item[0];
    option.textContent=item[1];
    select.appendChild(option)
  });
  select.value=getPromptOverride(promptId,storage)||'';
  select.addEventListener('change',function(){
    setPromptOverride(promptId,select.value||null,storage);
    refreshDetail(doc,storage,promptId)
  });
  label.appendChild(select);
  wrap.appendChild(label);
  var source=doc.createElement('span');
  source.className='prompt-compute-mode-source';
  source.textContent='effective '+resolution.profile+' · '+resolution.resolved_from;
  wrap.appendChild(source)
}

function install(root){
  if(!root||!root.document)return null;
  if(root.__promptKitComputeModeController)return root.__promptKitComputeModeController;
  var doc=root.document;
  var storage=null;
  try{storage=root.localStorage}catch(error){storage=null}
  boundStorage=storage;

  function currentUserDefault(){return readUserDefault(storage)}
  function setUserDefault(profile){
    var normalized=writeUserDefault(storage,profile);
    syncToggle(doc,normalized);
    var openId=doc.getElementById('promptDetail');
    if(openId&&openId.getAttribute('data-prompt-id'))refreshDetail(doc,storage,openId.getAttribute('data-prompt-id'));
    if(typeof root.showToast==='function')root.showToast('Compute Mode: '+normalized);
    return normalized
  }

  function ensureUi(){
    if(doc.getElementById('promptComputeMode'))return;
    ensureStyles(doc);
    var controls=doc.querySelector&&doc.querySelector('.header-controls');
    var storageBtn=doc.getElementById('promptStorageLifecycleBtn');
    var parent=controls||(storageBtn&&storageBtn.parentElement)||doc.body;
    if(!parent)return;
    var wrap=doc.createElement('div');
    wrap.id='promptComputeMode';
    wrap.className='prompt-compute-mode';
    wrap.setAttribute('role','group');
    wrap.setAttribute('aria-label','Compute Mode');
    wrap.setAttribute('data-ui-format-role','execution-profile-control');
    wrap.innerHTML='<span class="prompt-compute-mode-label">Compute</span><div class="prompt-compute-mode-toggle">'+
      '<button type="button" data-compute-mode="exhaustive" aria-pressed="false">Exhaustive</button>'+
      '<button type="button" data-compute-mode="efficient" aria-pressed="false">Efficient</button></div>';
    if(storageBtn&&storageBtn.parentNode===parent)parent.insertBefore(wrap,storageBtn);
    else parent.appendChild(wrap);
    wrap.querySelectorAll('button[data-compute-mode]').forEach(function(button){
      button.addEventListener('click',function(){
        setUserDefault(button.getAttribute('data-compute-mode'))
      })
    });
    syncToggle(doc,currentUserDefault())
  }

  function bindDetailOpen(){
    var baseOpen=root.canonicalOpenPrompt||root.showPromptDetail;
    if(typeof baseOpen!=='function'||baseOpen.__promptKitComputeModeWrapped)return;
    var wrapped=function(id){
      var result=baseOpen.apply(root,arguments);
      try{refreshDetail(doc,storage,id)}catch(error){}
      return result
    };
    wrapped.__promptKitComputeModeWrapped=true;
    if(typeof root.canonicalOpenPrompt==='function')root.canonicalOpenPrompt=wrapped;
    else if(typeof root.showPromptDetail==='function')root.showPromptDetail=wrapped
  }

  function mount(){
    ensureUi();
    bindDetailOpen()
  }
  if(doc.readyState==='loading')doc.addEventListener('DOMContentLoaded',mount);
  else mount();

  var controller={
    SCHEMA:SCHEMA,
    PRODUCT_DEFAULT:PRODUCT_DEFAULT,
    STORAGE_KEYS:STORAGE_KEYS,
    PROFILE_PRECEDENCE:PROFILE_PRECEDENCE,
    ComputeModeError:ComputeModeError,
    resolveProfile:resolveProfile,
    resolveCopyContent:function(prompt,options){
      return resolveCopyContent(prompt,Object.assign({storage:storage},options||{}))
    },
    getUserDefault:currentUserDefault,
    setUserDefault:setUserDefault,
    getPromptOverrides:function(){return readPromptOverrides(storage)},
    getPromptOverride:function(promptId){return getPromptOverride(promptId,storage)},
    setPromptOverride:function(promptId,profile){return setPromptOverride(promptId,profile,storage)},
    setRunOverride:setRunOverride,
    clearRunOverride:clearRunOverride,
    getRunOverride:getRunOverride,
    installUi:ensureUi,
    refreshDetail:function(promptId){return refreshDetail(doc,storage,promptId)}
  };
  root.__promptKitComputeModeController=controller;
  api.getUserDefault=controller.getUserDefault;
  api.setUserDefault=controller.setUserDefault;
  api.getPromptOverrides=controller.getPromptOverrides;
  api.getPromptOverride=controller.getPromptOverride;
  api.setPromptOverride=controller.setPromptOverride;
  api.getController=function(){return controller};
  return controller
}

var api={
  SCHEMA:SCHEMA,
  PRODUCT_DEFAULT:PRODUCT_DEFAULT,
  STORAGE_KEYS:STORAGE_KEYS,
  PROFILE_PRECEDENCE:PROFILE_PRECEDENCE,
  PREFERENCE_PRECEDENCE:PROFILE_PRECEDENCE,
  ComputeModeError:ComputeModeError,
  normalizeProfile:normalizeProfile,
  resolveProfile:resolveProfile,
  resolveCopyContent:resolveCopyContent,
  getUserDefault:function(){return readUserDefault(boundStorage)},
  setUserDefault:function(profile){return writeUserDefault(boundStorage,profile)},
  getPromptOverrides:function(){return readPromptOverrides(boundStorage)},
  getPromptOverride:function(promptId){return getPromptOverride(promptId,boundStorage)},
  setPromptOverride:function(promptId,profile){return setPromptOverride(promptId,profile,boundStorage)},
  setRunOverride:setRunOverride,
  clearRunOverride:clearRunOverride,
  getRunOverride:getRunOverride,
  install:install
};

return api
});
