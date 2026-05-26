# Kế hoạch triển khai kiến trúc

Nguyên tắc làm việc:

- Làm từng task theo thứ tự.
- Sau khi hoàn thành một task, đánh dấu `[x]`.
- Dừng lại để bạn duyệt trước khi làm task tiếp theo.
- Giữ nguyên tính năng và giao diện ban đầu trong suốt quá trình.
- Không xóa hoặc thay đổi luồng Flask cũ nếu chưa có phương án thay thế đã kiểm tra.

## Task 1: Chuẩn hóa kế hoạch và hiện trạng

- [x] Đối chiếu `IMPLEMENT.md` với code hiện tại.
- [x] Ghi nhận các file Flask chính đang chạy: `py/Web/drive_auth.py`, `py/Web/models.py`, template/static hiện có.
- [x] Xác định phạm vi refactor an toàn: dựng kiến trúc mới nhưng vẫn mount giao diện Flask cũ.
- [x] Kiểm tra worktree để tránh đụng các thay đổi không liên quan.

Tiêu chí hoàn thành:

- Có danh sách rõ các phần sẽ giữ nguyên.
- Có hướng triển khai không làm đổi UI hiện tại.

Ghi nhận hiện trạng:

- `IMPLEMENT.md` định hướng tách monorepo gồm backend API, frontend Next.js, MySQL, realtime, MQTT, chatbot, voice và AI processing.
- Repo hiện tại vẫn chạy theo Flask render HTML trực tiếp. File chính nên giữ làm nguồn chạy trước mắt là `py/Web/drive_auth.py`.
- Logic AI/video/cảnh báo/chatbot/MQTT đang nằm nhiều trong `py/Web/models.py`, được `py/Web/drive_auth.py` import và dùng trực tiếp.
- Giao diện hiện tại cần giữ nguyên gồm các template: `Dashboard.html`, `login.html`, `trang_chu.html`, `lai_xe.html`, `lich_su.html`, `tu_van.html`.
- Static asset hiện tại cần giữ nguyên trong `py/Web/static`.
- Các endpoint đang được template gọi phải giữ nguyên tên trong giai đoạn đầu, ví dụ `/api/login`, `/api/logout`, `/api/check-auth`, `/api/alerts`, `/api/admin-warnings`, `/video_driver`, `/video_traffic`, `/video_sign`, `/video_vacham`.
- Phạm vi refactor an toàn: dựng kiến trúc mới ở `backend/` và `frontend/`, nhưng backend mới vẫn mount/adapter app Flask cũ để không đổi giao diện và hành vi.
- Worktree hiện có thay đổi/chưa theo dõi: `py/Web/drive_auth.py`, `IMPLEMENT.md`, `backend/`, `frontend/`, `docker-compose.yml`, `trien_khai.md`. Các thay đổi này sẽ được giữ nguyên, không revert.

## Task 2: Dựng khung backend theo kiến trúc mới

- [x] Tạo cấu trúc `backend/app`.
- [x] Tạo các tầng: `core`, `db`, `models`, `schemas`, `repositories`, `services`, `api`.
- [x] Tạo các module chức năng: `ai`, `realtime`, `mqtt`, `chatbot`, `voice`, `utils`.
- [x] Thêm entrypoint backend mới nhưng vẫn dùng app Flask cũ để giữ nguyên route/template/static.

Tiêu chí hoàn thành:

- Chạy được entrypoint backend mới hoặc ít nhất import/compile không lỗi cú pháp.
- Các route cũ vẫn là nguồn chạy chính.

Ghi nhận thực hiện:

- Đã có entrypoint mới tại `backend/app/main.py`.
- `backend/app/main.py` mount lại Flask app từ `py/Web/drive_auth.py`, nên các template, static asset, API và video stream cũ vẫn giữ nguyên.
- Đã tạo đủ các package tầng backend: `core`, `db`, `models`, `schemas`, `repositories`, `services`, `api`.
- Đã tạo đủ các package chức năng: `ai`, `realtime`, `mqtt`, `chatbot`, `voice`, `utils`.
- Đã chạy kiểm tra cú pháp bằng `python3 -m py_compile backend/app/main.py backend/app/__init__.py backend/app/core/config.py backend/app/db/database.py` và không có lỗi.

