import tkinter as tk
from tkinter import messagebox, filedialog
import os
import json
import threading
import time
import random
from datetime import datetime
import pyttsx3
import whisper
import torch
import subprocess
import sys
import sounddevice as sd
import pyaudio
import wave
import tempfile
import queue
import numpy as np
import scipy.io.wavfile
import pyautogui

# === CONFIGURAZIONE GLOBALE ===
CONFIG_FILE = "config.json"
NOTE_DIR = "note"
LOG_FILE = "logs/kris_log.txt"

# Saluti personalizzati KIT
SALUTI_KIT = [
    "Ciao Kris. Come posso aiutarti?",
    "KIT operativo, dimmi Kris!?",
    "KIT pronto per l'azione. Cosa facciamo Kris?",
    "KIT in linea, Kris. Cosa facciamo oggi?",
    "KIT online, Kris. Pronto a partire.",
    "Salve Kris, KIT in cosa ti aiuto?",
    "KIT attivo, Kris. Dimmi cosa serve."
]
def saluto_casuale():
    return random.choice(SALUTI_KIT)

# Sistema gestione errori intelligente
def gestisci_errore(messaggio, livello="warning"):
    """Sistema errori: prima vocale, poi popup se fallisce"""
    try:
        # Tentativo notifica vocale
        speak(f"Attenzione Kris: {messaggio}")
    except Exception as e:
        # Fallback popup se sintesi vocale fallisce
        messagebox.showerror("KIT - Errore", f"{messaggio}\n\nErrore vocale: {str(e)}")

def gestisci_avviso(messaggio):
    """Avvisi meno critici"""
    try:
        speak(f"KIT informa: {messaggio}")
    except:
        messagebox.showinfo("KIT - Avviso", messaggio)
        
# --- CONFIGURAZIONE DI DEFAULT ---
 #default_config = {
 #   "blacklist": [],
 #  "voice": None,
 #   "rate": 150,
 #   "volume": 1.0,
 #   "note_dir": NOTE_DIR}
 
 
# === CONFIGURAZIONE ===
default_config = {
    "voice_settings": {
        "voice_index": 0,
        "rate": 150,
        "volume": 1.0
    },
    "response_timing": {
        "listen_timeout": 5,
        "processing_delay": 0.5,
        "voice_pause": 1.0
    },
    "whisper_model": "base",
    "language": "it",
    "directories": {
        "notes_dir": NOTE_DIR
    },
    "blacklist_commands": [
        "elimina sistema",
        "formatta disco",
        "shutdown"
    ]
}

def load_config():
    if os.path.exists(CONFIG_FILE):
        try:
            with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
                loaded = json.load(f)
                # Merge con default per nuovi campi
                config = default_config.copy()
                config.update(loaded)
                return config
        except:
            return default_config.copy()
    return default_config.copy()

def save_config(config):
    try:
        with open(CONFIG_FILE, 'w', encoding='utf-8') as f:
            json.dump(config, f, indent=2, ensure_ascii=False)
    except Exception as e:
        gestisci_errore(f"Errore salvataggio configurazione: {str(e)}")

config = load_config()

# --- CARICAMENTO/CREAZIONE CONFIGURAZIONE ---
def load_config():
    if not os.path.exists(CONFIG_FILE):
        save_config(default_config)
        return default_config.copy()
    with open(CONFIG_FILE, "r", encoding="utf-8") as f:
        return json.load(f)

def save_config(cfg):
    with open(CONFIG_FILE, "w", encoding="utf-8") as f:
        json.dump(cfg, f, indent=2)

config = load_config()

# --- CREA CARTELLA NOTE ---
if not os.path.exists(config["note_dir"]):
    os.makedirs(config["note_dir"])
if not os.path.exists("logs"):
    os.makedirs("logs")

# --- INIZIALIZZA SINTESI VOCALE ---
engine = pyttsx3.init()
voices = engine.getProperty('voices')
if config["voice"]:
    engine.setProperty('voice', config["voice"])
else:
    # Seleziona voce italiana se disponibile
    for v in voices:
        if 'it' in v.id or 'italian' in v.name.lower():
            engine.setProperty('voice', v.id)
            found_voice = True
            break
    if not found_voice:
        print("⚠️ Nessuna voce italiana trovata. Verrà usata la voce predefinita.")
engine.setProperty('rate', config["rate"])
engine.setProperty('volume', config["volume"])

lock = threading.Lock()
current_text = ""
reading_emails = True
last_command = ""

# --- PARLA ---
def speak(text):
    def _speak():
        engine.say(text)
        engine.runAndWait()
    threading.Thread(target=_speak, daemon=True).start()

# --- INIZIALIZZA WHISPER (modello base) ---
try:
    model = whisper.load_model("base")
