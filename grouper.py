
"""
Group files by extension.

Moves every file in a chosen folder (or a whole drive) into subfolders named
after the extension: all .pdf into "PDF", all .docx/.doc into "DOC", etc.

Usage:
    python group_by_extension.py                 (pops up a folder picker)
    python group_by_extension.py "D:\\Downloads"  (use a specific folder)
    python group_by_extension.py "E:\\" -r        (also go through subfolders)
    python group_by_extension.py "D:\\Downloads" --dry-run   (preview only)

Works on Windows, Python 3.8+. No extra packages needed.
"""

import argparse
import shutil
import sys
from pathlib import Path

GROUPS = {
    "DOC": {".doc", ".docx", ".odt", ".rtf"},
    "PDF": {".pdf"},
    "EXCEL": {".xls", ".xlsx", ".csv", ".ods"},
    "POWERPOINT": {".ppt", ".pptx", ".odp"},
    "TEXT": {".txt", ".md", ".log"},
    "IMAGES": {".jpg", ".jpeg", ".png", ".gif", ".bmp", ".webp", ".svg", ".tiff"},
    "VIDEOS": {".mp4", ".mkv", ".avi", ".mov", ".wmv", ".flv"},
    "AUDIO": {".mp3", ".wav", ".flac", ".aac", ".m4a", ".ogg"},
    "ARCHIVES": {".zip", ".rar", ".7z", ".tar", ".gz"},
    "INSTALLERS": {".exe", ".msi"},
}

SKIP_DIRS = {"windows", "program files", "program files (x86)", "programdata",
             "$recycle.bin", "system volume information", "appdata"}


def folder_for(ext: str) -> str:
    """Pick the destination folder name for an extension."""
    for name, exts in GROUPS.items():
        if ext in exts:
            return name
    return ext.lstrip(".").upper() + "_files" if ext else "NO_EXTENSION"


def unique_path(dest: Path) -> Path:
    """If a file with the same name exists, add (1), (2), ... instead of overwriting."""
    if not dest.exists():
        return dest
    i = 1
    while True:
        candidate = dest.with_name(f"{dest.stem} ({i}){dest.suffix}")
        if not candidate.exists():
            return candidate
        i += 1


def collect_files(root: Path, recursive: bool):
    if not recursive:
        return [p for p in root.iterdir() if p.is_file()]
    files = []
    for p in root.rglob("*"):
        if not p.is_file():
            continue
        parts = {part.lower() for part in p.relative_to(root).parts[:-1]}
        if parts & SKIP_DIRS:
            continue
        files.append(p)
    return files


def organize(root: Path, recursive: bool, dry_run: bool):
    files = collect_files(root, recursive)
    if not files:
        print("No files found.")
        return

    target_names = {folder_for(f.suffix.lower()) for f in files}
    moved = skipped = errors = 0

    for f in files:
        ext = f.suffix.lower()
        folder = folder_for(ext)
        dest_dir = root / folder

        if f.parent == dest_dir:
            skipped += 1
            continue
        if recursive and f.parent != root and f.parent.name in target_names and f.parent.parent == root:
            skipped += 1
            continue
        if f.resolve() == Path(__file__).resolve():
            continue

        dest = unique_path(dest_dir / f.name)
        if dry_run:
            print(f"[preview] {f}  ->  {dest}")
            moved += 1
            continue

        try:
            dest_dir.mkdir(exist_ok=True)
            shutil.move(str(f), str(dest))
            print(f"Moved: {f.name}  ->  {folder}\\")
            moved += 1
        except (PermissionError, OSError) as e:
            print(f"Could not move {f}: {e}")
            errors += 1

    verb = "Would move" if dry_run else "Moved"
    print(f"\nDone. {verb} {moved} file(s), skipped {skipped}, errors {errors}.")


def pick_folder() -> str:
    try:
        import tkinter as tk
        from tkinter import filedialog
        tk.Tk().withdraw()
        return filedialog.askdirectory(title="Select a folder or drive to organize")
    except Exception:
        return input("Enter folder or drive path (e.g. D:\\ or C:\\Users\\Me\\Downloads): ").strip('" ')


def main():
    ap = argparse.ArgumentParser(description="Group files into folders by extension.")
    ap.add_argument("path", nargs="?", help="Folder or drive to organize")
    ap.add_argument("-r", "--recursive", action="store_true", help="Include subfolders")
    ap.add_argument("--dry-run", action="store_true", help="Show what would happen, move nothing")
    args = ap.parse_args()

    path = args.path or pick_folder()
    if not path:
        print("Nothing selected.")
        sys.exit(1)

    root = Path(path)
    if not root.is_dir():
        print(f"Not a valid folder: {root}")
        sys.exit(1)

    print(f"Organizing: {root}  (subfolders: {'yes' if args.recursive else 'no'})")
    if not args.dry_run:
        if input("This will move files. Continue? (y/n): ").lower() != "y":
            print("Cancelled.")
            return

    organize(root, args.recursive, args.dry_run)


if __name__ == "__main__":
    try:
        main()
    finally:
        input("\nPress Enter to close...")