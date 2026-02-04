Plan

Tytuł
System “Charon” do pobierania kursów NBP (waluty + złoto), obliczania trendów i publikacji na publicznym dashboardzie.

Streszczenie
Cztery kontenery: miner (pobiera dane co godzinę, nadrabia historię), api (FastAPI), brain (oblicza sygnały BUY/HOLD/SELL), frontend (Streamlit z wykresami, tabelami i statusem minera). Dane trzymamy w PostgreSQL; opcjonalny Redis na cache. Modularny interfejs źródeł umożliwia dodawanie kolejnych providerów.

Architektura i przepływ danych

PostgreSQL (instancja zewnętrzna lub osobny kontener poza “czwórką” wymaganych usług).
miner → zapis do DB (tabele rates, gold_prices, jobs_log). Po każdym wsadzie emituje event (np. INSERT trigger lub Redis pub/sub) → brain.
brain pobiera nowe dane, przelicza metryki (EMA12/EMA26, MACD, sygnał 9), zapisuje do signals oraz analysis_snapshots.
api serwuje dane i sygnały, udostępnia statystyki minera, listę jobów oraz zdrowie systemu.
frontend czyta wyłącznie przez API.
Schemat bazy (kluczowe tabele)

currencies(code PK, name, source)
rates(id PK, code FK currencies, rate_mid NUMERIC, effective_date DATE, fetched_at TIMESTAMPTZ, source) indeks (code, effective_date) uniq.
gold_prices(id PK, price NUMERIC, effective_date DATE, fetched_at TIMESTAMPTZ, source)
jobs_log(id PK, job_type, status, started_at, finished_at, rows_written, error)
signals(id PK, asset_code, signal ENUM[BUY,HOLD,SELL], macd NUMERIC, signal_line NUMERIC, histogram NUMERIC, generated_at, horizon_days)
analysis_snapshots(id PK, asset_code, window, stats JSONB, generated_at)
Wspólne widoki/CTE na API do łączenia walut i złota.
Kontener miner

Python + httpx + APScheduler; uruchamia się co 1h (cron 0 * * * *).
Startup: sprawdza brak danych → ściąga pełną historię NBP (waluty: /api/exchangerates/tables/A, złoto: /api/cenyzlota, porcjowanie wg limitu 93 dni/żądanie).
Inkrementalnie: pobiera dzień bieżący; jeśli nie ma w DB, dopisuje. Obsługa weekendów/świąt (NBP brak notowań) – zapis statusu w jobs_log bez błędu.
Plug-in źródeł: interfejs SourceClient (metody fetch_rates(from,to), fetch_gold(from,to)), implementacja NBPClient; łatwe dodanie innych providerów.
Kontener brain

Python, działa jako worker (APS / Celery-beat opcjonalnie).
Reaguje na: 1) timer co godzinę, 2) event po insertach.
Logika: liczy EMA12/EMA26, MACD, signal 9; sygnał:
BUY gdy macd_cross_up lub histogram > 0 po ujemnym,
SELL gdy macd_cross_down lub histogram < 0 po dodatnim,
HOLD w pozostałych.
Parametry okna konfigurowalne (.env). Wyniki zapisuje w signals i analysis_snapshots.
Kontener api (FastAPI)

Endpointy:
GET /health
GET /sources (lista dostępnych providerów)
GET /rates?code=USD&from=2024-01-01&to=2024-02-01
GET /gold?from&to
GET /signals?code=USD&limit=100
GET /stats/miner (ostatnie joby, średni czas, rows_written)
GET /stats/upcoming (harmonogram)
POST /sources (rejestracja nowego providera – na razie stub)
Paginacja, filtrowanie, CORS dla frontu, rate limiting (np. slowapi), cache Redis (TTL 5 min).
Kontener frontend (Streamlit)

Zakładki:
“Dashboard” – wykres świecowy/wstęgowy waluty, MACD, tabela sygnałów.
“Złoto” – wykres cen złota, sygnały.
“Miner” – tabela jobs_log, liczba rekordów per job, statusy, harmonogram.
Odświeżanie co 60 s; środowisko publiczne (brak logowania zgodnie z wyborem).
Konfiguracja i infra

.env: DATABASE_URL (PostgreSQL prod), REFRESH_SECONDS=3600, REDIS_URL, api.nbp.pl, parametry EMA.
Docker Compose (dev): kontenery 4x + postgres + opcjonalnie redis. W CI build 3 obrazy (api, miner, frontend); brain może dzielić obraz z api lub osobny – tu osobny brain Dockerfile.
Obrazy lightweight (python:3.12-slim), multi-stage (poetry/pip + runtime).
Testy i scenariusze

