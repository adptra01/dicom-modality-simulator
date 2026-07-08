from io import BytesIO
from PIL import Image
from pydicom.dataset import FileMetaDataset, FileDataset
from pydicom.uid import generate_uid, ExplicitVRLittleEndian

SC_UID = "1.2.840.10008.5.1.4.1.1.7"


def jpg_to_dicom(image_path: str, patient_name="", patient_id="",
                 study_desc="", accession="", modality="XC") -> Dataset:
    pil_img = Image.open(image_path)
    if pil_img.mode == "RGBA":
        pil_img = pil_img.convert("RGB")
    width, height = pil_img.size

    sop_uid = generate_uid()
    study_uid = generate_uid()
    series_uid = generate_uid()

    file_meta = FileMetaDataset()
    file_meta.MediaStorageSOPClassUID = SC_UID
    file_meta.MediaStorageSOPInstanceUID = sop_uid
    file_meta.TransferSyntaxUID = ExplicitVRLittleEndian

    ds = FileDataset(None, {}, file_meta=file_meta, preamble=b"\x00" * 128)
    ds.SOPClassUID = SC_UID
    ds.SOPInstanceUID = sop_uid
    ds.StudyInstanceUID = study_uid
    ds.SeriesInstanceUID = series_uid
    ds.PatientName = patient_name or "UNKNOWN"
    ds.PatientID = patient_id or "UNKNOWN"
    if accession:
        ds.AccessionNumber = accession
    ds.StudyDescription = study_desc or ""
    ds.Modality = modality
    ds.StudyDate = ""
    ds.StudyTime = ""
    ds.SeriesNumber = 1
    ds.InstanceNumber = 1
    ds.Rows = height
    ds.Columns = width
    ds.SamplesPerPixel = 3
    ds.PhotometricInterpretation = "RGB"
    ds.PlanarConfiguration = 0
    ds.BitsAllocated = 8
    ds.BitsStored = 8
    ds.HighBit = 7
    ds.PixelRepresentation = 0

    buf = BytesIO()
    pil_img.save(buf, format="JPEG")
    ds.PixelData = buf.getvalue()

    ds.file_meta = file_meta
    ds.is_little_endian = True
    ds.is_implicit_vr = False
    return ds
