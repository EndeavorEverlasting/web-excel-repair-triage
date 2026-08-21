-- Lua command inspection policy.
-- The host owns result validation, blocking, retries, cleanup, execution, and handoff.

local RESULT_SCHEMA = "lua-command-safety-result/v1"
local CHECKER_VERSION = "1.0.0"
local MARKER_SEPARATOR = string.char(31)

local function line_for(command, needle)
  local target = string.lower(needle)
  local line_no = 1
  for line in string.gmatch(command .. "\n", "(.-)\n") do
    if string.find(string.lower(line), target, 1, true) then return line_no end
    line_no = line_no + 1
  end
  return 1
end

local function add(findings, rule_id, severity, category, shell_value, command, evidence, hint, retryable)
  local line_no = line_for(command, evidence)
  table.insert(findings, {
    rule_id = rule_id,
    severity = severity,
    category = category,
    shell_or_language = shell_value,
    location = { start_line = line_no, end_line = line_no },
    evidence = evidence,
    host_action = severity == "BLOCK" and "BLOCK_AND_REPAIR" or "PRESERVE_DIAGNOSTIC",
    remediation_hint = hint,
    retryable = retryable
  })
end

local function contains(text, needle)
  return string.find(string.lower(text), string.lower(needle), 1, true) ~= nil
end

local function split_lines(command)
  local result = {}
  for line in string.gmatch(command .. "\n", "(.-)\n") do table.insert(result, line) end
  return result
end

local function quote_state(command, shell_value)
  if contains(command, "@\"") and contains(command, "\"@") then return false end
  if contains(command, "@'") and contains(command, "'@") then return false end
  if shell_value == "bash" and contains(command, "<<") then return false end
  local single, double, escaped = false, false, false
  local index = 1
  while index <= #command do
    local ch = string.sub(command, index, index)
    if escaped then
      escaped = false
    elseif shell_value == "powershell" and ch == "`" then
      escaped = true
    elseif shell_value == "bash" and ch == "\\" and not single then
      escaped = true
    elseif ch == "'" and not double and shell_value ~= "cmd" then
      single = not single
    elseif ch == "\"" and not single then
      double = not double
    end
    index = index + 1
  end
  return single or double
end

local function split_markers(blob)
  local markers = {}
  if blob == nil or blob == "" then return markers end
  local start_pos = 1
  while true do
    local stop_pos = string.find(blob, MARKER_SEPARATOR, start_pos, true)
    if stop_pos == nil then
      table.insert(markers, string.sub(blob, start_pos)); break
    end
    table.insert(markers, string.sub(blob, start_pos, stop_pos - 1))
    start_pos = stop_pos + 1
  end
  return markers
end

local function inspect_wrong_shell(findings, command, shell_value, platform)
  local windows_profile = platform == "windows"
  local powershell_or_cmd = shell_value == "powershell" or shell_value == "cmd"
  if powershell_or_cmd and contains(command, "set -euo pipefail") then
    add(findings, "CS001_WRONG_SHELL_BASH_STRICT_MODE", "BLOCK", "wrong_shell", shell_value, command,
      "set -euo pipefail", "Use the selected Windows shell's native fail-fast and exit-code handling.", true)
  end
  if powershell_or_cmd and string.match(command, "[%a_][%w_]*%s*=%s*[\"']%${HOME}") then
    add(findings, "CS002_WRONG_SHELL_POSIX_ASSIGNMENT", "BLOCK", "wrong_shell", shell_value, command,
      "repo=\"${HOME}", "Use PowerShell variable assignment/Join-Path or CMD SET syntax for the selected shell.", true)
  end
  if windows_profile and contains(command, "mktemp") then
    add(findings, "CS003_PLATFORM_MKTEMP_ON_WINDOWS", "BLOCK", "platform_assumption", shell_value, command,
      "mktemp", "Use a Windows-native, repository-bounded workspace path or the canonical launcher.", true)
  end
  if powershell_or_cmd then
    for _, line in ipairs(split_lines(command)) do
      if string.match(string.lower(line), "^%s*test%s+") then
        add(findings, "CS004_WRONG_SHELL_TEST_BUILTIN", "BLOCK", "wrong_shell", shell_value, command,
          "test ", "Use an explicit PowerShell if/throw/exit check or CMD IF expression.", true)
        break
      end
    end
  end
  if windows_profile and contains(command, "/tmp/") then
    add(findings, "CS005_PLATFORM_POSIX_TEMP_PATH", "BLOCK", "platform_assumption", shell_value, command,
      "/tmp/", "Use a Windows-native bounded path selected by the host profile.", true)
  end
