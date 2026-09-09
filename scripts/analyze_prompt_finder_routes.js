const fs = require('fs');
const vm = require('vm');
const os = require('os');
const { execSync } = require('child_process');

const ROOT = require('path').resolve(__dirname, '..');

// Load the CANONICAL combined registry (overrides + actionability policy + display
// order applied) by delegating to the registered Python builder. This keeps the
// analyzer's view identical to the deployed Prompt Kit site instead of measuring
// stale raw docs/prompts.json that the overrides (P02, P13) already replaced.
function loadPrompts() {
  const py = [
    'import json, sys',
    'sys.path.insert(0, "scripts")',
    'import build_prompt_kit_registry as r',
    'print(json.dumps(r.load_prompt_kit_registry()))',
  ].join('\n');
  const tmpPy = require('path').join(os.tmpdir(), 'analyze_routes_dump_' + process.pid + '.py');
  fs.writeFileSync(tmpPy, py);
  try {
    const out = execSync('python "' + tmpPy + '"', { cwd: ROOT, encoding: 'utf8', maxBuffer: 64 * 1024 * 1024 });
    return JSON.parse(out);
  } finally {
    try { fs.unlinkSync(tmpPy); } catch (e) {}
  }
}

// Load JS search engine
const jsSource = fs.readFileSync(require('path').join(ROOT, 'docs', 'prompt-kit.js'), 'utf8');
const guidedSource = fs.readFileSync(require('path').join(ROOT, 'docs', 'prompt-kit-guided-recommendations.js'), 'utf8');

const shared = { console, setTimeout: () => {}, clearTimeout: () => {}, navigator: { clipboard: null } };
const ctx = vm.createContext({
  globalThis: shared,
  window: shared,
  document: {
    getElementById: () => ({ addEventListener: () => {}, classList: { add: () => {}, remove: () => {}, contains: () => false, toggle: () => {} }, onclick: null, innerHTML: '', style: {}, querySelectorAll: () => [], querySelector: () => null, value: '', setAttribute: () => {}, focus: () => {}, textContent: '' }),
    querySelector: () => null,
    querySelectorAll: () => [],
    createElement: () => ({ classList: { add: () => {} }, setAttribute: () => {}, appendChild: () => {}, style: {}, querySelectorAll: () => [], querySelector: () => null, focus: () => {} }),
    body: { insertBefore: () => {}, appendChild: () => {}, contains: () => false, firstChild: null },
    head: { appendChild: () => {} },
    addEventListener: () => {},
  },
  PROMPTS: [],
  SYNONYMS: {},
  COLORS: {},
  SECTIONS: [],
  setTimeout: () => {},
  clearTimeout: () => {},
  navigator: { clipboard: null },
  REF: {},
  DOCTRINE: {},
});
vm.runInContext(jsSource, ctx);
vm.runInContext(guidedSource, ctx);

const PROMPTS = loadPrompts();
ctx.PROMPTS = PROMPTS;

// Extract PROMPT_FINDER_QUESTIONS from the guided source
const match = guidedSource.match(/var PROMPT_FINDER_QUESTIONS=(\[[\s\S]*?\]);/);
if (!match) {
  console.error('Could not find PROMPT_FINDER_QUESTIONS');
  process.exit(1);
}
const PROMPT_FINDER_QUESTIONS = eval(match[1]);

// Enumerate all combinations
function cartesianProduct(arrays) {
  return arrays.reduce((acc, curr) => {
    const res = [];
    for (const a of acc) {
      for (const b of curr) {
        res.push(a.concat([b]));
      }
    }
    return res;
  }, [[]]);
}

const questionIds = PROMPT_FINDER_QUESTIONS.map(q => q.id);
const optionIdsPerQuestion = PROMPT_FINDER_QUESTIONS.map(q => q.options.map(o => o.id));
const allCombinations = cartesianProduct(optionIdsPerQuestion);

const primaryCount = {};
const followOnCount = {};
const anyReach = {};
const anyReachSet = new Set();

