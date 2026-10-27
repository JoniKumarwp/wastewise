# Local SQLite design

`scripts/initialize.py` creates a seeded `runtime/wastewise.sqlite3`. No server,
MySQL password or administrator account is needed for this local application.

| Table | Meaning |
|---|---|
| categories | Organic, Inorganic and Needs review |
| classes | Stable application key, display name, prompt, category and handling |
| recommendations | One-to-many JSON content records linked to a class |
| scans | Image paths, timestamps, model identity, settings and inference time |
| detections | Box, predicted class, category and score for each numbered proposal |
| feedback | Proposed corrections linked to detections; predictions stay unchanged |

Images are separate PNG files under `runtime/scans/<scan-id>/`. Paths stored
in SQLite are relative to the runtime directory. Boxes use original-image
pixels in `x1,y1,x2,y2` order, after EXIF orientation is applied.

Category mapping is a rule lookup; a model score belongs to object matching,
not an independently trained binary classifier. Every prediction is unverified.
Unmapped custom-model labels receive Needs review.

Use a consistent SQLite backup through the interface instead of copying a
database while it is being written. Keep the image folder when migrating data.
Corrections require human review before any future dataset update. There is
no automatic online learning or collection of user images into the supplied dataset.

This is a local personal workspace, without multi-user authentication. It
binds to loopback by default. A hosted multi-user service would require a
separate deployment design and user-specific storage/access controls.