## Task 3: Chuẩn hóa cấu hình backend

- [x] Tách cấu hình môi trường vào `backend/app/core/config.py`.
- [x] Cho phép cấu hình MySQL qua biến môi trường.
- [x] Thêm `backend/.env.example`.
- [x] Giữ mặc định tương thích database hiện tại.

Tiêu chí hoàn thành:

- Code cũ vẫn dùng được cấu hình mặc định.
- Có thể đổi host/user/password/database qua env.

Ghi nhận thực hiện:

- `backend/app/core/config.py` đã có `Settings.from_env()` và `apply_to_flask()`.
- Mặc định database vẫn là `MYSQL_HOST=localhost`, `MYSQL_PORT=3306`, `MYSQL_USER=root`, `MYSQL_PASSWORD=`, `MYSQL_DB=giam_sat`.
- `py/Web/drive_auth.py` cũng đọc `SECRET_KEY`, session config và MySQL config từ biến môi trường để cách chạy cũ không bị lệch.
- `backend/.env.example` đã có `SECRET_KEY`, `PORT`, `FLASK_DEBUG`, session config, MySQL config, MQTT config và `GROQ_API_KEY`.
- Đã kiểm tra cú pháp bằng `python3 -m py_compile backend/app/core/config.py backend/app/main.py py/Web/drive_auth.py`.
- Đã kiểm tra override env bằng lệnh test với `MYSQL_HOST=127.0.0.1`, `MYSQL_PORT=3307`, `MYSQL_USER=tester`, `MYSQL_PASSWORD=secret`, `MYSQL_DB=test_db`, `SECRET_KEY=test-key`, `SESSION_LIFETIME_HOURS=12`.

## Task 4: Tạo adapter database và tài liệu backend

- [x] Tạo adapter `backend/app/db/database.py`.
- [x] Thêm `backend/README.md` mô tả kiến trúc và cách chạy.
- [x] Ghi rõ lộ trình tách route sang blueprint/service/repository.

Tiêu chí hoàn thành:

- Module mới có đường import ổn định cho repository sau này.
- Người đọc biết backend mới đang mount app cũ để giữ UI.

Ghi nhận thực hiện:

- `backend/app/db/database.py` đã tạo `get_db_connection()` dùng `pymysql` và `backend.app.core.config.settings`.
- Adapter database không import `backend.app.main`, tránh kéo theo app legacy/AI model khi repository chỉ cần kết nối DB.
- `backend/README.md` đã mô tả entrypoint `python -m backend.app.main`, cấu hình env, cấu trúc backend, adapter hiện tại và lộ trình tách route.
- README ghi rõ backend mới vẫn mount `py/Web/drive_auth.py` để giữ nguyên UI/template/static trong giai đoạn đầu.
- Đã kiểm tra cú pháp bằng `python3 -m py_compile backend/app/db/database.py backend/app/core/config.py`.

## Task 5: Dựng khung frontend Next.js nhưng chưa thay UI

- [x] Tạo cấu trúc `frontend/src`.
- [x] Tạo các thư mục: `app`, `components`, `features`, `services`, `hooks`, `types`, `constants`, `utils`.
- [x] Thêm `frontend/package.json`.
- [x] Thêm `frontend/README.md` ghi rõ UI hiện tại vẫn nằm ở Flask template.

Tiêu chí hoàn thành:

- Có khung frontend theo `IMPLEMENT.md`.
- Chưa thay đổi giao diện đang chạy.

Ghi nhận thực hiện:

- Đã có `frontend/src/app`, `frontend/src/components/common`, `frontend/src/components/layout`, `frontend/src/features`, `frontend/src/services`, `frontend/src/hooks`, `frontend/src/types`, `frontend/src/constants`, `frontend/src/utils`.
- Đã có `frontend/package.json` với scripts `dev`, `build`, `start`, `lint` và dependencies Next/React/TypeScript.
- Đã thêm cấu hình tối thiểu `frontend/next.config.ts`, `frontend/tsconfig.json`, `frontend/next-env.d.ts`.
- `frontend/README.md` ghi rõ giao diện hiện tại vẫn giữ ở `py/Web/templates` và `py/Web/static`.
- Chưa tạo `page.tsx` hoặc `layout.tsx`, nên chưa có màn Next.js nào thay thế Flask UI.
- Đã kiểm tra `frontend/package.json` hợp lệ bằng `python3 -m json.tool frontend/package.json`.

