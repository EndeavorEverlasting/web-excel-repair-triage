#!/usr/bin/env node
'use strict';
const fs=require('fs');
const vm=require('vm');
const cp=require('child_process');
const path=require('path');
const root=path.resolve(__dirname,'..');
const py=process.env.PYTHON || process.env.PYTHON3 || 'python';
const registry=JSON.parse(cp.execFileSync(py,['-c',"from scripts import build_prompt_kit_registry; import json; print(json.dumps(build_prompt_kit_registry.load_prompt_kit_registry()))"],{cwd:root,encoding:'utf8',maxBuffer:16*1024*1024}));
global.PROMPTS=registry;
global.window=global;
global.document={createElement:function(){return {}},head:{appendChild:function(){}},getElementById:function(){return null}};
global.filterPromptsForQuery=function(prompts,query){const q=String(query||'').toLowerCase();return prompts.filter(p=>[p.id,p.name,p.type,p.class,p.useWhen,p.sprintRole].concat(p.keywords||[]).join(' ').toLowerCase().includes(q)).slice(0,8)};
global.escapePromptHtml=function(value){return String(value)};
vm.runInThisContext(fs.readFileSync(path.join(root,'docs/prompt-kit-guided-recommendations.js'),'utf8'));
const outcomes=global.PROMPT_FINDER_OUTCOMES;
if(!Array.isArray(outcomes)||!outcomes.length) throw new Error('no PROMPT_FINDER_OUTCOMES exported');
const byId=new Map(registry.map(p=>[p.id,p]));
const expectedCritical=new Map([['create-prompt','P79'],['prioritize-repos-now','P23'],['implement','P07']]);
const contexts={startingPoint:['new-repo','in-repo','app-open'],problemKnown:['known-failure','known-task','repeated-stall','not-yet'],shape:['one-sprint','parallel','sequential','runtime-proof']};
const repeats=10;
let cases=0;
for(const outcome of outcomes){
  if(!byId.has(outcome.ownerId)) throw new Error(`missing owner ${outcome.ownerId} for ${outcome.id}`);
  const owner=byId.get(outcome.ownerId);
  if(!global.promptFinderRouteIsActionable(owner)) throw new Error(`non-actionable owner ${outcome.ownerId} for ${outcome.id}`);
  if(expectedCritical.has(outcome.id)&&expectedCritical.get(outcome.id)!==outcome.ownerId) throw new Error(`critical owner drift ${outcome.id}: ${outcome.ownerId}`);
  for(const startingPoint of contexts.startingPoint) for(const problemKnown of contexts.problemKnown) for(const shape of contexts.shape) for(let repeat=0;repeat<repeats;repeat++){
    const route=global.resolvePromptFinderOutcome({startingPoint,problemKnown,goal:outcome.id,shape});
    if(route.error) throw new Error(`${outcome.id}: ${route.error}`);
    if(route.prompt.id!==outcome.ownerId) throw new Error(`${outcome.id} routed ${route.prompt.id}, expected ${outcome.ownerId}`);
    cases++;
  }
}
const createRoute=global.resolvePromptFinderOutcome({startingPoint:'in-repo',problemKnown:'known-task',goal:'create-prompt',shape:'one-sprint'});
if(createRoute.error) throw new Error(createRoute.error);
if(createRoute.prompt.id!=='P79') throw new Error(`prompt creation must route P79, got ${createRoute.prompt.id}`);
if(createRoute.prompt.id==='P07') throw new Error('prompt creation silently collapsed to P07');
process.stdout.write(JSON.stringify({schema_version:'prompt-finder-outcome-validation/v1',status:'PASS',outcomes:outcomes.length,repeats,cases,critical:Object.fromEntries(expectedCritical)})+'\n');
