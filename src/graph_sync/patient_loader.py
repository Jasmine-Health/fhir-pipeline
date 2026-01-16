"""
Neo4j Patient Loader

Loads transformed patients into cair-map Neo4j graph database.
Uses same patterns as cair-map/scripts/create_demo_showcase_patients.py
"""

from datetime import datetime, timedelta
from typing import List, Optional
from dataclasses import dataclass, field

from neo4j import GraphDatabase, Driver

from ..transformers.patient_transformer import CairMapPatient
from ..config.settings import Neo4jSettings


@dataclass
class LoadStats:
    """Statistics from patient loading operation"""
    total: int = 0
    loaded: int = 0
    failed: int = 0
    conditions_created: int = 0
    medications_created: int = 0
    allergies_created: int = 0
    errors: List[str] = field(default_factory=list)


class PatientLoader:
    """
    Loads patients into Neo4j graph database.

    Creates Patient nodes with relationships to:
    - Hospital (BELONGS_TO)
    - CarePathway (ENROLLED_IN)
    - Condition (HAS_CONDITION)
    - Medication (TAKES_MEDICATION)
    - Allergy (HAS_ALLERGY)
    """

    def __init__(
        self,
        neo4j_uri: str = None,
        neo4j_user: str = None,
        neo4j_password: str = None
    ):
        """
        Initialize loader with Neo4j connection.

        Args:
            neo4j_uri: Neo4j connection URI (defaults to cair-map settings)
            neo4j_user: Neo4j username
            neo4j_password: Neo4j password
        """
        settings = Neo4jSettings.from_cair_map()

        self.uri = neo4j_uri or settings.uri
        self.user = neo4j_user or settings.user
        self.password = neo4j_password or settings.password
        self._driver: Optional[Driver] = None

    def connect(self) -> bool:
        """Establish Neo4j connection"""
        try:
            self._driver = GraphDatabase.driver(
                self.uri,
                auth=(self.user, self.password)
            )
            # Verify connection
            with self._driver.session() as session:
                session.run("RETURN 1")
            return True
        except Exception as e:
            print(f"Failed to connect to Neo4j: {e}")
            return False

    def close(self):
        """Close Neo4j connection"""
        if self._driver:
            self._driver.close()
            self._driver = None

    def ensure_hospital(self, hospital_id: str, hospital_name: str = None) -> bool:
        """Ensure hospital node exists"""
        if not self._driver:
            return False

        name = hospital_name or f"FHIR Pipeline Hospital - {hospital_id}"

        with self._driver.session() as session:
            session.run("""
                MERGE (h:Hospital {id: $hospital_id})
                ON CREATE SET
                    h.name = $name,
                    h.created_at = datetime(),
                    h.description = 'Hospital created by FHIR pipeline'
            """, {"hospital_id": hospital_id, "name": name})

        return True

    def ensure_care_pathway(self, pathway_id: str) -> bool:
        """Ensure care pathway node exists"""
        if not self._driver:
            return False

        # Determine pathway type
        if "Cath" in pathway_id:
            pathway_type = "cardiac_intervention"
        else:
            pathway_type = "cardiac_imaging"

        with self._driver.session() as session:
            session.run("""
                MERGE (cp:CarePathway {id: $pathway_id})
                ON CREATE SET
                    cp.name = $pathway_id,
                    cp.type = $pathway_type,
                    cp.created_at = datetime()
            """, {"pathway_id": pathway_id, "pathway_type": pathway_type})

        return True

    def load_patients(
        self,
        patients: List[CairMapPatient],
        hospital_id: str,
        care_pathway: str = "CardiacMRI_Standard",
        procedure_days_ahead: int = 7,
        progress_callback: Optional[callable] = None
    ) -> LoadStats:
        """
        Load patients into Neo4j graph.

        Args:
            patients: List of CairMapPatient objects
            hospital_id: Hospital to associate patients with
            care_pathway: Default care pathway
            procedure_days_ahead: Days until procedure date
            progress_callback: Optional callback(current, total)

        Returns:
            LoadStats with results
        """
        if not self._driver:
            if not self.connect():
                return LoadStats(total=len(patients), errors=["Failed to connect to Neo4j"])

        stats = LoadStats(total=len(patients))

        # Ensure hospital and pathway exist
        self.ensure_hospital(hospital_id)
        self.ensure_care_pathway(care_pathway)

        for idx, patient in enumerate(patients):
            if progress_callback:
                progress_callback(idx + 1, len(patients))

            try:
                self._load_single_patient(
                    patient, hospital_id, care_pathway, procedure_days_ahead, stats
                )
                stats.loaded += 1
            except Exception as e:
                stats.failed += 1
                stats.errors.append(f"Patient {patient.ehr_id}: {str(e)}")

        return stats

    def _load_single_patient(
        self,
        patient: CairMapPatient,
        hospital_id: str,
        care_pathway: str,
        procedure_days_ahead: int,
        stats: LoadStats
    ):
        """Load a single patient with all relationships"""
        with self._driver.session() as session:
            # Calculate procedure date
            procedure_date = (
                datetime.now() + timedelta(days=procedure_days_ahead)
            ).strftime("%Y-%m-%d")

            # Create patient node
            session.run("""
                MERGE (p:Patient {ehr_id: $ehr_id})
                SET p.mrn = $mrn,
                    p.first_name = $first_name,
                    p.last_name = $last_name,
                    p.date_of_birth = $dob,
                    p.age = $age,
                    p.sex = $sex,
                    p.language = $language,
                    p.health_literacy = $health_literacy,
                    p.hospital_id = $hospital_id,
                    p.scenario = $scenario,
                    p.demo_question = $demo_question,
                    p.expected_personalization = $expected_personalization,
                    p.special_considerations = $special_considerations,
                    p.cohort = $cohort,
                    p.source = $source,
                    p.created_at = datetime(),
                    p.updated_at = datetime()
                WITH p
                MATCH (h:Hospital {id: $hospital_id})
                MERGE (p)-[:BELONGS_TO]->(h)
                WITH p
                MATCH (cp:CarePathway {id: $care_pathway})
                MERGE (p)-[e:ENROLLED_IN]->(cp)
                SET e.procedure_date = date($procedure_date),
                    e.status = 'active',
                    e.enrolled_at = datetime()
            """, {
                "ehr_id": patient.ehr_id,
                "mrn": patient.mrn,
                "first_name": patient.first_name,
                "last_name": patient.last_name,
                "dob": patient.date_of_birth,
                "age": patient.age,
                "sex": patient.sex,
                "language": patient.language,
                "health_literacy": patient.health_literacy,
                "hospital_id": hospital_id,
                "scenario": patient.scenario,
                "demo_question": patient.demo_question,
                "expected_personalization": patient.expected_personalization,
                "special_considerations": patient.special_considerations,
                "cohort": patient.cohort,
                "source": patient.source,
                "care_pathway": care_pathway,
                "procedure_date": procedure_date
            })

            # Add conditions
            for condition in patient.conditions:
                session.run("""
                    MATCH (p:Patient {ehr_id: $ehr_id})
                    MERGE (c:Condition {code: $code})
                    ON CREATE SET c.title = $title
                    MERGE (p)-[:HAS_CONDITION]->(c)
                """, {
                    "ehr_id": patient.ehr_id,
                    "code": condition.code,
                    "title": condition.title
                })
                stats.conditions_created += 1

            # Add medications
            for medication in patient.medications:
                session.run("""
                    MATCH (p:Patient {ehr_id: $ehr_id})
                    MERGE (m:Medication {name: $name})
                    MERGE (p)-[r:TAKES_MEDICATION]->(m)
                    SET r.note = $note
                """, {
                    "ehr_id": patient.ehr_id,
                    "name": medication.name,
                    "note": medication.note or ""
                })
                stats.medications_created += 1

            # Add allergies
            for allergy in patient.allergies:
                session.run("""
                    MATCH (p:Patient {ehr_id: $ehr_id})
                    MERGE (a:Allergy {name: $name})
                    ON CREATE SET
                        a.reaction = $reaction,
                        a.severity = $severity
                    MERGE (p)-[:HAS_ALLERGY]->(a)
                """, {
                    "ehr_id": patient.ehr_id,
                    "name": allergy.name,
                    "reaction": allergy.reaction or "",
                    "severity": allergy.severity or ""
                })
                stats.allergies_created += 1

    def delete_fhir_pipeline_patients(self, hospital_id: str = None) -> int:
        """
        Delete patients created by FHIR pipeline.

        Args:
            hospital_id: Optional hospital ID to filter

        Returns:
            Number of patients deleted
        """
        if not self._driver:
            return 0

        with self._driver.session() as session:
            if hospital_id:
                result = session.run("""
                    MATCH (p:Patient {source: 'fhir_pipeline', hospital_id: $hospital_id})
                    DETACH DELETE p
                    RETURN count(p) as deleted
                """, {"hospital_id": hospital_id})
            else:
                result = session.run("""
                    MATCH (p:Patient {source: 'fhir_pipeline'})
                    DETACH DELETE p
                    RETURN count(p) as deleted
                """)

            record = result.single()
            return record["deleted"] if record else 0

    def get_patient_count(self, hospital_id: str = None) -> int:
        """Get count of FHIR pipeline patients"""
        if not self._driver:
            return 0

        with self._driver.session() as session:
            if hospital_id:
                result = session.run("""
                    MATCH (p:Patient {source: 'fhir_pipeline', hospital_id: $hospital_id})
                    RETURN count(p) as count
                """, {"hospital_id": hospital_id})
            else:
                result = session.run("""
                    MATCH (p:Patient {source: 'fhir_pipeline'})
                    RETURN count(p) as count
                """)

            record = result.single()
            return record["count"] if record else 0
