# Architecture

PICTOSINT is intended as a modular geolocation pipeline.

```text
                    +------------------+
                    |   Source Image   |
                    +--------+---------+
                             |
              +--------------+--------------+
              |                             |
       +------v------+               +------v------+
       | Image Hash  |               | OCR Engine  |
       +-------------+               +------+------+
                                            |
                                     +------v------+
                                     | Clue Parser |
                                     +------+------+
                                            |
                                     +------v------+
                                     | Candidates  |
                                     +------+------+
                                            |
                                     +------v------+
                                     | Geocoder    |
                                     +------+------+
                                            |
                                     +------v------+
                                     | Satellite   |
                                     +------+------+
                                            |
                                     +------v------+
                                     | Verification|
                                     +------+------+
                                            |
                                     +------v------+
                                     | JSON/Report |
                                     +-------------+
```

## Design principle

The engine should separate:

1. clue extraction
2. candidate generation
3. candidate verification
4. final reporting

This prevents a weak clue from being silently promoted to a confirmed location.
