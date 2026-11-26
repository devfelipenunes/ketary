// Research-only CPU bridge. No Ketary runtime dependency, no private Qiskit ABI.
#include "quest.h"
#include <chrono>
#include <cmath>
#include <complex>
#include <cstdint>
#include <cstring>
#include <type_traits>

static_assert(std::is_same<qreal,double>::value,"double precision only");
static_assert(sizeof(qcomp)==2*sizeof(double),"complex128 layout required");
using Clock=std::chrono::steady_clock;
static double ms(Clock::time_point a,Clock::time_point b) {
    return std::chrono::duration<double,std::milli>(b-a).count();
}
static bool ready=false;
static int multithreaded=0;
extern "C" int ketary_quest_init(int omp) {
    if (ready || (omp!=0 && omp!=1)) return 1;
    initCustomQuESTEnv(0,0,omp);
    multithreaded=omp; ready=true;
    return 0;
}
extern "C" int ketary_quest_close() {
    if (!ready) return 1;
    finalizeQuESTEnv();
    ready=false;
    return 0;
}

static void evolve(Qureg reg,int count,const int32_t* ops,const double* angles) {
    for(int i=0;i<count;++i) {
        int op=ops[3*i],a=ops[3*i+1],b=ops[3*i+2];
        switch(op) {
            case 0: applyHadamard(reg,a); break;
            case 1: applyPauliX(reg,a); break;
            case 2: applyPauliY(reg,a); break;
            case 3: applyPauliZ(reg,a); break;
            case 4: applyRotateX(reg,a,angles[i]); break;
            case 5: applyRotateY(reg,a,angles[i]); break;
            case 6: applyRotateZ(reg,a,angles[i]); break;
            case 7: applyControlledPauliX(reg,a,b); break;
            case 8: applyControlledPauliZ(reg,a,b); break;
            case 9: applySwap(reg,a,b); break;
            case 10: applyPhaseShift(reg,a,angles[i]); break;
        }
    }
}
static void export_state(Qureg reg,size_t size,double phase,double* output) {
    if(phase==0.) {
        std::memcpy(output,reg.cpuAmps,size*sizeof(qcomp));
    } else {
        const auto p=std::polar(1.,phase);
        for(size_t i=0;i<size;++i) {
            auto v=reg.cpuAmps[i]*p;
            output[2*i]=v.real(); output[2*i+1]=v.imag();
        }
    }
}

// Each operation: [opcode, first wire, second wire (-1 for single)].
// One FFI call per complete program. All rows validated before allocation.
// timings: allocation+input, gate kernel dispatch, output+phase+destroy.
extern "C" int ketary_quest_run(int n,int count,const int32_t* ops,
    const double* angles,const double* input,double phase,double* output,
    double* timings) {
    if (!ready || n<1 || n>22 || count<0 || count>100000 ||
        !ops || !angles || !input || !output || !timings || !std::isfinite(phase))
        return 2;
    for(int i=0;i<count;++i) {
        int op=ops[3*i], a=ops[3*i+1], b=ops[3*i+2];
        bool two=op>=7 && op<=9;
        if(op<0 || op>10 || a<0 || a>=n || !std::isfinite(angles[i]) ||
           (two ? (b<0 || b>=n || a==b) : b!=-1)) return 3;
    }
    auto start=Clock::now();
    Qureg reg=createCustomQureg(n,0,0,0,multithreaded);
    const size_t size=size_t(1)<<n;
    if(reg.isDistributed || reg.isGpuAccelerated || !reg.cpuAmps) {
        destroyQureg(reg); return 4;
    }
    // Documented CPU storage access; not valid for distributed/GPU registers.
    // std::complex<double> has interleaved real/imag representation.
    std::memcpy(reg.cpuAmps,input,size*sizeof(qcomp));
    auto allocated=Clock::now();
    evolve(reg,count,ops,angles);
    auto evolved=Clock::now();
    export_state(reg,size,phase,output);
    destroyQureg(reg);
    auto finished=Clock::now();
    timings[0]=ms(start,allocated);
    timings[1]=ms(allocated,evolved);
    timings[2]=ms(evolved,finished);
    return 0;
}

// Same immutable topology and input, independent angle rows. One register and
// one FFI boundary per batch. Timings: allocation, aggregate input, kernels,
// export, destruction (milliseconds). Output is row-major complex128.
extern "C" int ketary_quest_batch(int n,int count,int runs,const int32_t* ops,
    const double* angles,const double* input,double phase,double* output,double* timings) {
    if (!ready || n<1 || n>22 || count<0 || count>100000 || runs<1 || runs>256 ||
        !ops || !angles || !input || !output || !timings || !std::isfinite(phase)) return 2;
    const size_t size=size_t(1)<<n;
    if (size*size_t(runs)>size_t(128)*1024*1024/sizeof(qcomp)) return 5;
    for(int i=0;i<count;++i) {
        int op=ops[3*i],a=ops[3*i+1],b=ops[3*i+2];
        bool two=op>=7 && op<=9;
        if(op<0 || op>10 || a<0 || a>=n || (two?(b<0 || b>=n || a==b):b!=-1)) return 3;
    }
    for(size_t i=0;i<size_t(count)*runs;++i)
        if(!std::isfinite(angles[i])) return 3;
    for(int i=0;i<5;++i) timings[i]=0.;
    auto start=Clock::now();
    Qureg reg=createCustomQureg(n,0,0,0,multithreaded);
    if(reg.isDistributed || reg.isGpuAccelerated || !reg.cpuAmps) {
        destroyQureg(reg); return 4;
    }
    timings[0]=ms(start,Clock::now());
    for(int row=0;row<runs;++row) {
        auto t=Clock::now();
        std::memcpy(reg.cpuAmps,input,size*sizeof(qcomp));
        auto loaded=Clock::now();
        evolve(reg,count,ops,angles+size_t(row)*count);
        auto evolved=Clock::now();
        export_state(reg,size,phase,output+size_t(row)*size*2);
        auto exported=Clock::now();
        timings[1]+=ms(t,loaded);
        timings[2]+=ms(loaded,evolved);
        timings[3]+=ms(evolved,exported);
    }
    auto finish=Clock::now();
    destroyQureg(reg);
    timings[4]=ms(finish,Clock::now());
    return 0;
}
