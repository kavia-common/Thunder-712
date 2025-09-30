# Thunder-712 Static Analysis Report

Generated: 2025-09-30 (UTC)
Scope: Thunder-712 (C++ and CMake)

Tools used:
- cpplint (C/C++ style linter) via `python3 -m cpplint`
- cmakelint (CMake style linter) via `cmakelint`

Environment notes:
- Python-based linters (cpplint and cmakelint) were installed and executed.
- System-level tools like clang-tidy/cppcheck were not available due to environment restrictions. Guidance to run these deeper analyzers is provided in the Recommendations section.

How to install tools locally if missing:
- python3 -m pip install --user cpplint cmakelint

Summary of findings (representative):
- cpplint highlighted common style issues across core files:
  - Include order
  - Namespace indentation
  - Brace placement
  - Long lines (>80 chars)
  - Spacing around parentheses and operators
  - Use of C types (e.g., long) flagged by runtime/int category
  - Occasional C-style casts

- cmakelint on top-level CMakeLists.txt found:
  - Lines exceeding 80 characters
  - Extra spaces between commands and parentheses
  - Inconsistent indentation
  - Trailing whitespace
  - Minor readability issues (endif usage)

Representative cpplint issues

Example: Source/core/SystemInfo.cpp (selected)
- Thunder-712/Source/core/SystemInfo.cpp:43: Found C system header after C++ system header. Should be: SystemInfo.h, c system, c++ system, other. [build/include_order] [4]
- Thunder-712/Source/core/SystemInfo.cpp:47: Missing space after , [whitespace/comma] [3]
- Thunder-712/Source/core/SystemInfo.cpp:54-58: Extra space before ( in function call [whitespace/parens] [4]
- Thunder-712/Source/core/SystemInfo.cpp:57,58: Use int16_t/int64_t/etc, rather than the C type long [runtime/int] [4]
- Thunder-712/Source/core/SystemInfo.cpp:71-79: Do not indent within a namespace; brace should be on previous line [whitespace/indent_namespace, whitespace/braces] [4]
- Thunder-712/Source/core/SystemInfo.cpp:100-108: Lines should be <= 80 characters long [whitespace/line_length] [2]
- Thunder-712/Source/core/SystemInfo.cpp:157-161,176-178: Missing spaces around = [whitespace/operators] [4]
- Thunder-712/Source/core/SystemInfo.cpp:192-210: Missing spaces before ( in while/if; trailing whitespace on multiple lines [whitespace/parens, whitespace/end_of_line] [4]
- Thunder-712/Source/core/SystemInfo.cpp:225: Using C-style cast; prefer reinterpret_cast [readability/casting] [4]

Example: Source/core/WarningReportingControl.h (selected)
- Many lines exceed 80 characters [whitespace/line_length] [2]
- Indentation inside namespace flagged [whitespace/indent_namespace] [4]
This header contains a large number of long lines; consider wrapping or reformatting to improve readability and meet style guidelines.

Representative cmakelint issues

Top-level CMakeLists.txt (selected)
- Line 33: Lines should be <= 80 characters long [linelength]
- Lines 33,35,36,38: Line ends in whitespace [whitespace/eol]
- Lines 36–38, 76–79: Weird indentation; use 2 spaces [whitespace/indent]
- Lines 40, 50, 128, 147: Extra spaces between command and parentheses [whitespace/extra]
- Line 99: Mismatching spaces inside () after command [whitespace/mismatch]
- Line 111: Expression repeated inside endif; better to use only endif() [readability/logic]
Total reported for top-level CMakeLists.txt: 27 style issues

Security-oriented grep checks (quick heuristic scan)
- Insecure C string APIs (strcpy/strcat/sprintf/gets): none found in a quick scan
- Safer variants (strncpy/strncat/snprintf): present in places; ensure length checks are correct where used
Note: A comprehensive security analysis should be performed with clang-tidy/cppcheck and code review.

Recommendations and next steps

1) Quick wins (style/formatting)
- Normalize include ordering (project header, C system, C++ system, then others).
- Fix spacing around operators and parentheses; remove trailing whitespace.
- Reformat long lines in headers like WarningReportingControl.h to <= 100 (or 120) chars as a practical project-specific rule, then adjust linter config accordingly.
- Avoid indenting inside namespaces; keep opening braces on the previous line per style.
- Replace C-style casts with C++ casts where reasonable.
- Prefer fixed-width integer types (int32_t, int64_t) over platform-dependent types (long) when ABI correctness matters.

2) CMake hygiene
- Standardize to 2-space indentation, remove trailing whitespace.
- Avoid extra spaces between command names and parentheses.
- Keep lines <= 80 characters (or update a documented project standard and linter config if adopting a wider limit).
- Use plain endif() without condition when possible (readability/logic).

3) Deeper static analysis (clang-tidy/cppcheck)
- Generate compile database (compile_commands.json) and run clang-tidy:
  - mkdir -p build && cd build
  - cmake -DCMAKE_EXPORT_COMPILE_COMMANDS=ON ..
  - clang-tidy -p build $(git ls-files '*.cpp' '*.cc' '*.cxx')
- Suggested checks: modernize-*, readability-*, performance-*, bugprone-*, cppcoreguidelines-*, hicpp-*
- Run cppcheck for additional diagnostics:
  - cppcheck --enable=all --inconclusive --std=c++17 --project=build/compile_commands.json

4) CI integration
- Add a lint job that runs cpplint and cmakelint on changed files.
- Optionally add clang-tidy with a baseline (using NOLINT suppressions where justified).

How to reproduce this analysis locally

- Install tools:
  - python3 -m pip install --user cpplint cmakelint
- Option A: Use helper script in repo:
  - python3 Utils/StaticAnalysis/run_static_analysis.py --repo-root Thunder-712 --out Thunder-712/docs/static-analysis/report-local.md
- Option B: Run directly:
  - python3 -m cpplint $(git -C Thunder-712 ls-files '*.cpp' '*.cc' '*.cxx' '*.h' '*.hpp' '*.hh' '*.hxx')
  - cmakelint Thunder-712/CMakeLists.txt Thunder-712/Source/CMakeLists.txt Thunder-712/cmake/**/*.cmake

Notes

- This report is an initial pass emphasizing style and hygiene using cpplint/cmakelint. A full pass with clang-tidy/cppcheck is recommended for correctness, performance, and security diagnostics.
- Some style warnings (e.g., 80-character limit) may be tuned to match the project's preferred standards; document any deviations in a linter config.
