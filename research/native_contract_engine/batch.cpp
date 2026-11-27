#include <cstdint>
#include <cstddef>
// Research C ABI: caller owns valid nonoverlapping contiguous buffers.
extern "C" int batch_bitslice(const uint8_t* g,size_t count,uint32_t n,uint64_t* x,uint64_t* z,uint8_t* r,size_t m){
 if(!g||!x||!z||!r||!n||n>64||!m||m>64||count>1000000)return 1;
 for(size_t j=0;j<m;++j)if(r[j]>1||(n<64&&((x[j]|z[j])>>n)))return 1;
 for(size_t i=0;i<count;++i){const auto* v=g+3*i;if(v[0]>5||v[1]>=n||(v[0]==5&&(v[2]>=n||v[1]==v[2])))return 2;}
 uint64_t X[64]={},Z[64]={},R=0;
 for(size_t j=0;j<m;++j){uint64_t lane=uint64_t(1)<<j;if(r[j])R|=lane;
  for(uint32_t i=0;i<n;++i){X[i]|=((x[j]>>i)&1)?lane:0;Z[i]|=((z[j]>>i)&1)?lane:0;}}
 for(size_t i=count;i>0;--i){const auto*v=g+3*(i-1);unsigned a=v[1],b=v[2];uint64_t xa=X[a],za=Z[a];
  switch(v[0]){
   case 0:R^=xa&za;X[a]=za;Z[a]=xa;break;
   case 1:R^=xa&~za;Z[a]^=xa;break;
   case 2:R^=xa&za;Z[a]^=xa;break;
   case 3:R^=za;break;
   case 4:R^=xa;break;
   case 5:{uint64_t xb=X[b],zb=Z[b];R^=xa&zb&~(xb^za);X[b]^=xa;Z[a]^=zb;break;}
  }
 }
 for(size_t j=0;j<m;++j){uint64_t xx=0,zz=0;for(uint32_t i=0;i<n;++i){xx|=((X[i]>>j)&1)<<i;zz|=((Z[i]>>j)&1)<<i;}x[j]=xx;z[j]=zz;r[j]=(R>>j)&1;}
 return 0;
}
