#include <cstdint>
#include <cstddef>
// Research C ABI, same admitted gates and input/output as Rust.
extern "C" int propagate(const uint8_t* gates,size_t count,uint32_t n,
 uint64_t* x,uint64_t* z,uint8_t* r){
 if(!gates||!x||!z||!r||n<1||n>64||count>1000000||*r>1)return 1;
 if(n<64&&((*x|*z)>>n))return 1;
 uint64_t X=*x,Z=*z;uint8_t R=*r;
 for(size_t i=count;i>0;--i){
  const uint8_t* g=gates+3*(i-1);unsigned op=g[0],a=g[1],b=g[2];
  if(a>=n||op>5||(op==5&&(b>=n||a==b)))return 2;
  uint64_t A=uint64_t(1)<<a;bool xa=(X&A)!=0,za=(Z&A)!=0;
  switch(op){
   case 0:R^=xa&za;if(xa!=za){X^=A;Z^=A;}break;
   case 1:R^=xa&!za;if(xa)Z^=A;break;
   case 2:R^=xa&za;if(xa)Z^=A;break;
   case 3:R^=za;break;
   case 4:R^=xa;break;
   case 5:{uint64_t B=uint64_t(1)<<b;bool xb=(X&B)!=0,zb=(Z&B)!=0;
    R^=xa&zb&!(xb^za);if(xa)X^=B;if(zb)Z^=A;break;}
  }
 }
 *x=X;*z=Z;*r=R;return 0;
}
