# Yahaha Cover Studio History Storage Schema

Both the Docker application and MoviePilot plugin use schema version `1` for new history data.

```text
history/
  index.json
  batches/<batch_id>/manifest.json
  batches/<batch_id>/servers/<server_id>/libraries/<library_id>/cover.<ext>
  batches/<batch_id>/servers/<server_id>/libraries/<library_id>/thumbnail.webp
```

`batch_id` is UTC `YYYYMMDDTHHMMSS.mmmZ_<six-hex>`; it is globally unique and sortable. A manifest records the trigger (`manual`, `schedule`, `monitor`, `api`), mode, status, immutable server/library IDs, display names, output template, hash, dimensions, stored path and upload status. `index.json` contains lightweight summaries only.

Library keys are `server_id:library_id`; local mode is `local:<library_id>`. Files are written under `.tmp/<batch_id>` and moved into `batches/` only after the manifest is finalized. Retention is evaluated per `library_key`: over-limit item files are removed from their manifests, and an empty batch is removed only after no library item remains.

Legacy flat files are imported once into `server_id=legacy` records without deleting the original files. The marker `history/.migration_v1_complete` makes this resumable and idempotent. Future restore operations must resolve `batch_id`, `server_id`, `library_id` from the manifest, validate the contained relative path and SHA-256, then upload the stored cover without creating another generation batch.
