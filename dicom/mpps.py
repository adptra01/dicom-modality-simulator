from datetime import datetime
from pydicom.dataset import Dataset
from pydicom.uid import generate_uid
from pynetdicom.sop_class import ModalityPerformedProcedureStep

from dicom.association import status_code as _status_code


def mpps_start(assoc, patient_name, patient_id, study_uid, step_id=None, desc=None):
    mpps_uid = generate_uid()
    req = Dataset()
    req.PerformedProcedureStepID = step_id or "001"
    req.PerformedStationAETitle = assoc.ae.ae_title
    req.PerformedProcedureStepStartDateTime = datetime.now()
    req.PerformedProcedureStepStatus = "IN PROGRESS"
    req.PatientName = patient_name
    req.PatientID = patient_id

    if study_uid:
        ref = Dataset()
        ref.StudyInstanceUID = study_uid
        req.ScheduledStepAttributesSequence = [ref]
    if desc:
        req.PerformedProcedureStepDescription = desc

    status, rsp = assoc.send_n_create(
        req, ModalityPerformedProcedureStep, mpps_uid
    )
    return _status_code(status), rsp, mpps_uid


def mpps_complete(assoc, mpps_instance_uid):
    req = Dataset()
    req.PerformedProcedureStepStatus = "COMPLETED"
    req.PerformedProcedureStepEndDateTime = datetime.now()
    status, rsp = assoc.send_n_set(
        req, ModalityPerformedProcedureStep, mpps_instance_uid
    )
    return _status_code(status), rsp


def mpps_discontinued(assoc, mpps_instance_uid):
    req = Dataset()
    req.PerformedProcedureStepStatus = "DISCONTINUED"
    req.PerformedProcedureStepEndDateTime = datetime.now()
    status, rsp = assoc.send_n_set(
        req, ModalityPerformedProcedureStep, mpps_instance_uid
    )
    return _status_code(status), rsp
