"""
Game Engine for Educational Roguelike
Handles combat, progression, enemies, and game state
"""

import random
import logging
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass, asdict
from datetime import datetime

import config
from database import question_manager, save_manager, stats_manager

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


# ═══════════════════════════════════════════════════════════════════
# 📦 DATA CLASSES
# ═══════════════════════════════════════════════════════════════════

@dataclass
class Player:
    """Player character state"""
    hp: int
    max_hp: int
    level: int
    score: int
    damage_boost: float = 1.0
    shield: int = 0
    score_boost: float = 1.0

    def to_dict(self) -> Dict:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict):
        return cls(**data)


@dataclass
class Enemy:
    """Enemy character state"""
    enemy_type: str
    name: str
    emoji: str
    hp: int
    max_hp: int
    damage: int
    score_value: int
    difficulty: int
    is_boss: bool = False

    def to_dict(self) -> Dict:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict):
        return cls(**data)


@dataclass
class GameState:
    """Complete game state"""
    pdf_id: int
    player: Player
    current_enemy: Optional[Enemy]
    current_encounter: int
    total_encounters: int
    session_id: int
    questions_answered: int
    questions_correct: int
    start_time: str
    active_powerups: Dict
    inventory: List[str] = None
    failed_question_ids: List[int] = None

    def __post_init__(self):
        if self.inventory is None:
            self.inventory = []
        if self.failed_question_ids is None:
            self.failed_question_ids = []

    def to_dict(self) -> Dict:
        data = asdict(self)
        data['player'] = self.player.to_dict()
        data['current_enemy'] = self.current_enemy.to_dict() if self.current_enemy else None
        return data

    @classmethod
    def from_dict(cls, data: Dict):
        data['player'] = Player.from_dict(data['player'])
        if data.get('current_enemy'):
            data['current_enemy'] = Enemy.from_dict(data['current_enemy'])
        if 'inventory' not in data:
            data['inventory'] = []
        return cls(**data)


# ═══════════════════════════════════════════════════════════════════
# 🎮 GAME ENGINE
# ═══════════════════════════════════════════════════════════════════

