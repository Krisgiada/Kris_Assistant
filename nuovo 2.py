import tkinter as tk
from tkinter import messagebox
import os
import json
import threading
import time
import whisper
import torch
import subprocess
import sys
import sounddevice as sd
import numpy as np
import scipy.io.wavfile
import pyautogui
import webbrowser
import coqui_tts

CONFIG_FILE = "config.json"
NOTE_DIR = "note"
LOG_FILE = "logs/kris_log.txt"

# --- CONFIGURAZIONE DI DEFAULT ---
default_config = {
    "blacklist": [],
    "voice": None,
    "rate": 150,
    "volume": 1.0,
    "note_dir": NOTE_DIR,
    "browser": "brave",
    "nome_utente": "Kris",
    "wake_enabled": True,
    "custom_commands": {}
}

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

# --- CREA CARTELLE ---
config = load_config()
if not os.path.exists(config["note_dir"]):
    os.makedirs(config["note_dir"])
if not os.path.exists("logs"):
    os.makedirs("logs")

lock = threading.Lock()
current_text = ""
reading_emails = True
last_command = ""
wake_enabled = config.get("wake_enabled", True)

# --- PARLA ---
def speak(text):
    print(f"[SPEAK] {text}")
    threading.Thread(target=lambda: os.system(f"echo {text} | python3 -m pyttsx3 > nul"), daemon=True).start()

# --- INIZIALIZZA WHISPER ---
try:
    model = whisper.load_model("base")
except Exception as e:
    print("Errore nel caricamento di Whisper:", e)
    sys.exit(1)

# --- TRASCRIZIONE AUDIO ---
def trascrivi_audio():
    samplerate = 16000
    duration = 5
    try:
        speak("Dimmi " + config.get("nome_utente", "Kris"))
        audio = sd.rec(int(samplerate * duration), samplerate=samplerate, channels=1, dtype='float32')
        sd.wait()
        audio = np.squeeze(audio)
        audio_path = "temp.wav"
        scipy.io.wavfile.write(audio_path, samplerate, audio)
        result = model.transcribe(audio_path, language='it')
        os.remove(audio_path)
        return result["text"]
    except Exception as e:
        return f"[Errore audio: {e}]"

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
    elif "thunderbird" in nome:
        subprocess.Popen(["C:\\Program Files\\Mozilla Thunderbird\\thunderbird.exe"])
        return "Thunderbird avviato."
    elif "brave" in nome:
        subprocess.Popen(["C:\\Program Files\\BraveSoftware\\Brave-Browser\\Application\\brave.exe"])
        return "Brave avviato."
    elif "prompt" in nome or "cmd" in nome:
        subprocess.Popen(["cmd.exe"])
        return "Prompt dei comandi aperto."
    elif "esplora" in nome or "cartella" in nome:
        subprocess.Popen(["explorer.exe"])
        return "Esplora file aperto."
    else:
        return "Applicazione non riconosciuta."

# --- RICERCA WEB ---
def ricerca_web(query):
    speak("Sto cercando...")
    # Simulazione AI come Siri: solo feedback vocale, no browser
    # TODO: Integrare con LLM se disponibile offline
    return f"Ho cercato: {query}. Vuoi che continui a cercare o va bene così?"

# --- LOG ---
def log_command(cmd):
    with open(LOG_FILE, "a", encoding="utf-8") as f:
        f.write(f"[{time.strftime('%H:%M:%S')}] {cmd}\n")

