#!/usr/bin/env python3

"""
CI Script for Detecting Changed Packages

This script analyzes Git changes in a GitHub Actions workflow to determine which
packages need to be built, tested, or linted. It supports monorepo setups where
multiple packages coexist in different language ecosystems (Python, TypeScript, Go).

Usage:
    python3 detect_changed_packages.py <type>

Where <type> is one of: python, typescript, go

The script outputs a JSON array of package names that have changes, which can
be consumed by GitHub Actions matrix strategy to run jobs selectively.

Configuration:
Each package type has its own configuration defining:
- paths: Direct package directories that trigger builds
- files: Shared files outside package directories that affect all packages
"""

import json
import os
import subprocess
import sys
from typing import Dict, List, Literal, TypedDict

GITHUB_SHA = os.environ.get("GITHUB_SHA")
GITHUB_BASE_REF = os.environ.get("GITHUB_BASE_REF")
GITHUB_EVENT_NAME = os.environ.get("GITHUB_EVENT_NAME")


class PackageConfig(TypedDict):
    paths: List[str]
    files: List[str]


PY_PACKAGES_CONFIG: Dict[str, PackageConfig] = {
    "liman": {
        "paths": ["python/packages/liman/"],
        "files": [
            "python/pyproject.toml",
            "python/uv.lock",
        ],
    },
    "liman_core": {
        "paths": ["python/packages/liman_core/"],
        "files": [
            "python/pyproject.toml",
            "python/uv.lock",
        ],
    },
    "liman_finops": {
        "paths": ["python/packages/liman_finops/"],
        "files": [
            "python/pyproject.toml",
            "python/uv.lock",
        ],
    },
    "liman_openapi": {
        "paths": ["python/packages/liman_openapi/"],
        "files": [
            "python/pyproject.toml",
            "python/uv.lock",
        ],
    },
}

TS_PACKAGES_CONFIG: Dict[str, PackageConfig] = {
    "liman_core": {
        "paths": ["typescript/packages/liman_core/"],
        "files": [
            "typescript/package.json",
            "typescript/pnpm-lock.yaml",
        ],
    },
}

GO_PACKAGES_CONFIG: Dict[str, PackageConfig] = {
    "liman_core": {
        "paths": ["go/pkg/liman_core/"],
        "files": [
            "go/go.mod",
            "go/go.sum",
        ],
    },
}


def get_packages_config(
    type_: str,
) -> Dict[str, PackageConfig]:
    """
    Get the configuration for packages based on the type.
    """
    if type_ == "python":
        return PY_PACKAGES_CONFIG
    elif type_ == "typescript":
        return TS_PACKAGES_CONFIG
    elif type_ == "go":
        return GO_PACKAGES_CONFIG
    else:
        raise ValueError(f"Unsupported package type: {type_}")


def get_changed_files() -> List[str] | Literal["ALL_FILES"]:
    """
    Get list of changed files based on GitHub event type.
    """
    if GITHUB_EVENT_NAME == "push":
        result = subprocess.run(
            ["git", "diff", "--name-only", f"{GITHUB_SHA}^..{GITHUB_SHA}"],
            capture_output=True,
            text=True,
            check=True,
        )
    elif GITHUB_EVENT_NAME == "pull_request":
        if not GITHUB_BASE_REF:
            raise ValueError("GITHUB_BASE_REF is not set for pull_request event")
        subprocess.run(["git", "fetch", "origin", GITHUB_BASE_REF], check=True)
        result = subprocess.run(
            ["git", "diff", "--name-only", f"origin/{GITHUB_BASE_REF}..HEAD"],
            capture_output=True,
            text=True,
            check=True,
        )
    elif GITHUB_EVENT_NAME == "workflow_dispatch":
        return "ALL_FILES"
    else:
        raise ValueError(f"Unsupported GitHub event: {GITHUB_EVENT_NAME}")

    return result.stdout.strip().split("\n") if result.stdout.strip() else []


def detect_changed_packages(type_: str, changed_files: List[str]) -> List[str]:
    """
    Detect which packages have changes based on file paths and triggers.
    """
    packages_config = get_packages_config(type_)
    packages = []

    # If workflow files changed, include all packages
    workflow_prefix = f".github/workflows/{type_}-"
    if any(file.startswith(workflow_prefix) for file in changed_files):
        return list(packages_config.keys())

    for package, config in packages_config.items():
        package_changed = False

        # Check direct paths
        for path in config["paths"]:
            if any(file.startswith(path) for file in changed_files):
                package_changed = True
                break

        # Check files outside of paths
        if not package_changed:
            for file in config["files"]:
                if file in changed_files:
                    package_changed = True
                    break

        if package_changed:
            packages.append(package)

    return packages


def main() -> None:
    """
    Main function to detect changed packages and output JSON.
    """
    if len(sys.argv) != 2:
        print("Usage: detect_changed_packages.py <type>", file=sys.stderr)
        print("Supported types: python, typescript, go", file=sys.stderr)
        sys.exit(1)

    type_ = sys.argv[1]

    try:
        changed_files = get_changed_files()

        if changed_files == "ALL_FILES":
            packages = list(get_packages_config(type_).keys())
        elif not changed_files:
            packages = []
        else:
            packages = detect_changed_packages(type_, changed_files)

        print(json.dumps(packages))

    except subprocess.CalledProcessError as e:
        print(f"Error running git command: {e}", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"Unexpected error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
