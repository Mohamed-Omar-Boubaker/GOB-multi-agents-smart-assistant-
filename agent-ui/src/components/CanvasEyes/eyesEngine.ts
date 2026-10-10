/**
 * Eyes Engine - Moteur de rendu pour les yeux animés
 * Adapté du test HTML complet vers TypeScript/React
 */

import { EYES_STATES, type EyesState, type EyesStateName } from './eyesConfig';

interface ZzzParticle {
  x: number;
  y: number;
  text: string;
  size: number;
  alpha: number;
  life: number;
  speed: number;
  drift: number;
  fadeIn: number;
}

export class EyesEngine {
  private canvas: HTMLCanvasElement;
  private ctx: CanvasRenderingContext2D;
  private offCanvas: HTMLCanvasElement;
  private octx: CanvasRenderingContext2D;
  
  private W: number = 0;
  private H: number = 0;
  
  // État actuel
  private state: EyesStateName = 'idle';
  private cur: EyesState;
  
  // Mouse tracking
  private mouseX: number = 0.5;
  private mouseY: number = 0.5;
  private mouseIdle: boolean = true;
  private mouseIdleTimer: number = 0;
  private autoPhase: number = 0;
  
  // Auto offsets pour expressions
  private autoBrowAngleOffset: number = 0;
  private autoBrowLiftOffset: number = 0;
  private autoMouthCurveOffset: number = 0;
  private autoMouthOpenOffset: number = 0;
  private autoBrowPhase: number = 0;
  private autoMouthPhase: number = 0;
  
  // Blink system
  private blinkFrames: number = 0;
  private nextBlink: number = 210;
  
  // Animation phases
  private frame: number = 0;
  private beatPhase: number = 0;
  private thinkPhase: number = 0;
  private talkPhase: number = 0;
  private distTime: number = 0;
  
  // ZZZ particles for sleep
  private zzzParticles: ZzzParticle[] = [];
  private zzzSpawnTimer: number = 0;
  private readonly ZZZ_INTERVAL = 90;
  
  // Animation frame
  private animationFrameId: number | null = null;
  
  // Constants
  private readonly SPEED = 0.065;
  private readonly SPEED_SLOW = 0.028;
  private readonly SPEED_DIST = 0.040;
  private readonly STRIPE = 4;
  
  constructor(canvas: HTMLCanvasElement, offCanvas: HTMLCanvasElement) {
    this.canvas = canvas;
    this.offCanvas = offCanvas;
    
    const ctx = canvas.getContext('2d');
    const octx = offCanvas.getContext('2d');
    
    if (!ctx || !octx) {
      throw new Error('Could not get canvas context');
    }
    
    this.ctx = ctx;
    this.octx = octx;
    this.cur = { ...EYES_STATES.idle };
    
    this.resize();
    window.addEventListener('resize', () => this.resize());
  }
  
  private resize(): void {
    this.W = this.canvas.width = this.offCanvas.width = window.innerWidth;
    this.H = this.canvas.height = this.offCanvas.height = window.innerHeight;
  }
  
  setState(name: EyesStateName): void {
    if (name === this.state) return;
    this.state = name;
    console.log('[Eyes] State changed to:', name);
  }
  
  setMousePosition(x: number, y: number): void {
    this.mouseX = x;
    this.mouseY = y;
    this.mouseIdle = false;
    
    clearTimeout(this.mouseIdleTimer);
    this.mouseIdleTimer = window.setTimeout(() => {
      this.mouseIdle = true;
    }, 3000);
  }
  
  start(): void {
    if (this.animationFrameId !== null) return;
    this.loop();
  }
  
  stop(): void {
    if (this.animationFrameId !== null) {
      cancelAnimationFrame(this.animationFrameId);
      this.animationFrameId = null;
    }
    window.removeEventListener('resize', () => this.resize());
  }
  
  // ─────────────────────────────────────────────────────────────────
  //  LERP & UTILITY FUNCTIONS
  // ─────────────────────────────────────────────────────────────────
  
  private lerp(a: number, b: number, t: number): number {
    return a + (b - a) * t;
  }
  
  private lerpRGB(a: [number, number, number], b: [number, number, number], t: number): [number, number, number] {
    return [
      this.lerp(a[0], b[0], t),
      this.lerp(a[1], b[1], t),
      this.lerp(a[2], b[2], t)
    ];
  }
  
