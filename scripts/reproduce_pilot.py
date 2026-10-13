import csv, hashlib, itertools, json, math
from pathlib import Path
import numpy as np

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'outputs';OUT.mkdir(exist_ok=True)
def read(path):
    with path.open(encoding='utf-8',newline='') as f:return list(csv.DictReader(f))
def write(name,rows):
    with (OUT/name).open('w',encoding='utf-8',newline='') as f:
        w=csv.DictWriter(f,fieldnames=list(rows[0]));w.writeheader();w.writerows(rows)

for r in read(ROOT/'manifest.csv'):
    assert hashlib.sha256((ROOT/r['path']).read_bytes()).hexdigest()==r['sha256'],r['path']
qs=read(ROOT/'data/questions.csv');judgments=read(ROOT/'data/relevance.csv');scores=read(ROOT/'data/candidate_scores.csv')
assert len(qs)==98 and len({q['need_id'] for q in qs})==49
assert len({r['record_id'] for r in judgments})==67
assert len({q['query_id'] for q in qs})==len(qs)
byneed={};byscore={}
for r in judgments:
    byneed.setdefault(r['need_id'],{})[r['record_id']]=int(r['relevance'])
for r in scores:
    key=(r['query_id'],r['variant']);group=byscore.setdefault(key,{})
    assert r['record_id'] not in group
    group[r['record_id']]=float(r['score'])
metrics=[];rankings=[]
for q in qs:
    gold=byneed[q['need_id']];pool={n for n,v in gold.items() if v!=-1};relevant={n for n,v in gold.items() if v==1}
    assert relevant
    for variant in ['original','enriched']:
        sc=byscore[q['query_id'],variant];assert set(sc)==pool and all(math.isfinite(v) for v in sc.values())
        ordered=sorted(pool,key=lambda n:(-sc[n],n))
        for k in [1,3,5,10]:
            hits=[int(n in relevant) for n in ordered[:k]]
            dcg=sum(h/math.log2(i+2) for i,h in enumerate(hits))
            ideal=sum(1/math.log2(i+2) for i in range(min(k,len(relevant))))
            metrics.append(dict(query_id=q['query_id'],need_id=q['need_id'],family=q['family'],formulation=q['formulation'],variant=variant,cutoff=k,ndcg=dcg/ideal,hit=int(any(hits)),recall=sum(hits)/len(relevant)))
        rankings.extend(dict(query_id=q['query_id'],variant=variant,rank=i,record_id=n,relevance=int(n in relevant)) for i,n in enumerate(ordered[:10],1))
write('query_metrics.csv',metrics);write('rankings.csv',rankings)
families=sorted({q['family'] for q in qs});familytable=[];cutoffs=[];changes=[]
rng=np.random.default_rng(20261009);samples=rng.integers(0,len(families),size=(20000,len(families)))
for formulation in ['primary','paraphrase']:
    for k in [1,3,5,10]:
        vectors={}
        for variant in ['original','enriched']:
            subset=[r for r in metrics if r['formulation']==formulation and r['cutoff']==k and r['variant']==variant]
            row=dict(formulation=formulation,variant=variant,cutoff=k)
            for metric in ['ndcg','hit','recall']:
                fv=np.array([np.mean([r[metric] for r in subset if r['family']==f]) for f in families]);vectors[variant,metric]=fv;row[metric]=float(fv.mean())
            cutoffs.append(row)
        if k==10 and formulation=='primary':
            for f in families:
                a={r['need_id']:r['ndcg'] for r in metrics if r['family']==f and r['formulation']=='primary' and r['variant']=='original' and r['cutoff']==10}
                b={r['need_id']:r['ndcg'] for r in metrics if r['family']==f and r['formulation']=='primary' and r['variant']=='enriched' and r['cutoff']==10}
                ds=[b[n]-a[n] for n in a]
                familytable.append(dict(family=f,needs=len(a),original_ndcg10=float(np.mean(list(a.values()))),enriched_ndcg10=float(np.mean(list(b.values()))),change=float(np.mean(ds)),improved=sum(d>1e-12 for d in ds),unchanged=sum(abs(d)<=1e-12 for d in ds),declined=sum(d< -1e-12 for d in ds)))
        delta=vectors['enriched','ndcg']-vectors['original','ndcg'];lo,hi=np.quantile(delta[samples].mean(1),[.025,.975])
        pv=sum(abs(sum(s*d for s,d in zip(signs,delta)))>=abs(delta.sum())-1e-12 for signs in itertools.product([-1,1],repeat=len(families)))/2**len(families)
        changes.append(dict(formulation=formulation,cutoff=k,original_ndcg=float(vectors['original','ndcg'].mean()),enriched_ndcg=float(vectors['enriched','ndcg'].mean()),change=float(delta.mean()),ci_low=float(lo),ci_high=float(hi),exact_family_p=pv))
write('family_results.csv',familytable);write('cutoff_results.csv',cutoffs);write('paired_ndcg_results.csv',changes)
primary=next(r for r in changes if r['formulation']=='primary' and r['cutoff']==10)
expected=json.loads((ROOT/'reference/expected_primary.json').read_text())
for k,v in expected.items():assert math.isclose(primary[k],v,abs_tol=1e-12),k
cases=[];questionmap={q['need_id']:q for q in qs if q['formulation']=='primary'}
for nid,q in questionmap.items():
    a=next(r['ndcg'] for r in metrics if r['need_id']==nid and r['formulation']=='primary' and r['variant']=='original' and r['cutoff']==10)
    b=next(r['ndcg'] for r in metrics if r['need_id']==nid and r['formulation']=='primary' and r['variant']=='enriched' and r['cutoff']==10)
    if b>a+1e-12:cases.append(dict(need_id=nid,family=q['family'],question=q['text'],original_ndcg10=a,enriched_ndcg10=b,change=b-a))
assert len(cases)==11;write('illustrative_cases.csv',cases)
binary=[]
for k in [5,10]:
    rr=[r for r in metrics if r['formulation']=='primary' and r['cutoff']==k]
    a={r['need_id']:r['hit'] for r in rr if r['variant']=='original'};b={r['need_id']:r['hit'] for r in rr if r['variant']=='enriched'}
    gain=sum(b[n]>a[n] for n in a);loss=sum(b[n]<a[n] for n in a);n=gain+loss
    p=min(1,2*sum(math.comb(n,j) for j in range(min(gain,loss)+1))/2**n) if n else 1
    binary.append(dict(cutoff=k,original_hits=sum(a.values()),enriched_hits=sum(b.values()),gained=gain,lost=loss,nominal_exact_mcnemar_p=p))
write('binary_hits.csv',binary)
report={'status':'passed','scope':'Saved-score reproduction of the exploratory retrieval pilot only','model_reencoded':False,'source_judgments_independently_reaudited':False,'queries':len(qs),'information_needs':len(questionmap),'candidate_records':67,'families':len(families),'metric_rows':len(metrics),'ranking_rows':len(rankings),'primary':primary,'selected_cases':len(cases),'selected_original_mean':float(np.mean([r['original_ndcg10'] for r in cases])),'selected_enriched_mean':float(np.mean([r['enriched_ndcg10'] for r in cases]))}
(OUT/'verification.json').write_text(json.dumps(report,indent=2));print(json.dumps(report,indent=2))
