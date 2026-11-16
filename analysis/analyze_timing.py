#!/usr/bin/env python3
"""Public I/O adaptation of the saved timing analyzer. Calculation functions unchanged.
Reads exported per-call CSV and bundled block records. No torch, GT, or scoring.
"""
from __future__ import annotations
import argparse, csv, json, math, sys
from collections import defaultdict
from pathlib import Path
import numpy as np
from common import PACKAGE, ProtocolError, checked_file, dump, load_json, read_csv, write_csv

P='source_prediction_mean'

def group_summary(rows):
    a=np.asarray([r['total_seconds'] for r in rows],dtype=np.float64)*1000
    if not len(a) or not np.isfinite(a).all() or np.any(a<=0):raise ProtocolError('Invalid measured timing values')
    return dict(calls=len(a),median_ms=float(np.median(a)),p90_ms=float(np.percentile(a,90)),
                mean_ms=float(np.mean(a)),min_ms=float(a.min()),max_ms=float(a.max()))

def validate_rows(rows,protocol,schedule):
    expected={}
    for b in schedule['blocks']:
        for rep,indices in enumerate(b['measured_orders']):
            for pos,idx in enumerate(indices):
                p=schedule['panel'][idx]
                key=(b['frontend'],b['method'],b['round'],rep,p['pair_id'])
                expected[key]=(b['block_index'],b['method_position'],pos,idx,int(p['scene']),int(p['view']))
    measured=[r for r in rows if r['phase']=='measured'];warm=[r for r in rows if r['phase']=='warmup']
    if len(rows)!=4224 or len(measured)!=3168 or len(warm)!=1056:
        raise ProtocolError('Incomplete run; do not produce full-run scientific summary')
    seen=set()
    for r in measured:
        key=(r['frontend'],r['method'],r['round'],r['repeat'],r['pair_id'])
        if key in seen or key not in expected:raise ProtocolError('Duplicate/unplanned measured call')
        seen.add(key)
        actual=tuple(r[k] for k in ['block_index','method_position','sequence_position','panel_index','scene','view'])
        if actual!=expected[key]:raise ProtocolError('Measured call ordering/pair mapping mismatch')
        if not math.isfinite(r['total_seconds']) or r['total_seconds']<=0:raise ProtocolError('Invalid time')
    if seen!=set(expected):raise ProtocolError('Missing paired calls')
    for b in schedule['blocks']:
        rr=[r for r in warm if r['block_index']==b['block_index']]
        if len(rr)!=33:raise ProtocolError('Warmup count changed')
        for r,idx in zip(rr,b['warmup_order']):
            if r['panel_index']!=idx or r['pair_id']!=schedule['panel'][idx]['pair_id']:
                raise ProtocolError('Warmup schedule changed')
    return measured,warm

def paired_comparisons(measured,protocol):
    keyed={(r['frontend'],r['method'],r['round'],r['repeat'],r['pair_id']):r for r in measured}
    pairs=[]
    for front in protocol['frontends']:
        ps=sorted([r for r in measured if r['frontend']==front and r['method']==P],key=lambda r:(r['round'],r['repeat'],r['panel_index']))
        for method in protocol['methods'][1:]:
            for p in ps:
                key=(front,method,p['round'],p['repeat'],p['pair_id'])
                if key not in keyed:raise ProtocolError('Unpaired P/V call')
                v=keyed[key];pp=p['total_seconds']*1000;vv=v['total_seconds']*1000
                pairs.append(dict(frontend=front,v_method=method,round=p['round'],repeat=p['repeat'],
                    pair_id=p['pair_id'],scene=p['scene'],view=p['view'],p_block=p['block_index'],v_block=v['block_index'],
                    p_ms=pp,v_ms=vv,P_minus_V_ms=pp-vv,paired_reduction_pct=100*(1-pp/vv)))
    return pairs

def paired_bootstrap(paired,protocol):
    """Scene resampling keeps every round/repeat and P/V pairing together.
    Uncertainty is conditional on this one panel/session; not independent calls.
    """
    results=[]
    for front in protocol['frontends']:
        for method in protocol['methods'][1:]:
            rr=[r for r in paired if r['frontend']==front and r['v_method']==method]
            groups={s:[r for r in rr if r['scene']==s] for s in sorted({r['scene'] for r in rr})}
            if len(groups)!=11 or any(len(x)!=36 for x in groups.values()):raise ProtocolError('Scene block incomplete')
            scenes=list(groups);arr={s:np.array([[r['p_ms'],r['v_ms']] for r in groups[s]]) for s in scenes}
            rng=np.random.default_rng(protocol['bootstrap_seed']);gains=[];diffs=[]
            for _ in range(protocol['bootstrap_replicates']):
                chosen=rng.choice(scenes,11,replace=True);z=np.concatenate([arr[int(s)] for s in chosen])
                gains.append(100*(1-np.median(z[:,0])/np.median(z[:,1])))
                diffs.append(np.percentile(z[:,0],90)-np.percentile(z[:,1],90))
            lo,hi=np.percentile(gains,[2.5,97.5]);dl,dh=np.percentile(diffs,[2.5,97.5])
            results.append(dict(frontend=front,v_method=method,replicates=protocol['bootstrap_replicates'],
                 seed=protocol['bootstrap_seed'],scene_groups=11,median_reduction_pct_ci_low=float(lo),median_reduction_pct_ci_high=float(hi),
                 p90_P_minus_V_ms_ci_low=float(dl),p90_P_minus_V_ms_ci_high=float(dh)))
    return results

