# Tutorials

Add each tutorial as its own folder, for example `tutorials/first-screen/`. The folder must be a
complete Ignition project with `project.json` at its root, plus an `item.json` with
`"kind": "tutorial"`. See the root `README.md` for the fields.

The steps a learner follows live on docs.openstudio.no, not in the project; point `docsUrl` at that
page. `first-screen/` is the worked example: an almost empty start view, the OpenBridge stylesheet
and the `font` and `text-color` style classes, and simulated tags in their own folder
`Tutorials/<id>` so they never collide with another item's tags in the `OpenBridge_demo` provider.
