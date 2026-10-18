from pathlib import Path

current_file = Path(__file__).resolve()
current_dir = current_file.parent

for filepath in current_dir.iterdir():
    if filepath.is_file() and filepath.resolve() != current_file:
        print(filepath.read_text(encoding="utf-16"))
