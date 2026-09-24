(function(){
'use strict';
var PROFILE='spec-architecture';
var ACCENT='#06b6d4';

function ensureSpecArchitectureStyles(){
  if(document.getElementById('prompt-kit-spec-architecture-styles'))return;
  var style=document.createElement('style');
  style.id='prompt-kit-spec-architecture-styles';
  style.textContent=''
    +'.prompt-card.spec-architecture{background:linear-gradient(145deg,#0d1e2a 0%,#102535 48%,#171a31 100%);border-color:rgba(6,182,212,.38);box-shadow:inset 0 0 34px rgba(6,182,212,.04)}'
    +'.prompt-card.spec-architecture:hover{border-color:#06b6d4;box-shadow:0 8px 32px rgba(0,0,0,.42),0 0 27px rgba(6,182,212,.22),inset 0 0 34px rgba(139,92,246,.06)}'
    +'.prompt-card.spec-architecture .glow-bar{background:linear-gradient(90deg,#0891b2,#06b6d4,#22d3ee,#8b5cf6,#06b6d4)!important;box-shadow:0 0 9px rgba(6,182,212,.75),0 0 19px rgba(139,92,246,.25)!important}'
    +'.prompt-card.spec-architecture .prompt-id{background:rgba(6,182,212,.13);color:#67e8f9;border-color:rgba(6,182,212,.36)}'
    +'.prompt-card.spec-architecture .prompt-name{color:#cffafe}.prompt-card.spec-architecture .prompt-type{color:rgba(165,243,252,.74)}'
    +'.spec-architecture-badge{display:inline-flex;align-items:center;gap:4px;font-size:9px;padding:2px 6px;border-radius:3px;background:rgba(6,182,212,.13);color:#67e8f9;border:1px solid rgba(6,182,212,.36);margin-left:6px;font-weight:650;white-space:nowrap}'
    +'.prompt-detail.spec-architecture{border-color:rgba(6,182,212,.45);box-shadow:0 20px 60px rgba(0,0,0,.52),0 0 34px rgba(6,182,212,.14)}'
    +'.prompt-detail.spec-architecture .pd-glow{background:linear-gradient(90deg,#0891b2,#06b6d4,#8b5cf6)!important;box-shadow:0 0 14px rgba(6,182,212,.48)}'
    +'.prompt-detail.spec-architecture .pd-id{background:rgba(6,182,212,.13);color:#67e8f9;border-color:rgba(6,182,212,.36)}'
    +'.prompt-detail.spec-architecture .pd-name{color:#cffafe}.prompt-detail.spec-architecture .pd-section h4{color:#22d3ee}'
    +'.prompt-detail.spec-architecture .pd-copy{background:#0891b2}.prompt-detail.spec-architecture .pd-copy:hover{background:#0e7490;box-shadow:0 0 18px rgba(6,182,212,.28)}';
  document.head.appendChild(style);
}

function promptById(id){
  return PROMPTS.find(function(prompt){return prompt.id===id});
}

function isSpecArchitecture(prompt){
  return !!prompt&&String(prompt.profile||'').toLowerCase()===PROFILE;
}

function decorateCard(card,prompt){
  if(!card||!isSpecArchitecture(prompt))return;
  card.classList.add(PROFILE);
  card.setAttribute('data-profile',PROFILE);
  var header=card.querySelector('.prompt-header');
  if(header&&!header.querySelector('.spec-architecture-badge')){
    var badge=document.createElement('span');
    badge.className='spec-architecture-badge';
    badge.textContent='◎ Spec Layers';
    var id=header.querySelector('.prompt-id');
    if(id&&id.nextSibling)header.insertBefore(badge,id.nextSibling);
    else if(id)header.appendChild(badge);
    else header.insertBefore(badge,header.firstChild);
  }
}

function decorateDetail(prompt){
  var detail=document.getElementById('promptDetail');
  if(!detail)return;
  detail.classList.toggle(PROFILE,isSpecArchitecture(prompt));
  if(isSpecArchitecture(prompt))detail.setAttribute('data-profile',PROFILE);
}

function installSpecArchitectureProfile(){
  if(typeof COLORS==='object'&&COLORS)COLORS.cyan=ACCENT;
  ensureSpecArchitectureStyles();

  var baseAppend=window.appendPromptCard;
  if(typeof baseAppend==='function'){
    window.appendPromptCard=function(grid,prompt){
      baseAppend(grid,prompt);
      var card=grid&&grid.lastElementChild;
      decorateCard(card,prompt);
    };
  }

  var baseShowPromptDetail=window.showPromptDetail;
  if(typeof baseShowPromptDetail==='function'){
    window.showPromptDetail=function(id,origin){
      baseShowPromptDetail(id,origin);
      decorateDetail(promptById(id));
    };
  }

  if(typeof window.render==='function')window.render();
}

installSpecArchitectureProfile();
})();
