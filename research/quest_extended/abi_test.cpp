// Direct ABI regression. No Python, no Qiskit; each call owns its buffers.
// Test with assertions independent of NDEBUG, including rejected calls.
#include <array>
#include <cmath>
#include <cstdint>
#include <cstdlib>
#include <iostream>
#include <limits>
#include <vector>
extern "C" int extended_abi_version();
extern "C" int extended_row_width();
extern "C" int extended_scalar_bytes();
extern "C" int extended_index_bytes();
extern "C" int extended_init();
extern "C" int extended_close();
extern "C" int extended_run(int,int,int,const int32_t*,const double*,const double*,double,double*,double*);
static void require(bool yes,const char* msg){
    if(!yes){std::cerr<<msg<<"\n";std::exit(1);}
}
int main(){
    require(extended_abi_version()==2 && extended_row_width()==24 &&
            extended_scalar_bytes()==8 && extended_index_bytes()==4,"ABI mismatch");
    std::array<int32_t,24> row;row.fill(-1);row[0]=1;row[1]=1;row[2]=2;
    std::array<double,2> theta={0.,0.};
    std::array<double,16> input{};input[0]=1.;
    std::array<double,32> output;
    std::array<double,5> times;
    auto call=[&](int n,int count,int runs,double phase){
        output.fill(99.);times.fill(99.);
        return extended_run(n,count,runs,row.data(),theta.data(),input.data(),phase,output.data(),times.data());
    };
    auto untouched=[&](){
        for(double x:output)require(x==99.,"rejected call wrote output");
        for(double x:times)require(x==99.,"rejected call wrote timing");
    };
    require(call(3,1,1,0.)==2,"uninitialized accepted");untouched();
    require(extended_init()==0,"init failed");
    require(extended_init()==1,"double init accepted");
    require(call(0,1,1,0.)==2,"invalid width accepted");untouched();
    require(call(3,-1,1,0.)==2,"negative count accepted");untouched();
    require(call(3,100001,1,0.)==2,"large count accepted");untouched();
    require(call(3,1,257,0.)==2,"large batch accepted");untouched();
    require(call(22,1,3,0.)==5,"large output accepted");untouched();
    require(call(3,100000,100,0.)==5,"large angle table accepted");untouched();
    require(call(3,1,1,std::numeric_limits<double>::infinity())==2,"nonfinite phase accepted");untouched();
    row[0]=99;require(call(3,1,1,0.)==3,"invalid opcode accepted");untouched();row[0]=1;
    row[2]=3;require(call(3,1,1,0.)==3,"invalid wire accepted");untouched();row[2]=2;
    row[3]=1;require(call(3,1,1,0.)==3,"invalid padding accepted");untouched();row[3]=-1;
    row[0]=7;row[1]=2;row[3]=2;
    require(call(3,1,1,0.)==3,"duplicate wires accepted");untouched();row[0]=1;row[1]=1;row[3]=-1;
    theta[1]=std::numeric_limits<double>::quiet_NaN();
    require(call(3,1,2,0.)==3,"nonfinite later row accepted");untouched();theta[1]=0.;
    require(call(3,1,2,.37)==0,"valid batch failed");
    for(int run=0;run<2;run++)for(int i=0;i<8;i++){
        double re=i==4?std::cos(.37):0.,im=i==4?std::sin(.37):0.;
        require(std::abs(output[run*16+2*i]-re)<1e-12,"wrong real");
        require(std::abs(output[run*16+2*i+1]-im)<1e-12,"wrong imag");
    }
    for(double t:times)require(std::isfinite(t)&&t>=0.,"invalid stage timing");
    require(input[0]==1.,"input mutated");
    for(size_t i=1;i<input.size();i++)require(input[i]==0.,"input mutated");
    require(extended_close()==0,"close failed");
    require(extended_close()==1,"double close accepted");
    require(call(3,1,1,0.)==2,"closed engine accepted call");untouched();
    std::cout<<"native v2 ABI checks passed\n";
}
