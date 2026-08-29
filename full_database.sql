-- phpMyAdmin SQL Dump
-- version 5.2.0
-- https://www.phpmyadmin.net/
--
-- Máy chủ: localhost
-- Thời gian đã tạo: Th3 11, 2026 lúc 05:13 AM
-- Phiên bản máy phục vụ: 10.4.27-MariaDB
-- Phiên bản PHP: 7.4.33

SET SQL_MODE = "NO_AUTO_VALUE_ON_ZERO";
START TRANSACTION;
SET time_zone = "+00:00";


/*!40101 SET @OLD_CHARACTER_SET_CLIENT=@@CHARACTER_SET_CLIENT */;
/*!40101 SET @OLD_CHARACTER_SET_RESULTS=@@CHARACTER_SET_RESULTS */;
/*!40101 SET @OLD_COLLATION_CONNECTION=@@COLLATION_CONNECTION */;
/*!40101 SET NAMES utf8mb4 */;

--
-- Cơ sở dữ liệu: `ai_traffic_monitoring`
--

-- --------------------------------------------------------

--
-- Cấu trúc bảng cho bảng `alerts`
--

CREATE TABLE `alerts` (
  `id` int(11) NOT NULL,
  `vehicle_id` int(11) DEFAULT NULL,
  `driver_id` int(11) DEFAULT NULL,
  `type` enum('eye','yawn','head','phone','seatbelt','hand','collision','lane','obstacle') DEFAULT NULL,
  `message` text DEFAULT NULL,
  `level` enum('critical','warning','info') DEFAULT 'warning',
  `image_path` varchar(255) DEFAULT NULL,
  `video_path` varchar(255) DEFAULT NULL,
  `timestamp` datetime DEFAULT current_timestamp(),
  `is_read` tinyint(4) DEFAULT 0,
  `is_processed` tinyint(4) DEFAULT 0
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

--
-- Đang đổ dữ liệu cho bảng `alerts`
--

INSERT INTO `alerts` (`id`, `vehicle_id`, `driver_id`, `type`, `message`, `level`, `image_path`, `video_path`, `timestamp`, `is_read`, `is_processed`) VALUES
(1, 1, 1, 'eye', 'Tài xế đang nhắm mắt quá lâu', 'critical', NULL, NULL, '2026-03-11 09:32:49', 1, 0),
(2, 1, 1, 'phone', 'Tài xế đang dùng điện thoại', 'critical', NULL, NULL, '2026-03-11 08:32:49', 1, 1),
(3, 1, 1, 'seatbelt', 'Tài xế không đeo dây an toàn', 'critical', NULL, NULL, '2026-03-11 07:32:49', 0, 0),
(4, 1, 1, 'yawn', 'Tài xế đang ngáp ngủ', 'warning', NULL, NULL, '2026-03-11 06:32:49', 1, 1),
(5, 1, 1, 'head', 'Tài xế mất tập trung', 'warning', NULL, NULL, '2026-03-11 05:32:49', 1, 1),
(6, 1, 1, 'hand', 'Không cầm vô lăng', 'warning', NULL, NULL, '2026-03-11 04:32:49', 1, 1),
(7, 2, 1, 'collision', '🚨 Cảnh báo va chạm', 'critical', NULL, NULL, '2026-03-10 10:32:49', 1, 1),
(8, 2, 1, 'lane', '⚠️ Xe đang lệch làn', 'warning', NULL, NULL, '2026-03-10 10:32:49', 1, 1),
(9, 3, 1, 'obstacle', '⚠️ Vật cản phía trước', 'warning', NULL, NULL, '2026-03-09 10:32:49', 1, 1),
(10, 1, 1, 'eye', 'Tài xế đang nhắm mắt quá lâu', 'critical', NULL, NULL, '2026-03-09 10:32:49', 1, 1),
(11, 1, 1, 'phone', 'Tài xế đang dùng điện thoại', 'critical', NULL, NULL, '2026-03-08 10:32:49', 1, 1);

-- --------------------------------------------------------

--
-- Cấu trúc đóng vai cho view `dashboard_stats`
-- (See below for the actual view)
--
CREATE TABLE `dashboard_stats` (
`active_vehicles` bigint(21)
,`active_drivers` bigint(21)
,`today_alerts` bigint(21)
,`today_warnings` bigint(21)
,`today_trips` bigint(21)
,`avg_safety_score` decimal(14,4)
);

-- --------------------------------------------------------

--
-- Cấu trúc bảng cho bảng `drivers`
--

CREATE TABLE `drivers` (
  `id` int(11) NOT NULL,
  `user_id` int(11) DEFAULT NULL,
  `full_name` varchar(100) DEFAULT NULL,
  `phone` varchar(20) DEFAULT NULL,
  `license_number` varchar(50) DEFAULT NULL,
  `experience_years` int(11) DEFAULT NULL,
  `rating` decimal(3,2) DEFAULT 5.00,
  `total_trips` int(11) DEFAULT 0,
  `safety_score` int(11) DEFAULT 100,
  `status` enum('active','inactive','suspended') DEFAULT 'active',
  `created_at` timestamp NOT NULL DEFAULT current_timestamp()
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

--
-- Đang đổ dữ liệu cho bảng `drivers`
--

INSERT INTO `drivers` (`id`, `user_id`, `full_name`, `phone`, `license_number`, `experience_years`, `rating`, `total_trips`, `safety_score`, `status`, `created_at`) VALUES
(1, 2, 'Nguyễn Văn A', '0909123456', 'B2-123456', 5, '5.00', 150, 85, 'active', '2026-03-11 03:32:49');

-- --------------------------------------------------------

--
-- Cấu trúc bảng cho bảng `login_history`
--

CREATE TABLE `login_history` (
  `id` int(11) NOT NULL,
  `user_id` int(11) DEFAULT NULL,
  `ip_address` varchar(45) DEFAULT NULL,
  `user_agent` text DEFAULT NULL,
  `status` enum('success','failed') DEFAULT 'success',
  `created_at` timestamp NOT NULL DEFAULT current_timestamp()
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

--
-- Đang đổ dữ liệu cho bảng `login_history`
--

INSERT INTO `login_history` (`id`, `user_id`, `ip_address`, `user_agent`, `status`, `created_at`) VALUES
(1, 2, '192.168.1.100', 'Mozilla/5.0 Windows Chrome', 'success', '2026-03-11 02:32:49'),
(2, 2, '192.168.1.100', 'Mozilla/5.0 Windows Chrome', 'success', '2026-03-10 03:32:49'),
(3, 1, '192.168.1.50', 'Mozilla/5.0 MacOS Chrome', 'success', '2026-03-11 01:32:49'),
(4, 2, '192.168.1.100', 'Mozilla/5.0 Windows Chrome', 'failed', '2026-03-08 03:32:49');

-- --------------------------------------------------------

--
-- Cấu trúc bảng cho bảng `notifications`
--

CREATE TABLE `notifications` (
  `id` int(11) NOT NULL,
  `user_id` int(11) DEFAULT NULL,
  `type` enum('alert','warning','system','success') DEFAULT 'system',
  `title` varchar(255) DEFAULT NULL,
  `message` text DEFAULT NULL,
  `is_read` tinyint(4) DEFAULT 0,
  `read_at` timestamp NULL DEFAULT NULL,
  `created_at` timestamp NOT NULL DEFAULT current_timestamp()
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

--
-- Đang đổ dữ liệu cho bảng `notifications`
--

INSERT INTO `notifications` (`id`, `user_id`, `type`, `title`, `message`, `is_read`, `read_at`, `created_at`) VALUES
(1, 2, 'alert', 'Cảnh báo an toàn', 'Bạn có 3 vi phạm mới trong hôm nay', 0, NULL, '2026-03-11 02:32:49'),
(2, 2, 'warning', 'Nhắc nhở từ Admin', 'Admin vừa gửi cảnh báo', 0, NULL, '2026-03-11 01:32:49'),
(3, 2, 'success', 'Hoàn thành chuyến xe', 'Chuyến xe T001 hoàn thành. Doanh thu: 2,500,000đ', 1, NULL, '2026-03-10 03:32:49'),
(4, 2, 'system', 'Cập nhật hệ thống', 'Hệ thống đã cập nhật tính năng mới', 1, NULL, '2026-03-09 03:32:49');

-- --------------------------------------------------------

--
-- Cấu trúc bảng cho bảng `routes`
--

CREATE TABLE `routes` (
  `id` int(11) NOT NULL,
  `code` varchar(20) DEFAULT NULL,
  `name` varchar(255) DEFAULT NULL,
  `start_point` varchar(255) DEFAULT NULL,
  `end_point` varchar(255) DEFAULT NULL,
  `distance_km` decimal(10,2) DEFAULT NULL,
  `duration_minutes` int(11) DEFAULT NULL,
  `vehicles_per_day` int(11) DEFAULT NULL,
  `status` enum('active','inactive') DEFAULT 'active',
  `path_coordinates` longtext CHARACTER SET utf8mb4 COLLATE utf8mb4_bin DEFAULT NULL CHECK (json_valid(`path_coordinates`)),
  `created_at` timestamp NOT NULL DEFAULT current_timestamp(),
  `updated_at` timestamp NOT NULL DEFAULT current_timestamp() ON UPDATE current_timestamp()
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

--
-- Đang đổ dữ liệu cho bảng `routes`
--

INSERT INTO `routes` (`id`, `code`, `name`, `start_point`, `end_point`, `distance_km`, `duration_minutes`, `vehicles_per_day`, `status`, `path_coordinates`, `created_at`, `updated_at`) VALUES
(1, 'T001', 'Mỹ Đình - Hải Phòng', 'Bến xe Mỹ Đình', 'Bến xe Hải Phòng', '102.00', 120, 12, 'active', NULL, '2026-03-11 03:32:49', '2026-03-11 03:32:49'),
(2, 'T002', 'Nội Bài - Trung tâm', 'Sân bay Nội Bài', 'Hồ Hoàn Kiếm', '28.00', 45, 45, 'active', NULL, '2026-03-11 03:32:49', '2026-03-11 03:32:49'),
(3, 'T003', 'Hồ Tây - Lăng Bác', 'Hồ Tây', 'Lăng Chủ tịch', '8.00', 25, 28, 'active', NULL, '2026-03-11 03:32:49', '2026-03-11 03:32:49');

-- --------------------------------------------------------

--
-- Cấu trúc bảng cho bảng `statistics`
--

CREATE TABLE `statistics` (
  `id` int(11) NOT NULL,
  `date` date DEFAULT NULL,
  `total_vehicles` int(11) DEFAULT 0,
  `total_drivers` int(11) DEFAULT 0,
  `total_trips` int(11) DEFAULT 0,
  `total_alerts` int(11) DEFAULT 0,
  `total_warnings` int(11) DEFAULT 0,
  `total_violations` int(11) DEFAULT 0,
  `total_revenue` decimal(15,2) DEFAULT 0.00,
  `avg_safety_score` decimal(5,2) DEFAULT 100.00,
  `created_at` timestamp NOT NULL DEFAULT current_timestamp(),
  `updated_at` timestamp NOT NULL DEFAULT current_timestamp() ON UPDATE current_timestamp()
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

--
-- Đang đổ dữ liệu cho bảng `statistics`
--

INSERT INTO `statistics` (`id`, `date`, `total_vehicles`, `total_drivers`, `total_trips`, `total_alerts`, `total_warnings`, `total_violations`, `total_revenue`, `avg_safety_score`, `created_at`, `updated_at`) VALUES
(1, '2026-03-11', 3, 1, 1, 3, 2, 3, '0.00', '85.00', '2026-03-11 03:32:49', '2026-03-11 03:32:49'),
(2, '2026-03-10', 3, 1, 3, 5, 1, 4, '0.00', '84.50', '2026-03-11 03:32:49', '2026-03-11 03:32:49'),
(3, '2026-03-09', 3, 1, 2, 4, 2, 3, '0.00', '86.00', '2026-03-11 03:32:49', '2026-03-11 03:32:49'),
(4, '2026-03-08', 3, 1, 2, 3, 1, 2, '0.00', '87.00', '2026-03-11 03:32:49', '2026-03-11 03:32:49'),
(5, '2026-03-07', 3, 1, 1, 2, 1, 1, '0.00', '88.00', '2026-03-11 03:32:49', '2026-03-11 03:32:49'),
(6, '2026-03-06', 3, 1, 2, 3, 2, 2, '0.00', '86.50', '2026-03-11 03:32:49', '2026-03-11 03:32:49'),
(7, '2026-03-05', 3, 1, 1, 2, 1, 1, '0.00', '87.50', '2026-03-11 03:32:49', '2026-03-11 03:32:49'),
(8, '2026-03-04', 3, 1, 2, 4, 2, 3, '0.00', '85.00', '2026-03-11 03:32:49', '2026-03-11 03:32:49');

-- --------------------------------------------------------

--
-- Cấu trúc bảng cho bảng `trips`
--

CREATE TABLE `trips` (
  `id` int(11) NOT NULL,
  `vehicle_id` int(11) DEFAULT NULL,
  `driver_id` int(11) DEFAULT NULL,
  `route_name` varchar(255) DEFAULT NULL,
  `start_location` varchar(255) DEFAULT NULL,
  `end_location` varchar(255) DEFAULT NULL,
  `start_time` datetime DEFAULT NULL,
  `end_time` datetime DEFAULT NULL,
  `distance_km` decimal(10,2) DEFAULT NULL,
  `status` enum('planned','ongoing','completed','cancelled') DEFAULT 'planned',
  `passengers` int(11) DEFAULT 0,
  `revenue` decimal(12,2) DEFAULT 0.00,
  `rating` int(11) DEFAULT 5,
  `created_at` timestamp NOT NULL DEFAULT current_timestamp()
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

--
-- Đang đổ dữ liệu cho bảng `trips`
--

INSERT INTO `trips` (`id`, `vehicle_id`, `driver_id`, `route_name`, `start_location`, `end_location`, `start_time`, `end_time`, `distance_km`, `status`, `passengers`, `revenue`, `rating`, `created_at`) VALUES
(1, 1, 1, 'T001 - Mỹ Đình - Hải Phòng', 'Bến xe Mỹ Đình', 'Bến xe Hải Phòng', '2026-03-11 09:32:49', '2026-03-11 10:32:49', '102.00', 'ongoing', 45, '0.00', 5, '2026-03-11 03:32:49'),
(2, 1, 1, 'T001 - Mỹ Đình - Hải Phòng', 'Bến xe Mỹ Đình', 'Bến xe Hải Phòng', '2026-03-10 10:32:49', '2026-03-10 10:32:49', '102.00', 'completed', 42, '2500000.00', 5, '2026-03-11 03:32:49'),
(3, 2, 1, 'T002 - Nội Bài - Trung tâm', 'Sân bay Nội Bài', 'Hồ Hoàn Kiếm', '2026-03-11 08:32:49', '2026-03-11 09:32:49', '28.00', 'completed', 4, '350000.00', 4, '2026-03-11 03:32:49'),
(4, 3, 1, 'T003 - Hồ Tây - Lăng Bác', 'Hồ Tây', 'Lăng Chủ tịch', '2026-03-11 07:32:49', '2026-03-11 08:32:49', '8.00', 'completed', 2, '150000.00', 5, '2026-03-11 03:32:49'),
(5, 1, 1, 'T001 - Mỹ Đình - Hải Phòng', 'Bến xe Mỹ Đình', 'Bến xe Hải Phòng', '2026-03-09 10:32:49', '2026-03-09 10:32:49', '102.00', 'completed', 38, '2300000.00', 4, '2026-03-11 03:32:49');

-- --------------------------------------------------------

--
-- Cấu trúc bảng cho bảng `users`
--

CREATE TABLE `users` (
  `id` int(11) NOT NULL,
  `username` varchar(50) DEFAULT NULL,
  `password` varchar(255) DEFAULT NULL,
  `email` varchar(100) DEFAULT NULL,
  `full_name` varchar(100) DEFAULT NULL,
  `role` enum('admin','user') DEFAULT 'user',
  `avatar` varchar(255) DEFAULT NULL,
  `phone` varchar(20) DEFAULT NULL,
  `is_active` tinyint(4) DEFAULT 1,
  `last_login` timestamp NULL DEFAULT NULL,
  `created_at` timestamp NOT NULL DEFAULT current_timestamp(),
  `updated_at` timestamp NOT NULL DEFAULT current_timestamp() ON UPDATE current_timestamp()
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

--
-- Đang đổ dữ liệu cho bảng `users`
--

INSERT INTO `users` (`id`, `username`, `password`, `email`, `full_name`, `role`, `avatar`, `phone`, `is_active`, `last_login`, `created_at`, `updated_at`) VALUES
(1, 'admin', '$2b$12$JxzHeL2A6QMUj2p1/Vp2iesAX2aq7pim865BU72PgKtVG/zYl9ZCe', 'admin@traffic.com', 'Quản trị viên hệ thống', 'admin', NULL, NULL, 1, NULL, '2026-03-11 03:32:49', '2026-03-11 03:36:35'),
(2, 'user', '$2b$12$ky/.i5fAGkuXM3gE3lFfSu5CLVNmy2kicBamm1oy7KJh4HHDbxRiW', 'user@traffic.com', 'Nguyễn Văn A', 'user', NULL, NULL, 1, NULL, '2026-03-11 03:32:49', '2026-03-11 03:36:35');

-- --------------------------------------------------------

--
-- Cấu trúc bảng cho bảng `vehicles`
--

CREATE TABLE `vehicles` (
  `id` int(11) NOT NULL,
  `plate_number` varchar(20) DEFAULT NULL,
  `type` enum('car','bus','truck','taxi','motorbike') DEFAULT NULL,
  `driver_id` int(11) DEFAULT NULL,
  `owner_name` varchar(100) DEFAULT NULL,
  `owner_phone` varchar(20) DEFAULT NULL,
  `status` enum('active','maintenance','inactive') DEFAULT 'active',
  `year` int(11) DEFAULT NULL,
  `km_traveled` decimal(10,2) DEFAULT 0.00,
  `created_at` timestamp NOT NULL DEFAULT current_timestamp(),
  `updated_at` timestamp NOT NULL DEFAULT current_timestamp() ON UPDATE current_timestamp()
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

--
-- Đang đổ dữ liệu cho bảng `vehicles`
--

INSERT INTO `vehicles` (`id`, `plate_number`, `type`, `driver_id`, `owner_name`, `owner_phone`, `status`, `year`, `km_traveled`, `created_at`, `updated_at`) VALUES
(1, '29B-222.22', 'bus', 1, 'Công ty Vận tải ABC', '0909123456', 'active', 2022, '45000.00', '2026-03-11 03:32:49', '2026-03-11 03:32:49'),
(2, '30G-666.66', 'taxi', 1, 'Taxi Hà Nội', '0912345678', 'active', 2021, '78000.00', '2026-03-11 03:32:49', '2026-03-11 03:32:49'),
(3, '29A-111.11', 'car', 1, 'Nguyễn Văn A', '0909123456', 'active', 2023, '12000.00', '2026-03-11 03:32:49', '2026-03-11 03:32:49');

-- --------------------------------------------------------

--
-- Cấu trúc bảng cho bảng `warnings`
--

CREATE TABLE `warnings` (
  `id` int(11) NOT NULL,
  `vehicle_plate` varchar(20) DEFAULT NULL,
  `driver_id` int(11) DEFAULT NULL,
  `message` text DEFAULT NULL,
  `admin_id` int(11) DEFAULT NULL,
  `priority` enum('low','medium','high') DEFAULT 'medium',
  `is_read` tinyint(4) DEFAULT 0,
  `read_at` timestamp NULL DEFAULT NULL,
  `created_at` timestamp NOT NULL DEFAULT current_timestamp()
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

--
-- Đang đổ dữ liệu cho bảng `warnings`
--

INSERT INTO `warnings` (`id`, `vehicle_plate`, `driver_id`, `message`, `admin_id`, `priority`, `is_read`, `read_at`, `created_at`) VALUES
(1, '29B-222.22', 1, 'Tài xế cần cải thiện thái độ lái xe', 1, 'high', 0, NULL, '2026-03-11 02:32:49'),
(2, '29B-222.22', 1, 'Không tuân thủ quy định tốc độ', 1, 'high', 0, NULL, '2026-03-11 01:32:49'),
(3, '30G-666.66', 1, 'Kiểm tra và bảo dưỡng phương tiện', 1, 'medium', 1, NULL, '2026-03-10 03:32:49'),
(4, '29A-111.11', 1, 'Đeo dây an toàn khi lái xe', 1, 'medium', 1, NULL, '2026-03-09 03:32:49'),
(5, '29B-222.22', 1, 'Nghỉ ngơi đầy đủ trước khi lái xe', 1, 'low', 1, NULL, '2026-03-08 03:32:49'),
(6, '30G-666.66', 1, 'Không sử dụng điện thoại khi lái xe', 1, 'high', 1, NULL, '2026-03-07 03:32:49');

-- --------------------------------------------------------

--
-- Cấu trúc cho view `dashboard_stats`
--
DROP TABLE IF EXISTS `dashboard_stats`;

CREATE ALGORITHM=UNDEFINED DEFINER=`root`@`localhost` SQL SECURITY DEFINER VIEW `dashboard_stats`  AS SELECT (select count(0) from `vehicles` where `vehicles`.`status` = 'active') AS `active_vehicles`, (select count(0) from `drivers` where `drivers`.`status` = 'active') AS `active_drivers`, (select count(0) from `alerts` where cast(`alerts`.`timestamp` as date) = curdate()) AS `today_alerts`, (select count(0) from `warnings` where cast(`warnings`.`created_at` as date) = curdate()) AS `today_warnings`, (select count(0) from `trips` where cast(`trips`.`start_time` as date) = curdate()) AS `today_trips`, (select avg(`drivers`.`safety_score`) from `drivers`) AS `avg_safety_score``avg_safety_score`  ;

--
-- Chỉ mục cho các bảng đã đổ
--

--
-- Chỉ mục cho bảng `alerts`
--
ALTER TABLE `alerts`
  ADD PRIMARY KEY (`id`),
  ADD KEY `driver_id` (`driver_id`),
  ADD KEY `idx_vehicle` (`vehicle_id`),
  ADD KEY `idx_type` (`type`),
  ADD KEY `idx_timestamp` (`timestamp`),
  ADD KEY `idx_level` (`level`);

--
-- Chỉ mục cho bảng `drivers`
--
ALTER TABLE `drivers`
  ADD PRIMARY KEY (`id`),
  ADD KEY `user_id` (`user_id`),
  ADD KEY `idx_phone` (`phone`),
  ADD KEY `idx_status` (`status`);

--
-- Chỉ mục cho bảng `login_history`
--
ALTER TABLE `login_history`
  ADD PRIMARY KEY (`id`),
  ADD KEY `idx_user` (`user_id`),
  ADD KEY `idx_created` (`created_at`);

--
-- Chỉ mục cho bảng `notifications`
--
ALTER TABLE `notifications`
  ADD PRIMARY KEY (`id`),
  ADD KEY `idx_user` (`user_id`),
  ADD KEY `idx_type` (`type`),
  ADD KEY `idx_created` (`created_at`);

--
-- Chỉ mục cho bảng `routes`
--
ALTER TABLE `routes`
  ADD PRIMARY KEY (`id`),
  ADD UNIQUE KEY `code` (`code`),
  ADD KEY `idx_code` (`code`),
  ADD KEY `idx_status` (`status`);

--
-- Chỉ mục cho bảng `statistics`
--
ALTER TABLE `statistics`
  ADD PRIMARY KEY (`id`),
  ADD UNIQUE KEY `date` (`date`),
  ADD KEY `idx_date` (`date`);

--
-- Chỉ mục cho bảng `trips`
--
ALTER TABLE `trips`
  ADD PRIMARY KEY (`id`),
  ADD KEY `idx_vehicle` (`vehicle_id`),
  ADD KEY `idx_driver` (`driver_id`),
  ADD KEY `idx_status` (`status`),
  ADD KEY `idx_start_time` (`start_time`);

--
-- Chỉ mục cho bảng `users`
--
ALTER TABLE `users`
  ADD PRIMARY KEY (`id`),
  ADD UNIQUE KEY `username` (`username`),
  ADD UNIQUE KEY `email` (`email`),
  ADD KEY `idx_username` (`username`),
  ADD KEY `idx_email` (`email`),
  ADD KEY `idx_role` (`role`);

--
-- Chỉ mục cho bảng `vehicles`
--
ALTER TABLE `vehicles`
  ADD PRIMARY KEY (`id`),
  ADD UNIQUE KEY `plate_number` (`plate_number`),
  ADD KEY `driver_id` (`driver_id`),
  ADD KEY `idx_plate` (`plate_number`),
  ADD KEY `idx_status` (`status`),
  ADD KEY `idx_type` (`type`);

--
-- Chỉ mục cho bảng `warnings`
--
ALTER TABLE `warnings`
  ADD PRIMARY KEY (`id`),
  ADD KEY `admin_id` (`admin_id`),
  ADD KEY `idx_vehicle` (`vehicle_plate`),
  ADD KEY `idx_driver` (`driver_id`),
  ADD KEY `idx_created` (`created_at`);

--
-- AUTO_INCREMENT cho các bảng đã đổ
--

--
-- AUTO_INCREMENT cho bảng `alerts`
--
ALTER TABLE `alerts`
  MODIFY `id` int(11) NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=12;

--
-- AUTO_INCREMENT cho bảng `drivers`
--
ALTER TABLE `drivers`
  MODIFY `id` int(11) NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=2;

--
-- AUTO_INCREMENT cho bảng `login_history`
--
ALTER TABLE `login_history`
  MODIFY `id` int(11) NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=5;

--
-- AUTO_INCREMENT cho bảng `notifications`
--
ALTER TABLE `notifications`
  MODIFY `id` int(11) NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=5;

--
-- AUTO_INCREMENT cho bảng `routes`
--
ALTER TABLE `routes`
  MODIFY `id` int(11) NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=4;

--
-- AUTO_INCREMENT cho bảng `statistics`
--
ALTER TABLE `statistics`
  MODIFY `id` int(11) NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=9;

--
-- AUTO_INCREMENT cho bảng `trips`
--
ALTER TABLE `trips`
  MODIFY `id` int(11) NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=6;

--
-- AUTO_INCREMENT cho bảng `users`
--
ALTER TABLE `users`
  MODIFY `id` int(11) NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=3;

--
-- AUTO_INCREMENT cho bảng `vehicles`
--
ALTER TABLE `vehicles`
  MODIFY `id` int(11) NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=4;

--
-- AUTO_INCREMENT cho bảng `warnings`
--
ALTER TABLE `warnings`
  MODIFY `id` int(11) NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=7;

--
-- Các ràng buộc cho các bảng đã đổ
--

--
-- Các ràng buộc cho bảng `alerts`
--
ALTER TABLE `alerts`
  ADD CONSTRAINT `alerts_ibfk_1` FOREIGN KEY (`vehicle_id`) REFERENCES `vehicles` (`id`) ON DELETE CASCADE,
  ADD CONSTRAINT `alerts_ibfk_2` FOREIGN KEY (`driver_id`) REFERENCES `drivers` (`id`) ON DELETE SET NULL;

--
-- Các ràng buộc cho bảng `drivers`
--
ALTER TABLE `drivers`
  ADD CONSTRAINT `drivers_ibfk_1` FOREIGN KEY (`user_id`) REFERENCES `users` (`id`) ON DELETE SET NULL;

--
-- Các ràng buộc cho bảng `login_history`
--
ALTER TABLE `login_history`
  ADD CONSTRAINT `login_history_ibfk_1` FOREIGN KEY (`user_id`) REFERENCES `users` (`id`) ON DELETE CASCADE;

--
-- Các ràng buộc cho bảng `notifications`
--
ALTER TABLE `notifications`
  ADD CONSTRAINT `notifications_ibfk_1` FOREIGN KEY (`user_id`) REFERENCES `users` (`id`) ON DELETE CASCADE;

--
-- Các ràng buộc cho bảng `trips`
--
ALTER TABLE `trips`
  ADD CONSTRAINT `trips_ibfk_1` FOREIGN KEY (`vehicle_id`) REFERENCES `vehicles` (`id`) ON DELETE CASCADE,
  ADD CONSTRAINT `trips_ibfk_2` FOREIGN KEY (`driver_id`) REFERENCES `drivers` (`id`) ON DELETE CASCADE;

--
-- Các ràng buộc cho bảng `vehicles`
--
ALTER TABLE `vehicles`
  ADD CONSTRAINT `vehicles_ibfk_1` FOREIGN KEY (`driver_id`) REFERENCES `drivers` (`id`) ON DELETE SET NULL;

--
-- Các ràng buộc cho bảng `warnings`
--
ALTER TABLE `warnings`
  ADD CONSTRAINT `warnings_ibfk_1` FOREIGN KEY (`driver_id`) REFERENCES `drivers` (`id`) ON DELETE SET NULL,
  ADD CONSTRAINT `warnings_ibfk_2` FOREIGN KEY (`admin_id`) REFERENCES `users` (`id`) ON DELETE CASCADE;
COMMIT;

/*!40101 SET CHARACTER_SET_CLIENT=@OLD_CHARACTER_SET_CLIENT */;
/*!40101 SET CHARACTER_SET_RESULTS=@OLD_CHARACTER_SET_RESULTS */;
/*!40101 SET COLLATION_CONNECTION=@OLD_COLLATION_CONNECTION */;
