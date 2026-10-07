# Current assessment — 2026-10-08

Status at baseline publication: **OBSERVED / REMEDIATION_PENDING**. Observations below were collected read-only around 02:03–02:10 KST. They are point-in-time facts, not a penetration test or incident-response conclusion.

## Controls retained

The uploader and crawler are active with separate service users and zero recorded restarts at observation. Both retain NoNewPrivileges, strict system protection, protected homes/devices/kernel/control groups, an empty capability bounding set, and a limited set of writable application/state/media directories. Neither account can traverse the operator home; sudo reports neither is permitted to run sudo.

The retired-host Discord command service is not installed on the replacement host. The media application directory is root-owned and not writable by its service account. The shared media directory is group-writable as required by the pipeline. The current uploader log directory has the intended service owner.

## Confirmed differences and constraints

| ID | Observation | Interpretation and current status |
| --- | --- | --- |
| H-01 | Effective SSH permits root public-key login, X11, TCP and agent forwarding; attempt/grace values differ from July hardening | Host-hardening drift confirmed. This does not prove a root key exists or that an unauthorized login occurred. Recovery-safe remediation required. |
| H-02 | rpcbind is active on TCP/UDP port 111 for IPv4 and IPv6 | Listener confirmed. The public host firewall does not list rpcbind as allowed. Internet reachability is not established. An active tracing dependency exists, so the old stop/mask script must not be blindly reused. |
| N-01 | The media units have no service-level IPAddressDeny policy | Application identity/filesystem isolation does not itself block internal-network destinations. Actual bounded positive/negative network tests are needed. |
| N-02 | DNS uses a cloud link-local resolver | A blanket block of all link-local traffic would disrupt DNS. A narrow destination-and-port DNS exception is required. |

## Additional plausible risks

These are threat-model findings with explicit prerequisites. They are not claims that an exploit was observed.

| ID | Risk and prerequisite | Existing mitigation / proposed response | Evidence limit |
| --- | --- | --- | --- |
| R-01 | Compromised downloader/uploader or unsafe URL handling connects to metadata, loopback, private LAN or tailnet endpoints | Add an independent per-service-account outbound destination guard with a trusted DNS-only exception | No malicious URL exploit or credential response requested |
| R-02 | Both workers can modify shared media; a compromised worker can plant symlinks or replace a file between path validation and opening | Separate privileged state is already outside the shared directory. A future immutable handoff/spool and descriptor-based regular-file processing would improve this boundary | Shared write access is confirmed; exfiltration or a race exploit is not reproduced |
| R-03 | A media decoder parses attacker-controlled files while running with uploader identity | Root-owned code, no capabilities and filesystem sandbox reduce blast radius; dedicated decoder isolation is a future stronger boundary | Decoder CVE inventory and hostile-media fuzzing not performed |
| R-04 | A writable serialized OAuth state file is loaded with Python pickle | Restrict ownership and isolate writers; migrate through an authorized authentication workflow to a data-only format if pursued | Source-review finding; no token file opened or copied. A compromised uploader already has access to its own OAuth capability |
| R-05 | Historically exposed secrets remain valid after relocation | Revoke/reissue through the owning provider when authorized; never infer rotation from filesystem hardening | No provider credential rotation audit or secret inspection |
| R-06 | Public outbound internet remains available to a compromised media worker | Internal-destination denial reduces lateral access, but cannot stop exfiltration to an attacker-controlled public service | Domain/HTTPS proxy allowlisting requires a separate compatibility design for dynamic CDNs |
| R-07 | Malicious inputs exhaust disk, CPU, memory or upload quota | Existing CPU/IO weights and task limit help, but are not strict disk/memory budgets; preserve media and add limits only with measured workload headroom | No destructive load test or upload-quota consumption |
| R-08 | Error output exposes URLs or provider response details in logs | Restrict log readers and improve targeted redaction in future application changes | No raw production log contents or credentials inspected |
| R-09 | A future migration drops host controls or account IDs change | Version the control design, verify effective state and record account-resolution/persistence requirements | An enabled unit alone is not proof of a successful cold boot |
| R-10 | Package/dependency vulnerabilities | Record actual package versions and use supported upgrade windows; upstream advisories alone do not prove exploitability | No blanket upgrade, reboot, or unsupported current-CVE claim |

## Why a network guard is not a complete fix

Blocking internal destinations does not revoke stolen credentials, repair unsafe deserialization, prevent public-internet exfiltration, or fully sandbox a media parser. A local same-user proxy or Unix socket may create an alternate route if exposed in the service's filesystem namespace. A separate host/container/namespace can strengthen that boundary but requires a larger operational change.

The present change should therefore be reported as specific containment with measured results, not a declaration that the server is universally secure.
