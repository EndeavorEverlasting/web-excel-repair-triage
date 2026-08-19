(function(){
'use strict';
var PROFILES={
  'billing-management':{
    className:'billing-management',accent:'#10b981',badgeClass:'billing-management-badge',badge:'▦ NTH Billing'
  },
  'fun-management':{
    className:'fun-management',accent:'#6366f1',badgeClass:'fun-management-badge',badge:'◆ FUN Management'
  },
  'triage-management':{
    className:'triage-management',accent:'#10b981',badgeClass:'triage-management-badge',badge:'▣ Triage Ops'
  }
};

function ensureManagementStyles(){
  if(document.getElementById('prompt-kit-management-styles'))return;
  var style=document.createElement('style');
  style.id='prompt-kit-management-styles';
  style.textContent=''
    +'.prompt-card.billing-management{background:linear-gradient(145deg,#10241d 0%,#112a22 46%,#0d1d19 100%);border-color:rgba(16,185,129,.34);box-shadow:inset 0 0 34px rgba(16,185,129,.035)}'
    +'.prompt-card.billing-management:hover{border-color:#10b981;box-shadow:0 8px 32px rgba(0,0,0,.42),0 0 26px rgba(16,185,129,.2),inset 0 0 34px rgba(16,185,129,.06)}'
    +'.prompt-card.billing-management .glow-bar{background:linear-gradient(90deg,#047857,#10b981,#34d399,#10b981,#047857)!important;box-shadow:0 0 9px rgba(16,185,129,.72),0 0 18px rgba(52,211,153,.3)!important}'
    +'.prompt-card.billing-management .prompt-id{background:rgba(16,185,129,.13);color:#6ee7b7;border-color:rgba(16,185,129,.34)}'
    +'.prompt-card.billing-management .prompt-name{color:#d1fae5}.prompt-card.billing-management .prompt-type{color:rgba(110,231,183,.72)}'
    +'.billing-management-badge{display:inline-flex;align-items:center;gap:4px;font-size:9px;padding:2px 6px;border-radius:3px;background:rgba(16,185,129,.14);color:#6ee7b7;border:1px solid rgba(16,185,129,.34);margin-left:6px;font-weight:650;white-space:nowrap}'
    +'.prompt-detail.billing-management{border-color:rgba(16,185,129,.42);box-shadow:0 20px 60px rgba(0,0,0,.52),0 0 32px rgba(16,185,129,.12)}'
    +'.prompt-detail.billing-management .pd-glow{background:linear-gradient(90deg,#047857,#10b981,#34d399)!important;box-shadow:0 0 14px rgba(16,185,129,.45)}'
    +'.prompt-detail.billing-management .pd-id{background:rgba(16,185,129,.13);color:#6ee7b7;border-color:rgba(16,185,129,.34)}'
    +'.prompt-detail.billing-management .pd-name{color:#d1fae5}.prompt-detail.billing-management .pd-section h4{color:#34d399}'
    +'.prompt-detail.billing-management .pd-copy{background:#059669}.prompt-detail.billing-management .pd-copy:hover{background:#047857;box-shadow:0 0 18px rgba(16,185,129,.25)}'
    +'.prompt-card.fun-management{background:linear-gradient(145deg,#15172b 0%,#181a35 46%,#111426 100%);border-color:rgba(99,102,241,.38);box-shadow:inset 0 0 34px rgba(99,102,241,.04)}'
    +'.prompt-card.fun-management:hover{border-color:#6366f1;box-shadow:0 8px 32px rgba(0,0,0,.42),0 0 26px rgba(99,102,241,.22),inset 0 0 34px rgba(99,102,241,.07)}'
    +'.prompt-card.fun-management .glow-bar{background:linear-gradient(90deg,#4338ca,#6366f1,#818cf8,#22d3ee,#6366f1)!important;box-shadow:0 0 9px rgba(99,102,241,.72),0 0 18px rgba(34,211,238,.24)!important}'
    +'.prompt-card.fun-management .prompt-id{background:rgba(99,102,241,.14);color:#a5b4fc;border-color:rgba(99,102,241,.36)}'
    +'.prompt-card.fun-management .prompt-name{color:#e0e7ff}.prompt-card.fun-management .prompt-type{color:rgba(165,180,252,.74)}'
    +'.fun-management-badge{display:inline-flex;align-items:center;gap:4px;font-size:9px;padding:2px 6px;border-radius:3px;background:rgba(99,102,241,.14);color:#a5b4fc;border:1px solid rgba(99,102,241,.36);margin-left:6px;font-weight:650;white-space:nowrap}'
    +'.prompt-detail.fun-management{border-color:rgba(99,102,241,.44);box-shadow:0 20px 60px rgba(0,0,0,.52),0 0 32px rgba(99,102,241,.14)}'
    +'.prompt-detail.fun-management .pd-glow{background:linear-gradient(90deg,#4338ca,#6366f1,#22d3ee)!important;box-shadow:0 0 14px rgba(99,102,241,.46)}'
    +'.prompt-detail.fun-management .pd-id{background:rgba(99,102,241,.14);color:#a5b4fc;border-color:rgba(99,102,241,.36)}'
    +'.prompt-detail.fun-management .pd-name{color:#e0e7ff}.prompt-detail.fun-management .pd-section h4{color:#818cf8}'
    +'.prompt-detail.fun-management .pd-copy{background:#4f46e5}.prompt-detail.fun-management .pd-copy:hover{background:#4338ca;box-shadow:0 0 18px rgba(99,102,241,.27)}'
    +'.prompt-card.triage-management{background:linear-gradient(145deg,#0f241b 0%,#10281e 46%,#0b1d16 100%);border-color:rgba(16,185,129,.42);box-shadow:inset 0 0 34px rgba(16,185,129,.05)}'
    +'.prompt-card.triage-management:hover{border-color:#10b981;box-shadow:0 8px 32px rgba(0,0,0,.42),0 0 28px rgba(16,185,129,.24),inset 0 0 34px rgba(16,185,129,.08)}'
    +'.prompt-card.triage-management .glow-bar{background:linear-gradient(90deg,#065f46,#10b981,#6ee7b7,#34d399,#10b981)!important;box-shadow:0 0 9px rgba(16,185,129,.76),0 0 18px rgba(110,231,183,.28)!important}'
    +'.prompt-card.triage-management .prompt-id{background:rgba(16,185,129,.15);color:#a7f3d0;border-color:rgba(16,185,129,.42)}'
    +'.prompt-card.triage-management .prompt-name{color:#dcfce7}.prompt-card.triage-management .prompt-type{color:rgba(167,243,208,.76)}'
    +'.triage-management-badge{display:inline-flex;align-items:center;gap:4px;font-size:9px;padding:2px 6px;border-radius:3px;background:rgba(16,185,129,.16);color:#a7f3d0;border:1px solid rgba(16,185,129,.42);margin-left:6px;font-weight:650;white-space:nowrap}'
    +'.prompt-detail.triage-management{border-color:rgba(16,185,129,.48);box-shadow:0 20px 60px rgba(0,0,0,.52),0 0 34px rgba(16,185,129,.15)}'
    +'.prompt-detail.triage-management .pd-glow{background:linear-gradient(90deg,#065f46,#10b981,#6ee7b7)!important;box-shadow:0 0 14px rgba(16,185,129,.5)}'
    +'.prompt-detail.triage-management .pd-id{background:rgba(16,185,129,.15);color:#a7f3d0;border-color:rgba(16,185,129,.42)}'
    +'.prompt-detail.triage-management .pd-name{color:#dcfce7}.prompt-detail.triage-management .pd-section h4{color:#6ee7b7}'
    +'.prompt-detail.triage-management .pd-copy{background:#059669}.prompt-detail.triage-management .pd-copy:hover{background:#047857;box-shadow:0 0 18px rgba(16,185,129,.3)}';
  document.head.appendChild(style);
}

function promptById(id){
  return PROMPTS.find(function(prompt){return prompt.id===id});
}

function profileFor(prompt){
  if(!prompt)return null;
  var key=String(prompt.profile||'').toLowerCase();
  return PROFILES[key]||null;
}

function decorateCard(card,prompt){
  var profile=profileFor(prompt);
  if(!card||!profile)return;
  card.classList.add(profile.className);
  card.setAttribute('data-profile',profile.className);
  var header=card.querySelector('.prompt-header');
  if(header&&!header.querySelector('.'+profile.badgeClass)){
    var badge=document.createElement('span');
    badge.className=profile.badgeClass;
    badge.textContent=profile.badge;
    var id=header.querySelector('.prompt-id');
    if(id&&id.nextSibling)header.insertBefore(badge,id.nextSibling);
    else if(id)header.appendChild(badge);
    else header.insertBefore(badge,header.firstChild);
  }
}

function decorateDetail(prompt){
  var detail=document.getElementById('promptDetail');
  if(!detail)return;
  Object.keys(PROFILES).forEach(function(key){detail.classList.remove(PROFILES[key].className);});
  var profile=profileFor(prompt);
  if(profile){
    detail.classList.add(profile.className);
    detail.setAttribute('data-profile',profile.className);
  }else{
    detail.setAttribute('data-profile','standard');
  }
}

function installManagementProfiles(){
  if(typeof COLORS==='object'&&COLORS){
    COLORS.emerald=PROFILES['billing-management'].accent;
    COLORS.indigo=PROFILES['fun-management'].accent;
  }
  ensureManagementStyles();

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

installManagementProfiles();
})();
