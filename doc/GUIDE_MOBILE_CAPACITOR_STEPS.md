# 📱 Guide Transformation Application Mobile avec Capacitor

## ✅ Configuration Mobile Complète

Tous les fichiers nécessaires ont été créés :

### Fichiers Créés/Modifiés

1. ✅ **vite.config.ts** - Configuration build mobile (`base: './'`)
2. ✅ **src/config/api.config.ts** - Configuration backend dynamique (dev/mobile/prod)
3. ✅ **src/services/permissions.service.ts** - Gestion permissions (micro, réseau)
4. ✅ **src/App.tsx** - Initialisation avec vérifications backend et permissions
5. ✅ **package.json** - Scripts `build:mobile` et `check` ajoutés
6. ✅ **scripts/check-config.js** - Script de vérification configuration

---

## 🚀 Prochaines Étapes

### 1️⃣ Configurer Votre IP Locale

**Trouvez votre IP :**

```powershell
ipconfig
```

Cherchez **"Adresse IPv4"** (ex: `192.168.1.10`)

**Modifiez le fichier :**

Ouvrez `src/config/api.config.ts` et remplacez ligne 25 :

```typescript
return 'http://192.168.1.10:8000'; // ⚠️ METTEZ VOTRE VRAIE IP ICI
```

---

### 2️⃣ Vérifier la Configuration

```powershell
cd pcd-ai-embedded-agent/agent-ui
npm run check
```

Ce script vérifie que tout est bien configuré.

---

### 3️⃣ Lancer le Backend Python

**Dans un terminal séparé :**

```powershell
cd pcd-ai-embedded-agent/backend
uvicorn main:app --host 0.0.0.0 --port 8000
```

**⚠️ Important :** Utilisez `--host 0.0.0.0` pour que le backend soit accessible depuis votre téléphone !

---

### 4️⃣ Tester le Build Frontend

```powershell
cd pcd-ai-embedded-agent/agent-ui
npm run build
```

**Résultat attendu :** Création du dossier `dist/` avec votre app compilée.

---

### 5️⃣ Installer Capacitor

```powershell
cd pcd-ai-embedded-agent/agent-ui

# Installer dépendances Capacitor
npm install @capacitor/core @capacitor/cli @capacitor/android

# Initialiser Capacitor
npx cap init
```

**Répondez aux questions :**
- **App name:** `Agent Intelligent`
- **App ID:** `com.pcd.agent`

---

### 6️⃣ Ajouter Plateforme Android

```powershell
npx cap add android
```

Cela crée un dossier `android/` avec le projet Android Studio.

---

### 7️⃣ Copier le Build vers Android

```powershell
# Après chaque modification du code
npm run build
npx cap copy android

# OU en une commande
npx cap sync android
```

---

### 8️⃣ Ouvrir dans Android Studio

```powershell
npx cap open android
```

Android Studio s'ouvre automatiquement avec votre projet.

---

### 9️⃣ Tester sur Téléphone Réel

**Sur votre téléphone Android :**

1. **Paramètres → À propos du téléphone**
2. Appuyez **7 fois** sur "Numéro de build"
3. **Paramètres → Options pour développeurs**
4. Activez **Débogage USB**

**Branchez le téléphone en USB et lancez :**

```powershell
# Vérifier connexion
adb devices

# Lancer l'app sur le téléphone
npx cap run android
```

---

## 📋 Workflow de Développement

### Cycle de développement standard :

```powershell
# 1. Modifier le code React (src/)
# 2. Tester en mode web dev
npm run dev

# 3. Build pour mobile
npm run build

# 4. Copier vers Android
npx cap copy android

# 5. Lancer sur téléphone
npx cap run android
```

---

## 🔧 Configuration Importante

### AndroidManifest.xml (Permissions)

Après `npx cap add android`, ajoutez ces permissions dans :

**Fichier :** `android/app/src/main/AndroidManifest.xml`

```xml
<manifest xmlns:android="http://schemas.android.com/apk/res/android">
    
    <!-- Permissions nécessaires -->
    <uses-permission android:name="android.permission.INTERNET" />
    <uses-permission android:name="android.permission.ACCESS_NETWORK_STATE" />
    <uses-permission android:name="android.permission.RECORD_AUDIO" />
    <uses-permission android:name="android.permission.MODIFY_AUDIO_SETTINGS" />
    
    <application
        android:usesCleartextTraffic="true">
        <!-- Pour autoriser HTTP local -->
    </application>
</manifest>
```

### capacitor.config.ts

**Fichier :** `capacitor.config.ts` (créé par `npx cap init`)

```typescript
import { CapacitorConfig } from '@capacitor/cli';

const config: CapacitorConfig = {
  appId: 'com.pcd.agent',
  appName: 'Agent Intelligent',
  webDir: 'dist',
  server: {
    androidScheme: 'https',
    allowNavigation: [
      'http://192.168.1.10:8000', // Votre backend local
    ]
  }
};

export default config;
```

---

## 🎯 Résumé des Commandes

```powershell
# Configuration initiale (1 fois)
npm install @capacitor/core @capacitor/cli @capacitor/android
npx cap init
npx cap add android

# Développement quotidien
npm run build
npx cap sync android
npx cap run android

# Vérification
npm run check
```

---

## 📱 Générer APK pour Partage

**Dans Android Studio :**

1. **Build → Build Bundle(s) / APK(s) → Build APK(s)**
2. Attendre compilation
3. **locate** → Récupérer `app-debug.apk`

**Installer sur téléphone :**

```powershell
adb install android/app/build/outputs/apk/debug/app-debug.apk
```

---

## ❓ Troubleshooting

### Erreur "Backend non accessible"

1. Vérifiez que le backend tourne : `uvicorn main:app --host 0.0.0.0 --port 8000`
2. Vérifiez votre IP locale dans `api.config.ts`
3. Téléphone et PC sur le **même WiFi**

### Microphone ne fonctionne pas

1. Permissions ajoutées dans `AndroidManifest.xml` ?
2. Permission accordée au runtime (popup Android) ?
3. Testez sur **téléphone réel** (pas émulateur)

### Erreur "webDir not found"

```powershell
npm run build
npx cap copy android
```

---

## ✅ Configuration Terminée !

Vous êtes maintenant prêt à :

- ✅ Développer votre interface React
- ✅ La compiler pour mobile
- ✅ La tester sur téléphone réel
- ✅ Générer un APK pour distribution

**Bon développement mobile ! 🚀**
