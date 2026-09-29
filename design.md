# Design System: Website Minimalis

Panduan ini menjadi acuan visual dan perilaku untuk seluruh halaman. Prinsip utamanya: **kurangi sampai hanya yang penting yang tersisa.** Setiap elemen harus punya alasan untuk ada.

---

## 1. Prinsip Utama

1. **Konten lebih dulu.** Desain melayani isi, bukan sebaliknya.
2. **Ruang kosong adalah elemen desain.** Jangan mengisi ruang hanya karena kosong.
3. **Satu titik fokus per layar.** Satu aksi utama, satu pesan utama.
4. **Konsistensi lebih penting daripada variasi.** Pakai ulang pola yang sama.
5. **Hapus dekorasi yang tidak membawa informasi.** Bayangan, gradien, dan ikon hanya dipakai bila membantu pemahaman.
6. **Aksesibel secara default.** Kontras cukup, fokus keyboard terlihat, responsif hingga layar kecil.

---

## 2. Warna

Palet **paten** terdiri dari tiga warna. Ketiganya tidak boleh diganti, digelapkan, atau dicampur dengan warna lain.

| Nama          | Hex       | Peran                                                        |
|---------------|-----------|--------------------------------------------------------------|
| `--bg`        | `#EDF6F9` | Latar halaman, area besar                                    |
| `--secondary` | `#83C5BE` | Penanda lembut: garis, tag, latar hover, area sorotan        |
| `--primary`   | `#006D77` | Aksi utama: tombol, tautan, judul, status aktif, fokus       |

Warna pendukung fungsional (bukan bagian palet, dipakai seperlunya):

| Nama        | Hex       | Peran                                          |
|-------------|-----------|------------------------------------------------|
| `--surface` | `#FFFFFF` | Kartu dan input agar terangkat dari latar      |
| `--ink`     | `#0E2A2D` | Teks isi panjang agar nyaman dibaca            |

### Kontras (terhitung)

| Kombinasi                          | Rasio  | Hasil                              |
|------------------------------------|--------|------------------------------------|
| `--primary` di atas `--bg`         | ≈ 5.5:1 | Lolos AA untuk teks                |
| Putih di atas `--primary`          | ≈ 6.1:1 | Lolos AA untuk teks tombol         |
| `--ink` di atas `--bg`             | > 12:1 | Lolos AAA                          |
| `--secondary` di atas `--bg`       | ≈ 1.8:1 | **Tidak lolos**: jangan untuk teks |

### Aturan penggunaan warna

- Komposisi kira-kira **70% `--bg` dan putih, 20% `--primary`, 10% `--secondary`**.
- `--secondary` hanya untuk elemen dekoratif fungsional (garis, latar, tag, indikator). Jangan dipakai sebagai warna teks pada latar terang.
- Teks di atas latar `--secondary` memakai `--ink`.
- Teks sekunder memakai `--primary` dengan ukuran lebih kecil, bukan abu-abu tambahan.
- Jangan gunakan gradien.
- Warna tidak boleh menjadi satu-satunya penanda status; tambahkan teks atau ikon.
- Mode gelap tidak disertakan agar palet tetap utuh.

---

## 3. Tipografi

Satu keluarga font sans-serif dengan bobot terbatas. Kepribadian datang dari skala dan spasi, bukan dari banyaknya gaya.

- **Font utama:** `Inter`, dengan cadangan `system-ui, -apple-system, "Segoe UI", sans-serif`
- **Bobot:** 400 (isi), 500 (label, tombol), 600 (judul)
- **Lebar baris:** maksimal 65–75 karakter untuk teks isi

### Skala tipografi

| Peran      | Ukuran                     | Bobot | Line-height | Letter-spacing |
|------------|----------------------------|-------|-------------|----------------|
| Display    | `clamp(2.5rem, 6vw, 4rem)` | 600   | 1.1         | -0.02em        |
| H1         | `2.25rem`                  | 600   | 1.15        | -0.015em       |
| H2         | `1.5rem`                   | 600   | 1.25        | -0.01em        |
| H3         | `1.125rem`                 | 600   | 1.35        | 0              |
| Isi        | `1rem` (16px)              | 400   | 1.65        | 0              |
| Kecil      | `0.875rem`                 | 400   | 1.5         | 0              |

### Aturan tipografi

