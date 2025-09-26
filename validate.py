#!/usr/bin/env python3
"""
MCP Federation Validation Script
Pre-push validation to prevent syntax errors and ensure code quality
"""

import ast
import os
import py_compile
import subprocess
import sys
from pathlib import Path
from typing import List, Tuple

# ANSI color codes
class Colors:
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKCYAN = '\033[96m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'


def check_syntax(file_path: Path) -> Tuple[bool, str]:
    """Check Python file syntax using py_compile"""
    try:
        py_compile.compile(str(file_path), doraise=True)
        return True, "OK"
    except py_compile.PyCompileError as e:
        return False, str(e)


def check_ast(file_path: Path) -> Tuple[bool, str]:
    """Validate Python file using AST parsing"""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            ast.parse(f.read())
        return True, "OK"
    except SyntaxError as e:
        return False, f"Line {e.lineno}: {e.msg}"


def check_parentheses_balance(file_path: Path) -> Tuple[bool, str]:
    """Check if parentheses, brackets, and braces are balanced"""
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()

    # Skip strings and comments for accurate counting
    try:
        tree = ast.parse(content)
        # Remove string content to avoid counting parens in strings
        for node in ast.walk(tree):
            if isinstance(node, ast.Constant) and isinstance(node.value, str):
                content = content.replace(node.value, '')
    except:
        pass  # If AST fails, do basic check anyway

    pairs = {'(': ')', '[': ']', '{': '}'}
    stack = []

    for i, char in enumerate(content):
        if char in pairs.keys():
            stack.append((char, i))
        elif char in pairs.values():
            if not stack:
                return False, f"Unmatched closing '{char}' at position {i}"
            opening, _ = stack.pop()
            if pairs[opening] != char:
                return False, f"Mismatched bracket: '{opening}' with '{char}' at position {i}"

    if stack:
        opening, pos = stack[-1]
        return False, f"Unclosed '{opening}' at position {pos}"

    return True, "Balanced"


def run_import_check(file_path: Path) -> Tuple[bool, str]:
    """Try to import the Python file as a module"""
    try:
        # Get module name from file
        module_name = file_path.stem

        # Try to import it
        result = subprocess.run(
            [sys.executable, "-c", f"import {module_name}"],
            cwd=file_path.parent,
            capture_output=True,
            text=True,
            timeout=5
        )

        if result.returncode == 0:
            return True, "Importable"
        else:
            # Check if it's a script (has if __name__ == '__main__')
            with open(file_path, 'r') as f:
                if "if __name__ == '__main__':" in f.read():
                    return True, "Script (not importable)"
            return False, result.stderr.split('\n')[0] if result.stderr else "Import failed"
    except Exception as e:
        return False, str(e)


def test_installer_help() -> Tuple[bool, str]:
    """Test that the installer can show help without crashing"""
    try:
        result = subprocess.run(
            [sys.executable, "install.py", "--help"],
            capture_output=True,
            text=True,
            timeout=5
        )
        if result.returncode == 0:
            return True, "Help works"
        else:
            return False, "Help command failed"
    except Exception as e:
        return False, str(e)


def validate_all_python_files() -> List[Tuple[str, dict]]:
    """Validate all Python files in the repository"""
    results = []

    # Find all Python files
    python_files = list(Path('.').glob('*.py'))

    for file_path in python_files:
        file_results = {
            'syntax': check_syntax(file_path),
            'ast': check_ast(file_path),
            'balanced': check_parentheses_balance(file_path),
            'import': run_import_check(file_path)
        }
        results.append((str(file_path), file_results))

    return results


def main():
    """Main validation routine"""
    print(f"\n{Colors.HEADER}{Colors.BOLD}")
    print("="*60)
    print("    MCP FEDERATION VALIDATION")
    print("    Pre-Push Code Quality Check")
    print("="*60)
    print(f"{Colors.ENDC}\n")

    # Change to script directory
    script_dir = Path(__file__).parent
    os.chdir(script_dir)

    print(f"{Colors.OKBLUE}Running validation checks...{Colors.ENDC}\n")

    results = validate_all_python_files()

    all_passed = True

    for file_name, checks in results:
        print(f"{Colors.BOLD}{file_name}:{Colors.ENDC}")

        for check_name, (passed, message) in checks.items():
            if passed:
                print(f"  [OK] {check_name.capitalize()}: {message}")
            else:
                print(f"  [FAIL] {check_name.capitalize()}: {message}")
                all_passed = False
        print()

    # Special test for installer
    print(f"{Colors.BOLD}Functional Tests:{Colors.ENDC}")
    help_test = test_installer_help()
    if help_test[0]:
        print(f"  [OK] Installer --help: {help_test[1]}")
    else:
        print(f"  [FAIL] Installer --help: {help_test[1]}")
        all_passed = False

    print()

    if all_passed:
        print(f"{Colors.OKGREEN}{Colors.BOLD}[SUCCESS] ALL VALIDATION CHECKS PASSED!{Colors.ENDC}")
        print(f"{Colors.OKGREEN}Code is ready to push.{Colors.ENDC}\n")
        return 0
    else:
        print(f"{Colors.FAIL}{Colors.BOLD}[ERROR] VALIDATION FAILED!{Colors.ENDC}")
        print(f"{Colors.FAIL}Fix the issues above before pushing.{Colors.ENDC}\n")
        return 1


if __name__ == '__main__':
    sys.exit(main())