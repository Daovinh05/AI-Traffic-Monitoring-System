# Backend

Entrypoint:

```bash
python -m backend.app.main
```

Luồng xử lý:

```text
api -> services -> repositories -> db
api -> ai/runtime -> services/repositories/mqtt
```

- `main.py`: Flask app factory và worker lifecycle.
- `extensions.py`: session, CORS và bcrypt.
- `api/`: auth, dashboard, alert, route và stream handlers.
- `services/`: nghiệp vụ và định dạng response.
- `repositories/`: truy vấn MySQL.
- `ai/runtime.py`: model, stream, warning state và traffic counter.
- `assets/`: weights, videos, sounds, pictures và Dlib landmark.

Backend render các giao diện cũ trong `frontend/legacy-templates` và cung cấp
API, AI runtime cho frontend Next.js.

Chạy bằng `.venv` và MySQL local:

```bash
source .venv/bin/activate
python -m backend.app.main
```

Trong môi trường không có audio device:

```bash
SDL_AUDIODRIVER=dummy MQTT_ENABLED=false python -m backend.app.main
```
