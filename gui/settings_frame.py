import tkinter as tk
from tkinter import ttk
import threading

import config
from dicom.association import create_ae, associate
from dicom.echo import echo


class SettingsFrame(ttk.LabelFrame):
    def __init__(self, parent, log_widget, on_status):
        super().__init__(parent, text="PACS Connection", padding=8)
        self._log = log_widget
        self._on_status = on_status
        self._ae = None
        self._cfg = config.load()
        self._create_widgets()
        self._load_config()

    def _create_widgets(self):
        row = 0
        ttk.Label(self, text="AE Title:").grid(row=row, column=0, sticky=tk.W, padx=4, pady=2)
        self._ae_title = ttk.Entry(self, width=16)
        self._ae_title.grid(row=row, column=1, sticky=tk.EW, padx=4, pady=2)
        row += 1

        ttk.Label(self, text="Called AE:").grid(row=row, column=0, sticky=tk.W, padx=4, pady=2)
        self._called_ae = ttk.Entry(self, width=16)
        self._called_ae.grid(row=row, column=1, sticky=tk.EW, padx=4, pady=2)
        row += 1

        ttk.Label(self, text="Host:").grid(row=row, column=0, sticky=tk.W, padx=4, pady=2)
        self._host = ttk.Entry(self, width=16)
        self._host.grid(row=row, column=1, sticky=tk.EW, padx=4, pady=2)
        row += 1

        ttk.Label(self, text="Port:").grid(row=row, column=0, sticky=tk.W, padx=4, pady=2)
        self._port = ttk.Entry(self, width=16)
        self._port.grid(row=row, column=1, sticky=tk.EW, padx=4, pady=2)
        row += 1

        btn_frame = ttk.Frame(self)
        btn_frame.grid(row=row, column=0, columnspan=2, pady=6)
        self._test_btn = ttk.Button(btn_frame, text="Test Connection", command=self._on_test)
        self._test_btn.pack(side=tk.LEFT, padx=4)
        self._save_btn = ttk.Button(btn_frame, text="Save", command=self._on_save)
        self._save_btn.pack(side=tk.LEFT, padx=4)
        self._status_lbl = ttk.Label(btn_frame, text="○ Offline", foreground="gray")
        self._status_lbl.pack(side=tk.LEFT, padx=8)
        row += 1

        self.columnconfigure(1, weight=1)

    def _load_config(self):
        self._ae_title.delete(0, tk.END)
        self._ae_title.insert(0, self._cfg.get("ae_title", "PZDR"))
        self._called_ae.delete(0, tk.END)
        self._called_ae.insert(0, self._cfg.get("called_ae", "DCM4CHEE"))
        self._host.delete(0, tk.END)
        self._host.insert(0, self._cfg.get("pacs_host", "localhost"))
        self._port.delete(0, tk.END)
        self._port.insert(0, str(self._cfg.get("pacs_port", 11112)))

    def get_config(self):
        return {
            "ae_title": self._ae_title.get().strip(),
            "called_ae": self._called_ae.get().strip(),
            "pacs_host": self._host.get().strip(),
            "pacs_port": int(self._port.get().strip()),
        }

    def get_ae(self):
        return self._ae

    def _on_save(self):
        cfg = self.get_config()
        config.save(cfg)
        self._log.log_info("Configuration saved")

    def _on_test(self):
        self._test_btn.configure(state=tk.DISABLED)
        self._status_lbl.configure(text="⟳ Testing...", foreground="orange")
        self._log.log_info("Testing connection...")
        cfg = self.get_config()
        threading.Thread(target=self._do_test, args=(cfg,), daemon=True).start()

    def _do_test(self, cfg):
        try:
            ae = create_ae(cfg["ae_title"])
            assoc = associate(ae, cfg["pacs_host"], cfg["pacs_port"], cfg["called_ae"])
            if assoc.is_established:
                status_code, comment = echo(assoc)
                assoc.release()
                if status_code == 0x0000:
                    self._ae = ae
                    self._on_status(True)
                    self.after(0, lambda: self._status_lbl.configure(text="● Online", foreground="green"))
                    self.after(0, lambda: self._log.log_ok(
                        f"Connected to {cfg['called_ae']}@{cfg['pacs_host']}:{cfg['pacs_port']}"
                    ))
                else:
                    self.after(0, lambda: self._log.log_error(
                        f"C-ECHO failed: Status 0x{status_code:04X} {comment or ''}"
                    ))
            else:
                assoc.release()
                self._on_status(False)
                self.after(0, lambda: self._log.log_error(
                    f"Could not associate with {cfg['called_ae']}@{cfg['pacs_host']}:{cfg['pacs_port']}"
                ))
        except Exception as e:
            self._on_status(False)
            self.after(0, lambda: self._log.log_error(f"Connection error: {e}"))
        finally:
            self.after(0, lambda: self._test_btn.configure(state=tk.NORMAL))
            if not self._ae:
                self.after(0, lambda: self._status_lbl.configure(text="○ Offline", foreground="gray"))