  private rgb(c: [number, number, number]): string {
    return `rgb(${c[0]|0},${c[1]|0},${c[2]|0})`;
  }
  
  private rgba(c: [number, number, number], a: number): string {
    return `rgba(${c[0]|0},${c[1]|0},${c[2]|0},${a})`;
  }
  
  private easeInOut(t: number): number {
    return t < 0.5 ? 2 * t * t : -1 + (4 - 2 * t) * t;
  }
  
  // ─────────────────────────────────────────────────────────────────
  //  AUTO PUPIL MOVEMENT (Lissajous curves)
  // ─────────────────────────────────────────────────────────────────
  
  private updateAutoPupil(): void {
    if (!this.mouseIdle) return;
    this.autoPhase += 0.008;
    
    let x = 0.5, y = 0.5;
    const p = this.autoPhase;
    
    switch(this.state) {
      case 'idle':
        x = 0.5 + Math.sin(p * 1.3) * 0.28;
        y = 0.5 + Math.sin(p * 0.9 + 1.2) * 0.20;
        break;
      case 'sleep':
        x = 0.5 + Math.sin(p * 0.2) * 0.06;
        y = 0.62 + Math.sin(p * 0.15 + 0.5) * 0.04;
        break;
      case 'listening':
        x = 0.5 + Math.sin(p * 0.6) * 0.10;
        y = 0.5 + Math.sin(p * 0.4 + 0.8) * 0.08;
        break;
      case 'thinking':
        x = 0.5 + Math.sin(p * 4.1) * 0.35 + Math.sin(p * 7.3 + 1.1) * 0.12;
        y = 0.5 + Math.sin(p * 3.7 + 0.5) * 0.28 + Math.sin(p * 5.9 + 2.3) * 0.10;
        break;
      case 'speaking':
        x = 0.5 + Math.sin(p * 1.1) * 0.38;
        y = 0.5 + Math.sin(p * 0.7 + 0.4) * 0.10;
        break;
      case 'happy':
        x = 0.5 + Math.sin(p * 2.8) * 0.30 + Math.sin(p * 5.1 + 0.9) * 0.10;
        y = 0.5 + Math.sin(p * 3.3 + 1.5) * 0.22 + Math.sin(p * 2.0 + 0.3) * 0.08;
        break;
      case 'error':
        x = 0.5 + Math.sin(p * 9.5) * 0.30 + Math.sin(p * 14.2 + 0.7) * 0.12;
        y = 0.5 + Math.sin(p * 6.8 + 1.0) * 0.18;
        break;
    }
    
    this.mouseX = x;
    this.mouseY = y;
  }
  
  // ─────────────────────────────────────────────────────────────────
  //  AUTO BROW & MOUTH EXPRESSIONS
  // ─────────────────────────────────────────────────────────────────
  
  private updateAutoBrow(): void {
    this.autoBrowPhase += 0.008;
    const p = this.autoBrowPhase;
    
    switch(this.state) {
      case 'idle':
        this.autoBrowAngleOffset = Math.sin(p * 0.7) * 1.5;
        this.autoBrowLiftOffset = Math.sin(p * 0.5 + 1.0) * 1.2;
        break;
      case 'sleep':
        this.autoBrowAngleOffset = Math.sin(p * 0.15) * 0.8;
        this.autoBrowLiftOffset = 3.0 + Math.sin(p * 0.1) * 0.5;
        break;
      case 'listening':
        this.autoBrowAngleOffset = Math.sin(p * 1.2) * 2.0;
        this.autoBrowLiftOffset = -3.0 + Math.sin(p * 0.9) * 1.0;
        break;
      case 'thinking':
        this.autoBrowAngleOffset = Math.sin(p * 3.5) * 6.0 + Math.sin(p * 7.1 + 0.4) * 2.0;
        this.autoBrowLiftOffset = Math.sin(p * 2.8 + 1.0) * 3.5;
        break;
      case 'speaking':
        this.autoBrowAngleOffset = Math.sin(p * 2.2) * 3.5;
        this.autoBrowLiftOffset = Math.sin(p * 1.8 + 0.5) * 2.5;
        break;
      case 'happy':
        this.autoBrowAngleOffset = Math.sin(p * 3.0) * 4.0;
        this.autoBrowLiftOffset = -5.0 + Math.sin(p * 2.5) * 2.0;
        break;
      case 'error':
        this.autoBrowAngleOffset = Math.sin(p * 10.0) * 4.0 + Math.sin(p * 15.5 + 1.2) * 1.5;
        this.autoBrowLiftOffset = 2.0 + Math.sin(p * 8.0) * 1.5;
        break;
      default:
        this.autoBrowAngleOffset = 0;
        this.autoBrowLiftOffset = 0;
    }
  }
  
