"""Find where candidate tracks occur in a mix, tolerant to tempo change.
usage: gmatch.py mix8k.raw files..."""
import numpy as np, sys, os, subprocess
SR=8000; N=1024; H=256; FPS=SR/H
MODE=os.environ.get("MODE","shape")
def feat(x):
    n=(len(x)-N)//H; w=np.hanning(N).astype(np.float32); out=[]
    for i in range(0,n,20000):
        j=np.arange(i,min(n,i+20000)); idx=np.arange(N)[None,:]+H*j[:,None]
        out.append(np.abs(np.fft.rfft(x[idx]*w,axis=1)).astype(np.float32))
    Sp=np.vstack(out)
    e=np.unique(np.geomspace(13,N//2,33).astype(int))  # ~100Hz..4kHz
    B=np.log(np.stack([Sp[:,a:b].sum(1) for a,b in zip(e[:-1],e[1:])],1)+1e-4)
    if MODE=="flux": return np.maximum(np.diff(B,axis=0),0)
    B=B-B.mean(1,keepdims=True)              # spectral shape, loudness-invariant
    k=int(2*FPS); ker=np.ones(k)/k
    for b in range(B.shape[1]): B[:,b]-=np.convolve(B[:,b],ker,'same')  # remove slow EQ drift
    return B.astype(np.float32)
def stretch(F,r):
    n=int(len(F)/r); t=np.arange(n)*r
    return np.stack([np.interp(t,np.arange(len(F)),F[:,b]) for b in range(F.shape[1])],1)
def load(p): return np.frombuffer(subprocess.check_output(["ffmpeg","-v","error","-i",p,"-ac","1","-ar",str(SR),"-f","f32le","-"]),dtype=np.float32)
mixF=feat(np.fromfile(sys.argv[1],dtype=np.float32)); M=len(mixF)
L=int(20*FPS)  # 20 s chunks (in mix time)
nfft=1<<int(np.ceil(np.log2(M+L)))
MF=np.fft.rfft(mixF,nfft,axis=0)
c=np.vstack([np.zeros((1,mixF.shape[1])),np.cumsum(mixF,0)]); c2=np.vstack([np.zeros((1,mixF.shape[1])),np.cumsum(mixF**2,0)])
mu=(c[L:]-c[:-L])/L; sd=np.sqrt(np.maximum((c2[L:]-c2[:-L])/L-mu**2,1e-9))
rates=np.round(np.arange(float(os.environ.get("R0",0.94)),float(os.environ.get("R1",1.061)),0.02),2)
for f in sys.argv[2:]:
    try: F=feat(load(f))
    except Exception as e: print("fail",f,e,flush=True); continue
    best=(0,0,0,0)
    for r in rates:
        G=stretch(F,r)
        for s in range(0,max(1,len(G)-L),int(30*FPS)):
            q=G[s:s+L]
            if len(q)<L: break
            q=(q-q.mean(0))/(q.std(0)+1e-6)
            R=np.fft.irfft(MF*np.conj(np.fft.rfft(q,nfft,axis=0)),nfft,axis=0)[:M-L+1]
            sc=(R/(sd*L)).mean(1); i=int(sc.argmax())
            if sc[i]>best[0]: best=(float(sc[i]),float(r),i/FPS,s/FPS*r)
    t=best[2]
    print(f"{best[0]:.3f}  mix {int(t)//60}:{int(t)%60:02d}  rate {best[1]:.2f}  (track {int(best[3])//60}:{int(best[3])%60:02d})  {os.path.basename(f)}",flush=True)
