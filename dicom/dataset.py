from pydicom.dataset import Dataset


def dump_info(ds: Dataset) -> str:
    fields = [
        ("PatientName", ds.get("PatientName", "")),
        ("PatientID", ds.get("PatientID", "")),
        ("PatientBirthDate", ds.get("PatientBirthDate", "")),
        ("PatientSex", ds.get("PatientSex", "")),
        ("StudyInstanceUID", ds.get("StudyInstanceUID", "")),
        ("SeriesInstanceUID", ds.get("SeriesInstanceUID", "")),
        ("SOPInstanceUID", ds.get("SOPInstanceUID", "")),
        ("StudyDate", ds.get("StudyDate", "")),
        ("StudyTime", ds.get("StudyTime", "")),
        ("StudyDescription", ds.get("StudyDescription", "")),
        ("Modality", ds.get("Modality", "")),
        ("AccessionNumber", ds.get("AccessionNumber", "")),
        ("StationName", ds.get("StationName", "")),
        ("Manufacturer", ds.get("Manufacturer", "")),
    ]
    lines = ["── DICOM Dataset ──"]
    for name, val in fields:
        lines.append(f"  {name}: {val}")
    if "TransferSyntaxUID" in ds.file_meta:
        lines.append(f"  TransferSyntaxUID: {ds.file_meta.TransferSyntaxUID}")
    return "\n".join(lines)


def set_patient_info(ds: Dataset, patient_name="", patient_id="",
                     accession="", study_desc="", modality=""):
    if patient_name:
        ds.PatientName = patient_name
    if patient_id:
        ds.PatientID = patient_id
    if accession:
        ds.AccessionNumber = accession
    if study_desc:
        ds.StudyDescription = study_desc
    if modality:
        ds.Modality = modality
    return ds
