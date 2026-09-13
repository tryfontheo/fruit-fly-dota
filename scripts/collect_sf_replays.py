"""Collect public professional Shadow Fiend matches, with explicit provenance."""
import argparse, bz2, hashlib, json, shutil, time, sys
import zstandard
from pathlib import Path
from urllib.parse import urlencode, urlparse
from urllib.request import urlopen, Request

def get_json(url):
    with urlopen(Request(url,headers={'User-Agent':'fruit-fly-dota research/0.1'}), timeout=60) as r: return json.load(r)

def main():
    if hasattr(sys.stdout,'reconfigure'):sys.stdout.reconfigure(errors='replace')
    parser=argparse.ArgumentParser(); parser.add_argument('--count',type=int,default=6)
    args=parser.parse_args()
    if not 3<=args.count<=30: raise ValueError('Choose 3–30 matches per collection')
    root=Path('data/replays'); raw=root/'raw'; raw.mkdir(parents=True,exist_ok=True)
    sql=f'SELECT m.match_id,m.start_time,m.leagueid FROM matches m JOIN player_matches p ON p.match_id=m.match_id WHERE p.hero_id=11 AND m.leagueid<>0 ORDER BY m.match_id DESC LIMIT {args.count*3}'
    candidates=get_json('https://api.opendota.com/api/explorer?'+urlencode({'sql':sql}))['rows']
    selected=[]
    for row in candidates:
        if len(selected)>=args.count: break
        mid=row['match_id']; time.sleep(1)
        try:
            meta=get_json(f'https://api.opendota.com/api/matches/{mid}')
            # League membership alone is not proof of high level play.
            if meta.get('league',{}).get('tier') not in ('professional','premium'): continue
            player=next(p for p in meta['players'] if p['hero_id']==11)
            url=meta.get('replay_url')
            if not url: continue
            host=urlparse(url).hostname or ''
            if not host.endswith('.valve.net'): raise ValueError('Unexpected replay host')
            dest=raw/f'{mid}.dem'; compressed=raw/f'{mid}.dem.bz2'
            if not dest.exists():
                print(f'Downloading SF match {mid}: {player.get("name","unnamed")}',flush=True)
                with urlopen(url,timeout=120) as r, compressed.open('wb') as f: shutil.copyfileobj(r,f)
                partial=dest.with_suffix('.partial')
                with compressed.open('rb') as source:
                    magic=source.read(4); source.seek(0)
                    if magic[:3]==b'BZh': reader=bz2.BZ2File(source)
                    elif magic==b'\x28\xb5\x2f\xfd': reader=zstandard.ZstdDecompressor().stream_reader(source)
                    else: raise ValueError(f'Unknown replay compression magic {magic!r}')
                    with reader as r, partial.open('wb') as f: shutil.copyfileobj(r,f)
                with partial.open('rb') as f:
                    if f.read(8)!=b'PBDEMS2\x00': raise ValueError('Not a Source 2 replay')
                partial.replace(dest)
            with dest.open('rb') as f: digest=hashlib.file_digest(f,'sha256').hexdigest()
            entry=dict(match_id=mid,hero_id=11,hero='npc_dota_hero_nevermore',player=player.get('name'),
                player_slot=player['player_slot'],league=meta['league']['name'],tier=meta['league']['tier'],
                radiant=meta.get('radiant_team',{}).get('name'),dire=meta.get('dire_team',{}).get('name'),
                replay_url=url,metadata_url=f'https://api.opendota.com/api/matches/{mid}',
                start_time=meta['start_time'],duration=meta['duration'],sha256=digest,bytes=dest.stat().st_size)
            selected.append(entry)
            # Whole-match split is fixed before extraction; no adjacent-frame leakage.
            for i,m in enumerate(selected): m['split']='train' if i<args.count-2 else ('validation' if i==args.count-2 else 'test')
            (root/'sf_manifest.json').write_text(json.dumps(dict(hero='Shadow Fiend',hero_id=11,
                selection='Recent OpenDota professional/premium league games featuring SF',
                query=sql,matches=selected,status='Raw replays only; not training trajectories'),indent=2))
            print(f'Collected {mid}, {dest.stat().st_size/1e6:.1f} MB',flush=True)
        except Exception as exc: print(f'Unavailable {mid}: {exc}',flush=True)
    if len(selected)<args.count: raise RuntimeError(f'Only obtained {len(selected)}/{args.count} requested replays')

if __name__=='__main__': main()
