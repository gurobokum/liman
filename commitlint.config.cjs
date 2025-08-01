// Docs: https://github.com/angular/angular/blob/main/CONTRIBUTING.md#commit

const Configuration = {
  /*
   * Resolve and load @commitlint/config-conventional from node_modules.
   * Referenced packages must be installed
   */
  extends: ["@commitlint/config-conventional"],
  /*
   * Resolve and load @commitlint/format from node_modules.
   * Referenced package must be installed
   */
  formatter: "@commitlint/format",
  /*
   * Any rules defined here will override rules from @commitlint/config-conventional
   */
  rules: {
    "type-enum": [
      2,
      "always",
      [
        "build",
        "chore",
        "ci",
        "docs",
        "feat",
        "feat_go",
        "feat_py",
        "feat_ts",
        "fix",
        "fix_go",
        "fix_py",
        "fix_ts",
        "perf",
        "refactor",
        "refactor_go",
        "refactor_py",
        "refactor_ts",
        "revert",
        "style",
        "test",
        // custom
        "release",
      ],
    ],
    "scope-enum": [
      2,
      "always",
      [
        "core",
        "ui",
        "api",
        "auth",
        "db",
        "deps",
        "config",
        "ci",
        "scripts",
        // custom
        "liman",
        "liman_core",
        "liman_finops",
        "liman_openapi",
      ],
    ],
  },
  /*
   * Array of functions that return true if commitlint should ignore the given message.
   * Given array is merged with predefined functions, which consist of matchers like:
   *
   * - 'Merge pull request', 'Merge X into Y' or 'Merge branch X'
   * - 'Revert X'
   * - 'v1.2.3' (ie semver matcher)
   * - 'Automatic merge X' or 'Auto-merged X into Y'
   *
   * To see full list, check https://github.com/conventional-changelog/commitlint/blob/master/%40commitlint/is-ignored/src/defaults.ts.
   * To disable those ignores and run rules always, set `defaultIgnores: false` as shown below.
   */
  ignores: [(commit) => commit === ""],
  /*
   * Whether commitlint uses the default ignore rules, see the description above.
   */
  defaultIgnores: true,
  /*
   * Custom URL to show upon failure
   */
  helpUrl:
    "https://github.com/conventional-changelog/commitlint/#what-is-commitlint",
  /*
   * Custom prompt configs
   */
  prompt: {
    messages: {},
    questions: {
      type: {
        description: "please input type:",
      },
    },
  },
};

module.exports = Configuration;
