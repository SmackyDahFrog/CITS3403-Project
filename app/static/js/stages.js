/*
stages.js- plays a tick on card hover and a different tick when play is clicked
*/

document.addEventListener('DOMContentLoaded', function () {
    const tickHover = document.getElementById('tickHover');
    const tickClick = document.getElementById('tickClick');

    tickHover.volume = 0.6;
    tickClick.volume = 0.6;
    tickClick.preservesPitch = false;
    tickClick.playbackRate = 1.5;

    document.querySelectorAll('.stage-card').forEach(card => {
        card.addEventListener('mouseenter', () => {
            tickHover.currentTime = 0;
            tickHover.play();
        });
    });

    document.querySelectorAll('.stage-card .btn').forEach(btn => {
        btn.addEventListener('click', () => {
            tickClick.currentTime = 0;
            tickClick.play();
        });
    });
});
