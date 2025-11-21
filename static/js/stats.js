/**
 * ═══════════════════════════════════════════════════════════════════
 * 📊 EDUCATIONAL ROGUELIKE - STATISTICS
 * Statistics visualization and management
 * ═══════════════════════════════════════════════════════════════════
 */

class StatsManager {
    constructor(pdfId) {
        this.pdfId = pdfId;
        this.stats = null;
        this.init();
    }

    async init() {
        await this.loadStats();
        this.setupEventListeners();
    }

    setupEventListeners() {
        // Export buttons
        const exportJson = document.getElementById('export-json');
        const exportCsv = document.getElementById('export-csv');
        const exportMarkdown = document.getElementById('export-markdown');

        if (exportJson) {
            exportJson.addEventListener('click', () => this.exportStats('json'));
        }

        if (exportCsv) {
            exportCsv.addEventListener('click', () => this.exportStats('csv'));
        }

        if (exportMarkdown) {
            exportMarkdown.addEventListener('click', () => this.exportStats('markdown'));
        }

        // Refresh button
        const refreshBtn = document.getElementById('refresh-stats');
        if (refreshBtn) {
            refreshBtn.addEventListener('click', () => this.loadStats());
        }
    }

    async loadStats() {
        try {
            this.showLoading();

            const response = await fetch(`/api/stats/${this.pdfId}`);
            const data = await response.json();

            if (!response.ok) {
                throw new Error(data.error || 'Failed to load statistics');
            }

            this.stats = data;
            this.displayStats();
            this.hideLoading();

        } catch (error) {
            console.error('Error loading stats:', error);
            this.showNotification(error.message, 'error');
            this.hideLoading();
        }
    }

    displayStats() {
        if (!this.stats) return;

        this.displayOverallStats(this.stats.overall);
        this.displayTopicPerformance(this.stats.topics);
        this.displayWeakAreas(this.stats.weak_areas);
    }

    displayOverallStats(overall) {
        // Total answers
        const totalEl = document.getElementById('total-answers');
        if (totalEl && overall.total_answers !== undefined) {
            animateNumber(totalEl, 0, overall.total_answers, 1000);
        }

        // Correct answers
        const correctEl = document.getElementById('correct-answers');
        if (correctEl && overall.correct_answers !== undefined) {
            animateNumber(correctEl, 0, overall.correct_answers, 1000);
        }

        // Accuracy
        const accuracyEl = document.getElementById('overall-accuracy');
        if (accuracyEl && overall.accuracy !== undefined) {
            setTimeout(() => {
                accuracyEl.textContent = `${overall.accuracy.toFixed(1)}%`;
                this.updateAccuracyColor(accuracyEl, overall.accuracy);
            }, 500);
        }

        // Total time
        const timeEl = document.getElementById('total-time');
        if (timeEl && overall.total_time_seconds !== undefined) {
            timeEl.textContent = this.formatTime(overall.total_time_seconds);
        }

        // Total score
        const scoreEl = document.getElementById('total-score');
        if (scoreEl && overall.total_score !== undefined) {
            animateNumber(scoreEl, 0, overall.total_score, 1200);
        }

        // Completed games
        const gamesEl = document.getElementById('completed-games');
        if (gamesEl && overall.completed_games !== undefined) {
            gamesEl.textContent = overall.completed_games;
        }
    }

    displayTopicPerformance(topics) {
        const container = document.getElementById('topic-performance');
        if (!container) return;

        if (!topics || topics.length === 0) {
            container.innerHTML = '<p class="text-accent">No topic data available yet. Start playing to see your performance!</p>';
            return;
        }

        container.innerHTML = '';

        topics.forEach((topic, index) => {
            const topicCard = document.createElement('div');
            topicCard.className = 'card';
            topicCard.style.animationDelay = `${index * 100}ms`;

            const accuracy = topic.accuracy || 0;
            const progressColor = this.getAccuracyColor(accuracy);

            topicCard.innerHTML = `
                <div class="card-title">${topic.topic || 'Unknown Topic'}</div>
                <div class="card-content">
                    <div class="character-stat">
                        <span>Attempts:</span>
                        <span class="text-accent">${topic.attempts || 0}</span>
                    </div>
                    <div class="character-stat">
                        <span>Correct:</span>
                        <span class="text-primary">${topic.correct || 0}</span>
                    </div>
                    <div class="progress-bar-container mt-md">
                        <div class="progress-label">Accuracy: ${accuracy.toFixed(1)}%</div>
                        <div class="progress-bar">
                            <div class="progress-bar-fill" style="width: ${accuracy}%; background-color: ${progressColor}"></div>
                        </div>
                    </div>
                </div>
            `;

            container.appendChild(topicCard);
        });
    }

