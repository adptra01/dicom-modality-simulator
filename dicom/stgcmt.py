from pydicom.dataset import Dataset
from pydicom.uid import generate_uid
from pynetdicom.sop_class import StorageCommitmentPushModel

SC_SOP_CLASS = "1.2.840.10008.1.20.1"


def stgcmt_request(assoc, scp_ae_title, scp_port, sop_instances):
    tx_uid = generate_uid()
    ds = Dataset()
    ds.TransactionUID = tx_uid
    ds.Timeout = 30
    refs = []
    for sop_class_uid, sop_instance_uid in sop_instances:
        item = Dataset()
        item.ReferencedSOPClassUID = sop_class_uid
        item.ReferencedSOPInstanceUID = sop_instance_uid
        refs.append(item)
    ds.ReferencedSOPSequence = refs
    status, rsp = assoc.send_n_action(
        ds, 1, StorageCommitmentPushModel, SC_SOP_CLASS
    )
    return status, rsp, tx_uid


def stgcmt_make_handler(on_result=None, on_fail=None):
    def handler(event):
        ds = event.request
        event_type = event.event_type
        if on_result and event_type == 1:
            seq = ds.get("ReferencedSOPSequence")
            count = len(seq) if seq else 0
            on_result(count)
        if on_fail and event_type == 2:
            seq = ds.get("FailedSOPSequence")
            count = len(seq) if seq else 0
            on_fail(count)
        return 0x0000
    return handler
