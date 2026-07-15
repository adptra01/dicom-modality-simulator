from pydicom.dataset import Dataset
from pynetdicom.sop_class import ModalityWorklistInformationFind

from models.patient import WorklistItem


def build_query(patient_id=None, patient_name=None, station_ae=None, modality=None, date=None):
    ds = Dataset()
    sps = Dataset()
    sps.ScheduledStationAETitle = station_ae or ""
    sps.Modality = modality or ""
    sps.ScheduledProcedureStepStartDate = date or ""
    sps.ScheduledProcedureStepStartTime = ""
    sps.ScheduledProcedureStepDescription = ""
    ds.ScheduledProcedureStepSequence = [sps]
    ds.PatientName = patient_name or ""
    ds.PatientID = patient_id or ""
    ds.PatientBirthDate = ""
    ds.PatientSex = ""
    ds.AccessionNumber = ""
    ds.RequestedProcedureDescription = ""
    ds.StudyInstanceUID = ""
    return ds


def parse_response(ds) -> WorklistItem | None:
    if not ds:
        return None

    def val(attr, seq=None):
        try:
            src = seq[0] if seq else ds
            v = getattr(src, attr, None)
            if v is None:
                return ""
            if isinstance(v, bytes):
                return v.decode("utf-8", "replace")
            return str(v)
        except (AttributeError, IndexError, TypeError):
            return ""

    sps = getattr(ds, "ScheduledProcedureStepSequence", None)
    return WorklistItem(
        patient_id=val("PatientID"),
        patient_name=val("PatientName"),
        patient_birth_date=val("PatientBirthDate"),
        patient_sex=val("PatientSex"),
        study_instance_uid=val("StudyInstanceUID"),
        accession_number=val("AccessionNumber"),
        study_date=val("ScheduledProcedureStepStartDate", sps),
        study_time=val("ScheduledProcedureStepStartTime", sps),
        study_description=val("ScheduledProcedureStepDescription", sps),
        modality=val("Modality", sps),
        station_name=val("ScheduledStationAETitle", sps),
        requested_procedure_description=val("RequestedProcedureDescription"),
        scheduled_procedure_step_start_date=val("ScheduledProcedureStepStartDate", sps),
        scheduled_procedure_step_start_time=val("ScheduledProcedureStepStartTime", sps),
        scheduled_station_ae_title=val("ScheduledStationAETitle", sps),
    )


def query_worklist(assoc, query_ds):
    results = []
    responses = assoc.send_c_find(query_ds, query_model=ModalityWorklistInformationFind)
    for status, ds in responses:
        item = parse_response(ds)
        if item:
            results.append(item)
    return results