class GameEngine:
    """Main game engine managing all game logic"""

    def __init__(self, pdf_id: int):
        self.pdf_id = pdf_id
        self.state: Optional[GameState] = None

    def new_game(self) -> GameState:
        """Start a new game"""
        # Create player
        player = Player(
            hp=config.PLAYER_MAX_HP,
            max_hp=config.PLAYER_MAX_HP,
            level=config.PLAYER_STARTING_LEVEL,
            score=0
        )

        # Create statistics session
        session_id = stats_manager.create_session(self.pdf_id)

        # Create initial game state
        self.state = GameState(
            pdf_id=self.pdf_id,
            player=player,
            current_enemy=None,
            current_encounter=1,
            total_encounters=config.TOTAL_ENCOUNTERS,
            session_id=session_id,
            questions_answered=0,
            questions_correct=0,
            start_time=datetime.now().isoformat(),
            active_powerups={}
        )

        # Generate first enemy
        self.state.current_enemy = self._generate_enemy(1)

        logger.info(f"New game started for PDF {self.pdf_id}")
        return self.state
    
    def load_game(self, save_id: int) -> Optional[GameState]:
        """Load a saved game"""
        save_data = save_manager.get_save(save_id)

        if not save_data:
            logger.error(f"Save {save_id} not found")
            return None

        extra_state = save_data.get('game_state') or {}
        
        current_enemy = None
        enemy_data = save_data.get('current_enemy')
        if enemy_data:
            if isinstance(enemy_data, dict):
                current_enemy = Enemy.from_dict(enemy_data)
            else:
                logger.warning("Enemy data was not a dict, trying to generate new one")
                
        if not current_enemy:
             current_enemy = self._generate_enemy(save_data['current_encounter'])

        self.state = GameState(
            pdf_id=save_data['pdf_id'],
            player=Player(
                hp=save_data['player_hp'],
                max_hp=save_data['player_max_hp'],
                level=save_data['player_level'],
                score=save_data['score']
            ),
            current_enemy=current_enemy,
            current_encounter=save_data['current_encounter'],
            total_encounters=config.TOTAL_ENCOUNTERS,
            session_id=extra_state.get('session_id', 0),
            questions_answered=extra_state.get('questions_answered', 0),
            questions_correct=extra_state.get('questions_correct', 0),
            failed_question_ids=extra_state.get('failed_question_ids', []),
            start_time=datetime.now().isoformat(),
            active_powerups=save_data.get('active_powerups', {}),
            inventory=extra_state.get('inventory', [])
        )

        logger.info(f"Game loaded from save {save_id}")
        return self.state

        logger.info(f"Game loaded from save {save_id}")
        return self.state
    
    def save_game(self, save_name: str = None) -> int:
        """Save current game state"""
        if not self.state:
            raise ValueError("No active game to save")

        save_name = save_name or f"Save {datetime.now().strftime('%Y-%m-%d %H:%M')}"

        current_enemy_data = None
        if self.state.current_enemy:
            if hasattr(self.state.current_enemy, 'to_dict'):
                current_enemy_data = self.state.current_enemy.to_dict()
            else:
                current_enemy_data = self.state.current_enemy

        extra_state = {
            'session_id': self.state.session_id,
            'questions_answered': self.state.questions_answered,
            'questions_correct': self.state.questions_correct,
            'failed_question_ids': self.state.failed_question_ids,
            'inventory': self.state.inventory
        }

        save_id = save_manager.create_save(
            pdf_id=self.state.pdf_id,
            save_name=save_name,
            player_hp=self.state.player.hp,
            player_max_hp=self.state.player.max_hp,
            player_level=self.state.player.level,
            current_encounter=self.state.current_encounter,
            score=self.state.player.score,
            active_powerups=self.state.active_powerups,
            current_enemy=current_enemy_data, 
            game_state=extra_state
        )

        logger.info(f"Game saved with ID {save_id}")
        return save_id

    def _generate_enemy(self, encounter_num: int) -> Enemy:
        """
        Generate an enemy appropriate for the encounter number

        Difficulty scales with encounter number
        Final encounter is always a boss
        """
        # Calculate difficulty tier based on encounter
        progress = encounter_num / self.state.total_encounters
        scaling_factor = 1.0 + (progress * (config.DIFFICULTY_SCALING - 1.0))

        # Check if this is the final encounter (boss fight)
        if encounter_num == self.state.total_encounters:
            # Generate boss enemy
            boss_type = random.choice(list(config.BOSS_TYPES.keys()))
            enemy_data = config.BOSS_TYPES[boss_type].copy()

            enemy = Enemy(
                enemy_type=boss_type,
                name=enemy_data['name'],
                emoji=enemy_data['emoji'],
                hp=enemy_data['hp'],  # Boss HP doesn't scale
                max_hp=enemy_data['hp'],
                damage=enemy_data['damage'],  # Boss damage doesn't scale
                score_value=enemy_data['score'],
                difficulty=enemy_data['difficulty'],
                is_boss=True
            )

            logger.info(f"Generated BOSS {enemy.name} for final encounter!")
            return enemy

        # Select enemy types based on difficulty
        if progress < 0.3:
            # Early game: easier enemies
            pool = ['slime', 'skeleton', 'ghost']
        elif progress < 0.7:
            # Mid game: medium enemies
            pool = ['skeleton', 'ghost', 'zombie']
        else:
            # Late game: harder enemies
            pool = ['zombie', 'demon', 'dragon']

        enemy_type = random.choice(pool)
        enemy_data = config.ENEMY_TYPES[enemy_type].copy()

        # Scale stats
        enemy = Enemy(
            enemy_type=enemy_type,
            name=enemy_data['name'],
            emoji=enemy_data['emoji'],
            hp=int(enemy_data['hp'] * scaling_factor),
            max_hp=int(enemy_data['hp'] * scaling_factor),
            damage=int(enemy_data['damage'] * scaling_factor),
            score_value=int(enemy_data['score'] * scaling_factor),
            difficulty=enemy_data['difficulty'],
            is_boss=False
        )

        logger.info(f"Generated {enemy.name} for encounter {encounter_num} (scaling: {scaling_factor:.2f}x)")
        return enemy

    def get_question(self) -> Optional[Dict]:
        """
        Get a question. Prioritizes new questions, falls back to failed questions.
        """
        if not self.state or not self.state.current_enemy:
            return None

        difficulty_map = {1: 'easy', 2: 'easy', 3: 'medium', 4: 'medium', 5: 'hard'}
        difficulty = difficulty_map.get(self.state.current_enemy.difficulty, 'medium')

        question = question_manager.get_random_question(
            pdf_id=self.pdf_id,
            difficulty=difficulty,
            exclude_recent=config.QUESTION_BUFFER
        )

        if not question and self.state.failed_question_ids:
            import random
            recycled_id = random.choice(self.state.failed_question_ids)
            logger.info(f"Recycling failed question ID: {recycled_id}")

            question = question_manager.get_question(recycled_id)
            
            if question:
                question['is_review'] = True 
                question['question_text'] = f"🔄 REPASO: {question['question_text']}"

        if not question:

            question = question_manager.get_random_question(
                pdf_id=self.pdf_id,
                difficulty=None,
                exclude_recent=0
            )

        return question

    def answer_question(self, question_id: int, user_answer: str, correct_answer: str) -> Dict:
        """
        Process a question answer and update game state

        Returns:
            Dict with result information
        """
        if not self.state:
            raise ValueError("No active game")

        is_correct = user_answer.strip().lower() == correct_answer.strip().lower()
        
        if not is_correct:
            if question_id not in self.state.failed_question_ids:
                self.state.failed_question_ids.append(question_id)
                logger.info(f"Question {question_id} added to review queue")
        else:
            if question_id in self.state.failed_question_ids:
                self.state.failed_question_ids.remove(question_id)
                logger.info(f"Question {question_id} removed from review queue (mastered)")

        # Update question stats
        question_manager.update_question_stats(question_id, is_correct)

        # Record answer in history
        stats_manager.record_answer(
            question_id=question_id,
            pdf_id=self.pdf_id,
            user_answer=user_answer,
            is_correct=is_correct,
            session_id=self.state.session_id
        )

        # Update game state
        self.state.questions_answered += 1
        if is_correct:
            self.state.questions_correct += 1

        result = {
            'is_correct': is_correct,
            'damage_dealt': 0,
            'damage_received': 0,
            'enemy_defeated': False,
            'player_died': False,
            'powerup_gained': None,
            'score_gained': 0
        }

        if is_correct:
            # Player attacks enemy
            damage = int(config.PLAYER_BASE_DAMAGE * self.state.player.damage_boost)
            self.state.current_enemy.hp -= damage
            result['damage_dealt'] = damage

            # Check if enemy is defeated
            if self.state.current_enemy.hp <= 0:
                result['enemy_defeated'] = True
                score_gained = int(self.state.current_enemy.score_value * self.state.player.score_boost)
                self.state.player.score += score_gained
                result['score_gained'] = score_gained

                # Check for powerup drop (now goes to inventory)
                powerup = self._try_powerup_drop()
                if powerup:
                    self.state.inventory.append(powerup)
                    result['powerup_gained'] = powerup

                # Progress to next encounter
                self.state.current_encounter += 1

                if self.state.current_encounter <= self.state.total_encounters:
                    self.state.current_enemy = self._generate_enemy(self.state.current_encounter)
                else:
                    # Game won!
                    result['game_won'] = True
                    self._complete_game()

        else:
            # Enemy attacks player
            damage = self.state.current_enemy.damage

            # Apply shield
            if self.state.player.shield > 0:
                shield_absorbed = min(self.state.player.shield, damage)
                self.state.player.shield -= shield_absorbed
                damage -= shield_absorbed

            self.state.player.hp -= damage
            result['damage_received'] = damage

            # Check if player died
            if self.state.player.hp <= 0:
                result['player_died'] = True
                self._game_over()

        return result

    def _try_powerup_drop(self) -> Optional[str]:
        """Randomly try to drop a powerup"""
        for powerup_id, powerup_data in config.POWERUPS.items():
            if random.random() < powerup_data['chance']:
                return powerup_id
        return None

    def use_powerup(self, powerup_id: str) -> Dict:
        """
        Use a powerup from inventory

        Returns:
            Dict with result information
        """
        if not self.state:
            raise ValueError("No active game")

        if powerup_id not in self.state.inventory:
            raise ValueError(f"Powerup {powerup_id} not in inventory")

        # Remove from inventory
        self.state.inventory.remove(powerup_id)

        # Apply powerup effect
        self._apply_powerup(powerup_id)

        return {
            'success': True,
            'powerup_id': powerup_id,
            'game_status': self.get_game_status()
        }

    def _apply_powerup(self, powerup_id: str):
        """Apply a powerup effect to the player"""
        powerup_data = config.POWERUPS[powerup_id]
        effect = powerup_data['effect']
        value = powerup_data['value']

        if effect == 'heal':
            self.state.player.hp = min(
                self.state.player.max_hp,
                self.state.player.hp + value
            )
        elif effect == 'shield':
            self.state.player.shield += value
        elif effect == 'damage_boost':
            self.state.player.damage_boost *= value
            self.state.active_powerups['damage_boost'] = True
        elif effect == 'score_boost':
            self.state.player.score_boost *= value
            self.state.active_powerups['score_boost'] = True

        logger.info(f"Applied powerup: {powerup_id}")

    def _complete_game(self):
        """Handle game completion"""
        stats_manager.update_session(
            session_id=self.state.session_id,
            questions_answered=self.state.questions_answered,
            questions_correct=self.state.questions_correct,
            total_score=self.state.player.score,
            highest_encounter=self.state.current_encounter,
            enemies_defeated=self.state.current_encounter - 1,
            game_completed=True
        )
        logger.info(f"Game completed! Score: {self.state.player.score}")

    def _game_over(self):
        """Handle game over"""
        stats_manager.update_session(
            session_id=self.state.session_id,
            questions_answered=self.state.questions_answered,
            questions_correct=self.state.questions_correct,
            total_score=self.state.player.score,
            highest_encounter=self.state.current_encounter,
            enemies_defeated=self.state.current_encounter - 1,
            game_completed=False
        )
        logger.info(f"Game over at encounter {self.state.current_encounter}")

    def get_game_status(self) -> Dict:
        """Get current game status for UI"""
        if not self.state:
            return {'active': False}

        return {
            'active': True,
            'player': {
                'hp': self.state.player.hp,
                'max_hp': self.state.player.max_hp,
                'hp_percent': (self.state.player.hp / self.state.player.max_hp) * 100,
                'level': self.state.player.level,
                'score': self.state.player.score,
                'shield': self.state.player.shield,
                'damage_boost': self.state.player.damage_boost,
                'score_boost': self.state.player.score_boost
            },
            'enemy': {
                'type': self.state.current_enemy.enemy_type,
                'name': self.state.current_enemy.name,
                'emoji': self.state.current_enemy.emoji,
                'hp': self.state.current_enemy.hp,
                'max_hp': self.state.current_enemy.max_hp,
                'hp_percent': (self.state.current_enemy.hp / self.state.current_enemy.max_hp) * 100,
                'damage': self.state.current_enemy.damage,
                'is_boss': self.state.current_enemy.is_boss
            } if self.state.current_enemy else None,
            'progress': {
                'current_encounter': self.state.current_encounter,
                'total_encounters': self.state.total_encounters,
                'percent': (self.state.current_encounter / self.state.total_encounters) * 100
            },
            'stats': {
                'questions_answered': self.state.questions_answered,
                'questions_correct': self.state.questions_correct,
                'accuracy': (self.state.questions_correct / self.state.questions_answered * 100)
                    if self.state.questions_answered > 0 else 0
            },
            'active_powerups': self.state.active_powerups,
            'inventory': self.state.inventory
        }


