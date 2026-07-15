from dicom.association import check_status


def echo(assoc):
    return check_status(assoc.send_c_echo())