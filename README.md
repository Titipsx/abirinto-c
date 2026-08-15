# Labirinto Python

Conversione moderna del gioco `LABIRINT.C`, pensata per funzionare sia sul PC
sia direttamente nel browser.

Nel menu iniziale il pulsante **MODALITÀ 3D** permette di scegliere tra il
labirinto classico dall'alto e la nuova visuale in prima persona con minimappa.

## Comandi

- Frecce oppure `W A S D`: movimento
- `F1` oppure `H`: mostra/nasconde la soluzione
- `Invio` oppure `N`: nuovo labirinto
- `Esc`: torna al menu
- Su telefono e tablet sono disponibili i pulsanti touch

In modalità 3D:

- Freccia su/giù: avanti e indietro
- Freccia sinistra/destra: rotazione di 90 gradi
- La minimappa laterale mostra posizione, direzione e uscita
- Muri in pietra, muschio, illuminazione in profondità e pavimento a lastre sono
  generati direttamente dal programma, senza immagini esterne
- Quattro varianti coerenti di pareti e luce laterale aiutano a riconoscere i passaggi
- Ogni livello garantisce almeno `livello × 3` vicoli ciechi; il percorso
  dall'inizio a ciascuno di quelli conteggiati misura almeno `livello × 5` passi
  e contiene almeno `livello × 2` curve
- In 3D il pulsante soluzione guida automaticamente il giocatore fino all'arrivo
- La soluzione automatica parte a velocità 1; la barra spaziatrice passa
  ciclicamente tra velocità 1, 2 e 3
- Un diamante luminoso segnala l'uscita e cresce avvicinandosi
- All'arrivo vengono confrontati i passi effettuati con il minimo necessario

## Prova sul computer

Installa Python 3.11 o successivo, poi esegui:

```bash
pip install pygame-ce
python main.py
```

## Pubblicazione su GitHub Pages

1. Crea un nuovo repository GitHub, ad esempio `labirinto-python`.
2. Carica **tutto il contenuto** di questa cartella, compresa `.github`.
3. Apri il repository e vai in **Settings → Pages**.
4. In **Build and deployment → Source** seleziona **GitHub Actions**.
5. Apri la scheda **Actions** e attendi il completamento di `Pubblica Labirinto`.
6. Il gioco sarà disponibile all'indirizzo indicato nella pagina dell'azione e in
   **Settings → Pages**.

Ogni successiva modifica inviata al ramo `main` pubblicherà automaticamente la
nuova versione.

## Creazione della versione Python per browser offline

Il workflow **Crea pacchetto Python web offline** compila lo stesso `main.py`
e include nel risultato anche Python WebAssembly, Pygame e i componenti che
normalmente verrebbero scaricati da Internet.

1. Apri **Actions → Crea pacchetto Python web offline**.
2. Premi **Run workflow**.
3. Al termine, scarica l'artifact **Labirinto-Python-Web-Offline**.
4. Estrai lo ZIP e fai doppio clic su `AVVIA.bat`.

Sul computer di destinazione non sono richiesti Python, Pygame o Internet.

## Struttura

- `main.py`: gioco completo e generatore parametrico
- `requirements.txt`: dipendenze per l'esecuzione locale e la compilazione web
- `.github/workflows/pages.yml`: compilazione e pubblicazione automatica

La versione web usa Pygbag, che esegue Python/Pygame nel browser tramite
WebAssembly.
