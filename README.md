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

### Konfiguracja przez .env
- Skopiuj `.env.example` do `.env` i dostosuj wartości:
	- `PORT=5000`
	- `DATABASE_URL=sqlite:///charon.db` (lub np. `postgresql://user:pass@localhost/dbname`)
	- `REFRESH_SECONDS=3600` (co ile sekund odświeżać dane z NBP)
	- `CURRENCIES` (opcjonalnie lista kodów oddzielona przecinkami; jeśli pusta, pobierane są wszystkie z tabeli A)
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

## Jak to działa

- `charon/nbp_client.py` — proste funkcje do pobierania kursów walut i złota z API NBP (bieżące i historyczne).
- `charon/decision.py` — heurystyka decyzji: porównuje ostatni kurs do średniej z ostatnich dni; domyślny próg to ±1% od średniej.
- `charon/db.py` — modele SQLAlchemy i zapisy historii kursów (waluty + złoto), domyślnie SQLite.
- `main.py` — uruchamia Flask, pobiera dane (wszystkie waluty z tabeli A + złoto), zapisuje je do bazy, buforuje i renderuje frontend (`templates/index.html`).

Konfigurowalne parametry w `main.py` (oraz przez `.env`):
- `CURRENCIES` (env `CURRENCIES`) — opcjonalna lista kodów walut; domyślnie wszystkie z tabeli A.
- `HISTORY_DAYS` — ile dni historii uwzględniać (domyślnie 60).
- `DECISION_BIAS_PERCENT` — próg procentowy odchylenia od średniej dla sygnału kup/sprzedaj (domyślnie 1%).
- `REFRESH_SECONDS` — co ile sekund odświeżać dane z NBP (domyślnie 3600s); na froncie wyświetlana jest informacja o ostatnim i następnym odświeżeniu.

## Notatki

- Endopoint `/health` zwraca prostą odpowiedź JSON do monitoringu.
- W pliku `db/charon.sql` jest szkic schematu bazy MySQL dla ewentualnej persystencji, ale aplikacja działa bez bazy.
