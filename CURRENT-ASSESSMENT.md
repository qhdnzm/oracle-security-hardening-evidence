# Current assessment — 2026-10-08

Initial observations below were collected read-only around 02:03–02:10 KST. **The scoped media-account network guard was deployed around 02:22 KST; its acceptance tests passed.** Host-wide SSH/rpcbind decisions and the additional application-hardening proposals remain separate. These are point-in-time facts, not a comprehensive penetration test or incident-response conclusion.

## Controls retained

The uploader and crawler are active with separate service users and zero recorded restarts at observation. Both retain NoNewPrivileges, strict system protection, protected homes/devices/kernel/control groups, an empty capability bounding set, and a limited set of writable application/state/media directories. Neither account can traverse the operator home; sudo reports neither is permitted to run sudo.

The retired-host Discord command service is not installed on the replacement host. The media application directory is root-owned and not writable by its service account. The shared media directory is group-writable as required by the pipeline. The current uploader log directory has the intended service owner.

## Confirmed differences and constraints

| ID | Observation | Interpretation and current status |
| --- | --- | --- |
| H-01 | Effective SSH permits root public-key login, X11, TCP and agent forwarding; attempt/grace values differ from July hardening | Host-hardening drift confirmed. This does not prove a root key exists or that an unauthorized login occurred. Recovery-safe remediation required. |
| H-02 | rpcbind is active on TCP/UDP port 111 for IPv4 and IPv6 | Listener confirmed. The public host firewall does not list rpcbind as allowed. Internet reachability is not established. No non-portmapper RPC registration or active NFS consumer was observed; host-wide stop/mask was not part of the media-identity change. |
| N-01 | Baseline media identities could connect to internal destinations; the units have no IPAddressDeny policy | Remediated with a separate UID-scoped nftables output guard. Ten targeted connection attempts now fail; see acceptance evidence. |
| N-02 | DNS uses a cloud link-local resolver | Remediated with a TCP/UDP port-53 exception only. Metadata HTTP is denied while DNS still works. |

## Additional plausible risks

These are threat-model findings with explicit prerequisites. They are not claims that an exploit was observed.

| ID | Risk and prerequisite | Existing mitigation / proposed response | Evidence limit |
| --- | --- | --- | --- |
| R-01 | Compromised downloader/uploader or unsafe URL handling connects to metadata, loopback, private LAN or tailnet endpoints | Independent per-service-account destination guard deployed; trusted DNS-only exception verified | Network path containment verified; no malicious URL exploit or credential response requested |
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

## Current application source observation

A read-only AST inspection of the installed application confirmed `pickle.load`, found no `shell=True` call, and found no explicit `islink`/`is_symlink`/`lstat` call in that file. These syntactic observations do not prove the absence of all path checks or all injection risks. Only booleans/counts and a source fingerprint were returned; secret-bearing files were not opened. The installed source differed from an older local snapshot, so the application was not overwritten from that snapshot. See `SOURCE-OBSERVATION.json`.

Dependency clarification: the initial expanded reverse-dependency listing included an active tracing service through a shared target. A subsequent direct RequiredBy/WantedBy inspection did **not** establish a direct rpcbind dependency for that service. The baseline document's stronger implication was corrected; no service was stopped on that assumption.
