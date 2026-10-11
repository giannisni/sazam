"""Flag likely Shazam false positives: mainstream (Deezer rank) + weak evidence (no sustained native-speed run)."""
import re, sys, json, glob, os, time, unicodedata, urllib.request, urllib.parse
S=sys.argv[1]; LIST=sys.argv[2]
LOGS={"scan.log":30,"scan2.log":10}  # AYIM passes; the rest use 20s steps
def norm(s):
    s=unicodedata.normalize("NFKD",s).encode("ascii","ignore").decode().casefold()
    s=re.sub(r"[\(\[].*?[\)\]]","",s); s=re.sub(r"feat\..*","",s)
    return re.sub(r"[^a-z0-9]+"," ",s).strip()
def split(x):
    a,_,t=x.partition(" - "); return norm(a), norm(t)
# --- evidence from scan logs: longest run of consecutive hits (seconds) per track
runs={}
for p in glob.glob(S+"/*scan*.log"):
    step=LOGS.get(os.path.basename(p),20); seq=[]
    for l in open(p):
        m=re.match(r"\s*(\d+):(\d\d):(\d\d)\s+(.*)",l)
        if not m: continue
        t=int(m[1])*3600+int(m[2])*60+int(m[3]); name=m[4].strip()
        if name!="--": seq.append((t,name))
    by={}
    for t,n in seq: by.setdefault(split(n),[]).append(t)
    for k,ts in by.items():
        best=cur=step; 
        for a,b in zip(ts,ts[1:]):
            cur = cur+step if b-a<=step+1 else step; best=max(best,cur)
        runs[k]=max(runs.get(k,0),best)
def evidence(entry):
    ea,et=split(entry); best=0
    for (a,t),r in runs.items():
        if t and et and (t.startswith(et) or et.startswith(t)) and a.split()[:1]==ea.split()[:1]: best=max(best,r)
    return best
def deezer(entry):
    a,_,t=entry.partition(" - ")
    q=re.sub(r"[\(\[].*?[\)\]]","",f"{a} {t}"); q=re.sub(r"feat\..*","",q)
    url="https://api.deezer.com/search?"+urllib.parse.urlencode({"q":q,"limit":5})
    for _ in range(3):
        try: d=json.load(urllib.request.urlopen(url,timeout=20)); break
        except Exception: time.sleep(2)
    else: return None
    ea,et=split(entry); best=0
    for x in d.get("data",[]):
        xa,xt=norm(x["artist"]["name"]),norm(x["title"])
        if ea.split()[:1]==xa.split()[:1] and (xt.startswith(et[:12]) or et.startswith(xt[:12])): best=max(best,x["rank"])
    return best
txt=open(LIST).read(); a,b=txt.split("\n\n\nUNCERTAIN")
entries=[l for l in a.splitlines()[2:] if l.strip()]+[l for l in b.splitlines()[2:] if l.strip()]
out=[]
for e in entries:
    r=deezer(e); ev=evidence(e); out.append((e,r,ev)); time.sleep(0.15)
json.dump(out,open(S+"/slop_scores.json","w"),ensure_ascii=False,indent=0)
for e,r,ev in sorted(out,key=lambda x:-(x[1] or 0)):
    if (r or 0)>=150000: print(f"{r:>8} rank  {ev:>4}s run  {e}")
