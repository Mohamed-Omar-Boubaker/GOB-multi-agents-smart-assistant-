PICOVOICE SETUP (agent-ui)

This document explains how to configure and test Picovoice Porcupine for the mobile app (Capacitor).

1) Add your Picovoice access key
- Create a file at the project root `agent-ui/.env` with:

```
VITE_PICOVOICE_ACCESS_KEY=your_real_access_key_here
```

- The frontend reads `import.meta.env.VITE_PICOVOICE_ACCESS_KEY` at build time.

2) Install the client library
- From `agent-ui` run:

```bash
npm install @picovoice/porcupine-react --save
# If you prefer an official Capacitor package (private), follow Picovoice docs and authenticate
npx cap sync
```

3) Native permissions
- Android: ensure `AndroidManifest.xml` contains the microphone permission and a runtime request if targeting modern Android:

```xml
<!-- AndroidManifest.xml (android/app/src/main/AndroidManifest.xml) -->
<uses-permission android:name="android.permission.RECORD_AUDIO" />
```

Also request runtime permission in app code (e.g., using Cordova/Capacitor permissions API or Android request).

- iOS: add the microphone usage description in `ios/App/App/Info.plist`:

```xml
<key>NSMicrophoneUsageDescription</key>
<string>Microphone is used to detect the wake word</string>
```

4) Build & sync

```bash
# from agent-ui
npm run build
npx cap sync
```

5) Testing on device
- Install on an Android device or emulator (or iOS device). Use remote debug (Chrome DevTools for Android) to view console logs.
- The `picovoiceService` logs appear as `[Picovoice] ...` and the `wakeWordService` logs as `[WakeWord] ...`.

6) Troubleshooting
- If the library is private or requires credentials, follow Picovoice docs to authenticate your npm account or install from a provided tarball or git URL.
- If `import.meta.env.VITE_PICOVOICE_ACCESS_KEY` is empty, the service will fall back to the placeholder and will not initialize properly.

7) Security
- Do not commit your real access key to the repository. Use environment variables and CI secrets for builds.

8) Optional
- To use custom keyword files (.ppn), upload them to your app assets and call `picovoiceService.initializeWithCustomKeywords([...paths])`.
