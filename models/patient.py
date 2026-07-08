from dataclasses import dataclass, field
from typing import Optional


@dataclass
class WorklistItem:
    patient_id: str = ""
    patient_name: str = ""
    patient_birth_date: str = ""
    patient_sex: str = ""
    study_instance_uid: str = ""
    accession_number: str = ""
    study_date: str = ""
    study_time: str = ""
    study_description: str = ""
    modality: str = ""
    station_name: str = ""
    requested_procedure_description: str = ""
    scheduled_procedure_step_start_date: str = ""
    scheduled_procedure_step_start_time: str = ""
    scheduled_station_ae_title: str = ""
    raw: dict = field(default_factory=dict)
