"""The download path, which only a fresh checkout ever exercises.

This is the one module no analysis run touches: once `data/raw/` exists, nothing
calls it again. That is precisely why it broke unnoticed, and why it is tested
here against a stubbed OSF rather than the network.
"""

import json
from io import BytesIO

import pytest

from wcab import io as wio


class _Response(BytesIO):
    """Minimal stand-in for what `urlopen` returns as a context manager."""

    def __enter__(self):
        return self

    def __exit__(self, *exc):
        self.close()
        return False


def _listing(names):
    return {
        "data": [
            {"attributes": {"name": n}, "links": {"download": f"https://osf/{n}"}}
            for n in names
        ]
    }


@pytest.fixture
def osf(monkeypatch):
    """Serve a listing first, then file bytes, recording what was requested."""
    state = {"requested": []}

    def fake_urlopen(url, timeout=None):
        state["requested"].append(url)
        if url == wio.API:
            return _Response(json.dumps(state["listing"]).encode())
        return _Response(b"headline,clicks\na,1\n")

    monkeypatch.setattr(wio.urllib.request, "urlopen", fake_urlopen)
    return state


def test_downloads_both_samples(tmp_path, osf):
    osf["listing"] = _listing(
        ["upworthy-exploratory.csv", "upworthy-confirmatory.csv"]
    )
    paths = wio.download(tmp_path)

    assert set(paths) == set(wio.TARGETS)
    for key, name in wio.TARGETS.items():
        assert paths[key].name == name
        assert paths[key].exists()


def test_does_not_redownload_what_is_already_there(tmp_path, osf):
    osf["listing"] = _listing(
        ["upworthy-exploratory.csv", "upworthy-confirmatory.csv"]
    )
    (tmp_path / "upworthy-exploratory.csv").write_bytes(b"already here")

    wio.download(tmp_path)

    # the listing is fetched, but only the missing file is pulled down
    downloads = [u for u in osf["requested"] if u != wio.API]
    assert len(downloads) == 1
    assert "confirmatory" in downloads[0]
    assert (tmp_path / "upworthy-exploratory.csv").read_bytes() == b"already here"


def test_raises_when_a_sample_is_missing_rather_than_returning_half(tmp_path, osf):
    """A partial archive must fail loudly.

    Returning one of the two would let the caller build a panel from an
    incomplete archive, and nothing downstream would reveal it.
    """
    osf["listing"] = _listing(["upworthy-exploratory.csv"])

    with pytest.raises(RuntimeError, match="confirmatory"):
        wio.download(tmp_path)


def test_creates_the_target_directory(tmp_path, osf):
    osf["listing"] = _listing(
        ["upworthy-exploratory.csv", "upworthy-confirmatory.csv"]
    )
    target = tmp_path / "does" / "not" / "exist"

    wio.download(target)

    assert target.is_dir()
