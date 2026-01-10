# Charon

Prosta aplikacja w Pythonie, która pobiera bieżące i historyczne kursy walut z NBP (tabela A) oraz cenę złota (NBP `/cenyzlota`). Na podstawie odchylenia od średniej z ostatnich dni wyznacza decyzję **kup / sprzedaj / hold**. Frontend realizuje Next.js, a backend to FastAPI + osobny miner zapisujący snapshot do Redisa.

## Wymagania

- Python 3.10+
- Dostęp do internetu (API NBP)

## Instalacja

```bash
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\\Scripts\\activate
pip install -r requirements.txt
```

## Uruchomienie (lokalnie)

API (FastAPI):

```bash
uvicorn services.api.main:app --host 0.0.0.0 --port 8000
```

Miner (cykliczne pobieranie i zapis snapshotu do Redisa):

```bash
python -m services.miner.main
```

### Frontend (Next.js)

Nowy interfejs kliencki w Next.js znajduje się w katalogu `frontend/`. Domyślnie
łączymy się z FastAPI z `api_main.py` (domyślnie port `8000`).

```bash
# 1) Uruchom backend API
uvicorn services.api.main:app --host 0.0.0.0 --port 8000

# 2) Frontend
cd frontend
cp .env.local.example .env.local   # opcjonalnie, aby ustawić adres API
npm install
npm run dev  # http://localhost:3000
```

Zmienne środowiskowe frontu (`frontend/.env.local`):
- `NEXT_PUBLIC_API_BASE` — adres API FastAPI (np. `http://localhost:8000`).
- `NEXT_PUBLIC_REFRESH_SECONDS` — (opcjonalnie) częstotliwość odświeżania w sekundach do wyliczenia "następnego odświeżenia".

### Uruchomienie przez Docker / docker-compose (backend + frontend)

```bash
docker-compose up --build
```

- Backend API FastAPI: `http://127.0.0.1:8000/`
- Frontend Next.js: `http://127.0.0.1:3000/`
- Domyślnie używany jest Postgres (usługa `db`). Poświadczenia i nazwy znajdziesz w `docker-compose.yml`.
- Przy pierwszym starcie `db` wykonuje się skrypt `docker/init-db.sql`, który tworzy rolę i bazę `charon`.
- Logi aplikacji i collectora trafiają do wolumenu `app_logs` (w kontenerze `/app/logs`).
- Możesz nadpisać zmienne środowiskowe (np. `REFRESH_SECONDS`, `SCHEDULER_ENABLED`, `DATABASE_URL`, `LOG_FILE`, `COLLECTOR_LOG_FILE`) w `docker-compose.yml` lub przez `.env`.
- Jeśli wcześniej powstał wolumen `db_data` bez użytkownika `charon`, usuń go przed ponownym uruchomieniem: `docker volume rm charon_db_data`.

Frontend honoruje zmienne `NEXT_PUBLIC_API_BASE` oraz `NEXT_PUBLIC_REFRESH_SECONDS` ustawione w compose (domyślnie `http://api:8000`).

### Konfiguracja przez .env
- Skopiuj `.env.example` do `.env` i dostosuj wartości (dla backendu/minera):
	- `PORT=8000`
	- `DATABASE_URL=sqlite:///charon.db` (lokalnie) lub np. `postgresql+psycopg2://user:pass@localhost/dbname`
	- `REFRESH_SECONDS=3600` (co ile sekund miner odświeża dane z NBP)
	- `REDIS_URL=redis://localhost:6379/0`, `REDIS_CACHE_KEY=charon:cache`
	- `COLLECTOR_LOG_FILE=collector.log` (ścieżka logów collectora)
- Plik `.env` jest ignorowany przez git; wartości możesz nadpisać też zmiennymi środowiskowymi przy uruchomieniu.
- `python-dotenv` wczytuje `.env` automatycznie przy starcie aplikacji.

### Baza danych
- Domyślnie używany jest SQLite (`charon.db` w katalogu projektu).
- Możesz wskazać inny silnik przez `DATABASE_URL` (np. PostgreSQL lub MySQL zgodny z SQLAlchemy).
- Inicjalizacja tabel odbywa się automatycznie przy starcie aplikacji.

## Testy

```bash
pytest
```

### Lint i formatowanie

```bash
ruff check .
black .
mypy .
```

## Jak to działa

- `charon/nbp_client.py` — proste funkcje do pobierania kursów walut i złota z API NBP (bieżące i historyczne).
- `charon/decision.py` — heurystyka decyzji: porównuje ostatni kurs do średniej z ostatnich dni; domyślny próg to ±1% od średniej.
- `charon/db.py` — modele SQLAlchemy i zapisy historii kursów (waluty + złoto), domyślnie SQLite.
- `services/api/main.py` — FastAPI wystawiające snapshot oraz historię z Redisa.
- `services/miner/main.py` — cykliczny collector zapisujący snapshot do Redisa.

Konfigurowalne parametry w `main.py` (oraz przez `.env`):
- `HISTORY_DAYS` — ile dni historii uwzględniać (domyślnie 60).
- `DECISION_BIAS_PERCENT` — próg procentowy odchylenia od średniej dla sygnału kup/sprzedaj (domyślnie 1%).
- `REFRESH_SECONDS` — co ile sekund odświeżać dane z NBP (domyślnie 3600s); na froncie wyświetlana jest informacja o ostatnim i następnym odświeżeniu.
- Zestaw walut jest stały (top10 powyżej) — złoto jest zawsze dołączone.
- `LOG_FILE` — ścieżka do pliku logów (domyślnie `charon.log`, rotacja 1 MB, 3 kopie).
- `LOG_FILE` — ścieżka do pliku logów (domyślnie `charon.log`, rotacja 1 MB, 3 kopie).
- Collector logs: `collector.log` (configurable via `COLLECTOR_LOG_FILE`) - zawiera szczegóły pobrań i zapisu.
- Cache: `REDIS_URL` i `REDIS_ENABLED` — gdy włączone, snapshot danych (items + historia) jest trzymany w Redisie; widoki nie odpytały NBP podczas requestów, korzystają ze snapshotu odświeżanego przez scheduler.

## Notatki

- Endopoint `/health` zwraca prostą odpowiedź JSON do monitoringu.
- W pliku `db/charon.sql` jest szkic schematu bazy MySQL dla ewentualnej persystencji, ale aplikacja działa bez bazy.
