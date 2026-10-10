uvicorn piper_tts_service:app --host 0.0.0.0 --port 8005

Invoke-RestMethod `
-Uri "http://127.0.0.1:8005/tts" `
-Method POST `
-Body '{"text":"bonjour montassar nawara"}' `
-ContentType "application/json"

curl.exe http://127.0.0.1:8005/audio/oki.wav --output test.wav
curl.exe http://192.168.1.3:8005/audio/437b6752-aa70-49cb-bcc8-116cd716b8e9.wav --output test0.wav