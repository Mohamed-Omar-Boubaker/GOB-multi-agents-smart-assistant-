"""
Voice Client - Phase A: Push-to-Talk
=====================================

Simple voice client that:
1. Press SPACE to start recording
2. Speak while holding SPACE
3. Release SPACE → send to backend
4. Listen for response via MQTT

Usage:
    python voice_client_pushto_talk.py

Controls:
    SPACE - Hold to record
    CTRL+C - Quit
"""

import asyncio
import base64
import io
import json
import sys
import time
import wave
from datetime import datetime
from pathlib import Path
from typing import Optional

import httpx
import keyboard
import numpy as np
import paho.mqtt.client as mqtt
import pygame
import sounddevice as sd
import yaml
from colorama import Fore, Style, init

# Initialize colorama for colored output
init(autoreset=True)


class AudioRecorder:
    """Records audio from microphone using sounddevice."""
    
    def __init__(self, sample_rate=16000, channels=1):
        self.sample_rate = sample_rate
        self.channels = channels
        self.is_recording = False
        self.audio_data = []
        
    def start_recording(self):
        """Start recording audio."""
        self.is_recording = True
        self.audio_data = []
        
        print(f"{Fore.YELLOW}🔴 Recording... (release SPACE to send)")
        
    def callback(self, indata, frames, time_info, status):
        """Callback for audio stream."""
        if status:
            print(f"{Fore.RED}⚠️  Audio status: {status}")
        
        if self.is_recording:
            # Append audio data
            self.audio_data.append(indata.copy())
    
    def stop_recording(self) -> Optional[bytes]:
        """Stop recording and return WAV bytes."""
        self.is_recording = False
        
        if not self.audio_data:
            print(f"{Fore.RED}❌ No audio recorded")
            return None
        
        # Concatenate all audio chunks
        audio_array = np.concatenate(self.audio_data, axis=0)
        
        # Convert to 16-bit PCM
        audio_int16 = (audio_array * 32767).astype(np.int16)
        
        # Create WAV file in memory
        wav_buffer = io.BytesIO()
        with wave.open(wav_buffer, 'wb') as wav_file:
            wav_file.setnchannels(self.channels)
            wav_file.setsampwidth(2)  # 16-bit
            wav_file.setframerate(self.sample_rate)
            wav_file.writeframes(audio_int16.tobytes())
        
        wav_bytes = wav_buffer.getvalue()
        
        duration = len(audio_int16) / self.sample_rate
        
        # 🔥 CRITICAL FILTER: Minimum duration check
        MIN_DURATION = 1.0  # seconds
        
        if duration < MIN_DURATION:
            print(f"{Fore.YELLOW}⚠️  Recording too short ({duration:.1f}s)")
            print(f"{Fore.CYAN}💡 Hold SPACE for at least {MIN_DURATION}s to send a command")
            return None
        
        print(f"{Fore.GREEN}✅ Recording complete ({duration:.1f}s, {len(wav_bytes)} bytes)")
        
        return wav_bytes


class MQTTAudioPlayer:
    """Plays audio responses received via MQTT."""
    
    def __init__(self, broker="localhost", port=1883, topic="device/audio"):
        self.broker = broker
        self.port = port
        self.topic = topic
        self.client = mqtt.Client(client_id="voice_client_player")
        self.client.on_connect = self._on_connect
        self.client.on_message = self._on_message
        self.connected = False
        
        # Initialize pygame mixer
        pygame.mixer.init(frequency=22050, size=-16, channels=1, buffer=512)
        
    def _on_connect(self, client, userdata, flags, rc):
        """Callback: MQTT connected."""
        if rc == 0:
            self.connected = True
            print(f"{Fore.GREEN}🔗 MQTT connected")
            client.subscribe(self.topic, qos=1)
            print(f"{Fore.CYAN}👂 Listening for responses on: {self.topic}")
        else:
            print(f"{Fore.RED}❌ MQTT connection failed: code {rc}")
    
    def _on_message(self, client, userdata, msg):
        """Callback: Audio response received."""
        try:
            print(f"{Fore.GREEN}🎵 Response received, playing...")
            
            # Decode base64 audio
            audio_base64 = msg.payload.decode('utf-8')
            audio_bytes = base64.b64decode(audio_base64)
            
            # Play audio
            self._play_audio(audio_bytes)
            
            print(f"{Fore.GREEN}✅ Playback complete")
            
        except Exception as e:
            print(f"{Fore.RED}❌ Error playing audio: {e}")
    
    def _play_audio(self, audio_bytes: bytes):
        """Play audio bytes using pygame."""
        audio_buffer = io.BytesIO(audio_bytes)
        pygame.mixer.music.load(audio_buffer)
        pygame.mixer.music.play()
        
        # Wait for playback to finish
        while pygame.mixer.music.get_busy():
            time.sleep(0.1)
    
    def connect(self):
        """Connect to MQTT broker."""
        try:
            print(f"{Fore.CYAN}⏳ Connecting to MQTT broker...")
            self.client.connect(self.broker, self.port, keepalive=60)
            self.client.loop_start()
            
            # Wait for connection
            timeout = 5
            start = time.time()
            while not self.connected and (time.time() - start) < timeout:
                time.sleep(0.1)
            
            if not self.connected:
                print(f"{Fore.RED}❌ MQTT connection timeout")
                return False
            
            return True
            
        except Exception as e:
            print(f"{Fore.RED}❌ MQTT connection error: {e}")
            return False
    
    def disconnect(self):
        """Disconnect from MQTT broker."""
        self.client.loop_stop()
        self.client.disconnect()
        pygame.mixer.quit()


