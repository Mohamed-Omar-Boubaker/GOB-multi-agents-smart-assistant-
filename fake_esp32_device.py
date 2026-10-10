"""
Fake ESP32 Device - Simulation pour tests sans matériel
=========================================================

Simule un ESP32 qui:
1. Se connecte au broker MQTT
2. Écoute le topic device/audio
3. Reçoit l'audio en base64
4. Décode et joue l'audio sur PC (haut-parleurs)
5. Publie son status sur device/status

Usage:
    python fake_esp32_device.py

Prérequis:
    - mosquitto broker running (mosquitto -v)
    - pip install paho-mqtt pygame

Architecture:
    Backend → MQTT (device/audio) → Fake ESP32 → PC speakers
"""

import base64
import io
import json
import time
import wave
from datetime import datetime
from pathlib import Path

import paho.mqtt.client as mqtt
import pygame


class FakeESP32Device:
    """
    Simulation d'un ESP32 qui reçoit et joue de l'audio via MQTT.
    """
    
    def __init__(
        self,
        device_id: str = "fake_esp32_001",
        mqtt_broker: str = "localhost",
        mqtt_port: int = 1883,
        audio_topic: str = "device/audio",
        status_topic: str = "device/status",
        save_audio: bool = False
    ):
        """
        Initialiser le fake device.
        
        Args:
            device_id: Identifiant unique du device
            mqtt_broker: Adresse du broker MQTT
            mqtt_port: Port du broker MQTT
            audio_topic: Topic pour recevoir l'audio
            status_topic: Topic pour publier le status
            save_audio: Sauvegarder l'audio reçu dans audio_received/
        """
        self.device_id = device_id
        self.mqtt_broker = mqtt_broker
        self.mqtt_port = mqtt_port
        self.audio_topic = audio_topic
        self.status_topic = status_topic
        self.save_audio = save_audio
        
        # Créer dossier pour sauvegarder audio (optionnel)
        if self.save_audio:
            self.audio_dir = Path("audio_received")
            self.audio_dir.mkdir(exist_ok=True)
        
        # Initialiser pygame mixer pour jouer l'audio
        pygame.mixer.init(frequency=22050, size=-16, channels=1, buffer=512)
        
        # Initialiser MQTT client
        self.client = mqtt.Client(client_id=device_id)
        self.client.on_connect = self._on_connect
        self.client.on_message = self._on_message
        self.client.on_disconnect = self._on_disconnect
        
        self.connected = False
        self.audio_count = 0
    
    def _on_connect(self, client, userdata, flags, rc):
        """Callback: Connexion au broker établie."""
        if rc == 0:
            self.connected = True
            print(f"✅ [{self.device_id}] Connecté au broker MQTT")
            print(f"   Broker: {self.mqtt_broker}:{self.mqtt_port}")
            
            # S'abonner au topic audio
            client.subscribe(self.audio_topic, qos=1)
            print(f"👂 [{self.device_id}] Écoute du topic: {self.audio_topic}")
            
            # Publier status: online
            self._publish_status("online", "Device ready to receive audio")
        else:
            print(f"❌ [{self.device_id}] Erreur connexion: code {rc}")
    
    def _on_disconnect(self, client, userdata, rc):
        """Callback: Déconnexion du broker."""
        self.connected = False
        if rc == 0:
            print(f"👋 [{self.device_id}] Déconnecté du broker (normal)")
        else:
            print(f"⚠️  [{self.device_id}] Déconnecté du broker (code: {rc})")
    
    def _on_message(self, client, userdata, msg):
        """Callback: Message reçu sur topic audio."""
        try:
            print(f"\n🎵 [{self.device_id}] Audio reçu sur {msg.topic}")
            
            # Publier status: receiving
            self._publish_status("receiving", "Audio message received")
            
            # Décoder base64 → bytes
            audio_base64 = msg.payload.decode('utf-8')
            audio_bytes = base64.b64decode(audio_base64)
            
            print(f"   Taille: {len(audio_bytes)} bytes")
            
            # Sauvegarder audio (optionnel)
            if self.save_audio:
                self.audio_count += 1
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                filename = self.audio_dir / f"audio_{timestamp}_{self.audio_count}.wav"
                filename.write_bytes(audio_bytes)
                print(f"   💾 Sauvegardé: {filename}")
            
            # Jouer l'audio
            self._play_audio(audio_bytes)
            
            # Publier status: completed
            self._publish_status("completed", f"Audio played successfully (count: {self.audio_count})")
            
        except Exception as e:
            print(f"❌ [{self.device_id}] Erreur traitement audio: {e}")
            self._publish_status("error", f"Audio playback failed: {str(e)}")
    
    def _play_audio(self, audio_bytes: bytes):
        """
        Jouer l'audio sur les haut-parleurs du PC.
        
        Args:
            audio_bytes: Audio WAV en bytes
        """
        try:
            # Publier status: playing
            self._publish_status("playing", "Playing audio on speakers")
            
            # Créer un buffer en mémoire pour l'audio
            audio_buffer = io.BytesIO(audio_bytes)
            
            # Charger l'audio dans pygame
            pygame.mixer.music.load(audio_buffer)
            
            # Jouer l'audio
            pygame.mixer.music.play()
            
            print(f"🔊 [{self.device_id}] Lecture audio en cours...")
            
            # Attendre la fin de la lecture
            while pygame.mixer.music.get_busy():
                time.sleep(0.1)
            
            print(f"✅ [{self.device_id}] Lecture terminée")
            
        except Exception as e:
            print(f"❌ [{self.device_id}] Erreur lecture audio: {e}")
            raise
    
    def _publish_status(self, status: str, message: str):
        """
        Publier le status du device sur MQTT.
        
        Args:
            status: Status du device (online, receiving, playing, completed, error)
            message: Message descriptif
        """
        if not self.connected:
            return
        
        try:
            status_data = {
                "device_id": self.device_id,
                "status": status,
                "message": message,
                "timestamp": datetime.now().isoformat()
            }
            
            status_json = json.dumps(status_data)
            self.client.publish(self.status_topic, status_json, qos=1)
            
            print(f"📱 [{self.device_id}] Status: {status} - {message}")
            
        except Exception as e:
            print(f"⚠️  [{self.device_id}] Erreur publish status: {e}")
    
    def start(self):
        """Démarrer le device (connexion MQTT et boucle d'écoute)."""
        try:
            print("=" * 70)
            print(f"🚀 FAKE ESP32 DEVICE - {self.device_id}")
            print("=" * 70)
            print(f"   MQTT Broker: {self.mqtt_broker}:{self.mqtt_port}")
            print(f"   Topic Audio: {self.audio_topic}")
            print(f"   Topic Status: {self.status_topic}")
            print(f"   Save Audio: {self.save_audio}")
            print("=" * 70)
            print("\n⏳ Connexion au broker MQTT...")
            
            # Connexion au broker
            self.client.connect(self.mqtt_broker, self.mqtt_port, keepalive=60)
            
            # Boucle d'écoute (bloquante)
            print("\n👂 En écoute des messages audio...")
            print("   (Ctrl+C pour arrêter)\n")
            
            self.client.loop_forever()
            
        except KeyboardInterrupt:
            print(f"\n\n👋 [{self.device_id}] Arrêt demandé par l'utilisateur")
            self.stop()
        except Exception as e:
            print(f"\n❌ [{self.device_id}] Erreur: {e}")
            self.stop()
    
    def stop(self):
        """Arrêter le device proprement."""
        try:
            # Publier status: offline
            if self.connected:
                self._publish_status("offline", "Device shutting down")
            
            # Déconnexion MQTT
            self.client.loop_stop()
            self.client.disconnect()
            
            # Cleanup pygame
            pygame.mixer.quit()
            
            print(f"✅ [{self.device_id}] Device arrêté proprement")
            
        except Exception as e:
            print(f"⚠️  [{self.device_id}] Erreur arrêt: {e}")


