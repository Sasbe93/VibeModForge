#!/usr/bin/env python3
"""Patch a COPY of ScmDraft 2 0.9.10 so its 1.16 font loader reads the harness' synthetic unencrypted fonts.
Keeps the original as '<exe>.orig'. Only the font path is changed; map parsing code is untouched."""
import sys,shutil,os
exe=sys.argv[1]; orig=exe.replace('.exe','.orig.exe')
if not os.path.exists(orig): shutil.copy(exe,orig)
b=bytearray(open(orig,'rb').read())
P=[(0x441db,b'\x74\x1f',b'\x90\x90'),            # skip the 'font is encrypted' branch
   (0x449d1,b'\x68\x00\x00\x00\x08',b'\x68\x00\x00\x00\x04')]   # push 0x8000000 -> 0x4000000
for off,old,new in P:
    assert b[off:off+len(old)]==old, f'unexpected bytes at {off:#x}: not ScmDraft 2 0.9.10?'
    b[off:off+len(new)]=new
open(exe,'wb').write(b); print('patched',exe)
