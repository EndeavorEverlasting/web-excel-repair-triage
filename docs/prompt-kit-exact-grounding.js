'use strict';

const crypto = require('crypto');
const fs = require('fs');
const path = require('path');
const {PromptKitProgramError, buildCommandKernelProgram} = require('./prompt-kit-program-prototype.js');

const DEFAULT_CONTRACT_PATH = path.join(__dirname, '..', 'harness', 'exact-grounding', 'agent-command-boundary.v1.json');
const PASS = 'GROUNDED_PASS';
const BLOCK_OUTCOMES = new Set(['UNSOURCED_BLOCK', 'CONTRADICTION_BLOCK', 'SCHEMA_MISMATCH', 'GROUNDING_FAILURE']);

function stable(value) {
  if (Array.isArray(value)) return value.map(stable);
  if (value && typeof value === 'object') return Object.fromEntries(Object.keys(value).sort().map(key => [key, stable(value[key])]));
  return value;
}
function digest(value) { return crypto.createHash('sha256').update(JSON.stringify(stable(value))).digest('hex'); }
function exactKeys(value, expected) {
  if (!value || typeof value !== 'object' || Array.isArray(value)) return false;
  return JSON.stringify(Object.keys(value).sort()) === JSON.stringify([...expected].sort());
}
function sameStringSet(value, expected) {
  return Array.isArray(value)
    && value.length === expected.length
    && value.every(item => typeof item === 'string' && item.trim())
    && new Set(value).size === value.length
    && JSON.stringify([...value].sort()) === JSON.stringify([...expected].sort());
}
function fail(status, reason, details = {}) { return {status, reason, details}; }

