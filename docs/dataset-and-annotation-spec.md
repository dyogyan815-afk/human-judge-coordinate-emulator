# Dataset and Annotation Specification — BOTB Spot the Ball Research Dataset

**Status:** Draft for research and annotation planning  
**Dataset version:** `v0.1.0`  
**Source context:** [BOTB Spot the Ball](https://www.botb.com/spot-the-ball?cguid=7a421ee0-f1a2-4198-a1b0-147e465ec461)

## 1. Scope and research objective

This specification defines a dataset for studying whether a model can emulate independent human decisions about the likely location of the centre of a missing football in a football photograph.

The target is a **human-decision location**, not an asserted physical truth. The model must be evaluated against independently collected human annotations and, where legally and operationally available, separately against the official adjudicated result.

The project is for research, benchmarking, and error analysis. It must not automate entries, submissions, account activity, payment, gameplay, or interaction with prize-game interfaces.

## 2. Source and provenance

Each source item must record provenance without relying on a temporary session URL as its identity.

Required provenance fields:

- `source_provider`: `BOTB`
- `source_page_url`: canonical public page URL, if permitted for the dataset record
- `source_competition_id`: provider identifier, if publicly available
- `source_image_id`: provider identifier, if publicly available
- `source_capture_timestamp`: when the research copy was acquired
- `source_publication_timestamp`: if available
- `source_terms_reviewed_at`: timestamp of the licensing/terms review
- `usage_permission`: `licensed`, `public-research-permitted`, `unknown`, or `restricted`
- `provenance_notes`

Do not redistribute source images unless the project has permission to do so. If redistribution is not permitted, store a secure content hash and a controlled local/object-storage reference instead.

## 3. Dataset unit definitions

### 3.1 Image instance

One image instance is one immutable research copy of a source photograph, identified by `image_id` and its SHA-256 hash.

### 3.2 Human annotation

One annotation is one independent coordinate decision made by one annotator without seeing other annotators' decisions for that image.

### 3.3 Adjudicated reference, if available

An official or panel-selected location is stored as a separate reference type. It must never silently replace individual human annotations or be treated as objective ground truth.

### 3.4 Image family

Images that are the same frame, near-duplicates, resized copies, crops, screenshots, or variants from the same sequence belong to one `image_family_id` and must remain in one split.

## 4. Coordinate convention

Use image-native pixel coordinates throughout the annotation database:

- origin: top-left pixel
- x: increases left to right
- y: increases top to bottom
- image width: `W` pixels
- image height: `H` pixels
- valid integer pixel coordinates: `x ∈ [0, W-1]`, `y ∈ [0, H-1]`

For a continuous click coordinate, use the closed display-space convention `x ∈ [0, W]`, `y ∈ [0, H]` during capture, then convert to the canonical pixel-center convention before storage. The conversion must be implemented once and tested.

Never mix browser/CSS coordinates, displayed-image coordinates, source-image coordinates, and normalized coordinates without recording the transformation.

Normalized values may be derived as:

```text
x_normalized = x / (W - 1)
y_normalized = y / (H - 1)
```

The original pixel coordinate remains authoritative.

## 5. Image manifest schema

One row/object per image:

```json
{
  "image_id": "botb_img_000001",
  "image_family_id": "botb_family_000001",
  "image_path": "controlled://images/botb_img_000001.jpg",
  "original_image_path": "controlled://originals/botb_img_000001.jpg",
  "image_hash_sha256": "sha256:<64 hex characters>",
  "perceptual_hash": "<algorithm-specific value>",
  "width": 1920,
  "height": 1080,
  "format": "JPEG",
  "file_size_bytes": 123456,
  "source_provider": "BOTB",
  "source_page_url": "https://www.botb.com/spot-the-ball",
  "source_competition_id": null,
  "source_image_id": null,
  "capture_timestamp": "2026-09-26T12:00:00Z",
  "publication_timestamp": null,
  "scene_categories": ["football", "multiple_players", "wide_shot"],
  "image_status": "usable",
  "usage_permission": "unknown",
  "dataset_version": "v0.1.0"
}
```

### Required image fields

- unique `image_id`
- `image_family_id`
- immutable SHA-256 hash
- width and height
- source and provenance status
- image format and integrity status
- dataset version

### Image integrity rules

- Decode the image successfully before annotation.
- Store the hash of the exact bytes used for annotation.
- Do not silently overwrite an image at an existing `image_id`.
- A changed image receives a new `image_id` and a new hash.
- Preserve original dimensions even when generating resized or cropped derivatives.

## 6. Annotation schema

One row/object per independent decision:

```json
{
  "annotation_id": "botb_ann_000001",
  "image_id": "botb_img_000001",
  "image_hash_sha256": "sha256:<64 hex characters>",
  "annotator_id": "human_017",
  "annotator_group": "trained_generalist",
  "x": 742.0,
  "y": 391.0,
  "x_normalized": 0.3861,
  "y_normalized": 0.3620,
  "coordinate_space": "source_pixel_center",
  "annotation_timestamp": "2026-09-26T12:03:14Z",
  "annotation_duration_ms": 8420,
  "interface_version": "annotation-ui-1.0.0",
  "instruction_version": "instructions-1.0.0",
  "annotation_quality": "valid",
  "annotator_confidence": null,
  "notes": null
}
```

### Annotation rules

- Annotators must make decisions independently.
- Do not reveal previous annotations, consensus points, official results, or winner locations before submission.
- Permit one confirmed coordinate per annotation task unless the protocol explicitly defines repeated trials.
- Record reset events and abandoned tasks separately from confirmed annotations.
- Do not infer a coordinate from a screenshot, filename, URL, or page metadata.
- Do not discard disagreement as noise before analysis.

## 7. Optional adjudicated-reference schema

If an official/panel result is lawfully available for research, store it separately:

```json
{
  "reference_id": "botb_ref_000001",
  "image_id": "botb_img_000001",
  "reference_type": "official_adjudication",
  "x": 744.0,
  "y": 390.0,
  "coordinate_space": "source_pixel_center",
  "published_timestamp": "2026-10-03T12:00:00Z",
  "source_url": null,
  "evidence_path": "controlled://references/botb_ref_000001.json",
  "verification_status": "pending",
  "notes": "Not used as a substitute for independent human labels."
}
```

The reference must include its provenance and verification status. If the provider's judging process is not available or cannot be verified, leave this record absent rather than inventing a target.

## 8. Annotation interface requirements

The annotation application should:

1. Load the source image at a known scale.
2. Preserve aspect ratio.
3. Convert display coordinates to source-image coordinates using one tested function.
4. Show the selected point and numeric x/y values.
5. Offer `Confirm` and `Reset`.
6. Prevent accidental submission before confirmation.
7. Record interface and instruction versions.
8. Avoid showing any other person's coordinate.
9. Support keyboard accessibility without changing coordinate semantics.
10. Store an audit event for load, click, reset, confirm, and failure.

The UI may provide neutral image inspection such as zooming, but any zoom/pan transformation must be inverted exactly before storage. Do not add tools that submit or interact with the live BOTB competition.

## 9. Annotator protocol

Before annotation, provide the same written instructions to every annotator:

- identify the likely centre of the missing football
- click once at the selected location
- use the displayed photograph and the defined coordinate convention
- do not consult other annotations or external answers
- confirm only when satisfied

Recommended sampling:

- minimum: 3 independent annotators per image
- target: 5 annotators per image
- strong agreement study: 10 or more annotators per image

Balance annotator workload and randomize image order. Include repeated blind images in a quality study only if the protocol labels them explicitly; do not treat repeated trials as independent people.

## 10. Scene and difficulty metadata

Use multi-label categories where applicable:

- `clear_scene`
- `crowded_scene`
- `occlusion`
- `multiple_players`
- `motion_blur`
- `perspective`
- `close_up`
- `wide_shot`
- `low_contrast`
- `high_contrast`
- `unusual_camera_angle`
- `partial_visibility`
- `complex_background`
- `small_target_context`

Difficulty labels should be assigned independently of model predictions. Record who assigned them and which rubric version was used.

## 11. Quality assurance and validation

A dataset validation job must fail on:

- missing required fields
- duplicate `image_id` or `annotation_id`
- invalid SHA-256 format
- image hash mismatch
- unreadable image
- non-positive dimensions
- coordinates outside bounds
- normalized coordinates inconsistent with pixel coordinates
- annotation linked to an unknown image
- missing annotator or timestamp
- split assignment missing
- source-permission status missing

Quarantine invalid records rather than silently deleting them. Produce a validation report with counts, IDs, and reasons.

## 12. Leakage prevention

Run all of the following before assigning splits:

- exact SHA-256 duplicate detection
- perceptual-hash nearest-neighbour comparison
- image-dimension and crop relationship checks
- sequence/frame and source-ID grouping
- embedding similarity checks where permitted
- filename and metadata leakage review
- annotation and reference leakage review

The split unit is `image_family_id`, not an annotation row. No family may occur across train, validation, test, or final holdout.

Recommended split:

- train: 70%
- validation: 15%
- test: 15%
- final holdout: separate and untouched where dataset size permits

Freeze the split manifest with a hash before model development.

## 13. Human-agreement benchmark

For each image with at least two independent annotations, compute pairwise distances:

```text
d_ij = sqrt((x_i - x_j)^2 + (y_i - y_j)^2)
```

Report per-image and aggregate:

- mean, median, standard deviation
- 90th, 95th, and 99th percentiles
- maximum disagreement
- percentage within 1, 2, 5, 10, and 20 pixels
- robust consensus centre, such as coordinate-wise median
- annotation count and missingness

Do not average away the underlying annotations. The agreement report is a benchmark for interpreting model-vs-human error.

## 14. Model evaluation target

Evaluate predictions against held-out human annotations. Report:

- MAE-X and MAE-Y
- Euclidean error
- mean, median, 90th, 95th, and 99th percentiles
- threshold accuracy at 1, 2, 5, 10, and 20 pixels
- performance by scene category and difficulty
- AI-vs-human compared with human-vs-human
- calibration and coverage of uncertainty regions

Do not report a single “accuracy” percentage without defining the tolerance and reference label.

## 15. Uncertainty and calibration labels

The model should produce a coordinate distribution or prediction interval, not just a point. Calibration must be evaluated on validation data and confirmed on untouched data.

Required analyses:

- coverage versus nominal confidence
- reliability diagram
- expected calibration error or a documented alternative
- uncertainty versus observed error
- abstention/low-confidence analysis on difficult images

A confidence value must not be described as a probability unless its empirical meaning has been measured.

## 16. Versioning and reproducibility

Every release and run must record:

- dataset version
- image-manifest hash
- split-manifest hash
- annotation instruction version
- interface version
- model version
- encoder
- configuration
- random seed
- code commit
- calibration version
- source-permission review status

Save at minimum:

```text
config.json
dataset_manifest.csv
split_manifest.csv
metrics.json
model.pt
calibration.joblib
training_log.json
```

## 17. Minimum acceptance criteria

The specification is implemented when:

- every image has a unique ID, dimensions, and immutable SHA-256 hash
- every annotation has an image ID, annotator ID, timestamp, and valid coordinate
- coordinate conversions are covered by tests
- at least three independent annotations are collected per pilot image
- annotators cannot see earlier decisions
- image families cannot cross data splits
- exact and near-duplicate checks produce an auditable report
- human-vs-human metrics are calculated before model claims are made
- source permission and retention status are recorded
- the system contains no automated external submission or gameplay path

## 18. Pilot acceptance test

For the first pilot:

- collect at least 1,000 permitted images where feasible
- obtain at least 3 independent annotations per image
- validate all image and annotation records
- produce the human-agreement report
- manually review the 100 highest-disagreement images
- freeze a pilot split manifest
- document any source/licensing limitation before training

The pilot passes only if all records are reproducible from the manifest and no unresolved integrity or leakage issue remains.

## 19. Scientific boundary

A zero-pixel guarantee is not an acceptable prior assumption. The result must be stated in terms of measured performance on held-out data and compared with measured human disagreement.

The primary research question is:

> Can a model reproduce independent human coordinate decisions on previously unseen images at an error level approaching the observed human-to-human disagreement?

That is the success criterion for this dataset.
