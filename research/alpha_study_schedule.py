"""Fixed formative enrollment schedule; no generated participants/results."""
SCHEDULE=(("Ketary","A","Qiskit","B","VDH"),
          ("Qiskit","A","Ketary","B","DHV"),
          ("Ketary","B","Qiskit","A","HVD"),
          ("Qiskit","B","Ketary","A","VHD"),
          ("Ketary","A","Qiskit","B","HDV"))

def assignments(count):
    if type(count) is not int or not 3<=count<=5:
        raise ValueError("formative protocol requires 3..5 enrollment slots")
    return tuple(dict(slot=i+1,first_route=a,first_variant=b,
        second_route=c,second_variant=d,task_order=e)
        for i,(a,b,c,d,e) in enumerate(SCHEDULE[:count]))
