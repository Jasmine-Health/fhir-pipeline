#!/usr/bin/env python3
"""
Load Patient Profiles Directly to Neo4j

This is a utility script that loads the bundled patient profiles directly
into Neo4j WITHOUT requiring a FHIR server. Use this for quick testing
when you don't have HAPI FHIR running.

For production use with real hospitals, use sync_fhir_to_graph.py instead.

Usage:
    python scripts/load_profiles_direct.py --hospital-id "test_hospital" --patient-count 10
"""

import sys
from pathlib import Path
from datetime import date

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

import click


def print_header(text: str):
    click.echo("\n" + "=" * 70)
    click.echo(f"  {text}")
    click.echo("=" * 70)


@click.command()
@click.option("--hospital-id", required=True, help="Hospital identifier")
@click.option("--hospital-name", default=None, help="Hospital display name")
@click.option("--patient-count", default=24, help="Number of patients to load")
@click.option("--care-pathway", default="CardiacMRI_Standard", help="Default care pathway")
@click.option("--procedure-days", default=7, help="Days until procedure date")
@click.option("--neo4j-uri", default=None, help="Neo4j URI")
@click.option("--neo4j-user", default=None, help="Neo4j username")
@click.option("--neo4j-password", default=None, help="Neo4j password")
def main(
    hospital_id: str,
    hospital_name: str,
    patient_count: int,
    care_pathway: str,
    procedure_days: int,
    neo4j_uri: str,
    neo4j_user: str,
    neo4j_password: str
):
    """
    Load bundled patient profiles directly to Neo4j.

    This bypasses the FHIR server for quick testing. For production
    with real hospital data, use sync_fhir_to_graph.py instead.
    """
    from src.generators.profiles.cardiac_profiles import CARDIAC_PATIENT_PROFILES
    from src.transformers import CairMapPatient
    from src.graph_sync import PatientLoader

    print_header("Load Patient Profiles Directly to Neo4j")

    click.echo(f"\nConfiguration:")
    click.echo(f"  Hospital ID: {hospital_id}")
    click.echo(f"  Patient Count: {patient_count}")
    click.echo(f"  Care Pathway: {care_pathway}")

    # Limit to available profiles
    patient_count = min(patient_count, len(CARDIAC_PATIENT_PROFILES))
    profiles = CARDIAC_PATIENT_PROFILES[:patient_count]

    click.echo(f"\nTransforming {patient_count} patient profiles...")

    # Transform profiles to cair-map format
    patients = []
    for profile in profiles:
        current_year = date.today().year
        age = current_year - profile.birth_year

        # Derive cohort
        if age < 40:
            age_bucket = "young"
        elif age < 65:
            age_bucket = "middle_aged"
        elif age < 75:
            age_bucket = "senior"
        else:
            age_bucket = "elderly"

        has_cardiac = any(c.code.startswith("I") for c in profile.conditions)
        condition_type = "cardiac" if has_cardiac else "general"
        cohort = f"{age_bucket}_{condition_type}_{profile.health_literacy.value}"

        patient = CairMapPatient(
            ehr_id=profile.id,
            mrn=f"MRN-{profile.id.upper()}",
            first_name=profile.first_name,
            last_name=profile.last_name,
            date_of_birth=f"{profile.birth_year}-06-15",
            sex=profile.sex,
            age=age,
            language=profile.language,
            health_literacy=profile.health_literacy.value,
            conditions=[
                type("Condition", (), {"code": c.code, "title": c.title})()
                for c in profile.conditions
            ],
            medications=[
                type("Medication", (), {"name": m.name, "note": m.note})()
                for m in profile.medications
            ],
            allergies=[
                type("Allergy", (), {
                    "name": a.name,
                    "reaction": a.reaction,
                    "severity": a.severity
                })()
                for a in profile.allergies
            ],
            special_considerations=profile.special_considerations,
            cohort=cohort,
            scenario=profile.scenario,
            demo_question=profile.demo_question,
            expected_personalization=profile.expected_personalization,
            source="fhir_pipeline"
        )
        patients.append(patient)

    click.echo(f"Transformed {len(patients)} patients")

    # Load to Neo4j
    click.echo(f"\nConnecting to Neo4j...")

    loader = PatientLoader(
        neo4j_uri=neo4j_uri,
        neo4j_user=neo4j_user,
        neo4j_password=neo4j_password
    )

    if not loader.connect():
        click.echo(click.style("Error: Cannot connect to Neo4j", fg="red"))
        return

    click.echo(click.style(f"Neo4j: Connected ({loader.uri})", fg="green"))

    click.echo(f"\nLoading patients...")

    def progress(current, total):
        click.echo(f"  [{current}/{total}] Loading...")

    stats = loader.load_patients(
        patients=patients,
        hospital_id=hospital_id,
        care_pathway=care_pathway,
        procedure_days_ahead=procedure_days,
        progress_callback=progress
    )

    loader.close()

    # Print results
    print_header("Load Complete")

    click.echo(f"\nResults:")
    click.echo(f"  Patients Loaded: {stats.loaded}/{stats.total}")
    click.echo(f"  Conditions: {stats.conditions_created}")
    click.echo(f"  Medications: {stats.medications_created}")
    click.echo(f"  Allergies: {stats.allergies_created}")

    if stats.errors:
        click.echo(f"\nErrors ({stats.failed}):")
        for error in stats.errors[:5]:
            click.echo(click.style(f"  - {error}", fg="red"))

    click.echo(f"\nVerification:")
    click.echo(f"  MATCH (p:Patient {{hospital_id: '{hospital_id}'}}) RETURN count(p)")


if __name__ == "__main__":
    main()
