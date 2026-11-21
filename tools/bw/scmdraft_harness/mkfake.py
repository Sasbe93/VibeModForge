#!/usr/bin/env python3
"""Write synthetic stand-ins for the StarCraft data ScmDraft 2 reads at start-up into
$HARNESS/fakesc/{stardat,broodat,patch_rt}.mpq. Tileset files come from $TS (tools/lib/bw/tileset)."""
import os,struct
from eudplib.bindings._rust import mpqapi
H=os.environ['HARNESS']; TS=os.environ['TS']; FILES={}
def w(name,data): FILES[name]=data
def tbl(n,prefix):
    strs=[f'{prefix}{i}'.encode()+b'\0' for i in range(n)]; off=2+2*n; offs=[]; data=b''
    for s in strs: offs.append(off+len(data)); data+=s
    return struct.pack('<H',n)+struct.pack(f'<{n}H',*offs)+data
def pcx(wd,ht,fill=1):
    hdr=struct.pack('<BBBBHHHHHH',10,5,1,8,0,0,wd-1,ht-1,72,72)+b'\0'*48+bytes([0,1])+struct.pack('<HH',wd+(wd&1),1)+b'\0'*58
    row=bytes([fill]*(wd+(wd&1))); body=b''.join(row for _ in range(ht))
    return hdr+body+bytes([0x0C])+bytes(i*v%256 for i in range(256) for v in (1,3,7))
def grp(frames=1,wd=8,ht=8):
    base=6+8*frames; row=bytes([wd])+bytes([1]*wd); body=b''; fhs=b''
    for f in range(frames):
        lt=base+len(body); body+=struct.pack(f'<{ht}H',*[2*ht+i*len(row) for i in range(ht)])+row*ht
        fhs+=struct.pack('<BBBBI',0,0,wd,ht,lt)
    return struct.pack('<HHH',frames,wd,ht)+fhs+body
def fnt():   # 'FONT', first 0x20, last 0xff, max w/h 1; one 1x1 letter per char (w,h,x,y + 1 RLE byte)
    n=0xff-0x20; base=12+4*n
    return b'FONT'+bytes([0x20,0xff,1,1])+b'\0'*4+struct.pack(f'<{n}I',*[base+5*i for i in range(n)])+b'\x01\x01\x00\x00\x01'*n
w('rez\\stat_txt.tbl',tbl(1600,'S'))
for t in ['rez\\network','arr\\sfxdata','arr\\images','arr\\portdata','arr\\mapdata']: w(t+'.tbl',tbl(1600,'N'))
for n,size in dict(sfxdata=10296,units=19876,weapons=5460,flingy=3135,sprites=3229,images=37962,upgrades=1281,
                   techdata=836,orders=4158,portdata=1962,mapdata=260).items(): w(f'arr\\{n}.dat',b'\0'*size)
w('scripts\\iscript.bin',bytes.fromhex('10001600534350450000000002000200000004 00ffff0000'.replace(' ','')))
for f in ['8','10','12','14','16','16x','32','50']: w(f'font\\font{f}.fnt',fnt())
for n,(pw,ph) in {'game\\tunit':(128,1),'game\\tselect':(24,1),'game\\tminimap':(16,1),'game\\thpbar':(19,1),'game\\twire':(24,1),
                  'game\\ticon':(16,1),'game\\tfontgam':(64,3),'unit\\cmdbtns\\ticon':(16,1),'glue\\palmm\\tfont':(48,1)}.items(): w(n+'.pcx',pcx(pw,ph))
for n,fr in {'unit\\thingy\\Juice01':1,'unit\\thingy\\Juice02':1,'unit\\cmdbtns\\cmdicons':400,'unit\\cmdicons\\cmdicons':400,'unit\\wirefram\\wirefram':300}.items():
    w(n+'.grp',grp(fr))
spk=struct.pack('<HH',1,1)+struct.pack('<HHI',0,0,12)+struct.pack('<HH',1,1)+b'\x01'
w('parallax\\star.spk',spk)
for t in ['badlands','platform','install','ashworld','jungle','desert','ice','twilight']:
    cv5=open(f'{TS}/{t}.cv5','rb').read(); ng=len(cv5)//52
    mx=max(max(struct.unpack_from('<16H',cv5,g*52+20)) for g in range(ng))
    vx=open(f'{TS}/{t}.vx4','rb').read(); vx+=b'\0'*max(0,(mx+1)*32-len(vx))   # remastered cv5 references more megatiles
    for ext in ['cv5','vr4','wpe']: w(f'tileset\\{t}.{ext}',open(f'{TS}/{t}.{ext}','rb').read())
    w(f'tileset\\{t}.vx4',vx); w(f'tileset\\{t}.vf4',b'\0'*len(vx)); w(f'tileset\\{t}.grp',grp()); w(f'tileset\\{t}.spk',spk)
    w(f'tileset\\{t}\\dddata.bin',b'\0'*(512*256*2))
    for p in ['bexpl','bfire','blue','dark','gfire','ofire','shift','trans50']: w(f'tileset\\{t}\\{p}.pcx',pcx(256,256 if p=='trans50' else 32))
os.makedirs(f'{H}/fakesc',exist_ok=True); tmp=f'{H}/fakedata'; os.makedirs(tmp,exist_ok=True)
for i,(n,d) in enumerate(FILES.items()): open(f'{tmp}/{i}','wb').write(d)
for mp in ['stardat.mpq','broodat.mpq','patch_rt.mpq']:
    p=f'{H}/fakesc/{mp}'
    if os.path.exists(p): os.remove(p)
    m=mpqapi.MPQ.create(p,3,4096)
    for i,n in enumerate(FILES): m.add_file(n,f'{tmp}/{i}')
    m.compact(); del m
print(len(FILES),'synthetic files')
