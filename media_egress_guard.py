#!/usr/bin/env python3
"""Per-account internal-destination guard; no credential or application I/O.

apply: atomically replace only this tool's nft table.
status: return sanitized configuration and counters.
remove: remove only a table carrying this tool's exact owner marker.
"""
import argparse
import hashlib
import ipaddress
import json
import os
import pwd
import subprocess

TABLE = 'media_pipeline_guard'
MARKER = 'media-egress-guard-v1'
USERS = ('svc_uploader', 'svc_twspace')
UNITS = ('auto-uploader.service', 'twspace-crawler.service')
NFT = '/usr/sbin/nft'
V4 = ('0.0.0.0/8', '10.0.0.0/8', '100.64.0.0/10', '127.0.0.0/8',
      '169.254.0.0/16', '172.16.0.0/12', '192.0.0.0/24', '192.0.2.0/24',
      '192.168.0.0/16', '198.18.0.0/15', '198.51.100.0/24', '203.0.113.0/24',
      '224.0.0.0/4', '240.0.0.0/4')
V6 = ('::/96', '::ffff:0:0/96', '64:ff9b::/96', '64:ff9b:1::/48',
      '100::/64', '2001:db8::/32', '2002::/16', 'fc00::/7', 'fe80::/10', 'ff00::/8')


def command(args, stdin=None, check=True):
    p = subprocess.run(args, input=stdin, text=True, capture_output=True, timeout=20)
    if check and p.returncode:
        # Do not leak arbitrary external command output.
        raise RuntimeError('command failed: ' + args[0])
    return p


def inspect_table():
    p = command([NFT, '-j', 'list', 'tables'])
    tables = json.loads(p.stdout).get('nftables', [])
    exists = any(x.get('table', {}).get('family') == 'inet' and x['table'].get('name') == TABLE for x in tables)
    if not exists:
        return None
    document = json.loads(command([NFT, '-j', 'list', 'table', 'inet', TABLE]).stdout)
    table = next(x['table'] for x in document['nftables'] if 'table' in x)
    if table.get('comment') != MARKER:
        raise RuntimeError('refusing an existing table without the exact ownership marker')
    return document


def identity_config():
    ids = []
    for user, unit in zip(USERS, UNITS):
        account = pwd.getpwnam(user)
        if account.pw_uid == 0 or account.pw_shell not in ('/sbin/nologin', '/usr/sbin/nologin', '/bin/false'):
            raise RuntimeError('unexpected privileged or login-capable media identity')
        configured = command(['systemctl', 'show', unit, '-p', 'User', '--value']).stdout.strip()
        if configured != user:
            raise RuntimeError('media unit identity drift')
        ids.append(account.pw_uid)
    if len(set(ids)) != len(ids):
        raise RuntimeError('service identities are not distinct')
    return ids


def resolver_config():
    found = []
    with open('/etc/resolv.conf', encoding='utf-8') as source:
        for line in source:
            fields = line.split()
            if len(fields) >= 2 and fields[0] == 'nameserver':
                address = ipaddress.ip_address(fields[1])
                if address.is_unspecified or address.is_multicast:
                    raise RuntimeError('invalid resolver')
                if str(address) not in found:
                    found.append(str(address))
    if not found or len(found) > 3:
        raise RuntimeError('unexpected resolver configuration')
    return found


def render(ids, resolvers):
    if len(ids) != 2 or any(type(uid) is not int or uid <= 0 for uid in ids) or len(set(ids)) != 2:
        raise ValueError('two distinct non-root integer UIDs are required')
    uid_set = ', '.join(str(uid) for uid in ids)
    lines = [
        'add table inet ' + TABLE + ' { comment "' + MARKER + '"; }',
        'flush table inet ' + TABLE,
        'table inet ' + TABLE + ' {',
        '  comment "' + MARKER + '"',
        '  chain output {',
        '    type filter hook output priority 10; policy accept;',
        '    meta skuid { ' + uid_set + ' } jump media_only',
        '  }',
        '  chain media_only {',
    ]
    for raw in resolvers:
        address = ipaddress.ip_address(raw)
        if address.is_unspecified or address.is_multicast:
            raise ValueError('invalid resolver')
        family = 'ip' if address.version == 4 else 'ip6'
        for protocol in ('udp', 'tcp'):
            lines.append('    ' + family + ' daddr ' + str(address) + ' ' + protocol + ' dport 53 counter accept comment "trusted_dns"')
    # Destination ports other than DNS on the metadata/resolver address remain denied.
    lines += [
        '    fib daddr type local counter reject with icmpx type admin-prohibited comment "deny_host_local"',
        '    ip daddr { ' + ', '.join(V4) + ' } counter reject with icmpx type admin-prohibited comment "deny_nonpublic_ipv4"',
        '    ip6 daddr { ' + ', '.join(V6) + ' } counter reject with icmpx type admin-prohibited comment "deny_nonpublic_ipv6"',
        '    counter accept comment "public_egress"',
        '  }',
        '}',
    ]
    return '\n'.join(lines) + '\n'


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('action', choices=('apply', 'status', 'remove', 'render'))
    args = parser.parse_args()
    if os.geteuid() != 0:
        raise SystemExit('root is required')
    previous = inspect_table()
    if args.action == 'remove':
        if previous:
            command([NFT, 'delete', 'table', 'inet', TABLE])
        print(json.dumps({'removed': previous is not None, 'scope': TABLE}))
        return
    ids, resolvers = identity_config(), resolver_config()
    rules = render(ids, resolvers)
    if args.action == 'render':
        print(rules, end='')
        return
    if args.action == 'apply':
        command([NFT, '--check', '--file', '-'], stdin=rules)
        command([NFT, '--file', '-'], stdin=rules)
        previous = inspect_table()
    counters = {}
    for entry in (previous or {}).get('nftables', []):
        rule = entry.get('rule', {})
        for expression in rule.get('expr', []):
            if 'counter' in expression:
                label = rule.get('comment', 'unnamed')
                counters[label] = counters.get(label, 0) + expression['counter'].get('packets', 0)
    print(json.dumps({
        'installed': previous is not None,
        'scope': TABLE,
        'accounts': list(USERS),
        'resolver_count': len(resolvers),
        'rendered_rules_sha256': hashlib.sha256(rules.encode()).hexdigest(),
        'packet_counters': counters,
    }, sort_keys=True))


if __name__ == '__main__':
    main()
