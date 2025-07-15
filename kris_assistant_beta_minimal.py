#!/usr/bin/env python3
"""
KRIS Assistant Beta - Minimal Test Version
For testing UI and core functionality without heavy dependencies
"""

import sys
import os
import json
import threading
import time
import random
import webbrowser
from datetime import datetime
from pathlib import Path

# Mock heavy dependencies for testing
class MockTTS:
    def __init__(self, model_name=None, progress_bar=False, gpu=False):
        self.model_name = model_name
        
    def tts_to_file(self, text, file_path):
        print(f"[MOCK TTS] Generating: {text[:50]}...")
        # Create empty file for testing
        with open(file_path, "w") as f:
            f.write("mock audio data")

class MockWhisper:
    def transcribe(self, audio_path, language='it'):
        return {"text": "test command recognized"}

class MockAudio:
    @staticmethod
    def rec(frames, samplerate=16000, channels=1, dtype='float32'):
        import numpy as np
        return np.random.random((frames, 1))
    
    @staticmethod
    def wait():
        time.sleep(0.1)
    
    @staticmethod
    def play(data, fs):
        print(f"[MOCK AUDIO] Playing audio: {len(data)} samples")
    
    @staticmethod
    def stop():
        print("[MOCK AUDIO] Stopping audio")

# Try to import real dependencies, fall back to mocks
try:
    import customtkinter as ctk
    GUI_AVAILABLE = True
except ImportError:
    print("⚠️ CustomTkinter not available, using mock GUI")
    GUI_AVAILABLE = False

try:
    import numpy as np
    import scipy.io.wavfile
    AUDIO_AVAILABLE = True
except ImportError:
    print("⚠️ Audio libraries not available, using mocks")
    AUDIO_AVAILABLE = False
    
    # Mock numpy for basic operations
    class MockNumpy:
        @staticmethod
        def random(*args, **kwargs):
            class MockRandom:
                @staticmethod
                def random(shape):
                    return [[0.5] * shape[1] for _ in range(shape[0])]
            return MockRandom()
    
    np = MockNumpy()

# Mock other heavy imports
whisper_model = MockWhisper()
coqui_tts = MockTTS()
sd = MockAudio()

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
        "tts_engine": "coqui",
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
microphone_active = True  # Mock as active
voice_lock = threading.Lock()

# === UTILITY FUNCTIONS ===
def get_username():
    """Get username from system or config"""
    if config["accessibility"]["auto_username_detection"]:
        try:
            return os.getenv("USER", config["accessibility"]["username"])
        except:
            return config["accessibility"]["username"]
    return config["accessibility"]["username"]

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

def speak(text, interrupt_check=True):
    """Mock speak function"""
    print(f"[SPEAK] {text}")

def transcribe_audio():
    """Mock transcribe function"""
    # Simulate some processing time
    time.sleep(0.5)
    
    # Return mock commands for testing
    mock_commands = [
        "kit scrivi hello world",
        "kit apri notepad",
        "kit cerca python tutorial",
        "kit leggi tutto",
        "kit salva nota"
    ]
    
    return random.choice(mock_commands)

def search_web(query, engine=None):
    """Enhanced web search with multiple engines"""
    if not engine:
        engine = config["search_settings"]["default_search_engine"]
    
    engines = config["search_settings"]["available_engines"]
    
    if engine not in engines:
        return "Motore di ricerca non supportato"
    
    try:
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
        
        print(f"[SEARCH] Opening: {search_url}")
        
        return response
        
    except Exception as e:
        return f"Errore durante la ricerca: {e}"

def open_program(program_name):
    """Mock program opening"""
    print(f"[PROGRAM] Opening: {program_name}")
    return f"{program_name.title()} would be opened"

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
        # Text input commands
        if text.startswith("scrivi") or "digita" in text:
            content = text.split("scrivi", 1)[-1] if "scrivi" in text else text.split("digita", 1)[-1]
            content = content.strip()
            print(f"[TYPING] {content}")
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

# === CONSOLE UI FOR TESTING ===
class ConsoleUI:
    def __init__(self):
        self.running = True
        self.led_states = [False] * config["ui_settings"]["led_count"]
        
    def display_led_bar(self):
        """Display ASCII LED bar"""
        led_display = "["
        for state in self.led_states:
            led_display += "█" if state else "░"
        led_display += "]"
        return led_display
    
    def animate_leds(self):
        """Simple LED animation"""
        # Knight Rider style sweep
        current_time = time.time()
        sweep_position = int((current_time * 2) % (len(self.led_states) * 2))
        
        # Clear all LEDs
        self.led_states = [False] * len(self.led_states)
        
        # Set active LED
        if sweep_position < len(self.led_states):
            self.led_states[sweep_position] = True
        else:
            self.led_states[len(self.led_states) * 2 - sweep_position - 1] = True
    
    def run(self):
        """Run console interface"""
        print("🚀 KRIS Assistant Beta - Console Mode")
        print("=" * 50)
        print(f"👤 User: {get_username()}")
        print(f"🎤 Microphone: {'Active' if microphone_active else 'Inactive'}")
        print(f"🔊 Wake word: {config['accessibility']['wake_word']}")
        print("=" * 50)
        print("Commands: 'voice', 'search', 'config', 'quit'")
        print()
        
        while self.running:
            try:
                # Animate LEDs
                self.animate_leds()
                
                # Display status
                print(f"\r{self.display_led_bar()} KRIS Ready", end="", flush=True)
                
                # Get user input
                user_input = input("\n\n> ").strip().lower()
                
                if user_input == "quit" or user_input == "exit":
                    self.running = False
                    print("👋 Goodbye!")
                    break
                
                elif user_input == "voice":
                    print("🎤 Simulating voice command...")
                    command = transcribe_audio()
                    print(f"🗣️ Recognized: {command}")
                    
                    result = process_command(command)
                    print(f"🤖 Response: {result}")
                    
                    log_command(command, result)
                    
                elif user_input == "search":
                    query = input("🔍 Enter search query: ").strip()
                    if query:
                        result = search_web(query)
                        print(f"📝 Search results:\n{result}")
                
                elif user_input == "config":
                    print("⚙️ Configuration:")
                    print(f"  Voice Engine: {config['voice_settings']['tts_engine']}")
                    print(f"  Wake Word: {config['accessibility']['wake_word']}")
                    print(f"  Username: {config['accessibility']['username']}")
                    print(f"  Search Engine: {config['search_settings']['default_search_engine']}")
                
                elif user_input.startswith("kit "):
                    # Direct command processing
                    result = process_command(user_input)
                    print(f"🤖 Response: {result}")
                    log_command(user_input, result)
                
                else:
                    print("❓ Unknown command. Try 'voice', 'search', 'config', or 'quit'")
                    
            except KeyboardInterrupt:
                print("\n👋 Goodbye!")
                break
            except Exception as e:
                print(f"❌ Error: {e}")

# === MAIN APPLICATION ===
def main():
    """Main application entry point"""
    print("🚀 Starting KRIS Assistant Beta...")
    
    if GUI_AVAILABLE:
        try:
            print("🖥️ GUI mode not fully implemented in minimal version")
            print("🖥️ Starting console mode instead...")
            app = ConsoleUI()
            app.run()
        except Exception as e:
            print(f"❌ GUI Error: {e}")
            print("🖥️ Falling back to console mode...")
            app = ConsoleUI()
            app.run()
    else:
        print("🖥️ GUI not available, starting console mode...")
        app = ConsoleUI()
        app.run()

if __name__ == "__main__":
    main()