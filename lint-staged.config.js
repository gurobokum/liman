export default {
  "python/**": () => ["pnpm run python:lint", "pnpm run python:typing"],
  "go/**": () => ["pnpm run go:lint"],
};
