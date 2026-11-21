"""Extract the StarEdit VCOD seed table from any StarCraft map you own into external/bw/vcod_seeds.txt.
Usage: python3 tools/bw/extract_vcod.py <map.scx|map.scm|scenario.chk> [out]"""
import sys,os,struct
src=sys.argv[1]; out=sys.argv[2] if len(sys.argv)>2 else os.environ.get('BW_VCOD_SEEDS','external/bw/vcod_seeds.txt')
if src.lower().endswith('.chk'): d=open(src,'rb').read()
else:
    from eudplib.bindings._rust import mpqapi
    d=bytes(mpqapi.MPQ.open(src).extract_file('staredit\\scenario.chk'))
i=0;v=None
while i+8<=len(d):
    n=d[i:i+4]; l=struct.unpack('<i',d[i+4:i+8])[0]
    if n==b'VCOD': v=d[i+8:i+8+l]; break
    i+=8+l
if not v or len(v)<1024: sys.exit('no VCOD section found')
seeds=struct.unpack('<256I',v[:1024])
os.makedirs(os.path.dirname(out) or '.',exist_ok=True)
open(out,'w').write(','.join('0x%08X'%x for x in seeds)+'\n')
print('wrote',out)
