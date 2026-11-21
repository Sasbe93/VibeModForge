"""cliff_outlines: organic cliff outlines. On each level mask (lvl>=k, k=1,2) measure the outline edges:
longest axis-aligned straight run (tiles), share of edge length in straight runs >=RUN tiles, corner density (turns per edge tile = diagonal steps/curvature)."""
import sys,os
sys.path.insert(0,os.path.dirname(os.path.abspath(__file__)))
from check_ranked_bw import sections,walkgrid
RUN=8
def metrics(path):
    s=sections(path);W,H,wk,lvl=walkgrid(s)
    runs=[];corners=0;elen=0
    for k in sorted({v for r in lvl for v in r}-{0}):
        L=[[lvl[y][x]>=k for x in range(W)] for y in range(H)]
        if not any(any(r) for r in L): continue
        # horizontal edges between row y and y+1; vertical edges between col x and x+1
        for y in range(H-1):
            r=0
            for x in range(W+1):
                e=x<W and L[y][x]!=L[y+1][x]
                if e: r+=1
                elif r: runs.append(r);r=0
        for x in range(W-1):
            r=0
            for y in range(H+1):
                e=y<H and L[y][x]!=L[y][x+1]
                if e: r+=1
                elif r: runs.append(r);r=0
        for y in range(H-1):
            for x in range(W-1):
                a,b,c,d=L[y][x],L[y][x+1],L[y+1][x],L[y+1][x+1]
                n=a+b+c+d
                if n in (1,3): corners+=1
                elif n==2 and a==d: corners+=2
    elen=sum(runs)
    if not elen: return dict(edge=0,longest=0,straight=0,corner=0)
    return dict(edge=elen,longest=max(runs),straight=sum(r for r in runs if r>=RUN)/elen,corner=corners/elen)
if __name__=='__main__':
    for f in sys.argv[1:]:
      try: print(os.path.basename(f)[:30].ljust(30),{k:round(v,3) for k,v in metrics(f).items()})
      except Exception as e: print("ERR",os.path.basename(f),e)

# calibration (cliff_outlines, refs n=29 unique): longest med 16 p90 24 max 38; straight med 0.116 p90 0.228 max 0.28; corner min 0.383 p10 0.40 med 0.464
LONG_FAIL=24;LONG_WARN=18;STR_FAIL=0.22;STR_WARN=0.16;COR_FAIL=0.38;COR_WARN=0.42
def check(path):
    F=[];I=[];m=metrics(path)
    I.append(f"cliff_outlines cliff outlines: longest straight run {m['longest']} (FAIL>{LONG_FAIL}, WARN>{LONG_WARN}), straight share {m['straight']:.3f} (WARN>{STR_WARN}), corners/edge {m['corner']:.3f} (WARN<{COR_WARN}); refs med 16/0.116/0.464")
    if m['edge']<300: return F,I
    if m['longest']>LONG_FAIL: F.append(f"cliff_outlines: cliff edge has a straight axis-aligned run of {m['longest']} tiles (> {LONG_FAIL}; refs p90 24)")
    if m['corner']<COR_FAIL: F.append(f"cliff_outlines: cliff outlines too angular: corner density {m['corner']:.3f} < {COR_FAIL} (refs min 0.383)")
    if m['straight']>STR_FAIL and m['corner']<0.40: F.append(f"cliff_outlines: cliff outlines too angular: straight share {m['straight']:.3f} > {STR_FAIL} and corner density {m['corner']:.3f} < 0.40")
    for c,t in ((m['longest']>LONG_WARN,'long straight run'),(m['straight']>STR_WARN,'high straight share'),(m['corner']<COR_WARN,'low corner density (few diagonal steps)')):
        if c: I.append(f"WARN cliff_outlines: {t}")
    return F,I
