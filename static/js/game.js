/**
 * ═══════════════════════════════════════════════════════════════════
 * 🎮 EDUCATIONAL ROGUELIKE - GAME LOGIC
 * Frontend game controller
 * ═══════════════════════════════════════════════════════════════════
 */

class RoguelikeGame {
    constructor(pdfId) {
        this.pdfId = pdfId;
        this.currentQuestion = null;
        this.gameStatus = null;
        this.battleLog = [];
        this.powerupsConfig = {};
        this.init();
    }

    async init() {
        this.setupEventListeners();
        await this.loadConfig();
        await this.checkGameStatus();
    }

    async loadConfig() {
        try {
            const response = await fetch('/api/config');
            const config = await response.json();
            this.powerupsConfig = config.powerups;
        } catch (error) {
            console.error('Error loading config:', error);
        }
    }

    setupEventListeners() {
        // New game button
        const newGameBtn = document.getElementById('new-game-btn');
        if (newGameBtn) {
            newGameBtn.addEventListener('click', () => this.startNewGame());
        }

        // Save game button
        const saveGameBtn = document.getElementById('save-game-btn');
        if (saveGameBtn) {
            saveGameBtn.addEventListener('click', () => this.saveGame());
        }

        // Submit answer button
        const submitBtn = document.getElementById('submit-answer-btn');
        if (submitBtn) {
            submitBtn.addEventListener('click', () => this.submitAnswer());
        }

        // Next question button
        const nextBtn = document.getElementById('next-question-btn');
        if (nextBtn) {
            nextBtn.addEventListener('click', () => this.loadNextQuestion());
        }
    }

    async startNewGame() {
        try {
            this.showLoading('Starting new game...');

            const response = await fetch(`/api/game/new/${this.pdfId}`, {
                method: 'POST'
            });

            const data = await response.json();

            if (!response.ok) {
                throw new Error(data.error || 'Failed to start game');
            }

            this.gameStatus = data.game_status;
            this.showGameScreen();
            this.updateUI();
            this.addBattleLog('⚔️ A new adventure begins!', 'info');
            await this.loadNextQuestion();

            this.hideLoading();
        } catch (error) {
            console.error('Error starting new game:', error);
            this.showNotification(error.message, 'error');
            this.hideLoading();
        }
    }

    async checkGameStatus() {
        try {
            const response = await fetch(`/api/game/status/${this.pdfId}`);
            const data = await response.json();

            if (data.active) {
                this.gameStatus = data;
                this.updateUI();
                await this.loadNextQuestion();
            } else {
                this.showWelcomeScreen();
            }
        } catch (error) {
            console.error('Error checking game status:', error);
        }
    }

    async loadNextQuestion() {
        try {
            this.showLoading('Loading question...');

            const response = await fetch(`/api/game/question/${this.pdfId}`);

            if (!response.ok) {
                const data = await response.json();
                throw new Error(data.error || 'Failed to load question');
            }

            const question = await response.json();
            this.currentQuestion = question;
            this.displayQuestion(question);

            this.hideLoading();
        } catch (error) {
            console.error('Error loading question:', error);
            this.showNotification(error.message, 'error');
            this.hideLoading();
        }
    }

    displayQuestion(question) {
        const questionPanel = document.getElementById('question-panel');
        if (!questionPanel) return;

        // Show question panel
        questionPanel.classList.remove('hidden');

        // Set topic and difficulty
        const topicEl = document.getElementById('question-topic');
        const difficultyEl = document.getElementById('question-difficulty');

        if (topicEl) topicEl.textContent = question.topic || 'General';
        if (difficultyEl) {
            difficultyEl.textContent = question.difficulty || 'medium';
            difficultyEl.className = `question-difficulty difficulty-${question.difficulty}`;
        }

        // Set question text
        const questionText = document.getElementById('question-text');
        if (questionText) {
            questionText.textContent = question.question_text;
        }

        // Display options
        this.displayOptions(question);

        // Hide feedback panel
        const feedbackPanel = document.getElementById('feedback-panel');
        if (feedbackPanel) {
            feedbackPanel.classList.add('hidden');
        }

        // Enable submit button
        const submitBtn = document.getElementById('submit-answer-btn');
        if (submitBtn) {
            submitBtn.disabled = false;
            submitBtn.classList.remove('hidden');
        }

        // Hide next button
        const nextBtn = document.getElementById('next-question-btn');
        if (nextBtn) {
            nextBtn.classList.add('hidden');
        }
    }