  private updateAutoMouth(): void {
    this.autoMouthPhase += 0.008;
    const p = this.autoMouthPhase;
    
    switch(this.state) {
      case 'idle':
        this.autoMouthCurveOffset = Math.sin(p * 0.6) * 0.02;
        this.autoMouthOpenOffset = Math.abs(Math.sin(p * 0.4)) * 0.03;
        break;
      case 'sleep':
        this.autoMouthCurveOffset = Math.sin(p * 0.1) * 0.01;
        this.autoMouthOpenOffset = 0.08 + Math.sin(p * 0.08) * 0.04;
        break;
      case 'listening':
        this.autoMouthCurveOffset = Math.sin(p * 0.5) * 0.015;
        this.autoMouthOpenOffset = Math.abs(Math.sin(p * 0.3)) * 0.06;
        break;
      case 'thinking':
        this.autoMouthCurveOffset = Math.sin(p * 2.5) * 0.06 + Math.sin(p * 5.3 + 1.0) * 0.02;
        this.autoMouthOpenOffset = Math.abs(Math.sin(p * 1.8)) * 0.08;
        break;
      case 'speaking':
        this.autoMouthCurveOffset = Math.sin(p * 2.0) * 0.04;
        this.autoMouthOpenOffset = Math.abs(Math.sin(p * 3.2)) * 0.20;
        break;
      case 'happy':
        this.autoMouthCurveOffset = 0.12 + Math.sin(p * 2.8) * 0.06;
        this.autoMouthOpenOffset = 0.15 + Math.abs(Math.sin(p * 2.2)) * 0.12;
        break;
      case 'error':
        this.autoMouthCurveOffset = Math.sin(p * 8.5) * 0.06 + Math.sin(p * 13.0 + 0.7) * 0.03;
        this.autoMouthOpenOffset = Math.abs(Math.sin(p * 6.0)) * 0.08;
        break;
      default:
        this.autoMouthCurveOffset = 0;
        this.autoMouthOpenOffset = 0;
    }
  }
  
  // ─────────────────────────────────────────────────────────────────
  //  LERP STATE TRANSITIONS
  // ─────────────────────────────────────────────────────────────────
  
  private updateLerps(): void {
    const T = EYES_STATES[this.state];
    this.cur.pupilScale = this.lerp(this.cur.pupilScale, T.pupilScale, this.SPEED);
    this.cur.irisRGB = this.lerpRGB(this.cur.irisRGB, T.irisRGB, this.SPEED);
    this.cur.irisEdgeRGB = this.lerpRGB(this.cur.irisEdgeRGB, T.irisEdgeRGB, this.SPEED);
    this.cur.irisGlow = this.lerp(this.cur.irisGlow, T.irisGlow, this.SPEED);
    this.cur.browAngle = this.lerp(this.cur.browAngle, T.browAngle, this.SPEED);
    this.cur.browLift = this.lerp(this.cur.browLift, T.browLift, this.SPEED);
    this.cur.lidClose = this.lerp(this.cur.lidClose, T.lidClose, this.SPEED);
    this.cur.followStr = this.lerp(this.cur.followStr, T.followStr, this.SPEED);
    this.cur.pupilShiftY = this.lerp(this.cur.pupilShiftY, T.pupilShiftY, this.SPEED);
    this.cur.mouthW = this.lerp(this.cur.mouthW, T.mouthW, this.SPEED);
    this.cur.mouthCurve = this.lerp(this.cur.mouthCurve, T.mouthCurve, this.SPEED);
    this.cur.mouthOpen = this.lerp(this.cur.mouthOpen, T.mouthOpen, this.SPEED);
    this.cur.mouthH = this.lerp(this.cur.mouthH, T.mouthH, this.SPEED);
    this.cur.mouthWobble = this.lerp(this.cur.mouthWobble, T.mouthWobble, this.SPEED);
    this.cur.motY = this.lerp(this.cur.motY, T.motY, this.SPEED);
    this.cur.motX = this.lerp(this.cur.motX, T.motX, this.SPEED);
    this.cur.motSpeed = this.lerp(this.cur.motSpeed, T.motSpeed, this.SPEED * 0.4);
    this.cur.motTilt = this.lerp(this.cur.motTilt, T.motTilt, this.SPEED);
    this.cur.blinkEvery = this.lerp(this.cur.blinkEvery, T.blinkEvery, this.SPEED_SLOW);
    this.cur.blinkDur = this.lerp(this.cur.blinkDur, T.blinkDur, this.SPEED_SLOW);
    this.cur.distortAmp = this.lerp(this.cur.distortAmp, T.distortAmp, this.SPEED_DIST);
    this.cur.distortFreq = this.lerp(this.cur.distortFreq, T.distortFreq, this.SPEED_DIST);
    this.cur.distortSpeed = this.lerp(this.cur.distortSpeed, T.distortSpeed, this.SPEED_DIST);
  }
  
