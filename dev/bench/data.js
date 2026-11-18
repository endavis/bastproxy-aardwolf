window.BENCHMARK_DATA = {
  "lastUpdate": 1795003738278,
  "repoUrl": "https://github.com/endavis/bastproxy-aardwolf",
  "entries": {
    "Benchmark": [
      {
        "commit": {
          "author": {
            "email": "6662995+endavis@users.noreply.github.com",
            "name": "Eric Davis",
            "username": "endavis"
          },
          "committer": {
            "email": "noreply@github.com",
            "name": "GitHub",
            "username": "web-flow"
          },
          "distinct": true,
          "id": "056893458c32848403b91b67c9ee97f5a65969ad",
          "message": "Initial commit",
          "timestamp": "2026-11-18T11:53:11Z",
          "tree_id": "a40ea1db7ce1f0f5856d67dd8a857a1d09bc1fbc",
          "url": "https://github.com/endavis/bastproxy-aardwolf/commit/056893458c32848403b91b67c9ee97f5a65969ad"
        },
        "date": 1795002837014,
        "tool": "pytest",
        "benches": [
          {
            "name": "tests/benchmarks/test_bench_core.py::test_bench_greet_default",
            "value": 9108338.99668735,
            "unit": "iter/sec",
            "range": "stddev: 1.5019524614571947e-8",
            "extra": "mean: 109.78950172624165 nsec\nrounds: 93844"
          },
          {
            "name": "tests/benchmarks/test_bench_core.py::test_bench_greet_with_name",
            "value": 9374739.51870515,
            "unit": "iter/sec",
            "range": "stddev: 1.2523114446468572e-8",
            "extra": "mean: 106.6696304473024 nsec\nrounds: 97848"
          },
          {
            "name": "tests/benchmarks/test_bench_core.py::test_bench_greet_long_name",
            "value": 6676205.9566930495,
            "unit": "iter/sec",
            "range": "stddev: 2.8768947662911143e-8",
            "extra": "mean: 149.78567265401347 nsec\nrounds: 70928"
          },
          {
            "name": "tests/benchmarks/test_bench_logging.py::test_bench_get_logger",
            "value": 2417132.2763537345,
            "unit": "iter/sec",
            "range": "stddev: 9.172848084209408e-8",
            "extra": "mean: 413.7133949113074 nsec\nrounds: 186429"
          },
          {
            "name": "tests/benchmarks/test_bench_logging.py::test_bench_setup_logging",
            "value": 535539.7857463727,
            "unit": "iter/sec",
            "range": "stddev: 3.976935846666201e-7",
            "extra": "mean: 1.8672749002323275 usec\nrounds: 59638"
          }
        ]
      },
      {
        "commit": {
          "author": {
            "email": "6662995+endavis@users.noreply.github.com",
            "name": "Eric Davis",
            "username": "endavis"
          },
          "committer": {
            "email": "noreply@github.com",
            "name": "GitHub",
            "username": "web-flow"
          },
          "distinct": true,
          "id": "ad14b19a657c29915f140dba3ae870c203c4e1af",
          "message": "chore: configure the repository from pyproject-template (merges PR #3, addresses #2)\n\nRun the template's configure step for bastproxy-aardwolf, the home of the\nAardwolf plugins for bastproxy.\n\n- Package src/package_name becomes src/aardwolf. bastproxy loads user\n  plugins from $BASTPROXY_HOME/plugins/<dir>/, so linking\n  plugins/aardwolf to src/aardwolf gives plugin IDs plugins.aardwolf.*.\n- Distribution name bastproxy-aardwolf, author Bast, GitHub\n  endavis/bastproxy-aardwolf; uv.lock regenerated for the new name.\n- SECURITY.md contact set to the project address. Repository URLs,\n  the docs site URL and clone paths point at endavis/bastproxy-aardwolf\n  (configure filled them from the package name).\n- sync-exclude.toml lists the template paths configuration removes but the\n  template's own docs still name, so the doc-scanning tests accept them.\n- Template sync point recorded: 1494b033 (the commit this repo was\n  created from; its initial commit is identical to that tree).\n\nAddresses #2\n\n\nClaude-Session: https://claude.ai/code/session_01NXu1sbBxFsEQW16MiZv7Je\n\nCo-authored-by: Claude Opus 5.5 <noreply@anthropic.com>",
          "timestamp": "2026-11-18T12:08:23Z",
          "tree_id": "180a4fd14bf768313dd29e2471c4f0d44cc44fc7",
          "url": "https://github.com/endavis/bastproxy-aardwolf/commit/ad14b19a657c29915f140dba3ae870c203c4e1af"
        },
        "date": 1795003737941,
        "tool": "pytest",
        "benches": [
          {
            "name": "tests/benchmarks/test_bench_core.py::test_bench_greet_default",
            "value": 13508628.623562759,
            "unit": "iter/sec",
            "range": "stddev: 7.981671434656308e-9",
            "extra": "mean: 74.02675933038276 nsec\nrounds: 140076"
          },
          {
            "name": "tests/benchmarks/test_bench_core.py::test_bench_greet_with_name",
            "value": 14005049.217488261,
            "unit": "iter/sec",
            "range": "stddev: 7.55371127918775e-9",
            "extra": "mean: 71.40281940254012 nsec\nrounds: 147776"
          },
          {
            "name": "tests/benchmarks/test_bench_core.py::test_bench_greet_long_name",
            "value": 10413489.378132455,
            "unit": "iter/sec",
            "range": "stddev: 1.1312290834418478e-8",
            "extra": "mean: 96.02929082541006 nsec\nrounds: 109987"
          },
          {
            "name": "tests/benchmarks/test_bench_logging.py::test_bench_get_logger",
            "value": 3784061.050465753,
            "unit": "iter/sec",
            "range": "stddev: 3.243569382687476e-8",
            "extra": "mean: 264.26634947576156 nsec\nrounds: 190151"
          },
          {
            "name": "tests/benchmarks/test_bench_logging.py::test_bench_setup_logging",
            "value": 818034.0676969555,
            "unit": "iter/sec",
            "range": "stddev: 1.2095763504884015e-7",
            "extra": "mean: 1.2224429757740294 usec\nrounds: 88629"
          }
        ]
      }
    ]
  }
}