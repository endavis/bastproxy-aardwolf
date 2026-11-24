window.BENCHMARK_DATA = {
  "lastUpdate": 1795515911298,
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
          "id": "b0d274f0a926fe2c42b313a6113508cb94e82e5f",
          "message": "feat: port itemu, skills, move and repop from the old bastproxy (merges PR #89, addresses #71, #72, #73, #85)\n\n* feat: port itemu as the aardwolf.libs.itemu library\n\nThe old itemu plugin held no state: five APIs returned constant tables\nand dataparse split a line by a fixed layout. It becomes a library\nmodule beside aardu, so the eq, itemid and itemkeep ports can import\nit; importing a library is allowed where importing a plugin is not.\n\n- the tables keep their old names as module constants, with\n  OBJECTTYPESREV and WEARLOCSREV for the reverse lookups\n- parse_item_data(line, layout, strip_color) splits comma layouts\n  (eqdata, tempmod, enchant) on commas and the rest on pipes, and\n  converts numbers to int; eqdata takes the colour stripper the\n  caller passes, as aardu takes its GMCP getter\n\nChanges from the old plugin: a short line or an unknown layout raises\nValueError instead of logging and returning a partial dict or None;\nthe dead invheader \"type\" branch is gone.\n\nAddresses #71\n\nCo-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>\nClaude-Session: https://claude.ai/code/session_01NXu1sbBxFsEQW16MiZv7Je\n\n* feat: add the move plugin, which raises an event on a room change\n\nPort the old move plugin as plugins.aardwolf.move. On each GMCP\nroom.info whose room number differs from the last one, it raises\nev_plugins.aardwolf.move_room with from, to and direction (the exit\nof the old room that leads to the new one, or \"unknown\").\n\nChanges from the old plugin:\n- the roominfo payload key, a copy of \"to\", is dropped\n- the last room is forgotten on disconnect, so a reconnect no longer\n  raises a move from the previous session's room\n- a room.info without a num is ignored instead of raising KeyError\n- the room is read from the event data, and seeded from the GMCP\n  cache when the plugin loads mid-session\n- the per-move echo is a debug log line; the room request on first\n  active is left to the connect plugin, which already sends it\n\nAddresses #73\nBatched in the PR for #71.\n\nCo-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>\nClaude-Session: https://claude.ai/code/session_01NXu1sbBxFsEQW16MiZv7Je\n\n* feat: add the skills plugin, which tracks skills, spells and recoveries\n\nPort the old skills plugin as plugins.aardwolf.skills. It reads\n`slist` through the core mudcmds queue on first active and after a\nremort or tier, keeps the skills and recoveries in memory, follows the\n{affon}, {affoff}, {recon}, {recoff}, {skillgain} and {sfail} tags,\nand raises ev_plugins.aardwolf.skills_* events. The old APIs become\ndotted APIs (skill.get, skill.is.affected, spellups.get, skill.send,\n...); docs/plugins/skills.md maps old names to new ones.\n\nThe queued slist output is hidden from its {spellheaders} start tag\nto its end tag, with a cap, and a typed slist is shown. The a102\nSPELLUPTAGS and SKILLGAINTAGS options are requested while the plugin\nis loaded.\n\nOld bugs fixed: isbad called a misspelt API and always failed; tags\nfor an unknown skill number raised KeyError or TypeError; an unknown\nfail reason or target code raised KeyError; {/spellheaders} leaked to\nthe client; skills_affected_update was never raised although su and\naflags listen for it; the refresh echo named the wrong slist.\n\ncodespell now ignores \"uptodate\", the old event and API name.\n\nAddresses #72\nBatched in the PR for #71.\n\nCo-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>\nClaude-Session: https://claude.ai/code/session_01NXu1sbBxFsEQW16MiZv7Je\n\n* feat: add the repop plugin, which announces area repops on a channel\n\nPort the old repop plugin as plugins.aardwolf.repop. On GMCP\ncomm.repop it fills the format setting with ${zone} and ${time} and\nsends \"<channel> <message>\" to the MUD. The channel (gt) and format\ndefaults are unchanged.\n\nChanges from the old plugin:\n- a comm.repop with no zone is skipped instead of raising KeyError\n- a blank channel sends nothing instead of \" <message>\"\n- the line goes straight to the MUD, so a proxy alias or #bp command\n  as the channel no longer expands; MUD aliases still work\n- the format setting is shown with its raw @ colour codes\n\nAddresses #85\nBatched in the PR for #71.\n\nCo-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>\nClaude-Session: https://claude.ai/code/session_01NXu1sbBxFsEQW16MiZv7Je\n\n* docs: record the slist forms checked against Aardwolf\n\nThe skills page said its slist forms were inferred from the old\nregexes. Aardwolf's own `slist noprompt` and `slist spellup noprompt`\noutput now confirms them: {spellheaders noprompt} and\n{spellheaders spellup noprompt} start the blocks, the full list has a\n{recoveries noprompt} section and runs to about 680 lines, the\nspellup list ends at {/spellheaders}, and neither sends a prompt. A\ntyped `slist` starts with a bare {spellheaders} and stays visible.\nThe affect and recovery tags remain inferred.\n\nAddresses #72\nBatched in the PR for #71.\n\nCo-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>\nClaude-Session: https://claude.ai/code/session_01NXu1sbBxFsEQW16MiZv7Je\n\n---------\n\nCo-authored-by: Claude Opus 5.5 <noreply@anthropic.com>",
          "timestamp": "2026-11-23T20:46:24Z",
          "tree_id": "1251c8da40fb767331fb8cb803c30d7236ab6c54",
          "url": "https://github.com/endavis/bastproxy-aardwolf/commit/b0d274f0a926fe2c42b313a6113508cb94e82e5f"
        },
        "date": 1795466818985,
        "tool": "pytest",
        "benches": [
          {
            "name": "tests/benchmarks/test_bench_aardu.py::test_bench_convert_level",
            "value": 2975623.984346827,
            "unit": "iter/sec",
            "range": "stddev: 4.649283662950671e-8",
            "extra": "mean: 336.06396683870923 nsec\nrounds: 197278"
          },
          {
            "name": "tests/benchmarks/test_bench_aardu.py::test_bench_parse_damage_line",
            "value": 170428.29882127786,
            "unit": "iter/sec",
            "range": "stddev: 8.958315648767612e-7",
            "extra": "mean: 5.867570156577487 usec\nrounds: 178572"
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
          "id": "2d289ee2aa07d131f32906b4b4dcca19a855c288",
          "message": "fix: mark Aardwolf prompt lines so the cp hide window closes at them (merges PR #91, addresses #90)\n\n* fix: mark Aardwolf prompt lines so the cp hide window closes at them\n\nAardwolf sends no IAC GA or EOR after a prompt, so no MUD line ever\nreached the triggers with is_prompt set. cp's hide window (#70) could\nnot close at a prompt and ran to its 60-line cap, hiding the next\nqueued command's output (whois) and letting its last blank line and\nprompt through.\n\npromptfix now builds an anchored pattern from each prompt template it\ngets in GMCP char.prompts and marks matching MUD lines as prompts, at\npriority 30 on ev_to_client_data_modify, before the core waiters (40)\nand triggers (50) read the flag. The pattern comes from the last line\nof the template; colour codes are stripped, each %-code is a wildcard,\nliteral text is escaped, and only trailing Aardwolf flags such as\n*[NOEXP]* are allowed after it. A template that does not end in %c, or\nhas fewer than 3 fixed characters, gets no pattern, with one warning.\nPatterns are built even with autofix off and cleared on disconnect.\n\nEvery consumer of is_prompt works unchanged: cp's window, the core's\non_prompt triggers and prompt trigger. Clients now get IAC GA or EOR\nafter a marked prompt, as they would from a MUD that sends GA.\n\ncp keeps HIDE_MAX_LINES as a safety net and logs at warning level when\nthe cap ends a window, so a missed prompt shows in the log.\n\nAddresses #90\n\nCo-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>\nClaude-Session: https://claude.ai/code/session_01NXu1sbBxFsEQW16MiZv7Je\n\n* fix: keep the prompt patterns from backtracking catastrophically\n\nEach %-code in a prompt template became a lazy .*? wildcard, and every\nMUD line is tested against the pattern. A line that nearly matched a\ntemplate with many codes made the regex try every split between the\nwildcards: with 12 codes, one 22-character near-miss line did not\nfinish within 60 seconds, which would freeze the proxy.\n\nA value now runs up to the first character of the fixed text after\nit and is possessive, so a near-miss fails in linear time. Adjacent\ncodes are merged into one value, the last value stops at Aardwolf's\n*[FLAG]* markers, and lines longer than MAX_PROMPT_LINE (400) are not\ntested. A value that contains the first character of the fixed text\nafter it now leaves its line unmarked; the docs say so.\n\nAddresses #90\n\nCo-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>\nClaude-Session: https://claude.ai/code/session_01NXu1sbBxFsEQW16MiZv7Je\n\n---------\n\nCo-authored-by: Claude Opus 5.5 <noreply@anthropic.com>",
          "timestamp": "2026-11-23T21:42:32Z",
          "tree_id": "5ee91d8207705ab0e0d3df51d07433ce42222884",
          "url": "https://github.com/endavis/bastproxy-aardwolf/commit/2d289ee2aa07d131f32906b4b4dcca19a855c288"
        },
        "date": 1795470197395,
        "tool": "pytest",
        "benches": [
          {
            "name": "tests/benchmarks/test_bench_aardu.py::test_bench_convert_level",
            "value": 5125841.2702303035,
            "unit": "iter/sec",
            "range": "stddev: 1.5295797375513454e-8",
            "extra": "mean: 195.0899271516205 nsec\nrounds: 53124"
          },
          {
            "name": "tests/benchmarks/test_bench_aardu.py::test_bench_parse_damage_line",
            "value": 269920.3142514231,
            "unit": "iter/sec",
            "range": "stddev: 5.077288943686773e-7",
            "extra": "mean: 3.704797109374022 usec\nrounds: 144467"
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
          "id": "544dd85b091d442b6ee2a74e29997f0f8e70c5b5",
          "message": "feat: hide all output of the whois the whois plugin queues (merges PR #93, addresses #92)\n\nThe whois plugin sends whois itself on first active and at load, but\nhid none of the output, so every login showed a whois the player\nnever asked for. The old plugin only parsed a whois the player typed.\n\nA queued whois (mudcmds runs the type's beforef only for a queued\ncommand) arms a hide flag. A new whoisstart trigger on the opening\n74-dash line opens a hide window when the flag is set: every line\nthrough the next marked prompt is hidden, the prompt included, using\nthe core before-all-lines trigger and line.send = False, as cp does.\nLines that arrive between the send and the reply stay visible. A\ntyped whois clears the flag and is always shown in full. The window\ncloses on disconnect, and after HIDE_MAX_LINES hidden lines with a\nwarning. Parsing and whois_received are unchanged.\n\nTwo existing assertions list the plugin's triggers and now include\nwhoisstart: test_after_load (the trigger set) and\ntest_single_class_typed_whois (the triggers enabled by a typed whois).\n\nAddresses #92\n\n\nClaude-Session: https://claude.ai/code/session_01NXu1sbBxFsEQW16MiZv7Je\n\nCo-authored-by: Claude Opus 5.5 <noreply@anthropic.com>",
          "timestamp": "2026-11-23T21:59:20Z",
          "tree_id": "90a5e5ff809934fdde861e2a6ba9f218c88382fd",
          "url": "https://github.com/endavis/bastproxy-aardwolf/commit/544dd85b091d442b6ee2a74e29997f0f8e70c5b5"
        },
        "date": 1795471196408,
        "tool": "pytest",
        "benches": [
          {
            "name": "tests/benchmarks/test_bench_aardu.py::test_bench_convert_level",
            "value": 2568980.855606168,
            "unit": "iter/sec",
            "range": "stddev: 6.035011322313592e-8",
            "extra": "mean: 389.25942083910286 nsec\nrounds: 193837"
          },
          {
            "name": "tests/benchmarks/test_bench_aardu.py::test_bench_parse_damage_line",
            "value": 150667.3111573087,
            "unit": "iter/sec",
            "range": "stddev: 0.0000025396505755239818",
            "extra": "mean: 6.637139750611997 usec\nrounds: 176679"
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
          "id": "e6ebcb0665d8efc68b39b255a7f2f20266ac97c1",
          "message": "refactor: hide queued cp, slist and whois output through mudcmds (merges PR #95, addresses #94)\n\ncp, skills and whois each kept their own hide window on the\nbefore-all-lines trigger. They now pass hide_output, hide_start,\nhide_end and hide_max to plugins.core.mudcmds:type.add, and the core\nwindow (endavis/bastproxy#738, #740) does the hiding. Their\n_start_hiding, _hide_line and _stop_hiding, the hiding state and\nBEFORE_ALL_LINES_ID are removed.\n\n- cp: hide_start is an alternation of each group's omit trigger\n  regexes; the window closes at the first prompt after finish, or on\n  the prompt itself for an info that finishes there.\n- skills: the spellup slist gets its own type, slistspellup, so each\n  type closes at its own end tag ({/spellheaders} or {/recoveries}).\n- whois: the window opens at the first 74-dash line; the whoisstart\n  trigger is gone.\n- hide_max is HIDE_MAX_LINES + 1, since mudcmds counts the opening line.\n\nBehaviour changes:\n- A whois typed while a queued whois waits for its reply is hidden\n  until the queued one finishes or times out.\n- The cap warning now comes from plugins.core.mudcmds, at WARNING.\n- uv.lock moves the core from 26be624f to a55e622a, which also brings\n  the mudcmds command timeout (5s by default).\n\nTests drive a real core MUDCmdsPlugin window through\ntests/mudcmds_support.py.\n\nAddresses #94\n\nBREAKING CHANGE: aardwolf.cp.libs, aardwolf.skills.libs and\naardwolf.whois.libs no longer export BEFORE_ALL_LINES_ID. Use the core\ntriggers plugin's before-all-lines trigger id,\n\"t_plugins.core.triggers_beall\", or hide a queued command's output with\nmudcmds' hide_output.\n\n\nClaude-Session: https://claude.ai/code/session_01NXu1sbBxFsEQW16MiZv7Je\n\nCo-authored-by: Claude Opus 5.5 <noreply@anthropic.com>",
          "timestamp": "2026-11-23T23:01:42Z",
          "tree_id": "9a924fb79600b0f44cc02ba11a24704d5d6e77f2",
          "url": "https://github.com/endavis/bastproxy-aardwolf/commit/e6ebcb0665d8efc68b39b255a7f2f20266ac97c1"
        },
        "date": 1795474950388,
        "tool": "pytest",
        "benches": [
          {
            "name": "tests/benchmarks/test_bench_aardu.py::test_bench_convert_level",
            "value": 3175816.742518827,
            "unit": "iter/sec",
            "range": "stddev: 5.464923752952101e-8",
            "extra": "mean: 314.8796297379781 nsec\nrounds: 196503"
          },
          {
            "name": "tests/benchmarks/test_bench_aardu.py::test_bench_parse_damage_line",
            "value": 171631.99523170583,
            "unit": "iter/sec",
            "range": "stddev: 0.0000010829470200383612",
            "extra": "mean: 5.826419477615374 usec\nrounds: 179180"
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
          "id": "a99d039e2b1f1c20d5732ed3452e48b0448a016b",
          "message": "feat: port the eqdb plugin (merges PR #96, addresses #74)\n\nplugins.aardwolf.eqdb keeps identified items in a SQLite database\nthrough plugins.core.sqldb, with the old plugin's 18 tables kept word\nfor word so an old eqdb file opens as it is.\n\n- item.get returns an item by serial or identifier as a dict, with its\n  details; item.save takes a dict and replaces each detail it holds.\n  A wrong detail shape is refused before anything is written.\n- getitem shows an item; the old debug test command is dropped.\n- backupstart and backupinterval drive its own backups, rescheduled\n  when either setting changes.\n\nOld bugs fixed, listed in docs/plugins/eqdb.md: type details (weapon,\nlight, container and the rest) were never saved because the numeric\nitype was compared with names; backup setting changes were ignored;\nmissing flags or keywords crashed save and get; stale mods were kept;\nthe caller's enchant data was changed; SQL was built with %.\n\ncodespell ignores \"anid\", the old affectmod key column.\n\nAddresses #74\n\n\nClaude-Session: https://claude.ai/code/session_01NXu1sbBxFsEQW16MiZv7Je\n\nCo-authored-by: Claude Opus 5.5 <noreply@anthropic.com>",
          "timestamp": "2026-11-23T23:39:27Z",
          "tree_id": "1e402a431d86692e993c52ea059dc08e69dada5d",
          "url": "https://github.com/endavis/bastproxy-aardwolf/commit/a99d039e2b1f1c20d5732ed3452e48b0448a016b"
        },
        "date": 1795477208636,
        "tool": "pytest",
        "benches": [
          {
            "name": "tests/benchmarks/test_bench_aardu.py::test_bench_convert_level",
            "value": 5137349.9204579815,
            "unit": "iter/sec",
            "range": "stddev: 2.0509092751890694e-8",
            "extra": "mean: 194.65288825621843 nsec\nrounds: 53721"
          },
          {
            "name": "tests/benchmarks/test_bench_aardu.py::test_bench_parse_damage_line",
            "value": 272444.25148834486,
            "unit": "iter/sec",
            "range": "stddev: 4.878375362729854e-7",
            "extra": "mean: 3.6704756827757103 usec\nrounds: 144342"
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
          "id": "2b1a1d77d1d54c52e80a581e5877ad0cc2fe3ada",
          "message": "feat: port the eq plugin's item tracking (merges PR #98, addresses #75)\n\n* feat: port the eq plugin's item tracking\n\nplugins.aardwolf.eq follows invmon, invitem and the eqdata, invdata,\nkeyring data and vault data blocks, and keeps worn items, inventory,\nkeyring, vault and bags in memory, one location per item. Items are\nplain dicts.\n\n- mudcmds types eq_worn, eq_inventory, eq_keyring, eq_vault and one\n  eq_container_<serial> per bag. A queued data command is hidden up to\n  and including the prompt after its end tag; a typed one is shown and\n  still parsed. Only a queued command starts command timing.\n- Events eq_worn, eq_removed, eq_inventory_added, eq_inventory_removed,\n  eq_put and eq_taken; fixed names with serial and container in the\n  payload replace the old per-serial event names.\n- APIs item.get, item.find.by.name, container.get, eq.worn.get (the\n  name mobk already calls), item.fetch, item.put, item.equip,\n  item.unequip and item.identify.add, which saves through eqdb's\n  item.save when eqdb is loaded.\n- Commands refresh, icache, get and put.\n\nThe eq and inv display commands follow in #97. The old bugs fixed are\nlisted in docs/plugins/eq.md.\n\nAddresses #75\n\nCo-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>\nClaude-Session: https://claude.ai/code/session_01NXu1sbBxFsEQW16MiZv7Je\n\n* fix: end the eq vault read when the character has no vault\n\nAardwolf answers \"vault data\" with \"You do not have a vault. See 'help\nvault' for how to acquire one.\" instead of a vault block for a\ncharacter with no vault. The queued vault read then never finished:\nmudcmds timed it out after 5 seconds with a warning, and the answer\nwas shown. Seen on a live login in a bank room.\n\nA trigger on that line now records an empty vault and finishes the\neq_vault command, and the vault hide window also opens on it, so a\nqueued read hides the answer and its prompt. The old plugin had the\nsame gap, and the old queue had no timeout.\n\nAddresses #75\n\nCo-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>\nClaude-Session: https://claude.ai/code/session_01NXu1sbBxFsEQW16MiZv7Je\n\n* feat: turn on Aardwolf's invmon tags from the eq plugin\n\nNothing is tracked without the {invmon} lines, and Aardwolf sends them\nonly when invmon is on for the character. The \"invmon\" command is a\ntoggle (\"You will now see inventory update tags.\"), so sending it could\nturn the tags off. eq instead asks the a102 plugin for option 102\nfeature 20, INVMONTAGS (TELOPT_INVMON_TAGS in Aardwolf's client\npackage), when it loads, and takes the request back when it unloads, as\nskills does for its tags.\n\n- a102: INVMONTAGS (20) is added to the option table and its docs.\n  test_a102_options pins the table size, so its two counts go from 24\n  to 25, and it now checks INVMONTAGS.\n- eq: depends on plugins.aardwolf.a102.\n\nAddresses #75\n\nCo-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>\nClaude-Session: https://claude.ai/code/session_01NXu1sbBxFsEQW16MiZv7Je\n\n* feat: hide the invmon and invitem lines from the client\n\neq turns the invmon tags on, so at login Aardwolf sends an {invmon}\nline for each worn item, and the client saw them as raw text. The\neq_invmon and eq_invitem triggers now omit their lines: the plugin\nstill parses them, and other lines are shown. The old plugin showed\nthem.\n\nAddresses #75\n\nCo-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>\nClaude-Session: https://claude.ai/code/session_01NXu1sbBxFsEQW16MiZv7Je\n\n---------\n\nCo-authored-by: Claude Opus 5.5 <noreply@anthropic.com>",
          "timestamp": "2026-11-24T00:56:28Z",
          "tree_id": "69f0cbc677cc5919913f72d8e72161688e782e75",
          "url": "https://github.com/endavis/bastproxy-aardwolf/commit/2b1a1d77d1d54c52e80a581e5877ad0cc2fe3ada"
        },
        "date": 1795481822038,
        "tool": "pytest",
        "benches": [
          {
            "name": "tests/benchmarks/test_bench_aardu.py::test_bench_convert_level",
            "value": 4465807.522723797,
            "unit": "iter/sec",
            "range": "stddev: 1.673097086202732e-8",
            "extra": "mean: 223.9236677603332 nsec\nrounds: 46936"
          },
          {
            "name": "tests/benchmarks/test_bench_aardu.py::test_bench_parse_damage_line",
            "value": 232930.81811781967,
            "unit": "iter/sec",
            "range": "stddev: 5.734151461262923e-7",
            "extra": "mean: 4.293120198007402 usec\nrounds: 124844"
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
          "id": "52710d2afb74adb219eee0f3976e147c5da62310",
          "message": "feat: port the itemid plugin (merges PR #99, addresses #76)\n\n* feat: port the itemid plugin\n\nplugins.aardwolf.itemid identifies an item by queuing invdetails and\nidentify for its serial through mudcmds, parses both replies into one\nplain dict in eqdb's item shape, hands it to eq (and to eqdb when eq\ndoes not know the item), and raises ev_plugins.aardwolf.itemid_identified.\n\n- Both commands hide their output when queued, up to and including the\n  prompt after them; typed ones are shown and not parsed. Command timing\n  starts in beforef, which runs only for queued commands.\n- Replies are matched to serials through a queue of pending serials, and\n  an invheader for another serial is dropped. Tagged lines outside the\n  {invdetails} block (a fetch's {invmon}) are not read.\n- An item outside the inventory is fetched first and put back after,\n  and the event waits for eq's matching eq_put or eq_worn.\n- APIs item.identify, item.format and item.show; the id command shows\n  the item box, with -f to identify again and -d to read eqdb.\n- The cache is in memory and cleared on disconnect.\n\nThe old bugs fixed (the item box crashed for every item, Light and\nPortal never shown, zeros written into the item, a stale item reused,\nan identify that never ended stopping the queue, and more) are listed\nin docs/plugins/itemid.md. codespell ignores \"sav\", the Sav stat column.\n\nAddresses #76\n\nCo-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>\nClaude-Session: https://claude.ai/code/session_01NXu1sbBxFsEQW16MiZv7Je\n\n* fix: keep eq's place keys out of identify merges and eqdb saves\n\neq keeps an item's place in \"container\" (a container id such as\n\"Inventory\"), while eqdb reads \"container\" as the container detail of a\nbag (capacity and so on) and wants a mapping. item.identify.add merged\nthe identify attributes into eq's cached item and saved that copy, so:\n\n- for any item with a place, eqdb's save refused the \"container\"\n  string (\"the container detail has the wrong shape\"), and\n  item.identify.add logged it and returned False;\n- an identify that carried a container detail overwrote eq's place.\n\nitem.identify.add now never overwrites container, origcontainer or\nhasbeenided in the cache, and the copy it saves to eqdb leaves those\nplace keys out before laying the attributes over it, so a container\ndetail is saved and a place string never is.\n\nBatched in the PR for #76, whose itemid port is the first caller.\n\nAddresses #76\n\nCo-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>\nClaude-Session: https://claude.ai/code/session_01NXu1sbBxFsEQW16MiZv7Je\n\n* fix: unescape Aardwolf's colour codes in eq item names\n\nAardwolf sends the colour codes of an item name as text in invdata and\neqdata lines (@WGueldar's@w ...). The proxy's colour coded copy of the\nline escapes each literal @ as @@, so eq stored cname with @@W codes and\nits plain name kept @W codes; itemid's box showed them raw and eqdb\nwould have saved them.\n\nparse_item_line now turns @@ back into @ in cname, and name is cname\nwith the codes stripped.\n\nFound by the live check of the itemid port. Batched in the PR for #76.\n\nAddresses #76\n\nCo-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>\nClaude-Session: https://claude.ai/code/session_01NXu1sbBxFsEQW16MiZv7Je\n\n* fix: show the item type and bag name in itemid's box\n\nA live check on a real character found two gaps in the itemid box:\n\n- {invheader} carries the item type as a name (Weapon), not a number.\n  parse_item_data kept the string, so the box had no Type line, a light\n  had no duration and eqdb's itype column got text. The invheader\n  layout now maps the name through OBJECTTYPESREV, in any case; an\n  unknown name stays text.\n- A bagged item's Location showed the bag's serial. It now shows the\n  bag's plain name from eq and the serial, and the bare serial when eq\n  does not know the bag.\n\ndocs/plugins/itemid.md drops the known gaps the live check confirmed.\n\nAddresses #76\n\nCo-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>\nClaude-Session: https://claude.ai/code/session_01NXu1sbBxFsEQW16MiZv7Je\n\n---------\n\nCo-authored-by: Claude Opus 5.5 <noreply@anthropic.com>",
          "timestamp": "2026-11-24T09:49:16Z",
          "tree_id": "eefba147c9a9bd5a9843825e8b5ad2aa9d80c67d",
          "url": "https://github.com/endavis/bastproxy-aardwolf/commit/52710d2afb74adb219eee0f3976e147c5da62310"
        },
        "date": 1795513788523,
        "tool": "pytest",
        "benches": [
          {
            "name": "tests/benchmarks/test_bench_aardu.py::test_bench_convert_level",
            "value": 6167630.141550563,
            "unit": "iter/sec",
            "range": "stddev: 8.965358442976928e-9",
            "extra": "mean: 162.13683003835192 nsec\nrounds: 62720"
          },
          {
            "name": "tests/benchmarks/test_bench_aardu.py::test_bench_parse_damage_line",
            "value": 314986.30377969274,
            "unit": "iter/sec",
            "range": "stddev: 2.857752987737414e-7",
            "extra": "mean: 3.174741212555764 usec\nrounds: 159745"
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
          "id": "4b22ce7879cd5a876992bc98cadf01dbfc12ef05",
          "message": "feat: port the itemkeep plugin (merges PR #100, addresses #78)\n\n* feat: port the itemkeep plugin\n\nplugins.aardwolf.itemkeep keeps items of chosen types when they reach\nthe inventory. Each object type has a bool setting, off by default;\nwhen eq reports an item of an enabled type without K in its flags, the\nplugin queues \"keep <serial>\" through mudcmds.\n\n- It listens to eq_inventory_added, eq_taken and eq_removed, so items\n  taken from a bag, the vault or the keyring, and worn items taken off,\n  are kept too. The old plugin listened only to eq_inventory_added.\n- The keep is a hidden queued command type, itemkeep_keep. Its reply,\n  the note lines and {invitem} line after it, and the prompt are\n  hidden; a typed keep is shown. The reply patterns are the three\n  Aardwolf answers recorded on a live character.\n- Serials already sent a keep are skipped until disconnect.\n\nThe old bugs fixed (a setting for type \"none\", \"raw material\" not\nsettable, an IndexError on a bad itype, a visible plain send, and more)\nare listed in docs/plugins/itemkeep.md.\n\nAddresses #78\n\nCo-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>\nClaude-Session: https://claude.ai/code/session_01NXu1sbBxFsEQW16MiZv7Je\n\n* test: import the itemkeep plugin module after BASTPROXY_HOME is set\n\ntests/test_itemkeep_plugin.py imported the plugin module at collection,\nwhich imports bastproxy. Without BASTPROXY_HOME (as in CI) that import\nraised, and the half-imported bastproxy broke the entry point tests.\nThe module is now imported in the fixture after setenv, as the itemid\ntests do.\n\nAddresses #78\n\nCo-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>\nClaude-Session: https://claude.ai/code/session_01NXu1sbBxFsEQW16MiZv7Je\n\n---------\n\nCo-authored-by: Claude Opus 5.5 <noreply@anthropic.com>",
          "timestamp": "2026-11-24T10:11:52Z",
          "tree_id": "c0ff98a337f1d918a8eaf677746b521ca2c39405",
          "url": "https://github.com/endavis/bastproxy-aardwolf/commit/4b22ce7879cd5a876992bc98cadf01dbfc12ef05"
        },
        "date": 1795515149438,
        "tool": "pytest",
        "benches": [
          {
            "name": "tests/benchmarks/test_bench_aardu.py::test_bench_convert_level",
            "value": 3085368.339427954,
            "unit": "iter/sec",
            "range": "stddev: 4.4154003666282877e-8",
            "extra": "mean: 324.11041081254047 nsec\nrounds: 186951"
          },
          {
            "name": "tests/benchmarks/test_bench_aardu.py::test_bench_parse_damage_line",
            "value": 166295.31960774836,
            "unit": "iter/sec",
            "range": "stddev: 0.0000015294416334507054",
            "extra": "mean: 6.013398346740998 usec\nrounds: 177589"
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
          "id": "64881c0033b90abbe4b79e16563717902446ecbd",
          "message": "feat: port the eq plugin's eq and inv display commands (merges PR #101, addresses #97)\n\nplugins.aardwolf.eq gets the old display commands, built from its state\nby a pure table builder in eq/libs/_display.py.\n\n- eq [-n] [-c] [-s]: the worn table, each location coloured. Empty\n  optional slots are hidden, and shield and hold are hidden while a\n  second weapon is wielded.\n- inv [container] [-n] [-c] [-s] [-g]: the flag, level, serial and score\n  columns, identical items grouped as (  n) with the serial \"Many\".\n  Inventory adds the keyring count line and the vault count lines; the\n  vault shows \"not been refreshed\" until it is read. Container names\n  match in any case, and inv Worn shows the worn table.\n- EqState.vault_read records that the vault was read, so a character\n  with no vault sees an empty vault rather than \"not refreshed\".\n- Score shows \"Unkn\" unless identify merged one into the item.\n\nOld bugs fixed (vault counts compared as strings, a Python 2 print, a\nrefresh command that never existed in the unread-vault message, @x with\nno digits, the rule line never resetting its colour, debug output on\nevery run) are listed in docs/plugins/eq.md, and its \"Not ported yet\"\nsection is gone.\n\nAddresses #97\n\n\nClaude-Session: https://claude.ai/code/session_01NXu1sbBxFsEQW16MiZv7Je\n\nCo-authored-by: Claude Opus 5.5 <noreply@anthropic.com>",
          "timestamp": "2026-11-24T10:24:27Z",
          "tree_id": "74661b7c7b1bab1e9eca096eea8124f3e33d87d1",
          "url": "https://github.com/endavis/bastproxy-aardwolf/commit/64881c0033b90abbe4b79e16563717902446ecbd"
        },
        "date": 1795515910629,
        "tool": "pytest",
        "benches": [
          {
            "name": "tests/benchmarks/test_bench_aardu.py::test_bench_convert_level",
            "value": 6018609.132317903,
            "unit": "iter/sec",
            "range": "stddev: 2.1209424455998233e-8",
            "extra": "mean: 166.15134460723442 nsec\nrounds: 61676"
          },
          {
            "name": "tests/benchmarks/test_bench_aardu.py::test_bench_parse_damage_line",
            "value": 305489.6887847351,
            "unit": "iter/sec",
            "range": "stddev: 4.05902698101771e-7",
            "extra": "mean: 3.273432906943891 usec\nrounds: 158228"
          }
        ]
      }
    ]
  }
}