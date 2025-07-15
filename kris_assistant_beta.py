#!/usr/bin/env python3
"""
KRIS Assistant Beta - Enhanced Accessibility Version
Enhanced KITT-style interface with 80s aesthetics and advanced accessibility features
"""

import sys
import os
import subprocess
import importlib.util
import json
import threading
import time
import random
import webbrowser
import tempfile
import queue
import platform
from datetime import datetime
from pathlib import Path

# Auto-installation system
def install_package(package_name, import_name=None):
    """Auto-install packages if not available"""
    if import_name is None:
        import_name = package_name
    
    try:
        __import__(import_name)
        return True
    except ImportError:
        print(f"Installing {package_name}...")
        try:
            subprocess.check_call([sys.executable, "-m", "pip", "install", package_name])
            return True
        except subprocess.CalledProcessError as e:
            print(f"Failed to install {package_name}: {e}")
            return False

def check_and_install_dependencies():
    """Check and install all required dependencies"""
    dependencies = [
        ("customtkinter", "customtkinter"),
        ("pyttsx3", "pyttsx3"),
        ("openai-whisper", "whisper"),
        ("torch", "torch"),
        ("sounddevice", "sounddevice"),
        ("pyaudio", "pyaudio"),
        ("numpy", "numpy"),
        ("scipy", "scipy"),
        ("pyautogui", "pyautogui"),
        ("requests", "requests"),
        ("TTS", "TTS"),  # Coqui-TTS
        ("soundfile", "soundfile"),
    ]
    
    print("🔍 Checking dependencies...")
    missing_deps = []
    
    for package, import_name in dependencies:
        if not install_package(package, import_name):
            missing_deps.append(package)
    
    if missing_deps:
        print(f"❌ Failed to install: {', '.join(missing_deps)}")
        return False
    
    print("✅ All dependencies installed successfully!")
    return True

# Check dependencies before importing
if not check_and_install_dependencies():
    print("❌ Dependency installation failed. Please install manually.")
    sys.exit(1)

# Import required modules after installation
try:
    import customtkinter as ctk
    import pyttsx3
    import whisper
    import torch
    import sounddevice as sd
    import pyaudio
    import numpy as np
    import scipy.io.wavfile
    import pyautogui
    import requests
    from TTS.api import TTS
    import soundfile as sf
except ImportError as e:
    print(f"❌ Import error: {e}")
    sys.exit(1)

# === CONFIGURATION SYSTEM ===
CONFIG_FILE = "config.json"
NOTE_DIR = "note"
LOG_FILE = "logs/kris_log.txt"

# Enhanced default configuration
default_config = {
    "voice_settings": {
        "voice_index": 0,
        "rate": 150,
        "volume": 1.0,
        "tts_engine": "coqui",  # "coqui" or "pyttsx3"
        "coqui_model": "tts_models/it/mai_female/glow-tts"
    },
    "ui_settings": {
        "theme": "dark",
        "led_animation_speed": 120,
        "led_count": 12,
        "high_contrast": True,
        "large_ui_elements": True,
        "window_size": "800x500"
    },
    "accessibility": {
        "wake_word_enabled": True,
        "wake_word": "kit",
        "auto_username_detection": True,
        "username": "Kris",
        "voice_interruption": True,
        "microphone_monitoring": True,
        "fallback_notifications": True
    },
    "search_settings": {
        "default_search_engine": "duckduckgo",
        "available_engines": {
            "duckduckgo": "https://duckduckgo.com/?q=",
            "google": "https://www.google.com/search?q=",
            "bing": "https://www.bing.com/search?q=",
            "ecosia": "https://www.ecosia.org/search?q="
        },
        "search_results_count": 3,
        "auto_read_results": True
    },
    "language_settings": {
        "primary_language": "it",
        "whisper_model": "base",
        "available_languages": {
            "it": "Italiano",
            "en": "English",
            "es": "Español",
            "fr": "Français",
            "de": "Deutsch"
        }
    },
    "programs": {
        "notepad": "notepad.exe",
        "calc": "calc.exe",
        "explorer": "explorer.exe",
        "cmd": "cmd.exe",
        "brave": "C:\\Program Files\\BraveSoftware\\Brave-Browser\\Application\\brave.exe",
        "chrome": "C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe",
        "firefox": "C:\\Program Files\\Mozilla Firefox\\firefox.exe"
    },
    "security": {
        "blacklist_commands": [
            "elimina sistema",
            "formatta disco",
            "shutdown",
            "del /f /s /q",
            "rm -rf",
            "format c:",
            "wipe",
            "destroy"
        ],
        "safe_mode": True,
        "require_confirmation": True
    },
    "response_timing": {
        "listen_timeout": 5,
        "processing_delay": 0.5,
        "voice_pause": 1.0,
        "led_response_delay": 0.1
    }
}

