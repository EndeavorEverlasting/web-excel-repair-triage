(function(){
'use strict';
var FIXED_PROMPT_FINDER_QUESTIONS=[
 {id:'startingPoint',prompt:'Where are you starting?',options:[
  {id:'new-repo',label:'I am starting without the repository checked out',queries:['clone repository','repository bootstrap','canonical path']},
  {id:'unfamiliar-repo',label:'I have the repository, but I do not understand it yet',queries:['repository discovery','codebase map','repo rules']},
  {id:'known-repo',label:'I know the repository and want to move work forward',queries:['bounded repository change','implement','sprint']},
  {id:'active-failure',label:'Something is failing or regressing now',queries:['troubleshoot','root cause','regression']},
  {id:'open-pr',label:'I am already on a branch, PR, or review floor',queries:['review repair','pull request','integration']},
  {id:'app-open',label:'The app or artifact is already open in front of me',queries:['app coach','usage coach','live app']}
 ]},
 {id:'goal',prompt:'What do you need to accomplish?',options:[
  {id:'discover',label:'Understand, discover, or investigate',queries:['discovery','understand repository','opportunity']},
  {id:'plan',label:'Plan, factor, or design the work',queries:['plan','factor','architecture']},
  {id:'coordinate',label:'Coordinate people, agents, lanes, or a work ledger',queries:['repository ledger','parallel','sequential']},
  {id:'repeated-stall',label:'The work keeps stalling, urgency is being missed, or I keep repeating the same correction',queries:['urgency','repeated pain','sub-part agent','stalled execution']},
  {id:'build',label:'Build, change, or repair repository behavior',queries:['implement','build','repair']},
  {id:'diagnose',label:'Diagnose a failure or find root cause',queries:['troubleshoot','root cause','failure']},
  {id:'artifact',label:'Create, transform, or repair a file or artifact',queries:['artifact builder','generate artifact','file transformation']},
  {id:'prove',label:'Validate, test, or prove behavior',queries:['validate','proof gate','regression test']},
  {id:'ship',label:'Integrate, release, deploy, or promote',queries:['integrate','release','deploy']},
  {id:'teach',label:'Teach, document, coach, or build a tutorial',queries:['tutorial','documentation','app coach']},
  {id:'agent-system',label:'Improve agents, harnesses, prompts, or AI engineering',queries:['agent harness','prompt kit','context engineering']},
  {id:'management',label:'Handle management, operations, correspondence, or client work',queries:['management','correspondence','operations']},
  {id:'close',label:'Close out, hand off, or clean up completed work',queries:['closeout','handoff','cleanup']}
 ]},
 {id:'proofNeed',prompt:'What kind of result do you need before you are done?',options:[
  {id:'not-sure',label:'I am not sure yet',queries:[]},
  {id:'static',label:'A plan, review, repository change, or deterministic proof',queries:['deterministic validation','review','repository change']},
  {id:'artifact',label:'A generated or transformed artifact',queries:['generated artifact','artifact output']},
  {id:'runtime',label:'Observed live or runtime behavior',queries:['runtime proof','live behavior']},
  {id:'production',label:'Integrated, deployed, or field-accepted behavior',queries:['deployment','field acceptance','production proof']}
 ]}
];
var PROMPT_FINDER_MAX_QUESTIONS=5;
var ADAPTIVE_CANDIDATE_LIMIT=6;
var S={step:0,answers:{},origin:null,selectedPromptId:null};
function rank(p){var n=Number(p&&p.discoveryRank);if(Number.isFinite(n))return n;n=parseInt(String((p&&p.seq)||'').replace(/\D/g,''),10);return 1000+(isNaN(n)?999999:n)}
function questionById(id){return FIXED_PROMPT_FINDER_QUESTIONS.find(function(q){return q.id===id})||null}
function optionById(question,id){return question&&question.options.find(function(option){return option.id===id})||null}
function sharedSearch(query){return typeof filterPromptsForQuery==='function'?filterPromptsForQuery(PROMPTS,query):[]}
function promptSummary(prompt){var text=String((prompt&&prompt.useWhen)||'').trim();if(!text)return 'Use this registered prompt for the matching current workflow.';var first=text.split(/(?<=[.!?])\s+/)[0];return first.length>180?first.slice(0,177)+'…':first}
function scorePromptFinderCandidates(answers){
 var scores={},reasons={};
 Object.keys(answers).forEach(function(questionId){
  var question=questionById(questionId),option=optionById(question,answers[questionId]);
  if(!option)return;
  var perQuestion={};
  option.queries.forEach(function(query){
   sharedSearch(query).forEach(function(prompt,index){
    var raw=Number(prompt._searchScore);
    var points=Number.isFinite(raw)?Math.max(1,Math.min(10,Math.round(raw/20))):Math.max(1,10-Math.min(index,9));
    perQuestion[prompt.id]=Math.max(perQuestion[prompt.id]||0,points)
   })
  });
  Object.keys(perQuestion).forEach(function(id){scores[id]=(scores[id]||0)+perQuestion[id];(reasons[id]||(reasons[id]=[])).push(option.label)})
 });
 return PROMPTS.map(function(prompt){return{prompt:prompt,score:scores[prompt.id]||0,reasons:Array.from(new Set(reasons[prompt.id]||[]))}}).sort(function(a,b){return b.score-a.score||rank(a.prompt)-rank(b.prompt)})
}
function adaptiveCandidates(){return scorePromptFinderCandidates(S.answers).slice(0,ADAPTIVE_CANDIDATE_LIMIT)}
function specialistPrompts(query){var q=String(query||'').trim();if(!q)return PROMPTS.slice().sort(function(a,b){return rank(a)-rank(b)});return sharedSearch(q)}
function shell(title,body){return '<button class="prompt-detail-close" onclick="closePromptFinder()" aria-label="Close prompt finder">&times;</button><div class="pd-glow" style="background:linear-gradient(90deg,#0ea5e9,#8b5cf6)"></div><div class="pd-header"><span class="pd-name">'+title+'</span></div>'+body}
function progress(step,total,label){var pct=Math.max(0,Math.min(100,(step/total)*100));return '<div class="finder-progress"><span style="width:'+pct+'%"></span></div><div class="finder-kicker">Question '+step+' of '+total+(label?' · '+label:'')+'</div>'}
function renderPromptFinderQuestion(){
 var q=FIXED_PROMPT_FINDER_QUESTIONS[S.step],body=progress(S.step+1,4,'')+'<h3 class="finder-question">'+escapePromptHtml(q.prompt)+'</h3><div class="finder-options">';
 q.options.forEach(function(o){body+='<button data-finder-option="'+o.id+'">'+escapePromptHtml(o.label)+'</button>'});
 body+='</div>'+(S.step?'<button class="finder-back" id="finderBack">&larr; Previous question</button>':'');
 var el=document.getElementById('promptDetail');el.innerHTML=shell('Prompt Kit Tutorial',body);
 el.querySelectorAll('[data-finder-option]').forEach(function(b){b.onclick=function(){S.answers[q.id]=b.getAttribute('data-finder-option');if(++S.step===FIXED_PROMPT_FINDER_QUESTIONS.length)renderAdaptiveQuestion();else renderPromptFinderQuestion()}});
 var back=document.getElementById('finderBack');if(back)back.onclick=function(){S.step--;renderPromptFinderQuestion()};
 var first=el.querySelector('[data-finder-option]');if(first)first.focus()
}
function renderAdaptiveQuestion(){
 var candidates=adaptiveCandidates(),body=progress(4,4,'usually final')+'<h3 class="finder-question">Which of these current Prompt Kit routes is closest?</h3><p class="finder-intro">These choices come from the live registry and your first three answers. Pick the closest route; you do not need to know a prompt ID.</p><div class="finder-options finder-candidate-options">';
 candidates.forEach(function(item){body+='<button data-finder-prompt="'+escapePromptHtml(item.prompt.id)+'"><strong>'+escapePromptHtml(item.prompt.name)+'</strong><span>'+escapePromptHtml(promptSummary(item.prompt))+'</span></button>'});
 body+='</div><button class="finder-specialist" id="finderSpecialist">Something else — show every prompt</button><button class="finder-back" id="finderBack">&larr; Previous question</button>';
 var el=document.getElementById('promptDetail');el.innerHTML=shell('Prompt Kit Tutorial',body);
 el.querySelectorAll('[data-finder-prompt]').forEach(function(b){b.onclick=function(){S.selectedPromptId=b.getAttribute('data-finder-prompt');renderPromptFinderResults()}});
 document.getElementById('finderSpecialist').onclick=function(){S.step=4;renderSpecialistQuestion()};
 document.getElementById('finderBack').onclick=function(){S.step=FIXED_PROMPT_FINDER_QUESTIONS.length-1;renderPromptFinderQuestion()};
 var first=el.querySelector('[data-finder-prompt]')||document.getElementById('finderSpecialist');if(first)first.focus()
}
function specialistListHtml(prompts){var body='<div class="finder-specialist-list">';prompts.forEach(function(prompt){body+='<button data-finder-specialist-prompt="'+escapePromptHtml(prompt.id)+'"><strong>'+escapePromptHtml(prompt.name)+'</strong><span>'+escapePromptHtml(promptSummary(prompt))+'</span></button>'});return body+'</div>'}
function renderSpecialistQuestion(){
 var body=progress(5,PROMPT_FINDER_MAX_QUESTIONS,'optional specialist finder')+'<h3 class="finder-question">Which registered prompt best matches the work?</h3><p class="finder-intro">Every current prompt is available here. Search by ordinary words, or browse the full live registry without memorizing an ID.</p><label class="finder-search-label" for="finderSpecialistSearch">Filter every prompt</label><input class="finder-search" id="finderSpecialistSearch" type="search" placeholder="e.g. deployment, tutorial, spreadsheet, agent, management">'+specialistListHtml(specialistPrompts(''))+'<button class="finder-back" id="finderBack">&larr; Back to recommended routes</button>';
 var el=document.getElementById('promptDetail');el.innerHTML=shell('Prompt Kit Tutorial',body);
 function bindChoices(){el.querySelectorAll('[data-finder-specialist-prompt]').forEach(function(b){b.onclick=function(){S.selectedPromptId=b.getAttribute('data-finder-specialist-prompt');renderPromptFinderResults()}})}
 bindChoices();
 var input=document.getElementById('finderSpecialistSearch');input.oninput=function(){var old=el.querySelector('.finder-specialist-list');if(old)old.outerHTML=specialistListHtml(specialistPrompts(input.value));bindChoices()};
 document.getElementById('finderBack').onclick=function(){S.step=FIXED_PROMPT_FINDER_QUESTIONS.length;renderAdaptiveQuestion()};input.focus()
}
function resultItemsForSelectedPrompt(){
 var ranked=scorePromptFinderCandidates(S.answers),selected=S.selectedPromptId&&PROMPTS.find(function(prompt){return prompt.id===S.selectedPromptId});
 if(!selected)return ranked.slice(0,3);
 var primary={prompt:selected,score:Number.MAX_SAFE_INTEGER,reasons:['Selected from the live Prompt Kit registry after your tutorial answers']};
 return[primary].concat(ranked.filter(function(item){return item.prompt.id!==selected.id}).slice(0,2))
}
function card(item,i){var p=item.prompt,label=i===0?'Primary recommendation':'Related option';return '<article class="finder-result'+(i===0?' primary':'')+'"><small>'+label+'</small><h3><span>'+escapePromptHtml(p.id)+'</span> '+escapePromptHtml(p.name)+'</h3><p>'+escapePromptHtml((item.reasons&&item.reasons.length?item.reasons:['Current registry metadata match']).join(' · '))+'</p><div><button data-finder-open="'+p.id+'">Open</button><button data-finder-copy="'+p.id+'">Copy</button></div></article>'}
function renderPromptFinderResults(){
 var results=resultItemsForSelectedPrompt(),body='<p class="finder-intro">The primary prompt is the route you selected from the current registry. Related options still use shared Prompt Kit search ranking. Open the primary prompt to continue through its registry-owned Guided workflow.</p>';
 results.forEach(function(x,i){body+=card(x,i)});body+='<button class="finder-back" id="finderRestart">Start over</button>';
 var el=document.getElementById('promptDetail');el.innerHTML=shell('Recommended Prompt Path',body);
 el.querySelectorAll('[data-finder-open]').forEach(function(b){b.onclick=function(){showPromptDetail(b.getAttribute('data-finder-open'),S.origin)}});
 el.querySelectorAll('[data-finder-copy]').forEach(function(b){b.onclick=function(){copyPrompt(b.getAttribute('data-finder-copy'));b.textContent='Copied!';setTimeout(function(){b.textContent='Copy'},1200)}});
 document.getElementById('finderRestart').onclick=function(){S.step=0;S.answers={};S.selectedPromptId=null;renderPromptFinderQuestion()};var first=el.querySelector('[data-finder-open]')||document.getElementById('finderRestart');if(first)first.focus()
}
function openPromptFinder(origin){S={step:0,answers:{},origin:origin||document.getElementById('addPromptBtn'),selectedPromptId:null};promptDetailOrigin=S.origin;document.getElementById('promptDetailOverlay').classList.add('open');renderPromptFinderQuestion()}
window.closePromptFinder=function(){closePromptDetail()};window.openPromptFinder=openPromptFinder;window.scorePromptFinderAnswers=scorePromptFinderCandidates;window.PROMPT_FINDER_QUESTIONS=FIXED_PROMPT_FINDER_QUESTIONS;window.promptFinderSpecialistMatches=specialistPrompts;
var style=document.createElement('style');style.id='prompt-kit-guided-recommendation-styles';style.textContent='.finder-progress{height:5px;border-radius:9px;background:var(--bg-surface);overflow:hidden;margin:4px 0 20px}.finder-progress span{display:block;height:100%;background:linear-gradient(90deg,#0ea5e9,#8b5cf6);box-shadow:0 0 12px rgba(59,130,246,.45)}.finder-kicker,.finder-result small{font-size:9px;text-transform:uppercase;letter-spacing:.08em;color:var(--text-muted)}.finder-question{font-size:17px;color:var(--text-primary);margin:8px 0 16px}.finder-options{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:10px}.finder-options button,.finder-back,.finder-specialist,.finder-result button,.finder-specialist-list button{border:1px solid var(--border);border-radius:8px;background:var(--bg-surface);color:var(--text-primary);cursor:pointer;padding:10px 12px}.finder-options button,.finder-specialist-list button{text-align:left;min-height:54px}.finder-candidate-options button strong,.finder-specialist-list button strong{display:block;font-size:12px}.finder-candidate-options button span,.finder-specialist-list button span{display:block;margin-top:4px;font-size:10px;line-height:1.4;color:var(--text-secondary)}.finder-options button:hover,.finder-options button:focus-visible,.finder-back:hover,.finder-specialist:hover,.finder-specialist:focus-visible,.finder-result button:hover,.finder-specialist-list button:hover,.finder-specialist-list button:focus-visible{outline:none;border-color:var(--accent);color:var(--accent);box-shadow:0 0 0 2px var(--accent-glow)}.finder-back,.finder-specialist{margin-top:16px}.finder-intro,.finder-result p{font-size:11px;line-height:1.5;color:var(--text-secondary)}.finder-result{border:1px solid var(--border);border-radius:10px;padding:14px;margin:10px 0}.finder-result.primary{border-color:rgba(34,197,94,.65);box-shadow:0 0 18px rgba(34,197,94,.1)}.finder-result h3{font-size:14px;margin:5px 0}.finder-result h3 span{color:var(--accent);font-family:monospace}.finder-result div{display:flex;gap:8px}.finder-result button{font-size:10px;padding:6px 12px}.finder-search-label{display:block;margin:0 0 6px;font-size:10px;color:var(--text-secondary)}.finder-search{width:100%;min-height:42px;padding:9px 10px;border:1px solid var(--border);border-radius:8px;background:var(--bg-surface);color:var(--text-primary);font-size:14px}.finder-search:focus{outline:none;border-color:var(--accent);box-shadow:0 0 0 2px var(--accent-glow)}.finder-specialist-list{display:grid;gap:8px;margin-top:12px;max-height:48vh;overflow:auto}.prompt-header-actions{display:flex;gap:8px;align-items:center}.prompt-header-actions .add-prompt-btn{white-space:nowrap}.finder-prompt-btn{border-color:rgba(56,189,248,.65)!important;color:#e0f2fe!important;background:linear-gradient(135deg,rgba(14,165,233,.18),rgba(139,92,246,.18))!important;box-shadow:0 0 12px rgba(56,189,248,.28);animation:prompt-finder-beacon 2.4s ease-in-out infinite}@keyframes prompt-finder-beacon{0%,100%{box-shadow:0 0 10px rgba(56,189,248,.28),0 0 0 0 rgba(56,189,248,.18)}50%{box-shadow:0 0 22px rgba(56,189,248,.58),0 0 0 5px rgba(56,189,248,.08)}}.finder-prompt-btn:hover,.finder-prompt-btn:focus-visible{border-color:#7dd3fc!important;color:#fff!important;box-shadow:0 0 24px rgba(56,189,248,.65)!important;outline:none}@media(prefers-reduced-motion:reduce){.finder-prompt-btn{animation:none;box-shadow:0 0 16px rgba(56,189,248,.45)}}@media(max-width:760px){.prompt-header-actions{grid-column:1/2;display:flex;flex-wrap:wrap;gap:8px;align-items:center}.prompt-header-actions .add-prompt-btn{min-height:40px}}@media(max-width:620px){.finder-options{grid-template-columns:1fr}}';document.head.appendChild(style);
var addButton=document.getElementById('addPromptBtn');if(addButton&&!document.getElementById('promptFinderBtn')){var actions=document.createElement('div');actions.className='prompt-header-actions';addButton.parentNode.insertBefore(actions,addButton);var finder=document.createElement('button');finder.className='add-prompt-btn finder-prompt-btn';finder.id='promptFinderBtn';finder.textContent='✦ Tutorial · Find My Prompt';finder.setAttribute('aria-label','Open the guided Prompt Kit tutorial and adaptive prompt finder');finder.title='Answer four quick questions; use the optional fifth to browse every prompt';finder.onclick=function(){openPromptFinder(finder)};actions.appendChild(finder);actions.appendChild(addButton)}
})();
