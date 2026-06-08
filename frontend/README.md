# Frontend

Next.js App Router UI:

- `/login`
- `/admin/dashboard`
- `/user/dashboard`
- `/user/drive`
- `/user/history`
- `/user/chatbot`

Các page gọi Flask API qua rewrite trong `next.config.ts`. Video stream,
recording và sound cũng được proxy về backend.

```bash
npm ci
npm run dev
npm run build
```