class CommandKernelGroundingSource {
  constructor({kernel, catalog, contractPath = DEFAULT_CONTRACT_PATH, contractLoader = null}) {
    this.kernel = kernel; this.catalog = catalog; this.contractPath = contractPath; this.contractLoader = contractLoader;
  }
  loadContract() {
    let contract;
    try { contract = this.contractLoader ? this.contractLoader() : JSON.parse(fs.readFileSync(this.contractPath, 'utf8')); }
    catch (error) { throw new PromptKitProgramError('GROUNDING_FAILURE', 'Grounding contract could not be loaded.', {cause: String(error && error.message || error)}); }
    const required = ['schema_version','packet_schema_version','proposal_schema_version','source_id','required_proposal_fields','required_command_fields','required_grounding_fields','exact_fields','outcomes','execution_authority','model_authority','proof_ceiling'];
    if (!exactKeys(contract, required)) throw new PromptKitProgramError('GROUNDING_FAILURE', 'Grounding contract shape is malformed.');
    if (contract.schema_version !== 'prompt-kit-agent-grounding-contract/v1') throw new PromptKitProgramError('GROUNDING_FAILURE', 'Unsupported grounding contract version.');
    if (![contract.packet_schema_version, contract.proposal_schema_version, contract.source_id, contract.proof_ceiling].every(value => typeof value === 'string' && value.trim())) throw new PromptKitProgramError('GROUNDING_FAILURE', 'Grounding contract identities must be non-empty strings.');
    if (!sameStringSet(contract.required_proposal_fields, ['schemaVersion', 'command', 'grounding'])) throw new PromptKitProgramError('GROUNDING_FAILURE', 'Grounding proposal field contract drifted.');
    if (!sameStringSet(contract.required_command_fields, ['type', 'promptId', 'source'])) throw new PromptKitProgramError('GROUNDING_FAILURE', 'Grounding command field contract drifted.');
    if (!sameStringSet(contract.required_grounding_fields, ['sourceId', 'sourceVersion', 'attributions'])) throw new PromptKitProgramError('GROUNDING_FAILURE', 'Grounding provenance field contract drifted.');
    if (!sameStringSet(contract.outcomes, [PASS, ...BLOCK_OUTCOMES])) throw new PromptKitProgramError('GROUNDING_FAILURE', 'Grounding outcome contract drifted.');
    if (contract.execution_authority !== 'host_command_kernel' || contract.model_authority !== 'proposal_only') throw new PromptKitProgramError('GROUNDING_FAILURE', 'Grounding authority boundary drifted.');
    if (!contract.exact_fields || !exactKeys(contract.exact_fields, contract.required_command_fields)) throw new PromptKitProgramError('GROUNDING_FAILURE', 'Exact-field authority map does not match command fields.');
    for (const field of contract.required_command_fields) {
      const spec = contract.exact_fields[field];
      const requiredSpecKeys = field === 'source' ? ['authority', 'source_key', 'constraint', 'allowed'] : ['authority', 'source_key', 'constraint'];
      if (!exactKeys(spec, requiredSpecKeys)) throw new PromptKitProgramError('GROUNDING_FAILURE', `Exact-field authority record is malformed: ${field}.`);
      for (const key of ['authority', 'source_key', 'constraint']) if (typeof spec[key] !== 'string' || !spec[key].trim()) throw new PromptKitProgramError('GROUNDING_FAILURE', `Exact-field authority value is malformed: ${field}.${key}.`);
    }
    const allowed = contract.exact_fields.source.allowed;
    if (!sameStringSet(allowed, ['agent'])) throw new PromptKitProgramError('GROUNDING_FAILURE', 'Agent boundary allowed-source enum is malformed.');
    return contract;
  }
  currentStructure(contract) {
    if (!(this.kernel && this.kernel.handlers instanceof Map) || !(this.catalog && this.catalog.byId instanceof Map)) throw new PromptKitProgramError('GROUNDING_FAILURE', 'Live command/catalog structure is unavailable.');
    const commandTypes = [...this.kernel.handlers.keys()].sort();
    const promptIds = [...this.catalog.byId.keys()].sort();
    if (!commandTypes.length || !promptIds.length) throw new PromptKitProgramError('GROUNDING_FAILURE', 'Live command/catalog structure is empty.');
    return {
      contractSchemaVersion: contract.schema_version,
      packetSchemaVersion: contract.packet_schema_version,
      proposalSchemaVersion: contract.proposal_schema_version,
      commandTypes,
      promptIds,
      allowedSources: [...contract.exact_fields.source.allowed].sort()
    };
  }
  buildPacket(operationName) {
    const contract = this.loadContract();
    const structure = this.currentStructure(contract);
    if (typeof operationName !== 'string' || !structure.commandTypes.includes(operationName)) return fail('UNSOURCED_BLOCK', 'Operation is absent from the live command registry.', {proposedOperation: operationName, sourceKey: contract.exact_fields.type.source_key});
    const packet = {
      schemaVersion: contract.packet_schema_version,
      proposalSchemaVersion: contract.proposal_schema_version,
      source: {id: contract.source_id, version: digest(structure), contractSchemaVersion: contract.schema_version, contractPath: path.relative(path.join(__dirname, '..'), this.contractPath).replaceAll('\\', '/')},
      operation: {name: operationName, sourceKey: `${contract.exact_fields.type.source_key}.${operationName}`},
      fields: {
        type: {required: true, const: operationName, sourceKey: `${contract.exact_fields.type.source_key}.${operationName}`},
        promptId: {required: true, enum: structure.promptIds, sourceKey: contract.exact_fields.promptId.source_key},
        source: {required: true, enum: structure.allowedSources, sourceKey: contract.exact_fields.source.source_key}
      }
    };
    return {status: PASS, packet, packetDigest: digest(packet)};
  }
}

