# Quiz Conquest

Мултиплейър куиз игра за завладяване на територии.

- `backend/` — Django 5.2 + Django REST Framework
- `frontend/` — React + Vite

## Стартиране

### Backend

Windows PowerShell:

```powershell
cd backend
py -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
python manage.py migrate
python manage.py runserver
```

Linux / macOS:

```bash
cd backend
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
python manage.py migrate
python manage.py runserver
```

Backend: `http://127.0.0.1:8000/`, Django admin: `http://127.0.0.1:8000/admin/`

```bash
python manage.py createsuperuser
```

### Frontend

```bash
cd frontend
npm install
npm run dev
```

Frontend: `http://localhost:5173/`

Vite dev сървърът проксира `/api` към Django, така че session и CSRF cookies работят в рамките на един origin.

## Банка с въпроси

Начални данни (6 категории, 12 choice и 12 numeric въпроса) от основната папка:

```bash
python backend/manage.py loaddata questions/question_bank.json
```

Въпросите се управляват през Django admin (`/admin/`).

## Тестове

От папка `backend/`:

```bash
python manage.py test
```

По приложения:

```bash
python manage.py test accounts
python manage.py test questions
python manage.py test games
```

## Authentication API

| Method | Endpoint | Достъп |
|---|---|---|
| `GET` | `/api/auth/csrf/` | Public |
| `POST` | `/api/auth/register/` | Public |
| `POST` | `/api/auth/login/` | Public |
| `POST` | `/api/auth/logout/` | Authenticated |
| `GET` | `/api/auth/me/` | Authenticated |
| `PATCH` | `/api/auth/me/` | Authenticated |

Грешките се връщат в единен формат:

```json
{ "errors": { "field": ["message"] } }
```