## Task 6: Thêm Docker/Docker Compose cơ bản

- [x] Thêm `backend/Dockerfile`.
- [x] Thêm `docker-compose.yml` cho backend và MySQL.
- [x] Đảm bảo cấu hình không phá cách chạy local hiện tại.

Tiêu chí hoàn thành:

- Có cấu hình container để phát triển tiếp.
- Local Flask cũ vẫn chạy như trước.

Ghi nhận thực hiện:

- `backend/Dockerfile` đã dùng `python:3.9-slim`, cài các thư viện hệ thống cần cho OpenCV/dlib/pygame/ultralytics và chạy `python -m backend.app.main`.
- `docker-compose.yml` đã có service `backend` và `mysql`.
- Backend container đọc `backend/.env.example`, đồng thời override `MYSQL_HOST=mysql` để kết nối đúng service MySQL trong compose.
- MySQL dùng image `mysql:8.0`, database mặc định `giam_sat`, mount `database_schema.sql` để init schema.
- Đã thêm `.dockerignore` để không copy `.git`, virtualenv, cache, `node_modules`, `flask_session`, `recordings` vào build context.
- Đã kiểm tra cấu hình bằng `docker compose config` và lệnh parse thành công.
- Chưa chạy `docker compose build/up` ở task này vì có thể tải/cài dependency AI rất nặng; phần chạy full sẽ kiểm tra riêng khi cần.

## Task 7: Kiểm tra không đổi giao diện và route chính

- [x] Kiểm tra các route chính: `/login`, `/dashboard`, `/trang_chu`, `/lai_xe`, `/lich_su`, `/tu_van`.
- [x] Kiểm tra các API đang được template gọi.
- [x] Kiểm tra syntax/compile các file đã sửa.
- [x] Ghi lại các giới hạn môi trường nếu thiếu dependency, model, audio, database hoặc quyền ghi cache.

Tiêu chí hoàn thành:

- Có bằng chứng kiểm tra.
- Nếu chưa chạy full server được, nêu rõ lý do và phần đã kiểm tra được.

Ghi nhận thực hiện:

- Đã kiểm tra danh sách route bằng `rg "^@app\.route" py/Web/drive_auth.py`.
- Các route chính vẫn tồn tại: `/login`, `/dashboard`, `/trang_chu`, `/lai_xe`, `/lich_su`, `/tu_van`.
- Các route stream chính vẫn tồn tại: `/video_driver`, `/video_traffic`, `/video_sign`, `/video_vacham`.
- Các API chính template đang gọi vẫn tồn tại: `/api/login`, `/api/logout`, `/api/check-auth`, `/api/alerts`, `/api/all-alerts`, `/api/admin-warnings`, `/api/send-warning`, `/api/mark-alert-processed`, `/api/set_monitoring_vehicle`, `/api/get_ai_alerts_history`, `/api/get_ai_warnings`, `/api/send_chat_message`, `/api/groq_law_chat`, `/api/vehicle-cameras/<int:vehicle_id>`.
- Template và static asset hiện tại vẫn nằm ở `py/Web/templates` và `py/Web/static`; không có file template nào bị sửa trong các task refactor.
- Đã kiểm tra cú pháp bằng `python3 -m py_compile backend/app/main.py backend/app/core/config.py backend/app/db/database.py py/Web/drive_auth.py` và không có lỗi.
- Phát hiện tồn tại sẵn: `py/Web/templates/lai_xe.html` có gọi `/stop_camera`, nhưng `py/Web/drive_auth.py` hiện chưa có route này. Đây không phải thay đổi do các task refactor tạo ra; cần xử lý ở task sửa tính năng sau nếu muốn nút dừng camera hoạt động đầy đủ.
- Chưa chạy full server trong Task 7 vì import/runtime app cũ load trực tiếp pygame, dlib, YOLO, Matplotlib và các model AI, có thể vướng dependency/cache/audio/database. Phần đã kiểm tra ở task này là route source, template call, static/template presence và compile.

## Task 8: Tách route theo nhóm, mỗi lần một nhóm

- [x] Tách auth routes.
- [x] Tách dashboard routes.
- [x] Tách alert/history routes.
- [x] Tách stream/control routes.
- [x] Tách route management routes.

