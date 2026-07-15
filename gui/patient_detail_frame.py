import tkinter as tk
from tkinter import ttk


class PatientDetailFrame(ttk.LabelFrame):
    def __init__(self, parent):
        super().__init__(parent, text="Patient / Study Detail", padding=8)
        self._create_widgets()

    def _create_widgets(self):
        fields = [
            ("Patient Name:", "patient_name"),
            ("Patient ID:", "patient_id"),
            ("Accession:", "accession"),
            ("Study Description:", "study_desc"),
            ("Modality:", "modality"),
            ("Scheduled:", "study_date"),
        ]
        self._labels = {}
        for i, (label, key) in enumerate(fields):
            ttk.Label(self, text=label, font=("", 9, "bold")).grid(
                row=i, column=0, sticky=tk.W, padx=4, pady=1)
            lbl = ttk.Label(self, text="-", foreground="#555")
            lbl.grid(row=i, column=1, sticky=tk.W, padx=4, pady=1)
            self._labels[key] = lbl

    def set_patient(self, item):
        self._labels["patient_name"].configure(text=item.patient_name, foreground="black")
        self._labels["patient_id"].configure(text=item.patient_id, foreground="black")
        self._labels["accession"].configure(text=item.accession_number, foreground="black")
        self._labels["study_desc"].configure(text=item.study_description, foreground="black")
        self._labels["modality"].configure(text=item.modality, foreground="black")
        self._labels["study_date"].configure(text=item.study_date, foreground="black")

