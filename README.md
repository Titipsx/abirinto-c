# Labirinto C: Windows e DOS

Questo progetto ricrea in C il funzionamento del listato Borland originale e
produce due eseguibili:

- `LABIRINTO-WINDOWS.exe`: applicazione grafica nativa per Windows 10/11;
- `LABIRINT.EXE`: programma DOS a 16 bit, da eseguire con DOSBox sui sistemi moderni.

## Compilazione automatica su GitHub

1. Caricare tutto il contenuto di questa cartella in un repository GitHub.
2. Se la cartella nascosta `.github` non viene caricata, creare manualmente il
   file `.github/workflows/build-executables.yml` con il contenuto incluso.
3. Aprire **Actions → Compila eseguibili C**.
4. Attendere il segno verde.
5. Aprire l'esecuzione completata e scaricare in fondo alla pagina:
   `Labirinto-Windows` e `Labirinto-DOS`.

## Comandi

- `1`–`4`: scelta difficoltà;
- frecce: movimento;
- `F1`: mostra o nasconde la soluzione;
- `Esc`: ritorna al menu;
- `F10`: chiude la versione DOS.

## Nota tecnica

Il sorgente originale dipendeva dalle librerie proprietarie Borland BGI
(`graphics.h`). La logica è stata mantenuta, mentre la grafica è stata adattata
a Win32 GDI e alla modalità testuale VGA 80×50 per ottenere eseguibili autonomi
e compilabili con strumenti attuali.
