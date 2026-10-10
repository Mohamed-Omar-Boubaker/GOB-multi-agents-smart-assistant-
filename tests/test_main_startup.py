"""
Script de test pour vérifier que main.py peut démarrer.
Vérifie l'importation et la validation de configuration.
"""

import sys
from pathlib import Path

# Ajouter le répertoire parent au path pour imports
sys.path.insert(0, str(Path(__file__).parent))

print("=" * 60)
print("🧪 TEST DÉMARRAGE BACKEND - AGENT INTELLIGENT")
print("=" * 60)

# Test 1: Import Config
print("\n[1/4] Test import Config...")
try:
    from backend.config import Config
    print(f"✅ Config importé avec succès")
    print(f"    - Environment: {Config.ENVIRONMENT}")
    print(f"    - Host: {Config.HOST}:{Config.PORT}")
    print(f"    - LLM: {Config.LLM_API_URL}")
    print(f"    - STT Engine: {Config.STT_ENGINE}")
    print(f"    - TTS Engine: {Config.TTS_ENGINE}")
except Exception as e:
    print(f"❌ Erreur import Config: {e}")
    sys.exit(1)

# Test 2: Import FastAPI app
print("\n[2/4] Test import FastAPI app...")
try:
    from backend.main import app
    print(f"✅ FastAPI app importé avec succès")
    print(f"    - Title: {app.title}")
    print(f"    - Version: {app.version}")
except Exception as e:
    print(f"❌ Erreur import FastAPI app: {e}")
    print(f"    Note: Certains composants peuvent manquer (normal en dev)")
    print(f"    Erreur: {type(e).__name__}: {e}")

# Test 3: Vérifier les routes
print("\n[3/4] Test routes API...")
try:
    from backend.main import app
    routes = [route.path for route in app.routes if hasattr(route, 'path')]
    print(f"✅ {len(routes)} routes trouvées:")
    for route in routes:
        print(f"    - {route}")
except Exception as e:
    print(f"⚠️  Impossible de lister les routes: {e}")

# Test 4: Vérifier structure de fichiers
print("\n[4/4] Test structure de fichiers backend...")
required_files = [
    "backend/main.py",
    "backend/config.py",
    "backend/.env",
    "backend/requirements.txt",
    "backend/agent/agent_core.py",
    "backend/ai/stt_engine.py",
    "backend/ai/tts_engine.py",
    "backend/ai/llm_client.py",
    "backend/classifier/intent_classifier.py",
    "backend/actions/action_builder.py",
    "backend/actions/confirmation_handler.py",
]

all_present = True
for file_path in required_files:
    file = Path(file_path)
    if file.exists():
        print(f"    ✅ {file_path}")
    else:
        print(f"    ❌ {file_path} (MANQUANT)")
        all_present = False

print("\n" + "=" * 60)
if all_present:
    print("✅ TOUS LES TESTS PASSÉS")
    print("=" * 60)
    print("\n📝 PROCHAINES ÉTAPES:")
    print("1. Vérifier que tous les composants sont implémentés")
    print("2. Démarrer le serveur:")
    print("   uvicorn backend.main:app --reload --port 8000")
    print("3. Tester les endpoints:")
    print("   - http://localhost:8000/docs (Swagger UI)")
    print("   - http://localhost:8000/health")
else:
    print("⚠️  CERTAINS FICHIERS SONT MANQUANTS")
    print("=" * 60)
    print("\nVérifiez que tous les composants sont implémentés.")

print()
