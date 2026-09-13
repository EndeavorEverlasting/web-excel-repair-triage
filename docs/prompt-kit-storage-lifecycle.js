(function(root,factory){
'use strict';
var api=factory();
if(typeof module!=='undefined'&&module.exports)module.exports=api;
if(root){
  root.PromptKitStorageLifecycle=api;
  if(root.document)api.install(root);
}
})(typeof window!=='undefined'?window:null,function(){
'use strict';

var SCHEMA='prompt-kit-storage-lifecycle/v1';
var DAY_MS=24*60*60*1000;
var DELETE_CONFIRMATION='DELETE PERSONAL STATE';
var EXTERNAL_USAGE_KEY='promptKit.usage.v1';
var PERSONAL_STATE_KEYS=Object.freeze([
  'promptKit.favoritePromptIds.v1',
  'promptKit.profileSlots.v1',
  'promptKit.activeProfileSlot.v1',
  'promptKit.profilePacks.v1',
  'promptKit.favoritePromptIds',
  'promptKit.favorites'
]);
var POLICIES=Object.freeze({
  local_journal:Object.freeze({key:'promptKit.localJournal.v1',maxAgeMs:14*DAY_MS,maxBytes:2097152,maxItems:null}),
  privacy_reducer_buffer:Object.freeze({key:'promptKit.privacyReducerBuffer.v1',maxAgeMs:30*DAY_MS,maxBytes:524288,maxItems:2048,uniqueIds:true}),
  sync_retry_queue:Object.freeze({key:'promptKit.syncRetryQueue.v1',maxAgeMs:7*DAY_MS,maxBytes:262144,maxItems:64}),
  polling_state:Object.freeze({key:'promptKit.pollingState.v1',maxAgeMs:DAY_MS,maxBytes:null,maxItems:1,replaceOnWrite:true})
});

function byteLength(value){
  var text=String(value==null?'':value);
  if(typeof TextEncoder!=='undefined')return new TextEncoder().encode(text).length;
  if(typeof Buffer!=='undefined')return Buffer.byteLength(text,'utf8');
  try{return unescape(encodeURIComponent(text)).length}catch(error){return text.length}
}
function clone(value){return JSON.parse(JSON.stringify(value))}
function nowMs(value){if(value==null||value==='')return Date.now();var parsed=Number(value);return Number.isFinite(parsed)&&parsed>=0?Math.floor(parsed):Date.now()}
function emptyEnvelope(name){return{schema:SCHEMA,store:name,items:[]}}
function hasStorage(storage){return !!(storage&&typeof storage.getItem==='function'&&typeof storage.setItem==='function'&&typeof storage.removeItem==='function')}
function safeRemove(storage,key){try{storage.removeItem(key);return true}catch(error){return false}}
function normalizedItem(item,now){
  if(!item||typeof item!=='object')return null;
  var at=Number(item.at);
  if(!Number.isFinite(at)||at<0)return null;
  var normalized={at:Math.min(Math.floor(at),now),value:item.value};
  if(typeof item.id==='string'&&item.id.trim())normalized.id=item.id.trim();
  return normalized
}
function dedupeLatestById(items){
  var latest=Object.create(null);
  var passthrough=[];
  items.forEach(function(item){
    if(!item.id){passthrough.push(item);return}
    var current=latest[item.id];
    if(!current||item.at>=current.at)latest[item.id]=item
  });
  return passthrough.concat(Object.keys(latest).map(function(id){return latest[id]}))
}
function serializedEnvelope(name,items){return JSON.stringify({schema:SCHEMA,store:name,items:items})}
function trimEnvelope(name,envelope,at){
  var policy=POLICIES[name];
  if(!policy)throw new Error('Unknown Prompt Kit lifecycle store: '+name);
  var now=nowMs(at);
  var cutoff=now-policy.maxAgeMs;
  var items=Array.isArray(envelope&&envelope.items)?envelope.items.map(function(item){return normalizedItem(item,now)}).filter(Boolean):[];
  items=items.filter(function(item){return item.at>=cutoff});
  if(policy.uniqueIds)items=dedupeLatestById(items);
  items.sort(function(a,b){return a.at-b.at});
  if(policy.maxItems!=null&&items.length>policy.maxItems)items=items.slice(items.length-policy.maxItems);
  if(policy.maxBytes!=null){
    while(items.length&&byteLength(serializedEnvelope(name,items))>policy.maxBytes)items.shift();
  }
  return{schema:SCHEMA,store:name,items:items}
}
function readDisposable(storage,name,at){
  if(!hasStorage(storage))return emptyEnvelope(name);
  var policy=POLICIES[name];
  if(!policy)throw new Error('Unknown Prompt Kit lifecycle store: '+name);
  var raw;
  try{raw=storage.getItem(policy.key)}catch(error){return emptyEnvelope(name)}
  if(!raw)return emptyEnvelope(name);
  try{
    var parsed=JSON.parse(raw);
    if(!parsed||parsed.schema!==SCHEMA||parsed.store!==name||!Array.isArray(parsed.items))throw new Error('invalid envelope');
    return trimEnvelope(name,parsed,at)
  }catch(error){
    safeRemove(storage,policy.key);
    return emptyEnvelope(name)
  }
}

function create(storage,host){
  var blocked=false;
  var lastFailure=null;
  host=host||{};

  function status(){return{writesBlocked:blocked,lastFailure:lastFailure}}
  function block(reason,name){blocked=true;lastFailure={reason:reason,store:name||null,at:Date.now()};return{ok:false,reason:reason,store:name||null}}
  function unblock(){blocked=false;lastFailure=null}
  function persist(name,envelope){
    if(!hasStorage(storage))return block('storage-unavailable',name);
    var policy=POLICIES[name];
    var text=serializedEnvelope(name,envelope.items);
    if(policy.maxBytes!=null&&byteLength(text)>policy.maxBytes)return block('store-byte-limit',name);
    try{storage.setItem(policy.key,text);return{ok:true,store:name,count:envelope.items.length}}
    catch(error){return block('storage-pressure',name)}
  }
  function cleanupStore(name,at){
    if(!hasStorage(storage))return block('storage-unavailable',name);
    var policy=POLICIES[name];
    var before;
    try{before=storage.getItem(policy.key)}catch(error){return block('storage-read-failed',name)}
    var cleaned=readDisposable(storage,name,at);
    var after=serializedEnvelope(name,cleaned.items);
    if(before==null)return{ok:true,store:name,count:0,changed:false};
    if(before===after)return{ok:true,store:name,count:cleaned.items.length,changed:false};
    var result=persist(name,cleaned);
    result.changed=result.ok;
    return result
  }
  function cleanupAll(at){
    var results={};
    Object.keys(POLICIES).forEach(function(name){results[name]=cleanupStore(name,at)});
    return{ok:Object.keys(results).every(function(name){return results[name].ok}),stores:results,status:status()}
  }
  function append(name,value,options){
    options=options||{};
    if(blocked)return{ok:false,reason:'writes-blocked',store:name};
    var policy=POLICIES[name];
    if(!policy)throw new Error('Unknown Prompt Kit lifecycle store: '+name);
    var at=nowMs(options.at);
    var existing=readDisposable(storage,name,at);
    var item={at:at,value:value};
    if(options.id!=null)item.id=String(options.id).trim();
    if(policy.uniqueIds&&!item.id)return{ok:false,reason:'aggregate-id-required',store:name};
    var items=policy.replaceOnWrite?[item]:existing.items.concat([item]);
    var candidate=trimEnvelope(name,{items:items},at);
    if(!candidate.items.length)return{ok:false,reason:'item-exceeds-store-bounds',store:name};
    return persist(name,candidate)
  }
  function clearKeys(keys){
    if(!hasStorage(storage))return{ok:false,reason:'storage-unavailable'};
    var ok=true;
    keys.forEach(function(key){if(!safeRemove(storage,key))ok=false});
    if(ok)unblock();
    return{ok:ok}
  }
  function clearUsageAndJournal(){return clearKeys([EXTERNAL_USAGE_KEY,POLICIES.local_journal.key])}
  function clearCollectiveBuffer(){return clearKeys([POLICIES.privacy_reducer_buffer.key])}
  function clearSyncState(){return clearKeys([POLICIES.sync_retry_queue.key,POLICIES.polling_state.key])}
  function clearAllDisposable(){
    var keys=Object.keys(POLICIES).map(function(name){return POLICIES[name].key});
    keys.push(EXTERNAL_USAGE_KEY);
    return clearKeys(keys)
  }
  function clearPersonalState(confirmation){
    if(confirmation!==DELETE_CONFIRMATION)return{ok:false,reason:'confirmation-required'};
    return clearKeys(PERSONAL_STATE_KEYS.slice())
  }
  function inspect(name,at){return clone(readDisposable(storage,name,at))}
  function storageKey(name){if(!POLICIES[name])throw new Error('Unknown Prompt Kit lifecycle store: '+name);return POLICIES[name].key}

  function toast(message){if(typeof host.showToast==='function')host.showToast(message)}
  function ensureControls(){
    var doc=host.document;
    if(!doc||typeof doc.createElement!=='function'||doc.getElementById('promptStorageLifecycleBtn'))return;
    var controls=doc.querySelector&&doc.querySelector('.header-controls');
    if(!controls)return;
    var button=doc.createElement('button');
    button.type='button';button.id='promptStorageLifecycleBtn';button.className='btn';button.textContent='Storage';
    button.setAttribute('aria-controls','promptStorageLifecycleDialog');button.setAttribute('aria-haspopup','dialog');
    var dialog=doc.createElement('div');
    dialog.id='promptStorageLifecycleDialog';dialog.hidden=true;dialog.setAttribute('role','dialog');dialog.setAttribute('aria-modal','true');dialog.setAttribute('aria-label','Prompt Kit storage controls');
    dialog.innerHTML='<div class="modal-content"><h2>Storage controls</h2><p>Temporary Prompt Kit data clears independently from saved Favorites and profiles.</p><div class="modal-actions"><button type="button" data-clear-usage>Clear temporary usage</button><button type="button" data-clear-collective>Clear collective buffer</button><button type="button" data-clear-sync>Clear sync queue</button><button type="button" data-clear-personal>Delete personal settings</button><button type="button" data-close-storage>Close</button></div></div>';
    function bind(selector,fn,message){var node=dialog.querySelector(selector);if(node)node.addEventListener('click',function(){var result=fn();toast(result.ok?message:'Storage action could not complete')})}
    bind('[data-clear-usage]',clearUsageAndJournal,'Temporary usage cleared');
    bind('[data-clear-collective]',clearCollectiveBuffer,'Collective buffer cleared');
    bind('[data-clear-sync]',clearSyncState,'Sync queue cleared');
    var personal=dialog.querySelector('[data-clear-personal]');
    if(personal)personal.addEventListener('click',function(){
      var confirmation=typeof host.prompt==='function'?host.prompt('Type DELETE PERSONAL STATE to remove saved Prompt Kit Favorites and profile settings.') : null;
      var result=clearPersonalState(confirmation);
      toast(result.ok?'Personal settings deleted':'Personal settings were not deleted')
    });
    function closeDialog(){dialog.hidden=true;if(typeof button.focus==='function')button.focus()}
    var close=dialog.querySelector('[data-close-storage]');if(close)close.addEventListener('click',closeDialog);
    dialog.addEventListener('keydown',function(event){if(event.key==='Escape'){event.stopPropagation();closeDialog()}});
    button.addEventListener('click',function(){
      dialog.hidden=false;
      var first=dialog.querySelector('button');
      if(first&&typeof first.focus==='function')first.focus()
    });
    controls.appendChild(button);doc.body.appendChild(dialog)
  }

  return{
    schema_version:SCHEMA,
    policies:POLICIES,
    personal_state_keys:PERSONAL_STATE_KEYS,
    external_usage_key:EXTERNAL_USAGE_KEY,
    cleanupStore:cleanupStore,
    cleanupAll:cleanupAll,
    append:append,
    inspect:inspect,
    storageKey:storageKey,
    clearUsageAndJournal:clearUsageAndJournal,
    clearCollectiveBuffer:clearCollectiveBuffer,
    clearSyncState:clearSyncState,
    clearAllDisposable:clearAllDisposable,
    clearPersonalState:clearPersonalState,
    status:status,
    ensureControls:ensureControls
  }
}

function install(root){
  if(root.__promptKitStorageLifecycleController)return root.__promptKitStorageLifecycleController;
  var storage=null;
  try{storage=root.localStorage}catch(error){storage=null}
  var controller=create(storage,root);
  root.__promptKitStorageLifecycleController=controller;
  controller.cleanupAll(Date.now());
  controller.ensureControls();
  return controller
}

return{
  SCHEMA:SCHEMA,
  POLICIES:POLICIES,
  PERSONAL_STATE_KEYS:PERSONAL_STATE_KEYS,
  EXTERNAL_USAGE_KEY:EXTERNAL_USAGE_KEY,
  DELETE_CONFIRMATION:DELETE_CONFIRMATION,
  create:create,
  install:install,
  byteLength:byteLength,
  trimEnvelope:trimEnvelope
}
});
