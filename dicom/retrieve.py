from pydicom.dataset import Dataset, FileDataset
from pynetdicom.sop_class import StudyRootQueryRetrieveInformationModelMove


def _status_code(s):
    if isinstance(s, Dataset) and (0x00000900) in s:
        return int(s[0x00000900].value)
    return int(s) if not isinstance(s, Dataset) else 0xFFFF


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
