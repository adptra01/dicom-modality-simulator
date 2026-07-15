from pydicom.dataset import Dataset
from pynetdicom.sop_class import StudyRootQueryRetrieveInformationModelMove

from dicom.association import status_code as _status_code


def cmove_study(assoc, study_uid, dest_ae):
    ds = Dataset()
    ds.QueryRetrieveLevel = "STUDY"
    ds.StudyInstanceUID = study_uid
    last_status = 0xFFFF
    last_rsp = None
    for status, rsp in assoc.send_c_move(
        ds, dest_ae, StudyRootQueryRetrieveInformationModelMove
    ):
        last_status = _status_code(status)
        last_rsp = rsp
    return last_status, last_rsp
