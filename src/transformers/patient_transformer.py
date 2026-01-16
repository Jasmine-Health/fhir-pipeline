"""
FHIR to cair-map Patient Transformer

Transforms FHIR Patient bundles to cair-map schema format.
"""

from datetime import datetime, date
from typing import Dict, Any, List, Optional
from dataclasses import dataclass, field

from ..fhir_client.extractor import ExtractedPatient


@dataclass
class CairMapCondition:
    """Condition in cair-map format"""
    code: str
    title: str


@dataclass
class CairMapMedication:
    """Medication in cair-map format"""
    name: str
    note: Optional[str] = None


@dataclass
class CairMapAllergy:
    """Allergy in cair-map format"""
    name: str
    reaction: Optional[str] = None
    severity: Optional[str] = None


@dataclass
class CairMapPatient:
    """Patient in cair-map schema format"""
    ehr_id: str
    mrn: str
    first_name: str
    last_name: str
    date_of_birth: str
    sex: str
    age: int
    language: str
    health_literacy: str
    conditions: List[CairMapCondition] = field(default_factory=list)
    medications: List[CairMapMedication] = field(default_factory=list)
    allergies: List[CairMapAllergy] = field(default_factory=list)
    special_considerations: List[str] = field(default_factory=list)
    cohort: str = ""
    scenario: str = ""
    demo_question: str = ""
    expected_personalization: str = ""
    source: str = "fhir_pipeline"


