# `organizer`: analisi dettagliata del comando

## Indice

1. [Panoramica](#panoramica)
2. [Dove vive il comando e come viene registrato](#dove-vive-il-comando-e-come-viene-registrato)
3. [Firma CLI: argomenti, opzioni, default ed environment variables](#firma-cli-argomenti-opzioni-default-ed-environment-variables)
4. [Flusso completo in ordine di esecuzione](#flusso-completo-in-ordine-di-esecuzione)
5. [Fase 1: bootstrap del comando Typer](#fase-1-bootstrap-del-comando-typer)
6. [Fase 2: validazioni iniziali](#fase-2-validazioni-iniziali)
7. [Fase 3: logging dei parametri e preparazione degli indici di ordinamento](#fase-3-logging-dei-parametri-e-preparazione-degli-indici-di-ordinamento)
8. [Fase 4: scelta della strategia di ricerca](#fase-4-scelta-della-strategia-di-ricerca)
9. [Fase 5: come funziona la ricerca filesystem](#fase-5-come-funziona-la-ricerca-filesystem)
10. [Fase 6: come funziona la ricerca su catalogo Eagle](#fase-6-come-funziona-la-ricerca-su-catalogo-eagle)
11. [Fase 7: costruzione del risultato di ricerca](#fase-7-costruzione-del-risultato-di-ricerca)
12. [Fase 8: stampa delle tabelle di preview](#fase-8-stampa-delle-tabelle-di-preview)
13. [Fase 9: stop se non ci sono file accettati](#fase-9-stop-se-non-ci-sono-file-accettati)
14. [Fase 10: conferma interattiva dell’utente](#fase-10-conferma-interattiva-dellutente)
15. [Fase 11: generazione XMP temporanei](#fase-11-generazione-xmp-temporanei)
16. [Fase 12: creazione delle opzioni di organizzazione](#fase-12-creazione-delle-opzioni-di-organizzazione)
17. [Fase 13: organizzazione vera e propria dei file](#fase-13-organizzazione-vera-e-propria-dei-file)
18. [Fase 14: stampa dei risultati finali](#fase-14-stampa-dei-risultati-finali)
19. [Fase 15: cleanup finale degli XMP generati](#fase-15-cleanup-finale-degli-xmp-generati)
20. [Dipendenze esterne importanti: `pylizlib`](#dipendenze-esterne-importanti-pylizlib)
21. [Punti critici e comportamenti non ovvi](#punti-critici-e-comportamenti-non-ovvi)
22. [Riassunto operativo ultra-compatto](#riassunto-operativo-ultra-compatto)

---

## Panoramica

Il comando `organizer` definito in [`eagleliz/organizer.py`](../eagleliz/organizer.py) è un **comando CLI Typer** che fa da orchestratore ad alto livello.

Non contiene tutta la logica di business al suo interno: coordina invece più componenti:

- [`EagleLocalSearcher`](../eagleliz/local/searcher.py) per trovare i media;
- [`FileSystemSearcher`](../eagleliz/local/searcher_os.py) per la scansione di directory normali;
- [`EagleCatalogSearcher`](../eagleliz/local/searcher_eagle.py) per leggere un catalogo `.library` di Eagle;
- [`MediaOrganizer`](../eagleliz/controller/media_org.py) per copiare/spostare davvero i file nelle cartelle target;
- [`OrganizerOptions`](../eagleliz/model/organizer.py) per configurare il comportamento del motore di organizzazione;
- classi di `pylizlib` come `LizMedia`, `LizMediaSearchResult`, `MediaListResultPrinter` e `MetadataHandler`.

In pratica il comando esegue questa pipeline:

1. riceve argomenti e opzioni dalla CLI;
2. valida input minimi;
3. sceglie **come cercare** i file;
4. raccoglie una lista di file accettati/rifiutati/in errore;
5. mostra tabelle di anteprima;
6. chiede conferma all’utente;
7. opzionalmente genera XMP temporanei mancanti;
8. organizza i file copiandoli nella struttura di destinazione;
9. stampa una tabella finale dei risultati;
10. rimuove eventuali XMP temporanei generati durante il processo.

---

## Dove vive il comando e come viene registrato

Il comando è registrato qui:

```python
from eagleliz import eagleliz_app

@eagleliz_app.command()
def organizer(...):
    ...
```

Questo significa che `organizer` è un **sottocomando** dell’app Typer principale definita in [`eagleliz/__init__.py`](../eagleliz/__init__.py):

```python
eagleliz_app = typer.Typer(help="Eagle.cool related utility scripts.")
```

L’entrypoint CLI del progetto è in [`eagleliz/cli.py`](../eagleliz/cli.py), dove `main()` invoca `eagleliz_app()`. In [`pyproject.toml`](../pyproject.toml) il comando installato è:

```toml
[project.scripts]
eagleliz = "eagleliz.cli:main"
```

Quindi, a runtime, il flusso è:

- shell → `eagleliz ...`
- entrypoint Python → `eagleliz.cli:main`
- Typer → dispatch al sottocomando `organizer`

---

## Firma CLI: argomenti, opzioni, default ed environment variables

La firma è piuttosto ricca. Il comando accetta **2 argomenti posizionali** e varie opzioni.

### Argomenti posizionali

#### `path`
Sorgente da cui cercare i file da organizzare.

- tipo: `str`
- env var: `PYL_M_ORG_PATH`
- `dir_okay=True`
- `readable=True`

#### `output`
Cartella di destinazione in cui copiare/organizzare i file.

- tipo: `str`
- env var: `PYL_M_ORG_OUTPUT`
- `dir_okay=True`
- `writable=True`
- `readable=True`

### Opzioni funzionali principali

#### `--eaglecatalog`
Se attiva la modalità Eagle catalog invece della scansione filesystem classica.

- tipo: `bool`
- default: `False`
- env var: `PYL_M_ORG_EAGLECATALOG`

#### `--eagletag` / `-et`
Lista opzionale di tag Eagle per filtrare gli item del catalogo.

- tipo: `Optional[List[str]]`
- può essere ripetuta più volte
- env var: `PYL_M_ORG_EAGLETAG`

#### `--xmp`
Genera file XMP mancanti prima della fase di organizzazione.

- tipo: `bool`
- default: `False`
- env var: `PYL_M_ORG_XMP`

#### `--dry`
Attiva la simulazione: il processo passa quasi tutto il flusso, ma senza scrivere davvero i file finali.

- tipo: `bool`
- default: `False`
- env var: `PYL_M_ORG_DRY`

#### `--exclude` / `-ex`
Pattern regex per escludere file nella modalità filesystem.

- tipo: `str | None`
- env var: `PYL_M_ORG_EXCLUDE`

> Nota importante: nel codice della ricerca filesystem la regex viene applicata al **solo nome file** (`file`), non all’intero path completo.

### Opzioni di visualizzazione ricerca

- `--list-accepted` / `-lac` → default `True`
- `--list-rejected` / `-lrej` → default `True`
- `--list-errored` / `-lerr` → default `True`

Environment variables:

- `PYL_M_ORG_LIST_ACCEPTED`
- `PYL_M_ORG_LIST_REJECTED`
- `PYL_M_ORG_LIST_ERRORED`

### Opzioni di ordinamento tabelle di ricerca

- `--list-accepted-order-index` / `-laoi` → `0..6`
- `--list-rejected-order-index` / `-lroi` → `0..6`
- `--list-errored-order-index` / `-leoi` → `0..6`

### Opzioni di visualizzazione risultati finali

- `--print-results` / `-pres` → default `True`
- `--list-result-order-index` / `-lresoi` → `0..5`

---

## Flusso completo in ordine di esecuzione

Qui sotto c’è il flusso logico reale, nell’ordine in cui il comando esegue il lavoro:

1. Typer invoca `organizer(...)`.
2. Verifica che `path` e `output` non siano vuoti.
3. Stampa il riepilogo dei parametri scelti.
4. Costruisce i nomi delle colonne da usare per descrivere l’ordinamento richiesto.
5. Istanzia `EagleLocalSearcher(path)`.
6. Se `eaglecatalog=True`, esegue la ricerca su catalogo Eagle.
7. Altrimenti esegue la ricerca filesystem, con eventuale regex `exclude`.
8. Recupera il risultato della ricerca e prende la lista `accepted`.
9. Se richiesto, stampa le tabelle Accepted / Rejected / Errored.
10. Se non c’è nessun file accettato, termina con exit code `0`.
11. Aspetta `Enter` dall’utente.
12. Se `xmp=True`, genera XMP mancanti e li associa ai media.
13. Costruisce un `OrganizerOptions` con valori hard-coded e pochi valori dinamici.
14. Crea `MediaOrganizer` e lancia `organize()`.
15. Se richiesto, stampa la tabella finale dei risultati.
16. Se `xmp=True`, rimuove gli XMP temporanei generati.
17. Il comando termina implicitamente.

---

## Fase 1: bootstrap del comando Typer

La funzione `organizer` è interamente guidata da Typer. Questo comporta alcuni effetti importanti:

- Typer converte gli argomenti da CLI a valori Python;
- applica i controlli basilari dichiarati nei `typer.Argument(...)` / `typer.Option(...)`;
- permette di valorizzare i parametri anche tramite environment variables;
- genera automaticamente help e parsing delle opzioni.

La funzione, però, **aggiunge anche validazioni manuali** proprie, quindi non si affida solo a Typer.

---

## Fase 2: validazioni iniziali

Subito dopo la docstring, il comando controlla due condizioni:

```python
if not path:
    typer.echo("❌ Error: path cannot be empty", err=True)
    raise typer.Exit(code=1)
if not output:
    typer.echo("❌ Error: output cannot be empty", err=True)
    raise typer.Exit(code=1)
```

### Cosa fa davvero

- Se `path` è `None`, stringa vuota o valore falsy, il comando fallisce con `exit code 1`.
- Stessa cosa per `output`.
- Il messaggio viene scritto su `stderr` (`err=True`).

### Perché è importante

Anche se Typer è già configurato con argomenti posizionali, qui lo script sceglie di difendersi esplicitamente contro input mancanti.

### Effetto pratico

Il comando si interrompe **prima di iniziare qualsiasi scansione**.

---

## Fase 3: logging dei parametri e preparazione degli indici di ordinamento

Dopo le validazioni il comando stampa un blocco introduttivo con i parametri attivi.

Esempio semplificato:

```python
typer.echo(f"📁 Source: {path}")
typer.echo(f"📁 Output: {output}")
typer.echo(f"🔍 Dry-run: {'Yes' if dry else 'No'}")
typer.echo(f"🦅 Eagle Catalog: {'Yes' if eaglecatalog else 'No'}")
```

### Cosa viene mostrato

- sorgente
- destinazione
- stato `dry-run`
- uso o meno del catalogo Eagle
- eventuali tag Eagle
- attivazione XMP
- pattern regex di esclusione
- stato delle tabelle Accepted / Rejected / Errored
- stato della stampa risultati finali

### Preparazione dell’ordinamento

Il comando definisce due array di nomi colonna:

```python
column_names_search = [
    "Index",
    "Filename",
    "Creation Date",
    "Exif",
    "Ext",
    "Size",
    "Extra (Sidecars/Reason)",
]
column_names_res = [
    "Index",
    "Status",
    "Filename",
    "Extension",
    "Destination",
    "Reason",
]
```

Poi usa gli indici passati via CLI per determinare **quale colonna** sarà usata come riferimento di ordinamento e la stampa nel riepilogo.

### Osservazione importante

Qui non avviene l’ordinamento vero e proprio: vengono solo tradotti gli indici in etichette leggibili per l’utente. L’ordinamento reale sarà applicato più avanti dai printer delle tabelle.

---

## Fase 4: scelta della strategia di ricerca

Questo è uno snodo chiave del comando:

```python
searcher = EagleLocalSearcher(path)
if eaglecatalog:
    searcher.run_search_eagle(eagletag)
else:
    searcher.run_search_system(exclude, dry)
```

`organizer` non implementa la scansione direttamente. Usa [`EagleLocalSearcher`](../eagleliz/local/searcher.py) come **facade**.

### Ruolo di `EagleLocalSearcher`

La classe incapsula due strategie diverse:

- `run_search_system(...)` → ricerca su filesystem classico
- `run_search_eagle(...)` → ricerca dentro un catalogo Eagle `.library`

Restituisce sempre un contenitore comune: `MediaListResult`, che arriva da `pylizlib`.

Questa scelta è importante perché permette al resto del comando di lavorare in modo uniforme, senza dover conoscere i dettagli della sorgente.

---

## Fase 5: come funziona la ricerca filesystem

Se `eaglecatalog=False`, il comando entra in [`FileSystemSearcher.search`](../eagleliz/local/searcher_os.py).

### Logica reale

1. Crea un `MediaListResult()` vuoto.
2. Se `exclude` è valorizzato, prova a compilare la regex con `re.compile(exclude)`.
3. Se la regex è invalida, stampa un errore e termina con `typer.Exit(code=1)`.
4. Esegue `os.walk(self.path)` ricorsivamente.
5. Per ogni file trovato:
   - aggiorna la progress bar `tqdm`;
   - controlla se il **nome file** fa match con la regex di esclusione;
   - se escluso, lo mette in `result.rejected` con reason `Rejected by regex pattern`;
   - altrimenti prova a costruire `LizMedia(file_path)`.
6. Se `LizMedia(file_path)` riesce, il file viene aggiunto a `result.accepted`.
7. Se `LizMedia(file_path)` solleva `ValueError`, il file viene semplicemente ignorato.

### Snippet significativo

```python
if exclude_regex and exclude_regex.search(file):
    result.rejected.append(
        LizMediaSearchResult(
            status=MediaStatus.REJECTED,
            path=file_path,
            media=None,
            reason="Rejected by regex pattern",
        )
    )
    continue

try:
    liz_media = LizMedia(file_path)
    result.accepted.append(...)
except ValueError:
    pass
```

### Cosa significa in pratica

- vengono accettati solo i file che `pylizlib` riconosce come media validi;
- i file non-media **non compaiono** come rifiutati: vengono scartati silenziosamente;
- i file esclusi dalla regex invece compaiono esplicitamente nella tabella dei rejected;
- `dry=True` qui non cambia la logica di ricerca, se non per qualche messaggio in output (`Skipping (regex match): ...`).

---

## Fase 6: come funziona la ricerca su catalogo Eagle

Se `eaglecatalog=True`, il comando usa [`EagleCatalogSearcher`](../eagleliz/local/searcher_eagle.py).

### Struttura generale

Il metodo `search(eagletag)`:

1. resetta il risultato interno;
2. costruisce un `EagleLocalReader` puntando al path del catalogo;
3. passa un set di `file_types` che include anche `MEDIA_SIDECAR`;
4. passa `filter_tags=eagletag`;
5. esegue `reader.run()`;
6. converte gli item trovati in `LizMediaSearchResult`;
7. collega eventuali sidecar ai file media corrispondenti;
8. costruisce le liste `accepted`, `rejected`, `errored`;
9. stampa un riepilogo finale.

### Come legge il catalogo Eagle

[`EagleLocalReader`](../eagleliz/local/reader.py) si aspetta una struttura `.library` con cartella `images/`.

#### Sequenza interna del reader

- verifica che esista `catalogue / "images"`;
- itera le sottocartelle UUID in `images/`;
- in ogni cartella cerca:
  - `metadata.json`
  - il media principale
  - eventuali file sidecar
- crea un `EagleLocalItem` con file e metadata;
- filtra per stato deleted, tipo file e tag;
- opzionalmente legge il base64 del contenuto.

### Filtro per tag

Se `eagletag` è valorizzato, il filtro applicato è questo:

```python
if self.filter_tags:
    item_tags = metadata_obj.tags if metadata_obj.tags else []
    if not any(tag in item_tags for tag in self.filter_tags):
        self.items_skipped.append((eagle_item, "Tag mismatch"))
        return None
```

Quindi la semantica è **OR**, non AND:

- basta che **uno** dei tag richiesti sia presente nell’item Eagle.

### Linking dei sidecar

Dopo aver creato gli accepted media, `EagleCatalogSearcher` collega i sidecar ai media accettati tramite due mappe:

- per `stem`
- per `name`

Snippet:

```python
accepted_map_by_stem = {item.path.stem: item for item in self._result.accepted}
accepted_map_by_name = {item.path.name: item for item in self._result.accepted}
```

Questo permette di gestire casi come:

- `image.png.xmp` → match su `image.png`
- `image.xmp` → match su `image.png`

Se il sidecar non trova un media corrispondente, finisce nei `rejected` con reason:

- `Orphan sidecar file (no matching media)`

### Cosa viene allegato al media

Per ogni item Eagle accettato:

- viene creato un `LizMedia(eagle.file_path)`;
- viene eseguito `lizmedia.attach_eagle_metadata(eagle.metadata)`;
- se disponibile, viene copiato anche `base64_content`.

Questo è importante perché più avanti gli XMP possono essere arricchiti con metadati Eagle.

---

## Fase 7: costruzione del risultato di ricerca

Dopo aver finito la ricerca, `organizer` esegue:

```python
search_result = searcher.get_result()
media_global = search_result.accepted
```

### Cosa contiene `search_result`

È un `MediaListResult` di `pylizlib`, con tre liste:

- `accepted: List[LizMediaSearchResult]`
- `rejected: List[LizMediaSearchResult]`
- `errored: List[LizMediaSearchResult]`

### Cosa contiene ogni `LizMediaSearchResult`

Dal sorgente di `pylizlib/media/lizmedia.py`:

- `status`
- `path`
- `media` (`LizMedia | None`)
- `reason`
- `index`

### Perché `media_global = search_result.accepted` è importante

La fase di organizzazione successiva **non lavora sui path grezzi**, ma sui `LizMediaSearchResult` accettati, in modo da mantenere:

- metadati Eagle eventualmente allegati;
- sidecar già associati;
- accesso immediato alle proprietà del media (`creation_date`, `has_exif_data`, ecc.).

---

## Fase 8: stampa delle tabelle di preview

Subito dopo la ricerca, il comando stampa le tabelle se abilitate.

```python
if list_accepted:
    with Console().status("[bold cyan]Generating Accepted Table...[/bold cyan]"):
        searcher.printAcceptedAsTable(list_accepted_order_index)
```

Stesso schema per Rejected ed Errored.

### Chi stampa davvero

`EagleLocalSearcher` delega a `MediaListResultPrinter` di `pylizlib`.

### Colonne base delle tabelle di ricerca

`MediaListResultPrinter` usa sempre queste colonne comuni:

- `Index`
- `Filename`
- `Creation Date`
- `Exif`
- `Ext`
- `Size (MB)`

Poi aggiunge una settima colonna:

- Accepted → `Sidecars`
- Rejected / Errored → `Reason`

### Ordinamento reale

L’ordinamento viene eseguito in `_sort_result_list(...)` usando `sort_index`.

Per esempio:

- `0` → indice interno
- `1` → filename
- `2` → data creazione
- `3` → presenza EXIF
- `4` → estensione
- `5` → dimensione
- `6` → sidecars o reason

### Nota importante sui dati mostrati

Per gli item che hanno `media`:

- `Creation Date` viene da `media.creation_date_from_exif_or_file_or_sidecar`
- `Exif` viene da `media.has_exif_data`
- `Size` viene da `media.size_mb`

Per gli item senza `media`:

- varie colonne diventano `N/A`

---

## Fase 9: stop se non ci sono file accettati

Dopo la preview, il comando controlla:

```python
if not media_global:
    print("No files to process. Exiting.")
    raise typer.Exit(code=0)
```

### Comportamento

Se la lista `accepted` è vuota:

- il comando stampa un messaggio informativo;
- termina con `exit code 0`;
- non chiede conferma;
- non genera XMP;
- non organizza nulla.

### Perché `exit code 0`

Perché non è considerato un errore applicativo: semplicemente non c’era nulla da fare.

---

## Fase 10: conferma interattiva dell’utente

Se ci sono file accettati, il comando si ferma qui:

```python
input("Press Enter to continue with organization...")
```

### Implicazioni pratiche

- la CLI è **interattiva**;
- il flusso si blocca finché l’utente non preme `Enter`;
- nei test automatici il runner deve simulare un `"\n"` in input.

Questo è visibile anche nei test di progetto, ad esempio in [`test/test_organizer.py`](../test/test_organizer.py), dove `runner.invoke(..., input="\n")` serve proprio a superare questo punto.

### Impatto su automazione / scripting

Se il comando viene usato in CI o in script non interattivi, questo prompt va considerato perché può bloccare l’esecuzione.

---

## Fase 11: generazione XMP temporanei

Se l’opzione `--xmp` è attiva:

```python
if xmp:
    searcher.generate_missing_xmps()
```

Questa è una fase molto importante perché arricchisce i media **prima** dell’organizzazione vera e propria.

### Cosa fa `generate_missing_xmps()`

Nel facade [`eagleliz/local/searcher.py`](../eagleliz/local/searcher.py):

1. resetta la lista degli XMP generati;
2. crea una directory temporanea con `tempfile.mkdtemp(prefix="pyliz_xmp_")`;
3. seleziona solo gli item `accepted` che:
   - hanno `item.media`
   - **non hanno già un sidecar XMP** (`not i.media.has_xmp_sidecar()`)
4. per ogni media selezionato:
   - crea una sottocartella temporanea univoca;
   - determina il nome XMP corretto (`<stem>.xmp`);
   - usa `MetadataHandler(item.path).generate_xmp(temp_path)`;
   - imposta la creation date nello XMP;
   - se presenti, appende i metadati Eagle nello XMP;
   - allega lo XMP al `LizMedia` con `attach_sidecar_file(...)`;
   - registra il file generato in `generated_xmps_list`.

### Snippet chiave

```python
handler = MetadataHandler(item.path)
if handler.generate_xmp(temp_path):
    creation_date = item.media.creation_date_from_exif_or_file_or_sidecar
    handler.set_creation_date(creation_date, temp_path)

    if item.media.eagle_metadata:
        handler.append_eagle_to_xmp(item.media.eagle_metadata, temp_path)

    item.media.attach_sidecar_file(Path(temp_path))
```

### Perché è importante

Questa fase ha due effetti:

1. crea davvero dei sidecar temporanei su disco;
2. li collega all’oggetto `LizMedia`, quindi `MediaOrganizer` li vedrà e li tratterà come sidecar da copiare insieme al media principale.

### Dipendenza esterna critica: `exiftool`

`MetadataHandler` appartiene a `pylizlib` e usa `exiftool` in sottoprocesso.

Se `exiftool` non è installato o non è nel `PATH`:

- `generate_xmp(...)` restituisce `False`;
- alcuni XMP non verranno creati.

### Nota sul fallback minimal XMP

Se Exiftool trova il file ma non ha metadata da copiare, `MetadataHandler.generate_xmp(...)` tenta comunque di scrivere un **minimal XMP**.

---

## Fase 12: creazione delle opzioni di organizzazione

Dopo la fase XMP, il comando costruisce un oggetto `OrganizerOptions`:

```python
options = OrganizerOptions(
    no_progress=False,
    daily=False,
    copy=True,
    no_year=False,
    delete_duplicates=False,
    dry_run=dry,
    exif=True,
)
```

### Significato reale di questi valori

#### `no_progress=False`
Le progress bar `tqdm` restano attive.

#### `daily=False`
La struttura delle cartelle target **non scende al giorno**. Quindi di default la struttura è:

```text
<output>/<year>/<month>/
```

non:

```text
<output>/<year>/<month>/<day>/
```

#### `copy=True`
Questo è molto importante: il comando `organizer`, così com’è scritto, **copia** i file, non li sposta.

Quindi usa `shutil.copy2(...)` e lascia l’originale al suo posto.

#### `no_year=False`
La struttura include sempre l’anno come primo livello.

#### `delete_duplicates=False`
Se trova un duplicato identico in destinazione, non cancella il sorgente: lo segna come `Duplicate skipped`.

#### `dry_run=dry`
Questo è l’unico flag realmente dinamico passato dall’esterno, oltre all’uso di `path/output`.

#### `exif=True`
La data usata per organizzare i file viene ricavata con priorità EXIF / metadata / sidecar, non semplicemente da `ctime` filesystem.

### Conseguenza progettuale importante

Molti comportamenti del motore sono **hard-coded** dentro il comando CLI.

Cioè l’utente può decidere ad esempio `--dry`, ma non può decidere via CLI:

- se fare move invece di copy;
- se organizzare per giorno;
- se rimuovere l’anno dalla struttura;
- se cancellare i duplicati.

---

## Fase 13: organizzazione vera e propria dei file

Qui il comando passa il controllo al motore di business:

```python
organizer_instance = MediaOrganizer(media_global, output, options)
organizer_instance.organize()
```

Il commento nel codice è importante:

```python
# Pass LizMediaSearchResult objects directly to MediaOrganizer to preserve sidecar info
```

### Perché passare `LizMediaSearchResult` e non solo `Path`

Perché ogni elemento può contenere:

- il `LizMedia`
- i sidecar allegati
- i metadati Eagle
- la data di creazione calcolata

Se si passassero solo i path, queste informazioni andrebbero perse o andrebbero ricalcolate.

### Flusso interno di `MediaOrganizer.organize()`

1. resetta `self.results`;
2. prepara l’iterazione, con `tqdm` se `no_progress=False`;
3. per ogni item:
   - se non ha `LizMedia`, lo salta;
   - aggiorna la descrizione della progress bar;
   - chiama `_process_single_item(item)`;
   - accumula i risultati.

Snippet:

```python
for item in file_iter:
    if not item.has_lizmedia():
        continue

    if not self.options.no_progress:
        file_iter.set_description(f"Organizing {item.media.file_name}")

    item_results = self._process_single_item(item)
    self.results.extend(item_results)
```

### `_process_single_item`: la vera unità di lavoro

Questa funzione è il cuore del motore.

#### 1. Sanificazione del path

```python
sanitized_path = self._sanitize_path(file_path)
```

`_sanitize_path()` rifiuta pattern sospetti come `..` per difendersi da traversal path, usando:

```python
if re.search(r"(\.\.[/\\]|^\.\.[/\\]|^\.\.)", path):
    raise ValueError("Path contains invalid traversal components")
```

Se fallisce, il media produce un `OrganizerResult` fallito e viene scartato.

#### 2. Determinazione della data di creazione

```python
year, month, day, original_timestamp = self._get_creation_details(media_item)
```

Con `exif=True`, `_get_creation_details()` usa:

```python
creation_date = media_item.creation_date_from_exif_or_file_or_sidecar
```

Questa proprietà di `LizMedia` segue questa priorità:

1. EXIF immagine (`exifread`)
2. fallback Exiftool per immagini
3. metadata video (`ffmpeg/ffprobe` via `VideoUtils`)
4. XMP sidecar (`photoshop:DateCreated`)
5. file creation time filesystem

Questa è una delle dipendenze più importanti da `pylizlib`.

#### 3. Costruzione della cartella target

```python
target_folder = self._build_target_folder_path(self.target, year, month, day)
```

Con le opzioni correnti del comando:

- `no_year=False`
- `daily=False`

il risultato è sempre:

```text
<output>/<year>/<month>
```

#### 4. Costruzione del file target

```python
target_path = os.path.join(target_folder, os.path.basename(sanitized_path))
```

Il nome file originale viene preservato.

#### 5. Creazione directory destinazione

Se non siamo in dry-run:

```python
self._ensure_directory_exists(target_folder)
```

che internamente fa:

```python
os.makedirs(folder_path, exist_ok=True)
```

#### 6. Gestione file già esistente in target

Se il file target esiste già:

```python
if os.path.exists(target_path):
    main_result = self._handle_existing_file(file_path, target_path, media_item)
```

`_handle_existing_file()` calcola hash MD5 di sorgente e target con `_get_file_hash()`.

##### Dettaglio importante sull’hash

`_get_file_hash()` non hash-a file oltre i 100 MB: in quel caso restituisce la stringa `"LARGE_FILE"`.

Quindi:

- se entrambi i file sono >100 MB, gli hash possono risultare entrambi `"LARGE_FILE"` e il sistema li considererà duplicati;
- se il calcolo fallisce, ritorna `None`.

##### Caso A: contenuto identico

Se gli hash coincidono:

- con `delete_duplicates=True` eliminerebbe il sorgente;
- ma qui `delete_duplicates=False`, quindi restituisce un risultato con reason `Duplicate skipped`.

##### Caso B: stesso nome, contenuto diverso

Se gli hash differiscono:

- il sistema segnala un conflitto;
- non sovrascrive il target;
- restituisce `File conflict: target exists but content differs`.

#### 7. Trasferimento del file principale

Se non c’era un risultato già deciso da duplicato/conflitto:

```python
main_result = self._execute_transfer(
    file_path, target_path, target_folder, original_timestamp, media_item
)
```

Con le opzioni correnti del comando:

- `copy=True`
- `dry_run` dipende dalla CLI

quindi il comportamento è:

- se `dry_run=False` → `shutil.copy2(source_path, target_path)`
- se `dry_run=True` → non copia davvero, ma restituisce comunque `success=True`

Questo è un punto molto importante: in dry-run il risultato appare come successo logico, pur non avendo scritto nulla su disco.

#### 8. Gestione sidecar

Dopo il media principale:

```python
sidecar_results = self._process_sidecars(item, target_folder, main_result)
```

I sidecar vengono processati solo se:

- il main file è stato trasferito con successo, **oppure**
- il main file era un duplicato con reason `Duplicate skipped`

Se l’item ha sidecar allegati, ciascun sidecar viene copiato nella stessa cartella target del media.

### Regole sidecar

- se il sidecar esiste già in target → risultato fallito con `Sidecar exists/Duplicate skipped`
- se non esiste → `_execute_sidecar_transfer(...)`
- in `copy=True` usa `shutil.copy2(...)`
- in `dry_run=True` non scrive ma ritorna comunque `success=True`

---

## Fase 14: stampa dei risultati finali

Se `print_results=True`:

```python
organizer_instance.print_results_table(list_result_order_index)
```

### Cosa stampa

Una tabella `Organization Results` con colonne:

- `Index`
- `Status`
- `Filename`
- `Extension`
- `Destination`
- `Reason`

### Chi la genera

È implementata in [`eagleliz/controller/media_org.py`](../eagleliz/controller/media_org.py), non in `pylizlib`.

### Logica di ordinamento

L’ordinamento dipende da `list_result_order_index`:

- `0` → indice
- `1` → successo/fallimento
- `2` → filename
- `3` → estensione
- `4` → destinazione
- `5` → reason

### Nota sulla colonna `Destination`

La stampa cerca di rendere il path più leggibile usando `os.path.relpath` rispetto al parent della cartella di output. Se questo fallisce, mostra il path assoluto.

---

## Fase 15: cleanup finale degli XMP generati

Alla fine:

```python
if xmp:
    searcher.cleanup_generated_xmps()
```

### Cosa fa davvero

`cleanup_generated_xmps()`:

1. scorre gli XMP temporanei generati;
2. li cancella dal filesystem;
3. rimuove la directory temporanea radice creata con `mkdtemp`.

Questa pulizia serve solo agli XMP **temporanei** creati durante la run corrente.

### Cosa non fa

- non rimuove XMP già esistenti prima del comando;
- non “stacca” esplicitamente i sidecar dall’oggetto `LizMedia`, ma a quel punto il comando sta terminando, quindi l’oggetto è destinato a sparire comunque.

---

## Dipendenze esterne importanti: `pylizlib`

Lo script dipende fortemente da `pylizlib`. In [`pyproject.toml`](../pyproject.toml) c’è infatti:

```toml
dependencies = [
    "pylizlib[media]>=0.3.70",
    ...
]
```

### `LizMedia`

Classe chiave per rappresentare un file media. Fornisce:

- validazione che il file sia un media riconosciuto;
- proprietà come `file_name`, `extension`, `size_mb`, `year`, `month`, `day`;
- accesso alla data `creation_date_from_exif_or_file_or_sidecar`;
- collegamento di metadati Eagle;
- gestione sidecar tramite `attach_sidecar_file(...)`.

### `LizMediaSearchResult`

Contenitore per il risultato di ricerca di un singolo item.

Serve a tenere insieme:

- stato (`accepted` / `rejected`)
- path
- media opzionale
- reason
- indice progressivo

### `MediaListResult`

Contenitore aggregato con le liste:

- `accepted`
- `rejected`
- `errored`

### `MediaListResultPrinter`

Responsabile della renderizzazione delle tabelle Accepted/Rejected/Errored con Rich.

### `MetadataHandler`

Responsabile della manipolazione metadati/XMP. Usa `exiftool` esternamente per:

- generare XMP da un file media;
- impostare la creation date nello XMP;
- aggiungere tag/annotation Eagle nello XMP;
- leggere date più affidabili da immagini.

---

## Punti critici e comportamenti non ovvi

Questa è la sezione più utile per capire i dettagli “nascosti”.

### 1. `organizer` copia, non sposta

Nonostante il nome possa far pensare a una riorganizzazione fisica “spostando” i file, questo comando è configurato con:

```python
copy=True
```

Quindi il sorgente resta al suo posto.

### 2. `--dry` produce risultati “success” senza scrivere davvero

Nel motore di organizzazione, in dry-run non vengono create directory né copiati file, ma i `OrganizerResult` possono risultare `success=True`.

Questo è voluto: il comando simula l’esito logico dell’operazione.

### 3. la regex `--exclude` si applica al nome file, non al path completo

Se vuoi filtrare directory o path annidati, con l’implementazione attuale non basta ragionare sul path completo: il matching viene fatto sulla variabile `file` di `os.walk`.

### 4. i file non-media vengono ignorati in silenzio nella scansione filesystem

Se `LizMedia(file_path)` fallisce con `ValueError`, il file non viene aggiunto ai rejected: sparisce semplicemente dalla vista del risultato.

### 5. il prompt `input(...)` rende il comando interattivo

Questo può essere scomodo in batch, CI, wrapper shell o chiamate automatizzate.

### 6. la data usata per organizzare non è banalmente il timestamp filesystem

Con `exif=True`, il sistema usa una pipeline più sofisticata:

- EXIF immagine
- Exiftool fallback
- metadata video
- XMP sidecar
- filesystem

Quindi due file copiati nello stesso giorno possono finire in cartelle diverse se i metadata interni raccontano una data diversa.

### 7. gli XMP generati sono temporanei, ma possono influenzare l’organizzazione corrente

Se `--xmp` è attivo, gli XMP temporanei vengono attaccati al `LizMedia` e quindi trattati come sidecar veri per quella run.

### 8. gestione duplicati basata su hash con limite 100 MB

La funzione `_get_file_hash()` usa MD5 ma smette di hashare file grandi oltre 100 MB e ritorna `"LARGE_FILE"`.

Questo introduce un comportamento da conoscere: file grandi con lo stesso “segnaposto hash” possono essere trattati come duplicati logici anche senza confronto byte-a-byte completo.

### 9. i sidecar vengono preservati solo perché si passano `LizMediaSearchResult`

Questo commento nel codice è corretto e molto importante:

```python
# Pass LizMediaSearchResult objects directly to MediaOrganizer to preserve sidecar info
```

Senza questo passaggio, gli XMP o altri sidecar associati andrebbero persi nella fase di copia.

### 10. il filtro tag in Eagle è OR

Con più `--eagletag`, basta un solo tag combaciante per accettare l’item.

---

## Riassunto operativo ultra-compatto

Se vogliamo descrivere `organizer` in una frase lunga ma precisa:

> `organizer` è un comando Typer che riceve una sorgente e una destinazione, sceglie una strategia di discovery (filesystem o catalogo Eagle), costruisce una lista tipizzata di media con eventuali sidecar e metadati, mostra una preview tabellare, attende conferma, genera opzionalmente XMP temporanei mancanti, poi copia i file nella struttura `output/year/month` usando come data di riferimento EXIF/XMP/filesystem, gestendo duplicati, conflitti e sidecar, e infine stampa un riepilogo finale dei risultati.

---

## Mini mappa delle classi coinvolte

```text
CLI Typer (`organizer`)
  -> EagleLocalSearcher
      -> FileSystemSearcher
      -> EagleCatalogSearcher
          -> EagleLocalReader
      -> MediaListResultPrinter (pylizlib)
      -> MetadataHandler (pylizlib, per XMP)
  -> MediaOrganizer
      -> OrganizerOptions
      -> OrganizerResult
      -> LizMedia / LizMediaSearchResult (pylizlib)
```

---

## Snippet finali di riferimento

### Selezione strategia di ricerca

```python
searcher = EagleLocalSearcher(path)
if eaglecatalog:
    searcher.run_search_eagle(eagletag)
else:
    searcher.run_search_system(exclude, dry)
```

### Generazione XMP opzionale

```python
if xmp:
    searcher.generate_missing_xmps()
```

### Costruzione delle opzioni del motore

```python
options = OrganizerOptions(
    no_progress=False,
    daily=False,
    copy=True,
    no_year=False,
    delete_duplicates=False,
    dry_run=dry,
    exif=True,
)
```

### Avvio del motore di organizzazione

```python
organizer_instance = MediaOrganizer(media_global, output, options)
organizer_instance.organize()
```

### Stampa risultati finali

```python
if print_results:
    organizer_instance.print_results_table(list_result_order_index)
```

### Cleanup XMP temporanei

```python
if xmp:
    searcher.cleanup_generated_xmps()
```

