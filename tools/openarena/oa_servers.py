#!/usr/bin/env python3
"""List OpenArena servers from dpmaster and probe them (getinfo + getstatus).
usage: oa_servers.py [--json out.json]"""
import socket, struct, sys, json
import concurrent.futures as cf

def master(host, query, port=27950):
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM); s.settimeout(2)
    s.sendto(b'\xff\xff\xff\xff' + query.encode(), (socket.gethostbyname(host), port))
    out = set()
    try:
        while True:
            d, _ = s.recvfrom(65536)
            i = d.find(b'\\')
            while 0 <= i and i + 7 <= len(d):
                c = d[i + 1:i + 7]
                if c.startswith(b'EOT'):
                    break
                out.add((socket.inet_ntoa(c[:4]), struct.unpack('>H', c[4:6])[0])); i += 7
    except socket.timeout:
        pass
    return out

def ask(addr, q):
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM); s.settimeout(0.8)
    try:
        s.sendto(b'\xff\xff\xff\xffget' + q + b' x', addr); return s.recvfrom(65536)[0].decode('latin1')
    except Exception:
        return None

def kv(txt):
    p = txt.split('\n')[1].split('\\')[1:]
    return dict(zip(p[::2], p[1::2]))

def probe(a):
    i, st = ask(a, b'info'), ask(a, b'status')
    if not i or not st:
        return None
    return {'addr': '%s:%d' % a, 'info': kv(i), 'status': kv(st), 'players': len(st.strip().split('\n')) - 2}

if __name__ == '__main__':
    addrs = master('dpmaster.deathmask.net', 'getservers 71 full empty')
    with cf.ThreadPoolExecutor(32) as ex:
        rows = [r for r in ex.map(probe, addrs) if r]
    rows.sort(key=lambda r: -r['players'])
    print(len(addrs), 'listed,', len(rows), 'answered')
    for r in rows:
        I, S = r['info'], r['status']
        print('%-22s pure=%-2s game=%-8s fs_game=%-8s gt=%-2s pl=%-2d %-22s %s' % (r['addr'], S.get('sv_pure', '?'), S.get('gamename', ''),
              S.get('fs_game', ''), S.get('g_gametype', ''), r['players'], S.get('version', '')[:22], I.get('hostname', '')[:30]))
    if '--json' in sys.argv:
        json.dump(rows, open(sys.argv[sys.argv.index('--json') + 1], 'w'), indent=1)