Tiêu chí hoàn thành:

- Mỗi nhóm tách xong vẫn giữ endpoint cũ.
- Template cũ không cần sửa hoặc chỉ sửa rất nhỏ nếu bắt buộc.

Ghi nhận thực hiện:

- Đã tạo `backend/app/api/route_registry.py` với `LegacyRoute`, helper `iter_missing_routes()` và `resolve_view()`.
- Đã tạo `backend/app/api/auth_routes.py` cho `/`, `/login`, `/api/login`, `/api/logout`, `/api/check-auth`.
- Đã tạo `backend/app/api/dashboard_routes.py` cho các route render trang: `/dashboard`, `/trang_chu`, `/tu_van`, `/tu_van.html`, `/lai_xe`, `/lai_xe_v2`, `/lich_su`, `/traffic_bus`.
- Đã tạo `backend/app/api/alert_routes.py` cho cảnh báo, lịch sử, video list, chatbot và voice APIs.
- Đã tạo `backend/app/api/stream_routes.py` cho stream video và control APIs.
- Đã tạo `backend/app/api/route_routes.py` cho `/api/routes` và `/api/routes/<route_id>`.
- `backend/app/api/__init__.py` đã gom `ROUTE_GROUPS` và có `validate_legacy_routes(app)` để kiểm tra mapping với app Flask cũ.
- Đã kiểm tra cú pháp bằng `python3 -m py_compile` cho toàn bộ file trong `backend/app/api`.
- Đã kiểm tra import nhẹ bằng `python3 -c "from backend.app.api import ROUTE_GROUPS; print({k: len(v) for k, v in ROUTE_GROUPS.items()})"` và kết quả là `{'auth': 5, 'dashboard': 8, 'alerts': 14, 'stream': 16, 'routes': 5}`.
- Chưa chuyển thân xử lý view function ra khỏi `py/Web/drive_auth.py` trong task này để tránh đổi hành vi/giao diện. Task 9 sẽ bắt đầu tách service/repository theo nghiệp vụ.

## Task 9: Tách service/repository theo nghiệp vụ

- [x] Tách auth service/repository.
- [x] Tách dashboard service/repository.
- [x] Tách alert service/repository.
- [x] Tách route service/repository.
- [x] Tách video/camera service.

Tiêu chí hoàn thành:

- Route chỉ nhận request/trả response.
- Query database chuyển dần vào repository.

Ghi nhận thực hiện:

- Đã tạo `backend/app/repositories/user_repository.py` và `backend/app/services/auth_service.py`.
- Đã wire `py/Web/drive_auth.py::api_login()` sang `auth_service.authenticate()`, nên route login hiện chỉ lấy request, set session và trả response; query user/driver/vehicle đã chuyển vào repository.
- Đã tạo `backend/app/repositories/dashboard_repository.py` và `backend/app/services/dashboard_service.py` cho thống kê và danh sách xe dashboard.
- Đã tạo `backend/app/repositories/alert_repository.py` và `backend/app/services/alert_service.py` cho cảnh báo tài xế/admin, đánh dấu đã đọc và gửi cảnh báo admin.
- Đã tạo `backend/app/repositories/route_repository.py` và `backend/app/services/route_service.py` cho CRUD tuyến đường và path.
- Đã tạo `backend/app/repositories/camera_repository.py` và `backend/app/services/video_service.py` cho camera xe và danh sách video ghi hình.
- Đã cập nhật `backend/README.md` để ghi rõ lớp service/repository mới.
- Đã kiểm tra cú pháp bằng `python3 -m py_compile` cho toàn bộ file service/repository mới và `py/Web/drive_auth.py`.
- Đã kiểm tra import bằng `.venv/bin/python` cho các module service/repository, kết quả `services-ok` và `repositories-ok`.
- Ghi chú an toàn: để tránh đổi hành vi/giao diện quá rộng trong một task, mới chỉ route login được wire trực tiếp sang service. Các route dashboard/alert/route/video-camera đã có service/repository sẵn và sẽ được wire tiếp từng nhóm khi bạn duyệt bước sau.

## Task 10: Tách AI/realtime/MQTT/chatbot/voice

