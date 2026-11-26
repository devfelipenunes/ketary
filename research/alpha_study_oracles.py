"""Reviewer-only mathematical values; no SDK, Qiskit or participant data."""
import numpy as np
from scipy.optimize import minimize_scalar

VARIANTS={"A":(.43,.61),"B":(.57,.39)}
EVOLUTION={"A":(.37,-.19,.23,.41,.53,.29,0,3,1j),
           "B":(-.28,.47,.31,.36,-.16,.62,1,2,-1j)}

def variational(key):
    a,b=VARIANTS[key]
    matrix=np.array([[2*a,b],[b,-2*a]])
    exact=float(np.linalg.eigvalsh(matrix)[0])
    result=minimize_scalar(lambda t:2*a*np.cos(t)+b*np.sin(t),
                           bounds=(-np.pi,np.pi),method="bounded")
    assert result.success and abs(result.fun-exact)<1e-7
    return exact

def phase_witness():
    correct=np.zeros(8,complex);correct[[0,7]]=1/np.sqrt(2)
    defective=correct.copy();defective[7]*=-1
    return correct,defective

def evolution(key,modified=False):
    a,b,c,t,updated_c,updated_t,left,right,phase=EVOLUTION[key]
    if modified:c,t=updated_c,updated_t
    v=np.zeros(4,complex);v[left]=1/np.sqrt(2);v[right]=phase/np.sqrt(2)
    z0=np.array([1.,-1.,1.,-1.]);z1=np.array([1.,1.,-1.,-1.])
    return np.exp(-1j*t*(a*z0+b*z1+c*z0*z1))*v
