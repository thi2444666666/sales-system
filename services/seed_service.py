"""
seed_service.py — Nạp dữ liệu mẫu thực tế cho hệ thống.
50 sản phẩm (10 danh mục), 30 khách hàng, 100+ hóa đơn trải đều 12 tháng.
"""
from datetime import datetime, timedelta
import random
import calendar
from bson import ObjectId
from flask_bcrypt import generate_password_hash


# ═══════════════════════════════════════════════════════════════════════════════
#  DỮ LIỆU SẢN PHẨM — 50 sản phẩm, 10 danh mục
# ═══════════════════════════════════════════════════════════════════════════════
PRODUCTS = [
    # ── Laptop (8) ──
    {"name": "Laptop Dell XPS 15 9530",             "category": "Laptop",           "price": 32_900_000, "stock": 12,
     "image": "laptop_dell_xps.png",
     "description": "Intel Core i7-13700H, RAM 16GB DDR5, SSD 512GB NVMe, màn hình OLED 3.5K 60Hz. Thiết kế siêu mỏng nhẹ, pin 86Wh dùng cả ngày. Lý tưởng cho đồ họa và lập trình chuyên nghiệp."},
    {"name": 'MacBook Pro 14" M3 Pro',              "category": "Laptop",           "price": 52_990_000, "stock": 7,
     "image": "laptop_macbook_pro.png",
     "description": "Chip Apple M3 Pro 11-core CPU, 14-core GPU, RAM 18GB, SSD 512GB. Màn hình Liquid Retina XDR 120Hz ProMotion. Pin lên tới 18 giờ. Hiệu năng đỉnh cao cho sáng tạo nội dung và lập trình."},
    {"name": "Laptop ASUS ROG Strix G16 2024",      "category": "Laptop",           "price": 38_500_000, "stock": 9,
     "image": "laptop_asus_rog.png",
     "description": "Intel Core i9-13980HX, RTX 4070 8GB, RAM 32GB DDR5, SSD 1TB PCIe 4.0. Màn hình 16 inch QHD 240Hz, tản nhiệt ROG Intelligent Cooling. Chinh phục mọi tựa game AAA ở setting Ultra."},
    {"name": "Laptop HP Spectre x360 14",           "category": "Laptop",           "price": 36_200_000, "stock": 5,
     "image": "laptop_hp_spectre.png",
     "description": "Intel Core i7-1355U, RAM 16GB, SSD 1TB. Màn hình OLED cảm ứng 2.8K 120Hz, xoay 360 độ. Thiết kế premium vỏ nhôm CNC, tích hợp bút stylus HP Tilt Pen trong hộp."},
    {"name": "Laptop Lenovo ThinkPad X1 Carbon Gen 11", "category": "Laptop",       "price": 41_500_000, "stock": 6,
     "image": "laptop_lenovo_thinkpad.png",
     "description": "Intel Core i7-1365U, RAM 16GB LPDDR5, SSD 512GB. Trọng lượng chỉ 1.12kg, màn hình IPS 14 inch 2.8K 90Hz chống chói. Đạt 12 chứng nhận MIL-SPEC về độ bền doanh nghiệp."},
    {"name": "Laptop MSI Titan GT77 HX",            "category": "Laptop",           "price": 89_000_000, "stock": 3,
     "image": "laptop_msi_titan.png",
     "description": "Intel Core i9-13980HX, RTX 4090 16GB, RAM 64GB DDR5, SSD 4TB RAID. Màn hình 17 inch UHD 144Hz 100% AdobeRGB. Bàn phím Cherry MX Ultra Low Profile RGB."},
    {"name": "Microsoft Surface Laptop 5 13.5\"",   "category": "Laptop",           "price": 29_900_000, "stock": 8,
     "image": "laptop_surface.png",
     "description": "Intel Core i5-1235U, RAM 8GB, SSD 256GB. Màn hình PixelSense 13.5 inch cảm ứng 2256x1504. Vỏ nhôm Alcantara sang trọng, Dolby Atmos, Windows 11 Home."},
    {"name": "Laptop ASUS Vivobook 15X OLED",       "category": "Laptop",           "price": 18_990_000, "stock": 20,
     "image": "laptop_dell_xps.png",
     "description": "Intel Core i5-12500H, RAM 8GB DDR4, SSD 512GB. Màn hình OLED 15.6 inch FHD 600nits PANTONE Validated. Cổng kết nối USB-C, HDMI 2.1, thẻ nhớ SD. Phù hợp học sinh, sinh viên."},

    # ── Điện thoại (8) ──
    {"name": "iPhone 15 Pro Max 256GB",             "category": "Điện thoại",       "price": 34_990_000, "stock": 18,
     "image": "phone_iphone15.png",
     "description": "Chip A17 Pro, màn hình Super Retina XDR 6.7 inch ProMotion 120Hz. Camera 48MP chính, 12MP telephoto 5x. Khung titanium Grade 5, Dynamic Island, USB-C 3.0. Pin 4422mAh sạc nhanh 27W."},
    {"name": "Samsung Galaxy S24 Ultra 512GB",      "category": "Điện thoại",       "price": 31_990_000, "stock": 15,
     "image": "phone_samsung_s24.png",
     "description": "Snapdragon 8 Gen 3, Dynamic AMOLED 6.8 inch QHD+ 120Hz. Camera 200MP chính, zoom quang 10x, S Pen tích hợp. RAM 12GB, 512GB. Pin 5000mAh sạc nhanh 45W, chống nước IP68."},
    {"name": "Xiaomi 14 Ultra 512GB",               "category": "Điện thoại",       "price": 24_990_000, "stock": 22,
     "image": "phone_xiaomi_14.png",
     "description": "Snapdragon 8 Gen 3, hệ thống camera Leica 4 ống kính. Cảm biến chính 1 inch 50MP, màn hình AMOLED 6.73 inch 120Hz 3200nit. RAM 16GB, 512GB, pin 5000mAh sạc 90W."},
    {"name": "OPPO Find X7 Pro 256GB",              "category": "Điện thoại",       "price": 22_990_000, "stock": 14,
     "image": "phone_oppo_find.png",
     "description": "Dimensity 9300, camera Hasselblad 50MP chính + periscope 64MP. AMOLED 6.82 inch 2K+ 120Hz. RAM 12GB LPDDR5X, 256GB UFS 4.0. Pin 5000mAh sạc nhanh 100W, không dây 50W."},
    {"name": "Google Pixel 8 Pro 128GB",            "category": "Điện thoại",       "price": 26_990_000, "stock": 10,
     "image": "phone_google_pixel.png",
     "description": "Chip Tensor G3, 7 năm cập nhật Android. Camera Pro 50MP Octa PD. LTPO OLED 6.7 inch 120Hz. AI features: Magic Eraser, Best Take, Call Screen. RAM 12GB, 128GB."},
    {"name": "Vivo X100 Pro 256GB",                 "category": "Điện thoại",       "price": 19_990_000, "stock": 17,
     "image": "phone_vivo_x100.png",
     "description": "Dimensity 9300, camera Zeiss 50MP chính 1-inch. AMOLED 6.78 inch 120Hz 2800nit. RAM 16GB, 256GB. Pin 5400mAh sạc nhanh 100W FlashCharge, không dây 50W."},
    {"name": "Samsung Galaxy A55 5G 128GB",         "category": "Điện thoại",       "price": 9_990_000,  "stock": 30,
     "image": "phone_samsung_s24.png",
     "description": "Exynos 1480, Super AMOLED 6.6 inch FHD+ 120Hz. Camera 50MP OIS, 12MP ultrawide, 5MP macro. RAM 8GB, 128GB. Pin 5000mAh sạc 25W, khung Armor Aluminum."},
    {"name": "iPhone 14 128GB",                     "category": "Điện thoại",       "price": 19_490_000, "stock": 25,
     "image": "phone_iphone15.png",
     "description": "Chip A15 Bionic, màn hình Super Retina XDR 6.1 inch. Camera Dual 12MP chính + ultrawide Photonic Engine. Crash Detection, Emergency SOS via satellite. Pin cải thiện 20% so với iPhone 13."},

    # ── Tablet (4) ──
    {"name": 'iPad Pro 12.9" M2 Wi-Fi 256GB',       "category": "Tablet",           "price": 31_990_000, "stock": 10,
     "image": "tablet_ipad_pro.png",
     "description": "Màn hình Liquid Retina XDR mini-LED 2732x2048 ProMotion 120Hz. Chip M2 mạnh mẽ, hỗ trợ Apple Pencil 2, Magic Keyboard. Kết nối Thunderbolt/USB 4, Wi-Fi 6E, Bluetooth 5.3."},
    {"name": "Samsung Galaxy Tab S9 Ultra 256GB",   "category": "Tablet",           "price": 27_990_000, "stock": 8,
     "image": "tablet_samsung_tab.png",
     "description": "Snapdragon 8 Gen 2, Dynamic AMOLED 14.6 inch 120Hz. S Pen included, DeX mode như máy tính. RAM 12GB, 256GB. WiFi 6E, Bluetooth 5.3, sạc 45W. Màn hình lớn nhất phân khúc."},
    {"name": "Xiaomi Pad 6 Pro 256GB",              "category": "Tablet",           "price": 10_990_000, "stock": 18,
     "image": "tablet_xiaomi_pad.png",
     "description": "Snapdragon 8+ Gen 1, màn hình 11 inch 2.8K 144Hz Dolby Vision. RAM 8GB LPDDR5, 256GB, 4 loa Dolby Atmos. Pin 8600mAh sạc 67W. Bút stylus và bàn phím bán riêng."},
    {"name": "Lenovo Tab P12 Pro",                  "category": "Tablet",           "price": 18_500_000, "stock": 12,
     "image": "tablet_lenovo.png",
     "description": "Snapdragon 870, AMOLED 12.6 inch 2K 120Hz. RAM 8GB, 256GB, 4 loa JBL Dolby Atmos. Pin 10200mAh sạc 45W. Kèm Precision Pen 3, hỗ trợ Google Meet và Lenovo Smart Paper."},

    # ── Màn hình (5) ──
    {"name": 'LG UltraFine 27" 4K IPS USB-C',       "category": "Màn hình",         "price": 14_900_000, "stock": 14,
     "image": "monitor_lg_4k.png",
     "description": "IPS 4K 60Hz, độ sáng 400nits HDR10, sRGB 99%, DCI-P3 95%. USB-C 90W sạc laptop. HDMI 2.0 x2, DisplayPort 1.4, USB-A x3. Đế tilt/height/pivot điều chỉnh linh hoạt."},
    {"name": 'Dell UltraSharp 32" 4K USB-C Hub',     "category": "Màn hình",         "price": 19_900_000, "stock": 9,
     "image": "monitor_dell_ultrasharp.png",
     "description": "IPS 4K 60Hz Delta-E < 2, sRGB 100%, Rec.709 100%. USB-C 90W, RJ45 LAN 2.5Gbps tích hợp, USB-A x4. ComfortView Plus bảo vệ mắt. Lý tưởng thiết kế đồ họa chuyên nghiệp."},
    {"name": "ASUS ROG Swift PG32UQX 4K 144Hz",     "category": "Màn hình",         "price": 52_000_000, "stock": 4,
     "image": "monitor_asus_pg.png",
     "description": "IPS 4K 144Hz HDMI 2.1, G-SYNC Ultimate HDR1400, Mini LED 1152 zones. DCI-P3 98%, sRGB 140%. HDMI 2.1 x3, DP 1.4. Tối ưu cho PS5, Xbox Series X và PC gaming 4K."},
    {"name": 'Samsung Odyssey OLED G9 49"',          "category": "Màn hình",         "price": 45_000_000, "stock": 3,
     "image": "monitor_samsung_oled.png",
     "description": "DQHD 5120x1440 240Hz 0.03ms, cong 1800R. QD-OLED thế hệ 3, DisplayHDR True Black 400, DCI-P3 99%. HDMI 2.1 x2, DP 1.4, USB-C 90W. Trải nghiệm ultrawide gaming đỉnh cao."},
    {"name": 'LG UltraWide 34" WQHD VA 160Hz',      "category": "Màn hình",         "price": 13_500_000, "stock": 14,
     "image": "monitor_lg_4k.png",
     "description": "VA WQHD 3440x1440 160Hz, cong 1500R. AMD FreeSync Premium Pro, HDR10, sRGB 99%. USB-C 65W, HDMI 2.0 x2, DP 1.4. Ideal cho lập trình, thiết kế và giải trí đa nhiệm."},

    # ── Tai nghe (5) ──
    {"name": "AirPods Pro 2nd Gen (USB-C)",         "category": "Tai nghe",         "price": 6_490_000,  "stock": 45,
     "image": "headphone_airpods.png",
     "description": "H2 chip, ANC thế hệ 2 giảm 2x tiếng ồn, Transparency mode tự điều chỉnh, Adaptive Audio. Pin 6h + 24h hộp sạc USB-C. Chống nước IPX4 cả tai nghe lẫn hộp."},
    {"name": "Sony WH-1000XM5",                     "category": "Tai nghe",         "price": 8_490_000,  "stock": 28,
     "image": "headphone_sony_wh.png",
     "description": "8 mic ANC giảm 40dB tiếng ồn, LDAC Hi-Res Wireless. Pin 30h có ANC, sạc nhanh 3 phút nghe 3h. Trọng lượng 250g, gập gọn. Đánh giá ANC tốt nhất thế giới liên tiếp 4 năm."},
    {"name": "Bose QuietComfort 45",                "category": "Tai nghe",         "price": 7_990_000,  "stock": 22,
     "image": "headphone_bose_qc.png",
     "description": "Over-ear ANC nhẹ nhất 238g, TriPort acoustic. Pin 24h, sạc nhanh 15 phút nghe 3h. Kết nối 2 thiết bị cùng lúc. Đệm tai MemoryFoam cực êm ái khi đeo lâu."},
    {"name": "Samsung Galaxy Buds2 Pro",            "category": "Tai nghe",         "price": 4_490_000,  "stock": 35,
     "image": "headphone_samsung_buds.png",
     "description": "In-ear ANC 5.5mm siêu nhỏ, 360 Audio spatial sound, Hi-Fi 24-bit. Pin 5h + 18h hộp sạc, IPX7. Tích hợp Galaxy AI, tối ưu cho hệ sinh thái Samsung Galaxy."},
    {"name": "Sennheiser Momentum 4 Wireless",      "category": "Tai nghe",         "price": 8_990_000,  "stock": 15,
     "image": "headphone_bose_qc.png",
     "description": "Pin 60h kỷ lục phân khúc, aptX Adaptive, SBC, AAC. ANC tự điều chỉnh theo môi trường, 5 chế độ EQ. Thiết kế tinh tế, vỏ nhựa siêu bền, gập gọn mang đi dễ dàng."},

    # ── Chuột & Bàn phím (6) ──
    {"name": "Logitech MX Master 3S",               "category": "Chuột & Bàn phím", "price": 2_290_000,  "stock": 60,
     "image": "mouse_logitech_mx.png",
     "description": "Sensor 8000DPI Darkfield, MagSpeed scroll wheel 1000 trang/giây không tiếng ồn. Pin 70 ngày, Bluetooth/USB Logi Bolt. 7 nút lập trình, ergonomic tối ưu làm việc 8h+."},
    {"name": "Razer DeathAdder V3 Pro",             "category": "Chuột & Bàn phím", "price": 3_290_000,  "stock": 40,
     "image": "mouse_razer_deathadder.png",
     "description": "Gaming mouse không dây 63g siêu nhẹ, Focus Pro 30K optical sensor. HyperSpeed Wireless 4000Hz polling rate. Pin 90h, HyperScroll. Ergonomic right-hand, tối ưu FPS, MOBA."},
    {"name": "SteelSeries Rival 600",               "category": "Chuột & Bàn phím", "price": 1_890_000,  "stock": 35,
     "image": "mouse_steelseries.png",
     "description": "Dual sensor TrueMove3+ với depth sensor 1-to-1 tracking. 8500DPI, 6 nút lập trình, customizable weight system. RGB per-zone, thiết kế ergonomic split-trigger bền bỉ."},
    {"name": "Keychron K8 Pro Wireless TKL",        "category": "Chuột & Bàn phím", "price": 2_890_000,  "stock": 50,
     "image": "keyboard_keychron_k8.png",
     "description": "Bàn phím cơ không dây TKL, switch Gateron G Pro hot-swap. Bluetooth 5.1 đa kết nối 3 thiết bị, USB-C. RGB per-key, pin 4000mAh 200h không đèn. Aluminium frame cao cấp."},
    {"name": "Corsair K100 RGB Optical",            "category": "Chuột & Bàn phím", "price": 5_490_000,  "stock": 20,
     "image": "keyboard_corsair_k100.png",
     "description": "Switch OPX optical 1ms, iCUE Control Wheel đa chức năng, 44 zone RGB. Macro 8000 profiles lưu on-device, USB Passthrough, PBT Doubleshot keycaps chống mòn."},
    {"name": "Keychron Q1 Pro 75% Aluminum",        "category": "Chuột & Bàn phím", "price": 4_190_000,  "stock": 25,
     "image": "keyboard_mechanical.png",
     "description": "Vỏ nhôm CNC nguyên khối nặng 1.4kg, gasket mount cực êm. Bluetooth 5.1 + USB-C, switch Gateron hot-swap. RGB per-key, foam nhiều lớp giảm tiếng ồn. Layout 75% tiết kiệm bàn."},

    # ── Linh kiện (6) ──
    {"name": "SSD Samsung 990 Pro 2TB NVMe",        "category": "Linh kiện",        "price": 4_290_000,  "stock": 80,
     "image": "ssd_samsung_970.png",
     "description": "PCIe Gen 4 NVMe M.2, đọc 7450MB/s ghi 6900MB/s. V-NAND TLC 3bit, Samsung Magician Software. Bảo hành 5 năm hoặc 1200TBW. Lý tưởng gaming, video editing 8K."},
    {"name": "WD Black SN850X 1TB NVMe",            "category": "Linh kiện",        "price": 2_590_000,  "stock": 65,
     "image": "nvme_wd_black.png",
     "description": "PCIe Gen 4 NVMe M.2, đọc 7300MB/s ghi 6600MB/s. Game Mode 2.0 tối ưu cho game. Bảo hành 5 năm, tương thích PlayStation 5. Có phiên bản kèm heatsink."},
    {"name": "RAM Corsair Vengeance DDR5 32GB 6000MHz", "category": "Linh kiện",    "price": 3_490_000,  "stock": 45,
     "image": "ram_corsair_32gb.png",
     "description": "2x16GB DDR5 6000MHz CL30 iCUE RGB. On-die ECC, XMP 3.0 auto-overclock. Tương thích Intel Alder/Raptor Lake và AMD Ryzen 7000. Tản nhiệt nhôm, tối ưu gaming và rendering."},
    {"name": "CPU AMD Ryzen 9 7950X",               "category": "Linh kiện",        "price": 18_500_000, "stock": 8,
     "image": "cpu_amd_ryzen.png",
     "description": "16 nhân 32 luồng, base 4.5GHz boost 5.7GHz. Socket AM5, TDP 170W, Zen 4 5nm TSMC. PCIe 5.0, DDR5, L3 cache 64MB. Hiệu năng đơn nhân và đa nhân dẫn đầu desktop."},
    {"name": "GPU NVIDIA RTX 4070 Ti Super 16GB",   "category": "Linh kiện",        "price": 24_990_000, "stock": 12,
     "image": "gpu_rtx_4070.png",
     "description": "16GB GDDR6X, DLSS 3.5 Frame Generation, Ray Tracing. Ada Lovelace 8448 CUDA cores, 285W TDP. HDMI 2.1, DP 1.4a x3. Render 4K 60fps mọi game AAA. Ideal cho AI workloads."},
    {"name": "WD Red Plus 4TB HDD NAS",             "category": "Linh kiện",        "price": 2_890_000,  "stock": 30,
     "image": "hdd_wd_4tb.png",
     "description": "3.5 inch HDD chuyên dụng NAS RAID, 5400RPM, cache 256MB. CMR ghi từ truyền thống đáng tin cậy. NASware 3.0 firmware, bảo hành 3 năm, workload 180TB/năm."},

    # ── Loa & Âm thanh (4) ──
    {"name": "Bose SoundLink Max Portable",         "category": "Loa & Âm thanh",   "price": 9_990_000,  "stock": 25,
     "image": "speaker_bose.png",
     "description": "Loa Bluetooth di động cao cấp, pin 20h. IP67 chống nước hoàn toàn, dây đeo vai tích hợp. PartyMode kết nối 2 loa, StereoMode tách kênh. USB-C sạc và audio out, BT 5.3."},
    {"name": "JBL Charge 5 Wi-Fi",                  "category": "Loa & Âm thanh",   "price": 5_490_000,  "stock": 38,
     "image": "speaker_jbl.png",
     "description": "Bluetooth + Wi-Fi, Apple AirPlay 2, Chromecast. IP67, pin 20h, JBL PartyBoost. Sạc USB-A cho thiết bị khác, bass mạnh mẽ. Tương thích Google Home và Amazon Alexa."},
    {"name": "Sonos Era 300 Spatial Audio",         "category": "Loa & Âm thanh",   "price": 12_990_000, "stock": 15,
     "image": "speaker_sonos.png",
     "description": "Loa thông minh Dolby Atmos spatial audio 6 driver. Wi-Fi, BT 5.0, AirPlay 2, Line-in USB-C. Alexa tích hợp, âm thanh 360 độ. Ghép cặp làm surround sound cho TV."},
    {"name": "Logitech Z407 Bluetooth 2.1",         "category": "Loa & Âm thanh",   "price": 1_890_000,  "stock": 50,
     "image": "speaker_jbl.png",
     "description": "Hệ thống 2.1 Bluetooth 5.0 + 3.5mm. Subwoofer 40W, 2 loa vệ tinh 10W. Điều khiển không dây tích hợp, Easy-Switch 3 nguồn. Giải pháp âm thanh tốt cho bàn làm việc."},

    # ── Phụ kiện & Sạc (4) ──
    {"name": "Anker Prime 240W GaN Charger 4 cổng", "category": "Phụ kiện & Sạc",  "price": 2_490_000,  "stock": 70,
     "image": "charger_anker_140w.png",
     "description": "4 cổng GaN 240W: 2x USB-C (140W+100W) + 2x USB-A. Sạc MacBook Pro 16 đầy trong 1h40p. ActiveShield 2.0 cảm biến nhiệt 3 triệu lần/giây. Nhỏ gọn 131g."},
    {"name": "Samsung 45W Super Fast Charger",      "category": "Phụ kiện & Sạc",  "price": 890_000,    "stock": 90,
     "image": "charger_samsung_45w.png",
     "description": "Super Fast Charging 2.0 USB-C PD PPS. Tương thích Galaxy S21-S24 series, Note 20. Sạc S24 Ultra từ 0 lên 50% trong 25 phút. Kích thước nhỏ gọn 60g, kèm cáp USB-C 1.8m."},
    {"name": "Ugreen Revodok Pro 13-in-1 Dock",     "category": "Phụ kiện & Sạc",  "price": 3_290_000,  "stock": 40,
     "image": "charger_anker_140w.png",
     "description": "Thunderbolt 4, 2x HDMI 4K60Hz, DP 8K, 4x USB-A 3.2, SD/TF reader, RJ45 2.5G LAN, PD 100W. Chip tích hợp giảm nhiệt, vỏ nhôm. Tương thích Mac và Windows."},
    {"name": "Baseus 65W Power Bank 20000mAh",      "category": "Phụ kiện & Sạc",  "price": 1_490_000,  "stock": 55,
     "image": "charger_samsung_45w.png",
     "description": "2x USB-C PD 65W + 1x USB-A QC. Hiển thị % pin LED digital. Sạc MacBook Air 13 được 1.5 lần. Trọng lượng 455g, TSA-approved mang lên máy bay không bị tịch thu."},

    # ── Smartwatch (3) ──
    {"name": "Apple Watch Series 9 GPS 45mm",       "category": "Smartwatch",       "price": 11_990_000, "stock": 22,
     "image": "watch_apple.png",
     "description": "Chip S9 SiP, màn hình Always-On Retina 2000nit. Double tap gesture mới, Precision Finding iPhone. Theo dõi ECG, SpO2, nhiệt độ da. WatchOS 10, pin 18h, sạc không dây."},
    {"name": "Samsung Galaxy Watch 6 Classic 47mm", "category": "Smartwatch",       "price": 8_990_000,  "stock": 18,
     "image": "watch_samsung.png",
     "description": "Vòng bezel xoay vật lý iconic, Exynos W930 Dual Core, AMOLED 1.5 inch 480x480. BIA body composition, Advanced Sleep Coaching, ECG, huyết áp. 5ATM + IP68, pin 40h."},
    {"name": "Garmin Fenix 7 Pro Solar",            "category": "Smartwatch",       "price": 24_990_000, "stock": 10,
     "image": "watch_apple.png",
     "description": "Sạc năng lượng mặt trời, pin 22 ngày thường. Bản đồ địa hình toàn cầu, VO2 Max, Recovery Time, HRV. Chống va đập, sapphire crystal, dive 10ATM. Đồng hồ thể thao đỉnh cao."},

    # ── Camera (2) ──
    {"name": "Sony Alpha A7 IV Full-Frame",         "category": "Camera",           "price": 68_990_000, "stock": 5,
     "image": "camera_sony_a7.png",
     "description": "33MP BSI CMOS, BIONZ XR. AF 759 điểm phase-detect, eye-tracking realtime. Video 4K 60fps 10-bit. 5-axis IBIS 5.5 stops, dual card CFexpress+SD. EVF 3.68M dots."},
    {"name": "GoPro Hero 12 Black",                 "category": "Camera",           "price": 11_990_000, "stock": 20,
     "image": "camera_gopro.png",
     "description": "Video 5.3K60fps, 27MP photo. HyperSmooth 6.0 chống rung điện tử, Enduro battery. Waterproof 10m không vỏ. BT/Wi-Fi/GPS. GP-Log flat color cho post-processing chuyên nghiệp."},

    # ── Router & Mạng (2) ──
    {"name": "ASUS ROG Rapture GT-AXE16000",        "category": "Router & Mạng",    "price": 22_990_000, "stock": 8,
     "image": "router_asus_ax.png",
     "description": "WiFi 6E quad-band 16000Mbps, băng tần 6GHz mới, 2.5G WAN, 10G LAN. Game Acceleration, VPN Fusion, AiProtection Pro. 8 anten, MU-MIMO 4x4, phủ sóng 500m2."},
    {"name": "TP-Link Deco XE75 WiFi 6E Mesh 3-pack", "category": "Router & Mạng", "price": 7_990_000,  "stock": 22,
     "image": "router_tp_link.png",
     "description": "Mesh WiFi 6E AXE5400 tri-band, phủ sóng 600m2, 300 thiết bị. Backhaul 6GHz riêng biệt, TP-Link HomeShield bảo vệ mạng gia đình. Cài đặt dễ qua app Deco."},
]

