"""
Cardiac Patient Profile Templates

20+ realistic patient profiles covering various cardiac scenarios for
demonstrating MAP personalization capabilities.
"""

from dataclasses import dataclass, field
from typing import List, Optional
from datetime import date
from enum import Enum


class HealthLiteracy(str, Enum):
    LOW = "low"
    STANDARD = "standard"
    HIGH = "high"


class CarePathway(str, Enum):
    CARDIAC_MRI_STANDARD = "CardiacMRI_Standard"
    CARDIAC_MRI_STRESS = "CardiacMRI_Stress"
    CARDIAC_CATH = "CardiacCath"


@dataclass
class ConditionTemplate:
    """ICD-10 coded condition"""
    code: str
    title: str


@dataclass
class MedicationTemplate:
    """Medication with optional instructions"""
    name: str
    note: Optional[str] = None


@dataclass
class AllergyTemplate:
    """Allergy with reaction details"""
    name: str
    reaction: str = ""
    severity: str = "mild"  # mild, moderate, severe


@dataclass
class PatientProfile:
    """Complete patient profile template"""
    id: str
    scenario: str
    demo_question: str
    expected_personalization: str
    first_name: str
    last_name: str
    birth_year: int
    sex: str
    language: str = "English"
    health_literacy: HealthLiteracy = HealthLiteracy.STANDARD
    care_pathway: CarePathway = CarePathway.CARDIAC_MRI_STANDARD
    procedure_days_ahead: int = 7
    conditions: List[ConditionTemplate] = field(default_factory=list)
    medications: List[MedicationTemplate] = field(default_factory=list)
    allergies: List[AllergyTemplate] = field(default_factory=list)
    special_considerations: List[str] = field(default_factory=list)


# =============================================================================
# 20+ CARDIAC PATIENT PROFILES
# =============================================================================