def load_config():
    """Load configuration with fallback to defaults"""
    if os.path.exists(CONFIG_FILE):
        try:
            with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
                loaded = json.load(f)
                # Merge with defaults for new fields
                config = default_config.copy()
                config.update(loaded)
                return config
        except Exception as e:
            print(f"⚠️ Config error: {e}. Using defaults.")
            return default_config.copy()
    return default_config.copy()

def save_config(config):
    """Save configuration to file"""
    try:
        with open(CONFIG_FILE, 'w', encoding='utf-8') as f:
            json.dump(config, f, indent=2, ensure_ascii=False)
        return True
    except Exception as e:
        print(f"❌ Config save error: {e}")
        return False

# Global configuration
config = load_config()

# Create necessary directories
for directory in [NOTE_DIR, "logs", "temp"]:
    Path(directory).mkdir(exist_ok=True)

# === GLOBAL VARIABLES ===
current_text = ""
reading_active = False
last_command = ""
wake_enabled = config["accessibility"]["wake_word_enabled"]
microphone_active = False
voice_lock = threading.Lock()
tts_engine = None
whisper_model = None
coqui_tts = None

# === COQUI TTS INTEGRATION ===
def initialize_coqui_tts():
    """Initialize Coqui TTS with Italian female voice"""
    global coqui_tts
    try:
        print("🔊 Initializing Coqui TTS...")
        model_name = config["voice_settings"]["coqui_model"]
        coqui_tts = TTS(model_name=model_name, progress_bar=False, gpu=False)
        print("✅ Coqui TTS initialized successfully!")
        return True
    except Exception as e:
        print(f"❌ Coqui TTS initialization failed: {e}")
        return False

def initialize_fallback_tts():
    """Initialize fallback pyttsx3 TTS"""
    global tts_engine
    try:
        print("🔊 Initializing fallback TTS...")
        tts_engine = pyttsx3.init()
        voices = tts_engine.getProperty('voices')
        
        # Try to find Italian voice
        italian_voice = None
        for voice in voices:
            if 'it' in voice.id.lower() or 'italian' in voice.name.lower():
                italian_voice = voice.id
                break
        
        if italian_voice:
            tts_engine.setProperty('voice', italian_voice)
        
        tts_engine.setProperty('rate', config["voice_settings"]["rate"])
        tts_engine.setProperty('volume', config["voice_settings"]["volume"])
        print("✅ Fallback TTS initialized!")
        return True
    except Exception as e:
        print(f"❌ Fallback TTS initialization failed: {e}")
        return False

# === VOICE SYNTHESIS ===
def speak(text, interrupt_check=True):
    """Enhanced speak function with Coqui TTS and fallback"""
    global reading_active
    
    if not text or text.strip() == "":
        return
    
    with voice_lock:
        reading_active = True
        
        try:
            # Try Coqui TTS first
            if coqui_tts and config["voice_settings"]["tts_engine"] == "coqui":
                temp_file = os.path.join("temp", f"tts_{int(time.time())}.wav")
                coqui_tts.tts_to_file(text=text, file_path=temp_file)
                
                # Play the generated audio
                if os.path.exists(temp_file):
                    play_audio_file(temp_file)
                    os.remove(temp_file)
                    
            # Fallback to pyttsx3
            elif tts_engine:
                tts_engine.say(text)
                tts_engine.runAndWait()
                
        except Exception as e:
            print(f"❌ TTS Error: {e}")
            # Ultimate fallback - system notification
            if config["accessibility"]["fallback_notifications"]:
                show_notification("KRIS Assistant", text)
                
        finally:
            reading_active = False

def play_audio_file(file_path):
    """Play audio file using sounddevice"""
    try:
        data, fs = sf.read(file_path)
        sd.play(data, fs)
        sd.wait()
    except Exception as e:
        print(f"❌ Audio playback error: {e}")

def stop_speech():
    """Stop current speech synthesis"""
    global reading_active
    try:
        if tts_engine:
            tts_engine.stop()
        sd.stop()
        reading_active = False
    except Exception as e:
        print(f"❌ Stop speech error: {e}")

# === WHISPER INTEGRATION ===
def initialize_whisper():
    """Initialize Whisper model"""
    global whisper_model
    try:
        print("🎤 Initializing Whisper...")
        model_name = config["language_settings"]["whisper_model"]
        whisper_model = whisper.load_model(model_name)
        print("✅ Whisper initialized successfully!")
        return True
    except Exception as e:
        print(f"❌ Whisper initialization failed: {e}")
        return False

def check_microphone():
    """Check if microphone is available and working"""
    global microphone_active
    try:
        # Test microphone access
        test_recording = sd.rec(int(0.1 * 16000), samplerate=16000, channels=1)
        sd.wait()
        microphone_active = True
        return True
    except Exception as e:
        microphone_active = False
        print(f"❌ Microphone error: {e}")
        return False

