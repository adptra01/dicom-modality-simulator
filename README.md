# DICOM Modality Simulator

Aplikasi desktop Linux untuk simulasi perangkat modality DICOM (CT, MRI, X-ray, USG console). Digunakan untuk testing integrasi PACS tanpa perlu modality sungguhan.

Dibuat dengan **Python/Tkinter** + **pynetdicom** + **pydicom**.

---

## Fitur

Koneksi &amp; Verifikasi
- ✔ C-ECHO — Test koneksi ke PACS
- ✔ C-FIND — Ambil worklist / daftar study
- ✔ C-STORE — Kirim file DICOM ke PACS
- ✔ C-MOVE — Retrieve study dari PACS

Storage
- ✔ Storage SCP — Terima file DICOM dari PACS / modality lain
- ✔ JPG/PNG → DICOM — Convert gambar biasa ke Secondary Capture

Workflow
- ✔ MPPS — N-CREATE / N-SET (IN PROGRESS → COMPLETED / DISCONTINUED)
- ✔ Storage Commitment — Minta konfirmasi penyimpanan dari PACS

Utilitas
- ✔ Dataset Viewer — Lihat isi tag DICOM sebelum kirim
- ✔ DICOM Log — Semua aktivitas tercatat di panel log

---

## Screenshot

(Lihat folder `screenshots/` atau jalankan `python main.py`)

---

## Requirements

- Python 3.10+
- Linux (X11/Wayland) — bisa juga di WSL2 dengan X server
- PACS Server (dcm4chee / Orthanc / Conquest) untuk testing penuh

### Dependencies

| Library | Versi | Fungsi |
|---------|-------|--------|
| pynetdicom | ≥2.0 | DICOM networking (SCU/SCP) |
| pydicom | ≥3.0 | Baca/tulis dataset DICOM |
| Pillow | ≥10.0 | Konversi gambar ke DICOM |

---

## Instalasi

```bash
# Clone
git clone https://github.com/adptra01/dicom-modality-simulator.git
cd dicom-modality-simulator

# Virtual env
python3 -m venv .venv
source .venv/bin/activate

# Install
pip install pynetdicom pydicom Pillow

# Jalankan
python main.py
```

---

## Konfigurasi

File `config.json` di root proyek:

```json
{
  "ae_title": "PZDR",
  "called_ae": "DCM4CHEE",
  "pacs_host": "192.168.1.100",
  "pacs_port": 11112
}
```

| Field | Default | Fungsi |
|-------|---------|--------|
| `ae_title` | PZDR | Nama aplikasi kita di jaringan DICOM |
| `called_ae` | DCM4CHEE | Nama PACS tujuan |
| `pacs_host` | localhost | Alamat IP PACS |
| `pacs_port` | 11112 | Port DICOM PACS |

Bisa diubah lewat GUI (isi field + klik Save) atau edit file langsung.

---

## Quick Start ⭐

Cuma 6 langkah, selesai 2 menit:

```
1. Jalankan: python main.py
         ↓
2. Test Connection — isi Host/Port PACS, klik [Test Connection]
         ↓
3. Refresh Worklist — klik [Refresh Worklist]
         ↓
4. Pilih pasien — klik salah satu baris di tabel
         ↓
5. Browse DICOM — klik [Browse DICOM...], pilih file .dcm
         ↓
6. Send — klik [Send to PACS]
```

Kalau semua berhasil, panel log akan menampilkan:

```
● Connected to DCM4CHEE@192.168.1.100:11112
Worklist: 4 items
Selected: KNIX^KNIX (KNIX)
C-STORE Success
```

---

## Roadmap

| Versi | Isi |
|-------|-----|
| v0.1 | C-ECHO, C-STORE |
| v0.2 | C-FIND Worklist + tabel |
| v0.3 | Auto-fill patient info |
| v0.4 | JPG/PNG → DICOM |
| v0.5 | Storage SCP |
| v1.0 | MPPS, Storage Commitment, C-MOVE |
| v1.1 | Cancel, timeout, graceful close |
| v1.2 | C-GET retrieve |
| v1.3 | Modality Worklist (MWL) |
| v2.0 | Config UI (preferences dialog) |

---

## Lisensi

MIT

---

## Acknowledgements

- [pynetdicom](https://github.com/pydicom/pynetdicom) — DICOM networking library
- [pydicom](https://github.com/pydicom/pydicom) — DICOM file format library
- [dcm4chee-arc-light](https://github.com/dcm4che/dcm4chee-arc-light) — PACS server untuk testing
- [DCMTK](https://dicom.offis.de/dcmtk/) — DICOM toolkit (referensi)