class VoiceClient:
    """Main voice client for push-to-talk interaction."""
    
    def __init__(self, config_path="voice_client_config.yaml"):
        """Initialize voice client."""
        # Load config
        self.config = self._load_config(config_path)
        
        # Audio recorder
        self.recorder = AudioRecorder(
            sample_rate=self.config['audio']['sample_rate'],
            channels=self.config['audio']['channels']
        )
        
        # MQTT audio player
        mqtt_config = self.config['mqtt']
        self.player = MQTTAudioPlayer(
            broker=mqtt_config['broker'],
            port=mqtt_config['port'],
            topic=mqtt_config['topic_audio_output']
        )
        
        # Backend config
        self.backend_url = self.config['backend']['url']
        self.backend_endpoint = self.config['backend']['endpoint']
        self.backend_timeout = self.config['backend']['timeout']
        self.language = self.config['backend']['language']
        
        # Audio stream
        self.stream = None
        
        # State
        self.is_running = False
        self.pending_action_id = None  # Track action awaiting confirmation
        
    def _load_config(self, path: str) -> dict:
        """Load configuration from YAML file."""
        config_file = Path(path)
        
        if not config_file.exists():
            print(f"{Fore.RED}❌ Config file not found: {path}")
            sys.exit(1)
        
        with open(config_file, 'r') as f:
            return yaml.safe_load(f)
    
    async def send_audio_to_backend(self, audio_bytes: bytes) -> bool:
        """Send audio to backend API."""
        try:
            print(f"{Fore.MAGENTA}📤 Sending to backend...")
            
            # Encode to base64
            audio_base64 = base64.b64encode(audio_bytes).decode('utf-8')
            
            # Prepare request
            payload = {
                "command_type": "audio",
                "user_id": "voice_client_pc_001",
                "audio_data": audio_base64,
                "audio_format": "wav",
                "language": self.language,
                "source": "voice_client"
            }
            
            # Send to backend
            url = f"{self.backend_url}{self.backend_endpoint}"
            
            async with httpx.AsyncClient(timeout=self.backend_timeout) as client:
                response = await client.post(url, json=payload)
                
                if response.status_code == 200:
                    result = response.json()
                    transcription = result.get('transcription', 'N/A')
                    
                    # Display transcription
                    print(f"{Fore.CYAN}📝 Transcription: {transcription}")
                    
                    # Check if this is a confirmation response for pending action
                    if self.pending_action_id:
                        confirmation_keywords = ['yes', 'oui', 'confirm', 'ok', 'no', 'non', 'cancel', 'annuler']
                        if any(kw in transcription.lower() for kw in confirmation_keywords):
                            # This is a confirmation! Send to /action/confirm endpoint
                            await self._confirm_action(transcription)
                            return True
                    
                    # Handle both conversation and action responses
                    response_text = result.get('response') or result.get('message')
                    classification = result.get('classification', 'unknown')
                    
                    if response_text:
                        if classification == 'action':
                            status = result.get('status', '')
                            if status == 'awaiting_confirmation':
                                # Store action_id for next response
                                self.pending_action_id = result.get('action_id')
                                print(f"{Fore.YELLOW}⚠️  ACTION CONFIRMATION NEEDED:")
                                print(f"{Fore.YELLOW}   {response_text}")
                                print(f"{Fore.YELLOW}   → Say 'YES' or 'CONFIRM' to proceed")
                                print(f"{Fore.YELLOW}   → Say 'NO' or 'CANCEL' to abort")
                            else:
                                print(f"{Fore.CYAN}🎬 Action: {response_text[:100]}...")
                        else:
                            print(f"{Fore.CYAN}💬 Response: {response_text[:100]}...")
                    
                    print(f"{Fore.GREEN}✅ Backend processed successfully")
                    return True
                else:
                    print(f"{Fore.RED}❌ Backend error: {response.status_code}")
                    print(f"{Fore.RED}   {response.text}")
                    return False
        
        except httpx.TimeoutException:
            print(f"{Fore.RED}❌ Backend timeout (>{self.backend_timeout}s)")
            return False
        except Exception as e:
            print(f"{Fore.RED}❌ Error sending to backend: {e}")
            return False
    
    async def _confirm_action(self, user_response: str):
        """Send action confirmation to backend."""
        if not self.pending_action_id:
            return
        
        try:
            print(f"{Fore.MAGENTA}📋 Confirming action {self.pending_action_id}...")
            
            url = f"{self.backend_url}/action/confirm/{self.pending_action_id}"
            payload = {
                "response": user_response,
                "user_id": "voice_client_pc_001"  # Required by backend
            }
            
            async with httpx.AsyncClient(timeout=self.backend_timeout) as client:
                response = await client.post(url, json=payload)
                
                if response.status_code == 200:
                    result = response.json()
                    status = result.get('status', 'unknown')
                    
                    if status == 'confirmed':
                        print(f"{Fore.GREEN}✅ Action CONFIRMED and executing!")
                    elif status == 'canceled':
                        print(f"{Fore.RED}❌ Action CANCELED")
                    else:
                        print(f"{Fore.CYAN}ℹ️  Action status: {status}")
                    
                    # Clear pending action
                    self.pending_action_id = None
                else:
                    print(f"{Fore.RED}❌ Confirmation error: {response.status_code}")
                    
        except Exception as e:
            print(f"{Fore.RED}❌ Error confirming action: {e}")
    
    def start(self):
        """Start voice client."""
        print("=" * 70)
        print(f"{Fore.CYAN}{Style.BRIGHT}🎤 VOICE CLIENT - PHASE A (PUSH-TO-TALK)")
        print("=" * 70)
        print(f"\n{Fore.YELLOW}Controls:")
        print(f"  - Hold {Fore.GREEN}SPACE{Fore.YELLOW} to record")
        print(f"  - Release {Fore.GREEN}SPACE{Fore.YELLOW} to send")
        print(f"  - Press {Fore.RED}CTRL+C{Fore.YELLOW} to quit")
        print(f"\n{Fore.CYAN}Connecting to services...")
        
        # Connect MQTT player
        if not self.player.connect():
            print(f"{Fore.RED}❌ Failed to connect MQTT")
            return
        
        # Start audio stream
        print(f"{Fore.CYAN}🎤 Opening microphone...")
        try:
            self.stream = sd.InputStream(
                samplerate=self.recorder.sample_rate,
                channels=self.recorder.channels,
                callback=self.recorder.callback
            )
            self.stream.start()
            print(f"{Fore.GREEN}✅ Microphone ready")
        except Exception as e:
            print(f"{Fore.RED}❌ Failed to open microphone: {e}")
            return
        
        print(f"\n{Fore.GREEN}{Style.BRIGHT}✅ Voice client ready!")
        print(f"{Fore.CYAN}👂 Press and hold SPACE to talk...\n")
        
        # Register keyboard hooks
        keyboard.on_press_key("space", self._on_space_press)
        keyboard.on_release_key("space", self._on_space_release)
        
        self.is_running = True
        
        try:
            # Keep running
            while self.is_running:
                time.sleep(0.1)
        
        except KeyboardInterrupt:
            print(f"\n{Fore.YELLOW}👋 Shutting down...")
        
        finally:
            self._cleanup()
    
    def _on_space_press(self, event):
        """Callback: SPACE key pressed."""
        if not self.recorder.is_recording:
            self.recorder.start_recording()
    
    def _on_space_release(self, event):
        """Callback: SPACE key released."""
        if self.recorder.is_recording:
            # Stop recording
            audio_bytes = self.recorder.stop_recording()
            
            if audio_bytes:
                # Send to backend (async)
                asyncio.run(self.send_audio_to_backend(audio_bytes))
            
            print(f"{Fore.CYAN}👂 Ready (press SPACE to talk)")
    
    def _cleanup(self):
        """Cleanup resources."""
        # Unhook keyboard
        keyboard.unhook_all()
        
        # Stop audio stream
        if self.stream:
            self.stream.stop()
            self.stream.close()
        
        # Disconnect MQTT
        self.player.disconnect()
        
        print(f"{Fore.GREEN}✅ Voice client stopped")


def main():
    """Main entry point."""
    # Check if config exists
    config_path = Path("voice_client_config.yaml")
    if not config_path.exists():
        print(f"{Fore.RED}❌ Configuration file not found: {config_path}")
        print(f"{Fore.YELLOW}Create voice_client_config.yaml first!")
        sys.exit(1)
    
    # Create and start voice client
    client = VoiceClient(str(config_path))
    client.start()


if __name__ == "__main__":
    main()