except Exception as e:
    print("Errore nel caricamento di Whisper:", e)
    sys.exit(1)

# --- FUNZIONI DI COMANDO e trascrizione audio---
current_text = ""
reading_emails = True

def trascrivi_audio():
    import sounddevice as sd
    import numpy as np
    samplerate = 16000
    duration = 5  # secondi di ascolto per comando
    try:
        speak("Dimmi Kris")
        audio = sd.rec(int(samplerate * duration), samplerate=samplerate, channels=1, dtype='float32')
        sd.wait()
        audio = np.squeeze(audio)
        audio_path = "temp.wav"
        import scipy.io.wavfile
        scipy.io.wavfile.write(audio_path, samplerate, audio)
        result = model.transcribe(audio_path, language='it')
        os.remove(audio_path)
        return result["text"]
    except Exception as e:
        return f"[Errore acquisizione audio: {e}]"

# --- SALVA NOTA ---
def salva_nota(text):
    fname = time.strftime("%Y%m%d_%H%M%S.txt")
    fpath = os.path.join(config["note_dir"], fname)
    with open(fpath, "w", encoding="utf-8") as f:
        f.write(text)
    return fpath
    
# --- APRI APP ---
def apri_app(nome):
    nome = nome.lower()
    if "notepad" in nome or "blocco" in nome:
        subprocess.Popen(["notepad.exe"])
        return "Blocco note aperto."
    elif "calcolatrice" in nome:
        subprocess.Popen(["calc.exe"])
        return "Calcolatrice aperta."
    elif "word" in nome:
        subprocess.Popen(["winword.exe"])
        return "Microsoft Word aperto."
    elif "brave" in nome:
        subprocess.Popen(["C:\\Program Files\\BraveSoftware\\Brave-Browser\\Application\\brave.exe"])
        return "Brave avviato."
    elif text.startswith("kit cerca"):
        query = text.split("kit cerca", 1)[-1].strip()
        url = f"https://duckduckgo.com/?q={query.replace(' ', '+')}"
        subprocess.Popen(["C:\\Program Files\\BraveSoftware\\Brave-Browser\\Application\\brave.exe", url])
    return f"Sto cercando: {query}"

    elif "thunderbird" in nome:
        subprocess.Popen(["C:\\Program Files\\Mozilla Thunderbird\\thunderbird.exe"])
        return "Thunderbird avviato."
    elif "excel" in nome:
        subprocess.Popen(["excel.exe"])
        return "Microsoft Excel aperto."
    elif "explorer" in nome or "cartella" in nome:
        subprocess.Popen(["explorer.exe"])
        return "Esplora file aperto."
    elif "prompt" in nome or "cmd" in nome:
        subprocess.Popen(["cmd.exe"])
        return "Prompt dei comandi aperto."
    elif "browser" in nome:
        subprocess.Popen(["start", "https://duckduckgo.com/"], shell=True)
        return "Browser."

    else:
        return "Applicazione non riconosciuta."
        
# --- LOG ---
def log_command(cmd):
    with open(LOG_FILE, "a", encoding="utf-8") as f:
        f.write(f"[{time.strftime('%H:%M:%S')}] {cmd}\n")

