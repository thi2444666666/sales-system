"""
download_images.py — Chạy script này TRÊN MÁY TÍNH của bạn (Windows)

Cách dùng:
  1. Copy file này vào thư mục gốc dự án  D:\\Doan\\
  2. Mở terminal tại D:\\Doan\\ rồi chạy:
         python download_images.py
  3. Ảnh tự tải vào D:\\Doan\\static\\images\\uploads\\

Yêu cầu:  pip install requests Pillow
"""

import os
import time
from io import BytesIO

import requests
try:
    from PIL import Image
    HAS_PIL = True
except ImportError:
    HAS_PIL = False
    print("Gợi ý: pip install Pillow để ảnh được resize đẹp hơn\n")

# ── Đường dẫn đích ────────────────────────────────────────────────────────────
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
DEST = os.path.join(SCRIPT_DIR, "static", "images", "uploads")
os.makedirs(DEST, exist_ok=True)

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/124.0.0.0 Safari/537.36"
    )
}

# ── Danh sách ảnh (Unsplash — miễn phí, không cần API key) ───────────────────
IMAGES = [
    # Laptop
    ("laptop_dell_xps.png",
     "https://images.unsplash.com/photo-1593642632559-0c6d3fc62b89?w=500&q=80&auto=format&fit=crop"),
    ("laptop_macbook_pro.png",
     "https://images.unsplash.com/photo-1517336714731-489689fd1ca8?w=500&q=80&auto=format&fit=crop"),
    ("laptop_asus_rog.png",
     "https://images.unsplash.com/photo-1603481588273-2f908a9a7a1b?w=500&q=80&auto=format&fit=crop"),
    ("laptop_hp_spectre.png",
     "https://images.unsplash.com/photo-1496181133206-80ce9b88a853?w=500&q=80&auto=format&fit=crop"),
    ("laptop_lenovo_thinkpad.png",
     "https://images.unsplash.com/photo-1525547719571-a2d4ac8945e2?w=500&q=80&auto=format&fit=crop"),
    ("laptop_msi_titan.png",
     "https://images.unsplash.com/photo-1587202372775-e229f172b9d7?w=500&q=80&auto=format&fit=crop"),
    ("laptop_surface.png",
     "https://images.unsplash.com/photo-1542744094-3a31f272c490?w=500&q=80&auto=format&fit=crop"),

    # Điện thoại
    ("phone_iphone15.png",
     "https://images.unsplash.com/photo-1695048133142-1a20484d2569?w=500&q=80&auto=format&fit=crop"),
    ("phone_samsung_s24.png",
     "https://images.unsplash.com/photo-1610945415295-d9bbf067e59c?w=500&q=80&auto=format&fit=crop"),
    ("phone_xiaomi_14.png",
     "https://images.unsplash.com/photo-1511707171634-5f897ff02aa9?w=500&q=80&auto=format&fit=crop"),
    ("phone_oppo_find.png",
     "https://images.unsplash.com/photo-1574944985070-8f3ebc6b79d2?w=500&q=80&auto=format&fit=crop"),
    ("phone_google_pixel.png",
     "https://images.unsplash.com/photo-1598327105666-5b89351aff97?w=500&q=80&auto=format&fit=crop"),
    ("phone_vivo_x100.png",
     "https://images.unsplash.com/photo-1565849904461-04a58ad377e0?w=500&q=80&auto=format&fit=crop"),

    # Tablet
    ("tablet_ipad_pro.png",
     "https://images.unsplash.com/photo-1544244015-0df4b3ffc6b0?w=500&q=80&auto=format&fit=crop"),
    ("tablet_samsung_tab.png",
     "https://images.unsplash.com/photo-1632516643720-e7f5d7d6ecc9?w=500&q=80&auto=format&fit=crop"),
    ("tablet_xiaomi_pad.png",
     "https://images.unsplash.com/photo-1561154464-82e9adf32764?w=500&q=80&auto=format&fit=crop"),
    ("tablet_lenovo.png",
     "https://images.unsplash.com/photo-1589739900266-43b2843f4c12?w=500&q=80&auto=format&fit=crop"),

    # Màn hình
    ("monitor_lg_4k.png",
     "https://images.unsplash.com/photo-1527443224154-c4a3942d3acf?w=500&q=80&auto=format&fit=crop"),
    ("monitor_dell_ultrasharp.png",
     "https://images.unsplash.com/photo-1585792180666-f7347c490ee2?w=500&q=80&auto=format&fit=crop"),
    ("monitor_asus_pg.png",
     "https://images.unsplash.com/photo-1616763355548-1b606f439f86?w=500&q=80&auto=format&fit=crop"),
    ("monitor_samsung_oled.png",
     "https://images.unsplash.com/photo-1547082299-de196ea013d6?w=500&q=80&auto=format&fit=crop"),

    # Tai nghe
    ("headphone_airpods.png",
     "https://images.unsplash.com/photo-1588423771073-b8903fead85b?w=500&q=80&auto=format&fit=crop"),
    ("headphone_sony_wh.png",
     "https://images.unsplash.com/photo-1505740420928-5e560c06d30e?w=500&q=80&auto=format&fit=crop"),
    ("headphone_bose_qc.png",
     "https://images.unsplash.com/photo-1546435770-a3e426bf472b?w=500&q=80&auto=format&fit=crop"),
    ("headphone_samsung_buds.png",
     "https://images.unsplash.com/photo-1590658268037-6bf12165a8df?w=500&q=80&auto=format&fit=crop"),

    # Chuột & Bàn phím
    ("mouse_logitech_mx.png",
     "https://images.unsplash.com/photo-1527864550417-7fd91fc51a46?w=500&q=80&auto=format&fit=crop"),
    ("mouse_razer_deathadder.png",
     "https://images.unsplash.com/photo-1615663245857-ac93bb7c39e7?w=500&q=80&auto=format&fit=crop"),
    ("mouse_steelseries.png",
     "https://images.unsplash.com/photo-1563297007-0686b7003af7?w=500&q=80&auto=format&fit=crop"),
    ("keyboard_keychron_k8.png",
     "https://images.unsplash.com/photo-1587829741301-dc798b83add3?w=500&q=80&auto=format&fit=crop"),
    ("keyboard_corsair_k100.png",
     "https://images.unsplash.com/photo-1595044426077-d36d9236d54a?w=500&q=80&auto=format&fit=crop"),
    ("keyboard_mechanical.png",
     "https://images.unsplash.com/photo-1601445638532-3c6f6c3aa1d6?w=500&q=80&auto=format&fit=crop"),

    # Linh kiện
    ("ssd_samsung_970.png",
     "https://images.unsplash.com/photo-1597872200969-2b65d56bd16b?w=500&q=80&auto=format&fit=crop"),
    ("nvme_wd_black.png",
     "https://images.unsplash.com/photo-1591488320449-011701bb6704?w=500&q=80&auto=format&fit=crop"),
    ("ram_corsair_32gb.png",
     "https://images.unsplash.com/photo-1562976540-1502c2145186?w=500&q=80&auto=format&fit=crop"),
    ("cpu_amd_ryzen.png",
     "https://images.unsplash.com/photo-1555617766-c94804975da7?w=500&q=80&auto=format&fit=crop"),
    ("gpu_rtx_4070.png",
     "https://images.unsplash.com/photo-1587202372583-49330a15584d?w=500&q=80&auto=format&fit=crop"),
    ("gpu_rx_7900.png",
     "https://images.unsplash.com/photo-1587202372583-49330a15584d?w=500&q=80&auto=format&fit=crop"),
    ("hdd_wd_4tb.png",
     "https://images.unsplash.com/photo-1531492746076-161ca9bcad58?w=500&q=80&auto=format&fit=crop"),

    # Loa & Âm thanh
    ("speaker_bose.png",
     "https://images.unsplash.com/photo-1608043152269-423dbba4e7e1?w=500&q=80&auto=format&fit=crop"),
    ("speaker_jbl.png",
     "https://images.unsplash.com/photo-1545454675-3531b543be5d?w=500&q=80&auto=format&fit=crop"),
    ("speaker_sonos.png",
     "https://images.unsplash.com/photo-1558618666-fcd25c85cd64?w=500&q=80&auto=format&fit=crop"),

    # Camera
    ("camera_sony_a7.png",
     "https://images.unsplash.com/photo-1516035069371-29a1b244cc32?w=500&q=80&auto=format&fit=crop"),
    ("camera_gopro.png",
     "https://images.unsplash.com/photo-1564466809058-bf4114d55352?w=500&q=80&auto=format&fit=crop"),
    ("wacom_intuos.png",
     "https://images.unsplash.com/photo-1626379953822-baec19c3accd?w=500&q=80&auto=format&fit=crop"),

    # Smartwatch
    ("watch_apple.png",
     "https://images.unsplash.com/photo-1579586337278-3befd40fd17a?w=500&q=80&auto=format&fit=crop"),
    ("watch_samsung.png",
     "https://images.unsplash.com/photo-1523275335684-37898b6baf30?w=500&q=80&auto=format&fit=crop"),

    # Router & Mạng
    ("router_asus_ax.png",
     "https://images.unsplash.com/photo-1606904825846-647eb07f5be2?w=500&q=80&auto=format&fit=crop"),
    ("router_tp_link.png",
     "https://images.unsplash.com/photo-1544197150-b99a580bb7a8?w=500&q=80&auto=format&fit=crop"),

    # Phụ kiện & Sạc
    ("charger_anker_140w.png",
     "https://images.unsplash.com/photo-1583863788434-e58a36330cf0?w=500&q=80&auto=format&fit=crop"),
    ("charger_samsung_45w.png",
     "https://images.unsplash.com/photo-1618384887929-16ec33fab9ef?w=500&q=80&auto=format&fit=crop"),
]


