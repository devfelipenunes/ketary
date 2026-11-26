// Research-only v2 CPU bridge; legacy ABI remains untouched.
#include "quest.h"
#include <chrono>
#include <cmath>
#include <complex>
#include <cstdint>
#include <cstring>
#include <type_traits>
static_assert(std::is_same<qreal,double>::value,"double only");
static_assert(sizeof(qcomp)==2*sizeof(double),"complex128 layout");
using Clock=std::chrono::steady_clock;
static double ms(Clock::time_point a,Clock::time_point b){
    return std::chrono::duration<double,std::milli>(b-a).count();
}
static bool ready=false;
extern "C" int extended_init(){
    if(ready)return 1;
    initCustomQuESTEnv(0,0,0);ready=true;return 0;
}
extern "C" int extended_close(){
    if(!ready)return 1;
    finalizeQuESTEnv();ready=false;return 0;
}
static bool valid(int n,const int32_t* row,double theta){
    int op=row[0],k=row[1];
    if(op<0||op>14||!std::isfinite(theta))return false;
    int want=op==13?3:((op>=7&&op<=9)||op==11||op==12)?2:1;
    if(op==14 ? (k<3||k>n) : k!=want)return false;
    for(int j=0;j<22;j++){
        int wire=row[j+2];
        if(j>=k){if(wire!=-1)return false;continue;}
        if(wire<0||wire>=n)return false;
        for(int i=0;i<j;i++)if(row[i+2]==wire)return false;
    }
    return true;
}
static void evolve(Qureg reg,const int32_t* rows,const double* angles,int count){
    for(int i=0;i<count;i++){
        const int32_t* row=rows+24*i;
        int op=row[0],k=row[1],a=row[2],b=row[3];double t=angles[i];
        switch(op){
            case 0:applyHadamard(reg,a);break;
            case 1:applyPauliX(reg,a);break;
            case 2:applyPauliY(reg,a);break;
            case 3:applyPauliZ(reg,a);break;
            case 4:applyRotateX(reg,a,t);break;
            case 5:applyRotateY(reg,a,t);break;
            case 6:applyRotateZ(reg,a,t);break;
            case 7:applyControlledPauliX(reg,a,b);break;
            case 8:applyControlledPauliZ(reg,a,b);break;
            case 9:applySwap(reg,a,b);break;
            case 10:applyPhaseShift(reg,a,t);break;
            case 11:applyTwoQubitPhaseShift(reg,a,b,t);break;
            case 12:applyPauliGadget(reg,getInlinePauliStr("ZZ",{a,b}),t);break;
            case 13:case 14:{
                int controls[21];
                for(int j=0;j<k-1;j++)controls[j]=row[j+2];
                applyMultiControlledPauliX(reg,controls,k-1,row[k+1]);break;
            }
        }
    }
}
// One explicit CPU register per call; independent row inputs share topology.
// Single-run output is written directly into fresh Python-owned memory.
extern "C" int extended_run(int n,int count,int runs,const int32_t* rows,
    const double* angles,const double* input,double phase,double* output,double* timing){
    if(!ready||n<1||n>22||count<0||count>100000||runs<1||runs>256||
        !rows||!angles||!input||!output||!timing||!std::isfinite(phase))return 2;
    size_t size=size_t(1)<<n;
    if(size*size_t(runs)>size_t(128)*1024*1024/sizeof(qcomp)||
       size_t(count)*runs>size_t(64)*1024*1024/sizeof(double))return 5;
    for(int i=0;i<count;i++)if(!valid(n,rows+24*i,angles[i]))return 3;
    for(size_t i=0;i<size_t(count)*runs;i++)if(!std::isfinite(angles[i]))return 3;
    for(int i=0;i<5;i++)timing[i]=0.;
    auto start=Clock::now();
    Qureg reg=createCustomQureg(n,0,0,0,0);
    if(reg.isDistributed||reg.isGpuAccelerated||!reg.cpuAmps){destroyQureg(reg);return 4;}
    timing[0]=ms(start,Clock::now());
    auto factor=std::polar(1.,phase);
    for(int row=0;row<runs;row++){
        auto t=Clock::now();
        std::memcpy(reg.cpuAmps,input,size*sizeof(qcomp));
        auto loaded=Clock::now();
        evolve(reg,rows,angles+size_t(row)*count,count);
        auto evolved=Clock::now();
        double* dest=output+size_t(row)*size*2;
        if(phase==0.)std::memcpy(dest,reg.cpuAmps,size*sizeof(qcomp));
        else for(size_t j=0;j<size;j++){
            auto z=reg.cpuAmps[j]*factor;dest[2*j]=z.real();dest[2*j+1]=z.imag();
        }
        auto exported=Clock::now();
        timing[1]+=ms(t,loaded);timing[2]+=ms(loaded,evolved);timing[3]+=ms(evolved,exported);
    }
    auto finish=Clock::now();destroyQureg(reg);timing[4]=ms(finish,Clock::now());
    return 0;
}