  // ─────────────────────────────────────────────────────────────────
  //  BLINK SYSTEM
  // ─────────────────────────────────────────────────────────────────
  
  private tickBlink(): number {
    if (this.state === 'sleep') return 1.0;
    
    if (this.blinkFrames > 0) {
      this.blinkFrames--;
      const half = this.cur.blinkDur / 2;
      const t = this.blinkFrames > half
        ? 1 - (this.blinkFrames - half) / half
        : this.blinkFrames / half;
      return Math.max(this.easeInOut(1 - t), this.cur.lidClose);
    }
    
    this.nextBlink--;
    if (this.nextBlink <= 0) {
      this.blinkFrames = Math.ceil(this.cur.blinkDur);
      this.nextBlink = Math.floor(this.cur.blinkEvery * (0.5 + Math.random()));
    }
    
    return this.cur.lidClose;
  }
  
  // ─────────────────────────────────────────────────────────────────
  //  DRAWING FUNCTIONS
  // ─────────────────────────────────────────────────────────────────
  
  private drawBackground(c: CanvasRenderingContext2D): void {
    c.fillStyle = '#09090e';
    c.fillRect(0, 0, this.W, this.H);
    
    const vg = c.createRadialGradient(this.W/2, this.H/2, 0, this.W/2, this.H/2, Math.max(this.W, this.H) * 0.72);
    vg.addColorStop(0, 'rgba(16,15,26,0.0)');
    vg.addColorStop(1, 'rgba(4,4,8,0.80)');
    c.fillStyle = vg;
    c.fillRect(0, 0, this.W, this.H);
    
    const bloom = c.createRadialGradient(this.W/2, this.H/2, 0, this.W/2, this.H/2, Math.min(this.W, this.H) * 0.6);
    bloom.addColorStop(0, this.rgba(this.cur.irisRGB, this.cur.irisGlow * 0.08));
    bloom.addColorStop(1, this.rgba(this.cur.irisRGB, 0));
    c.fillStyle = bloom;
    c.fillRect(0, 0, this.W, this.H);
  }
  
  private drawIris(c: CanvasRenderingContext2D, cx: number, cy: number, R: number): void {
    const glowG = c.createRadialGradient(cx, cy, R * 0.6, cx, cy, R * 1.8);
    glowG.addColorStop(0, this.rgba(this.cur.irisRGB, this.cur.irisGlow * 0.50));
    glowG.addColorStop(1, this.rgba(this.cur.irisRGB, 0));
    c.beginPath();
    c.arc(cx, cy, R * 1.8, 0, Math.PI * 2);
    c.fillStyle = glowG;
    c.fill();
    
    const mid: [number, number, number] = [
      (this.cur.irisRGB[0] + this.cur.irisEdgeRGB[0]) / 2,
      (this.cur.irisRGB[1] + this.cur.irisEdgeRGB[1]) / 2,
      (this.cur.irisRGB[2] + this.cur.irisEdgeRGB[2]) / 2
    ];
    const grad = c.createRadialGradient(cx - R * 0.18, cy - R * 0.18, R * 0.05, cx, cy, R);
    grad.addColorStop(0, this.rgb(this.cur.irisRGB));
    grad.addColorStop(0.55, this.rgb(mid));
    grad.addColorStop(1, this.rgb(this.cur.irisEdgeRGB));
    c.beginPath();
    c.arc(cx, cy, R, 0, Math.PI * 2);
    c.fillStyle = grad;
    c.fill();
    
    c.beginPath();
    c.arc(cx, cy, R, 0, Math.PI * 2);
    c.strokeStyle = this.rgba(this.cur.irisEdgeRGB, 0.55);
    c.lineWidth = R * 0.06;
    c.stroke();
  }
  
