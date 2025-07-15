# Kris Assistant

A dyslexia Ai Assistant: write, search the web, open programs

## Come si usa

1. Scarica e estrai il file `kris_assistant_alpha.zip`
2. Apri la cartella estratta
3. Fai doppio click su `assistant.exe`  
4. Segui le istruzioni a schermo

## Requisiti

- **Nessun requisito**:  serve Python lo fa in automatico.

## Note

- Per la prima esecuzione ci può volere qualche secondo per il caricamento dei modelli vocali.
- Il file `config.json` contiene le preferenze personali e i comportamenti da escludere.

## Supporto

Per problemi: [email di supporto o link]

# KRIS ASSISTANT – Versione Alpha (offline, vocale, stile KITT)

# ---
# 1. RICONOSCIMENTO VOCALE
# ---
# ✓ Whisper (modello "base") integrato nel pacchetto.
# ✓ Funziona offline (no connessione necessaria).
# ✓ Lingua impostata su 'it' per massimo supporto all'italiano.
# ✓ Input audio dal microfono predefinito (Realtek o webcam).
# ✓ Gestione fallback per errore input audio (dispositivo mancante o non accessibile).

# ---
# 2. COMANDI VOCALI BASE
# ---
# - "scrivi [testo]": aggiunge testo alla sessione.
# - "salva nota": salva in formato .txt la sessione corrente.
# - "apri [blocco note/calcolatrice/nome app]": apre alcune app di sistema.
# - "non leggere le email": blocca la lettura vocale di messaggi.
# - "leggi tutto": attiva sintesi vocale della sessione in corso.
# - "esci": chiude l’assistente vocalmente.

# ---
# 3. OUTPUT E UI
# ---
# ✓ Interfaccia stile "cruscotto KITT", con display digitale LED animato.
# ✓ Tema scuro predominante, sfondo #111, font "Consolas" verde fluo (#39ff14).
# ✓ Console interattiva stile terminale, con log dei comandi.
# ✓ Barra LED animata che simula l'ascolto.
# ✓ Feedback vocale con pyttsx3 in italiano (voce personalizzabile).

# ---
# 4. CONFIGURAZIONE E INTERAZIONE
# ---
# ✓ File config.json per gestire:
#     - Lista nera comandi (blacklist)
#     - Parametri voce (ID, velocità, volume)
#     - Directory note
# ✓ UI di configurazione accessibile da pulsante "Config"
# ✓ Parametri modificabili live, con salvataggio persistente

# ---
# 5. PACCHETTO ESECUTIVO
# ---
# ✓ Eseguibile standalone (assistant.exe), nessun Python richiesto all’utente.
# ✓ Archivio ZIP con:
#     - assistant.exe
#     - config.json
#     - directory "note/"
#     - directory "assets/" per suoni, icone, voce
#     - requirements.txt per debug e sviluppo
# ✓ Funziona out-of-the-box: estrai, clicca, interagisci

# ---
# 6. FUNZIONALITÀ AGGIUNTIVE (previste o future)
# ---
# - Parser intelligente: frasi tipo "Kris apri blocco note"
# - Log automatico comandi in "logs/kris_log.txt"
# - Lettura e risposta vocale a email/testi in input
# - Protezione thread con threading.Lock() su current_text
# - Switch automatico Whisper -> Vosk in fallback
# - Modalità markdown (salvataggio .md)
# - Tasto "ripeti ultimo comando"

# ---
# 7. STATO ATTUALE
# ---
# ✓ GUI KITT completata
# ✓ Comandi vocali base attivi e funzionanti
# ✓ Configurazione salvabile e persistente
# 🔧 Ottimizzazioni di stabilità in corso
# 📦 Compilazione ZIP finale in corso (con assistant.exe)
# 📍 Consegna prevista: a ore
