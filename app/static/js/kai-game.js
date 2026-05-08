/*
kai-game.js - canvas reaction game.
move the cursor onto the ball to eat it, every eat shrinks the next ball.
*/

// playfield and tuning constants
const W = 1000;
const H = 600;
const START_R = 65;
const MIN_R = 16;
const SHRINK = 0.95;
// PRESSURE matches the original ballsheet, score depletion grows logarithmically
// with elapsed seconds: pressureRate = PRESSURE * ln(1 + t)
const PRESSURE = 60;
const EAT_BONUS = 35;
const START_SCORE = 100;
// cursor circle radius in css pixels, matches the svg cursor in kai.css (r=9 + ~1px stroke)
const CURSOR_R_CSS = 10;

let canvas, ctx;
let ballX, ballY, ballR;
let score, isGameOver;
let lastTick;
let scoreSubmitted = false;
// pressure only starts after the first successful eat, like the original's noCheese flag
let pressureActive;
let pressureStartedAt;
// most recent mouse position in canvas coords, null until the cursor first enters the canvas
let mouseX = null;
let mouseY = null;
// css px to canvas px factor, recomputed each mousemove so the cursor hit radius scales with css resizing
let canvasScale = 1;

function init() {
    canvas = document.getElementById('kaiCanvas');
    ctx = canvas.getContext('2d');

    canvas.addEventListener('mousemove', onMouseMove);
    canvas.addEventListener('mouseleave', onMouseLeave);
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
    pressureActive = false;
    pressureStartedAt = 0;
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

    // hover-to-eat: eat when the cursor circle touches the ball, not just when its centre is inside
    if (mouseX !== null && mouseY !== null) {
        const dx = mouseX - ballX;
        const dy = mouseY - ballY;
        // circle-vs-circle overlap, cursor radius converted from css pixels into canvas units
        const cursorR = CURSOR_R_CSS * canvasScale;
        const reach = ballR + cursorR;
        if (dx * dx + dy * dy <= reach * reach) {
            // first eat starts the pressure clock, like the original's noCheese
            if (!pressureActive) {
                pressureActive = true;
                pressureStartedAt = performance.now();
            }
            score += EAT_BONUS;
            ballR = Math.max(MIN_R, ballR * SHRINK);
            spawnBall();
        }
    }

    // pressure only ticks once the first ball has been eaten
    if (!pressureActive) return;

    // logarithmic depletion, same model as the original ballsheet
    const elapsed = (performance.now() - pressureStartedAt) / 1000;
    const pressureRate = PRESSURE * Math.log(1 + elapsed);
    score -= pressureRate * dt;

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

function onMouseMove(e) {
    // translate page coords into canvas coords, accounting for css scaling
    const rect = canvas.getBoundingClientRect();
    const scaleX = canvas.width / rect.width;
    const scaleY = canvas.height / rect.height;
    mouseX = (e.clientX - rect.left) * scaleX;
    mouseY = (e.clientY - rect.top) * scaleY;
    // canvas may be css-scaled at narrow widths, cache the factor for the cursor hit radius
    canvasScale = scaleX;
}

function onMouseLeave() {
    // forget the cursor position when it leaves the canvas so we don't keep eating off-screen
    mouseX = null;
    mouseY = null;
}

function onKeyDown(e) {
    if (e.key === 'r' || e.key === 'R' || e.key === ' ') {
        gameSetup();
    }
}

function gameOver() {
    isGameOver = true;
    // submit once per round, R-restart resets the flag in gameSetup
    if (!scoreSubmitted) {
        scoreSubmitted = true;
        postScore(Math.floor(score));
    }
}

function postScore(value) {
    // CSRFProtect is on globally, the token lives in a meta tag rendered by Jinja
    const meta = document.querySelector('meta[name="csrf-token"]');
    const token = meta ? meta.getAttribute('content') : '';

    fetch('/api/scores', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': token
        },
        // server reads game + value, user comes from the session
        body: JSON.stringify({ game: 'kai', value: value })
    }).catch(() => {
        // network errors aren't fatal here, the player can still see their score and retry
    });
}

// kick everything off once the DOM is ready
document.addEventListener('DOMContentLoaded', init);
