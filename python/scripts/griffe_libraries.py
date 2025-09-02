#!/usr/bin/env python3
"""
Parse Python libraries using griffe to extract API information.
"""

from __future__ import annotations

import json
import logging
import sys
from pathlib import Path
from typing import Any, TypedDict

import griffe

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s"
)
logger = logging.getLogger(__name__)


class Parameter(TypedDict):
    name: str
    annotation: str | None
    description: str | None
    value: str | None


class Attribute(TypedDict):
    name: str
    annotation: str | None
    description: str | None
    value: str | None


class Function(TypedDict):
    name: str
    path: str
    signature: str
    description: str | None
    parameters: list[Parameter]
    returns: dict[str, str | None]
    docstring: str | None
    source: str | None


class Class(TypedDict):
    name: str
    path: str
    description: str | None
    parameters: list[Parameter]
    attributes: list[Attribute]
    docstring: str | None
    functions: dict[str, Function]
    source: str | None
    inherited_members: dict[str, list[dict[str, str]]]


class Module(TypedDict):
    name: str
    path: str
    filepath: str | None
    description: str | None
    docstring: str | None
    attributes: list[Attribute]
    modules: dict[str, Module]
    classes: dict[str, Class]
    functions: dict[str, Function]
    version: str | None


def main() -> None:
    """
    Main function to parse all packages in the workspace.
    """
    packages_dir = Path("packages")

    if not packages_dir.exists():
        logger.error(f"Error: {packages_dir} directory not found")
        sys.exit(1)

    results = {}
    for package_path in sorted(packages_dir.glob("[!.]*/")):
        logger.info(f"Parsing {package_path.name}...")
        results[package_path.name] = parse_package(package_path)

    # Output results as JSON
    output_file = Path("library_api_info.json")
    with output_file.open("w") as f:
        json.dump(results, f, indent=2, default=str)

    logger.info(f"Results written to {output_file}")

    # Print summary
    logger.info("Summary:")
    for package_name, info in results.items():
        if "error" in info:
            logger.info(f"  {package_name}: ERROR - {info['error']}")
        else:
            logger.info(f"  {package_name}: Successfully parsed package structure")


def parse_package(package_path: Path) -> dict[str, Any]:
    """
    Parse a Python package using griffe.

    Args:
        package_path: Path to the package directory

    Returns:
        Parsed package information
    """
    try:
        # Find the src directory or use package_path directly
        src_path = package_path / "src"
        search_path = src_path if src_path.exists() else package_path

        # Get package name from the directory structure
        package_name = None
        if src_path.exists():
            # Look for package in src directory
            for item in src_path.iterdir():
                if item.is_dir() and not item.name.startswith("."):
                    package_name = item.name
                    break
        else:
            package_name = package_path.name

        if not package_name:
            raise ValueError(f"Could not determine package name for {package_path}")

        # Load the package using griffe
        loader = griffe.GriffeLoader(search_paths=[str(search_path)])
        package = loader.load(package_name, try_relative_path=True)

        # Parse the module using our structured approach
        return parse_module(package)

    except Exception as e:
        return {
            "error": str(e),
        }


def parse_module(m: griffe.Module) -> Module:
    """Parse a griffe Module into our structured format."""
    if not isinstance(m, griffe.Module):
        raise ValueError("Module must be a module")

    description, docstring = extract_description_and_docstring(m.docstring)
    
    result: Module = {
        "name": m.name,
        "path": m.path,
        "filepath": str(m.filepath) if m.filepath else None,
        "description": description,
        "docstring": docstring,
        "attributes": extract_attributes(m),
        "modules": {
            name: parse_module(value)
            for name, value in m.modules.items()
            if not value.is_alias
        },
        "classes": {
            name: parse_class(value)
            for name, value in m.classes.items()
            if not value.is_alias
        },
        "functions": {
            name: parse_function(value)
            for name, value in m.functions.items()
            if not value.is_alias
        },
        "version": None,
    }
    
    if m.is_package:
        try:
            from importlib.metadata import version
            result["version"] = version(m.name)
        except Exception:
            result["version"] = "unknown"

    return result


