# Basis data

Bab 15.22 menuntut dokumentasi basis data. Ini isinya: cara menjalankannya,
apa isi skemanya, dan kenapa beberapa keputusannya diambil begitu.

## Menjalankan

```bash
cp .env.example .env        # lalu isi kata sandinya
cd infrastructure && docker compose --env-file ../.env up -d
```

Lalu dari akar repositori:

```bash
pip install -r backend/requirements.txt
python backend/db/migrasi.py
python backend/db/muat_awal.py
```

Hasilnya PostgreSQL 16 dengan PostGIS 3.4 di `127.0.0.1:5433`, Redis di
`6380`, berisi 3 tulisan dan 7 proyek yang dibaca dari `content/`.

Keduanya **hanya mendengar di localhost**. Basis data tidak pernah menghadap
internet, bahkan di mesin pengembangan.

## Migrasi

SQL bernomor di `backend/db/migrations/`, dijalankan
`backend/db/migrasi.py`. Yang sudah diterapkan dicatat di tabel
`skema_migrasi` beserta sidik SHA-256 isinya.

**Menyunting migrasi yang sudah jalan akan ditolak**, bukan diterapkan diam
diam separuh. Kalau skemanya perlu berubah, buat berkas dengan nomor
berikutnya.

Kenapa bukan Alembic: skema ini dibaca jauh lebih sering daripada diubah, dan
SQL yang bisa dibaca langsung lebih jujur daripada Python yang membangkitkan
SQL. Proyek Parkir Jogja memakai pola yang sama.

## Tabel

| Tabel | Isi |
| --- | --- |
| `users` | pemilik situs. Satu baris. `sandi_hash` boleh NULL sebab passkey jadi jalur utama |
| `blog_posts` | tulisan, dua bahasa, isinya Markdown |
| `projects` | tujuh karya, dengan `geom` titik |
| `spatial_layers` | lapisan spasial umum, belum dipakai |
| `settings` | pasangan kunci nilai |
| `skema_migrasi` | catatan migrasi yang sudah jalan |

## Dua keputusan yang perlu dijelaskan

### Kolom berpasangan, bukan tabel terjemahan

Tiap teks punya sepasang kolom `_en` dan `_id`, keduanya `NOT NULL`.

Bahasanya tepat dua, keduanya selalu wajib ada, dan tidak akan bertambah.
Tabel terjemahan akan menambah join pada tiap kueri demi keluwesan yang tidak
akan pernah dipakai, dan yang lebih buruk, membuat "tulisan tanpa terjemahan"
jadi keadaan yang **mungkin**. Dengan dua kolom `NOT NULL`, keadaan itu
mustahil.

### Keadaan mustahil ditutup oleh basis datanya

```sql
CONSTRAINT terbit_punya_tanggal
    CHECK (status <> 'terbit' OR terbit_pada IS NOT NULL)
```

Tulisan berstatus terbit tanpa tanggal terbit akan merusak urutan umpan RSS
**tanpa galat apa pun**. Kode bisa lupa memeriksanya; basis data tidak.

Empat batasan lain dengan alasan yang sama:

| Batasan | Menahan |
| --- | --- |
| `titik_di_indonesia` | proyek yang koordinatnya mendarat di Paris |
| `slug_bentuknya_benar` | slug berspasi atau berhuruf besar, yang jadi alamat rusak |
| `kategori_tidak_kosong` | proyek yang tidak muncul di filter mana pun |
| `idx_projects_urut` unik | dua proyek berebut posisi yang sama |

Kelimanya diuji di `tests/test_basis_data.py` dengan cara **mencoba
melanggarnya**. Batasan yang tidak pernah diuji adalah batasan yang mungkin
saja tidak pernah menyala.

## Data awal

`backend/db/muat_awal.py` membaca `content/` lewat `tools/isi.py`, sumber
yang sama persis dengan yang dipakai membangun situs statis. Kalau pemuat ini
punya salinan datanya sendiri, dua salinan itu pasti berpisah jalan.

Aman dijalankan berkali kali: baris yang sudah ada diperbarui, bukan
digandakan. Ada ujinya.

## Yang belum

Cadangan dan pemulihan, bab 15.18. Sampai itu ditulis dan **diuji**, basis
data ini belum boleh menyimpan apa pun yang tidak ada salinannya di
`content/`.
