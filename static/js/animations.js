/**
 * ═══════════════════════════════════════════════════════════════════
 * ✨ EDUCATIONAL ROGUELIKE - ANIMATION EFFECTS
 * Pixel art visual effects and animations
 * ═══════════════════════════════════════════════════════════════════
 */

/**
 * Play an animation by type
 * @param {string} type - Animation type: 'correct', 'incorrect', 'victory', 'defeat', 'attack', 'damage'
 */
function playAnimation(type) {
    switch (type) {
        case 'correct':
            animateCorrectAnswer();
            break;
        case 'incorrect':
            animateIncorrectAnswer();
            break;
        case 'victory':
            animateVictory();
            break;
        case 'defeat':
            animateDefeat();
            break;
        case 'attack':
            animatePlayerAttack();
            break;
        case 'damage':
            animatePlayerDamage();
            break;
    }
}

/**
 * Animate correct answer - player attacks
 */
function animateCorrectAnswer() {
    const playerSprite = document.getElementById('player-sprite');
    const enemySprite = document.getElementById('enemy-sprite');

    if (!playerSprite || !enemySprite) return;

    // Player attacks
    playerSprite.classList.add('attacking');
    createParticles(playerSprite, 'green');

    setTimeout(() => {
        // Enemy takes damage
        enemySprite.classList.add('damaged');
        screenShake();
        createParticles(enemySprite, 'red');
    }, 300);

    setTimeout(() => {
        playerSprite.classList.remove('attacking');
        enemySprite.classList.remove('damaged');
    }, 1000);
}

/**
 * Animate incorrect answer - enemy attacks
 */
function animateIncorrectAnswer() {
    const playerSprite = document.getElementById('player-sprite');
    const enemySprite = document.getElementById('enemy-sprite');

    if (!playerSprite || !enemySprite) return;

    // Enemy attacks
    enemySprite.classList.add('attacking');

    setTimeout(() => {
        // Player takes damage
        playerSprite.classList.add('damaged');
        screenShake('horizontal');
        createParticles(playerSprite, 'red');
    }, 300);

    setTimeout(() => {
        enemySprite.classList.remove('attacking');
        playerSprite.classList.remove('damaged');
    }, 1000);
}

/**
 * Animate victory
 */
function animateVictory() {
    const enemySprite = document.getElementById('enemy-sprite');
    const playerSprite = document.getElementById('player-sprite');

    if (enemySprite) {
        enemySprite.style.animation = 'defeat 1s ease-out forwards';
        createFireworks();
    }

    if (playerSprite) {
        playerSprite.style.animation = 'victory 1s ease-out infinite';
    }

    // Confetti!
    createConfetti();
}

/**
 * Animate defeat
 */
function animateDefeat() {
    const playerSprite = document.getElementById('player-sprite');

    if (playerSprite) {
        playerSprite.style.animation = 'defeat 1s ease-out forwards';
        playerSprite.style.opacity = '0.5';
    }
}

/**
 * Animate player attack
 */
function animatePlayerAttack() {
    const playerSprite = document.getElementById('player-sprite');

    if (playerSprite) {
        playerSprite.classList.add('attacking');
        setTimeout(() => {
            playerSprite.classList.remove('attacking');
        }, 600);
    }
}

/**
 * Animate player taking damage
 */
function animatePlayerDamage() {
    const playerSprite = document.getElementById('player-sprite');

    if (playerSprite) {
        playerSprite.classList.add('damaged');
        setTimeout(() => {
            playerSprite.classList.remove('damaged');
        }, 400);
    }
}

/**
 * Create particle effects
 * @param {HTMLElement} element - Element to emit particles from
 * @param {string} color - Particle color
 */