end

local function inspect_quotes(findings, command, shell_value)
  if quote_state(command, shell_value) then
    add(findings, "CS010_UNMATCHED_QUOTE", "BLOCK", "quoting", shell_value, command,
      "unmatched quote", "Repair quoting/escaping for the declared shell before handoff.", true)
  end
end

local function inspect_failure_propagation(findings, command, shell_value, required)
  if not required then return end
  if shell_value == "bash" and contains(command, "|| true") then
    add(findings, "CS020_SWALLOWED_BASH_FAILURE", "BLOCK", "failure_propagation", shell_value, command,
      "|| true", "Propagate the failing exit code or handle the expected failure explicitly.", true)
  end
  if shell_value == "powershell" and contains(command, "-erroraction silentlycontinue") then
    add(findings, "CS021_SWALLOWED_POWERSHELL_FAILURE", "BLOCK", "failure_propagation", shell_value, command,
      "-ErrorAction SilentlyContinue", "Use terminating error behavior or explicitly test and propagate the failure.", true)
  end
end

local function inspect_destructive(findings, command, shell_value)
  for _, line in ipairs(split_lines(command)) do
    local lower = string.lower(line)
    local trimmed = string.gsub(lower, "%s+$", "")
    if string.match(trimmed, "^%s*rm%s+%-[rf][rf]%s+/%s*$")
      or string.match(trimmed, "^%s*rm%s+%-r%s+%-f%s+/%s*$")
      or string.match(trimmed, "^%s*rm%s+%-f%s+%-r%s+/%s*$") then
      add(findings, "CS030_DESTRUCTIVE_ROOT_DELETE", "BLOCK", "destructive_scope", shell_value, command,
        "rm -rf /", "Replace root-wide deletion with an explicitly bounded repository/generated-artifact target.", false)
      return
    end
    if contains(lower, "remove-item") and contains(lower, "-recurse") and contains(lower, "-force")
      and string.match(trimmed, "[\"']?c:\\[\"']?%s*$") then
      add(findings, "CS030_DESTRUCTIVE_ROOT_DELETE", "BLOCK", "destructive_scope", shell_value, command,
        "Remove-Item ... C:\\", "Replace drive-root deletion with an explicitly bounded repository/generated-artifact target.", false)
      return
    end
    if contains(lower, "rd /s /q") and string.match(trimmed, "[\"']?c:\\[\"']?%s*$") then
      add(findings, "CS030_DESTRUCTIVE_ROOT_DELETE", "BLOCK", "destructive_scope", shell_value, command,
        "rd /s /q C:\\", "Replace drive-root deletion with an explicitly bounded target.", false)
      return
    end
  end
end

local function inspect_required_controls(findings, command, shell_value, required_launcher, markers_blob)
  if required_launcher ~= nil and required_launcher ~= "" and not contains(command, required_launcher) then
    add(findings, "CS040_REQUIRED_LAUNCHER_BYPASS", "BLOCK", "canonical_bypass", shell_value, command,
      "missing required launcher: " .. required_launcher,
      "Route through the canonical launcher required by the selected execution profile.", true)
  end
  for _, marker in ipairs(split_markers(markers_blob)) do
    if marker ~= "" and not contains(command, marker) then
      add(findings, "CS050_PARTIAL_REQUIRED_OPERATION", "BLOCK", "partial_operation", shell_value, command,
        "missing required operation marker: " .. marker,
        "Repair the snippet so it contains every operation-critical marker required by the host profile.", true)
      break
    end
  end
end

function inspect_command(command, shell_value, platform, required_launcher, markers_blob, failure_propagation_required)
  if type(command) ~= "string" or type(shell_value) ~= "string" or type(platform) ~= "string" then
    error("invalid host/Lua boundary type")
  end
  if type(required_launcher) ~= "string" or type(markers_blob) ~= "string"
    or type(failure_propagation_required) ~= "boolean" then
    error("invalid host/Lua policy boundary type")
  end
  local findings = {}
  inspect_wrong_shell(findings, command, shell_value, platform)
  inspect_quotes(findings, command, shell_value)
  inspect_failure_propagation(findings, command, shell_value, failure_propagation_required)
  inspect_destructive(findings, command, shell_value)
  inspect_required_controls(findings, command, shell_value, required_launcher, markers_blob)
  return { schema_version = RESULT_SCHEMA, checker_version = CHECKER_VERSION, findings = findings }
end