def build_outputs(measured,paired,boots,legacy,protocol,out):
    summary=[];rounds=[];scenes=[];pairrows=[]
    for front in protocol['frontends']:
        for method in protocol['methods']:
            rr=[r for r in measured if r['frontend']==front and r['method']==method]
            summary.append(dict(frontend=front,method=method,**group_summary(rr)))
            for rnd in range(4):
                rounds.append(dict(frontend=front,method=method,round=rnd,**group_summary([r for r in rr if r['round']==rnd])))
            for sc in sorted({r['scene'] for r in rr}):
                scenes.append(dict(frontend=front,method=method,scene=sc,**group_summary([r for r in rr if r['scene']==sc])))
    summ={(x['frontend'],x['method']):x for x in summary};old={(x['frontend'],x['method']):x for x in legacy}
    ci={(x['frontend'],x['v_method']):x for x in boots};comparison=[]
    for front in protocol['frontends']:
        for method in protocol['methods'][1:]:
            p=summ[(front,P)];v=summ[(front,method)];op=old[(front,P)];ov=old[(front,method)]
            gain=100*(1-p['median_ms']/v['median_ms']);c=ci[(front,method)]
            pr=[r for r in paired if r['frontend']==front and r['v_method']==method]
            state=('lower median supported by conditional interval' if c['median_reduction_pct_ci_low']>0 else
                   'higher median supported by conditional interval' if c['median_reduction_pct_ci_high']<0 else
                   'direction uncertain under scene resampling')
            comparison.append(dict(frontend=front,v_method=method,
                old_calls_per_condition=int(op['warm_calls']),new_calls_per_condition=p['calls'],
                old_P_median_ms=float(op['warm_median_ms']),old_V_median_ms=float(ov['warm_median_ms']),
                old_P_p90_ms=float(op['warm_p90_ms']),old_V_p90_ms=float(ov['warm_p90_ms']),
                old_median_reduction_pct=100*(1-float(op['warm_median_ms'])/float(ov['warm_median_ms'])),
                resident_P_median_ms=p['median_ms'],resident_V_median_ms=v['median_ms'],
                resident_P_p90_ms=p['p90_ms'],resident_V_p90_ms=v['p90_ms'],
                resident_median_reduction_pct=gain,median_advantage_point=gain>0,p90_not_higher=p['p90_ms']<=v['p90_ms'],
                median_paired_P_minus_V_ms=float(np.median([r['P_minus_V_ms'] for r in pr])),
                median_per_call_reduction_pct=float(np.median([r['paired_reduction_pct'] for r in pr])),
                descriptive_15pct_and_p90_condition=bool(gain>=15 and p['p90_ms']<=v['p90_ms']),
                conditional_interval_interpretation=state,
                **{k:v for k,v in c.items() if k not in ('frontend','v_method')}))
            for pid in sorted({r['pair_id'] for r in pr}):
                aa=[r for r in pr if r['pair_id']==pid]
                pairrows.append(dict(frontend=front,v_method=method,pair_id=pid,scene=aa[0]['scene'],view=aa[0]['view'],
                    paired_calls=len(aa),P_median_ms=float(np.median([r['p_ms'] for r in aa])),
                    V_median_ms=float(np.median([r['v_ms'] for r in aa])),
                    median_paired_difference_ms=float(np.median([r['P_minus_V_ms'] for r in aa]))))
    for name,rows in [('summary.csv',summary),('per_round.csv',rounds),('per_scene.csv',scenes),
                      ('paired_calls.csv',paired),('paired_per_pair.csv',pairrows),('bootstrap_intervals.csv',boots),
                      ('new_vs_legacy.csv',comparison)]:write_csv(out/name,rows)
    lines=['# Resident-call timing: completed fixed-protocol comparison','',
      'This is a timing-only sensitivity analysis. No accuracy metrics were recomputed. Internally selected best checkpoints remain fixed.',
      '', '| Front end | V-best | Legacy median reduction | Resident median reduction | Resident conditional 95% interval | P p90 not higher |',
      '|---|---|---:|---:|---|---|']
    for r in comparison:
        lines.append(f"|{r['frontend']}|{r['v_method']}|{r['old_median_reduction_pct']:.2f}%|{r['resident_median_reduction_pct']:.2f}%|[{r['median_reduction_pct_ci_low']:.2f}, {r['median_reduction_pct_ci_high']:.2f}]%|{r['p90_not_higher']}|")
    lines += ['',f"The resident median is lower for P in {sum(r['median_advantage_point'] for r in comparison)}/6 comparisons. "
              f"The p90 is no higher in {sum(r['p90_not_higher'] for r in comparison)}/6 comparisons.",
      '', '## Interpretation limits',
      'The historical and resident protocols use the same inputs, frozen checkpoints, FP32 computation and timed processing path. The new protocol changes model lifecycle, allocator residency, fixed warmup, blocked order and repetitions; it is not a controlled causal estimate of cache-clearing overhead alone.',
      'The main reduction is 100 * (1 - median(P calls) / median(V calls)). The median of paired per-call ratios is separately named and is not substituted for it.',
      'Pairing uses the same front end, round, repeat and sample, with conditions measured sequentially. Blocking and balanced order reduce but do not eliminate temporal or OS-cache effects.',
      'Intervals resample the 11 scene groups, preserving all within-scene pairs/rounds/repeats. They are conditional on one machine, one 33-pair panel and one session; calls are not independent scenes.',
      'The optional 15%/p90 field describes how the new observations compare with the old numerical margin. It does not overwrite historical G5 or gate completion.',
      'No universal deployment, real-time throughput, energy or robot-task claim follows from these timings. Any smaller or reversed advantage must be retained.',
      '', '## Manuscript consequences',
      'Report the resident results beside the original cache-clearing results with their separate protocols. Keep the original percentages explicitly attached to the original protocol. Update any broader cost claim only if supported by the resident measurements. Accuracy results, best/last G4 and observation-gain claims are unchanged by timing alone.']
    (out/'REPORT.md').write_text('\n'.join(lines)+'\n',encoding='utf-8')
    return comparison

