/*
kai-game.js - canvas reaction game.
move the cursor onto the ball to eat it, every eat shrinks the next ball.
*/

// playfield and tuning constants
const W = 1000;
const H = 600;
// cursor circle radius in css pixels, matches the svg cursor in kai.css (r=9 + ~1px stroke)
const CURSOR_R_CSS = 10;
// START_MAX_R is the cap a fresh ball grows to at the start of a round, MIN_MAX_R is the
// floor that cap can never shrink below; floor matches the cursor so the smallest possible
// ball is exactly the size of the thing you're hunting it with
const START_MAX_R = 65;
const MIN_MAX_R = CURSOR_R_CSS;
const SHRINK = 0.97;
// each ball reaches its current max in this many seconds, kept short so the rhythm stays snappy
const GROW_DURATION_SEC = 0.3;
// PRESSURE matches the original ballsheet, score depletion grows logarithmically
// with elapsed seconds: pressureRate = PRESSURE * ln(1 + t)
const PRESSURE = 60;
const EAT_BONUS = 35;
const START_SCORE = 100;

let canvas, ctx;
// ballMaxR is the cap for the currently-spawned ball, ballSpawnedAt is when it appeared so
// the draw loop can interpolate from cursor-sized up to ballMaxR
let ballX, ballY, ballMaxR, ballSpawnedAt;
let score, isGameOver;
let lastTick;
let scoreSubmitted = false;
// pressure only starts after the first successful eat, like the original's noCheese flag
let pressureActive;
let pressureStartedAt;
// frozen end-of-round timestamp, lets the game-over overlay show the exact time survived
let gameOverAt;
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
    ballMaxR = START_MAX_R;
    isGameOver = false;
    scoreSubmitted = false;
    pressureActive = false;
    pressureStartedAt = 0;
    gameOverAt = 0;
    spawnBall();
    lastTick = performance.now();
}

function spawnBall() {
    // margin uses the eventual max so a fully-grown ball still fits inside the canvas
    const margin = 4;
    const minX = ballMaxR + margin;
    const maxX = W - ballMaxR - margin;
    const minY = ballMaxR + margin;
    const maxY = H - ballMaxR - margin;
    ballX = minX + Math.random() * (maxX - minX);
    ballY = minY + Math.random() * (maxY - minY);
    ballSpawnedAt = performance.now();
}

// instantaneous radius, eases linearly from cursor-sized at spawn to ballMaxR over GROW_DURATION_SEC
function currentBallR() {
    const cursorR = CURSOR_R_CSS * canvasScale;
    const startR = Math.min(cursorR, ballMaxR);
    const elapsed = (performance.now() - ballSpawnedAt) / 1000;
    const t = Math.min(1, Math.max(0, elapsed / GROW_DURATION_SEC));
    return startR + (ballMaxR - startR) * t;
}

