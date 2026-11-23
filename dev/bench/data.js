window.BENCHMARK_DATA = {
  "lastUpdate": 1795465071580,
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
          "id": "f4b05922897a9ef48ef337ea3f7b1ec8be5dfbd2",
          "message": "feat: register the package as a bastproxy plugin source (merges PR #5, addresses #4)\n\nDepend on bastproxy through a direct git reference to its main branch,\nsince bastproxy is not on PyPI yet; a [tool.uv.sources] entry would\nleave the built wheel uninstallable, which wheel_check caught. uv.lock\npins the commit.\n\nRegister aardwolf = \"aardwolf\" in the bastproxy.plugins entry-point\ngroup, so bastproxy discovers the package and its plugins get\nplugins.aardwolf.* IDs. A test checks the entry point and bastproxy's\nsearch path for it, and the installation guide documents the\ndevelopment workflow.\n\nAddresses #4\n\n\nClaude-Session: https://claude.ai/code/session_01NXu1sbBxFsEQW16MiZv7Je\n\nCo-authored-by: Claude Opus 5.5 <noreply@anthropic.com>",
          "timestamp": "2026-11-19T13:57:00Z",
          "tree_id": "de070b46667d08e9691ff737025dc2ab34cccd6e",
          "url": "https://github.com/endavis/bastproxy-aardwolf/commit/f4b05922897a9ef48ef337ea3f7b1ec8be5dfbd2"
        },
        "date": 1795096663844,
        "tool": "pytest",
        "benches": [
          {
            "name": "tests/benchmarks/test_bench_core.py::test_bench_greet_default",
            "value": 16820846.91288535,
            "unit": "iter/sec",
            "range": "stddev: 5.577275944191737e-9",
            "extra": "mean: 59.45003870369722 nsec\nrounds: 169234"
          },
          {
            "name": "tests/benchmarks/test_bench_core.py::test_bench_greet_with_name",
            "value": 16973167.261015378,
            "unit": "iter/sec",
            "range": "stddev: 2.2320479894705266e-8",
            "extra": "mean: 58.91652304027183 nsec\nrounds: 176430"
          },
          {
            "name": "tests/benchmarks/test_bench_core.py::test_bench_greet_long_name",
            "value": 12838972.994965555,
            "unit": "iter/sec",
            "range": "stddev: 6.5053806763497035e-9",
            "extra": "mean: 77.88784978301007 nsec\nrounds: 130345"
          },
          {
            "name": "tests/benchmarks/test_bench_logging.py::test_bench_get_logger",
            "value": 4625596.631606525,
            "unit": "iter/sec",
            "range": "stddev: 1.413473853439342e-8",
            "extra": "mean: 216.18832761314252 nsec\nrounds: 48075"
          },
          {
            "name": "tests/benchmarks/test_bench_logging.py::test_bench_setup_logging",
            "value": 878978.244849869,
            "unit": "iter/sec",
            "range": "stddev: 1.3818588076195455e-7",
            "extra": "mean: 1.1376845853230435 usec\nrounds: 91601"
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
          "id": "c1b843e1fcd474677a71a9afcffd176c9159ccc0",
          "message": "chore: default BASTPROXY_HOME in .envrc and document it (merges PR #7, addresses #6)\n\nbastproxy will not import without BASTPROXY_HOME, so uv run bastproxy\nfrom this repo failed until each developer set it in .envrc.local.\n.envrc now defaults it to ~/bastproxy, as the bastproxy repo does,\nkeeping any value already set, and the installation guide documents\nthe requirement, the default and the override.\n\nAddresses #6\n\n\nClaude-Session: https://claude.ai/code/session_01NXu1sbBxFsEQW16MiZv7Je\n\nCo-authored-by: Claude Opus 5.5 <noreply@anthropic.com>",
          "timestamp": "2026-11-19T14:31:37Z",
          "tree_id": "f8c2b5d2dbc058b3cc5155e5d29af730b3ef6532",
          "url": "https://github.com/endavis/bastproxy-aardwolf/commit/c1b843e1fcd474677a71a9afcffd176c9159ccc0"
        },
        "date": 1795098737125,
        "tool": "pytest",
        "benches": [
          {
            "name": "tests/benchmarks/test_bench_core.py::test_bench_greet_default",
            "value": 8137686.608328219,
            "unit": "iter/sec",
            "range": "stddev: 1.1463503812190357e-8",
            "extra": "mean: 122.88504683586443 nsec\nrounds: 81348"
          },
          {
            "name": "tests/benchmarks/test_bench_core.py::test_bench_greet_with_name",
            "value": 8439912.841890687,
            "unit": "iter/sec",
            "range": "stddev: 1.1797107086280355e-8",
            "extra": "mean: 118.48463588825197 nsec\nrounds: 87789"
          },
          {
            "name": "tests/benchmarks/test_bench_core.py::test_bench_greet_long_name",
            "value": 5461545.7297058925,
            "unit": "iter/sec",
            "range": "stddev: 1.3079637772591247e-8",
            "extra": "mean: 183.09834788362204 nsec\nrounds: 56013"
          },
          {
            "name": "tests/benchmarks/test_bench_logging.py::test_bench_get_logger",
            "value": 2051815.117396837,
            "unit": "iter/sec",
            "range": "stddev: 8.391043852950857e-8",
            "extra": "mean: 487.3733464195898 nsec\nrounds: 194138"
          },
          {
            "name": "tests/benchmarks/test_bench_logging.py::test_bench_setup_logging",
            "value": 461855.63527452823,
            "unit": "iter/sec",
            "range": "stddev: 1.8217844536133113e-7",
            "extra": "mean: 2.1651787347048335 usec\nrounds: 48384"
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
          "id": "a6660b57c39365af3dc9cf5ee472337a017c81ca",
          "message": "feat: port the aardu helpers as a library module (merges PR #11, addresses #8)\n\nAdd aardwolf.libs.aardu with the class, reward and damage tables and\nactual_level, convert_level and parse_damage_line. It is a plain module,\nnot a plugin, so plugins import it directly.\n\nconvert_level fixes the old remort divisor (202 instead of 201), which\nmis-converted 45 totals in 1..4220. parse_damage_line no longer raises on\ndegenerate lines and always returns all five keys.\n\nAddresses #8\n\n\nClaude-Session: https://claude.ai/code/session_01NXu1sbBxFsEQW16MiZv7Je\n\nCo-authored-by: Claude Opus 5.5 <noreply@anthropic.com>",
          "timestamp": "2026-11-19T15:12:15Z",
          "tree_id": "749ccf32e6238ba192b5506b18117fbf4246a103",
          "url": "https://github.com/endavis/bastproxy-aardwolf/commit/a6660b57c39365af3dc9cf5ee472337a017c81ca"
        },
        "date": 1795101172362,
        "tool": "pytest",
        "benches": [
          {
            "name": "tests/benchmarks/test_bench_core.py::test_bench_greet_default",
            "value": 11073232.612228477,
            "unit": "iter/sec",
            "range": "stddev: 1.0598622749911974e-8",
            "extra": "mean: 90.30786537398954 nsec\nrounds: 102313"
          },
          {
            "name": "tests/benchmarks/test_bench_core.py::test_bench_greet_with_name",
            "value": 10753738.600117326,
            "unit": "iter/sec",
            "range": "stddev: 1.0174754581102304e-8",
            "extra": "mean: 92.99091573502538 nsec\nrounds: 107957"
          },
          {
            "name": "tests/benchmarks/test_bench_core.py::test_bench_greet_long_name",
            "value": 8205445.150985274,
            "unit": "iter/sec",
            "range": "stddev: 1.3307683453266018e-8",
            "extra": "mean: 121.87029242160304 nsec\nrounds: 85493"
          },
          {
            "name": "tests/benchmarks/test_bench_logging.py::test_bench_get_logger",
            "value": 2998631.7549640257,
            "unit": "iter/sec",
            "range": "stddev: 4.849850655458608e-8",
            "extra": "mean: 333.48542992802294 nsec\nrounds: 190549"
          },
          {
            "name": "tests/benchmarks/test_bench_logging.py::test_bench_setup_logging",
            "value": 596372.8834102348,
            "unit": "iter/sec",
            "range": "stddev: 1.2013925612745023e-7",
            "extra": "mean: 1.676803268253424 usec\nrounds: 61562"
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
          "id": "da1c45c4807e9cb931f80a81e0505fb32d58e8b5",
          "message": "feat: add the a102 plugin for telnet option 102 (merges PR #12, addresses #9)\n\nOwn option 102 through the generic telnet-option hook. Reference-counted\noption toggles (option.toggle) send on at 0->1 and off at 1->0, re-send\nthe counted state when the option is enabled or the MUD reconnects, and\naccept client toggles through the same counts. Two-byte MUD messages\nraise a per-message and a per-option event. payload.send wraps\ntelopt.send for raw payloads.\n\nAddresses #9\n\n\nClaude-Session: https://claude.ai/code/session_01NXu1sbBxFsEQW16MiZv7Je\n\nCo-authored-by: Claude Opus 5.5 <noreply@anthropic.com>",
          "timestamp": "2026-11-19T15:49:21Z",
          "tree_id": "2a0b2abe66bc9bce543768685b144b72389a1a74",
          "url": "https://github.com/endavis/bastproxy-aardwolf/commit/da1c45c4807e9cb931f80a81e0505fb32d58e8b5"
        },
        "date": 1795103406909,
        "tool": "pytest",
        "benches": [
          {
            "name": "tests/benchmarks/test_bench_core.py::test_bench_greet_default",
            "value": 7968809.708532444,
            "unit": "iter/sec",
            "range": "stddev: 2.6328231124715986e-8",
            "extra": "mean: 125.4892558080876 nsec\nrounds: 85529"
          },
          {
            "name": "tests/benchmarks/test_bench_core.py::test_bench_greet_with_name",
            "value": 8397866.898031898,
            "unit": "iter/sec",
            "range": "stddev: 1.4410658544629404e-8",
            "extra": "mean: 119.07785776342291 nsec\nrounds: 87474"
          },
          {
            "name": "tests/benchmarks/test_bench_core.py::test_bench_greet_long_name",
            "value": 5437409.025813367,
            "unit": "iter/sec",
            "range": "stddev: 1.3556459426762972e-8",
            "extra": "mean: 183.91112297284144 nsec\nrounds: 56297"
          },
          {
            "name": "tests/benchmarks/test_bench_logging.py::test_bench_get_logger",
            "value": 2112540.967553275,
            "unit": "iter/sec",
            "range": "stddev: 8.670938919491199e-8",
            "extra": "mean: 473.3636011604502 nsec\nrounds: 198847"
          },
          {
            "name": "tests/benchmarks/test_bench_logging.py::test_bench_setup_logging",
            "value": 463298.18309945345,
            "unit": "iter/sec",
            "range": "stddev: 1.7095034889868726e-7",
            "extra": "mean: 2.158437128568095 usec\nrounds: 47990"
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
          "id": "93df27f6869c9ffd9e4d8fef6e6ac060d8c286c2",
          "message": "feat: add the connect plugin that detects first active (merges PR #13, addresses #10)\n\nAdd plugins.aardwolf.connect: a Press Return trigger, GMCP module setup\n(Char, Room, Comm, Group, Core, rawcolor on, group on), one-time package\nrequests, and first-active detection that sets character.active and so\nraises ev_libs.api_character_active. Exposes character.is.first.active.\n\nAddresses #10\n\n\nClaude-Session: https://claude.ai/code/session_01NXu1sbBxFsEQW16MiZv7Je\n\nCo-authored-by: Claude Opus 5.5 <noreply@anthropic.com>",
          "timestamp": "2026-11-19T15:57:52Z",
          "tree_id": "ca8f6364c698fb5bf7f4834e5038222f4c62dad1",
          "url": "https://github.com/endavis/bastproxy-aardwolf/commit/93df27f6869c9ffd9e4d8fef6e6ac060d8c286c2"
        },
        "date": 1795103923322,
        "tool": "pytest",
        "benches": [
          {
            "name": "tests/benchmarks/test_bench_core.py::test_bench_greet_default",
            "value": 12583486.213436441,
            "unit": "iter/sec",
            "range": "stddev: 9.434507466774544e-9",
            "extra": "mean: 79.46923317102825 nsec\nrounds: 130668"
          },
          {
            "name": "tests/benchmarks/test_bench_core.py::test_bench_greet_with_name",
            "value": 13141459.529641055,
            "unit": "iter/sec",
            "range": "stddev: 8.674740940954845e-9",
            "extra": "mean: 76.09504847954388 nsec\nrounds: 137893"
          },
          {
            "name": "tests/benchmarks/test_bench_core.py::test_bench_greet_long_name",
            "value": 9758907.827208407,
            "unit": "iter/sec",
            "range": "stddev: 1.0625686042518107e-8",
            "extra": "mean: 102.47048314278993 nsec\nrounds: 101647"
          },
          {
            "name": "tests/benchmarks/test_bench_logging.py::test_bench_get_logger",
            "value": 3469942.2667702045,
            "unit": "iter/sec",
            "range": "stddev: 6.796437598590398e-8",
            "extra": "mean: 288.18923288046295 nsec\nrounds: 193912"
          },
          {
            "name": "tests/benchmarks/test_bench_logging.py::test_bench_setup_logging",
            "value": 772036.8458002092,
            "unit": "iter/sec",
            "range": "stddev: 1.332925969353295e-7",
            "extra": "mean: 1.2952749670431976 usec\nrounds: 83438"
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
          "id": "95f43acc179d877c52ec226ab91aadbf94c1bc15",
          "message": "fix: look up Aardwolf GMCP values with lower-case paths (merges PR #15, addresses #14)\n\nAardwolf sends lower-case GMCP package names (char.status, comm.quest)\nand gmcp.value.get is case-sensitive, so the capitalised paths the\nconnect plugin used (Char.Status.state, ...) always returned None and\nfirst active never fired. The paths are now lower-case, and the test\nstub resolves paths case-sensitively against Aardwolf-shaped data, so\na capitalised lookup misses as it does live.\n\nAddresses #14\n\n\nClaude-Session: https://claude.ai/code/session_01NXu1sbBxFsEQW16MiZv7Je\n\nCo-authored-by: Claude Opus 5.5 <noreply@anthropic.com>",
          "timestamp": "2026-11-19T16:55:51Z",
          "tree_id": "8b0cb15b4fca835fad7399c3bd27b1bda74bf40d",
          "url": "https://github.com/endavis/bastproxy-aardwolf/commit/95f43acc179d877c52ec226ab91aadbf94c1bc15"
        },
        "date": 1795107389469,
        "tool": "pytest",
        "benches": [
          {
            "name": "tests/benchmarks/test_bench_core.py::test_bench_greet_default",
            "value": 9454294.61299162,
            "unit": "iter/sec",
            "range": "stddev: 1.7759657257624483e-8",
            "extra": "mean: 105.77203704080152 nsec\nrounds: 98864"
          },
          {
            "name": "tests/benchmarks/test_bench_core.py::test_bench_greet_with_name",
            "value": 9743513.965363797,
            "unit": "iter/sec",
            "range": "stddev: 1.0837228837804859e-8",
            "extra": "mean: 102.63237714389243 nsec\nrounds: 101277"
          },
          {
            "name": "tests/benchmarks/test_bench_core.py::test_bench_greet_long_name",
            "value": 6680685.649961958,
            "unit": "iter/sec",
            "range": "stddev: 4.2105083406979196e-8",
            "extra": "mean: 149.685234779112 nsec\nrounds: 73665"
          },
          {
            "name": "tests/benchmarks/test_bench_logging.py::test_bench_get_logger",
            "value": 2578191.5082398355,
            "unit": "iter/sec",
            "range": "stddev: 1.0238156542601316e-7",
            "extra": "mean: 387.8687819752819 nsec\nrounds: 188751"
          },
          {
            "name": "tests/benchmarks/test_bench_logging.py::test_bench_setup_logging",
            "value": 560920.671820557,
            "unit": "iter/sec",
            "range": "stddev: 3.5193567943403796e-7",
            "extra": "mean: 1.78278328868562 usec\nrounds: 61222"
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
          "id": "866c2f68f80fc5cb2145f1218a42930d936f2735",
          "message": "feat: turn a102 option toggles off when the plugin unloads (merges PR #17, addresses #16)\n\nbastproxy now keeps a plugin-owned telnet option on with the MUD when\nits owner unregisters (endavis/bastproxy#586), so turning MUD-side\nfeatures off is the owning plugin's job.\n\na102 gets an uninitialize hook at priority 10, before the base hook that\nunregisters option 102. On a real unload, while option 102 is enabled,\nit sends \"off\" for every option with a count above 0. On a reload\n(is_reloading_f) it sends nothing: the counts are kept and the state is\nre-sent after the plugin loads again.\n\nAddresses #16\n\n\nClaude-Session: https://claude.ai/code/session_01NXu1sbBxFsEQW16MiZv7Je\n\nCo-authored-by: Claude Opus 5.5 <noreply@anthropic.com>",
          "timestamp": "2026-11-19T19:01:59Z",
          "tree_id": "c0970fc2c8b97750b3ebf4d1f8203f598f99adf0",
          "url": "https://github.com/endavis/bastproxy-aardwolf/commit/866c2f68f80fc5cb2145f1218a42930d936f2735"
        },
        "date": 1795114966876,
        "tool": "pytest",
        "benches": [
          {
            "name": "tests/benchmarks/test_bench_core.py::test_bench_greet_default",
            "value": 12659399.219157023,
            "unit": "iter/sec",
            "range": "stddev: 9.494751373471524e-9",
            "extra": "mean: 78.99269014968225 nsec\nrounds: 131528"
          },
          {
            "name": "tests/benchmarks/test_bench_core.py::test_bench_greet_with_name",
            "value": 12652687.213249132,
            "unit": "iter/sec",
            "range": "stddev: 9.426029624213433e-9",
            "extra": "mean: 79.03459424436416 nsec\nrounds: 135833"
          },
          {
            "name": "tests/benchmarks/test_bench_core.py::test_bench_greet_long_name",
            "value": 9444073.975859795,
            "unit": "iter/sec",
            "range": "stddev: 1.3007844713306183e-8",
            "extra": "mean: 105.88650645432492 nsec\nrounds: 99701"
          },
          {
            "name": "tests/benchmarks/test_bench_logging.py::test_bench_get_logger",
            "value": 3338079.7927677156,
            "unit": "iter/sec",
            "range": "stddev: 5.0737297874157104e-8",
            "extra": "mean: 299.5734260656682 nsec\nrounds: 194138"
          },
          {
            "name": "tests/benchmarks/test_bench_logging.py::test_bench_setup_logging",
            "value": 762012.9323636632,
            "unit": "iter/sec",
            "range": "stddev: 1.3369164684231353e-7",
            "extra": "mean: 1.3123136859346105 usec\nrounds: 83078"
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
          "id": "205a5821044bea6913b99fa8f7e2ea8b3c92fda3",
          "message": "chore: remove the template scaffold from src/aardwolf (merges PR #22, addresses #21)\n\n* chore: remove the template scaffold from src/aardwolf\n\nThe project template's example code (greet, the click CLI and the\ntemplate logging module) was never used by the Aardwolf plugins, which\nlog through bastproxy.libs.logger.\n\nRemoves src/aardwolf/core.py, cli.py and logging.py, the\nbastproxy-aardwolf console script, the click runtime dependency, the\nscaffold's tests and benchmarks, the examples/ tree, docs/usage/cli.md\nand docs/examples/add-a-feature.md. __init__.py keeps only __version__.\n\nA new benchmark of aardu.convert_level and parse_damage_line keeps the\nbenchmark job and test_benchmark_settings meaningful; that test now\ntargets it, with the maintainer's approval. The removed paths are in\nsync-exclude.toml so a template sync does not restore them, and the\ntemplate's own skill and ADR text that names them stays as is.\n\nAddresses #21\n\nCo-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>\nClaude-Session: https://claude.ai/code/session_01NXu1sbBxFsEQW16MiZv7Je\n\n* chore: finish removing the template scaffold from src/aardwolf\n\nThe first commit carried only the file deletions. This adds the rest of\nthe change: __init__.py without the scaffold imports, pyproject.toml and\nuv.lock without the console script and the click dependency, the mutmut\nselection, the aardu benchmark and the test_benchmark_settings target,\nthe sync-exclude entries, and the README, docs and nav updates.\n\nAddresses #21\n\nCo-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>\nClaude-Session: https://claude.ai/code/session_01NXu1sbBxFsEQW16MiZv7Je\n\n* chore: record the scaffold removal as a breaking change\n\nThe two previous commits remove the template scaffold's public API\n(aardwolf.greet, aardwolf.get_logger, aardwolf.setup_logging and the\naardwolf.core, aardwolf.logging and aardwolf.cli modules) and the\nbastproxy-aardwolf console script. This commit carries the footer.\n\nAddresses #21\n\nBREAKING CHANGE: aardwolf.greet, aardwolf.get_logger,\naardwolf.setup_logging, the aardwolf.core, aardwolf.logging and\naardwolf.cli modules, and the bastproxy-aardwolf console script are\nremoved. greet has no replacement; log through\nbastproxy.libs.logger.get_logger; the plugins load through bastproxy's\nbastproxy.plugins entry point.\n\nCo-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>\nClaude-Session: https://claude.ai/code/session_01NXu1sbBxFsEQW16MiZv7Je\n\n---------\n\nCo-authored-by: Claude Opus 5.5 <noreply@anthropic.com>",
          "timestamp": "2026-11-20T13:40:21Z",
          "tree_id": "bb78f34ea73e6392f94e1c46abc772e090eef507",
          "url": "https://github.com/endavis/bastproxy-aardwolf/commit/205a5821044bea6913b99fa8f7e2ea8b3c92fda3"
        },
        "date": 1795182071103,
        "tool": "pytest",
        "benches": [
          {
            "name": "tests/benchmarks/test_bench_aardu.py::test_bench_convert_level",
            "value": 5097645.873481111,
            "unit": "iter/sec",
            "range": "stddev: 1.5171183554866766e-8",
            "extra": "mean: 196.16898168666117 nsec\nrounds: 53186"
          },
          {
            "name": "tests/benchmarks/test_bench_aardu.py::test_bench_parse_damage_line",
            "value": 271176.0420769988,
            "unit": "iter/sec",
            "range": "stddev: 5.092415297324394e-7",
            "extra": "mean: 3.6876414020234725 usec\nrounds: 143679"
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
          "id": "ce177d6a24174bc57b42d024dea41e1133e118be",
          "message": "docs: consolidate the plugin docs under one Plugins section (merges PR #23, addresses #18)\n\nThe plugin docs were split: docs/usage/plugins.md held the entry-point\noverview and the whole connect plugin, while a102 had its own page under\nPlugins.\n\nAdds docs/plugins/index.md (overview, loading, a table of plugins) and\ndocs/plugins/connect.md (moved from usage/plugins.md, laid out like\na102.md), and removes docs/usage/plugins.md. A new Adding a Plugin page\nstates the one-page-plus-index-row rule for new and migrated plugins.\n\nThe template's docs/usage/basics.md is rewritten, as the maintainer\nchose, into this project's usage page: running bastproxy with the\nplugins, loading them, and working against a local bastproxy checkout.\nREADME and docs/index.md links point at the new pages.\n\nAddresses #18\n\n\nClaude-Session: https://claude.ai/code/session_01NXu1sbBxFsEQW16MiZv7Je\n\nCo-authored-by: Claude Opus 5.5 <noreply@anthropic.com>",
          "timestamp": "2026-11-20T14:19:31Z",
          "tree_id": "756a03786fd55973e72d1b7b0433316d5aa859c4",
          "url": "https://github.com/endavis/bastproxy-aardwolf/commit/ce177d6a24174bc57b42d024dea41e1133e118be"
        },
        "date": 1795184399829,
        "tool": "pytest",
        "benches": [
          {
            "name": "tests/benchmarks/test_bench_aardu.py::test_bench_convert_level",
            "value": 4287467.95593538,
            "unit": "iter/sec",
            "range": "stddev: 1.730640833004296e-8",
            "extra": "mean: 233.23789478487978 nsec\nrounds: 43872"
          },
          {
            "name": "tests/benchmarks/test_bench_aardu.py::test_bench_parse_damage_line",
            "value": 221839.97146045614,
            "unit": "iter/sec",
            "range": "stddev: 4.988382196791122e-7",
            "extra": "mean: 4.507753915656512 usec\nrounds: 115434"
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
          "id": "6dd88f5565011d403a60225fa5aba19b71bc6e33",
          "message": "feat: add a GMCP-backed total level helper to aardu (merges PR #25, addresses #24)\n\nThe old aardu.getactuallevel filled missing arguments from GMCP; the\nmigrated actual_level is pure, so each caller would have to read and\nconvert char.status.level and char.base.remorts/tier/redos itself.\n\nactual_level_from_gmcp(gmcp_get, level=None) reads those values through\na passed-in gmcp.value.get callable, converts each to int (0 when missing\nor not numeric, as the old code defaulted), and returns actual_level.\naardu still imports nothing from bastproxy.\n\nAddresses #24\n\n\nClaude-Session: https://claude.ai/code/session_01NXu1sbBxFsEQW16MiZv7Je\n\nCo-authored-by: Claude Opus 5.5 <noreply@anthropic.com>",
          "timestamp": "2026-11-20T15:28:38Z",
          "tree_id": "591ca37f19d4a25ae165ccf1743e34b68bf426b1",
          "url": "https://github.com/endavis/bastproxy-aardwolf/commit/6dd88f5565011d403a60225fa5aba19b71bc6e33"
        },
        "date": 1795188561924,
        "tool": "pytest",
        "benches": [
          {
            "name": "tests/benchmarks/test_bench_aardu.py::test_bench_convert_level",
            "value": 5010935.544465211,
            "unit": "iter/sec",
            "range": "stddev: 1.5182192839150864e-8",
            "extra": "mean: 199.56353282263666 nsec\nrounds: 52417"
          },
          {
            "name": "tests/benchmarks/test_bench_aardu.py::test_bench_parse_damage_line",
            "value": 270276.31065427297,
            "unit": "iter/sec",
            "range": "stddev: 5.141434789280039e-7",
            "extra": "mean: 3.699917308991099 usec\nrounds: 143885"
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
          "id": "6c57a662b6008fdf934ab675bb6f7a5dbd022b64",
          "message": "feat: migrate the statdb plugin from the old bastproxy (merges PR #31, addresses #26)\n\n* feat: migrate the statdb plugin from the old bastproxy\n\nAdd plugins.aardwolf.statdb, which records character stats, quests,\ncampaigns, global quests, levels and mob kills in SQLite and reports on\nthem with the old list, comp, quests, levels, cps, gqs and mobs\ncommands.\n\nThe schema is the old version 17 text, so a database from the old proxy\nopens without conversion once copied into the plugin's data directory;\ntables the plugin does not own are left alone. Migrations 13 to 17\nrebuild the changed tables, and older versions are refused. Storage goes\nthrough the core sqldb database.add API, so the bastproxy lock moves to\na core that has it.\n\nThe plugin imports no other plugin. It subscribes to the events the\nwhois, level, mobk, cp, gq and quest plugins will raise (#19, #20,\n#27-#30), records deaths from a trigger, and on GMCP char.status sends\none whois when there are no stats yet. Backups run at backupstart (UTC)\nand then every backupinterval.\n\nOld bugs fixed in the port: whois class names never matched the classes\ntable, the remort handler wrote a column that does not exist, finish\ntime checks compared an int with a string, the reports crashed on an\nunknown id or a row with no mobs, and SQL values were pasted into the\nstatement text instead of passed as parameters.\n\nAddresses #26\n\nCo-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>\nClaude-Session: https://claude.ai/code/session_01NXu1sbBxFsEQW16MiZv7Je\n\n* fix: drop a nosec bandit never reads from the statdb test helper\n\nBandit skips tests/, so the comment suppressed nothing and failed the\nguard that keeps nosec comments where bandit reads them.\n\nAddresses #26\n\nCo-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>\nClaude-Session: https://claude.ai/code/session_01NXu1sbBxFsEQW16MiZv7Je\n\n---------\n\nCo-authored-by: Claude Opus 5.5 <noreply@anthropic.com>",
          "timestamp": "2026-11-22T18:47:17Z",
          "tree_id": "96689b9877435fe9d687d6559602c3fd2ca6816c",
          "url": "https://github.com/endavis/bastproxy-aardwolf/commit/6c57a662b6008fdf934ab675bb6f7a5dbd022b64"
        },
        "date": 1795373277924,
        "tool": "pytest",
        "benches": [
          {
            "name": "tests/benchmarks/test_bench_aardu.py::test_bench_convert_level",
            "value": 5795895.286379337,
            "unit": "iter/sec",
            "range": "stddev: 1.1728212566738642e-8",
            "extra": "mean: 172.53589835379762 nsec\nrounds: 59225"
          },
          {
            "name": "tests/benchmarks/test_bench_aardu.py::test_bench_parse_damage_line",
            "value": 290472.36389960407,
            "unit": "iter/sec",
            "range": "stddev: 3.27765903485387e-7",
            "extra": "mean: 3.442668302674157 usec\nrounds: 156275"
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
          "id": "05e59c437faa8d9127141f7bc0784c0217390b29",
          "message": "feat: migrate the whois plugin from the old bastproxy (merges PR #32, addresses #28)\n\nAdd plugins.aardwolf.whois, which parses the output of the whois command\ninto a saved state and raises ev_plugins.aardwolf.whois_received with a\ncopy of it: the stat lines, powerups, GMCP name, level, tier, redos,\nrace, subclass and remorts, the sex from the header, the classes and the\ntotal level.\n\nA whois typed by a client starts the parse through a watch. A whois a\nplugin needs goes through the core command queue: the plugin registers a\nwhois command type whose before-send callback starts the parse, and the\nend line finishes the command so the queue moves on.\n\nstatdb now queues its automatic first whois that way when the whois\nplugin is loaded, and sends none otherwise, instead of sending it\nstraight to the MUD where the watch never sees it.\n\nFixed from the old plugin: missing GMCP values no longer raise, unknown\nclass names pass through, and subscribers get a plain copy rather than\nthe live saved state.\n\nAddresses #28\n\n\nClaude-Session: https://claude.ai/code/session_01NXu1sbBxFsEQW16MiZv7Je\n\nCo-authored-by: Claude Opus 5.5 <noreply@anthropic.com>",
          "timestamp": "2026-11-22T20:25:50Z",
          "tree_id": "ab8278adcdd9c5d9045c7e2eeabb168aa7458007",
          "url": "https://github.com/endavis/bastproxy-aardwolf/commit/05e59c437faa8d9127141f7bc0784c0217390b29"
        },
        "date": 1795379189690,
        "tool": "pytest",
        "benches": [
          {
            "name": "tests/benchmarks/test_bench_aardu.py::test_bench_convert_level",
            "value": 2987588.431845061,
            "unit": "iter/sec",
            "range": "stddev: 5.0893911547651694e-8",
            "extra": "mean: 334.7181256095655 nsec\nrounds: 193088"
          },
          {
            "name": "tests/benchmarks/test_bench_aardu.py::test_bench_parse_damage_line",
            "value": 170545.98627832843,
            "unit": "iter/sec",
            "range": "stddev: 9.011242440847272e-7",
            "extra": "mean: 5.8635211641276355 usec\nrounds: 177305"
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
          "id": "201cc6856c05bd152d558f97593ac6db5d68086d",
          "message": "feat: migrate the quest plugin from the old bastproxy (merges PR #33, addresses #19)\n\nAdd plugins.aardwolf.quest, which turns Aardwolf's GMCP comm.quest\nmessages into ev_plugins.aardwolf.quest_* events (ready, start, killed,\ncomp, failed for fail and timeout, status, reset) and keeps the current\nquest in a saved state that survives a reload or restart.\n\nstart resets the state with the target, area, room, timer and the\ncharacter's actual level from GMCP; comp merges the GMCP reward fields\nin. Every event carries a plain copy, so subscribers cannot change the\nsaved state. A message that is not a dict, or has no or an unknown\naction, raises nothing. The quest_comp and quest_failed payloads carry\nthe keys statdb saves.\n\nAddresses #19\n\n\nClaude-Session: https://claude.ai/code/session_01NXu1sbBxFsEQW16MiZv7Je\n\nCo-authored-by: Claude Opus 5.5 <noreply@anthropic.com>",
          "timestamp": "2026-11-22T21:40:41Z",
          "tree_id": "d3abd6e369b08709d2d087abe748718d2336635e",
          "url": "https://github.com/endavis/bastproxy-aardwolf/commit/201cc6856c05bd152d558f97593ac6db5d68086d"
        },
        "date": 1795383670939,
        "tool": "pytest",
        "benches": [
          {
            "name": "tests/benchmarks/test_bench_aardu.py::test_bench_convert_level",
            "value": 3116686.6710297093,
            "unit": "iter/sec",
            "range": "stddev: 4.2580171216001534e-8",
            "extra": "mean: 320.8535555707992 nsec\nrounds: 199641"
          },
          {
            "name": "tests/benchmarks/test_bench_aardu.py::test_bench_parse_damage_line",
            "value": 165970.91417267086,
            "unit": "iter/sec",
            "range": "stddev: 8.456250559319426e-7",
            "extra": "mean: 6.025152087549699 usec\nrounds: 172118"
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
          "id": "82efdd9a704700fc722a948cb56c8e4d087c7b4b",
          "message": "feat: migrate the level plugin from the old bastproxy (merges PR #34, addresses #20)\n\nAdd plugins.aardwolf.level, which follows level, powerup, superhero,\nremort and tier output and raises ev_plugins.aardwolf.level_gain with\nthe record of each (type, level, total level, gains, bonus and blessing\ntrains, bonus stats, start and finish times), plus level_hero,\nlevel_superhero, level_remort, level_tier and level_preremort. The\nrecord is saved and survives a reload or restart, and level_gain carries\nthe keys statdb saves.\n\nA record is collected until an empty line and finishes when trains were\ngained or a remort or tier completed. A tier is followed through GMCP\nchar.status state 2 then 3 and char.base, and a restart in the middle of\na tier picks it up again. GMCP state and level are read as numbers even\nwhen they arrive as strings.\n\nOld bugs fixed: the superhero loud trains group was empty, the gains\nline converted a group that does not exist, the finish guard made the\ntier branch unreachable, the char.base callback unregistered the wrong\nfunction, and the state 2 message called a misspelled API. A failed\nsuperhero no longer loses the previous finish time, and a disconnect\nturns the level triggers off.\n\ncodespell now ignores \"remorted\", which is Aardwolf's own text.\n\nAddresses #20\n\n\nClaude-Session: https://claude.ai/code/session_01NXu1sbBxFsEQW16MiZv7Je\n\nCo-authored-by: Claude Opus 5.5 <noreply@anthropic.com>",
          "timestamp": "2026-11-22T23:11:47Z",
          "tree_id": "8a9160a6288b96bb752f56f28d70d2191ae68736",
          "url": "https://github.com/endavis/bastproxy-aardwolf/commit/82efdd9a704700fc722a948cb56c8e4d087c7b4b"
        },
        "date": 1795389145411,
        "tool": "pytest",
        "benches": [
          {
            "name": "tests/benchmarks/test_bench_aardu.py::test_bench_convert_level",
            "value": 2968549.8037545444,
            "unit": "iter/sec",
            "range": "stddev: 4.5752086277103724e-8",
            "extra": "mean: 336.86482158231814 nsec\nrounds: 198453"
          },
          {
            "name": "tests/benchmarks/test_bench_aardu.py::test_bench_parse_damage_line",
            "value": 170620.66487386872,
            "unit": "iter/sec",
            "range": "stddev: 8.987346499219525e-7",
            "extra": "mean: 5.8609547720333275 usec\nrounds: 178540"
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
          "id": "b2194c9b2afec7fecde40a9e8337bf57168cbf72",
          "message": "feat: add the mobk plugin, which raises an event for each kill (merges PR #35, addresses #27)\n\nPort the mobk plugin from the old bastproxy as plugins.aardwolf.mobk.\nIt follows the combat output and GMCP char.status to build a kill\nrecord and raises ev_plugins.aardwolf.mobk_kill once per kill, when the\ncorpse is sacrificed or consumed, or on a slit, disintegrate or banish.\nstatdb already saves that event to the mobkills table.\n\nFixes from the old plugin: summed experience (123+45) is stored and the\nkill raised; the unused immunity handler and the unused instatext and\ninstaback settings are dropped; the blessing bonus no longer stops other\ntriggers on its line; debug echoes go to the log.\n\nAddresses #27\n\n\nClaude-Session: https://claude.ai/code/session_01NXu1sbBxFsEQW16MiZv7Je\n\nCo-authored-by: Claude Opus 5.5 <noreply@anthropic.com>",
          "timestamp": "2026-11-22T23:26:15Z",
          "tree_id": "d3dd57945dca4f83943e4277e3114151856385a7",
          "url": "https://github.com/endavis/bastproxy-aardwolf/commit/b2194c9b2afec7fecde40a9e8337bf57168cbf72"
        },
        "date": 1795390009521,
        "tool": "pytest",
        "benches": [
          {
            "name": "tests/benchmarks/test_bench_aardu.py::test_bench_convert_level",
            "value": 4989814.927092794,
            "unit": "iter/sec",
            "range": "stddev: 1.857422703956487e-7",
            "extra": "mean: 200.40823449590908 nsec\nrounds: 56001"
          },
          {
            "name": "tests/benchmarks/test_bench_aardu.py::test_bench_parse_damage_line",
            "value": 274526.6238133387,
            "unit": "iter/sec",
            "range": "stddev: 4.18832878144176e-7",
            "extra": "mean: 3.642633949703686 usec\nrounds: 146178"
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
          "id": "bdf73ef6ea9280e0ebe8561ca91b65fabf16b88e",
          "message": "feat: add the cp plugin, which follows Aardwolf campaigns (merges PR #36, addresses #29)\n\nPort the cp plugin from the old bastproxy as plugins.aardwolf.cp. It\nqueues a campaign check through the core mudcmds plugin, reads the\ntarget mobs, rewards and completion, keeps its state in a\nPersistentDict, and raises cp_mobsorig, cp_mobsleft, cp_comp and\ncp_failed. A target kill is matched against the mobk plugin's\nmobk_kill event. statdb already saves cp_comp and cp_failed.\n\nFixes from the old plugin: a kill of the first mob in the list removes\nit; the level comes from actual_level_from_gmcp; cp_comp is raised at\nthe next prompt when neither line follows the completion summary.\nDebug echoes go to the log. cpcheck is added to the codespell ignore\nlist.\n\nAddresses #29\n\n\nClaude-Session: https://claude.ai/code/session_01NXu1sbBxFsEQW16MiZv7Je\n\nCo-authored-by: Claude Opus 5.5 <noreply@anthropic.com>",
          "timestamp": "2026-11-22T23:43:43Z",
          "tree_id": "b90deb4463ee4f3486464e4edaf02a6901208e8a",
          "url": "https://github.com/endavis/bastproxy-aardwolf/commit/bdf73ef6ea9280e0ebe8561ca91b65fabf16b88e"
        },
        "date": 1795391066664,
        "tool": "pytest",
        "benches": [
          {
            "name": "tests/benchmarks/test_bench_aardu.py::test_bench_convert_level",
            "value": 3084839.6547023607,
            "unit": "iter/sec",
            "range": "stddev: 5.205537142612677e-8",
            "extra": "mean: 324.16595737015206 nsec\nrounds: 195734"
          },
          {
            "name": "tests/benchmarks/test_bench_aardu.py::test_bench_parse_damage_line",
            "value": 174332.42184602685,
            "unit": "iter/sec",
            "range": "stddev: 8.339591110281754e-7",
            "extra": "mean: 5.736167658378634 usec\nrounds: 180832"
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
          "id": "bacef92912a563c3e754961bda132d65d02294c8",
          "message": "feat: add the gq plugin, which follows Aardwolf global quests (merges PR #37, addresses #30)\n\n* feat: add the gq plugin, which follows Aardwolf global quests\n\nPort the gq plugin from the old bastproxy as plugins.aardwolf.gq. It\nfollows declared, joined, started, cancelled, won and finished global\nquests from the MUD output, keeps its state and the mobs left in\nPersistentDicts and the joined and maxkills settings, and raises the gq\nevents. The plugin's own gq check goes through a core mudcmds command\ntype; a check typed by the client is seen by a watch. A target kill is\nmatched against the mobk plugin's mobk_kill event. statdb already saves\ngq_won, gq_completed and gq_done.\n\nFixes from the old plugin: the kill listener handles one kill per\nmob-dead line; a kill of the first mob in the list counts it down;\njoined resets to -1; the mobs left are always a list; the level comes\nfrom actual_level_from_gmcp. Debug echoes go to the log.\n\nAddresses #30\n\nCo-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>\nClaude-Session: https://claude.ai/code/session_01NXu1sbBxFsEQW16MiZv7Je\n\n* fix: match only the joined gquest's win announcement\n\nThe gq_wonannounce trigger now starts at the beginning of the line,\ntakes a number for the gquest and a single word for the winner, and\nescapes the final period. The plugin raises gq_won only when the\nannounced gquest is the one joined.\n\nAddresses #30\n\nCo-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>\nClaude-Session: https://claude.ai/code/session_01NXu1sbBxFsEQW16MiZv7Je\n\n---------\n\nCo-authored-by: Claude Opus 5.5 <noreply@anthropic.com>",
          "timestamp": "2026-11-23T00:05:10Z",
          "tree_id": "d798061751049e9acd74deb16cd507ded7047fac",
          "url": "https://github.com/endavis/bastproxy-aardwolf/commit/bacef92912a563c3e754961bda132d65d02294c8"
        },
        "date": 1795392352396,
        "tool": "pytest",
        "benches": [
          {
            "name": "tests/benchmarks/test_bench_aardu.py::test_bench_convert_level",
            "value": 5150293.59178303,
            "unit": "iter/sec",
            "range": "stddev: 1.3983207224049932e-8",
            "extra": "mean: 194.16368837602525 nsec\nrounds: 53571"
          },
          {
            "name": "tests/benchmarks/test_bench_aardu.py::test_bench_parse_damage_line",
            "value": 270957.1151696478,
            "unit": "iter/sec",
            "range": "stddev: 5.413169830475275e-7",
            "extra": "mean: 3.6906209286067067 usec\nrounds: 144238"
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
          "id": "fa52729263b2895296772732dbeabe4d07b624e7",
          "message": "fix: send a whois every time the character is first active (merges PR #42, addresses #41)\n\nThe whois plugin now queues a whois on ev_libs.api_character_active,\nand after load when the character is already active. Before, only\nstatdb queued one, and only when its database had no kills yet, so a\nhome that already held a whois sent none on later logins, including a\nnew character's.\n\nstatdb no longer queues the whois or listens to char.status and the\ndisconnect for it, and drops its plugins.core.mudcmds dependency. It\nstill saves whois_received. The statdb tests of the removed queue are\nremoved with it.\n\nAddresses #41\n\n\nClaude-Session: https://claude.ai/code/session_01NXu1sbBxFsEQW16MiZv7Je\n\nCo-authored-by: Claude Opus 5.5 <noreply@anthropic.com>",
          "timestamp": "2026-11-23T10:50:12Z",
          "tree_id": "7368f737fe53e9fc853480324693cd96f9583597",
          "url": "https://github.com/endavis/bastproxy-aardwolf/commit/fa52729263b2895296772732dbeabe4d07b624e7"
        },
        "date": 1795431046124,
        "tool": "pytest",
        "benches": [
          {
            "name": "tests/benchmarks/test_bench_aardu.py::test_bench_convert_level",
            "value": 5165690.095711805,
            "unit": "iter/sec",
            "range": "stddev: 1.4085509716413194e-8",
            "extra": "mean: 193.58497731602796 nsec\nrounds: 53565"
          },
          {
            "name": "tests/benchmarks/test_bench_aardu.py::test_bench_parse_damage_line",
            "value": 273498.963242719,
            "unit": "iter/sec",
            "range": "stddev: 4.573993457419754e-7",
            "extra": "mean: 3.6563209898259883 usec\nrounds: 144718"
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
          "id": "d00e985ec70422e368ab904aca33ae7a41512ec0",
          "message": "chore: upgrade the locked bastproxy and document running against a local core (merges PR #47, addresses #46)\n\nMove the uv.lock pin of bastproxy from d6b01433 to 26be624f, which\nlets #bp.core.pluginm.load take several plugins or a whole package\n(bastproxy #724).\n\nThe docs now show loading the whole package with\n#bp.core.pluginm.load aardwolf, and describe running the proxy against\na local bastproxy checkout with uv run --with-editable ../bastproxy,\nwhich needs no lock bump. CI still uses the pinned commit, so a plugin\nchange that needs a newer core API moves the pin in its own PR.\n\nAddresses #46\n\n\nClaude-Session: https://claude.ai/code/session_01NXu1sbBxFsEQW16MiZv7Je\n\nCo-authored-by: Claude Opus 5.5 <noreply@anthropic.com>",
          "timestamp": "2026-11-23T11:03:50Z",
          "tree_id": "2d28166ef93178cc26edaf55ed704858cbbae5ea",
          "url": "https://github.com/endavis/bastproxy-aardwolf/commit/d00e985ec70422e368ab904aca33ae7a41512ec0"
        },
        "date": 1795431864664,
        "tool": "pytest",
        "benches": [
          {
            "name": "tests/benchmarks/test_bench_aardu.py::test_bench_convert_level",
            "value": 3054146.0841135536,
            "unit": "iter/sec",
            "range": "stddev: 4.225695309722392e-8",
            "extra": "mean: 327.4237618172883 nsec\nrounds: 189754"
          },
          {
            "name": "tests/benchmarks/test_bench_aardu.py::test_bench_parse_damage_line",
            "value": 170486.13280617612,
            "unit": "iter/sec",
            "range": "stddev: 9.637151637496795e-7",
            "extra": "mean: 5.865579701645819 usec\nrounds: 177305"
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
          "id": "4cf0abd4c5010279c44ecfbda4d60f5266837597",
          "message": "fix: describe every key the aardwolf events send (merges PR #48, addresses #43)\n\n* fix: describe every key the aardwolf events send\n\nwhois_received now carries the whois stat values under one described\nkey, stats, and statdb save_whois reads them from there. quest_status\ndescribes action and status, and quest_comp describes its keys. Tests\ncheck that each plugin's raised keys are a subset of its declared\narg_descriptions.\n\nAddresses #43\n\nCo-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>\nClaude-Session: https://claude.ai/code/session_01NXu1sbBxFsEQW16MiZv7Je\n\n* fix: keep the save_whois parameter name\n\nStatStore.save_whois keeps its info parameter, so its signature does\nnot change; it flattens the nested stats into a local dict instead.\n\nAddresses #43\n\nCo-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>\nClaude-Session: https://claude.ai/code/session_01NXu1sbBxFsEQW16MiZv7Je\n\n---------\n\nCo-authored-by: Claude Opus 5.5 <noreply@anthropic.com>",
          "timestamp": "2026-11-23T11:39:26Z",
          "tree_id": "1153588899508454a7ac3afc5ad8a86214fea6a8",
          "url": "https://github.com/endavis/bastproxy-aardwolf/commit/4cf0abd4c5010279c44ecfbda4d60f5266837597"
        },
        "date": 1795434017243,
        "tool": "pytest",
        "benches": [
          {
            "name": "tests/benchmarks/test_bench_aardu.py::test_bench_convert_level",
            "value": 5135395.96848187,
            "unit": "iter/sec",
            "range": "stddev: 1.4014785480453849e-8",
            "extra": "mean: 194.72695117132724 nsec\nrounds: 53391"
          },
          {
            "name": "tests/benchmarks/test_bench_aardu.py::test_bench_parse_damage_line",
            "value": 273908.38983678905,
            "unit": "iter/sec",
            "range": "stddev: 4.678803125840188e-7",
            "extra": "mean: 3.6508556769504565 usec\nrounds: 144426"
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
          "id": "4a4d09b1e5d7b649b8e372beaab6469c7d37098a",
          "message": "feat: warn when a whois names a different character than the stats hold (merges PR #49, addresses #44)\n\nstatdb keeps one database per home with no character column. A whois\nfor a character whose name differs from the name already stored now logs\na warning and tells the client that a home holds one character. The\nwhois is still saved. The docs state the one-character-per-home rule.\n\nAddresses #44\n\n\nClaude-Session: https://claude.ai/code/session_01NXu1sbBxFsEQW16MiZv7Je\n\nCo-authored-by: Claude Opus 5.5 <noreply@anthropic.com>",
          "timestamp": "2026-11-23T11:48:48Z",
          "tree_id": "a5babb231839651702dcac7a93091f9d665fb917",
          "url": "https://github.com/endavis/bastproxy-aardwolf/commit/4a4d09b1e5d7b649b8e372beaab6469c7d37098a"
        },
        "date": 1795434565320,
        "tool": "pytest",
        "benches": [
          {
            "name": "tests/benchmarks/test_bench_aardu.py::test_bench_convert_level",
            "value": 4116225.340890472,
            "unit": "iter/sec",
            "range": "stddev: 1.6730756409428087e-8",
            "extra": "mean: 242.94102416260523 nsec\nrounds: 42132"
          },
          {
            "name": "tests/benchmarks/test_bench_aardu.py::test_bench_parse_damage_line",
            "value": 223675.98585209178,
            "unit": "iter/sec",
            "range": "stddev: 4.400955921557234e-7",
            "extra": "mean: 4.4707526209865955 usec\nrounds: 115701"
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
          "id": "e47c78114e9cfec3f7d7089207f43573b9f36875",
          "message": "fix: describe the completed and wait keys of quest_comp (merges PR #53, addresses #50)\n\nAardwolf's GMCP comm.quest completion message carries completed (the\nquests the character has completed) and wait (minutes until the next\nquest) as well as the reward keys. The plugin merges every key of the\nmessage into quest_comp, so the core warned about the two undescribed\nkeys on every completed quest. Both are now in arg_descriptions and\nthe quest docs.\n\nAddresses #50\n\n\nClaude-Session: https://claude.ai/code/session_01NXu1sbBxFsEQW16MiZv7Je\n\nCo-authored-by: Claude Opus 5.5 <noreply@anthropic.com>",
          "timestamp": "2026-11-23T13:08:50Z",
          "tree_id": "bbae9e33f1abf4fdbfeac7aa2b3d2302b1a99b78",
          "url": "https://github.com/endavis/bastproxy-aardwolf/commit/e47c78114e9cfec3f7d7089207f43573b9f36875"
        },
        "date": 1795439362185,
        "tool": "pytest",
        "benches": [
          {
            "name": "tests/benchmarks/test_bench_aardu.py::test_bench_convert_level",
            "value": 6011322.841245241,
            "unit": "iter/sec",
            "range": "stddev: 1.1727916323254298e-8",
            "extra": "mean: 166.35273573043546 nsec\nrounds: 62020"
          },
          {
            "name": "tests/benchmarks/test_bench_aardu.py::test_bench_parse_damage_line",
            "value": 299052.070941585,
            "unit": "iter/sec",
            "range": "stddev: 0.0000010084995094129154",
            "extra": "mean: 3.343899264270047 usec\nrounds: 155764"
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
          "id": "f5226862f3a0380680cd59c2cce6da47e1692cdf",
          "message": "feat: add a mobk command that shows the last kill (merges PR #55, addresses #51)\n\nfeat: add a mobk last command that shows the last kill\n\nmobk keeps a copy of the last kill it raised, in memory only, and\n#bp.aard.mobk.last shows the mob, room, level, xp, gold, special-kill\nflags, fight time and damage table, or says there is none yet.\n\nAddresses #51\n\n\nClaude-Session: https://claude.ai/code/session_01NXu1sbBxFsEQW16MiZv7Je\n\nCo-authored-by: Claude Opus 5.5 <noreply@anthropic.com>",
          "timestamp": "2026-11-23T14:31:28Z",
          "tree_id": "ce47a850a344e85a57218352b3123aaeebf92d4a",
          "url": "https://github.com/endavis/bastproxy-aardwolf/commit/f5226862f3a0380680cd59c2cce6da47e1692cdf"
        },
        "date": 1795444325855,
        "tool": "pytest",
        "benches": [
          {
            "name": "tests/benchmarks/test_bench_aardu.py::test_bench_convert_level",
            "value": 3088738.8613025425,
            "unit": "iter/sec",
            "range": "stddev: 4.6829424796739524e-8",
            "extra": "mean: 323.75673208524114 nsec\nrounds: 196503"
          },
          {
            "name": "tests/benchmarks/test_bench_aardu.py::test_bench_parse_damage_line",
            "value": 170791.9635954209,
            "unit": "iter/sec",
            "range": "stddev: 0.0000010151825818130333",
            "extra": "mean: 5.855076427183902 usec\nrounds: 176992"
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
          "id": "6b8999bdae1b357e4b75f357d4f1414e187cbab0",
          "message": "feat: add a statdb command that lists recent kills (merges PR #56, addresses #52)\n\nfeat: add a statdb mobkills command that lists recent kills\n\nAdd `#bp.aardwolf.statdb.mobkills`, which lists the last N rows of the\nmobkills table, newest first: time (UTC), name, level, total XP, gold,\nroom and the special-kill flags. `-c N` sets the count (default 10), and\nan empty table gives a message instead of an error. The query is\nparameterised.\n\nAddresses #52\n\n\nClaude-Session: https://claude.ai/code/session_01NXu1sbBxFsEQW16MiZv7Je\n\nCo-authored-by: Claude Opus 5.5 <noreply@anthropic.com>",
          "timestamp": "2026-11-23T14:41:53Z",
          "tree_id": "b6fc8ab74b7e46d97d2d4840ea2dd675912d64e6",
          "url": "https://github.com/endavis/bastproxy-aardwolf/commit/6b8999bdae1b357e4b75f357d4f1414e187cbab0"
        },
        "date": 1795444949827,
        "tool": "pytest",
        "benches": [
          {
            "name": "tests/benchmarks/test_bench_aardu.py::test_bench_convert_level",
            "value": 3047066.4292748244,
            "unit": "iter/sec",
            "range": "stddev: 6.0406824270689e-8",
            "extra": "mean: 328.1845090059265 nsec\nrounds: 199641"
          },
          {
            "name": "tests/benchmarks/test_bench_aardu.py::test_bench_parse_damage_line",
            "value": 170711.72121943673,
            "unit": "iter/sec",
            "range": "stddev: 9.071292586716228e-7",
            "extra": "mean: 5.857828582927691 usec\nrounds: 176336"
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
          "id": "cbc8853837138d7a6e6ebd5bf051b51b559e7b4d",
          "message": "feat: add an aardwolf config plugin with a questmaster list (merges PR #58, addresses #57)\n\nplugins.aardwolf.config holds settings shared by the aardwolf plugins.\nIts first one is the list of questmasters, a read-only core list setting\nthat defaults to Commander Barcett and A QuestoR and is saved across\nrestarts.\n\n- #bp.aard.config.questmaster lists the names; add <name> and\n  remove <name> change one entry. Names may hold spaces and match\n  exactly, case included, as the questmaster's tell does.\n- The questmasters.get API returns a copy of the list.\n- ev_plugins.aardwolf.config_questmasters_changed carries the new list\n  whenever it changes; the load-time settings event is not passed on.\n\nAddresses #57\n\n\nClaude-Session: https://claude.ai/code/session_01NXu1sbBxFsEQW16MiZv7Je\n\nCo-authored-by: Claude Opus 5.5 <noreply@anthropic.com>",
          "timestamp": "2026-11-23T14:54:27Z",
          "tree_id": "af418628443a679a332c9b2fb228e463db43079f",
          "url": "https://github.com/endavis/bastproxy-aardwolf/commit/cbc8853837138d7a6e6ebd5bf051b51b559e7b4d"
        },
        "date": 1795445709611,
        "tool": "pytest",
        "benches": [
          {
            "name": "tests/benchmarks/test_bench_aardu.py::test_bench_convert_level",
            "value": 3971723.8401812566,
            "unit": "iter/sec",
            "range": "stddev: 1.623671139441319e-8",
            "extra": "mean: 251.77984176119438 nsec\nrounds: 41330"
          },
          {
            "name": "tests/benchmarks/test_bench_aardu.py::test_bench_parse_damage_line",
            "value": 224312.39765344208,
            "unit": "iter/sec",
            "range": "stddev: 4.5081779348234974e-7",
            "extra": "mean: 4.4580683478091965 usec\nrounds: 116646"
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
          "id": "b0d301b10c0dfed1c5dec8c2903460a902c6f2b2",
          "message": "fix: recognise a new campaign from any listed questmaster (merges PR #59, addresses #54)\n\n* fix: recognise a new campaign from any questmaster\n\nThe cp plugin started tracking a campaign only when Commander Barcett\ngave it. A newbie's questmaster, A QuestoR, sends the same\n\"Type 'campaign info' to see what you must kill.\" tell, so a campaign\nfrom it was never tracked or recorded in statdb.\n\nThe cp_new trigger now matches that tell from any sender. A spoofed tell\nfrom a player only queues a campaign check, which answers \"You are not\ncurrently on a campaign.\" and leaves tracking off.\n\nAddresses #54\n\nCo-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>\nClaude-Session: https://claude.ai/code/session_01NXu1sbBxFsEQW16MiZv7Je\n\n* fix: only start a campaign from a known questmaster\n\nMatching the new-campaign tell from any sender let a player's tell, or\nan emote that names a questmaster after the player's name, clear the\ntracked campaign. The cp_new trigger is now built from the questmaster\nlist of plugins.aardwolf.config, each name escaped and anchored at the\nstart of the line, and is updated when that list changes. With an empty\nlist it matches nothing.\n\ncp now depends on plugins.aardwolf.config, and reads the list through\nits API and its changed event.\n\nAddresses #54\n\nCo-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>\nClaude-Session: https://claude.ai/code/session_01NXu1sbBxFsEQW16MiZv7Je\n\n---------\n\nCo-authored-by: Claude Opus 5.5 <noreply@anthropic.com>",
          "timestamp": "2026-11-23T15:02:06Z",
          "tree_id": "98806bd2471105f1e71bc83a95e07ad620e3457f",
          "url": "https://github.com/endavis/bastproxy-aardwolf/commit/b0d301b10c0dfed1c5dec8c2903460a902c6f2b2"
        },
        "date": 1795446172570,
        "tool": "pytest",
        "benches": [
          {
            "name": "tests/benchmarks/test_bench_aardu.py::test_bench_convert_level",
            "value": 5106742.233697574,
            "unit": "iter/sec",
            "range": "stddev: 1.5171461370675454e-8",
            "extra": "mean: 195.81955662483927 nsec\nrounds: 53634"
          },
          {
            "name": "tests/benchmarks/test_bench_aardu.py::test_bench_parse_damage_line",
            "value": 269984.793103966,
            "unit": "iter/sec",
            "range": "stddev: 4.7513852716200184e-7",
            "extra": "mean: 3.703912314849967 usec\nrounds: 144614"
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
          "id": "7c8fb5ff9b13ffdbe11e58dd5dd9fbe4c2a0524f",
          "message": "feat: make the Aardwolf prompts end in %c (merges PR #61, addresses #60)\n\nAdd the promptfix plugin, ported from the MUSHclient prompt fixer. When the\ncharacter is first active, and whenever the MUD says \"Prompt set to\" or\n\"Battle prompt set to\", it requests the prompts over GMCP and changes any\nthat do not end in an unescaped %c with the prompt and bprompt commands,\ntelling the user. A result over 80 visible characters is not sent; the user\nis told to change it by hand. The autofix setting turns the fixer off.\n\nAddresses #60\n\n\nClaude-Session: https://claude.ai/code/session_01NXu1sbBxFsEQW16MiZv7Je\n\nCo-authored-by: Claude Opus 5.5 <noreply@anthropic.com>",
          "timestamp": "2026-11-23T17:05:44Z",
          "tree_id": "b5525f277ed9ab4464d945c8a490e6b8d18b7857",
          "url": "https://github.com/endavis/bastproxy-aardwolf/commit/7c8fb5ff9b13ffdbe11e58dd5dd9fbe4c2a0524f"
        },
        "date": 1795453581502,
        "tool": "pytest",
        "benches": [
          {
            "name": "tests/benchmarks/test_bench_aardu.py::test_bench_convert_level",
            "value": 2869242.6410198817,
            "unit": "iter/sec",
            "range": "stddev: 9.441314421814638e-8",
            "extra": "mean: 348.5240271086124 nsec\nrounds: 199881"
          },
          {
            "name": "tests/benchmarks/test_bench_aardu.py::test_bench_parse_damage_line",
            "value": 174740.1484311267,
            "unit": "iter/sec",
            "range": "stddev: 6.068417704875982e-7",
            "extra": "mean: 5.722783281222557 usec\nrounds: 183925"
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
          "id": "bec99d995ebcfdc5e5bbe0dc9cc700aaef563333",
          "message": "feat: add Questor to the default questmasters (merges PR #63, addresses #62)\n\nQuestor also gives campaigns, and a campaign from it was not tracked\nuntil the name was added by hand. The default questmaster list, in the\nconfig plugin and in cp's copy for its trigger, is now Commander\nBarcett, A QuestoR and Questor. A home that already saved its list\nkeeps it.\n\nAddresses #62\n\n\nClaude-Session: https://claude.ai/code/session_01NXu1sbBxFsEQW16MiZv7Je\n\nCo-authored-by: Claude Opus 5.5 <noreply@anthropic.com>",
          "timestamp": "2026-11-23T17:44:23Z",
          "tree_id": "34aaf178eae4a8577ba2d3c7270e3dce0c443558",
          "url": "https://github.com/endavis/bastproxy-aardwolf/commit/bec99d995ebcfdc5e5bbe0dc9cc700aaef563333"
        },
        "date": 1795455903128,
        "tool": "pytest",
        "benches": [
          {
            "name": "tests/benchmarks/test_bench_aardu.py::test_bench_convert_level",
            "value": 4536902.439699295,
            "unit": "iter/sec",
            "range": "stddev: 1.5262392542819255e-8",
            "extra": "mean: 220.4147021654448 nsec\nrounds: 47157"
          },
          {
            "name": "tests/benchmarks/test_bench_aardu.py::test_bench_parse_damage_line",
            "value": 241191.08812348705,
            "unit": "iter/sec",
            "range": "stddev: 5.804794481118348e-7",
            "extra": "mean: 4.146090171822649 usec\nrounds: 126647"
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
          "id": "1618784ab1316d78fa7aeb13f2fe434cbbaf6d05",
          "message": "feat: track campaigns from campaign info (merges PR #65, addresses #64)\n\ncp started tracking a campaign only on the questmaster's tell, so a\ncampaign was lost when the tell came from a questmaster not on the\nlist, or when the proxy or cp started mid-campaign. campaign check\ncould not recover it: it lists only the targets left.\n\ncp now reads campaign info, server output that lists the campaign's\nlevel, rewards and every target. It is queued as a second mudcmds\ncommand type: on the new-campaign tell, on a CAMPAIGN-mob kill while\ncp is off a campaign, and at load and first active ahead of the check.\n\n- A campaign cp is not on, or with a different Complete By, starts a\n  new state: the start time is now minus (7 days - Time Left), the\n  level comes from Level Taken, and the original targets from the\n  \"Find and kill\" lines. A target of count n is stored n times.\n- The campaign cp already tracks is left alone.\n- The not-on-a-campaign reply is assumed to match campaign check's; a\n  prompt fallback finishes the command if it does not.\n- The tell no longer clears the state, so a faked tell costs one\n  campaign info. completeby is added to the state and the comp/failed\n  payloads.\n\nAddresses #64\n\n\nClaude-Session: https://claude.ai/code/session_01NXu1sbBxFsEQW16MiZv7Je\n\nCo-authored-by: Claude Opus 5.5 <noreply@anthropic.com>",
          "timestamp": "2026-11-23T17:59:39Z",
          "tree_id": "49a71cfb32bae90659360aaae80ab641e0d03d84",
          "url": "https://github.com/endavis/bastproxy-aardwolf/commit/1618784ab1316d78fa7aeb13f2fe434cbbaf6d05"
        },
        "date": 1795456819552,
        "tool": "pytest",
        "benches": [
          {
            "name": "tests/benchmarks/test_bench_aardu.py::test_bench_convert_level",
            "value": 3769160.8060106994,
            "unit": "iter/sec",
            "range": "stddev: 3.6070841792848857e-8",
            "extra": "mean: 265.3110470652499 nsec\nrounds: 196387"
          },
          {
            "name": "tests/benchmarks/test_bench_aardu.py::test_bench_parse_damage_line",
            "value": 208601.79009363567,
            "unit": "iter/sec",
            "range": "stddev: 7.182417611412775e-7",
            "extra": "mean: 4.79382271624384 usec\nrounds: 109195"
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
          "id": "74ef162cf5c376a0266723091b6e99ef237379d2",
          "message": "fix: store only the time a level was reached (merges PR #67, addresses #66)\n\nA level record's starttime was the previous record's finish time, so\neach row carried the time spent at the level before it. A record now\nstarts at the time its level or powerup was reached, as the original\nplugin stored it.\n\n- level: _start uses now; next_starttime and its fallback chain are\n  gone, so a failed superhero no longer leaks its time into the next\n  record\n- statdb: save_level no longer closes the previous row; finishtime\n  stays in the schema as -1 for new rows\n- report: time at a level is the gap to the next row's starttime,\n  using LEAD() over level_id before filtering, in the averages, the\n  levels list and the single-level view (finish, kills, xp per mob)\n- docs: level and statdb pages describe the new meaning\n\nOld databases already store starttime as the time reached, so no\nmigration is needed and their report values are unchanged.\n\nAddresses #66\n\nBREAKING CHANGE: aardwolf.level.libs no longer exports next_starttime.\nA record's starttime is now the time it was reached; use the current\ntime instead of calling it.\n\n\nClaude-Session: https://claude.ai/code/session_01NXu1sbBxFsEQW16MiZv7Je\n\nCo-authored-by: Claude Opus 5.5 <noreply@anthropic.com>",
          "timestamp": "2026-11-23T19:22:58Z",
          "tree_id": "bde17e0ca886c2fd54cf6f996c063161d6b6e528",
          "url": "https://github.com/endavis/bastproxy-aardwolf/commit/74ef162cf5c376a0266723091b6e99ef237379d2"
        },
        "date": 1795461823583,
        "tool": "pytest",
        "benches": [
          {
            "name": "tests/benchmarks/test_bench_aardu.py::test_bench_convert_level",
            "value": 3058135.9015775514,
            "unit": "iter/sec",
            "range": "stddev: 3.5996933705810416e-8",
            "extra": "mean: 326.99658621585326 nsec\nrounds: 199522"
          },
          {
            "name": "tests/benchmarks/test_bench_aardu.py::test_bench_parse_damage_line",
            "value": 179007.98379538592,
            "unit": "iter/sec",
            "range": "stddev: 5.573661640700318e-7",
            "extra": "mean: 5.586343015533007 usec\nrounds: 185254"
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
          "id": "0f2f91745a031deb01592a87d52cdb884312ba4b",
          "message": "feat: add the scanh plugin, which highlights targets in scan output (merges PR #69, addresses #68)\n\nPort the old bastproxy's scanh plugin. Between {scan} and {/scan}, a\nline naming a campaign, global quest or quest target is rewritten in\nthe target's colours with a (CP), (GQ) or (Quest) tag.\n\n- targets come only from the cp, gq and quest events, plus a read of\n  the cp mobs.left.get API at load when it exists\n- a disabled trigger group is on only while a scan is shown, and a\n  disconnect turns it off\n- six colour settings carry over with their old defaults\n\nOld bugs fixed: a name must end the line on a word boundary, so \"rat\"\nno longer matches \"pirat\"; a line keeps every matching tag; gq won\nand completed clear the targets; a killed quest target stops being\nhighlighted; the text colour settings say \"text color\"; debug output\ngoes to the log, not to clients; the cp event is the one source of\ncampaign targets.\n\nAddresses #68\n\n\nClaude-Session: https://claude.ai/code/session_01NXu1sbBxFsEQW16MiZv7Je\n\nCo-authored-by: Claude Opus 5.5 <noreply@anthropic.com>",
          "timestamp": "2026-11-23T20:03:40Z",
          "tree_id": "5d22aa70998ad93129f28cdcb80248a35d86a3a8",
          "url": "https://github.com/endavis/bastproxy-aardwolf/commit/0f2f91745a031deb01592a87d52cdb884312ba4b"
        },
        "date": 1795464262453,
        "tool": "pytest",
        "benches": [
          {
            "name": "tests/benchmarks/test_bench_aardu.py::test_bench_convert_level",
            "value": 3145741.415812051,
            "unit": "iter/sec",
            "range": "stddev: 4.5331056953602333e-8",
            "extra": "mean: 317.89008307342294 nsec\nrounds: 191976"
          },
          {
            "name": "tests/benchmarks/test_bench_aardu.py::test_bench_parse_damage_line",
            "value": 175623.315171955,
            "unit": "iter/sec",
            "range": "stddev: 9.432327872509295e-7",
            "extra": "mean: 5.694004802385647 usec\nrounds: 181160"
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
          "id": "a083405ddd1711333a72d14c25ccbb3c3fabb660",
          "message": "feat: hide all output of the campaign commands the cp plugin queues (merges PR #88, addresses #70)\n\nThe cp plugin omitted the target and time lines of the campaign info\nand check it queues itself, but the state line (\"You will have to\nlevel ...\"), the campaigns-completed count, the blank line and the\nprompt still reached the client. After a cp req that showed up as\nthree extra prompts and the state line.\n\nThe first omitted line of a queued info or check now opens a hide\nwindow. A watcher on the core's before-all-lines trigger hides every\nline through the next prompt, which is hidden too. The triggers still\nmatch the hidden lines, so the state line still updates cantake,\nneed to level and shtime. A check or info the player types is shown\nin full, because those groups are only on for queued commands.\n\nThe window closes on disconnect, and after 60 hidden lines with no\nprompt, so output is never hidden for good.\n\nAddresses #70\n\n\nClaude-Session: https://claude.ai/code/session_01NXu1sbBxFsEQW16MiZv7Je\n\nCo-authored-by: Claude Opus 5.5 <noreply@anthropic.com>",
          "timestamp": "2026-11-23T20:17:14Z",
          "tree_id": "c195ebf7695df00ecf98ca06d092663c96c6229d",
          "url": "https://github.com/endavis/bastproxy-aardwolf/commit/a083405ddd1711333a72d14c25ccbb3c3fabb660"
        },
        "date": 1795465070813,
        "tool": "pytest",
        "benches": [
          {
            "name": "tests/benchmarks/test_bench_aardu.py::test_bench_convert_level",
            "value": 5796630.87907837,
            "unit": "iter/sec",
            "range": "stddev: 1.1042807476687904e-8",
            "extra": "mean: 172.51400354113875 nsec\nrounds: 58738"
          },
          {
            "name": "tests/benchmarks/test_bench_aardu.py::test_bench_parse_damage_line",
            "value": 287150.4840757552,
            "unit": "iter/sec",
            "range": "stddev: 3.9346834930415797e-7",
            "extra": "mean: 3.4824945645440146 usec\nrounds: 153989"
          }
        ]
      }
    ]
  }
}