export default {
  "python/**": () => ["pnpm run python:lint", "pnpm run python:typing"],
  "go/**": () => ["pnpm run go:lint"],
  "docs/**": () => ["pnpm run docs:lint", "pnpm run docs:format:check"],
  "typescript/**": () => [
    "pnpm run typescript:lint",
    "pnpm run typescript:format:check",
  ],
};
