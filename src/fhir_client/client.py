"""
FHIR REST Client

REST wrapper for HAPI FHIR server interactions.
"""

import requests
from typing import Dict, Any, List, Optional
from dataclasses import dataclass


@dataclass
class FHIRResponse:
    """Container for FHIR API response"""
    success: bool
    status_code: int
    data: Optional[Dict[str, Any]] = None
    error: Optional[str] = None


class FHIRClient:
    """
    FHIR R4 REST client for HAPI FHIR server.

    Provides methods for uploading bundles, fetching patients,
    and using the $everything operation.
    """

    def __init__(self, base_url: str = "http://localhost:8080/fhir", timeout: int = 30):
        """
        Initialize FHIR client.

        Args:
            base_url: FHIR server base URL
            timeout: Request timeout in seconds
        """
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout
        self.headers = {
            "Content-Type": "application/fhir+json",
            "Accept": "application/fhir+json"
        }

    def health_check(self) -> bool:
        """Check if FHIR server is available"""
        try:
            response = requests.get(
                f"{self.base_url}/metadata",
                headers=self.headers,
                timeout=self.timeout
            )
            return response.status_code == 200
        except requests.RequestException:
            return False

    def upload_bundle(self, bundle: Dict[str, Any]) -> FHIRResponse:
        """
        Upload a transaction bundle to the FHIR server.

        Args:
            bundle: FHIR Bundle resource

        Returns:
            FHIRResponse with result
        """
        try:
            response = requests.post(
                self.base_url,
                json=bundle,
                headers=self.headers,
                timeout=self.timeout
            )

            if response.status_code in (200, 201):
                return FHIRResponse(
                    success=True,
                    status_code=response.status_code,
                    data=response.json()
                )
            else:
                return FHIRResponse(
                    success=False,
                    status_code=response.status_code,
                    error=response.text
                )
        except requests.RequestException as e:
            return FHIRResponse(
                success=False,
                status_code=0,
                error=str(e)
            )

    def get_patient(self, patient_id: str) -> FHIRResponse:
        """
        Fetch a single patient by ID.

        Args:
            patient_id: Patient resource ID

        Returns:
            FHIRResponse with Patient resource
        """
        try:
            response = requests.get(
                f"{self.base_url}/Patient/{patient_id}",
                headers=self.headers,
                timeout=self.timeout
            )

            if response.status_code == 200:
                return FHIRResponse(
                    success=True,
                    status_code=response.status_code,
                    data=response.json()
                )
            else:
                return FHIRResponse(
                    success=False,
                    status_code=response.status_code,
                    error=response.text
                )
        except requests.RequestException as e:
            return FHIRResponse(
                success=False,
                status_code=0,
                error=str(e)
            )

    def search_patients(
        self,
        hospital_tag: Optional[str] = None,
        count: int = 100
    ) -> FHIRResponse:
        """
        Search for patients, optionally filtered by hospital tag.

        Args:
            hospital_tag: Optional hospital ID tag to filter
            count: Maximum number of results

        Returns:
            FHIRResponse with Bundle of patients
        """
        params = {"_count": count}
        if hospital_tag:
            params["_tag"] = f"http://cairiq.com/fhir/hospital|{hospital_tag}"

        try:
            response = requests.get(
                f"{self.base_url}/Patient",
                params=params,
                headers=self.headers,
                timeout=self.timeout
            )

            if response.status_code == 200:
                return FHIRResponse(
                    success=True,
                    status_code=response.status_code,
                    data=response.json()
                )
            else:
                return FHIRResponse(
                    success=False,
                    status_code=response.status_code,
                    error=response.text
                )
        except requests.RequestException as e:
            return FHIRResponse(
                success=False,
                status_code=0,
                error=str(e)
            )

    def get_patient_everything(self, patient_id: str) -> FHIRResponse:
        """
        Fetch all resources for a patient using $everything operation.

        Args:
            patient_id: Patient resource ID

        Returns:
            FHIRResponse with Bundle of all patient resources
        """
        try:
            response = requests.get(
                f"{self.base_url}/Patient/{patient_id}/$everything",
                headers=self.headers,
                timeout=self.timeout * 2  # Allow more time for large bundles
            )

            if response.status_code == 200:
                return FHIRResponse(
                    success=True,
                    status_code=response.status_code,
                    data=response.json()
                )
            else:
                return FHIRResponse(
                    success=False,
                    status_code=response.status_code,
                    error=response.text
                )
        except requests.RequestException as e:
            return FHIRResponse(
                success=False,
                status_code=0,
                error=str(e)
            )

    def get_conditions(self, patient_id: str) -> FHIRResponse:
        """Fetch conditions for a patient"""
        return self._search_by_patient("Condition", patient_id)

    def get_medications(self, patient_id: str) -> FHIRResponse:
        """Fetch medication requests for a patient"""
        return self._search_by_patient("MedicationRequest", patient_id)

    def get_allergies(self, patient_id: str) -> FHIRResponse:
        """Fetch allergies for a patient"""
        return self._search_by_patient("AllergyIntolerance", patient_id)

    def _search_by_patient(
        self,
        resource_type: str,
        patient_id: str
    ) -> FHIRResponse:
        """Generic search by patient reference"""
        try:
            response = requests.get(
                f"{self.base_url}/{resource_type}",
                params={"patient": patient_id},
                headers=self.headers,
                timeout=self.timeout
            )

            if response.status_code == 200:
                return FHIRResponse(
                    success=True,
                    status_code=response.status_code,
                    data=response.json()
                )
            else:
                return FHIRResponse(
                    success=False,
                    status_code=response.status_code,
                    error=response.text
                )
        except requests.RequestException as e:
            return FHIRResponse(
                success=False,
                status_code=0,
                error=str(e)
            )

    def get_patient_count(self) -> int:
        """Get total patient count on server"""
        try:
            response = requests.get(
                f"{self.base_url}/Patient",
                params={"_summary": "count"},
                headers=self.headers,
                timeout=self.timeout
            )
            if response.status_code == 200:
                data = response.json()
                return data.get("total", 0)
            return 0
        except requests.RequestException:
            return 0

    def delete_patient(self, patient_id: str) -> FHIRResponse:
        """Delete a patient resource"""
        try:
            response = requests.delete(
                f"{self.base_url}/Patient/{patient_id}",
                headers=self.headers,
                timeout=self.timeout
            )

            return FHIRResponse(
                success=response.status_code in (200, 204),
                status_code=response.status_code,
                error=response.text if response.status_code not in (200, 204) else None
            )
        except requests.RequestException as e:
            return FHIRResponse(
                success=False,
                status_code=0,
                error=str(e)
            )