def analyze(run_dir, output):
    """Replay the supplied exported calls and saved block-state records, not a live run."""
    run=Path(run_dir).resolve()
    out=Path(output).resolve()
    if out.exists():
        raise ProtocolError('Refusing to overwrite an existing output directory')
    if out.is_relative_to(PACKAGE/'data') or out.is_relative_to(PACKAGE/'configs'):
        raise ProtocolError('Output must not be within archived data or configs')
    protocol=load_json(run/'protocol.json');schedule=load_json(run/'schedule.json')
    if load_json(run/'execution_status.json')['status'] not in ('TIMING_COMPLETE','COMPLETE_RESIDENT_TIMING'):
        raise ProtocolError('Saved controller record does not certify completion')
    completed=load_json(run/'block_completion.json')['blocks']
    by_index={int(c['block_index']):c for c in completed}
    if len(completed)!=32 or len(by_index)!=32:
        raise ProtocolError('Expected 32 saved block-completion records')
    for b in schedule['blocks']:
        c=by_index[b['block_index']]
        if c.get('status')!='COMPLETE_BLOCK' or c.get('state_before')!=c.get('state_after') or not c.get('bn_unchanged'):
            raise ProtocolError('Saved block completion/state verification failed')
        for key in ('round','frontend','method','method_position','warmup_order','measured_orders'):
            if c[key]!=b[key]:
                raise ProtocolError('Saved block completion differs from schedule')
    rows=read_csv(run/'per_call.csv')
    string_cols={'frontend','method','phase','pair_id','utc'}
    for r in rows:
        for key,value in r.items():
            if key in string_cols: continue
            r[key]=float(value) if key.endswith('_seconds') else int(value)
    measured,warm=validate_rows(rows,protocol,schedule)
    rec=protocol['sources']['legacy_summary.csv'];fp=PACKAGE/rec['snapshot']
    checked_file(fp,rec['sha256'],rec['bytes'])
    legacy=read_csv(fp)
    paired=paired_comparisons(measured,protocol)
    boots=paired_bootstrap(paired,protocol)
    out.mkdir(parents=True,exist_ok=False)
    write_csv(out/'per_call.csv',rows)
    comparison=build_outputs(measured,paired,boots,legacy,protocol,out)
    dump(out/'analysis_complete.json',dict(status='ARCHIVED_RECORD_REPLAY',all_calls=len(rows),
        measured=len(measured),warmup=len(warm),paired_comparisons=len(paired),
        comparisons=len(comparison),accuracy_metrics_recomputed=0,
        scope='Saved-record replay only; no model output, GPU execution, or historical provenance authentication.'))
    return out

if __name__=='__main__':
    parser=argparse.ArgumentParser(description='Optional replay of existing timing records; no new measurement or inference.')
    parser.add_argument('--run-dir',required=True)
    parser.add_argument('--out',required=True)
    args=parser.parse_args()
    try:
        print(analyze(args.run_dir,args.out))
    except (OSError,ValueError,KeyError,ProtocolError) as exc:
        print(f'BLOCKED: {exc}',file=sys.stderr)
        sys.exit(2)