# ═══════════════════════════════════════════════════════════════════
# 🎲 UTILITY FUNCTIONS
# ═══════════════════════════════════════════════════════════════════

def validate_pdf_ready(pdf_id: int) -> Tuple[bool, str]:
    """
    Check if a PDF has enough questions to start a game

    Returns:
        (is_ready, message)
    """
    question_count = question_manager.get_question_count(pdf_id)

    if question_count < config.MIN_QUESTIONS_TO_START:
        return False, f"Need at least {config.MIN_QUESTIONS_TO_START} questions. Currently have {question_count}."

    return True, f"Ready to play with {question_count} questions!"


def get_difficulty_recommendation(encounter_num: int, total_encounters: int) -> str:
    """Get recommended question difficulty for an encounter"""
    progress = encounter_num / total_encounters

    if progress < 0.3:
        return 'easy'
    elif progress < 0.7:
        return 'medium'
    else:
        return 'hard'


def calculate_minimum_questions_needed() -> int:
    """
    Calculate minimum questions needed to complete a full run

    This calculates how many correct answers are needed to defeat all enemies,
    then adds a multiplier to account for incorrect answers

    Returns:
        Recommended minimum number of questions to generate
    """
    total_hp = 0

    # Calculate HP for regular encounters (1 to TOTAL_ENCOUNTERS - 1)
    for encounter in range(1, config.TOTAL_ENCOUNTERS):
        progress = encounter / config.TOTAL_ENCOUNTERS
        scaling_factor = 1.0 + (progress * (config.DIFFICULTY_SCALING - 1.0))

        # Estimate average enemy HP for this encounter
        if progress < 0.3:
            avg_hp = 40  # Average of slime, skeleton, ghost
        elif progress < 0.7:
            avg_hp = 55  # Average of skeleton, ghost, zombie
        else:
            avg_hp = 93  # Average of zombie, demon, dragon

        total_hp += int(avg_hp * scaling_factor)

    # Add boss HP (final encounter)
    avg_boss_hp = sum(boss['hp'] for boss in config.BOSS_TYPES.values()) / len(config.BOSS_TYPES)
    total_hp += int(avg_boss_hp)

    # Calculate questions needed if all answers are correct
    questions_if_perfect = total_hp // config.PLAYER_BASE_DAMAGE + 1

    # Add multiplier for incorrect answers (assume 60% accuracy)
    # If 60% correct, need more questions
    recommended_questions = int(questions_if_perfect / 0.6)

    # Add buffer for safety
    recommended_questions = int(recommended_questions * 1.2)

    # Ensure minimum
    recommended_questions = max(recommended_questions, config.MIN_QUESTIONS_TO_START * 3)

    logger.info(f"Calculated minimum questions needed: {recommended_questions} (total enemy HP: {total_hp})")

    return recommended_questions
