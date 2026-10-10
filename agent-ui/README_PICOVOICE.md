Picovoice integration (agent-ui)

Quick steps to configure Picovoice wake-word on mobile:

1) Set environment key
- Create `agent-ui/.env` with:

```
VITE_PICOVOICE_ACCESS_KEY=your_real_access_key_here
```

2) Install dependency

```
cd agent-ui
npm install @picovoice/porcupine-react --save
npx cap sync
```

3) Add native microphone permission
- Android: add `<uses-permission android:name="android.permission.RECORD_AUDIO" />` to `android/app/src/main/AndroidManifest.xml`.
- iOS: add `NSMicrophoneUsageDescription` to `ios/App/App/Info.plist`.

4) Build and deploy

```
npm run build
npx cap sync
npx cap open android
# build/install from Android Studio to device
```

5) Notes
- Do not commit `.env` with real keys.
- If `@picovoice/porcupine-react` is hook-only and doesn't expose a runtime API, consider using the Capacitor plugin or a community package that exposes a start/stop API.
