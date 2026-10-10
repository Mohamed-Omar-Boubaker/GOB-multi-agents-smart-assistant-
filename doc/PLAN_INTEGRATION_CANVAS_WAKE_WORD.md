# 📋 Plan d'Intégration Canvas Eyes + Wake Word Detection

## 🎯 Objectif Global

Intégrer le système **Canvas Eyes Animation** + **Wake Word Detection** depuis les fichiers de test HTML dans l'application React/Vite existante, en remplaçant le système Lottie actuel.

---

## 📊 État Actuel vs État Cible

### ✅ Ce qui existe actuellement (React/Vite):
- Application React avec Vite
- Avatar component utilisant Lottie animations
- MicButton component (Push-to-Talk)
- State management avec Zustand
- Backend integration (FastAPI Python)
- États : idle, listening, thinking, speaking, confirmation, execution, success, error

### 🎨 Ce qui existe dans les tests HTML:
- Canvas avec animation d'yeux (eyes rendering engine)
- États visuels : idle, sleep, listening, thinking, speaking, happy, error
- Wake word detection (Web Speech API)
- Push-to-talk functionality
- Smooth animations avec lerp, blink, expressions faciales
- Mouse/touch tracking pour suivre le regard

### 🚀 Ce qu'on veut accomplir:
- **Remplacer** Lottie Avatar par Canvas Eyes
- **Ajouter** Wake Word Mode (détection locale)
- **Garder** Push To Talk Mode (manuel)
- **Double mode** : L'utilisateur choisit entre Push To Talk ou Wake Word
- **Synchronisation** : Canvas states ↔ Backend states
- **États simplifiés visibles** : Sleep, Listening, Thinking, Speaking
- **Wake word personnalisable** : L'utilisateur peut définir son propre mot-clé

---

## 🏗️ Architecture Technique

### Structure des fichiers à créer/modifier:

```
agent-ui/src/
├── components/
│   ├── CanvasEyes/                    [NOUVEAU]
│   │   ├── CanvasEyes.tsx            # Composant principal Canvas
│   │   ├── CanvasEyes.css            # Styles du canvas
│   │   ├── eyesEngine.ts              # Logique rendering (états, lerp, blink)
│   │   └── eyesConfig.ts              # Configuration des états visuels
│   │
│   ├── WakeWordPanel/                 [NOUVEAU]
│   │   ├── WakeWordPanel.tsx         # UI pour configure wake word
│   │   └── WakeWordPanel.css
│   │
│   ├── Avatar/
│   │   └── Avatar.tsx                 [MODIFIER - décider garder ou remplacer]
│   │
│   └── MicButton/
│       └── MicButton.tsx              [MODIFIER - ajouter logique wake word]
│
├── services/
│   ├── wakeWordService.ts             [NOUVEAU - Web Speech API]
│   └── audio.ts                       [MODIFIER - intégrer wake word]
│
├── store/
│   └── agentStore.ts                  [MODIFIER - ajouter wake word state]
│
├── types/
│   └── index.ts                       [MODIFIER - ajouter types wake word]
│
└── screens/
    └── AgentScreen/
        └── AgentScreen.tsx            [MODIFIER - intégrer canvas + wake panel]
```

---

## 📝 Plan Détaillé Step-by-Step

### **Phase 1: Extraction et Préparation du Code Canvas** 

#### Step 1.1: Créer le Eyes Engine Module
**Fichier**: `agent-ui/src/components/CanvasEyes/eyesEngine.ts`

**Contenu à extraire du test HTML**:
- Canvas setup et resize logic
- STATES configuration (idle, sleep, listening, thinking, speaking, happy, error)
- Lerp functions (smooth transitions)
- Blink system
- Mouse/touch tracking
- Auto pupil movement (Lissajous curves)
- Face rendering functions

**Adaptations nécessaires**:
- ❌ Retirer : `document.getElementById()` (direct DOM access)
- ✅ Utiliser : Canvas refs de React
- ❌ Retirer : Global variables
- ✅ Utiliser : Class ou closure patterns
- ❌ Retirer : `requestAnimationFrame` global
- ✅ Utiliser : React useEffect cleanup

