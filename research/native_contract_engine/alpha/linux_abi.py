"""Audit the native Linux wheel ELF version requirements.

This is a static distribution gate, not a substitute for installation on
the oldest supported glibc host. Maturin separately audits the manylinux
tag and permitted libraries. Never repair or relabel a binary by hand.
"""
import json,pathlib,re,subprocess,sys,tempfile,zipfile

def inspect(wheel):
    wheel=pathlib.Path(wheel)
    with zipfile.ZipFile(wheel) as z:
        assert z.testzip() is None
        binaries=[n for n in z.namelist() if n.endswith(".so")]
        assert binaries
        rows=[]
        with tempfile.TemporaryDirectory() as tmp:
            for i,name in enumerate(binaries):
                p=pathlib.Path(tmp)/f"{i}.so";p.write_bytes(z.read(name))
                version=subprocess.check_output(["readelf","--version-info",p],text=True)
                dynamic=subprocess.check_output(["readelf","-d",p],text=True)
                # Only version requirements, not versions defined by the ELF.
                needs=version.split("Version needs section",1)[-1]
                names=sorted(set(re.findall(r"Name: (GLIBC_\S+)",needs)))
                versions=[]
                for v in names:
                    match=re.fullmatch(r"GLIBC_([0-9]+(?:\.[0-9]+)+)",v)
                    if not match:raise ValueError(f"unclassified GLIBC requirement: {v}")
                    versions.append(tuple(map(int,match[1].split("."))))
                maximum=max(versions,default=(0,0))
                libraries=sorted(set(re.findall(r"Shared library: \[([^\]]+)\]",dynamic)))
                rows.append({"member":name,"glibc_requirements":names,"max_glibc":".".join(map(str,maximum)),
                             "needed_libraries":libraries})
                if maximum>(2,34):raise ValueError(f"GLIBC requirement exceeds 2.34: {name}")
    return {"wheel":wheel.name,"binaries":rows,"scope":"ELF symbol version audit, not runtime compatibility"}

if __name__=="__main__":print(json.dumps(inspect(sys.argv[1]),indent=2))
