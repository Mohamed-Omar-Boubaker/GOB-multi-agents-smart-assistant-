# 🎯 Solution Wake Word Simple - FRONTEND ONLY

## 📋 Approche Simplifiée

**Principe:** Ajouter Picovoice pour mobile SANS toucher au backend

### Architecture

```
┌─────────────────────────────────────────────────────────┐
│               FRONTEND REACT UNIQUEMENT                  │
│                                                           │
│  ┌────────────────────────────────────────────────────┐ │
│  │         wakeWordService.ts (Modifié)               │ │
│  │                                                     │ │
│  │   if (isWeb) {                                     │ │
│  │     → Web Speech API (Google) ✅ DÉJÀ EN PLACE    │ │
│  │   }                                                 │ │
│  │   else if (isMobile) {                             │ │
│  │     → Picovoice Porcupine 🆕 À AJOUTER            │ │
│  │   }                                                 │ │
│  └────────────────────────────────────────────────────┘ │
│                                                           │
│  ┌──────────────────┐      ┌──────────────────────┐    │
│  │  Web Speech API  │      │  Picovoice Plugin    │    │
│  │  (Google Cloud)  │      │  (Natif Mobile)      │    │
│  │  ✅ Actuel       │      │  🆕 Nouveau          │    │
│  └──────────────────┘      └──────────────────────┘    │
└─────────────────────────────────────────────────────────┘

             ❌ PAS DE BACKEND REQUIS ❌
```

---

## 🎯 Avantages de cette approche

✅ **Simple** - Pas de backend à modifier
✅ **Rapide** - 1-2h d'implémentation seulement
✅ **Maintenable** - Peu de code à ajouter
✅ **Performant** - Picovoice natif ultra-rapide
✅ **Fonctionnel** - Web continue de marcher comme avant

---

## 📦 Ce qu'on doit faire

### ❌ PAS BESOIN de:
- ~~Créer wake_word_detector.py~~
- ~~Modifier backend/main.py~~
- ~~Ajouter routes FastAPI~~
- ~~Créer audioStreamService.ts~~
- ~~Créer whisperWakeWordService.ts~~

### ✅ SEULEMENT besoin de:
1. Installer plugin Picovoice
2. Créer picovoiceService.ts
3. Modifier wakeWordService.ts (switch web/mobile)
4. Configurer permissions mobile
5. Obtenir Access Key Picovoice
6. Créer wake words sur Picovoice Console

---

## 🚀 PHASE 1: Installation Plugin (10 min)

### 1.1 - Installer le plugin

```bash
cd pcd-ai-embedded-agent/agent-ui

# Installer le SDK OFFICIEL Picovoice Porcupine
npm install @picovoice/porcupine-capacitor

# Synchroniser avec projets natifs
npx cap sync
```

