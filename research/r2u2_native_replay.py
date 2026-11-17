"""Bounded, source-pinned CySat-I C2PO → R2U2 experiment.

The published CySat-I requirement 11 is the external source authority.  This
script tests arithmetic/dependency correspondence and collects native verdicts;
it does not assert that benchmark code is deployed spacecraft software.
"""

import argparse
import hashlib
import json
from pathlib import Path
import re
import subprocess


PINNED_R2U2 = "2875a1dfc0b8cb27c4c4f14bece6b95c3afff91a"
CELL_NAMES = tuple(f"Battery_Cell_Temp_{k}" for k in range(1, 5))


def _formula_match(source: str, cell_number: int) -> re.Match[str]:
    pattern = (
        rf"\bBattery_Cell_Temp_{cell_number}_RC_LT_1\s*:=\s*abs\(\s*"
        rf"(Battery_Cell_Temp_([1-4]))\s*-\s*prev\(\s*22\.0\s*,\s*"
        rf"Battery_Cell_Temp_([1-4])\s*\)\s*\)\s*<\s*1\.0\s*;"
    )
    matches = list(re.finditer(pattern, source))
    if len(matches) != 1:
        raise ValueError(f"Expected one exact RC formula for cell {cell_number}, got {len(matches)}")
    if int(matches[0].group(3)) != cell_number:
        raise ValueError(f"The previous-sample channel for cell {cell_number} changed")
    return matches[0]


def source_bindings(source: str) -> tuple[tuple[int, int], ...]:
    match = re.search(r"\bSPEC11\s*:\s*([^;]+);", source)
    expected = [f"Battery_Cell_Temp_{k}_RC_LT_1" for k in range(1, 5)]
    if match is None or [s.strip() for s in match.group(1).split("&&")] != expected:
        raise ValueError("SPEC11 no longer conjoins precisely the four cell checks")
    formulas = [_formula_match(source, k) for k in range(1, 5)]
    return tuple((int(m.group(2)), int(m.group(3))) for m in formulas)


def make_corrected(source: str) -> str:
    if source_bindings(source) != ((1, 1), (1, 2), (1, 3), (1, 4)):
        raise ValueError("Unrecognized source fingerprint; refuse an unreviewed edit")
    edits = [(_formula_match(source, k).span(1), CELL_NAMES[k - 1]) for k in (2, 3, 4)]
    for (start, end), replacement in reversed(edits):
        source = source[:start] + replacement + source[end:]
    if source_bindings(source) != ((1, 1), (2, 2), (3, 3), (4, 4)):
        raise AssertionError("Repair did not restore cell-local channel identities")
    return source


def expected_and_observed(
    source: str, previous: tuple[int, ...], current: tuple[int, ...]
) -> tuple[bool, bool]:
    if len(previous) != 4 or len(current) != 4:
        raise ValueError("Need four battery temperatures per time step")
    bindings = source_bindings(source)
    expected = all(abs(current[k] - previous[k]) < 1.0 for k in range(4))
    observed = all(abs(current[lhs - 1] - previous[prior - 1]) < 1.0 for lhs, prior in bindings)
    return expected, observed


def make_trace(
    header: str, first_data: str, previous: tuple[int, ...], current: tuple[int, ...]
) -> str:
    names = [s.strip() for s in header.removeprefix("#").strip().split(",")]
    first_values = [v.strip() for v in first_data.strip().split(",")]
    if len(names) != len(first_values) or len(set(names)) != len(names):
        raise ValueError("Unrecognized benchmark signal header")
    if not set(CELL_NAMES).issubset(names):
        raise ValueError("Four battery cell signals are required")

    def row(temperatures: tuple[int, ...]) -> str:
        values = first_values.copy()
        for name, value in zip(CELL_NAMES, temperatures):
            values[names.index(name)] = str(value)
        return ",".join(values)

    return "\n".join([header.strip(), row(previous), row(current), ""])


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _run(argv: list[str], destination: Path, cwd: Path) -> subprocess.CompletedProcess[str]:
    result = subprocess.run(argv, cwd=cwd, capture_output=True, text=True, timeout=240, check=False)
    destination.with_suffix(".stdout").write_text(result.stdout)
    destination.with_suffix(".stderr").write_text(result.stderr)
    if result.returncode != 0:
        raise RuntimeError(f"Exit {result.returncode}: {' '.join(argv)}\n{result.stderr[-4000:]}")
    return result