# --- INTERFACCIA GRAFICA STILE KITT ---
class KITTUI(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("KRIS Assistant Alpha - Stile KITT")
        self.configure(bg="#111")
        self.geometry("650x340")
        self.resizable(False, False)
        # Display retrò
        self.display = tk.Text(self, height=10, bg="#222", fg="#39ff14", font=("Consolas", 16), insertbackground="#39ff14")
        self.display.pack(fill="both", padx=10, pady=10)
        self.display.insert("end", ">>> KRIS ASSISTANT ALPHA <<<\n")
        self.display.configure(state="disabled")
        # Barra "in ascolto" LED
        self.led_canvas = tk.Canvas(self, width=400, height=30, bg="#111", highlightthickness=0)
        self.led_canvas.pack(pady=5)
        self.leds = [self.led_canvas.create_oval(10+40*i,5,40+40*i,25,fill="#222",outline="#39ff14",width=2) for i in range(10)]
        # Pulsanti
        btn_frame = tk.Frame(self, bg="#111")
        btn_frame.pack()
        tk.Button(btn_frame, text="Parla", font=("Consolas", 12), command=self.comando_vocale).pack(side="left", padx=7)
        tk.Button(btn_frame, text="Leggi tutto", font=("Consolas", 12), command=self.leggi_tutto).pack(side="left", padx=7)
        tk.Button(btn_frame, text="Salva nota", font=("Consolas", 12), command=self.salva_nota).pack(side="left", padx=7)
        tk.Button(btn_frame, text="Config", font=("Consolas", 12), command=self.apri_config).pack(side="left", padx=7)
        tk.Button(btn_frame, text="Esci", font=("Consolas", 12), command=self.destroy).pack(side="left", padx=7)
        self.after(100, self.anim_led)
        self.anim_idx = 0

    def anim_led(self):
        for i, led in enumerate(self.leds):
            color = "#39ff14" if i == self.anim_idx else "#222"
            self.led_canvas.itemconfig(led, fill=color)
        self.anim_idx = (self.anim_idx + 1) % len(self.leds)
        self.after(120, self.anim_led)

    def comando_vocale(self):
        self.display.configure(state="normal")
        self.display.insert("end", "\n[KRIS] In ascolto...\n")
        self.display.see("end")
        self.display.configure(state="disabled")
        threading.Thread(target=self._process_comando, daemon=True).start()

    def _process_comando(self):
        text = trascrivi_audio().strip().lower()
        if not text:
            r = "[Nessun comando rilevato]"
        else:
            r = self.processa_comando(text)
        self.display.configure(state="normal")
        self.display.insert("end", f"> {text}\n{r}\n")
        self.display.see("end")
        self.display.configure(state="disabled")
        speak(r)

    def processa_comando(self, text):
        global current_text, reading_emails
        if any(b in text for b in config["blacklist"]):
            return "[Comando bloccato]"
        if text.startswith("scrivi "):
            current_text += text[7:] + " "
            return "Testo aggiunto."
        elif text.startswith("salva nota"):
            if not current_text.strip():
                return "Nessun testo da salvare."
            path = salva_nota(current_text)
            current_text = ""
            return f"Nota salvata in {path}"
        elif text.startswith("apri "):
            app = text[5:]
            return apri_app(app)
        elif "non leggere le email" in text:
            reading_emails = False
            return "Lettura email disattivata."
        elif "leggi tutto" in text:
            if not current_text.strip():
                return "Nessun testo da leggere."
            speak(current_text)
            return "[Sintesi vocale avviata]"
        elif "esci" in text:
            self.quit()
            return "Arrivederci!"
        else:
            return "[Comando non riconosciuto]"

    def leggi_tutto(self):
        global current_text
        if not current_text.strip():
            speak("Nessun testo da leggere.")
        else:
            speak(current_text)

    def salva_nota(self):
        global current_text
        if not current_text.strip():
            messagebox.showinfo("KRIS", "Nessun testo da salvare.")
        else:
            path = salva_nota(current_text)
            messagebox.showinfo("KRIS", f"Nota salvata in\n{path}")
            current_text = ""

    def apri_config(self):
        ConfigDialog(self)

# --- PANNELLO DI CONFIGURAZIONE ---
class ConfigDialog(tk.Toplevel):
    def __init__(self, master):
        super().__init__(master)
        self.title("Configurazione KRIS")
        self.geometry("400x300")
        self.config(bg="#222")
        # Voce
        tk.Label(self, text="Voce (ID):", bg="#222", fg="#39ff14").pack()
        self.voice_var = tk.StringVar(value=config["voice"])
        tk.Entry(self, textvariable=self.voice_var, width=50).pack()
        # Velocità
        tk.Label(self, text="Velocità:", bg="#222", fg="#39ff14").pack()
        self.rate_var = tk.IntVar(value=config["rate"])
        tk.Entry(self, textvariable=self.rate_var).pack()
        # Volume
        tk.Label(self, text="Volume (0-1):", bg="#222", fg="#39ff14").pack()
        self.volume_var = tk.DoubleVar(value=config["volume"])
        tk.Entry(self, textvariable=self.volume_var).pack()
        # Blacklist
        tk.Label(self, text="Blacklist comandi (separati da ,):", bg="#222", fg="#39ff14").pack()
        self.bl_var = tk.StringVar(value=",".join(config["blacklist"]))
        tk.Entry(self, textvariable=self.bl_var, width=60).pack()
        # Note dir
        tk.Label(self, text="Cartella Note:", bg="#222", fg="#39ff14").pack()
        self.dir_var = tk.StringVar(value=config["note_dir"])
        tk.Entry(self, textvariable=self.dir_var, width=50).pack()
        # Salva
        tk.Button(self, text="Salva", command=self.salva).pack(pady=10)

    def salva(self):
        config["voice"] = self.voice_var.get() or None
        config["rate"] = int(self.rate_var.get())
        config["volume"] = float(self.volume_var.get())
        config["blacklist"] = [x.strip() for x in self.bl_var.get().split(",") if x.strip()]
        config["note_dir"] = self.dir_var.get() or NOTE_DIR
        save_config(config)
        messagebox.showinfo("KRIS", "Configurazione salvata. Riavvia per applicare i cambiamenti.")
        self.destroy()

if __name__ == "__main__":
    app = KITTUI()
    app.mainloop()