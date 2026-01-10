# Charon

Prosta aplikacja w Pythonie, która pobiera bieżące i historyczne kursy walut z NBP (tabela A) oraz cenę złota (NBP `/cenyzlota`). Na podstawie odchylenia od średniej z ostatnich dni wyznacza decyzję **kup / sprzedaj / hold** i prezentuje dane w prostym froncie webowym.

## Wymagania

- Python 3.10+
- Dostęp do internetu (API NBP)

## Instalacja

```bash
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\\Scripts\\activate
pip install -r requirements.txt
```

## Uruchomienie

```bash
python main.py
```

Aplikacja startuje na `http://127.0.0.1:5000/`.

### Uruchomienie przez Docker / docker-compose

```bash
docker-compose up --build
```

- Aplikacja będzie dostępna na `http://127.0.0.1:5000/`.
- Domyślnie używany jest Postgres (usługa `db`). Poświadczenia i nazwy znajdziesz w `docker-compose.yml`.
- Przy pierwszym starcie `db` wykonuje się skrypt `docker/init-db.sql`, który tworzy rolę i bazę `charon`.
- Logi aplikacji i collectora trafiają do wolumenu `app_logs` (w kontenerze `/app/logs`).
- Możesz nadpisać zmienne środowiskowe (np. `REFRESH_SECONDS`, `SCHEDULER_ENABLED`, `DATABASE_URL`, `LOG_FILE`, `COLLECTOR_LOG_FILE`) w `docker-compose.yml` lub przez `.env`.
- Jeśli wcześniej powstał wolumen `db_data` bez użytkownika `charon`, usuń go przed ponownym uruchomieniem: `docker volume rm charon_db_data`.

### Konfiguracja przez .env
- Skopiuj `.env.example` do `.env` i dostosuj wartości:
	- `PORT=5000`
	- `DATABASE_URL=sqlite:///charon.db` (lokalnie) lub np. `postgresql+psycopg2://user:pass@localhost/dbname`
	- `REFRESH_SECONDS=3600` (co ile sekund odświeżać dane z NBP)
	- `SCHEDULER_ENABLED=1` (włącza zadanie okresowego odświeżania)
	- `LOG_FILE=charon.log`, `COLLECTOR_LOG_FILE=collector.log` (ścieżki logów)
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
- `main.py` — uruchamia Flask (w obrazie serwowany przez gunicorn), pobiera dane (złoto + top10 walut: USD, EUR, JPY, GBP, AUD, CAD, CHF, CNY, SEK, NZD, NOK), zapisuje je do bazy, buforuje i renderuje frontend (`templates/index.html`).

Konfigurowalne parametry w `main.py` (oraz przez `.env`):
- `HISTORY_DAYS` — ile dni historii uwzględniać (domyślnie 60).
- `DECISION_BIAS_PERCENT` — próg procentowy odchylenia od średniej dla sygnału kup/sprzedaj (domyślnie 1%).
- `REFRESH_SECONDS` — co ile sekund odświeżać dane z NBP (domyślnie 3600s); na froncie wyświetlana jest informacja o ostatnim i następnym odświeżeniu.
- Zestaw walut jest stały (top10 powyżej) — złoto jest zawsze dołączone.
- `LOG_FILE` — ścieżka do pliku logów (domyślnie `charon.log`, rotacja 1 MB, 3 kopie).
- `LOG_FILE` — ścieżka do pliku logów (domyślnie `charon.log`, rotacja 1 MB, 3 kopie).
- Collector logs: `collector.log` (configurable via `COLLECTOR_LOG_FILE`) - zawiera szczegóły pobrań i zapisu.

## Notatki

- Endopoint `/health` zwraca prostą odpowiedź JSON do monitoringu.
- W pliku `db/charon.sql` jest szkic schematu bazy MySQL dla ewentualnej persystencji, ale aplikacja działa bez bazy.
