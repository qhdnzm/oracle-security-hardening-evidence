# Verification and deployment evidence

## Result

**DEPLOYED — 2026-10-08, approximately 02:22 KST.** A new dedicated nftables output table now contains media-worker traffic by originating socket UID. The pre-existing uploader and crawler processes remained active with unchanged PIDs and restart counts throughout the accepted rollout.

The observed baseline at **02:15:50 KST** is in [NETWORK-BEFORE.json](NETWORK-BEFORE.json). The accepted post-change observation is in [NETWORK-AFTER.json](NETWORK-AFTER.json). Exact observation timestamps are inside those receipts.

## Before/after acceptance matrix

Each media-identity row represents **two checks**, one under the uploader identity and one under the crawler identity.

| Probe | Before | Accepted after |
| --- | --- | --- |
| IPv4 loopback controlled TCP listener | 2/2 connected | 2/2 denied |
| IPv6 loopback controlled TCP listener | 2/2 connected | 2/2 denied |
| Cloud metadata HTTP port, handshake only | 2/2 connected | 2/2 denied |
| Own host private-address SSH port, no authentication | 2/2 connected | 2/2 denied |
| Own host tailnet-address SSH port, no authentication | 2/2 connected | 2/2 denied |
| Configured resolver TCP port 53 | 2/2 connected | 2/2 connected |
| Normal name resolution | 2/2 succeeded | 2/2 succeeded |
| Certificate-verified TLS to four public provider fronts | 8/8 succeeded | 8/8 succeeded |
| Operator-account control probes to the same targets | All succeeded | All succeeded |

The four public fronts were YouTube, Discord, Chzzk and X. A TLS handshake verifies transport and certificate validation, not authenticated application behavior, every CDN path, actual webhook delivery or a completed media upload.

## Why the denial evidence is meaningful

An unreachable address alone is weak evidence: there may never have been a listening service. This probe therefore:

1. Creates temporary listeners on IPv4 and IPv6 loopback.
2. Establishes a pre-change baseline.
3. Repeats under the same two application identities.
4. Repeats as the operator identity to show that the listener and routing remain available outside the policy scope.
5. Checks nftables reject-counter deltas alongside the connection result.

`GUARD-BEFORE-PROBE.json` and `GUARD-AFTER-PROBE.json` retain those counters. The accepted rollout recorded 10 host-local reject packets and 2 non-public IPv4 reject packets. Packet counters and attempted connections are different measures; the result is not presented as twelve distinct exploits.

IPv4 administrative rejection surfaced as `EHOSTUNREACH` on this kernel and IPv6 rejection as `EACCES`. Neither string alone establishes enforcement. The controlled listeners, working operator-account controls and exact rule counters supply the missing evidence.

## Identity and lifecycle scope

The probe uses short-lived processes under each actual account. The network policy is UID-scoped, so those processes exercise the same packet-owner boundary as existing workers and children. This is not a test of every application path or a clone of each service's complete mount namespace.

The guard is an enabled oneshot systemd unit with `RemainAfterExit=yes`. Media unit drop-ins require and order it before future starts. The policy resolves account IDs and the configured DNS resolver at load time. A deliberate guard reload exercises idempotent replacement; media processes are not restarted. Reload evidence is summarized in `DEPLOYMENT-RECEIPT.json`.

Actual reboot, VM replacement, future resolver changes and future firewall reloads were not tested. Configuration enablement must not be reported as a cold-boot success.

## Rollout corrections retained

- **Attempt 1:** nftables did not attach a table comment when the table was first created without that comment and then redeclared. The post-apply ownership check correctly refused success. The same ownership guard prevented automatic deletion. After confirming the exact newly created table and its rules, it was removed manually and the scoped rollback completed. Existing media PIDs/restart counts were unchanged.
- **Attempt 2:** the corrected table ownership worked and the actual network checks behaved correctly, but acceptance initially required only `EACCES`. IPv4 returned `EHOSTUNREACH`; the installer rejected completion and automatically rolled back. The acceptance logic was corrected to require a supported errno **plus** controlled listeners, working controls and reject-counter deltas.
- **Attempt 3:** the corrected policy, ownership checks and acceptance passed. The guard was left installed and enabled. Both earlier failed attempts remain recorded; they are not rewritten as successful deployments.

## Exact implementation and evidence

- `media_egress_guard.py`: installed policy generator, ownership guard, atomic apply, sanitized status and exact-scope removal.
- `media-egress-guard.service`: installed guard unit.
- `20-media-egress-guard.conf`: dependency drop-in for each media service.
- `probe_media_egress.py`: executed bounded probe.
- `INSTALLED-SHA256.txt`: observed installed-file hashes.
- `DEPLOYMENT-RECEIPT.json`: local/installed hash comparison and final lifecycle summary.
- `SOURCE-OBSERVATION.json`: limited current application source metadata; no application overwrite.

Operational rollback instructions are retained locally with the installed control. The rollback affects only the guard and its two dependency edges. No broad ruleset flush, global service restart, credential rotation, media deletion, order, webhook submission or test upload was performed.

## Residual risk

Public internet access is still available. This control contains internal network access; it does not stop exfiltration to a public endpoint or remove the worker's legitimate authentication capabilities. Shared-media path handling, parser isolation, serialized state format, provider credential rotation, resource exhaustion and host-wide administration remain separate review items in [CURRENT-ASSESSMENT.md](CURRENT-ASSESSMENT.md).