    displayOptions(question) {
        const optionsContainer = document.getElementById('answer-options');
        if (!optionsContainer) return;

        optionsContainer.innerHTML = '';

        if (question.question_type === 'true_false') {
            question.options = ['true', 'false'];
        }

        question.options.forEach((option, index) => {
            const optionEl = document.createElement('div');
            optionEl.className = 'answer-option';
            optionEl.textContent = option;
            optionEl.dataset.value = option;

            optionEl.addEventListener('click', () => this.selectOption(optionEl));

            optionsContainer.appendChild(optionEl);
        });
    }

    selectOption(optionEl) {
        // Deselect all options
        const allOptions = document.querySelectorAll('.answer-option');
        allOptions.forEach(opt => opt.classList.remove('selected'));

        // Select this option
        optionEl.classList.add('selected');
    }

    async submitAnswer() {
        const selectedOption = document.querySelector('.answer-option.selected');

        if (!selectedOption) {
            this.showNotification('Please select an answer!', 'error');
            return;
        }

        const userAnswer = selectedOption.dataset.value;

        try {
            this.showLoading('Checking answer...');

            // Disable submit button
            const submitBtn = document.getElementById('submit-answer-btn');
            if (submitBtn) submitBtn.disabled = true;

            const response = await fetch(`/api/game/answer/${this.pdfId}`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    question_id: this.currentQuestion.id,
                    answer: userAnswer
                })
            });

            const result = await response.json();

            if (!response.ok) {
                throw new Error(result.error || 'Failed to submit answer');
            }

            this.processAnswerResult(result, selectedOption);
            this.hideLoading();

        } catch (error) {
            console.error('Error submitting answer:', error);
            this.showNotification(error.message, 'error');
            this.hideLoading();
        }
    }

    processAnswerResult(result, selectedOption) {
        // Update game status
        this.gameStatus = result.game_status;

        // Show feedback
        this.showFeedback(result);

        // Mark correct/incorrect option
        if (result.is_correct) {
            selectedOption.classList.add('correct');
            playAnimation('correct');
            this.addBattleLog(`⚔️ You dealt ${result.damage_dealt} damage!`, 'damage');
        } else {
            selectedOption.classList.add('incorrect');
            playAnimation('incorrect');
            this.addBattleLog(`💔 You took ${result.damage_received} damage!`, 'damage');

            // Highlight correct answer
            const allOptions = document.querySelectorAll('.answer-option');
            allOptions.forEach(opt => {
                if (opt.dataset.value === result.correct_answer) {
                    opt.classList.add('correct');
                }
            });
        }

        // Show powerup notification
        if (result.powerup_gained) {
            this.showPowerupNotification(result.powerup_gained);
        }

        // Check for enemy defeat
        if (result.enemy_defeated) {
            this.addBattleLog(`🎉 Enemy defeated! +${result.score_gained} points!`, 'info');
            playAnimation('victory');
        }

        // Check for player death
        if (result.player_died) {
            this.addBattleLog('💀 You have been defeated...', 'info');
            playAnimation('defeat');
            this.showGameOver();
            return;
        }

        // Check for game won
        if (result.game_won) {
            this.addBattleLog('🌟 Victory! You completed the dungeon!', 'info');
            this.showVictory();
            return;
        }

        // Update UI
        this.updateUI();

        // Show next question button
        const nextBtn = document.getElementById('next-question-btn');
        if (nextBtn) {
            nextBtn.classList.remove('hidden');
        }

        // Hide submit button
        const submitBtn = document.getElementById('submit-answer-btn');
        if (submitBtn) {
            submitBtn.classList.add('hidden');
        }
    }

    showFeedback(result) {
        const feedbackPanel = document.getElementById('feedback-panel');
        if (!feedbackPanel) return;

        feedbackPanel.classList.remove('hidden');
        feedbackPanel.className = `feedback-panel ${result.is_correct ? 'correct' : 'incorrect'}`;

        const feedbackTitle = document.getElementById('feedback-title');
        const feedbackText = document.getElementById('feedback-text');

        if (feedbackTitle) {
            feedbackTitle.textContent = result.is_correct ? '✅ Correct!' : '❌ Incorrect';
        }

        if (feedbackText) {
            feedbackText.textContent = result.explanation || '';
        }
    }

    showPowerupNotification(powerupId) {
        // Get powerup info from config
        fetch('/api/config')
            .then(res => res.json())
            .then(config => {
                const powerup = config.powerups[powerupId];
                if (powerup) {
                    this.showNotification(`${powerup.name} obtained!`, 'success');
                    this.addBattleLog(`✨ ${powerup.name} obtained!`, 'heal');
                }
            });
    }

    updateUI() {
        if (!this.gameStatus) return;

        // Update player info
        this.updatePlayer(this.gameStatus.player);

        // Update enemy info
        if (this.gameStatus.enemy) {
            this.updateEnemy(this.gameStatus.enemy);
        }

        // Update progress
        this.updateProgress(this.gameStatus.progress);

        // Update stats
        this.updateStats(this.gameStatus.stats);

        // Update inventory
        this.updateInventory(this.gameStatus.inventory);
    }

    updatePlayer(player) {
        // Reset player sprite animations to ensure visibility
        const playerSprite = document.getElementById('player-sprite');
        if (playerSprite) {
            playerSprite.style.animation = '';
            playerSprite.style.opacity = '';
            playerSprite.style.transform = '';
            playerSprite.classList.remove('attacking', 'damaged');
        }

        // Update HP
        const playerHpFill = document.getElementById('player-hp-fill');
        const playerHpText = document.getElementById('player-hp-text');

        if (playerHpFill) {
            playerHpFill.style.width = `${player.hp_percent}%`;

            // Change color based on HP
            if (player.hp_percent < 30) {
                playerHpFill.classList.add('low');
            } else {
                playerHpFill.classList.remove('low');
            }
        }

        if (playerHpText) {
            playerHpText.textContent = `${player.hp}/${player.max_hp}`;
        }

        // Update shield
        const shieldIndicator = document.getElementById('player-shield');
        if (shieldIndicator) {
            if (player.shield > 0) {
                shieldIndicator.textContent = `🛡️ Shield: ${player.shield}`;
                shieldIndicator.classList.remove('hidden');
            } else {
                shieldIndicator.classList.add('hidden');
            }
        }

        // Update score
        const scoreEl = document.getElementById('player-score');
        if (scoreEl) {
            scoreEl.textContent = player.score.toLocaleString();
        }
    }

    updateEnemy(enemy) {
        // Update sprite
        const enemySprite = document.getElementById('enemy-sprite');
        if (enemySprite) {
            enemySprite.textContent = enemy.emoji;
            // Reset animations and styles to fix sprite visibility
            enemySprite.style.animation = '';
            enemySprite.style.opacity = '';
            enemySprite.style.transform = '';
            enemySprite.style.display = '';
            // Remove animation classes
            enemySprite.classList.remove('attacking', 'damaged');
        }

        // Update name
        const enemyName = document.getElementById('enemy-name');
        if (enemyName) {
            enemyName.textContent = enemy.name;
        }

        // Show boss indicator if this is a boss
        const bossIndicator = document.getElementById('boss-indicator');
        if (bossIndicator) {
            if (enemy.is_boss) {
                bossIndicator.classList.remove('hidden');
            } else {
                bossIndicator.classList.add('hidden');
            }
        }

        // Update HP
        const enemyHpFill = document.getElementById('enemy-hp-fill');
        const enemyHpText = document.getElementById('enemy-hp-text');

        if (enemyHpFill) {
            enemyHpFill.style.width = `${enemy.hp_percent}%`;
        }

        if (enemyHpText) {
            enemyHpText.textContent = `${enemy.hp}/${enemy.max_hp}`;
        }

        // Update damage
        const enemyDamage = document.getElementById('enemy-damage');
        if (enemyDamage) {
            enemyDamage.textContent = enemy.damage;
        }
    }

    updateProgress(progress) {
        const progressFill = document.getElementById('progress-fill');
        const progressText = document.getElementById('progress-text');

        if (progressFill) {
            progressFill.style.width = `${progress.percent}%`;
        }

        if (progressText) {
            progressText.textContent = `Encounter ${progress.current_encounter}/${progress.total_encounters}`;
        }
    }

    updateStats(stats) {
        const accuracyEl = document.getElementById('session-accuracy');
        if (accuracyEl) {
            accuracyEl.textContent = `${stats.accuracy.toFixed(1)}%`;
        }

        const answeredEl = document.getElementById('questions-answered');
        if (answeredEl) {
            answeredEl.textContent = stats.questions_answered;
        }
    }

    updateInventory(inventory) {
        const inventoryEmpty = document.getElementById('inventory-empty');
        const inventoryItems = document.getElementById('inventory-items');

        if (!inventoryItems) return;

        // Clear current items
        inventoryItems.innerHTML = '';

        if (!inventory || inventory.length === 0) {
            if (inventoryEmpty) inventoryEmpty.style.display = 'block';
            return;
        }

        if (inventoryEmpty) inventoryEmpty.style.display = 'none';

        // Group powerups by type and count
        const powerupCounts = {};
        inventory.forEach(powerupId => {
            powerupCounts[powerupId] = (powerupCounts[powerupId] || 0) + 1;
        });

        // Display each unique powerup
        Object.entries(powerupCounts).forEach(([powerupId, count]) => {
            const powerupData = this.powerupsConfig[powerupId];
            if (!powerupData) return;

            const itemEl = document.createElement('button');
            itemEl.className = 'inventory-item';
            itemEl.innerHTML = `
                <span class="powerup-name">${powerupData.name}</span>
                ${count > 1 ? `<span class="powerup-count">x${count}</span>` : ''}
            `;
            itemEl.title = `Click to use: ${this.getPowerupDescription(powerupId, powerupData)}`;
            itemEl.addEventListener('click', () => this.usePowerup(powerupId));

            inventoryItems.appendChild(itemEl);
        });
    }

    getPowerupDescription(powerupId, powerupData) {
        const descriptions = {
            'heal': `Restores ${powerupData.value} HP`,
            'shield': `Adds ${powerupData.value} shield`,
            'damage_boost': `Multiplies damage by ${powerupData.value}x`,
            'score_boost': `Multiplies score by ${powerupData.value}x`
        };
        return descriptions[powerupData.effect] || 'Unknown effect';
    }

    async usePowerup(powerupId) {
        try {
            this.showLoading('Using powerup...');

            const response = await fetch(`/api/game/use-powerup/${this.pdfId}`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({ powerup_id: powerupId })
            });

            const result = await response.json();

            if (!response.ok) {
                throw new Error(result.error || 'Failed to use powerup');
            }

            // Update game status
            this.gameStatus = result.game_status;
            this.updateUI();

            // Show notification
            const powerupData = this.powerupsConfig[powerupId];
            if (powerupData) {
                this.showNotification(`Used ${powerupData.name}!`, 'success');
                this.addBattleLog(`✨ Used ${powerupData.name}`, 'heal');
            }

            this.hideLoading();

        } catch (error) {
            console.error('Error using powerup:', error);
            this.showNotification(error.message, 'error');
            this.hideLoading();
        }
    }

    addBattleLog(message, type = 'info') {
        this.battleLog.push({ message, type, timestamp: new Date() });

        const logContainer = document.getElementById('battle-log');
        if (!logContainer) return;

        const logEntry = document.createElement('div');
        logEntry.className = `log-entry log-${type}`;
        logEntry.textContent = `> ${message}`;

        logContainer.appendChild(logEntry);

        // Auto-scroll to bottom
        logContainer.scrollTop = logContainer.scrollHeight;

        // Limit log entries
        while (logContainer.children.length > 20) {
            logContainer.removeChild(logContainer.firstChild);
        }
    }

    async saveGame() {
        try {
            const saveName = prompt('Enter a name for this save:');
            if (!saveName) return;

            this.showLoading('Saving game...');

            const response = await fetch(`/api/game/save/${this.pdfId}`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({ save_name: saveName })
            });

            const data = await response.json();

            if (!response.ok) {
                throw new Error(data.error || 'Failed to save game');
            }

            this.showNotification('Game saved successfully!', 'success');
            this.hideLoading();

        } catch (error) {
            console.error('Error saving game:', error);
            this.showNotification(error.message, 'error');
            this.hideLoading();
        }
    }

    showWelcomeScreen() {
        const welcomeScreen = document.getElementById('welcome-screen');
        const gameScreen = document.getElementById('game-screen');

        if (welcomeScreen) welcomeScreen.classList.remove('hidden');
        if (gameScreen) gameScreen.classList.add('hidden');
    }

    showGameScreen() {
        console.log('🎮 Showing game screen');
        const welcomeScreen = document.getElementById('welcome-screen');
        const gameScreen = document.getElementById('game-screen');

        if (welcomeScreen) welcomeScreen.classList.add('hidden');
        if (gameScreen) gameScreen.classList.remove('hidden');

    }

    showGameOver() {
        setTimeout(() => {
            alert('Game Over! Your progress has been saved.');
            window.location.href = `/stats/${this.pdfId}`;
        }, 2000);
    }

    showVictory() {
        setTimeout(() => {
            alert('🎉 Victory! You completed the dungeon! Check your stats.');
            window.location.href = `/stats/${this.pdfId}`;
        }, 2000);
    }

    showLoading(message = 'Loading...') {
        const loadingEl = document.getElementById('loading-indicator');
        if (loadingEl) {
            loadingEl.textContent = message;
            loadingEl.classList.remove('hidden');
        }
    }

    hideLoading() {
        const loadingEl = document.getElementById('loading-indicator');
        if (loadingEl) {
            loadingEl.classList.add('hidden');
        }
    }

    showNotification(message, type = 'info') {
        const notification = document.createElement('div');
        notification.className = `notification ${type}`;
        notification.textContent = message;

        document.body.appendChild(notification);

        setTimeout(() => {
            notification.remove();
        }, 3000);
    }
}

// Initialize game when page loads
document.addEventListener('DOMContentLoaded', () => {
    const gameContainer = document.getElementById('game-container');
    if (gameContainer) {
        const pdfId = gameContainer.dataset.pdfId;
        if (pdfId) {
            window.roguelikeGame = new RoguelikeGame(parseInt(pdfId));
        }
    }
});
