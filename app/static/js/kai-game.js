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
// PRESSURE matches the original ballsheet, hunger depletion grows logarithmically
// with elapsed seconds: pressureRate = PRESSURE * ln(1 + t)
const PRESSURE = 60;
const EAT_BONUS = 35;
const START_HUNGER = 100;

let canvas, ctx;
// ballMaxR is the cap for the currently-spawned ball, ballSpawnedAt is when it appeared so
// the draw loop can interpolate from cursor-sized up to ballMaxR
let ballX, ballY, ballMaxR, ballSpawnedAt;
let hunger, isGameOver;
// peak hunger reached this run, used as the bar's denominator so the bar visibly shrinks
// from peak back down to 0 even when eats have pushed hunger above its starting bank
let hungerCeiling;
let lastTick;
// scoreSubmitted is about the leaderboard time submission, kept distinct from the hunger bar
let scoreSubmitted = false;
// pressure only starts after the first successful eat, like the original's noCheese flag
let pressureActive;
// accumulated game-clock seconds since pressure started, summed from per-frame dt instead
// of taken from wall clock so tab-hidden gaps and frame stalls don't inflate the run
let survivedTimeSec;
// survivedTimeSec at each eat, used at game over to compute the inter-eat average
// after dropping any interval shorter than CHAIN_EAT_MIN_MS
let eatTimes;
// intervals tighter than this aren't counted toward the average, stops chain-eats on a
// freshly spawned ball from gaming the per-eat speed metric
const CHAIN_EAT_MIN_MS = 100;
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
    hunger = START_HUNGER;
    hungerCeiling = START_HUNGER;
    ballMaxR = START_MAX_R;
    isGameOver = false;
    scoreSubmitted = false;
    pressureActive = false;
    survivedTimeSec = 0;
    eatTimes = [];
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
            }
            // record the moment of this eat in game-clock seconds, the gameover summary
            // averages the gaps between consecutive eats and drops any tighter than 100ms
            eatTimes.push(survivedTimeSec);
            hunger += EAT_BONUS;
            // peak hunger this run sets the bar's denominator, so an eat that pushes
            // hunger above the previous high refills the bar back to a full strip
            if (hunger > hungerCeiling) hungerCeiling = hunger;
            // shrink the cap for the next ball, the floor stops it disappearing entirely
            ballMaxR = Math.max(MIN_MAX_R, ballMaxR * SHRINK);
            spawnBall();
        }
    }

    // pressure only ticks once the first ball has been eaten
    if (!pressureActive) return;

    // accumulate game-clock seconds from this frame's dt, decoupled from wall clock so
    // tab-hidden gaps don't sneak time into the survival timer or the pressure rate
    survivedTimeSec += dt;

    // logarithmic depletion, same model as the original ballsheet
    const pressureRate = PRESSURE * Math.log(1 + survivedTimeSec);
    hunger -= pressureRate * dt;

    if (hunger <= 0) {
        hunger = 0;
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

        // hunger gauge along the bottom of the playfield
        drawHungerBar();
    }

    // top-left readouts, the time survived is the metric that gets submitted to the leaderboard,
    // the hunger bank below it is just the visible "you are about to die" indicator
    ctx.fillStyle = '#ffffff';
    ctx.textAlign = 'left';
    ctx.textBaseline = 'top';
    ctx.font = '28px Arial, sans-serif';
    ctx.fillText('Time: ' + survivedSeconds().toFixed(3) + 's', 12, 12);
    ctx.font = '18px Arial, sans-serif';
    ctx.fillText('Hunger: ' + Math.floor(hunger), 12, 46);

    if (isGameOver) {
        // overlay with final time, per-eat pace, and restart prompt
        ctx.fillStyle = 'rgba(0, 0, 0, 0.6)';
        ctx.fillRect(0, 0, W, H);

        ctx.fillStyle = '#ffffff';
        ctx.textAlign = 'center';
        ctx.textBaseline = 'middle';
        ctx.font = '48px Arial, sans-serif';
        ctx.fillText('Game Over', W / 2, H / 2 - 60);
        ctx.font = '28px Arial, sans-serif';
        ctx.fillText('You survived ' + survivedSeconds().toFixed(3) + 's', W / 2, H / 2 - 15);
        // pace line, only when there's at least one inter-eat gap that wasn't a chain-eat,
        // otherwise the figure would just be 0 and read as misleading
        const finalAvgMs = computeAvgEatMs();
        if (finalAvgMs > 0) {
            ctx.font = '22px Arial, sans-serif';
            ctx.fillText((finalAvgMs / 1000).toFixed(3) + 's/munch', W / 2, H / 2 + 20);
        }
        ctx.font = '20px Arial, sans-serif';
        ctx.fillText('Press R or Space to restart', W / 2, H / 2 + 60);
    }
}

