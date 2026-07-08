from pathlib import Path
from pydicom import dcmwrite
from pynetdicom import AE, evt, AllStoragePresentationContexts
from pynetdicom.sop_class import StorageCommitmentPushModel


class StorageSCP:
    def __init__(self):
        self._ae = None
        self._server = None
        self._running = False

    @property
    def is_running(self):
        return self._running

    def start(self, ae_title, host, port, storage_dir, on_store=None, on_stgcmt=None):
        if self._running:
            return

        self._ae = AE(ae_title=ae_title.encode("utf-8"))
        for cx in AllStoragePresentationContexts:
            self._ae.add_supported_context(str(cx.abstract_syntax))
        self._ae.add_supported_context(StorageCommitmentPushModel)

        handlers = [(evt.EVT_C_STORE, _handle_store(self, storage_dir, on_store))]

        if on_stgcmt:
            def _handle_event(event):
                ds = event.request
                event_type = event.event_type
                count = 0
                seq = ds.get("ReferencedSOPSequence") if event_type == 1 else ds.get("FailedSOPSequence")
                if seq:
                    count = len(seq)
                on_stgcmt(event_type, count, ds, str(ds.get("TransactionUID", "")))
                return 0x0000
            handlers.append((evt.EVT_N_EVENT_REPORT, _handle_event, StorageCommitmentPushModel))

        self._server = self._ae.start_server(
            (host, int(port)), evt_handlers=handlers, block=False
        )
        self._running = True

    def stop(self):
        if self._server and self._running:
            self._server.shutdown()
            self._running = False


def _handle_store(scp, storage_dir, on_store):
    def handler(event):
        ds = event.dataset
        ds.file_meta = event.file_meta
        sop_uid = ds.SOPInstanceUID or "unknown"
        study_uid = ds.StudyInstanceUID or "unknown"
        patient = str(ds.get("PatientName", ""))
        patient_id = str(ds.get("PatientID", ""))
        mod = str(ds.get("Modality", ""))

        path = Path(storage_dir) / study_uid
        path.mkdir(parents=True, exist_ok=True)
        fpath = path / f"{sop_uid}.dcm"
        dcmwrite(str(fpath), ds)

        if on_store:
            on_store(sop_uid, study_uid, patient, patient_id, mod, str(fpath))
        return 0x0000
    return handler
