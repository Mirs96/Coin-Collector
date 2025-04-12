document.addEventListener('DOMContentLoaded', () => {
    const gameControls = {
        startForm: document.getElementById('startGameForm'),
        closeForm: document.getElementById('closeGameForm'),
        init() {
            this.setupEventListeners();
            this.updateGameStatus();
            this.setupPolling();
        },
        // Links forms to events
        setupEventListeners() {
            this.startForm?.addEventListener('submit', this.handleFormSubmit);
            this.closeForm?.addEventListener('submit', this.handleFormSubmit);
        },

        handleFormSubmit(e) {
            e.preventDefault();
            const form = e.target;
            fetch(form.action, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/x-www-form-urlencoded',
                },
                body: new URLSearchParams(new FormData(form)) // turns the object FormData in a string of key-value pairs separated by &
            })
            .then(() => gameControls.updateGameStatus())
            .catch(error => console.error('Error:', error));
        },
        // check the game status
        updateGameStatus() {
            fetch('/check_game_status')
                .then(response => response.json())
                .then(data => this.updateUI(data.game_active))
                .catch(error => console.error('Error:', error));
        },
        updateUI(gameActive) {
            if(this.startForm && this.closeForm) {
                this.startForm.style.display = gameActive ? 'none' : 'block';
                this.closeForm.style.display = gameActive ? 'block' : 'none';
            }
        },
        setupPolling() {
            setInterval(() => this.updateGameStatus(), 1000);
        }
    };

    gameControls.init();
});