#!/usr/bin/env python3
"""
FHIR Pipeline CLI Orchestrator

End-to-end pipeline for hospital pilot setup:
1. Generate FHIR bundles from patient profiles
2. (Optional) Upload to HAPI FHIR server
3. Transform to cair-map format
4. Load into Neo4j graph database
"""

import sys
from pathlib import Path
from datetime import datetime, date

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

import click


def print_header(text: str):
    """Print a formatted header"""
    click.echo("\n" + "=" * 70)
    click.echo(f"  {text}")
    click.echo("=" * 70)


def print_step(step_num: int, text: str):
    """Print a step indicator"""
    click.echo(f"\n[Step {step_num}] {text}")
    click.echo("-" * 50)


@click.group()
def cli():
    """FHIR Pipeline for Hospital Pilot Setup"""
    pass


@cli.command()
@click.option("--hospital-id", default="pilot_cardiac_center", help="Hospital identifier")
@click.option("--hospital-name", default=None, help="Hospital display name")
@click.option("--patient-count", default=24, help="Number of patients to generate")
@click.option("--care-pathway", default="CardiacMRI_Standard", help="Default care pathway")
@click.option("--procedure-days", default=7, help="Days until procedure date")
@click.option("--use-fhir-server", is_flag=True, help="Upload to FHIR server before Neo4j")
@click.option("--fhir-url", default="http://localhost:8080/fhir", help="FHIR server URL")
@click.option("--save-bundles", is_flag=True, help="Save generated bundles to files")
@click.option("--output-dir", default="data/generated", help="Directory for saved bundles")
@click.option("--neo4j-uri", default=None, help="Neo4j URI (defaults to cair-map settings)")
@click.option("--neo4j-user", default=None, help="Neo4j username")
@click.option("--neo4j-password", default=None, help="Neo4j password")
@click.option("--dry-run", is_flag=True, help="Generate bundles without loading to Neo4j")
def run(
    hospital_id: str,
    hospital_name: str,
    patient_count: int,
    care_pathway: str,
    procedure_days: int,
    use_fhir_server: bool,
    fhir_url: str,
    save_bundles: bool,
    output_dir: str,
    neo4j_uri: str,
    neo4j_user: str,
    neo4j_password: str,
    dry_run: bool
):
    """
    Run the complete FHIR pipeline.

    Generates patient data from profiles and loads into Neo4j.
    Optionally uploads to HAPI FHIR server first.
    """
    # Lazy imports
    from src.generators.profiles.cardiac_profiles import CARDIAC_PATIENT_PROFILES
    from src.generators.bundle_factory import create_all_patient_bundles, save_bundles_to_files
    from src.transformers import CairMapPatient

    print_header("FHIR Pipeline for Hospital Pilot Setup")

    click.echo(f"\nConfiguration:")
    click.echo(f"  Hospital ID: {hospital_id}")
    click.echo(f"  Patient Count: {patient_count}")
    click.echo(f"  Care Pathway: {care_pathway}")
    click.echo(f"  Use FHIR Server: {use_fhir_server}")
    click.echo(f"  Dry Run: {dry_run}")

    # Limit to available profiles
    patient_count = min(patient_count, len(CARDIAC_PATIENT_PROFILES))
    click.echo(f"\nUsing {patient_count} patient profiles from library")

    # Step 1: Generate FHIR bundles
    print_step(1, "Generating FHIR Bundles")

    profiles = CARDIAC_PATIENT_PROFILES[:patient_count]
    bundles = create_all_patient_bundles(hospital_id, patient_count)

    click.echo(f"Generated {len(bundles)} patient bundles")

    # Optionally save bundles
    if save_bundles:
        file_paths = save_bundles_to_files(bundles, output_dir)
        click.echo(f"Saved bundles to {output_dir}/")
        for path in file_paths[:3]:
            click.echo(f"  - {Path(path).name}")
        if len(file_paths) > 3:
            click.echo(f"  ... and {len(file_paths) - 3} more")

    # Step 2: (Optional) Upload to FHIR server
    if use_fhir_server:
        from src.fhir_client import FHIRClient, BundleLoader

        print_step(2, "Uploading to FHIR Server")

        client = FHIRClient(base_url=fhir_url)

        if not client.health_check():
            click.echo(click.style("Error: FHIR server not available", fg="red"))
            click.echo(f"Please ensure HAPI FHIR is running at {fhir_url}")
            click.echo("\nTo start FHIR server:")
            click.echo("  cd fhir-pipeline/docker")
            click.echo("  docker-compose up -d")
            return

        loader = BundleLoader(client)

        def progress(current, total, patient_id):
            click.echo(f"  [{current}/{total}] Uploading {patient_id}")

        result = loader.load_bundles(bundles, progress_callback=progress)

        click.echo(f"\nFHIR Upload Results:")
        click.echo(f"  Successful: {result.successful}")
        click.echo(f"  Failed: {result.failed}")

        if result.errors:
            for error in result.errors[:3]:
                click.echo(click.style(f"  Error: {error}", fg="red"))

    # Step 3: Transform to cair-map format
    print_step(3 if use_fhir_server else 2, "Transforming to cair-map Format")

    # Transform directly from profiles (more efficient than FHIR round-trip)
    cair_map_patients = transform_profiles_to_cair_map(profiles, CairMapPatient)

    click.echo(f"Transformed {len(cair_map_patients)} patients")

    if dry_run:
        print_step(4 if use_fhir_server else 3, "Dry Run - Skipping Neo4j Load")
        click.echo("Would load the following patients:")
        for patient in cair_map_patients[:5]:
            click.echo(f"  - {patient.first_name} {patient.last_name} ({patient.ehr_id})")
        if len(cair_map_patients) > 5:
            click.echo(f"  ... and {len(cair_map_patients) - 5} more")
        return

    # Step 4: Load into Neo4j
    from src.graph_sync import PatientLoader

    print_step(4 if use_fhir_server else 3, "Loading into Neo4j Graph")

    graph_loader = PatientLoader(
        neo4j_uri=neo4j_uri,
        neo4j_user=neo4j_user,
        neo4j_password=neo4j_password
    )

    if not graph_loader.connect():
        click.echo(click.style("Error: Cannot connect to Neo4j", fg="red"))
        return

    def graph_progress(current, total):
        click.echo(f"  [{current}/{total}] Loading patient...")

    stats = graph_loader.load_patients(
        patients=cair_map_patients,
        hospital_id=hospital_id,
        care_pathway=care_pathway,
        procedure_days_ahead=procedure_days,
        progress_callback=graph_progress
    )

    graph_loader.close()

    # Print results
    print_header("Pipeline Complete")

    click.echo(f"\nResults:")
    click.echo(f"  Patients Loaded: {stats.loaded}/{stats.total}")
    click.echo(f"  Conditions Created: {stats.conditions_created}")
    click.echo(f"  Medications Created: {stats.medications_created}")
    click.echo(f"  Allergies Created: {stats.allergies_created}")

    if stats.errors:
        click.echo(f"\nErrors ({stats.failed}):")
        for error in stats.errors[:5]:
            click.echo(click.style(f"  - {error}", fg="red"))

    click.echo(f"\nVerification:")
    click.echo(f"  Neo4j Query: MATCH (p:Patient {{source: 'fhir_pipeline', hospital_id: '{hospital_id}'}}) RETURN count(p)")

    click.echo(f"\nNext Steps:")
    click.echo(f"  1. Run cair-map demo API: cd ../cair-map && python demo/api.py")
    click.echo(f"  2. Test personalization with loaded patients")


