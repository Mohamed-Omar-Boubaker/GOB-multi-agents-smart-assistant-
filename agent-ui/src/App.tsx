/**
 * App.tsx - Point d'entrée de l'application
 * Phase 4: Ajout du routing pour mode normal et fullscreen wake mode
 * Phase 5: Initialisation mobile avec permissions et backend check
 * Phase 6: Background particules animées
 */

import { useEffect, useState } from 'react';
import { BrowserRouter, Routes, Route } from 'react-router-dom';
import { AgentScreen } from './screens/AgentScreen';
import { FullscreenEyesScreen } from './screens/FullscreenEyesScreen/FullscreenEyesScreen';
import { requestAllPermissions, setupNetworkListener } from './services/permissions.service';
import { apiService } from './services/api';
import { logAPIConfig } from './config/api.config';
import { StatusBar, Style } from '@capacitor/status-bar';
import { Capacitor } from '@capacitor/core';
import { useAgentStore } from './store/agentStore';
import { wakeWordService } from './services/wakeWordService';
import './App.css';

function App() {
  const setWakeWord = useAgentStore((state) => state.setWakeWord);
  const [isInitialized, setIsInitialized] = useState(false);
  const [isBackendReady, setIsBackendReady] = useState(false);
  const [permissionsGranted, setPermissionsGranted] = useState(false);
  const [isOnline, setIsOnline] = useState(navigator.onLine);
  const [initError, setInitError] = useState<string | null>(null);

  // ✅ Cacher la status bar via Capacitor (seulement sur mobile natif)
  useEffect(() => {
    if (Capacitor.isNativePlatform()) {
      StatusBar.setOverlaysWebView({ overlay: true });
      StatusBar.setStyle({ style: Style.Dark });
      StatusBar.hide();
    }
  }, []);

  // ✅ Particules background animées
  useEffect(() => {
    const canvas = document.createElement('canvas');
    canvas.id = 'particles-canvas';
    document.body.insertBefore(canvas, document.body.firstChild);
    const ctx = canvas.getContext('2d')!;

    let W: number, H: number;
    let animId: number;
    const mouse = { x: -999, y: -999 };

    interface Particle {
      x: number; y: number;
      vx: number; vy: number;
      r: number;
      color: string;
      alpha: number;
      pulse: number;
    }

    let particles: Particle[] = [];

    const COLORS = [
      'rgba(80,160,255,',
      'rgba(120,80,255,',
      'rgba(0,220,180,',
      'rgba(180,100,255,',
    ];

    function createParticle(): Particle {
      return {
        x: Math.random() * W,
        y: Math.random() * H,
        r: Math.random() * 1.8 + 0.4,
        vx: (Math.random() - 0.5) * 0.4,
        vy: (Math.random() - 0.5) * 0.4,
        color: COLORS[Math.floor(Math.random() * COLORS.length)],
        alpha: Math.random() * 0.6 + 0.2,
        pulse: Math.random() * Math.PI * 2,
      };
    }

    function init() {
      W = canvas.width = window.innerWidth;
      H = canvas.height = window.innerHeight;
      particles = [];
      const count = Math.floor((W * H) / 6000);
      for (let i = 0; i < count; i++) particles.push(createParticle());
    }

    function draw() {
      ctx.clearRect(0, 0, W, H);

      for (let i = 0; i < particles.length; i++) {
        const p = particles[i];
        p.x += p.vx;
        p.y += p.vy;
        p.pulse += 0.02;

        if (p.x < 0) p.x = W;
        if (p.x > W) p.x = 0;
        if (p.y < 0) p.y = H;
        if (p.y > H) p.y = 0;

        const dx = p.x - mouse.x;
        const dy = p.y - mouse.y;
        const dist = Math.sqrt(dx * dx + dy * dy);
        if (dist < 80 && dist > 0) {
          p.x += (dx / dist) * 0.8;
          p.y += (dy / dist) * 0.8;
        }

        const alpha = p.alpha * (0.7 + 0.3 * Math.sin(p.pulse));
        ctx.beginPath();
        ctx.arc(p.x, p.y, p.r, 0, Math.PI * 2);
        ctx.fillStyle = p.color + alpha + ')';
        ctx.fill();

        for (let j = i + 1; j < particles.length; j++) {
          const q = particles[j];
          const dx2 = p.x - q.x;
          const dy2 = p.y - q.y;
          const d2 = Math.sqrt(dx2 * dx2 + dy2 * dy2);
          if (d2 < 100) {
            ctx.beginPath();
            ctx.moveTo(p.x, p.y);
            ctx.lineTo(q.x, q.y);
            ctx.strokeStyle = 'rgba(100,160,255,' + (0.12 * (1 - d2 / 100)) + ')';
            ctx.lineWidth = 0.5;
            ctx.stroke();
          }
        }
      }
      animId = requestAnimationFrame(draw);
    }

    const onMouseMove = (e: MouseEvent) => {
      mouse.x = e.clientX;
      mouse.y = e.clientY;
    };
    const onMouseLeave = () => {
      mouse.x = -999;
      mouse.y = -999;
    };
    const onResize = () => init();

    window.addEventListener('mousemove', onMouseMove);
    window.addEventListener('mouseleave', onMouseLeave);
    window.addEventListener('resize', onResize);

    init();
    draw();

    return () => {
      cancelAnimationFrame(animId);
      window.removeEventListener('mousemove', onMouseMove);
      window.removeEventListener('mouseleave', onMouseLeave);
      window.removeEventListener('resize', onResize);
      canvas.remove();
    };
  }, []);

  /**
   * Initialisation de l'application au démarrage
   */
  useEffect(() => {
    const initializeApp = async () => {
      try {
        console.log('🚀 Initialisation application...');
        setInitError(null);

        logAPIConfig();

        // Wake word par défaut a chaque démarrage
        const defaultWakeWord = 'red';
        setWakeWord(defaultWakeWord);
        wakeWordService.setWakeWord(defaultWakeWord);

        console.log('📡 Vérification backend...');
        const backendOk = await apiService.healthCheck();
        setIsBackendReady(backendOk);

        if (!backendOk) {
          console.warn('⚠️ Backend non accessible');
        }

        console.log('🔐 Demande permissions...');
        const permsOk = await requestAllPermissions();
        setPermissionsGranted(permsOk);

        setIsInitialized(true);
        console.log('✅ Application initialisée avec succès');

      } catch (error: any) {
        console.error('❌ Erreur initialisation:', error);
        setInitError(error.message);
        setIsInitialized(true);
      }
    };

    initializeApp();
  }, [setWakeWord]);

  /**
   * Écouter changements de connexion réseau
   */
  useEffect(() => {
    const cleanup = setupNetworkListener((online) => {
      setIsOnline(online);
      if (online && !isBackendReady) {
        apiService.healthCheck().then(setIsBackendReady);
      }
    });
    return cleanup;
  }, [isBackendReady]);

  /**
   * Écran de chargement pendant initialisation
   */
  if (!isInitialized) {
    return (
      <div className="min-h-screen flex items-center justify-center p-4">
        <div className="bg-white rounded-2xl shadow-2xl p-8 max-w-md w-full">
          <div className="text-center">
            <div className="mb-6">
              <div className="w-20 h-20 bg-blue-500 rounded-full mx-auto flex items-center justify-center">
                <span className="text-4xl">🤖</span>
              </div>
            </div>

            <h1 className="text-2xl font-bold text-gray-800 mb-4">
              Agent Intelligent
            </h1>

            {!initError ? (
              <>
                <div className="flex justify-center mb-4">
                  <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-500"></div>
                </div>
                <p className="text-gray-600">
                  Initialisation en cours...
                </p>
                <div className="mt-4 space-y-2 text-sm text-gray-500">
                  <div className="flex items-center justify-center gap-2">
                    {isBackendReady ? '✅' : '⏳'} Connexion backend
                  </div>
                  <div className="flex items-center justify-center gap-2">
                    {permissionsGranted ? '✅' : '⏳'} Permissions système
                  </div>
                </div>
              </>
            ) : (
              <>
                <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-4 mb-4">
                  <div className="flex items-start gap-3">
                    <span className="text-2xl">⚠️</span>
                    <div className="flex-1 text-left">
                      <h3 className="font-semibold text-yellow-800 mb-2">
                        Mode dégradé
                      </h3>
                      <p className="text-sm text-yellow-600">
                        Certaines fonctionnalités peuvent être limitées
                      </p>
                    </div>
                  </div>
                </div>

                <button
                  onClick={() => setIsInitialized(true)}
                  className="w-full bg-blue-500 hover:bg-blue-600 text-white font-semibold py-3 px-6 rounded-lg transition-colors"
                >
                  Continuer quand même
                </button>
              </>
            )}
          </div>
        </div>
      </div>
    );
  }

  /**
   * Interface principale (quand tout est initialisé)
   */
  return (
    <BrowserRouter>
      <div className="app">
        {!isOnline && (
          <div className="fixed top-0 left-0 right-0 bg-red-500 text-white p-2 text-center font-semibold z-50 text-sm">
            ⚠️ Pas de connexion internet
          </div>
        )}
        {/*
        {!isBackendReady && (
          <div
            className="fixed top-0 left-0 right-0 bg-yellow-500 text-white p-2 text-center font-semibold z-50 text-sm"
            style={{ top: !isOnline ? '2rem' : '0' }}
          >
            ⚠️ Backend non accessible
          </div>
        )} */}
      

        <Routes>
          <Route path="/" element={<AgentScreen />} />
          <Route path="/wake" element={<FullscreenEyesScreen />} />
        </Routes>
      </div>
    </BrowserRouter>
  );
}

export default App;