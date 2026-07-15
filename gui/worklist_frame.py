import tkinter as tk
from tkinter import ttk
import threading

from dicom.association import associate
from dicom.worklist import build_query, query_worklist


class WorklistFrame(ttk.LabelFrame):
    def __init__(self, parent, log_widget, get_config, get_ae, on_select, cancel_event):
        super().__init__(parent, text="Worklist", padding=8)
        self._log = log_widget
        self._get_config = get_config
        self._get_ae = get_ae
        self._on_select = on_select
        self._cancel = cancel_event
        self._assoc = None
        self._items = []
        self._create_widgets()

    def _create_widgets(self):
        toolbar = ttk.Frame(self)
        toolbar.pack(fill=tk.X, pady=(0, 4))
        self._refresh_btn = ttk.Button(toolbar, text="Refresh Worklist", command=self._on_refresh)
        self._refresh_btn.pack(side=tk.LEFT, padx=2)
        self._cancel_btn = ttk.Button(toolbar, text="Cancel", command=self._on_cancel, state=tk.DISABLED)
        self._cancel_btn.pack(side=tk.LEFT, padx=2)
        self._count_lbl = ttk.Label(toolbar, text="0 items")
        self._count_lbl.pack(side=tk.RIGHT, padx=4)

        columns = ("patient_id", "patient_name", "study_date", "modality", "accession", "study_desc")
        self._tree = ttk.Treeview(self, columns=columns, show="headings",
                                  height=8, selectmode="browse")
        self._tree.heading("patient_id", text="Patient ID")
        self._tree.heading("patient_name", text="Patient Name")
        self._tree.heading("study_date", text="Scheduled")
        self._tree.heading("modality", text="Modality")
        self._tree.heading("accession", text="Accession")
        self._tree.heading("study_desc", text="Description")
        self._tree.column("patient_id", width=90)
        self._tree.column("patient_name", width=140)
        self._tree.column("study_date", width=90)
        self._tree.column("modality", width=70)
        self._tree.column("accession", width=100)
        self._tree.column("study_desc", width=160)
        scroll = ttk.Scrollbar(self, orient=tk.VERTICAL, command=self._tree.yview)
        self._tree.configure(yscrollcommand=scroll.set)
        self._tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scroll.pack(side=tk.RIGHT, fill=tk.Y)
        self._tree.bind("<<TreeviewSelect>>", self._on_tree_select)

    def _on_cancel(self):
        if self._assoc:
            self._assoc.abort()
            self._assoc = None
        self._cancel.set()

    def _on_refresh(self):
        self._cancel.clear()
        self._refresh_btn.configure(state=tk.DISABLED)
        self._cancel_btn.configure(state=tk.NORMAL)
        self._log.log_info("Querying worklist...")
        threading.Thread(target=self._do_refresh, daemon=True).start()

    def _do_refresh(self):
        cfg = self._get_config()
        ae = self._get_ae()
        if ae is None:
            self.after(0, lambda: self._log.log_error("Not connected. Test connection first."))
            self.after(0, lambda: self._reset_refresh_btn())
            return
        if self._cancel.is_set():
            self.after(0, lambda: self._reset_refresh_btn())
            return
        try:
            assoc = associate(ae, cfg["pacs_host"], cfg["pacs_port"], cfg["called_ae"])
            self._assoc = assoc
            if self._cancel.is_set():
                assoc.abort()
                self.after(0, lambda: self._reset_refresh_btn())
                return
            if not assoc.is_established:
                self._assoc = None
                self.after(0, lambda: self._log.log_error("Association failed"))
                self.after(0, lambda: self._reset_refresh_btn())
                return
            query = build_query()
            results = query_worklist(assoc, query)
            self._assoc = None
            assoc.release()
            self._items = results
            self.after(0, self._update_table)
            self.after(0, lambda: self._log.log_ok(f"Worklist: {len(results)} items"))
        except Exception as e:
            self._assoc = None
            msg = f"Worklist error: {e}"
            self.after(0, lambda m=msg: self._log.log_error(m))
        finally:
            self.after(0, lambda: self._reset_refresh_btn())

    def _reset_refresh_btn(self):
        self._refresh_btn.configure(state=tk.NORMAL)
        self._cancel_btn.configure(state=tk.DISABLED)

    def _update_table(self):
        for row in self._tree.get_children():
            self._tree.delete(row)
        for item in self._items:
            self._tree.insert("", tk.END, values=(
                item.patient_id,
                item.patient_name,
                item.study_date,
                item.modality,
                item.accession_number,
                item.study_description,
            ))
        self._count_lbl.configure(text=f"{len(self._items)} items")

    def _on_tree_select(self, event):
        sel = self._tree.selection()
        if not sel or not self._items:
            return
        idx = self._tree.index(sel[0])
        if 0 <= idx < len(self._items):
            self._on_select(self._items[idx])
