(function(){
'use strict';

var PROMPT_FINDER_QUESTIONS=[
 {id:'startingPoint',prompt:'Where are you starting?',options:[
  {id:'no-checkout',label:'I do not have the repository checked out yet',queries:['clone','repository bootstrap','git clone','existing repository clone']},
  {id:'unfamiliar',label:'I have a repository but it is unfamiliar',queries:['discovery','unfamiliar repo','repo rules','repository evidence']},
  {id:'known-working',label:'I am in a known repository and want to do work',queries:['sprint','implement','execute','build']},
  {id:'active-failure',label:'Something is failing or broken right now',queries:['troubleshoot','diagnose','root cause','failure']},
  {id:'pr-review',label:'I need to review, repair, or merge existing work',queries:['review','pr review','repair','merge']},
  {id:'app-open',label:'The app or artifact is already open in front of me',queries:['app coach','usage coach','app-at-hand']}
 ]},
 {id:'intent',prompt:'What is your job to be done?',options:[
  {id:'implement',label:'Implement a bounded code or repository change',queries:['implement','bounded change','repo sprint']},
  {id:'diagnose',label:'Diagnose or repair a failure',queries:['troubleshoot','diagnose','root cause']},
  {id:'plan',label:'Plan, factor, or divide the work',queries:['plan','factor','sprint plan','parallel sprint']},
  {id:'artifact',label:'Create an artifact, report, or tutorial',queries:['artifact','generate artifact','build artifact','tutorial']},
  {id:'validate',label:'Validate, prove, or guard behavior',queries:['validate','behavior proof','runtime','regression']},
  {id:'integrate',label:'Integrate, deploy, or release',queries:['integrate','deploy','release']},
  {id:'maintain',label:'Repository maintenance, cleanup, or upgrade',queries:['cleanup','dependency','upgrade','maintenance']},
  {id:'ai-engineering',label:'AI engineering, agent architecture, or LLM Ops',queries:['ai engineering','evals','context engineering','production agents','llm ops']},
  {id:'teach',label:'Teaching, coaching, or durable documentation',queries:['teach','tutorial','documentation','socratic']},
  {id:'manage',label:'Management, correspondence, or billing work',queries:['management','correspondence','billing','evidence']},
  {id:'prompt-kit',label:'Prompt Kit maintenance, registry, or classification',queries:['prompt kit','registry','classification','prompt architecture']},
  {id:'testing',label:'Testing, QA, regression guards, or failure analysis',queries:['test','regression','failure analysis','audit']}
 ]},
 {id:'stage',prompt:'What stage or work shape?',options:[
  {id:'planning',label:'Planning or factoring only',queries:['plan','factor']},
  {id:'one-sprint',label:'One bounded sprint',queries:['sprint','one bounded']},
  {id:'parallel',label:'Several safe parallel lanes',queries:['parallel sprint','multi-agent plan']},
  {id:'sequential',label:'A dependency-ordered sequence',queries:['sprint plan','launch pack','sequential']},
  {id:'review',label:'Review, repair, or validate',queries:['review','repair','validate']},
  {id:'integrate',label:'Integration, deployment, or closeout',queries:['integrate','deploy','closeout']}
 ]}
];

var S={step:0,answers:{},origin:null,adaptiveQuestion:null};

function seqValue(p){
  var raw=String((p&&p.seq)||((p&&p.id)||''));
  var n=parseInt(raw.replace(/\D/g,''),10);
  return isNaN(n)?999999:n;
}

function questionById(id){
  if(id==='discriminator'&&S.adaptiveQuestion)return S.adaptiveQuestion;
  return PROMPT_FINDER_QUESTIONS.find(function(q){return q.id===id})||null;
}

function optionById(question,id){
  return question&&question.options.find(function(option){return option.id===id})||null;
}

function sharedSearch(query){
  return typeof filterPromptsForQuery==='function'?filterPromptsForQuery(PROMPTS,query):[];
}

function buildAdaptiveQuestion(candidates){
  var families={};
  candidates.slice(0,10).forEach(function(c){
    var cls=String(c.prompt.class||'Other').split('/')[0].trim();
    if(!families[cls])families[cls]={label:cls,prompts:[]};
    families[cls].prompts.push(c.prompt);
  });
  var options=[];
  Object.keys(families).sort(function(a,b){
    return families[b].prompts.length-families[a].prompts.length;
  }).slice(0,4).forEach(function(cls,index){
    var first=families[cls].prompts[0];
    var queries=[first.type.toLowerCase(),cls.toLowerCase()];
    var kw=(first.keywords||[]).slice(0,3);
    kw.forEach(function(k){queries.push(k.toLowerCase())});
    options.push({id:'adaptive-'+index,label:cls,queries:queries});
  });
  if(options.length<2){
    options.push({id:'adaptive-fallback',label:'General purpose',queries:['prompt']});
  }
  return {id:'discriminator',prompt:'Which area matches your need most closely?',options:options};
}

function scorePromptFinderAnswers(answers,allPrompts,includeAll){
  var scores={},reasons={};
  Object.keys(answers).forEach(function(questionId){
    var question=questionById(questionId),option=optionById(question,answers[questionId]);
    if(!option)return;
    option.queries.forEach(function(query){
      var results=sharedSearch(query);
      if(!results.length)return;
      results.forEach(function(r){
        var id=r.id;
        var points=Math.min(r._searchScore||0,100);
        scores[id]=(scores[id]||0)+points;
        (reasons[id]||(reasons[id]=[])).push(option.label);
      });
    });
  });
  var sorted=Object.keys(scores).map(function(id){
    var prompt=(allPrompts||PROMPTS).find(function(p){return p.id===id});
    return prompt?{prompt:prompt,score:scores[id],reasons:Array.from(new Set(reasons[id]))}:null;
  }).filter(Boolean).sort(function(a,b){
    return b.score-a.score||seqValue(a.prompt)-seqValue(b.prompt);
  });
  return includeAll?sorted:sorted.slice(0,3);
}

function getCurrentQuestion(){
  if(S.step<3)return PROMPT_FINDER_QUESTIONS[S.step];
  if(S.step===3){
    if(!S.adaptiveQuestion){
      var candidates=scorePromptFinderAnswers(S.answers,PROMPTS,true);
      S.adaptiveQuestion=buildAdaptiveQuestion(candidates);
    }
    return S.adaptiveQuestion;
  }
  return null;
}

function shell(title,body){
  return '<button class="prompt-detail-close" onclick="closePromptFinder()" aria-label="Close prompt finder">&times;</button><div class="pd-glow" style="background:linear-gradient(90deg,#0ea5e9,#8b5cf6)"></div><div class="pd-header"><span class="pd-name">'+title+'</span></div>'+body;
}

function renderPromptFinderQuestion(){
  var q=getCurrentQuestion();
  if(!q)return renderPromptFinderResults();
  var total=4;
  var pct=((S.step+1)/total)*100;
  var body='<div class="finder-progress"><span style="width:'+pct+'%"></span></div><div class="finder-kicker">Question '+(S.step+1)+' of '+total+'</div><h3 class="finder-question">'+escapePromptHtml(q.prompt)+'</h3><div class="finder-options">';
  q.options.forEach(function(o){
    body+='<button data-finder-option="'+o.id+'">'+escapePromptHtml(o.label)+'</button>';
  });
  body+='</div>'+(S.step?'<button class="finder-back" id="finderBack">&larr; Previous question</button>':'');
  var el=document.getElementById('promptDetail');
  el.innerHTML=shell('Prompt Kit Tutorial',body);
  el.querySelectorAll('[data-finder-option]').forEach(function(b){
    b.onclick=function(){
      S.answers[q.id]=b.getAttribute('data-finder-option');
      if(++S.step===total)renderPromptFinderResults();
      else renderPromptFinderQuestion();
    };
  });
  var back=document.getElementById('finderBack');
  if(back)back.onclick=function(){
    if(S.step===3)S.adaptiveQuestion=null;
    S.step--;
    renderPromptFinderQuestion();
  };
  var first=el.querySelector('[data-finder-option]');
  if(first)first.focus();
}

function card(item,i){
  var p=item.prompt,label=i===0?'Phase 1 · Found':'Follow-on option';
  return '<article class="finder-result'+(i===0?' primary':'')+'"><small>'+label+'</small><h3><span>'+escapePromptHtml(p.id)+'</span> '+escapePromptHtml(p.name)+'</h3><p>'+escapePromptHtml(item.reasons.join(' · '))+'</p><div><button data-finder-open="'+p.id+'">Open</button><button data-finder-copy="'+p.id+'">Copy</button></div></article>';
}

function phaseRailHtml(activePhase){
  var phases=['Find','Use','Prove','Continue'];
  var html='<div class="finder-phase-rail" aria-label="Tutorial phase progress">';
  phases.forEach(function(name,index){
    var n=index+1,state=index<activePhase?'done':(index===activePhase?'active':'pending');
    html+='<div class="finder-phase '+state+'"><span class="finder-phase-n">'+(state==='done'?'✓':n)+'</span><span class="finder-phase-name">'+name+'</span></div>';
    if(index<phases.length-1)html+='<span class="finder-phase-link'+(state==='done'?' done':'')+'" aria-hidden="true"></span>';
  });
  return html+'</div>';
}

function primaryPhaseBody(model){
  var p=model.current;
  var html=phaseRailHtml(1);
  html+='<div class="finder-phase-block use"><small>Phase 2 · Use</small><p>Copy <strong>'+escapePromptHtml(p.id)+'</strong> and run it in a new chat. Fill its concrete variables and execute the bounded sprint it describes.</p></div>';
  html+='<div class="finder-phase-block prove"><small>Phase 3 · Prove</small><p>'+escapePromptHtml(String(p.expectedOutput||p.proofGate||'Produce the prompt\'s expected output or proof gate.'))+'</p></div>';
  html+='<div class="finder-phase-block continue"><small>Phase 4 · Continue</small><p>'+escapePromptHtml(String(p.nextStep||'No explicit next step is registered. Re-run Find My Prompt after this result changes your context.'))+'</p>';
  if(model.next&&model.next.length){
    html+='<div class="finder-phase-next">';
    model.next.forEach(function(np){html+='<button type="button" data-finder-open="'+np.id+'">Then '+escapePromptHtml(np.id)+'</button>'});
    html+='</div>';
  }
  html+='</div>';
  return html;
}

function renderPromptFinderResults(){
  var results=scorePromptFinderAnswers(S.answers);
  var body='<p class="finder-intro">Your prompt path is one continuous experience: <strong>Find</strong> the right prompt, <strong>Use</strong> it, <strong>Prove</strong> the result, then <strong>Continue</strong> to the registered next step.</p>';
  if(results.length){
    var primary=results[0];
    var resolved=PROMPTS.find(function(p){return p.id===primary.prompt.id});
    if(resolved){
      body+=card(primary,0);
      var model=typeof buildPromptGuidanceModel==='function'?buildPromptGuidanceModel(resolved.id):null;
      if(model)body+=primaryPhaseBody(model);
    }
    for(var i=1;i<results.length;i++){
      var r=results[i],rr=PROMPTS.find(function(p){return p.id===r.prompt.id});
      if(rr)body+=card(r,i);
    }
  }
  else body+='<p>No registered prompt matched strongly enough. Search for P65 for the conversational fallback.</p>';
  body+='<button class="finder-back" id="finderRestart">Start over</button>';
  var el=document.getElementById('promptDetail');
  el.innerHTML=shell('Find → Use → Prove → Continue',body);
  el.querySelectorAll('[data-finder-open]').forEach(function(b){
    b.onclick=function(){showPromptDetail(b.getAttribute('data-finder-open'),S.origin)};
  });
  el.querySelectorAll('[data-finder-copy]').forEach(function(b){
    b.onclick=function(){
      copyPrompt(b.getAttribute('data-finder-copy'));
      b.textContent='Copied!';
      setTimeout(function(){b.textContent='Copy'},1200);
    };
  });
  document.getElementById('finderRestart').onclick=function(){
    S={step:0,answers:{},origin:S.origin,adaptiveQuestion:null};
    renderPromptFinderQuestion();
  };
  var first=el.querySelector('[data-finder-open]')||document.getElementById('finderRestart');
  if(first)first.focus();
}

function openPromptFinder(origin){
  S={step:0,answers:{},origin:origin||document.getElementById('addPromptBtn'),adaptiveQuestion:null};
  promptDetailOrigin=S.origin;
  document.getElementById('promptDetailOverlay').classList.add('open');
  renderPromptFinderQuestion();
}

window.closePromptFinder=function(){closePromptDetail()};
window.openPromptFinder=openPromptFinder;
window.scorePromptFinderAnswers=scorePromptFinderAnswers;
window.PROMPT_FINDER_QUESTIONS=PROMPT_FINDER_QUESTIONS;

var style=document.createElement('style');style.id='prompt-kit-guided-recommendation-styles';style.textContent='.finder-progress{height:5px;border-radius:9px;background:var(--bg-surface);overflow:hidden;margin:4px 0 20px}.finder-progress span{display:block;height:100%;background:linear-gradient(90deg,#0ea5e9,#8b5cf6);box-shadow:0 0 12px rgba(59,130,246,.45)}.finder-kicker,.finder-result small{font-size:9px;text-transform:uppercase;letter-spacing:.08em;color:var(--text-muted)}.finder-question{font-size:17px;color:var(--text-primary);margin:8px 0 16px}.finder-options{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:10px}.finder-options button,.finder-back,.finder-result button{border:1px solid var(--border);border-radius:8px;background:var(--bg-surface);color:var(--text-primary);cursor:pointer;padding:10px 12px}.finder-options button{text-align:left;min-height:54px}.finder-options button:hover,.finder-options button:focus-visible,.finder-back:hover,.finder-result button:hover{outline:none;border-color:var(--accent);color:var(--accent);box-shadow:0 0 0 2px var(--accent-glow)}.finder-back{margin-top:16px}.finder-intro,.finder-result p{font-size:11px;line-height:1.5;color:var(--text-secondary)}.finder-result{border:1px solid var(--border);border-radius:10px;padding:14px;margin:10px 0}.finder-result.primary{border-color:rgba(34,197,94,.65);box-shadow:0 0 18px rgba(34,197,94,.1)}.finder-result h3{font-size:14px;margin:5px 0}.finder-result h3 span{color:var(--accent);font-family:monospace}.finder-result div{display:flex;gap:8px}.finder-result button{font-size:10px;padding:6px 12px}.prompt-header-actions{display:flex;gap:8px;align-items:center}.prompt-header-actions .add-prompt-btn{white-space:nowrap}.finder-prompt-btn{border-color:rgba(56,189,248,.65)!important;color:#e0f2fe!important;background:linear-gradient(135deg,rgba(14,165,233,.18),rgba(139,92,246,.18))!important;box-shadow:0 0 12px rgba(56,189,248,.28);animation:prompt-finder-beacon 2.4s ease-in-out infinite}@keyframes prompt-finder-beacon{0%,100%{box-shadow:0 0 10px rgba(56,189,248,.28),0 0 0 0 rgba(56,189,248,.18)}50%{box-shadow:0 0 22px rgba(56,189,248,.58),0 0 0 5px rgba(56,189,248,.08)}}.finder-prompt-btn:hover,.finder-prompt-btn:focus-visible{border-color:#7dd3fc!important;color:#fff!important;box-shadow:0 0 24px rgba(56,189,248,.65)!important;outline:none}.finder-phase-rail{display:flex;align-items:center;gap:6px;margin:14px 0 12px;overflow-x:auto;scrollbar-width:none;padding:2px 1px 6px}.finder-phase-rail::-webkit-scrollbar{display:none}.finder-phase{display:flex;align-items:center;gap:6px;flex:0 0 auto;padding:6px 9px;border:1px solid var(--border);border-radius:999px;background:rgba(15,23,42,.48)}.finder-phase.done{border-color:rgba(34,197,94,.5)}.finder-phase.active{border-color:rgba(56,189,248,.6);box-shadow:0 0 16px rgba(56,189,248,.12)}.finder-phase.pending{opacity:.55}.finder-phase-n{display:grid;place-items:center;width:20px;height:20px;border-radius:50%;background:rgba(56,189,248,.14);color:#bae6fd;font-size:9px;font-weight:800}.finder-phase.done .finder-phase-n{background:rgba(34,197,94,.16);color:#bbf7d0}.finder-phase-name{font-size:9px;font-weight:700;letter-spacing:.06em;color:var(--text-primary)}.finder-phase-link{width:24px;height:1px;flex:0 0 24px;background:linear-gradient(90deg,rgba(56,189,248,.5),rgba(139,92,246,.5))}.finder-phase-link.done{background:rgba(34,197,94,.5)}.finder-phase-block{padding:10px 12px;border-left:2px solid rgba(56,189,248,.5);background:rgba(2,6,23,.22);border-radius:0 9px 9px 0;margin:8px 0}.finder-phase-block.prove{border-left-color:rgba(245,158,11,.5)}.finder-phase-block.continue{border-left-color:rgba(139,92,246,.5)}.finder-phase-block small{color:#7dd3fc;font-size:8px;font-weight:800;letter-spacing:.08em;text-transform:uppercase}.finder-phase-block.prove small{color:#fbbf24}.finder-phase-block.continue small{color:#c4b5fd}.finder-phase-block p{margin:5px 0 0;color:var(--text-secondary);font-size:10px;line-height:1.55}.finder-phase-next{display:flex;flex-wrap:wrap;gap:6px;margin-top:8px}.finder-phase-next button{border:1px solid var(--border);border-radius:8px;background:var(--bg-surface);color:var(--text-primary);cursor:pointer;padding:6px 10px;font-size:9px;font-weight:700}.finder-phase-next button:hover,.finder-phase-next button:focus-visible{outline:none;border-color:#7dd3fc;color:#e0f2fe;box-shadow:0 0 0 2px rgba(56,189,248,.12)}@media(prefers-reduced-motion:reduce){.finder-prompt-btn{animation:none;box-shadow:0 0 16px rgba(56,189,248,.45)}}@media(max-width:760px){.prompt-header-actions{grid-column:1/2;display:flex;flex-wrap:wrap;gap:8px;align-items:center}.prompt-header-actions .add-prompt-btn{min-height:40px}}@media(max-width:620px){.finder-options{grid-template-columns:1fr}}';document.head.appendChild(style);
var addButton=document.getElementById('addPromptBtn');if(addButton&&!document.getElementById('promptFinderBtn')){var actions=document.createElement('div');actions.className='prompt-header-actions';addButton.parentNode.insertBefore(actions,addButton);var finder=document.createElement('button');finder.className='add-prompt-btn finder-prompt-btn';finder.id='promptFinderBtn';finder.textContent='✦ Tutorial · Find My Prompt';finder.setAttribute('aria-label','Open the guided Prompt Kit tutorial and prompt recommendation questionnaire');finder.title='Answer four quick questions to find the best prompt';finder.onclick=function(){openPromptFinder(finder)};actions.appendChild(finder);actions.appendChild(addButton)}
})();