@cli.command()
@click.option("--hospital-id", default=None, help="Hospital ID to filter (optional)")
@click.option("--neo4j-uri", default=None, help="Neo4j URI")
@click.option("--neo4j-user", default=None, help="Neo4j username")
@click.option("--neo4j-password", default=None, help="Neo4j password")
def cleanup(hospital_id: str, neo4j_uri: str, neo4j_user: str, neo4j_password: str):
    """Delete FHIR pipeline patients from Neo4j"""
    from src.graph_sync import PatientLoader

    print_header("Cleanup FHIR Pipeline Patients")

    loader = PatientLoader(
        neo4j_uri=neo4j_uri,
        neo4j_user=neo4j_user,
        neo4j_password=neo4j_password
    )

    if not loader.connect():
        click.echo(click.style("Error: Cannot connect to Neo4j", fg="red"))
        return

    count = loader.get_patient_count(hospital_id)
    click.echo(f"Found {count} FHIR pipeline patients")

    if count == 0:
        click.echo("Nothing to delete")
        return

    if click.confirm(f"Delete {count} patients?"):
        deleted = loader.delete_fhir_pipeline_patients(hospital_id)
        click.echo(f"Deleted {deleted} patients")

    loader.close()


@cli.command("list-profiles")
@click.option("--patient-count", default=24, help="Number of patients")
def list_profiles(patient_count: int):
    """List available patient profiles"""
    from src.generators.profiles.cardiac_profiles import CARDIAC_PATIENT_PROFILES

    print_header("Available Patient Profiles")

    count = min(patient_count, len(CARDIAC_PATIENT_PROFILES))

    click.echo(f"\n{'ID':<12} {'Scenario':<50} {'Pathway':<20}")
    click.echo("-" * 82)

    for profile in CARDIAC_PATIENT_PROFILES[:count]:
        click.echo(f"{profile.id:<12} {profile.scenario:<50} {profile.care_pathway.value:<20}")

    click.echo(f"\nTotal: {len(CARDIAC_PATIENT_PROFILES)} profiles available")


