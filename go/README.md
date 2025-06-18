# Liman

## Development

```bash
bazel run //:gazelle
```

## Building

```bash
bazel run @rules_go//go -- mod tidy
bazel run //....
```
