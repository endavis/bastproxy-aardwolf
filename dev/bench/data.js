window.BENCHMARK_DATA = {
  "lastUpdate": 1795771849125,
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
          "id": "1e9604b0cfdaf7255478ea2fea14011481eed3bd",
          "message": "feat: port the iceage plugin (merges PR #102, addresses #84)\n\nPort plugins/aardwolf/iceage.py from the old bastproxy as\nplugins.aardwolf.iceage. Two triggers match the Ice Age and reboot\ncountdown lines and raise ev_plugins.aardwolf.iceage_iceage and\nev_plugins.aardwolf.iceage_reboot, each carrying the minutes left.\n\nOld bugs fixed: the events dropped the captured minutes, the reboot\nminutes were group 2 behind an optional group, and \\d* matched an empty\nnumber. Each change is listed in docs/plugins/iceage.md.\n\nAddresses #84\n\n\nClaude-Session: https://claude.ai/code/session_01NXu1sbBxFsEQW16MiZv7Je\n\nCo-authored-by: Claude Opus 5.5 <noreply@anthropic.com>",
          "timestamp": "2026-11-24T10:36:25Z",
          "tree_id": "b971416eafd82d4b7c5ae6b600218851c7ff8edb",
          "url": "https://github.com/endavis/bastproxy-aardwolf/commit/1e9604b0cfdaf7255478ea2fea14011481eed3bd"
        },
        "date": 1795516628109,
        "tool": "pytest",
        "benches": [
          {
            "name": "tests/benchmarks/test_bench_aardu.py::test_bench_convert_level",
            "value": 3838441.057811573,
            "unit": "iter/sec",
            "range": "stddev: 3.168641191654072e-8",
            "extra": "mean: 260.5224321381489 nsec\nrounds: 198492"
          },
          {
            "name": "tests/benchmarks/test_bench_aardu.py::test_bench_parse_damage_line",
            "value": 222191.11040105752,
            "unit": "iter/sec",
            "range": "stddev: 5.550405666316463e-7",
            "extra": "mean: 4.500630102594962 usec\nrounds: 114917"
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
          "id": "9f7784ca49f93e9e53575270c6f6f04356fae813",
          "message": "feat: port the idle plugin (merges PR #103, addresses #86)\n\nAdd plugins.aardwolf.idle: when Aardwolf says \"Your eyes glaze over.\"\nthe plugin sends look so an idle character is not disconnected.\n\nChanges from the old plugin: the regex escapes the dot, the trigger\nevent is event_t_plugins.aardwolf.idle_glaze, and look goes straight to\nthe mud instead of through proxy command processing. The look output\nstays visible, as before.\n\nAddresses #86\n\n\nClaude-Session: https://claude.ai/code/session_01NXu1sbBxFsEQW16MiZv7Je\n\nCo-authored-by: Claude Opus 5.5 <noreply@anthropic.com>",
          "timestamp": "2026-11-24T10:41:46Z",
          "tree_id": "19cdace4bf9f55cea6ebaf5425e313b68fabb51e",
          "url": "https://github.com/endavis/bastproxy-aardwolf/commit/9f7784ca49f93e9e53575270c6f6f04356fae813"
        },
        "date": 1795516943885,
        "tool": "pytest",
        "benches": [
          {
            "name": "tests/benchmarks/test_bench_aardu.py::test_bench_convert_level",
            "value": 3094657.315872542,
            "unit": "iter/sec",
            "range": "stddev: 4.432294131675068e-8",
            "extra": "mean: 323.1375554478958 nsec\nrounds: 189394"
          },
          {
            "name": "tests/benchmarks/test_bench_aardu.py::test_bench_parse_damage_line",
            "value": 171023.45149457856,
            "unit": "iter/sec",
            "range": "stddev: 0.0000011368578321724597",
            "extra": "mean: 5.847151319079185 usec\nrounds: 180506"
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
          "id": "919659507e87923858a2a7c5535ae22ee2549b7f",
          "message": "feat: port the aarch plugin (merges PR #104, addresses #77)\n\n* feat: migrate the aarch plugin from the old bastproxy\n\nAdd plugins.aardwolf.aarch with the need [filter] command, which counts the\nAarchaeology items and pamphlets in eq's cache and lists the pieces still\nneeded. It reaches eq only through the item.find.by.name API.\n\nFixes old bugs: case-sensitive filter, pamphlet parse crash, misleading\nheader with a filter, silent unknown names, fragile name matching, the\nAarcheology spelling and the single-word filter. Each change is listed in\ndocs/plugins/aarch.md.\n\nAddresses #77\n\nCo-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>\nClaude-Session: https://claude.ai/code/session_01NXu1sbBxFsEQW16MiZv7Je\n\n* docs: record that Aardwolf's help confirms the aarch piece table\n\nhelp aarchaeology-rewards on a live character lists each piece with its\npamphlet number. The 50 names match the plugin's table and pamphlet #N\nis piece N, so the docs no longer ask the maintainer to confirm it.\n\nBatched in the PR for #77.\n\nAddresses #77\n\nCo-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>\nClaude-Session: https://claude.ai/code/session_01NXu1sbBxFsEQW16MiZv7Je\n\n---------\n\nCo-authored-by: Claude Opus 5.5 <noreply@anthropic.com>",
          "timestamp": "2026-11-24T11:00:01Z",
          "tree_id": "04b7e45e44c4baee39433eba7bd4e47271526f8e",
          "url": "https://github.com/endavis/bastproxy-aardwolf/commit/919659507e87923858a2a7c5535ae22ee2549b7f"
        },
        "date": 1795518032428,
        "tool": "pytest",
        "benches": [
          {
            "name": "tests/benchmarks/test_bench_aardu.py::test_bench_convert_level",
            "value": 6138484.191707684,
            "unit": "iter/sec",
            "range": "stddev: 1.0794515174210132e-8",
            "extra": "mean: 162.90666698317372 nsec\nrounds: 63168"
          },
          {
            "name": "tests/benchmarks/test_bench_aardu.py::test_bench_parse_damage_line",
            "value": 312528.9756418348,
            "unit": "iter/sec",
            "range": "stddev: 2.8292104096290346e-7",
            "extra": "mean: 3.1997033169366746 usec\nrounds: 160540"
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
          "id": "9df7bc4ab58b5c7d3492543e5ce2ec613f296496",
          "message": "feat: port the daily plugin (merges PR #105, addresses #83)\n\n* feat: port the daily plugin\n\nAdd plugins.aardwolf.daily: raises ev_plugins.aardwolf.daily_available\nwhen the daily blessing can be received, arms a one-time timer from the\nwait line, and adds the next command. Fixes old bugs (unescaped dots,\nempty numbers, shape-locked wait regexes, stale next time, zero-second\ntimer, unguarded timer removal, check without an active character).\n\nAddresses #83\n\nCo-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>\nClaude-Session: https://claude.ai/code/session_01NXu1sbBxFsEQW16MiZv7Je\n\n* docs: record the daily reply seen on a live character\n\nOn a live character, daily answered with the time of the last blessing\nand \"You can receive a new daily blessing in 56 minutes and 47 seconds.\"\nThe wait line matched and next showed the right time. The docs show that\nreply and say which lines are still unseen.\n\nBatched in the PR for #83.\n\nAddresses #83\n\nCo-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>\nClaude-Session: https://claude.ai/code/session_01NXu1sbBxFsEQW16MiZv7Je\n\n---------\n\nCo-authored-by: Claude Opus 5.5 <noreply@anthropic.com>",
          "timestamp": "2026-11-24T11:27:32Z",
          "tree_id": "002b1f348bd212db53015cff1adf6f4929c4ea92",
          "url": "https://github.com/endavis/bastproxy-aardwolf/commit/9df7bc4ab58b5c7d3492543e5ce2ec613f296496"
        },
        "date": 1795519693072,
        "tool": "pytest",
        "benches": [
          {
            "name": "tests/benchmarks/test_bench_aardu.py::test_bench_convert_level",
            "value": 3035354.032649955,
            "unit": "iter/sec",
            "range": "stddev: 4.725931273541471e-8",
            "extra": "mean: 329.450861165928 nsec\nrounds: 198060"
          },
          {
            "name": "tests/benchmarks/test_bench_aardu.py::test_bench_parse_damage_line",
            "value": 170610.71758761996,
            "unit": "iter/sec",
            "range": "stddev: 0.000001108339166496714",
            "extra": "mean: 5.861296489104991 usec\nrounds: 177305"
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
          "id": "2e3ba79d0a9ed5677fa64f87d1aa7fda173c3ea1",
          "message": "feat: port the afk plugin (merges PR #106, addresses #87)\n\n* feat: migrate the afk plugin from the old bastproxy\n\nAdd plugins.aardwolf.afk. When the last client that can play leaves, it\nsets an AFK title and keeps tells received over GMCP comm.channel; when a\nclient logs in it restores the user's title and reports the queued tells.\nCommands: show, clear, toggle. The title sends are hidden queued mudcmds.\nOld bugs and changes are listed in docs/plugins/afk.md.\n\nAddresses #87\n\nCo-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>\nClaude-Session: https://claude.ai/code/session_01NXu1sbBxFsEQW16MiZv7Je\n\n* fix: restore an empty title when afk ends\n\nA live check found that a character with no title kept the AFK title\nafter AFK ended: the plugin skips an empty remembered title (so it\nnever sends a bare \"title \"), and it only learned the title from titles\ntyped through the proxy.\n\nWhen AFK turns on, the plugin now reads the current title with a hidden\nqueued \"title\" (\"Your title is: <title>\", empty for no title), then sets\nthe AFK title. When AFK ends it sends \"title <title>\", or \"title clear\"\nwhen the title was empty or the read timed out. \"Your title is\ncleared.\" finishes the queued command. The texts were captured on a\nlive character and are marked confirmed in docs/plugins/afk.md.\n\nBatched in the PR for #87.\n\nAddresses #87\n\nCo-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>\nClaude-Session: https://claude.ai/code/session_01NXu1sbBxFsEQW16MiZv7Je\n\n---------\n\nCo-authored-by: Claude Opus 5.5 <noreply@anthropic.com>",
          "timestamp": "2026-11-24T11:34:37Z",
          "tree_id": "ba499bdfd91ea70e72bade652adfc3b7258faf8b",
          "url": "https://github.com/endavis/bastproxy-aardwolf/commit/2e3ba79d0a9ed5677fa64f87d1aa7fda173c3ea1"
        },
        "date": 1795520107858,
        "tool": "pytest",
        "benches": [
          {
            "name": "tests/benchmarks/test_bench_aardu.py::test_bench_convert_level",
            "value": 5980566.105031691,
            "unit": "iter/sec",
            "range": "stddev: 3.2593874108319334e-8",
            "extra": "mean: 167.20825126548803 nsec\nrounds: 60478"
          },
          {
            "name": "tests/benchmarks/test_bench_aardu.py::test_bench_parse_damage_line",
            "value": 304398.30444988766,
            "unit": "iter/sec",
            "range": "stddev: 3.494262796269184e-7",
            "extra": "mean: 3.285169415799514 usec\nrounds: 159262"
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
          "id": "4ac1f838538312e59a8461450c35f6996c78b326",
          "message": "feat: port the aflags plugin (merges PR #107, addresses #79)\n\n* feat: port the aflags plugin\n\nKeep the character's affect flags from a hidden queued `aflags`, refresh\nthem when the skills plugin reports an affect change, and raise\nev_plugins.aardwolf.aflags_diff with the flags added and removed. Adds\nthe flag.check API and the refresh, check and list commands, tests, and\ndocs/plugins/aflags.md with the old bugs fixed.\n\nAddresses #79\n\nCo-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>\nClaude-Session: https://claude.ai/code/session_01NXu1sbBxFsEQW16MiZv7Je\n\n* docs: record the aflags output seen on a live character\n\nA live character with one affect answered a queued aflags with\n\"Affect Flags: detecthidden\", two blank lines and the prompt, and the\nproxy hid all of it from the client. The docs now show that output and\nkeep only the long-list wrapping and the no-flags output as unconfirmed.\n\nBatched in the PR for #79.\n\nAddresses #79\n\nCo-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>\nClaude-Session: https://claude.ai/code/session_01NXu1sbBxFsEQW16MiZv7Je\n\n---------\n\nCo-authored-by: Claude Opus 5.5 <noreply@anthropic.com>",
          "timestamp": "2026-11-24T11:41:32Z",
          "tree_id": "98597ed647db7175f4ee5657261afeabb0c4c5c5",
          "url": "https://github.com/endavis/bastproxy-aardwolf/commit/4ac1f838538312e59a8461450c35f6996c78b326"
        },
        "date": 1795520530882,
        "tool": "pytest",
        "benches": [
          {
            "name": "tests/benchmarks/test_bench_aardu.py::test_bench_convert_level",
            "value": 3853077.053896249,
            "unit": "iter/sec",
            "range": "stddev: 3.419018495112964e-8",
            "extra": "mean: 259.53283207476875 nsec\nrounds: 193874"
          },
          {
            "name": "tests/benchmarks/test_bench_aardu.py::test_bench_parse_damage_line",
            "value": 222393.53469597964,
            "unit": "iter/sec",
            "range": "stddev: 4.947378266222987e-7",
            "extra": "mean: 4.496533594679529 usec\nrounds: 115301"
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
          "id": "9ebcfc5543f13b4cf568c227b7bb04052b80f4e2",
          "message": "feat: port the ct plugin (merges PR #108, addresses #81)\n\n* feat: port the ct plugin\n\nAdd plugins.aardwolf.ct, the combat tracker of the old bastproxy. After each\nmob kill it queues a table of the damage done by damage type, with hits,\nmisses, time and xp, and shows it on the next empty line. It listens to the\nmobk kill event and imports no other plugin.\n\nThe port fixes the Python 2 only key sort and integer division, the error on\na kill with no damage, a dead key skip, and unescaped mob names.\n\nAddresses #81\n\nCo-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>\nClaude-Session: https://claude.ai/code/session_01NXu1sbBxFsEQW16MiZv7Je\n\n* fix: count critical hits in mobk's damage\n\nAardwolf marks a critical hit with a leading \"*\":\n\"*Your stab ERADICATES a lazy pupil. [40]\". mobk's damage triggers were\nanchored on \"^Your \" and \"^[n] Your \", so a crit never reached the\nkill's damage, and on a live character ct printed an empty table for a\nkill whose only hit was a crit. aardu.parse_damage_line also kept the\n\"*\" in the damage type (\"*Your stab\").\n\nBoth triggers now accept an optional \"*\" before the hits bracket or\nbefore \"Your\", and parse_damage_line strips it. Tested with the two\nlines captured live.\n\nBatched in the PR for #81, whose ct port showed the gap.\n\nAddresses #81\n\nCo-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>\nClaude-Session: https://claude.ai/code/session_01NXu1sbBxFsEQW16MiZv7Je\n\n---------\n\nCo-authored-by: Claude Opus 5.5 <noreply@anthropic.com>",
          "timestamp": "2026-11-24T13:10:51Z",
          "tree_id": "55f274164d54ac5c21f69a9c8b2bd5afe4dd68ed",
          "url": "https://github.com/endavis/bastproxy-aardwolf/commit/9ebcfc5543f13b4cf568c227b7bb04052b80f4e2"
        },
        "date": 1795525886220,
        "tool": "pytest",
        "benches": [
          {
            "name": "tests/benchmarks/test_bench_aardu.py::test_bench_convert_level",
            "value": 3144820.323990414,
            "unit": "iter/sec",
            "range": "stddev: 5.172583751537467e-8",
            "extra": "mean: 317.9831904453974 nsec\nrounds: 192716"
          },
          {
            "name": "tests/benchmarks/test_bench_aardu.py::test_bench_parse_damage_line",
            "value": 168735.4783501897,
            "unit": "iter/sec",
            "range": "stddev: 8.71174062015769e-7",
            "extra": "mean: 5.926435920752975 usec\nrounds: 176679"
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
          "id": "55b9bce81c94b62d3f8927b8a0abeceea3e76d1c",
          "message": "feat: migrate the statmn plugin from the old bastproxy (merges PR #109, addresses #82)\n\n* feat: migrate the statmn plugin from the old bastproxy\n\nAdd plugins.aardwolf.statmn: totals of quests, campaigns, global quests\nand mob kills over a recent window, read through the statdb stats.select\nAPI, plus a one-line message for each quest, campaign, gquest and level\ncompletion. Port of the old plugin on the new core APIs and events; ten\nold bugs are fixed and listed in docs/plugins/statmn.md.\n\nAddresses #82\n\nCo-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>\nClaude-Session: https://claude.ai/code/session_01NXu1sbBxFsEQW16MiZv7Je\n\n* fix: keep the statmn timed report off by default\n\nThe port started the report timer at load with the 5-minute default, so\na StatMonitor report would print every 5 minutes. In the old plugin the\ntimer only started after \"show\" was changed, so in practice no timed\nreport appeared. The maintainer chose to keep it off: \"show\" now\ndefaults to 0, a saved non-zero value still starts the timer at load,\nand \"rep\" is unchanged.\n\nAddresses #82\n\nCo-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>\nClaude-Session: https://claude.ai/code/session_01NXu1sbBxFsEQW16MiZv7Je\n\n---------\n\nCo-authored-by: Claude Opus 5.5 <noreply@anthropic.com>",
          "timestamp": "2026-11-24T13:14:46Z",
          "tree_id": "0fd048180f6298357716084ab3601f2d294e2436",
          "url": "https://github.com/endavis/bastproxy-aardwolf/commit/55b9bce81c94b62d3f8927b8a0abeceea3e76d1c"
        },
        "date": 1795526122371,
        "tool": "pytest",
        "benches": [
          {
            "name": "tests/benchmarks/test_bench_aardu.py::test_bench_convert_level",
            "value": 3055368.590786986,
            "unit": "iter/sec",
            "range": "stddev: 4.237109555770339e-8",
            "extra": "mean: 327.2927538154816 nsec\nrounds: 196117"
          },
          {
            "name": "tests/benchmarks/test_bench_aardu.py::test_bench_parse_damage_line",
            "value": 174538.22234095426,
            "unit": "iter/sec",
            "range": "stddev: 0.0000010572505693739915",
            "extra": "mean: 5.729404061687619 usec\nrounds: 178891"
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
          "id": "c1cfdb778125967a2de2917226ef84b2fe6715e7",
          "message": "feat: port the su plugin (merges PR #110, addresses #80)\n\n* feat: port the su plugin\n\nAdd plugins.aardwolf.su, which recasts the spellups in its list when\nthey wear off. It casts only while enabled (default on, as in the old\nplugin), connected, with an active character in GMCP state 3 and the\nskills up to date, and never while a cast is pending, the room is\nnocast or mana or moves ran out. It reaches skills and move through\ntheir APIs and events only.\n\nOld bugs fixed and listed in docs/plugins/su.md: rem all returned\nnothing and never saved, nomoves recorded the mana, a cast with no\nreply stopped casting for good, transient state was saved in settings,\nen and dis never synced, and a few messages and loops.\n\nAddresses #80\n\nCo-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>\nClaude-Session: https://claude.ai/code/session_01NXu1sbBxFsEQW16MiZv7Je\n\n* docs: record the su texts confirmed on a real character\n\nA live check on Aardwolf with Underwater breathing (sn 333) confirmed\n\"cast 333\", \"{sfail}333,0,1,-1\" for a lost concentration (the plugin\ncast again) and \"{affon}333,300\" when the spell took hold (the wait\nended and the list showed it affecting). The other tags, fail codes 2\nto 12 and the char.vitals keys stay listed as unconfirmed.\n\nAddresses #80\n\nCo-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>\nClaude-Session: https://claude.ai/code/session_01NXu1sbBxFsEQW16MiZv7Je\n\n---------\n\nCo-authored-by: Claude Opus 5.5 <noreply@anthropic.com>",
          "timestamp": "2026-11-24T13:26:10Z",
          "tree_id": "0bb1c547f715f97c6ca38ed291734964e1963c8d",
          "url": "https://github.com/endavis/bastproxy-aardwolf/commit/c1cfdb778125967a2de2917226ef84b2fe6715e7"
        },
        "date": 1795526827329,
        "tool": "pytest",
        "benches": [
          {
            "name": "tests/benchmarks/test_bench_aardu.py::test_bench_convert_level",
            "value": 5086685.127333821,
            "unit": "iter/sec",
            "range": "stddev: 1.6238239411673173e-8",
            "extra": "mean: 196.59168495144277 nsec\nrounds: 53141"
          },
          {
            "name": "tests/benchmarks/test_bench_aardu.py::test_bench_parse_damage_line",
            "value": 266149.9015845512,
            "unit": "iter/sec",
            "range": "stddev: 5.130550839181077e-7",
            "extra": "mean: 3.7572811188221213 usec\nrounds: 141024"
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
          "id": "9a7d1950b0e41ba3ba38710b74b13e674a659af9",
          "message": "chore: update the bastproxy core pin in uv.lock (merges PR #113, addresses #111)\n\nMove the bastproxy pin from a55e622a to 9acaff5e, which sends plugin\noutput after the MUD packet that triggered it (endavis/bastproxy#747).\nOnly the bastproxy entry in uv.lock changes.\n\nAddresses #111\n\n\nClaude-Session: https://claude.ai/code/session_01NXu1sbBxFsEQW16MiZv7Je\n\nCo-authored-by: Claude Opus 5.5 <noreply@anthropic.com>",
          "timestamp": "2026-11-24T13:44:47Z",
          "tree_id": "cf52608ee5c6d295cfa2da2a8a0a82510e4a5933",
          "url": "https://github.com/endavis/bastproxy-aardwolf/commit/9a7d1950b0e41ba3ba38710b74b13e674a659af9"
        },
        "date": 1795527923580,
        "tool": "pytest",
        "benches": [
          {
            "name": "tests/benchmarks/test_bench_aardu.py::test_bench_convert_level",
            "value": 6011541.602817084,
            "unit": "iter/sec",
            "range": "stddev: 1.9140042647945676e-8",
            "extra": "mean: 166.34668211085614 nsec\nrounds: 61943"
          },
          {
            "name": "tests/benchmarks/test_bench_aardu.py::test_bench_parse_damage_line",
            "value": 298863.7890815225,
            "unit": "iter/sec",
            "range": "stddev: 6.748406523082505e-7",
            "extra": "mean: 3.346005894769758 usec\nrounds: 157258"
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
          "id": "3477b8441b3a402e8d6f58bc114c0b513b57a528",
          "message": "refactor: rename the shared libs package to _libs (merges PR #114, addresses #112)\n\nRename src/aardwolf/libs (aardu, itemu) to src/aardwolf/_libs so the\nleading underscore marks it as not a plugin and it no longer shares a\nname with each plugin's own libs/ subpackage. Per-plugin libs/ packages\nare unchanged. Imports, tests and docs updated. No behaviour change.\n\nAddresses #112\n\n\nClaude-Session: https://claude.ai/code/session_01NXu1sbBxFsEQW16MiZv7Je\n\nCo-authored-by: Claude Opus 5.5 <noreply@anthropic.com>",
          "timestamp": "2026-11-24T13:54:11Z",
          "tree_id": "d2052b482fec139712f7b038950102419bc73968",
          "url": "https://github.com/endavis/bastproxy-aardwolf/commit/3477b8441b3a402e8d6f58bc114c0b513b57a528"
        },
        "date": 1795528489853,
        "tool": "pytest",
        "benches": [
          {
            "name": "tests/benchmarks/test_bench_aardu.py::test_bench_convert_level",
            "value": 5020017.401193957,
            "unit": "iter/sec",
            "range": "stddev: 1.588063669818752e-8",
            "extra": "mean: 199.2024967407804 nsec\nrounds: 52925"
          },
          {
            "name": "tests/benchmarks/test_bench_aardu.py::test_bench_parse_damage_line",
            "value": 264757.9735673069,
            "unit": "iter/sec",
            "range": "stddev: 9.312751778844442e-7",
            "extra": "mean: 3.7770344988147437 usec\nrounds: 141744"
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
          "id": "e5554dcc401fe1b138625cabb63c556b2924a8c4",
          "message": "chore: synchronize with pyproject-template f641847 (merges PR #116, addresses #115)\n\n* chore: synchronize with pyproject-template 62ef0c9\n\nSyncs from 1494b03 to 62ef0c9. Syncs the following template improvements:\n- endavis/pyproject-template#1270 (project name and repo URLs built from the PyPI and repo names when configuring)\n- endavis/pyproject-template#1271, #1276 (documented-path checks)\n- endavis/pyproject-template#1273, #1277 (mutmut config checks for files mutmut does not copy)\n- endavis/pyproject-template#1279 (test_docs_dev_sync scans committed markdown only)\n- endavis/pyproject-template#1281, #1310 (branch checks judged where git runs, following only an unconditional cd chain)\n- endavis/pyproject-template#1286 (portable-tests rule)\n- endavis/pyproject-template#1289 (doit stdout and stderr in UTF-8)\n- endavis/pyproject-template#1290 (.gitattributes with LF line endings)\n- endavis/pyproject-template#1294 (test git fixtures isolated from global config)\n- endavis/pyproject-template#1295, #1296, #1309 (doit guard without a POSIX shell, Windows CI doit steps)\n- endavis/pyproject-template#1298 (publish token via UV_PUBLISH_TOKEN)\n- endavis/pyproject-template#1300, #1303, #1304, #1307 (shipped tooling type-clean under variant mypy configs)\n\nThe aardwolf names are kept in the merged files. Dev-dependency floors\nraised to the template's (ruff, pymdown-extensions, types-pyyaml) and\nuv.lock relocked (specifiers only).\n\nAddresses #115\n\nCo-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>\nClaude-Session: https://claude.ai/code/session_01NXu1sbBxFsEQW16MiZv7Je\n\n* chore: synchronize with pyproject-template f641847\n\nMoves the sync point from 62ef0c9 to f641847 for\nendavis/pyproject-template#1312: the protected-branch merge check judges\nevery merge in a command. The hook and its test are taken as is.\n\nAddresses #115\n\nCo-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>\nClaude-Session: https://claude.ai/code/session_01NXu1sbBxFsEQW16MiZv7Je\n\n---------\n\nCo-authored-by: Claude Opus 5.5 <noreply@anthropic.com>",
          "timestamp": "2026-11-24T18:39:22Z",
          "tree_id": "ddfd9f654b85c27bc8a80b83ba82dd5e4c043bb5",
          "url": "https://github.com/endavis/bastproxy-aardwolf/commit/e5554dcc401fe1b138625cabb63c556b2924a8c4"
        },
        "date": 1795545600435,
        "tool": "pytest",
        "benches": [
          {
            "name": "tests/benchmarks/test_bench_aardu.py::test_bench_convert_level",
            "value": 2525031.393563663,
            "unit": "iter/sec",
            "range": "stddev: 4.7025571175536507e-8",
            "extra": "mean: 396.0346800237861 nsec\nrounds: 177905"
          },
          {
            "name": "tests/benchmarks/test_bench_aardu.py::test_bench_parse_damage_line",
            "value": 164940.66835962987,
            "unit": "iter/sec",
            "range": "stddev: 0.000001433985805374138",
            "extra": "mean: 6.062786151803636 usec\nrounds: 174521"
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
          "id": "6aaa4e2119b508c4cd807eba9ddc6fec900860fb",
          "message": "feat: add the Aardwolf mapper adapter (merges PR #122, addresses #118)\n\n* chore: update the bastproxy core pin in uv.lock\n\nMove the bastproxy pin from 9acaff5e to 02fd7e92. That commit adds the\ncore mapper plugins.client.mapper (endavis/bastproxy#755 and #757), and\nalso brings the startup gc freeze (endavis/bastproxy#759). Only the\nbastproxy entry in uv.lock changes.\n\nAddresses #118\n\nCo-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>\nClaude-Session: https://claude.ai/code/session_01NXu1sbBxFsEQW16MiZv7Je\n\n* feat: add the Aardwolf mapper adapter\n\nAdd plugins.aardwolf.mapper. It feeds the core mapper\n(plugins.client.mapper) only through its APIs and events.\n\n- Rooms: GMCP room.info becomes room.add (with the exits) and\n  room.current.set, on the move plugin's room-change event. The first\n  room after a load or a reconnect comes from the GMCP cache or the\n  first room.info.\n- Areas: an unknown area is requested with \"request area\" once per\n  connection, and the room.area reply goes to area.add.\n- Flags: noportal and norecall come from \"Magic walls bounce you back.\"\n  and \"You cannot recall/return home from this room.\", and the room's\n  exits are kept.\n- Requirements: a {\"level\", \"tier\"} requirement is checked against GMCP\n  char.status.level and char.base.tier. Portals and recalls use\n  level + 10 * tier, as the old mapper did.\n- Movement: runs of plain directions become one \"run 3n2e\" speedwalk,\n  a single direction is sent bare, and any other exit is sent as-is.\n- Mismatch: room_mismatch is reported to the client with what changed\n  and the purge command to use.\n\nDocs are in docs/plugins/mapper.md, with an index row, a nav entry and\nthe regenerated table of contents. The new tests are added to the\nmutmut test selection.\n\nAddresses #118\n\nCo-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>\nClaude-Session: https://claude.ai/code/session_01NXu1sbBxFsEQW16MiZv7Je\n\n---------\n\nCo-authored-by: Claude Opus 5.5 <noreply@anthropic.com>",
          "timestamp": "2026-11-24T23:07:06Z",
          "tree_id": "6a532288d1332d85449034b000a0d8ba43ae47ce",
          "url": "https://github.com/endavis/bastproxy-aardwolf/commit/6aaa4e2119b508c4cd807eba9ddc6fec900860fb"
        },
        "date": 1795561693666,
        "tool": "pytest",
        "benches": [
          {
            "name": "tests/benchmarks/test_bench_aardu.py::test_bench_convert_level",
            "value": 5093614.22866538,
            "unit": "iter/sec",
            "range": "stddev: 1.7411887546529826e-8",
            "extra": "mean: 196.3242513287109 nsec\nrounds: 55879"
          },
          {
            "name": "tests/benchmarks/test_bench_aardu.py::test_bench_parse_damage_line",
            "value": 247040.12458185497,
            "unit": "iter/sec",
            "range": "stddev: 6.002918784616196e-7",
            "extra": "mean: 4.047925419777941 usec\nrounds: 147995"
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
          "id": "5e5753b3b7a67b9464427e68da02ad438a944bd2",
          "message": "feat: import a MUSHclient Aardwolf.db and add the Aardwolf map searches (merges PR #123, addresses #119)\n\n* feat: import a MUSHclient Aardwolf.db and add the Aardwolf map searches\n\nAdd to plugins.aardwolf.mapper:\n\n- importmush <path>: copies a MUSHclient Aardwolf.db into the core map\n  through the plugins.client.mapper APIs.\n  - Path: absolute or starting with ~, and must be a file.\n  - Reading: the database is opened read-only (mode=ro) in a worker\n    thread and checked for the MUSH tables and columns before anything\n    is written. Older schemas without noportal/norecall, exit levels or\n    bookmarks are read too.\n  - Writing: writes run on the event loop in short time slices with\n    progress lines. One import runs at a time, and it stops if the\n    plugin unloads.\n  - Captured data wins and the import only fills gaps, so importing the\n    same file again writes nothing.\n  - Mapping: MUSH info becomes the room details the adapter already\n    stores. noportal and norecall become flags. Exit levels become\n    {\"level\": n} requirements. Portals and recall (* and **) carry over,\n    and bookmarks become notes.\n  - Not imported: nomap rooms, orphan exits, storage, environments.\n- shops, train, quest and notes [here|<area>]: list the rooms whose\n  details hold shop/bank, trainer or questor, or that have a note. They\n  work on imported and captured rooms alike.\n\nThe MUSH reader uses fixed SELECT * queries and reads optional columns\nby name, so no SQL is built from strings. Docs are in\ndocs/plugins/mapper.md. The new tests (a made-up fixture DB built in\ntmp_path) are in the mutmut selection.\n\nAddresses #119\n\nCo-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>\nClaude-Session: https://claude.ai/code/session_01NXu1sbBxFsEQW16MiZv7Je\n\n* test: keep the special-character import path valid on Windows\n\nWindows does not allow ? in a file name, so the path test left the\nWindows CI job failing with WinError 123. The folder name now uses\n#, % and a space on every platform, and adds ? only off Windows.\n\nAddresses #119\n\nCo-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>\nClaude-Session: https://claude.ai/code/session_01NXu1sbBxFsEQW16MiZv7Je\n\n---------\n\nCo-authored-by: Claude Opus 5.5 <noreply@anthropic.com>",
          "timestamp": "2026-11-24T23:30:09Z",
          "tree_id": "ac4512579d4b4a8fa52bf0d6c6a99546f06cde16",
          "url": "https://github.com/endavis/bastproxy-aardwolf/commit/5e5753b3b7a67b9464427e68da02ad438a944bd2"
        },
        "date": 1795563049928,
        "tool": "pytest",
        "benches": [
          {
            "name": "tests/benchmarks/test_bench_aardu.py::test_bench_convert_level",
            "value": 5437603.810485782,
            "unit": "iter/sec",
            "range": "stddev: 9.9699775295395e-8",
            "extra": "mean: 183.90453494820954 nsec\nrounds: 59015"
          },
          {
            "name": "tests/benchmarks/test_bench_aardu.py::test_bench_parse_damage_line",
            "value": 295251.92192725826,
            "unit": "iter/sec",
            "range": "stddev: 4.610375519481757e-7",
            "extra": "mean: 3.3869381559737035 usec\nrounds: 152440"
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
          "id": "ae1cdbc5bc547eeef8b115ffb1eaaec573658b2c",
          "message": "feat: add Aardwolf custom exits, portals and exit locks to the mapper (merges PR #125, addresses #120)\n\n* feat: add Aardwolf custom exits, portals and exit locks to the mapper\n\nAdd to plugins.aardwolf.mapper:\n\n- Custom exits:\n  - cexit <command> records an exit from the current room. It sends the\n    command and stores the exit when the next room arrives, or times\n    out. With -t, it stores the exit directly without sending anything.\n  - cexits lists them, cexitdel deletes them, and cexitpurge removes\n    them for an area or everywhere (it needs -c).\n  - A command may hold several steps separated by \";\" and wait(N)\n    pauses, as MUSHclient writes them.\n- Exit locks: lockexit shows or sets a {\"level\": n} requirement on any\n  existing exit, plain or custom. Level 0 removes the lock.\n- Portals: portal adds a \"*\" exit to a room with a level. Recall-type\n  commands (recall, home) and -r go under \"**\". portals lists them,\n  portalchange, portallevel and portalrecall edit one by number or\n  command, portaldel deletes one, and portalpurge removes them all.\n- Movement: a step whose command holds \";\" or wait(N) is split. The\n  first chunk goes back to the core, and the rest is sent after the\n  delays. A new move, a stopped or failed walk, disconnect or unload\n  cancels what is still waiting.\n- Bounce portal and bounce recall need no commands. The core path\n  search already chains a recall and a portal from noportal and\n  norecall rooms. Path tests over a test map with the real core\n  pathfinder cover both, plus locks and custom exits.\n\nDocs are in docs/plugins/mapper.md, and tests/test_mapper_paths.py is\nin the mutmut selection.\n\nAddresses #120\n\nCo-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>\nClaude-Session: https://claude.ai/code/session_01NXu1sbBxFsEQW16MiZv7Je\n\n* chore: update the bastproxy core pin in uv.lock\n\nMove the bastproxy pin from 02fd7e92 to 80693576. That adds the batched\nmap write (endavis/bastproxy#761) and the fix that keeps an exit's\nrequirement and cost when its room is recaptured (endavis/bastproxy#763).\nWithout the fix, a lockexit lock or an imported level is lost the next\ntime the character walks through the room. Only the bastproxy entry in\nuv.lock changes.\n\nAddresses #120\n\nCo-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>\nClaude-Session: https://claude.ai/code/session_01NXu1sbBxFsEQW16MiZv7Je\n\n---------\n\nCo-authored-by: Claude Opus 5.5 <noreply@anthropic.com>",
          "timestamp": "2026-11-24T23:55:08Z",
          "tree_id": "b81802f79c048162f1630cfff3ca85928e6f229a",
          "url": "https://github.com/endavis/bastproxy-aardwolf/commit/ae1cdbc5bc547eeef8b115ffb1eaaec573658b2c"
        },
        "date": 1795564546249,
        "tool": "pytest",
        "benches": [
          {
            "name": "tests/benchmarks/test_bench_aardu.py::test_bench_convert_level",
            "value": 3085236.3079401557,
            "unit": "iter/sec",
            "range": "stddev: 4.425691867627412e-8",
            "extra": "mean: 324.1242809915087 nsec\nrounds: 197668"
          },
          {
            "name": "tests/benchmarks/test_bench_aardu.py::test_bench_parse_damage_line",
            "value": 159395.28639356434,
            "unit": "iter/sec",
            "range": "stddev: 0.0000017980758726338821",
            "extra": "mean: 6.2737112409390265 usec\nrounds: 175101"
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
          "id": "842f28ba40b348b5daa4cf9dedbf4fef06b1a962",
          "message": "feat: write the MUSHclient import through the core batch API (merges PR #126, addresses #124)\n\nimportmush wrote every area, room, note and exit with its own core\nmapper call, and each call is its own database transaction. On disk\nthat made a large import take many minutes.\n\nThe import now sends areas, rooms with their notes, and exits to\nmap.batch.add in fill mode (overwrite=False), so captured data still\nwins. Chunks stay within the core row cap, counted as core counts them.\nThe import yields to the event loop and checks for an unload between\nchunks, and reports progress after each chunk. The summary line keeps\nits wording, summed from the batch counts: \"flags added to N stored\"\nis rooms - new_rooms and \"updated\" is exits - new_exits.\n\nexit_update and stored_room_with_flags are removed with their tests;\nthe core fill mode does their merge. With approval, five per-item\ntests (unload, write failure, the two yield tests, progress) are\nrewritten to check the same behaviour per batch.\n\nThe lock moves core to cbfa5bd2 for the new_exits count.\n\nAddresses #124\n\n\nClaude-Session: https://claude.ai/code/session_01NXu1sbBxFsEQW16MiZv7Je\n\nCo-authored-by: Claude Opus 5.5 <noreply@anthropic.com>",
          "timestamp": "2026-11-25T00:18:14Z",
          "tree_id": "142153f96354493088b399889428fd9ce062dd5f",
          "url": "https://github.com/endavis/bastproxy-aardwolf/commit/842f28ba40b348b5daa4cf9dedbf4fef06b1a962"
        },
        "date": 1795565933945,
        "tool": "pytest",
        "benches": [
          {
            "name": "tests/benchmarks/test_bench_aardu.py::test_bench_convert_level",
            "value": 5743145.352247722,
            "unit": "iter/sec",
            "range": "stddev: 3.9057472329187055e-8",
            "extra": "mean: 174.1206148663163 nsec\nrounds: 59330"
          },
          {
            "name": "tests/benchmarks/test_bench_aardu.py::test_bench_parse_damage_line",
            "value": 284153.06256827933,
            "unit": "iter/sec",
            "range": "stddev: 5.140313331069639e-7",
            "extra": "mean: 3.519230062001212 usec\nrounds: 145752"
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
          "id": "a1779738f303962dbfa9b66673100451c901e436",
          "message": "feat: add web pages for statdb: tables and charts (merges PR #129, addresses #128)\n\nfeat: add web pages for statdb tables and charts\n\nstatdb registers 15 routes under /aardwolf/statdb/ through the core web\nserver: a table page for each listing command (milestones, quests,\nlevels, cps, cpmobs, gqs, gqmobs, mobs, mobkills), a comp page, and four\nstatic SVG charts (quest points and gold per day, time per level, kills\nper area). The core server supplies GET-only routing, the session login\nand the 400 for bad table parameters.\n\nQueries are fixed fragments chosen by column name, with values bound,\nand run in asyncio.to_thread on a read-only connection. The text reports\nare split into a stats part and a summary part so the pages reuse them.\nCharts escape every label and contain no script. The core is moved to\nthe web-server commit in uv.lock.\n\nAddresses #128\n\n\nClaude-Session: https://claude.ai/code/session_01NXu1sbBxFsEQW16MiZv7Je\n\nCo-authored-by: Claude Opus 5.5 <noreply@anthropic.com>",
          "timestamp": "2026-11-25T07:35:25Z",
          "tree_id": "e2021e05be7186dda1c86ed3afa494213034b3b9",
          "url": "https://github.com/endavis/bastproxy-aardwolf/commit/a1779738f303962dbfa9b66673100451c901e436"
        },
        "date": 1795592163949,
        "tool": "pytest",
        "benches": [
          {
            "name": "tests/benchmarks/test_bench_aardu.py::test_bench_convert_level",
            "value": 5123895.007556592,
            "unit": "iter/sec",
            "range": "stddev: 1.6453548497398315e-8",
            "extra": "mean: 195.16403020070183 nsec\nrounds: 53377"
          },
          {
            "name": "tests/benchmarks/test_bench_aardu.py::test_bench_parse_damage_line",
            "value": 269308.6809259545,
            "unit": "iter/sec",
            "range": "stddev: 4.855147072000732e-7",
            "extra": "mean: 3.7132111618598236 usec\nrounds: 143390"
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
          "id": "3a6d9f6a16532dd8c182d8cdc20a00975e5604ca",
          "message": "feat: add web pages for the Aardwolf mapper: portals, custom exits and places (merges PR #130, addresses #127)\n\nfeat: add web pages for the Aardwolf mapper\n\nServe the mapper's portals, custom exits (with locked exits) and\nshop, train, quest and note places as sortable, filterable tables\nunder /aardwolf/mapper/, through plugins.core.web:web.route.add.\nEach page builds its rows with the same code as its text command.\nRoom and area cells are link cells to the core mapper pages.\nMove the shared test fakes to tests/mapper_support.py and move\nbastproxy to the core web link-cell release.\n\nAddresses #127\n\n\nClaude-Session: https://claude.ai/code/session_01NXu1sbBxFsEQW16MiZv7Je\n\nCo-authored-by: Claude Opus 5.5 <noreply@anthropic.com>",
          "timestamp": "2026-11-25T07:54:46Z",
          "tree_id": "9fcf4799bbd228c72d6b0c6a65ef7f0d71cab54d",
          "url": "https://github.com/endavis/bastproxy-aardwolf/commit/3a6d9f6a16532dd8c182d8cdc20a00975e5604ca"
        },
        "date": 1795593326465,
        "tool": "pytest",
        "benches": [
          {
            "name": "tests/benchmarks/test_bench_aardu.py::test_bench_convert_level",
            "value": 3098942.6301878477,
            "unit": "iter/sec",
            "range": "stddev: 3.606040747884322e-8",
            "extra": "mean: 322.6907107794323 nsec\nrounds: 189790"
          },
          {
            "name": "tests/benchmarks/test_bench_aardu.py::test_bench_parse_damage_line",
            "value": 174229.95608306368,
            "unit": "iter/sec",
            "range": "stddev: 7.183117884949317e-7",
            "extra": "mean: 5.739541135642901 usec\nrounds: 184366"
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
          "id": "ae3b33a7943791ceef063685f58d5d64b66088de",
          "message": "feat: link statdb web cells and return 404 and 400 from the comp page (merges PR #132, addresses #131)\n\nTable pages now return link cells: quests and levels ids link to the\nsingle-row view, cps and gqs ids to their mob lists, and a mob kill's\nroom to the core mapper's room page. Links are added after the query, so\nsorting, filtering and paging on those columns are unchanged.\n\nThe comp page needs both milestone names (400 otherwise) and returns 404\nfor a name that does not exist. It is registered with listed=False, so\nit stays off the core index; the lock moves core to d055c2a5 for that.\n\nAddresses #131\n\n\nClaude-Session: https://claude.ai/code/session_01NXu1sbBxFsEQW16MiZv7Je\n\nCo-authored-by: Claude Opus 5.5 <noreply@anthropic.com>",
          "timestamp": "2026-11-25T08:53:23Z",
          "tree_id": "6283561bae5d1bc52eb85cd4ccf70d163bcf95b3",
          "url": "https://github.com/endavis/bastproxy-aardwolf/commit/ae3b33a7943791ceef063685f58d5d64b66088de"
        },
        "date": 1795596841201,
        "tool": "pytest",
        "benches": [
          {
            "name": "tests/benchmarks/test_bench_aardu.py::test_bench_convert_level",
            "value": 3037271.328743362,
            "unit": "iter/sec",
            "range": "stddev: 8.252079709849145e-8",
            "extra": "mean: 329.24289329585156 nsec\nrounds: 198413"
          },
          {
            "name": "tests/benchmarks/test_bench_aardu.py::test_bench_parse_damage_line",
            "value": 158817.5940838293,
            "unit": "iter/sec",
            "range": "stddev: 9.479462668934754e-7",
            "extra": "mean: 6.296531601354988 usec\nrounds: 167477"
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
          "id": "a1a8820f1706002327999839ee46d86ebb7784fc",
          "message": "fix: leave NOEXP kills out of XP totals, averages and bonus flags (merges PR #135, addresses #133)\n\nmobk stores a NOEXP kill's would-have XP with noexp=1, but several\nreaders ignored the flag and reported that XP as gained:\n\n- statdb mobs report: XP sums and averages, and the Bonus and Blessing\n  Mobs counts and averages, now count only noexp = 0 kills\n- statdb level report and statmn level message: the kill count and\n  xp/mob average leave NOEXP kills out\n- statmn report: the Mobs XP total leaves NOEXP kills out\n- the text mob list and the web mobs page show no D/E flags on NOEXP rows\n\nKill counts other than those, gold, TP and special kills are unchanged.\nmobk and the schema are unchanged.\n\nAddresses #133\n\n\nClaude-Session: https://claude.ai/code/session_01NXu1sbBxFsEQW16MiZv7Je\n\nCo-authored-by: Claude Opus 5.5 <noreply@anthropic.com>",
          "timestamp": "2026-11-25T09:40:37Z",
          "tree_id": "251c5ebb53595ce029cd4bbab5a23ae0be1902ed",
          "url": "https://github.com/endavis/bastproxy-aardwolf/commit/a1a8820f1706002327999839ee46d86ebb7784fc"
        },
        "date": 1795599673468,
        "tool": "pytest",
        "benches": [
          {
            "name": "tests/benchmarks/test_bench_aardu.py::test_bench_convert_level",
            "value": 2983964.6261628056,
            "unit": "iter/sec",
            "range": "stddev: 4.176929410428085e-8",
            "extra": "mean: 335.12461616743036 nsec\nrounds: 190840"
          },
          {
            "name": "tests/benchmarks/test_bench_aardu.py::test_bench_parse_damage_line",
            "value": 170819.61938067593,
            "unit": "iter/sec",
            "range": "stddev: 0.000001404618734036012",
            "extra": "mean: 5.85412848726395 usec\nrounds: 176679"
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
          "id": "05aa7aab93095ff7f5f54e3c43246875c6d0626c",
          "message": "chore: bump virtualenv in the lock to clear the pip-audit finding (merges PR #141, addresses #140)\n\nuv lock --upgrade-package virtualenv moves the transitive dev dependency\nfrom 21.14.12 (PYSEC-2026-4402, fixed in 21.14.13) to 21.15.13.\npyproject.toml is unchanged; doit audit now finds no known\nvulnerabilities.\n\nAddresses #140\n\n\nClaude-Session: https://claude.ai/code/session_01NXu1sbBxFsEQW16MiZv7Je\n\nCo-authored-by: Claude Opus 5.5 <noreply@anthropic.com>",
          "timestamp": "2026-11-25T10:20:57Z",
          "tree_id": "27a6aa9e77a8baa9e7e2376f28bd289623ecc319",
          "url": "https://github.com/endavis/bastproxy-aardwolf/commit/05aa7aab93095ff7f5f54e3c43246875c6d0626c"
        },
        "date": 1795602099528,
        "tool": "pytest",
        "benches": [
          {
            "name": "tests/benchmarks/test_bench_aardu.py::test_bench_convert_level",
            "value": 3096730.1591002136,
            "unit": "iter/sec",
            "range": "stddev: 4.2417729334508345e-8",
            "extra": "mean: 322.9212584316872 nsec\nrounds: 186916"
          },
          {
            "name": "tests/benchmarks/test_bench_aardu.py::test_bench_parse_damage_line",
            "value": 167915.75505213224,
            "unit": "iter/sec",
            "range": "stddev: 9.06672291508866e-7",
            "extra": "mean: 5.955367319103162 usec\nrounds: 173612"
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
          "id": "f91535d4167f003fd25b8d982edbdac36bdca815",
          "message": "feat: make the idle command and glaze regex settings (merges PR #137, addresses #136)\n\nThe idle plugin now has two settings:\n- command (default look): sent when the glaze line fires, read at fire\n  time\n- regex (default ^Your eyes glaze over\\.$): an empty or invalid value is\n  refused by a validator; a change updates the trigger through\n  trigger.update, and a failed update is logged and leaves the trigger\n  on its last working regex\n\nTRIGGER_GLAZE stays a constant (the internal trigger name). The unused\nPLUGIN_ID is removed from the idle libs.\n\nAddresses #136\n\n\nClaude-Session: https://claude.ai/code/session_01NXu1sbBxFsEQW16MiZv7Je\n\nCo-authored-by: Claude Opus 5.5 <noreply@anthropic.com>",
          "timestamp": "2026-11-25T10:26:18Z",
          "tree_id": "7ae96d66b6f901703cfe7dd3f5c72dbb140d0ef9",
          "url": "https://github.com/endavis/bastproxy-aardwolf/commit/f91535d4167f003fd25b8d982edbdac36bdca815"
        },
        "date": 1795602415585,
        "tool": "pytest",
        "benches": [
          {
            "name": "tests/benchmarks/test_bench_aardu.py::test_bench_convert_level",
            "value": 3104973.3779376415,
            "unit": "iter/sec",
            "range": "stddev: 4.539800066958858e-8",
            "extra": "mean: 322.0639529812044 nsec\nrounds: 191976"
          },
          {
            "name": "tests/benchmarks/test_bench_aardu.py::test_bench_parse_damage_line",
            "value": 166092.8876332926,
            "unit": "iter/sec",
            "range": "stddev: 0.0000010669265128325967",
            "extra": "mean: 6.020727402896658 usec\nrounds: 173883"
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
          "id": "303c1bdaef6ebd01ccc9f82e061580292f0adff4",
          "message": "refactor: build each plugin's own event names from its plugin id (merges PR #142, addresses #138)\n\nPlugin libs no longer hold their own plugin id. The own-event constants\nbecome suffixes (SUFFIX_*), and each plugin builds the full name from\nself.plugin_id through the new aardwolf._libs.eventu helpers or the\n\"ev_{plugin_id}_var_<setting>_modified\" decorator template. Other\nplugins' events stay as literals. A new test scans every plugin's libs\nfor its own plugin id.\n\nTests that imported the removed constants build the expected names from\nthe test's plugin id.\n\nAddresses #138\n\nBREAKING CHANGE: the plugin libs packages no longer export PLUGIN_ID,\nPREFIX or their own EVENT_* constants (aflags, config, cp, daily, eq, gq,\niceage, itemid, level, mapper, mobk, move, promptfix, quest, repop,\nscanh, skills, su). The event names themselves are unchanged. Code that\nimported one of these constants should use the plugin id instead: inside\na plugin, aardwolf._libs.eventu.own_event(self.plugin_id, SUFFIX_<X>);\nfor another plugin's event, its full literal name.\n\n\nClaude-Session: https://claude.ai/code/session_01NXu1sbBxFsEQW16MiZv7Je\n\nCo-authored-by: Claude Opus 5.5 <noreply@anthropic.com>",
          "timestamp": "2026-11-25T10:56:27Z",
          "tree_id": "695d51cb320e1296cd4b61f988a9448c377b9619",
          "url": "https://github.com/endavis/bastproxy-aardwolf/commit/303c1bdaef6ebd01ccc9f82e061580292f0adff4"
        },
        "date": 1795604220997,
        "tool": "pytest",
        "benches": [
          {
            "name": "tests/benchmarks/test_bench_aardu.py::test_bench_convert_level",
            "value": 3060240.825884418,
            "unit": "iter/sec",
            "range": "stddev: 4.145437692061568e-8",
            "extra": "mean: 326.771668275812 nsec\nrounds: 197668"
          },
          {
            "name": "tests/benchmarks/test_bench_aardu.py::test_bench_parse_damage_line",
            "value": 168929.92139113366,
            "unit": "iter/sec",
            "range": "stddev: 8.51531481935291e-7",
            "extra": "mean: 5.919614428071861 usec\nrounds: 174826"
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
          "id": "eea92038337218e4cec7bf68523d9576a793fb6b",
          "message": "feat: make user-facing timings, counts, time formats and line lengths settings (merges PR #144, addresses #139)\n\nEach value the issue lists is now a setting in the plugin that uses it,\nwith the old constant as its default and a validator that refuses bad\nvalues. Libs functions take the value as a parameter. A shared validator\nmodule backs the integer and time format checks. The statdb report no\nlonger hard-codes +0000 in its time format.\n\nAddresses #139\n\n\nClaude-Session: https://claude.ai/code/session_01NXu1sbBxFsEQW16MiZv7Je\n\nCo-authored-by: Claude Opus 5.5 <noreply@anthropic.com>",
          "timestamp": "2026-11-25T11:04:19Z",
          "tree_id": "58497a0dbc5f449fcae6c8265cf6917fb28e3b50",
          "url": "https://github.com/endavis/bastproxy-aardwolf/commit/eea92038337218e4cec7bf68523d9576a793fb6b"
        },
        "date": 1795604706128,
        "tool": "pytest",
        "benches": [
          {
            "name": "tests/benchmarks/test_bench_aardu.py::test_bench_convert_level",
            "value": 3889725.2162037306,
            "unit": "iter/sec",
            "range": "stddev: 8.629863852893718e-8",
            "extra": "mean: 257.0875690226709 nsec\nrounds: 193163"
          },
          {
            "name": "tests/benchmarks/test_bench_aardu.py::test_bench_parse_damage_line",
            "value": 208672.1866809426,
            "unit": "iter/sec",
            "range": "stddev: 7.799431263649532e-7",
            "extra": "mean: 4.792205496600219 usec\nrounds: 108649"
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
          "id": "f70bdbe825391945824dad2f273970522ba1b7b5",
          "message": "fix: turn the SCAN tag on so scanh sees the scan output (merges PR #145, addresses #143)\n\nscanh only reads scan lines between {scan} and {/scan}, which Aardwolf\nsends only while the character's SCAN tag is on, and nothing turned it\non. SCAN is set with the MUD's tags command, not option 102.\n\n- a102: new counted tag.toggle API for \"tags <name> on|off\". The first\n  request sends \"on\" and the last release sends \"off\", only while the\n  character is active and only for tags turned on during this\n  connection. Counted tags are sent once when the character becomes\n  active, and the sent set is cleared on disconnect. A reload sends\n  nothing.\n- scanh: requests SCAN at load and releases it on a real unload. The\n  {scan} and {/scan} lines are omitted, so the client does not see raw\n  tags.\n- Docs for a102 and scanh, including the note that tags names differ\n  from option 102 names.\n\nAddresses #143\n\n\nClaude-Session: https://claude.ai/code/session_01NXu1sbBxFsEQW16MiZv7Je\n\nCo-authored-by: Claude Opus 5.5 <noreply@anthropic.com>",
          "timestamp": "2026-11-25T11:17:41Z",
          "tree_id": "164c0dd3f6dc70ceb8065a33ab5534be7b04a44f",
          "url": "https://github.com/endavis/bastproxy-aardwolf/commit/f70bdbe825391945824dad2f273970522ba1b7b5"
        },
        "date": 1795605496482,
        "tool": "pytest",
        "benches": [
          {
            "name": "tests/benchmarks/test_bench_aardu.py::test_bench_convert_level",
            "value": 5316645.9824354695,
            "unit": "iter/sec",
            "range": "stddev: 1.4317174422600537e-8",
            "extra": "mean: 188.08850604378895 nsec\nrounds: 55015"
          },
          {
            "name": "tests/benchmarks/test_bench_aardu.py::test_bench_parse_damage_line",
            "value": 271107.1612596253,
            "unit": "iter/sec",
            "range": "stddev: 8.452839920676499e-7",
            "extra": "mean: 3.6885783295202286 usec\nrounds: 145922"
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
          "id": "3bd7a09d9fe4ad4bb4b19b5b94aab55321ccd4f6",
          "message": "fix: update the mapper adapter for core mismatch handling and norecall (merges PR #163, addresses #157, #158, #161)\n\n#161: mismatch_lines shows every difference the core mapper reports\n(name, terrain, x/y/z, details, area, exits), escapes the values, and\nfor a held area or exit change suggests #bp.client.mapper.accept <uid>\nand, for changed exits, #bp.client.mapper.ignoreexits <uid>, instead of\npurge -r. purge -a <old> stays for a replaced area. The MUSHclient import\nmaps rooms.ignore_exits_mismatch to the ignoreexits flag.\n\n#158: the norecall regex no longer ends in $, so the message matches with\ntext after the period, as in the old plugin.\n\n#157: no room request is sent after room.area. The room is stored and\ncurrent before its area is requested, and a reply for the same room is\nignored; the reason is recorded in the code and the plugin docs, and a\ntest pins it.\n\nuv.lock: bastproxy bumped to 487c4c4e (includes core #812 and #813, which\nadd accept and ignoreexits).\n\nApproved existing-test edit: test_mismatch_lines_area no longer expects\nthe purge -r hint and expects the accept hint.\n\nAddresses #157\nAddresses #158\nAddresses #161\n\n\nClaude-Session: https://claude.ai/code/session_01NXu1sbBxFsEQW16MiZv7Je\n\nCo-authored-by: Claude Opus 5.5 <noreply@anthropic.com>",
          "timestamp": "2026-11-25T23:05:41Z",
          "tree_id": "b817377bd2630a32dcba00864fa2f482add4c543",
          "url": "https://github.com/endavis/bastproxy-aardwolf/commit/3bd7a09d9fe4ad4bb4b19b5b94aab55321ccd4f6"
        },
        "date": 1795647977284,
        "tool": "pytest",
        "benches": [
          {
            "name": "tests/benchmarks/test_bench_aardu.py::test_bench_convert_level",
            "value": 4065656.3560031317,
            "unit": "iter/sec",
            "range": "stddev: 4.2499916331379025e-8",
            "extra": "mean: 245.96274560279875 nsec\nrounds: 191645"
          },
          {
            "name": "tests/benchmarks/test_bench_aardu.py::test_bench_parse_damage_line",
            "value": 223167.36326511402,
            "unit": "iter/sec",
            "range": "stddev: 5.938378201687423e-7",
            "extra": "mean: 4.4809419503336585 usec\nrounds: 114247"
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
          "id": "a057567263a9ebb122c2f459f43c8bf8ae336d8c",
          "message": "fix: refuse unknown strftime directives in time formats on every platform (merges PR #166, addresses #165)\n\ntime_format_error relied on how the C library treats an unknown\ndirective: glibc returns it unchanged and Windows raises, but macOS drops\nthe % and returns the letter, so %Q was accepted there (the nightly OS\nmatrix failed on test_time_format_refuses[%Q]).\n\nEach % directive is now checked against a fixed portable set (a A b B c\nd H I j m M p S U w W x X y Y Z z); %% is a literal percent but a format\nstill needs one real directive. Flags (%-d, %#d) and the E/O modifiers\nare platform-specific and refused. An unknown directive is named in the\nmessage (\"unsupported strftime directive: %Q\"). time.strftime still runs\nlast for errors it raises. Every settings default (daily, afk, statdb) is\naccepted, and a test mimics the BSD behaviour so Linux CI covers it.\n\nThe timeformat rows in the daily, statdb and afk docs list the accepted\ndirectives.\n\nAddresses #165\n\n\nClaude-Session: https://claude.ai/code/session_01NXu1sbBxFsEQW16MiZv7Je\n\nCo-authored-by: Claude Opus 5.5 <noreply@anthropic.com>",
          "timestamp": "2026-11-25T23:18:57Z",
          "tree_id": "abc0e5f07ba9f9c73e737a3a19fe132bdd98208c",
          "url": "https://github.com/endavis/bastproxy-aardwolf/commit/a057567263a9ebb122c2f459f43c8bf8ae336d8c"
        },
        "date": 1795648770585,
        "tool": "pytest",
        "benches": [
          {
            "name": "tests/benchmarks/test_bench_aardu.py::test_bench_convert_level",
            "value": 3596756.502517256,
            "unit": "iter/sec",
            "range": "stddev: 4.422646078146392e-8",
            "extra": "mean: 278.0282733346368 nsec\nrounds: 196890"
          },
          {
            "name": "tests/benchmarks/test_bench_aardu.py::test_bench_parse_damage_line",
            "value": 186736.62221407937,
            "unit": "iter/sec",
            "range": "stddev: 0.0000013989860953451133",
            "extra": "mean: 5.355135956425173 usec\nrounds: 105486"
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
          "id": "2c3b5515dcde98c8bc1a0d0460f6ffbd71092437",
          "message": "fix: stop the statmn out-of-order and quest_status undeclared-key warnings (merges PR #167, addresses #162, #164)\n\n#162: the level plugin raises level_gain from its empty-line callback,\nand statmn's _queue registered _flush on that same empty-line event while\nit was running, so the core ran it in the same pass and logged \"called\nout of order\". _queue now checks plugins.core.events:event.stack.get and,\nwhen the empty-line event is being raised and nothing is waiting yet,\nflushes at once instead of registering. The message still shows at that\nempty line. Messages queued outside an empty line (quest, cp, gq) still\nwait for the next one and go out together.\n\n#164: quest_status passes the GMCP status data through, which can carry\nwait; wait is now described in its arg_descriptions, like quest_comp\n(#50).\n\nDocs: statmn (completion messages, events) and quest (quest_status row).\n\nAddresses #162\nAddresses #164\n\n\nClaude-Session: https://claude.ai/code/session_01NXu1sbBxFsEQW16MiZv7Je\n\nCo-authored-by: Claude Opus 5.5 <noreply@anthropic.com>",
          "timestamp": "2026-11-25T23:25:35Z",
          "tree_id": "504e1b0d916c5bbca913b7a77d96d9f7621ff7cd",
          "url": "https://github.com/endavis/bastproxy-aardwolf/commit/2c3b5515dcde98c8bc1a0d0460f6ffbd71092437"
        },
        "date": 1795649176258,
        "tool": "pytest",
        "benches": [
          {
            "name": "tests/benchmarks/test_bench_aardu.py::test_bench_convert_level",
            "value": 4988258.159284093,
            "unit": "iter/sec",
            "range": "stddev: 1.498805048967424e-8",
            "extra": "mean: 200.47077919149203 nsec\nrounds: 52362"
          },
          {
            "name": "tests/benchmarks/test_bench_aardu.py::test_bench_parse_damage_line",
            "value": 270438.3732654753,
            "unit": "iter/sec",
            "range": "stddev: 5.111743139046358e-7",
            "extra": "mean: 3.6977001004896297 usec\nrounds: 143308"
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
          "id": "e7b57549698509f040e4fc988c433806169defc8",
          "message": "fix: correct campaign and gq tracking for repeated mobs, ended campaigns and wins (merges PR #168, addresses #154, #155, #153)\n\n#154: a mobk_kill carries only the mob's name. cp and gq keep removing\nthe first match (the same in both plugins), and when the killed name is\nlisted at more than one location they now queue `campaign check` or\n`gq check` after raising the mobs-left event, so the MUD's list replaces\nthe guess at once. Duplicates at one location queue nothing.\n\n#155: scanh asks plugins.aardwolf.cp:oncp at every {scan} start and clears\nits campaign targets unless cp is loaded and a campaign is on; at load it\nreads the mobs left only while oncp is true. This covers a campaign that\nexpires without a completion or failure event, a stale state after a\nrestart, and cp being unloaded. No new cp API or event.\n\n#153: the gq win announcement trigger is always on (no longer in gqin) and\nfollows the old regex forms. When the winner is the character (case\nignored), gq_won is raised even if the join was missed or the gq number\ndiffers (logged at debug), with won set and finishtime filled in so statdb\ncounts the win.\n\nDocs: cp, gq and scanh plugin pages.\n\nApproved existing-test edits (#153): ALWAYS_ON gains gq_wonannounce in\ntest_gq_libs.py and test_gq_plugin.py; the always-on count test now\nexpects eight and is renamed; the gqin group no longer holds\ngq_wonannounce; the \"1st win!\" case now matches and moved to its own\nannouncement test; test_announce_of_another_gquest_does_nothing became\ntest_announce_of_another_gquest_number_still_raises_won.\n\nAddresses #154\nAddresses #155\nAddresses #153\n\n\nClaude-Session: https://claude.ai/code/session_01NXu1sbBxFsEQW16MiZv7Je\n\nCo-authored-by: Claude Opus 5.5 <noreply@anthropic.com>",
          "timestamp": "2026-11-25T23:42:16Z",
          "tree_id": "0cffb06feeebc7ed8f9ed760b4194cea506d603d",
          "url": "https://github.com/endavis/bastproxy-aardwolf/commit/e7b57549698509f040e4fc988c433806169defc8"
        },
        "date": 1795650170949,
        "tool": "pytest",
        "benches": [
          {
            "name": "tests/benchmarks/test_bench_aardu.py::test_bench_convert_level",
            "value": 5930554.574444823,
            "unit": "iter/sec",
            "range": "stddev: 1.661510327297858e-8",
            "extra": "mean: 168.61829487398538 nsec\nrounds: 60887"
          },
          {
            "name": "tests/benchmarks/test_bench_aardu.py::test_bench_parse_damage_line",
            "value": 291242.80902809015,
            "unit": "iter/sec",
            "range": "stddev: 5.703139365689742e-7",
            "extra": "mean: 3.433561169585995 usec\nrounds: 152208"
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
          "id": "c06fada82f131e7d3b905654c0b8d4964d12cb02",
          "message": "fix: eq bags, death, container refresh, optional items, and itemkeep forgetting (#146, #147, #148, #149, #152) (merges PR #169, addresses #146, #147, #148, #149, #152)\n\n* fix: give bags worn, on the keyring or in the vault their own container\n\nEqState.commit only made a container for a bag seen in the inventory or\nin another bag, so a worn bag, a keyring bag or a vault bag had no\ncontainer and no read, and inv <serial> said it did not exist. A bag\n(item type 11) now gets a container and a read the first time it is seen\nin any block. It still goes when it leaves the inventory.\n\nDocs: eq plugin page (Bags, and the new-bag note).\n\nAddresses #146\n\nCo-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>\nClaude-Session: https://claude.ai/code/session_01NXu1sbBxFsEQW16MiZv7Je\n\n* feat: forget what is carried when the character dies and read it again\n\nAardwolf leaves the worn and carried items in the corpse. eq now has its\nown ^You die\\.$ trigger (eq_dead; the line is still shown).\nEqState.reset_carried forgets Worn, Inventory, Keyring, the bags and\ntheir items, and keeps the vault, its counts, whether it was read and\nthe bags in it. The plugin then drops a block being read, removes the\ntypes of the dropped bags and queues the same reads as refresh.\n\nApproved existing-test edit: test_after_load's trigger set gains eq_dead.\n\nDocs: eq plugin page (Death, MUD output, old-plugin table, changes).\n\nAddresses #147\nGrouped under #146: one PR for #146, #147, #148, #149 and #152, as asked.\n\nCo-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>\nClaude-Session: https://claude.ai/code/session_01NXu1sbBxFsEQW16MiZv7Je\n\n* feat: add the container.refresh API to read one container\n\nplugins.aardwolf.eq:container.refresh(cid) queues the read of Worn,\nInventory, Keyring, Vault (names not case sensitive) or a bag serial,\nint or text, and returns True when it was queued. It returns False for\nan unknown container, or for the vault outside a bank. _queue now\nreturns whether it queued. This is the port of the old\neq.getcontainer refresh().\n\nDocs: eq plugin page (API table, old-plugin table).\n\nAddresses #148\nGrouped under #146: one PR for #146, #147, #148, #149 and #152, as asked.\n\nCo-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>\nClaude-Session: https://claude.ai/code/session_01NXu1sbBxFsEQW16MiZv7Je\n\n* fix: let icache, get and put run without an item\n\nThe item argument of icache, get and put is now optional. A bare get or\nput sends exactly get or put, with no trailing space, and a bare icache\nsays how many items are in the cache.\n\nDocs: eq plugin page (command table).\n\nAddresses #149\nGrouped under #146: one PR for #146, #147, #148, #149 and #152, as asked.\n\nCo-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>\nClaude-Session: https://claude.ai/code/session_01NXu1sbBxFsEQW16MiZv7Je\n\n* fix: forget a kept item once it leaves the inventory\n\nitemkeep remembered every serial it kept, so an item that left (given,\nsold, left in a corpse) and came back without its K was not kept again.\nIt now listens to eq_inventory_removed and forgets that serial, so the\nitem is kept again when it returns.\n\nDocs: itemkeep plugin page.\n\nAddresses #152\nGrouped under #146: one PR for #146, #147, #148, #149 and #152, as asked.\n\nCo-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>\nClaude-Session: https://claude.ai/code/session_01NXu1sbBxFsEQW16MiZv7Je\n\n---------\n\nCo-authored-by: Claude Opus 5.5 <noreply@anthropic.com>",
          "timestamp": "2026-11-26T07:42:33Z",
          "tree_id": "1440cba64d08852c360af68ef746687791e3277e",
          "url": "https://github.com/endavis/bastproxy-aardwolf/commit/c06fada82f131e7d3b905654c0b8d4964d12cb02"
        },
        "date": 1795678987393,
        "tool": "pytest",
        "benches": [
          {
            "name": "tests/benchmarks/test_bench_aardu.py::test_bench_convert_level",
            "value": 5797429.370101309,
            "unit": "iter/sec",
            "range": "stddev: 1.1988861189968774e-8",
            "extra": "mean: 172.49024285784876 nsec\nrounds: 59542"
          },
          {
            "name": "tests/benchmarks/test_bench_aardu.py::test_bench_parse_damage_line",
            "value": 289126.2531507253,
            "unit": "iter/sec",
            "range": "stddev: 4.168366487753935e-7",
            "extra": "mean: 3.4586966389340192 usec\nrounds: 149032"
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
          "id": "440027f573e9b134ca8016eae102828298280032",
          "message": "fix: eqdb itype as a number for old rows, and WAL mode for statdb and eqdb (#150, #151) (merges PR #170, addresses #150, #151)\n\n* fix: store eqdb itype as the object type number for old rows too\n\nThe old proxy stored items.itype as the type name the MUD sent\n(Weapon); the new parser stores the OBJECTTYPES number, so item.get\nreturned text for old rows and an int for new ones. eqdb's schema goes\nto version 2: its migration maps every text itype through\nOBJECTTYPESREV (stripped, case ignored) and leaves unknown names and\nnumbers as they are. The core backs the version 1 file up first.\n\nDocs: eqdb (version 2, itype, the old proxy should not use the upgraded\nfile, and the \"Bugs fixed\" note on type details corrected: only spells\nrows were never saved) and eq (unique is now a bool).\n\nApproved existing-test edit: test_tables_are_the_old_ones and\ntest_database_is_created expect version 2.\n\nAddresses #150\n\nCo-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>\nClaude-Session: https://claude.ai/code/session_01NXu1sbBxFsEQW16MiZv7Je\n\n* feat: open the statdb and eqdb databases in WAL mode\n\nThe old plugins set journal_mode=WAL; the new ones set no journal mode,\nso statdb's web pages, which read while the proxy writes, and the\nwriter block each other. Both plugins now pass journal_mode=\"wal\" to\nplugins.core.sqldb:database.add (endavis/bastproxy#829), and uv.lock\nmoves to core d3e4d509, which adds that option.\n\nDocs: eqdb (the pragma row split in two: foreign keys stay off, WAL is\npassed to database.add; the -wal and -shm files) and statdb.\n\nAddresses #151\nGrouped under #150: one PR for #150 and #151, as asked.\n\nCo-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>\nClaude-Session: https://claude.ai/code/session_01NXu1sbBxFsEQW16MiZv7Je\n\n---------\n\nCo-authored-by: Claude Opus 5.5 <noreply@anthropic.com>",
          "timestamp": "2026-11-26T09:25:56Z",
          "tree_id": "82612e805df71f396b4dd2c6629ef989c8c0a3f5",
          "url": "https://github.com/endavis/bastproxy-aardwolf/commit/440027f573e9b134ca8016eae102828298280032"
        },
        "date": 1795685193837,
        "tool": "pytest",
        "benches": [
          {
            "name": "tests/benchmarks/test_bench_aardu.py::test_bench_convert_level",
            "value": 5731054.272721199,
            "unit": "iter/sec",
            "range": "stddev: 1.631285528345609e-8",
            "extra": "mean: 174.4879654621005 nsec\nrounds: 58942"
          },
          {
            "name": "tests/benchmarks/test_bench_aardu.py::test_bench_parse_damage_line",
            "value": 291576.1138108209,
            "unit": "iter/sec",
            "range": "stddev: 0.0000011084048518610191",
            "extra": "mean: 3.4296362172136488 usec\nrounds: 149926"
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
          "id": "d340a4966aeded9d15311f8f20641ccd944887fc",
          "message": "docs: record small behaviour changes found in the migration audit (merges PR #171, addresses #159)\n\nEach plugin page's changes from the old plugin now records the eight\nchanges the audit found, all kept as intended (the user chose to file\nno fix issue):\n\n- su: add all uses skill.is.practiced (more than 10 percent), not 1.\n- statdb: an existing milestone is skipped without a client message.\n- afk: a queued tell keeps only timestamp, player and msg.\n- connect: no empty line after look and map at first active.\n- mobk and the aardu docstring: a damage line ends in ! or ., no\n  longer | (a literal in the old character class).\n- whois: a stat with an empty label is skipped.\n- a102: a client toggle is used only with flag 1 or 2 and a known\n  option; the old bool() read OFF as on and unknown options raised.\n- itemid: the identify command type regex is ^identify \\d+$.\n\nThe issue said the old itemid regex was .*; it was\n^identify (?P<item>.*)$.\n\nAddresses #159\n\n\nClaude-Session: https://claude.ai/code/session_01NXu1sbBxFsEQW16MiZv7Je\n\nCo-authored-by: Claude Opus 5.5 <noreply@anthropic.com>",
          "timestamp": "2026-11-26T18:42:09Z",
          "tree_id": "c4c0a24183a7242d03a84e722adfce5c428df484",
          "url": "https://github.com/endavis/bastproxy-aardwolf/commit/d340a4966aeded9d15311f8f20641ccd944887fc"
        },
        "date": 1795718572685,
        "tool": "pytest",
        "benches": [
          {
            "name": "tests/benchmarks/test_bench_aardu.py::test_bench_convert_level",
            "value": 4888848.5102010425,
            "unit": "iter/sec",
            "range": "stddev: 1.7330627388653966e-8",
            "extra": "mean: 204.54714395698824 nsec\nrounds: 50654"
          },
          {
            "name": "tests/benchmarks/test_bench_aardu.py::test_bench_parse_damage_line",
            "value": 264723.018569941,
            "unit": "iter/sec",
            "range": "stddev: 5.435055965883612e-7",
            "extra": "mean: 3.7775332322897173 usec\nrounds: 142512"
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
          "id": "eec928fa516ecb7188de314ad1d178065470d8f1",
          "message": "feat: add a hunger plugin that drinks when hungry or thirsty (merges PR #176, addresses #174)\n\nplugins.aardwolf.hunger drinks from a configured container when any of\nAardwolf's six hunger or thirst stage lines arrives (start to feel,\nvery, starving/dehydrated). Drinking is off by default; a cooldown\n(default 60 s) stops the repeating lines from sending a burst. Orange\njuice satisfies both, so there is no eating (the user's decision).\n\nThe container is fetched through plugins.aardwolf.eq:item.fetch, the\ndrink goes out once eq reports eq_taken, and item.put returns it.\nReply triggers (drank, \"<container> is empty.\", filled, no liquid\nsource) are on only while a drink or fill the plugin sent is waiting.\nA missing or empty container gives one client message and stops\ndrinking until the setting changes or the container is filled.\n\nfillsource records the current GMCP room, and optionally a source\nobject. fill fills in that room, or walks there with\nplugins.client.mapper:walk.start and fills once on walk_done; failed,\nstopped or impossible walks are reported. Only the fill command starts\na walk. An automatic fill runs only when the character enters the fill\nroom with the container known to be empty.\n\nThe Aardwolf lines come from the user's live check on 2026-11-26.\ndrink/fill with a serial are still to be confirmed live.\n\nDocs: docs/plugins/hunger.md, the plugin index and the nav.\n\nAddresses #174\n\n\nClaude-Session: https://claude.ai/code/session_01NXu1sbBxFsEQW16MiZv7Je\n\nCo-authored-by: Claude Opus 5.5 <noreply@anthropic.com>",
          "timestamp": "2026-11-26T20:29:13Z",
          "tree_id": "f2f0a0cd4c326c9b60924d2929c7dba6022fdb8e",
          "url": "https://github.com/endavis/bastproxy-aardwolf/commit/eec928fa516ecb7188de314ad1d178065470d8f1"
        },
        "date": 1795724996894,
        "tool": "pytest",
        "benches": [
          {
            "name": "tests/benchmarks/test_bench_aardu.py::test_bench_convert_level",
            "value": 5163845.177254341,
            "unit": "iter/sec",
            "range": "stddev: 1.4297177092719347e-8",
            "extra": "mean: 193.65414060142453 nsec\nrounds: 53328"
          },
          {
            "name": "tests/benchmarks/test_bench_aardu.py::test_bench_parse_damage_line",
            "value": 270906.91742496646,
            "unit": "iter/sec",
            "range": "stddev: 4.6940669016844794e-7",
            "extra": "mean: 3.6913047828576455 usec\nrounds: 143576"
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
          "id": "77bff8753c8a7b1d9198006813a077c13c56b6e3",
          "message": "feat: add a mapper portal by item serial, recorded by entering it (merges PR #181, addresses #175)\n\n* feat: add a mapper portal by item serial, recorded by entering it\n\n`portal <serial>` looks the item up through eq, takes it out of its\ncontainer, holds it in the portal slot, sends `enter`, and stores the\nnext room as a `*` exit with the item's level. The portal and the\nslot's previous item are then restored. The exit is stored as a\nportal-by-serial marker; a walk expands it into the same steps, and the\nrequirement callback blocks it when eq no longer has the item. Text\nportals are unchanged.\n\nThe portal wear slot, whether `enter` alone takes the portal, and the\nrefusal lines other than noportal are still to be confirmed live.\n\nAddresses #175\n\nCo-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>\nClaude-Session: https://claude.ai/code/session_01NXu1sbBxFsEQW16MiZv7Je\n\n* feat: wear a portal where Aardwolf puts it, in the slot or held\n\nThe portal wear location is bought: a character with it wears a portal\nthere, and one without it holds the portal. A plain wear puts it in the\nright place and swaps out what was there. Using a portal by serial now\nsends a plain wear, notes the items in the portal and held slots\nbeforehand, and after the room change puts the portal back and\nre-equips the item from the slot the portal landed in. When eq has not\nseen where it went, the slot whose item changed is restored; when\nnothing can be decided, the portal is put back and a warning is logged.\n\nThe portal-by-serial tests now expect the plain wear with no unequip\nfirst, as approved by the user. FakeEq gains a lands option.\n\nAddresses #175\n\nCo-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>\nClaude-Session: https://claude.ai/code/session_01NXu1sbBxFsEQW16MiZv7Je\n\n---------\n\nCo-authored-by: Claude Opus 5.5 <noreply@anthropic.com>",
          "timestamp": "2026-11-26T22:05:26Z",
          "tree_id": "18b948cccf90102e90a311f6e047df5cdee417c0",
          "url": "https://github.com/endavis/bastproxy-aardwolf/commit/77bff8753c8a7b1d9198006813a077c13c56b6e3"
        },
        "date": 1795730770265,
        "tool": "pytest",
        "benches": [
          {
            "name": "tests/benchmarks/test_bench_aardu.py::test_bench_convert_level",
            "value": 3074179.9367280905,
            "unit": "iter/sec",
            "range": "stddev: 4.8488736285345554e-8",
            "extra": "mean: 325.2900027264895 nsec\nrounds: 198099"
          },
          {
            "name": "tests/benchmarks/test_bench_aardu.py::test_bench_parse_damage_line",
            "value": 170196.34060619186,
            "unit": "iter/sec",
            "range": "stddev: 8.409600547591711e-7",
            "extra": "mean: 5.875566985977954 usec\nrounds: 176119"
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
          "id": "463136b63d4ca35d8435405781de3d73dc908cea",
          "message": "fix: mark a battle prompt whose value holds spaces as a prompt (merges PR #182, addresses #178)\n\nA prompt value ended at the first character of the fixed text after it.\nIn the battle prompt the enemy health value is followed by \" ]>\", so the\nvalue stopped at its first space and could not hold \"Enemy: 100%\". The\nbattle line never matched, was not marked is_prompt, and got no GA, so\nhide windows stayed open in combat.\n\nWhen the fixed text after a value starts with blanks and has other text,\nthe value now ends at that text's first non-blank character and the\nblanks match as \\s*. Values stay possessive, so matching stays linear.\n\nAddresses #178\n\n\nClaude-Session: https://claude.ai/code/session_01NXu1sbBxFsEQW16MiZv7Je\n\nCo-authored-by: Claude Opus 5.5 <noreply@anthropic.com>",
          "timestamp": "2026-11-26T22:25:50Z",
          "tree_id": "7066ceecb8691a07e9a6df875e7b2f48b06483b5",
          "url": "https://github.com/endavis/bastproxy-aardwolf/commit/463136b63d4ca35d8435405781de3d73dc908cea"
        },
        "date": 1795731991274,
        "tool": "pytest",
        "benches": [
          {
            "name": "tests/benchmarks/test_bench_aardu.py::test_bench_convert_level",
            "value": 6058727.983566201,
            "unit": "iter/sec",
            "range": "stddev: 1.1252199929520109e-8",
            "extra": "mean: 165.05114649682528 nsec\nrounds: 62329"
          },
          {
            "name": "tests/benchmarks/test_bench_aardu.py::test_bench_parse_damage_line",
            "value": 311038.5110763722,
            "unit": "iter/sec",
            "range": "stddev: 3.450615147769743e-7",
            "extra": "mean: 3.2150359662519756 usec\nrounds: 156202"
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
          "id": "734e25c49716e6b7cdfa103006e77c68f92cf1c8",
          "message": "feat: gulp instead of drink in the hunger plugin (merges PR #183, addresses #180)\n\nAn automatic drink now sends gulp <serial>. Aardwolf's gulp drinks until\nthe container is empty, the character is drunk, thirst is quenched or\nthe character is full, so one hunger or thirst line usually leaves the\ncharacter full instead of needing several drinks.\n\nA gulp answers with one line, \"You gulp down <liquid> from <container>.\",\nfollowed by \"You are now full.\". The drank trigger now matches it as\nwell as the drink line, so the reply wait ends on it. The empty-container\nhandling is unchanged.\n\nThe 11 existing plugin test expectations of \"drink <serial>\" now expect\n\"gulp <serial>\", as approved by the user.\n\nAddresses #180\n\n\nClaude-Session: https://claude.ai/code/session_01NXu1sbBxFsEQW16MiZv7Je\n\nCo-authored-by: Claude Opus 5.5 <noreply@anthropic.com>",
          "timestamp": "2026-11-26T22:44:51Z",
          "tree_id": "6182a8dfecd061926602e6024871e3ebde83d35e",
          "url": "https://github.com/endavis/bastproxy-aardwolf/commit/734e25c49716e6b7cdfa103006e77c68f92cf1c8"
        },
        "date": 1795733127377,
        "tool": "pytest",
        "benches": [
          {
            "name": "tests/benchmarks/test_bench_aardu.py::test_bench_convert_level",
            "value": 3825476.189336654,
            "unit": "iter/sec",
            "range": "stddev: 3.97234544945326e-8",
            "extra": "mean: 261.40536511178817 nsec\nrounds: 196967"
          },
          {
            "name": "tests/benchmarks/test_bench_aardu.py::test_bench_parse_damage_line",
            "value": 220429.81466553692,
            "unit": "iter/sec",
            "range": "stddev: 8.547507644882516e-7",
            "extra": "mean: 4.536591393125845 usec\nrounds: 115036"
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
          "id": "2f0de9e3857ec2afc7377ee96356110f0ecdb0ec",
          "message": "fix: refuse to record a portal above the character's level (merges PR #185, addresses #184)\n\n_command_portal now checks the portal's level (eq's item level or -l)\nwith the same tier-adjusted requirement check walks use, and refuses\nat once with \"Mapper: <name> (<serial>) needs level <N>\". Nothing is\nsent to the MUD and nothing is stored.\n\nAddresses #184\n\n\nClaude-Session: https://claude.ai/code/session_01NXu1sbBxFsEQW16MiZv7Je\n\nCo-authored-by: Claude Opus 5.5 <noreply@anthropic.com>",
          "timestamp": "2026-11-26T23:13:03Z",
          "tree_id": "ac19bce1735ca168b88927b55d3e4d5b0e4bec82",
          "url": "https://github.com/endavis/bastproxy-aardwolf/commit/2f0de9e3857ec2afc7377ee96356110f0ecdb0ec"
        },
        "date": 1795734814353,
        "tool": "pytest",
        "benches": [
          {
            "name": "tests/benchmarks/test_bench_aardu.py::test_bench_convert_level",
            "value": 5820126.793534802,
            "unit": "iter/sec",
            "range": "stddev: 1.706231552511842e-8",
            "extra": "mean: 171.81756265358936 nsec\nrounds: 59015"
          },
          {
            "name": "tests/benchmarks/test_bench_aardu.py::test_bench_parse_damage_line",
            "value": 282852.48659575096,
            "unit": "iter/sec",
            "range": "stddev: 0.0000029090856476647103",
            "extra": "mean: 3.535411733640464 usec\nrounds: 155280"
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
          "id": "493820119e3b4dd2b5b385bc5dbe39f7ac667a9b",
          "message": "fix: hide the spellup tag lines the skills plugin reads from the client (merges PR #187, addresses #179)\n\nSet omit on the six skills tag triggers (affon, affoff, recon, recoff,\nskillgain, sfail) so the client no longer sees raw tag lines. The plugin\nand su events still fire. Update the skills plugin docs, and flip the two\nexisting assertions that expected the lines to be shown.\n\nAddresses #179\n\n\nClaude-Session: https://claude.ai/code/session_01NXu1sbBxFsEQW16MiZv7Je\n\nCo-authored-by: Claude Opus 5.5 <noreply@anthropic.com>",
          "timestamp": "2026-11-26T23:29:59Z",
          "tree_id": "438fa32d41c5542c65c178f6b29bc9526b5906ff",
          "url": "https://github.com/endavis/bastproxy-aardwolf/commit/493820119e3b4dd2b5b385bc5dbe39f7ac667a9b"
        },
        "date": 1795735831625,
        "tool": "pytest",
        "benches": [
          {
            "name": "tests/benchmarks/test_bench_aardu.py::test_bench_convert_level",
            "value": 3049050.576567949,
            "unit": "iter/sec",
            "range": "stddev: 3.895751095135151e-8",
            "extra": "mean: 327.97094534444 nsec\nrounds: 198531"
          },
          {
            "name": "tests/benchmarks/test_bench_aardu.py::test_bench_parse_damage_line",
            "value": 177059.46531209996,
            "unit": "iter/sec",
            "range": "stddev: 6.005644544172695e-7",
            "extra": "mean: 5.647820059985585 usec\nrounds: 186012"
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
          "id": "15c4d77c5aac0244e3fef7ed05df7d3bf407d98f",
          "message": "fix: treat an already-full container as a finished fill in the hunger plugin (merges PR #188, addresses #186)\n\nAdd a reply trigger for \"<container> is already full.\" that ends the\nawaited fill reply and clears the empty mark and block, as \"You fill ...\"\ndoes. Previously the plugin waited out PENDING_TIMEOUT and left the empty\nmark set.\n\nAddresses #186\n\n\nClaude-Session: https://claude.ai/code/session_01NXu1sbBxFsEQW16MiZv7Je\n\nCo-authored-by: Claude Opus 5.5 <noreply@anthropic.com>",
          "timestamp": "2026-11-26T23:35:31Z",
          "tree_id": "ca6576cb4df0923aa82dda3eab971a0bc36ac4e1",
          "url": "https://github.com/endavis/bastproxy-aardwolf/commit/15c4d77c5aac0244e3fef7ed05df7d3bf407d98f"
        },
        "date": 1795736162593,
        "tool": "pytest",
        "benches": [
          {
            "name": "tests/benchmarks/test_bench_aardu.py::test_bench_convert_level",
            "value": 2992298.742307587,
            "unit": "iter/sec",
            "range": "stddev: 4.6326117298584436e-8",
            "extra": "mean: 334.1912309293104 nsec\nrounds: 192345"
          },
          {
            "name": "tests/benchmarks/test_bench_aardu.py::test_bench_parse_damage_line",
            "value": 170063.8396941017,
            "unit": "iter/sec",
            "range": "stddev: 0.0000010164183155975552",
            "extra": "mean: 5.8801447844452195 usec\nrounds: 177305"
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
          "id": "fad5f14ed80db1b9c2dc8546915b68a3353b14bf",
          "message": "feat: add the Aardwolf mapper commands under #bp.client.mapper (merges PR #190, addresses #189)\n\nOn load, the Aardwolf mapper adds each of its own user commands under\nplugins.client.mapper with plugins.core.commands:command.add.for.plugin\n(endavis/bastproxy#839, ADR-0024). They work as\n#bp.client.mapper.<name> and are listed in an aardwolf.mapper section.\nThe old #bp.aardwolf.mapper.<name> names keep working and are documented\nas deprecated.\n\nThe commands are the class's own _command_* methods, so the base\nhelp/save/reset/set are left out and a new command is picked up without\na list to update. A test checks the names never clash with the core\nmapper's commands.\n\nuv.lock moves bastproxy from d3e4d509 to b2b81bf6, the first core commit\nwith the API.\n\nAddresses #189\n\n\nClaude-Session: https://claude.ai/code/session_01NXu1sbBxFsEQW16MiZv7Je\n\nCo-authored-by: Claude Opus 5.5 <noreply@anthropic.com>",
          "timestamp": "2026-11-27T00:12:26Z",
          "tree_id": "cde0673a5c7faa95824030c72a653671b4b2bf94",
          "url": "https://github.com/endavis/bastproxy-aardwolf/commit/fad5f14ed80db1b9c2dc8546915b68a3353b14bf"
        },
        "date": 1795738382038,
        "tool": "pytest",
        "benches": [
          {
            "name": "tests/benchmarks/test_bench_aardu.py::test_bench_convert_level",
            "value": 3767136.1176111796,
            "unit": "iter/sec",
            "range": "stddev: 3.802464046423064e-8",
            "extra": "mean: 265.45364138159175 nsec\nrounds: 197123"
          },
          {
            "name": "tests/benchmarks/test_bench_aardu.py::test_bench_parse_damage_line",
            "value": 203643.0129237905,
            "unit": "iter/sec",
            "range": "stddev: 8.791408378844165e-7",
            "extra": "mean: 4.910553942620319 usec\nrounds: 108050"
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
          "id": "5c15d3ad1da8d1bae575efb9120535859b66e0a0",
          "message": "refactor: print the mapper tables through the core table.format (merges PR #192, addresses #191)\n\nshops, train, quest, notes, cexits, the lockexit exit list and portals\nnow print through plugins.core.utils:table.format, like the core\nmapper's find. Columns line up, colour codes no longer throw them off,\nand long cells wrap to the line length. Before, the cells were joined\nwith \" | \".\n\nThe libs gain the column lists and table_data, which turns the row\ntuples the plugin already builds (and the web pages share) into dicts.\ntable_lines and search_lines are removed. plugins.core.utils is now\nin PLUGIN_DEPENDENCIES.\n\nThe test fake records each table.format call, so the tests check the\ncells the plugin passes in. Assertions that only checked the old \" | \"\nlines were rewritten to check the same cells, with the user's approval.\n\nPart 1 of 5 under #191; statmn, mobk, cp and statdb follow.\n\nAddresses #191\n\n\nClaude-Session: https://claude.ai/code/session_01NXu1sbBxFsEQW16MiZv7Je\n\nCo-authored-by: Claude Opus 5.5 <noreply@anthropic.com>",
          "timestamp": "2026-11-27T01:03:40Z",
          "tree_id": "1e9d781a38047c894cf427f3e38bbe087a58ae6f",
          "url": "https://github.com/endavis/bastproxy-aardwolf/commit/5c15d3ad1da8d1bae575efb9120535859b66e0a0"
        },
        "date": 1795741459380,
        "tool": "pytest",
        "benches": [
          {
            "name": "tests/benchmarks/test_bench_aardu.py::test_bench_convert_level",
            "value": 3133417.783429858,
            "unit": "iter/sec",
            "range": "stddev: 4.272769666323454e-8",
            "extra": "mean: 319.1403346493406 nsec\nrounds: 189072"
          },
          {
            "name": "tests/benchmarks/test_bench_aardu.py::test_bench_parse_damage_line",
            "value": 173940.2736980696,
            "unit": "iter/sec",
            "range": "stddev: 8.677097182380342e-7",
            "extra": "mean: 5.749099841798731 usec\nrounds: 179534"
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
          "id": "6a812def3d006276a5e9995cd94903137554132e",
          "message": "refactor: print the mobk damage table through the core table.format (merges PR #193, addresses #191)\n\nThe last command built its damage-type table by hand with fixed widths and\na dashed rule. It now passes the rows to plugins.core.utils:table.format,\nso the columns line up whatever the damage-type names. The libs hold the\ncolumn list and a pure rows-to-dicts helper. The numeric columns are now\nleft-justified, as table.format does for every column.\n\nPart 3 of 5 under #191. Addresses #191.\n\n\nClaude-Session: https://claude.ai/code/session_01NXu1sbBxFsEQW16MiZv7Je\n\nCo-authored-by: Claude Opus 5.5 <noreply@anthropic.com>",
          "timestamp": "2026-11-27T01:21:21Z",
          "tree_id": "c4a1e1f4bcbf5f0dcf397cbbcf2373dacfed80a2",
          "url": "https://github.com/endavis/bastproxy-aardwolf/commit/6a812def3d006276a5e9995cd94903137554132e"
        },
        "date": 1795742515146,
        "tool": "pytest",
        "benches": [
          {
            "name": "tests/benchmarks/test_bench_aardu.py::test_bench_convert_level",
            "value": 2854226.254095564,
            "unit": "iter/sec",
            "range": "stddev: 1.3121272630628419e-7",
            "extra": "mean: 350.35764896531515 nsec\nrounds: 195734"
          },
          {
            "name": "tests/benchmarks/test_bench_aardu.py::test_bench_parse_damage_line",
            "value": 167484.09440833496,
            "unit": "iter/sec",
            "range": "stddev: 0.00000768183605438982",
            "extra": "mean: 5.970716225517797 usec\nrounds: 175717"
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
          "id": "97bba6986a57c393f22de204bb4fbcd4ad15e418",
          "message": "refactor: print the statmn totals table through the core table.format API (merges PR #194, addresses #191)\n\nThe per-type totals table of the statmn report was laid out by hand with a\nfixed format string and two dividers. It now goes through\nplugins.core.utils:table.format, passed into the libs through Formatters.\nThe libs hold the column list and a pure stat_data helper; colour stays in\nthe cells. The centre title line keeps the linelength setting; the table\nitself takes the proxy's line length and left-aligns its cells.\n\nTests rewritten because they only checked the old layout: the report layout\nand line-length tests in test_statmn_libs.py, and the line-length and timer\nreport tests in test_statmn_plugin.py. The cells, order and counts they\nassert are unchanged.\n\nPart 2 of 5 under #191. Addresses #191\n\n\nClaude-Session: https://claude.ai/code/session_01NXu1sbBxFsEQW16MiZv7Je\n\nCo-authored-by: Claude Opus 5.5 <noreply@anthropic.com>",
          "timestamp": "2026-11-27T01:27:01Z",
          "tree_id": "d14e43f0d8767f3c30c31938725b57ad76fb9c0b",
          "url": "https://github.com/endavis/bastproxy-aardwolf/commit/97bba6986a57c393f22de204bb4fbcd4ad15e418"
        },
        "date": 1795742855049,
        "tool": "pytest",
        "benches": [
          {
            "name": "tests/benchmarks/test_bench_aardu.py::test_bench_convert_level",
            "value": 3110209.416250026,
            "unit": "iter/sec",
            "range": "stddev: 4.680628289383276e-8",
            "extra": "mean: 321.5217582376489 nsec\nrounds: 190877"
          },
          {
            "name": "tests/benchmarks/test_bench_aardu.py::test_bench_parse_damage_line",
            "value": 152034.1196067736,
            "unit": "iter/sec",
            "range": "stddev: 0.000002712762247554549",
            "extra": "mean: 6.577470916307703 usec\nrounds: 175717"
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
          "id": "94ac3f7c3bdace3794fa6e686345d89e45667f9f",
          "message": "refactor: print the cp mobs-left list through table.format (merges PR #195, addresses #191)\n\nThe cp show command built its table by hand. Print it through the core\nplugins.core.utils:table.format API. The libs hold the column list and a\npure rows-to-dicts helper; the dead-mob colour stays in the cell text,\non both cells so the whole row stays red.\n\nAddresses #191. Part 4 of 5 under #191.\n\n\nClaude-Session: https://claude.ai/code/session_01NXu1sbBxFsEQW16MiZv7Je\n\nCo-authored-by: Claude Opus 5.5 <noreply@anthropic.com>",
          "timestamp": "2026-11-27T01:33:49Z",
          "tree_id": "8f8a8a190e7de70bd6edaab354e7435a269bc1f0",
          "url": "https://github.com/endavis/bastproxy-aardwolf/commit/94ac3f7c3bdace3794fa6e686345d89e45667f9f"
        },
        "date": 1795743264988,
        "tool": "pytest",
        "benches": [
          {
            "name": "tests/benchmarks/test_bench_aardu.py::test_bench_convert_level",
            "value": 3955496.0853482173,
            "unit": "iter/sec",
            "range": "stddev: 3.6897528120542674e-8",
            "extra": "mean: 252.81278970396608 nsec\nrounds: 194667"
          },
          {
            "name": "tests/benchmarks/test_bench_aardu.py::test_bench_parse_damage_line",
            "value": 217898.37278031433,
            "unit": "iter/sec",
            "range": "stddev: 5.874138884922965e-7",
            "extra": "mean: 4.589295400604953 usec\nrounds: 113341"
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
          "id": "8e183a5a6d859398f91eda6a2871819f94f4ac4a",
          "message": "refactor: print the statdb tables through the core table.format (merges PR #196, addresses #191)\n\n* refactor: print the statdb tables through the core table.format (part 5 of 5)\n\nThe milestone list, the milestone comparison, the quest lists, the level\nlist and the mob kill list now build rows and columns in the libs and\nprint through plugins.core.utils:table.format, which the plugin injects\nthrough Formatters.table. The libs stay free of bastproxy imports. The\nweb milestone read stays in the worker thread; formatting moves to the\nloop.\n\nCells are now left-aligned, headers use the core colour and each table\nhas a title line. Assertions that only checked the old hand-built layout\nnow check the rows and columns passed to table.format.\n\nAddresses #191\n\nCo-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>\nClaude-Session: https://claude.ai/code/session_01NXu1sbBxFsEQW16MiZv7Je\n\n* refactor: print the statdb cp, gq and mob report tables through table.format\n\nThe cps, gqs and mobs lists and the mob lists of show_cp and show_gq\nnow build rows and columns in the libs and print through the injected\nFormatters.table, like the other statdb tables. Colour stays in the cell\ntext; a no-exp kill colours each of its four xp cells. Assertions that\nonly checked the old hand-built layout now check the rows and columns\npassed to table.format.\n\nAddresses #191\n\nCo-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>\nClaude-Session: https://claude.ai/code/session_01NXu1sbBxFsEQW16MiZv7Je\n\n---------\n\nCo-authored-by: Claude Opus 5.5 <noreply@anthropic.com>",
          "timestamp": "2026-11-27T01:41:44Z",
          "tree_id": "e9e766c2468056f9e3faa765f9f7af2c51f81dc9",
          "url": "https://github.com/endavis/bastproxy-aardwolf/commit/8e183a5a6d859398f91eda6a2871819f94f4ac4a"
        },
        "date": 1795743735903,
        "tool": "pytest",
        "benches": [
          {
            "name": "tests/benchmarks/test_bench_aardu.py::test_bench_convert_level",
            "value": 5673292.2860370455,
            "unit": "iter/sec",
            "range": "stddev: 1.401978476428935e-8",
            "extra": "mean: 176.26449503777079 nsec\nrounds: 58945"
          },
          {
            "name": "tests/benchmarks/test_bench_aardu.py::test_bench_parse_damage_line",
            "value": 288090.0395644516,
            "unit": "iter/sec",
            "range": "stddev: 3.32309941307108e-7",
            "extra": "mean: 3.471137015052128 usec\nrounds: 147929"
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
          "id": "739cbb1bac669c650f823fdb77cd4475b207a5f8",
          "message": "docs: describe eq on a PK death and record the live-checked death timing (merges PR #197, addresses #177)\n\nThe Death bullet in the eq docs now gives the read order a live check of a\ndeath to a mob showed: the {invmon} action 1 and action 3 stream, then the\nempty eqdata, invdata and keyring data replies, none reaching the client.\nIt replaces the \"inferred, not checked live\" wording there and in the\n\"Changed: death\" entry.\n\nIt also covers a PK death, which keeps the equipment: eq still forgets and\nre-reads, so its APIs report an empty character until the re-reads are\nanswered.\n\nAddresses #177\n\n\nClaude-Session: https://claude.ai/code/session_01NXu1sbBxFsEQW16MiZv7Je\n\nCo-authored-by: Claude Opus 5.5 <noreply@anthropic.com>",
          "timestamp": "2026-11-27T09:15:41Z",
          "tree_id": "58cf41992176b799dfc5456ae509930dddf86d3c",
          "url": "https://github.com/endavis/bastproxy-aardwolf/commit/739cbb1bac669c650f823fdb77cd4475b207a5f8"
        },
        "date": 1795770974984,
        "tool": "pytest",
        "benches": [
          {
            "name": "tests/benchmarks/test_bench_aardu.py::test_bench_convert_level",
            "value": 2946664.8369271923,
            "unit": "iter/sec",
            "range": "stddev: 9.304653535105101e-8",
            "extra": "mean: 339.36672656765694 nsec\nrounds: 194629"
          },
          {
            "name": "tests/benchmarks/test_bench_aardu.py::test_bench_parse_damage_line",
            "value": 171765.75497609412,
            "unit": "iter/sec",
            "range": "stddev: 8.861720938204811e-7",
            "extra": "mean: 5.821882249690441 usec\nrounds: 174887"
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
          "id": "5d85cf62c1a492c5c3514328188bb8e1b691f8a8",
          "message": "fix: head the statdb comparison columns in time order (merges PR #199, addresses #198)\n\nformat_comparison built the column headers from the two milestone names\nbefore swapping the rows into time order, so comp 5 3 headed its columns\n5 and 3 while showing milestone 3's values first. The columns are now\nbuilt after the swap, so each header names the milestone whose values\nsit under it. The web comp page shares this path.\n\ntest_compare_one_and_two_names_in_either_order asserted the mislabelled\nheader for comp 5 3; it now expects 3 then 5, as the issue states. A new\ntest checks the headers against the data for both name orders.\n\nAddresses #198\n\n\nClaude-Session: https://claude.ai/code/session_01NXu1sbBxFsEQW16MiZv7Je\n\nCo-authored-by: Claude Opus 5.5 <noreply@anthropic.com>",
          "timestamp": "2026-11-27T09:30:03Z",
          "tree_id": "2ff70b135a582fe8bbe32142466c7f78af661dc8",
          "url": "https://github.com/endavis/bastproxy-aardwolf/commit/5d85cf62c1a492c5c3514328188bb8e1b691f8a8"
        },
        "date": 1795771848386,
        "tool": "pytest",
        "benches": [
          {
            "name": "tests/benchmarks/test_bench_aardu.py::test_bench_convert_level",
            "value": 3659456.80076167,
            "unit": "iter/sec",
            "range": "stddev: 3.7810206047126635e-8",
            "extra": "mean: 273.2646003067621 nsec\nrounds: 199921"
          },
          {
            "name": "tests/benchmarks/test_bench_aardu.py::test_bench_parse_damage_line",
            "value": 198619.58729615866,
            "unit": "iter/sec",
            "range": "stddev: 6.420350031719799e-7",
            "extra": "mean: 5.03475016544524 usec\nrounds: 105776"
          }
        ]
      }
    ]
  }
}