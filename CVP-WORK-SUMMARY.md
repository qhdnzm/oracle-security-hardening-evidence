# Work and system scope

## Application field: Describe the work and whose systems it covers

I conduct defensive vulnerability analysis and remediation on Oracle Linux infrastructure and Python/Node.js automation services that I own and administer. My work covers privilege boundaries, credential exposure, cloud-metadata and internal-network access, and controlled reproduction and verification of security fixes within those systems.

## Supporting evidence

[Security assessment and remediation report](https://github.com/qhdnzm/oracle-security-hardening-evidence/blob/main/SECURITY-REPORT.md)

The report documents July 2026 service isolation and credential-handling improvements, followed by an October 2026 network-containment implementation. It links sanitized application diffs, the deployed policy and test code, historical document fingerprints, and before/after measurements. The accepted follow-up blocked ten targeted internal connections across two service identities, preserved eight public-provider TLS checks and DNS, and retained the running media-service PIDs and restart counts.

## Intended defensive workflow

Use AI assistance to analyze interacting code paths and deployment trust boundaries, develop narrowly scoped fixes, and validate that those fixes enforce the intended restrictions without disrupting legitimate service behavior. Testing is confined to owned and administered infrastructure; ordinary public-provider connectivity checks do not expand that scope into third-party vulnerability testing.

## Author / maintainer

[hwangbo0718](https://github.com/qhdnzm)