**Structure proposée**:
```typescript
// eyesEngine.ts
export interface EyesState {
  pupilScale: number;
  irisRGB: [number, number, number];
  irisEdgeRGB: [number, number, number];
  irisGlow: number;
  browAngle: number;
  browLift: number;
  lidClose: number;
  followStr: number;
  pupilShiftY: number;
  mouthW: number;
  mouthCurve: number;
  mouthOpen: number;
  mouthH: number;
  mouthWobble: number;
  motY: number;
  motX: number;
  motSpeed: number;
  motTilt: number;
  blinkEvery: number;
  blinkDur: number;
  distortAmp: number;
  distortFreq: number;
  distortSpeed: number;
}

export type EyesStateName = 'idle' | 'sleep' | 'listening' | 'thinking' | 'speaking' | 'happy' | 'error';

export class EyesEngine {
  private canvas: HTMLCanvasElement;
  private ctx: CanvasRenderingContext2D;
  private offCanvas: HTMLCanvasElement;
  private octx: CanvasRenderingContext2D;
  private currentState: EyesStateName = 'idle';
  private animationFrameId: number | null = null;
  
  constructor(canvas: HTMLCanvasElement, offCanvas: HTMLCanvasElement) {
    // ... initialization
  }
  
  setState(name: EyesStateName): void {
    // ... change state logic
  }
  
  start(): void {
    // ... start animation loop
  }
  
  stop(): void {
    // ... cleanup
  }
  
  setMousePosition(x: number, y: number): void {
    // ... update cursor tracking
  }
  
  private render(): void {
    // ... main render loop
  }
}
```

---

#### Step 1.2: Créer le Composant CanvasEyes React
**Fichier**: `agent-ui/src/components/CanvasEyes/CanvasEyes.tsx`

**Responsabilités**:
- Créer les canvas elements (main + offscreen)
- Initialiser EyesEngine
- Synchroniser avec agentStore state
- Gérer le cycle de vie (mount/unmount)
- Écouter les changements d'état global

**Code structure**:
```tsx
import { useEffect, useRef } from 'react';
import { useAgentStore } from '../../store/agentStore';
import { EyesEngine } from './eyesEngine';
import './CanvasEyes.css';

export function CanvasEyes() {
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const offscreenRef = useRef<HTMLCanvasElement>(null);
  const engineRef = useRef<EyesEngine | null>(null);
  
  const state = useAgentStore((s) => s.state);
  const wakeMode = useAgentStore((s) => s.wakeMode);
  
  // Initialize engine
  useEffect(() => {
    if (!canvasRef.current || !offscreenRef.current) return;
    
    engineRef.current = new EyesEngine(
      canvasRef.current,
      offscreenRef.current
    );
    
    engineRef.current.start();
    
    return () => {
      engineRef.current?.stop();
    };
  }, []);
  
  // Sync state with engine
  useEffect(() => {
    if (!engineRef.current) return;
    
    // Map React state to Canvas state
    const canvasState = mapStateToCanvasState(state, wakeMode);
    engineRef.current.setState(canvasState);
  }, [state, wakeMode]);
  
  // Mouse tracking
  useEffect(() => {
    const handleMouseMove = (e: MouseEvent) => {
      if (!engineRef.current || !canvasRef.current) return;
      const rect = canvasRef.current.getBoundingClientRect();
      const x = (e.clientX - rect.left) / rect.width;
      const y = (e.clientY - rect.top) / rect.height;
      engineRef.current.setMousePosition(x, y);
    };
    
    window.addEventListener('mousemove', handleMouseMove);
    return () => window.removeEventListener('mousemove', handleMouseMove);
  }, []);
  
  return (
    <div className="canvas-eyes-container">
      <canvas ref={canvasRef} className="canvas-eyes" />
      <canvas ref={offscreenRef} className="canvas-offscreen" />
    </div>
  );
}

// Helper function to map states
function mapStateToCanvasState(
  reactState: string,
  wakeMode: boolean
): EyesStateName {
  // Si wake mode est activé mais idle → sleep
  if (wakeMode && reactState === 'idle') return 'sleep';
  
  // Mapping direct des états
  const stateMap: Record<string, EyesStateName> = {
    'idle': 'idle',
    'listening': 'listening',
    'thinking': 'thinking',
    'speaking': 'speaking',
    'confirmation': 'thinking', // map to thinking
    'execution': 'thinking',    // map to thinking
    'success': 'happy',
    'error': 'error'
  };
  
  return stateMap[reactState] || 'idle';
}
```