def compiler_command(repo: Path | str, spec: Path | str, trace: Path | str, output: Path | str) -> list[str]:
    # The CySat EPS benchmark declares float channels.  C2PO's booleanizer is
    # opt-in; without it the original upstream source fails type checking.
    return [
        "python3", str(Path(repo) / "compiler/c2po.py"), "--booleanizer",
        "--spec", str(spec), "--trace", str(trace), "--output", str(output),
    ]


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    repo = args.repo.resolve()
    output = args.out.resolve()
    output.mkdir(parents=True, exist_ok=True)

    head = subprocess.check_output(["git", "-C", str(repo), "rev-parse", "HEAD"], text=True).strip()
    if head != PINNED_R2U2:
        raise ValueError(f"Expected pinned R2U2 commit {PINNED_R2U2}, got {head}")

    benchmark = repo / "benchmarks/cysat/c2po/eps.c2po"
    csv = repo / "benchmarks/cysat/trace/eps.csv"
    source = benchmark.read_text()
    repaired = make_corrected(source)
    header, first_data = csv.read_text().splitlines()[:2]
    if source_bindings(source) != ((1, 1), (1, 2), (1, 3), (1, 4)):
        raise ValueError("Pinned official formula fingerprint not recognized")

    cases = {
        "neutral": ((22, 22, 22, 22), (22, 22, 22, 22)),
        "missed_cell_2_jump": ((22, 22, 22, 22), (22, 25, 22, 22)),
        "false_alarm": ((25, 22, 22, 22), (25, 22, 22, 22)),
    }

    manifest: dict[str, object] = {
        "upstream_repo": "R2U2/r2u2",
        "upstream_sha": head,
        "source_requirement": "Aurandt-Jones-Rozier CySat-I Supplement Eq. (11)",
        "source_url": "https://temporallogic.org/research/CySat-NFM22/Specifications_And_Signals.pdf",
        "benchmark_sha256": _sha256(benchmark),
        "original_dependency_fingerprint": source_bindings(source),
        "corrected_dependency_fingerprint": source_bindings(repaired),
        "native_verdict_interpretation": "Pending review of actual R2U2 output format",
        "cases": {},
    }
    for key, spec in {"official": source, "cell_local_control": repaired}.items():
        spec_path = output / f"{key}.c2po"
        spec_path.write_text(spec)
        binary = output / f"{key}.bin"
        _run(compiler_command(repo, spec_path, csv, binary), output / f"compile_{key}", cwd=repo)
        manifest[f"{key}_source_sha256"] = _sha256(spec_path)
        manifest[f"{key}_binary_sha256"] = _sha256(binary)

    for name, (previous, current) in cases.items():
        trace_path = output / f"{name}.csv"
        trace_path.write_text(make_trace(header, first_data, previous, current))
        expected, official_source = expected_and_observed(source, previous, current)
        _, controlled_source = expected_and_observed(repaired, previous, current)
        if expected != controlled_source:
            raise AssertionError(f"Repaired-source comparator mismatch for {name}")
        record: dict[str, object] = {
            "previous": previous, "current": current,
            "published_requirement_time1": expected,
            "official_source_time1": official_source,
            "cell_local_control_source_time1": controlled_source,
            "trace_sha256": _sha256(trace_path),
        }
        for variant in ("official", "cell_local_control"):
            native = _run([
                str(repo / "monitors/c/build/r2u2"),
                str(output / f"{variant}.bin"), str(trace_path),
            ], output / f"run_{name}_{variant}", cwd=repo)
            record[f"{variant}_native_stdout"] = native.stdout.strip()
        manifest["cases"][name] = record

    (output / "manifest.json").write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n")
    print(json.dumps(manifest, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
