(function(){
'use strict';
var copyToastTimer=null;

function ensurePromptKitPolishStyles(){
  if(document.getElementById('prompt-kit-polish-styles'))return;
  var style=document.createElement('style');
  style.id='prompt-kit-polish-styles';
  style.textContent='.prompt-card .prompt-header{padding-right:176px;min-height:34px}.prompt-card-actions{position:absolute;top:12px;right:12px;display:flex;align-items:center;justify-content:flex-end;gap:6px;z-index:3;max-width:168px}.prompt-card-actions .prompt-favorite-btn,.prompt-card-actions .prompt-open-btn,.prompt-card-actions .prompt-copy-btn{position:static!important;top:auto!important;right:auto!important;margin:0!important;opacity:1!important;display:inline-flex;align-items:center;justify-content:center;min-height:30px;box-sizing:border-box}.prompt-card-actions .prompt-favorite-btn{width:30px;min-width:30px}.prompt-card-actions .prompt-open-btn,.prompt-card-actions .prompt-copy-btn{padding:4px 8px;white-space:nowrap}.prompt-card.copy-confirmed{animation:prompt-copy-confirm 800ms ease-out}.prompt-card.copy-confirmed .glow-bar{background:var(--success)!important;box-shadow:0 0 12px rgba(34,197,94,.9),0 0 28px rgba(34,197,94,.45)!important}.toast.success{border-color:var(--success);background:linear-gradient(135deg,rgba(20,83,45,.96),rgba(17,24,39,.98));color:#dcfce7;box-shadow:0 0 0 1px rgba(34,197,94,.2),0 0 24px rgba(34,197,94,.42),0 10px 34px rgba(0,0,0,.42)}.toast.success.show{animation:prompt-toast-success 1.7s ease both}@keyframes prompt-copy-confirm{0%{border-color:var(--success);box-shadow:0 0 0 1px rgba(34,197,94,.7),0 0 30px rgba(34,197,94,.42);transform:translateY(-1px) scale(1.006)}45%{border-color:rgba(34,197,94,.78);box-shadow:0 0 22px rgba(34,197,94,.3)}100%{border-color:var(--border);box-shadow:none;transform:none}}@keyframes prompt-toast-success{0%{opacity:0;transform:translate(-50%,12px) scale(.96)}12%{opacity:1;transform:translate(-50%,0) scale(1.03)}24%,82%{opacity:1;transform:translate(-50%,0) scale(1)}100%{opacity:0;transform:translate(-50%,-4px) scale(.99)}}@media(max-width:760px){.prompt-card .prompt-header{padding-right:0;min-height:0}.prompt-card-actions{position:static;max-width:none;width:100%;display:grid;grid-template-columns:44px minmax(72px,1fr) minmax(72px,1fr);gap:8px;margin-top:12px}.prompt-card-actions .prompt-favorite-btn,.prompt-card-actions .prompt-open-btn,.prompt-card-actions .prompt-copy-btn{width:100%;min-height:42px;margin:0!important}}@media(prefers-reduced-motion:reduce){.prompt-card.copy-confirmed,.toast.success.show{animation:none}.toast.success.show{opacity:1}}';
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
render();
})();
