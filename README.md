# Securing a cloud media pipeline

**Least privilege · Secret handling · Internal-network containment · Controlled verification**

Original remediation: **July 2026** · Evidence publication and follow-up: **October 2026**

This repository records the reconstruction of a July 2026 security remediation, its reconciliation with a replacement Oracle Linux server in October 2026, and follow-up defense-in-depth work. All dates and operational times are **Asia/Seoul (KST, UTC+9)**.

The original work separated external media and messaging integrations from the operator's privileged trust domain. An October follow-up added an independent outbound network boundary and tested it on the owner-administered Oracle Linux host.

## Measured result of the October follow-up

| Boundary / compatibility check | Before | After |
| --- | --- | --- |
| Media identities → metadata HTTP port | TCP reachable | Denied |
| Media identities → IPv4 and IPv6 loopback | TCP reachable | Denied |
| Media identities → host private/tailnet SSH listener | TCP reachable, no authentication attempted | Denied |
| Trusted DNS | Working | Working; port 53 exception only |
| Public YouTube, Discord, Chzzk and X fronts | Certificate-verified TLS works | Certificate-verified TLS works |
| Operator-account control probes | Working | Unchanged |
| Existing uploader and crawler processes | Running | Same PIDs and restart counts |

**10/10 targeted internal connection attempts denied across two media identities; 8/8 media-identity public TLS checks passed.** These are bounded connectivity checks, not real uploads, webhook deliveries, exploitation of a third-party system, or a comprehensive security certification. [Read the method and limitations](VERIFICATION.md).

## What the original problem was

An internet-facing integration does not need to accept inbound HTTP connections to create a server trust-boundary risk. A Discord command bot, a media downloader, and an uploader process external data. If they run as the same operator account as sensitive workloads, a compromised dependency or unsafe input handler can inherit access to those workloads and possibly passwordless administrative privileges.

The recovered July documents describe precisely this shared-account problem. They describe hardening, not a confirmed intrusion. They do **not** establish that possession of a Discord notification webhook alone allowed arbitrary server commands, or that a specific SSRF exploit was reproduced.

## Evidence map

| Document | Purpose |
| --- | --- |
| [HISTORY.md](HISTORY.md) | Original risk, July controls, historical results, and evidence limitations |
| [CODE-BEFORE-AFTER.md](CODE-BEFORE-AFTER.md) | Sanitized application diffs, design rationale and attack-path diagrams |
| [CURRENT-ASSESSMENT.md](CURRENT-ASSESSMENT.md) | October observations, migration drift, and prioritized additional risks |
| [CONTROL-DESIGN.md](CONTROL-DESIGN.md) | Implemented network control, compatibility boundaries, rollback and acceptance criteria |
| [VERIFICATION.md](VERIFICATION.md) | Before/after test results, deployment evidence, and rollout corrections |
| [EVIDENCE-PROVENANCE.json](EVIDENCE-PROVENANCE.json) | SHA-256 fingerprints of the locally retained historical documents |
| [media_egress_guard.py](media_egress_guard.py) | Exact deployed policy renderer and scoped lifecycle helper |
| [probe_media_egress.py](probe_media_egress.py) | Reproducible, bounded acceptance probe |

## Status vocabulary

- **HISTORICALLY_REPORTED_DEPLOYED:** a retained contemporary report records deployment; this is not a new observation of the retired server.
- **OBSERVED:** a current read-only inspection returned the stated value.
- **PLANNED:** proposed control; no current deployment claim.
- **DEPLOYED:** the exact new control was installed and the stated acceptance evidence exists.
- **UNVERIFIED:** no sufficient direct observation or test exists.

## Publication boundaries

This is a curated evidence package, not a copy of the production directory or the parent research repository. No credentials, browser state, real webhook URLs, host addresses, cloud resource identifiers, private media identifiers, trading records, or full runtime logs are included. The existing local-only repository is not connected to GitHub.

Document hashes bind these summaries to retained originals. They do not prove an independent timestamp, the absence of an intrusion, or comprehensive security. The original material remains local because it contains operational details outside the scope of publication.

## Verification boundaries

The user authorized bounded tests on the current host. Acceptance tests may inspect service properties, account boundaries, firewall enforcement, DNS, and anonymous HTTPS reachability. They must not send notification webhooks, create or modify orders, submit YouTube uploads, inspect secret stores, or invoke an unrelated workload. Boot persistence must be distinguished from an actual reboot test.

## System ownership and purpose

This case study covers infrastructure operated and administered by the repository owner. The purpose is defensive review, remediation and verification of the owner's own service integrations. Public provider checks are ordinary anonymous TLS connections; they are not vulnerability assessments of those providers.