class PatientTransformer:
    """
    Transforms FHIR Patient data to cair-map schema.

    Handles:
    - Patient demographics
    - Conditions with ICD-10 codes
    - Medications with notes
    - Allergies with reactions
    - Derived fields (cohort, health literacy)
    """

    def transform(self, extracted: ExtractedPatient) -> CairMapPatient:
        """
        Transform an extracted FHIR patient to cair-map format.

        Args:
            extracted: ExtractedPatient from FHIR server

        Returns:
            CairMapPatient ready for Neo4j loading
        """
        patient_resource = extracted.patient

        # Extract identifiers
        ehr_id = self._extract_ehr_id(patient_resource)
        mrn = self._extract_mrn(patient_resource)

        # Extract demographics
        name = self._extract_name(patient_resource)
        dob = patient_resource.get("birthDate", "1970-01-01")
        sex = patient_resource.get("gender", "unknown")
        age = self._calculate_age(dob)
        language = self._extract_language(patient_resource)

        # Extract extensions (health literacy, scenario, etc.)
        extensions = self._extract_extensions(patient_resource)
        health_literacy = extensions.get("health-literacy", "standard")
        scenario = extensions.get("scenario", "")
        special_considerations = extensions.get("special-considerations", "").split(",")
        special_considerations = [s.strip() for s in special_considerations if s.strip()]

        # Transform conditions
        conditions = [
            self._transform_condition(c) for c in extracted.conditions
        ]

        # Transform medications
        medications = [
            self._transform_medication(m) for m in extracted.medications
        ]

        # Transform allergies
        allergies = [
            self._transform_allergy(a) for a in extracted.allergies
        ]

        # Derive cohort
        cohort = self._derive_cohort(age, sex, health_literacy, conditions)

        return CairMapPatient(
            ehr_id=ehr_id,
            mrn=mrn,
            first_name=name["first"],
            last_name=name["last"],
            date_of_birth=dob,
            sex=sex,
            age=age,
            language=language,
            health_literacy=health_literacy,
            conditions=conditions,
            medications=medications,
            allergies=allergies,
            special_considerations=special_considerations,
            cohort=cohort,
            scenario=scenario,
            source="fhir_pipeline"
        )

    def transform_batch(
        self,
        extracted_patients: List[ExtractedPatient]
    ) -> List[CairMapPatient]:
        """Transform a batch of extracted patients"""
        return [self.transform(p) for p in extracted_patients]

    def _extract_ehr_id(self, patient: Dict[str, Any]) -> str:
        """Extract EHR ID from patient identifiers"""
        # First try the patient ID
        if "id" in patient:
            return patient["id"]

        # Then try identifiers
        for identifier in patient.get("identifier", []):
            system = identifier.get("system", "")
            if "ehr-id" in system:
                return identifier.get("value", "")

        return f"unknown_{datetime.now().timestamp()}"

    def _extract_mrn(self, patient: Dict[str, Any]) -> str:
        """Extract MRN from patient identifiers"""
        for identifier in patient.get("identifier", []):
            type_codings = identifier.get("type", {}).get("coding", [])
            for coding in type_codings:
                if coding.get("code") == "MR":
                    return identifier.get("value", "")

        return f"MRN-{patient.get('id', 'unknown')}"

    def _extract_name(self, patient: Dict[str, Any]) -> Dict[str, str]:
        """Extract patient name"""
        names = patient.get("name", [])
        if not names:
            return {"first": "Unknown", "last": "Patient"}

        # Prefer official name
        for name in names:
            if name.get("use") == "official":
                return {
                    "first": name.get("given", [""])[0] if name.get("given") else "",
                    "last": name.get("family", "")
                }

        # Fall back to first name entry
        name = names[0]
        return {
            "first": name.get("given", [""])[0] if name.get("given") else "",
            "last": name.get("family", "")
        }

    def _extract_language(self, patient: Dict[str, Any]) -> str:
        """Extract preferred language"""
        communications = patient.get("communication", [])

        for comm in communications:
            if comm.get("preferred"):
                language = comm.get("language", {})
                text = language.get("text")
                if text:
                    return text

                codings = language.get("coding", [])
                for coding in codings:
                    display = coding.get("display")
                    if display:
                        return display

        return "English"

    def _extract_extensions(self, patient: Dict[str, Any]) -> Dict[str, str]:
        """Extract custom extensions"""
        extensions = {}

        for ext in patient.get("extension", []):
            url = ext.get("url", "")

            if "health-literacy" in url:
                extensions["health-literacy"] = ext.get("valueCode", "standard")
            elif "scenario" in url:
                extensions["scenario"] = ext.get("valueString", "")
            elif "special-considerations" in url:
                extensions["special-considerations"] = ext.get("valueString", "")

        return extensions

    def _calculate_age(self, dob_str: str) -> int:
        """Calculate age from date of birth string"""
        try:
            dob = datetime.strptime(dob_str, "%Y-%m-%d").date()
            today = date.today()
            age = today.year - dob.year
            if (today.month, today.day) < (dob.month, dob.day):
                age -= 1
            return age
        except (ValueError, TypeError):
            return 0

    def _transform_condition(self, condition: Dict[str, Any]) -> CairMapCondition:
        """Transform FHIR Condition to cair-map format"""
        code_obj = condition.get("code", {})

        # Extract ICD-10 code
        icd_code = ""
        title = code_obj.get("text", "")

        for coding in code_obj.get("coding", []):
            system = coding.get("system", "")
            if "icd-10" in system.lower():
                icd_code = coding.get("code", "")
                if not title:
                    title = coding.get("display", "")
                break

        # Fall back to first coding if no ICD-10
        if not icd_code and code_obj.get("coding"):
            coding = code_obj["coding"][0]
            icd_code = coding.get("code", "")
            if not title:
                title = coding.get("display", "")

        return CairMapCondition(code=icd_code, title=title)

    def _transform_medication(self, medication: Dict[str, Any]) -> CairMapMedication:
        """Transform FHIR MedicationRequest to cair-map format"""
        med_codeable = medication.get("medicationCodeableConcept", {})
        name = med_codeable.get("text", "")

        if not name:
            for coding in med_codeable.get("coding", []):
                name = coding.get("display", "")
                if name:
                    break

        # Extract note
        note = None
        notes = medication.get("note", [])
        if notes:
            note = notes[0].get("text")

        return CairMapMedication(name=name, note=note)

    def _transform_allergy(self, allergy: Dict[str, Any]) -> CairMapAllergy:
        """Transform FHIR AllergyIntolerance to cair-map format"""
        code_obj = allergy.get("code", {})
        name = code_obj.get("text", "")

        if not name:
            for coding in code_obj.get("coding", []):
                name = coding.get("display", "")
                if name:
                    break

        # Extract reaction and severity
        reaction = None
        severity = None

        reactions = allergy.get("reaction", [])
        if reactions:
            rxn = reactions[0]
            severity = rxn.get("severity")

            manifestations = rxn.get("manifestation", [])
            if manifestations:
                manif = manifestations[0]
                reaction = manif.get("text") or manif.get("coding", [{}])[0].get("display")

        return CairMapAllergy(name=name, reaction=reaction, severity=severity)

    def _derive_cohort(
        self,
        age: int,
        sex: str,
        health_literacy: str,
        conditions: List[CairMapCondition]
    ) -> str:
        """Derive patient cohort based on demographics and conditions"""
        # Age bucket
        if age < 40:
            age_bucket = "young"
        elif age < 65:
            age_bucket = "middle_aged"
        elif age < 75:
            age_bucket = "senior"
        else:
            age_bucket = "elderly"

        # Check for cardiac conditions
        has_cardiac = any(
            c.code.startswith("I") for c in conditions
        )
        condition_type = "cardiac" if has_cardiac else "general"

        return f"{age_bucket}_{condition_type}_{health_literacy}"
