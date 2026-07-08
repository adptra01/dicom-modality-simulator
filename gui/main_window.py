import tkinter as tk
from tkinter import ttk
import threading

from gui.settings_frame import SettingsFrame
from gui.worklist_frame import WorklistFrame
from gui.patient_detail_frame import PatientDetailFrame
from gui.send_frame import SendFrame
from gui.scp_frame import SCPFrame
from gui.log_widget import LogWidget


class MainWindow(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("DICOM Modality Simulator")
        self.geometry("900x700")
        self.minsize(700, 500)
        self._selected_patient = None
        self._connected = False
        self._cancel_event = threading.Event()
        self.protocol("WM_DELETE_WINDOW", self._on_close)
        self._create_widgets()

    def _create_widgets(self):
        self.log_widget = LogWidget(self)

        middle = ttk.Frame(self)
        send_row = ttk.Frame(middle)
        send_row.pack(fill=tk.X)
        self.patient_detail = PatientDetailFrame(send_row)
        self.patient_detail.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 4))
        self.send_frame = SendFrame(
            send_row, self.log_widget,
            get_config=self._get_config,
            get_ae=self._get_ae,
            get_selected_patient=self._get_selected_patient,
            cancel_event=self._cancel_event,
        )
        self.send_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(4, 0))

        self.scp_frame = SCPFrame(middle, self.log_widget, get_config=self._get_config)
        self.scp_frame.pack(fill=tk.X, pady=(4, 0))

        self.settings = SettingsFrame(
            self, self.log_widget,
            on_status=self._on_connection_status,
            cancel_event=self._cancel_event,
        )
        self.worklist = WorklistFrame(
            self, self.log_widget,
            get_config=self._get_config,
            get_ae=self._get_ae,
            on_select=self._on_patient_select,
            cancel_event=self._cancel_event,
        )

        self.settings.pack(fill=tk.X, padx=8, pady=(8, 4))
        self.worklist.pack(fill=tk.BOTH, expand=True, padx=8, pady=4)
        middle.pack(fill=tk.X, padx=8, pady=4)
        self.log_widget.pack(fill=tk.BOTH, padx=8, pady=(4, 8))

    def _get_config(self):
        return self.settings.get_config()

    def _get_ae(self):
        return self.settings.get_ae()

    def _get_selected_patient(self):
        return self._selected_patient

    def _on_patient_select(self, item):
        self._selected_patient = item
        self.patient_detail.set_patient(item)
        self.log_widget.log_info(f"Selected: {item.patient_name} ({item.patient_id})")

    def _on_connection_status(self, connected):
        self._connected = connected

    def _on_close(self):
        self._cancel_event.set()
        self.scp_frame.destroy()
        for _ in range(5):
            self.update_idletasks()
        self.destroy()

    def destroy(self):
        self.scp_frame.destroy()
        super().destroy()
