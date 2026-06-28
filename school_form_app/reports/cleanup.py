"""Remove generated runtime files while protecting authentication data."""

from pathlib import Path


PROTECTED_JSON_FILES = {
    "credentials.json",
    "token.json",
}


def delete_file_safely(path: Path) -> bool:
    try:
        if path.exists() and path.is_file():
            path.unlink()
            return True
    except PermissionError:
        return False
    except OSError:
        return False

    return False


def cleanup_generated_files(project_root: str = ".") -> list[str]:
    root = Path(project_root)
    deleted_files = []

    # 1. Delete root JSON files except credentials.json and token.json
    for json_file in root.glob("*.json"):
        if json_file.name in PROTECTED_JSON_FILES:
            continue

        if delete_file_safely(json_file):
            deleted_files.append(str(json_file))

    # 2. Empty answer_keys folder
    answer_keys_dir = root / "answer_keys"

    if answer_keys_dir.exists():
        for file in answer_keys_dir.glob("*"):
            if file.is_file():
                if delete_file_safely(file):
                    deleted_files.append(str(file))

    # 3. Delete QR code images in root folder
    for qr_file in root.glob("qr_code_*.png"):
        if delete_file_safely(qr_file):
            deleted_files.append(str(qr_file))

    # 4. Delete QR code images in qr_codes folder if you later create it
    qr_codes_dir = root / "qr_codes"

    if qr_codes_dir.exists():
        for qr_file in qr_codes_dir.glob("*.png"):
            if delete_file_safely(qr_file):
                deleted_files.append(str(qr_file))

    return deleted_files