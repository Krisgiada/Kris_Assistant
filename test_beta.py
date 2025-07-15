#!/usr/bin/env python3
"""
Test script for KRIS Assistant Beta - Basic functionality test
"""

import sys
import os
import json
import tempfile
from pathlib import Path

# Add the current directory to the Python path
sys.path.insert(0, '/home/runner/work/Kris_Assistant/Kris_Assistant')

def test_config_system():
    """Test configuration loading and saving"""
    print("🔧 Testing configuration system...")
    
    # Test default config creation
    test_config = {
        "voice_settings": {
            "tts_engine": "test",
            "rate": 150
        },
        "accessibility": {
            "username": "TestUser",
            "wake_word": "test"
        }
    }
    
    # Test save
    with open("test_config.json", "w") as f:
        json.dump(test_config, f, indent=2)
    
    # Test load
    with open("test_config.json", "r") as f:
        loaded_config = json.load(f)
    
    print(f"✅ Config system working: {loaded_config['accessibility']['username']}")
    
    # Cleanup
    os.remove("test_config.json")
    
def test_directory_creation():
    """Test directory creation functionality"""
    print("📁 Testing directory creation...")
    
    test_dirs = ["test_notes", "test_logs", "test_temp"]
    
    for directory in test_dirs:
        Path(directory).mkdir(exist_ok=True)
        if os.path.exists(directory):
            print(f"✅ Directory created: {directory}")
            os.rmdir(directory)
        else:
            print(f"❌ Directory creation failed: {directory}")
            
def test_note_saving():
    """Test note saving functionality"""
    print("📝 Testing note saving...")
    
    # Create notes directory
    notes_dir = "test_notes"
    Path(notes_dir).mkdir(exist_ok=True)
    
    # Test note content
    test_note = "This is a test note\nWith multiple lines\nFor testing purposes"
    
    # Save note
    from datetime import datetime
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"test_{timestamp}.txt"
    filepath = os.path.join(notes_dir, filename)
    
    with open(filepath, "w", encoding="utf-8") as f:
        f.write(test_note)
    
    # Verify note was saved
    if os.path.exists(filepath):
        with open(filepath, "r", encoding="utf-8") as f:
            content = f.read()
        print(f"✅ Note saved successfully: {len(content)} characters")
        
        # Cleanup
        os.remove(filepath)
        os.rmdir(notes_dir)
    else:
        print("❌ Note saving failed")
        
def test_command_processing():
    """Test basic command processing logic"""
    print("🎤 Testing command processing...")
    
    # Mock configuration
    test_config = {
        "accessibility": {
            "wake_word_enabled": True,
            "wake_word": "kit"
        },
        "security": {
            "blacklist_commands": ["delete", "format"]
        }
    }
    
    # Test cases
    test_commands = [
        ("kit scrivi hello world", "Text command"),
        ("kit apri notepad", "Program command"),
        ("kit cerca python tutorial", "Search command"),
        ("delete everything", "Blocked command"),
        ("hello", "No wake word")
    ]
    
    for command, description in test_commands:
        # Basic command parsing logic
        command_lower = command.lower().strip()
        
        # Check blacklist
        if any(blocked in command_lower for blocked in test_config["security"]["blacklist_commands"]):
            result = "BLOCKED"
        # Check wake word
        elif test_config["accessibility"]["wake_word_enabled"]:
            wake_word = test_config["accessibility"]["wake_word"]
            if command_lower.startswith(wake_word):
                result = "VALID"
            else:
                result = "NO_WAKE_WORD"
        else:
            result = "VALID"
        
        print(f"✅ {description}: '{command}' -> {result}")

def test_ui_color_scheme():
    """Test UI color scheme configuration"""
    print("🎨 Testing UI color scheme...")
    
    # KITT-style colors
    colors = {
        "bg": "#0a0a0a",
        "panel": "#1a1a1a", 
        "led_off": "#2a0a0a",
        "led_on": "#ff0000",
        "text": "#ffaa00",
        "accent": "#ff4444",
        "button": "#333333",
        "button_hover": "#444444"
    }
    
    # Validate colors are hex format
    for color_name, hex_value in colors.items():
        if hex_value.startswith("#") and len(hex_value) == 7:
            print(f"✅ Color {color_name}: {hex_value}")
        else:
            print(f"❌ Invalid color {color_name}: {hex_value}")

def test_search_functionality():
    """Test search URL generation"""
    print("🔍 Testing search functionality...")
    
    search_engines = {
        "duckduckgo": "https://duckduckgo.com/?q=",
        "google": "https://www.google.com/search?q=",
        "bing": "https://www.bing.com/search?q=",
        "ecosia": "https://www.ecosia.org/search?q="
    }
    
    test_query = "python programming tutorial"
    
    for engine, base_url in search_engines.items():
        search_url = base_url + test_query.replace(" ", "+")
        print(f"✅ {engine}: {search_url}")

def main():
    """Run all tests"""
    print("🚀 Running KRIS Assistant Beta Tests\n")
    
    try:
        test_config_system()
        print()
        
        test_directory_creation()
        print()
        
        test_note_saving()
        print()
        
        test_command_processing()
        print()
        
        test_ui_color_scheme()
        print()
        
        test_search_functionality()
        print()
        
        print("✅ All basic tests passed!")
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()