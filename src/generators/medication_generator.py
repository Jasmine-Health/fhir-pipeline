"""
FHIR MedicationRequest Resource Generator

Generates FHIR R4 MedicationRequest resources from medication templates.
"""

from datetime import datetime
from typing import Dict, Any, List

from .profiles.cardiac_profiles import PatientProfile, MedicationTemplate


def generate_medication_resources(
    profile: PatientProfile,
    patient_reference: str
) -> List[Dict[str, Any]]:
    """
    Generate FHIR R4 MedicationRequest resources for a patient profile.

    Args:
        profile: Patient profile with medications
        patient_reference: FHIR reference to the patient

    Returns:
        List of FHIR MedicationRequest resources as dicts
    """
    medications = []

    for idx, medication in enumerate(profile.medications):
        med_resource = generate_single_medication(
            medication=medication,
            patient_reference=patient_reference,
            medication_id=f"{profile.id}-med-{idx + 1}"
        )
        medications.append(med_resource)

    return medications


def generate_single_medication(
    medication: MedicationTemplate,
    patient_reference: str,
    medication_id: str
) -> Dict[str, Any]:
    """
    Generate a single FHIR R4 MedicationRequest resource.

    Args:
        medication: Medication template
        patient_reference: FHIR reference to the patient
        medication_id: Unique identifier for this medication

    Returns:
        FHIR MedicationRequest resource as dict
    """
    # Parse medication name to extract drug and dosage
    med_name, dosage = parse_medication_name(medication.name)

    resource = {
        "resourceType": "MedicationRequest",
        "id": medication_id,
        "meta": {
            "profile": ["http://hl7.org/fhir/us/core/StructureDefinition/us-core-medicationrequest"]
        },
        "status": "active",
        "intent": "order",
        "medicationCodeableConcept": {
            "coding": [
                {
                    "system": "http://www.nlm.nih.gov/research/umls/rxnorm",
                    "code": get_rxnorm_code(med_name),
                    "display": medication.name
                }
            ],
            "text": medication.name
        },
        "subject": {
            "reference": patient_reference
        },
        "authoredOn": datetime.now().strftime("%Y-%m-%dT%H:%M:%S+00:00"),
        "requester": {
            "display": "Ordering Physician"
        }
    }

    # Add dosage if parsed
    if dosage:
        resource["dosageInstruction"] = [
            {
                "text": f"Take {medication.name} as directed",
                "timing": {
                    "repeat": {
                        "frequency": 1,
                        "period": 1,
                        "periodUnit": "d"
                    }
                },
                "doseAndRate": [
                    {
                        "doseQuantity": {
                            "value": float(dosage.replace("mg", "").strip()) if "mg" in dosage else 1,
                            "unit": "mg" if "mg" in dosage else "unit",
                            "system": "http://unitsofmeasure.org"
                        }
                    }
                ]
            }
        ]

    # Add note if present (e.g., "Hold morning of procedure")
    if medication.note:
        resource["note"] = [
            {
                "text": medication.note
            }
        ]

    return resource


def parse_medication_name(full_name: str) -> tuple[str, str]:
    """
    Parse medication name to extract drug name and dosage.

    Args:
        full_name: Full medication string (e.g., "Metformin 500mg")

    Returns:
        Tuple of (drug_name, dosage)
    """
    parts = full_name.split()
    if len(parts) >= 2 and any(char.isdigit() for char in parts[-1]):
        return " ".join(parts[:-1]), parts[-1]
    return full_name, ""


def get_rxnorm_code(drug_name: str) -> str:
    """
    Get RxNorm code for common cardiac medications.
    Returns a placeholder code if not found.
    """
    rxnorm_codes = {
        "Metformin": "6809",
        "Metoprolol": "6918",
        "Atorvastatin": "83367",
        "Carvedilol": "20352",
        "Furosemide": "4603",
        "Lisinopril": "29046",
        "Warfarin": "11289",
        "Aspirin": "1191",
        "Digoxin": "3407",
        "Amlodipine": "17767",
        "Theophylline": "10438",
        "Albuterol": "435",
        "Spironolactone": "9997",
        "Apixaban": "1364430",
        "Entresto": "1656328",
        "Clopidogrel": "32968",
        "Verapamil": "11170",
        "Insulin": "5856",
    }

    for drug, code in rxnorm_codes.items():
        if drug.lower() in drug_name.lower():
            return code

    return "unknown"
