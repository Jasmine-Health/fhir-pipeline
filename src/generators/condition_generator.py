"""
FHIR Condition Resource Generator

Generates FHIR R4 Condition resources from condition templates.
"""

from datetime import datetime
from typing import Dict, Any, List

from .profiles.cardiac_profiles import PatientProfile, ConditionTemplate


def generate_condition_resources(
    profile: PatientProfile,
    patient_reference: str
) -> List[Dict[str, Any]]:
    """
    Generate FHIR R4 Condition resources for a patient profile.

    Args:
        profile: Patient profile with conditions
        patient_reference: FHIR reference to the patient (e.g., "Patient/fhir_001")

    Returns:
        List of FHIR Condition resources as dicts
    """
    conditions = []

    for idx, condition in enumerate(profile.conditions):
        condition_resource = generate_single_condition(
            condition=condition,
            patient_reference=patient_reference,
            condition_id=f"{profile.id}-condition-{idx + 1}"
        )
        conditions.append(condition_resource)

    return conditions


def generate_single_condition(
    condition: ConditionTemplate,
    patient_reference: str,
    condition_id: str
) -> Dict[str, Any]:
    """
    Generate a single FHIR R4 Condition resource.

    Args:
        condition: Condition template with ICD-10 code
        patient_reference: FHIR reference to the patient
        condition_id: Unique identifier for this condition

    Returns:
        FHIR Condition resource as dict
    """
    return {
        "resourceType": "Condition",
        "id": condition_id,
        "meta": {
            "profile": ["http://hl7.org/fhir/us/core/StructureDefinition/us-core-condition"]
        },
        "clinicalStatus": {
            "coding": [
                {
                    "system": "http://terminology.hl7.org/CodeSystem/condition-clinical",
                    "code": "active",
                    "display": "Active"
                }
            ]
        },
        "verificationStatus": {
            "coding": [
                {
                    "system": "http://terminology.hl7.org/CodeSystem/condition-ver-status",
                    "code": "confirmed",
                    "display": "Confirmed"
                }
            ]
        },
        "category": [
            {
                "coding": [
                    {
                        "system": "http://terminology.hl7.org/CodeSystem/condition-category",
                        "code": get_condition_category(condition.code),
                        "display": get_condition_category_display(condition.code)
                    }
                ]
            }
        ],
        "code": {
            "coding": [
                {
                    "system": "http://hl7.org/fhir/sid/icd-10-cm",
                    "code": condition.code,
                    "display": condition.title
                }
            ],
            "text": condition.title
        },
        "subject": {
            "reference": patient_reference
        },
        "recordedDate": datetime.now().strftime("%Y-%m-%d")
    }


def get_condition_category(icd10_code: str) -> str:
    """Determine condition category based on ICD-10 code prefix"""
    if icd10_code.startswith("I"):
        return "problem-list-item"  # Circulatory conditions
    elif icd10_code.startswith("E"):
        return "problem-list-item"  # Endocrine conditions (diabetes, etc.)
    elif icd10_code.startswith("J"):
        return "problem-list-item"  # Respiratory conditions
    elif icd10_code.startswith("N"):
        return "problem-list-item"  # Renal conditions
    elif icd10_code.startswith("F"):
        return "problem-list-item"  # Mental health conditions
    elif icd10_code.startswith("Z"):
        return "health-concern"  # Factors influencing health (devices, etc.)
    else:
        return "problem-list-item"


def get_condition_category_display(icd10_code: str) -> str:
    """Get display name for condition category"""
    category = get_condition_category(icd10_code)
    category_map = {
        "problem-list-item": "Problem List Item",
        "encounter-diagnosis": "Encounter Diagnosis",
        "health-concern": "Health Concern"
    }
    return category_map.get(category, "Problem List Item")
