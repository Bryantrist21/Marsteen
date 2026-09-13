
# MARSTEEN — School Food Ordering System

Aplikasi simulasi pemesanan makanan sekolah berbasis Python + Tkinter dengan arsitektur OOP.

## Jalankan
Pastikan Python 3.10+ tersedia.

```bash
python marsteen.py
```

Tidak membutuhkan package eksternal karena GUI memakai Tkinter dan grafik dibuat dengan Tkinter Canvas.

## Akun Demo
### Buyer
- Email: `buyer@smamarsudirinibekasi.sch.id`
- Password: `buyer123`

### Seller
- Email: `seller@marsteen.sch.id`
- Password: `seller123`

## Fitur
### Entrance & Authentication
- Pilihan role Buyer / Seller
- Validasi domain email Buyer
- Login Seller terverifikasi
- Forgot Password dengan instruksi admin

### Buyer
- Dashboard
- Search menu
- Daftar tenant
- Promo & rekomendasi
- Stock validation
- King Size
- Add-ons / saus
- Cart
- Wishlist
- Checkout
- Simulasi QR payment
- QR pembayaran terpisah untuk setiap tenant
- Upload bukti pembayaran buyer per tenant dengan batas 15 menit
- Nomor antrean
- Order tracking
- Reminder pengambilan

### Seller
- Dashboard statistik
- Manajemen stok produk
- Status Available / Habis
- Add-ons / saus
- Order management
- Konfirmasi order
- Verifikasi atau tolak bukti pembayaran
- Upload QR pembayaran tenant dari dashboard seller
- Pengurangan stok otomatis saat konfirmasi
- Tandai siap diambil
- Laporan pemasukan
- Grafik harian / mingguan / bulanan / akumulasi

## Struktur OOP
- `User` — parent authentication model
- `Buyer(User)` — cart, wishlist, buyer flow
- `Seller(User)` — seller flow
- `Product` — menu, harga, stok, add-ons, king size
- `Order` — transaksi, status, queue, payment
- `OrderItem` — detail item transaksi
- `DatabaseManager` — local JSON persistence
- `MarsteenApp` — Tkinter controller / UI

## Penyimpanan
Saat pertama kali dijalankan, aplikasi membuat:
`marsteen_data.json`

File tersebut merupakan mock/local database. Hapus file tersebut jika ingin mengembalikan data demo awal.

## Catatan
ZIP referensi yang diberikan hanya berisi folder `css/` dan `js/` tanpa file HTML/CSS/JS yang dapat dipakai sebagai sumber visual. Karena itu aplikasi dibuat sebagai implementasi Tkinter mandiri berdasarkan spesifikasi fitur yang diberikan.
