-- ========================================
-- RESET PASSWORD FOR USERS
-- Chạy trong phpMyAdmin khi quên mật khẩu
-- ========================================

USE ai_traffic_monitoring;

-- Password: admin123
UPDATE users SET password = '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewY5GyYzS3MebAJu' 
WHERE username = 'admin';

-- Password: user123
UPDATE users SET password = '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewY5GyYzS3MebAJu' 
WHERE username = 'user';

-- Xong! Giờ có thể đăng nhập với:
-- Admin: admin / admin123
-- User: user / user123
