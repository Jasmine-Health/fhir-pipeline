"""
FHIR AllergyIntolerance Resource Generator

Generates FHIR R4 AllergyIntolerance resources from allergy templates.
"""

from datetime import datetime
from typing import Dict, Any, List

from .profiles.cardiac_profiles import PatientProfile, AllergyTemplate


def generate_allergy_resources(
    profile: PatientProfile,
    patient_reference: str
) -> List[Dict[str, Any]]:
    """
    Generate FHIR R4 AllergyIntolerance resources for a patient profile.

    Args:
        profile: Patient profile with allergies
        patient_reference: FHIR reference to the patient

    Returns:
        List of FHIR AllergyIntolerance resources as dicts
    """
    allergies = []

    for idx, allergy in enumerate(profile.allergies):
        allergy_resource = generate_single_allergy(
            allergy=allergy,
            patient_reference=patient_reference,
            allergy_id=f"{profile.id}-allergy-{idx + 1}"
        )
        allergies.append(allergy_resource)

    return allergies


def generate_single_allergy(
    allergy: AllergyTemplate,
    patient_reference: str,
    allergy_id: str
) -> Dict[str, Any]:
    """
    Generate a single FHIR R4 AllergyIntolerance resource.

    Args:
        allergy: Allergy template
        patient_reference: FHIR reference to the patient
        allergy_id: Unique identifier for this allergy

    Returns:
        FHIR AllergyIntolerance resource as dict
    """
    return {
        "resourceType": "AllergyIntolerance",
        "id": allergy_id,
        "meta": {
            "profile": ["http://hl7.org/fhir/us/core/StructureDefinition/us-core-allergyintolerance"]
        },
        "clinicalStatus": {
            "coding": [
                {
                    "system": "http://terminology.hl7.org/CodeSystem/allergyintolerance-clinical",
                    "code": "active",
                    "display": "Active"
                }
            ]
        },
        "verificationStatus": {
            "coding": [
                {
                    "system": "http://terminology.hl7.org/CodeSystem/allergyintolerance-verification",
                    "code": "confirmed",
                    "display": "Confirmed"
                }
            ]
        },
        "type": "allergy",
        "category": [get_allergy_category(allergy.name)],
        "criticality": map_severity_to_criticality(allergy.severity),
        "code": {
            "coding": [
                {
                    "system": "http://snomed.info/sct",
                    "code": get_snomed_code(allergy.name),
                    "display": allergy.name
                }
            ],
            "text": allergy.name
        },
        "patient": {
            "reference": patient_reference
        },
        "recordedDate": datetime.now().strftime("%Y-%m-%d"),
        "reaction": [
            {
                "manifestation": [
                    {
                        "coding": [
                            {
                                "system": "http://snomed.info/sct",
                                "code": get_reaction_snomed_code(allergy.reaction),
                                "display": allergy.reaction
                            }
                        ],
                        "text": allergy.reaction
                    }
                ],
                "severity": allergy.severity
            }
        ] if allergy.reaction else []
    }


def get_allergy_category(allergen_name: str) -> str:
    """Determine allergy category based on allergen"""
    medication_allergens = [
        "Penicillin", "Sulfa", "Aspirin", "NSAIDs", "Codeine",
        "Morphine", "Gadolinium", "Iodine contrast", "Contrast"
    ]

    food_allergens = [
        "Peanut", "Shellfish", "Eggs", "Milk", "Soy", "Wheat", "Fish"
    ]

    for med in medication_allergens:
        if med.lower() in allergen_name.lower():
            return "medication"

    for food in food_allergens:
        if food.lower() in allergen_name.lower():
            return "food"

    return "environment"


def map_severity_to_criticality(severity: str) -> str:
    """Map allergy severity to FHIR criticality"""
    severity_map = {
        "mild": "low",
        "moderate": "low",
        "severe": "high"
    }
    return severity_map.get(severity.lower(), "low")


def get_snomed_code(allergen_name: str) -> str:
    """Get SNOMED CT code for common allergens"""
    snomed_codes = {
        "Penicillin": "764146007",
        "Sulfa drugs": "91936005",
        "Sulfa": "91936005",
        "Gadolinium": "418389008",
        "Iodine contrast": "418589001",
        "Iodine": "418589001",
        "Contrast": "418589001",
        "Aspirin": "293586001",
        "Latex": "111088007",
        "Peanut": "91935009",
        "Shellfish": "91934008",
        "Eggs": "91930004",
    }

    for allergen, code in snomed_codes.items():
        if allergen.lower() in allergen_name.lower():
            return code

    return "unknown"


def get_reaction_snomed_code(reaction: str) -> str:
    """Get SNOMED CT code for common reactions"""
    reaction_codes = {
        "Anaphylaxis": "39579001",
        "Rash": "271807003",
        "Hives": "126485001",
        "Urticaria": "126485001",
        "Swelling": "65124004",
        "Difficulty breathing": "267036007",
        "Nausea": "422587007",
        "Vomiting": "422400008",
    }

    for rxn, code in reaction_codes.items():
        if rxn.lower() in reaction.lower():
            return code

    return "unknown"
