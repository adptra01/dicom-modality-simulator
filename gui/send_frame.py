import tkinter as tk
from tkinter import ttk
from tkinter import filedialog
import threading

from pydicom import dcmread
from pydicom.errors import InvalidDicomError

from dicom.association import associate
from dicom.store import store
from dicom.dataset import dump_info, set_patient_info
from dicom.image import jpg_to_dicom
from dicom.mpps import mpps_start, mpps_complete, mpps_discontinued
from dicom.notify import update_worklist_status


class SendFrame(ttk.LabelFrame):
    def __init__(self, parent, log_widget, get_config, get_ae, get_selected_patient, cancel_event):
        super().__init__(parent, text="Send DICOM", padding=8)
        self._log = log_widget
        self._get_config = get_config
        self._get_ae = get_ae
        self._get_selected_patient = get_selected_patient
        self._cfg = None
        self._cancel = cancel_event
        self._current_ds = None
        self._current_path = None
        self._mpps_uid = None
        self._create_widgets()

    def _create_widgets(self):
        row = 0
        ttk.Label(self, text="File:").grid(row=row, column=0, sticky=tk.W, padx=4, pady=2)
        self._file_path = ttk.Entry(self, width=50)
        self._file_path.grid(row=row, column=1, sticky=tk.EW, padx=4, pady=2)
        self._browse_btn = ttk.Button(self, text="Browse DICOM...", command=self._on_browse)
        self._browse_btn.grid(row=row, column=2, padx=4, pady=2)
        row += 1

        ttk.Label(self, text="Image:").grid(row=row, column=0, sticky=tk.W, padx=4, pady=2)
        self._img_path = ttk.Entry(self, width=50)
        self._img_path.grid(row=row, column=1, sticky=tk.EW, padx=4, pady=2)
        self._img_btn = ttk.Button(self, text="From Image...", command=self._on_image)
        self._img_btn.grid(row=row, column=2, padx=4, pady=2)
        row += 1

        btn_frame = ttk.Frame(self)
        btn_frame.grid(row=row, column=0, columnspan=3, pady=4)
        self._dump_btn = ttk.Button(btn_frame, text="Dump Dataset", command=self._on_dump)
        self._dump_btn.pack(side=tk.LEFT, padx=4)
        self._send_btn = ttk.Button(btn_frame, text="Send to PACS", command=self._on_send)
        self._send_btn.pack(side=tk.LEFT, padx=4)
        row += 1

        sep = ttk.Separator(self, orient=tk.HORIZONTAL)
        sep.grid(row=row, column=0, columnspan=3, sticky=tk.EW, pady=4)
        row += 1

        ttk.Label(self, text="Workflow:").grid(row=row, column=0, sticky=tk.W, padx=4)
        wf = ttk.Frame(self)
        wf.grid(row=row, column=1, columnspan=2, sticky=tk.W, padx=4)
        self._mpps_start_btn = ttk.Button(wf, text="MPPS Start", command=self._on_mpps_start)
        self._mpps_start_btn.pack(side=tk.LEFT, padx=2)
        self._mpps_done_btn = ttk.Button(wf, text="Complete", command=self._on_mpps_complete, state=tk.DISABLED)
        self._mpps_done_btn.pack(side=tk.LEFT, padx=2)
        self._mpps_stop_btn = ttk.Button(wf, text="Discontinue", command=self._on_mpps_discontinued, state=tk.DISABLED)
        self._mpps_stop_btn.pack(side=tk.LEFT, padx=2)
        self._mpps_lbl = ttk.Label(wf, text="—", foreground="gray")
        self._mpps_lbl.pack(side=tk.LEFT, padx=8)
        self._stgcmt_btn = ttk.Button(wf, text="Stg Cmt", command=self._on_stgcmt, state=tk.DISABLED)
        self._stgcmt_btn.pack(side=tk.LEFT, padx=4)
        row += 1

        ttk.Label(self, text="Retrieve:").grid(row=row, column=0, sticky=tk.W, padx=4)
        self._retrieve_btn = ttk.Button(self, text="Retrieve Study", command=self._on_retrieve)
        self._retrieve_btn.grid(row=row, column=1, sticky=tk.W, padx=4, pady=2)
        row += 1

        self.columnconfigure(1, weight=1)

    def _notify_worklist(self, status_key):
        cfg = self._get_config()
        patient = self._get_selected_patient()
        if not patient or not patient.accession_number:
            return
        ok = update_worklist_status(
            cfg.get("portal_url", ""),
            cfg.get("portal_api_key", ""),
            patient.accession_number,
            status_key,
            study_uid=patient.study_instance_uid,
        )
        if ok:
            self._log.log_info(f"Portal notified: {status_key}")

    def _merged_ds(self):
        if self._current_ds is None:
            return None
        patient = self._get_selected_patient()
        if patient:
            return set_patient_info(
                self._current_ds,
                patient_name=patient.patient_name,
                patient_id=patient.patient_id,
                accession=patient.accession_number,
                study_desc=patient.study_description,
                modality=patient.modality,
            )
        return self._current_ds

    def _on_retrieve(self):
        patient = self._get_selected_patient()
        if not patient:
            self._log.log_error("Select a patient from worklist first")
            return
        self._retrieve_btn.configure(state=tk.DISABLED)
        threading.Thread(target=self._do_retrieve, args=(patient,), daemon=True).start()

    def _do_retrieve(self, patient):
        if self._cancel.is_set():
            self.after(0, lambda: self._retrieve_btn.configure(state=tk.NORMAL))
            return
        from dicom.retrieve import cmove_study
        cfg = self._get_config()
        ae = self._get_ae()
        if not ae:
            self.after(0, lambda: self._log.log_error("Test connection first"))
            self.after(0, lambda: self._retrieve_btn.configure(state=tk.NORMAL))
            return
        scp_ae = cfg.get("scp_ae", "PZDR-SCP")
        try:
            assoc = associate(ae, cfg["pacs_host"], cfg["pacs_port"], cfg["called_ae"])
            if not assoc.is_established:
                self.after(0, lambda: self._log.log_error("Association failed"))
                self.after(0, lambda: self._retrieve_btn.configure(state=tk.NORMAL))
                return
            status, rsp = cmove_study(assoc, patient.study_instance_uid, scp_ae)
            assoc.release()
            if status == 0x0000:
                self.after(0, lambda: self._log.log_ok(f"C-MOVE success → {scp_ae}"))
            elif status == 0xFF00:
                self.after(0, lambda: self._log.log_ok("C-MOVE sub-operations complete (pending)"))
            else:
                self.after(0, lambda: self._log.log_error(f"C-MOVE: 0x{status:04X}"))
        except Exception as e:
            self.after(0, lambda: self._log.log_error(f"C-MOVE error: {e}"))
        self.after(0, lambda: self._retrieve_btn.configure(state=tk.NORMAL))

    def _on_mpps_start(self):
        patient = self._get_selected_patient()
        if not patient:
            self._log.log_error("Select a patient from worklist first")
            return
        self._mpps_start_btn.configure(state=tk.DISABLED)
        threading.Thread(target=self._do_mpps_start, args=(patient,), daemon=True).start()

    def _do_mpps_start(self, patient):
        if self._cancel.is_set():
            self.after(0, lambda: self._mpps_start_btn.configure(state=tk.NORMAL))
            return
        cfg = self._get_config()
        ae = self._get_ae()
        if not ae:
            self.after(0, lambda: self._log.log_error("Test connection first"))
            self.after(0, lambda: self._mpps_start_btn.configure(state=tk.NORMAL))
            return
        try:
            assoc = associate(ae, cfg["pacs_host"], cfg["pacs_port"], cfg["called_ae"])
            if not assoc.is_established:
                self.after(0, lambda: self._log.log_error("Association failed"))
                self.after(0, lambda: self._mpps_start_btn.configure(state=tk.NORMAL))
                return
            status, rsp, mpps_uid = mpps_start(
                assoc, patient.patient_name, patient.patient_id,
                patient.study_instance_uid,
                desc=patient.study_description or "Modality simulator",
            )
            assoc.release()
            self._mpps_uid = mpps_uid
            if status == 0x0000:
                self.after(0, lambda: self._log.log_ok(f"MPPS started: {mpps_uid}"))
                self.after(0, lambda: self._mpps_lbl.configure(text="● IN PROGRESS", foreground="orange"))
                self.after(0, lambda: self._mpps_done_btn.configure(state=tk.NORMAL))
                self.after(0, lambda: self._mpps_stop_btn.configure(state=tk.NORMAL))
                self.after(0, lambda: self._stgcmt_btn.configure(state=tk.DISABLED))
                self.after(0, lambda: self._notify_worklist("in_progress"))
            else:
                self.after(0, lambda: self._log.log_error(f"MPPS N-CREATE: 0x{status:04X}"))
                self.after(0, lambda: self._mpps_start_btn.configure(state=tk.NORMAL))
        except Exception as e:
            self.after(0, lambda: self._log.log_error(f"MPPS error: {e}"))
            self.after(0, lambda: self._mpps_start_btn.configure(state=tk.NORMAL))

    def _on_mpps_complete(self):
        if not self._mpps_uid:
            return
        self._mpps_done_btn.configure(state=tk.DISABLED)
        self._mpps_stop_btn.configure(state=tk.DISABLED)
        threading.Thread(target=self._do_mpps_end, args=(False,), daemon=True).start()

    def _on_mpps_discontinued(self):
        if not self._mpps_uid:
            return
        self._mpps_done_btn.configure(state=tk.DISABLED)
        self._mpps_stop_btn.configure(state=tk.DISABLED)
        threading.Thread(target=self._do_mpps_end, args=(True,), daemon=True).start()

    def _do_mpps_end(self, discontinued):
        if self._cancel.is_set():
            return
        cfg = self._get_config()
        ae = self._get_ae()
        try:
            assoc = associate(ae, cfg["pacs_host"], cfg["pacs_port"], cfg["called_ae"])
            if not assoc.is_established:
                self.after(0, lambda: self._log.log_error("Association failed"))
                return
            fn = mpps_discontinued if discontinued else mpps_complete
            status, rsp = fn(assoc, self._mpps_uid)
            assoc.release()
            if status == 0x0000:
                label = "DISCONTINUED" if discontinued else "COMPLETED"
                color = "red" if discontinued else "green"
                self.after(0, lambda: self._log.log_ok(f"MPPS {label}"))
                self.after(0, lambda: self._mpps_lbl.configure(text=f"● {label}", foreground=color))
                self.after(0, lambda: self._mpps_start_btn.configure(state=tk.NORMAL))
                self.after(0, lambda: self._stgcmt_btn.configure(state=tk.NORMAL))
                if not discontinued:
                    self.after(0, lambda: self._notify_worklist("acquired"))
            else:
                self.after(0, lambda: self._log.log_error(f"MPPS N-SET: 0x{status:04X}"))
        except Exception as e:
            self.after(0, lambda: self._log.log_error(f"MPPS error: {e}"))

    def _on_stgcmt(self):
        if not self._current_ds:
            self._log.log_error("Send a file first")
            return
        self._stgcmt_btn.configure(state=tk.DISABLED)
        threading.Thread(target=self._do_stgcmt, daemon=True).start()

    def _do_stgcmt(self):
        if self._cancel.is_set():
            self.after(0, lambda: self._stgcmt_btn.configure(state=tk.NORMAL))
            return
        from dicom.stgcmt import stgcmt_request
        cfg = self._get_config()
        ae = self._get_ae()
        try:
            assoc = associate(ae, cfg["pacs_host"], cfg["pacs_port"], cfg["called_ae"])
            if not assoc.is_established:
                self.after(0, lambda: self._log.log_error("Association failed"))
                self.after(0, lambda: self._stgcmt_btn.configure(state=tk.NORMAL))
                return
            ds = self._merged_ds()
            if ds is None:
                self.after(0, lambda: self._log.log_error("No data loaded"))
                self.after(0, lambda: self._stgcmt_btn.configure(state=tk.NORMAL))
                assoc.release()
                return
            sop_class_uid = ds.SOPClassUID
            sop_uid = ds.SOPInstanceUID
            status, rsp, tx_uid = stgcmt_request(
                assoc,
                cfg.get("scp_ae", "PZDR-SCP"),
                cfg.get("scp_port", "11113"),
                [(sop_class_uid, sop_uid)],
            )
            assoc.release()
            if status == 0x0000:
                self.after(0, lambda: self._log.log_ok(f"StgCmt requested: tx={tx_uid}"))
            else:
                self.after(0, lambda: self._log.log_error(f"StgCmt N-ACTION: 0x{status:04X}"))
        except Exception as e:
            self.after(0, lambda: self._log.log_error(f"StgCmt error: {e}"))
        self.after(0, lambda: self._stgcmt_btn.configure(state=tk.NORMAL))

    def _on_browse(self):
        path = filedialog.askopenfilename(
            title="Select DICOM file",
            filetypes=[("DICOM files", "*.dcm"), ("All files", "*.*")],
        )
        if not path:
            return
        try:
            ds = dcmread(path, force=True)
            self._current_ds = ds
            self._current_path = path
            self._file_path.delete(0, tk.END)
            self._file_path.insert(0, path)
            self._log.log_info(f"Loaded DICOM: {path}")
        except InvalidDicomError as e:
            self._log.log_error(f"Invalid DICOM: {e}")
        except Exception as e:
            self._log.log_error(f"Error reading file: {e}")

    def _on_image(self):
        path = filedialog.askopenfilename(
            title="Select image file",
            filetypes=[("Images", "*.jpg *.jpeg *.png *.bmp"), ("All files", "*.*")],
        )
        if not path:
            return
        try:
            patient = self._get_selected_patient()
            ds = jpg_to_dicom(
                path,
                patient_name=patient.patient_name if patient else "",
                patient_id=patient.patient_id if patient else "",
                study_desc=patient.study_description if patient else "",
                accession=patient.accession_number if patient else "",
            )
            self._current_ds = ds
            self._current_path = path
            self._img_path.delete(0, tk.END)
            self._img_path.insert(0, path)
            self._log.log_info(f"Converted image to DICOM: {path}")
        except Exception as e:
            self._log.log_error(f"Image conversion error: {e}")

    def _on_dump(self):
        ds = self._merged_ds()
        if ds is None:
            self._log.log_error("No data loaded")
            return
        info = dump_info(ds)
        for line in info.split("\n"):
            self._log.log_raw(line)

    def _on_send(self):
        ds = self._merged_ds()
        if ds is None:
            self._log.log_error("No data loaded")
            return
        self._send_btn.configure(state=tk.DISABLED)
        self._log.log_info("Sending...")
        threading.Thread(target=self._do_send, args=(ds,), daemon=True).start()

    def _do_send(self, ds):
        if self._cancel.is_set():
            self.after(0, lambda: self._send_btn.configure(state=tk.NORMAL))
            return
        cfg = self._get_config()
        ae = self._get_ae()
        if ae is None:
            self.after(0, lambda: self._log.log_error("Not connected. Test connection first."))
            self.after(0, lambda: self._send_btn.configure(state=tk.NORMAL))
            return
        try:
            assoc = associate(ae, cfg["pacs_host"], cfg["pacs_port"], cfg["called_ae"])
            if not assoc.is_established:
                self.after(0, lambda: self._log.log_error("Association failed"))
                self.after(0, lambda: self._send_btn.configure(state=tk.NORMAL))
                return
            status_code, comment = store(assoc, ds)
            assoc.release()
            if status_code == 0x0000:
                self.after(0, lambda: self._log.log_ok("C-STORE Success"))
                self.after(0, lambda: self._notify_worklist("sent_to_pacs"))
            else:
                self.after(0, lambda: self._log.log_error(
                    f"C-STORE failed: Status 0x{status_code:04X} {comment or ''}"
                ))
        except Exception as e:
            self.after(0, lambda: self._log.log_error(f"Send error: {e}"))
        finally:
            self.after(0, lambda: self._send_btn.configure(state=tk.NORMAL))
