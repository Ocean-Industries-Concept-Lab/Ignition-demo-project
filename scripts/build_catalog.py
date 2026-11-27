#!/usr/bin/env python3
import argparse
import io
import json
import re
import subprocess
import sys
import zipfile
from pathlib import Path, PurePosixPath

KINDS = {"demos": "demo", "templates": "template", "tutorials": "tutorial"}
KIND_ORDER = list(KINDS.values())
REQUIRED_TEXT = ("id", "kind", "title", "description", "projectName")
ID_PATTERN = re.compile(r"[a-z0-9-]+")
PROJECT_NAME_PATTERN = re.compile(r"[A-Za-z0-9_]+")
FULL_DEMO_ID = "full-demo"
ZIP_TIMESTAMP = (1980, 1, 1, 0, 0, 0)


class CatalogError(Exception):
    pass


def tracked_files(repo):
    output = subprocess.run(
        ["git", "ls-files", "-z"],
        cwd=repo,
        check=True,
        capture_output=True,
    ).stdout
    paths = (PurePosixPath(name) for name in output.decode("utf-8").split("\0") if name)
    return {path for path in paths if (repo / path).is_file()}


def relative_item_path(folder, item, field):
    value = item.get(field)
    if value is None:
        return None
    path = PurePosixPath(value) if isinstance(value, str) else None
    if path is None or path.is_absolute() or ".." in path.parts or not path.parts:
        raise CatalogError(f"{folder}: {field} must be a path inside the item folder")
    return path


def is_docs_url(value):
    return isinstance(value, str) and value.startswith("https://") and len(value) > len("https://")


def read_item(repo, folder, files):
    try:
        item = json.loads((repo / folder / "item.json").read_text(encoding="utf-8"))
    except json.JSONDecodeError as error:
        raise CatalogError(f"{folder}: item.json is not valid JSON: {error}") from error
    if not isinstance(item, dict):
        raise CatalogError(f"{folder}: item.json must be an object")

    for field in REQUIRED_TEXT:
        if not isinstance(item.get(field), str) or not item[field].strip():
            raise CatalogError(f"{folder}: missing required field {field}")
    if not isinstance(item.get("runnable"), bool):
        raise CatalogError(f"{folder}: missing required field runnable")
    if not ID_PATTERN.fullmatch(item["id"]):
        raise CatalogError(f"{folder}: invalid id {item['id']}")
    if not PROJECT_NAME_PATTERN.fullmatch(item["projectName"]):
        raise CatalogError(f"{folder}: invalid projectName {item['projectName']}")
    if item["kind"] != KINDS[folder.parts[0]]:
        raise CatalogError(f"{folder}: kind must be {KINDS[folder.parts[0]]}")
    if folder / "project.json" not in files:
        raise CatalogError(f"{folder}: project.json is missing")

    tags = relative_item_path(folder, item, "tags")
    image = relative_item_path(folder, item, "image")
    if tags and not item["runnable"]:
        raise CatalogError(f"{folder}: an item with tags must be runnable")
    for path in filter(None, (tags, image)):
        if folder / path not in files:
            raise CatalogError(f"{folder}: {path} is not a tracked file")
    if image and "imageAlt" not in item:
        raise CatalogError(f"{folder}: an item with an image needs imageAlt")
    if "imageAlt" in item and not isinstance(item["imageAlt"], str):
        raise CatalogError(f"{folder}: imageAlt must be text")
    if "docsUrl" in item and not is_docs_url(item["docsUrl"]):
        raise CatalogError(f"{folder}: docsUrl must be an https:// URL")
    return item, tags, image


def read_items(repo, files):
    item_folders = sorted(
        path.parent
        for path in files
        if path.name == "item.json"
        and len(path.parts) == 3
        and path.parts[0] in KINDS
    )
    items = [(folder, *read_item(repo, folder, files)) for folder in item_folders]
    for field in ("id", "projectName"):
        seen = set()
        for folder, item, _, _ in items:
            if item[field] in seen:
                raise CatalogError(f"{folder}: duplicate {field} {item[field]}")
            seen.add(item[field])
    return sorted(items, key=lambda entry: (KIND_ORDER.index(entry[1]["kind"]), entry[1]["id"]))


def write_entry(archive, name, data):
    info = zipfile.ZipInfo(str(name), ZIP_TIMESTAMP)
    info.compress_type = zipfile.ZIP_DEFLATED
    info.external_attr = 0o644 << 16
    archive.writestr(info, data)


def project_zip(repo, folder, files, image):
    excluded = {folder / "item.json"}
    if image:
        excluded.add(folder / image)
    project_files = sorted(
        path
        for path in files
        if folder in path.parents
        and path not in excluded
        and path.relative_to(folder).parts[0] != "tags"
    )
    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, "w") as archive:
        for path in project_files:
            write_entry(archive, path.relative_to(folder), (repo / path).read_bytes())
    return buffer.getvalue()


def catalog_entry(item, tags, image):
    entry = {
        "id": item["id"],
        "kind": item["kind"],
        "title": item["title"],
        "description": item["description"],
        "projectName": item["projectName"],
        "runnable": item["runnable"],
        "hasTags": tags is not None,
        "hasImage": image is not None,
        "imageAlt": item.get("imageAlt", ""),
    }
    if "docsUrl" in item:
        entry["docsUrl"] = item["docsUrl"]
    return entry


def build(repo, version, out):
    files = tracked_files(repo)
    items = read_items(repo, files)
    out.mkdir(parents=True, exist_ok=True)
    catalog = {
        "schema": 1,
        "version": version,
        "items": [catalog_entry(item, tags, image) for _, item, tags, image in items],
    }

    with zipfile.ZipFile(out / f"OpenBridge_content_{version}.zip", "w") as bundle:
        write_entry(bundle, "catalog.json", json.dumps(catalog, indent=2) + "\n")
        for folder, item, tags, image in items:
            item_id = item["id"]
            item_zip = project_zip(repo, folder, files, image)
            write_entry(bundle, f"items/{item_id}.zip", item_zip)
            if tags:
                write_entry(bundle, f"items/{item_id}.tags.json", (repo / folder / tags).read_bytes())
            if image:
                write_entry(bundle, f"items/{item_id}.png", (repo / folder / image).read_bytes())
            if item_id == FULL_DEMO_ID:
                (out / f"OpenBridge_demo_{version}.zip").write_bytes(item_zip)


def main():
    parser = argparse.ArgumentParser(description="Build the OpenBridge content bundle.")
    parser.add_argument("--version", required=True)
    parser.add_argument("--out", required=True, type=Path)
    args = parser.parse_args()
    repo = Path(
        subprocess.run(
            ["git", "rev-parse", "--show-toplevel"],
            check=True,
            capture_output=True,
            text=True,
        ).stdout.strip()
    )
    try:
        build(repo, args.version, args.out)
    except CatalogError as error:
        print(f"error: {error}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
