"""
FHIR Pipeline Configuration Settings
"""
import os
from dataclasses import dataclass, field
from typing import Optional


@dataclass
class FHIRServerSettings:
    """HAPI FHIR server configuration"""
    base_url: str = "http://localhost:8080/fhir"
    timeout: int = 30

    @classmethod
    def from_env(cls) -> "FHIRServerSettings":
        return cls(
            base_url=os.getenv("FHIR_BASE_URL", "http://localhost:8080/fhir"),
            timeout=int(os.getenv("FHIR_TIMEOUT", "30"))
        )


@dataclass
class Neo4jSettings:
    """Neo4j connection configuration - imports from cair-map if available"""
    uri: str = "bolt://172.190.179.112:7687"
    user: str = "neo4j"
    password: str = "Neo4jPassword123!"

    @classmethod
    def from_env(cls) -> "Neo4jSettings":
        return cls(
            uri=os.getenv("NEO4J_URI", "bolt://172.190.179.112:7687"),
            user=os.getenv("NEO4J_USER", "neo4j"),
            password=os.getenv("NEO4J_PASSWORD", "Neo4jPassword123!")
        )

    @classmethod
    def from_cair_map(cls) -> "Neo4jSettings":
        """Try to import settings from cair-map shared constants"""
        try:
            import sys
            from pathlib import Path
            # Add cair-map to path
            cair_map_path = Path(__file__).parent.parent.parent.parent / "cair-map"
            sys.path.insert(0, str(cair_map_path))
            from shared.constants import (
                DEFAULT_NEO4J_URI,
                DEFAULT_NEO4J_USER,
                DEFAULT_NEO4J_PASSWORD
            )
            return cls(
                uri=DEFAULT_NEO4J_URI,
                user=DEFAULT_NEO4J_USER,
                password=DEFAULT_NEO4J_PASSWORD
            )
        except ImportError:
            return cls.from_env()


@dataclass
class PipelineSettings:
    """Overall pipeline configuration"""
    fhir: FHIRServerSettings = field(default_factory=FHIRServerSettings.from_env)
    neo4j: Neo4jSettings = field(default_factory=Neo4jSettings.from_cair_map)
    output_dir: str = "data/generated"
    default_hospital_id: str = "pilot_cardiac_center"
    default_care_pathway: str = "CardiacMRI_Standard"

    @classmethod
    def load(cls) -> "PipelineSettings":
        """Load settings from environment and cair-map"""
        return cls(
            fhir=FHIRServerSettings.from_env(),
            neo4j=Neo4jSettings.from_cair_map(),
            output_dir=os.getenv("OUTPUT_DIR", "data/generated"),
            default_hospital_id=os.getenv("DEFAULT_HOSPITAL_ID", "pilot_cardiac_center"),
            default_care_pathway=os.getenv("DEFAULT_CARE_PATHWAY", "CardiacMRI_Standard")
        )
