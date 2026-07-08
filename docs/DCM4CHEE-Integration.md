# Integrasi dengan DCM4CHEE

Panduan lengkap menghubungkan DICOM Modality Simulator dengan server PACS dcm4chee.

---

## Daftar Isi

1. [Akses LDAP DCM4CHEE](#1-akses-ldap-dcm4chee)
2. [Daftar AE Title Simulator (PZDR)](#2-daftar-ae-title-simulator-pzdr)
3. [Daftar AE Title SCP (PZDR-SCP)](#3-daftar-ae-title-scp-pzdr-scp)
4. [Setup Transfer Capability](#4-setup-transfer-capability)
5. [Setup MPPS Service](#5-setup-mpps-service)
6. [Setup Storage Commitment](#6-setup-storage-commitment)
7. [Setup Modality Worklist](#7-setup-modality-worklist)
8. [Verifikasi Konfigurasi](#8-verifikasi-konfigurasi)
9. [DICOM Workflow Diagram](#9-dicom-workflow-diagram)
10. [Kendala Setup DCM4CHEE](#10-kendala-setup-dcm4chee)

---

## 1. Akses LDAP DCM4CHEE

DCM4CHEE menggunakan **ApacheDS (OpenDJ)** sebagai database konfigurasi. Semua pengaturan device, AE Title, dan service dilakukan lewat LDAP.

### Cek LDAP

```bash
# Port default LDAP dcm4chee: 1389
# Dari luar container (kalau port di-expose)
ldapsearch -h <ip-dcm4chee> -p 1389 \
  -D "cn=admin,cn=config" -w password \
  -b "cn=DICOM,cn=Configuration,dc=dcm4che,dc=org" \
  -s one "objectClass=*" dn
```

### Kalau LDAP Tidak Bisa Diakses


ldapadd: Can't contact LDAP server (-1)


**Kemungkinan:**
1. Port 1389 tidak di-expose dari container
2. Container tidak jalan
3. Firewall

**Solusi 1 — Akses dari dalam container:**

```bash
docker exec -it <nama-container-dcm4chee> ldapadd ...
```

**Solusi 2 — Expose port 1389 (docker-compose.yml):**

```yaml
services:
  ldap:
    ports:
      - "1389:1389"
```

**Solusi 3 — Cari container yang tepat:**

```bash
# Cari container yang jalan
docker ps | grep dcm4chee

# Cari container ldap
docker ps --format "{{.Names}}" | grep -i ldap

# Akses shell
docker exec -it <nama-container-ldap> bash
```

### Tools LDAP

| Tool | Fungsi |
|------|--------|
| `ldapsearch` | Cari/melihat konfigurasi |
| `ldapadd` | Tambah entry baru |
| `ldapmodify` | Ubah entry yang ada |
| `ldapdelete` | Hapus entry |

Semua tool tersedia di container dcm4chee (kalau tidak ada di host, jalankan dari dalam container).

---

## 2. Daftar AE Title Simulator (PZDR)

Biar PACS kenal sama simulator kita, daftarkan device `PZDR` dan network connection-nya.

### Langkah

Buat file `register-pzdr.ldif`:

```ldif
# 1. Device PZDR
dn: dicomDeviceName=PZDR,cn=Devices,cn=DICOM,cn=Configuration,dc=dcm4che,dc=org
objectClass: dicomDevice
objectClass: top
dicomDeviceName: PZDR
dicomInstalled: TRUE
dicomManufacturer: Python pynetdicom
dicomManufacturerModelName: DICOM Modality Simulator
dicomSoftwareVersion: 1.0
dicomNetworkConnectionReference: dicomNetworkConnectionName=PZDR-CONN,cn=PZDR,cn=Devices,cn=DICOM,cn=Configuration,dc=dcm4che,dc=org

# 2. Network Connection PZDR (SCU only → port 0)
dn: dicomNetworkConnectionName=PZDR-CONN,cn=PZDR,cn=Devices,cn=DICOM,cn=Configuration,dc=dcm4che,dc=org
objectClass: dicomNetworkConnection
objectClass: top
dicomNetworkConnectionName: PZDR-CONN
dicomHostname: <ip-simulator>
dicomPort: 0

# 3. AE Title PZDR
dn: dicomAETitle=PZDR,cn=AE Titles,cn=DICOM,cn=Configuration,dc=dcm4che,dc=org
objectClass: dicomAETitle
objectClass: top
dicomAETitle: PZDR
dicomNetworkAE: dicomNetworkConnectionName=PZDR-CONN,cn=PZDR,cn=Devices,cn=DICOM,cn=Configuration,dc=dcm4che,dc=org
```

Jalankan:

```bash
ldapadd -h <ip-dcm4chee> -p 1389 \
  -D "cn=admin,cn=config" -w password -x \
  -f register-pzdr.ldif
```

### Penjelasan

| Field | Isi | Arti |
|-------|-----|------|
| `dicomDeviceName` | PZDR | Nama device di PACS |
| `dicomInstalled` | TRUE | Device aktif |
| `dicomHostname` | `<ip-simulator>` | IP komputer simulator |
| `dicomPort` | 0 | 0 = SCU aja (cuma ngirim) |
| `dicomAETitle` | PZDR | AE Title yang dipake koneksi |

### Verifikasi

```bash
ldapsearch -h <ip-dcm4chee> -p 1389 \
  -D "cn=admin,cn=config" -w password -x \
  -b "dicomAETitle=PZDR,cn=AE Titles,cn=DICOM,cn=Configuration,dc=dcm4che,dc=org"
```

---

## 3. Daftar AE Title SCP (PZDR-SCP)

Untuk C-MOVE destination dan Storage Commitment, daftarkan device `PZDR-SCP` dengan port aktif.

### Langkah

Buat file `register-pzdr-scp.ldif`:

```ldif
# 1. Device PZDR-SCP
dn: dicomDeviceName=PZDR-SCP,cn=Devices,cn=DICOM,cn=Configuration,dc=dcm4che,dc=org
objectClass: dicomDevice
objectClass: top
dicomDeviceName: PZDR-SCP
dicomInstalled: TRUE
dicomNetworkConnectionReference: dicomNetworkConnectionName=PZDR-SCP-CONN,cn=PZDR-SCP,cn=Devices,cn=DICOM,cn=Configuration,dc=dcm4che,dc=org

# 2. Network Connection (port 11113)
dn: dicomNetworkConnectionName=PZDR-SCP-CONN,cn=PZDR-SCP,cn=Devices,cn=DICOM,cn=Configuration,dc=dcm4che,dc=org
objectClass: dicomNetworkConnection
objectClass: top
dicomNetworkConnectionName: PZDR-SCP-CONN
dicomHostname: <ip-simulator>
dicomPort: 11113

# 3. AE Title
dn: dicomAETitle=PZDR-SCP,cn=AE Titles,cn=DICOM,cn=Configuration,dc=dcm4che,dc=org
objectClass: dicomAETitle
objectClass: top
dicomAETitle: PZDR-SCP
dicomNetworkAE: dicomNetworkConnectionName=PZDR-SCP-CONN,cn=PZDR-SCP,cn=Devices,cn=DICOM,cn=Configuration,dc=dcm4che,dc=org
```

Jalankan:

```bash
ldapadd -h <ip-dcm4chee> -p 1389 \
  -D "cn=admin,cn=config" -w password -x \
  -f register-pzdr-scp.ldif
```

### Penting

- **dicomHostname** harus diisi IP simulator yang bisa diakses dari container PACS
- Kalau PACS dan simulator di komputer yang sama: `172.17.0.1` (gateway Docker) atau `host.docker.internal`
- **dicomPort** (11113) harus sama dengan port yang diisi di panel Storage SCP simulator

---

## 4. Setup Transfer Capability

Transfer Capability menentukan SOP Class apa yang diizinkan untuk suatu AE.

### Untuk PZDR (SCU)

Biar PACS nerima C-STORE dari simulator, tambah Transfer Capability untuk storage SOP Class:

Buat file `tc-store.ldif`:

```ldif
dn: dicomTransferCapability=CTImageStorage,dicomAETitle=PZDR,cn=AE Titles,cn=DICOM,cn=Configuration,dc=dcm4che,dc=org
objectClass: dicomTransferCapability
objectClass: top
dicomTransferCapability: CTImageStorage
dicomSOPClass: 1.2.840.10008.5.1.4.1.1.2
dicomTransferRole: SCU
dicomTransferSyntax: 1.2.840.10008.1.2
dicomTransferSyntax: 1.2.840.10008.1.2.1
dicomTransferSyntax: 1.2.840.10008.1.2.4.50
dicomTransferSyntax: 1.2.840.10008.1.2.4.51
dicomTransferSyntax: 1.2.840.10008.1.2.4.57
dicomTransferSyntax: 1.2.840.10008.1.2.4.70
```

Tapi ini akan panjang kalau untuk 17 SOP Class. Alternatif: **jangan set Transfer Capability** — dcm4chee secara default menerima semua SOP Class dari AE yang terdaftar (tergantung konfigurasi).

### Kalau C-STORE Gagal (0xA900 atau 0x0122)

Coba tambah Transfer Capability manual. Atau cek dcm4chee log:

```bash
docker logs <container-dcm4chee> 2>&1 | grep -i "store\|aetitle\|rejected"
```

---

## 5. Setup MPPS Service

MPPS (Modality Performed Procedure Step) membutuhkan service khusus di Wildfly.

### Langkah

**1. Edit standalone.xml**

```bash
docker exec -it <container-dcm4chee> bash
vi /opt/wildfly/standalone/configuration/standalone.xml
```

Cari bagian `<subsystem>` dan tambah:

```xml
<subsystem xmlns="urn:jboss:domain:dcm4che-mpps-service:1.0">
    <mpps-service name="mpps-dcm4chee"/>
</subsystem>
```

**2. Tambah extension (kalau belum ada)**

Di bagian `<extensions>`:

```xml
<extension module="org.dcm4che.wildfly.mpps"/>
```

**3. Restart dcm4chee**

```bash
docker restart <container-dcm4chee>
```

### Verifikasi

Buka dcm4chee log dan cari "mpps":

```bash
docker exec <container-dcm4chee> \
  cat /opt/wildfly/standalone/log/server.log | grep -i mpps
```

Kalau sukses, akan terlihat:

```
MPPSService started
```

### Kalau Masih Error 0x0110

```
MPPS N-CREATE: 0x0110
Error Comment: java.lang.NullPointerException
```

Ini berarti MPPS service tidak terdeploy dengan benar. Beberapa hal yang bisa dicek:

1. **Apakah module wildfly ada?**
   ```bash
   docker exec <container-dcm4chee> ls /opt/wildfly/modules/org/dcm4che/wildfly/mpps/
   ```

2. **Apakah ada error di log?**
   ```bash
   docker exec <container-dcm4chee> \
     cat /opt/wildfly/standalone/log/server.log | grep -i "mpps\|error" | tail -20
   ```

3. **Apakah ada service MPPS di deployments?**
   ```bash
   docker exec <container-dcm4chee> ls /opt/wildfly/standalone/deployments/ | grep mpps
   ```

4. **Coba pakai versi dcm4chee yang lebih baru** — beberapa versi lama ada bug NullPointerException di MPPS.

---

## 6. Setup Storage Commitment

Storage Commitment membutuhkan:
1. AE SCP tujuan terdaftar (PZDR-SCP) — sudah dilakukan di langkah 3
2. Service Storage Commitment aktif di dcm4chee

### Storage Commitment di dcm4chee

Di dcm4chee-arc, Storage Commitment biasanya sudah aktif secara default. Yang perlu dipastikan:

1. **AE SCP PZDR-SCP terdaftar** — sudah
2. **SCP simulator sedang berjalan** — Start Server di panel Storage SCP
3. **PACS bisa akses port SCP simulator** — cek dengan `telnet <ip-simulator> 11113`

### Alur Storage Commitment

```
Simulator                          PACS (dcm4chee)
    │                                   │
    │──── N-ACTION-RQ (TransactionUID)──→│
    │    SOP Instance UID list           │
    │                                   │
    │    (PACS proses async)            │
    │                                   │
    │←─── N-EVENT-REPORT-RQ ────────────│
    │    Success: ReferencedSOPSequence  │
    │    atau                            │
    │    Failure: FailedSOPSequence      │
```

### Kalau Gagal

**N-ACTION return 0x0110:**
Service Storage Commitment tidak aktif. Cek log dcm4chee.

**N-EVENT-REPORT tidak datang:**
- SCP tidak aktif → Start Server
- Firewall blokir port 11113
- AE PZDR-SCP tidak dikenal → daftarkan

### Cara Debug

```bash
# Cek apakah PACS bisa reach port SCP
docker exec <container-dcm4chee> bash -c "echo test | nc -w 3 <ip-simulator> 11113"

# Cek log PACS untuk Storage Commitment
docker exec <container-dcm4chee> \
  cat /opt/wildfly/standalone/log/server.log | grep -i "storage\|commitment\|stgcmt"
```

---

## 7. Setup Modality Worklist

Simulator saat ini menggunakan query **Study Root** (bukan Modality Worklist). Study Root query mengambil semua study dari PACS — tidak spesifik per modality.

### Cara Kerja

```
C-FIND-RQ:
  QueryRetrieveLevel: STUDY
  StudyInstanceUID: (empty — cari semua)
  PatientName: (empty — cari semua)
  ...

PACS response:
  Semua study yang cocok dengan kriteria
```

### Kalau Worklist Kosong

```
Worklist: 0 items
```

**Kemungkinan:**
1. PACS benar-benar kosong — belum ada study
2. C-FIND context tidak di-accept — cek accepted contexts

**Solusi:**
1. Kirim dulu file DICOM ke PACS (via simulator atau tool lain)
2. Cek accepted contexts:
   ```python
   for cx in assoc.accepted_contexts:
       print(cx.abstract_syntax)
   ```
   Harus ada `1.2.840.10008.5.1.4.1.2.2.1` (StudyRootQueryRetrieveInformationModelFind)

### Kalau Mau Query Modality Worklist

Fitur MWL (Modality Worklist) belum diimplementasikan. Rencana ada di versi 1.3.

---

## 8. Verifikasi Konfigurasi

Setelah semua konfigurasi selesai, verifikasi dengan langkah berikut:

### Step 1: Cek Koneksi

```
Simulator → [Test Connection] → PACS
```

Harus: **● Online**

### Step 2: Cek Worklist

```
Simulator → [Refresh Worklist] → PACS
```

Harus: **X items** (ada data)

### Step 3: Kirim File

```
Simulator → [Browse DICOM] → [Send to PACS]
```

Harus: **C-STORE Success**

### Step 4: C-MOVE

```
1. Start SCP (PZDR-SCP, port 11113)
2. Simulator → [Retrieve Study]
```

Harus: File masuk ke `~/dicom-received/`

### Step 5: MPPS (Kalau Service Ada)

```
1. Pilih pasien
2. MPPS Start → Complete
```

Harus: **MPPS COMPLETED** (atau error 0x0110 kalo service belum ada)

---

## 9. DICOM Workflow Diagram

### Alur Dasar

```
        Simulator                     DCM4CHEE
            │                            │
   ┌────────┼────────────────────────────┼───┐
   │ 1.     │──── C-ECHO-RQ ────────────→│   │
   │ Test   │←─── C-ECHO-RSP (0x0000) ───│   │
   ├────────┼────────────────────────────┼───┤
   │ 2.     │──── C-FIND-RQ ────────────→│   │
   │ Query  │←─── C-FIND-RSP (study) ────│   │
   │        │←─── C-FIND-RSP (study) ────│   │
   │        │←─── C-FIND-RSP (pending) ──│   │
   ├────────┼────────────────────────────┼───┤
   │ 3.     │──── C-STORE-RQ ───────────→│   │
   │ Send   │←─── C-STORE-RSP (0x0000) ──│   │
   ├────────┼────────────────────────────┼───┤
   │ 4.     │──── N-ACTION-RQ ──────────→│   │
   │ StgCmt │←─── N-ACTION-RSP ──────────│   │
   │        │←─── N-EVENT-REPORT-RQ ─────│   │
   └────────┴────────────────────────────┴───┘
```

### Alur Lengkap (Dengan MPPS)

```
   Simulator                     DCM4CHEE
       │                            │
       │ 1. Test Connection         │
       │──── C-ECHO ──────────────→│
       │←─── C-ECHO ───────────────│
       │                            │
       │ 2. Get Worklist            │
       │──── C-FIND ──────────────→│
       │←─── C-FIND (studies) ─────│
       │                            │
       │ 3. MPPS Start              │
       │──── N-CREATE (IN PROGRESS)→│
       │←─── N-CREATE Response ─────│
       │                            │
       │ 4. Store Images            │
       │──── C-STORE (image 1) ────→│
       │←─── C-STORE Response ──────│
       │──── C-STORE (image 2) ────→│
       │←─── C-STORE Response ──────│
       │                            │
       │ 5. MPPS Complete           │
       │──── N-SET (COMPLETED) ────→│
       │←─── N-SET Response ────────│
       │                            │
       │ 6. Storage Commitment      │
       │──── N-ACTION ─────────────→│
       │←─── N-ACTION Response ─────│
       │←─── N-EVENT-REPORT ────────│
```

---

## 10. Kendala Setup DCM4CHEE

### 1. LDAP "Can't contact LDAP server"

```
ldapadd: Can't contact LDAP server (-1)
```

**Solusi:**
```bash
# Cari container LDAP
docker ps | grep -i ldap

# Coba akses dari dalam container
docker exec -it <container-ldap> ldapadd -h localhost -p 1389 ...
```

### 2. AE sudah terdaftar (duplicate entry)

```
ldapadd: Entry already exists (20)
```

**Solusi:** Hapus dulu, atau pakai `ldapmodify`:
```bash
ldapdelete -h <host> -p 1389 \
  -D "cn=admin,cn=config" -w password -x \
  "dicomAETitle=PZDR,cn=AE Titles,cn=DICOM,cn=Configuration,dc=dcm4che,dc=org"
```

### 3. DCM4CHEE di Docker — cara dapat IP host

Kalau simulator di host dan dcm4chee di container:

```bash
# Gateway Docker = IP host dari container
docker network inspect bridge | grep Gateway
# Biasanya 172.17.0.1

# Atau pake host.docker.internal (kalau support)
```

Set `dicomHostname` simulator ke `172.17.0.1` atau `host.docker.internal`.

### 4. Log dcm4chee kosong

```bash
docker logs <container-dcm4chee> 2>&1
```
Cuma nampilin JBoss banner?

Log runtime ada di dalam container:
```bash
docker exec <container-dcm4chee> \
  cat /opt/wildfly/standalone/log/server.log | tail -100
```

### 5. dcm4chee reject semua koneksi

Cek apakah konfigurasi DICOM aktif:
```bash
docker exec <container-dcm4chee> \
  cat /opt/wildfly/standalone/configuration/standalone.xml | grep -i dicom
```

Pastikan ada:
```xml
<subsystem xmlns="urn:jboss:domain:dcm4che-dicom-service:3.0">
    <service name="dicom-service"/>
</subsystem>
```

### 6. Container dcm4chee restart terus

```bash
docker logs <container-dcm4chee> 2>&1 | grep -i error
```

Biasanya karena:
- Port 11112 sudah dipakai → mapping port beda
- LDAP corrupted → hapus volume LDAP dan restart
- RAM tidak cukup → tambah memory container

### 7. Setup dari Awal dengan Docker Compose

```yaml
version: '3.8'
services:
  ldap:
    image: dcm4che/slapd-dcm4chee:2.4.57-26.0
    container_name: dcm4chee-ldap
    ports:
      - "1389:389"
    volumes:
      - ldap-data:/var/lib/ldap
      - ldap-config:/etc/ldap/slapd.d

  db:
    image: dcm4che/postgres-dcm4chee:16.4-26.0
    container_name: dcm4chee-db
    ports:
      - "5432:5432"
    volumes:
      - db-data:/var/lib/postgresql/data

  arc:
    image: dcm4che/dcm4chee-arc-psql:5.34.3
    container_name: dcm4chee-arc
    ports:
      - "11112:11112"
      - "8080:8080"
      - "8443:8443"
    environment:
      LDAP_HOST: ldap
      LDAP_PORT: 389
      DB_HOST: db
      DB_PORT: 5432
    depends_on:
      - ldap
      - db

volumes:
  ldap-data:
  ldap-config:
  db-data:
```

Kalau pake compose ini, akses LDAP dari host:

```bash
ldapadd -h localhost -p 1389 -D "cn=admin,cn=config" -w password -x ...
```