function createParticles(element, color = 'green') {
    if (!element) return;

    const rect = element.getBoundingClientRect();
    const centerX = rect.left + rect.width / 2;
    const centerY = rect.top + rect.height / 2;

    for (let i = 0; i < 12; i++) {
        const particle = document.createElement('div');
        particle.className = 'particle';

        const angle = (Math.PI * 2 * i) / 12;
        const velocity = 50 + Math.random() * 50;

        particle.style.cssText = `
            position: fixed;
            left: ${centerX}px;
            top: ${centerY}px;
            width: 8px;
            height: 8px;
            background-color: ${getColorHex(color)};
            border-radius: 50%;
            pointer-events: none;
            z-index: 9999;
        `;

        document.body.appendChild(particle);

        // Animate particle
        const animation = particle.animate([
            {
                transform: 'translate(0, 0) scale(1)',
                opacity: 1
            },
            {
                transform: `translate(${Math.cos(angle) * velocity}px, ${Math.sin(angle) * velocity}px) scale(0)`,
                opacity: 0
            }
        ], {
            duration: 600,
            easing: 'ease-out'
        });

        animation.onfinish = () => particle.remove();
    }
}

/**
 * Create confetti effect
 */
function createConfetti() {
    const colors = ['#00ff00', '#ff00ff', '#00ffff', '#ffff00'];
    const confettiCount = 50;

    for (let i = 0; i < confettiCount; i++) {
        setTimeout(() => {
            const confetti = document.createElement('div');
            confetti.style.cssText = `
                position: fixed;
                left: ${Math.random() * window.innerWidth}px;
                top: -20px;
                width: ${4 + Math.random() * 8}px;
                height: ${4 + Math.random() * 8}px;
                background-color: ${colors[Math.floor(Math.random() * colors.length)]};
                pointer-events: none;
                z-index: 9999;
            `;

            document.body.appendChild(confetti);

            const animation = confetti.animate([
                {
                    transform: 'translateY(0) rotate(0deg)',
                    opacity: 1
                },
                {
                    transform: `translateY(${window.innerHeight + 20}px) rotate(${Math.random() * 720}deg)`,
                    opacity: 0
                }
            ], {
                duration: 2000 + Math.random() * 2000,
                easing: 'ease-in'
            });

            animation.onfinish = () => confetti.remove();
        }, i * 30);
    }
}

/**
 * Create fireworks effect
 */
function createFireworks() {
    const centerX = window.innerWidth / 2;
    const centerY = window.innerHeight / 2;
    const colors = ['#00ff00', '#ff00ff', '#00ffff', '#ffff00', '#ff0000'];

    for (let burst = 0; burst < 3; burst++) {
        setTimeout(() => {
            const burstX = centerX + (Math.random() - 0.5) * 400;
            const burstY = centerY + (Math.random() - 0.5) * 300;
            const color = colors[Math.floor(Math.random() * colors.length)];

            for (let i = 0; i < 24; i++) {
                const particle = document.createElement('div');
                particle.style.cssText = `
                    position: fixed;
                    left: ${burstX}px;
                    top: ${burstY}px;
                    width: 4px;
                    height: 4px;
                    background-color: ${color};
                    border-radius: 50%;
                    pointer-events: none;
                    z-index: 9999;
                    box-shadow: 0 0 10px ${color};
                `;

                document.body.appendChild(particle);

                const angle = (Math.PI * 2 * i) / 24;
                const velocity = 100 + Math.random() * 100;

                const animation = particle.animate([
                    {
                        transform: 'translate(0, 0) scale(1)',
                        opacity: 1
                    },
                    {
                        transform: `translate(${Math.cos(angle) * velocity}px, ${Math.sin(angle) * velocity + 50}px) scale(0)`,
                        opacity: 0
                    }
                ], {
                    duration: 1000,
                    easing: 'ease-out'
                });

                animation.onfinish = () => particle.remove();
            }
        }, burst * 400);
    }
}

/**
 * Screen shake effect
 * @param {string} direction - 'both', 'horizontal', or 'vertical'
 * @param {number} intensity - Shake intensity in pixels
 */
