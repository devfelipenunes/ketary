// Research-only extension using documented Qiskit 2.6 C API.
#define PY_SSIZE_T_CLEAN
#include <Python.h>
#define QISKIT_PYTHON_EXTENSION
#include <qiskit.h>
#include <stdint.h>
#include <string.h>
#include <math.h>

static const QkGate gates[]={QkGate_H,QkGate_X,QkGate_Z,QkGate_RX,QkGate_RY,QkGate_RZ,QkGate_CX,QkGate_CZ};
static const char *names[]={"h","x","z","rx","ry","rz","cx","cz"};
static int two(int op){return op>=6;}
static int angle(int op){return op>=3 && op<=5;}
static int decode(const QkCircuitInstructionView *v){
    for(int i=0;i<8;i++)
        if(strlen(names[i])==v->name_len && memcmp(names[i],v->name,v->name_len)==0) return i;
    return -1;
}
static PyObject *bad(const char *msg){PyErr_SetString(PyExc_ValueError,msg);return NULL;}

static PyObject *build(PyObject *self,PyObject *args){
    int n; double phase; PyObject *r,*p;
    if(!PyArg_ParseTuple(args,"iOOd",&n,&r,&p,&phase)) return NULL;
    if(n<1 || n>4096 || !isfinite(phase) || !PyBytes_Check(r) || !PyBytes_Check(p))
        return bad("invalid circuit input");
    Py_ssize_t bytes=PyBytes_GET_SIZE(r), count=bytes/(3*sizeof(int32_t));
    if(bytes%(3*sizeof(int32_t)) || count>100000 || PyBytes_GET_SIZE(p)!=count*sizeof(double))
        return bad("invalid operation payload");
    const char *rows=PyBytes_AS_STRING(r),*angles=PyBytes_AS_STRING(p);
    for(Py_ssize_t i=0;i<count;i++){
        int32_t row[3];double theta;
        memcpy(row,rows+i*sizeof(row),sizeof(row));
        memcpy(&theta,angles+i*sizeof(theta),sizeof(theta));
        int op=row[0],a=row[1],b=row[2];
        if(op<0 || op>=8 || a<0 || a>=n || !isfinite(theta) ||
           (two(op)?(b<0 || b>=n || a==b):b!=-1)) return bad("invalid gate row");
    }
    QkCircuit *qc=qk_circuit_new(n,0);
    QkParam *ph=qk_param_from_double(phase);
    QkExitCode rc=qk_circuit_set_global_phase(qc,ph);
    qk_param_free(ph);
    if(rc!=QkExitCode_Success){qk_circuit_free(qc);return bad("global phase rejected");}
    for(Py_ssize_t i=0;i<count;i++){
        int32_t row[3];double theta;
        memcpy(row,rows+i*sizeof(row),sizeof(row));
        memcpy(&theta,angles+i*sizeof(theta),sizeof(theta));
        uint32_t wires[2]={(uint32_t)row[1],(uint32_t)row[2]};
        rc=qk_circuit_gate(qc,gates[row[0]],wires,angle(row[0])?&theta:NULL);
        if(rc!=QkExitCode_Success){qk_circuit_free(qc);return bad("native gate rejected");}
    }
    // Ownership moves to Python. No borrowed native pointer escapes.
    return qk_circuit_to_python_full(qc);
}

static PyObject *pack(PyObject *self,PyObject *data){
    QkCircuit *qc=qk_circuit_borrow_from_python(data);
    if(!qc) return NULL;
    uint32_t n=qk_circuit_num_qubits(qc);
    size_t count=qk_circuit_num_instructions(qc);
    if(!n || n>4096 || count>100000 || qk_circuit_num_clbits(qc) ||
       qk_circuit_num_param_symbols(qc)) return bad("unsupported circuit mode or size");
    QkParam *phase=qk_circuit_global_phase(qc);
    double ph=qk_param_as_real(phase);
    qk_param_free(phase);
    if(!isfinite(ph)) return bad("nonfinite phase");
    PyObject *r=PyBytes_FromStringAndSize(NULL,count*3*sizeof(int32_t));
    PyObject *p=PyBytes_FromStringAndSize(NULL,count*sizeof(double));
    if(!r || !p){Py_XDECREF(r);Py_XDECREF(p);return NULL;}
    for(size_t i=0;i<count;i++){
        // Only native standard gates: name alone cannot authorize a custom gate.
        if(qk_circuit_instruction_kind(qc,i)!=QkOperationKind_Gate) goto reject;
        QkCircuitInstructionView v;
        qk_circuit_view_instruction(qc,i,&v);
        int op=decode(&v);
        if(op<0 || v.num_clbits || v.num_qubits!=(two(op)?2:1) ||
           v.num_params!=(angle(op)?1:0)) goto reject;
        if(v.qubits[0]>=n || (two(op)&&(v.qubits[1]>=n || v.qubits[0]==v.qubits[1]))) goto reject;
        double theta=0.;
        if(angle(op)){
            if(qk_param_kind(v.params)!=QkParamKind_Real) goto reject;
            theta=qk_param_as_real(v.params);
            if(!isfinite(theta)) goto reject;
        }
        int32_t row[3]={op,(int32_t)v.qubits[0],two(op)?(int32_t)v.qubits[1]:-1};
        memcpy(PyBytes_AS_STRING(r)+i*sizeof(row),row,sizeof(row));
        memcpy(PyBytes_AS_STRING(p)+i*sizeof(theta),&theta,sizeof(theta));
    }
    // GIL retained; no native mutation, and instruction views do not escape.
    return Py_BuildValue("iNNd",(int)n,r,p,ph);
reject:
    Py_DECREF(r);Py_DECREF(p);return bad("unsupported native instruction");
}

static PyMethodDef methods[]={
    {"build",build,METH_VARARGS,"Build native circuit from bounded packed rows."},
    {"pack",pack,METH_O,"Read native standard-gate data without Python gate objects."},
    {NULL,NULL,0,NULL}
};
static struct PyModuleDef module={PyModuleDef_HEAD_INIT,"_ketary_capi_probe",NULL,-1,methods};
PyMODINIT_FUNC PyInit__ketary_capi_probe(void){
    if(qk_import()<0) return NULL;
    return PyModule_Create(&module);
}
