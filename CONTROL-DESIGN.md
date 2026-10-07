# Narrow containment design and acceptance plan

Status: **DEPLOYED — bounded network acceptance passed on 2026-10-08 around 02:22 KST**. The initial evidence commit correctly recorded the then-planned state; [VERIFICATION.md](VERIFICATION.md) records the subsequent execution.

## Design decision

Retain the proven service identities and filesystem sandboxes. Add a dedicated nftables output policy scoped to the uploader/crawler identities. This centralizes internal-destination containment instead of scattering URL filters across Python, Node, Streamlink, ffmpeg and future child processes.

Do not alter trading/research identities, SSH routing, the existing public firewall zone, Tailscale ACLs, or unrelated services. Do not restart active recordings merely to activate a firewall rule.

## Intended traffic policy

1. Resolve the two existing service accounts and refuse unexpected identities.
2. Restrict the policy to locally generated packets owned by those accounts.
3. Permit TCP/UDP DNS only to the currently configured trusted resolver on destination port 53.
4. Deny destinations local to the host and private, loopback, link-local, carrier-grade NAT/tailnet and multicast/reserved ranges for both address families as appropriate.
5. Preserve normal public-internet connections; do not flush or replace the system ruleset.

The implemented output hook uses a **positive UID match** that jumps to a separate policy chain. This matters for kernel-generated packets with no socket owner: using a negative UID test followed by unrestricted deny rules could accidentally apply the policy to packets outside the intended identities.

The DNS exception must not allow arbitrary ports to the resolver. In this environment the resolver and cloud metadata service share a link-local address, so allowing that entire address would reopen the metadata route.

## Implementation requirements

- Dedicated named nftables table and root-owned configuration.
- Fail closed on unexpected pre-existing artifacts; preserve current work.
- Apply the table in one nft transaction after syntax validation.
- A dedicated systemd oneshot loads the policy before future media-service starts. Account IDs and resolver configuration must be checked rather than silently becoming stale.
- Scoped rollback removes only this task's table and dependency drop-ins, leaving the system firewall untouched.
- Compare uploader/crawler PIDs and restart counts around application; capture failures and rollback if required.
- Never write secret-bearing units, environment dumps, credential values or authentication files into the evidence package.

The helper resolves the current UIDs and DNS resolver at each load and rejects identity drift, root/login-capable service accounts, malformed resolver configuration, and a pre-existing table without the ownership marker. Resolver changes require a guard reload; no background watcher was added. The dedicated guard unit is enabled and media units require it before future starts. Cold-boot execution was not tested.

Rollback removes the new dependency drop-ins **before** stopping the guard, so systemd does not stop media services through a still-present Requires edge. The old global firewall and application sources are never restored from a broad snapshot.

## Acceptance evidence

The explicitly authorized tests should record:

| Test | Expected result |
| --- | --- |
| Two service accounts / operator-home traversal / sudo permission | Original separation retained |
| Loopback TCP sentinel under each media identity | Denied after policy application |
| Metadata HTTP-port TCP handshake only, no HTTP request | Denied after policy application; no metadata response read |
| Private/tailnet destination rule counters and targeted bounded probe | Enforcement observed, without sending an application payload |
| DNS lookup through configured resolver | Success |
| Anonymous HTTPS/TLS to public provider fronts | Success; no webhook or upload action |
| Unrelated account to the controlled loopback sentinel | Unchanged, proving identity scope |
| Existing media-service PIDs and restart counts | Unchanged |
| Installed configuration hashes, service enablement, dependency ordering | Recorded; actual reboot remains untested unless separately performed |

Failed tests are results, not evidence to omit. Evidence must distinguish a host with no reachable target from a firewall rejection: use a controlled listener and/or before/after comparison and rule counters.

## Host-wide follow-up

SSH hardening must preserve a working administrative session, prepare automatic rollback, validate syntax/effective options, reload rather than restart, and prove a new operator connection before cancelling rollback. The historical workflow also required an authenticated cloud-console recovery path; do not invent that evidence.

The initial expanded dependency graph included an active tracing service through a shared target; direct RequiredBy/WantedBy inspection did not establish an actual tracing-to-rpcbind dependency. No active non-portmapper registration or NFS consumer was observed. rpcbind was not changed in this media-identity rollout. Port-111 listening is not equivalent to internet exposure.

## References

- [OpenSSH sshd_config](https://man.openbsd.org/sshd_config): effective options and forwarding semantics. Disabling SSH forwarding does not prevent an authenticated shell user from implementing another forwarder.
- [nftables official documentation](https://wiki.nftables.org/): packet filtering, owner metadata and atomic ruleset operations.
- [systemd execution environment](https://www.freedesktop.org/software/systemd/man/latest/systemd.exec.html): process, privilege and filesystem sandbox concepts.