- Gunakan *sentence case* untuk judul, tombol, dan label.
- Hindari huruf kapital semua untuk label.
- Hindari menonjolkan satu kata dalam judul dengan warna atau miring hanya demi hiasan.
- Rata kiri untuk teks panjang. Rata tengah hanya untuk judul pendek.

---

## 4. Tata Letak dan Spasi

### Grid

- Lebar konten maksimal: `1120px`; lebar teks bacaan: `680px`
- Grid 12 kolom di desktop, 4 kolom di mobile
- Gutter: `24px` (desktop), `16px` (mobile)

### Skala spasi (kelipatan 4px)

```
4 · 8 · 12 · 16 · 24 · 32 · 48 · 64 · 96 · 128
```

- Jarak antar-bagian halaman: `96px` (desktop), `64px` (mobile)
- Jarak antar-elemen dalam satu grup: `16px–24px`
- Padding kontainer horizontal: `24px` (mobile), `48px` (tablet ke atas)

### Konsep tata letak

Rata kiri, satu kolom dominan, dengan banyak ruang kosong di sisi kanan sebagai penyeimbang.

```
+--------------------------------------------------+
|  Logo                        Beranda  Karya  Kontak |
|                                                  |
|                                                  |
|  Judul utama yang jelas                          |
|  Satu kalimat penjelas.                          |
|                                                  |
|  [ Aksi utama ]                                  |
|                                                  |
|                                                  |
|  ----------------------------------------------  |
|  Bagian 1                                        |
|  Teks bacaan dengan lebar terbatas               |
|                                                  |
+--------------------------------------------------+
```

### Breakpoint

| Nama    | Lebar        |
|---------|--------------|
| Mobile  | < 640px      |
| Tablet  | 640–1023px   |
| Desktop | ≥ 1024px     |

---

## 5. Komponen

### Tombol

- **Utama:** latar `--primary`, teks putih, padding `12px 20px`, radius `8px`; hover memunculkan cincin `--secondary` 4px
- **Sekunder:** transparan, border `1px solid --primary`, teks `--primary`; hover berlatar `--secondary` dengan teks `--ink`
- **Teks (tertaut):** tanpa border, garis bawah saat hover
- Satu tombol utama per tampilan
- Label menyebut aksi yang terjadi: "Simpan perubahan", bukan "Kirim"

### Tautan

- Warna `--primary`, garis bawah dengan `text-underline-offset: 3px`
- Status hover: ketebalan garis bawah bertambah, tanpa perubahan warna drastis

### Formulir

- Label di atas input, selalu terlihat (jangan hanya placeholder)
- Input: border `1px solid --line`, radius `8px`, tinggi minimal `44px`
- Fokus: outline `2px solid --primary` dengan offset `2px`
- Pesan galat menjelaskan masalah dan cara memperbaikinya

### Kartu

- Gunakan hanya bila konten memang perlu dikelompokkan
- Latar `--surface`, border `1px solid --line`, radius `12px`, tanpa bayangan
- Jangan memecah semua konten menjadi kartu yang seragam

### Navigasi

- Maksimal 5 item utama
- Item aktif ditandai dengan warna `--primary` dan garis bawah `--secondary`, item lain memakai `--ink`
- Di mobile: menu ringkas yang membuka panel penuh

### Pemisah

- Garis `1px solid --line` atau cukup ruang kosong
- Utamakan ruang kosong daripada garis

---

## 6. Bentuk, Elevasi, dan Ikon

- **Radius:** `8px` untuk kontrol (tombol, input), `12px` untuk wadah. Tidak lebih dari dua nilai.
- **Bayangan:** hindari. Bila terpaksa (menu dropdown, modal): `0 8px 24px rgba(0,0,0,0.08)`
- **Border:** `1px`, warna `--line`
- **Ikon:** gaya garis tunggal, tebal `1.5px`, ukuran `20px` atau `24px`. Pakai hanya bila menambah makna.

---

## 7. Gambar dan Media

- Gambar berkualitas tinggi, sedikit, dan relevan dengan isi
- Rasio konsisten (misalnya 4:3 atau 16:9) dalam satu halaman
- Selalu sertakan atribut `alt` yang deskriptif
- Gunakan `loading="lazy"` untuk gambar di bawah lipatan
- Format modern (WebP/AVIF) dan ukuran responsif dengan `srcset`
- Hindari foto stok generik dan ilustrasi dekoratif

