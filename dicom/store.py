from dicom.association import check_status


def store(assoc, ds):
    return check_status(assoc.send_c_store(ds))