---

#### Step 1.3: Styles CSS pour Canvas
**Fichier**: `agent-ui/src/components/CanvasEyes/CanvasEyes.css`

```css
.canvas-eyes-container {
  position: relative;
  width: 100%;
  height: 100%;
  display: flex;
  align-items: center;
  justify-content: center;
}

.canvas-eyes {
  position: absolute;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  z-index: 1;
}

.canvas-offscreen {
  display: none;
}
```

---

### **Phase 2: Wake Word Service**

#### Step 2.1: Créer le Wake Word Service
**Fichier**: `agent-ui/src/services/wakeWordService.ts`

**Responsabilités**:
- Initialiser Web Speech API
- Démarrer/arrêter la reconnaissance continue
- Détecter le wake word configuré
- Gérer les erreurs (permission, browser support)
- Émettre des événements quand le wake word est détecté

**Code structure**:
```typescript
type WakeWordCallback = (transcript: string) => void;
type ErrorCallback = (error: string) => void;

export class WakeWordService {
  private recognition: SpeechRecognition | null = null;
  private wakeWord: string = '';
  private isActive: boolean = false;
  private onWakeWordDetected: WakeWordCallback | null = null;
  private onError: ErrorCallback | null = null;
  
  constructor() {
    this.initializeSpeechRecognition();
  }
  
  private initializeSpeechRecognition(): void {
    if (!('webkitSpeechRecognition' in window || 'SpeechRecognition' in window)) {
      console.warn('Speech Recognition not supported');
      return;
    }
    
    const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
    this.recognition = new SpeechRecognition();
    this.recognition.continuous = true;
    this.recognition.interimResults = false;
    this.recognition.lang = 'en-US';
    
    this.recognition.onresult = (event) => {
      // ... detection logic
    };
    
    this.recognition.onerror = (event) => {
      // ... error handling
    };
    
    this.recognition.onend = () => {
      // Auto-restart if still active
      if (this.isActive) {
        try {
          this.recognition?.start();
        } catch (e) {
          console.error('Failed to restart recognition:', e);
        }
      }
    };
  }
  
  setWakeWord(word: string): void {
    this.wakeWord = this.normalize(word);
  }
  
  start(): Promise<void> {
    // ... start recognition
  }
  
  stop(): void {
    // ... stop recognition
  }
  
  onDetection(callback: WakeWordCallback): void {
    this.onWakeWordDetected = callback;
  }
  
  onErrorEvent(callback: ErrorCallback): void {
    this.onError = callback;
  }
  
  private normalize(text: string): string {
    return text.toLowerCase().replace(/[^a-z0-9]/g, '').trim();
  }
  
  isSupported(): boolean {
    return this.recognition !== null;
  }
}

export const wakeWordService = new WakeWordService();
```

---

### **Phase 3: UI pour Wake Word Configuration**

#### Step 3.1: Créer WakeWordPanel Component
**Fichier**: `agent-ui/src/components/WakeWordPanel/WakeWordPanel.tsx`

**UI Elements**:
- Input pour définir le wake word
- Button "Save" pour sauvegarder
- Toggle button "Wake Mode ON/OFF"
- Status indicator (wake word actuel)

**Code structure**:
```tsx
import { useState } from 'react';
import { useAgentStore } from '../../store/agentStore';
import './WakeWordPanel.css';

export function WakeWordPanel() {
  const [inputValue, setInputValue] = useState('');
  const { wakeWord, wakeMode, setWakeWord, toggleWakeMode } = useAgentStore();
  
  const handleSave = () => {
    if (!inputValue.trim()) return;
    setWakeWord(inputValue.trim());
    setInputValue('');
  };
  
  return (
    <div className="wake-word-panel">
      <div className="wake-word-input-group">
        <input
          type="text"
          placeholder="Wake word..."
          value={inputValue}
          onChange={(e) => setInputValue(e.target.value)}
          className="wake-word-input"
        />
        <button onClick={handleSave} className="wake-btn">
          Save
        </button>
        <button 
          onClick={toggleWakeMode} 
          className={`wake-btn ${wakeMode ? 'active' : ''}`}
          disabled={!wakeWord}
        >
          Wake {wakeMode ? 'ON' : 'OFF'}
        </button>
      </div>
      
      <div className={`wake-status ${wakeMode ? 'active' : ''}`}>
        {wakeWord ? `Wake word: ${wakeWord.toUpperCase()}` : 'No wake word set'}
      </div>
    </div>
  );
}
```

