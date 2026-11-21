"""Generates bw_techtree.json. IDs = StarEdit/BWAPI indices (cross-checked with eudplib DefUnitDict/DefUpgradeDict/DefTechDict)."""
import json
from eudplib.core.rawtrigger.strdict.trg import DefUnitDict
from eudplib.core.rawtrigger.strdict.upgrade import DefUpgradeDict
from eudplib.core.rawtrigger.strdict.tech import DefTechDict
UN={v:k for k,v in DefUnitDict.items() if v<229}; UP={v:k for k,v in DefUpgradeDict.items()}; TN={v:k for k,v in DefTechDict.items()}
# name, id, kind, produced_by, prereq buildings (besides producer), extra
U=[]
def u(race,id,kind,by,req=(),how='train',note=''):
    U.append(dict(id=id,name=UN[id],race=race,kind=kind,produced_by=by,how=how,requires=list(req),note=note))
T='Terran';Z='Zerg';P='Protoss'
# Terran
u(T,106,'building',[7],[],'build'); u(T,109,'building',[7],[],'build'); u(T,110,'building',[7],[],'build')
u(T,111,'building',[7],[106],'build'); u(T,122,'building',[7],[106],'build'); u(T,112,'building',[7],[111],'build')
u(T,125,'building',[7],[111],'build'); u(T,124,'building',[7],[122],'build'); u(T,113,'building',[7],[111],'build')
u(T,114,'building',[7],[113],'build'); u(T,123,'building',[7],[113],'build'); u(T,116,'building',[7],[114],'build')
u(T,107,'addon',[106],[112],'addon'); u(T,108,'addon',[106],[117],'addon'); u(T,120,'addon',[113],[],'addon')
u(T,115,'addon',[114],[],'addon'); u(T,117,'addon',[116],[],'addon'); u(T,118,'addon',[116],[],'addon')
u(T,7,'unit',[106]); u(T,0,'unit',[111]); u(T,32,'unit',[111],[112]); u(T,34,'unit',[111],[112]); u(T,1,'unit',[111],[112,117])
u(T,2,'unit',[113]); u(T,5,'unit',[113],[120],note='needs Machine Shop attached to the producing Factory'); u(T,3,'unit',[113],[123])
u(T,8,'unit',[114]); u(T,11,'unit',[114],[115],note='Control Tower attached'); u(T,9,'unit',[114],[115,116]); u(T,58,'unit',[114],[115,123]); u(T,12,'unit',[114],[115,118])
u(T,14,'unit',[108],[117],note='nuke armed in attached silo'); u(T,13,'unit',[2],[],'tech:3',note='laid by Vulture')
# Zerg
u(Z,131,'building',[41],[],'build'); u(Z,149,'building',[41],[],'build'); u(Z,142,'building',[41],[131],'build'); u(Z,139,'building',[41],[131],'build')
u(Z,143,'building',[41],[131],'build'); u(Z,146,'building',[143],[142],'morph'); u(Z,144,'building',[143],[139],'morph')
u(Z,132,'building',[131],[142],'morph'); u(Z,133,'building',[132],[138],'morph'); u(Z,135,'building',[41],[142],'build')
u(Z,141,'building',[41],[132],'build',note='Lair or Hive'); u(Z,138,'building',[41],[132],'build',note='Lair or Hive')
u(Z,140,'building',[41],[133],'build'); u(Z,136,'building',[41],[133],'build'); u(Z,137,'building',[141],[133],'morph'); u(Z,134,'building',[41],[133],'build')
u(Z,41,'unit',[35]); u(Z,42,'unit',[35]); u(Z,37,'unit',[35],[142]); u(Z,38,'unit',[35],[135]); u(Z,43,'unit',[35],[141],note='Spire or Greater Spire')
u(Z,47,'unit',[35],[141],note='Spire or Greater Spire'); u(Z,45,'unit',[35],[138]); u(Z,39,'unit',[35],[140]); u(Z,46,'unit',[35],[136])
u(Z,44,'unit',[43],[137],'morph'); u(Z,62,'unit',[43],[137],'morph'); u(Z,103,'unit',[38],[135],'morph',note='needs Lurker Aspect (tech 32) researched')
u(Z,50,'unit',[130]); u(Z,40,'unit',[45],[],'tech:13',note='Spawn Broodlings'); u(Z,35,'unit',[131],[],'auto')
# Protoss
u(P,154,'building',[64],[],'build'); u(P,156,'building',[64],[],'build'); u(P,157,'building',[64],[],'build')
u(P,160,'building',[64],[154],'build'); u(P,166,'building',[64],[154],'build'); u(P,162,'building',[64],[166],'build')
u(P,164,'building',[64],[160],'build'); u(P,172,'building',[64],[160],'build'); u(P,163,'building',[64],[164],'build')
u(P,155,'building',[64],[164],'build'); u(P,167,'building',[64],[164],'build'); u(P,165,'building',[64],[163],'build')
u(P,159,'building',[64],[155],'build'); u(P,171,'building',[64],[155],'build'); u(P,169,'building',[64],[167],'build'); u(P,170,'building',[64],[165,167],'build')
u(P,64,'unit',[154]); u(P,65,'unit',[160]); u(P,66,'unit',[160],[164]); u(P,67,'unit',[160],[165]); u(P,61,'unit',[160],[165])
u(P,68,'unit',[67],[],'merge',note='2 High Templar, tech 23'); u(P,63,'unit',[61],[],'merge',note='2 Dark Templar, tech 28')
u(P,69,'unit',[155]); u(P,83,'unit',[155],[171]); u(P,84,'unit',[155],[159]); u(P,70,'unit',[167]); u(P,60,'unit',[167])
u(P,72,'unit',[167],[169]); u(P,71,'unit',[167],[170]); u(P,73,'unit',[72]); u(P,85,'unit',[83])
UPG=[]
def g(race,id,by,mx=1,req=(),lvl_req=None,benefits=()):
    UPG.append(dict(id=id,name=UP[id],race=race,researched_at=by,max_level=mx,requires=list(req),level_requires=lvl_req or {},benefits=list(benefits)))
