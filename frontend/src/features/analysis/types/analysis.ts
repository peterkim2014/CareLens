export type PatientSex =
  | "female"
  | "male"
  | "intersex"
  | "other"
  | "unknown";

export interface PatientDetails {
  age: number | null;
  sex: PatientSex;
}

export interface HistoryOfPresentIllness {
  duration: string;
  symptoms: string[];
  severity: string;
}

export interface SocialHistory {
  smoking_status: string;
  pack_years: number | null;
}

export interface Medication {
  id: string;
  name: string;
  dose: string;
  frequency: string;
}

export interface VitalSigns {
  temperature_celsius: number | null;
  heart_rate_bpm: number | null;
  blood_pressure_mmHg: string;
  respiratory_rate_bpm: number | null;
  oxygen_saturation_percent: number | null;
  oxygen_support: string;
}

export interface PhysicalExam {
  general: string;
  respiratory: string[];
  cardiovascular: string[];
  neurologic: string[];
  abdominal: string[];
  other: string[];
}

export interface LaboratoryResult {
  id: string;
  test_name: string;
  value: string;
  unit: string;
  reference_range: string;
}

export interface ImagingStudy {
  id: string;
  type: string;
  findings: string[];
}

export interface ClinicalCase {
  patient: PatientDetails;
  chief_complaint: string;
  history_of_present_illness: HistoryOfPresentIllness;
  medical_history: string[];
  social_history: SocialHistory;
  medications: Medication[];
  allergies: string[];
  vital_signs: VitalSigns;
  physical_exam: PhysicalExam;
  laboratory_results: LaboratoryResult[];
  imaging: ImagingStudy[];
  clinical_question: string[];
}

export interface DiagnosisAssessment {
  name: string;
  confidence: number | null;
  reasoning: string[];
}

export interface DifferentialDiagnosis {
  name: string;
  reasoning: string;
  urgency?: string;
}

export interface RecommendedTest {
  name: string;
  rationale: string;
  priority?: string;
}

export interface ManagementRecommendation {
  recommendation: string;
  rationale?: string;
}

export interface StructuredAnalysisResult {
  most_likely_diagnosis: DiagnosisAssessment;
  differential_diagnoses: DifferentialDiagnosis[];
  supporting_evidence: string[];
  recommended_tests: RecommendedTest[];
  initial_management: ManagementRecommendation[];
  red_flags: string[];
  limitations: string[];
  trace_id?: string;
}

export type ClinicalCaseFormState =
  | {
      status: "idle";
      result: null;
      message: null;
      traceId: null;
    }
  | {
      status: "validation_error";
      result: null;
      message: string;
      traceId: null;
    }
  | {
      status: "error";
      result: null;
      message: string;
      traceId: string | null;
    }
  | {
      status: "success";
      result: StructuredAnalysisResult;
      message: null;
      traceId: string | null;
    };

export const initialClinicalCaseFormState: ClinicalCaseFormState = {
  status: "idle",
  result: null,
  message: null,
  traceId: null,
};

export function createEmptyClinicalCase(): ClinicalCase {
  return {
    patient: {
      age: null,
      sex: "unknown",
    },
    chief_complaint: "",
    history_of_present_illness: {
      duration: "",
      symptoms: [],
      severity: "",
    },
    medical_history: [],
    social_history: {
      smoking_status: "",
      pack_years: null,
    },
    medications: [],
    allergies: [],
    vital_signs: {
      temperature_celsius: null,
      heart_rate_bpm: null,
      blood_pressure_mmHg: "",
      respiratory_rate_bpm: null,
      oxygen_saturation_percent: null,
      oxygen_support: "",
    },
    physical_exam: {
      general: "",
      respiratory: [],
      cardiovascular: [],
      neurologic: [],
      abdominal: [],
      other: [],
    },
    laboratory_results: [],
    imaging: [],
    clinical_question: [
      "What is the most likely diagnosis?",
      "What alternative diagnoses should be considered?",
      "What additional tests are appropriate?",
      "What initial treatment plan is recommended?",
    ],
  };
}

export function createExampleClinicalCase(): ClinicalCase {
  return {
    patient: {
      age: 58,
      sex: "male",
    },
    chief_complaint:
      "Worsening shortness of breath and productive cough",
    history_of_present_illness: {
      duration: "3 days",
      symptoms: [
        "Shortness of breath",
        "Productive cough with yellow sputum",
        "Fever",
        "Right-sided pleuritic chest pain",
      ],
      severity: "Worsening",
    },
    medical_history: [
      "Hypertension",
      "Type 2 diabetes mellitus",
    ],
    social_history: {
      smoking_status: "Former smoker",
      pack_years: 20,
    },
    medications: [
      {
        id: "synthetic-medication-metformin",
        name: "Metformin",
        dose: "1000 mg",
        frequency: "Twice daily",
      },
      {
        id: "synthetic-medication-lisinopril",
        name: "Lisinopril",
        dose: "20 mg",
        frequency: "Once daily",
      },
    ],
    allergies: [],
    vital_signs: {
      temperature_celsius: 38.6,
      heart_rate_bpm: 108,
      blood_pressure_mmHg: "132/78",
      respiratory_rate_bpm: 24,
      oxygen_saturation_percent: 91,
      oxygen_support: "Room air",
    },
    physical_exam: {
      general:
        "Fatigued and mildly distressed",
      respiratory: [
        "Decreased breath sounds at the right lung base",
        "Crackles in the right lower lung field",
      ],
      cardiovascular: [
        "No lower-extremity edema",
      ],
      neurologic: [],
      abdominal: [],
      other: [],
    },
    laboratory_results: [
      {
        id: "synthetic-lab-wbc",
        test_name: "White blood cell count",
        value: "15.2",
        unit: "× 10⁹/L",
        reference_range: "",
      },
      {
        id: "synthetic-lab-neutrophils",
        test_name: "Neutrophils",
        value: "84",
        unit: "%",
        reference_range: "",
      },
      {
        id: "synthetic-lab-hemoglobin",
        test_name: "Hemoglobin",
        value: "13.8",
        unit: "g/dL",
        reference_range: "",
      },
      {
        id: "synthetic-lab-platelets",
        test_name: "Platelets",
        value: "245",
        unit: "× 10⁹/L",
        reference_range: "",
      },
      {
        id: "synthetic-lab-creatinine",
        test_name: "Creatinine",
        value: "1.1",
        unit: "mg/dL",
        reference_range: "",
      },
      {
        id: "synthetic-lab-glucose",
        test_name: "Glucose",
        value: "186",
        unit: "mg/dL",
        reference_range: "",
      },
      {
        id: "synthetic-lab-lactate",
        test_name: "Lactate",
        value: "1.7",
        unit: "mmol/L",
        reference_range: "",
      },
    ],
    imaging: [
      {
        id: "synthetic-imaging-chest-xray",
        type: "Chest X-ray",
        findings: [
          "Right lower-lobe airspace opacity consistent with consolidation",
          "No pleural effusion",
          "No pneumothorax",
        ],
      },
    ],
    clinical_question: [
      "What is the most likely diagnosis?",
      "What alternative diagnoses should be considered?",
      "What additional tests are appropriate?",
      "What initial treatment plan is recommended?",
    ],
  };
}