# Panduan Deployment (Streamlit Community Cloud)

Streamlit Community Cloud adalah cara termudah dan gratis untuk melakukan deployment aplikasi ini.

## Langkah-langkah
1. Pastikan seluruh code proyek sudah di-push ke repository GitHub Anda.
2. Kunjungi [Streamlit Community Cloud](https://share.streamlit.io/) dan login menggunakan akun GitHub.
3. Klik tombol **New app**.
4. Hubungkan repository GitHub Anda, pilih branch (misal: `main`), dan set main file path ke `app.py`.
5. Klik **Deploy**.

## Penanganan Database (IDX-API) di Cloud

Karena `IDX-API` menggunakan **SQLite** (database lokal `IDX-API/data/database.sqlite`), Streamlit Cloud secara default tidak dapat menjalankan sinkronisasi data Deno di background. 

Oleh karena itu, ada beberapa opsi untuk menjaga data tetap up-to-date di cloud:

### Opsi 1: Commit Database Berkala (Paling Mudah)
Hapus file `.gitignore` yang memblokir folder `data/` jika ada, lalu lakukan commit file `IDX-API/data/database.sqlite` ke GitHub. Lakukan sinkronisasi data secara lokal (`deno run -A sync_init.ts`) dan push perubahan database tersebut setiap hari setelah market tutup.

### Opsi 2: Otomatisasi dengan GitHub Actions
Buat workflow GitHub Actions yang berjalan secara terjadwal (misal jam 18:00 WIB / 11:00 UTC setiap hari kerja). Workflow ini akan:
1. Setup Deno.
2. Menjalankan `cd IDX-API && deno run -A sync_init.ts`.
3. Melakukan commit file `database.sqlite` yang berubah, lalu push kembali ke repository. Streamlit Cloud akan otomatis membaca perubahan tersebut dan melakukan reboot aplikasi.

### Opsi 3: Gunakan VPS / Railway / Render
Jika ingin sinkronisasi berjalan sepenuhnya otomatis di server yang sama dengan aplikasi, gunakan layanan VPS atau PaaS seperti Render. Buat file `Dockerfile` atau gunakan script bash (`update_data.sh`) yang menjalankan sinkronisasi Deno secara background menggunakan `cron`.