class AgentCommandGroundingInterceptor {
  constructor({kernel, catalog, trace = [], groundingSource = null}) {
    this.kernel = kernel; this.catalog = catalog; this.trace = trace;
    this.source = groundingSource || new CommandKernelGroundingSource({kernel, catalog});
  }
  prepare(operationName) {
    try {
      const result = this.source.buildPacket(operationName);
      this.trace.push({layer: 'grounding', event: 'packet_prepared', operationName, status: result.status});
      return result;
    } catch (error) {
      const normalized = error instanceof PromptKitProgramError ? error : new PromptKitProgramError('GROUNDING_FAILURE', String(error && error.message || error));
      return fail('GROUNDING_FAILURE', normalized.message, normalized.details || {});
    }
  }
  validate(proposal) {
    let contract;
    try { contract = this.source.loadContract(); }
    catch (error) { return fail('GROUNDING_FAILURE', error.message, error.details || {}); }
    if (!exactKeys(proposal, contract.required_proposal_fields)) return fail('SCHEMA_MISMATCH', 'Proposal must contain exactly schemaVersion, command, and grounding.');
    if (proposal.schemaVersion !== contract.proposal_schema_version) return fail('SCHEMA_MISMATCH', 'Proposal schema version is not current.');
    if (!exactKeys(proposal.command, contract.required_command_fields)) return fail('SCHEMA_MISMATCH', 'Command fields do not match the protected boundary schema.');
    if (!proposal.grounding || typeof proposal.grounding !== 'object') return fail('UNSOURCED_BLOCK', 'Critical command fields lack grounding provenance.');
    if (!exactKeys(proposal.grounding, contract.required_grounding_fields)) return fail('SCHEMA_MISMATCH', 'Grounding metadata shape is malformed.');
    const packetResult = this.prepare(proposal.command.type);
    if (packetResult.status !== PASS) return packetResult;
    const packet = packetResult.packet;
    if (proposal.grounding.sourceId !== packet.source.id) return fail('UNSOURCED_BLOCK', 'Grounding source identity does not match the live authority.', {expected: packet.source.id, observed: proposal.grounding.sourceId});
    if (proposal.grounding.sourceVersion !== packet.source.version) return fail('GROUNDING_FAILURE', 'Grounding source version is stale; refresh before execution.', {expected: packet.source.version, observed: proposal.grounding.sourceVersion, refreshRequired: true});
    if (!exactKeys(proposal.grounding.attributions, contract.required_command_fields)) return fail('UNSOURCED_BLOCK', 'Every exactness-critical field must have one resolvable source key.');
    for (const field of contract.required_command_fields) {
      const expectedKey = packet.fields[field].sourceKey;
      if (proposal.grounding.attributions[field] !== expectedKey) return fail('UNSOURCED_BLOCK', `Field ${field} is not attributed to its current authority.`, {field, expected: expectedKey, observed: proposal.grounding.attributions[field]});
    }
    if (proposal.command.type !== packet.fields.type.const) return fail('CONTRADICTION_BLOCK', 'Command type contradicts the grounded operation.');
    for (const field of ['promptId', 'source']) if (!packet.fields[field].enum.includes(proposal.command[field])) return fail('CONTRADICTION_BLOCK', `Field ${field} contradicts current grounded structure.`, {field, observed: proposal.command[field], allowed: packet.fields[field].enum});
    const verdict = {status: PASS, sourceId: packet.source.id, sourceVersion: packet.source.version, packetDigest: packetResult.packetDigest};
    this.trace.push({layer: 'grounding', event: 'proposal_validated', status: PASS, operationName: proposal.command.type});
    return verdict;
  }
  async execute(proposal) {
    const first = this.validate(proposal);
    if (first.status !== PASS) {
      this.trace.push({layer: 'grounding', event: 'execution_blocked', status: first.status, reason: first.reason});
      throw new PromptKitProgramError(first.status, first.reason, first.details || {});
    }
    const second = this.validate(proposal);
    if (second.status !== PASS || second.packetDigest !== first.packetDigest || second.sourceVersion !== first.sourceVersion) {
      const failure = second.status === PASS ? fail('GROUNDING_FAILURE', 'Grounding changed during adversarial consistency pass.', {refreshRequired: true}) : second;
      this.trace.push({layer: 'grounding', event: 'execution_blocked', status: failure.status, reason: failure.reason});
      throw new PromptKitProgramError(failure.status, failure.reason, failure.details || {});
    }
    this.trace.push({layer: 'grounding', event: 'execution_authorized', operationName: proposal.command.type, sourceVersion: second.sourceVersion});
    const result = await this.kernel.execute(proposal.command);
    return {status: PASS, sourceVersion: second.sourceVersion, result};
  }
}