def download_one(filename, url):
    """Tải 1 ảnh, crop vuông, resize 500x500, lưu PNG."""
    try:
        r = requests.get(url, headers=HEADERS, timeout=20)
        if r.status_code != 200 or len(r.content) < 5000:
            return False, f"HTTP {r.status_code} / {len(r.content)} bytes"

        out_path = os.path.join(DEST, filename)

        if HAS_PIL:
            img = Image.open(BytesIO(r.content)).convert("RGB")
            w, h = img.size
            side = min(w, h)
            left = (w - side) // 2
            top  = (h - side) // 2
            img  = img.crop((left, top, left + side, top + side))
            img  = img.resize((500, 500), Image.LANCZOS)
            img.save(out_path, "PNG", optimize=True)
        else:
            with open(out_path, "wb") as f:
                f.write(r.content)

        size_kb = os.path.getsize(out_path) // 1024
        return True, f"{size_kb} KB"

    except Exception as exc:
        return False, str(exc)


if __name__ == "__main__":
    print("=" * 55)
    print("  TẢI ẢNH SẢN PHẨM — TechSales System")
    print("=" * 55)
    print(f"  Thư mục lưu : {DEST}")
    print(f"  Tổng số ảnh : {len(IMAGES)}")
    print("=" * 55 + "\n")

    success_count = 0
    failed_files  = []

    for idx, (fname, url) in enumerate(IMAGES, start=1):
        ok, info = download_one(fname, url)
        status   = "✔" if ok else "✗"
        print(f"  {status} [{idx:02d}/{len(IMAGES)}] {fname:<35} {info}")
        if ok:
            success_count += 1
        else:
            failed_files.append(fname)
        time.sleep(0.4)   # nghỉ 0.4s tránh rate-limit

    print()
    print("=" * 55)
    print(f"  Thành công : {success_count}/{len(IMAGES)}")
    if failed_files:
        print(f"  Thất bại   : {len(failed_files)}")
        for f in failed_files:
            print(f"    - {f}")
        print()
        print("  Với ảnh thất bại, bạn tự tìm ảnh phù hợp và")
        print("  đặt đúng tên vào thư mục static/images/uploads/")
    print("=" * 55)
    print()
    print("  Xong! Khởi động lại Flask rồi F5 trang web.")
    print()