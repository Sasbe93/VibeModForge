import json, textwrap
from PIL import Image, ImageDraw, ImageFont
J=json.load(open('bw_techtree.json')); N={int(k):v for k,v in J['unit_names'].items()}
F=ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf',14); FB=ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf',16)
short=lambda s:s.replace('Terran ','').replace('Zerg ','').replace('Protoss ','')
COL={'Terran':(60,110,200),'Zerg':(150,60,150),'Protoss':(200,160,40)}
for race in ('Terran','Zerg','Protoss'):
    B=[u for u in J['units'] if u['race']==race and u['kind'] in('building','addon')]
    ids={b['id'] for b in B}; par={b['id']:[p for p in b['requires']+[x for x in b['produced_by'] if x in ids]] for b in B}
    depth={}
    def d(i): 
        if i not in depth: depth[i]=0 if not par[i] else 1+max(d(p) for p in par[i])
        return depth[i]
    for i in ids: d(i)
    enab={i:[] for i in ids}
    for u in J['units']:
        if u['race']==race and u['kind']=='unit':
            key=max(u['requires']+[131 if p==35 else p for p in u['produced_by'] if p in ids or p==35] or [None],key=lambda x:depth.get(x,-1))
            if key in enab: enab[key].append('U: '+short(N[u['id']])+(' (+'+', '.join(short(N[r]) for r in u['requires'] if r!=key)+')' if len(u['requires'])>1 or (u['requires'] and u['requires'][0]!=key) else ''))
    for g in J['upgrades']:
        if g['race']==race: enab[g['researched_at']].append(f"Up: {g['name']} (max {g['max_level']})"+(f" L2/3: {short(N[g['level_requires']['2'][0]])}" if g['level_requires'] else '')+(' +'+short(N[g['requires'][0]]) if g['requires'] else ''))
    for t in J['techs']:
        if t['race']==race and t['researched_at']: enab[t['researched_at']].append('T: '+t['name']+(' +'+short(N[t['requires'][0]]) if t['requires'] else ''))
    cols={}
    for i in sorted(ids,key=lambda i:(depth[i],i)): cols.setdefault(depth[i],[]).append(i)
    W=360; pos={}; boxes={}
    H=0
    for c,lst in cols.items():
        y=70
        for i in lst:
            lines=[]; [lines.extend(textwrap.wrap(l,44,subsequent_indent='   ')) for l in enab[i]]
            h=30+17*len(lines)+8; boxes[i]=(c*(W+70)+20,y,W,h,lines); y+=h+25
        H=max(H,y)
    img=Image.new('RGB',(len(cols)*(W+70)+20,H+60),'white'); dr=ImageDraw.Draw(img)
    dr.text((20,15),f'StarCraft: Brood War – {race} tech tree (arrows = prerequisite / producer; U=unit, Up=upgrade, T=tech)',font=FB,fill='black')
    for i,(x,y,w,h,_) in boxes.items():
        for p in par[i]:
            px,py,pw,ph,_=boxes[p]; dr.line([(px+pw,py+15),(x,y+15)],fill=(150,150,150),width=2); dr.ellipse([x-5,y+10,x+5,y+20],fill=(150,150,150))
    for i,(x,y,w,h,lines) in boxes.items():
        b=[u for u in B if u['id']==i][0]
        dr.rectangle([x,y,x+w,y+h],outline=COL[race],width=3,fill=(245,245,250) if b['kind']=='building' else (235,250,235))
        dr.text((x+6,y+5),f"{short(N[i])} [{i}]"+(' (addon)' if b['kind']=='addon' else ' (morph)' if b['how']=='morph' else ''),font=FB,fill=COL[race])
        for k,l in enumerate(lines): dr.text((x+8,y+28+17*k),l,font=F,fill='black')
    img.save(f'bw_techtree_{race.lower()}.png'); print(race,img.size)
