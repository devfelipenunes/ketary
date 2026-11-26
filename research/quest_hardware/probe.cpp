// Research-only standalone process; explicit CPU/GPU/MPI deployment.
#include "quest.h"
#include <chrono>
#include <cmath>
#include <complex>
#include <cstdint>
#include <fstream>
#include <iostream>
#include <iomanip>
#include <stdexcept>
#include <string>
#include <type_traits>
#include <vector>
using Clock=std::chrono::steady_clock;
static_assert(std::is_same<qreal,double>::value,"double precision only");
static_assert(sizeof(qcomp)==2*sizeof(double),"complex128 layout required");
double ms(Clock::time_point a,Clock::time_point b) {
    return std::chrono::duration<double,std::milli>(b-a).count();
}
template<class T> void read(std::ifstream& f,T* ptr,size_t count) {
    if(!f.read(reinterpret_cast<char*>(ptr),count*sizeof(T)))
        throw std::runtime_error("truncated input");
}
struct Program {
    int32_t n,count; double phase;
    std::vector<int32_t> rows;
    std::vector<double> angles;
    std::vector<qcomp> state;
};
Program load(const char* path) {
    std::ifstream f(path,std::ios::binary);
    Program p{};
    read(f,&p.n,1);read(f,&p.count,1);read(f,&p.phase,1);
    if(p.n<2 || p.n>22 || p.count<1 || p.count>100000 || !std::isfinite(p.phase))
        throw std::runtime_error("invalid program header");
    p.rows.resize(3*p.count);p.angles.resize(p.count);p.state.resize(size_t(1)<<p.n);
    read(f,p.rows.data(),p.rows.size());read(f,p.angles.data(),p.angles.size());
    read(f,p.state.data(),p.state.size());
    if(f.peek()!=EOF) throw std::runtime_error("trailing data");
    for(int i=0;i<p.count;i++){
        int op=p.rows[3*i],a=p.rows[3*i+1],b=p.rows[3*i+2];
        bool two=op>=7 && op<=9;
        if(op<0 || op>10 || a<0 || a>=p.n || !std::isfinite(p.angles[i]) ||
           (two?(b<0 || b>=p.n || a==b):b!=-1)) throw std::runtime_error("invalid gate");
    }
    double norm=0.;
    for(auto z:p.state){
        if(!std::isfinite(z.real()) || !std::isfinite(z.imag())) throw std::runtime_error("nonfinite state");
        norm+=std::norm(z);
    }
    if(std::abs(norm-1.)>1e-9) throw std::runtime_error("nonunit input");
    return p;
}
void evolve(Qureg reg,const Program& p){
    for(int i=0;i<p.count;i++){
        int op=p.rows[3*i],a=p.rows[3*i+1],b=p.rows[3*i+2];
        double t=p.angles[i];
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
        }
    }
}
int main(int argc,char** argv){
    try{
        if(argc!=7) throw std::runtime_error("input output mode threads reps reuse");
        Program p=load(argv[1]);
        std::string mode=argv[3];
        if(mode!="cpu" && mode!="gpu" && mode!="mpi") throw std::runtime_error("invalid mode");
        int threads=std::stoi(argv[4]),reps=std::stoi(argv[5]),reuse=std::stoi(argv[6]);
        if(threads<1 || threads>64 || reps<3 || reps>100 || (reuse!=0 && reuse!=1))
            throw std::runtime_error("invalid repetitions/threads/reuse");
        bool mpi=mode=="mpi",gpu=mode=="gpu";
        initCustomQuESTEnv(mpi,gpu,threads>1);
        auto env=getQuESTEnv();
        if((mpi && env.numNodes<2) || bool(env.isDistributed)!=mpi ||
           bool(env.isGpuAccelerated)!=gpu) throw std::runtime_error("deployment mismatch");
        bool root=env.rank==0;
        if(root) std::cout<<std::setprecision(17);
        std::vector<qcomp> out(p.state.size());
        Qureg reg{};
        if(reuse) reg=createCustomQureg(p.n,0,mpi,gpu,threads>1);
        for(int i=0;i<reps+3;i++){
            syncQuESTEnv();
            auto t0=Clock::now();
            if(!reuse) reg=createCustomQureg(p.n,0,mpi,gpu,threads>1);
            initArbitraryPureState(reg,p.state.data());
            syncQuESTEnv();
            auto t1=Clock::now();
            evolve(reg,p);
            syncQuESTEnv();
            auto t2=Clock::now();
            // All ranks participate in gather. Full export is for correctness,
            // not a scalable distributed-storage design.
            getQuregAmps(out.data(),reg,0,out.size());
            syncQuESTEnv();
            if(!reuse) destroyQureg(reg);
            auto t3=Clock::now();
            if(root && i>=3)
                std::cout<<ms(t0,t1)<<","<<ms(t1,t2)<<","<<ms(t2,t3)<<"\n";
        }
        if(reuse) destroyQureg(reg);
        if(root){
            auto ph=std::polar(1.,p.phase);
            for(auto& z:out) z*=ph;
            std::ofstream file(argv[2],std::ios::binary);
            file.write(reinterpret_cast<const char*>(out.data()),out.size()*sizeof(qcomp));
            if(!file) throw std::runtime_error("output write failed");
        }
        syncQuESTEnv();
        finalizeQuESTEnv();
        return 0;
    }catch(const std::exception& e){std::cerr<<e.what()<<"\n";return 1;}
}
