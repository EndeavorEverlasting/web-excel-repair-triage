(function(){
'use strict';
var PROFILE='correspondence';
var ACCENT='#ec4899';

function ensureCorrespondenceStyles(){
  if(document.getElementById('prompt-kit-correspondence-styles'))return;
  var style=document.createElement('style');
  style.id='prompt-kit-correspondence-styles';
  style.textContent='.prompt-card.correspondence{background:linear-gradient(145deg,#211321 0%,#281526 42%,#1b111d 100%);border-color:rgba(236,72,153,.34);box-shadow:inset 0 0 34px rgba(236,72,153,.035)}.prompt-card.correspondence:hover{border-color:#ec4899;box-shadow:0 8px 32px rgba(0,0,0,.42),0 0 26px rgba(236,72,153,.2),inset 0 0 34px rgba(236,72,153,.06)}.prompt-card.correspondence .glow-bar{background:linear-gradient(90deg,#db2777,#ec4899,#f472b6,#ec4899,#db2777)!important;box-shadow:0 0 9px rgba(236,72,153,.72),0 0 18px rgba(244,114,182,.32)!important}.prompt-card.correspondence .prompt-id{background:rgba(236,72,153,.13);color:#f9a8d4;border-color:rgba(236,72,153,.34)}.prompt-card.correspondence .prompt-name{color:#fce7f3}.prompt-card.correspondence .prompt-type{color:rgba(249,168,212,.72)}.prompt-card.correspondence .prompt-badge{border-color:rgba(236,72,153,.22);color:rgba(251,207,232,.76)}.correspondence-badge{display:inline-flex;align-items:center;gap:4px;font-size:9px;padding:2px 6px;border-radius:3px;background:rgba(236,72,153,.14);color:#f9a8d4;border:1px solid rgba(236,72,153,.34);margin-left:6px;font-weight:650;white-space:nowrap}.prompt-detail.correspondence{border-color:rgba(236,72,153,.42);box-shadow:0 20px 60px rgba(0,0,0,.52),0 0 32px rgba(236,72,153,.12)}.prompt-detail.correspondence .pd-glow{background:linear-gradient(90deg,#db2777,#ec4899,#f472b6)!important;box-shadow:0 0 14px rgba(236,72,153,.45)}.prompt-detail.correspondence .pd-id{background:rgba(236,72,153,.13);color:#f9a8d4;border-color:rgba(236,72,153,.34)}.prompt-detail.correspondence .pd-name{color:#fce7f3}.prompt-detail.correspondence .pd-section h4{color:#f472b6}.prompt-detail.correspondence .pd-copy{background:#db2777}.prompt-detail.correspondence .pd-copy:hover{background:#be185d;box-shadow:0 0 18px rgba(236,72,153,.25)}';
  document.head.appendChild(style);
}

function promptById(id){
  return PROMPTS.find(function(prompt){return prompt.id===id});
}

function isCorrespondence(prompt){
  return !!prompt&&String(prompt.profile||'').toLowerCase()===PROFILE;
}

function decorateCard(card,prompt){
  if(!card||!isCorrespondence(prompt))return;
  card.classList.add(PROFILE);
  card.setAttribute('data-profile',PROFILE);
  var header=card.querySelector('.prompt-header');
  if(header&&!header.querySelector('.correspondence-badge')){
    var badge=document.createElement('span');
    badge.className='correspondence-badge';
    badge.textContent='✉ Correspondence';
    var id=header.querySelector('.prompt-id');
    if(id&&id.nextSibling)header.insertBefore(badge,id.nextSibling);
    else if(id)header.appendChild(badge);
    else header.insertBefore(badge,header.firstChild);
  }
}

function decorateDetail(prompt){
  var detail=document.getElementById('promptDetail');
  if(!detail)return;
  detail.classList.toggle(PROFILE,isCorrespondence(prompt));
  detail.setAttribute('data-profile',isCorrespondence(prompt)?PROFILE:'standard');
}

function installCorrespondenceProfile(){
  if(typeof COLORS==='object'&&COLORS)COLORS.magenta=ACCENT;
  ensureCorrespondenceStyles();

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

installCorrespondenceProfile();
})();
