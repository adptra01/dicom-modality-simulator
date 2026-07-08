from pydicom.dataset import Dataset
from pynetdicom.sop_class import StudyRootQueryRetrieveInformationModelFind

from models.patient import WorklistItem


def build_query(patient_id=None, patient_name=None):
    ds = Dataset()
    ds.QueryRetrieveLevel = "STUDY"
    ds.PatientID = patient_id or ""
    ds.PatientName = patient_name or ""
    ds.StudyDate = ""
    ds.StudyDescription = ""
    ds.AccessionNumber = ""
    ds.StudyInstanceUID = ""
    ds.Modality = ""
    return ds


def parse_response(ds) -> WorklistItem:
    def _val(attr):
        v = getattr(ds, attr, None)
        if v is None:
            return ""
        if isinstance(v, bytes):
            return v.decode("utf-8", "replace")
        return str(v)

    return WorklistItem(
        patient_id=_val("PatientID"),
        patient_name=_val("PatientName"),
        study_instance_uid=_val("StudyInstanceUID"),
        accession_number=_val("AccessionNumber"),
        study_date=_val("StudyDate"),
        study_description=_val("StudyDescription"),
        modality=_val("Modality"),
        raw=dict(ds.items()),
    )


def query_worklist(assoc, query_ds):
    results = []
    responses = assoc.send_c_find(query_ds, query_model=StudyRootQueryRetrieveInformationModelFind)
    for status, ds in responses:
        if ds:
            results.append(parse_response(ds))
    return results
