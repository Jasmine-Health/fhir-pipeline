# FHIR Pipeline for Hospital Pilot Setup

A pipeline for syncing FHIR patient data to the cair-map Neo4j graph database. Includes tools for both testing with dummy data and production use with real hospital FHIR endpoints.

## Two Workflows

### 1. Testing/Demo Workflow (Dummy Data)

For testing and demonstrations, use the dummy patient profiles:

```bash
# Option A: Use HAPI FHIR server (full FHIR workflow)
cd docker && docker-compose up -d          # Start HAPI FHIR
python scripts/setup_fhir_server.py        # Populate with dummy patients
python scripts/sync_fhir_to_graph.py \     # Sync to Neo4j
    --fhir-url http://localhost:8080/fhir \
    --hospital-id demo_hospital

# Option B: Direct load (skip FHIR, faster for testing)
python scripts/load_profiles_direct.py --hospital-id "test_hospital"
```

### 2. Production Workflow (Real Hospital)

For real hospital deployments, only run the sync script:

```bash
python scripts/sync_fhir_to_graph.py \
    --fhir-url https://hospital.example.com/fhir \
    --hospital-id memorial_cardiac \
    --care-pathway CardiacMRI_Standard
```

## Scripts

| Script | Purpose | When to Use |
|--------|---------|-------------|
| `setup_fhir_server.py` | Populate HAPI FHIR with dummy patients | Testing/demos only |
| `sync_fhir_to_graph.py` | Read any FHIR server → load to Neo4j | **Production use** |
| `load_profiles_direct.py` | Load profiles directly to Neo4j | Quick testing without FHIR |

## Quick Start

```bash
# Install dependencies
cd fhir-pipeline
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

# Quick test (loads 10 dummy patients directly to Neo4j)
python scripts/load_profiles_direct.py --hospital-id "quick_test" --patient-count 10

# Verify
python scripts/run_pipeline.py check-neo4j
```

## Script Reference

### setup_fhir_server.py

Populates a HAPI FHIR server with realistic dummy cardiac patients.

```bash
python scripts/setup_fhir_server.py \
    --fhir-url http://localhost:8080/fhir \
    --patient-count 20 \
    --hospital-tag demo_hospital \
    --save-bundles  # Optional: save FHIR bundles to files
```

**Options:**
- `--fhir-url` - HAPI FHIR server URL (default: http://localhost:8080/fhir)
- `--patient-count` - Number of dummy patients (default: 24, max: 24)
- `--hospital-tag` - Tag to identify these patients in FHIR
- `--save-bundles` - Also save generated FHIR bundles to disk

### sync_fhir_to_graph.py

**This is the production script.** Reads from any FHIR R4 server and loads patients to Neo4j.

```bash
# For testing with local HAPI FHIR
python scripts/sync_fhir_to_graph.py \
    --fhir-url http://localhost:8080/fhir \
    --hospital-id demo_hospital

# For real hospital FHIR endpoint
python scripts/sync_fhir_to_graph.py \
    --fhir-url https://hospital.epic.com/fhir/R4 \
    --hospital-id memorial_cardiac \
    --hospital-name "Memorial Cardiac Center" \
    --care-pathway CardiacMRI_Standard \
    --procedure-days 7
```

**Options:**
- `--fhir-url` - FHIR server URL **(required)**
- `--hospital-id` - Hospital identifier for Neo4j **(required)**
- `--hospital-name` - Display name for the hospital
- `--care-pathway` - Default care pathway (default: CardiacMRI_Standard)
- `--procedure-days` - Days until procedure (default: 7)
- `--patient-tag` - Filter patients by FHIR tag
- `--dry-run` - Extract and transform without loading to Neo4j

### load_profiles_direct.py

Utility script for quick testing - loads bundled profiles directly to Neo4j without requiring a FHIR server.

```bash
python scripts/load_profiles_direct.py \
    --hospital-id "test_hospital" \
    --patient-count 10
```

## Patient Profiles (24 Scenarios)

The bundled profiles cover diverse cardiac personalization scenarios:

| ID | Scenario | Key Personalization |
|----|----------|-------------------|
| fhir_001 | Diabetic | Modified fasting, blood sugar monitoring |
| fhir_002 | Theophylline | CRITICAL: Stop 24h before stress MRI |
| fhir_003 | Claustrophobia | Sedation options, wide-bore scanner |
| fhir_004 | Pacemaker | Device interrogation required |
| fhir_005 | Low Health Literacy | Simple language |
| fhir_006 | Spanish Speaker | Respond in Spanish |
| fhir_007 | Gadolinium Allergy | No contrast protocol |
| fhir_008 | CKD Stage 4 | Nephrology clearance |
| fhir_009 | First MRI | Detailed walkthrough |
| fhir_010 | Warfarin for MRI | Continue medication |
| fhir_011 | Warfarin for Cath | STOP 5 days before |
| ... | ... | ... |

Run `python scripts/run_pipeline.py list-profiles` to see all 24.

## Project Structure

```
fhir-pipeline/
├── docker/
│   └── docker-compose.yml          # HAPI FHIR + PostgreSQL
├── scripts/
│   ├── setup_fhir_server.py        # Populate FHIR with dummy data
│   ├── sync_fhir_to_graph.py       # FHIR → Neo4j (PRODUCTION)
│   ├── load_profiles_direct.py     # Direct load for testing
│   └── run_pipeline.py             # Utility commands
├── src/
│   ├── generators/                  # FHIR resource generators
│   │   └── profiles/
│   │       └── cardiac_profiles.py  # 24 patient templates
│   ├── fhir_client/                 # FHIR REST client
│   ├── transformers/                # FHIR → cair-map format
│   └── graph_sync/                  # Neo4j loader
└── data/generated/                  # Saved FHIR bundles
```

## Starting HAPI FHIR Server

```bash
cd docker
docker-compose up -d

# Wait ~60 seconds for startup
# Verify at http://localhost:8080
```

## Verification

```bash
# Check Neo4j connection and patient count
python scripts/run_pipeline.py check-neo4j

# Check FHIR server status
python scripts/run_pipeline.py check-fhir

# Verify in Neo4j directly
# MATCH (p:Patient {source: 'fhir_pipeline'}) RETURN count(p)
```

## Cleanup

```bash
# Remove test patients from Neo4j
python scripts/run_pipeline.py cleanup --hospital-id "test_hospital"
```

## Integration with cair-map

After loading patients:

```bash
# Start cair-map demo
cd ../cair-map
python demo/api.py

# Access at http://localhost:8002
# Select a patient and test personalization
```

## For Real Hospital Deployment

1. **Get FHIR endpoint URL** from hospital IT
2. **Configure authentication** if required (OAuth2, API key)
3. **Run sync script**:
   ```bash
   python scripts/sync_fhir_to_graph.py \
       --fhir-url https://hospital-fhir.example.com/R4 \
       --hospital-id hospital_001 \
       --hospital-name "Hospital Name"
   ```
4. **Verify** patients loaded correctly
5. **Configure cair-map** to use the hospital's Neo4j instance

## Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `NEO4J_URI` | `bolt://172.190.179.112:7687` | Neo4j connection |
| `NEO4J_USER` | `neo4j` | Neo4j username |
| `NEO4J_PASSWORD` | `Neo4jPassword123!` | Neo4j password |