def parse_class(c: griffe.Class) -> Class:
    """Parse a griffe Class into our structured format."""
    description, docstring = extract_description_and_docstring(c.docstring)
    
    result: Class = {
        "name": c.name,
        "path": c.path,
        "description": description,
        "parameters": extract_parameters(c) if hasattr(c, 'parameters') else [],
        "attributes": extract_attributes(c),
        "docstring": docstring,
        "functions": {
            name: parse_function(value)
            for name, value in c.functions.items()
            if not value.is_alias
        },
        "source": getattr(c, 'source', None),
        "inherited_members": {},
    }
    
    # Extract inherited members
    if hasattr(c, 'inherited_members'):
        for member in c.inherited_members.values():
            parent_path = ".".join(member.canonical_path.split(".")[:-1])
            member_info = {"kind": str(member.kind), "path": member.canonical_path}
            if parent_path not in result["inherited_members"]:
                result["inherited_members"][parent_path] = []
            result["inherited_members"][parent_path].append(member_info)
    
    return result


def parse_function(f: griffe.Function) -> Function:
    """Parse a griffe Function into our structured format."""
    description, docstring = extract_description_and_docstring(f.docstring)
    
    result: Function = {
        "name": f.name,
        "path": f.path,
        "signature": build_signature(f),
        "description": description,
        "parameters": extract_parameters(f),
        "returns": extract_returns(f),
        "docstring": docstring,
        "source": getattr(f, 'source', None),
    }
    
    return result


def extract_description_and_docstring(docstring: griffe.Docstring | None) -> tuple[str | None, str | None]:
    """Extract description and remaining docstring from griffe docstring."""
    if not docstring:
        return None, None
    
    # Get the first text section as description
    description = None
    remainder_parts = []
    
    if hasattr(docstring, 'parsed') and docstring.parsed:
        for i, section in enumerate(docstring.parsed):
            if section.kind == "text" and i == 0:
                description = section.value
            else:
                remainder_parts.append(str(section.value))
    
    remainder = "\n".join(remainder_parts) if remainder_parts else None
    
    return description, remainder


def extract_parameters(obj: griffe.Class | griffe.Function) -> list[Parameter]:
    """Extract parameters from a griffe object."""
    if not hasattr(obj, 'parameters'):
        return []
    
    return [
        {
            "name": p.name,
            "annotation": str(p.annotation) if p.annotation else None,
            "description": None,  # Could be extracted from docstring
            "value": str(p.default) if p.default is not None else None,
        }
        for p in obj.parameters
    ]


def extract_attributes(obj: griffe.Module | griffe.Class) -> list[Attribute]:
    """Extract attributes from a griffe object."""
    if not hasattr(obj, 'attributes'):
        return []
    
    return [
        {
            "name": attr.name,
            "annotation": str(attr.annotation) if attr.annotation else None,
            "description": str(attr.docstring.parsed) if attr.docstring else None,
            "value": str(attr.value) if hasattr(attr, 'value') and attr.value is not None else None,
        }
        for attr in obj.attributes.values()
        if not attr.is_alias and not getattr(attr, 'is_private', False)
    ]


def extract_returns(func: griffe.Function) -> dict[str, str | None]:
    """Extract return information from a griffe function."""
    return {
        "name": "",
        "annotation": str(func.returns) if func.returns else None,
        "description": None,  # Could be extracted from docstring
    }


def build_signature(func: griffe.Function) -> str:
    """Build a function signature string."""
    if not hasattr(func, 'parameters'):
        return f"{func.name}()"
    
    parameters = func.parameters
    parts = []
    
    positional_only = True
    keyword_only = False
    
    for i, p in enumerate(parameters):
        if i > 0 and positional_only and p.kind in (
            griffe.ParameterKind.positional_or_keyword,
            griffe.ParameterKind.keyword_only,
        ):
            parts.append("/")
            positional_only = False
        
        if p.kind == griffe.ParameterKind.keyword_only and not keyword_only:
            parts.append("*")
            keyword_only = True
        
        if p.kind == griffe.ParameterKind.var_keyword:
            parts.append(f"**{p.name}")
        elif p.kind == griffe.ParameterKind.var_positional:
            parts.append(f"*{p.name}")
        else:
            param_str = p.name
            if p.default is not None:
                param_str += f"={p.default}"
            parts.append(param_str)
    
    signature = f"{func.name}({', '.join(parts)})"
    if func.returns:
        signature += f" -> {func.returns}"
    
    return signature


if __name__ == "__main__":
    main()