    displayWeakAreas(weakAreas) {
        const container = document.getElementById('weak-areas');
        if (!container) return;

        if (!weakAreas || weakAreas.length === 0) {
            container.innerHTML = '<p class="text-primary">🌟 Great job! No weak areas identified.</p>';
            return;
        }

        container.innerHTML = '<p class="text-warning mb-md">📚 Focus your study on these areas:</p>';

        const list = document.createElement('div');
        list.className = 'card-grid';

        weakAreas.forEach((area, index) => {
            const areaCard = document.createElement('div');
            areaCard.className = 'card';
            areaCard.style.borderColor = 'var(--color-warning)';
            areaCard.style.animationDelay = `${index * 100}ms`;

            areaCard.innerHTML = `
                <div class="card-title text-warning">${area.topic || 'Unknown'}</div>
                <div class="card-content">
                    <div class="character-stat">
                        <span>Difficulty:</span>
                        <span class="difficulty-${area.difficulty}">${(area.difficulty || 'unknown').toUpperCase()}</span>
                    </div>
                    <div class="character-stat">
                        <span>Accuracy:</span>
                        <span class="text-danger">${(area.accuracy || 0).toFixed(1)}%</span>
                    </div>
                    <div class="character-stat">
                        <span>Attempts:</span>
                        <span>${area.attempts || 0}</span>
                    </div>
                </div>
            `;

            list.appendChild(areaCard);
        });

        container.appendChild(list);
    }

    async exportStats(format) {
        try {
            this.showLoading('Exporting...');

            const response = await fetch(`/api/stats/export/${this.pdfId}/${format}`);
            const data = await response.json();

            if (!response.ok) {
                throw new Error(data.error || 'Failed to export statistics');
            }

            this.showNotification(`Statistics exported successfully!`, 'success');

            // Download files
            if (data.files) {
                for (const [fmt, filepath] of Object.entries(data.files)) {
                    const filename = filepath.split('/').pop();
                    window.open(`/api/stats/download/${filename}`, '_blank');
                }
            }

            this.hideLoading();

        } catch (error) {
            console.error('Error exporting stats:', error);
            this.showNotification(error.message, 'error');
            this.hideLoading();
        }
    }

    formatTime(seconds) {
        if (!seconds || seconds === 0) return '0 minutes';

        const hours = Math.floor(seconds / 3600);
        const minutes = Math.floor((seconds % 3600) / 60);
        const secs = seconds % 60;

        const parts = [];
        if (hours > 0) parts.push(`${hours}h`);
        if (minutes > 0) parts.push(`${minutes}m`);
        if (secs > 0 && hours === 0) parts.push(`${secs}s`);

        return parts.join(' ') || '0s';
    }

    getAccuracyColor(accuracy) {
        if (accuracy >= 80) return 'var(--color-hp-high)';
        if (accuracy >= 60) return 'var(--color-warning)';
        if (accuracy >= 40) return 'var(--color-hp-low)';
        return 'var(--color-danger)';
    }

    updateAccuracyColor(element, accuracy) {
        element.style.color = this.getAccuracyColor(accuracy);
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

// Initialize stats manager when page loads
document.addEventListener('DOMContentLoaded', () => {
    const statsContainer = document.getElementById('stats-container');
    if (statsContainer) {
        const pdfId = statsContainer.dataset.pdfId;
        if (pdfId) {
            window.statsManager = new StatsManager(parseInt(pdfId));
        }
    }
});
