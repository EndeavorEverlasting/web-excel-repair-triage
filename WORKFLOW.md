# Workflow Specifications

## How to Pick Up a Task

1. **Read AGENTS.md** - Understand the agent operating contract
2. **Read CODEBASE_MAP.md** - Understand repository structure
3. **Check current state** - Run `git status` and `git log --oneline -5`
4. **Identify workflow direction** - Determine which workflow applies
5. **Select appropriate prompt** - Use the prompt kit to choose the right prompt

## Workflow Directions

### 1. Roster Log to Admin Sheet (High Priority)

**Trigger:** User needs admin-facing Project Team sheet for Friday billing

**Steps:**
1. Input: Roster log file
2. Validate input format
3. Run `scripts/roster_to_admin_submission.py`
4. Output: Clean admin-facing Project Team sheet
5. Validate output meets admin requirements

**Validation:**
- Output contains only admin-facing data
- No internal exception machinery exposed
- No confidence fields exposed
- No private notes exposed

### 2. Roster Log to Task Tracker (Medium Priority)

**Trigger:** User needs task tracker context for hours

**Steps:**
1. Input: Roster log file
2. Validate input format
3. Run `scripts/roster_to_task_context.py`
4. Output: Task tracker context
5. Validate output preserves contribution evidence

**Validation:**
- Staff, date, hours, project assignment mapped
- Override logic preserved
- Contribution evidence preserved

### 3. Task Tracker to Roster Log (Low Priority)

**Trigger:** User needs proposed roster updates from task tracker

**Steps:**
1. Input: Task tracker file
2. Validate input format
3. Run `scripts/task_tracker_to_roster_backfill.py`
4. Output: Proposed roster updates
5. **REVIEW REQUIRED** - Updates must be reviewed before mutation

**Validation:**
- Updates are proposed, not applied
- Rejected updates stay as tracker-only context
- No silent roster mutation

## How to Validate Before Committing

1. **Run existing tests:**
   ```bash
   pytest tests/
   ```

2. **Run specific test for changed area:**
   ```bash
   pytest tests/test_billing_rules.py
   ```

3. **Check for linting issues:**
   ```bash
   # If configured
   flake8 triage/
   black --check triage/
   ```

4. **Verify no secrets or credentials:**
   ```bash
   git diff --check
   ```

5. **Run harness completeness check:**
   ```bash
   python scripts/validate_harness.py
   ```

## How to Handle Failures

1. **Test failures:**
   - Read the test output carefully
   - Identify the root cause
   - Fix the issue, not the test
   - Re-run tests to verify

2. **Validation failures:**
   - Check input data format
   - Verify configuration
   - Check for missing dependencies

3. **Build failures:**
   - Check `requirements.txt` for missing packages
   - Verify Python version compatibility
   - Check for syntax errors

## How to Hand Off to the Next Agent or Chat

1. **Commit your changes:**
   ```bash
   git add <changed files>
   git commit -m "feat: descriptive commit message"
   ```

2. **Push if appropriate:**
   ```bash
   git push origin <branch>
   ```

3. **Document what you did:**
   - Files changed
   - Validation results
   - Any skipped checks
   - Remaining blockers

4. **Provide next command:**
   - Exact command to continue
   - Or "None" if work is complete

5. **Use P12 (Final Handoff Compressor) if needed:**
   - Compress context for next agent
   - Include exact state, gaps, and next command

## Error Recovery

### Interrupted Run
- Check `git status` for uncommitted changes
- Check `git stash` for stashed work
- Review recent commits with `git log --oneline -10`
- Use P27 (GNHF Interrupted Run Recovery) if needed

### Failed Validation
- Identify the failing test or validator
- Read the error message carefully
- Fix the root cause, not the symptom
- Re-run validation

### Merge Conflicts
- Identify conflicting files
- Resolve conflicts manually
- Test after resolution
- Commit the merge