# ── Không còn assert cứng số lượng — thêm sản phẩm qua web sẽ không bị lỗi ──
_n = len(PRODUCTS)
_cats = len(set(p["category"] for p in PRODUCTS))
print(f"📦 seed_service loaded: {_n} sản phẩm mẫu, {_cats} danh mục")


# ═══════════════════════════════════════════════════════════════════════════════
#  KHÁCH HÀNG — 30 bản ghi
# ═══════════════════════════════════════════════════════════════════════════════
CUSTOMERS = [
    ("Nguyễn Văn An",       "van.an.nguyen@gmail.com",      "0901111101", "12 Lê Lợi, Hoàn Kiếm, Hà Nội"),
    ("Trần Minh Châu",      "minh.chau.tran@gmail.com",     "0901111102", "45 Nguyễn Trãi, Thanh Xuân, Hà Nội"),
    ("Lê Thị Diễm",         "thi.diem.le@gmail.com",        "0901111103", "78 Cầu Giấy, Cầu Giấy, Hà Nội"),
    ("Phạm Hùng Dũng",      "hung.dung.pham@gmail.com",     "0901111104", "23 Kim Mã, Ba Đình, Hà Nội"),
    ("Hoàng Thị Lan",       "thi.lan.hoang@gmail.com",      "0901111105", "56 Đội Cấn, Ba Đình, Hà Nội"),
    ("Vũ Đình Mạnh",        "dinh.manh.vu@gmail.com",       "0901111106", "89 Xuân Thủy, Cầu Giấy, Hà Nội"),
    ("Đặng Quốc Huy",       "quoc.huy.dang@gmail.com",      "0901111107", "34 Láng Hạ, Đống Đa, Hà Nội"),
    ("Bùi Thu Trang",       "thu.trang.bui@gmail.com",      "0901111108", "67 Văn Phú, Hà Đông, Hà Nội"),
    ("Ngô Thanh Tùng",      "thanh.tung.ngo@gmail.com",     "0901111109", "15 Nguyễn Huệ, Quận 1, TP.HCM"),
    ("Phan Thị Hoa",        "thi.hoa.phan@gmail.com",       "0901111110", "38 Lê Thánh Tôn, Quận 1, TP.HCM"),
    ("Trịnh Văn Bảo",       "van.bao.trinh@gmail.com",      "0901111111", "92 Đinh Tiên Hoàng, Bình Thạnh, TP.HCM"),
    ("Đinh Thị Ngọc",       "thi.ngoc.dinh@gmail.com",      "0901111112", "27 Võ Văn Tần, Quận 3, TP.HCM"),
    ("Mai Xuân Phúc",       "xuan.phuc.mai@gmail.com",      "0901111113", "63 Phan Văn Trị, Gò Vấp, TP.HCM"),
    ("Lý Thị Kim Anh",      "thi.kimanh.ly@gmail.com",      "0901111114", "44 Lý Thường Kiệt, Quận 10, TP.HCM"),
    ("Tô Văn Khải",         "van.khai.to@gmail.com",        "0901111115", "18 Trần Não, Quận 2, TP.HCM"),
    ("Cao Thị Bích",        "thi.bich.cao@gmail.com",       "0901111116", "55 Nguyễn Thị Minh Khai, Quận 1, TP.HCM"),
    ("Nguyễn Đức Tài",      "duc.tai.nguyen2@gmail.com",    "0901111117", "110 Trần Phú, Hải Châu, Đà Nẵng"),
    ("Lê Thị Phương",       "thi.phuong.le2@gmail.com",     "0901111118", "47 Nguyễn Văn Linh, Thanh Khê, Đà Nẵng"),
    ("Phạm Trọng Toàn",     "trong.toan.pham2@gmail.com",   "0901111119", "88 Pasteur, Thanh Khê, Đà Nẵng"),
    ("Huỳnh Thị Sương",     "thi.suong.huynh@gmail.com",    "0901111120", "23 Lê Duẩn, Đông Hà, Quảng Trị"),
    ("Dương Minh Trí",      "minh.tri.duong@gmail.com",     "0901111121", "12 Ngô Quyền, Ninh Kiều, Cần Thơ"),
    ("Trương Thị Mai",      "thi.mai.truong@gmail.com",     "0901111122", "56 3/2, Ninh Kiều, Cần Thơ"),
    ("Lâm Văn Quang",       "van.quang.lam@gmail.com",      "0901111123", "78 Trần Hưng Đạo, Rạch Giá, Kiên Giang"),
    ("Võ Thị Thanh",        "thi.thanh.vo@gmail.com",       "0901111124", "34 Nguyễn Công Trứ, Long Xuyên, An Giang"),
    ("Hà Văn Long",         "van.long.ha@gmail.com",        "0901111125", "66 Lê Lợi, Vinh, Nghệ An"),
    ("Chu Thị Nhi",         "thi.nhi.chu@gmail.com",        "0901111126", "19 Phạm Ngũ Lão, Huế, Thừa Thiên Huế"),
    ("Tăng Minh Khoa",      "minh.khoa.tang@gmail.com",     "0901111127", "45 Bạch Đằng, Quy Nhơn, Bình Định"),
    ("Lưu Thị Hằng",        "thi.hang.luu@gmail.com",       "0901111128", "32 Nguyễn Trãi, Đà Lạt, Lâm Đồng"),
    ("Ký Văn Đức",          "van.duc.ky@gmail.com",         "0901111129", "88 Lê Thánh Tôn, Nha Trang, Khánh Hòa"),
    ("Sầm Thị Linh",        "thi.linh.sam@gmail.com",       "0901111130", "14 Hùng Vương, Buôn Ma Thuột, Đắk Lắk"),
]