---

## 8. Gerak dan Interaksi

- Gerak dipakai untuk **menunjukkan perubahan**, bukan menghias
- Durasi: `150–250ms`, easing `cubic-bezier(0.2, 0, 0, 1)`
- Yang boleh beranimasi: hover/fokus, buka-tutup panel, konfirmasi aksi
- Hindari animasi masuk otomatis di setiap bagian saat scroll
- Hormati preferensi pengguna:

```css
@media (prefers-reduced-motion: reduce) {
  * { animation: none !important; transition: none !important; }
}
```

---

## 9. Penulisan Konten (Microcopy)

- Bahasa sederhana dan langsung; gunakan kalimat aktif
- Namai hal sesuai pemahaman pengguna, bukan istilah teknis sistem
- Tombol menyebut hasilnya ("Unduh laporan", "Buat akun")
- Nama aksi sama di seluruh alur: tombol "Terbitkan" menghasilkan notifikasi "Diterbitkan"
- Galat tidak meminta maaf dan tidak samar; jelaskan apa yang salah dan cara memperbaikinya
- Keadaan kosong mengajak bertindak: "Belum ada proyek. Buat proyek pertama Anda."

---

## 10. Aksesibilitas

- Kontras teks ≥ 4.5:1, teks besar ≥ 3:1
- Target sentuh minimal `44 × 44px`
- Fokus keyboard selalu terlihat
- Struktur heading berurutan (satu `h1` per halaman)
- Gunakan elemen HTML semantik (`nav`, `main`, `section`, `button`)
- Semua fungsi dapat dioperasikan tanpa mouse
- Dukung `prefers-reduced-motion`

---

## 11. Design Tokens (CSS)

```css
:root {
  /* Palet paten */
  --bg: #EDF6F9;
  --secondary: #83C5BE;
  --primary: #006D77;

  /* Pendukung fungsional */
  --surface: #FFFFFF;
  --ink: #0E2A2D;

  /* Turunan dari palet */
  --line: rgba(131, 197, 190, 0.6);   /* --secondary transparan */
  --focus: #006D77;

  /* Tipografi */
  --font: "Inter", system-ui, -apple-system, "Segoe UI", sans-serif;

  /* Spasi */
  --space-1: 4px;
  --space-2: 8px;
  --space-3: 12px;
  --space-4: 16px;
  --space-6: 24px;
  --space-8: 32px;
  --space-12: 48px;
  --space-16: 64px;
  --space-24: 96px;

  /* Bentuk */
  --radius-control: 8px;
  --radius-container: 12px;

  /* Gerak */
  --ease: cubic-bezier(0.2, 0, 0, 1);
  --duration: 200ms;
}

body {
  background: var(--bg);
  color: var(--ink);
  font-family: var(--font);
  line-height: 1.65;
}

h1, h2, h3 { color: var(--primary); }

a { color: var(--primary); text-underline-offset: 3px; }

.btn-primary {
  background: var(--primary);
  color: #FFFFFF;
  border: 0;
  border-radius: var(--radius-control);
  padding: 12px 20px;
  transition: box-shadow var(--duration) var(--ease);
}
.btn-primary:hover { box-shadow: 0 0 0 4px var(--secondary); }

.btn-secondary {
  background: transparent;
  color: var(--primary);
  border: 1px solid var(--primary);
  border-radius: var(--radius-control);
  padding: 12px 20px;
}
.btn-secondary:hover { background: var(--secondary); color: var(--ink); }

:focus-visible { outline: 2px solid var(--focus); outline-offset: 2px; }
```

---

## 12. Checklist Sebelum Rilis

- [ ] Hanya ada satu aksi utama per tampilan
- [ ] Hanya tiga warna palet paten yang dipakai (ditambah putih dan `--ink` sebagai pendukung)
- [ ] Tidak ada dekorasi yang tidak membawa informasi
- [ ] Teks bacaan tidak lebih lebar dari 75 karakter
- [ ] Kontras dan fokus keyboard sudah diuji
- [ ] Tampilan diperiksa di 360px, 768px, dan 1280px
- [ ] `prefers-reduced-motion` berfungsi
- [ ] Ada satu hal yang menjadi ciri khas, dan sisanya dibiarkan tenang
