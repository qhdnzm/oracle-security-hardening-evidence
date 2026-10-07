#!/usr/bin/env python3
"""Bounded, secret-free connectivity evidence. Run on the target as root.

No HTTP payload is sent to internal destinations; no provider API writes occur.
Temporary TCP listeners bind loopback only and close before exit.
"""
import datetime
import errno
import json
import os
import socket
import subprocess
import sys


CHILD = r'''
import errno,json,socket,ssl,sys
from concurrent.futures import ThreadPoolExecutor
cfg=json.loads(sys.argv[1]); result={}
for label,host,port in cfg['tcp']:
    try:
        with socket.create_connection((host,port),timeout=3): pass
        result[label]={'connected':True}
    except OSError as e:
        result[label]={'connected':False,'errno':errno.errorcode.get(e.errno,'TIMEOUT_OR_NETWORK_ERROR')}
try:
    result['dns_resolution']={'ok':bool(socket.getaddrinfo('www.youtube.com',443,type=socket.SOCK_STREAM))}
except OSError:
    result['dns_resolution']={'ok':False}
def tls(host):
    try:
        ctx=ssl.create_default_context()
        with socket.create_connection((host,443),timeout=5) as raw:
            with ctx.wrap_socket(raw,server_hostname=host) as connection:
                return host,{'ok':True,'protocol':connection.version()}
    except (OSError,ssl.SSLError):
        return host,{'ok':False}
with ThreadPoolExecutor(max_workers=2) as pool:
    result['public_tls']=dict(pool.map(tls,cfg['public_tls']))
print(json.dumps(result,sort_keys=True))
'''


def run(args):
    p = subprocess.run(args, text=True, capture_output=True, timeout=20)
    if p.returncode:
        raise RuntimeError('read-only command failed: ' + args[0])
    return p.stdout


def service_snapshot():
    result = {}
    for unit in ('auto-uploader.service', 'twspace-crawler.service'):
        text = run(['systemctl', 'show', unit, '-p', 'MainPID', '-p', 'NRestarts', '-p', 'ActiveState', '-p', 'User'])
        result[unit] = dict(line.split('=', 1) for line in text.splitlines() if '=' in line)
    return result


def main():
    if os.geteuid() != 0:
        raise SystemExit('root required for identity-only test subprocesses')
    listeners = []
    tcp_targets = []
    try:
        for family, host, label in ((socket.AF_INET, '127.0.0.1', 'loopback_ipv4'), (socket.AF_INET6, '::1', 'loopback_ipv6')):
            server = socket.socket(family, socket.SOCK_STREAM)
            server.bind((host, 0))
            server.listen(16)
            listeners.append(server)
            tcp_targets.append((label, host, server.getsockname()[1]))
        # This standard cloud address is probed with TCP handshake only.
        tcp_targets.append(('metadata_http_port_no_payload', '169.254.169.254', 80))
        resolvers = []
        with open('/etc/resolv.conf', encoding='utf-8') as f:
            for line in f:
                fields = line.split()
                if len(fields) >= 2 and fields[0] == 'nameserver':
                    resolvers.append(fields[1])
        if not resolvers:
            raise RuntimeError('no configured resolver')
        tcp_targets.append(('trusted_dns_tcp53', resolvers[0], 53))
        addresses = json.loads(run(['ip', '-j', 'address', 'show']))
        for interface in addresses:
            wanted = {'enp0s6': 'private_host_ssh_no_auth', 'tailscale0': 'tailnet_host_ssh_no_auth'}.get(interface.get('ifname'))
            if wanted:
                for address in interface.get('addr_info', []):
                    if address.get('family') == 'inet':
                        tcp_targets.append((wanted, address['local'], 22))
                        break
        cfg = {'tcp': tcp_targets, 'public_tls': ['www.youtube.com', 'discord.com', 'api.chzzk.naver.com', 'x.com']}
        before = service_snapshot()
        identities = {}
        for user in ('svc_uploader', 'svc_twspace', 'opc'):
            p = subprocess.run(['runuser', '-u', user, '--', '/usr/bin/python3', '-c', CHILD, json.dumps(cfg)], text=True, capture_output=True, timeout=55)
            if p.returncode:
                raise RuntimeError('identity probe failed for ' + user)
            identities[user] = json.loads(p.stdout)
        report = {
            'schema_version': 1,
            'observed_at_kst': datetime.datetime.now(datetime.timezone(datetime.timedelta(hours=9))).isoformat(),
            'method': 'Loopback sentinels; internal TCP handshakes without application data; normal DNS and public certificate-verified TLS only.',
            'services_before': before,
            'services_after': service_snapshot(),
            'identities': identities,
            'no_webhook_or_upload_or_order': True,
            'no_credential_files_accessed': True,
        }
        report['service_identity_unchanged_during_probe'] = report['services_before'] == report['services_after']
        print(json.dumps(report, indent=2, sort_keys=True))
    finally:
        for server in listeners:
            server.close()


if __name__ == '__main__':
    main()
