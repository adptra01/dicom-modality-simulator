from pynetdicom import AE
from pynetdicom.sop_class import (
    Verification,
    StudyRootQueryRetrieveInformationModelFind,
    StudyRootQueryRetrieveInformationModelMove,
    ModalityPerformedProcedureStep,
    StorageCommitmentPushModel,
)

STORE_CONTEXTS = [
    "1.2.840.10008.5.1.4.1.1.1",    # CR Image Storage
    "1.2.840.10008.5.1.4.1.1.1.1",  # CR Image Storage (old)
    "1.2.840.10008.5.1.4.1.1.2",    # CT Image Storage
    "1.2.840.10008.5.1.4.1.1.3",    # US Image Storage
    "1.2.840.10008.5.1.4.1.1.4",    # MR Image Storage
    "1.2.840.10008.5.1.4.1.1.6.1",  # XA Image Storage
    "1.2.840.10008.5.1.4.1.1.6.2",  # XRF Image Storage
    "1.2.840.10008.5.1.4.1.1.7",    # Secondary Capture Image Storage
    "1.2.840.10008.5.1.4.1.1.9.1.1",# DX Image Storage
    "1.2.840.10008.5.1.4.1.1.9.1.3",# MG Image Storage
    "1.2.840.10008.5.1.4.1.1.12.1", # NM Image Storage
    "1.2.840.10008.5.1.4.1.1.20",   # NM Image Storage (old)
    "1.2.840.10008.5.1.4.1.1.77.1", # VL Image Storage
    "1.2.840.10008.5.1.4.1.1.104.1",# Ophthalmic Photography
    "1.2.840.10008.5.1.4.1.1.128",  # PET Image Storage
    "1.2.840.10008.5.1.4.1.1.481.1",# RT Image Storage
]

PRESENTATION_CONTEXTS = [
    "1.2.840.10008.5.1.4.1.1.88.11",  # Basic Text SR
    "1.2.840.10008.5.1.4.1.1.88.22",  # Enhanced SR
    "1.2.840.10008.5.1.4.1.1.88.33",  # Comprehensive SR
    "1.2.840.10008.5.1.4.1.1.88.34",  # Comprehensive 3D SR
    "1.2.840.10008.5.1.4.1.1.88.35",  # Extensible SR
]


def create_ae(ae_title: str):
    ae = AE(ae_title=ae_title.encode("utf-8"))
    ae.add_requested_context(Verification)
    ae.add_requested_context(StudyRootQueryRetrieveInformationModelFind)
    ae.add_requested_context(StudyRootQueryRetrieveInformationModelMove)
    ae.add_requested_context(ModalityPerformedProcedureStep)
    ae.add_requested_context(StorageCommitmentPushModel)
    for ctx in STORE_CONTEXTS + PRESENTATION_CONTEXTS:
        ae.add_requested_context(ctx)
    return ae


def associate(ae, host, port, called_ae):
    return ae.associate(host, int(port), ae_title=called_ae.encode("utf-8"))
