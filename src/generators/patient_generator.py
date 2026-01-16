"""
FHIR Patient Resource Generator

Generates FHIR R4 Patient resources from patient profile templates.
"""

import uuid
from datetime import date, datetime
from typing import Dict, Any, Optional

from .profiles.cardiac_profiles import PatientProfile


def generate_patient_resource(profile: PatientProfile, hospital_id: str) -> Dict[str, Any]:
    """
    Generate a FHIR R4 Patient resource from a patient profile.

    Args:
        profile: Patient profile template
        hospital_id: Hospital identifier for tagging

    Returns:
        FHIR Patient resource as dict
    """
    # Calculate date of birth from birth year
    dob = f"{profile.birth_year}-06-15"  # Use mid-year as default

    # Generate MRN
    mrn = f"MRN-{profile.id.upper()}"

    patient = {
        "resourceType": "Patient",
        "id": profile.id,
        "meta": {
            "profile": ["http://hl7.org/fhir/us/core/StructureDefinition/us-core-patient"],
            "tag": [
                {
                    "system": "http://cairiq.com/fhir/hospital",
                    "code": hospital_id
                },
                {
                    "system": "http://cairiq.com/fhir/source",
                    "code": "fhir_pipeline"
                }
            ]
        },
        "identifier": [
            {
                "use": "usual",
                "type": {
                    "coding": [
                        {
                            "system": "http://terminology.hl7.org/CodeSystem/v2-0203",
                            "code": "MR",
                            "display": "Medical Record Number"
                        }
                    ]
                },
                "system": f"http://cairiq.com/hospital/{hospital_id}/mrn",
                "value": mrn
            },
            {
                "use": "secondary",
                "type": {
                    "coding": [
                        {
                            "system": "http://terminology.hl7.org/CodeSystem/v2-0203",
                            "code": "PI",
                            "display": "Patient internal identifier"
                        }
                    ]
                },
                "system": "http://cairiq.com/fhir/ehr-id",
                "value": profile.id
            }
        ],
        "active": True,
        "name": [
            {
                "use": "official",
                "family": profile.last_name,
                "given": [profile.first_name]
            }
        ],
        "gender": profile.sex,
        "birthDate": dob,
        "communication": [
            {
                "language": {
                    "coding": [
                        get_language_coding(profile.language)
                    ],
                    "text": profile.language
                },
                "preferred": True
            }
        ],
        "extension": [
            {
                "url": "http://cairiq.com/fhir/StructureDefinition/health-literacy",
                "valueCode": profile.health_literacy.value
            },
            {
                "url": "http://cairiq.com/fhir/StructureDefinition/scenario",
                "valueString": profile.scenario
            },
            {
                "url": "http://cairiq.com/fhir/StructureDefinition/special-considerations",
                "valueString": ",".join(profile.special_considerations)
            }
        ]
    }

    return patient


def get_language_coding(language: str) -> Dict[str, str]:
    """Get BCP-47 language coding for FHIR"""
    language_map = {
        "English": {"system": "urn:ietf:bcp:47", "code": "en", "display": "English"},
        "Spanish": {"system": "urn:ietf:bcp:47", "code": "es", "display": "Spanish"},
        "Mandarin": {"system": "urn:ietf:bcp:47", "code": "zh", "display": "Chinese"},
        "French": {"system": "urn:ietf:bcp:47", "code": "fr", "display": "French"},
        "Vietnamese": {"system": "urn:ietf:bcp:47", "code": "vi", "display": "Vietnamese"},
        "Korean": {"system": "urn:ietf:bcp:47", "code": "ko", "display": "Korean"},
        "Arabic": {"system": "urn:ietf:bcp:47", "code": "ar", "display": "Arabic"},
    }
    return language_map.get(language, {"system": "urn:ietf:bcp:47", "code": "en", "display": "English"})


def calculate_age(birth_year: int) -> int:
    """Calculate current age from birth year"""
    current_year = datetime.now().year
    return current_year - birth_year
