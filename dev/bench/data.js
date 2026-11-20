window.BENCHMARK_DATA = {
  "lastUpdate": 1795182071432,
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
      }
    ]
  }
}