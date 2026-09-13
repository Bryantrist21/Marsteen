
import tkinter as tk
from tkinter import ttk, messagebox, filedialog
from dataclasses import dataclass, asdict, field
from datetime import datetime, timedelta
import json, os, random, hashlib, shutil

try:
    from PIL import Image, ImageTk
except ImportError:
    Image = None
    ImageTk = None

APP_TITLE = "MARSTEEN — School Food Ordering"
DATA_FILE = "marsteen_data.json"
SCHOOL_DOMAIN = "@smamarsudirinibekasi.sch.id"


# ============================================================
# MODEL LAYER — OOP ENTITIES
# ============================================================

@dataclass
class Product:
    id: str
    tenant: str
    name: str
    category: str
    price: int
    stock: int
    addons: list = field(default_factory=list)
    king_price: int = 0
    description: str = ""

    @property
    def available(self):
        return self.stock > 0

    def final_price(self, king=False, selected_addons=None):
        total = self.king_price if king and self.king_price else self.price
        for addon in selected_addons or []:
            total += int(addon.get("price", 0))
        return total


@dataclass
class User:
    user_id: str
    name: str
    email: str
    password_hash: str
    role: str

    @staticmethod
    def hash_password(password):
        return hashlib.sha256(password.encode()).hexdigest()

    def verify_password(self, password):
        return self.password_hash == self.hash_password(password)


@dataclass
class Buyer(User):
    wishlist: list = field(default_factory=list)
    cart: list = field(default_factory=list)


@dataclass
class Seller(User):
    tenant: str = ""


@dataclass
class OrderItem:
    product_id: str
    product_name: str
    tenant: str
    quantity: int
    unit_price: int
    king_size: bool = False
    addons: list = field(default_factory=list)
    notes: str = ""

    @property
    def subtotal(self):
        return self.quantity * self.unit_price


@dataclass
class Order:
    order_id: str
    buyer_id: str
    buyer_name: str
    items: list
    total: int
    queue_number: int
    status: str
    payment_status: str
    created_at: str
    pickup_reminder: str = "Belum ada pengingat"
    payment_deadline: str = ""
    tenant_payments: list = field(default_factory=list)

    def all_tenants(self):
        return sorted(set(item["tenant"] for item in self.items))


# ============================================================
# DATABASE / MANAGER
# ============================================================

class DatabaseManager:
    """Local JSON persistence. Acts as a lightweight mock database."""

    def __init__(self, filename=DATA_FILE):
        self.filename = filename
        self.data = {
            "users": [],
            "products": [],
            "orders": [],
            "archived_orders": [],
            "queue": 0,
            "addons": [
                {"name": "Saus Keju", "price": 2000},
                {"name": "Saus Pedas", "price": 1000},
                {"name": "Telur", "price": 3000},
                {"name": "Extra Sambal", "price": 0},
            ],
            "archived_sales": {},
        }
        self.load()
        if not self.data["users"]:
            self.seed_demo_data()

    def load(self):
        try:
            if os.path.exists(self.filename):
                with open(self.filename, "r", encoding="utf-8") as f:
                    self.data.update(json.load(f))
        except (json.JSONDecodeError, OSError):
            messagebox.showwarning("Database", "Data lokal rusak/tidak dapat dibaca. Data demo akan digunakan.")

    def save(self):
        try:
            with open(self.filename, "w", encoding="utf-8") as f:
                json.dump(self.data, f, indent=2, ensure_ascii=False)
        except OSError as e:
            messagebox.showerror("Database Error", f"Gagal menyimpan data:\n{e}")

    def seed_demo_data(self):
        self.data["users"] = [
            {
                "user_id": "B001", "name": "Vincent William",
                "email": "vincentw@smamarsudirinibekasi.sch.id",
                "password_hash": User.hash_password("buyer123"), "role": "buyer"
            },

            {
                "user_id": "B002", "name": "Bryan Tristan",
                "email": "bryantt@smamarsudirinibekasi.sch.id",
                "password_hash": User.hash_password("buyer123"), "role": "buyer"
            },

            {
                "user_id": "B003", "name": "Hernawan Charis",
                "email": "nawancharis@smamarsudirinibekasi.sch.id",
                "password_hash": User.hash_password("buyer123"), "role": "buyer"
            },

            {
                "user_id": "B004", "name": "Ecclesia Miracle",
                "email": "emiracle@smamarsudirinibekasi.sch.id",
                "password_hash": User.hash_password("buyer123"), "role": "buyer"
            },


            #SELLER
            {
                "user_id": "S001", "name": "Bu Linda",
                "email": "bulinda@marsteen.sch.id",
                "password_hash": User.hash_password("seller123"),
                "role": "seller", "tenant": "Bu Linda"
            },

             {
                "user_id": "S002", "name": "Opung Tobing",
                "email": "opungtobing@marsteen.sch.id",
                "password_hash": User.hash_password("seller123"),
                "role": "seller", "tenant": "Opung Tobing"
            },

             {
                "user_id": "S003", "name": "Mama Jones",
                "email": "mamajones@marsteen.sch.id",
                "password_hash": User.hash_password("seller123"),
                "role": "seller", "tenant": "Mama Jones"
            },

             {
                "user_id": "S004", "name": "Pakde Geprek",
                "email": "geprekbos@marsteen.sch.id",
                "password_hash": User.hash_password("seller123"),
                "role": "seller", "tenant": "Pakde Geprek"
            },

             {
                "user_id": "S005", "name": "Warung Nyai",
                "email": "bunyai@marsteen.sch.id",
                "password_hash": User.hash_password("seller123"),
                "role": "seller", "tenant": "Warung Nyai"
            },
        ]

        products = [
            Product("P001", "Bu Linda", "Chicken Katsu Rice", "Rice Bowl", 18000, 20,
                     self.data["addons"], 22000, "Nasi hangat dengan chicken katsu dan saus."),
            Product("P002", "Opung Tobing", "Ayam Black Pepper", "Rice Bowl", 20000, 15,
                     self.data["addons"], 24000, "Ayam lada hitam dengan nasi hangat."),
            Product("P003", "Pakde Geprek", "Ayam Geprek Level 5", "Rice Bowl", 17000, 12,
                     self.data["addons"], 21000, "Ayam pedas gurih untuk pecinta rasa kuat."),
            Product("P004", "Opung Tobing", "Kebab", "Snack", 10000, 18,
                     self.data["addons"], 13000, "Kebab dengan isian daging dan sayuran."),
            Product("P005", "Warung Nyai", "Mac n Cheese", "Snack", 9000, 25,
                     self.data["addons"], 12000, "Makaroni keju enak."),
            Product("P006", "Mama Jones", "Nasi Nugget", "Rice Bowl", 12000, 20,
                     self.data["addons"], 15000, "Nasi hangat dengan nugget."),
            Product("P007", "Mama Jones", "Spageti Carbonara", "Rice Bowl", 15000, 20,
                     self.data["addons"], 17000, "Spageti carbonara creamy ala Nyai"),
        ]
        self.data["products"] = [asdict(p) for p in products]
        self.save()

    # ---------- Users ----------
    def get_user(self, email, role):
        for u in self.data["users"]:
            if u["email"].lower() == email.lower() and u["role"] == role:
                return u
        return None

    def authenticate(self, email, password, role):
        u = self.get_user(email, role)
        if u and User("", "", "", u["password_hash"], role).verify_password(password):
            return u
        return None

    def update_user_wishlist(self, user_id, wishlist):
        for u in self.data["users"]:
            if u["user_id"] == user_id:
                u["wishlist"] = list(wishlist)
                self.save()
                return True
        return False

    # ---------- Products ----------
    def get_products(self):
        return [Product(**p) for p in self.data["products"]]

    def get_product(self, product_id):
        for p in self.data["products"]:
            if p["id"] == product_id:
                return Product(**p)
        return None

    def update_product_stock(self, product_id, amount):
        for p in self.data["products"]:
            if p["id"] == product_id:
                p["stock"] = max(0, int(amount))
                self.save()
                return True
        return False

    def add_product(self, product):
        if isinstance(product, Product):
            p_dict = asdict(product)
        else:
            p_dict = product
        self.data["products"].append(p_dict)
        self.save()
        return True

    def delete_product(self, product_id):
        initial_len = len(self.data["products"])
        self.data["products"] = [p for p in self.data["products"] if p["id"] != product_id]
        if len(self.data["products"]) < initial_len:
            self.save()
            return True
        return False

    # ---------- Orders ----------
    def next_queue(self):
        self.data["queue"] = int(self.data.get("queue", 0)) + 1
        self.save()
        return self.data["queue"]

    def add_order(self, order):
        self.data["orders"].append(asdict(order))
        self.save()

    def get_orders(self):
        return self.data["orders"]

    def get_archived_orders(self):
        return self.data.get("archived_orders", [])

    def clear_archived_orders(self):
        self.data["archived_orders"] = []
        self.save()

    def get_seller_product_sales(self, tenant):
        """Return paid sales grouped by product and order date for one seller."""
        products = {}
        for p in self.data.get("products", []):
            if p.get("tenant") == tenant:
                products[p["id"]] = {"id": p["id"], "name": p["name"], "daily": {}, "quantity": 0, "revenue": 0}

        for archived in self.data.get("archived_sales", {}).get(tenant, []):
            archived_id = archived.get("id")
            if archived_id not in products:
                products[archived_id] = {"id": archived_id, "name": archived.get("name", archived_id), "daily": {}, "quantity": 0, "revenue": 0}
            product = products[archived_id]
            for date_key, quantity in archived.get("daily", {}).items():
                product["daily"][date_key] = product["daily"].get(date_key, 0) + int(quantity)
            product["quantity"] += int(archived.get("quantity", 0))
            product["revenue"] += int(archived.get("revenue", 0))

        for order in self.data.get("orders", []):
            tenant_payment = next((payment for payment in order.get("tenant_payments", [])
                                   if payment.get("tenant") == tenant), None)
            if tenant_payment:
                if tenant_payment.get("status") != "PAID":
                    continue
            elif order.get("payment_status") != "PAID":
                continue
            try:
                order_date = datetime.strptime(order.get("created_at", ""), "%d/%m/%Y %H:%M").date()
            except (TypeError, ValueError):
                continue
            date_key = order_date.isoformat()
            for item in order.get("items", []):
                if item.get("tenant") != tenant:
                    continue
                product_id = item.get("product_id")
                if product_id not in products:
                    products[product_id] = {"id": product_id, "name": item.get("name") or item.get("product_name") or product_id,
                                            "daily": {}, "quantity": 0, "revenue": 0}
                product = products[product_id]
                quantity = max(0, int(item.get("quantity", 0)))
                unit_price = max(0, int(item.get("unit_price", 0)))
                product["daily"][date_key] = product["daily"].get(date_key, 0) + quantity
                product["quantity"] += quantity
                product["revenue"] += quantity * unit_price

        return list(products.values())

    def clear_order_history(self):
        archived_sales = self.data.setdefault("archived_sales", {})
        snapshot = {}
        today = datetime.now().date()
        remaining_orders = []
        archived_orders = self.data.setdefault("archived_orders", [])

        for order in self.data.get("orders", []):
            order_date = order.get("created_at", "")
            try:
                order_date_obj = datetime.strptime(order_date, "%d/%m/%Y %H:%M").date()
            except (TypeError, ValueError):
                remaining_orders.append(order)
                continue

            if order_date_obj == today:
                archived_orders.append(order)
                tenant_payments = order.get("tenant_payments", [])
                if not tenant_payments:
                    continue

                for payment in tenant_payments:
                    if payment.get("status") != "PAID":
                        continue
                    tenant = payment.get("tenant")
                    tenant_snapshot = snapshot.setdefault(tenant, {})
                    for item in order.get("items", []):
                        if item.get("tenant") != tenant:
                            continue
                        product_id = item.get("product_id")
                        product_name = item.get("name") or item.get("product_name") or product_id
                        product = tenant_snapshot.setdefault(product_id, {
                            "id": product_id,
                            "name": product_name,
                            "daily": {},
                            "quantity": 0,
                            "revenue": 0,
                        })
                        quantity = max(0, int(item.get("quantity", 0)))
                        unit_price = max(0, int(item.get("unit_price", 0)))
                        date_key = order_date_obj.isoformat()
                        product["daily"][date_key] = product["daily"].get(date_key, 0) + quantity
                        product["quantity"] += quantity
                        product["revenue"] += quantity * unit_price
                continue

            remaining_orders.append(order)

        for tenant, tenant_products in snapshot.items():
            merged = {}
            for entry in archived_sales.get(tenant, []):
                merged[entry["id"]] = {
                    "id": entry.get("id"),
                    "name": entry.get("name", entry.get("id")),
                    "daily": dict(entry.get("daily", {})),
                    "quantity": int(entry.get("quantity", 0)),
                    "revenue": int(entry.get("revenue", 0)),
                }

            for product_id, product in tenant_products.items():
                if product_id not in merged:
                    merged[product_id] = {
                        "id": product_id,
                        "name": product.get("name", product_id),
                        "daily": {},
                        "quantity": 0,
                        "revenue": 0,
                    }
                current = merged[product_id]
                for date_key, quantity in product.get("daily", {}).items():
                    current["daily"][date_key] = current["daily"].get(date_key, 0) + int(quantity)
                current["quantity"] += int(product.get("quantity", 0))
                current["revenue"] += int(product.get("revenue", 0))

            archived_sales[tenant] = list(merged.values())

        self.data["orders"] = remaining_orders
        self.save()

    def update_order(self, order_id, **changes):
        for order in self.data["orders"]:
            if order["order_id"] == order_id:
                order.update(changes)
                self.save()
                return True
        return False

    def get_tenant_qr(self, tenant):
        for user in self.data.get("users", []):
            if user.get("role") == "seller" and user.get("tenant") == tenant:
                qr_path = user.get("qr_path", "")
                return qr_path if qr_path and os.path.exists(qr_path) else ""
        return ""

    def update_seller_qr(self, user_id, qr_path):
        for user in self.data.get("users", []):
            if user.get("user_id") == user_id and user.get("role") == "seller":
                user["qr_path"] = qr_path
                self.save()
                return True
        return False


