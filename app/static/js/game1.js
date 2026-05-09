const timer = document.getElementById('timer');
const wilson = document.getElementById('wilson');
const startButton = document.getElementById('start-button');
const startOverlay = document.getElementById('startOverlay');
const gameArea = document.querySelector('.game-area');
const resultOverlay = document.getElementById('resultOverlay');
const resultMessage = document.getElementById('result-message');
const playAgainButton = document.getElementById('play-again-button');
const wilsonPositions = [
    {top: '70%', left: '72%', width: '40px'},
    {top: '60%', left: '30%', width: '20px'},
    {top: '60%', left: '53%', width: '30px'},
]

let startTime;
let gameFinished = false;
let timerInterval;

startButton.addEventListener('click', () => {
    setWilsonPosition();

    gameArea.classList.add('active');
    startOverlay.style.display = 'none';

    startTime = Date.now();

    timerInterval = setInterval(() => {
        if (gameFinished) return;

        const currTime = (Date.now() - startTime) / 1000;
        timer.textContent = `Time: ${currTime.toFixed(2)}s`;
    }, 100);
});

playAgainButton.addEventListener('click', () => {
    window.location.reload();
});

wilson.addEventListener('click', () => {
    if (gameFinished || !startTime) return;

    gameFinished = true;
    clearInterval(timerInterval);

    const finalTime = (Date.now() - startTime) / 1000;
    timer.textContent = `Time: ${finalTime.toFixed(2)}s`;

    resultMessage.textContent= `You found Wilson in ${finalTime.toFixed(2)} seconds!`;
    resultOverlay.style.display = 'flex';
});

function setWilsonPosition() {
    const randomIndex = Math.floor(Math.random() * wilsonPositions.length);
    const chosenPosition = wilsonPositions[randomIndex];

    wilson.style.top = chosenPosition.top;
    wilson.style.left = chosenPosition.left;
    wilson.style.width = chosenPosition.width;
}