@cli.command("check-fhir")
@click.option("--fhir-url", default="http://localhost:8080/fhir", help="FHIR server URL")
def check_fhir(fhir_url: str):
    """Check FHIR server status"""
    from src.fhir_client import FHIRClient

    print_header("FHIR Server Status")

    client = FHIRClient(base_url=fhir_url)

    if client.health_check():
        click.echo(click.style(f"FHIR Server: Online ({fhir_url})", fg="green"))
        count = client.get_patient_count()
        click.echo(f"Patient Count: {count}")
    else:
        click.echo(click.style(f"FHIR Server: Offline ({fhir_url})", fg="red"))
        click.echo("\nTo start FHIR server:")
        click.echo("  cd fhir-pipeline/docker")
        click.echo("  docker-compose up -d")


@cli.command("check-neo4j")
@click.option("--neo4j-uri", default=None, help="Neo4j URI")
@click.option("--neo4j-user", default=None, help="Neo4j username")
@click.option("--neo4j-password", default=None, help="Neo4j password")
def check_neo4j(neo4j_uri: str, neo4j_user: str, neo4j_password: str):
    """Check Neo4j connection status"""
    from src.graph_sync import PatientLoader

    print_header("Neo4j Status")

    loader = PatientLoader(
        neo4j_uri=neo4j_uri,
        neo4j_user=neo4j_user,
        neo4j_password=neo4j_password
    )

    if loader.connect():
        click.echo(click.style(f"Neo4j: Connected ({loader.uri})", fg="green"))
        count = loader.get_patient_count()
        click.echo(f"FHIR Pipeline Patients: {count}")
        loader.close()
    else:
        click.echo(click.style(f"Neo4j: Connection Failed ({loader.uri})", fg="red"))


def transform_profiles_to_cair_map(profiles, CairMapPatient):
    """
    Transform patient profiles directly to cair-map format.

    This is more efficient than generating FHIR bundles and then
    transforming them, when we don't need the FHIR server.
    """
    patients = []

    for profile in profiles:
        # Calculate age
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

    return patients


def main():
    """Entry point"""
    cli()


if __name__ == "__main__":
    main()
