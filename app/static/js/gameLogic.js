let board = ['', '', '', '', '', '', '', '', ''];
let gameOver = false;
let gameStartTime = Date.now();
let pauseStartTime = null;
let timerInterval = null;
let restartTimeout = null;
let lastOutcomeWin = false;

const timerEl = document.getElementById('tttTimer');

function startTimer() {
    clearInterval(timerInterval);
    timerInterval = setInterval(() => {
        if (!gameOver) {
            timerEl.textContent = ((Date.now() - gameStartTime) / 1000).toFixed(3) + 's';
        }
    }, 10);
}

startTimer();
 
const cells = document.querySelectorAll('.tttCell');
 
const lines = [
    [0,1,2], [3,4,5], [6,7,8],
    [0,3,6], [1,4,7], [2,5,8],
    [0,4,8], [2,4,6]
];
 
function checkWinner(b) {
    for (const [a, c, d] of lines) {
        if (b[a] && b[a] === b[c] && b[a] === b[d]) {
            return { winner: b[a], line: [a, c, d] };
        }
    }
    if (b.every(cell => cell !== '')) return { winner: 'draw', line: null };
    return null;
}
 
function highlightWin(line) {
    line.forEach(i => cells[i].classList.add('winning'));
}

function highlightDraw() {
    cells.forEach(cell => cell.classList.add('draw'));
}

function handleResult(result) {
    if (!result) return null;
    clearTimeout(restartTimeout);
    restartTimeout = null;
    gameOver = true;
    clearInterval(timerInterval);
    pauseStartTime = Date.now();
    if (result.winner === 'draw') {
        highlightDraw();
    } else if (result.line) {
        highlightWin(result.line);
    }
    return result.winner; // 'X', 'O', or 'draw'
}

function scheduleRestart() {
    restartTimeout = setTimeout(resetGame, 1500);
}

function escapeHtml(str) {
    return String(str)
        .replace(/&/g, '&amp;')
        .replace(/</g, '&lt;')
        .replace(/>/g, '&gt;')
        .replace(/"/g, '&quot;');
}

async function refreshLeaderboard() {
    try {
        const res = await fetch('/api/tictactoe/leaderboard');
        const data = await res.json();

        const topList = document.querySelector('.ttt-leaderboard ol.list-group');
        if (topList) {
            if (data.top.length === 0) {
                topList.innerHTML = '<li class="list-group-item bg-dark text-white">No wins yet, be the first.</li>';
            } else {
                topList.innerHTML = data.top.map(e =>
                    `<li class="list-group-item bg-dark text-white d-flex justify-content-between">` +
                    `<span>${escapeHtml(e.name)}</span>` +
                    `<span>${(e.best_win_ms / 1000).toFixed(3)}s &middot; ${e.wins}W ${e.draws}D ${e.losses}L</span>` +
                    `</li>`
                ).join('');
            }
        }

        const personalList = document.querySelector('.ttt-leaderboard ul.list-group');
        if (personalList) {
            if (!data.personal) {
                personalList.innerHTML = '<li class="list-group-item bg-dark text-white">No games yet, play to set your record.</li>';
            } else {
                const timeStr = data.personal.best_win_ms != null
                    ? `${(data.personal.best_win_ms / 1000).toFixed(3)}s &middot; `
                    : '';
                personalList.innerHTML =
                    `<li class="list-group-item bg-dark text-white d-flex justify-content-between">` +
                    `<span>${escapeHtml(data.personal.name)}</span>` +
                    `<span>${timeStr}${data.personal.wins}W ${data.personal.draws}D ${data.personal.losses}L</span>` +
                    `</li>`;
            }
        }
    } catch (e) {
        console.error('leaderboard refresh failed:', e);
    }
}

function showEndScreen(timeMs) {
    lastOutcomeWin = true;
    document.getElementById('tttEndTitle').textContent = 'You Win!';
    document.getElementById('tttEndTime').textContent = (timeMs / 1000).toFixed(3) + 's';
    document.getElementById('tttEndScreen').style.display = 'flex';
}

async function submitResult(outcome, timeMs) {
    const csrfToken = document.querySelector('meta[name="csrf-token"]')?.content;
    const body = { result: outcome };
    if (timeMs !== undefined) body.time_ms = timeMs;
    try {
        const res = await fetch('/api/tictactoe/runs', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                ...(csrfToken ? { 'X-CSRFToken': csrfToken } : {}),
            },
            body: JSON.stringify(body),
        });
        const data = await res.json();
        if (data.ok && outcome === 'win') {
            setTimeout(() => location.reload(), 1500);
        } else if (data.ok) {
            refreshLeaderboard();
        }
    } catch (e) {
        console.error('tictactoe score submit failed:', e);
    }
}
 
function minimax(b, isAI) {
    const result = checkWinner(b);
    if (result?.winner === 'O') return { score: 1 };
    if (result?.winner === 'X') return { score: -1 };
    if (result?.winner === 'draw') return { score: 0 };
 
    let bestScore = isAI ? -Infinity : Infinity;
    let bestMove = -1;
 
    for (let i = 0; i < 9; i++) {
        if (b[i] !== '') continue;
        b[i] = isAI ? 'O' : 'X';
        const { score } = minimax(b, !isAI);
        b[i] = '';
 
        if (isAI && score > bestScore) { bestScore = score; bestMove = i; }
        if (!isAI && score < bestScore) { bestScore = score; bestMove = i; }
    }
    return { score: bestScore, index: bestMove };
}
 
function aiMove() {
    let move;

    if (Math.random() < 0.15) {
        const empty = [];
        for (let i = 0; i < 9; i++) if (board[i] === '') empty.push(i);
        move = empty[Math.floor(Math.random() * empty.length)];
    } else {
        move = minimax([...board], true).index;
    }

    board[move] = 'O';
    cells[move].textContent = 'O';

    const winner = handleResult(checkWinner(board));
    if (winner) {
        const outcome = winner === 'draw' ? 'draw' : 'loss';
        submitResult(outcome);
        scheduleRestart();
    }
}

cells.forEach((cell, i) => {
    cell.addEventListener('click', () => {
        if (board[i] !== '' || gameOver) return;

        board[i] = 'X';
        cell.textContent = 'X';

        // capture time before any processing so DB, win screen, and top timer all match
        const timeMs = Date.now() - gameStartTime;

        const winner = handleResult(checkWinner(board));
        if (winner) {
            const outcome = winner === 'X' ? 'win' : winner === 'draw' ? 'draw' : 'loss';
            if (outcome === 'win') {
                timerEl.textContent = (timeMs / 1000).toFixed(3) + 's';
                submitResult('win', timeMs);
                showEndScreen(timeMs);
            } else {
                submitResult(outcome);
                scheduleRestart();
            }
            return;
        }

        aiMove();
    });
});

function resetGame() {
    if (lastOutcomeWin) {
        location.reload();
        return;
    }
    clearTimeout(restartTimeout);
    restartTimeout = null;
    board = ['', '', '', '', '', '', '', '', ''];
    gameOver = false;
    if (pauseStartTime !== null) {
        gameStartTime += Date.now() - pauseStartTime;
        pauseStartTime = null;
    }
    cells.forEach(cell => {
        cell.textContent = '';
        cell.classList.remove('winning');
        cell.classList.remove('draw');
    });
    startTimer();
}

document.getElementById('resetBtn').addEventListener('click', resetGame);
document.getElementById('tttRetryBtn').addEventListener('click', resetGame);

document.addEventListener('keydown', e => {
    if (e.key === 'r' || e.key === 'R') resetGame();
});