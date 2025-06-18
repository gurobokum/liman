# Liman

## Building

```bash
bazel run @rules_go//go -- mod tidy
bazel run //....
```

## Development

- Install [golangci-lint](https://golangci-lint.run/welcome/install/#local-installation)

```bash
bazel run //:gazelle
```