// four colour bands keyed off the bar's own fill ratio, with green held back to the top
// 20% so it reads as "actually doing well" rather than the default. red and orange split
// the lower half evenly as a warning, yellow covers the broad middle from half to 80%
const HUNGER_BAR_BANDS = [
    { upTo: 0.25,     rgb: [0xff, 0x41, 0x36] }, // red, hunger almost gone
    { upTo: 0.50,     rgb: [0xff, 0x85, 0x1b] }, // orange, running low
    { upTo: 0.80,     rgb: [0xff, 0xdc, 0x00] }, // yellow, the warning middle
    { upTo: Infinity, rgb: [0x2e, 0xcc, 0x40] }, // green, only above 80% full
];

// pick the band that t falls inside, returning a solid rgb string for the canvas fillStyle
function colourAtPosition(t) {
    for (const band of HUNGER_BAR_BANDS) {
        if (t < band.upTo) return `rgb(${band.rgb.join(',')})`;
    }
    // unreachable since the last band is Infinity, kept as a safety fallback
    return `rgb(${HUNGER_BAR_BANDS[HUNGER_BAR_BANDS.length - 1].rgb.join(',')})`;
}

function drawHungerBar() {
    // thin strip across the bottom, length itself is the gauge so no separate marker is needed
    const barH = 4;
    const barX = 30;
    const barFullW = W - barX * 2;
    const barY = H - barH - 1;

    // bar length tracks remaining hunger relative to this run's peak, anchored on the left
    // so the right edge recedes as pressure depletes hunger and the bar vanishes at hunger=0
    const fillRatio = hungerCeiling > 0 ? Math.max(0, Math.min(1, hunger / hungerCeiling)) : 0;
    const visibleW = barFullW * fillRatio;
    if (visibleW <= 0) return;

    // colour also reads off the same fill ratio: each 25% quartile gets one solid band so
    // the strip drifts from green through yellow and orange to red as hunger drains
    ctx.fillStyle = colourAtPosition(fillRatio);
    ctx.fillRect(barX, barY, visibleW, barH);
}

// seconds elapsed since the first eat, the original ballsheet's high-score metric
function survivedSeconds() {
    return survivedTimeSec;
}

function gameLoop(now) {
    // cap dt so a tab-switch, sleep, or frame stall can't fast-forward the run on resume.
    // 0.1s is much larger than a normal frame (~0.016s) so it's invisible during smooth play
    let dt = (now - lastTick) / 1000;
    if (dt > 0.1) dt = 0.1;
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

// average milliseconds between eats over the run, after dropping any inter-eat gap
// shorter than CHAIN_EAT_MIN_MS so a flurry of chain-eats can't deflate the average
function computeAvgEatMs() {
    if (eatTimes.length < 2) return 0;
    const minSec = CHAIN_EAT_MIN_MS / 1000;
    let total = 0;
    let count = 0;
    for (let i = 1; i < eatTimes.length; i++) {
        const gap = eatTimes[i] - eatTimes[i - 1];
        if (gap >= minSec) {
            total += gap;
            count += 1;
        }
    }
    if (count === 0) return 0;
    return Math.round((total / count) * 1000);
}

function gameOver() {
    isGameOver = true;
    // submit once per round, R-restart resets the flag in gameSetup
    if (!scoreSubmitted) {
        scoreSubmitted = true;
        // submitted values are milliseconds of accumulated game-clock survival plus per-eat
        // pacing, both ignore any time spent with the tab hidden thanks to survivedTimeSec
        const survivedMs = Math.round(survivedTimeSec * 1000);
        const avgEatMs = computeAvgEatMs();
        postKaiRun(survivedMs, avgEatMs, eatTimes.length);
    }
}

function postKaiRun(timeMs, avgEatMs, eatCount) {
    // CSRFProtect is on globally, the token lives in a meta tag rendered by Jinja
    const meta = document.querySelector('meta[name="csrf-token"]');
    const token = meta ? meta.getAttribute('content') : '';

    fetch('/api/kai/runs', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': token
        },
        // structured payload, the server reads each field, user comes from the session
        body: JSON.stringify({ time_ms: timeMs, avg_eat_ms: avgEatMs, eat_count: eatCount })
    }).then(res => res.json()).then(data => {
        // if the server says this run is the user's new best, give them a couple seconds
        // on the game-over screen and then reload so the leaderboard and the Your Best
        // panel both pick up the freshly-saved row from the server-rendered HTML
        if (data && data.is_new_best) {
            setTimeout(() => window.location.reload(), 2000);
        }
    }).catch(() => {
        // network errors aren't fatal here, the player can still see their score and retry
    });
}

// kick everything off once the DOM is ready
document.addEventListener('DOMContentLoaded', init);
