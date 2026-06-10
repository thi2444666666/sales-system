# ============================================================
#  Script tự động giải nén & cập nhật dự án Sales System
#  Chạy: .\deploy.ps1
# ============================================================

$zipFile  = "C:\Users\thi24\Downloads\sales-system-updated (1).zip"
$extractTo = "C:\Users\thi24\Downloads\_deploy_temp"
$projectDir = "D:\Doan"

Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "   Sales System - Auto Deploy Script   " -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# 1. Kiểm tra file zip tồn tại
if (-not (Test-Path $zipFile)) {
    Write-Host "[LOI] Khong tim thay file zip:" -ForegroundColor Red
    Write-Host "      $zipFile" -ForegroundColor Yellow
    Write-Host ""
    Write-Host "Vui long kiem tra lai ten file hoac duong dan." -ForegroundColor Yellow
    Read-Host "Nhan Enter de thoat"
    exit 1
}

# 2. Xoá thư mục temp nếu còn sót từ lần trước
if (Test-Path $extractTo) {
    Write-Host "[INFO] Xoa thu muc temp cu..." -ForegroundColor Gray
    Remove-Item -Recurse -Force $extractTo
}

# 3. Giải nén
Write-Host "[1/4] Giai nen file zip..." -ForegroundColor Green
try {
    Expand-Archive -Path $zipFile -DestinationPath $extractTo -Force
    Write-Host "      OK" -ForegroundColor Green
} catch {
    Write-Host "[LOI] Giai nen that bai: $_" -ForegroundColor Red
    Read-Host "Nhan Enter de thoat"
    exit 1
}

# 4. Tìm thư mục gốc bên trong zip (có thể là sales-system/)
$innerFolder = Get-ChildItem -Path $extractTo -Directory | Select-Object -First 1
if ($null -eq $innerFolder) {
    Write-Host "[LOI] Khong tim thay thu muc ben trong zip." -ForegroundColor Red
    Read-Host "Nhan Enter de thoat"
    exit 1
}
$sourceDir = $innerFolder.FullName
Write-Host "      Thu muc nguon: $sourceDir" -ForegroundColor Gray

# 5. Copy đè vào D:\Doan
Write-Host "[2/4] Sao chep file vao $projectDir ..." -ForegroundColor Green
try {
    Copy-Item -Path "$sourceDir\*" -Destination $projectDir -Recurse -Force
    Write-Host "      OK" -ForegroundColor Green
} catch {
    Write-Host "[LOI] Copy that bai: $_" -ForegroundColor Red
    Read-Host "Nhan Enter de thoat"
    exit 1
}

# 6. Dọn __pycache__ và file .pyc
Write-Host "[3/4] Xoa cache Python..." -ForegroundColor Green
Get-ChildItem -Path $projectDir -Recurse -Filter "__pycache__" -ErrorAction SilentlyContinue |
    Remove-Item -Recurse -Force -ErrorAction SilentlyContinue
Get-ChildItem -Path $projectDir -Recurse -Filter "*.pyc" -ErrorAction SilentlyContinue |
    Remove-Item -Force -ErrorAction SilentlyContinue
Write-Host "      OK" -ForegroundColor Green

# 7. Xoá thư mục temp
Write-Host "[4/4] Don dep thu muc tam..." -ForegroundColor Green
Remove-Item -Recurse -Force $extractTo -ErrorAction SilentlyContinue
Write-Host "      OK" -ForegroundColor Green

Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "   Hoan thanh! Du an da duoc cap nhat." -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "Chay ung dung:" -ForegroundColor Yellow
Write-Host "  cd D:\Doan" -ForegroundColor White
Write-Host "  python app.py" -ForegroundColor White
Write-Host ""
Read-Host "Nhan Enter de dong"