CARDIAC_PATIENT_PROFILES = [
    # -------------------------------------------------------------------------
    # PROFILE 1: Diabetic cardiac patient (Metformin hold)
    # -------------------------------------------------------------------------
    PatientProfile(
        id="fhir_001",
        scenario="Diabetic - Modified Fasting",
        demo_question="What should I eat before my MRI?",
        expected_personalization="Modified fasting - can have clear juice to prevent hypoglycemia",
        first_name="Margaret",
        last_name="Chen",
        birth_year=1958,
        sex="female",
        language="English",
        health_literacy=HealthLiteracy.STANDARD,
        care_pathway=CarePathway.CARDIAC_MRI_STANDARD,
        procedure_days_ahead=5,
        conditions=[
            ConditionTemplate("E11.9", "Type 2 diabetes mellitus"),
            ConditionTemplate("I25.10", "Coronary artery disease"),
        ],
        medications=[
            MedicationTemplate("Metformin 500mg", "Hold morning of procedure"),
            MedicationTemplate("Metoprolol 25mg"),
            MedicationTemplate("Atorvastatin 40mg"),
        ],
        allergies=[],
        special_considerations=["diabetes_fasting_protocol"],
    ),

    # -------------------------------------------------------------------------
    # PROFILE 2: COPD + Theophylline (stress MRI contraindication)
    # -------------------------------------------------------------------------
    PatientProfile(
        id="fhir_002",
        scenario="Theophylline - Medication Hold Required",
        demo_question="Do I need to stop any medications?",
        expected_personalization="CRITICAL: Must stop Theophylline 24h before stress MRI",
        first_name="William",
        last_name="Rodriguez",
        birth_year=1952,
        sex="male",
        language="English",
        health_literacy=HealthLiteracy.STANDARD,
        care_pathway=CarePathway.CARDIAC_MRI_STRESS,
        procedure_days_ahead=7,
        conditions=[
            ConditionTemplate("I42.0", "Dilated cardiomyopathy"),
            ConditionTemplate("J44.9", "COPD"),
        ],
        medications=[
            MedicationTemplate("Theophylline 300mg", "HOLD 24h before - interferes with adenosine"),
            MedicationTemplate("Carvedilol 12.5mg"),
            MedicationTemplate("Furosemide 40mg"),
            MedicationTemplate("Albuterol inhaler"),
        ],
        allergies=[],
        special_considerations=["theophylline_hold", "copd_breathing_support"],
    ),

    # -------------------------------------------------------------------------
    # PROFILE 3: Claustrophobia (sedation needs)
    # -------------------------------------------------------------------------
    PatientProfile(
        id="fhir_003",
        scenario="Claustrophobia - Anxiety Management Needed",
        demo_question="I'm really scared of the MRI machine. What can I do?",
        expected_personalization="Offers sedation options, pre-visit tour, wide-bore scanner",
        first_name="Jennifer",
        last_name="Thompson",
        birth_year=1975,
        sex="female",
        language="English",
        health_literacy=HealthLiteracy.HIGH,
        care_pathway=CarePathway.CARDIAC_MRI_STANDARD,
        procedure_days_ahead=10,
        conditions=[
            ConditionTemplate("I42.1", "Hypertrophic cardiomyopathy"),
            ConditionTemplate("F40.240", "Claustrophobia"),
        ],
        medications=[
            MedicationTemplate("Metoprolol 50mg"),
            MedicationTemplate("Lisinopril 10mg"),
        ],
        allergies=[],
        special_considerations=["severe_claustrophobia", "may_need_sedation"],
    ),

    # -------------------------------------------------------------------------
    # PROFILE 4: Pacemaker patient (device interrogation)
    # -------------------------------------------------------------------------
    PatientProfile(
        id="fhir_004",
        scenario="Pacemaker - MRI Safety Verification",
        demo_question="Is the MRI safe with my pacemaker?",
        expected_personalization="Requires pacemaker interrogation before/after MRI",
        first_name="Robert",
        last_name="Williams",
        birth_year=1948,
        sex="male",
        language="English",
        health_literacy=HealthLiteracy.STANDARD,
        care_pathway=CarePathway.CARDIAC_MRI_STANDARD,
        procedure_days_ahead=14,
        conditions=[
            ConditionTemplate("I50.9", "Heart failure"),
            ConditionTemplate("I48.91", "Atrial fibrillation"),
            ConditionTemplate("Z95.0", "Presence of cardiac pacemaker"),
        ],
        medications=[
            MedicationTemplate("Digoxin 0.125mg"),
            MedicationTemplate("Warfarin 5mg"),
            MedicationTemplate("Furosemide 20mg"),
            MedicationTemplate("Lisinopril 20mg"),
        ],
        allergies=[],
        special_considerations=["pacemaker_mri_conditional", "requires_device_interrogation", "anticoagulated"],
    ),

    # -------------------------------------------------------------------------
    # PROFILE 5: Low health literacy (simplified language)
    # -------------------------------------------------------------------------
    PatientProfile(
        id="fhir_005",
        scenario="Low Health Literacy - Simplified Instructions",
        demo_question="What do I need to do?",
        expected_personalization="Uses simple words, short sentences, avoids medical jargon",
        first_name="Maria",
        last_name="Gonzalez",
        birth_year=1962,
        sex="female",
        language="English",
        health_literacy=HealthLiteracy.LOW,
        care_pathway=CarePathway.CARDIAC_MRI_STANDARD,
        procedure_days_ahead=4,
        conditions=[
            ConditionTemplate("I25.10", "Coronary artery disease"),
            ConditionTemplate("I10", "Essential hypertension"),
        ],
        medications=[
            MedicationTemplate("Aspirin 81mg"),
            MedicationTemplate("Lisinopril 10mg"),
            MedicationTemplate("Amlodipine 5mg"),
        ],
        allergies=[],
        special_considerations=["low_health_literacy", "prefers_simple_language"],
    ),

    # -------------------------------------------------------------------------
    # PROFILE 6: Spanish speaker (language preference)
    # -------------------------------------------------------------------------
    PatientProfile(
        id="fhir_006",
        scenario="Spanish Speaker - Language Preference",
        demo_question="Que debo hacer antes del examen?",
        expected_personalization="Responds in Spanish, culturally appropriate",
        first_name="Carlos",
        last_name="Martinez",
        birth_year=1955,
        sex="male",
        language="Spanish",
        health_literacy=HealthLiteracy.STANDARD,
        care_pathway=CarePathway.CARDIAC_MRI_STRESS,
        procedure_days_ahead=6,
        conditions=[
            ConditionTemplate("I25.5", "Ischemic cardiomyopathy"),
            ConditionTemplate("E11.9", "Type 2 diabetes mellitus"),
        ],
        medications=[
            MedicationTemplate("Metoprolol 50mg"),
            MedicationTemplate("Metformin 1000mg"),
            MedicationTemplate("Atorvastatin 40mg"),
            MedicationTemplate("Aspirin 81mg"),
        ],
        allergies=[],
        special_considerations=["spanish_preferred", "diabetes_fasting_protocol"],
    ),

    # -------------------------------------------------------------------------
    # PROFILE 7: Gadolinium allergy (no contrast)
    # -------------------------------------------------------------------------
    PatientProfile(
        id="fhir_007",
        scenario="Gadolinium Allergy - Modified Protocol",
        demo_question="Will I get the contrast dye?",
        expected_personalization="No gadolinium contrast due to allergy, alternative protocol",
        first_name="Susan",
        last_name="Anderson",
        birth_year=1968,
        sex="female",
        language="English",
        health_literacy=HealthLiteracy.HIGH,
        care_pathway=CarePathway.CARDIAC_MRI_STANDARD,
        procedure_days_ahead=8,
        conditions=[
            ConditionTemplate("I34.0", "Mitral valve insufficiency"),
        ],
        medications=[
            MedicationTemplate("Metoprolol 25mg"),
            MedicationTemplate("Aspirin 81mg"),
        ],
        allergies=[
            AllergyTemplate("Gadolinium", "Anaphylaxis", "severe"),
        ],
        special_considerations=["no_gadolinium_contrast", "non_contrast_protocol"],
    ),

    # -------------------------------------------------------------------------
    # PROFILE 8: CKD Stage 4 (nephrology clearance)
    # -------------------------------------------------------------------------
    PatientProfile(
        id="fhir_008",
        scenario="CKD Stage 4 - Contrast Risk Assessment",
        demo_question="Is the contrast dye safe for my kidneys?",
        expected_personalization="Requires nephrology clearance, may use reduced dose",
        first_name="James",
        last_name="Wilson",
        birth_year=1950,
        sex="male",
        language="English",
        health_literacy=HealthLiteracy.STANDARD,
        care_pathway=CarePathway.CARDIAC_MRI_STANDARD,
        procedure_days_ahead=12,
        conditions=[
            ConditionTemplate("I50.9", "Heart failure"),
            ConditionTemplate("N18.4", "Chronic kidney disease, stage 4"),
            ConditionTemplate("E11.9", "Type 2 diabetes mellitus"),
        ],
        medications=[
            MedicationTemplate("Carvedilol 25mg"),
            MedicationTemplate("Furosemide 80mg"),
            MedicationTemplate("Insulin glargine"),
            MedicationTemplate("Sodium bicarbonate"),
        ],
        allergies=[],
        special_considerations=["ckd_stage_4", "contrast_risk", "nephrology_clearance_required", "diabetes_fasting_protocol"],
    ),

    # -------------------------------------------------------------------------
    # PROFILE 9: First MRI patient (detailed explanation)
    # -------------------------------------------------------------------------
    PatientProfile(
        id="fhir_009",
        scenario="First MRI - Detailed Explanation Needed",
        demo_question="I've never had an MRI. What will happen?",
        expected_personalization="Detailed walkthrough of entire process",
        first_name="Emily",
        last_name="Davis",
        birth_year=1992,
        sex="female",
        language="English",
        health_literacy=HealthLiteracy.HIGH,
        care_pathway=CarePathway.CARDIAC_MRI_STANDARD,
        procedure_days_ahead=3,
        conditions=[
            ConditionTemplate("I42.1", "Hypertrophic cardiomyopathy"),
        ],
        medications=[
            MedicationTemplate("Metoprolol 25mg"),
        ],
        allergies=[],
        special_considerations=["first_mri", "needs_detailed_explanation", "anxiety_about_unknown"],
    ),

    # -------------------------------------------------------------------------
    # PROFILE 10: Warfarin for MRI (continue medication)
    # -------------------------------------------------------------------------
    PatientProfile(
        id="fhir_010",
        scenario="Anticoagulated - No Changes Needed for MRI",
        demo_question="Should I stop my blood thinner?",
        expected_personalization="Reassurance - blood thinners NOT stopped for MRI",
        first_name="Dorothy",
        last_name="Brown",
        birth_year=1945,
        sex="female",
        language="English",
        health_literacy=HealthLiteracy.STANDARD,
        care_pathway=CarePathway.CARDIAC_MRI_STANDARD,
        procedure_days_ahead=9,
        conditions=[
            ConditionTemplate("I48.91", "Atrial fibrillation"),
            ConditionTemplate("I35.0", "Aortic valve stenosis"),
            ConditionTemplate("Z95.2", "Presence of prosthetic heart valve"),
        ],
        medications=[
            MedicationTemplate("Warfarin 7.5mg", "Continue - no hold needed for MRI"),
            MedicationTemplate("Metoprolol 50mg"),
            MedicationTemplate("Digoxin 0.125mg"),
            MedicationTemplate("Furosemide 40mg"),
        ],
        allergies=[
            AllergyTemplate("Penicillin", "Rash", "mild"),
        ],
        special_considerations=["anticoagulated", "prosthetic_valve", "elderly_patient"],
    ),

    # -------------------------------------------------------------------------
    # PROFILE 11: Warfarin for Cath (stop medication)
    # -------------------------------------------------------------------------
    PatientProfile(
        id="fhir_011",
        scenario="Cardiac Cath - Blood Thinner MUST STOP",
        demo_question="Should I stop my blood thinner?",
        expected_personalization="CRITICAL: Must STOP Warfarin 5 days before cath",
        first_name="Richard",
        last_name="Thompson",
        birth_year=1951,
        sex="male",
        language="English",
        health_literacy=HealthLiteracy.STANDARD,
        care_pathway=CarePathway.CARDIAC_CATH,
        procedure_days_ahead=7,
        conditions=[
            ConditionTemplate("I25.10", "Coronary artery disease"),
            ConditionTemplate("I48.91", "Atrial fibrillation"),
            ConditionTemplate("I10", "Essential hypertension"),
        ],
        medications=[
            MedicationTemplate("Warfarin 5mg", "STOP 5 days before cardiac cath"),
            MedicationTemplate("Metoprolol 50mg"),
            MedicationTemplate("Atorvastatin 40mg"),
            MedicationTemplate("Lisinopril 10mg"),
        ],
        allergies=[],
        special_considerations=["anticoagulated", "blood_thinner_hold_required", "cardiac_cath"],
    ),

    # -------------------------------------------------------------------------
    # PROFILE 12: Heart failure + AFib
    # -------------------------------------------------------------------------
    PatientProfile(
        id="fhir_012",
        scenario="Heart Failure with AFib - Complex Management",
        demo_question="Will I be okay lying flat for the MRI?",
        expected_personalization="May need breaks, pillows, careful monitoring",
        first_name="Thomas",
        last_name="Jackson",
        birth_year=1946,
        sex="male",
        language="English",
        health_literacy=HealthLiteracy.STANDARD,
        care_pathway=CarePathway.CARDIAC_MRI_STANDARD,
        procedure_days_ahead=11,
        conditions=[
            ConditionTemplate("I50.23", "Acute on chronic systolic heart failure"),
            ConditionTemplate("I48.91", "Atrial fibrillation"),
            ConditionTemplate("I10", "Essential hypertension"),
        ],
        medications=[
            MedicationTemplate("Carvedilol 25mg"),
            MedicationTemplate("Spironolactone 25mg"),
            MedicationTemplate("Furosemide 60mg"),
            MedicationTemplate("Apixaban 5mg"),
            MedicationTemplate("Entresto 49/51mg"),
        ],
        allergies=[],
        special_considerations=["heart_failure", "may_not_tolerate_lying_flat", "fluid_restrictions"],
    ),

    # -------------------------------------------------------------------------
    # PROFILE 13: Post-MI patient
    # -------------------------------------------------------------------------
    PatientProfile(
        id="fhir_013",
        scenario="Recent MI - Viability Assessment",
        demo_question="Why do I need this MRI after my heart attack?",
        expected_personalization="Explains viability assessment purpose",
        first_name="Patricia",
        last_name="Harris",
        birth_year=1958,
        sex="female",
        language="English",
        health_literacy=HealthLiteracy.HIGH,
        care_pathway=CarePathway.CARDIAC_MRI_STANDARD,
        procedure_days_ahead=5,
        conditions=[
            ConditionTemplate("I21.09", "ST elevation myocardial infarction"),
            ConditionTemplate("I25.10", "Coronary artery disease"),
            ConditionTemplate("E11.9", "Type 2 diabetes mellitus"),
        ],
        medications=[
            MedicationTemplate("Aspirin 81mg"),
            MedicationTemplate("Clopidogrel 75mg"),
            MedicationTemplate("Atorvastatin 80mg"),
            MedicationTemplate("Metoprolol 100mg"),
            MedicationTemplate("Lisinopril 20mg"),
        ],
        allergies=[],
        special_considerations=["recent_mi", "dual_antiplatelet", "viability_assessment"],
    ),

    # -------------------------------------------------------------------------
    # PROFILE 14: Hypertrophic cardiomyopathy
    # -------------------------------------------------------------------------
    PatientProfile(
        id="fhir_014",
        scenario="HCM - Genetic Screening Context",
        demo_question="Will this MRI show why I have this condition?",
        expected_personalization="Explains HCM imaging, genetic testing discussion",
        first_name="David",
        last_name="Clark",
        birth_year=1985,
        sex="male",
        language="English",
        health_literacy=HealthLiteracy.HIGH,
        care_pathway=CarePathway.CARDIAC_MRI_STANDARD,
        procedure_days_ahead=6,
        conditions=[
            ConditionTemplate("I42.1", "Obstructive hypertrophic cardiomyopathy"),
        ],
        medications=[
            MedicationTemplate("Metoprolol 100mg"),
            MedicationTemplate("Verapamil 180mg"),
        ],
        allergies=[],
        special_considerations=["hcm", "family_screening_may_be_needed", "activity_restrictions"],
    ),

    # -------------------------------------------------------------------------
    # PROFILE 15: Dilated cardiomyopathy
    # -------------------------------------------------------------------------
    PatientProfile(
        id="fhir_015",
        scenario="DCM - ICD Evaluation",
        demo_question="Does this MRI check if I need a defibrillator?",
        expected_personalization="Explains EF assessment, ICD criteria",
        first_name="Lisa",
        last_name="Lewis",
        birth_year=1970,
        sex="female",
        language="English",
        health_literacy=HealthLiteracy.STANDARD,
        care_pathway=CarePathway.CARDIAC_MRI_STANDARD,
        procedure_days_ahead=8,
        conditions=[
            ConditionTemplate("I42.0", "Dilated cardiomyopathy"),
            ConditionTemplate("I50.22", "Chronic systolic heart failure"),
        ],
        medications=[
            MedicationTemplate("Carvedilol 25mg"),
            MedicationTemplate("Lisinopril 40mg"),
            MedicationTemplate("Spironolactone 25mg"),
            MedicationTemplate("Furosemide 40mg"),
        ],
        allergies=[],
        special_considerations=["dcm", "icd_evaluation", "heart_failure"],
    ),

    # -------------------------------------------------------------------------
    # PROFILE 16: Aortic stenosis
    # -------------------------------------------------------------------------
    PatientProfile(
        id="fhir_016",
        scenario="Aortic Stenosis - Pre-TAVR Evaluation",
        demo_question="Is this for planning my valve replacement?",
        expected_personalization="Explains pre-TAVR assessment role",
        first_name="George",
        last_name="Walker",
        birth_year=1941,
        sex="male",
        language="English",
        health_literacy=HealthLiteracy.STANDARD,
        care_pathway=CarePathway.CARDIAC_MRI_STANDARD,
        procedure_days_ahead=14,
        conditions=[
            ConditionTemplate("I35.0", "Aortic valve stenosis"),
            ConditionTemplate("I10", "Essential hypertension"),
            ConditionTemplate("E78.5", "Hyperlipidemia"),
        ],
        medications=[
            MedicationTemplate("Atorvastatin 40mg"),
            MedicationTemplate("Amlodipine 10mg"),
            MedicationTemplate("Aspirin 81mg"),
        ],
        allergies=[],
        special_considerations=["severe_aortic_stenosis", "tavr_evaluation", "elderly_patient"],
    ),

    # -------------------------------------------------------------------------
    # PROFILE 17: Elderly patient (>80)
    # -------------------------------------------------------------------------
    PatientProfile(
        id="fhir_017",
        scenario="Elderly (85) - Special Considerations",
        demo_question="I'm worried about being in there so long.",
        expected_personalization="Extra time allowed, comfort measures, hearing considerations",
        first_name="Eleanor",
        last_name="Hall",
        birth_year=1940,
        sex="female",
        language="English",
        health_literacy=HealthLiteracy.STANDARD,
        care_pathway=CarePathway.CARDIAC_MRI_STANDARD,
        procedure_days_ahead=10,
        conditions=[
            ConditionTemplate("I50.9", "Heart failure"),
            ConditionTemplate("I10", "Essential hypertension"),
            ConditionTemplate("M79.3", "Panniculitis"),
        ],
        medications=[
            MedicationTemplate("Furosemide 20mg"),
            MedicationTemplate("Lisinopril 5mg"),
            MedicationTemplate("Metoprolol 12.5mg"),
        ],
        allergies=[
            AllergyTemplate("Sulfa drugs", "Hives", "moderate"),
        ],
        special_considerations=["elderly_patient", "hearing_impaired", "mobility_limitations", "extra_time_needed"],
    ),

    # -------------------------------------------------------------------------
    # PROFILE 18: Young adult cardiac
    # -------------------------------------------------------------------------
    PatientProfile(
        id="fhir_018",
        scenario="Young Adult - Athlete Heart Evaluation",
        demo_question="Can I still play sports after this?",
        expected_personalization="Addresses athletic activity concerns, screening context",
        first_name="Michael",
        last_name="Young",
        birth_year=2000,
        sex="male",
        language="English",
        health_literacy=HealthLiteracy.HIGH,
        care_pathway=CarePathway.CARDIAC_MRI_STANDARD,
        procedure_days_ahead=4,
        conditions=[
            ConditionTemplate("R00.1", "Bradycardia"),
            ConditionTemplate("I47.1", "Supraventricular tachycardia"),
        ],
        medications=[],
        allergies=[],
        special_considerations=["young_athlete", "sports_clearance_needed", "minimal_anxiety"],
    ),

    # -------------------------------------------------------------------------
    # PROFILE 19: Obesity + sleep apnea
    # -------------------------------------------------------------------------
    PatientProfile(
        id="fhir_019",
        scenario="Obesity with Sleep Apnea - Positioning Challenges",
        demo_question="Will I fit in the MRI machine?",
        expected_personalization="Reassurance about wide-bore scanner, positioning support",
        first_name="Kevin",
        last_name="Turner",
        birth_year=1972,
        sex="male",
        language="English",
        health_literacy=HealthLiteracy.STANDARD,
        care_pathway=CarePathway.CARDIAC_MRI_STANDARD,
        procedure_days_ahead=7,
        conditions=[
            ConditionTemplate("E66.01", "Morbid obesity due to excess calories"),
            ConditionTemplate("G47.33", "Obstructive sleep apnea"),
            ConditionTemplate("I10", "Essential hypertension"),
            ConditionTemplate("E11.9", "Type 2 diabetes mellitus"),
        ],
        medications=[
            MedicationTemplate("Metformin 1000mg"),
            MedicationTemplate("Lisinopril 20mg"),
            MedicationTemplate("Amlodipine 10mg"),
            MedicationTemplate("CPAP at night"),
        ],
        allergies=[],
        special_considerations=["obesity", "wide_bore_scanner", "positioning_support", "diabetes_fasting_protocol"],
    ),

    # -------------------------------------------------------------------------
    # PROFILE 20: Multiple comorbidities
    # -------------------------------------------------------------------------
    PatientProfile(
        id="fhir_020",
        scenario="Multiple Comorbidities - Complex Patient",
        demo_question="I have so many conditions. Is this safe?",
        expected_personalization="Addresses multiple concerns, coordinated care approach",
        first_name="Barbara",
        last_name="Adams",
        birth_year=1950,
        sex="female",
        language="English",
        health_literacy=HealthLiteracy.LOW,
        care_pathway=CarePathway.CARDIAC_MRI_STANDARD,
        procedure_days_ahead=12,
        conditions=[
            ConditionTemplate("I50.9", "Heart failure"),
            ConditionTemplate("E11.65", "Type 2 diabetes with hyperglycemia"),
            ConditionTemplate("N18.3", "Chronic kidney disease, stage 3"),
            ConditionTemplate("I10", "Essential hypertension"),
            ConditionTemplate("E78.5", "Hyperlipidemia"),
            ConditionTemplate("J44.9", "COPD"),
        ],
        medications=[
            MedicationTemplate("Carvedilol 12.5mg"),
            MedicationTemplate("Lisinopril 10mg"),
            MedicationTemplate("Furosemide 40mg"),
            MedicationTemplate("Metformin 500mg", "Hold day of procedure"),
            MedicationTemplate("Atorvastatin 40mg"),
            MedicationTemplate("Albuterol inhaler"),
        ],
        allergies=[
            AllergyTemplate("Iodine contrast", "Rash", "moderate"),
        ],
        special_considerations=[
            "multiple_comorbidities",
            "ckd_contrast_consideration",
            "diabetes_fasting_protocol",
            "copd_breathing_support",
            "low_health_literacy"
        ],
    ),

    # -------------------------------------------------------------------------
    # PROFILE 21: Mandarin speaker
    # -------------------------------------------------------------------------
    PatientProfile(
        id="fhir_021",
        scenario="Mandarin Speaker - Language Preference",
        demo_question="Wo yao zhunbei shenme?",
        expected_personalization="Responds in Mandarin Chinese",
        first_name="Wei",
        last_name="Zhang",
        birth_year=1960,
        sex="male",
        language="Mandarin",
        health_literacy=HealthLiteracy.STANDARD,
        care_pathway=CarePathway.CARDIAC_MRI_STANDARD,
        procedure_days_ahead=6,
        conditions=[
            ConditionTemplate("I25.10", "Coronary artery disease"),
            ConditionTemplate("I10", "Essential hypertension"),
        ],
        medications=[
            MedicationTemplate("Aspirin 81mg"),
            MedicationTemplate("Metoprolol 50mg"),
            MedicationTemplate("Atorvastatin 20mg"),
        ],
        allergies=[],
        special_considerations=["mandarin_preferred", "interpreter_may_be_needed"],
    ),

    # -------------------------------------------------------------------------
    # PROFILE 22: Metal implant concern
    # -------------------------------------------------------------------------
    PatientProfile(
        id="fhir_022",
        scenario="Orthopedic Hardware - MRI Compatibility Check",
        demo_question="I have a metal plate in my leg. Is MRI safe?",
        expected_personalization="Explains modern implants usually MRI-safe, verification needed",
        first_name="Andrew",
        last_name="Mitchell",
        birth_year=1965,
        sex="male",
        language="English",
        health_literacy=HealthLiteracy.HIGH,
        care_pathway=CarePathway.CARDIAC_MRI_STANDARD,
        procedure_days_ahead=5,
        conditions=[
            ConditionTemplate("I42.0", "Dilated cardiomyopathy"),
            ConditionTemplate("Z96.641", "Presence of right artificial hip joint"),
        ],
        medications=[
            MedicationTemplate("Carvedilol 25mg"),
            MedicationTemplate("Lisinopril 20mg"),
        ],
        allergies=[],
        special_considerations=["orthopedic_hardware", "implant_compatibility_check"],
    ),

    # -------------------------------------------------------------------------
    # PROFILE 23: Pregnancy concern
    # -------------------------------------------------------------------------
    PatientProfile(
        id="fhir_023",
        scenario="Childbearing Age - Pregnancy Screening",
        demo_question="Could I be pregnant and have this MRI?",
        expected_personalization="Pregnancy test required, no gadolinium if pregnant",
        first_name="Amanda",
        last_name="Roberts",
        birth_year=1990,
        sex="female",
        language="English",
        health_literacy=HealthLiteracy.HIGH,
        care_pathway=CarePathway.CARDIAC_MRI_STANDARD,
        procedure_days_ahead=4,
        conditions=[
            ConditionTemplate("I34.0", "Mitral valve prolapse"),
            ConditionTemplate("R00.0", "Tachycardia"),
        ],
        medications=[
            MedicationTemplate("Metoprolol 25mg"),
        ],
        allergies=[],
        special_considerations=["childbearing_age", "pregnancy_test_required", "no_gadolinium_if_pregnant"],
    ),

    # -------------------------------------------------------------------------
    # PROFILE 24: Tattoo concerns
    # -------------------------------------------------------------------------
    PatientProfile(
        id="fhir_024",
        scenario="Recent Tattoos - MRI Safety Question",
        demo_question="I have new tattoos. Can I still get an MRI?",
        expected_personalization="Modern tattoo inks usually safe, may feel warmth",
        first_name="Jason",
        last_name="Phillips",
        birth_year=1988,
        sex="male",
        language="English",
        health_literacy=HealthLiteracy.STANDARD,
        care_pathway=CarePathway.CARDIAC_MRI_STANDARD,
        procedure_days_ahead=3,
        conditions=[
            ConditionTemplate("I47.1", "Supraventricular tachycardia"),
        ],
        medications=[
            MedicationTemplate("Metoprolol 50mg"),
        ],
        allergies=[],
        special_considerations=["recent_tattoos", "may_feel_warmth"],
    ),
]


def get_profile_by_id(profile_id: str) -> PatientProfile:
    """Get a patient profile by ID"""
    for profile in CARDIAC_PATIENT_PROFILES:
        if profile.id == profile_id:
            return profile
    raise ValueError(f"Profile not found: {profile_id}")


def get_profiles_by_pathway(pathway: CarePathway) -> list[PatientProfile]:
    """Get all profiles for a specific care pathway"""
    return [p for p in CARDIAC_PATIENT_PROFILES if p.care_pathway == pathway]