TINF=[0,32,1,34,10,16,20,99,100]; TVEH=[2,5,30,3,17,19,23,25]; TSHIP=[8,11,9,12,58,21,22,27,28,29,102]
g(T,0,122,3,[],{'2':[116],'3':[116]},TINF); g(T,7,122,3,[],{'2':[116],'3':[116]},[0,32,1,10,16,20,99,100])
g(T,1,123,3,[],{'2':[116],'3':[116]},TVEH); g(T,8,123,3,[],{'2':[116],'3':[116]},TVEH)
g(T,2,123,3,[],{'2':[116],'3':[116]},TSHIP); g(T,9,123,3,[],{'2':[116],'3':[116]},[8,12,58,21,27,28,29,102])
g(T,16,112,benefits=[0]); g(T,17,120,benefits=[2]); g(T,19,116,benefits=[9]); g(T,20,117,benefits=[1]); g(T,21,117,benefits=[1])
g(T,22,115,benefits=[8]); g(T,23,118,benefits=[12]); g(T,51,112,benefits=[34]); g(T,54,120,1,[123],benefits=[3])
ZG=[41,37,38,39,46,103,40,50,48,52,53,54]; ZA=[42,43,44,45,47,62,55,56,57,49]
g(Z,3,139,3,[],{'2':[132],'3':[133]},ZG); g(Z,10,139,3,[],{'2':[132],'3':[133]},[37,39,40,48,54])
g(Z,11,139,3,[],{'2':[132],'3':[133]},[38,103,53]); g(Z,4,141,3,[],{'2':[132],'3':[133]},ZA); g(Z,12,141,3,[],{'2':[132],'3':[133]},[43,44,62,55,56])
g(Z,24,132,1,[],None,[42,57]); g(Z,25,132,1,[],None,[42,57]); g(Z,26,132,1,[],None,[42,57]); g(Z,27,142,benefits=[37,54]); g(Z,28,142,1,[133],None,[37,54])
g(Z,29,135,1,[132],None,[38,53]); g(Z,30,135,1,[132],None,[38,53]); g(Z,31,138,benefits=[45,49]); g(Z,32,136,benefits=[46,52]); g(Z,52,140,benefits=[39,48]); g(Z,53,140,benefits=[39,48])
PG=[64,65,66,67,61,68,63,83,74,75,76,77,78,79,81,87]; PA=[69,84,70,60,72,71,73,80,82,86,88,98]
g(P,13,166,3,[],{'2':[165],'3':[165]},[65,66,68,61,74,75,76,77,78]); g(P,5,166,3,[],{'2':[165],'3':[165]},PG)
g(P,15,166,3,[],{'2':[164],'3':[164]},PG+PA); g(P,14,164,3,[],{'2':[169],'3':[169]},[70,60,72,71,73,80,82,86,88,98]); g(P,6,164,3,[],{'2':[169],'3':[169]},PA)
g(P,33,164,benefits=[66,78]); g(P,34,163,benefits=[65,77]); g(P,35,171,benefits=[83,81]); g(P,36,171,benefits=[83,81]); g(P,37,171,benefits=[69])
g(P,38,159,benefits=[84]); g(P,39,159,benefits=[84]); g(P,40,165,benefits=[67,79,87]); g(P,41,169,benefits=[70,80,88]); g(P,42,169,benefits=[70,80,88])
g(P,43,169,benefits=[72,82]); g(P,44,170,benefits=[71,86]); g(P,47,169,benefits=[60,98]); g(P,49,165,benefits=[63])
TE=[]
def t(race,id,by,req=(),default=False,users=()):
    TE.append(dict(id=id,name=TN[id],race=race,researched_at=by,requires=list(req),researched_by_default=default,users=list(users)))
