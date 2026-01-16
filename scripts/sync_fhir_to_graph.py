#!/usr/bin/env python3
"""
Sync FHIR Server to Neo4j Graph

This script reads patients from any FHIR R4 server (real hospital EHR or
test HAPI FHIR) and loads them into the cair-map Neo4j graph database.

Usage:
    # For testing with local HAPI FHIR
    python scripts/sync_fhir_to_graph.py --fhir-url http://localhost:8080/fhir

    # For real hospital FHIR endpoint
    python scripts/sync_fhir_to_graph.py \\
        --fhir-url https://hospital.example.com/fhir \\
        --hospital-id memorial_cardiac \\
        --care-pathway CardiacMRI_Standard

This is the production script - use it with any FHIR-compliant server.
"""

import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

import click


def print_header(text: str):
    click.echo("\n" + "=" * 70)
    click.echo(f"  {text}")
    click.echo("=" * 70)


def print_step(step_num: int, text: str):
    click.echo(f"\n[Step {step_num}] {text}")
    click.echo("-" * 50)


@click.command()
@click.option("--fhir-url", required=True, help="FHIR server URL (e.g., http://localhost:8080/fhir)")
@click.option("--hospital-id", required=True, help="Hospital identifier for Neo4j")
@click.option("--hospital-name", default=None, help="Hospital display name")
@click.option("--care-pathway", default="CardiacMRI_Standard", help="Default care pathway")
@click.option("--procedure-days", default=7, help="Days until procedure date")
@click.option("--patient-tag", default=None, help="Filter patients by tag (optional)")
@click.option("--neo4j-uri", default=None, help="Neo4j URI (defaults to cair-map settings)")
@click.option("--neo4j-user", default=None, help="Neo4j username")
@click.option("--neo4j-password", default=None, help="Neo4j password")
@click.option("--dry-run", is_flag=True, help="Extract and transform without loading to Neo4j")
def main(
    fhir_url: str,
    hospital_id: str,
    hospital_name: str,
    care_pathway: str,
    procedure_days: int,
    patient_tag: str,
    neo4j_uri: str,
    neo4j_user: str,
    neo4j_password: str,
    dry_run: bool
):
    """
    Sync patients from FHIR server to Neo4j graph.

    Reads patients and their clinical data (conditions, medications, allergies)
    from any FHIR R4 compliant server and loads them into the cair-map graph.
    """
    from src.fhir_client import FHIRClient, PatientExtractor
    from src.transformers import PatientTransformer
    from src.graph_sync import PatientLoader

    print_header("Sync FHIR to Neo4j Graph")

    click.echo(f"\nConfiguration:")
    click.echo(f"  FHIR Server: {fhir_url}")
    click.echo(f"  Hospital ID: {hospital_id}")
    click.echo(f"  Care Pathway: {care_pathway}")
    click.echo(f"  Patient Tag Filter: {patient_tag or 'None (all patients)'}")
    click.echo(f"  Dry Run: {dry_run}")

    # Step 1: Connect to FHIR server
    print_step(1, "Connecting to FHIR Server")

    client = FHIRClient(base_url=fhir_url)

    if not client.health_check():
        click.echo(click.style("Error: FHIR server not available", fg="red"))
        click.echo(f"Cannot connect to: {fhir_url}")
        return

    patient_count = client.get_patient_count()
    click.echo(click.style(f"FHIR Server: Online", fg="green"))
    click.echo(f"Total patients on server: {patient_count}")

    if patient_count == 0:
        click.echo(click.style("No patients found on FHIR server", fg="yellow"))
        return

    # Step 2: Extract patients from FHIR
    print_step(2, "Extracting Patients from FHIR")

    extractor = PatientExtractor(client)

    def extract_progress(current, total):
        click.echo(f"  [{current}/{total}] Extracting patient data...")

    extracted_patients = extractor.extract_all_patients(
        hospital_tag=patient_tag,
        use_everything=True,
        progress_callback=extract_progress
    )

    click.echo(f"Extracted {len(extracted_patients)} patients with clinical data")

    if not extracted_patients:
        click.echo(click.style("No patients extracted", fg="yellow"))
        return

    # Show sample
    click.echo(f"\nSample extracted patient:")
    sample = extracted_patients[0]
    click.echo(f"  ID: {sample.patient_id}")
    click.echo(f"  Conditions: {len(sample.conditions)}")
    click.echo(f"  Medications: {len(sample.medications)}")
    click.echo(f"  Allergies: {len(sample.allergies)}")

    # Step 3: Transform to cair-map format
    print_step(3, "Transforming to cair-map Format")

    transformer = PatientTransformer()
    cair_map_patients = transformer.transform_batch(extracted_patients)

    click.echo(f"Transformed {len(cair_map_patients)} patients")

    # Show sample
    if cair_map_patients:
        sample = cair_map_patients[0]
        click.echo(f"\nSample transformed patient:")
        click.echo(f"  Name: {sample.first_name} {sample.last_name}")
        click.echo(f"  Age: {sample.age}")
        click.echo(f"  Language: {sample.language}")
        click.echo(f"  Health Literacy: {sample.health_literacy}")
        click.echo(f"  Cohort: {sample.cohort}")

    if dry_run:
        print_header("Dry Run Complete")
        click.echo(f"\nWould load {len(cair_map_patients)} patients to Neo4j")
        click.echo("Run without --dry-run to actually load to Neo4j")
        return

    # Step 4: Load to Neo4j
    print_step(4, "Loading to Neo4j Graph")

    loader = PatientLoader(
        neo4j_uri=neo4j_uri,
        neo4j_user=neo4j_user,
        neo4j_password=neo4j_password
    )

    if not loader.connect():
        click.echo(click.style("Error: Cannot connect to Neo4j", fg="red"))
        return

    click.echo(click.style(f"Neo4j: Connected ({loader.uri})", fg="green"))

    def load_progress(current, total):
        click.echo(f"  [{current}/{total}] Loading patient...")

    stats = loader.load_patients(
        patients=cair_map_patients,
        hospital_id=hospital_id,
        care_pathway=care_pathway,
        procedure_days_ahead=procedure_days,
        progress_callback=load_progress
    )

    loader.close()

    # Print results
    print_header("Sync Complete")

    click.echo(f"\nResults:")
    click.echo(f"  Patients Loaded: {stats.loaded}/{stats.total}")
    click.echo(f"  Conditions Created: {stats.conditions_created}")
    click.echo(f"  Medications Created: {stats.medications_created}")
    click.echo(f"  Allergies Created: {stats.allergies_created}")

    if stats.errors:
        click.echo(f"\nErrors ({stats.failed}):")
        for error in stats.errors[:5]:
            click.echo(click.style(f"  - {error}", fg="red"))

    click.echo(f"\nVerification Query:")
    click.echo(f"  MATCH (p:Patient {{source: 'fhir_pipeline', hospital_id: '{hospital_id}'}}) RETURN count(p)")

    click.echo(f"\nNext Steps:")
    click.echo(f"  1. Run cair-map demo: cd ../cair-map && python demo/api.py")
    click.echo(f"  2. Test personalization with synced patients")


if __name__ == "__main__":
    main()
