(function(root){
'use strict';

var PORTABLE_FAVORITES_SCHEMA='prompt-kit-favorites/v1';
var PORTABLE_FAVORITES_MAX_BYTES=65536;
var PORTABLE_FAVORITES_LEGACY_KEYS=['promptKit.favoritePromptIds','promptKit.favorites'];

function normalizePromptId(value){
  var id=String(value==null?'':value).trim().toUpperCase();
  if(!/^[A-Z][A-Z0-9._:-]{0,63}$/.test(id))throw new Error('Invalid prompt id in favorites payload: '+id);
  return id
}

function normalizeFavoritePromptIds(values){
  if(!Array.isArray(values))throw new Error('favorite_prompt_ids must be an array');
  var seen={};
  var ids=[];
  values.forEach(function(value){
    var id=normalizePromptId(value);
    if(!seen[id]){seen[id]=true;ids.push(id)}
  });
  ids.sort();
  return ids
}

function currentFavoritePromptIds(){
  var source=root.favoritePromptIds||{};
  return Object.keys(source).filter(function(id){return source[id]===true}).map(normalizePromptId).sort()
}

function promptKitVersion(){
  if(typeof document==='undefined')return 'unknown';
  var badge=document.getElementById('versionBadge');
  return badge&&badge.textContent?badge.textContent.trim():'unknown'
}

function buildPortableFavoritesPayload(){
  return{
    schema_version:PORTABLE_FAVORITES_SCHEMA,
    exported_at:new Date().toISOString(),
    source:{application:'AI Harness Prompt Kit',version:promptKitVersion()},
    favorite_prompt_ids:currentFavoritePromptIds()
  }
}

function parsePortableFavoritesPayload(text){
  var source=String(text==null?'':text);
  if(new TextEncoder().encode(source).length>PORTABLE_FAVORITES_MAX_BYTES)throw new Error('Favorites file exceeds 64 KiB limit');
  var parsed=JSON.parse(source);
  if(Array.isArray(parsed))return{schema_version:'legacy-array/v0',favorite_prompt_ids:normalizeFavoritePromptIds(parsed)};
  if(!parsed||typeof parsed!=='object')throw new Error('Favorites payload must be an object or legacy array');
  if(parsed.schema_version!==PORTABLE_FAVORITES_SCHEMA)throw new Error('Unsupported favorites schema: '+String(parsed.schema_version||'missing'));
  return{schema_version:parsed.schema_version,favorite_prompt_ids:normalizeFavoritePromptIds(parsed.favorite_prompt_ids)}
}

function knownPromptIds(){
  var known={};
  (root.PROMPTS||[]).forEach(function(prompt){if(prompt&&prompt.id)known[normalizePromptId(prompt.id)]=true});
  return known
}

function mergePortableFavorites(ids){
  var known=knownPromptIds();
  var unknown=[];
  root.favoritePromptIds=root.favoritePromptIds||{};
  normalizeFavoritePromptIds(ids).forEach(function(id){root.favoritePromptIds[id]=true;if(!known[id])unknown.push(id)});
  if(typeof root.saveFavoritePromptIds==='function')root.saveFavoritePromptIds();
  if(typeof root.render==='function')root.render();
  return{saved:currentFavoritePromptIds().length,unknown_prompt_ids:unknown}
}

function migrateLegacyFavoriteStorage(){
  if(!root.localStorage)return 0;
  var current=currentFavoritePromptIds();
  if(current.length)return 0;
  var migrated=[];
  PORTABLE_FAVORITES_LEGACY_KEYS.some(function(key){
    var raw=root.localStorage.getItem(key);
    if(!raw)return false;
    try{var parsed=JSON.parse(raw);if(Array.isArray(parsed)){migrated=normalizeFavoritePromptIds(parsed);return migrated.length>0}}catch(error){}
    return false
  });
  if(!migrated.length)return 0;
  mergePortableFavorites(migrated);
  return migrated.length
}

function safeDateStamp(){return new Date().toISOString().slice(0,10)}

function exportPortableFavorites(){
  var payload=buildPortableFavoritesPayload();
  var text=JSON.stringify(payload,null,2)+'\n';
  var blob=new Blob([text],{type:'application/json'});
  var url=URL.createObjectURL(blob);
  var anchor=document.createElement('a');
  anchor.href=url;
  anchor.download='prompt-kit-favorites-'+safeDateStamp()+'.json';
  document.body.appendChild(anchor);
  anchor.click();
  document.body.removeChild(anchor);
  setTimeout(function(){URL.revokeObjectURL(url)},0);
  if(typeof root.showToast==='function')root.showToast('Exported '+payload.favorite_prompt_ids.length+' Favorites')
}

function importPortableFavoritesFile(file){
  if(!file)return;
  if(file.size>PORTABLE_FAVORITES_MAX_BYTES){if(typeof root.showToast==='function')root.showToast('Favorites file is larger than 64 KiB');return}
  var reader=new FileReader();
  reader.onload=function(){
    try{
      var payload=parsePortableFavoritesPayload(reader.result);
      var result=mergePortableFavorites(payload.favorite_prompt_ids);
      var message='Imported '+payload.favorite_prompt_ids.length+' Favorites';
      if(result.unknown_prompt_ids.length)message+=' ('+result.unknown_prompt_ids.length+' unavailable in this version)';
      if(typeof root.showToast==='function')root.showToast(message)
    }catch(error){if(typeof root.showToast==='function')root.showToast('Favorites import failed: '+error.message)}
  };
  reader.onerror=function(){if(typeof root.showToast==='function')root.showToast('Favorites import failed: file could not be read')};
  reader.readAsText(file)
}

function ensureFavoritesPortabilitySupport(){
  if(typeof document==='undefined'||document.getElementById('favoritePortabilityControls'))return;
  var addPrompt=document.getElementById('addPromptBtn');
  if(!addPrompt||!addPrompt.parentNode)return;
  var style=document.createElement('style');
  style.id='prompt-kit-favorites-portability-styles';
  style.textContent='.favorite-portability-controls{display:inline-flex;gap:6px;align-items:center}.favorite-portability-btn{min-height:32px;padding:6px 10px;border:1px solid var(--border);border-radius:var(--radius);background:var(--bg-surface);color:var(--text-secondary);font-size:11px;font-weight:600;cursor:pointer}.favorite-portability-btn:hover,.favorite-portability-btn:focus-visible{outline:none;border-color:#f59e0b;color:#fbbf24;box-shadow:0 0 0 2px rgba(245,158,11,.18)}@media(max-width:760px),(hover:none),(pointer:coarse){.favorite-portability-controls{grid-column:1/-1;display:grid;grid-template-columns:1fr 1fr;width:100%}.favorite-portability-btn{min-height:42px}}';
  document.head.appendChild(style);
  var controls=document.createElement('div');
  controls.id='favoritePortabilityControls';
  controls.className='favorite-portability-controls';
  controls.setAttribute('aria-label','Favorites backup and restore');
  var exportButton=document.createElement('button');
  exportButton.type='button';
  exportButton.id='exportFavoritesBtn';
  exportButton.className='favorite-portability-btn';
  exportButton.textContent='Export Favorites';
  exportButton.setAttribute('aria-label','Export Favorites to a portable JSON backup');
  exportButton.addEventListener('click',exportPortableFavorites);
  var importButton=document.createElement('button');
  importButton.type='button';
  importButton.id='importFavoritesBtn';
  importButton.className='favorite-portability-btn';
  importButton.textContent='Import Favorites';
  importButton.setAttribute('aria-label','Import and merge Favorites from a portable JSON backup');
  var input=document.createElement('input');
  input.type='file';
  input.id='favoritesImportInput';
  input.accept='.json,application/json';
  input.hidden=true;
  importButton.addEventListener('click',function(){input.value='';input.click()});
  input.addEventListener('change',function(){importPortableFavoritesFile(input.files&&input.files[0])});
  controls.appendChild(exportButton);
  controls.appendChild(importButton);
  controls.appendChild(input);
  addPrompt.parentNode.insertBefore(controls,addPrompt);
  var migrated=migrateLegacyFavoriteStorage();
  if(migrated&&typeof root.showToast==='function')root.showToast('Migrated '+migrated+' legacy Favorites')
}

root.PromptKitFavoritesPortability={
  schema_version:PORTABLE_FAVORITES_SCHEMA,
  max_bytes:PORTABLE_FAVORITES_MAX_BYTES,
  normalizeFavoritePromptIds:normalizeFavoritePromptIds,
  buildPayload:buildPortableFavoritesPayload,
  parsePayload:parsePortableFavoritesPayload,
  mergeFavorites:mergePortableFavorites,
  migrateLegacyStorage:migrateLegacyFavoriteStorage,
  initialize:ensureFavoritesPortabilitySupport
};

ensureFavoritesPortabilitySupport()
})(typeof globalThis!=='undefined'?globalThis:this);