# ============================================================
# APPLICATION CONTROLLER
# ============================================================

class MarsteenApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title(APP_TITLE)
        self.geometry("1180x760")
        self.minsize(1000, 650)
        self.configure(bg="#F5F7FB")

        self.db = DatabaseManager()
        self.current_user = None
        self.buyer = None
        self.seller = None
        self.qr_image_refs = []
        self.payment_timer_job = None
        self.pending_checkout_orders = []

        self.colors = {
            "navy": "#17233C",
            "blue": "#356AE6",
            "light_blue": "#EAF0FF",
            "bg": "#F5F7FB",
            "white": "#FFFFFF",
            "text": "#1F2937",
            "muted": "#6B7280",
            "green": "#22A06B",
            "orange": "#F59E0B",
            "red": "#DC4C4C",
            "line": "#E5E7EB",
        }
        self.style = ttk.Style(self)
        try:
            self.style.theme_use("clam")
        except tk.TclError:
            pass
        self.style.configure("Treeview", rowheight=34, font=("Segoe UI", 10))
        self.style.configure("Treeview.Heading", font=("Segoe UI", 10, "bold"))
        self.style.configure("TNotebook.Tab", padding=(16, 9), font=("Segoe UI", 10, "bold"))

        self.show_entrance()

    def clear(self):
        if self.payment_timer_job:
            self.after_cancel(self.payment_timer_job)
            self.payment_timer_job = None
        for w in self.winfo_children():
            w.destroy()

    def load_qr_image(self, path, max_size=180):
        if not path or not os.path.exists(path):
            return None
        try:
            if Image and ImageTk:
                image = Image.open(path)
                image.thumbnail((max_size, max_size))
                return ImageTk.PhotoImage(image)
            return tk.PhotoImage(file=path)
        except (OSError, tk.TclError):
            return None

    def header(self, parent, title, subtitle=""):
        f = tk.Frame(parent, bg=self.colors["bg"])
        f.pack(fill="x", padx=28, pady=(24, 10))
        tk.Label(f, text="MARSTEEN", font=("Segoe UI", 22, "bold"),
                 fg=self.colors["navy"], bg=self.colors["bg"]).pack(side="left")
        tk.Label(f, text=title, font=("Segoe UI", 18, "bold"),
                 fg=self.colors["text"], bg=self.colors["bg"]).pack(side="left", padx=25)
        if subtitle:
            tk.Label(f, text=subtitle, font=("Segoe UI", 10),
                     fg=self.colors["muted"], bg=self.colors["bg"]).pack(side="left")
        return f

    def button(self, parent, text, command, primary=True, width=None):
        bg = self.colors["blue"] if primary else self.colors["white"]
        fg = "white" if primary else self.colors["text"]
        active = "#2858C7" if primary else "#EEF1F6"
        b = tk.Button(parent, text=text, command=command, bg=bg, fg=fg,
                      activebackground=active, activeforeground=fg,
                      relief="flat", bd=0, padx=18, pady=10,
                      font=("Segoe UI", 10, "bold"), cursor="hand2")
        if width:
            b.config(width=width)
        return b

    def card(self, parent, padx=20, pady=18):
        return tk.Frame(parent, bg=self.colors["white"], highlightbackground=self.colors["line"],
                        highlightthickness=1, padx=padx, pady=pady)

    # ========================================================
    # ENTRANCE / AUTH
    # ========================================================

    def show_entrance(self):
        self.clear()
        root = tk.Frame(self, bg=self.colors["bg"])
        root.pack(fill="both", expand=True)

        hero = tk.Frame(root, bg=self.colors["navy"], height=180)
        hero.pack(fill="x")
        tk.Label(hero, text="MARSTEEN", font=("Segoe UI", 38, "bold"),
                 fg="white", bg=self.colors["navy"]).pack(pady=(42, 0))
        tk.Label(hero, text="School Food Ordering System",
                 font=("Segoe UI", 13), fg="#D9E2FF", bg=self.colors["navy"]).pack(pady=5)

        tk.Label(root, text="Selamat datang!", font=("Segoe UI", 25, "bold"),
                 bg=self.colors["bg"], fg=self.colors["text"]).pack(pady=(48, 8))
        tk.Label(root, text="Pilih peran untuk melanjutkan ke MARSTEEN.",
                 font=("Segoe UI", 11), bg=self.colors["bg"], fg=self.colors["muted"]).pack()

        roles = tk.Frame(root, bg=self.colors["bg"])
        roles.pack(pady=35)

        for title, desc, emoji, cmd in [
            ("Pembeli", "Cari makanan, pesan, bayar, dan pantau antrean.", "🛒", lambda: self.show_login("buyer")),
            ("Penjual", "Kelola menu, stok, pesanan, dan laporan.", "🏪", lambda: self.show_login("seller")),
        ]:
            c = self.card(roles, padx=28, pady=25)
            c.pack(side="left", padx=15)
            tk.Label(c, text=emoji, font=("Segoe UI Emoji", 30), bg="white").pack()
            tk.Label(c, text=title, font=("Segoe UI", 16, "bold"),
                     fg=self.colors["text"], bg="white").pack(pady=(8, 4))
            tk.Label(c, text=desc, width=34, wraplength=250, justify="center",
                     fg=self.colors["muted"], bg="white").pack(pady=5)
            self.button(c, f"Masuk sebagai {title}", cmd).pack(pady=(14, 0))

        tk.Label(root, text="Demo Buyer: buyer@smamarsudirinibekasi.sch.id / buyer123    •    Demo Seller: seller@marsteen.sch.id / seller123",
                 font=("Segoe UI", 9), fg=self.colors["muted"], bg=self.colors["bg"]).pack(side="bottom", pady=18)

    def show_login(self, role):
        self.clear()
        container = tk.Frame(self, bg=self.colors["bg"])
        container.pack(fill="both", expand=True)

        self.header(container, "Login " + ("Pembeli" if role == "buyer" else "Penjual"),
                    "Akses akun MARSTEEN")

        card = self.card(container, padx=35, pady=30)
        card.pack(pady=30, ipadx=20)

        tk.Label(card, text="Email", bg="white", fg=self.colors["text"],
                 font=("Segoe UI", 10, "bold")).pack(anchor="w")
        email = tk.Entry(card, width=44, font=("Segoe UI", 11), relief="solid", bd=1)
        email.pack(pady=(5, 16), ipady=8)

        tk.Label(card, text="Password", bg="white", fg=self.colors["text"],
                 font=("Segoe UI", 10, "bold")).pack(anchor="w")
        password = tk.Entry(card, width=44, show="•", font=("Segoe UI", 11), relief="solid", bd=1)
        password.pack(pady=(5, 10), ipady=8)

        if role == "buyer":
            tk.Label(card, text=f"Email wajib menggunakan domain {SCHOOL_DOMAIN}",
                     bg="white", fg=self.colors["muted"], font=("Segoe UI", 9)).pack(anchor="w")
        else:
            tk.Label(card, text="Gunakan akun penjual yang telah diverifikasi admin.",
                     bg="white", fg=self.colors["muted"], font=("Segoe UI", 9)).pack(anchor="w")

        def login():
            e, p = email.get().strip(), password.get()
            if not e or not p:
                messagebox.showwarning("Validasi", "Email dan password wajib diisi.")
                return
            if role == "buyer" and not e.lower().endswith(SCHOOL_DOMAIN):
                messagebox.showerror("Email tidak valid", f"Pembeli harus menggunakan {SCHOOL_DOMAIN}")
                return
            user = self.db.authenticate(e, p, role)
            if not user:
                messagebox.showerror("Login gagal", "Email/password salah atau akun tidak sesuai role.")
                return
            self.current_user = user
            if role == "buyer":
                buyer_kwargs = {k: user[k] for k in ["user_id","name","email","password_hash","role"] if k in user}
                if "wishlist" in user:
                    buyer_kwargs["wishlist"] = list(user["wishlist"])
                self.buyer = Buyer(**buyer_kwargs)
                self.show_buyer()
            else:
                self.seller = Seller(**{k: user[k] for k in ["user_id","name","email","password_hash","role","tenant"]})
                self.show_seller()

        self.button(card, "Masuk", login).pack(fill="x", pady=(15, 10))
        self.button(card, "Lupa Password", lambda: self.forgot_password(), primary=False).pack(fill="x")
        self.button(container, "← Kembali", self.show_entrance, primary=False).pack(pady=10)

        password.bind("<Return>", lambda e: login())

    def forgot_password(self):
        messagebox.showinfo(
            "Lupa Password",
            "Jika lupa password, hubungi Admin Sekolah / Tim MARSTEEN.\n\n"
            "Sampaikan nama, email sekolah, dan role akun.\n"
            "Admin akan melakukan verifikasi sebelum reset password."
        )

    # ========================================================
    # BUYER UI
    # ========================================================

    def show_buyer(self):
        self.clear()
        self.header(self, "Buyer Dashboard", f"Halo, {self.buyer.name}")
        nav = tk.Frame(self, bg=self.colors["navy"], height=54)
        nav.pack(fill="x")
        for text, cmd in [
            ("🏠 Beranda", self.buyer_home),
            ("🏪 Tenant", self.buyer_tenants),
            ("🛒 Keranjang", self.buyer_cart),
            ("♡ Wishlist", self.buyer_wishlist),
            ("📦 Pesanan", self.buyer_orders),
        ]:
            tk.Button(nav, text=text, command=cmd, bg=self.colors["navy"], fg="white",
                      activebackground="#293A5E", relief="flat", bd=0, padx=17, pady=16,
                      font=("Segoe UI", 10, "bold"), cursor="hand2").pack(side="left")
        self.button(nav, "Keluar", self.show_entrance, primary=False).pack(side="right", padx=12, pady=8)
        self.buyer_home()

    def buyer_home(self):
        self._buyer_content("home")

    def _buyer_content(self, mode):
        old = getattr(self, "buyer_content", None)
        if old:
            old.destroy()
        self.buyer_content = tk.Frame(self, bg=self.colors["bg"])
        self.buyer_content.pack(fill="both", expand=True, padx=28, pady=15)

        if mode == "home":
            self.build_home(self.buyer_content)
        elif mode == "tenant":
            self.build_tenants(self.buyer_content)
        elif mode == "cart":
            self.build_cart(self.buyer_content)
        elif mode == "wishlist":
            self.build_wishlist(self.buyer_content)
        elif mode == "orders":
            self.build_orders(self.buyer_content)

    def build_home(self, parent):
        top = self.card(parent, padx=22, pady=20)
        top.pack(fill="x", pady=(0, 15))
        tk.Label(top, text="Mau makan apa hari ini?", font=("Segoe UI", 18, "bold"),
                 bg="white", fg=self.colors["text"]).pack(side="left")
        search = tk.Entry(top, font=("Segoe UI", 11), width=35, relief="solid", bd=1)
        search.pack(side="right", ipady=8, padx=8)

        area = tk.Frame(parent, bg=self.colors["bg"])
        area.pack(fill="both", expand=True)

        left = tk.Frame(area, bg=self.colors["bg"])
        left.pack(side="left", fill="both", expand=True)
        tk.Label(left, text="Promo & Rekomendasi", font=("Segoe UI", 16, "bold"),
                 bg=self.colors["bg"], fg=self.colors["text"]).pack(anchor="w", pady=(0, 10))

        promo = self.card(left, padx=20, pady=18)
        promo.pack(fill="x", pady=(0, 18))
        tk.Label(promo, text="🔥 WEEKDAY LUNCH", font=("Segoe UI", 11, "bold"),
                 fg=self.colors["blue"], bg="white").pack(anchor="w")
        tk.Label(promo, text="Upgrade King Size dan pilih add-ons favoritmu.",
                 font=("Segoe UI", 14, "bold"), fg=self.colors["text"], bg="white").pack(anchor="w", pady=5)
        tk.Label(promo, text="Stok selalu dicek saat item dimasukkan ke keranjang dan checkout.",
                 font=("Segoe UI", 9), fg=self.colors["muted"], bg="white").pack(anchor="w")

        grid = tk.Frame(left, bg=self.colors["bg"])
        grid.pack(fill="both", expand=True)

        products = self.db.get_products()[:6]
        for i, product in enumerate(products):
            self.product_card(grid, product, i % 3, i // 3)

        search.bind("<KeyRelease>", lambda e: self.filter_products(grid, search.get()))

        right = self.card(area, padx=18, pady=18)
        right.pack(side="right", fill="y", padx=(18, 0))
        tk.Label(right, text="Tenant", font=("Segoe UI", 14, "bold"),
                 bg="white", fg=self.colors["text"]).pack(anchor="w")
        tenants = sorted(set(p.tenant for p in self.db.get_products()))
        for t in tenants:
            tk.Button(right, text=t, command=lambda x=t: self.show_tenant_products(x),
                      anchor="w", bg="white", fg=self.colors["text"], relief="flat",
                      padx=8, pady=9, cursor="hand2").pack(fill="x", pady=2)

    def filter_products(self, grid, query):
        for w in grid.winfo_children():
            w.destroy()
        q = query.lower()
        products = [p for p in self.db.get_products() if q in p.name.lower() or q in p.tenant.lower() or q in p.category.lower()]
        for i, product in enumerate(products):
            self.product_card(grid, product, i % 3, i // 3)

    def product_card(self, parent, product, col, row):
        c = self.card(parent, padx=14, pady=14)
        c.grid(row=row, column=col, padx=7, pady=7, sticky="nsew")
        for i in range(3):
            parent.grid_columnconfigure(i, weight=1)

        # Header card: Kategori + Tombol Heart Wishlist
        top_bar = tk.Frame(c, bg="white")
        top_bar.pack(fill="x")
        
        tk.Label(top_bar, text=product.category.upper(), bg="white", fg=self.colors["blue"],
                 font=("Segoe UI", 8, "bold")).pack(side="left")

        # Cek apakah buyer login & produk ada di wishlist
        is_fav = False
        if self.buyer and hasattr(self.buyer, "wishlist") and self.buyer.wishlist is not None:
            is_fav = product.id in self.buyer.wishlist

        heart_icon = "♥" if is_fav else "♡"
        heart_fg = "#DC4C4C" if is_fav else "#9CA3AF"
        heart_active_fg = "#B91C1C" if is_fav else "#4B5563"

        heart_btn = tk.Button(top_bar, text=heart_icon, bg="white", fg=heart_fg,
                              activebackground="white", activeforeground=heart_active_fg,
                              relief="flat", bd=0, font=("Segoe UI", 13, "bold"), cursor="hand2")
        heart_btn.pack(side="right")

        def toggle_wishlist():
            if not self.buyer:
                messagebox.showwarning("Login", "Silakan login sebagai Pembeli terlebih dahulu.")
                return
            if not hasattr(self.buyer, "wishlist") or self.buyer.wishlist is None:
                self.buyer.wishlist = []
            
            if product.id in self.buyer.wishlist:
                self.buyer.wishlist.remove(product.id)
                heart_btn.config(text="♡", fg="#9CA3AF", activeforeground="#4B5563")
                messagebox.showinfo("Wishlist", f"'{product.name}' dihapus dari wishlist.")
            else:
                self.buyer.wishlist.append(product.id)
                heart_btn.config(text="♥", fg="#DC4C4C", activeforeground="#B91C1C")
                messagebox.showinfo("Wishlist", f"'{product.name}' berhasil ditambahkan ke wishlist!")

            # Simpan perubahan wishlist ke database JSON
            if hasattr(self, "db") and self.db and hasattr(self.buyer, "user_id"):
                self.db.update_user_wishlist(self.buyer.user_id, self.buyer.wishlist)

        heart_btn.config(command=toggle_wishlist)

        tk.Label(c, text=product.name, bg="white", fg=self.colors["text"],
                 font=("Segoe UI", 12, "bold"), wraplength=180).pack(anchor="w", pady=(5, 2))
        tk.Label(c, text=product.tenant, bg="white", fg=self.colors["muted"],
                 font=("Segoe UI", 9)).pack(anchor="w")
        tk.Label(c, text=f"Rp{product.price:,}".replace(",", "."),
                 bg="white", fg=self.colors["text"], font=("Segoe UI", 11, "bold")).pack(anchor="w", pady=6)
        stock_text = f"Stok {product.stock}" if product.available else "HABIS"
        stock_color = self.colors["green"] if product.available else self.colors["red"]
        tk.Label(c, text=stock_text, bg="white", fg=stock_color,
                 font=("Segoe UI", 9, "bold")).pack(anchor="w")
        btn = self.button(c, "Tambah ke Keranjang", lambda p=product: self.open_product(p),
                          primary=product.available)
        btn.pack(fill="x", pady=(9, 0))
        if not product.available:
            btn.config(state="disabled")

    def open_product(self, product):
        if product.stock <= 0:
            messagebox.showwarning("Stok habis", "Produk ini sedang habis.")
            return
        win = tk.Toplevel(self)
        win.title(product.name)
        win.geometry("460x630")
        win.configure(bg=self.colors["bg"])
        tk.Label(win, text=product.name, font=("Segoe UI", 18, "bold"),
                 bg=self.colors["bg"], fg=self.colors["text"]).pack(pady=(20, 4))
        tk.Label(win, text=product.description, wraplength=360, bg=self.colors["bg"],
                 fg=self.colors["muted"]).pack(pady=3)

        form = self.card(win, padx=24, pady=20)
        form.pack(fill="both", expand=True, padx=25, pady=15)

        king = tk.BooleanVar(value=False)
        if product.king_price and product.king_price > product.price:
            extra = product.king_price - product.price
            tk.Checkbutton(form, text=f"King Size (+Rp{extra:,})".replace(",", "."),
                           variable=king, bg="white", anchor="w").pack(fill="x", pady=4)

        tk.Label(form, text="Add-ons / Saus", bg="white", font=("Segoe UI", 10, "bold")).pack(anchor="w", pady=(8, 3))
        addon_vars = []
        for addon in product.addons:
            v = tk.BooleanVar()
            addon_vars.append((addon, v))
            tk.Checkbutton(form, text=f'{addon["name"]} (+Rp{addon["price"]:,})'.replace(",", "."),
                           variable=v, bg="white", anchor="w").pack(fill="x")

        # Catatan / Notes Textbox
        tk.Label(form, text="Catatan Khusus (Notes)", bg="white", font=("Segoe UI", 10, "bold")).pack(anchor="w", pady=(10, 2))
        notes_entry = tk.Entry(form, font=("Segoe UI", 10), relief="solid", bd=1)
        notes_entry.pack(fill="x", pady=(0, 2), ipady=4)
        tk.Label(form, text="Contoh: Pedas sedang, tanpa bawang, dsb.", bg="white", fg=self.colors["muted"], font=("Segoe UI", 8)).pack(anchor="w", pady=(0, 6))

        tk.Label(form, text="Jumlah", bg="white", font=("Segoe UI", 10, "bold")).pack(anchor="w", pady=(6, 2))
        qty = tk.Spinbox(form, from_=1, to=product.stock, width=8, font=("Segoe UI", 10))
        qty.pack(anchor="w")

        def add():
            try:
                q = int(qty.get())
                if q < 1 or q > product.stock:
                    raise ValueError
            except ValueError:
                messagebox.showerror("Jumlah tidak valid", "Jumlah harus sesuai stok yang tersedia.")
                return
            selected = [a for a, v in addon_vars if v.get()]
            unit = product.final_price(king.get(), selected)
            notes_text = notes_entry.get().strip()
            self.buyer.cart.append({
                "product_id": product.id, "name": product.name, "tenant": product.tenant,
                "quantity": q, "unit_price": unit, "king_size": king.get(), "addons": selected,
                "notes": notes_text
            })
            win.destroy()
            messagebox.showinfo("Keranjang", "Produk berhasil ditambahkan ke keranjang.")

        self.button(form, "Tambah ke Keranjang", add).pack(fill="x", pady=15)

    def buyer_tenants(self):
        self._buyer_content("tenant")

    def build_tenants(self, parent):
        tk.Label(parent, text="Daftar Tenant", font=("Segoe UI", 19, "bold"),
                 bg=self.colors["bg"], fg=self.colors["text"]).pack(anchor="w")
        tk.Label(parent, text="Pilih tenant untuk melihat menu yang tersedia.",
                 bg=self.colors["bg"], fg=self.colors["muted"]).pack(anchor="w", pady=(3, 18))
        for tenant in sorted(set(p.tenant for p in self.db.get_products())):
            c = self.card(parent, padx=20, pady=15)
            c.pack(fill="x", pady=6)
            count = len([p for p in self.db.get_products() if p.tenant == tenant])
            tk.Label(c, text=tenant, font=("Segoe UI", 13, "bold"), bg="white").pack(side="left")
            tk.Label(c, text=f"{count} menu", fg=self.colors["muted"], bg="white").pack(side="left", padx=15)
            self.button(c, "Lihat Menu", lambda t=tenant: self.show_tenant_products(t)).pack(side="right")

    def show_tenant_products(self, tenant):
        self._buyer_content("tenant")
        # Replace content with tenant detail
        for w in self.buyer_content.winfo_children():
            w.destroy()
        tk.Label(self.buyer_content, text=tenant, font=("Segoe UI", 20, "bold"),
                 bg=self.colors["bg"], fg=self.colors["text"]).pack(anchor="w")
        grid = tk.Frame(self.buyer_content, bg=self.colors["bg"])
        grid.pack(fill="both", expand=True, pady=15)
        products = [p for p in self.db.get_products() if p.tenant == tenant]
        for i, p in enumerate(products):
            self.product_card(grid, p, i % 3, i // 3)

    def buyer_cart(self):
        self._buyer_content("cart")

    def build_cart(self, parent):
        tk.Label(parent, text="Keranjang", font=("Segoe UI", 19, "bold"),
                 bg=self.colors["bg"], fg=self.colors["text"]).pack(anchor="w", pady=(0, 15))
        if not self.buyer.cart:
            self.card(parent).pack(fill="x")
            tk.Label(parent.winfo_children()[-1], text="Keranjang masih kosong.",
                     bg="white", fg=self.colors["muted"]).pack()
            return

        total = 0
        for i, item in enumerate(self.buyer.cart):
            c = self.card(parent, padx=15, pady=12)
            c.pack(fill="x", pady=5)
            subtotal = item["quantity"] * item["unit_price"]
            total += subtotal
            
            left_info = tk.Frame(c, bg="white")
            left_info.pack(side="left", fill="both")
            tk.Label(left_info, text=f'{item["name"]} × {item["quantity"]}',
                     bg="white", font=("Segoe UI", 11, "bold")).pack(anchor="w")
            if item.get("notes"):
                tk.Label(left_info, text=f'📝 Catatan: {item["notes"]}',
                         bg="white", fg=self.colors["blue"], font=("Segoe UI", 9, "italic")).pack(anchor="w", pady=(2, 0))

            tk.Label(c, text=f'Rp{subtotal:,}'.replace(",", "."),
                     bg="white", fg=self.colors["text"]).pack(side="right")
            self.button(c, "Bayar Produk Ini", lambda item=item: self.checkout(item=item), primary=True).pack(side="right", padx=8)
            tk.Button(c, text="Hapus", command=lambda idx=i: self.remove_cart(idx),
                      bg="white", fg=self.colors["red"], relief="flat").pack(side="right", padx=15)

        bottom = self.card(parent, padx=18, pady=15)
        bottom.pack(fill="x", pady=15)
        tk.Label(bottom, text=f"Total: Rp{total:,}".replace(",", "."),
                 font=("Segoe UI", 15, "bold"), bg="white").pack(side="left")
        self.button(bottom, "Checkout", self.checkout).pack(side="right")

    def remove_cart(self, idx):
        del self.buyer.cart[idx]
        self.buyer_cart()

    def remove_cart_from_tenant(self, idx, tenant):
        tenant_items = [item for item in self.buyer.cart if item["tenant"] == tenant]
        if idx < 0 or idx >= len(tenant_items):
            return

        target = tenant_items[idx]
        self.buyer.cart = [item for item in self.buyer.cart if id(item) != id(target)]
        self.buyer_cart()

    def checkout(self, tenant=None, item=None):
        if not self.buyer.cart:
            return

        if item is not None:
            selected_items = [item]
        elif tenant is not None:
            selected_items = [i for i in self.buyer.cart if i["tenant"] == tenant]
        else:
            selected_items = list(self.buyer.cart)

        if not selected_items:
            return

        for item_entry in selected_items:
            p = self.db.get_product(item_entry["product_id"])
            if not p or p.stock < item_entry["quantity"]:
                messagebox.showerror("Stok berubah", f"Stok {item_entry['name']} tidak mencukupi. Keranjang perlu diperbarui.")
                self.buyer_cart()
                return

        missing_qr = sorted({item_entry["tenant"] for item_entry in selected_items
                             if not self.db.get_tenant_qr(item_entry["tenant"])})
        if missing_qr:
            messagebox.showwarning(
                "QR belum tersedia",
                "Maaf, seller belum upload qr code nih, produk belum bisa dibeli.\n\n"
                + "Tenant: " + ", ".join(missing_qr)
            )
            return

        total = sum(i["quantity"] * i["unit_price"] for i in selected_items)
        if not messagebox.askyesno("Konfirmasi", f"Konfirmasi pesanan dengan total Rp{total:,}?".replace(",", ".")):
            return

        grouped_items = {}
        for item_entry in selected_items:
            grouped_items.setdefault(item_entry["tenant"], []).append(item_entry)

        created_orders = []
        for tenant_name in sorted(grouped_items):
            tenant_items = grouped_items[tenant_name]
            tenant_total = sum(i["quantity"] * i["unit_price"] for i in tenant_items)
            deadline = datetime.now() + timedelta(minutes=15)
            order = Order(
                order_id=f"ORD-{datetime.now().strftime('%Y%m%d%H%M%S')}-{random.randint(10,99)}",
                buyer_id=self.buyer.user_id,
                buyer_name=self.buyer.name,
                items=tenant_items.copy(),
                total=tenant_total,
                queue_number=self.db.next_queue(),
                status="Menunggu Pembayaran",
                payment_status="UNPAID",
                created_at=datetime.now().strftime("%d/%m/%Y %H:%M"),
                payment_deadline=deadline.strftime("%Y-%m-%d %H:%M:%S"),
                tenant_payments=[{
                    "tenant": tenant_name,
                    "amount": tenant_total,
                    "qr_path": self.db.get_tenant_qr(tenant_name),
                    "proof_path": "",
                    "status": "UNPAID",
                    "submitted_at": "",
                }],
            )
            self.db.add_order(order)
            self.after(15 * 60 * 1000, lambda oid=order.order_id: self._scheduled_payment_expiration(oid))
            created_orders.append(order)

        self.pending_checkout_orders = [
            next((o for o in self.db.get_orders() if o["order_id"] == order.order_id), None)
            for order in created_orders
            if next((o for o in self.db.get_orders() if o["order_id"] == order.order_id), None)
        ]

        selected_item_ids = {id(item_entry) for item_entry in selected_items}
        self.buyer.cart = [item_entry for item_entry in self.buyer.cart if id(item_entry) not in selected_item_ids]
        self.buyer_cart()
        if self.pending_checkout_orders:
            self.show_payment(self.pending_checkout_orders[0])

    def _scheduled_payment_expiration(self, order_id):
        order = next((o for o in self.db.get_orders() if o["order_id"] == order_id), None)
        if order:
            self.expire_payment_if_needed(order)

    def show_payment(self, order):
        order_id = order["order_id"] if isinstance(order, dict) else order.order_id
        persisted_order = next((o for o in self.db.get_orders() if o["order_id"] == order_id), None)
        if persisted_order:
            order = persisted_order

        pending_orders = getattr(self, "pending_checkout_orders", []) or []
        checkout_orders = []
        for pending_order in pending_orders:
            if isinstance(pending_order, dict):
                pending_order_id = pending_order.get("order_id")
            else:
                pending_order_id = pending_order
            matched = next((o for o in self.db.get_orders() if o["order_id"] == pending_order_id), None)
            if matched:
                checkout_orders.append(matched)

        if not checkout_orders:
            checkout_orders = [order]

        if order_id not in {o["order_id"] for o in checkout_orders}:
            order = checkout_orders[0]
            order_id = order["order_id"]

        self.expire_payment_if_needed(order)
        self.clear()
        self.header(self, "Pembayaran per Tenant", "Upload bukti pembayaran maksimal 15 menit")

        nav = tk.Frame(self, bg=self.colors["bg"])
        nav.pack(fill="x", padx=28, pady=(0, 10))
        for checkout_order in checkout_orders:
            tenant_name = checkout_order.get("tenant_payments", [{}])[0].get("tenant", checkout_order["order_id"])
            btn = self.button(nav, f"{tenant_name} ({checkout_order['order_id']})",
                              lambda oid=checkout_order["order_id"]: self.show_payment(oid),
                              primary=(checkout_order["order_id"] == order_id))
            btn.pack(side="left", padx=4)

        order = next((o for o in self.db.get_orders() if o["order_id"] == order_id), None) or order
        deadline = order.get("payment_deadline", "")
        timer_label = tk.Label(self, text="", font=("Segoe UI", 13, "bold"),
                               bg=self.colors["bg"], fg=self.colors["orange"])
        timer_label.pack(anchor="w", padx=28, pady=(3, 0))
        tk.Label(self, text=f"Order {order_id}  •  Batas waktu: {deadline}",
                 bg=self.colors["bg"], fg=self.colors["muted"]).pack(anchor="w", padx=28)
        body = tk.Frame(self, bg=self.colors["bg"])
        body.pack(fill="both", expand=True, padx=28, pady=15)

        payments = order.get("tenant_payments", []) if isinstance(order, dict) else order.tenant_payments
        for payment in payments:
            card = self.card(body, padx=20, pady=16)
            card.pack(fill="x", pady=6)
            tenant = payment["tenant"]
            tk.Label(card, text=tenant, font=("Segoe UI", 14, "bold"), bg="white", fg=self.colors["text"]).pack(anchor="w")
            tk.Label(card, text=f"Nominal Rp{payment['amount']:,}".replace(",", "."), bg="white", fg=self.colors["muted"]).pack(anchor="w")
            qr_path = payment.get("qr_path") or self.db.get_tenant_qr(tenant)
            status_label = tk.Label(card, text=f"Status: {payment.get('status', 'UNPAID')}", bg="white", fg=self.colors["muted"])
            status_label.pack(anchor="w")

            if qr_path:
                self.button(card, "LIHAT QR", lambda p=qr_path, t=tenant: self.show_image_popup(p, f"QR {t}")).pack(anchor="w", pady=(8, 0))
            else:
                tk.Label(card, text="Maaf, seller belum upload qr code nih, produk belum bisa dibeli",
                         bg="white", fg=self.colors["red"], wraplength=850, justify="left").pack(anchor="w", pady=5)

            def upload(target=payment, label=status_label):
                self.upload_payment_proof(order_id, target["tenant"], label)

            tk.Label(card, text="HANYA MENDUKUNG FORMAT PNG", bg="white", fg=self.colors["red"], font=("Segoe UI", 9, "bold")).pack(anchor="w", pady=(8, 0))
            self.button(card, "Upload Bukti Pembayaran", upload).pack(anchor="w", pady=(8, 0))

        self.update_payment_timer(order_id, timer_label)
        self.button(self, "Selesai / Lihat Pesanan", lambda: self.show_order_detail(order_id), primary=False).pack(pady=12)

    def show_image_popup(self, path, title="Preview Gambar"):
        if not path or not os.path.exists(path):
            messagebox.showwarning("Preview", "File gambar tidak ditemukan.")
            return

        win = tk.Toplevel(self)
        win.title(title)
        win.geometry("440x420")
        win.configure(bg=self.colors["bg"])
        win.transient(self)
        win.grab_set()

        image = self.load_qr_image(path, 320)
        if image:
            self.qr_image_refs.append(image)
            tk.Label(win, image=image, bg="white").pack(padx=20, pady=20)
        else:
            tk.Label(win, text="HANYA MENDUKUNG FORMAT PNG.",
                     bg=self.colors["bg"], fg=self.colors["text"], font=("Segoe UI", 11), justify="center").pack(padx=20, pady=20)

    def update_payment_timer(self, order_id, timer_label):
        order = next((o for o in self.db.get_orders() if o["order_id"] == order_id), None)
        if not order or not timer_label.winfo_exists():
            return
        try:
            remaining = max(0, int((datetime.strptime(order["payment_deadline"], "%Y-%m-%d %H:%M:%S") - datetime.now()).total_seconds()))
        except (KeyError, ValueError):
            remaining = 0
        if remaining <= 0:
            timer_label.config(text="Waktu pembayaran habis", fg=self.colors["red"])
            if self.expire_payment_if_needed(order):
                messagebox.showwarning("Pesanan dibatalkan", "Batas waktu 15 menit telah habis. Pesanan otomatis dibatalkan.")
            return
        minutes, seconds = divmod(remaining, 60)
        timer_label.config(text=f"Sisa waktu upload bukti: {minutes:02d}:{seconds:02d}")
        self.payment_timer_job = self.after(1000, lambda: self.update_payment_timer(order_id, timer_label))

    def expire_payment_if_needed(self, order):
        deadline = order.get("payment_deadline", "")
        if not deadline or order.get("status") in ("Selesai", "Dibatalkan", "Pembayaran Ditolak"):
            return False
        try:
            expired = datetime.now() >= datetime.strptime(deadline, "%Y-%m-%d %H:%M:%S")
        except ValueError:
            return False
        pending_upload = any(p.get("status") == "UNPAID" for p in order.get("tenant_payments", []))
        if expired and pending_upload:
            for payment in order.get("tenant_payments", []):
                if payment.get("status") in ("UNPAID", "SUBMITTED"):
                    payment["status"] = "EXPIRED"
            self.db.update_order(order["order_id"], status="Dibatalkan", payment_status="EXPIRED",
                                 tenant_payments=order.get("tenant_payments", []))
            return True
        return False

    def upload_payment_proof(self, order_id, tenant, status_label=None):
        order = next((o for o in self.db.get_orders() if o["order_id"] == order_id), None)
        if not order or self.expire_payment_if_needed(order):
            messagebox.showwarning("Batas waktu", "Waktu pembayaran 15 menit telah habis. Pesanan dibatalkan.")
            self.show_order_detail(order_id)
            return
        source = filedialog.askopenfilename(title="Pilih bukti pembayaran (PNG)",
                                            filetypes=[("Gambar PNG", "*.png"), ("Semua file", "*.*")])
        if not source:
            return
        source_ext = os.path.splitext(source)[1].lower()
        if source_ext != ".png":
            messagebox.showwarning("Format file", "HANYA MENDUKUNG FORMAT PNG.")
            return
        os.makedirs("payment_proofs", exist_ok=True)
        target = os.path.join("payment_proofs", f"{order_id}_{tenant.replace(' ', '_')}{source_ext}")
        shutil.copy2(source, target)
        for payment in order.get("tenant_payments", []):
            if payment["tenant"] == tenant:
                payment.update(proof_path=target, status="SUBMITTED", submitted_at=datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
        payment_status = "SUBMITTED" if all(p.get("status") == "SUBMITTED" for p in order.get("tenant_payments", [])) else "PARTIAL"
        self.db.update_order(order_id, payment_status=payment_status, status="Menunggu Konfirmasi Penjual",
                             tenant_payments=order.get("tenant_payments", []))
        if status_label:
            status_label.config(text="Status: SUBMITTED")
        messagebox.showinfo("Bukti pembayaran", "Bukti pembayaran berhasil diunggah dan menunggu verifikasi seller.")

    def draw_fake_qr(self, canvas, seed):
        rng = random.Random(seed)
        n = 21
        size = 10
        for y in range(n):
            for x in range(n):
                if rng.random() > 0.5:
                    canvas.create_rectangle(x*size+15, y*size+15, x*size+size+15, y*size+size+15, fill="black", outline="")
        for ox, oy in [(0,0),(14,0),(0,14)]:
            for y in range(7):
                for x in range(7):
                    if x in (0,6) or y in (0,6) or (2 <= x <= 4 and 2 <= y <= 4):
                        canvas.create_rectangle((x+ox)*size+15,(y+oy)*size+15,
                                                (x+ox+1)*size+15,(y+oy+1)*size+15, fill="black", outline="")

    def buyer_wishlist(self):
        self._buyer_content("wishlist")

    def build_wishlist(self, parent):
        tk.Label(parent, text="Wishlist / Menu Favorit", font=("Segoe UI", 19, "bold"),
                 bg=self.colors["bg"], fg=self.colors["text"]).pack(anchor="w")
        tk.Label(parent, text="Simpan menu favorit kamu dengan menekan tombol hati ❤️ pada kartu produk.",
                 bg=self.colors["bg"], fg=self.colors["muted"]).pack(anchor="w", pady=(2, 15))

        if getattr(self.buyer, "wishlist", None) is None:
            self.buyer.wishlist = ["P001", "P006"]

        valid_wishlist = [pid for pid in self.buyer.wishlist if self.db.get_product(pid) is not None]

        if not valid_wishlist:
            c = self.card(parent, padx=20, pady=25)
            c.pack(fill="x", pady=10)
            tk.Label(c, text="🤍 Wishlist kamu masih kosong.", font=("Segoe UI", 12, "bold"),
                     bg="white", fg=self.colors["text"]).pack()
            tk.Label(c, text="Jelajahi Beranda dan tekan tombol hati ❤️ pada menu makanan favoritmu untuk menyimpannya di sini!",
                     font=("Segoe UI", 10), bg="white", fg=self.colors["muted"]).pack(pady=5)
            return

        for pid in list(valid_wishlist):
            p = self.db.get_product(pid)
            if p:
                c = self.card(parent, padx=18, pady=14)
                c.pack(fill="x", pady=5)
                
                left_frame = tk.Frame(c, bg="white")
                left_frame.pack(side="left")
                
                tk.Label(left_frame, text=p.name, bg="white", font=("Segoe UI", 12, "bold")).pack(anchor="w")
                tk.Label(left_frame, text=f"{p.tenant}  •  Rp{p.price:,}".replace(",", "."),
                         bg="white", fg=self.colors["muted"], font=("Segoe UI", 9)).pack(anchor="w", pady=(2, 0))
                
                btn_frame = tk.Frame(c, bg="white")
                btn_frame.pack(side="right")
                
                def remove_fav(target_p=p):
                    if target_p.id in self.buyer.wishlist:
                        self.buyer.wishlist.remove(target_p.id)
                        if hasattr(self, "db") and self.db and hasattr(self.buyer, "user_id"):
                            self.db.update_user_wishlist(self.buyer.user_id, self.buyer.wishlist)
                        messagebox.showinfo("Wishlist", f"'{target_p.name}' dihapus dari wishlist.")
                        self.buyer_wishlist()
                
                self.button(btn_frame, "🗑 Hapus", lambda tp=p: remove_fav(tp), primary=False).pack(side="right", padx=5)
                self.button(btn_frame, "🛒 Pesan Sekarang", lambda tp=p: self.open_product(tp)).pack(side="right", padx=5)

    def buyer_orders(self):
        self._buyer_content("orders")

    def build_orders(self, parent):
        tk.Label(parent, text="Pesanan Saya", font=("Segoe UI", 19, "bold"),
                 bg=self.colors["bg"], fg=self.colors["text"]).pack(anchor="w", pady=(0, 15))
        orders = [o for o in self.db.get_orders() if o["buyer_id"] == self.buyer.user_id]
        for order in orders:
            self.expire_payment_if_needed(order)
        if not orders:
            tk.Label(parent, text="Belum ada pesanan.", bg=self.colors["bg"],
                     fg=self.colors["muted"]).pack(anchor="w")
            return
        for o in reversed(orders):
            c = self.card(parent, padx=18, pady=14)
            c.pack(fill="x", pady=6)
            tk.Label(c, text=o["order_id"], bg="white", font=("Segoe UI", 11, "bold")).pack(anchor="w")
            tk.Label(c, text=f'Antrean #{o["queue_number"]}  •  {o["status"]}',
                     bg="white", fg=self.colors["blue"]).pack(anchor="w", pady=4)
            tk.Label(c, text=f'Total Rp{o["total"]:,}  •  {o["payment_status"]}'.replace(",", "."),
                     bg="white", fg=self.colors["muted"]).pack(anchor="w")
            self.button(c, "Detail & Tracking", lambda oid=o["order_id"]: self.show_order_detail(oid)).pack(anchor="e", pady=(5,0))

    def show_order_detail(self, order_id):
        order = next((o for o in self.db.get_orders() if o["order_id"] == order_id), None)
        if not order:
            messagebox.showerror("Order", "Pesanan tidak ditemukan.")
            return
        self.expire_payment_if_needed(order)
        self.clear()
        self.header(self, "Order Tracking", order["order_id"])
        c = self.card(self, padx=30, pady=25)
        c.pack(fill="x", padx=28, pady=15)
        tk.Label(c, text=f"Nomor Antrean  #{order['queue_number']}", font=("Segoe UI", 22, "bold"),
                 bg="white", fg=self.colors["blue"]).pack(anchor="w")
        tk.Label(c, text=f"Total Rp{order['total']:,}".replace(",", "."),
                 bg="white", font=("Segoe UI", 13, "bold")).pack(anchor="w", pady=4)
        tk.Label(c, text=f"Reminder: {order.get('pickup_reminder','Belum ada pengingat')}",
                 bg="white", fg=self.colors["muted"]).pack(anchor="w", pady=(0, 10))
        if order.get("payment_deadline"):
            tk.Label(c, text=f"Batas upload bukti: {order['payment_deadline']}",
                     bg="white", fg=self.colors["orange"]).pack(anchor="w", pady=(0, 8))
        for payment in order.get("tenant_payments", []):
            payment_row = tk.Frame(c, bg="white")
            payment_row.pack(fill="x", pady=2)
            tk.Label(payment_row, text=f"{payment['tenant']}: {payment.get('status', 'UNPAID')} • Rp{payment['amount']:,}".replace(",", "."),
                     bg="white", fg=self.colors["text"]).pack(side="left")
            if payment.get("proof_path"):
                self.button(payment_row, "LIHAT BUKTI BAYAR", lambda p=payment: self.show_image_popup(p.get("proof_path"), f"Bukti Bayar {p.get('tenant', '')}")).pack(side="right", padx=4)
            if payment.get("status") == "UNPAID" and order.get("status") != "Dibatalkan":
                self.button(payment_row, "Upload Bukti", lambda p=payment: self.upload_payment_proof(order_id, p["tenant"])).pack(side="right", padx=4)

        # Rincian item & catatan
        tk.Label(c, text="Rincian Item Dipesan:", font=("Segoe UI", 10, "bold"), bg="white", fg=self.colors["text"]).pack(anchor="w")
        for item in order.get("items", []):
            item_name = item.get("name") or item.get("product_name") or "Produk"
            line_str = f"• {item_name} × {item['quantity']}"
            if item.get("king_size"): line_str += " (King Size)"
            tk.Label(c, text=line_str, font=("Segoe UI", 10), bg="white", fg=self.colors["text"]).pack(anchor="w", padx=10)
            if item.get("notes"):
                tk.Label(c, text=f"   📝 Catatan: {item['notes']}", font=("Segoe UI", 9, "italic"), bg="white", fg=self.colors["blue"]).pack(anchor="w", padx=10)

        steps = ["Menunggu Pembayaran", "Menunggu Konfirmasi Penjual", "Sedang Diproses", "Siap Diambil"]
        status = order["status"]
        try:
            current = steps.index(status)
        except ValueError:
            current = 1 if order["payment_status"] == "PAID" else 0
        for i, step in enumerate(steps):
            row = tk.Frame(self, bg=self.colors["bg"])
            row.pack(fill="x", padx=50, pady=8)
            mark = "●" if i <= current else "○"
            fg = self.colors["green"] if i <= current else self.colors["muted"]
            tk.Label(row, text=mark, font=("Segoe UI", 18), fg=fg, bg=self.colors["bg"]).pack(side="left")
            tk.Label(row, text=step, font=("Segoe UI", 12, "bold" if i == current else "normal"),
                     fg=self.colors["text"] if i <= current else self.colors["muted"],
                     bg=self.colors["bg"]).pack(side="left", padx=12)

        reminder = tk.Frame(self, bg=self.colors["bg"])
        reminder.pack(pady=18)
        self.button(reminder, "🔔 Ingatkan Saya", lambda: self.set_reminder(order_id)).pack(side="left", padx=5)
        if order.get("status") == "Menunggu Pembayaran":
            self.button(reminder, "BATALKAN PESANAN", lambda: self.cancel_order(order_id), primary=False).pack(side="left", padx=5)
        self.button(reminder, "← Kembali ke Pesanan", self.show_buyer, primary=False).pack(side="left", padx=5)

    def cancel_order(self, order_id):
        order = next((o for o in self.db.get_orders() if o["order_id"] == order_id), None)
        if not order:
            messagebox.showerror("Order", "Pesanan tidak ditemukan.")
            return
        if order.get("status") != "Menunggu Pembayaran":
            messagebox.showwarning("Pembatalan", "Pesanan ini tidak dapat dibatalkan karena status sudah berubah.")
            return
        if not messagebox.askyesno("Konfirmasi", "Apakah kamu yakin ingin membatalkan pesanan ini?"):
            return
        for payment in order.get("tenant_payments", []):
            payment["status"] = "CANCELED"
            payment["proof_path"] = payment.get("proof_path", "")
        self.db.update_order(order_id, status="Dibatalkan", payment_status="CANCELED",
                             tenant_payments=order.get("tenant_payments", []))
        messagebox.showinfo("Pesanan dibatalkan", "Pesanan telah dibatalkan dan status pembayaran diubah menjadi batal.")
        self.show_buyer()

    def set_reminder(self, order_id):
        text = "Pengingat aktif — cek kembali saat pesanan sudah siap diambil."
        self.db.update_order(order_id, pickup_reminder=text)
        messagebox.showinfo("Reminder", "Notifikasi pengambilan makanan diaktifkan.")
        self.show_order_detail(order_id)

    # ========================================================
    # SELLER UI
    # ========================================================

    def show_seller(self):
        self.clear()
        self.header(self, "Seller Dashboard", f"{self.seller.name} • {self.seller.tenant}")
        nav = tk.Frame(self, bg=self.colors["navy"])
        nav.pack(fill="x")
        for text, cmd in [
            ("📊 Dashboard", self.seller_dashboard),
            ("🍱 Produk", self.seller_products),
            ("🧂 Add-ons", self.seller_addons),
            ("📦 Pesanan", self.seller_orders),
            ("📈 Laporan", self.seller_reports),
        ]:
            tk.Button(nav, text=text, command=cmd, bg=self.colors["navy"], fg="white",
                      activebackground="#293A5E", relief="flat", bd=0, padx=18, pady=15,
                      font=("Segoe UI", 10, "bold"), cursor="hand2").pack(side="left")
        self.button(nav, "Keluar", self.show_entrance, primary=False).pack(side="right", padx=12, pady=7)
        self.seller_dashboard()

    def seller_dashboard(self):
        old = getattr(self, "seller_content", None)
        if old: old.destroy()
        self.seller_content = tk.Frame(self, bg=self.colors["bg"])
        self.seller_content.pack(fill="both", expand=True, padx=28, pady=18)
        orders = self.db.get_orders()
        seller_orders = [o for o in orders if any(i["tenant"] == self.seller.tenant for i in o["items"])]
        pending = [o for o in seller_orders if o["status"] == "Menunggu Konfirmasi Penjual"]
        revenue = sum(self.tenant_payment(o, self.seller.tenant)["amount"]
                  for o in seller_orders
                  if self.tenant_payment(o, self.seller.tenant).get("status") == "PAID")
        stats = tk.Frame(self.seller_content, bg=self.colors["bg"])
        stats.pack(fill="x")
        for title, value in [("Pesanan Masuk", len(pending)), ("Pesanan Selesai", len(seller_orders)),
                             ("Pemasukan", f"Rp{revenue:,}".replace(",", "."))]:
            c = self.card(stats, padx=20, pady=18)
            c.pack(side="left", fill="x", expand=True, padx=5)
            tk.Label(c, text=title, bg="white", fg=self.colors["muted"]).pack(anchor="w")
            tk.Label(c, text=str(value), bg="white", fg=self.colors["text"],
                     font=("Segoe UI", 20, "bold")).pack(anchor="w", pady=(5,0))
        self.seller_qr_panel(self.seller_content)
        self.seller_orders_table(self.seller_content, pending_only=True)

    def seller_qr_panel(self, parent):
        card = self.card(parent, padx=18, pady=14)
        card.pack(fill="x", pady=(15, 8))
        tk.Label(card, text="QR Pembayaran Tenant", font=("Segoe UI", 13, "bold"),
                 bg="white", fg=self.colors["text"]).pack(anchor="w")
        current = self.db.get_tenant_qr(self.seller.tenant)
        text = current or "Belum ada QR yang diunggah."
        qr_label = tk.Label(card, text=text, bg="white", fg=self.colors["muted"], wraplength=800, justify="left")
        qr_label.pack(anchor="w", pady=5)
        tk.Label(card, text="HANYA MENDUKUNG FORMAT PNG", bg="white", fg=self.colors["red"], font=("Segoe UI", 9, "bold")).pack(anchor="w", pady=(0, 4))

        def upload():
            source = filedialog.askopenfilename(title="Pilih QR pembayaran tenant (PNG)",
                                                filetypes=[("Gambar PNG", "*.png"), ("Semua file", "*.*")])
            if not source:
                return
            source_ext = os.path.splitext(source)[1].lower()
            if source_ext != ".png":
                messagebox.showwarning("Format file", "HANYA MENDUKUNG FORMAT PNG.")
                return
            os.makedirs("qr_uploads", exist_ok=True)
            target = os.path.join("qr_uploads", f"{self.seller.user_id}{source_ext}")
            shutil.copy2(source, target)
            self.db.update_seller_qr(self.seller.user_id, target)
            qr_label.config(text=target)
            for order in self.db.get_orders():
                for payment in order.get("tenant_payments", []):
                    if payment.get("tenant") == self.seller.tenant and payment.get("status") == "UNPAID":
                        payment["qr_path"] = target
                self.db.update_order(order["order_id"], tenant_payments=order.get("tenant_payments", []))
            messagebox.showinfo("QR pembayaran", "QR pembayaran tenant berhasil diunggah.")

        row = tk.Frame(card, bg="white")
        row.pack(fill="x", pady=(5, 0))
        self.button(row, "Upload / Ganti QR", upload).pack(side="left")
        if current:
            self.button(row, "LIHAT QR", lambda: self.show_image_popup(current, f"QR {self.seller.tenant}")).pack(side="left", padx=(8, 0))

    def seller_products(self):
        old = getattr(self, "seller_content", None)
        if old: old.destroy()
        self.seller_content = tk.Frame(self, bg=self.colors["bg"])
        self.seller_content.pack(fill="both", expand=True, padx=28, pady=18)
        
        top_bar = tk.Frame(self.seller_content, bg=self.colors["bg"])
        top_bar.pack(fill="x", pady=(0, 10))
        
        title_frame = tk.Frame(top_bar, bg=self.colors["bg"])
        title_frame.pack(side="left")
        tk.Label(title_frame, text="Manajemen Produk", font=("Segoe UI", 19, "bold"),
                 bg=self.colors["bg"], fg=self.colors["text"]).pack(anchor="w")
        tk.Label(title_frame, text="Tambah produk baru, kelola harga, stok, atau hapus menu.",
                 bg=self.colors["bg"], fg=self.colors["muted"]).pack(anchor="w", pady=2)
                 
        self.button(top_bar, "+ Tambah Produk Baru", self.open_add_product_dialog).pack(side="right")

        tree = ttk.Treeview(self.seller_content, columns=("name","price","stock","status"), show="headings")
        for col, label in [("name","Produk"),("price","Harga"),("stock","Stok"),("status","Status")]:
            tree.heading(col, text=label)
            tree.column(col, width=200)
        tree.pack(fill="both", expand=True, pady=10)
        for p in self.db.get_products():
            if p.tenant == self.seller.tenant:
                tree.insert("", "end", iid=p.id, values=(p.name, f"Rp{p.price:,}".replace(",", "."), p.stock,
                                                         "Available" if p.available else "Habis"))
        tools = tk.Frame(self.seller_content, bg=self.colors["bg"])
        tools.pack(fill="x", pady=(5, 0))
        
        tk.Label(tools, text="Set stok:", bg=self.colors["bg"], font=("Segoe UI", 10)).pack(side="left", padx=(0, 5))
        qty = tk.Spinbox(tools, from_=0, to=999, width=8, font=("Segoe UI", 10))
        qty.pack(side="left")
        
        def update():
            sel = tree.selection()
            if not sel:
                messagebox.showwarning("Produk", "Pilih produk terlebih dahulu dari tabel.")
                return
            try: n = int(qty.get())
            except ValueError:
                return
            self.db.update_product_stock(sel[0], n)
            self.seller_products()
            
        def delete_prod():
            sel = tree.selection()
            if not sel:
                messagebox.showwarning("Hapus Produk", "Pilih produk yang ingin dihapus dari tabel.")
                return
            product_id = sel[0]
            product = self.db.get_product(product_id)
            if not product:
                return
            if messagebox.askyesno("Konfirmasi Hapus", f"Apakah Anda yakin ingin menghapus produk '{product.name}' dari database?"):
                self.db.delete_product(product_id)
                messagebox.showinfo("Berhasil", f"Produk '{product.name}' telah berhasil dihapus.")
                self.seller_products()

        self.button(tools, "Update Stok", update).pack(side="left", padx=8)
        self.button(tools, "🗑 Hapus Produk", delete_prod, primary=False).pack(side="left", padx=8)

    def open_add_product_dialog(self):
        win = tk.Toplevel(self)
        win.title("Tambah Produk Baru")
        win.geometry("480x620")
        win.configure(bg=self.colors["bg"])
        win.transient(self)
        win.grab_set()

        tk.Label(win, text="Tambah Produk Baru", font=("Segoe UI", 16, "bold"),
                 bg=self.colors["bg"], fg=self.colors["text"]).pack(pady=(20, 5))
        tk.Label(win, text=f"Tenant: {self.seller.tenant}", font=("Segoe UI", 10),
                 bg=self.colors["bg"], fg=self.colors["muted"]).pack(pady=(0, 10))

        form = self.card(win, padx=24, pady=20)
        form.pack(fill="both", expand=True, padx=25, pady=(0, 20))

        # Nama Produk
        tk.Label(form, text="Nama Produk *", bg="white", fg=self.colors["text"],
                 font=("Segoe UI", 10, "bold")).pack(anchor="w")
        name_entry = tk.Entry(form, font=("Segoe UI", 10), relief="solid", bd=1)
        name_entry.pack(fill="x", pady=(3, 10), ipady=4)

        # Kategori
        tk.Label(form, text="Kategori *", bg="white", fg=self.colors["text"],
                 font=("Segoe UI", 10, "bold")).pack(anchor="w")
        cat_cb = ttk.Combobox(form, values=["Rice Bowl", "Snack", "Minuman", "Makanan Berat", "Lainnya"],
                              font=("Segoe UI", 10), state="readonly")
        cat_cb.set("Rice Bowl")
        cat_cb.pack(fill="x", pady=(3, 10))

        # Harga Produk
        tk.Label(form, text="Harga Produk (Rp) *", bg="white", fg=self.colors["text"],
                 font=("Segoe UI", 10, "bold")).pack(anchor="w")
        price_entry = tk.Entry(form, font=("Segoe UI", 10), relief="solid", bd=1)
        price_entry.pack(fill="x", pady=(3, 10), ipady=4)

        # Harga King Size (opsional)
        tk.Label(form, text="Harga King Size (Rp) (Opsional)", bg="white", fg=self.colors["text"],
                 font=("Segoe UI", 10, "bold")).pack(anchor="w")
        tk.Label(form, text="Isi tambahan harga (contoh: 3000) ATAU total harga King Size (contoh: 18000). Isi 0 jika tidak ada.",
                 bg="white", fg=self.colors["muted"], font=("Segoe UI", 8)).pack(anchor="w", pady=(0, 2))
        king_price_entry = tk.Entry(form, font=("Segoe UI", 10), relief="solid", bd=1)
        king_price_entry.insert(0, "0")
        king_price_entry.pack(fill="x", pady=(3, 10), ipady=4)

        # Stok Awal
        tk.Label(form, text="Stok Awal *", bg="white", fg=self.colors["text"],
                 font=("Segoe UI", 10, "bold")).pack(anchor="w")
        stock_spin = tk.Spinbox(form, from_=0, to=999, font=("Segoe UI", 10), width=10)
        stock_spin.delete(0, "end")
        stock_spin.insert(0, "20")
        stock_spin.pack(anchor="w", pady=(3, 10))

        # Deskripsi Produk
        tk.Label(form, text="Deskripsi Produk", bg="white", fg=self.colors["text"],
                 font=("Segoe UI", 10, "bold")).pack(anchor="w")
        desc_entry = tk.Entry(form, font=("Segoe UI", 10), relief="solid", bd=1)
        desc_entry.pack(fill="x", pady=(3, 15), ipady=4)

        def save_product():
            name = name_entry.get().strip()
            category = cat_cb.get().strip() or "Lainnya"
            price_str = price_entry.get().strip()
            king_price_str = king_price_entry.get().strip() or "0"
            stock_str = stock_spin.get().strip()
            desc = desc_entry.get().strip()

            if not name:
                messagebox.showwarning("Validasi", "Nama produk wajib diisi.")
                return

            try:
                price = int(price_str)
                if price <= 0:
                    raise ValueError
            except ValueError:
                messagebox.showerror("Validasi", "Harga produk harus berupa angka bulat positif (contoh: 15000).")
                return

            try:
                king_price_input = int(king_price_str)
                if king_price_input < 0:
                    raise ValueError
            except ValueError:
                messagebox.showerror("Validasi", "Harga King Size harus berupa angka valid (0 jika tidak ada).")
                return

            try:
                stock = int(stock_str)
                if stock < 0:
                    raise ValueError
            except ValueError:
                messagebox.showerror("Validasi", "Stok awal harus berupa angka 0 atau lebih.")
                return

            # Kalkulasi King Size: Jika seller menginput selisih tambahan (contoh 3000 ketika harga 15000),
            # ubah menjadi total harga King Size (18000).
            if 0 < king_price_input < price:
                final_king_price = price + king_price_input
            else:
                final_king_price = king_price_input

            # Generate ID unik
            existing_ids = [int(p["id"][1:]) for p in self.db.data["products"] if p["id"].startswith("P") and p["id"][1:].isdigit()]
            next_num = max(existing_ids, default=0) + 1
            new_id = f"P{next_num:03d}"

            new_prod = Product(
                id=new_id,
                tenant=self.seller.tenant,
                name=name,
                category=category,
                price=price,
                stock=stock,
                addons=self.db.data.get("addons", []),
                king_price=final_king_price,
                description=desc
            )

            self.db.add_product(new_prod)
            win.destroy()
            messagebox.showinfo("Berhasil", f"Produk '{name}' berhasil disimpan ke database!")
            self.seller_products()

        # Bind Enter key pada semua bidang input
        name_entry.bind("<Return>", lambda e: save_product())
        price_entry.bind("<Return>", lambda e: save_product())
        king_price_entry.bind("<Return>", lambda e: save_product())
        stock_spin.bind("<Return>", lambda e: save_product())
        desc_entry.bind("<Return>", lambda e: save_product())

        self.button(form, "💾 Simpan Produk ke Database", save_product).pack(fill="x", pady=10)

    def seller_addons(self):
        old = getattr(self, "seller_content", None)
        if old: old.destroy()
        self.seller_content = tk.Frame(self, bg=self.colors["bg"])
        self.seller_content.pack(fill="both", expand=True, padx=28, pady=18)
        tk.Label(self.seller_content, text="Manajemen Add-ons / Saus", font=("Segoe UI", 19, "bold"),
                 bg=self.colors["bg"], fg=self.colors["text"]).pack(anchor="w")
        for a in self.db.data["addons"]:
            c = self.card(self.seller_content, padx=15, pady=12)
            c.pack(fill="x", pady=4)
            tk.Label(c, text=a["name"], bg="white", font=("Segoe UI", 11, "bold")).pack(side="left")
            price = "Gratis" if a["price"] == 0 else f'Rp{a["price"]:,}'.replace(",", ".")
            tk.Label(c, text=price, bg="white", fg=self.colors["muted"]).pack(side="right")
        tk.Label(self.seller_content, text="Add-ons demo dapat digunakan pada semua produk. Implementasi produksi dapat menambahkan relasi add-on per tenant/product.",
                 bg=self.colors["bg"], fg=self.colors["muted"], wraplength=850, justify="left").pack(anchor="w", pady=15)

    def seller_orders(self):
        old = getattr(self, "seller_content", None)
        if old: old.destroy()
        self.seller_content = tk.Frame(self, bg=self.colors["bg"])
        self.seller_content.pack(fill="both", expand=True, padx=28, pady=18)
        tk.Label(self.seller_content, text="Order Management", font=("Segoe UI", 19, "bold"),
                 bg=self.colors["bg"], fg=self.colors["text"]).pack(anchor="w")

        controls = tk.Frame(self.seller_content, bg=self.colors["bg"])
        controls.pack(fill="x", pady=(8, 0))
        self.button(controls, "📦 Pindahkan Pesanan Hari Ini ke Histori", self.clear_order_history, primary=False).pack(side="left", padx=(0, 8))
        self.button(controls, "📜 Laman Histori Pesanan", self.seller_order_history, primary=False).pack(side="left")

        self.seller_orders_table(self.seller_content, pending_only=False)

    def seller_order_history(self):
        old = getattr(self, "seller_content", None)
        if old: old.destroy()
        self.seller_content = tk.Frame(self, bg=self.colors["bg"])
        self.seller_content.pack(fill="both", expand=True, padx=28, pady=18)
        tk.Label(self.seller_content, text="Histori Pesanan", font=("Segoe UI", 19, "bold"),
                 bg=self.colors["bg"], fg=self.colors["text"]).pack(anchor="w")

        controls = tk.Frame(self.seller_content, bg=self.colors["bg"])
        controls.pack(fill="x", pady=(8, 0))
        self.button(controls, "← Kembali ke Pesanan", self.seller_orders, primary=False).pack(side="left", padx=(0, 8))
        self.button(controls, "🗑 Hapus Histori Pesanan", self.clear_archived_orders, primary=False).pack(side="left")

        archived_orders = [o for o in self.db.get_archived_orders() if any(i["tenant"] == self.seller.tenant for i in o["items"])]
        tree = ttk.Treeview(self.seller_content, columns=("order", "buyer", "created", "total", "payment", "status"), show="headings")
        for col, label, width in [
            ("order", "Order", 180), ("buyer", "Pembeli", 180), ("created", "Dibuat", 150),
            ("total", "Total", 130), ("payment", "Bayar", 100), ("status", "Status", 220)
        ]:
            tree.heading(col, text=label)
            tree.column(col, width=width)
        tree.pack(fill="both", expand=True, pady=15)

        for order in archived_orders:
            payment = self.tenant_payment(order, self.seller.tenant)
            tree.insert("", "end", iid=order["order_id"], values=(
                order["order_id"], order["buyer_name"], order.get("created_at", ""),
                f'Rp{payment["amount"]:,}'.replace(",", "."), payment["status"], order["status"]
            ))

        def get_selected_oid():
            sel = tree.selection()
            if not sel:
                messagebox.showwarning("Order", "Pilih pesanan dari tabel terlebih dahulu.")
                return None
            return sel[0]

        def view_detail():
            oid = get_selected_oid()
            if oid:
                self.show_seller_order_detail_dialog(oid)

        tree.bind("<Double-1>", lambda e: view_detail())

        tools = tk.Frame(self.seller_content, bg=self.colors["bg"])
        tools.pack(fill="x", pady=(5, 0))
        self.button(tools, "📋 Detail & Catatan Pesanan", view_detail).pack(side="left", padx=4)

    def clear_order_history(self):
        if not messagebox.askyesno(
            "Konfirmasi",
            "Apakah kamu yakin?\n\nPesanan yang dibuat hari ini akan dipindahkan ke histori penjualan dan daftar pesanan aktif akan dibersihkan."
        ):
            return
        self.db.clear_order_history()
        messagebox.showinfo("Histori pesanan", "Pesanan hari ini telah dipindahkan ke histori penjualan.")
        self.seller_orders()

    def clear_archived_orders(self):
        if not messagebox.askyesno("Konfirmasi", "Apakah kamu yakin?\n\nSemua histori pesanan akan dihapus dari database."):
            return
        self.db.clear_archived_orders()
        messagebox.showinfo("Histori pesanan", "Semua histori pesanan berhasil dihapus.")
        self.seller_order_history()

    def seller_orders_table(self, parent, pending_only=False):
        orders = [o for o in self.db.get_orders() if any(i["tenant"] == self.seller.tenant for i in o["items"])]
        if pending_only:
            orders = [o for o in orders if o["status"] == "Menunggu Konfirmasi Penjual"]
        tree = ttk.Treeview(parent, columns=("order","buyer","queue","total","payment","status"), show="headings")
        for col, label, width in [
            ("order","Order",180),("buyer","Pembeli",150),("queue","Antrean",80),
            ("total","Total",120),("payment","Bayar",90),("status","Status",230)]:
            tree.heading(col, text=label); tree.column(col, width=width)
        tree.pack(fill="both", expand=True, pady=15)
        for o in orders:
            payment = self.tenant_payment(o, self.seller.tenant)
            tree.insert("", "end", iid=o["order_id"], values=(
                o["order_id"], o["buyer_name"], o["queue_number"],
                f'Rp{payment["amount"]:,}'.replace(",", "."), payment["status"], o["status"]
            ))

        def get_selected_oid():
            sel = tree.selection()
            if not sel:
                messagebox.showwarning("Order", "Pilih pesanan dari tabel terlebih dahulu.")
                return None
            return sel[0]

        def view_detail():
            oid = get_selected_oid()
            if oid:
                self.show_seller_order_detail_dialog(oid)

        tree.bind("<Double-1>", lambda e: view_detail())

        def confirm():
            oid = get_selected_oid()
            if not oid: return
            self._confirm_seller_order(oid)

        def ready():
            oid = get_selected_oid()
            if not oid: return
            self._ready_seller_order(oid)

        tools = tk.Frame(parent, bg=self.colors["bg"])
        tools.pack(fill="x", pady=(5, 0))
        self.button(tools, "📋 Detail & Catatan Pesanan", view_detail).pack(side="left", padx=4)
        self.button(tools, "✓ Konfirmasi Pesanan", confirm).pack(side="left", padx=4)
        self.button(tools, "✕ Tolak Bukti", lambda: self._reject_seller_order(get_selected_oid()), primary=False).pack(side="left", padx=4)
        self.button(tools, "✓ Tandai Siap Diambil", ready, primary=False).pack(side="left", padx=4)

    def tenant_payment(self, order, tenant):
        payments = order.get("tenant_payments", [])
        for payment in payments:
            if payment.get("tenant") == tenant:
                return payment
        amount = sum(i.get("quantity", 0) * i.get("unit_price", 0) for i in order.get("items", []) if i.get("tenant") == tenant)
        legacy_status = order.get("payment_status", "UNPAID")
        return {"tenant": tenant, "amount": amount, "status": legacy_status, "proof_path": "", "qr_path": ""}

    def _all_tenant_payments(self, order):
        tenants = sorted(set(i.get("tenant") for i in order.get("items", [])))
        return [self.tenant_payment(order, tenant) for tenant in tenants]

    def _reject_seller_order(self, oid):
        if not oid:
            return
        order = next((x for x in self.db.get_orders() if x["order_id"] == oid), None)
        if not order:
            return
        payment = self.tenant_payment(order, self.seller.tenant)
        if not payment.get("proof_path"):
            messagebox.showwarning("Bukti pembayaran", "Belum ada bukti pembayaran untuk tenant ini.")
            return
        if not messagebox.askyesno("Tolak pembayaran", "Tolak bukti pembayaran ini dan batalkan pesanan?" ):
            return
        payment["status"] = "REJECTED"
        order["tenant_payments"] = [payment if p.get("tenant") == self.seller.tenant else p for p in order.get("tenant_payments", [])]
        self.db.update_order(oid, status="Pembayaran Ditolak", payment_status="REJECTED",
                             tenant_payments=order.get("tenant_payments", []))
        messagebox.showinfo("Pesanan ditolak", "Bukti pembayaran ditolak. Pesanan dibatalkan.")
        self.seller_orders()

    def _confirm_seller_order(self, oid):
        o = next((x for x in self.db.get_orders() if x["order_id"] == oid), None)
        if not o: return
        if not messagebox.askyesno("Konfirmasi", "Apakah kamu yakin ingin mengonfirmasi pesanan ini?"):
            return
        if self.expire_payment_if_needed(o):
            messagebox.showwarning("Batas waktu", "Pesanan sudah melewati batas pembayaran 15 menit.")
            self.seller_orders()
            return
        payment = self.tenant_payment(o, self.seller.tenant)
        if payment.get("status") != "SUBMITTED":
            messagebox.showwarning("Bukti pembayaran", "Seller hanya dapat mengonfirmasi setelah buyer mengunggah bukti pembayaran.")
            return
        # Check if items have notes to remind seller
        seller_items = [i for i in o.get("items", []) if i.get("tenant") == self.seller.tenant]
        has_notes = [i for i in seller_items if (i.get("notes") or "").strip()]

        for item in o["items"]:
            if item.get("tenant") != self.seller.tenant:
                continue
            p = self.db.get_product(item["product_id"])
            if not p or p.stock < item["quantity"]:
                p_name = item.get("name") or item.get("product_name")
                messagebox.showerror("Stok tidak cukup", f"Stok {p_name} tidak mencukupi.")
                return
        for item in o["items"]:
            if item.get("tenant") == self.seller.tenant:
                p = self.db.get_product(item["product_id"])
                if p:
                    self.db.update_product_stock(p.id, p.stock - item["quantity"])
        payment["status"] = "PAID"
        updated_payments = [payment if p.get("tenant") == self.seller.tenant else p for p in o.get("tenant_payments", [])]
        all_paid = all(p.get("status") == "PAID" for p in self._all_tenant_payments(o))
        self.db.update_order(oid, status="Sedang Diproses" if all_paid else "Menunggu Konfirmasi Penjual",
                     payment_status="PAID" if all_paid else "PARTIAL", tenant_payments=updated_payments)

        msg = "Pesanan dikonfirmasi dan stok telah dikurangi."
        if has_notes:
            msg += "\n\n⚠️ PERHATIKAN CATATAN PEMBELI:\n"
            for item in has_notes:
                p_name = item.get("name") or item.get("product_name")
                msg += f"• {p_name}: \"{item['notes']}\"\n"
        messagebox.showinfo("Berhasil", msg)
        self.seller_orders()

    def _ready_seller_order(self, oid):
        o = next((x for x in self.db.get_orders() if x["order_id"] == oid), None)
        if not o: return
        self.db.update_order(oid, status="Siap Diambil")
        messagebox.showinfo("Order", "Pesanan ditandai siap diambil.")
        self.seller_orders()

    def show_seller_order_detail_dialog(self, order_id):
        o = next((x for x in self.db.get_orders() if x["order_id"] == order_id), None)
        if not o:
            messagebox.showerror("Order", "Pesanan tidak ditemukan.")
            return

        win = tk.Toplevel(self)
        win.title(f"Detail & Catatan Order {o['order_id']}")
        win.geometry("520x640")
        win.configure(bg=self.colors["bg"])
        win.transient(self)
        win.grab_set()

        tk.Label(win, text=f"Detail Pesanan (Antrean #{o['queue_number']})", font=("Segoe UI", 16, "bold"),
                 bg=self.colors["bg"], fg=self.colors["text"]).pack(pady=(20, 4))
        tk.Label(win, text=f"ID: {o['order_id']} | Pembeli: {o['buyer_name']}",
                 bg=self.colors["bg"], fg=self.colors["muted"], font=("Segoe UI", 10)).pack(pady=(0, 10))

        card = self.card(win, padx=24, pady=20)
        card.pack(fill="both", expand=True, padx=25, pady=(0, 20))

        status_info = f"Status: {o['status']}  •  Pembayaran: {o['payment_status']}"
        tk.Label(card, text=status_info, font=("Segoe UI", 11, "bold"), bg="white", fg=self.colors["blue"]).pack(anchor="w", pady=(0, 10))
        seller_payment = self.tenant_payment(o, self.seller.tenant)
        proof = seller_payment.get("proof_path") or "Belum ada bukti pembayaran"
        tk.Label(card, text=f"Pembayaran tenant: {seller_payment.get('status', 'UNPAID')} • Rp{seller_payment.get('amount', 0):,}".replace(",", "."),
             bg="white", fg=self.colors["text"]).pack(anchor="w")
        if seller_payment.get("proof_path"):
            self.button(card, "LIHAT BUKTI BAYAR", lambda: self.show_image_popup(seller_payment.get("proof_path"), f"Bukti Bayar {self.seller.tenant}")).pack(anchor="w", pady=(2, 10))
        else:
            tk.Label(card, text=f"Bukti: {proof}", bg="white", fg=self.colors["muted"], wraplength=420,
                 justify="left").pack(anchor="w", pady=(2, 10))

        tk.Label(card, text="Item Dipesan & Catatan Khusus:", font=("Segoe UI", 11, "bold"), bg="white", fg=self.colors["text"]).pack(anchor="w", pady=(0, 5))

        seller_items = [item for item in o.get("items", []) if item.get("tenant") == self.seller.tenant]
        if not seller_items:
            seller_items = o.get("items", [])

        # Scrollable container for items
        canvas = tk.Canvas(card, bg="white", highlightthickness=0)
        canvas.pack(fill="both", expand=True)

        items_container = tk.Frame(canvas, bg="white")
        canvas.create_window((0, 0), window=items_container, anchor="nw")

        def _on_frame_configure(e):
            canvas.configure(scrollregion=canvas.bbox("all"))
        items_container.bind("<Configure>", _on_frame_configure)

        for item in seller_items:
            p_name = item.get("name") or item.get("product_name") or "Produk"
            item_box = tk.Frame(items_container, bg="#F9FAFB", highlightbackground=self.colors["line"],
                                highlightthickness=1, padx=12, pady=10)
            item_box.pack(fill="x", pady=6, ipadx=5)

            line_text = f"{p_name} × {item['quantity']}"
            if item.get("king_size"):
                line_text += " (King Size)"
            tk.Label(item_box, text=line_text, font=("Segoe UI", 11, "bold"), bg="#F9FAFB", fg=self.colors["text"]).pack(anchor="w")

            if item.get("addons"):
                addons_str = ", ".join(a.get("name", "") for a in item["addons"])
                tk.Label(item_box, text=f"Add-ons: {addons_str}", font=("Segoe UI", 9), bg="#F9FAFB", fg=self.colors["muted"]).pack(anchor="w", pady=(2, 0))

            notes = (item.get("notes") or "").strip()
            notes_bg = "#FEF3C7" if notes else "#F3F4F6"
            notes_fg = "#92400E" if notes else "#6B7280"
            notes_header = "📝 CATATAN KHUSUS PEMBELI:" if notes else "📝 Catatan:"
            display_notes = notes if notes else "(Tidak ada catatan)"

            n_box = tk.Frame(item_box, bg=notes_bg, padx=10, pady=8)
            n_box.pack(fill="x", pady=(6, 0))
            tk.Label(n_box, text=notes_header, font=("Segoe UI", 9, "bold"), bg=notes_bg, fg=notes_fg).pack(anchor="w")
            tk.Label(n_box, text=display_notes, font=("Segoe UI", 10, "bold" if notes else "normal"),
                     bg=notes_bg, fg=notes_fg, wraplength=360, justify="left").pack(anchor="w", pady=(2, 0))

        btn_area = tk.Frame(card, bg="white")
        btn_area.pack(fill="x", pady=(15, 0))

        def confirm_modal():
            win.destroy()
            self._confirm_seller_order(order_id)

        def ready_modal():
            win.destroy()
            self._ready_seller_order(order_id)

        if o["status"] == "Menunggu Konfirmasi Penjual":
            self.button(btn_area, "✓ Konfirmasi Pesanan Ini", confirm_modal).pack(fill="x", pady=4)
            self.button(btn_area, "✕ Tolak Bukti Pembayaran", lambda: (win.destroy(), self._reject_seller_order(order_id)), primary=False).pack(fill="x", pady=4)
        elif o["status"] == "Sedang Diproses":
            self.button(btn_area, "✓ Tandai Siap Diambil", ready_modal, primary=False).pack(fill="x", pady=4)

    def seller_reports(self):
        old = getattr(self, "seller_content", None)
        if old: old.destroy()
        self.seller_content = tk.Frame(self, bg=self.colors["bg"])
        self.seller_content.pack(fill="both", expand=True, padx=28, pady=18)
        tk.Label(self.seller_content, text="Laporan & Analitik", font=("Segoe UI", 19, "bold"),
                 bg=self.colors["bg"], fg=self.colors["text"]).pack(anchor="w")
        controls = tk.Frame(self.seller_content, bg=self.colors["bg"])
        controls.pack(fill="x", pady=(8, 10))
        tk.Label(controls, text="Tampilan:", bg=self.colors["bg"], fg=self.colors["text"]).pack(side="left")
        period = tk.StringVar(value="Harian")
        period_box = ttk.Combobox(controls, textvariable=period,
                                  values=["Harian", "Mingguan", "Bulanan", "Akumulasi"],
                                  state="readonly", width=15)
        period_box.pack(side="left", padx=(8, 10))
        updated_label = tk.Label(controls, bg=self.colors["bg"], fg=self.colors["muted"])
        updated_label.pack(side="right")
        notebook = ttk.Notebook(self.seller_content)
        notebook.pack(fill="both", expand=True)
        report_content = self.seller_content

        def draw_product_chart(chart, product):
            chart.delete("all")
            today = datetime.now().date()
            if period.get() == "Harian":
                points = [(today - timedelta(days=i), (today - timedelta(days=i)).strftime("%d/%m"))
                          for i in range(6, -1, -1)]
            elif period.get() == "Mingguan":
                points = [(today - timedelta(days=i * 7), f"M-{6-i}") for i in range(6, -1, -1)]
            elif period.get() == "Bulanan":
                points = [(today - timedelta(days=i * 30), (today - timedelta(days=i * 30)).strftime("%b"))
                          for i in range(5, -1, -1)]
            else:
                points = [(today, "Total")]

            values = []
            for point_date, label in points:
                if period.get() == "Akumulasi":
                    value = product["quantity"]
                elif period.get() == "Harian":
                    value = product["daily"].get(point_date.isoformat(), 0)
                elif period.get() == "Mingguan":
                    start = point_date - timedelta(days=6)
                    value = sum(quantity for date_key, quantity in product["daily"].items()
                                if start.isoformat() <= date_key <= point_date.isoformat())
                else:
                    value = sum(quantity for date_key, quantity in product["daily"].items()
                                if date_key[:7] == point_date.strftime("%Y-%m"))
                values.append((label, value))

            max_value = max((value for _, value in values), default=0)
            width = max(1, chart.winfo_width())
            chart.create_text(50, 20, anchor="w", text=f"Unit terjual • {period.get()}",
                              font=("Segoe UI", 11, "bold"), fill=self.colors["text"])
            if max_value == 0:
                chart.create_text(width / 2, 150, text="Belum ada pesanan berbayar pada periode ini.",
                                  fill=self.colors["muted"])
                return
            bar_width = max(35, (width - 100) / len(values) * 0.55)
            for index, (label, value) in enumerate(values):
                center = 60 + index * ((width - 100) / len(values))
                bottom = 270
                top = bottom - (value / max_value) * 205
                chart.create_rectangle(center - bar_width / 2, top, center + bar_width / 2, bottom,
                                       fill=self.colors["blue"], outline="")
                chart.create_text(center, top - 10, text=str(value), fill=self.colors["text"])
                chart.create_text(center, 292, text=label, fill=self.colors["muted"])

        def render(force_reload=False):
            if force_reload:
                self.db.load()
            sales = self.db.get_seller_product_sales(self.seller.tenant)
            for tab in notebook.tabs():
                notebook.forget(tab)
            total_revenue = sum(product["revenue"] for product in sales)
            total_quantity = sum(product["quantity"] for product in sales)
            updated_label.config(text=f"{total_quantity} unit terjual • Rp{total_revenue:,}".replace(",", "."))
            for product in sales:
                tab = tk.Frame(notebook, bg=self.colors["bg"])
                notebook.add(tab, text=product["name"][:20])
                summary = tk.Frame(tab, bg=self.colors["bg"])
                summary.pack(fill="x", pady=(8, 4))
                tk.Label(summary, text=f"{product['quantity']} unit terjual",
                         bg=self.colors["bg"], fg=self.colors["text"],
                         font=("Segoe UI", 12, "bold")).pack(side="left")
                tk.Label(summary, text=f"Omzet: Rp{product['revenue']:,}".replace(",", "."),
                         bg=self.colors["bg"], fg=self.colors["green"],
                         font=("Segoe UI", 12, "bold")).pack(side="right")
                chart = tk.Canvas(tab, height=320, bg="white",
                                  highlightbackground=self.colors["line"], highlightthickness=1)
                chart.pack(fill="both", expand=True, pady=8)
                draw_product_chart(chart, product)
                chart.bind("<Configure>",
                           lambda event, current_chart=chart, current_product=product:
                           draw_product_chart(current_chart, current_product))

        def refresh_realtime():
            if getattr(self, "seller_content", None) is report_content and report_content.winfo_exists():
                render(force_reload=True)
                report_content.after(5000, refresh_realtime)

        self.button(controls, "Refresh Grafik", lambda: render(force_reload=True)).pack(side="left")
        period_box.bind("<<ComboboxSelected>>", lambda event: render())
        render()
        report_content.after(5000, refresh_realtime)


if __name__ == "__main__":
    app = MarsteenApp()
    app.mainloop()