**Note:** 
- ✅ `@picovoice/porcupine-capacitor` = SDK Officiel Picovoice pour Capacitor
- ✅ Porcupine = Wake Word SEULEMENT (c'est exactement ce qu'on veut)
- ❌ Pas besoin de Rhino (compréhension d'intentions)
- ❌ Pas besoin de Leopard (transcription complète)
- ❌ Pas besoin de backend

---

## 🔧 PHASE 2: Configuration Permissions (5 min)

### 2.1 - Android

**Fichier:** `agent-ui/android/app/src/main/AndroidManifest.xml`

**Ajouter après `<manifest>`:**

```xml
<uses-permission android:name="android.permission.RECORD_AUDIO" />
<uses-permission android:name="android.permission.INTERNET" />
```

### 2.2 - iOS

**Fichier:** `agent-ui/ios/App/App/Info.plist`

**Ajouter dans `<dict>`:**

```xml
<key>NSMicrophoneUsageDescription</key>
<string>This app needs microphone access to listen for wake word commands</string>
```

---

## 💻 PHASE 3: Code Frontend (1h)

### 3.1 - Créer `agent-ui/src/services/picovoiceService.ts`

```typescript
/**
 * Picovoice Service - Wake Word natif mobile
 * Utilise SDK OFFICIEL @picovoice/porcupine-capacitor
 */

import { Porcupine } from '@picovoice/porcupine-capacitor';

export class PicovoiceService {
  private porcupine: Porcupine | null = null;
  private isListening: boolean = false;
  private onDetectedCallback: ((keyword: string) => void) | null = null;
  
  // 🔑 REMPLACER PAR VOTRE ACCESS KEY de console.picovoice.ai
  private readonly ACCESS_KEY = 'YOUR_PICOVOICE_ACCESS_KEY_HERE';
  
  // Wake words disponibles (utiliser built-in keywords ou custom .ppn)
  private readonly BUILT_IN_KEYWORDS = [
    'porcupine',
    'bumblebee',
    'alexa',
    'americano',
    'blueberry',
    'terminator',
    'picovoice'
  ];
  
  /**
   * Initialiser Picovoice
   */
  async initialize(): Promise<void> {
    try {
      console.log('[Picovoice] Initializing...');
      
      // Créer instance Porcupine avec built-in keywords
      this.porcupine = await Porcupine.fromBuiltInKeywords(
        this.ACCESS_KEY,
        ['porcupine', 'bumblebee'], // Utiliser built-in keywords
        [0.5, 0.5] // Sensibilités (0.0-1.0)
      );
      
      console.log('[Picovoice] ✅ Initialized successfully');
      
    } catch (error) {
      console.error('[Picovoice] ❌ Initialization failed:', error);
      throw error;
    }
  }
  
  /**
   * Démarrer l'écoute
   */
  async start(): Promise<void> {
    if (this.isListening || !this.porcupine) {
      console.log('[Picovoice] Already listening or not initialized');
      return;
    }
    
    try {
      // Démarrer et écouter les détections
      await this.porcupine.start(
        (keywordIndex: number) => {
          const detectedKeyword = ['porcupine', 'bumblebee'][keywordIndex];
          console.log('[Picovoice] 🔥 Wake word detected:', detectedKeyword);
          
          if (this.onDetectedCallback) {
            this.onDetectedCallback(detectedKeyword);
          }
        }
      );
      
      this.isListening = true;
      console.log('[Picovoice] 👂 Listening for wake words...');
      
    } catch (error) {
      console.error('[Picovoice] ❌ Failed to start:', error);
      throw error;
    }
  }
  
  /**
   * Arrêter l'écoute
   */
  async stop(): Promise<void> {
    if (!this.isListening || !this.porcupine) {
      return;
    }
    
    try {
      await this.porcupine.stop();
      this.isListening = false;
      console.log('[Picovoice] 🔇 Stopped listening');
      
    } catch (error) {
      console.error('[Picovoice] Failed to stop:', error);
    }
  }
  
  /**
   * Nettoyer ressources
   */
  async cleanup(): Promise<void> {
    await this.stop();
    
    try {
      if (this.porcupine) {
        await this.porcupine.delete();
        this.porcupine = null;
      }
      console.log('[Picovoice] 🧹 Cleaned up');
    } catch (error) {
      console.error('[Picovoice] Cleanup error:', error);
    }
  }
  
  /**
   * Définir callback
   */
  onDetection(callback: (keyword: string) => void): void {
    this.onDetectedCallback = callback;
  }
  
  /**
   * Statut
   */
  getIsListening(): boolean {
    return this.isListening;
  }
   (Built-in)
   */
  getAvailableWakeWords(): string[] {
    return [...this.BUILT_IN_KEYWORDS];
  }
  
  /**
   * Initialiser avec custom wake words (.ppn files)
   * Pour utiliser vos propres wake words créés sur console.picovoice.ai
   */
  async initializeWithCustomKeywords(
    modelPaths: string[],
    sensitivities?: number[]
  ): Promise<void> {
    try {
      console.log('[Picovoice] Initializing with custom keywords...');
      
      this.porcupine = await Porcupine.fromKeywordPaths(
        this.ACCESS_KEY,
        modelPaths, // Chemins vers fichiers .ppn custom
        sensitivities || modelPaths.map(() => 0.5)
      );
      
      console.log('[Picovoice] ✅ Custom keywords initialized');
      
    } catch (error) {
      console.error('[Picovoice] ❌ Custom keywords failed:', error);
      throw error;
    }
  getAvailableWakeWords(): string[] {
    return [...this.WAKE_WORDS];
  }
}

// Singleton
export const picovoiceService = new PicovoiceService();
```

---

### 3.2 - Modifier `agent-ui/src/services/wakeWordService.ts`

**Ajouter en haut du fichier:**

```typescript
import { picovoiceService } from './picovoiceService';
```

**Modifier la méthode `initializeSpeechRecognition()`:**

```typescript
/**
 * Détecte si on est sur mobile Capacitor
 */
private isCapacitor(): boolean {
  return typeof window !== 'undefined' && (window as any).Capacitor !== undefined;
}

private initializeSpeechRecognition(): void {
  // Si mobile Capacitor, on utilisera Picovoice à la place
  if (this.isCapacitor()) {
    console.log('[WakeWord] Mobile detected - Will use Picovoice');
    return;
  }
  
  // Reste du code existant pour Web Speech API...
  if (!('webkitSpeechRecognition' in window || 'SpeechRecognition' in window)) {
    console.warn('[WakeWord] Speech Recognition not supported');
    return;
  }
  
  // ... code existant ...
}
```

**Modifier la méthode `start()`:**

```typescript
async start(): Promise<void> {
  if (this.isActive) {
    console.log('[WakeWord] Already active');
    return;
  }
  
  this.isActive = true;
  
  // Mobile: Utiliser Picovoice
  if (this.isCapacitor()) {
    try {
      console.log('[WakeWord] Starting Picovoice...');
      
      // Initialiser Picovoice
      await picovoiceService.initialize();
      
      // Définir callback
      picovoiceService.onDetection((keyword: string) => {
        console.log('[WakeWord] Picovoice detected:', keyword);
        if (this.onWakeWordDetected) {
          this.onWakeWordDetected(keyword);
        }
      });
      
      // Démarrer écoute
      await picovoiceService.start();
      
      console.log('[WakeWord] ✅ Picovoice started');
      
    } catch (error) {
      console.error('[WakeWord] ❌ Picovoice failed:', error);
      this.isActive = false;
      throw error;
    }
    return;
  }
  
  // Web: Utiliser Web Speech API (code existant)
  if (!this.recognition) {
    throw new Error('Speech Recognition not supported');
  }
  
  if (!this.wakeWord) {
    throw new Error('Wake word not set');
  }
  
  return new Promise((resolve, reject) => {
    try {
      this.recognition!.start();
      console.log('[WakeWord] ✅ Web Speech API started');
      resolve();
    } catch (error) {
      this.isActive = false;
      console.error('[WakeWord] Start failed:', error);
      reject(error);
    }
  });
}
```

**Modifier la méthode `stop()`:**

```typescript
async stop(): Promise<void> {
  if (!this.isActive) return;
  
  this.isActive = false;
  
  // Mobile: Arrêter Picovoice
  if (this.isCapacitor()) {
    await picovoiceService.stop();
    console.log('[WakeWord] Picovoice stopped');
    return;
  }
  
  // Web: Arrêter Web Speech API (code existant)
  if (!this.recognition) return;
  
  try {
    this.recognition.stop();
    console.log('[WakeWord] Web Speech API stopped');
  } catch (e) {
    console.warn('[WakeWord] Stop error:', e);
  }
}
```

**Modifier la méthode `isSupported()`:**

```typescript
isSupported(): boolean {
  // Mobile: Picovoice toujours supporté
  if (this.isCapacitor()) {
    return true;
  }
  
  // Web: Web Speech API
  return this.recognition !== null;
}
```

---

## 🎮 PHASE 4: Configuration Picovoice Console (20 min)

### 4.1 - Créer compte (Gratuit)

1. Aller sur: https://console.picovoice.ai/
2. Cliquer "Sign Up"
3. Créer un compte (email + password)
4. Confirmer email
5. Se connecter

### 4.2 - Obtenir Access Key

1. Dans le dashboard, aller à **"Access Keys"**
2. Cliquer "Create new key" ou utiliser la clé par défaut
3. **Copier la clé** (format: `xxxxxxxxxxxxxxxxxxx...`)
4. La coller dans `picovoiceService.ts`:

```typescript
private readonly ACCESS_KEY = 'VOTRE_CLE_COPIEE_ICI';
```

⚠️ **Important:** Ne PAS commit la clé dans Git ! Utiliser `.env` si possible.

### 4.3 - Créer Wake Words personnalisés

**Option A: Utiliser wake words pré-intégrés** (Plus simple)
- Picovoice offre des wake words par défaut comme "porcupine", "bumblebee"
- Aucun téléchargement nécessaire
- Modifier dans `picovoiceService.ts`:

```typescript
private readonly WAKE_WORDS = [
  'porcupine',    // Wake word par défaut Picovoice
  'bumblebee',    // Wake word par défaut Picovoice
  'alexa'         // Autres disponibles
];
```

**Option B: Créer wake words custom** (Plus personnalisé)

1. Dans le dashboard, cliquer **"Porcupine Wake Word"**
2. Cliquer **"Train Custom Wake Word"**
3. Entrer le wake word (ex: "hey gob")
4. Choisir les plateformes:
   - ☑️ Android
   - ☑️ iOS
5. Cliquer **"Train"** (prend 1-2 minutes)
6. Télécharger les fichiers `.ppn` générés

### 4.4 - Ajouter modèles dans le projet (Si Option B)

**Pour Android:**

1. Copier `hey-gob_android.ppn` dans:
   ```
   agent-ui/android/app/src/main/assets/
   ```

2. Si le dossier `assets` n'existe pas, le créer

**Pour iOS:**

1. Copier `hey-gob_ios.ppn` dans:
   ```
   agent-ui/ios/App/App/Resources/
   ```

2. Dans Xcode:
   - Ouvrir le projet
   - Clic droit sur "App" folder
   - "Add Files to App"
   - Sélectionner les fichiers `.ppn`
   - Cocher "Copy items if needed"

---

## 🧪 PHASE 5: Tests (30 min)

### 5.1 - Test Web (Vérifier que rien n'est cassé)

```bash
cd pcd-ai-embedded-agent/agent-ui

# Mode dev
npm run dev

# Ouvrir http://localhost:5173
# Activer wake mode
# Dire le wake word
# Vérifier que ça marche toujours
```

### 5.2 - Test Mobile Android

```bash
# Build l'app
npm run build

# Sync avec Capacitor
npx cap sync android

# Ouvrir Android Studio
npx cap open android
```

**Dans Android Studio:**

1. Connecter téléphone via USB (mode développeur activé)
2. Cliquer **Run ▶️**
3. L'app s'installe sur le téléphone

**Sur le téléphone:**

1. Ouvrir l'app
2. Aller dans Settings
3. Entrer un wake word (ou choisir parmi les pré-définis)
4. Activer wake mode
5. Dire le wake word (ex: "porcupine", "hey gob")
6. **Vérifier que les yeux réagissent**
7. Parler une commande
8. Vérifier la réponse

### 5.3 - Debug Chrome Remote (Voir les logs)

1. Sur PC, ouvrir Chrome
2. Aller à: `chrome://inspect`
3. Trouver votre app dans la liste
4. Cliquer **"inspect"**
5. Voir les logs console en temps réel:
   ```
   [WakeWord] Mobile detected - Will use Picovoice
   [Picovoice] Initializing...
   [Picovoice] ✅ Initialipicovoice/porcupine-capacitor` (SDK Officiel)
   [Picovoice] 👂 Listening for wake words...
   [Picovoice] 🔥 Wake word detected: porcupine
   ```

---

## 📊 Comparaison Finale Simple

| Aspect | Web (Actuel) | Mobile (Nouveau) |
|--------|--------------|------------------|
| **Moteur** | Web Speech API | Picovoice |
| **Modifications** | ❌ Aucune | ✅ Minimales |
| **Backend** | ❌ Non requis | ❌ Non requis |
| **Performance** | ⚡ Instantané | ⚡ < 200ms |
| **Batterie** | N/A | 🔋 < 2%/h |
| **Wake Words** | ✅ Custom | ⚠️ Pré-définis ou custom |
| **Coût** | 🆓 Gratuit | 💰 100K/mois gratuit |

---

## 📋 Checklist Finale

### Backend
- [ ] ❌ **AUCUNE MODIFICATION** (on ne touche pas!)

### Frontend
- [ ] Installer plugin `@capacitor-community/porcupine-wake-word`
- [ ] Créer `picovoiceService.ts`
- [ ] Modifier `wakeWordService.ts` (3 méthodes)
- [ ] Configurer permissions Android/iOS

### Configuration
- [ ] Créer compte Picovoice
- [ ] Obtenir Access Key
- [ ] Ajouter la clé dans `picovoiceService.ts`
- [ ] Choisir wake words (pré-définis ou custom)
- [ ] Si custom: télécharger et ajouter fichiers `.ppn`

### Tests
- [ ] Test web (vérifier que rien n'est cassé)
- [ ] Build mobile
- [ ] Test sur téléphone
- [ ] Vérifier détection wake word
- [ ] Vérifier commandes fonctionnent

---

## ⏱️ Temps Estimé Total: **1-2 heures**

| Étape | Temps |
|-------|-------|
| Installation plugin | 10 min |
| Permissions mobile | 5 min |
| Code frontend | 1h |
| Configuration Picovoice | 20 min |
| Tests | 30 min |

---

## 💡 Pourquoi cette solution est PARFAITE

✅ **Simple** - Pas de backend, modifications minimales
✅ **Rapide** - 1-2h d'implémentation
✅ **Performant** - Picovoice ultra-optimisé pour mobile
✅ **Maintenable** - Code propre, peu de dépendances
✅ **Fonctionnel** - Web continue de marcher parfaitement
✅ **Gratuit** - 100K détections/mois (largement suffisant)

---

## 🚀 Prochaine Étape

**Tu es prêt à commencer ?**

Je peux:
1. **Créer `picovoiceService.ts`** maintenant
2. **Modifier `wakeWordService.ts`** maintenant
3. **T'expliquer plus en détail** une étape spécifique

**Qu'est-ce que tu veux faire en premier ?** 💪
