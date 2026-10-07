# Security assessment: privilege boundaries and cloud-internal access in a self-hosted media pipeline

**Author / maintainer:** [hwangbo0718](https://github.com/qhdnzm)  
**Scope:** owner-administered Oracle Linux infrastructure and maintained Python/Node.js automation  
**Work:** security assessment, targeted remediation and before/after verification  
**Timeline:** July 2026 remediation; October 2026 follow-up implementation, verification and publication

## Executive result

This work addressed two connected security boundaries: excessive privileges inherited by externally connected integrations, and internal-network reachability that remained available after service-account separation.

The resulting design combines least-privilege Linux identities, restricted filesystems, safer application credential handling and an independent UID-scoped network policy. On the maintained host, the follow-up policy denied **10/10 targeted internal connection attempts** across two media identities while preserving **8/8 public-provider TLS checks**, DNS, and the existing media-service PIDs and restart counts.

## Finding 1 — shared privileged execution context

**Affected condition.** The historical Discord command integration shared the operator identity used by sensitive co-located workloads. That identity could reach their application/state files and broad passwordless sudo. The media services also required isolation from operator files and one another's authentication material.

**Security consequence.** Code execution in an external integration could inherit access beyond the integration's operational purpose. The finding concerns privilege propagation in this deployment; the initial compromise of a dependency or input handler is an attack prerequisite.

**Remediation.** Separate non-login/non-sudo identities; root-owned application code; systemd filesystem, device, kernel and privilege restrictions; explicit writable state/media directories; notification capability supplied outside application source; cookie values removed from process arguments. The historical reporting bot received a fixed read-only report-file set instead of the whole operator directory.

**Evidence.** Retained July reports record successful account/boundary checks and continuity of protected services. October observations confirm that media-account isolation and operator-home denial remain in place. The historical Discord bridge is absent from the replacement host. See [history](HISTORY.md) and [application/service before-and-after excerpts](CODE-BEFORE-AFTER.md).

## Finding 2 — service isolation left cloud-internal routes reachable

**Reproduced condition.** Before the network change, each media identity could establish TCP connections to controlled IPv4/IPv6 loopback listeners, the cloud metadata HTTP port, and the maintained host's private/tailnet SSH listeners. [Baseline receipt](NETWORK-BEFORE.json).

**Security consequence.** A compromised worker or an application path permitting attacker-influenced requests could contact services outside its intended public-provider workflow. The demonstrated condition is TCP reachability; the tests did not request metadata contents or attempt SSH authentication.

**Remediation.** One dedicated nftables output table positively matches the two originating socket UIDs and blocks host-local and non-public destinations. This applies across Python, Node.js and their child processes without relying on every library or media tool implementing identical URL validation.

**Compatibility-critical detail.** DNS and metadata use the same cloud link-local address. Permitting the resolver address wholesale would reopen metadata HTTP. The implemented exception permits only TCP/UDP destination port 53 to the configured resolver.

The guard resolves account IDs and resolver configuration at load time, refuses identity drift, and uses an ownership marker to avoid modifying unrelated tables. Atomic table replacement and ordered systemd startup make the control independently maintainable. [Implementation](media_egress_guard.py) · [design](CONTROL-DESIGN.md).

## Verification that distinguishes enforcement from an unreachable target

| Measure | Baseline | Accepted after-change result |
| --- | --- | --- |
| Five internal probes × two media identities | 10 successful connections | **10 denied** |
| Four public-provider TLS checks × two media identities | 8 successful handshakes | **8 successful handshakes** |
| DNS and configured resolver TCP/53 | Working for both identities | **Preserved** |
| Operator-account controls to the same targets | Working | **Unchanged** |
| Existing uploader/crawler processes | Running | **Same PIDs and restart counts** |

The method combines temporary controlled listeners, a before/after comparison, a working operator-account control, and nftables reject-counter deltas. This avoids treating a failed connection or an errno as sufficient proof on its own. The raw sanitized receipts and the executed probe are published: [after-change receipt](NETWORK-AFTER.json), [counters](GUARD-AFTER-PROBE.json), [probe code](probe_media_egress.py), [full verification record](VERIFICATION.md).

## Safe deployment and evidence integrity

- The change was confined to one nftables table, its lifecycle helper/unit, and two service dependency drop-ins.
- Existing application code and system-wide firewall rules were preserved.
- The accepted deployment and a subsequent guard reload retained both media processes.
- Exact-scope rollback and two corrected rollout attempts are retained in the verification record.
- Published helper bytes matched the installed and retained local source by SHA-256. [Deployment receipt](DEPLOYMENT-RECEIPT.json).
- A full-history Gitleaks scan of the original published revision returned zero findings across two commits and 22 current files. [Exact scan scope and receipt](SECRET-SCAN.json).

## Further analysis

The assessment also identified the shared-media write boundary, serialized OAuth state, media-parser identity, and public-egress exfiltration as distinct areas for further reduction of exposure. Each is documented with its prerequisites and evidence level rather than being counted as an additional reproduced exploit. [Risk register](CURRENT-ASSESSMENT.md).

## Scope and provenance

The tested infrastructure is owned and administered by the repository owner. Public provider fronts received ordinary certificate-verified TLS connections. Internal checks sent no application payload, and the acceptance procedure submitted no orders, notification webhooks or media uploads.

July findings are supported by retained deployment reports and transformation scripts; October findings are supported by current source/configuration observations and target-host tests. [Historical fingerprints](EVIDENCE-PROVENANCE.json) bind the reconstruction to retained documents. Original implementation and later publication dates are distinguished.

This report's evidence basis is the owner's deployment work and controlled measurements. Its verification scope covers the listed network and service-continuity properties; cold boot and completed authenticated uploads remain outside those acceptance results.
