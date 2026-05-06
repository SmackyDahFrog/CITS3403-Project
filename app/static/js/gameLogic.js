let board = ['', '', '', '', '', '', '', '', ''];
let gameOver = false;
 
const cells = document.querySelectorAll('.tttCell');
 
const lines = [
    [0,1,2], [3,4,5], [6,7,8],
    [0,3,6], [1,4,7], [2,5,8],
    [0,4,8], [2,4,6]
]; // all winning line formations
 
function checkWinner(b) { // returns winner, or if draw
    for (const [a, c, d] of lines) {
        if (b[a] && b[a] === b[c] && b[a] === b[d]) {
            return { winner: b[a], line: [a, c, d] };
        }
    }
    if (b.every(cell => cell !== '')) return { winner: 'draw', line: null };
    return null;
}
 
function highlightWin(line) { // highlight winning cells
    line.forEach(i => cells[i].classList.add('winning'));
}
 
function minimax(b, isAI) { // minimax algo that gives the best optimal move
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
 
function aiMove() { // move to pick, 85% being the optimal move
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
 
    const result = checkWinner(board);
    if (result) {
        gameOver = true;
        if (result.line) highlightWin(result.line);
    }
}
 
cells.forEach((cell, i) => {
    cell.addEventListener('click', () => {
        if (board[i] !== '' || gameOver) return;
 
        board[i] = 'X';
        cell.textContent = 'X';
 
        const result = checkWinner(board);
        if (result) {
            gameOver = true;
            if (result.line) highlightWin(result.line);
            return;
        }
 
        aiMove();
    });
});