def transcribe_audio():
    """Enhanced audio transcription with better error handling"""
    if not whisper_model:
        return "[Whisper non disponibile]"
    
    samplerate = 16000
    duration = config["response_timing"]["listen_timeout"]
    
    try:
        # Check microphone first
        if not check_microphone():
            return "[Microfono non disponibile]"
        
        # Get username for personalized response
        username = get_username()
        speak(f"Dimmi {username}")
        
        # Record audio
        audio = sd.rec(int(samplerate * duration), samplerate=samplerate, channels=1, dtype='float32')
        sd.wait()
        
        # Process audio
        audio = np.squeeze(audio)
        temp_audio = os.path.join("temp", f"audio_{int(time.time())}.wav")
        scipy.io.wavfile.write(temp_audio, samplerate, audio)
        
        # Transcribe
        result = whisper_model.transcribe(temp_audio, language=config["language_settings"]["primary_language"])
        
        # Clean up
        if os.path.exists(temp_audio):
            os.remove(temp_audio)
        
        return result["text"].strip()
        
    except Exception as e:
        return f"[Errore trascrizione: {e}]"

# === UTILITY FUNCTIONS ===
def get_username():
    """Get username from system or config"""
    if config["accessibility"]["auto_username_detection"]:
        try:
            if platform.system() == "Windows":
                return os.getenv("USERNAME", config["accessibility"]["username"])
            else:
                return os.getenv("USER", config["accessibility"]["username"])
        except:
            return config["accessibility"]["username"]
    return config["accessibility"]["username"]

def show_notification(title, message):
    """Show system notification as fallback"""
    try:
        if platform.system() == "Windows":
            import plyer
            plyer.notification.notify(title=title, message=message, timeout=5)
        else:
            print(f"[{title}] {message}")
    except:
        print(f"[{title}] {message}")

def log_command(command, result=""):
    """Enhanced logging system"""
    try:
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        with open(LOG_FILE, "a", encoding="utf-8") as f:
            f.write(f"[{timestamp}] Command: {command}\n")
            if result:
                f.write(f"[{timestamp}] Result: {result}\n")
            f.write("-" * 50 + "\n")
    except Exception as e:
        print(f"❌ Log error: {e}")

# === WEB SEARCH FUNCTIONALITY ===
def search_web(query, engine=None):
    """Enhanced web search with multiple engines"""
    if not engine:
        engine = config["search_settings"]["default_search_engine"]
    
    engines = config["search_settings"]["available_engines"]
    
    if engine not in engines:
        return "Motore di ricerca non supportato"
    
    try:
        speak("Sto effettuando la ricerca...")
        
        # For demonstration - in real implementation this would use actual search APIs
        search_url = engines[engine] + query.replace(" ", "+")
        
        # Simulate search results
        results = [
            f"Primo risultato per '{query}': Informazioni dettagliate disponibili",
            f"Secondo risultato per '{query}': Documentazione e guide utili",
            f"Terzo risultato per '{query}': Forum e discussioni della comunità"
        ]
        
        response = f"Ho trovato {len(results)} risultati per '{query}':\n"
        for i, result in enumerate(results, 1):
            response += f"{i}. {result}\n"
        
        if config["search_settings"]["auto_read_results"]:
            speak(response)
        
        # Open browser with search results
        webbrowser.open(search_url)
        
        return response
        
    except Exception as e:
        return f"Errore durante la ricerca: {e}"

# === PROGRAM MANAGEMENT ===
def open_program(program_name):
    """Enhanced program opening with configurable paths"""
    program_name = program_name.lower().strip()
    programs = config["programs"]
    
    # Map common names to program keys
    program_map = {
        "blocco note": "notepad",
        "notepad": "notepad",
        "calcolatrice": "calc",
        "calc": "calc",
        "esplora file": "explorer",
        "explorer": "explorer",
        "cartella": "explorer",
        "prompt": "cmd",
        "cmd": "cmd",
        "brave": "brave",
        "chrome": "chrome",
        "firefox": "firefox"
    }
    
    program_key = program_map.get(program_name, program_name)
    
    if program_key in programs:
        try:
            subprocess.Popen([programs[program_key]])
            return f"{program_name.title()} aperto con successo"
        except Exception as e:
            return f"Errore nell'apertura di {program_name}: {e}"
    else:
        return f"Programma '{program_name}' non configurato"

