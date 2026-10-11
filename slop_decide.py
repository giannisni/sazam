import json, re, sys, glob, unicodedata
S,T=sys.argv[1],sys.argv[2]
def norm(s):
    s=unicodedata.normalize("NFKD",s).encode("ascii","ignore").decode().casefold()
    s=re.sub(r"[\(\[].*?[\)\]]","",s); s=re.sub(r"feat\..*","",s)
    return re.sub(r"[^a-z0-9]+"," ",s).strip()
def key(x):
    a,_,t=x.partition(" - "); a=norm(a); return (a.split()[:1] or [""])[0], norm(t)
def same(e,n):
    ea,et=key(e); na,nt=key(n)
    return bool(ea==na and et and nt and (et.startswith(nt) or nt.startswith(et)))
# verify-line agreement from transcript
texts=[]
for l in open(T):
    try: o=json.loads(l)
    except: continue
    c=o.get("message",{}).get("content")
    if isinstance(c,list):
        for b in c:
            if b.get("type")=="tool_result":
                x=b.get("content")
                if isinstance(x,list): x="\n".join(i.get("text","") for i in x if isinstance(i,dict))
                if isinstance(x,str): texts.append(x)
vlines={ln for t in texts for ln in t.splitlines() if " | " in ln and re.match(r"^\d+:\d\d ",ln)}
vparts=[ [p.strip() for p in ln.split(" ",1)[1].split(" | ")] for ln in vlines]
# scan runs
runs=[]
for p in glob.glob(S+"/*scan*.log"):
    step={"scan.log":30,"scan2.log":10}.get(p.split("/")[-1],20); seq=[]
    for l in open(p):
        m=re.match(r"\s*(\d+):(\d\d):(\d\d)\s+(.+)",l)
        if m and m[4].strip()!="--": seq.append((int(m[1])*3600+int(m[2])*60+int(m[3]),m[4].strip()))
    runs.append((step,seq))
def best_run(e):
    best=0
    for step,seq in runs:
        ts=[t for t,n in seq if same(e,n)]; cur=0; prev=None
        for t in ts:
            cur = cur+1 if prev is not None and t-prev<=step+1 else 1; prev=t; best=max(best,cur)
    return best
def best_agree(e):
    return max([sum(same(e,p) for p in ps) for ps in vparts]+[0])
counts=json.load(open(S+"/hitcounts.json"))
def total(e): return sum(v for n,v in counts.items() if same(e,n))
TRUSTED={"Underworld - Born Slippy (Nuxx)","Veracocha - Carte Blanche (Extended Mix)","Road Runner - Oh Yeah! (Club Mix)","DJ Misjah & DJ Tim - Access (Ky Jelly Babies Mix)"}
scores=json.load(open(S+"/slop_scores.json"))
rows=[]
for e,rank,_ in scores:
    r=rank or 0; run=best_run(e); ag=best_agree(e); tot=total(e)
    mainstream = r>=300000
    solid = e in TRUSTED or run>=3 or ag>=4
    rows.append((e,r,run,ag,tot,mainstream and not solid))
json.dump(rows,open(S+"/decisions.json","w"),ensure_ascii=False)
print("REMOVE (mainstream + weak evidence):")
for e,r,run,ag,tot,rm in sorted(rows,key=lambda x:-x[1]):
    if rm: print(f"  {r:>7}  run={run} agree={ag}/6 total={tot}  {e}")
print("\nKEEP mainstream (solid evidence):")
for e,r,run,ag,tot,rm in sorted(rows,key=lambda x:-x[1]):
    if r>=300000 and not rm: print(f"  {r:>7}  run={run} agree={ag}/6 total={tot}  {e}")