  private drawPupil(c: CanvasRenderingContext2D, cx: number, cy: number, R: number): void {
    const PR = R * 0.36 * this.cur.pupilScale;
    const maxF = R * 0.26 * this.cur.followStr;
    const dx = (this.mouseX - 0.5) * 2;
    const dy = (this.mouseY - 0.5) * 2;
    const ang = Math.atan2(dy, dx);
    const mag = Math.min(1, Math.sqrt(dx * dx + dy * dy));
    const driftX = this.state === 'thinking' ? Math.sin(this.thinkPhase * 0.6) * R * 0.06 : 0;
    const driftY = this.cur.pupilShiftY * R;
    const px = cx + Math.cos(ang) * mag * maxF + driftX;
    const py = cy + Math.sin(ang) * mag * maxF + driftY;
    
    const pg = c.createRadialGradient(px - PR * 0.3, py - PR * 0.3, PR * 0.05, px, py, PR);
    pg.addColorStop(0, '#242424');
    pg.addColorStop(1, '#050505');
    c.beginPath();
    c.arc(px, py, PR, 0, Math.PI * 2);
    c.fillStyle = pg;
    c.fill();
    
    c.beginPath();
    c.arc(px - PR * 0.30, py - PR * 0.30, PR * 0.20, 0, Math.PI * 2);
    c.fillStyle = 'rgba(255,255,255,0.50)';
    c.fill();
    
    c.beginPath();
    c.arc(px - PR * 0.46, py - PR * 0.44, PR * 0.09, 0, Math.PI * 2);
    c.fillStyle = 'rgba(255,255,255,0.88)';
    c.fill();
  }
  
  private drawLid(c: CanvasRenderingContext2D, cx: number, cy: number, R: number, closure: number): void {
    if (closure < 0.015) return;
    
    c.save();
    c.beginPath();
    c.arc(cx, cy, R + 1, 0, Math.PI * 2);
    c.clip();
    
    const lidY = cy - R + R * 2 * closure;
    const lidGrad = c.createLinearGradient(cx, cy - R, cx, lidY + 3);
    lidGrad.addColorStop(0, 'rgba(10,9,14,0.98)');
    lidGrad.addColorStop(0.88, 'rgba(18,16,24,0.96)');
    lidGrad.addColorStop(1, 'rgba(30,26,38,0.55)');
    c.fillStyle = lidGrad;
    c.fillRect(cx - R - 2, cy - R - 2, (R + 2) * 2, lidY - (cy - R) + 5);
    c.fill();
    
    c.beginPath();
    c.moveTo(cx - R, lidY);
    c.quadraticCurveTo(cx, lidY + R * 0.06 * closure, cx + R, lidY);
    c.strokeStyle = 'rgba(0,0,0,0.55)';
    c.lineWidth = 2.5;
    c.stroke();
    
    if (this.cur.lidClose > 0.12) {
      const ly2 = cy + R * (1 - closure * 0.45);
      c.beginPath();
      c.moveTo(cx - R * 0.8, ly2);
      c.quadraticCurveTo(cx, ly2 - R * 0.16 * closure, cx + R * 0.8, ly2);
      c.strokeStyle = 'rgba(255,255,255,0.05)';
      c.lineWidth = 1.8;
      c.stroke();
    }
    
    c.restore();
  }
  
