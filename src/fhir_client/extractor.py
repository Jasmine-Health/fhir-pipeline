"""
FHIR Patient Extractor

Extracts patients with all related resources from FHIR server.
"""

from typing import Dict, Any, List, Optional
from dataclasses import dataclass, field

from .client import FHIRClient


@dataclass
class ExtractedPatient:
    """Container for patient with all related resources"""
    patient_id: str
    patient: Dict[str, Any]
    conditions: List[Dict[str, Any]] = field(default_factory=list)
    medications: List[Dict[str, Any]] = field(default_factory=list)
    allergies: List[Dict[str, Any]] = field(default_factory=list)
    raw_bundle: Optional[Dict[str, Any]] = None


class PatientExtractor:
    """
    Extracts complete patient records from FHIR server.

    Uses the $everything operation when available, falls back to
    individual resource queries.
    """

    def __init__(self, client: FHIRClient):
        """
        Initialize extractor with FHIR client.

        Args:
            client: Configured FHIRClient instance
        """
        self.client = client

    def extract_patient(self, patient_id: str, use_everything: bool = True) -> Optional[ExtractedPatient]:
        """
        Extract a single patient with all related resources.

        Args:
            patient_id: Patient resource ID
            use_everything: Use $everything operation if True

        Returns:
            ExtractedPatient or None if not found
        """
        if use_everything:
            return self._extract_via_everything(patient_id)
        else:
            return self._extract_via_individual_queries(patient_id)

    def extract_all_patients(
        self,
        hospital_tag: Optional[str] = None,
        use_everything: bool = True,
        progress_callback: Optional[callable] = None
    ) -> List[ExtractedPatient]:
        """
        Extract all patients (optionally filtered by hospital).

        Args:
            hospital_tag: Optional hospital ID to filter
            use_everything: Use $everything operation
            progress_callback: Optional callback(current, total)

        Returns:
            List of ExtractedPatient objects
        """
        # First, get list of patient IDs
        patient_ids = self._get_patient_ids(hospital_tag)

        extracted = []
        total = len(patient_ids)

        for idx, patient_id in enumerate(patient_ids):
            if progress_callback:
                progress_callback(idx + 1, total)

            patient = self.extract_patient(patient_id, use_everything)
            if patient:
                extracted.append(patient)

        return extracted

    def _get_patient_ids(self, hospital_tag: Optional[str] = None) -> List[str]:
        """Get list of patient IDs from server"""
        response = self.client.search_patients(hospital_tag=hospital_tag)

        if not response.success or not response.data:
            return []

        patient_ids = []
        for entry in response.data.get("entry", []):
            resource = entry.get("resource", {})
            if resource.get("resourceType") == "Patient":
                patient_id = resource.get("id")
                if patient_id:
                    patient_ids.append(patient_id)

        return patient_ids

    def _extract_via_everything(self, patient_id: str) -> Optional[ExtractedPatient]:
        """Extract patient using $everything operation"""
        response = self.client.get_patient_everything(patient_id)

        if not response.success or not response.data:
            return None

        bundle = response.data
        extracted = ExtractedPatient(
            patient_id=patient_id,
            patient={},
            raw_bundle=bundle
        )

        # Parse resources from bundle
        for entry in bundle.get("entry", []):
            resource = entry.get("resource", {})
            resource_type = resource.get("resourceType")

            if resource_type == "Patient":
                extracted.patient = resource
            elif resource_type == "Condition":
                extracted.conditions.append(resource)
            elif resource_type == "MedicationRequest":
                extracted.medications.append(resource)
            elif resource_type == "AllergyIntolerance":
                extracted.allergies.append(resource)

        return extracted

    def _extract_via_individual_queries(self, patient_id: str) -> Optional[ExtractedPatient]:
        """Extract patient using individual resource queries"""
        # Get patient
        patient_response = self.client.get_patient(patient_id)
        if not patient_response.success:
            return None

        extracted = ExtractedPatient(
            patient_id=patient_id,
            patient=patient_response.data
        )

        # Get conditions
        cond_response = self.client.get_conditions(patient_id)
        if cond_response.success and cond_response.data:
            extracted.conditions = self._extract_resources_from_bundle(cond_response.data)

        # Get medications
        med_response = self.client.get_medications(patient_id)
        if med_response.success and med_response.data:
            extracted.medications = self._extract_resources_from_bundle(med_response.data)

        # Get allergies
        allergy_response = self.client.get_allergies(patient_id)
        if allergy_response.success and allergy_response.data:
            extracted.allergies = self._extract_resources_from_bundle(allergy_response.data)

        return extracted

    def _extract_resources_from_bundle(self, bundle: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Extract resources from a search bundle"""
        resources = []
        for entry in bundle.get("entry", []):
            resource = entry.get("resource")
            if resource:
                resources.append(resource)
        return resources
