# Work and system scope

I operate and maintain my own Oracle Linux cloud infrastructure, including automated media recording and upload services and their external integrations. My defensive security work covers source-code review, threat modeling, least-privilege service isolation, safer credential handling, and verification of access boundaries on systems I administer.

In July 2026, the remediation work separated externally connected services from a privileged shared account, restricted filesystem access, and removed sensitive values from application source and process arguments. In October 2026, I documented that work and added an outbound network control for the media-service identities. Authorized before-and-after tests showed that targeted metadata, loopback, private-network and tailnet connections were denied while DNS and public-provider TLS connectivity remained available.

This work is limited to my own infrastructure and authorized defensive testing. It does not involve unauthorized testing of third-party systems. The linked repository contains sanitized code comparisons, threat analysis, historical provenance and current verification evidence.

Evidence: https://github.com/qhdnzm/oracle-security-hardening-evidence