  private drawBrow(c: CanvasRenderingContext2D, cx: number, cy: number, R: number): void {
    const baseY = cy - R - 24 + this.cur.browLift + this.autoBrowLiftOffset;
    const span = R * 0.62;
    const rad = (this.cur.browAngle + this.autoBrowAngleOffset) * Math.PI / 180;
    const liftL = -Math.sin(rad) * span;
    const liftR = Math.sin(rad) * span;
    const ctrlY = baseY - R * 0.12;
    
    c.save();
    c.shadowColor = 'rgba(0,0,0,0.45)';
    c.shadowBlur = 7;
    c.shadowOffsetY = 2;
    c.beginPath();
    c.moveTo(cx - span, baseY + liftL);
    c.quadraticCurveTo(cx, ctrlY, cx + span, baseY + liftR);
    c.strokeStyle = '#16100a';
    c.lineWidth = R * 0.14;
    c.lineCap = 'round';
    c.stroke();
    
    c.shadowBlur = 0;
    c.beginPath();
    c.moveTo(cx - span + 2, baseY + liftL - 2);
    c.quadraticCurveTo(cx, ctrlY - 2, cx + span - 2, baseY + liftR - 2);
    c.strokeStyle = 'rgba(50,40,28,0.45)';
    c.lineWidth = R * 0.04;
    c.stroke();
    c.restore();
  }
  
  private drawMouth(c: CanvasRenderingContext2D, cx: number, cy: number, R: number): void {
    const hw = R * this.cur.mouthW;
    const open = Math.min(1.0, this.cur.mouthOpen + this.autoMouthOpenOffset);
    const openH = R * this.cur.mouthH * open;
    const lw = R * 0.13;
    const wobble = this.cur.mouthWobble > 0.01
      ? Math.sin(this.thinkPhase * 3.1) * this.cur.mouthWobble * R * 0.10
      : 0;
    const talkMod = this.state === 'speaking'
      ? 0.5 + 0.5 * Math.abs(Math.sin(this.talkPhase))
      : 1.0;
    const effOpenH = openH * talkMod;
    const ctrlY = cy + wobble - R * (this.cur.mouthCurve + this.autoMouthCurveOffset) * 2.0;
    const lowerY = ctrlY + effOpenH * 2.4;
    const mColor = this.rgba(this.cur.irisRGB, 0.80);
    
    c.save();
    
    if (open > 0.06) {
      c.beginPath();
      c.moveTo(cx - hw, cy);
      c.quadraticCurveTo(cx, ctrlY, cx + hw, cy);
      c.quadraticCurveTo(cx, lowerY, cx - hw, cy);
      c.closePath();
      c.fillStyle = 'rgba(4,2,2,0.94)';
      c.fill();
      
      if ((this.cur.mouthCurve + this.autoMouthCurveOffset) > 0.06 && open > 0.28 && talkMod > 0.35) {
        const th = effOpenH * 0.40;
        c.save();
        c.beginPath();
        c.moveTo(cx - hw, cy);
        c.quadraticCurveTo(cx, ctrlY, cx + hw, cy);
        c.quadraticCurveTo(cx, lowerY, cx - hw, cy);
        c.clip();
        c.fillStyle = 'rgba(235,228,222,0.90)';
        c.fillRect(cx - hw, ctrlY, hw * 2, th + 2);
        c.restore();
      }
      
      c.beginPath();
      c.moveTo(cx - hw, cy);
      c.quadraticCurveTo(cx, ctrlY, cx + hw, cy);
      c.strokeStyle = mColor;
      c.lineWidth = lw;
      c.lineCap = 'round';
      c.stroke();
      
      c.beginPath();
      c.moveTo(cx - hw, cy);
      c.quadraticCurveTo(cx, lowerY, cx + hw, cy);
      c.strokeStyle = this.rgba(this.cur.irisRGB, 0.36);
      c.lineWidth = lw * 0.65;
      c.stroke();
    } else {
      c.beginPath();
      c.moveTo(cx - hw, cy + wobble);
      c.quadraticCurveTo(cx, ctrlY, cx + hw, cy + wobble);
      c.strokeStyle = mColor;
      c.lineWidth = lw;
      c.lineCap = 'round';
      c.shadowColor = this.rgba(this.cur.irisRGB, this.cur.irisGlow);
      c.shadowBlur = 10;
      c.stroke();
    }
    
    if ((this.cur.mouthCurve + this.autoMouthCurveOffset) > 0.14) {
      const da = Math.min(1, ((this.cur.mouthCurve + this.autoMouthCurveOffset) - 0.14) * 2.5) * 0.28;
      c.beginPath();
      c.arc(cx - hw - R * 0.16, cy + R * 0.04, R * 0.065, 0, Math.PI * 2);
      c.fillStyle = this.rgba(this.cur.irisRGB, da);
      c.fill();
      c.beginPath();
      c.arc(cx + hw + R * 0.16, cy + R * 0.04, R * 0.065, 0, Math.PI * 2);
      c.fill();
    }
    
    c.restore();
  }
  
