# Ignition-demo-project

The demos, templates and tutorials offered on the OpenBridge module's Config page. Users install
only the items they need. Each item is a self-sufficient Ignition project.

```text
demos/<name>/       runnable applications
templates/<name>/   inheritable projects used as a parent
tutorials/<name>/   guided examples
scripts/            builds and tests the release bundle
```

## Add an item

1. Create a folder under `demos`, `templates` or `tutorials` containing a complete project, with
   `project.json` at its root. Copy any shared style classes it needs.
2. Add `item.json`:

   ```json
   {
     "id": "my-item",
     "kind": "template",
     "title": "My template",
     "description": "Shown on the Config page.",
     "projectName": "OpenBridge_my_template",
     "runnable": false,
     "image": "preview.png",
     "imageAlt": "Describes the preview image"
   }
   ```

   `kind` must match the root folder (`demo`, `template` or `tutorial`). `id` uses lowercase
   letters, digits and hyphens. `projectName` uses letters, digits and underscores. Both must be
   unique. `image`, `imageAlt`, `tags` and `docsUrl` are optional, but an image needs `imageAlt`.
   `docsUrl` must start with `https://`; the Config page shows it as a link on the item's card
   ("Follow the tutorial" for a tutorial, "Read the docs" otherwise).

   A `runnable` item is installed with its inheritable flag off. `tags` is the path of a tag export
   in the item's `tags/` folder. An item with tags must be runnable. Its tags are imported into the
   `OpenBridge_demo` provider and its bindings are pointed there.
3. Check it. Only files tracked by git are packaged, so `git add` the item first:

   ```bash
   python3 -I scripts/test_build_catalog.py
   python3 -I scripts/build_catalog.py --version local --out /tmp/openbridge-content
   ```

4. Run the **Release** workflow, then pin the new release in the module's
   `gateway/build.gradle.kts`. The item reaches users with the next module release.

## Release assets

- `OpenBridge_content_<version>.zip` holds the catalog and every item. The module bundles it.
- `OpenBridge_demo_<version>.zip` is the full demo as a directly importable project.

## Develop an item on a local gateway

The repo root is not a project, and Ignition 8.3 ignores a symlinked project folder. Keep the
checkout outside the gateway's projects folder and sync the item into it after each `git pull`:

```bash
rsync -a --delete \
  --exclude=/project.json --exclude=/item.json --exclude=/tags/ --exclude=/preview.png \
  demos/full-demo/ /usr/local/ignition/data/projects/<project>/
```

`--delete` removes anything in the target that is not in the repo, including unsaved Designer
work. `project.json` is excluded so the gateway's own project settings survive, so copy it once
when creating the project and set `inheritable` to `false` for a runnable project. Then scan the
projects.