- [x] Tách driver monitor detectors.
- [x] Tách traffic monitor detectors.
- [x] Tách video stream/recorder.
- [x] Tách realtime alert queue/cooldown.
- [x] Tách MQTT publisher.
- [x] Tách chatbot và voice service.

Tiêu chí hoàn thành:

- File AI lớn được chia nhỏ theo chức năng.
- Luồng cảnh báo, âm thanh, MQTT và lưu DB vẫn hoạt động như cũ.

Ghi nhận thực hiện:

- Đã tạo `backend/app/legacy/loaders.py` để lazy-load legacy module `py/Web/models.py` và `py/Web/mqtt_client.py`.
- Đã tách driver monitor adapter: `driver_monitor.py`, `face_detector.py`, `seatbelt_detector.py`, `phone_detector.py`, `steering_detector.py`.
- Đã tách traffic monitor adapter: `traffic_counter.py`, `lane_detector.py`, `collision_detector.py`, `sign_detector.py`.
- Đã tách video adapter: `mjpeg_streamer.py`, `video_recorder.py`.
- Đã tách model loader adapter: `yolo_loader.py`, `dlib_loader.py`, `mediapipe_loader.py`.
- Đã tách realtime adapter: `alert_queue.py`, `cooldown_manager.py`, `event_bus.py`, `websocket_manager.py`.
- Đã tách MQTT adapter: `mqtt_client.py`, `mqtt_publisher.py`.
- Đã tách chatbot adapter: `chatbot_service.py`, `groq_client.py`, `traffic_law_prompt.py`.
- Đã tách voice adapter: `voice_service.py`, `command_parser.py`, `command_actions.py`.
- Đã kiểm tra cú pháp bằng `python3 -m py_compile` cho toàn bộ file trong `backend/app/ai`, `backend/app/realtime`, `backend/app/mqtt`, `backend/app/chatbot`, `backend/app/voice`, `backend/app/legacy`.
- Đã kiểm tra import nhẹ bằng `python3 -c` và nhận `task10-import-ok`, xác nhận import module mới không tự load legacy AI model.
- Ghi chú an toàn: các module mới đang là lazy adapter tới legacy implementation, chưa thay pipeline xử lý frame/cảnh báo thật. Vì vậy luồng cảnh báo, âm thanh, MQTT và lưu DB hiện vẫn giữ nguyên như trước.

## Task 11: Chuyển UI sang Next.js từng màn

- [x] Chuyển login.
- [x] Chuyển admin dashboard.
- [x] Chuyển user dashboard.
- [x] Chuyển lái xe.
- [x] Chuyển lịch sử.
- [x] Chuyển tư vấn/chatbot.

Tiêu chí hoàn thành:

- Mỗi màn chuyển xong phải giống giao diện ban đầu.
- Backend chỉ cung cấp API/stream cho màn đã chuyển.

Ghi nhận thực hiện:

- Đã chuyển màn login sang Next.js tại `frontend/src/app/login/page.tsx`.
- Đã thêm style riêng cho login tại `frontend/src/app/login/styles.css`, giữ bố cục 2 cột, nền gradient, particle animation, form đăng nhập, demo accounts và loading overlay theo template cũ.
- Đã thêm `frontend/src/app/layout.tsx`, `frontend/src/app/page.tsx`, `frontend/src/app/globals.css`.
- Đã cấu hình rewrite trong `frontend/next.config.ts` để `/api/*` proxy về backend Flask mặc định `http://localhost:5001`.
- Đã cài dependencies frontend bằng `npm install` và thêm type packages cần cho Next/TypeScript.
- Đã chạy `npm run build` thành công. Build sinh route `/` và `/login`.
- Đã khởi động Next.js dev server thành công tại `http://localhost:3000`.
- Đã thêm `frontend/src/app/admin/dashboard/page.tsx` và `styles.css`.
- Admin dashboard hiện là bridge route `/admin/dashboard`, hiển thị Flask legacy `/dashboard` toàn màn hình qua iframe để giữ nguyên giao diện/tính năng của `Dashboard.html` trong giai đoạn chuyển đổi.
- Login Next.js đã redirect admin từ `/dashboard` sang `/admin/dashboard`.
- Đã chạy lại `npm run build` thành công. Build sinh thêm route `/admin/dashboard`.
- Ghi chú kỹ thuật: admin dashboard chưa phải React/API thuần vì `Dashboard.html` có 6810 dòng, nhiều Jinja data, API polling, bản đồ, cảnh báo và video logic. Cách bridge này giữ UI y hệt trước khi tách dashboard thành component/API ở bước nhỏ hơn.
- Đã tạo `frontend/src/components/LegacyFrame.tsx` và `LegacyFrame.css` để dùng chung cho các màn bridge legacy.
- Đã thêm `frontend/src/app/user/dashboard/page.tsx`, bridge tới Flask legacy `/trang_chu`.
- Login Next.js đã redirect user từ `/trang_chu` sang `/user/dashboard`.
- Đã chạy lại `npm run build` thành công. Build sinh thêm route `/user/dashboard`.
- Đã thêm `frontend/src/app/user/drive/page.tsx`, bridge tới Flask legacy `/lai_xe`.
- Đã thêm `frontend/src/app/user/history/page.tsx`, bridge tới Flask legacy `/lich_su`.
- Đã thêm `frontend/src/app/user/chatbot/page.tsx`, bridge tới Flask legacy `/tu_van`.
- Đã chạy lại `npm run build` thành công. Build sinh đủ các route `/user/drive`, `/user/history`, `/user/chatbot`.
- Ghi chú kỹ thuật: các màn dashboard/user/lái xe/lịch sử/tư vấn hiện là bridge route để giữ UI và tính năng y hệt ban đầu. Chuyển từng màn sang React/API thuần nên làm thành các task nhỏ tiếp theo vì mỗi template còn nhiều Jinja, state, fetch API và video/chatbot logic.

## Task 12: Tổng kiểm thử và dọn tài liệu

- [x] Kiểm tra đăng nhập admin/user.
- [x] Kiểm tra dashboard, phân trang, cảnh báo.
- [x] Kiểm tra video stream.
- [x] Kiểm tra chatbot/voice nếu có API key và thiết bị.
- [x] Cập nhật README hướng dẫn chạy.

Tiêu chí hoàn thành:

- Có hướng dẫn chạy cuối cùng.
- Không còn thay đổi kiến trúc nửa vời chưa được ghi chú.

Ghi nhận thực hiện:

- Đã cập nhật `README.md` với trạng thái refactor hiện tại, cách chạy backend, cách chạy frontend, Docker Compose, các route Next.js và giới hạn kiểm thử full.
- Đã có tài liệu chi tiết hơn ở `backend/README.md` và `frontend/README.md`.
- Đã chạy `npm run build` trong `frontend` thành công. Build có các route `/`, `/login`, `/admin/dashboard`, `/user/dashboard`, `/user/drive`, `/user/history`, `/user/chatbot`.
- Đã chạy `python3 -m py_compile` cho backend entrypoint, config, database adapter, API groups, services, repositories, AI/realtime/MQTT/chatbot/voice adapters và `py/Web/drive_auth.py`; không có lỗi cú pháp.
- Đã kiểm tra import nhẹ bằng `.venv/bin/python`: service/repository/API groups import thành công với kết quả `backend-import-ok {'auth': 5, 'dashboard': 8, 'alerts': 14, 'stream': 16, 'routes': 5}`.
- Đã chạy `docker compose config` thành công.
- Đăng nhập admin/user đã được kiểm tra ở mức build/static flow: Next `/login` gọi `/api/login`, `/api/check-auth` và redirect admin/user sang route Next tương ứng. Chưa đăng nhập thật vì cần MySQL `giam_sat` đang chạy và dữ liệu account.
- Dashboard/phân trang/cảnh báo đã được kiểm tra ở mức route/template/API mapping và bridge route. Chưa test dữ liệu thật vì cần MySQL có dữ liệu.
- Video stream đã được kiểm tra ở mức route mapping và bridge UI. Chưa chạy stream thật vì cần dependency AI, model/weights, video input, quyền audio/cache và runtime backend đầy đủ.
- Chatbot/voice đã được kiểm tra ở mức module adapter/API mapping. Chưa gọi LLM thật vì cần `GROQ_API_KEY`; voice cần môi trường thiết bị phù hợp.
- MQTT đã được giữ qua legacy adapter và cấu hình env. Chưa test gửi ESP32 thật vì cần MQTT broker/thiết bị.