function screenShake(direction = 'both', intensity = 10) {
    const body = document.body;
    const originalTransform = body.style.transform;

    const frames = [];
    const frameCount = 10;

    for (let i = 0; i < frameCount; i++) {
        const progress = i / frameCount;
        const amplitude = intensity * (1 - progress);

        let x = 0, y = 0;

        if (direction === 'both' || direction === 'horizontal') {
            x = (Math.random() - 0.5) * amplitude * 2;
        }

        if (direction === 'both' || direction === 'vertical') {
            y = (Math.random() - 0.5) * amplitude * 2;
        }

        frames.push({
            transform: `translate(${x}px, ${y}px)`
        });
    }

    frames.push({ transform: originalTransform || 'none' });

    body.animate(frames, {
        duration: 400,
        easing: 'ease-out'
    });
}

/**
 * Flash effect
 * @param {string} color - Flash color
 */
function screenFlash(color = 'white') {
    const flash = document.createElement('div');
    flash.style.cssText = `
        position: fixed;
        top: 0;
        left: 0;
        right: 0;
        bottom: 0;
        background-color: ${color};
        pointer-events: none;
        z-index: 99999;
    `;

    document.body.appendChild(flash);

    flash.animate([
        { opacity: 0.7 },
        { opacity: 0 }
    ], {
        duration: 300,
        easing: 'ease-out'
    }).onfinish = () => flash.remove();
}

/**
 * Get hex color from name
 * @param {string} colorName - Color name
 * @returns {string} Hex color code
 */
function getColorHex(colorName) {
    const colorMap = {
        'green': '#00ff00',
        'red': '#ff0000',
        'blue': '#0000ff',
        'yellow': '#ffff00',
        'cyan': '#00ffff',
        'magenta': '#ff00ff',
        'white': '#ffffff'
    };

    return colorMap[colorName] || colorName;
}

/**
 * Animate number counting up
 * @param {HTMLElement} element - Element to animate
 * @param {number} from - Starting number
 * @param {number} to - Ending number
 * @param {number} duration - Animation duration in ms
 */
function animateNumber(element, from, to, duration = 600) {
    if (!element) return;

    const startTime = performance.now();
    const difference = to - from;

    function update(currentTime) {
        const elapsed = currentTime - startTime;
        const progress = Math.min(elapsed / duration, 1);

        const easeOutQuad = progress * (2 - progress); // Easing function
        const currentValue = Math.round(from + (difference * easeOutQuad));

        element.textContent = currentValue.toLocaleString();

        if (progress < 1) {
            requestAnimationFrame(update);
        }
    }

    requestAnimationFrame(update);
}

/**
 * Pulse animation for elements
 * @param {HTMLElement} element - Element to pulse
 * @param {number} duration - Pulse duration in ms
 */
function pulse(element, duration = 400) {
    if (!element) return;

    element.animate([
        { transform: 'scale(1)' },
        { transform: 'scale(1.1)' },
        { transform: 'scale(1)' }
    ], {
        duration,
        easing: 'ease-in-out'
    });
}

/**
 * Glow effect
 * @param {HTMLElement} element - Element to glow
 * @param {string} color - Glow color
 * @param {number} duration - Glow duration in ms
 */
function glow(element, color = '#00ff00', duration = 1000) {
    if (!element) return;

    element.animate([
        { boxShadow: `0 0 0 ${color}` },
        { boxShadow: `0 0 30px ${color}` },
        { boxShadow: `0 0 0 ${color}` }
    ], {
        duration,
        easing: 'ease-in-out'
    });
}

// Export functions for use in other modules
if (typeof module !== 'undefined' && module.exports) {
    module.exports = {
        playAnimation,
        createParticles,
        createConfetti,
        createFireworks,
        screenShake,
        screenFlash,
        animateNumber,
        pulse,
        glow
    };
}
