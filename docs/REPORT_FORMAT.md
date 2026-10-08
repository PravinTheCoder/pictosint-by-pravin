# Report Format

A JSON report should contain enough information to reproduce the investigation.

Example:

```json
{
  "tool": "PICTOSINT by Pravin",
  "version": "1.0.0",
  "source_image": "/path/to/image.jpg",
  "source_sha256": "<sha256>",
  "candidates": [],
  "satellite": [],
  "verification": {
    "status": "unverified",
    "confidence": "low"
  }
}
```

The implementation may extend this structure as new modules are added.

## Verification rule

Coordinates should be treated as hypotheses until satellite/geometry comparison or another independent verification method supports them.
