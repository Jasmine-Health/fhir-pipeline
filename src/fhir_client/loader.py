"""
FHIR Bundle Loader

Batch upload of FHIR bundles to HAPI FHIR server.
"""

import json
from pathlib import Path
from typing import Dict, Any, List, Optional
from dataclasses import dataclass, field

from .client import FHIRClient, FHIRResponse


@dataclass
class LoadResult:
    """Result of bundle loading operation"""
    total: int = 0
    successful: int = 0
    failed: int = 0
    errors: List[str] = field(default_factory=list)
    patient_ids: List[str] = field(default_factory=list)


class BundleLoader:
    """
    Batch loader for FHIR bundles.

    Handles uploading multiple bundles to HAPI FHIR server
    with error tracking and progress reporting.
    """

    def __init__(self, client: FHIRClient):
        """
        Initialize loader with FHIR client.

        Args:
            client: Configured FHIRClient instance
        """
        self.client = client

    def load_bundles(
        self,
        bundles: List[Dict[str, Any]],
        progress_callback: Optional[callable] = None
    ) -> LoadResult:
        """
        Load multiple bundles to FHIR server.

        Args:
            bundles: List of FHIR Bundle resources
            progress_callback: Optional callback(current, total, patient_id)

        Returns:
            LoadResult with statistics
        """
        result = LoadResult(total=len(bundles))

        for idx, bundle in enumerate(bundles):
            # Extract patient ID for reporting
            patient_id = self._extract_patient_id(bundle)

            if progress_callback:
                progress_callback(idx + 1, len(bundles), patient_id)

            response = self.client.upload_bundle(bundle)

            if response.success:
                result.successful += 1
                if patient_id:
                    result.patient_ids.append(patient_id)
            else:
                result.failed += 1
                error_msg = f"Patient {patient_id}: {response.error}"
                result.errors.append(error_msg)

        return result

    def load_from_files(
        self,
        file_paths: List[str],
        progress_callback: Optional[callable] = None
    ) -> LoadResult:
        """
        Load bundles from JSON files.

        Args:
            file_paths: List of paths to bundle JSON files
            progress_callback: Optional callback(current, total, filename)

        Returns:
            LoadResult with statistics
        """
        bundles = []

        for filepath in file_paths:
            try:
                with open(filepath) as f:
                    bundle = json.load(f)
                    bundles.append(bundle)
            except (json.JSONDecodeError, FileNotFoundError) as e:
                print(f"Error loading {filepath}: {e}")

        return self.load_bundles(bundles, progress_callback)

    def load_from_directory(
        self,
        directory: str,
        pattern: str = "bundle_*.json",
        progress_callback: Optional[callable] = None
    ) -> LoadResult:
        """
        Load all bundle files from a directory.

        Args:
            directory: Path to directory
            pattern: Glob pattern for bundle files
            progress_callback: Optional callback

        Returns:
            LoadResult with statistics
        """
        dir_path = Path(directory)
        file_paths = sorted(dir_path.glob(pattern))

        return self.load_from_files([str(f) for f in file_paths], progress_callback)

    def load_combined_bundle(
        self,
        bundle: Dict[str, Any]
    ) -> LoadResult:
        """
        Load a single combined bundle with multiple patients.

        Args:
            bundle: Combined FHIR Bundle

        Returns:
            LoadResult with statistics
        """
        result = LoadResult(total=1)

        response = self.client.upload_bundle(bundle)

        if response.success:
            result.successful = 1
            # Extract all patient IDs from combined bundle
            result.patient_ids = self._extract_all_patient_ids(bundle)
        else:
            result.failed = 1
            result.errors.append(response.error or "Unknown error")

        return result

    def _extract_patient_id(self, bundle: Dict[str, Any]) -> Optional[str]:
        """Extract patient ID from bundle"""
        for entry in bundle.get("entry", []):
            resource = entry.get("resource", {})
            if resource.get("resourceType") == "Patient":
                return resource.get("id")
        return None

    def _extract_all_patient_ids(self, bundle: Dict[str, Any]) -> List[str]:
        """Extract all patient IDs from combined bundle"""
        patient_ids = []
        for entry in bundle.get("entry", []):
            resource = entry.get("resource", {})
            if resource.get("resourceType") == "Patient":
                patient_id = resource.get("id")
                if patient_id:
                    patient_ids.append(patient_id)
        return patient_ids
