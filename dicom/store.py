from pydicom.dataset import Dataset


def store(assoc, ds: Dataset):
    status = assoc.send_c_store(ds)
    if status:
        return status.Status, status.get("ErrorComment", "")
    return None, "Association not established"