function proposalFromPacket(packet, command) {
  return {schemaVersion: packet.proposalSchemaVersion, command: {...command}, grounding: {sourceId: packet.source.id, sourceVersion: packet.source.version, attributions: Object.fromEntries(Object.entries(packet.fields).map(([field, spec]) => [field, spec.sourceKey]))}};
}
async function expectBlocked(expectedStatus, fn) {
  try { await fn(); } catch (error) { if (!(error instanceof PromptKitProgramError) || error.code !== expectedStatus) throw error; return error; }
  throw new Error(`Expected ${expectedStatus}`);
}

async function runSelfTest() {
  const checks = [];
  const freshProgram = () => buildCommandKernelProgram();
  {
    const program = freshProgram(); const gate = new AgentCommandGroundingInterceptor({kernel: program.kernel, catalog: program.catalog, trace: program.trace});
    const prepared = gate.prepare('COPY_REVEAL_PROMPT'); if (prepared.status !== PASS) throw new Error('Expected grounding packet');
    const proposal = proposalFromPacket(prepared.packet, {type: 'COPY_REVEAL_PROMPT', promptId: 'P07', source: 'agent'});
    const result = await gate.execute(proposal); if (result.status !== PASS || program.clipboard.writes.length !== 1) throw new Error('Valid grounded command did not execute exactly once');
    const starts = program.trace.filter(item => item.layer === 'kernel' && item.event === 'command_started'); if (starts.length !== 1) throw new Error('Existing side-effect path executed more than once');
    const validations = program.trace.filter(item => item.layer === 'grounding' && item.event === 'proposal_validated'); if (validations.length !== 2) throw new Error('Adversarial consistency pass did not run twice');
    checks.push({case: 'valid_exact_signature', outcome: PASS, sideEffectExecutions: 1, consistencyPasses: 2});
  }
  {
    const program = freshProgram(); const gate = new AgentCommandGroundingInterceptor({kernel: program.kernel, catalog: program.catalog, trace: program.trace}); const prepared = gate.prepare('COPY_REVEAL_PROMPT');
    const proposal = proposalFromPacket(prepared.packet, {type: 'COPY_REVEAL_PROMPT', promptId: 'P999', source: 'agent'}); await expectBlocked('CONTRADICTION_BLOCK', () => gate.execute(proposal));
    if (program.clipboard.writes.length !== 0) throw new Error('Blocked hallucinated identifier reached side effect'); checks.push({case: 'hallucinated_identifier', outcome: 'CONTRADICTION_BLOCK', sideEffectExecutions: 0});
  }
  {
    const program = freshProgram(); const gate = new AgentCommandGroundingInterceptor({kernel: program.kernel, catalog: program.catalog, trace: program.trace}); const prepared = gate.prepare('COPY_REVEAL_PROMPT');
    const proposal = proposalFromPacket(prepared.packet, {type: 'COPY_REVEAL_PROMPT', promptId: 'P07', source: 'card'}); await expectBlocked('CONTRADICTION_BLOCK', () => gate.execute(proposal)); checks.push({case: 'in_context_constraint_contradiction', outcome: 'CONTRADICTION_BLOCK'});
  }
  {
    const program = freshProgram(); const gate = new AgentCommandGroundingInterceptor({kernel: program.kernel, catalog: program.catalog, trace: program.trace});
    const proposal = {schemaVersion: 'prompt-kit-grounded-command/v1', command: {type: 'NOT_A_COMMAND', promptId: 'P07', source: 'agent'}, grounding: {sourceId: 'prompt-kit-command-kernel-live-structure', sourceVersion: 'unknown', attributions: {type: 'kernel.handlers.NOT_A_COMMAND', promptId: 'catalog.byId', source: 'boundary.allowedSources'}}};
    await expectBlocked('UNSOURCED_BLOCK', () => gate.execute(proposal)); checks.push({case: 'hallucinated_operation', outcome: 'UNSOURCED_BLOCK'});
  }
  {
    const program = freshProgram(); const gate = new AgentCommandGroundingInterceptor({kernel: program.kernel, catalog: program.catalog, trace: program.trace}); const prepared = gate.prepare('COPY_REVEAL_PROMPT');
    const proposal = proposalFromPacket(prepared.packet, {type: 'COPY_REVEAL_PROMPT', promptId: 'P07', source: 'agent'}); delete proposal.grounding.attributions.promptId;
    await expectBlocked('UNSOURCED_BLOCK', () => gate.execute(proposal)); checks.push({case: 'missing_provenance', outcome: 'UNSOURCED_BLOCK'});
  }
  {
    const program = freshProgram(); const gate = new AgentCommandGroundingInterceptor({kernel: program.kernel, catalog: program.catalog, trace: program.trace}); const prepared = gate.prepare('COPY_REVEAL_PROMPT');
    const proposal = proposalFromPacket(prepared.packet, {type: 'COPY_REVEAL_PROMPT', promptId: 'P07', source: 'agent'}); proposal.command.extra = 'model-invented';
    await expectBlocked('SCHEMA_MISMATCH', () => gate.execute(proposal)); checks.push({case: 'schema_mismatch', outcome: 'SCHEMA_MISMATCH'});
  }
  {
    const program = freshProgram(); const gate = new AgentCommandGroundingInterceptor({kernel: program.kernel, catalog: program.catalog, trace: program.trace}); const prepared = gate.prepare('COPY_REVEAL_PROMPT');
    const proposal = proposalFromPacket(prepared.packet, {type: 'COPY_REVEAL_PROMPT', promptId: 'P07', source: 'agent'}); program.catalog.byId.set('PNEW', Object.freeze({id: 'PNEW', copyContent: 'new'}));
    await expectBlocked('GROUNDING_FAILURE', () => gate.execute(proposal)); const refreshed = gate.prepare('COPY_REVEAL_PROMPT'); const repaired = proposalFromPacket(refreshed.packet, {type: 'COPY_REVEAL_PROMPT', promptId: 'P07', source: 'agent'}); await gate.execute(repaired);
    if (program.clipboard.writes.length !== 1) throw new Error('Refreshed grounded command did not execute exactly once'); checks.push({case: 'stale_structure_refresh', outcome: 'GROUNDING_FAILURE_THEN_GROUNDED_PASS', sideEffectExecutions: 1});
  }
  {
    const program = freshProgram(); const badSource = new CommandKernelGroundingSource({kernel: program.kernel, catalog: program.catalog, contractLoader: () => ({schema_version: 'broken'})}); const gate = new AgentCommandGroundingInterceptor({kernel: program.kernel, catalog: program.catalog, trace: program.trace, groundingSource: badSource});
    const prepared = gate.prepare('COPY_REVEAL_PROMPT'); if (prepared.status !== 'GROUNDING_FAILURE') throw new Error('Malformed grounding contract must fail closed'); checks.push({case: 'malformed_grounding_source', outcome: 'GROUNDING_FAILURE'});
  }
  {
    const program = freshProgram(); const malformed = JSON.parse(fs.readFileSync(DEFAULT_CONTRACT_PATH, 'utf8')); malformed.exact_fields.source.allowed = 'agent';
    const badSource = new CommandKernelGroundingSource({kernel: program.kernel, catalog: program.catalog, contractLoader: () => malformed}); const gate = new AgentCommandGroundingInterceptor({kernel: program.kernel, catalog: program.catalog, trace: program.trace, groundingSource: badSource});
    const prepared = gate.prepare('COPY_REVEAL_PROMPT'); if (prepared.status !== 'GROUNDING_FAILURE') throw new Error('Malformed nested source enum must fail closed'); checks.push({case: 'malformed_nested_contract', outcome: 'GROUNDING_FAILURE'});
  }
  return {status: 'PASS', boundary: 'agent proposal -> JIT grounding -> deterministic host interceptor -> existing CommandKernel side effects', exactnessCriticalFields: ['type','promptId','source'], outcomes: [PASS, ...BLOCK_OUTCOMES], checks, proofCeiling: 'Repository prototype proof for current Prompt Kit command/catalog structure; no claim of arbitrary external API or production browser interception.'};
}

if (require.main === module) runSelfTest().then(result => process.stdout.write(JSON.stringify(result, null, 2) + '\n')).catch(error => { process.stderr.write(`${error && error.stack || error}\n`); process.exitCode = 1; });
module.exports = {PASS, BLOCK_OUTCOMES, CommandKernelGroundingSource, AgentCommandGroundingInterceptor, proposalFromPacket, runSelfTest};
