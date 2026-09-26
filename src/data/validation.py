"""Image validation and integrity checking pipeline."""

import hashlib
import json
import logging
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass, asdict
from datetime import datetime

import numpy as np
from PIL import Image


logger = logging.getLogger(__name__)


@dataclass
class ImageValidationResult:
    """Result of image validation."""
    image_id: str
    image_path: str
    valid: bool
    width: int
    height: int
    format: str
    file_size_bytes: int
    sha256_hash: str
    validation_timestamp: str
    errors: List[str]
    warnings: List[str]


class ImageValidator:
    """Validates image integrity and generates metadata."""

    def __init__(self, max_file_size_mb: int = 50):
        self.max_file_size_mb = max_file_size_mb
        self.max_file_size_bytes = max_file_size_mb * 1024 * 1024

    def compute_sha256(self, file_path: str) -> str:
        """Compute SHA-256 hash of image file."""
        sha256_hash = hashlib.sha256()
        with open(file_path, 'rb') as f:
            for byte_block in iter(lambda: f.read(4096), b""):
                sha256_hash.update(byte_block)
        return f"sha256:{sha256_hash.hexdigest()}"

    def validate_image(self, image_path: str, image_id: str) -> ImageValidationResult:
        """Validate a single image file."""
        errors = []
        warnings = []

        path_obj = Path(image_path)

        # Check file exists
        if not path_obj.exists():
            errors.append(f"File does not exist: {image_path}")
            return ImageValidationResult(
                image_id=image_id,
                image_path=image_path,
                valid=False,
                width=0,
                height=0,
                format="",
                file_size_bytes=0,
                sha256_hash="",
                validation_timestamp=datetime.utcnow().isoformat() + "Z",
                errors=errors,
                warnings=warnings,
            )

        # Check file size
        file_size = path_obj.stat().st_size
        if file_size == 0:
            errors.append("File size is 0")
        if file_size > self.max_file_size_bytes:
            errors.append(f"File exceeds max size: {file_size} > {self.max_file_size_bytes}")

        # Try to open and validate image
        width, height, img_format = 0, 0, ""
        sha256_hash = ""

        try:
            sha256_hash = self.compute_sha256(image_path)
            logger.debug(f"Computed hash for {image_id}: {sha256_hash}")
        except Exception as e:
            errors.append(f"Failed to compute hash: {str(e)}")

        try:
            img = Image.open(image_path)
            img.load()  # Force load to catch corruption
            width, height = img.size
            img_format = img.format or "UNKNOWN"

            if width <= 0 or height <= 0:
                errors.append(f"Invalid dimensions: {width}x{height}")

            # Warn on small images
            if width < 320 or height < 240:
                warnings.append(f"Small image dimensions: {width}x{height}")

        except Exception as e:
            errors.append(f"Failed to open/decode image: {str(e)}")

        valid = len(errors) == 0

        return ImageValidationResult(
            image_id=image_id,
            image_path=image_path,
            valid=valid,
            width=width,
            height=height,
            format=img_format,
            file_size_bytes=file_size,
            sha256_hash=sha256_hash,
            validation_timestamp=datetime.utcnow().isoformat() + "Z",
            errors=errors,
            warnings=warnings,
        )

    def validate_batch(self, image_list: List[Tuple[str, str]]) -> List[ImageValidationResult]:
        """Validate a batch of images (path, image_id pairs)."""
        results = []
        for image_path, image_id in image_list:
            result = self.validate_image(image_path, image_id)
            results.append(result)
        return results

    def validate_coordinates(self, x: float, y: float, width: int, height: int) -> Tuple[bool, List[str]]:
        """Validate coordinates are within image bounds."""
        errors = []

        # Check types
        if not isinstance(x, (int, float)) or not isinstance(y, (int, float)):
            errors.append(f"Coordinate must be numeric: x={x}, y={y}")
            return False, errors

        # Check bounds (pixel-center convention: [0, W-1] x [0, H-1])
        if x < 0 or x >= width:
            errors.append(f"X coordinate out of bounds: {x} not in [0, {width-1}]")
        if y < 0 or y >= height:
            errors.append(f"Y coordinate out of bounds: {y} not in [0, {height-1}]")

        return len(errors) == 0, errors


def generate_image_manifest(
    validation_results: List[ImageValidationResult],
    source_provider: str = "BOTB",
    usage_permission: str = "unknown",
) -> List[Dict]:
    """Generate image manifest entries from validation results."""
    manifest = []

    for result in validation_results:
        if not result.valid:
            logger.warning(f"Skipping invalid image {result.image_id}: {result.errors}")
            continue

        entry = {
            "image_id": result.image_id,
            "image_family_id": result.image_id,  # Placeholder; update with actual family grouping
            "image_path": f"controlled://images/{result.image_id}.{result.format.lower()}",
            "original_image_path": result.image_path,
            "image_hash_sha256": result.sha256_hash,
            "perceptual_hash": None,  # To be computed later if needed
            "width": result.width,
            "height": result.height,
            "format": result.format,
            "file_size_bytes": result.file_size_bytes,
            "source_provider": source_provider,
            "source_page_url": "https://www.botb.com/spot-the-ball",
            "source_competition_id": None,
            "source_image_id": None,
            "capture_timestamp": datetime.utcnow().isoformat() + "Z",
            "publication_timestamp": None,
            "scene_categories": [],
            "image_status": "usable",
            "usage_permission": usage_permission,
            "dataset_version": "v0.1.0",
        }
        manifest.append(entry)

    return manifest


def save_validation_report(results: List[ImageValidationResult], output_path: str) -> None:
    """Save validation report to JSON."""
    report = {
        "validation_timestamp": datetime.utcnow().isoformat() + "Z",
        "total_images": len(results),
        "valid_images": sum(1 for r in results if r.valid),
        "invalid_images": sum(1 for r in results if not r.valid),
        "results": [asdict(r) for r in results],
    }

    with open(output_path, "w") as f:
        json.dump(report, f, indent=2)

    logger.info(f"Validation report saved to {output_path}")
    logger.info(f"Valid: {report['valid_images']}/{report['total_images']}")