---

### **Phase 4: Intégration dans le Store (State Management)**

#### Step 4.1: Modifier agentStore.ts
**Fichier**: `agent-ui/src/store/agentStore.ts`

**Ajouts nécessaires**:
```typescript
interface AgentStore {
  // ... existing fields
  
  // NOUVEAUX champs pour wake word
  wakeMode: boolean;           // Wake mode activé ou non
  wakeWord: string;            // Wake word configuré
  
  // NOUVELLES actions
  setWakeWord: (word: string) => void;
  toggleWakeMode: () => void;
  enableWakeMode: () => void;
  disableWakeMode: () => void;
}

export const useAgentStore = create<AgentStore>((set) => ({
  // ... existing state
  
  wakeMode: false,
  wakeWord: '',
  
  // ... existing actions
  
  setWakeWord: (word) => set({ wakeWord: word }),
  
  toggleWakeMode: () => set((state) => ({ 
    wakeMode: !state.wakeMode 
  })),
  
  enableWakeMode: () => set({ wakeMode: true }),
  
  disableWakeMode: () => set({ wakeMode: false }),
}));
```

---

### **Phase 5: Intégration Logique Wake Word + Push To Talk**

#### Step 5.1: Modifier MicButton
**Fichier**: `agent-ui/src/components/MicButton/MicButton.tsx`

**Changements**:
- Gérer le wake word detection
- Ne pas afficher le bouton en mode Wake (ou le griser)
- Ajouter la logique d'activation automatique

**Structure modifiée**:
```tsx
export function MicButton() {
  const { 
    state, 
    wakeMode, 
    wakeWord,
    setState, 
    showToast,
    disableWakeMode
  } = useAgentStore();
  
  // Initialiser wake word service
  useEffect(() => {
    wakeWordService.onDetection((transcript) => {
      console.log('[Wake] Detected:', transcript);
      showToast(`Wake word detected: "${transcript}"`, 'success');
      
      // Activer listening mode
      setState('listening');
      
      // TODO: Start real audio capture after wake word
      // ... (similaire à handleMouseDown mais automatique)
    });
    
    wakeWordService.onErrorEvent((error) => {
      showToast(`Wake word error: ${error}`, 'error');
      disableWakeMode();
    });
  }, []);
  
  // Start/stop wake word service based on wakeMode
  useEffect(() => {
    if (wakeMode && wakeWord) {
      wakeWordService.setWakeWord(wakeWord);
      wakeWordService.start()
        .then(() => {
          showToast('Wake word listening started', 'success');
        })
        .catch((error) => {
          showToast(`Failed to start wake word: ${error}`, 'error');
          disableWakeMode();
        });
    } else {
      wakeWordService.stop();
    }
    
    return () => {
      wakeWordService.stop();
    };
  }, [wakeMode, wakeWord]);
  
  // Push to talk functionality (existing logic)
  const handleMouseDown = async () => {
    // Ne pas permettre push to talk si wake mode est actif
    if (wakeMode) {
      showToast('Wake mode active. Disable it to use Push To Talk', 'warning');
      return;
    }
    
    // ... existing push to talk logic
  };
  
  const handleMouseUp = async () => {
    // ... existing logic
  };
  
  return (
    <button
      className={`mic-button ${wakeMode ? 'disabled' : ''}`}
      onMouseDown={handleMouseDown}
      onMouseUp={handleMouseUp}
      onMouseLeave={handleMouseUp}
      disabled={wakeMode}
    >
      {wakeMode ? '🌙' : '🎤'}
    </button>
  );
}
```

---

### **Phase 6: Intégration dans AgentScreen**

#### Step 6.1: Modifier AgentScreen.tsx
**Fichier**: `agent-ui/src/screens/AgentScreen/AgentScreen.tsx`

**Changements**:
- Remplacer `<Avatar />` par `<CanvasEyes />`
- Ajouter `<WakeWordPanel />`
- Ajuster le layout