  // ─────────────────────────────────────────────────────────────────
  //  ZZZ PARTICLES (sleep mode)
  // ─────────────────────────────────────────────────────────────────
  
  private spawnZzz(mouthX: number, mouthY: number): void {
    const sizes = ['Z', 'Z', 'z', 'Z', 'zz'];
    this.zzzParticles.push({
      x: mouthX + (Math.random() - 0.5) * 30,
      y: mouthY - 10,
      text: sizes[Math.floor(Math.random() * sizes.length)],
      size: 14 + Math.random() * 18,
      alpha: 0.0,
      life: 0,
      speed: 0.004 + Math.random() * 0.003,
      drift: (Math.random() - 0.5) * 0.6,
      fadeIn: 0.18,
    });
  }
  
  private updateDrawZzz(c: CanvasRenderingContext2D, mouthX: number, mouthY: number): void {
    if (this.state === 'sleep') {
      this.zzzSpawnTimer++;
      if (this.zzzSpawnTimer >= this.ZZZ_INTERVAL) {
        this.zzzSpawnTimer = 0;
        this.spawnZzz(mouthX, mouthY);
      }
    } else {
      this.zzzSpawnTimer = 0;
    }
    
    for (let i = this.zzzParticles.length - 1; i >= 0; i--) {
      const p = this.zzzParticles[i];
      p.life += p.speed;
      
      if (p.life < p.fadeIn) {
        p.alpha = p.life / p.fadeIn;
      } else {
        p.alpha = 1.0 - (p.life - p.fadeIn) / (1.0 - p.fadeIn);
      }
      
      p.y -= 0.5 + p.life * 1.2;
      p.x += p.drift + Math.sin(p.life * 8) * 0.4;
      p.size += 0.04;
      
      if (p.life >= 1.0 || p.alpha <= 0) {
        this.zzzParticles.splice(i, 1);
        continue;
      }
      
      const col = this.cur.irisRGB;
      c.save();
      c.globalAlpha = Math.max(0, p.alpha) * 0.85;
      c.font = `bold ${p.size|0}px 'SF Mono', 'Fira Code', 'Courier New', monospace`;
      c.fillStyle = `rgb(${col[0]|0},${col[1]|0},${col[2]|0})`;
      c.shadowColor = `rgba(${col[0]|0},${col[1]|0},${col[2]|0},0.6)`;
      c.shadowBlur = 12;
      c.textAlign = 'center';
      c.fillText(p.text, p.x, p.y);
      c.restore();
    }
  }
  
  // ─────────────────────────────────────────────────────────────────
  //  RENDER FACE TO OFFSCREEN
  // ─────────────────────────────────────────────────────────────────
  
  private renderFaceToOffscreen(): void {
    this.octx.clearRect(0, 0, this.W, this.H);
    this.drawBackground(this.octx);
    
    const R = Math.min(this.W, this.H) * 0.175;
    const GAP = R * 1.55;
    const sp = this.cur.motSpeed;
    const motY = Math.sin(this.beatPhase * sp) * this.cur.motY * R;
    const motX = Math.sin(this.beatPhase * sp * 0.61) * this.cur.motX * R;
    const tilt = Math.sin(this.beatPhase * sp * 0.39) * this.cur.motTilt;
    
    const fcx = this.W / 2 + motX;
    const fcy = this.H / 2 - R * 0.30 + motY;
    
    this.octx.save();
    this.octx.translate(fcx, fcy);
    this.octx.rotate(tilt);
    this.octx.translate(-fcx, -fcy);
    
    const eyes = [
      { cx: fcx - GAP, cy: fcy },
      { cx: fcx + GAP, cy: fcy },
    ];
    const mouthX = fcx;
    const mouthY = fcy + R * 1.65;
    const lid = this.tickBlink();
    
    for (const { cx, cy } of eyes) {
      this.drawIris(this.octx, cx, cy, R);
      this.drawPupil(this.octx, cx, cy, R);
      this.drawLid(this.octx, cx, cy, R, lid);
      this.drawBrow(this.octx, cx, cy, R);
    }
    this.drawMouth(this.octx, mouthX, mouthY, R);
    this.updateDrawZzz(this.octx, mouthX, mouthY);
    this.octx.restore();
    
    // Post-FX per state
    if (this.state === 'listening') {
      const p = 0.5 + 0.5 * Math.sin(this.frame * 0.055);
      for (const { cx, cy } of eyes) {
        this.octx.beginPath();
        this.octx.arc(cx, cy, R + 14 + p * 10, 0, Math.PI * 2);
        this.octx.strokeStyle = this.rgba([0, 200, 175], 0.10 + p * 0.09);
        this.octx.lineWidth = 2;
        this.octx.stroke();
      }
    }
    
    if (this.state === 'thinking') {
      for (let i = 0; i < 2; i++) {
        const { cx, cy } = eyes[i];
        const ph = this.thinkPhase * 0.48 + i * Math.PI;
        const orx = cx + Math.cos(ph) * R * 1.32;
        const ory = cy + Math.sin(ph) * R * 0.30;
        const a = 0.18 + 0.14 * Math.sin(this.thinkPhase + i);
        this.octx.beginPath();
        this.octx.arc(orx, ory, 3.5, 0, Math.PI * 2);
        this.octx.fillStyle = this.rgba([100, 120, 240], a);
        this.octx.fill();
      }
    }
    
    if (this.state === 'error') {
      const fl = 0.5 + 0.5 * Math.sin(this.frame * 0.16);
      for (const { cx, cy } of eyes) {
        this.octx.beginPath();
        this.octx.arc(cx, cy, R + 5, 0, Math.PI * 2);
        this.octx.strokeStyle = this.rgba([220, 55, 40], 0.18 + fl * 0.15);
        this.octx.lineWidth = 3;
        this.octx.stroke();
      }
    }
  }
  