ORDER_NOTES = [
    "Khách đã thanh toán tiền mặt",
    "Giao hàng tận nơi, gọi trước 30 phút",
    "Mua trả góp 0% lãi suất 12 tháng",
    "Khách VIP, ưu tiên xử lý nhanh",
    "Tặng kèm túi xách và bộ phụ kiện",
    "Khách đã kiểm tra kỹ trước khi nhận",
    "Xuất hóa đơn VAT theo yêu cầu công ty",
    "Đơn online, đã xác nhận chuyển khoản",
    "Mua kèm gói bảo hành mở rộng 2 năm",
    "Đổi trả trong 7 ngày nếu lỗi sản xuất",
    "", "", "", "", "",  # nhiều đơn không ghi chú
]


# ═══════════════════════════════════════════════════════════════════════════════
#  HÀM SEED CHÍNH
# ═══════════════════════════════════════════════════════════════════════════════
def seed_data(db):
    """Populate database with rich sample data if empty."""
    if db.users.count_documents({}) > 0:
        print("ℹ️  Database already has data, skipping seed.")
        return

    print("🌱 Đang nạp dữ liệu mẫu thực tế...")

    now = datetime.utcnow()

    # ── Users ─────────────────────────────────────────────────────────────────
    users = [
        {"username": "admin",  "email": "admin@techsales.vn",    "full_name": "Nguyễn Quản Trị",
         "role": "admin",  "password_hash": generate_password_hash("admin123").decode("utf-8"),
         "created_at": now},
        {"username": "staff1", "email": "nhanvien1@techsales.vn", "full_name": "Trần Văn Bán Hàng",
         "role": "staff",  "password_hash": generate_password_hash("staff123").decode("utf-8"),
         "created_at": now},
        {"username": "staff2", "email": "nhanvien2@techsales.vn", "full_name": "Lê Thị Thu Ngân",
         "role": "staff",  "password_hash": generate_password_hash("staff123").decode("utf-8"),
         "created_at": now},
    ]
    db.users.insert_many(users)
    print(f"   ✔ {len(users)} tài khoản người dùng")

    # ── Products ──────────────────────────────────────────────────────────────
    product_records = []
    for p in PRODUCTS:
        r = db.products.insert_one({
            "name":        p["name"],
            "category":    p["category"],
            "price":       float(p["price"]),
            "stock":       int(p["stock"]),
            "description": p["description"],
            "image":       p["image"],
            "created_at":  now - timedelta(days=random.randint(30, 365)),
            "updated_at":  now,
        })
        product_records.append({
            "id":    str(r.inserted_id),
            "name":  p["name"],
            "price": float(p["price"]),
            "stock": int(p["stock"]),
        })
    categories = len(set(p["category"] for p in PRODUCTS))
    print(f"   ✔ {len(PRODUCTS)} sản phẩm thuộc {categories} danh mục")

    # ── Customers ─────────────────────────────────────────────────────────────
    customer_records = []
    for name, email, phone, address in CUSTOMERS:
        r = db.customers.insert_one({
            "name":        name,
            "email":       email,
            "phone":       phone,
            "address":     address,
            "total_spent": 0.0,
            "created_at":  now - timedelta(days=random.randint(7, 500)),
        })
        customer_records.append({"id": str(r.inserted_id), "name": name})
    print(f"   ✔ {len(CUSTOMERS)} khách hàng")

    # ── Orders — đúng 100 hóa đơn, trải đều 12 tháng ─────────────────────────
    # Phân bổ có xu hướng tăng nhẹ để Linear Regression có slope dương
    monthly_counts = [5, 6, 6, 7, 8, 8, 9, 9, 10, 10, 11, 11]  # tổng = 100
    random.shuffle(monthly_counts[2:8])  # xáo nhẹ giữa cho tự nhiên

    order_count = 1
    total_created = 0

    for offset, n_orders in enumerate(reversed(monthly_counts)):
        # offset 0 = tháng xa nhất (11 tháng trước), offset 11 = tháng hiện tại
        months_back = len(monthly_counts) - 1 - offset

        # Tính năm/tháng đích
        target_month = now.month - months_back
        target_year = now.year
        while target_month <= 0:
            target_month += 12
            target_year -= 1

        days_in_month = calendar.monthrange(target_year, target_month)[1]

        for _ in range(n_orders):
            day    = random.randint(1, days_in_month)
            hour   = random.randint(8, 21)
            minute = random.randint(0, 59)
            order_date = datetime(target_year, target_month, day, hour, minute)

            # Chọn khách hàng (15% khách vãng lai)
            if random.random() < 0.15:
                cid   = None
                cname = random.choice(["Khách lẻ", "Khách vãng lai", "Mua hộ"])
            else:
                rec   = random.choice(customer_records)
                cid   = rec["id"]
                cname = rec["name"]

            # Chọn 1-4 sản phẩm với trọng số
            n_items   = random.choices([1, 2, 3, 4], weights=[50, 30, 15, 5])[0]
            selected  = random.sample(product_records, min(n_items, len(product_records)))

            items = []
            total = 0.0
            for prod in selected:
                qty      = random.choices([1, 2, 3], weights=[70, 20, 10])[0]
                subtotal = prod["price"] * qty
                total   += subtotal
                items.append({
                    "product_id": prod["id"],
                    "name":       prod["name"],
                    "price":      prod["price"],
                    "qty":        qty,
                    "subtotal":   subtotal,
                })

            order_code = f"HD{order_date.strftime('%Y%m')}{order_count:04d}"
            staff      = random.choice(["admin", "staff1", "staff2"])
            note       = random.choice(ORDER_NOTES)

            db.orders.insert_one({
                "order_code":    order_code,
                "customer_id":   ObjectId(cid) if cid else None,
                "customer_name": cname,
                "items":         items,
                "total":         round(total, 0),
                "status":        "paid",
                "note":          note,
                "created_at":    order_date,
                "created_by":    staff,
            })

            if cid:
                db.customers.update_one(
                    {"_id": ObjectId(cid)},
                    {"$inc": {"total_spent": round(total, 0)}},
                )

            order_count  += 1
            total_created += 1

    print(f"   ✔ {total_created} hóa đơn trải đều 12 tháng")
    print()
    print("=" * 52)
    print("✅  SEED HOÀN TẤT! Thông tin đăng nhập:")
    print("    Admin  : admin   / admin123")
    print("    Staff 1: staff1  / staff123")
    print("    Staff 2: staff2  / staff123")
    print("=" * 52)