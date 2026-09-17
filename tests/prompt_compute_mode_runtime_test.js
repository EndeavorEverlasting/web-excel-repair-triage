'use strict';

const assert = require('assert');
const computeMode = require('../docs/prompt-kit-compute-mode.js');

function makeStorage() {
  const values = new Map();
  return {
    getItem(key) { return values.has(key) ? values.get(key) : null; },
    setItem(key, value) { values.set(key, String(value)); },
  };
}

function makeRoot() {
  return {
    localStorage: makeStorage(),
    PROMPT_KIT_COMPUTE_MODE_MANIFEST: {
      schema_version: 'prompt-compute-mode-product/v1',
      product_default: 'exhaustive',
      profile_precedence: [
        'explicit_run_override',
        'prompt_override',
        'user_default',
        'product_default',
      ],
      eligible_actionability_policy: 'actionable-next-command/v1',
      legacy_exhaustive_section: {
        start_marker: 'EXHAUSTIVE AVAILABLE COMPUTE RULE',
        end_marker: 'NON-PROGRESS / QUIESCENCE CONTRACT',
      },
      profiles: {
        exhaustive: { overlay: 'COMPILED EXECUTION PROFILE\nExecution profile: exhaustive\n' },
        efficient: { overlay: 'COMPILED EXECUTION PROFILE\nExecution profile: efficient\n' },
      },
    },
  };
}

function operationalPrompt() {
  return {
    id: 'P07',
    actionabilityPolicy: 'actionable-next-command/v1',
    copyContent: [
      'BASE CONTRACT',
      '',
      'EXHAUSTIVE AVAILABLE COMPUTE RULE',
      '- exhaustive-only behavior',
      '',
      'NON-PROGRESS / QUIESCENCE CONTRACT',
      '- preserve quiescence',
      '',
      'TAIL CONTRACT',
    ].join('\n'),
  };
}

(function testPrecedence() {
  const root = makeRoot();
  assert.deepStrictEqual(computeMode.resolve(root, 'P07'), {
    profile: 'exhaustive',
    resolved_from: 'product_default',
    precedence: ['explicit_run_override', 'prompt_override', 'user_default', 'product_default'],
  });

  computeMode.setUserDefault(root, 'efficient');
  assert.strictEqual(computeMode.resolve(root, 'P07').profile, 'efficient');
  assert.strictEqual(computeMode.resolve(root, 'P07').resolved_from, 'user_default');

  computeMode.setPromptOverride(root, 'P07', 'exhaustive');
  assert.strictEqual(computeMode.resolve(root, 'P07').profile, 'exhaustive');
  assert.strictEqual(computeMode.resolve(root, 'P07').resolved_from, 'prompt_override');

  const run = computeMode.resolve(root, 'P07', 'efficient');
  assert.strictEqual(run.profile, 'efficient');
  assert.strictEqual(run.resolved_from, 'explicit_run_override');
})();

(function testEffectivePromptComposition() {
  const root = makeRoot();
  const prompt = operationalPrompt();

  const exhaustive = computeMode.effectivePrompt(root, prompt, 'exhaustive');
  assert.ok(exhaustive.includes('EXHAUSTIVE AVAILABLE COMPUTE RULE'));
  assert.ok(exhaustive.includes('exhaustive-only behavior'));
  assert.ok(exhaustive.includes('NON-PROGRESS / QUIESCENCE CONTRACT'));
  assert.ok(exhaustive.includes('Execution profile: exhaustive'));

  const efficient = computeMode.effectivePrompt(root, prompt, 'efficient');
  assert.ok(!efficient.includes('EXHAUSTIVE AVAILABLE COMPUTE RULE'));
  assert.ok(!efficient.includes('exhaustive-only behavior'));
  assert.ok(efficient.includes('BASE CONTRACT'));
  assert.ok(efficient.includes('NON-PROGRESS / QUIESCENCE CONTRACT'));
  assert.ok(efficient.includes('TAIL CONTRACT'));
  assert.ok(efficient.includes('Execution profile: efficient'));
})();

(function testContentOnlyPromptRemainsCanonical() {
  const root = makeRoot();
  const prompt = {
    id: 'P999',
    actionabilityPolicy: 'not-applicable:content-only',
    copyContent: 'CONTENT ONLY',
  };
  assert.strictEqual(computeMode.effectivePrompt(root, prompt, 'efficient'), 'CONTENT ONLY');
})();

console.log('prompt_compute_mode_runtime_test: PASS');