def save_note(text):
    """Save note with timestamp"""
    try:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"{timestamp}.txt"
        filepath = os.path.join(NOTE_DIR, filename)
        
        with open(filepath, "w", encoding="utf-8") as f:
            f.write(f"KRIS Assistant Note - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write("=" * 50 + "\n")
            f.write(text)
        
        return filepath
    except Exception as e:
        return f"Errore salvataggio: {e}"

# === COMMAND PROCESSING ===
def process_command(text):
    """Enhanced command processing with wake word support"""
    global current_text, reading_active, last_command
    
    text = text.strip().lower()
    last_command = text
    
    # Security check
    if any(blocked in text for blocked in config["security"]["blacklist_commands"]):
        return "🚫 Comando bloccato per sicurezza"
    
    # Wake word check
    if config["accessibility"]["wake_word_enabled"]:
        wake_word = config["accessibility"]["wake_word"]
        if not text.startswith(wake_word):
            return f"Comando deve iniziare con '{wake_word}'"
        text = text[len(wake_word):].strip()
    
    try:
        # Voice interruption
        if config["accessibility"]["voice_interruption"] and reading_active:
            stop_speech()
        
        # Text input commands
        if text.startswith("scrivi") or "digita" in text:
            content = text.split("scrivi", 1)[-1] if "scrivi" in text else text.split("digita", 1)[-1]
            content = content.strip()
            pyautogui.typewrite(content)
            return f"Testo digitato: {content}"
        
        # Note management
        elif text.startswith("salva nota"):
            if not current_text.strip():
                return "Nessun testo da salvare"
            filepath = save_note(current_text)
            current_text = ""
            return f"Nota salvata: {filepath}"
        
        elif text.startswith("aggiungi nota"):
            content = text.split("aggiungi nota", 1)[-1].strip()
            current_text += content + " "
            return f"Testo aggiunto alla nota"
        
        # Program management
        elif text.startswith("apri"):
            program = text.split("apri", 1)[-1].strip()
            return open_program(program)
        
        # Search functionality
        elif text.startswith("cerca") or text.startswith("ricerca"):
            query = text.split("cerca", 1)[-1] if "cerca" in text else text.split("ricerca", 1)[-1]
            query = query.strip()
            return search_web(query)
        
        # Voice control
        elif "leggi tutto" in text:
            if not current_text.strip():
                return "Nessun testo da leggere"
            speak(current_text)
            return "Lettura avviata"
        
        elif "smetti di leggere" in text or "stop" in text:
            stop_speech()
            return "Lettura interrotta"
        
        # System commands
        elif "ripeti ultimo comando" in text:
            if last_command:
                return f"Ultimo comando: {last_command}"
            return "Nessun comando precedente"
        
        elif "stato microfono" in text:
            status = "attivo" if microphone_active else "non attivo"
            return f"Microfono: {status}"
        
        elif "esci" in text or "chiudi" in text:
            return "QUIT_COMMAND"
        
        else:
            return f"Comando non riconosciuto: {text}"
            
    except Exception as e:
        return f"Errore elaborazione comando: {e}"

# === ENHANCED KITT UI ===
class KITTBetaUI(ctk.CTk):
    def __init__(self):
        super().__init__()
        
        # Initialize TTS systems
        self.initialize_systems()
        
        # Window setup
        self.title("KRIS Assistant Beta - KITT Interface")
        self.geometry(config["ui_settings"]["window_size"])
        self.resizable(False, False)
        
        # Set theme
        ctk.set_appearance_mode("dark")
        ctk.set_default_color_theme("dark-blue")
        
        # Colors - 80s KITT style
        self.colors = {
            "bg": "#0a0a0a",
            "panel": "#1a1a1a",
            "led_off": "#2a0a0a",
            "led_on": "#ff0000",
            "text": "#ffaa00",
            "accent": "#ff4444",
            "button": "#333333",
            "button_hover": "#444444"
        }
        
        self.configure(fg_color=self.colors["bg"])
        
        # Initialize variables
        self.led_states = [False] * config["ui_settings"]["led_count"]
        self.led_animation_active = True
        self.voice_level = 0
        self.is_listening = False
        
        self.setup_ui()
        self.start_animations()
        
    def initialize_systems(self):
        """Initialize all required systems"""
        print("🚀 Initializing KRIS Assistant Beta...")
        
        # Initialize TTS
        if not initialize_coqui_tts():
            initialize_fallback_tts()
        
        # Initialize Whisper
        initialize_whisper()
        
        # Check microphone
        check_microphone()
        
        print("✅ Systems initialized!")
        
    def setup_ui(self):
        """Setup the enhanced KITT-style interface"""
        # Main title
        title_frame = ctk.CTkFrame(self, fg_color=self.colors["panel"])
        title_frame.pack(fill="x", padx=10, pady=5)
        
        title_label = ctk.CTkLabel(
            title_frame,
            text="K R I S   A S S I S T A N T   B E T A",
            font=ctk.CTkFont(family="Courier", size=24, weight="bold"),
            text_color=self.colors["accent"]
        )
        title_label.pack(pady=10)
        
        # LED Display Panel
        self.led_frame = ctk.CTkFrame(self, fg_color=self.colors["panel"])
        self.led_frame.pack(fill="x", padx=10, pady=5)
        
        # LED Canvas
        self.led_canvas = ctk.CTkCanvas(
            self.led_frame,
            height=60,
            bg=self.colors["bg"],
            highlightthickness=0
        )
        self.led_canvas.pack(fill="x", padx=20, pady=10)
        
        # Create LED elements
        self.leds = []
        led_count = config["ui_settings"]["led_count"]
        canvas_width = 760  # Approximate canvas width
        led_spacing = canvas_width // (led_count + 1)
        
        for i in range(led_count):
            x = led_spacing * (i + 1)
            led = self.led_canvas.create_rectangle(
                x-15, 20, x+15, 40,
                fill=self.colors["led_off"],
                outline=self.colors["led_on"],
                width=2
            )
            self.leds.append(led)
        
        # Status display
        self.status_frame = ctk.CTkFrame(self, fg_color=self.colors["panel"])
        self.status_frame.pack(fill="both", expand=True, padx=10, pady=5)
        
        self.status_text = ctk.CTkTextbox(
            self.status_frame,
            font=ctk.CTkFont(family="Courier", size=14),
            text_color=self.colors["text"],
            fg_color=self.colors["bg"],
            wrap="word"
        )
        self.status_text.pack(fill="both", expand=True, padx=10, pady=10)
        
        # Initial message
        self.add_status_message(">>> KRIS ASSISTANT BETA INITIALIZED <<<")
        self.add_status_message("🎤 Microphone: " + ("Active" if microphone_active else "Inactive"))
        self.add_status_message("🔊 TTS Engine: " + config["voice_settings"]["tts_engine"])
        self.add_status_message("👤 User: " + get_username())
        
        # Control buttons
        self.button_frame = ctk.CTkFrame(self, fg_color=self.colors["panel"])
        self.button_frame.pack(fill="x", padx=10, pady=5)
        
        button_config = {
            "font": ctk.CTkFont(family="Courier", size=12, weight="bold"),
            "text_color": self.colors["text"],
            "fg_color": self.colors["button"],
            "hover_color": self.colors["button_hover"],
            "height": 44 if config["ui_settings"]["large_ui_elements"] else 32
        }
        
        # Wake toggle button
        self.wake_btn = ctk.CTkButton(
            self.button_frame,
            text="WAKE ON" if wake_enabled else "WAKE OFF",
            command=self.toggle_wake,
            **button_config
        )
        self.wake_btn.pack(side="left", padx=5, pady=5)
        
        # Voice command button
        self.voice_btn = ctk.CTkButton(
            self.button_frame,
            text="VOICE COMMAND",
            command=self.voice_command,
            **button_config
        )
        self.voice_btn.pack(side="left", padx=5, pady=5)
        
        # Search button
        self.search_btn = ctk.CTkButton(
            self.button_frame,
            text="WEB SEARCH",
            command=self.web_search,
            **button_config
        )
        self.search_btn.pack(side="left", padx=5, pady=5)
        
        # Configuration button
        self.config_btn = ctk.CTkButton(
            self.button_frame,
            text="CONFIG",
            command=self.open_config,
            **button_config
        )
        self.config_btn.pack(side="left", padx=5, pady=5)
        
        # Exit button
        self.exit_btn = ctk.CTkButton(
            self.button_frame,
            text="EXIT",
            command=self.quit_application,
            **button_config
        )
        self.exit_btn.pack(side="right", padx=5, pady=5)
        
    def add_status_message(self, message):
        """Add message to status display"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        formatted_message = f"[{timestamp}] {message}\n"
        self.status_text.insert("end", formatted_message)
        self.status_text.see("end")
        
    def start_animations(self):
        """Start LED animations"""
        self.animate_leds()
        
    def animate_leds(self):
        """Animate LED display based on system state"""
        if not self.led_animation_active:
            return
            
        # Different animation patterns based on state
        if self.is_listening:
            # Audio-reactive animation during listening
            self.animate_audio_reactive()
        elif reading_active:
            # Speaking animation
            self.animate_speaking()
        else:
            # Idle animation
            self.animate_idle()
            
        # Schedule next animation frame
        self.after(config["ui_settings"]["led_animation_speed"], self.animate_leds)
        
    def animate_idle(self):
        """Idle LED animation - classic KITT sweep"""
        current_time = time.time()
        sweep_position = int((current_time * 2) % (len(self.leds) * 2))
        
        for i, led in enumerate(self.leds):
            if sweep_position < len(self.leds):
                # Forward sweep
                distance = abs(i - sweep_position)
            else:
                # Backward sweep
                distance = abs(i - (len(self.leds) * 2 - sweep_position - 1))
            
            if distance == 0:
                color = self.colors["led_on"]
            elif distance == 1:
                color = "#aa0000"
            elif distance == 2:
                color = "#550000"
            else:
                color = self.colors["led_off"]
                
            self.led_canvas.itemconfig(led, fill=color)
            
    def animate_speaking(self):
        """Animation during speech synthesis"""
        # Random LED activation to simulate speech
        for i, led in enumerate(self.leds):
            if random.random() < 0.3:
                color = self.colors["led_on"]
            else:
                color = self.colors["led_off"]
            self.led_canvas.itemconfig(led, fill=color)
            
    def animate_audio_reactive(self):
        """Audio-reactive animation during listening"""
        # Simulate audio level response
        self.voice_level = random.random()
        active_leds = int(self.voice_level * len(self.leds))
        
        for i, led in enumerate(self.leds):
            if i < active_leds:
                color = self.colors["led_on"]
            else:
                color = self.colors["led_off"]
            self.led_canvas.itemconfig(led, fill=color)
            
    def toggle_wake(self):
        """Toggle wake word functionality"""
        global wake_enabled
        wake_enabled = not wake_enabled
        config["accessibility"]["wake_word_enabled"] = wake_enabled
        save_config(config)
        
        self.wake_btn.configure(text="WAKE ON" if wake_enabled else "WAKE OFF")
        status = "enabled" if wake_enabled else "disabled"
        self.add_status_message(f"🔊 Wake word {status}")
        
    def voice_command(self):
        """Process voice command"""
        self.is_listening = True
        self.voice_btn.configure(text="LISTENING...")
        self.add_status_message("🎤 Listening for command...")
        
        # Run in separate thread to avoid blocking UI
        threading.Thread(target=self._process_voice_command, daemon=True).start()
        
    def _process_voice_command(self):
        """Process voice command in background thread"""
        try:
            # Transcribe audio
            command = transcribe_audio()
            
            # Process command
            if command and command.strip():
                self.add_status_message(f"👤 Command: {command}")
                
                result = process_command(command)
                
                if result == "QUIT_COMMAND":
                    self.quit_application()
                    return
                
                self.add_status_message(f"🤖 Response: {result}")
                
                # Log command
                log_command(command, result)
                
                # Speak result
                if result and not result.startswith("Testo digitato"):
                    speak(result)
                    
            else:
                self.add_status_message("❌ No command detected")
                
        except Exception as e:
            error_msg = f"Error processing command: {e}"
            self.add_status_message(f"❌ {error_msg}")
            
        finally:
            self.is_listening = False
            self.voice_btn.configure(text="VOICE COMMAND")
            
    def web_search(self):
        """Open web search dialog"""
        search_dialog = SearchDialog(self)
        
    def open_config(self):
        """Open configuration dialog"""
        config_dialog = ConfigDialog(self)
        
    def quit_application(self):
        """Quit application safely"""
        self.led_animation_active = False
        stop_speech()
        speak("Arrivederci!")
        self.after(2000, self.quit)  # Give time for goodbye message

# === CONFIGURATION DIALOG ===
class ConfigDialog(ctk.CTkToplevel):
    def __init__(self, parent):
        super().__init__(parent)
        
        self.title("KRIS Assistant Configuration")
        self.geometry("600x700")
        self.resizable(False, False)
        
        # Make dialog modal
        self.transient(parent)
        self.grab_set()
        
        self.setup_ui()
        
    def setup_ui(self):
        """Setup configuration interface"""
        # Notebook for tabs
        self.notebook = ctk.CTkTabview(self)
        self.notebook.pack(fill="both", expand=True, padx=10, pady=10)
        
        # Voice settings tab
        voice_tab = self.notebook.add("Voice")
        self.setup_voice_tab(voice_tab)
        
        # Accessibility tab
        accessibility_tab = self.notebook.add("Accessibility")
        self.setup_accessibility_tab(accessibility_tab)
        
        # Search tab
        search_tab = self.notebook.add("Search")
        self.setup_search_tab(search_tab)
        
        # Programs tab
        programs_tab = self.notebook.add("Programs")
        self.setup_programs_tab(programs_tab)
        
        # Security tab
        security_tab = self.notebook.add("Security")
        self.setup_security_tab(security_tab)
        
        # Save button
        save_btn = ctk.CTkButton(
            self,
            text="Save Configuration",
            command=self.save_config,
            font=ctk.CTkFont(size=14, weight="bold")
        )
        save_btn.pack(pady=10)
        
    def setup_voice_tab(self, tab):
        """Setup voice configuration"""
        # TTS Engine selection
        ctk.CTkLabel(tab, text="TTS Engine:").pack(pady=5)
        self.tts_engine_var = ctk.StringVar(value=config["voice_settings"]["tts_engine"])
        tts_engine_menu = ctk.CTkOptionMenu(
            tab,
            values=["coqui", "pyttsx3"],
            variable=self.tts_engine_var
        )
        tts_engine_menu.pack(pady=5)
        
        # Voice rate
        ctk.CTkLabel(tab, text="Voice Rate:").pack(pady=5)
        self.rate_var = ctk.IntVar(value=config["voice_settings"]["rate"])
        rate_slider = ctk.CTkSlider(tab, from_=100, to=300, variable=self.rate_var)
        rate_slider.pack(pady=5)
        
        # Voice volume
        ctk.CTkLabel(tab, text="Voice Volume:").pack(pady=5)
        self.volume_var = ctk.DoubleVar(value=config["voice_settings"]["volume"])
        volume_slider = ctk.CTkSlider(tab, from_=0.1, to=1.0, variable=self.volume_var)
        volume_slider.pack(pady=5)
        
    def setup_accessibility_tab(self, tab):
        """Setup accessibility configuration"""
        # Username
        ctk.CTkLabel(tab, text="Username:").pack(pady=5)
        self.username_var = ctk.StringVar(value=config["accessibility"]["username"])
        username_entry = ctk.CTkEntry(tab, textvariable=self.username_var)
        username_entry.pack(pady=5)
        
        # Wake word
        ctk.CTkLabel(tab, text="Wake Word:").pack(pady=5)
        self.wake_word_var = ctk.StringVar(value=config["accessibility"]["wake_word"])
        wake_word_entry = ctk.CTkEntry(tab, textvariable=self.wake_word_var)
        wake_word_entry.pack(pady=5)
        
        # Checkboxes
        self.auto_username_var = ctk.BooleanVar(value=config["accessibility"]["auto_username_detection"])
        auto_username_check = ctk.CTkCheckBox(tab, text="Auto-detect username", variable=self.auto_username_var)
        auto_username_check.pack(pady=5)
        
        self.voice_interruption_var = ctk.BooleanVar(value=config["accessibility"]["voice_interruption"])
        voice_interruption_check = ctk.CTkCheckBox(tab, text="Voice interruption", variable=self.voice_interruption_var)
        voice_interruption_check.pack(pady=5)
        
        self.high_contrast_var = ctk.BooleanVar(value=config["ui_settings"]["high_contrast"])
        high_contrast_check = ctk.CTkCheckBox(tab, text="High contrast UI", variable=self.high_contrast_var)
        high_contrast_check.pack(pady=5)
        
        self.large_ui_var = ctk.BooleanVar(value=config["ui_settings"]["large_ui_elements"])
        large_ui_check = ctk.CTkCheckBox(tab, text="Large UI elements", variable=self.large_ui_var)
        large_ui_check.pack(pady=5)
        
    def setup_search_tab(self, tab):
        """Setup search configuration"""
        # Default search engine
        ctk.CTkLabel(tab, text="Default Search Engine:").pack(pady=5)
        self.search_engine_var = ctk.StringVar(value=config["search_settings"]["default_search_engine"])
        search_engine_menu = ctk.CTkOptionMenu(
            tab,
            values=list(config["search_settings"]["available_engines"].keys()),
            variable=self.search_engine_var
        )
        search_engine_menu.pack(pady=5)
        
        # Auto-read results
        self.auto_read_var = ctk.BooleanVar(value=config["search_settings"]["auto_read_results"])
        auto_read_check = ctk.CTkCheckBox(tab, text="Auto-read search results", variable=self.auto_read_var)
        auto_read_check.pack(pady=5)
        
        # Results count
        ctk.CTkLabel(tab, text="Results Count:").pack(pady=5)
        self.results_count_var = ctk.IntVar(value=config["search_settings"]["search_results_count"])
        results_slider = ctk.CTkSlider(tab, from_=1, to=10, variable=self.results_count_var)
        results_slider.pack(pady=5)
        
    def setup_programs_tab(self, tab):
        """Setup programs configuration"""
        # Scrollable frame for programs
        scroll_frame = ctk.CTkScrollableFrame(tab)
        scroll_frame.pack(fill="both", expand=True, padx=10, pady=10)
        
        self.program_vars = {}
        for program, path in config["programs"].items():
            ctk.CTkLabel(scroll_frame, text=f"{program.title()}:").pack(pady=2)
            var = ctk.StringVar(value=path)
            entry = ctk.CTkEntry(scroll_frame, textvariable=var, width=400)
            entry.pack(pady=2)
            self.program_vars[program] = var
            
    def setup_security_tab(self, tab):
        """Setup security configuration"""
        # Blacklist commands
        ctk.CTkLabel(tab, text="Blacklisted Commands:").pack(pady=5)
        self.blacklist_text = ctk.CTkTextbox(tab, height=200)
        self.blacklist_text.pack(fill="both", expand=True, padx=10, pady=5)
        
        # Populate blacklist
        blacklist_content = "\n".join(config["security"]["blacklist_commands"])
        self.blacklist_text.insert("0.0", blacklist_content)
        
        # Safety options
        self.safe_mode_var = ctk.BooleanVar(value=config["security"]["safe_mode"])
        safe_mode_check = ctk.CTkCheckBox(tab, text="Safe mode", variable=self.safe_mode_var)
        safe_mode_check.pack(pady=5)
        
        self.require_confirmation_var = ctk.BooleanVar(value=config["security"]["require_confirmation"])
        confirmation_check = ctk.CTkCheckBox(tab, text="Require confirmation", variable=self.require_confirmation_var)
        confirmation_check.pack(pady=5)
        
    def save_config(self):
        """Save configuration changes"""
        try:
            # Update config with new values
            config["voice_settings"]["tts_engine"] = self.tts_engine_var.get()
            config["voice_settings"]["rate"] = self.rate_var.get()
            config["voice_settings"]["volume"] = self.volume_var.get()
            
            config["accessibility"]["username"] = self.username_var.get()
            config["accessibility"]["wake_word"] = self.wake_word_var.get()
            config["accessibility"]["auto_username_detection"] = self.auto_username_var.get()
            config["accessibility"]["voice_interruption"] = self.voice_interruption_var.get()
            
            config["ui_settings"]["high_contrast"] = self.high_contrast_var.get()
            config["ui_settings"]["large_ui_elements"] = self.large_ui_var.get()
            
            config["search_settings"]["default_search_engine"] = self.search_engine_var.get()
            config["search_settings"]["auto_read_results"] = self.auto_read_var.get()
            config["search_settings"]["search_results_count"] = self.results_count_var.get()
            
            # Update programs
            for program, var in self.program_vars.items():
                config["programs"][program] = var.get()
            
            # Update security settings
            config["security"]["safe_mode"] = self.safe_mode_var.get()
            config["security"]["require_confirmation"] = self.require_confirmation_var.get()
            
            # Update blacklist
            blacklist_content = self.blacklist_text.get("0.0", "end").strip()
            config["security"]["blacklist_commands"] = [cmd.strip() for cmd in blacklist_content.split("\n") if cmd.strip()]
            
            # Save to file
            if save_config(config):
                # Show success message
                success_dialog = ctk.CTkMessageBox(
                    title="Configuration Saved",
                    message="Configuration saved successfully!\nRestart required for some changes to take effect.",
                    icon="check"
                )
                success_dialog.get()
                self.destroy()
            else:
                # Show error message
                error_dialog = ctk.CTkMessageBox(
                    title="Error",
                    message="Failed to save configuration!",
                    icon="cancel"
                )
                error_dialog.get()
                
        except Exception as e:
            error_dialog = ctk.CTkMessageBox(
                title="Error",
                message=f"Configuration error: {e}",
                icon="cancel"
            )
            error_dialog.get()

# === SEARCH DIALOG ===
class SearchDialog(ctk.CTkToplevel):
    def __init__(self, parent):
        super().__init__(parent)
        
        self.title("Web Search")
        self.geometry("500x200")
        self.resizable(False, False)
        
        # Make dialog modal
        self.transient(parent)
        self.grab_set()
        
        self.setup_ui()
        
    def setup_ui(self):
        """Setup search interface"""
        # Search query
        ctk.CTkLabel(self, text="Search Query:").pack(pady=10)
        self.query_var = ctk.StringVar()
        query_entry = ctk.CTkEntry(self, textvariable=self.query_var, width=400)
        query_entry.pack(pady=5)
        query_entry.focus()
        
        # Search engine selection
        ctk.CTkLabel(self, text="Search Engine:").pack(pady=10)
        self.engine_var = ctk.StringVar(value=config["search_settings"]["default_search_engine"])
        engine_menu = ctk.CTkOptionMenu(
            self,
            values=list(config["search_settings"]["available_engines"].keys()),
            variable=self.engine_var
        )
        engine_menu.pack(pady=5)
        
        # Buttons
        button_frame = ctk.CTkFrame(self)
        button_frame.pack(pady=20)
        
        search_btn = ctk.CTkButton(
            button_frame,
            text="Search",
            command=self.perform_search
        )
        search_btn.pack(side="left", padx=10)
        
        cancel_btn = ctk.CTkButton(
            button_frame,
            text="Cancel",
            command=self.destroy
        )
        cancel_btn.pack(side="left", padx=10)
        
        # Bind Enter key
        query_entry.bind("<Return>", lambda e: self.perform_search())
        
    def perform_search(self):
        """Perform web search"""
        query = self.query_var.get().strip()
        if not query:
            return
        
        engine = self.engine_var.get()
        result = search_web(query, engine)
        
        # Show result in parent window
        if hasattr(self.master, 'add_status_message'):
            self.master.add_status_message(f"🔍 Search: {query}")
            self.master.add_status_message(f"📝 Results: {result}")
        
        self.destroy()

# === MAIN APPLICATION ===
def main():
    """Main application entry point"""
    try:
        print("🚀 Starting KRIS Assistant Beta...")
        
        # Create and run application
        app = KITTBetaUI()
        app.mainloop()
        
    except Exception as e:
        print(f"❌ Application error: {e}")
        # Show error dialog if possible
        try:
            import tkinter as tk
            from tkinter import messagebox
            root = tk.Tk()
            root.withdraw()
            messagebox.showerror("KRIS Assistant Beta Error", f"Application failed to start:\n{e}")
        except:
            pass

if __name__ == "__main__":
    main()