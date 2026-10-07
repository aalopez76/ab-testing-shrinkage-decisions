"""The contract between the result files and the figure generator.

When the analysis was translated, five JSON files were renamed and the figure
generator kept reading the old names. Every unit test stayed green: nothing in
`src/` reads those files. The failure only surfaced when the generator ran, at
the end of a long pipeline.

This closes that gap cheaply. It does not draw anything; it checks that every
result file and every literal subscript key `11_figures.py` reaches for is
present in the committed artefacts.

The key check was added after the file check alone proved insufficient: when the
ship analysis moved from accuracy to policy value, four keys the generator read
(`improvement`, `shrunk_wins_in`, `ships_raw`, `ships_shrunk`) ceased to exist
and every test still passed, because the file they lived in was still there.
"""

import json
import re
from pathlib import Path

import pytest

from _figure_keys import subscript_keys_by_file

ROOT = Path(__file__).resolve().parents[1]
RESULTS = ROOT / "reports" / "results"
GENERATOR = ROOT / "scripts" / "11_figures.py"
FIGURES = ROOT / "reports" / "figures"


def _files_read_by_the_generator() -> set[str]:
    source = GENERATOR.read_text(encoding="utf-8")
    return set(re.findall(r'(?:read|leer)\("([^"]+\.json)"\)', source))


def _figures_written_by_the_generator() -> set[str]:
    source = GENERATOR.read_text(encoding="utf-8")
    return set(re.findall(r'(?:guardar|save)\(fig,\s*"([^"]+\.png)"\)', source))


def test_every_result_file_the_generator_reads_exists():
    """The exact failure the translation introduced."""
    missing = sorted(
        name for name in _files_read_by_the_generator()
        if not (RESULTS / name).exists()
    )
    assert not missing, (
        f"11_figures.py reads result files that do not exist: {missing}. "
        f"Present: {sorted(p.name for p in RESULTS.glob('*.json'))}"
    )


def test_the_generator_reads_at_least_the_expected_files():
    """Guards the test itself: a generator that read nothing would pass above."""
    assert len(_files_read_by_the_generator()) >= 4


def test_every_committed_result_file_is_valid_json_with_content():
    for path in sorted(RESULTS.glob("*.json")):
        payload = json.loads(path.read_text(encoding="utf-8"))
        assert payload, f"{path.name} is empty"


@pytest.mark.parametrize("sample", ["exploratory", "confirmatory"])
def test_the_samples_the_report_cites_are_present(sample):
    """Both samples must be in the files the README quotes side by side."""
    payload = json.loads((RESULTS / "07_result.json").read_text(encoding="utf-8"))
    assert sample in payload


def test_every_figure_the_generator_writes_is_committed():
    missing = sorted(
        name for name in _figures_written_by_the_generator()
        if not (FIGURES / name).exists()
    )
    assert not missing, f"figures declared but not committed: {missing}"


def test_the_readme_references_only_figures_that_exist():
    readme = (ROOT / "README.md").read_text(encoding="utf-8")
    referenced = set(re.findall(r"reports/figures/([A-Za-z0-9_\-]+\.png)", readme))
    missing = sorted(name for name in referenced if not (FIGURES / name).exists())
    assert not missing, f"README points at figures that do not exist: {missing}"
    assert referenced, "the README references no figures at all"


def test_every_key_the_generator_subscripts_exists_in_the_file_it_reads():
    """A renamed key inside a file that still exists was invisible before.

    When the ship analysis moved from accuracy to policy value, four keys the
    generator read ceased to exist and every test still passed, because the
    file they lived in was still there. This is that gap.
    """
    source = GENERATOR.read_text(encoding="utf-8")
    problems = []
    for name, keys in subscript_keys_by_file(source).items():
        path = RESULTS / name
        if not path.exists():
            continue                      # covered by the file-level test
        text = path.read_text(encoding="utf-8")
        for key in sorted(keys):
            if f'"{key}"' not in text:
                problems.append(f"{name}: {key}")
    assert not problems, (
        f"11_figures.py subscripts keys absent from the committed results: {problems}"
    )


def test_the_key_check_actually_finds_keys():
    """Guards the test above: a broken extractor would pass it vacuously.

    It already earned its place: the first extractor resolved every file and
    zero keys, and this is what said so.
    """
    found = subscript_keys_by_file(GENERATOR.read_text(encoding="utf-8"))
    assert found, "no result file was matched to any subscript key"
    assert sum(len(keys) for keys in found.values()) >= 20
