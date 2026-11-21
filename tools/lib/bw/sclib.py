"""Shared builder for 'The Silent Swarm' campaign maps (CHK writer, ISOM terrain via Chkdraft core, TTS, preview)."""
import struct, os, math, random, subprocess, json, asyncio
from eudplib.bindings._rust import mpqapi
TOOLS=os.path.dirname(os.path.abspath(__file__))
TSNAMES=['badlands','platform','install','ashworld','jungle','desert','ice','twilight']
def _vcod():
    """StarEdit verification code (VCOD). Not shipped: it is Blizzard data present in every map.
    Generate it with tools/bw/extract_vcod.py (see external/README.md)."""
    p=os.environ.get('BW_VCOD_SEEDS','external/bw/vcod_seeds.txt')
    if not os.path.isfile(p):
        raise FileNotFoundError(f"{p} not found. Run: python3 tools/bw/extract_vcod.py <any .scx/.scm map> (or set BW_VCOD_SEEDS). See external/README.md.")
    seeds=[int(x,16) for x in open(p).read().replace('\n','').split(',') if x.strip()]
    return struct.pack('<256I',*seeds)+bytes([1,4,5,6,2,1,5,2,0,3,7,7,5,4,6,3])
# unit ids (fixed: 125=Bunker, 124=Missile Turret)
DRONE,OVERLORD,LARVA,ZERGLING,HYDRA,ULTRA,MUTA,GUARDIAN,QUEEN,DEFILER,SCOURGE,LURKER,DEVOURER=41,42,35,37,38,39,43,44,45,46,47,103,62
MATRIARCH,HATCH,LAIR,HIVE,POOL,HYDEN,EXTRACTOR,CREEP,SUNKEN,SPORE,EVO=49,131,132,133,142,135,149,143,146,144,139
MARINE,FIREBAT,MEDIC,GHOST,VULTURE,TANK,GOLIATH,WRAITH,BC,VALK,SCV=0,32,34,1,2,5,3,8,12,58,7
CC,BARRACKS,FACTORY,SUPPLY,BUNKER,TURRET,ACADEMY,REFINERY,STARPORT,EBAY=106,111,113,109,125,124,112,110,114,122
ZEALOT,DRAGOON,ARCHON,REAVER,CARRIER,SCOUT,DT,HT,PROBE,NEXUS,GATEWAY,PYLON,CANNON=65,66,68,83,72,70,61,67,64,154,160,156,162
MINERAL,GEYSER,STARTLOC,CRYSTAL,TEMPLE,XEL_TEMPLE,STASIS=176,188,214,173,174,175,168
ANYUNIT,MEN,BUILDINGS=229,230,231
# hero units + map revealer + beacons are never multiplied by the difficulty wave scale (fixes duplicate Kerrigan)
HEROES={101,10,16,17,19,20,21,22,23,25,27,28,29,48,49,51,52,53,54,75,76,77,78,79,86,87,88,98,99,100}|set(range(191,200))
BUILDSIZE={HATCH:(4,3),LAIR:(4,3),HIVE:(4,3),POOL:(3,2),HYDEN:(3,2),EXTRACTOR:(4,2),CREEP:(2,2),SUNKEN:(2,2),SPORE:(2,2),EVO:(3,2),
 CC:(4,3),BARRACKS:(4,3),FACTORY:(4,3),SUPPLY:(3,2),BUNKER:(3,2),TURRET:(2,2),ACADEMY:(3,2),STARPORT:(4,3),EBAY:(3,2),
 NEXUS:(4,3),GATEWAY:(4,3),PYLON:(2,2),CANNON:(2,2),MINERAL:(2,1),GEYSER:(4,2),CRYSTAL:(4,3),TEMPLE:(7,4),XEL_TEMPLE:(13,6),STASIS:(4,3)}
# Terran addons (2x2) and remaining buildings. An addon sits at parent top-left + (4,1) tiles (= parent centre + (96,16) px)
# AND must be linked to its parent in the UNIT section (use Map.addon(); see check_addon_attached.py).
COMSAT_,NUKESILO_,CTOWER_,COVERT_,PHYSICS_,MSHOP_=107,108,115,117,118,120
ADDON_PARENT={COMSAT_:CC,NUKESILO_:CC,CTOWER_:STARPORT,COVERT_:116,PHYSICS_:116,MSHOP_:FACTORY}
BUILDSIZE.update({a:(2,2) for a in ADDON_PARENT})
# Morph chains: a building that morphs becomes a NEW unit type (the engine changes the unit's type in place; unit
# counts move from the old type to the new one and no death is recorded). A destroy objective on the first type alone
# therefore fires when the target morphs, and a Deaths condition on it never fires once the target has morphed.
# Value = the type itself plus every type it can become.
MORPH_CHAIN={HATCH:(HATCH,LAIR,HIVE),LAIR:(LAIR,HIVE),CREEP:(CREEP,SUNKEN,SPORE),141:(141,137)}   # 141 Spire -> 137 Greater Spire
# (A Queen-infested Command Center becomes an Infested CC owned by the Zerg player: for the Terran owner it is gone.)
LIFTABLE={CC,BARRACKS,FACTORY,STARPORT,EBAY,116}   # Terran buildings that can lift off and leave a location
BUILDSIZE.update({116:(4,3),123:(3,2),REFINERY:(4,2),157:(4,2),EXTRACTOR:(4,2),
                  155:(3,2),159:(3,2),163:(3,2),164:(3,2),165:(3,2),166:(3,2),167:(4,3),169:(3,2),170:(3,2),171:(3,2),172:(2,2)})
GASB={REFINERY,EXTRACTOR,157}   # pre-placed gas buildings must carry the geyser's gas amount

def _peak(f):
    r=subprocess.run(['ffmpeg','-hide_banner','-i',f,'-af','volumedetect','-f','null','-'],capture_output=True,text=True).stderr
    import re; return float(re.search(r'max_volume: (-?[\d.]+) dB',r).group(1))
def loudify(src):
    """voice mastering: compression + limiter, then peak-normalise to -1 dBFS so lines cut through unit sounds."""
    dst=src[:-4]+'_loud.wav'
    if not os.path.exists(dst):
        tmp=src[:-4]+'_c.wav'
        subprocess.run(['ffmpeg','-y','-loglevel','error','-i',src,'-af','highpass=f=90,acompressor=threshold=-22dB:ratio=4:attack=4:release=90:makeup=8,alimiter=limit=0.89:level=false',
                        '-ar','22050','-ac','1','-acodec','pcm_s16le',tmp],check=True)
        g=-1.0-_peak(tmp)
        subprocess.run(['ffmpeg','-y','-loglevel','error','-i',tmp,'-af',f'volume={g:.2f}dB,alimiter=limit=0.891:level=false','-ar','22050','-ac','1','-acodec','pcm_s16le',dst],check=True)
        os.remove(tmp)
    Map.LOUDLOG[os.path.basename(src)]=_peak(dst)
    return dst
def _voice_script_render(script,voice,pitch,rate,fx,out):
    """VO markup -> wav via edge-tts segments (edge-tts reads SSML literally, so pauses/stress are done here)"""
    import sys as _s,tempfile,numpy as np,soundfile as sf,re as _re
    _s.path.insert(0,os.path.join(os.path.dirname(os.path.abspath(__file__)),'..'))
    import voice_delivery as VD
    base=int(_re.sub(r'[^-+0-9]','',rate) or 0)
    def synth(text,speed):
        r='%+d%%'%round(base+(speed-1)*100)
        with tempfile.TemporaryDirectory() as d:
            m=os.path.join(d,'s.mp3'); w=os.path.join(d,'s.wav')
            for k in range(6):
                q=subprocess.run(['edge-tts','--voice',voice,f'--pitch={pitch}',f'--rate={r}','--text',text,'--write-media',m],capture_output=True)
                if q.returncode==0 and os.path.getsize(m)>1000: break
                import time; time.sleep(3+k*4)
            else: raise RuntimeError('edge-tts failed: '+q.stderr.decode()[-300:])
            subprocess.run(['ffmpeg','-y','-loglevel','error','-i',m,'-ar','24000','-ac','1',w],check=True)
            return sf.read(w,dtype='float32')[0]
    a,_=VD.render(script,synth,24000,1.0)
    tmp=out[:-4]+'_vd.wav'; sf.write(tmp,a,24000)
    af=['-af',fx] if fx else []
    subprocess.run(['ffmpeg','-y','-loglevel','error','-i',tmp]+af+['-ar','22050','-ac','1','-acodec','pcm_s16le',out],check=True); os.remove(tmp)
def trim_tail(src):
    return trim_both(src)
def trim_both(src):
    """cut leading AND trailing silence (edge-tts adds ~200 ms in front and up to ~1 s behind); keeps 30 ms lead, 60 ms tail"""
    dst=src[:-4]+'_tt.wav'
    if not os.path.exists(dst):
        subprocess.run(['ffmpeg','-y','-loglevel','error','-i',src,'-af',
            'silenceremove=start_periods=1:start_threshold=-45dB:start_silence=0.03,'
            'areverse,silenceremove=start_periods=1:start_threshold=-45dB:start_silence=0.06,areverse',
            '-ar','22050','-ac','1','-acodec','pcm_s16le',dst],check=True)
    return dst
def _trim_tail_old(src):
    """cut trailing silence (TTS files end with up to ~1 s of silence) so speaker gaps stay short; keeps 60 ms tail"""
    dst=src[:-4]+'_t.wav'
    if not os.path.exists(dst):
        subprocess.run(['ffmpeg','-y','-loglevel','error','-i',src,'-af',
            'areverse,silenceremove=start_periods=1:start_threshold=-45dB:start_silence=0.06,areverse',
            '-ar','22050','-ac','1','-acodec','pcm_s16le',dst],check=True)
    return dst
# --- text colours ---
# Briefing text uses the glue palette: only these are bright there: 02 periwinkle, 03 lime, 04 yellow-green, 06 white, 07 red.
# In-game the same codes are 02 periwinkle, 03 yellow, 04 white, 06 red, 07 green -> readable in BOTH contexts.
# Speaker names (shared by briefing and in-game lines) must use one of NAME_COLOURS.
NAME_COLOURS={'white':'\x04','yellow':'\x03','green':'\x07','red':'\x06','blue':'\x02'}
BRIEF_OK=set('\x01\x02\x03\x04\x06\x07')
GAME_DARK=set('\x05\x0e\x10\x15\x18\x1c')
_FMT=set('\x09\x0a\x0b\x0c\x0d\x12\x13\x14')
def check_colours(t,briefing):
    import re as _re
    for mm in _re.finditer(r'([\x01-\x1f])([^\x01-\x1f]*)',t):
        c=mm.group(1)
        if not mm.group(2).strip() or c in _FMT: continue
        bad=(c not in BRIEF_OK) if briefing else (c in GAME_DARK)
        assert not bad, f'unreadable colour code \\x{ord(c):02x} in {"briefing" if briefing else "in-game"} text: {t[:60]!r} (use NAME_COLOURS)'
    return t
