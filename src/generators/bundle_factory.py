"""
FHIR Bundle Factory

Assembles FHIR transaction bundles from individual resources.
"""

import json
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, Any, List, Optional

from .profiles.cardiac_profiles import PatientProfile, CARDIAC_PATIENT_PROFILES
from .patient_generator import generate_patient_resource
from .condition_generator import generate_condition_resources
from .medication_generator import generate_medication_resources
from .allergy_generator import generate_allergy_resources


def create_patient_bundle(
    profile: PatientProfile,
    hospital_id: str
) -> Dict[str, Any]:
    """
    Create a FHIR transaction bundle containing a patient and all related resources.

    Args:
        profile: Patient profile template
        hospital_id: Hospital identifier

    Returns:
        FHIR Bundle resource as dict
    """
    patient_reference = f"Patient/{profile.id}"

    # Generate all resources
    patient = generate_patient_resource(profile, hospital_id)
    conditions = generate_condition_resources(profile, patient_reference)
    medications = generate_medication_resources(profile, patient_reference)
    allergies = generate_allergy_resources(profile, patient_reference)

    # Create bundle entries
    entries = []

    # Add patient entry
    entries.append({
        "fullUrl": f"urn:uuid:{profile.id}",
        "resource": patient,
        "request": {
            "method": "PUT",
            "url": patient_reference
        }
    })

    # Add condition entries
    for condition in conditions:
        entries.append({
            "fullUrl": f"urn:uuid:{condition['id']}",
            "resource": condition,
            "request": {
                "method": "PUT",
                "url": f"Condition/{condition['id']}"
            }
        })

    # Add medication entries
    for medication in medications:
        entries.append({
            "fullUrl": f"urn:uuid:{medication['id']}",
            "resource": medication,
            "request": {
                "method": "PUT",
                "url": f"MedicationRequest/{medication['id']}"
            }
        })

    # Add allergy entries
    for allergy in allergies:
        entries.append({
            "fullUrl": f"urn:uuid:{allergy['id']}",
            "resource": allergy,
            "request": {
                "method": "PUT",
                "url": f"AllergyIntolerance/{allergy['id']}"
            }
        })

    # Create the bundle
    bundle = {
        "resourceType": "Bundle",
        "type": "transaction",
        "timestamp": datetime.now().isoformat(),
        "entry": entries
    }

    return bundle


def create_all_patient_bundles(
    hospital_id: str,
    patient_count: Optional[int] = None,
    profiles: Optional[List[PatientProfile]] = None
) -> List[Dict[str, Any]]:
    """
    Create transaction bundles for all patient profiles or a subset.

    Args:
        hospital_id: Hospital identifier
        patient_count: Optional limit on number of patients
        profiles: Optional list of specific profiles to use

    Returns:
        List of FHIR Bundle resources
    """
    if profiles is None:
        profiles = CARDIAC_PATIENT_PROFILES

    if patient_count is not None:
        profiles = profiles[:patient_count]

    bundles = []
    for profile in profiles:
        bundle = create_patient_bundle(profile, hospital_id)
        bundles.append(bundle)

    return bundles


def save_bundles_to_files(
    bundles: List[Dict[str, Any]],
    output_dir: str = "data/generated"
) -> List[str]:
    """
    Save bundles to JSON files.

    Args:
        bundles: List of FHIR bundles
        output_dir: Directory to save files

    Returns:
        List of file paths
    """
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)

    file_paths = []
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

    for idx, bundle in enumerate(bundles):
        # Extract patient ID from bundle
        patient_entry = next(
            (e for e in bundle.get("entry", []) if e.get("resource", {}).get("resourceType") == "Patient"),
            None
        )
        if patient_entry:
            patient_id = patient_entry["resource"].get("id", f"patient_{idx}")
        else:
            patient_id = f"patient_{idx}"

        filename = f"bundle_{patient_id}_{timestamp}.json"
        filepath = output_path / filename

        with open(filepath, "w") as f:
            json.dump(bundle, f, indent=2)

        file_paths.append(str(filepath))

    return file_paths


def create_combined_bundle(
    hospital_id: str,
    patient_count: Optional[int] = None
) -> Dict[str, Any]:
    """
    Create a single combined transaction bundle with all patients.

    Args:
        hospital_id: Hospital identifier
        patient_count: Optional limit on number of patients

    Returns:
        Combined FHIR Bundle resource
    """
    individual_bundles = create_all_patient_bundles(hospital_id, patient_count)

    # Combine all entries
    all_entries = []
    for bundle in individual_bundles:
        all_entries.extend(bundle.get("entry", []))

    combined = {
        "resourceType": "Bundle",
        "type": "transaction",
        "timestamp": datetime.now().isoformat(),
        "entry": all_entries
    }

    return combined