function update(dt) {
    if (isGameOver) return;

    // hover-to-eat: eat when the cursor circle touches the *current* ball, which starts
    // small and grows toward ballMaxR, so a freshly-spawned ball is too tiny to clip
    // unless the cursor is sitting right on top of its centre
    if (mouseX !== null && mouseY !== null) {
        const dx = mouseX - ballX;
        const dy = mouseY - ballY;
        // circle-vs-circle overlap, cursor radius converted from css pixels into canvas units
        const cursorR = CURSOR_R_CSS * canvasScale;
        const reach = currentBallR() + cursorR;
        if (dx * dx + dy * dy <= reach * reach) {
            // first eat starts the pressure clock, like the original's noCheese
            if (!pressureActive) {
                pressureActive = true;
                pressureStartedAt = performance.now();
            }
            score += EAT_BONUS;
            // shrink the cap for the next ball, the floor stops it disappearing entirely
            ballMaxR = Math.max(MIN_MAX_R, ballMaxR * SHRINK);
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
        // the target ball, plain white circle, drawn at its animated growing size
        ctx.fillStyle = '#ffffff';
        ctx.beginPath();
        ctx.arc(ballX, ballY, currentBallR(), 0, Math.PI * 2);
        ctx.fill();

        // pressure gauge along the bottom of the playfield
        drawPressureBar();
    }

    // top-left readouts, the time survived is the metric that gets submitted as the score,
    // the point bank below it is just the visible "you are about to die" indicator
    ctx.fillStyle = '#ffffff';
    ctx.textAlign = 'left';
    ctx.textBaseline = 'top';
    ctx.font = '28px Arial, sans-serif';
    ctx.fillText('Time: ' + survivedSeconds().toFixed(2) + 's', 12, 12);
    ctx.font = '18px Arial, sans-serif';
    ctx.fillText('Score: ' + Math.floor(score), 12, 46);

    if (isGameOver) {
        // overlay with final time and restart prompt
        ctx.fillStyle = 'rgba(0, 0, 0, 0.6)';
        ctx.fillRect(0, 0, W, H);

        ctx.fillStyle = '#ffffff';
        ctx.textAlign = 'center';
        ctx.textBaseline = 'middle';
        ctx.font = '48px Arial, sans-serif';
        ctx.fillText('Game Over', W / 2, H / 2 - 40);
        ctx.font = '28px Arial, sans-serif';
        ctx.fillText('You survived ' + survivedSeconds().toFixed(2) + 's', W / 2, H / 2 + 10);
        ctx.font = '20px Arial, sans-serif';
        ctx.fillText('Press R or Space to restart', W / 2, H / 2 + 50);
    }
}

// pressure rate caps the bar at full red, picked so the marker spans most of the bar over a typical run
const MAX_DISPLAY_PRESSURE = 250;
// segment dividers along the gauge, one extra to give a sense of pressure beyond the four colour stops
const PRESSURE_BAR_SEGMENTS = 11;

function drawPressureBar() {
    const barH = 8;
    const barX = 30;
    const barW = W - barX * 2;
    // sit a pixel above the bottom edge of the canvas, the css border lives outside this area
    const barY = H - barH - 1;

    // red on the left, orange, yellow, green on the right; the marker starts at the
    // green end and descends leftward toward red as pressure builds
    const gradient = ctx.createLinearGradient(barX, 0, barX + barW, 0);
    gradient.addColorStop(0.0, '#ff4136');
    gradient.addColorStop(1 / 3, '#ff851b');
    gradient.addColorStop(2 / 3, '#ffdc00');
    gradient.addColorStop(1.0, '#2ecc40');
    ctx.fillStyle = gradient;
    ctx.fillRect(barX, barY, barW, barH);

    // thin segment dividers, the +0.5 offset keeps single-pixel lines crisp on most displays
    ctx.strokeStyle = 'rgba(0, 0, 0, 0.55)';
    ctx.lineWidth = 1;
    for (let i = 1; i < PRESSURE_BAR_SEGMENTS; i++) {
        const x = Math.round(barX + (barW * i) / PRESSURE_BAR_SEGMENTS) + 0.5;
        ctx.beginPath();
        ctx.moveTo(x, barY);
        ctx.lineTo(x, barY + barH);
        ctx.stroke();
    }

    // outline so the gauge reads as a contained widget rather than a painted strip
    ctx.strokeStyle = '#d9d9d9';
    ctx.strokeRect(barX + 0.5, barY + 0.5, barW - 1, barH - 1);

    // marker rides the bar from no-pressure (right, green) to capped (left, red),
    // so it starts pinned right and descends through the colours as pressure rises
    const elapsed = pressureActive ? (performance.now() - pressureStartedAt) / 1000 : 0;
    const pressureRate = PRESSURE * Math.log(1 + elapsed);
    const fill = Math.min(1, pressureRate / MAX_DISPLAY_PRESSURE);
    const markerX = Math.round(barX + barW * (1 - fill));

    // white block with a thin dark outline so it stays visible across every colour band
    ctx.fillStyle = '#ffffff';
    ctx.fillRect(markerX - 2, barY - 3, 4, barH + 6);
    ctx.strokeStyle = '#000000';
    ctx.strokeRect(markerX - 2.5, barY - 3.5, 5, barH + 7);
}

// seconds elapsed since the first eat, the original ballsheet's high-score metric
function survivedSeconds() {
    if (!pressureActive) return 0;
    const endRef = isGameOver ? gameOverAt : performance.now();
    return (endRef - pressureStartedAt) / 1000;
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
    // freeze the end timestamp so the overlay and the submitted value agree exactly
    gameOverAt = performance.now();
    // submit once per round, R-restart resets the flag in gameSetup
    if (!scoreSubmitted) {
        scoreSubmitted = true;
        // submitted value is milliseconds survived since the first eat, matches the original game's high-score metric
        const survivedMs = pressureStartedAt > 0 ? gameOverAt - pressureStartedAt : 0;
        postScore(Math.floor(survivedMs));
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
