/*
kai-game.js - canvas reaction game.
click the ball before the score bleeds out, every hit shrinks it.
*/

// playfield and tuning constants, tweak these for difficulty feel
const W = 600;
const H = 600;
const START_R = 60;
const MIN_R = 15;
const SHRINK = 0.95;
const PRESSURE = 5;        // points lost per second while a ball sits unclicked
const EAT_BONUS = 35;
const MISS_PENALTY = 5;
const START_SCORE = 100;

let canvas, ctx;
let ballX, ballY, ballR;
let score, isGameOver;
let lastTick;
let scoreSubmitted = false;

function init() {
    canvas = document.getElementById('kaiCanvas');
    ctx = canvas.getContext('2d');

    canvas.addEventListener('mousedown', onMouseDown);
    document.addEventListener('keydown', onKeyDown);

    const restartBtn = document.getElementById('restartBtn');
    if (restartBtn) {
        restartBtn.addEventListener('click', gameSetup);
    }

    gameSetup();
    requestAnimationFrame(gameLoop);
}

function gameSetup() {
    score = START_SCORE;
    ballR = START_R;
    isGameOver = false;
    scoreSubmitted = false;
    spawnBall();
    lastTick = performance.now();
}

function spawnBall() {
    // keep the ball fully inside the canvas with a small margin
    const margin = 4;
    const minX = ballR + margin;
    const maxX = W - ballR - margin;
    const minY = ballR + margin;
    const maxY = H - ballR - margin;
    ballX = minX + Math.random() * (maxX - minX);
    ballY = minY + Math.random() * (maxY - minY);
}

function update(dt) {
    if (isGameOver) return;
    // continuous bleed, score drops by PRESSURE points per second
    score -= PRESSURE * dt;
    if (score <= 0) {
        score = 0;
        gameOver();
    }
}

function draw() {
    // page background bleeds through but the canvas paints itself for crisp edges
    ctx.fillStyle = '#1e1e1e';
    ctx.fillRect(0, 0, W, H);

    if (!isGameOver) {
        // the target ball, plain white circle
        ctx.fillStyle = '#ffffff';
        ctx.beginPath();
        ctx.arc(ballX, ballY, ballR, 0, Math.PI * 2);
        ctx.fill();
    }

    // score readout, top-left
    ctx.fillStyle = '#ffffff';
    ctx.font = '24px Arial, sans-serif';
    ctx.textAlign = 'left';
    ctx.textBaseline = 'top';
    ctx.fillText('Score: ' + Math.floor(score), 12, 12);

    if (isGameOver) {
        // overlay with final score and restart prompt
        ctx.fillStyle = 'rgba(0, 0, 0, 0.6)';
        ctx.fillRect(0, 0, W, H);

        ctx.fillStyle = '#ffffff';
        ctx.textAlign = 'center';
        ctx.textBaseline = 'middle';
        ctx.font = '48px Arial, sans-serif';
        ctx.fillText('Game Over', W / 2, H / 2 - 30);
        ctx.font = '24px Arial, sans-serif';
        ctx.fillText('Press R or Space to restart', W / 2, H / 2 + 20);
    }
}

function gameLoop(now) {
    const dt = (now - lastTick) / 1000;
    lastTick = now;
    update(dt);
    draw();
    requestAnimationFrame(gameLoop);
}

function onMouseDown(e) {
    if (isGameOver) return;
    // translate page coords into canvas coords, accounting for css scaling
    const rect = canvas.getBoundingClientRect();
    const scaleX = canvas.width / rect.width;
    const scaleY = canvas.height / rect.height;
    const cx = (e.clientX - rect.left) * scaleX;
    const cy = (e.clientY - rect.top) * scaleY;

    // squared-distance check, avoids a sqrt every frame
    const dx = cx - ballX;
    const dy = cy - ballY;
    if (dx * dx + dy * dy <= ballR * ballR) {
        score += EAT_BONUS;
        ballR = Math.max(MIN_R, ballR * SHRINK);
        spawnBall();
    } else {
        score -= MISS_PENALTY;
        if (score <= 0) {
            score = 0;
            gameOver();
        }
    }
}

function onKeyDown(e) {
    if (e.key === 'r' || e.key === 'R' || e.key === ' ') {
        gameSetup();
    }
}

function gameOver() {
    isGameOver = true;
    // score persistence is wired in a later phase
}

// kick everything off once the DOM is ready
document.addEventListener('DOMContentLoaded', init);