**Structure modifiée**:
```tsx
import { CanvasEyes } from '../../components/CanvasEyes/CanvasEyes';
import { WakeWordPanel } from '../../components/WakeWordPanel/WakeWordPanel';

export function AgentScreen() {
  // ... existing code
  
  return (
    <div className="agent-screen">
      <SettingsPanel />
      
      <header>
        <h1>GOB Agent</h1>
        <span>State: {state}</span>
      </header>
      
      {/* Wake Word Configuration */}
      <WakeWordPanel />
      
      {/* Warnings */}
      {/* ... existing warnings ... */}
      
      {/* Canvas Eyes Animation (remplace Avatar) */}
      <div className="avatar-section">
        <CanvasEyes />
      </div>
      
      {/* Rest of the UI */}
      <Waveform />
      <MicButton />
      
      {/* ... existing code ... */}
    </div>
  );
}
```

---

## 🎭 Mapping des États

### États React ↔ États Canvas

| React State     | Canvas State | Description                           |
|-----------------|--------------|---------------------------------------|
| `idle`          | `idle`       | Standby (si wake mode OFF)            |
| `idle`          | `sleep`      | Dormant (si wake mode ON)             |
| `listening`     | `listening`  | En écoute                             |
| `thinking`      | `thinking`   | Traitement backend                    |
| `speaking`      | `speaking`   | Réponse audio                         |
| `confirmation`  | `thinking`   | Attente confirmation → thinking       |
| `execution`     | `thinking`   | Exécution action → thinking           |
| `success`       | `happy`      | Action réussie                        |
| `error`         | `error`      | Erreur                                |

---

## 🔄 Workflow Utilisateur Complet

### Scénario 1: Push To Talk (Mode Manuel)

```
1. Utilisateur ouvre l'app
   → État: idle
   → Canvas: yeux idle (regard naturel)
   
2. Utilisateur appuie sur bouton mic 🎤
   → État: listening
   → Canvas: yeux listening (attentifs)
   → Audio capture START
   
3. Utilisateur parle puis relâche le bouton
   → État: thinking
   → Canvas: yeux thinking (réflexion)
   → Audio envoyé au backend
   
4. Backend répond
   → État: speaking
   → Canvas: yeux speaking (communication)
   → Audio playback
   
5. Fin de la réponse
   → État: idle
   → Canvas: yeux idle
```

### Scénario 2: Wake Word (Mode Automatique)

```
1. Utilisateur configure wake word "hi gob"
   → Input: "hi gob"
   → Click: Save
   → Wake word sauvegardé
   
2. Utilisateur active Wake Mode
   → Click: "Wake ON"
   → État: idle → sleep (automatique)
   → Canvas: yeux sleep (paupières semi-fermées)
   → Microphone écoute localement (pas de backend)
   
3. Utilisateur dit "hi gob"
   → Wake word détecté localement
   → État: listening
   → Canvas: yeux listening (s'ouvrent immédiatement)
   → Audio capture START
   
4. Utilisateur continue à parler
   → Audio capturé pendant 5 secondes max
   
5. Silence détecté OU timeout
   → État: thinking
   → Canvas: yeux thinking
   → Audio envoyé au backend
   
6. Backend répond
   → État: speaking
   → Canvas: yeux speaking
   → Audio playback
   
7. Fin de la réponse
   → État: idle → sleep (automatique car wake mode ON)
   → Canvas: yeux sleep (retour en veille)
   → Microphone re-écoute le wake word
```

---

## ⚠️ Points d'Attention & Décisions à Prendre

### Questions à clarifier:

1. **Mode par défaut**:
   - [ ] Option A: Push To Talk activé par défaut
   - [ ] Option B: Wake Mode activé avec wake word par défaut

2. **Position UI Wake Panel**:
   - [ ] Option A: En haut de l'écran (header)
   - [ ] Option B: Dans SettingsPanel
   - [ ] Option C: Les deux (input dans settings + status en haut)

3. **États visibles**:
   - [ ] Option A: Tous les états (idle, sleep, listening, thinking, speaking, happy, error)
   - [ ] Option B: Seulement 4 états (sleep, listening, thinking, speaking)

4. **Transition Avatar**:
   - [ ] Option A: Remplacer Lottie complètement par Canvas
   - [ ] Option B: Garder les deux, permettre de choisir dans settings