# BW hero unit ids (units.dat hero flag)
HERO_IDS={10,16,17,19,20,21,22,23,25,27,28,29,52,54,61,63,64,65,66,68,74,75,76,77,78,79,80,81,86,87,88,98,99,100,101,102}
class Map:
    def __init__(s,W,H,tileset,base_terrain,seed=1):
        assert W in (64,96,128,192,256) and H in (64,96,128,192,256), 'BW map sides must be 64/96/128/192/256 (minimap scaling)'
        s.W,s.H,s.ts,s.base_t=W,H,tileset,base_terrain; s.rnd=random.Random(seed)
        s.strings=['']; s.units=[]; s.mrgn=[b'\0'*20]*255; s.locs={}; s.trigs=[]; s.brief=[]; s.paint=[]; s.wavs=[]; s.wavfiles={}
        s.unitnames={}; s.unitstats={}; s.timelines=[]; s.cinelog=[]
        s.ownr=[0]*12; s.side=[7]*8+[4]*4; s.forces=[0]*8; s.forcenames=['Force 1','Force 2','Force 3','Force 4']; s.forceflags=[1,0,0,0]
        s.mrgn[63]=struct.pack('<IIIIHH',0,0,W*32,H*32,s.S('Anywhere'),0); s.locs['Anywhere']=(64,0,0,W,H)
    timelines=None
    def S(s,t):
        if t in s.strings[1:]: return s.strings.index(t)
        s.strings.append(t); return len(s.strings)-1
    # ---------- terrain painting ----------
    def blob(s,cx,cy,r,terrain,jit=0.3,seed=None):
        """organic blob centred at tile (cx,cy) radius r tiles; queued as ISOM diamonds"""
        ph=[s.rnd.random()*6.28 for _ in range(5)]; jit=max(jit,0.3)   # never near-circular/diamond: organic outline
        for dy in range(0,s.H+1):
            for dx in range(0,s.W//2+1):
                if (dx+dy)%2: continue
                tx,ty=dx*2,dy
                a=math.atan2(ty-cy,tx-cx)
                rr=r*(1+jit*(0.6*math.sin(2*a+ph[0])+0.4*math.sin(3*a+ph[1])+0.25*math.sin(5*a+ph[2])+0.3*math.sin(a+ph[4])))
                if (tx-cx)**2+(ty-cy)**2<rr*rr: s.paint.append((dx,dy,terrain,1))
    def path(s,pts,width,terrain):
        for (x0,y0),(x1,y1) in zip(pts,pts[1:]):
            n=int(max(abs(x1-x0),abs(y1-y0))/2)+1
            L=max(1e-6,math.hypot(x1-x0,y1-y0)); nx,ny=-(y1-y0)/L,(x1-x0)/L; ph=s.rnd.random()*6.28
            for i in range(n+1):
                t=i/n; amp=min(6.0,L/5)*math.sin(math.pi*t)   # organic meander, anchored at the waypoints
                off=amp*(0.6*math.sin(2*math.pi*t*1.7+ph)+0.4*math.sin(2*math.pi*t*3.3+ph*2))
                w=width*(0.8+0.4*s.rnd.random())
                s.blob(x0+(x1-x0)*t+nx*off,y0+(y1-y0)*t+ny*off,w,terrain,0.35)
    def edges(s,terrain,skip=(),step=3,mix=None):
        """natural map border: perimeter split into irregular stretches (8-22 tiles), each one high ground/cliff,
        tileset obstacle (water/lava/space) or plain ground, with a noisy depth (0-7 tiles) - never a straight seam."""
        mix=list(mix or [terrain]); per=[]
        for x in range(0,s.W,step): per.append((x,0))
        for y in range(0,s.H,step): per.append((s.W-1,y))
        for x in range(s.W-1,-1,-step): per.append((x,s.H-1))
        for y in range(s.H-1,-1,-step): per.append((0,y))
        i=0; last=None
        while i<len(per):
            seg=s.rnd.randint(3,7); t=s.rnd.choice([m for m in mix+[None] if m!=last] or mix); last=t
            base=1.5+s.rnd.random()*4.5
            for k,(x,y) in enumerate(per[i:i+seg]):
                if t is None or any((x-a)**2+(y-b)**2<r*r for a,b,r in skip): continue
                r=max(1.2,base+(s.rnd.random()-.5)*2.5)
                ox=(s.rnd.random()-.5)*4; oy=(s.rnd.random()-.5)*4
                s.blob(min(max(x+ox,0),s.W-1),min(max(y+oy,0),s.H-1),r,t,0.5)
                if s.rnd.random()<0.25: s.blob(min(max(x+ox*2,0),s.W-1),min(max(y+oy*2,0),s.H-1),r*0.6,t,0.5)   # ragged spurs
            i+=seg
    def build_terrain(s):
        tmp=f'/tmp/isom_{os.getpid()}'
        with open(tmp+'.txt','w') as f:
            f.write(f'{s.W} {s.H} {s.base_t}\n')
            seen=set()
            for p in s.paint:
                f.write('%d %d %d %d\n'%p)
        cv5=f'{TOOLS}/tileset/{TSNAMES[s.ts]}.cv5'
        if not os.path.exists(f'{TOOLS}/isomtool') or not os.path.exists(cv5):
            raise SystemExit(f'build_terrain needs the ISOM terrain tool {TOOLS}/isomtool and the tileset file {cv5}. '
                             'Build isomtool and install the tileset files first (docs/bw-terrain-setup.md). '
                             'There is no fallback terrain: do not ship rectangle plateaus.')
        r=subprocess.run([f'{TOOLS}/isomtool',cv5,str(s.ts),tmp+'.txt',tmp+'.bin'],capture_output=True,text=True)
        if r.returncode!=0 or not os.path.exists(tmp+'.bin'):
            raise SystemExit(f'isomtool failed (exit {r.returncode}): {r.stderr.strip()[-400:]} (docs/bw-terrain-setup.md)')
        d=open(tmp+'.bin','rb').read()
        s.mtxm=d[:s.W*s.H*2]
        isom=bytearray(d[s.W*s.H*2:])
        for i in range(0,len(isom),2):
            v=struct.unpack_from('<H',isom,i)[0]&0xFFF0; struct.pack_into('<H',isom,i,v)
        s.isom=bytes(isom); assert len(s.isom)==(s.W//2+1)*(s.H+1)*8
    # ---------- units ----------
    def unit(s,uid,x,y,owner,res=0,hp=100,flags=0,pixel=False):
        """x,y = top-left tile for buildings/resources, tile for units; pixel=True for raw px centre"""
        if pixel: px,py=int(x),int(y)
        elif uid in BUILDSIZE:
            w,h=BUILDSIZE[uid]; px,py=int(x*32+w*16),int(y*32+h*16)
        else: px,py=int(x*32+16),int(y*32+16)
        if uid in GASB and res==0: res=5000   # fix: a pre-placed Refinery/Extractor/Assimilator keeps its gas (was 0)
        valid=0x10 if uid in (MINERAL,GEYSER) else 0x1F if uid!=STARTLOC else 0
        # unique class instance (serial): len(s.units)+1 repeated a serial after gas_building() popped a geyser,
        # and add-on links point at serials, so they must be unique
        ser=max([getattr(s,'_ser',0)]+[struct.unpack_from('<I',r,0)[0] for r in s.units[-1:]])+1; s._ser=ser
        s.units.append(struct.pack('<IHHHHHHBBBBIHHII',ser,px,py,uid,0,0x1F if flags else 0,valid,owner,hp,100,100,res,0,flags,0,0))
        return ser
    def addon(s,uid,px_,py_,owner):
        """attach addon `uid` to the pre-placed parent building whose top-left tile is (px_,py_).
        Position alone does NOT attach an add-on in the game: StarEdit/ScmDraft maps link both units in the UNIT
        section - relation field bit 9 (0x200) on BOTH records, and each record's last u32 = the other unit's serial.
        Verified on all 328 add-ons in 17 third-party campaign maps: addon centre = parent centre + (96,16) px, i.e.
        addon top-left tile = parent top-left + (4,1). Trigger 'Create Unit' cannot attach add-ons: pre-place them."""
        assert uid in ADDON_PARENT, f'unit {uid} is not a Terran add-on'
        pid=ADDON_PARENT[uid]; pc=(px_*32+64,py_*32+48)
        pi=[i for i,r in enumerate(s.units) if struct.unpack_from('<H',r,8)[0]==pid and r[16]==owner and struct.unpack_from('<HH',r,4)==pc]
        assert pi, f'addon {uid}: no parent {pid} of player {owner} with top-left tile ({px_},{py_}); place the parent first'
        pr=bytearray(s.units[pi[0]])
        assert struct.unpack_from('<I',pr,32)[0]==0, f'parent at ({px_},{py_}) already has an add-on'
        ser=s.unit(uid,px_+4,py_+1,owner); pser=struct.unpack_from('<I',pr,0)[0]
        ar=bytearray(s.units[-1]); struct.pack_into('<H',ar,10,0x200); struct.pack_into('<I',ar,32,pser); s.units[-1]=bytes(ar)
        struct.pack_into('<H',pr,10,0x200); struct.pack_into('<I',pr,32,ser); s.units[pi[0]]=bytes(pr)
        return ser
    def gas_building(s,uid,owner,gx,gy,amount=5000):
        """pre-placed gas building on the geyser at top-left tile (gx,gy); the geyser unit is replaced and its gas kept"""
        gp=(gx*32+64,gy*32+32); keep=amount
        for i,r in enumerate(s.units):
            if struct.unpack_from('<H',r,8)[0]==GEYSER and struct.unpack_from('<HH',r,4)==gp:
                keep=struct.unpack_from('<I',r,20)[0] or amount; s.units.pop(i); break
        s.unit(uid,gx,gy,owner,res=keep)
    def base(s,hx,hy,owner,side='left',hall=HATCH,minerals=9,geysers=1,amount=None,gas=5000,expansion=False,enemy=None):
        """Blizzard-like staggered mineral arc. hx,hy = top-left of 4x3 town hall.
        Enemy bases (enemy=True, or owner is a computer slot): fields default to varied 2500-4000 and are clamped at 4000
       . Player bases default to 1500."""
        if enemy is None: enemy=owner<8 and s.ownr[owner]==5
        if enemy:
            rnd=random.Random(hx*1000+hy)
            if amount is not None and amount>4000: print(f'sclib: enemy mineral amount {amount} clamped to 4000')
            amt=[min(4000,amount) if amount is not None else rnd.randrange(2500,4001,250) for _ in range(9)]
        else: amt=[1500 if amount is None else amount]*9
        arc=[(-5,-4),(-6,-3),(-7,-2),(-6,-1),(-7,0),(-6,1),(-7,2),(-6,3),(-5,4)][:minerals] if minerals<=9 else []
        gy=[(0,-5),(0,5)][:geysers]
        for k,(dx,dy) in enumerate(arc):
            amount=amt[k]
            if side=='left': s.unit(MINERAL,hx+dx,hy+dy,11,amount)
            elif side=='right': s.unit(MINERAL,hx+2-dx,hy+dy,11,amount)
            elif side=='up': s.unit(MINERAL,hx+dy+1,hy+dx+1,11,amount)
            else: s.unit(MINERAL,hx+dy+1,hy+2-dx,11,amount)
        for dx,dy in gy:
            if side in('left','right'): s.unit(GEYSER,hx+dx,hy+dy if dy<0 else hy+6,11,gas)   # 3-tile gap both sides (was hy+4 = 1-tile gap, geyser touching the hall)
            else: s.unit(GEYSER,hx+(-7 if dy<0 else 7),hy+0,11,gas)   # 3-tile gap (was +-6 = 2)
        if not expansion: s.unit(hall,hx,hy,owner)
    def loc(s,name,x0,y0,x1,y1,idx=None):
        idx=idx or len([k for k in s.locs if k!='Anywhere'])+1
        s.mrgn[idx-1]=struct.pack('<IIIIHH',int(x0*32),int(y0*32),int(x1*32),int(y1*32),s.S(name),0); s.locs[name]=(idx,x0,y0,x1,y1); return idx
    def L(s,n): return s.locs[n][0]
    # ---------- audio ----------
    LOUDLOG={}
    def voice(s,key,text,voice,pitch='+0Hz',rate='+0%',fx='',script=None,speaker=None,profile=None):
        """generate TTS wav, return (stringid,ms).
        script: VO markup v1 delivery notes for this line (tools/lib/voice_delivery.py, rule voice_delivery): rendered
        segment by segment (pauses = silence, tempo/pitch/volume per emotion, local stress); the subtitle stays `text`.
        speaker/profile: recorded with the script; write_voice_script() saves Voice_Script_<name>.md next to the map."""
        import hashlib,time as _t
        if not hasattr(s,'voice_rows'): s.voice_rows=[]; s.voice_profiles={}
        s.voice_rows.append(dict(id=key,speaker=speaker or '?',text=text,script=script or ''))
        if speaker and profile: s.voice_profiles[speaker]=profile
        hsh=hashlib.md5(repr((text,voice,pitch,rate,fx) if not script else (script,voice,pitch,rate,fx,'vd1')).encode()).hexdigest()[:10]
        os.makedirs('.cache/tts',exist_ok=True)
        out=f'.cache/tts/{key}_{hsh}.wav'; mp3=out+'.mp3'
        if script and not os.path.exists(out):
            _voice_script_render(script,voice,pitch,rate,fx,out)
        if not os.path.exists(out):
            for k in range(6):
                r=subprocess.run(['edge-tts','--voice',voice,f'--pitch={pitch}',f'--rate={rate}','--text',text,'--write-media',mp3],capture_output=True)
                if r.returncode==0 and os.path.getsize(mp3)>1000: break
                _t.sleep(3+k*4)
            else: raise RuntimeError('edge-tts failed: '+r.stderr.decode()[-300:])
            af=['-af',fx] if fx else []
            subprocess.run(['ffmpeg','-y','-loglevel','error','-i',mp3]+af+['-ar','22050','-ac','1','-acodec','pcm_s16le',out],check=True)
        out=trim_tail(loudify(out))
        ms=int(float(subprocess.run(['ffprobe','-v','error','-show_entries','format=duration','-of','csv=p=0',out],capture_output=True,text=True).stdout)*1000)
        arch=f'staredit\\wav\\{key}.wav'; sid=s.S(arch); s.wavfiles[arch]=out
        if sid not in s.wavs: s.wavs.append(sid)
        return sid,ms
    def write_voice_script(s,path,title,profiles=None):
        """Voice_Script_<map>.md: subtitles + delivery notes + speaker profiles (checked by tools/bw/check_voice_delivery.py)"""
        import sys as _s; _s.path.insert(0,os.path.join(os.path.dirname(os.path.abspath(__file__)),'..'))
        import voice_delivery as VD
        VD.write_script_md(path,title,getattr(s,'voice_rows',[]),dict(getattr(s,'voice_profiles',{}),**(profiles or {})))
    # ---------- triggers ----------
    @staticmethod
    def cond(ctype,loc=0,player=0,qty=0,unit=0,cmp=0,res=0,flags=0x10):
        return struct.pack('<IIIHBBBBH',loc,player,qty,unit,cmp,ctype,res,flags,0)
    @staticmethod
    def act(atype,loc=0,s=0,wav=0,time=0,player=0,num=0,unit=0,mod=0,flags=0x14):
        return struct.pack('<IIIIIIHBBB3x',loc,s,wav,time,player,num,unit,atype,mod,flags)
    def _pack(s,players,conds,acts):
        assert len(conds)<=16 and len(acts)<=64, (len(conds),len(acts))
        c=b''.join(conds)+b'\0'*20*(16-len(conds)); a=b''.join(acts)+b'\0'*32*(64-len(acts))
        pl=bytearray(28)
        for p in players: pl[p]=1
        return c+a+struct.pack('<I',0)+bytes(pl)
    LOCK=249   # switch 250 = 'talking' lock
    # Rule: silence between two spoken lines <= 1 s; interruption = 0; a longer pause ONLY
    # when explicitly requested for an afterward 'scheming with the player' beat (scheme=True).
    GAP=250    # default pause after a line (in-mission); + <=84 ms trigger latency with hyper triggers
    BGAP=250   # default pause after a line (briefing)
    MAXGAP=1000
    @staticmethod
    def _setgap(a,gap,scheme=False):
        """per-line pause stored in the action's padding bytes 29-31 (stripped again before the map is written)"""
        if gap is None: return a
        assert gap<=Map.MAXGAP or scheme, f'pause {gap} ms > 1 s: only allowed with scheme=True (scheming beat)'
        b=bytearray(a); b[29:31]=struct.pack('<H',min(gap,65534)+1); b[31]=1 if scheme else 0; return bytes(b)
    @staticmethod
    def _getgap(a,default):
        g=struct.unpack_from('<H',a,29)[0]; return (g-1 if g else default), bool(a[31])
    @staticmethod
    def _clean(a): return a[:29]+b'\0\0\0' 
    LEADERBOARD={17,18,19,20,21,33,34,35,36,37,38,39,40}-{38}   # 38 = Move Location, not a leaderboard
    allow_leaderboard=False   # BW cannot hide a leaderboard: it stays on screen after its objective is done
    def T(s,players,conds,acts):
        acts=[a for a in acts if a is not None]
        # Predelivery check 28: a Map Revealer created here is removed again at the end of this trigger
        # unless a Comment action says REVEAL_PERMANENT_OK (or a removal of it is already in the trigger).
        perm=any(a[26]==47 and 'REVEAL_PERMANENT_OK' in s.strings[struct.unpack_from('<I',a,4)[0]] for a in acts)
        if not perm:
            for a in [a for a in acts if a[26]==44 and struct.unpack_from('<H',a,24)[0]==101]:
                p_,l_=struct.unpack_from('<I',a,16)[0],struct.unpack_from('<I',a,0)[0]
                if not any(b[26] in (22,23,24,25) and struct.unpack_from('<H',b,24)[0] in (101,229) and struct.unpack_from('<I',b,16)[0]==p_ for b in acts):
                    acts=acts+[s.wait(s.REVEAL_MS),s.act(25,loc=l_,player=p_,unit=101,mod=0,flags=0x04)]
        # Set HP is not damage: a unit already below the value gets HEALED. Only allowed on units this trigger just created.
        for i,x in enumerate(acts):
            if x[26]==49 and struct.unpack_from('<I',x,20)[0]<100 and not any(y[26]==44 and y[24:26]==x[24:26] and y[16:20]==x[16:20] for y in acts[:i]):
                print('WARNING sclib: Modify Unit Hit Points <100% on existing units can heal them - use Kill/real damage instead (predelivery check 15 fails)')
        assert s.allow_leaderboard or not any(a[26] in (17,18,19,20,21,33,34,35,36,37,39,40) for a in acts), \
            'leaderboards cannot be removed in BW and stay after the objective is done: use progress text messages (or set m.allow_leaderboard for a whole-mission board)' 
        # voice lines: each Transmission blocks for its measured WAV duration; add a fixed gap after it,
        # and wrap the trigger in the 'talking' lock so no two conversations can overlap.
        if not getattr(s,'_instag',False) and any(a[26]==44 and struct.unpack_from('<I',a,16)[0] not in (0,7) and struct.unpack_from('<I',a,12)[0] not in (0xC1A5,0xF05F) and struct.unpack_from('<H',a,24)[0] not in HEROES|{101,33,202,194} for a in acts):
            # Rule: enemy trigger spawns trickle out one small group (<=4) after another, 5 s apart, from that enemy's own trigger
            new=[]; per={}
            for a in acts:
                pl=struct.unpack_from('<I',a,16)[0]
                if a[26]==44 and pl not in (0,7) and struct.unpack_from('<I',a,12)[0] not in (0xC1A5,0xF05F) and struct.unpack_from('<H',a,24)[0] not in HEROES|{101,33,202,194}:
                    per.setdefault(pl,[[],[]])[0].append(a); continue
                if a[26]==46 and pl in per: per[pl][1].append(a); continue
                new.append(a)
            for pl,(cr,od) in per.items():
                units=[(a,1) for a in cr for _ in range(a[27])]
                # meridian: balanced groups of 2-4 (never a lone straggler): n units -> ceil(n/3) groups, sizes differ by <=1
                k=max(1,-(-len(units)//3)); sz=[len(units)//k+(1 if i<len(units)%k else 0) for i in range(k)]
                chunks=[];i0=0
                for z in sz: chunks.append([a for a,_ in units[i0:i0+z]]); i0+=z
                seq=[]
                for i,ch in enumerate(chunks):
                    if i: seq.append(s.wait(5000))
                    cnt={}
                    for a in ch: cnt[a]=cnt.get(a,0)+1
                    for a,k in cnt.items(): b=bytearray(a); b[27]=k; seq.append(bytes(b))
                    seq+=od
                s.spawnlog=getattr(s,'spawnlog',[])+[(pl,struct.unpack_from('<I',cr[0],0)[0],[len(c) for c in chunks])]
                while seq:
                    part,seq=seq[:60],seq[60:]
                    sw=getattr(s,'stagsw',150); s.stagsw=sw+1; assert sw<240,'out of switches'
                    new.append(s.setsw(sw)); s._instag=True
                    s.T([pl],[s.SW(sw)],[s.setsw(sw,False)]+part); s._instag=False
            acts=new
        nx=getattr(s,'nextmap',None)
        if nx: acts=[y for a in acts for y in ([s.act(41,s=s.S(nx),flags=0x04),a] if a[26]==1 else [a])]   # Set Next Scenario before Victory
        out=[];talk=False;t=0;tl=[]
        # the pause after a line is set by the NEXT line's gap (gap=0 -> interruption: starts right away)
        voice=[a for a in acts if a[26] in (7,8)]
        nextgap={id(a):s._getgap(b,s.GAP) for a,b in zip(voice,voice[1:])}
        for a in acts:
            typ=a[26]
            if typ in (7,8):
                g,sch=nextgap.get(id(a),(s.GAP,False))
                ms=struct.unpack_from('<I',a,20 if typ==7 else 12)[0]; tl.append((t,t+ms,g,sch))
                a=s._clean(a)
                if typ==7: out+=[a]+([s.wait(g)] if g else []); t+=ms+g
                else: out+=[a,s.wait(ms+g)]; t+=ms+g
                talk=True
            else:
                if typ==4: t+=struct.unpack_from('<I',a,12)[0]
                out.append(s._clean(a))
        if talk:
            conds=list(conds)+[s.SW(s.LOCK,False)]
            lines=len(tl); cine=lines>=2   # story conversation -> cinematic pseudo-pause; single barks stay live
            pre=[s.setsw(s.LOCK),s.act(30,flags=0x04)]          # Mute Unit Speech
            post=[s.act(31,flags=0x04),s.setsw(s.LOCK,False)]  # Unmute Unit Speech
            if cine:
                rev=[a for a in out if a[26]==44 and struct.unpack_from('<H',a,24)[0]==101]
                if rev:
                    out=[a for a in out if not (a[26]==44 and struct.unpack_from('<H',a,24)[0]==101)]
                    pre+=rev+[s.wait(250)]          # let the revealer's vision update before the game pauses
                # Verified BW rule (scmjs trigger reference): Pause Game works for a human's trigger in single player;
                # triggers keep running while paused (Wait + Transmission still count down), game clock and countdown stop,
                # and the game auto-unpauses when the pausing trigger ends. Pause Timer/Unpause Timer is the fallback that
                # still protects countdowns if the map is played via multiplayer/LAN (where Pause Game does nothing).
                tloc=next((struct.unpack_from('<I',a,0)[0] for a in out if a[26]==7),0)
                pre+=([s.act(10,loc=tloc,flags=0x04)] if tloc else [])+[s.act(5,flags=0x04),s.act(54,flags=0x04)]   # centre camera on the scene, pause
                post=[s.act(55,flags=0x04),s.act(6,flags=0x04)]+post
                s.cinelog.append(('trig%d'%len(s.trigs),lines))
            out=pre+out+post
            s.timelines.append(('trig%d'%len(s.trigs),[x[:2] for x in tl],[x[2:] for x in tl]))
        s.trigs.append(s._pack(players,conds,out))
    def B(s,acts):
        # briefing transmissions do NOT pause the briefing; insert an explicit Wait (duration + gap) after each.
        # Each line = Display Speaking Portrait + Play WAV + Text Message (all non-blocking, Blizzard's own
        # briefing pattern) followed by ONE Wait(duration + pause). The old briefing Transmission (action 8) is
        # never used by Blizzard and also holds the briefing for its duration, so Transmission + Wait(ms+gap)
        # doubled every line: the next speaker started a whole line-length late.
        flat=[]
        for a in acts: flat+=(a if isinstance(a,list) else [a])
        acts=flat; isline=lambda i: acts[i][26]==2 and i+2<len(acts) and acts[i+2][26]==0xFE
        for i in range(len(acts)):
            if isline(i): acts[i]=bytes(acts[i][:28])+b'\xA5'+bytes(acts[i][29:])   # temp tag in flags
        out=[];t=0;tl=[];gaps=[]
        lines=[a for a in acts if a[26]==2 and a[28]==0xA5]
        nextgap={id(a):s._getgap(b,s.BGAP) for a,b in zip(lines,lines[1:])}
        for a in acts:
            if a[26]==2 and a[28]==0xA5:
                g,sch=nextgap.get(id(a),(s.BGAP,False)); ms=struct.unpack_from('<I',a,12)[0]
                out.append(s._clean(a[:28]+b'\x04'+a[29:])); tl.append((t,t+ms)); gaps.append((g,sch))
                s._bpend=(ms,g)
            elif a[26]==0xFE:   # end of a line bundle -> the single wait
                ms,g=s._bpend; out.append(s.b_wait(ms+g)); t+=ms+g
            else:
                out.append(s._clean(a))
                if a[26]==1: t+=struct.unpack_from('<I',a,12)[0]
        assert not any(a[26]==8 for a in out), 'briefing Transmission (8) is banned: use b_trans()'
        out=[a for a in out if a[26]!=0xFE]
        s.timelines.append(('briefing',tl,gaps))
        s.brief.append(s._pack([0],[s.cond(13,flags=0)],out))
    def check_timelines(s):
        """no overlap, and silence between consecutive lines <= MAXGAP (1 s) unless the line was marked scheme=True"""
        for name,tl,gp in s.timelines:
            for i,((a0,a1),(b0,b1)) in enumerate(zip(tl,tl[1:])):
                g,sch=gp[i]; assert a1<=b0, (name,'overlap',tl)
                assert b0-a1<=s.MAXGAP or sch, (name,f'pause {b0-a1} ms before line {i+2} > 1 s',tl)
        return [(n,[(round(a/1000,1),round(b/1000,1)) for a,b in tl]) for n,tl,_ in s.timelines]
    # helpers
    ALWAYS=staticmethod(lambda: Map.cond(22,flags=0))
    def ET(s,sec): return s.cond(12,qty=sec,flags=0)
    def SW(s,i,on=True): return s.cond(11,res=i,cmp=2 if on else 3,flags=0)
    def setsw(s,i,on=True): return s.act(13,num=i,mod=4 if on else 5,flags=0x04)
    def text(s,t): return s.act(9,s=s.S(check_colours(t,False)))
    def trans(s,t,unit,loc,snd,gap=None,scheme=False):
        """gap = pause BEFORE this line (default GAP; 0 = interrupts the previous speaker; >1000 only with scheme=True)"""
        sid,ms=snd; return s._setgap(s.act(7,loc=loc,s=s.S(check_colours(t,False)),wav=sid,time=ms,unit=unit,mod=7,num=ms),gap,scheme)
    def wav(s,snd): return s.act(8,wav=snd[0],time=snd[1],flags=0x04)
    AIR_FX={60,58,70,71,84,62,73}   # Protoss air (blue-white energy deaths); air units can be created anywhere
    def fx_burst(s,p,u,locs):
        """visual effect: ONE unit per location, created invincible and killed (Kill Unit) in the SAME trigger, so only the
        death animation is seen. Never ordered, never alive for a frame, never staggered into a wave (marker 0xF05F)."""
        assert p!=0, 'effect player must not be the human'
        assert len(set(locs))==len(locs), 'fx_burst: max one effect unit per location per trigger'
        assert u in s.AIR_FX or getattr(s,'fx_ground_verified',False), 'fx_burst: use an air unit (no placement errors) or verify every spot walkable'
        return [s.act(44,loc=l,player=p,unit=u,mod=1,time=0xF05F) for l in locs]+[s.act(43,loc=64,player=p,unit=u,mod=4,flags=0x04),   # invincible
                s.act(22,player=p,unit=u,mod=0,flags=0x04)]   # Kill Unit ignores invincibility and plays the death animation (Remove would not)
    def fx_cycle(s,owner,p,u,spots,schedule,conds=(),gap=4,seed=0,extra=None):
        """scattered effect over time. schedule = [(elapsed_s, n_spots), ...]; each step fires ONE unit at each of n spots,
        rotating through the shuffled spots so a spot is reused only after >= gap s (the previous unit is long gone).
        Paced by Elapsed Time (not trigger passes, so hyper triggers do not speed it up); a step whose second has passed
        is skipped instead of piling up. extra(t, spots) may add actions to a step (e.g. a Scanner Sweep shimmer)."""
        import random as _r
        sp=list(spots); _r.Random(seed).shuffle(sp); k=0; last={}
        for t,n in schedule:
            assert n<=len(sp), 'fx_cycle: more spots per step than spots'
            grp=[sp[(k+i)%len(sp)] for i in range(n)]; k=(k+n)%len(sp)
            for l in grp:
                assert t-last.get(l,-999)>=gap, f'fx_cycle: spot reused after {t-last[l]} s (< {gap} s): add spots or slow down'
                last[l]=t
            s.T([owner],list(conds)+[s.ET(t),s.cond(12,qty=t+1,cmp=1,flags=0)],s.fx_burst(p,u,grp)+(extra(t,grp) if extra else []))
    def wait(s,ms): return s.act(4,time=ms,flags=0x04)
    REVEAL_MS=3000   # how long an auto-removed revealer keeps its vision after the trigger's other actions
    def reveal(s,p,loc,hold_ms=None,permanent=False,why=''):
        """temporary vision: create a Map Revealer, ping, hold, remove it.
        permanent=True needs a reason and writes a Comment REVEAL_PERMANENT_OK: <why>."""
        a=[s.create(p,101,1,loc),s.ping(loc)]
        if permanent:
            assert why, 'permanent reveal needs a mission design reason'
            return a+[s.act(47,s=s.S('REVEAL_PERMANENT_OK: '+why),flags=0x04)]
        return a+[s.wait(s.REVEAL_MS if hold_ms is None else hold_ms),s.act(25,loc=loc,player=p,unit=101,mod=0,flags=0x04)]
    def scene_reveal(s,loc,p=0,remove_after=True,why=''):
        """vision for a dialogue scene at a location the human may not see (check scene_location_visible): put these
        actions BEFORE the scene's first line. Creates a Map Revealer for player p at loc and centres the camera there.
        T() moves the revealer ahead of the cinematic pause and removes it after the scene (REVEAL_MS later).
        remove_after=False keeps the vision and needs a reason (Comment REVEAL_PERMANENT_OK: <why>).
        Design note: 'SCENE_VIEW: <scene> :: <location name> :: revealer'."""
        a=[s.create(p,101,1,loc),s.act(10,loc=loc,flags=0x04)]
        if not remove_after:
            assert why, 'scene_reveal(remove_after=False) needs a mission design reason'
            a.append(s.act(47,s=s.S('REVEAL_PERMANENT_OK: '+why),flags=0x04))
        return a
    def create(s,p,u,n,loc,clash=False):
        # enemy wave scaling per mission (difficulty curve); P1 creates and visible-clash spawns are untouched
        k=getattr(s,'wavescale',1.0)
        if p!=0 and not clash and k!=1.0 and u not in HEROES: n=max(1,min(255,int(n*k+0.5)))
        # Rule: trigger spawns stay small (real bases produce the rest) and come from a visible source
        if p!=0 and u not in HEROES and u not in (101,33,202,194):
            n=max(1,min(4,n))   # meridian: sizes are written explicitly (2-4), cap 4
            if not clash: s.spawnsrc=getattr(s,'spawnsrc',set())|{(p,loc)}
        if (p in (0,7) or clash or u in HEROES) and u!=101 and loc!=64: s.storylocs=getattr(s,'storylocs',set())|{loc}
        return s.act(44,loc=loc,player=p,unit=u,mod=n,time=0xC1A5 if clash else 0)
    def order(s,p,u,src,dst,o=2): return s.act(46,loc=src,player=p,unit=u,mod=o,num=dst)
    def obj(s,t): return s.act(12,s=s.S(t),flags=0x04)
    def ping(s,loc): return s.act(28,loc=loc,flags=0x04)
    def ai(s,script,loc=None,keep=False):
        # enemy AI tier per mission: Custom -> Expansion Campaign Difficult (M1-M3) / Insane (M4+)
        tier=getattr(s,'aitier',None)
        if tier and not keep and script[1:]=='MCu': script=script[0]+tier
        n=struct.unpack('<I',script.encode())[0]
        return s.act(16,loc=loc,num=n,flags=0x04) if loc else s.act(15,num=n,flags=0x04)
    TOWN_HALLS=(106,130,131,132,133,154)
    def town_ai(s,p,script,hall,area=None,name=None,start_loc=True):
        """Start computer player p's town AI the way Blizzard's campaign maps do (a computer town without a running town AI leaves its SCVs idle).
        hall = top-left tile of the pre-placed town hall (as passed to unit()); script = 4-letter code (e.g. 'THIx').
        Main town (area=None): a location on exactly the hall's footprint (Blizzard: 4x3 'Main Town' locations), so the
        AI town is centred on the hall and takes its workers, minerals and buildings. Second base: area=(x0,y0,x1,y1)
        around it with an Area Town script ('TARx'/'ZARx'/'PARx'). Adds the start location on the hall (every official
        computer base has one) and a trigger owned by p with Always, so the workers mine from the first second.
        Returns the location index."""
        w,h=4,3   # every town hall (CC, Hatchery/Lair/Hive, Nexus, Infested CC) is 4x3 tiles
        x,y=hall
        if area is None: x0,y0,x1,y1=x,y,x+w,y+h
        else:
            x0,y0,x1,y1=area; assert x0<=x+w/2<=x1 and y0<=y+h/2<=y1, f'town_ai: area {area} does not contain the hall {hall}'
            assert script[1:3]=='AR', f'town_ai: a large area location needs an Area Town script, not {script}'
        if start_loc and not any(struct.unpack_from('<H',u,8)[0]==STARTLOC and u[16]==p for u in s.units):
            s.unit(STARTLOC,int(x*32+w*16),int(y*32+h*16),p,pixel=True)
        li=s.loc(name or f'AI Town P{p+1} {x},{y}',x0,y0,x1,y1)
        s.T([p],[s.ALWAYS()],[s.act(16,loc=li,num=struct.unpack('<I',script.encode())[0],flags=0x04)])
        return li
    def target_gone(s,p,uid,loc=None):
        """conditions (all must hold) that a destroy target of player p is really gone, robust against morphing:
        'p brings exactly 0' of EVERY type in its morph chain at loc (Command exactly 0 when loc is None).
        A Terran building that can lift off would 'leave' a location without dying: for those, loc must be None
        (Command counts the player's buildings anywhere) or use target_killed(). Check: destroy_target_morph_chain."""
        assert not (uid in LIFTABLE and loc is not None), f'unit {uid} can lift off and leave the location: use loc=None or target_killed()'
        return [s.cond(3,loc=loc,player=p,qty=0,unit=t,cmp=10) if loc is not None else s.cond(2,player=p,qty=0,unit=t,cmp=10) for t in MORPH_CHAIN.get(uid,(uid,))]
    def target_stands(s,p,uid,loc=None):
        """alternatives (one condition each) meaning 'the target or what it morphed into still stands'; a trigger
        needs one copy per alternative (BW conditions are AND only): use T_each()."""
        return [s.cond(3,loc=loc,player=p,qty=1,unit=t,cmp=0) if loc is not None else s.cond(2,player=p,qty=1,unit=t,cmp=0) for t in MORPH_CHAIN.get(uid,(uid,))]
    def target_killed(s,p,uid):
        """alternatives 'p has suffered at least 1 death of a type in the chain' (Deaths ignore lift-off; a morph is
        no death, so every chain type needs its own alternative). Use T_each(); assumes the target is p's only unit
        of these types (or reset the death counters first)."""
        return [s.cond(15,player=p,qty=1,unit=t,cmp=0) for t in MORPH_CHAIN.get(uid,(uid,))]
    def T_each(s,players,conds,alts,acts,switch=None):
        """one trigger per alternative condition (OR over alts). With switch=k each copy also requires switch k clear and
        sets it, so the actions run once even if two alternatives become true."""
        for c in alts:
            extra=[s.SW(switch,False)] if switch is not None else []
            s.T(players,list(conds)+[c]+extra,list(acts)+([s.setsw(switch)] if switch is not None else []))
    def ally(s,p,status): return s.act(57,player=p,unit=status,flags=0x04)  # 0 enemy 1 ally 2 allied victory; save() adds the shared-vision script (_ally_vision)
    # briefing actions
    def b_portrait(s,unit,slot): return s.act(5,unit=unit,player=slot,flags=0x14)
    def b_obj(s,t): return s.act(4,s=s.S(check_colours(t,True)),flags=0x04)
    def b_trans(s,t,slot,snd,gap=None,scheme=False):
        """one briefing line: portrait talks + wav + text, then a single Wait(ms+pause) is added by B().
        gap = pause BEFORE this line (0 = interruption; >1000 only with scheme=True). Returns a list: use acts+=..."""
        sid,ms=snd
        return [s.act(7,time=ms,player=slot,flags=0x04),                              # Display Speaking Portrait
                s._setgap(s.act(2,wav=sid,time=ms,flags=0x04),gap,scheme),            # Play WAV (timing anchor)
                s.act(3,s=s.S(check_colours(t,True)),time=ms,flags=0x04),             # Text Message (glue palette)
                s.act(0xFE)]                                                          # marker -> Wait
    def b_text(s,t,ms): return s.act(3,s=s.S(check_colours(t,True)),time=ms,flags=0x04)
    def b_wait(s,ms): return s.act(1,time=ms,flags=0x04)
    def b_hide(s,slot): return s.act(6,player=slot,flags=0x04)
    def b_end(s,slots=(0,1,2,3)): return [s.b_hide(k) for k in slots]+[s.b_text('\x13End of Briefing.',4000),s.b_wait(4000)]
    # ---------- save ----------
    def rename(s,uid,name,hp,armor,shields=0,build=1500,minc=0,gas=0): s.unitnames[uid]=(name,hp,armor,shields,build,minc,gas)
    # ---------- pre-save rules ----------
    startres=None      # {player:(minerals,gas)} -> injected Set Resources at mission start (mandatory for humans)
    hyper=True         # hyper triggers: trigger passes every 2 frames instead of every 31 (1.3 s at Fastest)
    hyperplayer=None
    @staticmethod
    def _trig_parts(t):
        conds=[t[i*20:i*20+20] for i in range(16) if t[i*20+15]]
        acts=[t[320+i*32:352+i*32] for i in range(64) if t[320+i*32+26]]
        return conds,acts,[p for p in range(28) if t[2372+p]]
    def _start_trigs(s,p):
        for t in s.trigs:
            c,a,pl=s._trig_parts(t)
            if p in pl and all(x[15]==22 or (x[15]==12 and struct.unpack_from('<I',x,8)[0]<=2 and x[14] in (0,1,10)) for x in c): yield a
    # Allies share vision both ways. Verified (staredit.net Scenario.chk wiki, eudplib trigger tables):
    # action 57 = Set Alliance Status(player, 0 enemy/1 ally/2 allied victory); action 15 = Run AI Script with the
    # 4-char script id in the number field; 'Turn ON/OFF Shared Vision for Player N' = '+Vi<N-1>' / '-Vi<N-1>'.
    # The TRIGGER OWNER receives the vision of player N (staredit.net FAQ). FORC force flag bit 3 = shared vision.
    ally_no_vision=()   # per map: players (0-based) exempt, matching 'ALLY_NO_VISION_OK: P<n> :: reason' in the design note
    # When the alliance with a player begins (design note 'ALLIANCE_STARTS: P<n> :: start' or ':: switch <k> :: <event>'):
    # {player: k} for alliances that begin at an event. Vision is then added ONLY next to an Ally/Allied-victory action in
    # a trigger conditioned on switch k being set; a truce 'Ally' set at mission start (or anywhere without switch k)
    # gets no vision. Players not listed: vision goes with every Ally action (alliance from the start).
    alliance_switch={}
    @staticmethod
    def vision_ai(target,on=True): return Map.act(15,num=struct.unpack('<I',(('+' if on else '-')+'Vi'+str(target)).encode())[0],flags=0x04)
    def _ally_targets(s,t):
        if 0<=t<8: return [t]
        if t==17: return list(range(8))                      # All Players (13 = Current Player -> itself)
        if 18<=t<=21: return [p for p in range(8) if s.forces[p]==t-18]
        return []
    def _ally_vision(s):
        """same trigger as the Set Alliance Status that starts the alliance: owner gets (ally) or loses (enemy) the
        target's vision. Exempt players (ally_no_vision) get no vision in EITHER direction. Event alliances
        (alliance_switch) get vision only in triggers that require their switch (never with a start-of-mission truce)."""
        ex=set(getattr(s,'ally_no_vision',()) or ()); asw=dict(getattr(s,'alliance_switch',{}) or {})
        for i,t in enumerate(s.trigs):
            c,a,pl=s._trig_parts(t)
            if not any(x[26]==57 for x in a): continue
            have={struct.unpack_from('<I',x,20)[0] for x in a if x[26] in (15,16)}
            own={o for q in pl for o in (s._ally_targets(q) if q>=8 else [q])}
            sws={x[16] for x in c if x[15]==11 and x[14]==2}     # switches this trigger requires to be set
            out=[]
            for x in a:
                out.append(x)
                if x[26]!=57: continue
                tgt=struct.unpack_from('<I',x,16)[0]; st=struct.unpack_from('<H',x,24)[0]
                for tp in s._ally_targets(tgt):
                    if tp in own: continue                      # never '-Vi' an owner's own vision
                    if tp in ex or own&ex: continue             # exemption covers both directions
                    if st>=1:
                        need={asw[q] for q in own|{tp} if q in asw}
                        if need and not need<=sws: continue     # ally before the event (truce): no vision
                    v=s.vision_ai(tp,st>=1); n=struct.unpack_from('<I',v,20)[0]
                    if n not in have: out.append(v); have.add(n)
            assert len(out)<=64, f'trig{i}: no room for the shared-vision actions next to Set Alliance Status'
            players=[q for q in pl]
            s.trigs[i]=s._pack(players,c,out)
        for f in range(4):
            mem=[p for p in range(8) if s.forces[p]==f and s.ownr[p] in (5,6)]
            if s.forceflags[f]&2 and len(mem)>1 and not (set(mem)&ex) and not (set(mem)&set(asw)): s.forceflags[f]|=8
    def _presave(s):
        s._ally_vision()
        for p,(mn,gs) in (s.startres or {}).items():
            s.trigs.insert(0,s._pack([p],[s.ALWAYS()],[s.act(26,player=p,num=mn,mod=7,unit=0,flags=0x04),s.act(26,player=p,num=gs,mod=7,unit=1,flags=0x04)]))
        for p in range(8):
            if s.ownr[p]!=6: continue
            got={struct.unpack_from('<H',a,24)[0] for acts in s._start_trigs(p) for a in acts if a[26]==26 and struct.unpack_from('<I',a,16)[0] in (p,13) and a[27]==7}
            assert (0 in got or 2 in got) and (1 in got or 2 in got), \
                f'P{p+1} (human) gets no deliberate starting minerals+gas: set m.startres={{{p}:(min,gas)}}'
        if s.hyper:
            # with hyper triggers a preserved trigger runs every 2 frames instead of every 1.3 s: per-pass counters must pace themselves
            for t in s.trigs:
                c,a,_=s._trig_parts(t)
                if any(x[26]==3 for x in a) and not any(x[26]==4 for x in a) and any(x[26] in (26,27,45) and x[27]==8 for x in a):
                    raise AssertionError('preserved trigger adds score/resources/deaths every pass without a Wait: with hyper triggers it runs 15x faster')
            hp=s.hyperplayer
            if hp is None:
                busy={p for t in s.trigs for p in s._trig_parts(t)[2] if any(a[26] in (4,7,10) for a in s._trig_parts(t)[1])}
                hp=next((p for p in range(8) if s.ownr[p]==5 and p not in busy),None)
            assert hp is not None, 'no computer player without Waits for hyper triggers: set m.hyperplayer'
            for _ in range(3): s.trigs.append(s._pack([hp],[s.ALWAYS()],[s.wait(0)]*63+[s.act(3,flags=0x04)]))
            s.hyperused=hp
    def hero_spot_near(s,g,player,cands=None,maxd=2):
        """free walkable tile within maxd tiles (Chebyshev) of a MOBILE unit of `player`. Use for every hero that is rescued/handed over at start."""
        mob=[(px//32,py//32) for px,py,uid,o in s._placed() if o==player and uid<106]
        for ux,uy in mob:
            for d in range(1,maxd+1):
                for dx in range(-d,d+1):
                    for dy in range(-d,d+1):
                        x,y=ux+dx,uy+dy
                        if max(abs(dx),abs(dy))==d and g.spot_unit(x,y) and (x,y) not in g.occ and (not cands or (x,y) in cands): return x,y
        raise AssertionError(f'no free tile within {maxd} of a mobile unit of P{player+1}')
    def _placed(s):
        return [(struct.unpack_from('<H',u,4)[0],struct.unpack_from('<H',u,6)[0],struct.unpack_from('<H',u,8)[0],u[16]) for u in s.units]
    def check_rescue_heroes(s,maxd=2):
        """a hero of a Rescuable player (OWNR 3) at start must have a mobile human-player unit within maxd tiles"""
        P=s._placed(); bad=[]
        for px,py,uid,o in P:
            if o<8 and s.ownr[o]==3 and (uid in s.unitnames or uid in HERO_IDS):
                if not any(s.ownr[o2]==6 and u2<106 and max(abs(px-x2),abs(py-y2))<=maxd*32+16 for x2,y2,u2,o2 in P): bad.append((uid,px//32,py//32))
        assert not bad, f'rescue hero without a player unit within {maxd} tiles: {bad}'
    def save(s,path,name,desc):
        s._presave(); s.check_rescue_heroes()
        W,H=s.W,s.H
        sn,sd=s.S(name),s.S(desc); fn=[s.S(x) for x in s.forcenames]
        # UNIx
        dflt=bytearray(b'\1'*228); hp=[0]*228; sh=[0]*228; ar=[0]*228; bt=[0]*228; mn=[0]*228; gs=[0]*228; st=[0]*228
        # weapon damage in UNIx is indexed by WEAPON id and is read for every unit whose use-default flag is 0.
        # Always fill the real weapons.dat default for each weapon of each customised unit (map may override via WDMG).
        wdb=json.load(open(_WEAPON_DB)); WU=wdb['units']; WW=wdb['weapons']; wd={}
        for u in s.unitnames:
            for slot in ('ground','air'):
                w=WU[str(u)][slot]
                if w is not None: wd[w]=WDMG.get(w,(WW[str(w)]['dmg'],WW[str(w)]['bonus']))
        for w,(d,b) in WDMG.items():
            if w not in wd and (d,b)!=(WW[str(w)]['dmg'],WW[str(w)]['bonus']):
                print(f'WARNING WDMG[{w}] {WW[str(w)]["name"]} is not a weapon of any customised unit (wrong weapon index?) - ignored')
        for w,(d,b) in wd.items(): assert d>0 or WW[str(w)]['dmg']==0, f'weapon {w} {WW[str(w)]["name"]} of a customised unit would deal 0 damage'
        for u,(nm,h,a,shd,b,m,g) in s.unitnames.items():
            dflt[u]=0; hp[u]=h*256; ar[u]=a; sh[u]=shd; bt[u]=b; mn[u]=m; gs[u]=g; st[u]=s.S(nm)
        unix=bytes(dflt)+struct.pack('<228I',*hp)+struct.pack('<228H',*sh)+bytes(ar)+struct.pack('<228H',*bt)+struct.pack('<228H',*mn)+struct.pack('<228H',*gs)+struct.pack('<228H',*st)+struct.pack('<130H',*[wd.get(i,(0,0))[0] for i in range(130)])+struct.pack('<130H',*[wd.get(i,(0,0))[1] for i in range(130)])
        assert len(unix)==4168
        unis=unix[:3648]+unix[3648:3648+200]+unix[3648+260:3648+260+200]; assert len(unis)==4048   # vanilla: 100 weapons
        enc=[x.encode('utf-8')+b'\0' for x in s.strings[1:]]
        n=len(enc); off=2+2*n; offs=[]; data=b''
        for e in enc: offs.append(off+len(data)); data+=e
        assert off+len(data)<65536, 'STR too big'
        STR=struct.pack('<H',n)+struct.pack(f'<{n}H',*offs)+data
        wav=struct.pack('<512I',*(s.wavs+[0]*(512-len(s.wavs))))
        _named=named_doodad_ids(s.ts); _bad=sorted({struct.unpack_from('<H',d)[0] for d in getattr(s,'dd2',[])}-_named)
        assert not _bad, f'DD2 holds unnamed tileset doodad ids {_bad[:10]}: ScmDraft 2 would refuse to open the map'
        ownr=bytes(s.ownr); side=bytes(s.side)
        pupx,ptex,puni,ptec=tech_sections(getattr(s,'tech',None))
        sec=[('VER ',struct.pack('<H',205)),('TYPE',b'RAWB'),('IVE2',struct.pack('<H',11)),('VCOD',_vcod()),('IOWN',ownr),('OWNR',ownr),
         ('ERA ',struct.pack('<H',s.ts)),('DIM ',struct.pack('<HH',W,H)),('SIDE',side),('MTXM',s.mtxm),('PUNI',puni),
         ('UPGR',_vanilla_pupg(pupx)),('PTEC',ptec),('UNIT',b''.join(s.units)),('ISOM',s.isom),('TILE',s.mtxm),('DD2 ',b''.join(getattr(s,'dd2',[]))),('THG2',b''),('MASK',b'\xff'*(W*H)),
         ('STR ',STR),('UPRP',b'\0'*(64*20)),('UPUS',b'\0'*64),('MRGN',b''.join(s.mrgn)),('TRIG',b''.join(s.trigs)),('MBRF',b''.join(s.brief)),
         ('SPRP',struct.pack('<HH',sn,sd)),('FORC',bytes(s.forces)+struct.pack('<4H',*fn)+bytes(s.forceflags)),
         ('WAV ',wav),('UNIS',unis),('UPGS',b'\1'*46+b'\0'*552),('TECS',b'\1'*24+b'\0'*192),('SWNM',b'\0'*1024),('COLR',bytes(getattr(s,'colr',[0,1,2,3,4,5,6,7]))),
         ('PUPx',pupx),('PTEx',ptex),('UNIx',unix),('UPGx',b'\1'*61+b'\0'*(794-61)),('TECx',b'\1'*44+b'\0'*(396-44))]
        assert len(pupx)==2318 and len(ptex)==1672
        chk=b''.join(k.encode()+struct.pack('<I',len(v))+v for k,v in sec)
        tmp=path+'.chk'; open(tmp,'wb').write(chk)
        try:   # computer_ai_started / ai_workers_mining: warn at build time, predelivery check 48 FAILs
            import sys as _sys; _here=os.path.dirname(os.path.abspath(__file__))
            for _p in (_here, os.path.join(_here,'..','..','bw')):
                if os.path.exists(os.path.join(_p,'check_computer_ai.py')) and _p not in _sys.path: _sys.path.insert(0,_p)
            import check_computer_ai as _cca
            for _l in _cca.run(tmp):
                if _l.startswith('FAIL'): print('WARNING (fix before delivery; use Map.town_ai) '+_l)
        except Exception as _e: print(f'WARNING computer_ai check skipped: {_e!r}')
        if os.path.exists(path): os.remove(path)
        m=mpqapi.MPQ.create(path,3,64+len(s.wavfiles)*2)
        m.add_file('staredit\\scenario.chk',tmp)
        for arch,f in s.wavfiles.items(): m.add_file(arch,f)
        m.compact(); del m; os.remove(tmp)
        return chk

def validate(path):
    """re-open MPQ, re-parse CHK, check sections/trigs/wavs; then eudplib LoadMap"""
    m=mpqapi.MPQ.open(path); d=bytes(m.extract_file('staredit\\scenario.chk'))
    s={}; i=0
    while i<len(d):
        k=d[i:i+4].decode(); n=struct.unpack_from('<I',d,i+4)[0]; s.setdefault(k,d[i+8:i+8+n]); i+=8+n
    assert i==len(d)
    req=['VER ','VCOD','OWNR','ERA ','DIM ','SIDE','MTXM','UNIT','STR ','MRGN','TRIG','MBRF','SPRP','FORC','UNIx','PUPx','PTEx','UPGx','TECx','ISOM']
    for r in req: assert r in s, r
    W,H=struct.unpack('<HH',s['DIM ']); assert len(s['MTXM'])==W*H*2 and len(s['ISOM'])==(W//2+1)*(H+1)*8
    assert len(s['TRIG'])%2400==0 and len(s['MBRF'])%2400==0 and len(s['UNIT'])%36==0
    # addon_attached: pre-placed add-ons must be linked to their parent, else they stand detached in the game
    import sys as _sys; _here=os.path.dirname(os.path.abspath(__file__))
    for _p in (_here, os.path.join(_here,'..','..','bw')):
        if os.path.exists(os.path.join(_p,'check_addon_attached.py')) and _p not in _sys.path: _sys.path.insert(0,_p)
    import check_addon_attached as _caa
    _af,_=_caa.check(s['UNIT']); assert not _af, 'addon_attached: '+'; '.join(_af[:4])
    st=s['STR ']; c=struct.unpack_from('<H',st)[0]; offs=struct.unpack_from(f'<{c}H',st,2)
    strs=[st[o:].split(b'\0')[0].decode('utf-8') for o in offs]
    wavs=[w for w in struct.unpack('<512I',s['WAV ']) if w]
    for w in wavs:
        data=bytes(m.extract_file(strs[w-1])); assert data[:4]==b'RIFF', strs[w-1]
    r=subprocess.run(['python3','-c',f"import eudplib as ep; ep.LoadMap({path!r}); print('LOADMAP_OK')"],capture_output=True,text=True,cwd='/tmp')
    assert 'LOADMAP_OK' in r.stdout, r.stdout+r.stderr
    return dict(trigs=len(s['TRIG'])//2400,brief=len(s['MBRF'])//2400,units=len(s['UNIT'])//36,strings=c,wavs=len(wavs),size=os.path.getsize(path))

PAL={0:(235,50,50),1:(60,110,255),2:(40,200,190),3:(170,80,240),4:(255,150,40),5:(150,95,50),6:(240,240,240),7:(250,220,40),8:(40,200,60),9:(150,190,255),10:(230,200,150),11:(120,230,255)}
RENDER_COLR=None
def render(path,png,labels,title):
    from PIL import Image, ImageDraw, ImageFont
    m=mpqapi.MPQ.open(path); d=bytes(m.extract_file('staredit\\scenario.chk')); s={}; i=0
    while i<len(d):
        k=d[i:i+4].decode(); n=struct.unpack_from('<I',d,i+4)[0]; s.setdefault(k,d[i+8:i+8+n]); i+=8+n
    W,H=struct.unpack('<HH',s['DIM ']); ts=struct.unpack('<H',s['ERA '])[0]%8; T=f'{TOOLS}/tileset/{TSNAMES[ts]}'
    cv5=open(T+'.cv5','rb').read(); vx4=open(T+'.vx4ex','rb').read(); vr4=open(T+'.vr4','rb').read(); wpe=open(T+'.wpe','rb').read()
    pal=bytes(b for i in range(256) for b in wpe[i*4:i*4+3])
    mt=struct.unpack(f'<{W*H}H',s['MTXM']); cache={}
    def mega(tid):
        if tid in cache: return cache[tid]
        g,v=(tid>>4)&0x7FF,tid&15
        if g*52+52>len(cv5): g,v=0,0
        mi=struct.unpack_from('<H',cv5,g*52+20+v*2)[0]
        buf=bytearray(32*32)
        for j in range(16):
            r=struct.unpack_from('<I',vx4,mi*64+j*4)[0]; fl=r&1; mn=r>>1
            blk=vr4[mn*64:mn*64+64]
            for yy in range(8):
                row=blk[yy*8:yy*8+8]
                if fl: row=row[::-1]
                o=((j//4)*8+yy)*32+(j%4)*8; buf[o:o+8]=row
        im=Image.frombytes('P',(32,32),bytes(buf)); im.putpalette(pal); im=im.convert('RGB'); cache[tid]=im; return im
    big=Image.new('RGB',(W*32,H*32))
    for y in range(H):
        for x in range(W): big.paste(mega(mt[y*W+x]),(x*32,y*32))
    S=1024/(W*32) if W>=H else 1024/(H*32)
    img=big.resize((int(W*32*S),int(H*32*S)),Image.LANCZOS).convert('RGBA')
    ov=Image.new('RGBA',img.size,(0,0,0,0)); dr=ImageDraw.Draw(ov)
    font=lambda n:ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf',n)
    st=s['STR ']; c=struct.unpack_from('<H',st)[0]; offs=struct.unpack_from(f'<{c}H',st,2)
    gs=lambda k: st[offs[k-1]:].split(b'\0')[0].decode() if k else ''
    UC={0:(190,80,255),1:(235,50,50),2:(60,130,255),3:(250,200,40),4:(60,220,120),5:(240,240,240),6:(255,120,200),7:(140,90,40),11:(120,230,255)}
    if RENDER_COLR: UC={**{p:PAL[c] for p,c in enumerate(RENDER_COLR)},11:(120,230,255)}
    import collections as _co
    UL=[struct.unpack_from('<IHHHHHHB',s['UNIT'],k*36) for k in range(len(s['UNIT'])//36)]
    zrects=[]
    for idx in range(255):
        x0,y0,x1,y1,sn,_=struct.unpack_from('<IIIIHH',s['MRGN'],idx*20); n=gs(sn)
        if n in labels.get('zones',{}):
            cc=tuple(labels['zones'][n])
            # faction zones take the colour of the player owning most buildings inside (keeps box/legend/units consistent)
            own=_co.Counter(o for _,x,y,u,_,_,_,o in UL if u in (HATCH,LAIR,HIVE,CC,NEXUS,STARTLOC) and o<8 and x0<=x<x1 and y0<=y<y1)
            if own: cc=UC[own.most_common(1)[0][0]]
            zrects.append((x0/32,y0/32,x1/32,y1/32,cc,bool(own)))
            dr.ellipse([x0*S,y0*S,x1*S,y1*S],fill=cc+(30,),outline=cc+(200,),width=2)   # soft marker, not a terrain box
    for k in range(len(s['UNIT'])//36):
        _,x,y,u,_,_,_,o=struct.unpack_from('<IHHHHHHB',s['UNIT'],k*36); x*=S; y*=S
        if u==STARTLOC: dr.ellipse([x-9,y-9,x+9,y+9],outline=(255,255,255,255),width=3); continue
        if u in BUILDSIZE:
            w,h=BUILDSIZE[u]; w*=16*S; h*=16*S
            col=UC.get(o,(200,200,200)) if u not in (MINERAL,GEYSER) else ((110,200,255) if u==MINERAL else (90,230,120))
            if u in (CRYSTAL,TEMPLE,XEL_TEMPLE,STASIS): col=(255,230,80)
            dr.rectangle([x-w,y-h,x+w,y+h],fill=col+(235,),outline=(0,0,0,255))
        else: dr.ellipse([x-3,y-3,x+3,y+3],fill=UC.get(o,(200,200,200))+(255,),outline=(0,0,0,255))
    img=Image.alpha_composite(img,ov); dr=ImageDraw.Draw(img)
    for (x,y,t,cc,sz) in labels.get('text',[]):
        _d=lambda r: max(r[0]-x,0,x-r[2])+max(r[1]-y,0,y-r[3])
        if zrects:
            _z=min(zrects,key=_d)
            if _z[5] and _d(_z)<=3: cc=tuple(min(255,int(c*0.6+255*0.4)) for c in _z[4])
        dr.text((x*32*S,y*32*S),t,font=font(sz),fill=tuple(cc),stroke_width=3,stroke_fill=(0,0,0))
    leg=Image.new('RGB',(img.size[0],110),(18,14,12)); ld=ImageDraw.Draw(leg)
    ld.text((14,8),title,font=font(22),fill=(240,220,200))
    items=labels.get('legend',[])
    for i,(cc,t) in enumerate(items):
        x=14+(i%3)*340; y=44+(i//3)*30; ld.rectangle([x,y+4,x+18,y+22],fill=tuple(cc)); ld.text((x+26,y+2),t,font=font(16),fill=(230,230,230))
    out=Image.new('RGB',(img.size[0],img.size[1]+110)); out.paste(img.convert('RGB'),(0,0)); out.paste(leg,(0,img.size[1])); out.save(png)

# ---------- doodads ----------
def _pure_groups(ts,terrain):
    tmp=f'/tmp/pure_{ts}_{terrain}'
    if not os.path.exists(tmp+'.bin'):
        open(tmp+'.txt','w').write(f'16 16 {terrain}\n')
        subprocess.run([f'{TOOLS}/isomtool',f'{TOOLS}/tileset/{TSNAMES[ts]}.cv5',str(ts),tmp+'.txt',tmp+'.bin'],capture_output=True)
    d=open(tmp+'.bin','rb').read()[:16*16*2]
    return {v>>4 for v in struct.unpack('<256H',d)}

def doodad_is_real(cv5,g,did,w,h):
    """True if cv5 doodad group g (id did) is a real, editor-listed doodad.
    cv5 also holds empty doodad slots: group-name string 0 and only blank megatiles. ScmDraft builds its doodad
    table only from named groups, so a DD2 entry pointing at an empty slot makes the whole map fail to open
    ("Could not locate information in the tileset for a particular (Type N)"). Such slots also draw nothing."""
    n=len(cv5)//52
    if struct.unpack_from('<H',cv5,g*52+8)[0]==0: return False          # no doodad group name -> not in ScmDraft/StarEdit palette
    rows=[r for r in range(g,min(n,g+h)) if struct.unpack_from('<H',cv5,r*52)[0]==1 and struct.unpack_from('<H',cv5,r*52+12)[0]==did]
    return any(struct.unpack_from('<H',cv5,r*52+20+2*c)[0] for r in rows for c in range(min(w,16)))

def named_doodad_ids(ts):
    """doodad ids ScmDraft can load for tileset ts (see doodad_is_real)."""
    d=open(f'{TOOLS}/tileset/{TSNAMES[ts]}.cv5','rb').read(); ids=set()
    for g in range(len(d)//52):
        t,f,ov,scr,sname,u,did,w,h=struct.unpack_from('<9H',d,g*52)
        if t==1 and sname!=0: ids.add(did)
    return ids

def doodad_catalog(ts):
    d=open(f'{TOOLS}/tileset/{TSNAMES[ts]}.cv5','rb').read(); n=len(d)//52; cat={}
    for g in range(n):
        t,f,ov,scr,sname,u,did,w,h=struct.unpack_from('<9H',d,g*52)
        if t==1 and did not in cat and 0<w<=8 and 0<h<=8 and g+h<=n:
            if f & 0x3000: continue  # skip doodads that need sprite/unit overlays
            if not doodad_is_real(d,g,did,w,h): continue
            cat[did]=dict(g=g,w=w,h=h,high=bool(f&0x400),mid=bool(f&0x200),flags=f)
    return cat,d

def place_doodads(m,count,terrains,forbid=(),high=False,seed=5,maxw=8):
    """scatter tile-only doodads onto areas whose tiles are pure `terrains` (brush indices)."""
    rnd=random.Random(seed); cat,cv5=doodad_catalog(m.ts)
    pure=set()
    for t in terrains: pure|=_pure_groups(m.ts,t)
    cands=[c for c in cat.items() if c[1]['high']==high and not c[1]['mid'] and c[1]['w']<=maxw]
    if not cands: return 0
    mt=list(struct.unpack(f'<{m.W*m.H}H',m.mtxm)); used=set(); placed=0
    if not hasattr(m,'dd2'): m.dd2=[]
    def free(x,y,w,h):
        if x<1 or y<1 or x+w>=m.W-1 or y+h>=m.H-3: return False
        for (a,b,c,d_) in list(forbid)+list(getattr(m,'noddrects',[])):
            if x<c and x+w>a and y<d_ and y+h>b: return False
        for yy in range(y-1,y+h+1):
            for xx in range(x-1,x+w+1):
                if (xx,yy) in used or (mt[yy*m.W+xx]>>4) not in pure: return False
        return True
    tries=0
    while placed<count and tries<count*400:
        tries+=1; did,c=rnd.choice(cands); w,h=c['w'],c['h']
        x=rnd.randrange(1,m.W-w-1); y=rnd.randrange(1,m.H-h-3)
        if not free(x,y,w,h): continue
        # blend check: a tile doodad is a hard rectangle; only keep it if its outer ring matches the ground around it
        # (LY3: rock patches / dark plating pasted onto Twilight dirt showed straight unblended edges)
        new={}
        for r in range(h):
            for col in range(w):
                mega=struct.unpack_from('<H',cv5,(c['g']+r)*52+20+col*2)[0]
                if mega: new[(y+r)*m.W+x+col]=(c['g']+r)*16+col
        if not new: continue   # nothing visible to place
        if _doodad_edge(m.ts,cv5,mt,m.W,m.H,new,x,y,w,h)>DOODAD_EDGE_MAX or _doodad_edge.peak>DOODAD_EDGE_PEAK: continue
        for k,v in new.items(): mt[k]=v
        for r in range(h):
            for col in range(w): used.add((x+col,y+r))
        m.dd2.append(struct.pack('<HHHBB',did,x*32+w*16,y*32+h*16,12,0)); placed+=1
    m.mtxm=struct.pack(f'<{m.W*m.H}H',*mt)
    return placed

DOODAD_EDGE_MAX=5.0
DOODAD_EDGE_PEAK=15.0  # max single border-edge step   # mean minitile colour step at a doodad border; blended ground ~1.5-4.5, visible rectangles >6
_MF={}
def _doodad_edge(ts,cv5,mt,W,H,new,x0,y0,w,h):
    import numpy as np
    if ts not in _MF: _MF[ts]=_megafeat(ts)
    F=_MF[ts]
    def tf(xx,yy):
        v=new.get(yy*W+xx,mt[yy*W+xx]); mg=struct.unpack_from('<H',cv5,(v>>4)*52+20+(v&15)*2)[0]
        return F[min(mg,len(F)-1)].reshape(4,4,3)
    e=[]
    for yy in range(y0,y0+h):
        if x0>0: e.append(np.abs(tf(x0-1,yy)[:,3]-tf(x0,yy)[:,0]).mean())
        if x0+w<W: e.append(np.abs(tf(x0+w-1,yy)[:,3]-tf(x0+w,yy)[:,0]).mean())
    for xx in range(x0,x0+w):
        if y0>0: e.append(np.abs(tf(xx,y0-1)[3]-tf(xx,y0)[0]).mean())
        if y0+h<H: e.append(np.abs(tf(xx,y0+h-1)[3]-tf(xx,y0+h)[0]).mean())
    _doodad_edge.peak=float(np.max(e)) if e else 0.0
    return float(np.mean(e))
def _megafeat(ts):
    import numpy as np
    T=f'{TOOLS}/tileset/{TSNAMES[ts]}'
    vx4=open(T+'.vx4ex','rb').read();vr4=np.frombuffer(open(T+'.vr4','rb').read(),np.uint8).reshape(-1,64)
    pal=np.frombuffer(open(T+'.wpe','rb').read(),np.uint8).reshape(256,4)[:,:3].astype(np.float32)
    n=len(vx4)//64; refs=np.frombuffer(vx4,np.uint32).reshape(n,16)>>1
    refs=np.minimum(refs,len(vr4)-1)
    mini=pal[vr4].mean(1)            # (nmini,3)
    return mini[refs]                # (nmega,16,3)

def place_ramps(m,dids,spots,radius=10,maxscore=6.0):
    """Ramp doodads placed where their border cells best match the existing cliff (pixel matching). spots: approx (x,y)."""
    import numpy as np
    cat,cv5=doodad_catalog_all(m.ts); F=_megafeat(m.ts)
    mt=list(struct.unpack(f'<{m.W*m.H}H',m.mtxm))
    M=lambda tid: struct.unpack_from('<H',cv5,(tid>>4)*52+20+(tid&15)*2)[0] if (tid>>4)*52+52<=len(cv5) else 0
    MF=F[np.array([M(v) for v in mt])].reshape(m.H,m.W,16,3)
    if not hasattr(m,'dd2'): m.dd2=[]
    done=[]; used=set()
    for (sx,sy) in spots:
        best=None; lock=any((sx-a)**2+(sy-b)**2<r*r for a,b,r in getattr(m,'ramplock',()))   # locked ramps ignore fix-up exclusion zones
        for did in dids:
            c=cat[did]; w,h=c['w'],c['h']
            cells=[(r,col,struct.unpack_from('<H',cv5,(c['g']+r)*52+20+col*2)[0]) for r in range(h) for col in range(w)]
            ring=[(r,col,F[mg]) for r,col,mg in cells if mg and (r in(0,h-1) or col in(0,w-1))]
            rr=np.array([r for r,_,_ in ring]); cc=np.array([c_ for _,c_,_ in ring]); fe=np.stack([f for _,_,f in ring])
            for y in range(max(1,sy-radius),min(m.H-h-1,sy+radius)):
                for x in range(max(1,sx-radius),min(m.W-w-1,sx+radius)):
                    if any((x+a,y+b) in used for a in range(w) for b in range(h)): continue
                    if not lock and any(x<c2 and x+w>a2 and y<d2 and y+h>b2 for (a2,b2,c2,d2) in getattr(m,'noddrects',[])): continue
                    sc=float(np.abs(MF[y+rr,x+cc]-fe).mean())
                    if best is None or sc<best[0]: best=(sc,did,x,y)
        if not best or best[0]>(maxscore+1.5 if lock else maxscore): continue
        sc,did,x,y=best; c=cat[did]; w,h=c['w'],c['h']
        _nw={(y+r)*m.W+x+col:(c['g']+r)*16+col for r in range(h) for col in range(w) if struct.unpack_from('<H',cv5,(c['g']+r)*52+20+col*2)[0]}
        _doodad_edge(m.ts,cv5,mt,m.W,m.H,_nw,x,y,w,h)
        if _doodad_edge.peak>DOODAD_EDGE_PEAK and not lock:
            print('  ramp rejected (hard seam %.1f)'%_doodad_edge.peak,did,x,y); continue
        for r in range(h):
            for col in range(w):
                mega=struct.unpack_from('<H',cv5,(c['g']+r)*52+20+col*2)[0]
                if mega: mt[(y+r)*m.W+x+col]=(c['g']+r)*16+col
                used.add((x+col,y+r))
        for a in range(-2,w+2):
            for b in range(-2,h+2): used.add((x+a,y+b))
        m.dd2.append(struct.pack('<HHHBB',did,x*32+w*16,y*32+h*16,12,0)); done.append((did,x,y,round(sc,2)))
    m.mtxm=struct.pack(f'<{m.W*m.H}H',*mt)
    m.ramp_cells=getattr(m,'ramp_cells',set())|used
    return done

def doodad_catalog_all(ts):
    d=open(f'{TOOLS}/tileset/{TSNAMES[ts]}.cv5','rb').read(); n=len(d)//52; cat={}
    for g in range(n):
        t,f,ov,scr,sname,u,did,w,h=struct.unpack_from('<9H',d,g*52)
        if t==1 and did not in cat and w>0 and h>0 and doodad_is_real(d,g,did,w,h): cat[did]=dict(g=g,w=w,h=h,flags=f,s=sname)
    return cat,d

# ---------- tech tree (Blizzard-campaign style restrictions) ----------
UPG_MAX={**{i:3 for i in (0,1,2,3,4,5,6,7,8,9,10,11,12,13,14,15)},**{i:1 for i in range(16,61)}}
for i in (18,45,46,48,50,55,56,57,58,59,60): UPG_MAX[i]=0
DEFAULT_RESEARCHED={4,6,12,14,18,23,28,29,34}   # real BW: scanner, def.matrix, infestation, dark swarm, parasite, archon warp, DA meld, feedback, healing

# core abilities: an available unit always gets its defining abilities (rule: e.g. never a Comsat without Scanner Sweep)
import json as _json
CORE_TECH={int(k):v for k,v in _json.load(open('data/bw/tech/bw_techtree.json'))['core_abilities'].items() if not k.startswith('_')}
def _with_core(tech):
    if not tech: return tech
    t=dict(tech); t['techs']=set(t['techs'])
    for u in t['units']:
        t['techs']|=set(CORE_TECH.get(u,()))
    return t
def tech_sections(tech):
    """tech=None -> everything standard for all players. Else dict(player=0, units=set, upgrades={id:max}, techs=set):
    that player gets only the listed units/upgrade levels/abilities; computers keep the full standard tree."""
    tech=_with_core(tech)
    umax=[UPG_MAX.get(i,1) for i in range(61)]
    pmax=[[0]*61 for _ in range(12)]; pstart=[[0]*61 for _ in range(12)]; pdef=[[1]*61 for _ in range(12)]
    tav=[[0]*44 for _ in range(12)]; tres=[[0]*44 for _ in range(12)]; tdef=[[1]*44 for _ in range(12)]
    uav=[[1]*228 for _ in range(12)]; udef=[[1]*228 for _ in range(12)]
    if tech:
        for p in tech.get('players',[tech.get('player',0)]):
            pdef[p]=[0]*61; tdef[p]=[0]*44; udef[p]=[0]*228
            for i in range(61): pmax[p][i]=min(tech['upgrades'].get(i,0),umax[i])
            for i in range(44):
                tav[p][i]=1 if i in tech['techs'] else 0
                tres[p][i]=1 if (i in tech['techs'] and (i in DEFAULT_RESEARCHED or i in tech.get('pre',()))) else 0
            for u in range(228): uav[p][u]=1 if u in tech['units'] else 0
    f=lambda rows: b''.join(bytes(r) for r in rows)
    pupx=f(pmax)+f(pstart)+bytes(umax)+bytes(61)+f(pdef)
    tdefav=[1]*44; tdefres=[1 if i in DEFAULT_RESEARCHED else 0 for i in range(44)]
    ptex=f(tav)+f(tres)+bytes(tdefav)+bytes(tdefres)+f(tdef)
    puni=f(uav)+b'\1'*228+f(udef)
    T=lambda rows: b''.join(bytes(r[:24]) for r in rows)
    ptec=T(tav)+T(tres)+bytes(tdefav[:24])+bytes(tdefres[:24])+T(tdef)
    assert len(pupx)==2318 and len(ptex)==1672 and len(puni)==5700 and len(ptec)==912
    return pupx,ptex,puni,ptec
BUILDSIZE[134]=(2,2)   # Nydus Canal (spawn source)

# default damage/bonus of weapons fired by units we customise (UNIx overrides weapon damage for customised units)
WDMG={}   # optional per-map OVERRIDES by weapon id; defaults come from tech/bw_weapons.json automatically
_WEAPON_DB=next((p for p in [os.environ.get('BW_WEAPON_DB',''),os.path.join(os.path.dirname(os.path.abspath(__file__)),'..','..','..','tech','bw_weapons.json'),os.path.join(os.path.dirname(os.path.abspath(__file__)),'..','tech','bw_weapons.json'),'data/bw/tech/bw_weapons.json'] if p and os.path.exists(p)),'data/bw/tech/bw_weapons.json')

def _vanilla_pupg(pupx):
    """vanilla UPGR (46 upgrades) derived from the expansion PUPx (61 upgrades): same per-player max/start/defaults."""
    o=0; mx=[pupx[o+p*61:o+p*61+46] for p in range(12)]; o=12*61
    st=[pupx[o+p*61:o+p*61+46] for p in range(12)]; o+=12*61
    gmx=pupx[o:o+46]; o+=61; gst=pupx[o:o+46]; o+=61
    df=[pupx[o+p*61:o+p*61+46] for p in range(12)]
    r=b''.join(mx)+b''.join(st)+gmx+gst+b''.join(df); assert len(r)==1748; return r