Jednostkowe: parsery NBP JSON, obliczenia EMA/MACD, selektor sygnałów.
Integracyjne: miner→DB (mock NBP lub VCR), API kontrakty OpenAPI, brain na sztucznych szeregach (przecięcia MACD).
E2E: docker-compose up, sprawdzenie że w DB pojawiają się wpisy, API zwraca dane, frontend renderuje.
Obsługa błędów: brak internetu/NBP 429 → exponential backoff, job zapisuje status=failed i retry następnej godziny; brak nowych danych weekend → status=skipped.
Założenia / domyślne

Produkcyjna baza: PostgreSQL (zgodnie z wyborem).
Dashboard publiczny, bez logowania; API zabezpieczone rate limit + CORS tylko dla frontu.
Źródła dodatkowe będą dodawane później poprzez interfejs SourceClient; na start tylko NBP.
Harmonogram co godzinę, okno MACD 12/26/9; można zmienić w .env bez przebudowy.
Nie implementujemy realnego tradingu, tylko rekomendacje tekstowe.
Kryteria gotowości

Po starcie na czystej bazie historia NBP jest wczytana, tabele wypełnione.
GET /health 200, GET /stats/miner pokazuje ostatni job.
GET /signals zwraca co najmniej jeden sygnał dla USD/PLN i dla złota.
Frontend pokazuje wykresy i tabelę sygnałów oraz listę jobów.
Trzeba dodać Redis jako cache i jako kolejkę Pub/Sub

Plan

Tytuł
Charon z Redis jako cache + Pub/Sub między minerem a brainem.

Zmiany vs poprzedni plan (kluczowe)

Redis staje się wymagany:
Cache dla API (TTL 5 min na odczyty /rates, /gold, /signals).
Kolejka Pub/Sub: kanał rates.ingested (payload: asset_code, from_date, to_date, rows) emitowany przez miner, konsumowany przez brain.
Dodajemy opis kontraktu komunikacji oraz mechanikę wygaszania cache po nowych danych.
Architektura

4 kontenery wymagane: miner, api, brain, frontend.
Dodatkowe usługi w compose: postgres, redis (poza “czwórką”).
Przepływ: miner zapisuje do PostgreSQL → publikuje event na Redis → brain subskrybuje i liczy sygnały → zapisuje do DB → API serwuje (z cache) → frontend konsumuje API.
Redis – kontrakty

Kanał Pub/Sub: rates.ingested. JSON: {"type":"currency|gold","asset":"USD","from":"2024-01-01","to":"2024-02-01","rows":93,"job_id":123}.
Brain subscriber: na event czyści/cache invalidates klucze cache:rates:* i cache:signals:* dla assetu, potem liczy MACD i zapisuje sygnały.
Cache klucze:
cache:rates:{code}:{from}:{to}
cache:gold:{from}:{to}
cache:signals:{code}:{limit}
TTL domyślnie 300 s (konfig .env).
Fallback: jeśli Redis niedostępny, API i brain działają bez cache/pubsub (log warning).
Komponenty (aktualizacja)

miner: po każdym udanym wsadzie publikuje event do Redis; zapisuje job w jobs_log.
brain: nasłuch na Redis (async listener); po eventach lub co godzinę (watchdog) przelicza sygnały; po zapisie sygnałów publikuje signals.updated (opcjonalnie na przyszłość).
api: używa Redis do cache GET, z invalidacją na eventach signals.updated (jeśli włączymy) lub po TTL; rate limiting może dzielić instancję Redis.
frontend: bezpośrednio przez API (brak bezpośredniego dostępu do Redis).
Konfiguracja .env

REDIS_URL=redis://redis:6379/0 (prod zewnętrzny endpoint)
REDIS_ENABLED=1
REDIS_CACHE_TTL=300
REDIS_PUBSUB_CHANNEL_RATES=rates.ingested
REDIS_PUBSUB_CHANNEL_SIGNALS=signals.updated (opcjonalne)
Testy dopisane

Integracja: publish→brain subscriber→sygnały w DB, invalidacja cache.
API: cache hit/miss, TTL, brak Redis = graceful degrade.
Miner: event publish po wsadzie, poprawny payload.
Kryteria gotowości (doprecyzowane)

Po pierwszym pełnym imporcie miner publikuje event w Redis; brain generuje sygnały w <60 s.
Cache API działa (cache-hit ratio widoczne w logach), a po nowym evencie dane są odświeżone najpóźniej po TTL lub po invalidacji.
Redis outage nie blokuje przetwarzania (system loguje ostrzeżenie, ale dane nadal trafiają do DB i sygnały są liczone z timerem).