for (const combo of allCombinations) {
  const answers = {};
  for (let i = 0; i < questionIds.length; i++) {
    answers[questionIds[i]] = combo[i];
  }
  const scoreFn = ctx.window.scorePromptFinderAnswers || ctx.globalThis.scorePromptFinderAnswers;
  const results = scoreFn(answers);
  if (results.length > 0) {
    const primary = results[0].prompt.id;
    primaryCount[primary] = (primaryCount[primary] || 0) + 1;
    anyReach[primary] = true;
    anyReachSet.add(primary);
  }
  for (let i = 1; i < results.length; i++) {
    const id = results[i].prompt.id;
    followOnCount[id] = (followOnCount[id] || 0) + 1;
    anyReach[id] = true;
    anyReachSet.add(id);
  }
}

// Determine nextStep ids referenced by a prompt.
function nextStepIds(prompt) {
  const text = String(prompt && prompt.nextStep || '');
  const ids = [];
  const seen = {};
  (text.match(/\bP\d{2,3}\b/gi) || []).forEach(raw => {
    const id = raw.toUpperCase();
    if (!seen[id] && PROMPTS.find(p => p.id === id)) {
      seen[id] = true;
      ids.push(id);
    }
  });
  return ids;
}

// Compute transitive nextStep reachability starting from the ENTRY_ELIGIBLE set.
// A prompt is only CONTINUATION_SPECIALIST if it is reachable by following
// nextStep chains from at least one entry-eligible prompt. This prevents
// self-referential gaming where an unreachable prompt merely mentions another
// unreachable prompt and both are miscounted as reachable.
const reachableFromNextStep = new Set(anyReachSet);
const bfsQueue = [...anyReachSet];
while (bfsQueue.length) {
  const current = bfsQueue.shift();
  const prompt = PROMPTS.find(p => p.id === current);
  if (!prompt) continue;
  for (const id of nextStepIds(prompt)) {
    if (!reachableFromNextStep.has(id)) {
      reachableFromNextStep.add(id);
      bfsQueue.push(id);
    }
  }
}

const unreachable = [];
const entryEligible = [];
const continuationSpecialist = [];

for (const p of PROMPTS) {
  const id = p.id;
  if (anyReachSet.has(id)) {
    entryEligible.push(id);
  } else if (reachableFromNextStep.has(id)) {
    continuationSpecialist.push(id);
  } else {
    unreachable.push(id);
  }
}

const total = PROMPTS.length;
console.log('TUTORIAL ROUTE COVERAGE REPORT');
console.log('============================');
console.log(`Total prompts: ${total}`);
console.log(`ENTRY_ELIGIBLE: ${entryEligible.length} (${(entryEligible.length/total*100).toFixed(1)}%)`);
console.log(`CONTINUATION_SPECIALIST: ${continuationSpecialist.length} (${(continuationSpecialist.length/total*100).toFixed(1)}%)`);
console.log(`UNREACHABLE: ${unreachable.length} (${(unreachable.length/total*100).toFixed(1)}%)`);
console.log('Methodology: canonical combined registry (overrides + actionability + display order);');
console.log('  CONTINUATION requires transitive nextStep reachability from an ENTRY_ELIGIBLE prompt.');

console.log('\nPRIMARY CONCENTRATION');
console.log('=====================');
const primaryEntries = Object.entries(primaryCount).sort((a, b) => b[1] - a[1]);
for (const [id, count] of primaryEntries) {
  const p = PROMPTS.find(p => p.id === id);
  console.log(`  ${id}: ${count} routes (${(count/allCombinations.length*100).toFixed(1)}%) - ${p ? p.name : '?'}`);
}

if (unreachable.length) {
  console.log('\nUNREACHABLE PROMPTS');
  console.log('=====================');
  for (const id of unreachable) {
    const p = PROMPTS.find(p => p.id === id);
    console.log(`  ${id}: ${p ? p.name : '?'}`);
  }
}

console.log('\nFOLLOW-ON CONCENTRATION');
console.log('========================');
const followEntries = Object.entries(followOnCount).sort((a, b) => b[1] - a[1]);
for (const [id, count] of followEntries) {
  const p = PROMPTS.find(p => p.id === id);
  console.log(`  ${id}: ${count} times - ${p ? p.name : '?'}`);
}

// Fail closed when unreachable prompts remain so this can gate CI as a real
// route-coverage contract rather than an advisory report.
if (unreachable.length) {
  process.exit(1);
}
