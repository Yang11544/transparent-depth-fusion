#!/usr/bin/env python3
"""Reaggregate existing per-image CSVs; no images, models, inference or training.

Python >=3.10; standard library only. Computes original and postprocessed stages
separately. G4's tail requirement is GLOBAL, not a new leave-one tail criterion.
Original-stage applications of G4 are explicitly diagnostic, not historical gates.
Never selects a checkpoint using final evaluation results. Refuses output overwrite.
"""
from __future__ import annotations
import argparse, collections, csv, hashlib, json, math, re, sys, time
from pathlib import Path
from typing import Any, Iterable

FRONTS=('D','FDCT')
STAGES=('original','target_raw_upper_projection')
SEEDS=(11,29,47)
SCENES=(11,12,13,15,16,20,21,23,24,27,29)
P='source_prediction_mean'
METHODS=('single','source_raw_mean',P,'source_prediction_replace')+tuple(
    f'vfuse_seed{s}_{kind}' for s in SEEDS for kind in ('best','last'))
METRICS=('images','pixels','E_mae_mm','Q_rmse_mm','over50_fraction')
RATIO_MAX=1.03
TAIL_MAX_FRACTION=0.002
ABS_CHECK_MM=1e-8

class ValidationError(RuntimeError): pass

def require(ok: bool, message: str) -> None:
    if not ok: raise ValidationError(message)

def sha(path: Path) -> str:
    h=hashlib.sha256()
    with path.open('rb') as f:
        for block in iter(lambda:f.read(4*1024*1024),b''): h.update(block)
    return h.hexdigest()

def read_csv(path: Path) -> list[dict[str,str]]:
    with path.open(encoding='utf-8-sig',newline='') as f: return list(csv.DictReader(f))

def write_csv(path: Path, rows: list[dict[str,Any]]) -> None:
    require(bool(rows),f'No output rows for {path.name}')
    with path.open('x',encoding='utf-8',newline='') as f:
        w=csv.DictWriter(f,fieldnames=list(rows[0]));w.writeheader();w.writerows(rows)

def aggregate(rows: Iterable[dict[str,Any]]) -> dict[str,Any]:
    rr=list(rows);require(bool(rr),'Empty aggregation')
    n=sum(r['pixels'] for r in rr);require(n>0,'Empty pixel support')
    return dict(images=len(rr),pixels=n,
        E_mae_mm=math.fsum(r['mae_mm'] for r in rr)/len(rr),
        Q_rmse_mm=1000*math.sqrt(math.fsum(r['sq_sum_m2'] for r in rr)/n),
        over50_fraction=sum(r['over50_pixels'] for r in rr)/n)

def flags(p: dict[str,Any],v: dict[str,Any],loo: list[dict[str,Any]]) -> dict[str,Any]:
    er=p['E_mae_mm']/v['E_mae_mm'];qr=p['Q_rmse_mm']/v['Q_rmse_mm']
    fd=p['over50_fraction']-v['over50_fraction']
    em=max(r['P_V_MAE_ratio'] for r in loo);qm=max(r['P_V_RMSE_ratio'] for r in loo)
    tests=dict(overall_MAE_ok=er<=RATIO_MAX,overall_RMSE_ok=qr<=RATIO_MAX,
               all_LOSO_MAE_ok=em<=RATIO_MAX,all_LOSO_RMSE_ok=qm<=RATIO_MAX,
               global_tail_ok=fd<=TAIL_MAX_FRACTION)
    return dict(P_V_MAE_ratio=er,P_V_RMSE_ratio=qr,worst_LOSO_MAE_ratio=em,
        worst_LOSO_RMSE_ratio=qm,
        worst_MAE_omission=';'.join(str(r['omitted_scene']) for r in loo if r['P_V_MAE_ratio']==em),
        worst_RMSE_omission=';'.join(str(r['omitted_scene']) for r in loo if r['P_V_RMSE_ratio']==qm),
        violating_MAE_scenes=';'.join(str(r['omitted_scene']) for r in loo if r['P_V_MAE_ratio']>RATIO_MAX),
        violating_RMSE_scenes=';'.join(str(r['omitted_scene']) for r in loo if r['P_V_RMSE_ratio']>RATIO_MAX),
        P_minus_V_over50_percentage_points=100*fd,**tests,
        full_G4=all(tests.values()),
        failed_components=';'.join(k for k,x in tests.items() if not x))

def compare_metrics(calculated: dict[str,Any], saved: dict[str,str], identity: str,
                    maxima: dict[str,float]) -> None:
    for key in METRICS:
        x=float(calculated[key]);y=float(saved[key]);delta=abs(x-y)
        maxima[key]=max(maxima.get(key,0),delta)
        tol=0 if key in ('images','pixels') else (ABS_CHECK_MM if key.endswith('_mm') else 1e-12)
        require(delta<=tol,f'{identity}: {key} mismatch: {x} vs {y}, delta {delta}')

