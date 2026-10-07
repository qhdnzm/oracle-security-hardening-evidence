# Historical remediation and evidence

## 1. Scope and reconstruction

The user recalled a July–August 2026 security problem involving webhooks or YouTube uploads and possible access to the internal server. A focused review found contemporary **July 10–11, 2026** deployment reports, design notes and approval conditions. The old host has since been retired. This repository therefore separates historical reports from current-host observations.

## 2. Original trust-boundary failure

The Discord recording command bot ran as the same operator account used by sensitive workloads. That account could access their code and state and had broad passwordless sudo. An attacker who first gained code execution in the external integration could consequently access a much larger trust domain. The uploader and downloader also needed isolation from the operator home and each other's authentication material.

This is a **conditional compromise chain**, not evidence that such an attacker existed. A notification webhook URL is an outbound posting capability; its exposure can allow unauthorized notifications but does not, by itself, prove arbitrary execution on the sending server. The separate Discord Gateway command bot was the stronger bridge into local files in the recovered design.

## 3. Uploader/crawler isolation — July 10, 12:20 KST

The contemporary deployment result reports:

- Separate non-login, non-sudo identities for the uploader and crawler.
- Denial of access to the operator home and sensitive workload directory.
- Separation of service configuration, OAuth state and logs.
- A single controlled group-shared media download directory.
- Root-owned read-only application code and dependencies.
- Discord webhook delivery through systemd credentials instead of a source-code literal.
- Streamlink authentication inputs removed from command-line arguments and supplied through a restricted runtime configuration.
- Filesystem, device, kernel and privilege restrictions through systemd.
- Reduced CPU and IO weight to preserve co-located workload responsiveness.

Reported acceptance evidence: both services running under the intended identities with zero recorded restarts; syntax/import and configuration parsing checks; shared-media create/read/delete checks; channel monitoring initialization; no observed permission loop or OOM; 27 protected services unchanged in active state, main PID and restart count.

The report records `systemd-analyze security` exposure scores improving from **9.2 to 3.6**. This score measures configuration exposure. A natural end-to-end recording/conversion/upload remained outstanding at that reporting point.

## 4. Discord and host hardening — July 10–11

The final historical report records:

| Control | Historical result |
| --- | --- |
| Discord identity | Dedicated non-sudo service user, root-owned runtime, restricted state directory |
| Data access | Read-only access to an explicit set of 16 report CSV inputs, rather than the entire sensitive directory |
| Privilege/filesystem sandbox | NoNewPrivileges, strict system protection and hidden operator home |
| SSH | Root login disabled, password/keyboard-interactive login disabled, X11/TCP/agent forwarding disabled, operator-only allowlist, tighter attempt/time limits |
| SSH recovery | Authenticated cloud console, retained session, timed rollback, fresh operator connection and sudo check before rollback cancellation |
| rpcbind | Service/socket stopped and masked only after the then-current dependency checks; port 111 listener removed |
| OS update/reboot | Not performed in that security window |

The final snapshot is reported at **July 11, 00:28 KST**. The report filename contains a different preparation time; the stated observation time is preserved here instead of inferring time from the filename.

## 5. Explicitly incomplete or deferred work

- Stage-A DRY service drop-ins were rejected as **NO-GO** and not deployed. A release package existing on disk must not be counted as installation.
- Webhook/credential revocation and reissue were not completed by these hardening steps. Moving a secret does not revoke its prior copies.
- OS updates and reboot were separate maintenance work, not part of the claimed completion.
- The broad operator sudo policy was not removed because existing operations depended on it.
- The July 21 troubleshooting memory identifies a file-logging path/permission regression following isolation; stdout journaling continued. This is a documented compatibility limitation, not evidence that account isolation was reversed.

## 6. October migration interpretation

The old host was retired after a migration. The media service account isolation survived on the replacement host, while some host-wide settings differed. A migration can copy application units without copying host hardening; it is therefore necessary to check effective state, rather than assume the historical report describes the new machine.

The old Discord command bridge was not migrated and is absent on the replacement host. That specific bridge should not be reported as currently active.

## 7. Provenance and limits

`EVIDENCE-PROVENANCE.json` records hashes of selected locally retained original documents. Originals are not uploaded because they include operational identifiers and unrelated system details. The hash is a content commitment made during this reconstruction, not a cryptographic proof that the document existed in July. No raw credential, account state, private session, or historical chat transcript was used to fill gaps.
