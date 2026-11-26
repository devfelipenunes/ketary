"""Strict mutation evidence classifier regression tests."""
import pytest
from research.production_mutations import classify,read_evidence

def evidence(status,exit=0,id="test::case"):
    return {"exit":exit,"evidence":{"valid":True,"cases":[{"id":id,"status":status}]}}

@pytest.mark.parametrize("status,exit,want",[("assertion",1,"killed"),("passed",0,"survived"),("error",1,"invalid"),("unexpected_exception",1,"invalid"),("skipped",0,"invalid"),("assertion",2,"invalid")])
def test_classification(status,exit,want):
    assert classify(evidence("passed"),evidence(status,exit))==want

def test_no_fake_kill_on_different_cases():
    assert classify(evidence("passed"),evidence("assertion",1,id="other::case"))=="invalid"
    assert classify(evidence("skipped"),evidence("assertion",1))=="invalid_baseline"

@pytest.mark.parametrize("tag,body,want",[
    ("failure","test.py:1: AssertionError","assertion"),
    ("failure","test.py:1: Failed","assertion"),
    ("failure","test.py:1: TypeError","unexpected_exception"),
    ("error","setup failed","error"),
    ("skipped","reason","skipped")])
def test_xml_status(tmp_path,tag,body,want):
    path=tmp_path/"r.xml"
    path.write_text(f'<testsuites><testsuite><testcase classname="test" name="case"><{tag}>{body}</{tag}></testcase></testsuite></testsuites>')
    assert read_evidence(path)=={"valid":True,"cases":[{"id":"test::case","status":want}]}

def test_invalid_report(tmp_path):
    path=tmp_path/"missing.xml"
    assert not read_evidence(path)["valid"]
    path.write_text("<bad")
    assert not read_evidence(path)["valid"]
    path.write_text("<testsuites/>")
    assert not read_evidence(path)["valid"]
