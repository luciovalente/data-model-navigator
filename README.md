# Data Model Navigator

Tool locale (CLI) per:

1. connettersi a **PostgreSQL** e **MongoDB**;
2. estrarre entità/campi e salvarli in JSON;
3. applicare una fase di configurazione (pulizia automatica + intervento manuale);
4. proporre/aggiungere relazioni anche cross-db (Mongo ↔ PostgreSQL);
5. generare un viewer **E/R navigabile** in HTML;
6. correggere il JSON del modello dati con supporto LLM e prompt guidato;
7. opzionalmente applicare un prompt LLM iniziale per regole di interpretazione semantica.

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
# opzionale: durante la fase discovery puoi inserire un prompt LLM
# per ottenere regole di interpretazione e tag entità senza chiamate per-record

dmn --phase curate
# pulizia + suggerimenti relazioni + eventuale input manuale

dmn --phase viewer --open-browser
# genera output/viewer.html

dmn --phase fix-json
# chiede un prompt di correzione e usa l'LLM per aggiornare output/model.json
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


## Correzione JSON modello dati (nuova fase)

- Esegui `dmn --phase fix-json` dopo discovery/curation.
- La CLI chiede un prompt (es. "uniforma naming, correggi relazioni mancanti, rinomina entità duplicate").
- Con supporto LLM viene prodotto un JSON corretto e salvato in `output/model.json`.
- L'output deve rispettare la struttura del modello (`entities`, `relationships`, `metadata`).

## Prompt LLM di interpretazione (opzionale, in discovery)

- Puoi inserire un prompt descrittivo prima dell'analisi (es. tabelle polimorfiche, gerarchie in collection).
- Il sistema esegue **una sola chiamata LLM** su tutto lo schema, oppure una chiamata per batch di entità.
- Le istruzioni restituite vengono salvate in `metadata.interpretation_instructions` nel JSON modello.
- Non viene chiamato l'LLM per ogni record/documento.


## Configurazione persistente CLI

Durante `dmn --phase discover`, i parametri inseriti vengono salvati automaticamente in `output/config.json`:

- PostgreSQL: host, porta, dbname, utente, password, schema
- MongoDB: URI, dbname, sample size
- LLM: prompt, modello, endpoint, token API, batch size

Alle esecuzioni successive, se `output/config.json` è presente, la CLI riusa tali valori e non richiede nuovamente gli input interattivi.

## Demo rapida senza DB

```bash
mkdir -p output
cp examples/sample_model.json output/model.json
dmn --phase viewer
python -m http.server 8000
# apri http://localhost:8000/output/viewer.html
```

## Risoluzione problemi

### Errore LLM SSL: `CERTIFICATE_VERIFY_FAILED`

Se durante una chiamata LLM compare un errore SSL tipo:

`CERTIFICATE_VERIFY_FAILED: unable to get local issuer certificate`

significa che Python non riesce a validare il certificato HTTPS dell'endpoint (tipico in reti aziendali con proxy/TLS inspection).

Imposta il percorso del bundle CA aziendale (formato PEM) prima di eseguire `dmn`:

```bash
export DMN_CA_BUNDLE=/percorso/ca-azienda.pem
# alternativa compatibile con Python/OpenSSL
export SSL_CERT_FILE=/percorso/ca-azienda.pem
dmn --phase discover
```

`DMN_CA_BUNDLE` ha priorità e viene usata dalle chiamate LLM del tool.

Se `dmn` risponde `command not found`, hai due opzioni:

```bash
# opzione A: installazione comando in ambiente virtuale
python -m venv .venv
source .venv/bin/activate
pip install -e .
dmn --menu

# opzione B: launcher locale senza installazione
./dmn --menu

# opzione C: entrypoint modulo Python
PYTHONPATH=src python -m datamodel_navigator --menu
```
