# Agent UI (React + Vite + Capacitor)

Frontend application for the PCD AI Embedded Agent.

## Maintainers

- Montassar


## What This App Does

The UI provides:

- Push-to-talk audio capture
- Wake mode with fullscreen visual assistant screen
- Voice response playback
- Real-time action and conversation feedback
- Settings for language, audio behavior, and wake word
- Device/contact configuration panels for backend integration

The app runs in:

- Web browser (development and desktop testing)
- Android app (via Capacitor)

## Tech Stack

- React 19 + TypeScript
- Vite 7
- Zustand state management
- React Router
- Capacitor 8 (Android)
- Speech recognition and status bar plugins

## App Flow

1. User taps mic or wake mode triggers recording.
2. Audio is sent to backend /command/audio.
3. Backend returns transcription, response, and metadata.
4. UI updates state: listening -> thinking -> speaking -> idle.
5. Action confirmations and status are displayed in the app.

## Project Structure

```text
agent-ui/
|- src/
|  |- components/
|  |  |- MicButton/
|  |  |- CanvasEyes/
|  |  |- SettingsPanel/
|  |  |- WakeWordPanel/
|  |  |- ActionPanel/
|  |  |- MemoryPanel/
|  |  |- ContactManagerPanel/
|  |  |- DeviceManagerPanel/
|  |- screens/
|  |  |- AgentScreen/
|  |  |- FullscreenEyesScreen/
|  |- services/
|  |  |- api.ts
|  |  |- wakeWordService.ts
|  |- config/
|  |  |- api.config.ts
|- android/
|- capacitor.config.ts
|- vite.config.ts
```

## Scripts

- npm run dev: start local Vite dev server
- npm run build: compile TypeScript and create web build
- npm run build:mobile: build assets for Capacitor deployment
- npm run preview: preview production build
- npm run lint: run ESLint
- npm run check: run configuration check script

## Local Development

### 1) Install dependencies

```bash
cd agent-ui
npm install
```

### 2) Run web app

```bash
npm run dev
```

Default URL: http://localhost:5173

### 3) Backend requirement

Start backend separately on port 8000:

```bash
python -m uvicorn backend.main:app --reload --host 0.0.0.0 --port 8000
```

## Backend Connectivity

Connection logic is centralized in src/config/api.config.ts.

Recommended mode for mobile (Option 2): environment-based URL.

1. Copy .env.example to .env.
2. Set backend LAN URL in .env:

```env
VITE_BACKEND_URL=http://YOUR_PC_IP:8000
```

3. Start backend with host 0.0.0.0.
4. Rebuild and sync mobile app after backend IP changes.

Fallback behavior when env is missing:

- Web development: runtime host or localhost
- Mobile/production: warning + fallback (not recommended)

### Network Configuration (Mobile / LAN)

Use this checklist to avoid backend connection issues on phone:

1. Put phone and PC on the same Wi-Fi network.
2. Start backend on the PC with host 0.0.0.0:

```bash
python -m uvicorn backend.main:app --reload --host 0.0.0.0 --port 8000
```

3. Set agent-ui/.env with PC LAN IP:

```env
VITE_BACKEND_URL=http://YOUR_PC_IP:8000
```

4. Allow inbound TCP 8000 in Windows Firewall (Private network).
5. Confirm backend is reachable from phone browser:
	http://YOUR_PC_IP:8000/health
6. Rebuild and sync Android app after every IP or env change:

```bash
npm run build:mobile
npx cap sync android
```

If wake mode is active but no voice results are returned, ensure no other app/process keeps the microphone stream open.

## Mobile App with Capacitor (Android)

The app is already configured for Android in android/.

### Build and sync

```bash
cd agent-ui
npm install
npm run build:mobile
npx cap sync android
```

### Open in Android Studio

```bash
npx cap open android
```

### Important mobile details

- capacitor.config.ts allows cleartext HTTP for local backend testing
- AndroidManifest.xml includes INTERNET and RECORD_AUDIO permissions
- vite.config.ts uses base './' for Capacitor compatibility

### Testing on a real phone

1. Start backend on your PC with host 0.0.0.0.
2. Ensure phone and PC are on the same network.
3. Set VITE_BACKEND_URL to the PC LAN IP in agent-ui/.env.
4. Build and run from Android Studio.

## Wake Mode and Wake Word

- Route / is normal mode.
- Route /wake is fullscreen wake mode.
- Wake word behavior is handled by wakeWordService.ts.
- Wake mode state is stored in the Zustand store.

Picovoice setup notes are in README_PICOVOICE.md.

## Troubleshooting

### Microphone permission denied

- Allow microphone access in browser/app settings.
- Reinstall app on Android if permission state is stuck.

### Backend unreachable

- Check backend health at http://localhost:8000/health.
- Verify API URL resolution in api.config.ts logs.
- For Android, use PC LAN IP, not localhost.

### Capacitor app shows blank screen

- Rebuild with npm run build:mobile.
- Run npx cap sync android again.
- Confirm vite base is './'.

## Related Docs

- [../README.md](../README.md)
- [INTEGRATION_COMPLETE.md](INTEGRATION_COMPLETE.md)
- [README_PICOVOICE.md](README_PICOVOICE.md)