def run(sources: Path, out: Path) -> dict[str,Any]:
    started=time.perf_counter()
    sources=sources.resolve();out=out.resolve()
    require(sources.exists(),'Source directory does not exist')
    require(not out.exists() or not any(out.iterdir()),'Refusing nonempty output directory')
    require(not out.is_relative_to(sources),'Output may not be inside source directory')
    out.mkdir(parents=True,exist_ok=True)
    file_manifest=json.loads((sources/'source_manifest.json').read_text())
    for rec in file_manifest['files']:
        f=sources/rec['file']
        require(f.stat().st_size==rec['bytes'] and sha(f)==rec['sha256'],f'Source identity mismatch: {f}')
    protocol=json.loads((sources/'evaluation_alignment.json').read_text())
    pairfile=sources/'legal_pairs_final.json'
    require(sha(pairfile)==protocol['pair_manifest_sha256'],'Pair manifest SHA mismatch')
    manifest=json.loads(pairfile.read_text());pairs=manifest['pairs']
    require(len(pairs)==2193==manifest['count'],'Unexpected pair count')
    pair_map={p['pair_id']:(int(p['scene']),int(p['view'])) for p in pairs}
    require(len(pair_map)==2193,'Duplicate pairs in manifest')
    require(set(s for s,v in pair_map.values())==set(SCENES),'Scene identities changed')
    require(protocol['main_stage']==STAGES[1],'Main stage mismatch')
    require(protocol['criteria']['G4']['formula']=='E_P <= 1.03*E_V and Q_P <= 1.03*Q_V','G4 formula changed')
    require(protocol['criteria']['G4']['extra']=='same both constraints after leaving each scene; F_P-F_V <= 0.002','G4 constraints changed')
    canon_order=sorted(pair_map,key=lambda k:pair_map[k])
    model_locks=json.loads((sources/'model_lock_record.json').read_text())
    groups={};all_rows={};ref_pixels={};row_counts={};mae_check_max=0.0
    for front in FRONTS:
        rr=read_csv(sources/f'{front}_per_image.csv');converted=[];seen=set();local=collections.defaultdict(list)
        require(len(rr)==2193*len(METHODS)*len(STAGES),f'{front}: wrong row count')
        for r0 in rr:
            r=dict(r0)
            require(r['frontend']==front,'Front-end column mismatch')
            for k in ('scene','view','pixels','over50_pixels'):r[k]=int(r[k])
            for k in ('abs_sum_m','sq_sum_m2','mae_mm'):r[k]=float(r[k])
            require(r['pair_id'] in pair_map and (r['scene'],r['view'])==pair_map[r['pair_id']], 'Sample identity mismatch')
            require(r['cohort']=='reserved11' and r['stage'] in STAGES and r['method'] in METHODS,'Condition mismatch')
            require(r['pixels']>0 and 0<=r['over50_pixels']<=r['pixels'],'Bad counts')
            require(all(math.isfinite(r[k]) and r[k]>=0 for k in ('abs_sum_m','sq_sum_m2','mae_mm')),'Bad numeric record')
            diff=abs(r['mae_mm']-1000*r['abs_sum_m']/r['pixels']);mae_check_max=max(mae_check_max,diff)
            require(diff<=ABS_CHECK_MM,'Unit/MAE relation mismatch')
            key=(r['stage'],r['method'],r['pair_id']);require(key not in seen,'Duplicate score key');seen.add(key)
            if r['pair_id'] not in ref_pixels:ref_pixels[r['pair_id']]=r['pixels']
            require(ref_pixels[r['pair_id']]==r['pixels'],'Evaluation support size differs by condition')
            local[r['stage'],r['method']].append(r);converted.append(r)
        for (st,method),rows in local.items():
            require({r['pair_id'] for r in rows}==set(pair_map),'Incomplete sample coverage')
            require([r['pair_id'] for r in rows]==canon_order,'Saved row order differs from numeric scene/view order')
            require(sum(r['pixels'] for r in rows)==23112023,'Pixel count mismatch')
            groups[front,st,method]=rows
        all_rows[front]=converted;row_counts[front]=len(converted)
    require(len(groups)==40,'Wrong number of score conditions')
    # Verify reused D/seed11 statistics against the original uploaded evaluation CSV.
    historical=read_csv(sources/'initial_per_image.csv');lookup={(r['pair_id'],r['stage'],r['method']):r for r in all_rows['D']}
    hist_max=0.0
    for r in historical:
        method={'vfuse_best':'vfuse_seed11_best','vfuse_last':'vfuse_seed11_last'}.get(r['method'],r['method'])
        saved=lookup[r['pair_id'],r['stage'],method]
        for k in ('pixels','abs_sum_m','sq_sum_m2','mae_mm','over50_pixels'):
            delta=abs(float(saved[k])-float(r[k]));hist_max=max(hist_max,delta)
            require(delta<=1e-10,'Historical D scores changed')
    summary=[];scene_rows=[];loo_rows=[];smap={};lmap={}
    for key,rr in groups.items():
        front,stage,method=key;total=aggregate(rr);smap[key]=total
        summary.append(dict(frontend=front,stage=stage,method=method,**total))
        for scene in SCENES:
            sc=aggregate(r for r in rr if r['scene']==scene)
            scene_rows.append(dict(frontend=front,stage=stage,method=method,scene=scene,**sc))
            lo=aggregate(r for r in rr if r['scene']!=scene);lmap[(*key,scene)]=lo
            loo_rows.append(dict(frontend=front,stage=stage,method=method,left_out_scene=scene,**lo))
    maxima={}
    saved_summary=read_csv(sources/'summary_all.csv')
    require(len(saved_summary)==40,'Wrong saved summary size')
    for r in saved_summary: compare_metrics(smap[r['frontend'],r['stage'],r['method']],r,'overall',maxima)
    for front in FRONTS:
        saved_loo=read_csv(sources/f'{front}_saved_leave_one_scene.csv')
        require(len(saved_loo)==220,'Saved LOO incomplete')
        for r in saved_loo:
            compare_metrics(lmap[front,r['stage'],r['method'],int(r['left_out_scene'])],r,'LOSO',maxima)
        scmap={(r['stage'],r['method'],r['scene']):r for r in scene_rows if r['frontend']==front}
        saved_scenes=read_csv(sources/f'{front}_saved_per_scene.csv');require(len(saved_scenes)==220,'Saved scene table incomplete')
        for r in saved_scenes:compare_metrics(scmap[r['stage'],r['method'],int(r['scene'])],r,'scene',maxima)
    gate_rows=[];comparisons=[];changes=[];identities=[]
    for front in FRONTS:
        for seed in SEEDS:
            lock=model_locks['locks'][f'{front}_seed{seed}']
            for kind in ('best','last'):
                method=f'vfuse_seed{seed}_{kind}'
                identities.append(dict(frontend=front,seed=seed,checkpoint=kind,
                    epoch=lock['best_epoch'] if kind=='best' else 30,
                    checkpoint_path=lock[kind+'_path'],checkpoint_sha256=lock[kind+'_sha256'],
                    evidence_scope='recorded identity; model bytes not loaded in this analysis'))
                for stage in STAGES:
                    p=smap[front,stage,P];v=smap[front,stage,method];lo=[]
                    for scene in SCENES:
                        pp=lmap[front,stage,P,scene];vv=lmap[front,stage,method,scene]
                        er=pp['E_mae_mm']/vv['E_mae_mm'];qr=pp['Q_rmse_mm']/vv['Q_rmse_mm']
                        a=dict(frontend=front,stage=stage,seed=seed,checkpoint=kind,
                            omitted_scene=scene,remaining_images=pp['images'],remaining_pixels=pp['pixels'],
                            P_MAE_mm=pp['E_mae_mm'],V_MAE_mm=vv['E_mae_mm'],P_V_MAE_ratio=er,
                            P_RMSE_mm=pp['Q_rmse_mm'],V_RMSE_mm=vv['Q_rmse_mm'],P_V_RMSE_ratio=qr,
                            MAE_tolerance_ok=er<=RATIO_MAX,RMSE_tolerance_ok=qr<=RATIO_MAX,
                            P_minus_V_over50_pp_descriptive=100*(pp['over50_fraction']-vv['over50_fraction']))
                        lo.append(a);comparisons.append(a)
                    role='primary_best_reproduction' if kind=='best' and stage==STAGES[1] else ('posthoc_last_sensitivity_same_rule' if stage==STAGES[1] else 'original_output_diagnostic_same_rule_not_primary_gate')
                    gate_rows.append(dict(frontend=front,stage=stage,seed=seed,checkpoint=kind,
                        checkpoint_epoch=lock['best_epoch'] if kind=='best' else 30,analysis_role=role,
                        P_MAE_mm=p['E_mae_mm'],V_MAE_mm=v['E_mae_mm'],
                        P_RMSE_mm=p['Q_rmse_mm'],V_RMSE_mm=v['Q_rmse_mm'],
                        P_over50_pct=100*p['over50_fraction'],V_over50_pct=100*v['over50_fraction'],
                        **flags(p,v,lo)))
            for stage in STAGES:
                b=smap[front,stage,f'vfuse_seed{seed}_best'];l=smap[front,stage,f'vfuse_seed{seed}_last']
                changes.append(dict(frontend=front,stage=stage,seed=seed,best_epoch=lock['best_epoch'],last_epoch=30,
                    best_MAE_mm=b['E_mae_mm'],last_MAE_mm=l['E_mae_mm'],last_minus_best_MAE_mm=l['E_mae_mm']-b['E_mae_mm'],
                    best_RMSE_mm=b['Q_rmse_mm'],last_RMSE_mm=l['Q_rmse_mm'],last_minus_best_RMSE_mm=l['Q_rmse_mm']-b['Q_rmse_mm'],
                    last_minus_best_over50_pp=100*(l['over50_fraction']-b['over50_fraction'])))
    best_gates={(r['frontend'],r['seed']):r for r in gate_rows if r['stage']==STAGES[1] and r['checkpoint']=='best'}
    saved_criteria=read_csv(sources/'saved_best_criteria.csv')
    require(len(saved_criteria)==6,'Historical criteria table wrong size')
    for r in saved_criteria:
        cur=best_gates[r['frontend'],int(r['seed'])]
        require(cur['full_G4']==(r['G4_pass']=='True'),'Historical best G4 changed')
        for a,b in [('P_V_MAE_ratio','P_V_mae_ratio'),('P_V_RMSE_ratio','P_V_rmse_ratio')]:
            require(abs(cur[a]-float(r[b]))<1e-10,'Historical comparison ratio changed')
    outputs={'recomputed_overall.csv':summary,'recomputed_per_scene.csv':scene_rows,'recomputed_LOSO_metrics.csv':loo_rows,
             'best_last_full_G4.csv':gate_rows,'best_last_LOSO_comparisons.csv':comparisons,
             'best_last_checkpoint_changes.csv':changes,'checkpoint_identity.csv':identities}
    for name,rr in outputs.items():write_csv(out/name,rr)
    report=dict(status='CSV_SENSITIVITY_COMPLETE',rows_by_frontend=row_counts,total_rows=sum(row_counts.values()),
        conditions=len(groups),pairs_per_condition=2193,common_pixels_per_condition=23112023,
        scenes=list(SCENES),methods=list(METHODS),stages=list(STAGES),main_stage=STAGES[1],
        pair_manifest_sha256=sha(pairfile),unique_keys_and_complete_pair_coverage=True,
        per_pair_pixel_counts_same_all_conditions=True,
        caveat='Same counts cannot by themselves prove identical pixel membership; scoring source and fixed original mask protocol supply that definition. No pixels were rescored.',
        source_hashes_verified=True,paired_method_row_order_verified=True,
        image_MAE_unit_check_max_abs_difference_mm=mae_check_max,
        source_units=dict(abs_sum_m='metres',sq_sum_m2='metres squared',mae_mm='millimetres',over50_pixels='count above 0.05 m'),
        aggregation='image-equal MAE; pooled-pixel RMSE; pixel-pooled tail fraction',
        saved_summary_scene_and_LOSO_max_abs_differences=maxima,
        historical_D_rows_compared=len(historical),historical_D_max_numeric_difference=hist_max,
        saved_LOSO_tables_already_included_best_and_last=True,
        historical_best_G4_reproduced=True,
        G4=dict(max_error_ratio=RATIO_MAX,max_global_tail_difference_fraction=TAIL_MAX_FRACTION,
                max_global_tail_difference_percentage_points=100*TAIL_MAX_FRACTION,
                leave_one_constraints='MAE and RMSE ratios only; global tail bound unchanged',
                decision_on_unrounded_values=True,bootstrap_not_recomputed=True),
        original_stage_is_secondary_diagnostic=True,last_checkpoints_not_promoted=True,
        new_training=0,new_model_forwards=0,new_image_scoring=0,new_bootstrap=0,
        cpu_script_elapsed_seconds=time.perf_counter()-started,
        outputs={k:dict(rows=len(rr),sha256=sha(out/k)) for k,rr in outputs.items()})
    (out/'validation.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n')
    return report

def main() -> None:
    ap=argparse.ArgumentParser(description=__doc__);ap.add_argument('--sources',type=Path,required=True);ap.add_argument('--out',type=Path,required=True)
    args=ap.parse_args()
    try:
        report=run(args.sources,args.out)
    except (OSError,ValueError,KeyError,ValidationError) as ex:
        print(f'BLOCKED: {ex}',file=sys.stderr);sys.exit(2)
    print(json.dumps(report,ensure_ascii=False,indent=2))
if __name__=='__main__': main()
