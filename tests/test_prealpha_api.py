"""Signature parity and bounded public contracts, including installed stubs."""
import ast
import inspect
from pathlib import Path
import pytest
import ketary as q

def surface():
    c=q.Circuit(2)
    r=q.bell().run()
    classes={name:getattr(q,name) for name in q.__all__ if inspect.isclass(getattr(q,name))}
    classes.update({type(obj).__name__:type(obj) for obj in
                    (c.gates,c.debug,c.test,c.resources,c.visualize,r.math,r.test,r.visualize)})
    return classes

def shape(sig):
    return [(p.name,p.kind,p.default is not inspect.Parameter.empty) for p in sig.parameters.values()]

def ast_shape(node):
    a=node.args
    positional=a.posonlyargs+a.args
    required=len(positional)-len(a.defaults)
    rows=[(arg.arg,inspect.Parameter.POSITIONAL_ONLY if i<len(a.posonlyargs) else inspect.Parameter.POSITIONAL_OR_KEYWORD,i>=required)
          for i,arg in enumerate(positional)]
    if a.vararg:
        rows.append((a.vararg.arg,inspect.Parameter.VAR_POSITIONAL,False))
    rows.extend((arg.arg,inspect.Parameter.KEYWORD_ONLY,d is not None) for arg,d in zip(a.kwonlyargs,a.kw_defaults,strict=True))
    if a.kwarg:
        rows.append((a.kwarg.arg,inspect.Parameter.VAR_KEYWORD,False))
    return rows

def assert_overload_shape(signature,nodes):
    runtime=shape(signature)
    variants=[ast_shape(n) for n in nodes]
    if len(variants)==1 or all(v==variants[0] for v in variants):
        assert runtime==variants[0]
        return
    assert all(any(isinstance(d,ast.Name) and d.id=="overload" for d in n.decorator_list)
               for n in nodes)
    names={name:(kind,default) for name,kind,default in runtime}
    covered=set()
    for variant in variants:
        wanted={name for name,_,_ in variant}
        assert wanted<=names.keys()
        assert [name for name,_,_ in variant]==[name for name,_,_ in runtime if name in wanted]
        for name,kind,default in variant:
            actual_kind,actual_default=names[name]
            assert kind==actual_kind
            assert not default or actual_default
        for name,kind,default in runtime:
            if not default and kind not in (inspect.Parameter.VAR_POSITIONAL,inspect.Parameter.VAR_KEYWORD):
                assert name in wanted
        covered.update(wanted)
    assert covered==names.keys()


def test_stub_signatures_and_complete_method_surface():
    root=ast.parse(Path(q.__file__).with_name("__init__.pyi").read_text())
    classes=surface()
    declared={node.name:node for node in root.body if isinstance(node,ast.ClassDef)}
    for name,cls in classes.items():
        assert name in declared
        methods={}
        for node in declared[name].body:
            if isinstance(node,ast.FunctionDef):
                methods.setdefault(node.name,[]).append(node)
        public={key for key,value in vars(cls).items() if not key.startswith("_") and
                (callable(value) or isinstance(value,(property,classmethod,staticmethod)))}
        assert public<=set(methods),(name,public-set(methods))
        for key,nodes in methods.items():
            if key in getattr(cls,'__dataclass_fields__',{}) and key not in vars(cls):
                continue
            value=inspect.getattr_static(cls,key)
            if isinstance(value,property):
                value=value.fget
            elif isinstance(value,(classmethod,staticmethod)):
                value=value.__func__
            elif not callable(value):
                # Frozen dataclass field exposed as read-only property in stub.
                assert key in getattr(cls,"__dataclass_fields__",{}),(name,key)
                continue
            try:
                assert_overload_shape(inspect.signature(value),nodes)
            except AssertionError as exc:
                raise AssertionError((name,key)) from exc
    functions={n.name:n for n in root.body if isinstance(n,ast.FunctionDef)}
    for name in q.__all__:
        obj=getattr(q,name)
        if inspect.isfunction(obj):
            assert shape(inspect.signature(obj))==ast_shape(functions[name]),name
    assert set(functions)=={name for name in q.__all__ if inspect.isfunction(getattr(q,name))}

def test_mode_and_snapshot_compatibility():
    c=q.bell()
    r=c.run()
    c.z(0)
    assert r.math.expectation("XX")==pytest.approx(1)
    assert c.analyze().math.expectation("XX")==pytest.approx(-1)
    assert q.Circuit(2).gates.h(0).cx(0,1).test.equivalent(q.bell()).status=="PASS"
    for budget in (0,True,"64"):
        with pytest.raises(ValueError):
            r.math.purity(max_bytes=budget)
    assert r.math.purity(max_bytes=1)==1
    assert q.Circuit.classical(2,2).capabilities["run_shots"]
    assert not q.Circuit.classical(2,2).capabilities["run_statevector"]
