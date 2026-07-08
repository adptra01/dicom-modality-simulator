import tkinter as tk
from tkinter import ttk
from pathlib import Path

from dicom.scp import StorageSCP


class SCPFrame(ttk.LabelFrame):
    def __init__(self, parent, log_widget, get_config):
        super().__init__(parent, text="Storage SCP (Receive)", padding=8)
        self._log = log_widget
        self._get_config = get_config
        self._scp = StorageSCP()
        self._create_widgets()

    def _create_widgets(self):
        row = 0
        ttk.Label(self, text="AE Title:").grid(row=row, column=0, sticky=tk.W, padx=4, pady=2)
        self._ae_entry = ttk.Entry(self, width=16)
        self._ae_entry.insert(0, "PZDR-SCP")
        self._ae_entry.grid(row=row, column=1, sticky=tk.W, padx=4, pady=2)
        row += 1

        ttk.Label(self, text="Listen Port:").grid(row=row, column=0, sticky=tk.W, padx=4, pady=2)
        self._port_entry = ttk.Entry(self, width=16)
        self._port_entry.insert(0, "11113")
        self._port_entry.grid(row=row, column=1, sticky=tk.W, padx=4, pady=2)
        row += 1

        ttk.Label(self, text="Storage Dir:").grid(row=row, column=0, sticky=tk.W, padx=4, pady=2)
        self._dir_entry = ttk.Entry(self, width=40)
        self._dir_entry.insert(0, str(Path.home() / "dicom-received"))
        self._dir_entry.grid(row=row, column=1, sticky=tk.EW, padx=4, pady=2)
        row += 1

        btn_frame = ttk.Frame(self)
        btn_frame.grid(row=row, column=0, columnspan=2, pady=4)
        self._start_btn = ttk.Button(btn_frame, text="Start Server", command=self._on_start)
        self._start_btn.pack(side=tk.LEFT, padx=4)
        self._stop_btn = ttk.Button(btn_frame, text="Stop Server", command=self._on_stop, state=tk.DISABLED)
        self._stop_btn.pack(side=tk.LEFT, padx=4)
        self._status_lbl = ttk.Label(btn_frame, text="○ Stopped", foreground="gray")
        self._status_lbl.pack(side=tk.LEFT, padx=8)
        row += 1

        self.columnconfigure(1, weight=1)

    def _on_start(self):
        ae_title = self._ae_entry.get().strip()
        port = self._port_entry.get().strip()
        storage_dir = self._dir_entry.get().strip()

        Path(storage_dir).mkdir(parents=True, exist_ok=True)

        def _on_store(sop_uid, study_uid, patient, patient_id, mod, fpath):
            self._log.log_ok(f"Received: {patient} ({patient_id}) [{mod}]")
            self._log.log_raw(f"  SOP: {sop_uid}")
            self._log.log_raw(f"  Study: {study_uid}")
            self._log.log_raw(f"  Saved: {fpath}")

        def _on_stgcmt(event_type, count, ds, tx_uid):
            kind = "Success" if event_type == 1 else "Failed"
            self._log.log_raw(f"  StgCmt {kind}: {count} instances, tx={tx_uid}")

        try:
            self._scp.start(ae_title, "0.0.0.0", port, storage_dir, on_store=_on_store, on_stgcmt=_on_stgcmt)
            self._start_btn.configure(state=tk.DISABLED)
            self._stop_btn.configure(state=tk.NORMAL)
            self._status_lbl.configure(text=f"● Listening on :{port}", foreground="green")
            self._log.log_info(f"SCP started: {ae_title} on port {port}")
            self._log.log_info(f"  Storage: {storage_dir}")
        except Exception as e:
            self._log.log_error(f"SCP start failed: {e}")

    def _on_stop(self):
        self._scp.stop()
        self._start_btn.configure(state=tk.NORMAL)
        self._stop_btn.configure(state=tk.DISABLED)
        self._status_lbl.configure(text="○ Stopped", foreground="gray")
        self._log.log_info("SCP stopped")

    def destroy(self):
        self._scp.stop()
        super().destroy()