5. **Comportement après wake word**:
   - [ ] Option A: Capture automatique jusqu'au silence (5s)
   - [ ] Option B: Capture automatique pendant X secondes fixes
   - [ ] Option C: Utilisateur doit maintenir le bouton après wake word

6. **Gestion du silence timeout**:
   - [ ] 3 secondes
   - [ ] 5 secondes
   - [ ] 7 secondes
   - [ ] Configurable par l'utilisateur

---

## 📦 Dépendances & Compatibility

### Browser Support:
- **Web Speech API**: Chrome, Edge (webkit), Safari
- **Canvas API**: Tous les navigateurs modernes
- **Audio Recording**: Nécessite HTTPS en production

### NPM Packages (déjà installés):
- `zustand`: State management ✅
- `react`: Framework ✅
- `vite`: Build tool ✅

### Pas de nouvelles dépendances nécessaires! 🎉

---

## 🚀 Ordre d'Implémentation Recommandé

### Sprint 1: Canvas Engine (2-3 heures)
1. ✅ Créer `eyesEngine.ts` (extraction HTML → TypeScript)
2. ✅ Créer `CanvasEyes.tsx` component
3. ✅ Tester le canvas seul (sans wake word)
4. ✅ Vérifier que les états changent correctement

### Sprint 2: Wake Word Service (1-2 heures)
1. ✅ Créer `wakeWordService.ts`
2. ✅ Tester la détection dans console
3. ✅ Gérer les erreurs et permissions

### Sprint 3: UI Wake Word (1 heure)
1. ✅ Créer `WakeWordPanel.tsx`
2. ✅ Styles CSS
3. ✅ Intégrer dans AgentScreen

### Sprint 4: Integration avec Backend (2 heures)
1. ✅ Modifier `agentStore.ts` (ajouter wake fields)
2. ✅ Modifier `MicButton.tsx` (logique wake word)
3. ✅ Tester le flow complet : Wake Word → Backend → Response

### Sprint 5: Polish & Testing (1-2 heures)
1. ✅ Ajuster les timings (silence timeout, etc.)
2. ✅ Tester sur mobile (orientation, touch)
3. ✅ Améliorer les messages d'erreur
4. ✅ Documentation utilisateur

**Total estimé: 7-10 heures de développement**

---

## 🧪 Tests à Effectuer

### Test 1: Canvas Rendering
- [ ] Canvas s'affiche correctement
- [ ] Yeux suivent le curseur
- [ ] Clignements automatiques
- [ ] Transitions fluides entre états
- [ ] Responsive (mobile + desktop)

### Test 2: Wake Word Detection
- [ ] Wake word sauvegardé correctement
- [ ] Détection fonctionne (case insensitive)
- [ ] Pas de faux positifs
- [ ] Gestion des erreurs microphone
- [ ] Auto-restart après "no-speech" error

### Test 3: Push To Talk
- [ ] Bouton fonctionne en mode normal
- [ ] Bouton désactivé en wake mode
- [ ] Audio capturé correctement
- [ ] Backend reçoit l'audio

### Test 4: Flow Complet Wake Word
- [ ] Sleep mode activé quand wake ON
- [ ] Wake word déclenche listening
- [ ] Audio capturé après wake word
- [ ] Timeout silence fonctionne
- [ ] Retour en sleep après réponse

### Test 5: Integration Backend
- [ ] États synchronisés (Canvas ↔ Zustand ↔ Backend)
- [ ] Audio response joué correctement
- [ ] Toasts affichés au bon moment
- [ ] Historique mis à jour

---

## 📚 Documentation Utilisateur (à créer)

### Guide d'utilisation:

**Mode Push To Talk:**
1. Click & maintenir le bouton 🎤
2. Parler
3. Relâcher le bouton
4. Attendre la réponse

**Mode Wake Word:**
1. Entrer un wake word (ex: "hi gob")
2. Cliquer "Save"
3. Activer "Wake ON"
4. Dire le wake word
5. Parler normalement
6. L'assistant répond automatiquement

---

## 🎯 Prochaines Étapes Immédiates

**Attente de réponses aux questions:**
1. Mode par défaut ?
2. Position UI ?
3. États visibles ?
4. Garder Lottie ou remplacer complètement ?

**Une fois les décisions prises:**
→ Je commence l'implémentation avec le Sprint 1 (Canvas Engine)

---

*Document créé le 2026-02-21*
*Version: 1.0*
