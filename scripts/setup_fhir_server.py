#!/usr/bin/env python3
"""
Setup FHIR Server with Dummy Patients

This script populates a HAPI FHIR server with dummy cardiac patients
for testing and demonstration purposes.

Usage:
    # Start HAPI FHIR first
    cd docker && docker-compose up -d

    # Then populate with dummy patients
    python scripts/setup_fhir_server.py --patient-count 20

For real hospitals, you don't need this script - just run sync_fhir_to_graph.py
pointing to their FHIR endpoint.
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
@click.option("--fhir-url", default="http://localhost:8080/fhir", help="FHIR server URL")
@click.option("--patient-count", default=24, help="Number of dummy patients to create")
@click.option("--hospital-tag", default="demo_hospital", help="Hospital tag for patients")
@click.option("--save-bundles", is_flag=True, help="Also save bundles to files")
@click.option("--output-dir", default="data/generated", help="Directory for saved bundles")
def main(
    fhir_url: str,
    patient_count: int,
    hospital_tag: str,
    save_bundles: bool,
    output_dir: str
):
    """
    Populate HAPI FHIR server with dummy cardiac patients.

    This creates realistic patient profiles for testing MAP personalization.
    Use this for demos and testing only - not for production.
    """
    from src.generators.profiles.cardiac_profiles import CARDIAC_PATIENT_PROFILES
    from src.generators.bundle_factory import create_all_patient_bundles, save_bundles_to_files
    from src.fhir_client import FHIRClient, BundleLoader

    print_header("Setup FHIR Server with Dummy Patients")

    click.echo(f"\nConfiguration:")
    click.echo(f"  FHIR Server: {fhir_url}")
    click.echo(f"  Patient Count: {patient_count}")
    click.echo(f"  Hospital Tag: {hospital_tag}")

    # Step 1: Check FHIR server
    print_step(1, "Checking FHIR Server")

    client = FHIRClient(base_url=fhir_url)

    if not client.health_check():
        click.echo(click.style("Error: FHIR server not available", fg="red"))
        click.echo(f"\nPlease start HAPI FHIR first:")
        click.echo("  cd fhir-pipeline/docker")
        click.echo("  docker-compose up -d")
        click.echo("  # Wait ~60 seconds for startup")
        return

    current_count = client.get_patient_count()
    click.echo(click.style(f"FHIR Server: Online", fg="green"))
    click.echo(f"Current patient count: {current_count}")

    # Step 2: Generate FHIR bundles
    print_step(2, "Generating FHIR Bundles")

    patient_count = min(patient_count, len(CARDIAC_PATIENT_PROFILES))
    bundles = create_all_patient_bundles(hospital_tag, patient_count)

    click.echo(f"Generated {len(bundles)} patient bundles")

    # Optionally save bundles
    if save_bundles:
        file_paths = save_bundles_to_files(bundles, output_dir)
        click.echo(f"Saved bundles to {output_dir}/")

    # Step 3: Upload to FHIR server
    print_step(3, "Uploading to FHIR Server")

    loader = BundleLoader(client)

    def progress(current, total, patient_id):
        click.echo(f"  [{current}/{total}] {patient_id}")

    result = loader.load_bundles(bundles, progress_callback=progress)

    # Print results
    print_header("Setup Complete")

    click.echo(f"\nResults:")
    click.echo(f"  Patients Uploaded: {result.successful}/{result.total}")
    click.echo(f"  Failed: {result.failed}")

    if result.errors:
        click.echo(f"\nErrors:")
        for error in result.errors[:5]:
            click.echo(click.style(f"  - {error}", fg="red"))

    new_count = client.get_patient_count()
    click.echo(f"\nFHIR Server Status:")
    click.echo(f"  Total patients now: {new_count}")

    click.echo(f"\nPatient IDs created:")
    for pid in result.patient_ids[:5]:
        click.echo(f"  - {pid}")
    if len(result.patient_ids) > 5:
        click.echo(f"  ... and {len(result.patient_ids) - 5} more")

    click.echo(f"\nNext Step:")
    click.echo(f"  Run sync_fhir_to_graph.py to load these patients into Neo4j:")
    click.echo(f"  python scripts/sync_fhir_to_graph.py --fhir-url {fhir_url} --hospital-id {hospital_tag}")


if __name__ == "__main__":
    main()
