#!/usr/bin/env python3
"""Read-only package integrity and record-shape checks; no scientific reanalysis.

No images, model weights, training, inference, pixel scoring, or bootstrap are run.
Python >=3.10; standard library only.
"""
from __future__ import annotations
import argparse
from collections import Counter, defaultdict
import csv
import hashlib
import json
from pathlib import Path
import sys

SCENES={11,12,13,15,16,20,21,23,24,27,29}
STAGES={'original','target_raw_upper_projection'}
METHODS={'single','source_raw_mean','source_prediction_mean','source_prediction_replace'} | {
    f'vfuse_seed{s}_{kind}' for s in (11,29,47) for kind in ('best','last')}

class PackageError(RuntimeError):
    pass

def require(condition: bool, message: str) -> None:
    if not condition:
        raise PackageError(message)

def digest(path: Path) -> str:
    h=hashlib.sha256()
    with path.open('rb') as stream:
        for block in iter(lambda:stream.read(1024*1024),b''):
            h.update(block)
    return h.hexdigest()

def load_json(path: Path):
    return json.loads(path.read_text(encoding='utf-8-sig'))

def rows(path: Path):
    with path.open(encoding='utf-8-sig',newline='') as stream:
        yield from csv.DictReader(stream)

def verify(root: Path) -> dict:
    root=root.resolve()
    manifest=root/'SHA256SUMS.txt'
    require(manifest.is_file(),'SHA256SUMS.txt not found')
    count=0;expected=set()
    for line in manifest.read_text(encoding='utf-8').splitlines():
        if not line.strip():continue
        sha,name=line.split(maxsplit=1);name=name.lstrip('*')
        path=(root/name).resolve()
        require(path.is_relative_to(root),f'Unsafe manifest path: {name}')
        require(path.is_file(),f'Missing file: {name}')
        require(name not in expected,f'Duplicate manifest path: {name}')
        require(digest(path)==sha,f'Checksum mismatch: {name}')
        expected.add(name);count+=1
    expected.add('SHA256SUMS.txt')
    extras=[]
    for p in root.rglob('*'):
        if not p.is_file():continue
        rel=p.relative_to(root)
        if any(x in {'.git','__pycache__','local_outputs','.venv'} for x in rel.parts):continue
        if rel.name in {'.DS_Store','Thumbs.db'}:continue
        if rel.as_posix() not in expected: extras.append(rel.as_posix())
    require(not extras,f'Unlisted files in package (inspect before uploading): {extras[:10]}')
    source=root/'data/accuracy/sources'
    for r in load_json(source/'source_manifest.json')['files']:
        p=source/r['file']
        require(p.is_file() and p.stat().st_size==r['bytes'] and digest(p)==r['sha256'],f'Public accuracy input mismatch: {r["file"]}')
    pairfile=load_json(source/'legal_pairs_final.json')
    pairs=pairfile['pairs']
    ids=[r['pair_id'] for r in pairs]
    require(pairfile['count']==2193 and len(ids)==2193 and len(set(ids))==2193,'Final pair count/uniqueness mismatch')
    require(pairfile['exclusions']==[],'Final-stage exclusions field changed')
    require({r['scene'] for r in pairs}==SCENES,'Evaluation scenes changed')
    alignment=load_json(source/'evaluation_alignment.json')
    require(digest(source/'legal_pairs_final.json')==alignment['pair_manifest_sha256'],'Frozen pair identity mismatch')
    expected_ids=set(ids);score_counts={}
    for front in ('D','FDCT'):
        groups=defaultdict(list);num=0
        for row in rows(source/f'{front}_per_image.csv'):
            require(row['frontend']==front,'Front-end field mismatch')
            require(row['stage'] in STAGES and row['method'] in METHODS,'Unexpected score condition')
            groups[(row['stage'],row['method'])].append(row['pair_id']);num+=1
        require(num==43860 and len(groups)==20,'Accuracy rows/condition count mismatch')
        for condition,values in groups.items():
            require(len(values)==2193 and set(values)==expected_ids,f'Pair coverage mismatch {front} {condition}')
        score_counts[front]=num
    early=load_json(root/'data/data_selection/source_records/reference/old_inclusion_exclusion.json')['per_view']
    require(len(early)==2498 and len({r['pair_id'] for r in early})==2498,'Early directory rows mismatch')
    excluded=[r for r in early if r['status']=='excluded_missing_required_member']
    included=[r for r in early if r['status']=='candidate_key_complete']
    require(len(excluded)==305 and len(included)==2193,'Early exclusion counts mismatch')
    require([r['pair_id'] for r in included]==ids,'Early candidate order differs from frozen final pairs')
    readable=list(rows(root/'data/data_selection/excluded_305_existing_records.csv'))
    require(len(readable)==305 and {r['pair_id'] for r in readable}=={r['pair_id'] for r in excluded},'305-row readable extraction mismatch')
    orig=list(rows(root/'data/timing/original/per_call.csv'))
    require(len(orig)==1400,'Original call count mismatch')
    origgroups=defaultdict(list)
    for row in orig:origgroups[row['frontend'],row['method']].append(row)
    require(len(origgroups)==14,'Original condition count mismatch')
    for rr in origgroups.values():
        require(len(rr)==100 and sum(r['first_call']=='True' for r in rr)==1,'Original initial/subsequent call split mismatch')
    resident=list(rows(root/'data/timing/resident/per_call.csv'))
    phases=Counter(r['phase'] for r in resident)
    require(len(resident)==4224 and phases=={'warmup':1056,'measured':3168},'Resident phase/count mismatch')
    measured=Counter((r['frontend'],r['method']) for r in resident if r['phase']=='measured')
    require(len(measured)==8 and set(measured.values())=={396},'Resident condition counts mismatch')
    blocks=load_json(root/'data/timing/resident/block_completion.json')['blocks']
    require(len(blocks)==32 and {r['block_index'] for r in blocks}==set(range(32)),'Saved block metadata missing')
    return {'status':'PACKAGE_STRUCTURE_AND_HASHES_OK','manifest_entries_verified':count,
        'total_public_files':len(expected),'final_pairs':2193,'early_directories':2498,'early_exclusions':305,
        'later_additional_exclusions':0,'final_score_rows':score_counts,'original_calls':1400,
        'resident_calls':4224,'resident_warmup':1056,'resident_measured':3168,
        'scope':'Integrity, saved identifiers and counts only. No training, inference, pixel scoring, metric reaggregation, or bootstrap.'}

def main() -> int:
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root',type=Path,default=Path(__file__).resolve().parents[1])
    args=parser.parse_args()
    try: result=verify(args.root)
    except (OSError,ValueError,KeyError,PackageError) as exc:
        print(f'FAILED: {exc}',file=sys.stderr);return 2
    print(json.dumps(result,indent=2));return 0

if __name__=='__main__':
    raise SystemExit(main())
