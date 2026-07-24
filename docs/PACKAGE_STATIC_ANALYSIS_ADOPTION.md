# Package Static Analysis Adoption

Web-Excel Repair Triage consumes sanitized package-analysis evidence. SysAdminSuite remains the canonical executable-analysis harness.

## Cross-repository boundary

| Responsibility | Owner |
|---|---|
| Hash local package files | SysAdminSuite |
| Inspect PE, OLE/MSI, ZIP, scripts, and configurations | SysAdminSuite |
| Create the isolated analysis virtual environment | SysAdminSuite |
| Define the result schema and proof flags | SysAdminSuite |
| Keep raw packages and evidence ignored | Operator and SysAdminSuite |
| Compare sanitized evidence and preserve durable lessons | Web-Excel Repair Triage |
| Execute an installer or validate application behavior | Separate authorized VM/runtime lane |

The triage repository must not copy the analyzer implementation. That would create two drifting authorities for safety, redaction, and proof classification.

## Canonical local command

From a SysAdminSuite checkout on Windows:

```powershell
.\scripts\Invoke-SasPackageStaticAnalysis.ps1 `
  -InputPath 'D:\PrivatePackages\Allscripts' `
  -CreateVenv
```

Optional deeper PE/OLE inspection may use an approved offline wheelhouse:

```powershell
.\scripts\Invoke-SasPackageStaticAnalysis.ps1 `
  -InputPath 'D:\PrivatePackages\Allscripts' `
  -CreateVenv `
  -OfflineWheelhouse 'D:\ApprovedWheelhouse'
```

The SysAdminSuite wrapper uses `pip --no-index --find-links`; it does not fall back to public package indexes.

## Evidence intake

Canonical outputs:

```text
package_analysis.json
package_analysis.txt
```

Before a sanitized fixture enters this repository, verify:

- `schema_version` is `sas-package-static-analysis/v1`;
- every execution, extraction, network, mutation, trust, and runtime proof flag is false;
- no absolute input path is emitted;
- endpoint-like values are fingerprints only;
- raw private strings are absent;
- package and client names are replaced when the fixture is public;
- the fixture remains useful for the exact regression under test.

## Suitable triage work

This repository may:

- compare two sanitized analysis results;
- classify changed hashes and package composition;
- render a leadership-safe or developer-safe report;
- preserve package-shape lessons;
- identify missing preflight, logging, runtime-acceptance, reboot, and rollback requirements;
- create sanitized regression fixtures.

It must not:

- execute, unpack, patch, or rewrite private installers;
- infer approved arguments from common conventions;
- contact discovered endpoints;
- claim that static indicators ran;
- claim that a package installs or works.

## Promotion boundary

Static evidence is the intake floor. A package enters VM testing only after its identity is complete and package-specific preflight, logging, runtime acceptance, reboot, and rollback requirements are defined. Physical-device acceptance remains a later gate.
