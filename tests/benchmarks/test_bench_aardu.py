"""Performance benchmarks for the aardu helpers."""

from typing import Any

import pytest

from aardwolf._libs.aardu import convert_level, parse_damage_line


@pytest.mark.benchmark
def test_bench_convert_level(benchmark: Any) -> None:
    """Benchmark convert_level() with a mid-range level."""
    benchmark(convert_level, 5000)


@pytest.mark.benchmark
def test_bench_parse_damage_line(benchmark: Any) -> None:
    """Benchmark parse_damage_line() with a typical damage line."""
    benchmark(parse_damage_line, "[3] Your fire <-*-> RAVAGES <-*-> a goblin! [123]")
