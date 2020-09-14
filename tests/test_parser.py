from datetime import datetime

import pytest

import vcd_parser
from vcd_parser import VCD

def test_tokenize():
    TOKENS = ['$keyword', '"', 'word', '123', '16/8/2048', '-0.42', '4:20', '#0', 'b001011"']
    WHITESPACE = [' ', '\t', '\n', '   ', '\t\t\t', '\n\n\n', ' \t ', '\r\n', '\t \r\n \t \n\t']
    class DummyFile:
        def open(self):
            for tok, sep in zip(TOKENS, WHITESPACE):
                yield tok+sep
    parsed_tokens = list(VCD._tokenize(DummyFile()))
    assert parsed_tokens == TOKENS

ENDDEFS = ['$enddefinitions', '$end']

def make_mock_tokenize(monkeypatch, tokens):
    def mock__tokenize(file):
        yield from tokens
    monkeypatch.setattr(VCD, '_tokenize', mock__tokenize)

def test_minimal_vcd(monkeypatch, tmp_path):
    TOKENS = ENDDEFS
    make_mock_tokenize(monkeypatch, TOKENS)

    vcd = VCD(tmp_path)
    assert vcd._headers_complete
    assert vcd.comments == []
    assert vcd.date == None
    assert vcd.version == None
    assert vcd.vars == {}

def test_enddefs_extra_token(monkeypatch, tmp_path):
    TOKENS = [ENDDEFS[0], 'tok', ENDDEFS[1]]
    make_mock_tokenize(monkeypatch, TOKENS)

    with pytest.raises(vcd_parser.vcd.VcdSyntaxError):
        vcd = VCD(tmp_path)

@pytest.mark.xfail(raises=StopIteration)
def test_empty(monkeypatch, tmp_path):
    TOKENS = []
    make_mock_tokenize(monkeypatch, TOKENS)

    with pytest.raises(vcd_parser.vcd.VcdSyntaxError):
        vcd = VCD(tmp_path)


@pytest.mark.xfail(raises=StopIteration)
def test_missing_end(monkeypatch, tmp_path):
    TOKENS = ['$comment', 'a', 'b']
    make_mock_tokenize(monkeypatch, TOKENS)

    with pytest.raises(vcd_parser.vcd.VcdSyntaxError):
        vcd = VCD(tmp_path)


@pytest.mark.xfail(raises=StopIteration)
def test_missing_end_upscope(monkeypatch, tmp_path):
    TOKENS = ['$upscope']
    make_mock_tokenize(monkeypatch, TOKENS)

    with pytest.raises(vcd_parser.vcd.VcdSyntaxError):
        vcd = VCD(tmp_path)


@pytest.mark.xfail(raises=StopIteration)
def test_missing_end_enddefs(monkeypatch, tmp_path):
    TOKENS = [ENDDEFS[0]]
    make_mock_tokenize(monkeypatch, TOKENS)

    with pytest.raises(vcd_parser.vcd.VcdSyntaxError):
        vcd = VCD(tmp_path)


@pytest.mark.xfail(raises=KeyError)
def test_unknown_keyword(monkeypatch, tmp_path):
    TOKENS = ['$unknown', '$end'] + ENDDEFS
    make_mock_tokenize(monkeypatch, TOKENS)

    with pytest.raises(vcd_parser.vcd.VcdSyntaxError):
        vcd = VCD(tmp_path)
    assert list(vcd._token_stream) == ['$end'] + ENDDEFS

def test_comment(monkeypatch, tmp_path):
    TOKENS = ['$comment', 'Hello,', 'world!', '$end'] + ENDDEFS
    make_mock_tokenize(monkeypatch, TOKENS)

    vcd = VCD(tmp_path)
    assert vcd.comments == ['Hello, world!']
    assert vcd.date == None
    assert vcd.version == None
    assert vcd.vars == {}

def test_empty_comment(monkeypatch, tmp_path):
    TOKENS = ['$comment', '$end'] + ENDDEFS
    make_mock_tokenize(monkeypatch, TOKENS)

    vcd = VCD(tmp_path)
    assert vcd.comments == ['']
    assert vcd.date == None
    assert vcd.version == None
    assert vcd.vars == {}

def test_comment(monkeypatch, tmp_path):
    TOKENS = ['$comment', 'Hello,', 'world!', '$end',
              '$comment', '$end',
              '$comment', 'comment3', '$end'] + ENDDEFS
    make_mock_tokenize(monkeypatch, TOKENS)

    vcd = VCD(tmp_path)
    assert vcd.comments == ['Hello, world!', '', 'comment3']
    assert vcd.date == None
    assert vcd.version == None
    assert vcd.vars == {}

def test_version(monkeypatch, tmp_path):
    TOKENS = ['$version', 'test', 'v0.0.1', '$end'] + ENDDEFS
    make_mock_tokenize(monkeypatch, TOKENS)

    vcd = VCD(tmp_path)
    assert vcd.comments == []
    assert vcd.date == None
    assert vcd.version == 'test v0.0.1'
    assert vcd.vars == {}

def test_version_empty(monkeypatch, tmp_path):
    TOKENS = ['$version', '$end'] + ENDDEFS
    make_mock_tokenize(monkeypatch, TOKENS)

    vcd = VCD(tmp_path)
    assert vcd.comments == []
    assert vcd.date == None
    assert vcd.version == ''
    assert vcd.vars == {}

def test_date(monkeypatch, tmp_path):
    t = datetime.now()
    TOKENS = ['$date', t.isoformat(), '$end'] + ENDDEFS
    make_mock_tokenize(monkeypatch, TOKENS)

    vcd = VCD(tmp_path)
    assert vcd.comments == []
    assert vcd.date == t
    assert vcd.version == None
    assert vcd.vars == {}

def test_date_unparseable(monkeypatch, tmp_path):
    TOKENS = ['$date', 'unparseable', 'date', '$end'] + ENDDEFS
    make_mock_tokenize(monkeypatch, TOKENS)

    vcd = VCD(tmp_path)
    assert vcd.comments == []
    assert vcd.date == 'unparseable date'
    assert vcd.version == None
    assert vcd.vars == {}
