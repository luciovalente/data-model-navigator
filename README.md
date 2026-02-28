# Data Model Navigator

Tool locale (CLI) per:

1. connettersi a **PostgreSQL** e **MongoDB**;
2. estrarre entità/campi e salvarli in JSON;
3. applicare una fase di configurazione (pulizia automatica + intervento manuale);
4. proporre/aggiungere relazioni anche cross-db (Mongo ↔ PostgreSQL);
5. generare un viewer **E/R navigabile** in HTML.

## Installazione

```bash
python -m venv .venv
source .venv/bin/activate
pip install -e .
# opzionali per discovery reale
pip install psycopg[binary] pymongo
```

## Avvio

Menu interattivo:

```bash
dmn --menu
```

Fasi dirette:

```bash
dmn --phase discover
# genera output/model.json

dmn --phase curate
# pulizia + suggerimenti relazioni + eventuale input manuale

dmn --phase viewer --open-browser
# genera output/viewer.html
```

## Fase di configurazione (pulizia e relazioni)

- Pulizia automatica dei campi tecnici comuni (`created_at`, `updated_at`, ...).
- Heuristica relazioni automatiche:
  - campo `customer_id` -> entità `customer.id` (se presente).
- Intervento manuale guidato da menu per creare relazioni:
  - Mongo→Mongo
  - Mongo→Postgres
  - Postgres→Mongo
  - Postgres→Postgres

## Demo rapida senza DB

```bash
mkdir -p output
cp examples/sample_model.json output/model.json
dmn --phase viewer
python -m http.server 8000
# apri http://localhost:8000/output/viewer.html
```
