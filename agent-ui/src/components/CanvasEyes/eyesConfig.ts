/**
 * Eyes Config - Configuration des états visuels pour le canvas
 * Extrait du test HTML complet
 */

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

export const EYES_STATES: Record<EyesStateName, EyesState> = {
  idle: {
    pupilScale: 1.0,
    irisRGB: [38, 130, 220],
    irisEdgeRGB: [12, 60, 130],
    irisGlow: 0.22,
    browAngle: 0,
    browLift: 0,
    lidClose: 0,
    followStr: 0.9,
    pupilShiftY: 0,
    mouthW: 1.05,
    mouthCurve: 0.07,
    mouthOpen: 0,
    mouthH: 0.28,
    mouthWobble: 0,
    motY: 0.16,
    motX: 0.05,
    motSpeed: 0.65,
    motTilt: 0.010,
    blinkEvery: 210,
    blinkDur: 6,
    distortAmp: 0.8,
    distortFreq: 0.012,
    distortSpeed: 0.4,
  },
  sleep: {
    pupilScale: 0.4,
    irisRGB: [20, 35, 65],
    irisEdgeRGB: [8, 15, 35],
    irisGlow: 0.06,
    browAngle: 4,
    browLift: 5,
    lidClose: 1.0,
    followStr: 0,
    pupilShiftY: 0,
    mouthW: 0.75,
    mouthCurve: 0.05,
    mouthOpen: 0.15,
    mouthH: 0.20,
    mouthWobble: 0,
    motY: 0.50,
    motX: 0.0,
    motSpeed: 0.36,
    motTilt: 0.005,
    blinkEvery: 9999,
    blinkDur: 30,
    distortAmp: 2.0,
    distortFreq: 0.008,
    distortSpeed: 0.15,
  },
  listening: {
    pupilScale: 1.15,
    irisRGB: [0, 200, 175],
    irisEdgeRGB: [0, 90, 105],
    irisGlow: 0.30,
    browAngle: 3,
    browLift: 5,
    lidClose: 0,
    followStr: 0.05,
    pupilShiftY: 0,
    mouthW: 0.85,
    mouthCurve: 0.04,
    mouthOpen: 0.42,
    mouthH: 0.32,
    mouthWobble: 0,
    motY: 0.04,
    motX: 0.02,
    motSpeed: 0.45,
    motTilt: 0.003,
    blinkEvery: 600,
    blinkDur: 4,
    distortAmp: 3.5,
    distortFreq: 0.016,
    distortSpeed: 0.6,
  },
  thinking: {
    pupilScale: 0.82,
    irisRGB: [90, 100, 240],
    irisEdgeRGB: [30, 38, 160],
    irisGlow: 0.24,
    browAngle: -7,
    browLift: 7,
    lidClose: 0,
    followStr: 0.08,
    pupilShiftY: -0.14,
    mouthW: 0.65,
    mouthCurve: -0.02,
    mouthOpen: 0,
    mouthH: 0.18,
    mouthWobble: 0.38,
    motY: 0.09,
    motX: 0.12,
    motSpeed: 1.7,
    motTilt: 0.022,
    blinkEvery: 360,
    blinkDur: 5,
    distortAmp: 5.0,
    distortFreq: 0.022,
    distortSpeed: 1.2,
  },
  speaking: {
    pupilScale: 0.95,
    irisRGB: [60, 190, 145],
    irisEdgeRGB: [18, 95, 72],
    irisGlow: 0.26,
    browAngle: 2,
    browLift: 2,
    lidClose: 0,
    followStr: 0.6,
    pupilShiftY: 0,
    mouthW: 1.0,
    mouthCurve: 0.10,
    mouthOpen: 0.5,
    mouthH: 0.38,
    mouthWobble: 0,
    motY: 0.14,
    motX: 0.04,
    motSpeed: 0.80,
    motTilt: 0.009,
    blinkEvery: 180,
    blinkDur: 6,
    distortAmp: 4.0,
    distortFreq: 0.018,
    distortSpeed: 0.9,
  },
  happy: {
    pupilScale: 0.92,
    irisRGB: [55, 200, 110],
    irisEdgeRGB: [15, 105, 55],
    irisGlow: 0.22,
    browAngle: 9,
    browLift: -3,
    lidClose: 0.26,
    followStr: 0.8,
    pupilShiftY: 0,
    mouthW: 1.30,
    mouthCurve: 0.35,
    mouthOpen: 0.55,
    mouthH: 0.42,
    mouthWobble: 0,
    motY: 0.28,
    motX: 0.08,
    motSpeed: 1.30,
    motTilt: 0.016,
    blinkEvery: 150,
    blinkDur: 8,
    distortAmp: 6.0,
    distortFreq: 0.014,
    distortSpeed: 1.5,
  },
  error: {
    pupilScale: 0.62,
    irisRGB: [220, 55, 40],
    irisEdgeRGB: [130, 18, 10],
    irisGlow: 0.32,
    browAngle: -20,
    browLift: -1,
    lidClose: 0,
    followStr: 0.35,
    pupilShiftY: 0,
    mouthW: 0.95,
    mouthCurve: -0.26,
    mouthOpen: 0.12,
    mouthH: 0.18,
    mouthWobble: 0,
    motY: 0.03,
    motX: 0.20,
    motSpeed: 2.2,
    motTilt: 0.007,
    blinkEvery: 9999,
    blinkDur: 4,
    distortAmp: 7.0,
    distortFreq: 0.028,
    distortSpeed: 2.0,
  },
};

export const STATE_LABELS: Record<EyesStateName, string> = {
  idle: 'Standby',
  sleep: 'Dormant',
  listening: 'Listening…',
  thinking: 'Processing…',
  speaking: 'Speaking',
  happy: 'Done',
  error: 'Error'
};
