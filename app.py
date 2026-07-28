import streamlit as st
import streamlit.components.v1 as components

st.set_page_config(
    page_title="Rock Paper Scissors Arena",
    page_icon="✊",
    layout="wide",
    initial_sidebar_state="collapsed",
)

st.markdown(
    """
    <style>
    #MainMenu {visibility: hidden;}
    header {visibility: hidden;}
    footer {visibility: hidden;}
    div.block-container {
        padding: 0 !important;
        margin: 0 !important;
        max-width: 100% !important;
    }
    section.main > div {
        padding: 0 !important;
    }
    iframe {
        position: fixed !important;
        top: 0 !important;
        left: 0 !important;
        width: 100vw !important;
        height: 100vh !important;
        border: none !important;
        z-index: 999999;
    }
    html, body {
        overflow: hidden !important;
        margin: 0 !important;
        padding: 0 !important;
        background: #ffffff !important;
    }
    </style>
    """,
    unsafe_allow_html=True,
)

GAME_HTML = """
<!DOCTYPE html>
<html>
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no, viewport-fit=cover">
<style>
  html, body {
    margin: 0;
    padding: 0;
    width: 100%;
    height: 100%;
    overflow: hidden;
    background: #ffffff;
    touch-action: none;
    -webkit-user-select: none;
    -webkit-touch-callout: none;
    user-select: none;
  }
  #gameRoot {
    position: fixed;
    inset: 0;
    width: 100vw;
    height: 100vh;
    display: block;
    background: #ffffff;
  }
  #gameCanvas {
    width: 100%;
    height: 100%;
    display: block;
    touch-action: none;
    cursor: pointer;
  }
</style>
</head>
<body>
<div id="gameRoot">
  <canvas id="gameCanvas"></canvas>
</div>
<script>
(function(){
  "use strict";

  var canvas = document.getElementById('gameCanvas');
  var ctx = canvas.getContext('2d');
  var root = document.getElementById('gameRoot');
  var W = 0, H = 0, DPR = window.devicePixelRatio || 1;

  function resize(){
    var rect = root.getBoundingClientRect();
    DPR = window.devicePixelRatio || 1;
    W = Math.max(1, rect.width);
    H = Math.max(1, rect.height);
    canvas.width = Math.round(W * DPR);
    canvas.height = Math.round(H * DPR);
    ctx.setTransform(DPR, 0, 0, DPR, 0, 0);
  }

  if (window.ResizeObserver) {
    new ResizeObserver(resize).observe(root);
  } else {
    window.addEventListener('resize', resize);
  }
  window.addEventListener('orientationchange', function(){ setTimeout(resize, 200); });
  window.addEventListener('load', resize);
  resize();

  // ---------------------------------------------------------------------
  // AUDIO ENGINE
  // ---------------------------------------------------------------------
  var audioCtx = null;
  var bgInterval = null;

  function setupAudio(){
    try {
      if (!audioCtx) {
        audioCtx = new (window.AudioContext || window.webkitAudioContext)();
      }
      if (audioCtx.state === 'suspended') {
        audioCtx.resume();
      }
    } catch (e) {
      audioCtx = null;
    }
  }

  function sound(type){
    if (!audioCtx) return;
    var now = audioCtx.currentTime;

    if (type === 'snap') {
      // Sharp physical cloth snap / slap: high-frequency bandpass + ultra-fast decay
      var osc = audioCtx.createOscillator();
      osc.type = 'square';
      osc.frequency.setValueAtTime(1600, now);
      osc.frequency.exponentialRampToValueAtTime(900, now + 0.04);

      var band = audioCtx.createBiquadFilter();
      band.type = 'bandpass';
      band.frequency.value = 1200;
      band.Q.value = 9;

      var g = audioCtx.createGain();
      g.gain.setValueAtTime(0.55, now);
      g.gain.exponentialRampToValueAtTime(0.001, now + 0.04);

      osc.connect(band);
      band.connect(g);
      g.connect(audioCtx.destination);
      osc.start(now);
      osc.stop(now + 0.05);

    } else if (type === 'thud') {
      // Heavy organic impact: low triangle sweep 150Hz -> 30Hz + low-pass white noise burst
      var tOsc = audioCtx.createOscillator();
      tOsc.type = 'triangle';
      tOsc.frequency.setValueAtTime(150, now);
      tOsc.frequency.exponentialRampToValueAtTime(30, now + 0.30);

      var tGain = audioCtx.createGain();
      tGain.gain.setValueAtTime(0.85, now);
      tGain.gain.exponentialRampToValueAtTime(0.001, now + 0.35);

      tOsc.connect(tGain);
      tGain.connect(audioCtx.destination);
      tOsc.start(now);
      tOsc.stop(now + 0.36);

      var bufferSize = Math.floor(audioCtx.sampleRate * 0.35);
      var buffer = audioCtx.createBuffer(1, bufferSize, audioCtx.sampleRate);
      var data = buffer.getChannelData(0);
      for (var i = 0; i < bufferSize; i++) {
        data[i] = (Math.random() * 2 - 1) * (1 - i / bufferSize);
      }
      var noise = audioCtx.createBufferSource();
      noise.buffer = buffer;

      var low = audioCtx.createBiquadFilter();
      low.type = 'lowpass';
      low.frequency.value = 350;

      var nGain = audioCtx.createGain();
      nGain.gain.setValueAtTime(0.5, now);
      nGain.gain.exponentialRampToValueAtTime(0.001, now + 0.35);

      noise.connect(low);
      low.connect(nGain);
      nGain.connect(audioCtx.destination);
      noise.start(now);
    }
  }

  function startBgMusic(){
    if (bgInterval || !audioCtx) return;
    var pattern = [220, 0, 262, 220, 0, 330, 262, 0, 220, 0, 294, 262];
    var step = 0;
    bgInterval = setInterval(function(){
      if (!audioCtx) return;
      var freq = pattern[step % pattern.length];
      step++;
      if (freq > 0) {
        var now = audioCtx.currentTime;
        var osc = audioCtx.createOscillator();
        osc.type = 'square';
        osc.frequency.value = freq;
        var g = audioCtx.createGain();
        g.gain.setValueAtTime(0.06, now);
        g.gain.exponentialRampToValueAtTime(0.001, now + 0.14);
        osc.connect(g);
        g.connect(audioCtx.destination);
        osc.start(now);
        osc.stop(now + 0.15);
      }
    }, 165);
  }

  function stopBgMusic(){
    if (bgInterval) {
      clearInterval(bgInterval);
      bgInterval = null;
    }
  }

  // ---------------------------------------------------------------------
  // GAME STATE
  // ---------------------------------------------------------------------
  var game = {
    state: 'loading',           // loading | menu | battle | victory | defeat
    battlePhase: 'select',      // select | clash | result
    difficulty: 'EASY',
    playerHP: 3,
    compHP: 3,
    playerHistory: [],
    playerWinMoves: [],
    selectedMove: null,
    compMove: null,
    clashStart: 0,
    clashDuration: 1500,
    resultStart: 0,
    resultMessage: '',
    impactTriggered: false,
    particles: [],
    shake: 0,
    hoverSlot: null,
    diffButtons: [],
    enterButton: null,
    weaponSlots: [],
    retryButton: null
  };

  var BEATS = { rock: 'scissors', scissors: 'paper', paper: 'rock' };
  var COUNTER = { scissors: 'rock', paper: 'scissors', rock: 'paper' };
  var LABELS = { rock: '✊ ROCK', paper: '✋ PAPER', scissors: '✌️ SCISSORS' };

  function randomMove(){
    var m = ['rock', 'paper', 'scissors'];
    return m[Math.floor(Math.random() * 3)];
  }

  function countFreq(arr){
    var f = { rock: 0, paper: 0, scissors: 0 };
    for (var i = 0; i < arr.length; i++) f[arr[i]]++;
    return f;
  }

  function mostFrequent(freq){
    var best = null, bestCount = -1;
    var keys = ['rock', 'paper', 'scissors'];
    for (var i = 0; i < keys.length; i++) {
      if (freq[keys[i]] > bestCount) {
        bestCount = freq[keys[i]];
        best = keys[i];
      }
    }
    return best;
  }

  function computerChoose(){
    if (game.difficulty === 'EASY') {
      return randomMove();
    }
    if (game.difficulty === 'MEDIUM') {
      if (game.playerHistory.length === 0) return randomMove();
      var recent = game.playerHistory.slice(-6);
      var predicted = mostFrequent(countFreq(recent));
      return COUNTER[predicted];
    }
    if (game.difficulty === 'HARD') {
      var source = game.playerWinMoves.length > 0 ? game.playerWinMoves : game.playerHistory;
      if (source.length === 0) return randomMove();
      var predictedBias = mostFrequent(countFreq(source));
      return COUNTER[predictedBias];
    }
    return randomMove();
  }

  function resolveRound(playerMove, compMove){
    if (playerMove === compMove) return 'tie';
    if (BEATS[playerMove] === compMove) return 'player';
    return 'computer';
  }

  function applyOutcome(outcome){
    if (outcome === 'player') {
      game.compHP = Math.max(0, game.compHP - 1);
      game.resultMessage = 'YOU WIN THE CLASH!';
      game.playerWinMoves.push(game.selectedMove);
    } else if (outcome === 'computer') {
      game.playerHP = Math.max(0, game.playerHP - 1);
      game.resultMessage = 'COMPUTER WINS THE CLASH!';
    } else {
      game.resultMessage = "IT'S A TIE!";
    }
  }

  function startBattle(){
    game.playerHP = 3;
    game.compHP = 3;
    game.playerHistory = [];
    game.playerWinMoves = [];
    game.selectedMove = null;
    game.compMove = null;
    game.particles = [];
    game.shake = 0;
    game.state = 'battle';
    game.battlePhase = 'select';
    startBgMusic();
  }

  function chooseMove(move){
    game.selectedMove = move;
    game.playerHistory.push(move);
    game.compMove = computerChoose();
    game.battlePhase = 'clash';
    game.clashStart = performance.now();
    game.impactTriggered = false;
  }

  function resetGame(){
    stopBgMusic();
    game.state = 'menu';
    game.battlePhase = 'select';
  }

  // ---------------------------------------------------------------------
  // PARTICLES / SCREEN SHAKE
  // ---------------------------------------------------------------------
  function spawnParticles(cx, cy, count){
    for (var i = 0; i < count; i++) {
      var angle = (Math.PI * 2 * i / count) + (Math.random() * 0.35 - 0.175);
      var speed = 2.2 + Math.random() * 3.2;
      game.particles.push({
        x: cx, y: cy,
        vx: Math.cos(angle) * speed,
        vy: Math.sin(angle) * speed,
        life: 1
      });
    }
  }

  function updateAndDrawParticles(dt){
    var factor = Math.min(2.5, dt / 16.67);
    for (var i = game.particles.length - 1; i >= 0; i--) {
      var p = game.particles[i];
      p.x += p.vx * factor;
      p.y += p.vy * factor;
      p.vx *= 0.93;
      p.vy *= 0.93;
      p.life -= 0.028 * factor;
      if (p.life <= 0) {
        game.particles.splice(i, 1);
        continue;
      }
      ctx.fillStyle = 'rgba(0,0,0,' + Math.max(0, p.life).toFixed(2) + ')';
      var s = 5 * p.life + 1;
      ctx.fillRect(p.x - s / 2, p.y - s / 2, s, s);
    }
  }

  // ---------------------------------------------------------------------
  // DRAWING HELPERS
  // ---------------------------------------------------------------------
  function lerp(a, b, t){ return a + (b - a) * t; }
  function clamp(v, a, b){ return Math.max(a, Math.min(b, v)); }
  function easeOutCubic(t){ t = clamp(t, 0, 1); return 1 - Math.pow(1 - t, 3); }

  function roundRectPath(c, x, y, w, h, r){
    c.beginPath();
    c.moveTo(x + r, y);
    c.arcTo(x + w, y, x + w, y + h, r);
    c.arcTo(x + w, y + h, x, y + h, r);
    c.arcTo(x, y + h, x, y, r);
    c.arcTo(x, y, x + w, y, r);
    c.closePath();
  }

  // A single tapered finger, drawn in LOCAL space with its base at (0,0)
  // and its tip pointing toward -y (straight up) before any rotation is
  // applied by the caller. Knuckle creases are drawn at the given
  // fractional positions along its length (0 = base, 1 = tip).
  function drawFingerLocal(c, length, wBase, wTip, joints, shadowOn){
    var hwB = wBase / 2, hwT = wTip / 2;
    c.beginPath();
    c.moveTo(-hwB, 0);
    c.quadraticCurveTo(-hwB * 0.96, -length * 0.42, -hwT * 1.05, -length * 0.82);
    c.quadraticCurveTo(-hwT * 0.7, -length, 0, -length);
    c.quadraticCurveTo(hwT * 0.7, -length, hwT * 1.05, -length * 0.82);
    c.quadraticCurveTo(hwB * 0.96, -length * 0.42, hwB, 0);
    c.closePath();
    c.fill(); c.stroke();

    if (joints && joints.length) {
      c.save();
      if (!shadowOn) { c.shadowColor = 'transparent'; c.shadowBlur = 0; c.shadowOffsetY = 0; }
      var savedWidth = c.lineWidth;
      c.lineWidth = Math.max(1.5, savedWidth * 0.55);
      c.strokeStyle = 'rgba(0,0,0,0.55)';
      for (var i = 0; i < joints.length; i++) {
        var f = joints[i];
        var yy = -length * f;
        var ww = (hwB + (hwT - hwB) * f) * 0.8;
        c.beginPath();
        c.moveTo(-ww, yy);
        c.quadraticCurveTo(0, yy + length * 0.035, ww, yy);
        c.stroke();
      }
      c.restore();
    }
  }

  // Places a finger at (x,y) in the hand's local space, rotated by angle
  // (radians, 0 = straight up, positive = tilts toward +x/right).
  function drawFingerAt(c, x, y, angle, length, wBase, wTip, joints, shadowOn){
    c.save();
    c.translate(x, y);
    c.rotate(angle);
    drawFingerLocal(c, length, wBase, wTip, joints, shadowOn);
    c.restore();
  }

  // A short rounded bump representing the visible top of a curled finger
  // (used on the fist and for the tucked-in fingers on the scissors hand).
  function drawKnuckleBump(c, x, y, w, h, shadowOn){
    c.beginPath();
    c.moveTo(x - w / 2, y + h * 0.35);
    c.quadraticCurveTo(x - w / 2, y - h * 0.55, x, y - h * 0.6);
    c.quadraticCurveTo(x + w / 2, y - h * 0.55, x + w / 2, y + h * 0.35);
    c.lineTo(x - w / 2, y + h * 0.35);
    c.closePath();
    c.fill(); c.stroke();

    c.save();
    if (!shadowOn) { c.shadowColor = 'transparent'; c.shadowBlur = 0; c.shadowOffsetY = 0; }
    var savedWidth = c.lineWidth;
    c.lineWidth = Math.max(1.5, savedWidth * 0.5);
    c.strokeStyle = 'rgba(0,0,0,0.5)';
    c.beginPath();
    c.moveTo(x - w * 0.32, y - h * 0.05);
    c.quadraticCurveTo(x, y + h * 0.03, x + w * 0.32, y - h * 0.05);
    c.stroke();
    c.restore();
  }

  // A soft curved crease line (palm lines, wrist lines) with no shadow.
  function drawCrease(c, x1, y1, cx1, cy1, x2, y2, weight){
    c.save();
    c.shadowColor = 'transparent';
    c.shadowBlur = 0;
    c.shadowOffsetY = 0;
    var savedWidth = c.lineWidth;
    c.lineWidth = Math.max(1.2, savedWidth * weight);
    c.strokeStyle = 'rgba(0,0,0,0.4)';
    c.beginPath();
    c.moveTo(x1, y1);
    c.quadraticCurveTo(cx1, cy1, x2, y2);
    c.stroke();
    c.restore();
  }

  function beginHand(c, cx, cy, size, flip, shadow){
    c.save();
    c.translate(cx, cy);
    if (flip) c.scale(-1, 1);
    if (shadow) {
      c.shadowColor = 'rgba(0,0,0,0.45)';
      c.shadowBlur = size * 0.14;
      c.shadowOffsetY = size * 0.07;
    }
    c.fillStyle = '#ffffff';
    c.strokeStyle = '#000000';
    c.lineWidth = Math.max(2.5, size * 0.032);
    c.lineJoin = 'round';
    c.lineCap = 'round';
  }

  function drawWrist(c, size){
    c.beginPath();
    c.moveTo(-size * 0.17, size * 0.32);
    c.lineTo(size * 0.17, size * 0.32);
    c.quadraticCurveTo(size * 0.19, size * 0.22, size * 0.20, size * 0.13);
    c.lineTo(-size * 0.20, size * 0.13);
    c.quadraticCurveTo(-size * 0.19, size * 0.22, -size * 0.17, size * 0.32);
    c.closePath();
    c.fill(); c.stroke();
  }

  // ROCK — a closed fist: wrist, rounded knuckle mound, four curled
  // finger-top bumps with knuckle creases, and a thumb wrapping the front.
  function drawFistHand(c, cx, cy, size, flip, shadow){
    beginHand(c, cx, cy, size, flip, shadow);

    drawWrist(c, size);

    c.beginPath();
    c.moveTo(-size * 0.30, size * 0.13);
    c.bezierCurveTo(-size * 0.40, -size * 0.02, -size * 0.36, -size * 0.20, -size * 0.20, -size * 0.24);
    c.lineTo(size * 0.24, -size * 0.24);
    c.bezierCurveTo(size * 0.38, -size * 0.20, size * 0.40, -size * 0.02, size * 0.30, size * 0.13);
    c.closePath();
    c.fill(); c.stroke();

    var bumpXs = [-0.235, -0.075, 0.085, 0.235];
    for (var i = 0; i < bumpXs.length; i++) {
      drawKnuckleBump(c, size * bumpXs[i], -size * 0.24, size * 0.165, size * 0.24, shadow);
    }

    drawFingerAt(c, -size * 0.31, size * 0.08, 1.12, size * 0.40, size * 0.185, size * 0.135, [0.55], shadow);

    drawCrease(c, -size * 0.10, size * 0.26, 0, size * 0.29, size * 0.10, size * 0.26, 0.4);
    drawCrease(c, -size * 0.14, size * 0.03, -size * 0.02, size * 0.10, size * 0.10, size * 0.02, 0.35);

    c.restore();
  }

  // SCISSORS — index and middle fingers fully extended in a V (each with
  // two knuckle creases), ring and pinky curled into bumps, thumb tucked
  // across the front.
  function drawScissorsHandShape(c, cx, cy, size, flip, shadow){
    beginHand(c, cx, cy, size, flip, shadow);

    drawWrist(c, size);

    c.beginPath();
    c.ellipse(0.02 * size, size * 0.02, size * 0.27, size * 0.17, 0, 0, Math.PI * 2);
    c.fill(); c.stroke();

    drawKnuckleBump(c, size * 0.20, -size * 0.06, size * 0.15, size * 0.20, shadow);
    drawKnuckleBump(c, size * 0.335, -size * 0.02, size * 0.145, size * 0.19, shadow);

    drawFingerAt(c, -size * 0.30, size * 0.06, 1.02, size * 0.34, size * 0.18, size * 0.13, [0.55], shadow);

    drawFingerAt(c, -size * 0.10, -size * 0.13, -0.24, size * 0.66, size * 0.15, size * 0.095, [0.42, 0.74], shadow);
    drawFingerAt(c, size * 0.05, -size * 0.13, 0.16, size * 0.70, size * 0.155, size * 0.10, [0.42, 0.74], shadow);

    drawCrease(c, -size * 0.08, size * 0.14, 0.02 * size, size * 0.18, size * 0.14, size * 0.10, 0.35);

    c.restore();
  }

  // PAPER — an open palm with five distinct, individually tapered fingers
  // fanned out (varied lengths), a thumb to the side, knuckle creases on
  // every finger, and soft palm-line creases.
  function drawPaperHandShape(c, cx, cy, size, flip, shadow){
    beginHand(c, cx, cy, size, flip, shadow);

    drawWrist(c, size);

    c.beginPath();
    c.moveTo(-size * 0.28, size * 0.13);
    c.quadraticCurveTo(-size * 0.34, -size * 0.02, -size * 0.27, -size * 0.16);
    c.quadraticCurveTo(-size * 0.20, -size * 0.24, -size * 0.06, -size * 0.24);
    c.lineTo(size * 0.20, -size * 0.24);
    c.quadraticCurveTo(size * 0.33, -size * 0.22, size * 0.32, -size * 0.06);
    c.quadraticCurveTo(size * 0.31, size * 0.06, size * 0.28, size * 0.13);
    c.closePath();
    c.fill(); c.stroke();

    // pinky, ring, middle, index — varied lengths for a natural fan
    drawFingerAt(c, -size * 0.245, -size * 0.225, -0.36, size * 0.42, size * 0.085, size * 0.052, [0.4, 0.76], shadow);
    drawFingerAt(c, -size * 0.095, -size * 0.245, -0.13, size * 0.56, size * 0.095, size * 0.056, [0.4, 0.76], shadow);
    drawFingerAt(c, size * 0.065, -size * 0.245, 0.07, size * 0.62, size * 0.10, size * 0.06, [0.4, 0.76], shadow);
    drawFingerAt(c, size * 0.205, -size * 0.22, 0.30, size * 0.50, size * 0.09, size * 0.055, [0.4, 0.76], shadow);

    // thumb — shorter, thicker, angled out to the side
    drawFingerAt(c, -size * 0.30, size * 0.02, -0.95, size * 0.34, size * 0.135, size * 0.085, [0.5], shadow);

    drawCrease(c, -size * 0.14, size * 0.02, 0, size * 0.09, size * 0.16, -size * 0.01, 0.4);
    drawCrease(c, -size * 0.16, size * 0.13, -size * 0.02, size * 0.16, size * 0.15, size * 0.11, 0.35);

    c.restore();
  }

  function drawHandForMove(move, c, x, y, size, flip, shadow){
    if (move === 'rock') drawFistHand(c, x, y, size, flip, shadow);
    else if (move === 'scissors') drawScissorsHandShape(c, x, y, size, flip, shadow);
    else drawPaperHandShape(c, x, y, size, flip, shadow);
  }

  // ---------------------------------------------------------------------
  // SCREEN DRAWERS
  // ---------------------------------------------------------------------
  function drawLoading(t){
    ctx.fillStyle = '#ffffff';
    ctx.fillRect(0, 0, W, H);

    ctx.textAlign = 'center';
    ctx.fillStyle = '#dc2626';
    var titleSize = Math.max(24, Math.min(W * 0.075, H * 0.09));
    ctx.font = '900 ' + titleSize + 'px "Arial Black", Arial, sans-serif';
    ctx.fillText('ROCK PAPER SCISSORS', W / 2, H * 0.16);

    var handSize = Math.min(W, H) * 0.24;
    drawFistHand(ctx, W * 0.32, H * 0.48, handSize, false, false);
    drawScissorsHandShape(ctx, W * 0.68, H * 0.48, handSize, true, false);

    var alpha = (Math.sin(t / 400) + 1) / 2;
    ctx.fillStyle = 'rgba(0,0,0,' + alpha.toFixed(3) + ')';
    var promptSize = Math.max(13, W * 0.022);
    ctx.font = '700 ' + promptSize + 'px Arial, sans-serif';
    ctx.fillText('TAP ON SCREEN TO CONTINUE', W / 2, H * 0.82);
  }

  function drawMenu(){
    ctx.fillStyle = '#ffffff';
    ctx.fillRect(0, 0, W, H);

    ctx.textAlign = 'center';
    ctx.fillStyle = '#111111';
    ctx.font = '900 ' + Math.max(20, W * 0.04) + 'px "Arial Black", Arial, sans-serif';
    ctx.fillText('SELECT DIFFICULTY', W / 2, H * 0.20);

    var diffs = ['EASY', 'MEDIUM', 'HARD'];
    var btnW = Math.min(210, W * 0.26);
    var btnH = Math.max(48, H * 0.075);
    var gap = W * 0.03;
    var totalW = diffs.length * btnW + (diffs.length - 1) * gap;
    var startX = W / 2 - totalW / 2;
    var y = H * 0.30;
    game.diffButtons = [];

    for (var i = 0; i < diffs.length; i++) {
      var d = diffs[i];
      var x = startX + i * (btnW + gap);
      var selected = game.difficulty === d;
      ctx.fillStyle = selected ? '#dc2626' : '#ffffff';
      ctx.strokeStyle = '#000000';
      ctx.lineWidth = 4;
      roundRectPath(ctx, x, y, btnW, btnH, 10);
      ctx.fill(); ctx.stroke();
      ctx.fillStyle = selected ? '#ffffff' : '#111111';
      ctx.font = '800 ' + Math.max(15, btnW * 0.15) + 'px Arial, sans-serif';
      ctx.fillText(d, x + btnW / 2, y + btnH / 2);
      game.diffButtons.push({ x: x, y: y, w: btnW, h: btnH, value: d });
    }

    var descs = {
      EASY: 'Computer picks completely at random.',
      MEDIUM: 'Computer studies your move history to guess your next move.',
      HARD: 'Computer predicts and counters your winning patterns.'
    };
    ctx.fillStyle = '#555555';
    ctx.font = '500 ' + Math.max(12, W * 0.017) + 'px Arial, sans-serif';
    ctx.fillText(descs[game.difficulty], W / 2, y + btnH + H * 0.05);

    var eW = Math.min(340, W * 0.42);
    var eH = Math.max(58, H * 0.09);
    var ex = W / 2 - eW / 2;
    var ey = H * 0.58;
    ctx.fillStyle = '#dc2626';
    ctx.strokeStyle = '#000000';
    ctx.lineWidth = 4;
    roundRectPath(ctx, ex, ey, eW, eH, 14);
    ctx.fill(); ctx.stroke();
    ctx.fillStyle = '#ffffff';
    ctx.font = '900 ' + Math.max(17, eW * 0.088) + 'px Arial, sans-serif';
    ctx.fillText('ENTER THE ARENA 🔥', ex + eW / 2, ey + eH / 2);
    game.enterButton = { x: ex, y: ey, w: eW, h: eH };
  }

  function drawHealthBar(x, y, w, h, hp, maxHp, label, align){
    ctx.textAlign = align === 'left' ? 'left' : 'right';
    ctx.fillStyle = '#111111';
    ctx.font = '800 ' + Math.max(12, h * 0.55) + 'px Arial, sans-serif';
    ctx.fillText(label, align === 'left' ? x : x + w, y - h * 0.35);

    ctx.strokeStyle = '#000000';
    ctx.lineWidth = 3;
    ctx.strokeRect(x, y, w, h);

    var frac = hp / maxHp;
    var color = frac > 0.66 ? '#16a34a' : (frac > 0.33 ? '#eab308' : '#dc2626');
    ctx.fillStyle = color;
    var fillW = w * frac;
    if (align === 'left') {
      ctx.fillRect(x, y, fillW, h);
    } else {
      ctx.fillRect(x + w - fillW, y, fillW, h);
    }
    ctx.strokeRect(x, y, w, h);
  }

  function drawWeaponSlots(){
    var slots = [
      { value: 'rock', label: '✊ ROCK' },
      { value: 'paper', label: '✋ PAPER' },
      { value: 'scissors', label: '✌️ SCISSORS' }
    ];
    var r = Math.min(W, H) * 0.085;
    var gap = W * 0.05;
    var totalW = slots.length * r * 2 + (slots.length - 1) * gap;
    var startX = W / 2 - totalW / 2 + r;
    var cy = H * 0.85;
    game.weaponSlots = [];

    for (var i = 0; i < slots.length; i++) {
      var s = slots[i];
      var cx = startX + i * (r * 2 + gap);
      var hovered = game.hoverSlot === s.value;
      ctx.beginPath();
      ctx.arc(cx, cy, r, 0, Math.PI * 2);
      ctx.fillStyle = '#ffffff';
      ctx.strokeStyle = hovered ? '#dc2626' : '#000000';
      ctx.lineWidth = hovered ? 6 : 4;
      ctx.fill(); ctx.stroke();
      ctx.fillStyle = '#111111';
      ctx.textAlign = 'center';
      ctx.font = '700 ' + Math.max(13, r * 0.24) + 'px Arial, sans-serif';
      ctx.fillText(s.label, cx, cy);
      game.weaponSlots.push({ cx: cx, cy: cy, r: r, value: s.value });
    }
  }

  function moveLabel(m){ return LABELS[m]; }

  function drawClashAnimation(t){
    var progress = clamp((t - game.clashStart) / game.clashDuration, 0, 1);
    var ease = easeOutCubic(progress / 0.6);
    var startOffset = W * 0.62;
    var leftX = lerp(W * 0.5 - startOffset, W * 0.32, ease);
    var rightX = lerp(W * 0.5 + startOffset, W * 0.68, ease);
    var handSize = Math.min(W, H) * 0.24;

    drawHandForMove(game.selectedMove, ctx, leftX, H * 0.42, handSize, false, true);
    drawHandForMove(game.compMove, ctx, rightX, H * 0.42, handSize, true, true);

    if (progress >= 0.55) {
      ctx.textAlign = 'center';
      ctx.fillStyle = '#000000';
      ctx.font = '900 ' + Math.max(15, W * 0.028) + 'px Arial, sans-serif';
      ctx.fillText(moveLabel(game.selectedMove) + '  VS  ' + moveLabel(game.compMove), W / 2, H * 0.70);
    }
  }

  function drawResultBanner(){
    ctx.textAlign = 'center';
    ctx.fillStyle = game.resultMessage.indexOf('YOU WIN') === 0 ? '#16a34a'
                    : (game.resultMessage.indexOf('COMPUTER') === 0 ? '#dc2626' : '#555555');
    ctx.font = '900 ' + Math.max(18, W * 0.035) + 'px "Arial Black", Arial, sans-serif';
    ctx.fillText(game.resultMessage, W / 2, H * 0.68);
  }

  function drawBattle(t, dt){
    ctx.save();
    if (game.shake > 0) {
      var sx = (Math.random() * 2 - 1) * game.shake;
      var sy = (Math.random() * 2 - 1) * game.shake;
      ctx.translate(sx, sy);
      game.shake = Math.max(0, game.shake - dt * 0.03);
    }

    ctx.fillStyle = '#ffffff';
    ctx.fillRect(-30, -30, W + 60, H + 60);
    ctx.strokeStyle = '#000000';
    ctx.lineWidth = 6;
    ctx.strokeRect(3, 3, W - 6, H - 6);

    drawHealthBar(W * 0.05, H * 0.09, W * 0.36, H * 0.055, game.playerHP, 3, 'YOU', 'left');
    drawHealthBar(W * 0.59, H * 0.09, W * 0.36, H * 0.055, game.compHP, 3, 'CPU', 'right');

    if (game.battlePhase === 'select') {
      drawWeaponSlots();
    } else if (game.battlePhase === 'clash') {
      drawClashAnimation(t);
    } else if (game.battlePhase === 'result') {
      drawWeaponSlots();
      drawResultBanner();
    }

    updateAndDrawParticles(dt);
    ctx.restore();
  }

  function drawVictory(){
    ctx.fillStyle = '#f5b300';
    ctx.fillRect(0, 0, W, H);
    ctx.textAlign = 'center';
    ctx.fillStyle = '#111111';
    ctx.font = '900 ' + Math.max(24, W * 0.055) + 'px "Arial Black", Arial, sans-serif';
    ctx.fillText('🔥 ARENA CONQUERED', W / 2, H * 0.40);
    ctx.font = '900 ' + Math.max(20, W * 0.045) + 'px "Arial Black", Arial, sans-serif';
    ctx.fillText('VICTORY', W / 2, H * 0.50);
    drawRetryButton('PLAY AGAIN 🔥', '#111111');
  }

  function drawDefeat(){
    ctx.fillStyle = '#dc2626';
    ctx.fillRect(0, 0, W, H);
    ctx.textAlign = 'center';
    ctx.fillStyle = '#ffffff';
    ctx.font = '900 ' + Math.max(24, W * 0.055) + 'px "Arial Black", Arial, sans-serif';
    ctx.fillText('🐋 ELIMINATED', W / 2, H * 0.38);
    ctx.font = '900 ' + Math.max(20, W * 0.045) + 'px "Arial Black", Arial, sans-serif';
    ctx.fillText('WASTED', W / 2, H * 0.48);
    drawRetryButton('RE-ENTER COMBAT 🔄', '#ffffff');
  }

  function drawRetryButton(label, textColor){
    var bW = Math.min(320, W * 0.42);
    var bH = Math.max(54, H * 0.085);
    var bx = W / 2 - bW / 2;
    var by = H * 0.62;
    ctx.fillStyle = '#ffffff';
    ctx.strokeStyle = textColor;
    ctx.lineWidth = 4;
    roundRectPath(ctx, bx, by, bW, bH, 14);
    ctx.fill(); ctx.stroke();
    ctx.fillStyle = textColor;
    ctx.textAlign = 'center';
    ctx.font = '800 ' + Math.max(15, bW * 0.085) + 'px Arial, sans-serif';
    ctx.fillText(label, bx + bW / 2, by + bH / 2);
    game.retryButton = { x: bx, y: by, w: bW, h: bH };
  }

  // ---------------------------------------------------------------------
  // MAIN LOOP
  // ---------------------------------------------------------------------
  function update(t, dt){
    if (game.state === 'battle') {
      if (game.battlePhase === 'clash') {
        var progress = clamp((t - game.clashStart) / game.clashDuration, 0, 1);
        if (progress >= 0.5 && !game.impactTriggered) {
          game.impactTriggered = true;
          spawnParticles(W / 2, H * 0.42, 15);
          game.shake = 18;
          sound('thud');
        }
        if (progress >= 1) {
          game.battlePhase = 'result';
          game.resultStart = t;
          var outcome = resolveRound(game.selectedMove, game.compMove);
          applyOutcome(outcome);
        }
      } else if (game.battlePhase === 'result') {
        if (t - game.resultStart > 1100) {
          if (game.playerHP <= 0) {
            stopBgMusic();
            game.state = 'defeat';
          } else if (game.compHP <= 0) {
            stopBgMusic();
            game.state = 'victory';
          } else {
            game.battlePhase = 'select';
          }
        }
      }
    }
  }

  function draw(t, dt){
    ctx.textBaseline = 'middle';
    ctx.clearRect(0, 0, W, H);
    if (game.state === 'loading') drawLoading(t);
    else if (game.state === 'menu') drawMenu();
    else if (game.state === 'battle') drawBattle(t, dt);
    else if (game.state === 'victory') drawVictory();
    else if (game.state === 'defeat') drawDefeat();
  }

  var lastT = performance.now();
  function loop(t){
    var dt = t - lastT;
    lastT = t;
    update(t, dt);
    draw(t, dt);
    requestAnimationFrame(loop);
  }
  requestAnimationFrame(loop);

  // ---------------------------------------------------------------------
  // INPUT HANDLING
  // ---------------------------------------------------------------------
  function pointFromEvent(e){
    var rect = canvas.getBoundingClientRect();
    return { x: e.clientX - rect.left, y: e.clientY - rect.top };
  }

  function hitButton(b, x, y){
    return b && x >= b.x && x <= b.x + b.w && y >= b.y && y <= b.y + b.h;
  }

  canvas.addEventListener('pointerdown', function(e){
    setupAudio();
    var p = pointFromEvent(e);
    var x = p.x, y = p.y;

    if (game.state === 'loading') {
      sound('snap');
      game.state = 'menu';
      return;
    }

    if (game.state === 'menu') {
      for (var i = 0; i < game.diffButtons.length; i++) {
        if (hitButton(game.diffButtons[i], x, y)) {
          sound('snap');
          game.difficulty = game.diffButtons[i].value;
          return;
        }
      }
      if (hitButton(game.enterButton, x, y)) {
        sound('snap');
        startBattle();
        return;
      }
      return;
    }

    if (game.state === 'battle' && game.battlePhase === 'select') {
      for (var j = 0; j < game.weaponSlots.length; j++) {
        var s = game.weaponSlots[j];
        var dx = x - s.cx, dy = y - s.cy;
        if (dx * dx + dy * dy <= s.r * s.r) {
          sound('snap');
          chooseMove(s.value);
          return;
        }
      }
      return;
    }

    if (game.state === 'victory' || game.state === 'defeat') {
      if (hitButton(game.retryButton, x, y)) {
        sound('snap');
        resetGame();
      }
      return;
    }
  });

  canvas.addEventListener('pointermove', function(e){
    if (game.state === 'battle' && game.battlePhase === 'select') {
      var p = pointFromEvent(e);
      game.hoverSlot = null;
      for (var i = 0; i < game.weaponSlots.length; i++) {
        var s = game.weaponSlots[i];
        var dx = p.x - s.cx, dy = p.y - s.cy;
        if (dx * dx + dy * dy <= s.r * s.r) {
          game.hoverSlot = s.value;
          break;
        }
      }
    }
  });

})();
</script>
</body>
</html>
"""

components.html(GAME_HTML, height=1000, scrolling=False)
