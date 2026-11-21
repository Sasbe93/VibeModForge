# builds bw_weapons.json from BWAPI sources (= weapons.dat / units.dat defaults). Weapon ids = weapons.dat ids.
import re,json
W=open('sources/bwapi_WeaponType.cpp').read(); U=open('sources/bwapi_UnitType.cpp').read()
def block(src,key):
    i=src.index(key); i=src.index('{',i); j=src.index('};',i)
    body=re.sub(r'//[^\n]*','',src[i+1:j]); return [t.strip() for t in body.split(',') if t.strip()]
wn=[x.strip('"') for x in block(W,'typeNames[WeaponTypes')]
un=[x.strip('"') for x in block(U,'typeNames[UnitTypes')]
amt=list(map(int,block(W,'defaultWpnDamageAmt[')));bon=list(map(int,block(W,'defaultWpnDamageBonus[')))
gw=block(U,'groundWeapon[UnitTypes');aw=block(U,'airWeapon[UnitTypes')
wid={n:i for i,n in enumerate(wn)}
def w(n): return None if n=='None' or wid.get(n,200)>=130 else wid[n]
out=dict(weapons={i:dict(name=wn[i],dmg=amt[i],bonus=bon[i]) for i in range(130)},
         units={i:dict(name=un[i],ground=w(gw[i]),air=w(aw[i])) for i in range(228)})
json.dump(out,open('bw_weapons.json','w'),indent=0)
print(len(wn),len(un),len(amt),len(gw),out['units'][16],out['units'][20],out['weapons'][1],out['weapons'][3])
