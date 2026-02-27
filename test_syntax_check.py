import ast

def check_syntax():
    try:
        with open("Aether_Audio_Archivist_Pro.py", "r") as f:
            ast.parse(f.read())
        print("Syntax OK")
    except SyntaxError as e:
        print(f"Syntax Error: {e}")

if __name__ == "__main__":
    check_syntax()