  // ─────────────────────────────────────────────────────────────────
  //  DISTORTION PASS
  // ─────────────────────────────────────────────────────────────────
  
  private applyDistortion(): void {
    const amp = this.cur.distortAmp;
    const freq = this.cur.distortFreq;
    const t = this.distTime;
    this.ctx.clearRect(0, 0, this.W, this.H);
    
    if (amp < 0.15) {
      this.ctx.drawImage(this.offCanvas, 0, 0);
      return;
    }
    
    for (let y = 0; y < this.H; y += this.STRIPE) {
      const dx = amp * (
        Math.sin(y * freq * 1.0 + t * 2.1) * 0.55 +
        Math.sin(y * freq * 2.3 + t * 1.3 + 0.7) * 0.30 +
        Math.sin(y * freq * 5.1 + t * 3.7 + 1.4) * 0.15
      );
      const dy = amp * 0.25 * (
        Math.sin(y * freq * 0.8 + t * 1.8 + 2.0) * 0.6 +
        Math.sin(y * freq * 3.2 + t * 2.5 + 0.3) * 0.4
      );
      const srcY = Math.max(0, Math.min(this.H - this.STRIPE, y + dy));
      this.ctx.drawImage(this.offCanvas, 0, srcY, this.W, this.STRIPE, dx, y, this.W, this.STRIPE);
    }
    
    if (amp > 1.5) {
      this.ctx.save();
      this.ctx.globalCompositeOperation = 'screen';
      this.ctx.globalAlpha = Math.min(0.04, amp * 0.008);
      this.ctx.filter = 'hue-rotate(0deg) saturate(3)';
      this.ctx.drawImage(this.offCanvas, -amp * 0.6, 0, this.W, this.H);
      this.ctx.filter = 'hue-rotate(240deg) saturate(3)';
      this.ctx.drawImage(this.offCanvas, amp * 0.6, 0, this.W, this.H);
      this.ctx.filter = 'none';
      this.ctx.globalAlpha = 1;
      this.ctx.globalCompositeOperation = 'source-over';
      this.ctx.restore();
    }
  }
  
  // ─────────────────────────────────────────────────────────────────
  //  MAIN LOOP
  // ─────────────────────────────────────────────────────────────────
  
  private loop = (): void => {
    this.frame++;
    this.beatPhase += 0.017;
    this.thinkPhase += 0.038;
    this.talkPhase += 0.11;
    this.distTime += 0.016 * this.cur.distortSpeed;
    
    this.updateAutoPupil();
    this.updateAutoBrow();
    this.updateAutoMouth();
    this.updateLerps();
    this.renderFaceToOffscreen();
    this.applyDistortion();
    
    this.animationFrameId = requestAnimationFrame(this.loop);
  };
}