t(T,0,112,users=[0,32,20]); t(T,1,117,users=[1,16,99,100]); t(T,2,116,users=[9,22]); t(T,3,120,users=[2,19]); t(T,4,None,default=True,users=[107])
t(T,5,120,users=[5,23]); t(T,6,None,default=True,users=[9,22]); t(T,7,116,users=[9,22]); t(T,8,118,users=[12,27,28,29,102]); t(T,9,115,users=[8,21])
t(T,10,117,users=[1,16,99,100]); t(T,24,112,users=[34]); t(T,30,112,users=[34]); t(T,34,None,default=True,users=[34])
t(Z,11,131,users=[41,37,38,46,50,103]); t(Z,12,None,default=True,users=[45,49]); t(Z,13,138,users=[45,49]); t(Z,14,None,default=True,users=[46,52])
t(Z,15,136,users=[46,52]); t(Z,16,136,users=[46,52]); t(Z,17,138,users=[45,49]); t(Z,18,None,default=True,users=[45,49]); t(Z,32,135,[132],users=[38])
t(P,19,165,users=[67,79,87]); t(P,20,165,users=[67,79,87]); t(P,21,170,users=[71,86]); t(P,22,170,users=[71,86]); t(P,23,None,default=True,users=[67])
t(P,25,169,users=[60,98]); t(P,27,165,users=[63]); t(P,28,None,default=True,users=[61]); t(P,29,None,default=True,users=[63]); t(P,31,165,users=[63])
out=dict(source='StarEdit/BWAPI index order (eudplib DefUnitDict/DefUpgradeDict/DefTechDict, BWAPI UnitTypes/UpgradeTypes/TechTypes); BW 1.16 rules',
 notes=['requires = buildings that must exist (owned, completed) besides the producer','Lair/Hive satisfy Hatchery/Lair requirements; Greater Spire satisfies Spire',
 'level_requires: extra building needed for upgrade level 2/3','benefits/users include campaign hero ids','weapon/armor families must share max level'],
 equivalents={'131':[132,133],'132':[133],'141':[137]},
 families=[[0,7],[1,8],[2,9],[3,10,11],[4,12],[5,13,15],[6,14]],
 units=U,upgrades=UPG,techs=TE,unit_names={str(k):v for k,v in UN.items()},upgrade_names={str(k):v for k,v in UP.items()},tech_names={str(k):v for k,v in TN.items()})
json.dump(out,open('bw_techtree.json','w'),indent=1); print(len(U),len(UPG),len(TE))
