# Frontend

Giao diện hiện tại vẫn được giữ nguyên trong `py/Web/templates` và
`py/Web/static` để đảm bảo UI giống bản ban đầu.

Thư mục này là khung Next.js theo kiến trúc trong `IMPLEMENT.md`. Khi tách UI
sang React/Next.js, hãy chuyển từng màn theo thứ tự an toàn:

1. `login.html` -> `src/app/login/page.tsx`
2. `Dashboard.html` -> `src/app/admin/dashboard/page.tsx`
3. `trang_chu.html` -> `src/app/user/dashboard/page.tsx`
4. `lai_xe.html`, `lich_su.html`, `tu_van.html` -> các route user tương ứng

Trong giai đoạn hiện tại, backend mới vẫn mount Flask template cũ nên không có
thay đổi giao diện.

## Trạng thái chuyển màn

- `src/app/login/page.tsx`: đã chuyển sang React/Next.js.
- `src/app/admin/dashboard/page.tsx`: đang là bridge route hiển thị dashboard
  Flask legacy toàn màn hình để giữ nguyên giao diện và tính năng trong khi tách
  dần dữ liệu/API khỏi `Dashboard.html`.
- `src/app/user/dashboard/page.tsx`: đang là bridge route hiển thị trang chủ
  user Flask legacy toàn màn hình để giữ nguyên giao diện và tính năng.
- `src/app/user/drive/page.tsx`: bridge route tới `/lai_xe`.
- `src/app/user/history/page.tsx`: bridge route tới `/lich_su`.
- `src/app/user/chatbot/page.tsx`: bridge route tới `/tu_van`.
