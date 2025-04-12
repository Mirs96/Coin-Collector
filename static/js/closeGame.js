function closeGame() {
    fetch('/close_game', {
        method: 'GET',
        credentials: 'include'  // Send session cookies
    })
    .then(response => {
        if (response.ok) {
            alert('Game closed successfully.');
            window.location.reload();
        } else {
            alert('Failed to close the game.');
        }
    })
    .catch(error => {
        console.error('Error closing game:', error);
        alert('Error closing game.');
    });
}