def main():
    """Point d'entrée principal."""
    import argparse
    
    parser = argparse.ArgumentParser(
        description="Fake ESP32 Device - Simulation pour tests MQTT audio"
    )
    parser.add_argument(
        "--device-id",
        default="fake_esp32_001",
        help="Identifiant unique du device (default: fake_esp32_001)"
    )
    parser.add_argument(
        "--broker",
        default="localhost",
        help="Adresse du broker MQTT (default: localhost)"
    )
    parser.add_argument(
        "--port",
        type=int,
        default=1883,
        help="Port du broker MQTT (default: 1883)"
    )
    parser.add_argument(
        "--audio-topic",
        default="device/audio",
        help="Topic pour recevoir l'audio (default: device/audio)"
    )
    parser.add_argument(
        "--status-topic",
        default="device/status",
        help="Topic pour publier le status (default: device/status)"
    )
    parser.add_argument(
        "--save-audio",
        action="store_true",
        help="Sauvegarder l'audio reçu dans audio_received/"
    )
    
    args = parser.parse_args()
    
    # Créer et démarrer le device
    device = FakeESP32Device(
        device_id=args.device_id,
        mqtt_broker=args.broker,
        mqtt_port=args.port,
        audio_topic=args.audio_topic,
        status_topic=args.status_topic,
        save_audio=args.save_audio
    )
    
    device.start()


if __name__ == "__main__":
    main()