# --- UI PRINCIPALE ---
class KITTUI(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("KRIS Assistant Alpha")
        self.configure(bg="#111")
        self.geometry("700x450")
        self.resizable(False, False)
        self.display = tk.Text(self, height=10, bg="#222", fg="#39ff14", font=("Consolas", 16), insertbackground="#39ff14")
        self.display.pack(fill="both", padx=10, pady=10)
        self.display.insert("end", ">>> KRIS ASSISTANT ALPHA <<<\n")
        self.display.configure(state="disabled")
        self.led_canvas = tk.Canvas(self, width=400, height=30, bg="#111", highlightthickness=0)
        self.led_canvas.pack(pady=5)
        self.leds = [self.led_canvas.create_oval(10+40*i,5,40+40*i,25,fill="#222",outline="#39ff14",width=2) for i in range(10)]
        btn_frame = tk.Frame(self, bg="#111")
        btn_frame.pack()
        tk.Button(btn_frame, text="Parla", font=("Consolas", 12), command=self.comando_vocale).pack(side="left", padx=7)
        tk.Button(btn_frame, text="Leggi tutto", font=("Consolas", 12), command=self.leggi_tutto).pack(side="left", padx=7)
        tk.Button(btn_frame, text="Salva nota", font=("Consolas", 12), command=self.salva_nota).pack(side="left", padx=7)
        self.toggle_btn = tk.Button(btn_frame, text="Wake On" if wake_enabled else "Wake Off", font=("Consolas", 12), command=self.toggle_wake)
        self.toggle_btn.pack(side="left", padx=7)
        tk.Button(btn_frame, text="Esci", font=("Consolas", 12), command=self.destroy).pack(side="left", padx=7)
        self.after(100, self.anim_led)
        self.anim_idx = 0

    def anim_led(self):
        for i, led in enumerate(self.leds):
            color = "#39ff14" if i == self.anim_idx else "#222"
            self.led_canvas.itemconfig(led, fill=color)
        self.anim_idx = (self.anim_idx + 1) % len(self.leds)
        self.after(120, self.anim_led)

    def toggle_wake(self):
        global wake_enabled
        wake_enabled = not wake_enabled
        config["wake_enabled"] = wake_enabled
        save_config(config)
        self.toggle_btn.config(text="Wake On" if wake_enabled else "Wake Off")

    def comando_vocale(self):
        self.display.configure(state="normal")
        self.display.insert("end", f"\n[KRIS] In ascolto...\n")
        self.display.see("end")
        self.display.configure(state="disabled")
        threading.Thread(target=self._process_comando, daemon=True).start()

    def _process_comando(self):
        global current_text, last_command
        text = trascrivi_audio().strip().lower()
        if not text:
            r = "[Nessun comando rilevato]"
        else:
            last_command = text
            r = self.processa_comando(text)
        log_command(text)
        self.display.configure(state="normal")
        self.display.insert("end", f"> {text}\n{r}\n")
        self.display.see("end")
        self.display.configure(state="disabled")
        speak(r)

    def processa_comando(self, text):
        global current_text, reading_emails
        if any(b in text for b in config["blacklist"]):
            return "[Comando bloccato]"
        if text.startswith("scrivi") or "mi digiti" in text:
            content = text.split("scrivi", 1)[-1] if "scrivi" in text else text.split("digiti", 1)[-1]
            pyautogui.typewrite(content.strip())
            return "Testo digitato."
        elif text.startswith("salva nota"):
            with lock:
                if not current_text.strip():
                    return "Nessun testo da salvare."
                path = salva_nota(current_text)
                current_text = ""
            return f"Nota salvata in {path}"
        elif text.startswith("apri "):
            return apri_app(text[5:])
        elif text.startswith("fai una ricerca") or text.startswith("kit cerca"):
            query = text.split("cerca", 1)[-1].strip()
            return ricerca_web(query)
        elif text in config.get("custom_commands", {}):
            return config["custom_commands"][text]
        elif "non leggere le email" in text:
            reading_emails = False
            return "Lettura email disattivata."
        elif "leggi tutto" in text:
            with lock:
                if not current_text.strip():
                    speak("Nessun testo da leggere.")
                    return ""
                speak(current_text)
                return "[Sintesi vocale avviata]"
        elif "ripeti" in text:
            speak(last_command)
            return f"[Ultimo comando: {last_command}]"
        elif "esci" in text:
            self.quit()
            return "Arrivederci!"
        else:
            return "[Comando non riconosciuto]"

    def leggi_tutto(self):
        global current_text
        with lock:
            if not current_text.strip():
                speak("Nessun testo da leggere.")
            else:
                speak(current_text)

    def salva_nota(self):
        global current_text
        with lock:
            if not current_text.strip():
                messagebox.showinfo("KRIS", "Nessun testo da salvare.")
            else:
                path = salva_nota(current_text)
                messagebox.showinfo("KRIS", f"Nota salvata in\n{path}")
                current_text = ""

if __name__ == "__main__":
    app = KITTUI()
    app.mainloop()
