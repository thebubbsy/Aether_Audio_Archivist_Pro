# This script ensures we are NOT using subprocess for search anymore
import ast
import sys

def check_for_subprocess_usage():
    with open("Aether_Audio_Archivist_Pro.py", "r") as f:
        tree = ast.parse(f.read())

    for node in ast.walk(tree):
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute):
            if node.func.attr == 'create_subprocess_exec':
                print(f"Warning: create_subprocess_exec still in use at line {node.lineno}")

if __name__ == "__main__":
    check_for_subprocess_usage()
