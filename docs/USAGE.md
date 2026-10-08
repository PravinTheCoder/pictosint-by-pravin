# Usage Guide

## Basic command

```bash
python3 pictosint_geo.py IMAGE
```

Example:

```bash
python3 pictosint_geo.py ~/Downloads/taj.jpeg
```

## What the engine should do

The intended pipeline is:

```text
Input image
    |
    +--> SHA-256
    |
    +--> OCR / visual clues
    |
    +--> candidate generation
    |
    +--> geocoding
    |
    +--> satellite imagery
    |
    +--> geometry comparison
    |
    +--> report
```

## Candidate ranking

A useful candidate should be supported by multiple independent clues.

For example:

```text
Text clue        -> candidate city
Building shape  -> candidate location
Road geometry   -> candidate location
Satellite view  -> visual confirmation
```

A single OCR hit should not automatically become the final answer.

## Satellite imagery

The satellite stage should save the imagery or candidate sheet inside the case directory. Prefer storing the candidate coordinate, imagery source, zoom level, and retrieval time alongside the image.

## Confidence

A simple reporting scheme:

- **Low** — weak clue or one source only
- **Medium** — multiple clues agree
- **High** — independent clues plus satellite/geometry verification agree

Do not report a high-confidence location solely because a reverse-image engine labels an image with a famous place.

## Reproducibility

Keep:

- original source image
- SHA-256
- OCR output
- candidate list
- coordinates
- satellite candidate images
- final report
- timestamps
