Open-source image geolocation and satellite verification tool using visual landmark analysis, OCR, geocoding and satellite imagery.
# PICTOSINT by Pravin

```text
██████╗ ██╗ ██████╗████████╗ ██████╗  ███████╗ ██╗ ███╗   ██╗████████╗
██╔══██╗██║██╔════╝╚══██╔══╝██╔═══██╗ ██╔════╝ ██║ ████╗  ██║╚══██╔══╝
██████╔╝██║██║        ██║   ██║   ██║ ███████╗ ██║ ██╔██╗ ██║   ██║
██╔═══╝ ██║██║        ██║   ██║   ██║╚════ ██║ ██║ ██║╚██╗██║   ██║
██║     ██║╚██████╗   ██║   ╚ ████ ╔╝ ███████║ ██║ ██║ ╚████║   ██║
╚═╝     ╚═╝ ╚═════╝   ╚═╝     ╚════╝  ╚══════╝ ╚═╝ ╚═╝  ╚═══╝   ╚═╝
                         by pravinthehacker
<p align="center">

**Image Geolocation & Satellite Verification Engine**

</p>

<p align="center">

Analyze images, identify visual landmarks, extract textual clues,
generate geographic candidates and verify them using satellite imagery.

</p>

---

## Overview

PICTOSINT by Pravin is an open-source image geolocation and OSINT
tool designed to assist with geographic investigation of photographs.

The tool combines multiple signals:

- OCR
- Multi-scale image analysis
- CLIP zero-shot visual landmark recognition
- Geographic candidate generation
- Nominatim geocoding
- Satellite imagery retrieval
- Candidate comparison
- HTML and JSON reporting

The goal is not to blindly guess a location.

PICTOSINT generates hypotheses that can be independently verified
using geographic and satellite evidence.

---

## Features

### Visual landmark analysis

PICTOSINT uses CLIP zero-shot image recognition to compare an image
against landmark and location descriptions.

This allows the tool to recognize landmark images even when the
photograph contains no readable landmark name.

Example:

A photograph of the Taj Mahal does not need to contain the text
"Taj Mahal".

---

### OCR analysis

The tool performs OCR to extract potentially useful text from images.

OCR may help identify:

- Street names
- Signs
- Buildings
- Organizations
- Geographic names
- Other visible textual clues

OCR output is filtered before being considered for geographic lookup.

Garbage OCR fragments are not intentionally treated as valid locations.

---

### Geographic candidate generation

Potential locations are generated from available evidence.

Candidates may originate from:

- Visual landmark recognition
- Filtered OCR
- Geographic lookup

Each candidate should be treated as a hypothesis rather than confirmed
ground truth.

---

### Satellite verification

PICTOSINT can automatically retrieve satellite imagery for generated
candidate coordinates.

The current implementation uses:

**Esri World Imagery**

Satellite imagery can be used to manually compare:

- Building footprints
- Roads
- Rivers
- Parks
- Courtyards
- Bridges
- Terrain
- Other geographic structures

Example

PICTOSINT by Pravin

Image: taj.jpeg
Visual analysis

    a photograph of the Taj Mahal in Agra India: 99.84%
    a photograph of India Gate in New Delhi India: 0.11%
    an ordinary street in Agra India: 0.04%
    a photograph of Charminar in Hyderabad India: 0.01%
    a photograph of the Gateway of India in Mumbai India: 0.00%
    a photograph of Chennai Central Railway Station in Chennai India: 0.00%

Satellite candidates
#1 Taj Mahal, Agra, Uttar Pradesh, India

27.175144, 78.042142 — CLIP visual landmark match
<img width="768" height="768" alt="candidate_01" src="https://github.com/user-attachments/assets/7dbcfe7a-3461-41c0-9f92-79b7ab48f533" />



---

### Reports

Each investigation produces:

- HTML report
- JSON report
- OCR output
- Satellite imagery
- Satellite candidate sheet

---

# Architecture

```text
                 Input Image
                      |
          +-----------+-----------+
          |                       |
         OCR                 Visual Analysis
          |                       |
          |                     CLIP
          |                       |
          +-----------+-----------+
                      |
              Candidate Generation
                      |
               Geographic Lookup
                      |
                Candidate List
                      |
             Satellite Retrieval
                      |
             Satellite Comparison
                      |
             +--------+--------+
             |                 |
          report.html    report.json
