from pathlib import Path


def append_text(target_file: str, text: str) -> dict[str, str]:
    """Append text to a file, creating the file if it does not exist."""
    path = Path(target_file)
    path.parent.mkdir(parents=True, exist_ok=True)

    if path.exists():
        current = path.read_text(encoding="utf-8")
        prefix = "" if current.endswith("\n") or current == "" else "\n"
    else:
        prefix = ""

    with path.open("a", encoding="utf-8") as file_obj:
        file_obj.write(f"{prefix}{text}\n")

    return {
        "changed_file": str(path),
        "appended_text": text,
    }
