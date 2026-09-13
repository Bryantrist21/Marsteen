# MARSTEEN Frontend V4

Frontend prototype yang dibangun ulang dengan visual **editorial canteen / warm modern** dan tidak menggunakan gaya V3. Backend asli tidak diubah. Salinan backend asli berada di `BACKEND_UNTOUCHED/`.

## Yang dipertahankan dari backend
- Buyer: Beranda, Tenant, Keranjang, Wishlist, Pesanan.
- Product customization: Regular/King Size, add-ons/saus, jumlah, notes/catatan khusus.
- Checkout per tenant.
- Pembayaran per tenant dengan QR, upload bukti **PNG**, timer 15 menit, status UNPAID/PARTIAL/SUBMITTED/PAID/EXPIRED/REJECTED.
- Order tracker dan nomor antrean.
- Pickup reminder.
- Seller Dashboard.
- Seller QR upload/ganti.
- Product management: tambah produk, update stok, hapus produk.
- Add-ons management.
- Seller order detail, catatan pembeli, konfirmasi/tolak pembayaran, tandai siap diambil.
- Riwayat/archive dan laporan.

## Login contoh
Tidak ditampilkan di halaman login. Untuk pengujian, lihat akun yang tersimpan di `BACKEND_UNTOUCHED/marsteen_data.json`.

Placeholder di UI: buyer `yourname@smamarsudirinibekasi.sch.id`; seller `yourname@marsteen.sch.id`.

## Catatan integrasi
Frontend browser tidak memanggil method Tkinter secara langsung. Karena backend Python diminta tetap utuh, V4 memakai salinan dataset dan state browser (`localStorage`) sebagai adapter prototype. Backend asli tetap identik dan tidak diedit. Untuk deployment multi-user sungguhan, buat API adapter terpisah di atas backend tanpa mengubah model/OOP backend.
