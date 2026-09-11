# Project instructions

This directory is the root of the standalone `mech_animation_library` Git repository. Treat it as a maintained project, not a disposable artifacts folder.

## Working in this repository

- Run Git commands from this repository. Inspect status and preserve the user's existing changes before editing.
- Keep project-specific documentation and tooling here. Do not assume scripts or dependencies in the parent GrimGames workspace are available to other contributors.
- Keep changes focused and reviewable. Report validation results and whether changes are committed or pushed accurately.
- Do not remove files merely because they are generated: GIF previews, the contact sheet, HTML, manifest, and verification reports are project deliverables.

## Gallery contract

- `index.html` is the main entry point. Keep the current `revision_N.html` page named by the manifest's revision working as well, since existing bookmarks use it.
- The gallery must work offline after cloning or extracting a release, without a build step or web server.
- Keep clips in numeric order by their label prefix. Preserve existing clip numbers and filenames when adding clips.
- `manifest.json` records the clip inventory, timing, revision, and verification data. Update it with relevant animation changes.
- Keep relative asset links portable. HTML, GIFs, contact sheet, and notes must agree about which revision they describe; identify any previews retained from an earlier model revision.
- Preserve the 24 fps, in-place gameplay animation convention. Preview controller travel is distinct from gameplay root motion.
- Do not claim that this repository contains editable Blender Actions or the source model unless those files have actually been added.

## Generated files and validation

- Keep raw `frame_*.png` render sequences, temporary builds, and ZIP packages out of Git. Retain final GIFs and intentional review images.
- Use project-relative paths in new tools. The previous render/packaging scripts outside this repository are legacy local tools, not a reproducible build provided by this project.
- Run `python tools/validate_gallery.py` after changing gallery assets, HTML, or the manifest. Also visually review any changed previews.
- Check `git diff --check` before handing changes back.
- For live Blender changes, use the Blender MCP skill. Respect the user's save instructions and release the Blender claim when finished.
