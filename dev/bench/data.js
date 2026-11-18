window.BENCHMARK_DATA = {
  "lastUpdate": 1795002837435,
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
      }
    ]
  }
}