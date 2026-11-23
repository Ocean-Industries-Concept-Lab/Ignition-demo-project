import json
import subprocess
import sys
import tempfile
import unittest
import zipfile
from pathlib import Path

SCRIPT = Path(__file__).resolve().parent / "build_catalog.py"


def item_json(item_id, kind, project_name, **overrides):
    item = {
        "id": item_id,
        "kind": kind,
        "title": item_id.title(),
        "description": "Description",
        "projectName": project_name,
        "runnable": False,
    }
    item.update(overrides)
    return {key: value for key, value in item.items() if value is not None}


class BuildCatalogTest(unittest.TestCase):
    def setUp(self):
        temp = tempfile.TemporaryDirectory()
        self.addCleanup(temp.cleanup)
        self.repo = Path(temp.name) / "repo"
        self.out = Path(temp.name) / "out"
        self.repo.mkdir()
        self.git("init", "-q")

    def git(self, *args):
        subprocess.run(["git", *args], cwd=self.repo, check=True)

    def add_item(self, folder, item, project_json=True, files=()):
        root = self.repo / folder
        root.mkdir(parents=True)
        (root / "item.json").write_text(json.dumps(item), encoding="utf-8")
        if project_json:
            (root / "project.json").write_text("{}", encoding="utf-8")
        resource = root / "com.inductiveautomation.perspective" / "view.json"
        resource.parent.mkdir()
        resource.write_text("{}", encoding="utf-8")
        for name, content in files:
            path = root / name
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(content)

    def build(self):
        self.git("add", "-A")
        return subprocess.run(
            [sys.executable, "-I", str(SCRIPT), "--version", "v9", "--out", str(self.out)],
            cwd=self.repo,
            capture_output=True,
            text=True,
        )

    def built_bundle(self):
        result = self.build()
        self.assertEqual(result.returncode, 0, result.stderr)
        return zipfile.ZipFile(self.out / "OpenBridge_content_v9.zip")

    def item_names(self, bundle, item_id):
        with zipfile.ZipFile(bundle.open(f"items/{item_id}.zip")) as item:
            return set(item.namelist())

    def assert_rejected(self, mentions):
        result = self.build()
        self.assertNotEqual(result.returncode, 0)
        self.assertIn(mentions, result.stderr)

    def test_packs_project_at_zip_root(self):
        self.add_item("templates/pid", item_json("pid", "template", "Pid_template"))
        with self.built_bundle() as bundle:
            names = self.item_names(bundle, "pid")
        self.assertIn("project.json", names)
        self.assertIn("com.inductiveautomation.perspective/view.json", names)

    def test_excludes_item_json_tags_and_preview(self):
        self.add_item(
            "demos/full-demo",
            item_json(
                "full-demo",
                "demo",
                "Full_demo",
                runnable=True,
                tags="tags/default-tags.json",
                image="preview.png",
                imageAlt="Preview",
            ),
            files=[("tags/default-tags.json", b"{}"), ("preview.png", b"png")],
        )
        with self.built_bundle() as bundle:
            names = self.item_names(bundle, "full-demo")
            self.assertEqual(bundle.read("items/full-demo.tags.json"), b"{}")
            self.assertEqual(bundle.read("items/full-demo.png"), b"png")
            catalog = json.loads(bundle.read("catalog.json"))
        self.assertFalse({"item.json", "tags/default-tags.json", "preview.png"} & names)
        self.assertTrue(catalog["items"][0]["hasTags"])
        self.assertTrue(catalog["items"][0]["hasImage"])

    def test_excludes_untracked_and_ignored_files(self):
        self.add_item("templates/pid", item_json("pid", "template", "Pid_template"))
        (self.repo / ".gitignore").write_text(".env.local\n", encoding="utf-8")
        (self.repo / "templates/pid/.env.local").write_text("secret", encoding="utf-8")
        with self.built_bundle() as bundle:
            names = self.item_names(bundle, "pid")
        self.assertNotIn(".env.local", names)

    def test_rejects_duplicate_id(self):
        self.add_item("templates/one", item_json("same", "template", "One"))
        self.add_item("templates/two", item_json("same", "template", "Two"))
        self.assert_rejected("same")

    def test_rejects_duplicate_project_name(self):
        self.add_item("templates/one", item_json("one", "template", "Same"))
        self.add_item("templates/two", item_json("two", "template", "Same"))
        self.assert_rejected("Same")

    def test_rejects_missing_required_field(self):
        self.add_item("templates/pid", item_json("pid", "template", "Pid", title=None))
        self.assert_rejected("title")

    def test_rejects_missing_project_json(self):
        self.add_item(
            "templates/pid",
            item_json("pid", "template", "Pid"),
            project_json=False,
        )
        self.assert_rejected("project.json")

    def test_rejects_kind_not_matching_root_folder(self):
        self.add_item("templates/pid", item_json("pid", "demo", "Pid"))
        self.assert_rejected("kind")

    def test_rejects_tags_on_non_runnable_item(self):
        self.add_item(
            "templates/pid",
            item_json("pid", "template", "Pid", tags="tags/t.json"),
            files=[("tags/t.json", b"{}")],
        )
        self.assert_rejected("runnable")

    def test_rejects_invalid_id(self):
        self.add_item("templates/pid", item_json("../x", "template", "Pid"))
        self.assert_rejected("../x")

    def test_rejects_non_string_image_alt_without_image(self):
        item = item_json("pid", "template", "Pid")
        item["imageAlt"] = None
        self.add_item("templates/pid", item)
        self.assert_rejected("imageAlt")

    def test_empty_tutorials_folder_is_valid(self):
        self.add_item("demos/full-demo", item_json("full-demo", "demo", "Full_demo"))
        (self.repo / "tutorials").mkdir()
        (self.repo / "tutorials/README.md").write_text("Tutorials", encoding="utf-8")
        with self.built_bundle() as bundle:
            catalog = json.loads(bundle.read("catalog.json"))
        self.assertEqual([item["id"] for item in catalog["items"]], ["full-demo"])

    def test_writes_legacy_full_demo_zip_with_project_json_at_root(self):
        self.add_item("demos/full-demo", item_json("full-demo", "demo", "Full_demo"))
        with self.built_bundle() as bundle:
            bundled = bundle.read("items/full-demo.zip")
        legacy = self.out / "OpenBridge_demo_v9.zip"
        self.assertEqual(legacy.read_bytes(), bundled)
        with zipfile.ZipFile(legacy) as archive:
            self.assertIn("project.json", archive.namelist())


if __name__ == "__main__":
    unittest.main()
