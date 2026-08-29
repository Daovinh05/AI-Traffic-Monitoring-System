-- ========================================
-- DATABASE SCHEMA FOR AI TRAFFIC MONITORING SYSTEM v3.0
-- Hệ thống có phân quyền Admin/User
-- ========================================
-- Cách sử dụng:
-- 1. Mở terminal
-- 2. Chạy: mysql -u root -p < database_schema.sql
-- 3. Hoặc import qua phpMyAdmin
-- ========================================

-- Tạo database mới
CREATE DATABASE IF NOT EXISTS ai_traffic_monitoring
CHARACTER SET utf8mb4
COLLATE utf8mb4_unicode_ci;

USE ai_traffic_monitoring;

-- ========================================
-- TABLE: users (Người dùng - Phân quyền)
-- ========================================
CREATE TABLE IF NOT EXISTS users (
    id INT AUTO_INCREMENT PRIMARY KEY,
    username VARCHAR(50) NOT NULL UNIQUE,
    password VARCHAR(255) NOT NULL,
    email VARCHAR(100) NOT NULL UNIQUE,
    full_name VARCHAR(100) NOT NULL,
    role ENUM('admin', 'user') NOT NULL DEFAULT 'user',
    avatar VARCHAR(255) DEFAULT NULL,
    phone VARCHAR(20) DEFAULT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    last_login TIMESTAMP NULL DEFAULT NULL,
    is_active TINYINT(1) DEFAULT 1,
    INDEX idx_username (username),
    INDEX idx_email (email),
    INDEX idx_role (role)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ========================================
-- TABLE: drivers (Tài xế)
-- ========================================
CREATE TABLE IF NOT EXISTS drivers (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT,
    full_name VARCHAR(100) NOT NULL,
    phone VARCHAR(20),
    license_number VARCHAR(50),
    experience_years INT,
    rating DECIMAL(3,2) DEFAULT 5.0,
    total_trips INT DEFAULT 0,
    safety_score INT DEFAULT 100,
    status ENUM('active', 'inactive', 'suspended') DEFAULT 'active',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE SET NULL,
    INDEX idx_phone (phone),
    INDEX idx_status (status)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ========================================
-- TABLE: vehicles (Phương tiện)
-- ========================================
CREATE TABLE IF NOT EXISTS vehicles (
    id INT AUTO_INCREMENT PRIMARY KEY,
    plate_number VARCHAR(20) NOT NULL UNIQUE,
    type ENUM('car', 'bus', 'truck', 'taxi', 'motorbike') NOT NULL,
    driver_id INT,
    owner_name VARCHAR(100),
    owner_phone VARCHAR(20),
    status ENUM('active', 'maintenance', 'inactive') DEFAULT 'active',
    year INT,
    km_traveled DECIMAL(10,2) DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (driver_id) REFERENCES drivers(id) ON DELETE SET NULL,
    INDEX idx_plate (plate_number),
    INDEX idx_status (status),
    INDEX idx_type (type)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ========================================
-- TABLE: alerts (Cảnh báo AI - Tự động)
-- ========================================
CREATE TABLE IF NOT EXISTS alerts (
    id INT AUTO_INCREMENT PRIMARY KEY,
    vehicle_id INT,
    driver_id INT,
    type ENUM('eye', 'yawn', 'head', 'phone', 'seatbelt', 'hand', 'collision', 'lane', 'obstacle') NOT NULL,
    message TEXT NOT NULL,
    level ENUM('critical', 'warning', 'info') DEFAULT 'warning',
    image_path VARCHAR(255),
    video_path VARCHAR(255),
    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
    is_read TINYINT(1) DEFAULT 0,
    is_processed TINYINT(1) DEFAULT 0,
    FOREIGN KEY (vehicle_id) REFERENCES vehicles(id) ON DELETE CASCADE,
    FOREIGN KEY (driver_id) REFERENCES drivers(id) ON DELETE SET NULL,
    INDEX idx_vehicle (vehicle_id),
    INDEX idx_type (type),
    INDEX idx_timestamp (timestamp),
    INDEX idx_level (level)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ========================================
-- TABLE: warnings (Cảnh cáo từ Admin → User)
-- ========================================
CREATE TABLE IF NOT EXISTS warnings (
    id INT AUTO_INCREMENT PRIMARY KEY,
    vehicle_plate VARCHAR(20) NOT NULL,
    driver_id INT,
    message TEXT NOT NULL,
    admin_id INT NOT NULL,
    priority ENUM('low', 'medium', 'high') DEFAULT 'medium',
    is_read TINYINT(1) DEFAULT 0,
    read_at TIMESTAMP NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (driver_id) REFERENCES drivers(id) ON DELETE SET NULL,
    FOREIGN KEY (admin_id) REFERENCES users(id) ON DELETE CASCADE,
    INDEX idx_vehicle (vehicle_plate),
    INDEX idx_driver (driver_id),
    INDEX idx_created (created_at)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ========================================
-- TABLE: trips (Chuyến xe)
-- ========================================
CREATE TABLE IF NOT EXISTS trips (
    id INT AUTO_INCREMENT PRIMARY KEY,
    vehicle_id INT NOT NULL,
    driver_id INT NOT NULL,
    route_name VARCHAR(255),
    start_location VARCHAR(255),
    end_location VARCHAR(255),
    start_time DATETIME,
    end_time DATETIME,
    distance_km DECIMAL(10,2),
    status ENUM('planned', 'ongoing', 'completed', 'cancelled') DEFAULT 'planned',
    passengers INT DEFAULT 0,
    revenue DECIMAL(12,2) DEFAULT 0,
    rating INT DEFAULT 5,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (vehicle_id) REFERENCES vehicles(id) ON DELETE CASCADE,
    FOREIGN KEY (driver_id) REFERENCES drivers(id) ON DELETE CASCADE,
    INDEX idx_vehicle (vehicle_id),
    INDEX idx_driver (driver_id),
    INDEX idx_status (status),
    INDEX idx_start_time (start_time)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ========================================
-- TABLE: routes (Tuyến đường)
-- ========================================
CREATE TABLE IF NOT EXISTS routes (
    id INT AUTO_INCREMENT PRIMARY KEY,
    code VARCHAR(20) UNIQUE,
    name VARCHAR(255) NOT NULL,
    start_point VARCHAR(255),
    end_point VARCHAR(255),
    distance_km DECIMAL(10,2),
    duration_minutes INT,
    vehicles_per_day INT,
    status ENUM('active', 'inactive') DEFAULT 'active',
    path_coordinates JSON,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    INDEX idx_code (code),
    INDEX idx_status (status)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ========================================
-- TABLE: notifications (Thông báo hệ thống)
-- ========================================
CREATE TABLE IF NOT EXISTS notifications (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT,
    type ENUM('alert', 'warning', 'system', 'success') DEFAULT 'info',
    title VARCHAR(255),
    message TEXT,
    is_read TINYINT(1) DEFAULT 0,
    read_at TIMESTAMP NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    INDEX idx_user (user_id),
    INDEX idx_type (type),
    INDEX idx_created (created_at)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ========================================
-- TABLE: login_history (Lịch sử đăng nhập)
-- ========================================
CREATE TABLE IF NOT EXISTS login_history (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT NOT NULL,
    ip_address VARCHAR(45),
    user_agent TEXT,
    status ENUM('success', 'failed') DEFAULT 'success',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    INDEX idx_user (user_id),
    INDEX idx_created (created_at)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ========================================
-- TABLE: statistics (Thống kê hàng ngày)
-- ========================================
CREATE TABLE IF NOT EXISTS statistics (
    id INT AUTO_INCREMENT PRIMARY KEY,
    date DATE NOT NULL,
    total_vehicles INT DEFAULT 0,
    total_drivers INT DEFAULT 0,
    total_trips INT DEFAULT 0,
    total_alerts INT DEFAULT 0,
    total_warnings INT DEFAULT 0,
    total_violations INT DEFAULT 0,
    total_revenue DECIMAL(15,2) DEFAULT 0,
    avg_safety_score DECIMAL(5,2) DEFAULT 100,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    UNIQUE KEY unique_date (date),
    INDEX idx_date (date)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ========================================
-- INSERT DỮ LIỆU MẪU
-- ========================================

-- Users mặc định (password: admin123 / user123)
-- Password được hash bằng bcrypt
INSERT INTO users (username, password, email, full_name, role, is_active) VALUES
('admin', '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewY5GyYzS3MebAJu', 'admin@traffic.com', 'Quản trị viên hệ thống', 'admin', 1),
('user', '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewY5GyYzS3MebAJu', 'user@traffic.com', 'Tài xế mẫu', 'user', 1);

-- Drivers mẫu
INSERT INTO drivers (user_id, full_name, phone, license_number, experience_years, rating, total_trips, safety_score, status) VALUES
(2, 'Nguyễn Văn A', '0909123456', 'B2-123456', 5, 4.8, 150, 85, 'active');

-- Vehicles mẫu
INSERT INTO vehicles (plate_number, type, driver_id, owner_name, owner_phone, status, year, km_traveled) VALUES
('29B-222.22', 'bus', 1, 'Công ty Vận tải ABC', '0909123456', 'active', 2022, 45230),
('30G-666.66', 'taxi', 1, 'Taxi Hà Nội', '0912345678', 'active', 2021, 78450),
('29A-111.11', 'car', 1, 'Nguyễn Văn A', '0909123456', 'active', 2023, 12890);

-- Routes mẫu
INSERT INTO routes (code, name, start_point, end_point, distance_km, duration_minutes, vehicles_per_day, status) VALUES
('T001', 'Mỹ Đình - Hải Phòng', 'Bến xe Mỹ Đình', 'Bến xe Hải Phòng', 102, 120, 12, 'active'),
('T002', 'Nội Bài - Trung tâm Hà Nội', 'Sân bay Nội Bài', 'Hồ Hoàn Kiếm', 28, 45, 45, 'active'),
('T003', 'Hồ Tây - Lăng Bác', 'Hồ Tây', 'Lăng Chủ tịch', 8, 25, 28, 'active');

-- ========================================
-- VIEW: Thống kê tổng hợp
-- ========================================
CREATE OR REPLACE VIEW dashboard_stats AS
SELECT 
    (SELECT COUNT(*) FROM vehicles WHERE status = 'active') as active_vehicles,
    (SELECT COUNT(*) FROM drivers WHERE status = 'active') as active_drivers,
    (SELECT COUNT(*) FROM alerts WHERE DATE(timestamp) = CURDATE()) as today_alerts,
    (SELECT COUNT(*) FROM warnings WHERE DATE(created_at) = CURDATE()) as today_warnings,
    (SELECT COUNT(*) FROM trips WHERE DATE(start_time) = CURDATE()) as today_trips,
    (SELECT AVG(safety_score) FROM drivers) as avg_safety_score;

-- ========================================
-- STORED PROCEDURE: Cập nhật thống kê hàng ngày
-- ========================================
DELIMITER //
CREATE PROCEDURE update_daily_statistics(IN stat_date DATE)
BEGIN
    INSERT INTO statistics (date, total_vehicles, total_drivers, total_trips, total_alerts, total_warnings, total_violations, avg_safety_score)
    SELECT 
        stat_date,
        (SELECT COUNT(*) FROM vehicles),
        (SELECT COUNT(*) FROM drivers),
        (SELECT COUNT(*) FROM trips WHERE DATE(start_time) = stat_date),
        (SELECT COUNT(*) FROM alerts WHERE DATE(timestamp) = stat_date),
        (SELECT COUNT(*) FROM warnings WHERE DATE(created_at) = stat_date),
        (SELECT COUNT(*) FROM alerts WHERE DATE(timestamp) = stat_date AND level = 'critical'),
        (SELECT AVG(safety_score) FROM drivers)
    ON DUPLICATE KEY UPDATE
        total_vehicles = VALUES(total_vehicles),
        total_drivers = VALUES(total_drivers),
        total_trips = VALUES(total_trips),
        total_alerts = VALUES(total_alerts),
        total_warnings = VALUES(total_warnings),
        total_violations = VALUES(total_violations),
        avg_safety_score = VALUES(avg_safety_score);
END //
DELIMITER ;

-- ========================================
-- TRIGGER: Tự động cập nhật thống kê khi có alert mới
-- ========================================
DELIMITER //
CREATE TRIGGER after_alert_insert
AFTER INSERT ON alerts
FOR EACH ROW
BEGIN
    CALL update_daily_statistics(CURDATE());
END //
DELIMITER ;

-- ========================================
-- GRANT PERMISSIONS (nếu cần)
-- ========================================
-- CREATE USER IF NOT EXISTS 'traffic_app'@'localhost' IDENTIFIED BY 'your_password';
-- GRANT ALL PRIVILEGES ON ai_traffic_monitoring.* TO 'traffic_app'@'localhost';
-- FLUSH PRIVILEGES;

-- ========================================
-- KẾT THÚC
-- ========================================
-- File này đã tạo:
-- ✅ 11 tables cho hệ thống phân quyền Admin/User
-- ✅ Dữ liệu mẫu (users, drivers, vehicles, routes)
-- ✅ View dashboard_stats
-- ✅ Stored procedure update_daily_statistics
-- ✅ Trigger tự động cập nhật thống kê
-- 
-- Tài khoản mặc định:
-- 👮 Admin: username=admin, password=admin123
-- 👤 User:  username=user, password=user123
-- ========================================
