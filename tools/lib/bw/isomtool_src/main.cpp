#include "mapping_core/scenario.h"
#include "cross_cut/logger.h"
Logger logger(LogLevel::Error);
#include <fstream>
#include <iostream>
#include <cstring>
struct MyCache : Chk::IsomCache { Scenario & m; MyCache(Sc::Terrain::Tileset t,size_t w,size_t h,const Sc::Terrain::Tiles & d,Scenario & m):Chk::IsomCache(t,w,h,d),m(m){}
 void setTileValue(size_t x,size_t y,uint16_t v) override { m.setTile(x,y,v,Chk::Scope::Both); } };
int main(int argc,char**argv){
  if(argc<4){ // list mode: cv5 tilesetIdx
    std::cerr<<"usage: isomtool cv5 tilesetIdx script out\n"; }
  std::ifstream f(argv[1],std::ios::binary); std::vector<char> d((std::istreambuf_iterator<char>(f)),{});
  size_t ts=std::stoul(argv[2]);
  Sc::Terrain::Tiles tiles; tiles.tileGroups.resize(d.size()/sizeof(Sc::Terrain::TileGroup));
  std::memcpy(tiles.tileGroups.data(),d.data(),tiles.tileGroups.size()*sizeof(Sc::Terrain::TileGroup));
  tiles.loadIsom(ts);
  if(argc==3){ for(size_t i=0;i<tiles.terrainTypes.size();i++){auto&t=tiles.terrainTypes[i]; std::cout<<i<<" "<<t.name<<" sort="<<t.brushSortOrder<<" isom="<<t.isomValue<<"\n";} return 0;}
  std::ifstream s(argv[3]); size_t W,H,base; s>>W>>H>>base;
  Scenario map(Sc::Terrain::Tileset(ts),u16(W),u16(H),base,Chk::DefaultTriggers::NoTriggers,SaveType::HybridScm,&tiles);
  MyCache cache(Sc::Terrain::Tileset(ts),W,H,tiles,map);
  size_t x,y,t,b; int n=0;
  while(s>>x>>y>>t>>b){ if(map.placeIsomTerrain({x,y},t,b,cache)){ n++; map.updateTilesFromIsom(cache);} }

  std::ofstream o(argv[4],std::ios::binary);
  for(size_t yy=0;yy<H;yy++)for(size_t xx=0;xx<W;xx++){u16 v=map.getTile(xx,yy,Chk::Scope::Editor); o.write((char*)&v,2);}
  for(size_t i=0;i<(W/2+1)*(H+1);i++){auto r=map.getIsomRect(i); o.write((char*)&r,8);}
  std::cerr<<"placed "<<n<<"\n";
}
