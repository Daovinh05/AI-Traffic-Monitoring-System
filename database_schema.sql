-- ==============================================================================
-- HỆ THỐNG GIÁM SÁT GIAO THÔNG THÔNG MINH AI
-- Database Schema - 6 Bảng Chính
-- ==============================================================================

-- Tạo database
CREATE DATABASE IF NOT EXISTS giam_sat DEFAULT CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
USE giam_sat;

-- ==============================================================================
-- 1. BẢNG `nguoi_dung`: Quản lý tài khoản đăng nhập (Admin/User)
-- ==============================================================================
CREATE TABLE nguoi_dung (
    id INT AUTO_INCREMENT PRIMARY KEY,
    ten_dang_nhap VARCHAR(50) NOT NULL UNIQUE,
    mat_khau VARCHAR(255) NOT NULL,
    vai_tro ENUM('admin', 'user') NOT NULL DEFAULT 'user',
    ho_ten VARCHAR(100) NOT NULL,
    trang_thai_hoat_dong TINYINT(1) DEFAULT 1,
    ngay_tao TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    INDEX idx_ten_dang_nhap (ten_dang_nhap),
    INDEX idx_vai_tro (vai_tro)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ==============================================================================
-- 2. BẢNG `tai_xe`: Hồ sơ tài xế chi tiết
-- ==============================================================================
CREATE TABLE tai_xe (
    id INT AUTO_INCREMENT PRIMARY KEY,
    ma_tai_xe VARCHAR(20) UNIQUE,
    ho_ten VARCHAR(100) NOT NULL,
    so_dien_thoai VARCHAR(20) NULL,
    so_giay_phep_lai_xe VARCHAR(50) NULL,
    diem_danh_gia INT DEFAULT 100 CHECK (diem_danh_gia BETWEEN 0 AND 100),
    trang_thai_hoat_dong TINYINT(1) DEFAULT 1,
    ngay_tao TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    INDEX idx_ma_tai_xe (ma_tai_xe),
    INDEX idx_diem_danh_gia (diem_danh_gia)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ==============================================================================
-- 3. BẢNG `tuyen_duong`: Quản lý các tuyến đường / điểm giám sát
-- ==============================================================================
CREATE TABLE tuyen_duong (
    id VARCHAR(50) PRIMARY KEY,
    ten_tuyen VARCHAR(100) NOT NULL,
    mo_ta TEXT,
    toa_do_lat DECIMAL(10, 8),
    toa_do_lng DECIMAL(11, 8),
    trang_thai ENUM('active', 'waiting', 'offline') DEFAULT 'active',
    
    INDEX idx_trang_thai (trang_thai)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ==============================================================================
-- 4. BẢNG `phuong_tien`: Các xe đang được giám sát
-- ==============================================================================
CREATE TABLE phuong_tien (
    id INT AUTO_INCREMENT PRIMARY KEY,
    bien_so VARCHAR(20) NOT NULL UNIQUE,
    loai_xe VARCHAR(50) DEFAULT 'car',
    hinh_anh_xe VARCHAR(255) DEFAULT 'default-car.png',
    id_tai_xe INT NULL,
    id_tuyen_duong VARCHAR(50) NULL,
    trang_thai_hoat_dong VARCHAR(50) DEFAULT 'Đang dừng',
    toc_do_hien_tai INT DEFAULT 0,
    ngay_cap_nhat TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    
    FOREIGN KEY (id_tai_xe) REFERENCES tai_xe(id) ON DELETE SET NULL,
    FOREIGN KEY (id_tuyen_duong) REFERENCES tuyen_duong(id) ON DELETE SET NULL,
    
    INDEX idx_bien_so (bien_so),
    INDEX idx_loai_xe (loai_xe),
    INDEX idx_tai_xe (id_tai_xe),
    INDEX idx_tuyen_duong (id_tuyen_duong)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ==============================================================================
-- 5. BẢNG `canh_bao_vi_pham`: Cảnh báo do AI đưa ra kèm dẫn chứng video
-- ==============================================================================
CREATE TABLE canh_bao_vi_pham (
    id INT AUTO_INCREMENT PRIMARY KEY,
    loai_vi_pham VARCHAR(50) NOT NULL,
    noi_dung_vi_pham VARCHAR(255) NOT NULL,
    muc_do VARCHAR(20) NOT NULL,
    thoi_gian_vi_pham DATETIME NOT NULL,
    id_phuong_tien INT NULL,
    id_tai_xe INT NULL,
    id_video_ghi_hinh INT NULL,
    da_doc TINYINT(1) DEFAULT 0,
    ngay_tao TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    FOREIGN KEY (id_phuong_tien) REFERENCES phuong_tien(id) ON DELETE SET NULL,
    FOREIGN KEY (id_tai_xe) REFERENCES tai_xe(id) ON DELETE SET NULL,
    
    INDEX idx_loai_vi_pham (loai_vi_pham),
    INDEX idx_muc_do (muc_do),
    INDEX idx_thoi_gian_vi_pham (thoi_gian_vi_pham),
    INDEX idx_da_doc (da_doc)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ==============================================================================
-- 6. BẢNG `thong_bao_admin`: Cảnh báo do Admin tạo ra
-- ==============================================================================
CREATE TABLE thong_bao_admin (
    id INT AUTO_INCREMENT PRIMARY KEY,
    id_admin INT NOT NULL,
    bien_so_xe VARCHAR(20) NOT NULL,
    noi_dung_thong_bao TEXT NOT NULL,
    muc_do_uu_tien ENUM('low', 'medium', 'high') DEFAULT 'low',
    da_doc TINYINT(1) DEFAULT 0,
    ngay_tao TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    ngay_doc TIMESTAMP NULL,
    
    FOREIGN KEY (id_admin) REFERENCES nguoi_dung(id) ON DELETE CASCADE,
    
    INDEX idx_admin (id_admin),
    INDEX idx_bien_so (bien_so_xe),
    INDEX idx_muc_do_uu_tien (muc_do_uu_tien),
    INDEX idx_da_doc (da_doc),
    INDEX idx_ngay_tao (ngay_tao)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ==============================================================================
-- PHẦN 2: DỮ LIỆU MẪU
-- ==============================================================================

-- Dữ liệu 1: Người dùng
INSERT INTO nguoi_dung (ten_dang_nhap, mat_khau, vai_tro, ho_ten) VALUES 
('admin', '$2b$12$R.32832E4rBY27Z0.qK2T.hXoLYb0d4CXYg16S4LwH4fWeS2DmsuG', 'admin', 'Quản Trị Viên Hệ Thống'),
('user', '$2b$12$R.32832E4rBY27Z0.qK2T.hXoLYb0d4CXYg16S4LwH4fWeS2DmsuG', 'user', 'Điều Hành Viên');

-- Dữ liệu 2: Tài xế
INSERT INTO tai_xe (ma_tai_xe, ho_ten, so_dien_thoai, so_giay_phep_lai_xe, diem_danh_gia) VALUES 
('TX01', 'Nguyễn Văn Đức', '0912111111', 'GPLX-001', 98),
('TX02', 'Trần Văn Hoan', '0912222222', 'GPLX-002', 85),
('TX03', 'Lê Thị Đào', '0912333333', 'GPLX-003', 95),
('TX04', 'Phạm Văn Dũng', '0912444444', 'GPLX-004', 90),
('TX05', 'Hoàng Văn Việt', '0912555555', 'GPLX-005', 75),
('TX06', 'Vũ Thị Hồng', '0912666666', 'GPLX-006', 100),
('TX07', 'Công ty Travel', '19001111', 'BUSINESS-001', 100);

-- Dữ liệu 3: Tuyến đường
INSERT INTO tuyen_duong (id, ten_tuyen, mo_ta, toa_do_lat, toa_do_lng, trang_thai) VALUES 
('hanoi', 'Tuyến Võ Chí Công - Hà Nội', 'Tuyến đường huyết mạch nối thẳng vào Trung tâm', 21.0506, 105.8049, 'active'),
('hadong', 'Khu vực Hà Đông', 'Tuyến đường quanh bến xe Yên Nghĩa', 20.9719, 105.7766, 'active'),
('thanhxuan', 'Đường Nguyễn Trãi - Thanh Xuân', 'Tuyến đường có mật độ giao thông cao', 20.9934, 105.8078, 'active'),
('ngatuso', 'Vòng xuyến Ngã Tư Sở', 'Điểm giao cắt trọng yếu, thường xuyên theo dõi', 21.0039, 105.8193, 'waiting');

-- Dữ liệu 4: Phương tiện
INSERT INTO phuong_tien (bien_so, loai_xe, hinh_anh_xe, id_tai_xe, id_tuyen_duong, trang_thai_hoat_dong, toc_do_hien_tai) VALUES 
('29A-111.11', 'car', 'car-avatar-1.jpg', 1, 'hanoi', 'Đang chạy', 45),
('29B-222.22', 'bus', 'bus-avatar.jpg', 2, 'hadong', 'Đang dừng', 0),
('30E-333.33', 'car', 'car-avatar-2.jpg', 3, 'thanhxuan', 'Đang chạy', 30),
('29H-444.44', 'truck', 'truck-avatar.jpg', 4, 'ngatuso', 'Đang chạy', 50),
('15B-555.55', 'bus', 'bus-avatar-2.jpg', 5, 'hanoi', 'Đang chạy', 40),
('30G-666.66', 'car', 'car-avatar-3.jpg', 6, 'hadong', 'Đang chạy', 40),
('29LD-777.77', 'bus', 'travel-bus.jpg', 7, 'thanhxuan', 'Đang chạy', 60);

-- Dữ liệu 5: Cảnh báo vi phạm
INSERT INTO canh_bao_vi_pham (loai_vi_pham, noi_dung_vi_pham, muc_do, thoi_gian_vi_pham, id_phuong_tien, id_tai_xe, da_doc) VALUES
('eye', 'Tài xế nhắm mắt quá lâu', 'critical', '2026-03-12 10:15:00', 1, 1, 0),
('phone', 'Phát hiện dùng điện thoại', 'critical', '2026-03-12 11:20:30', 2, 2, 1),
('yawn', 'Tài xế đang ngáp ngủ', 'warning', '2026-03-12 12:05:15', 3, 3, 0),
('seatbelt', 'Không đeo dây an toàn', 'critical', '2026-03-12 14:10:00', 4, 4, 1),
('collision', 'Cảnh báo va chạm phía trước', 'critical', '2026-03-12 16:45:00', 6, 6, 0);

-- Dữ liệu 6: Thông báo của Admin
INSERT INTO thong_bao_admin (id_admin, bien_so_xe, noi_dung_thong_bao, muc_do_uu_tien, da_doc, ngay_tao) VALUES 
(1, '29A-111.11', 'Đề nghị tài xế Đức dừng xe ở trạm nghỉ tiếp theo, phát hiện mệt mỏi.', 'high', 0, '2026-03-12 10:20:00'),
(1, '29B-222.22', 'Cảnh cáo: Không được sử dụng điện thoại lúc đang lái xe.', 'high', 1, '2026-03-12 11:25:00'),
(1, '15B-555.55', 'Lưu ý giữ khoảng cách an toàn với xe phía trước.', 'medium', 0, '2026-03-12 15:00:00');

-- ==============================================================================
-- XÁC MINH DỮ LIỆU
-- ==============================================================================
SELECT '✓ Database created successfully!' AS status;
SELECT '✓ Tables created: nguoi_dung, tai_xe, tuyen_duong, phuong_tien, canh_bao_vi_pham, thong_bao_admin' AS status;
SELECT '✓ Sample data inserted' AS status;

-- Thống kê nhanh
SELECT 
    (SELECT COUNT(*) FROM nguoi_dung) AS total_users,
    (SELECT COUNT(*) FROM tai_xe) AS total_drivers,
    (SELECT COUNT(*) FROM tuyen_duong) AS total_routes,
    (SELECT COUNT(*) FROM phuong_tien) AS total_vehicles,
    (SELECT COUNT(*) FROM canh_bao_vi_pham) AS total_alerts,
    (SELECT COUNT(*) FROM thong_bao_admin) AS total_admin_warnings;
