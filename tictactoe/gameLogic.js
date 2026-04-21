let isX = true; 
 
const cells = document.querySelectorAll('.tttCell');
 
cells.forEach(cell => {
    cell.addEventListener('click', () => {
        if (cell.textContent !== '') return; 
 
        cell.textContent = isX ? 'X' : 'O';
        isX = !isX; 
    });
});
    