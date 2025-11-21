"""
Database models and operations for Educational Roguelike Game
Uses SQLite for storing questions, game saves, and statistics
"""

import sqlite3
import json
from datetime import datetime
from typing import List, Dict, Optional, Tuple
from contextlib import contextmanager
import config


class Database:
    """Main database class handling all SQLite operations"""
    def __init__(self, db_path: str = None):
        """Initialize database with path"""
        self.db_path = db_path or str(config.DATABASE_PATH)
        self.init_database()
    @contextmanager
    def get_connection(self):
        """Context manager for database connections"""
        conn = sqlite3.connect(self.db_path)
        conn.execute("PRAGMA foreign_keys = ON")  
        conn.row_factory = sqlite3.Row
        
        try:
            yield conn
            conn.commit()
        except Exception as e:
            conn.rollback()  
            raise e
        finally:
            conn.close()     


    def init_database(self):
        """Initialize database tables"""
        with self.get_connection() as conn:
            cursor = conn.cursor()

            # ═══════════════════════════════════════════════════════
            # 📄 PDFs Table
            # ═══════════════════════════════════════════════════════
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS pdfs (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    filename TEXT NOT NULL,
                    filepath TEXT NOT NULL UNIQUE,
                    title TEXT,
                    upload_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    num_pages INTEGER,
                    total_chars INTEGER,
                    processed BOOLEAN DEFAULT FALSE,
                    processing_date TIMESTAMP
                )
            ''')

            # ═══════════════════════════════════════════════════════
            # ❓ Questions Table
            # ═══════════════════════════════════════════════════════
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS questions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    pdf_id INTEGER NOT NULL,
                    question_text TEXT NOT NULL,
                    question_type TEXT NOT NULL,
                    correct_answer TEXT NOT NULL,
                    options TEXT,
                    explanation TEXT,
                    topic TEXT,
                    difficulty TEXT DEFAULT 'medium',
                    created_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    times_asked INTEGER DEFAULT 0,
                    times_correct INTEGER DEFAULT 0,
                    last_asked TIMESTAMP,
                    FOREIGN KEY (pdf_id) REFERENCES pdfs(id) ON DELETE CASCADE
                )
            ''')

            # ═══════════════════════════════════════════════════════
            # 💾 Game Saves Table
            # ═══════════════════════════════════════════════════════
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS game_saves (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    pdf_id INTEGER NOT NULL,
                    save_name TEXT NOT NULL,
                    player_hp INTEGER NOT NULL,
                    player_max_hp INTEGER NOT NULL,
                    player_level INTEGER NOT NULL,
                    current_encounter INTEGER NOT NULL,
                    score INTEGER DEFAULT 0,
                    active_powerups TEXT,
                    current_enemy TEXT,
                    game_state TEXT,
                    created_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    last_played TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    is_active BOOLEAN DEFAULT TRUE,
                    FOREIGN KEY (pdf_id) REFERENCES pdfs(id) ON DELETE CASCADE
                )
            ''')

            # ═══════════════════════════════════════════════════════
            # 📊 Statistics Table
            # ═══════════════════════════════════════════════════════
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS statistics (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    pdf_id INTEGER NOT NULL,
                    session_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    questions_answered INTEGER DEFAULT 0,
                    questions_correct INTEGER DEFAULT 0,
                    total_score INTEGER DEFAULT 0,
                    time_played_seconds INTEGER DEFAULT 0,
                    highest_encounter INTEGER DEFAULT 0,
                    enemies_defeated INTEGER DEFAULT 0,
                    game_completed BOOLEAN DEFAULT FALSE,
                    FOREIGN KEY (pdf_id) REFERENCES pdfs(id) ON DELETE CASCADE
                )
            ''')

            # ═══════════════════════════════════════════════════════
            # 📝 Answer History Table
            # ═══════════════════════════════════════════════════════
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS answer_history (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    question_id INTEGER NOT NULL,
                    pdf_id INTEGER NOT NULL,
                    session_id INTEGER,
                    user_answer TEXT NOT NULL,
                    is_correct BOOLEAN NOT NULL,
                    time_taken_seconds INTEGER,
                    answered_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (question_id) REFERENCES questions(id) ON DELETE CASCADE,
                    FOREIGN KEY (pdf_id) REFERENCES pdfs(id) ON DELETE CASCADE
                )
            ''')

            # Create indexes for better query performance
            cursor.execute('''
                CREATE INDEX IF NOT EXISTS idx_questions_pdf
                ON questions(pdf_id)
            ''')
            cursor.execute('''
                CREATE INDEX IF NOT EXISTS idx_questions_difficulty
                ON questions(difficulty)
            ''')
            cursor.execute('''
                CREATE INDEX IF NOT EXISTS idx_answer_history_question
                ON answer_history(question_id)
            ''')
            cursor.execute('''
                CREATE INDEX IF NOT EXISTS idx_answer_history_date
                ON answer_history(answered_date)
            ''')


# ═══════════════════════════════════════════════════════════════════
# 📄 PDF OPERATIONS
# ═══════════════════════════════════════════════════════════════════

class PDFManager:
    """Handles PDF-related database operations"""

    def __init__(self, db: Database):
        self.db = db

    def add_pdf(self, filename: str, filepath: str, title: str = None,
                num_pages: int = 0, total_chars: int = 0) -> int:
        """Add a new PDF to the database"""
        with self.db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO pdfs (filename, filepath, title, num_pages, total_chars)
                VALUES (?, ?, ?, ?, ?)
            ''', (filename, filepath, title or filename, num_pages, total_chars))
            return cursor.lastrowid

    def mark_processed(self, pdf_id: int):
        """Mark a PDF as processed"""
        with self.db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                UPDATE pdfs
                SET processed = TRUE, processing_date = CURRENT_TIMESTAMP
                WHERE id = ?
            ''', (pdf_id,))

    def get_pdf(self, pdf_id: int) -> Optional[Dict]:
        """Get PDF information by ID"""
        with self.db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT * FROM pdfs WHERE id = ?', (pdf_id,))
            row = cursor.fetchone()
            return dict(row) if row else None

    def get_all_pdfs(self) -> List[Dict]:
        """Get all PDFs"""
        with self.db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT * FROM pdfs ORDER BY upload_date DESC')
            return [dict(row) for row in cursor.fetchall()]

    def get_pdf_by_filepath(self, filepath: str) -> Optional[Dict]:
        """Get PDF by filepath"""
        with self.db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT * FROM pdfs WHERE filepath = ?', (filepath,))
            row = cursor.fetchone()
            return dict(row) if row else None


# ═══════════════════════════════════════════════════════════════════
# ❓ QUESTION OPERATIONS
# ═══════════════════════════════════════════════════════════════════

class QuestionManager:
    """Handles question-related database operations"""

    def __init__(self, db: Database):
        self.db = db

    def add_question(self, pdf_id: int, question_text: str, question_type: str,
                    correct_answer: str, options: List[str] = None,
                    explanation: str = None, topic: str = None,
                    difficulty: str = 'medium') -> int:
        """Add a new question to the database"""
        with self.db.get_connection() as conn:
            cursor = conn.cursor()
            options_json = json.dumps(options) if options else None
            cursor.execute('''
                INSERT INTO questions
                (pdf_id, question_text, question_type, correct_answer, options,
                 explanation, topic, difficulty)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ''', (pdf_id, question_text, question_type, correct_answer,
                  options_json, explanation, topic, difficulty))
            return cursor.lastrowid

    def add_questions_batch(self, questions: List[Dict]) -> int:
        """Add multiple questions at once"""
        with self.db.get_connection() as conn:
            cursor = conn.cursor()
            count = 0
            for q in questions:
                options_json = json.dumps(q.get('options')) if q.get('options') else None
                cursor.execute('''
                    INSERT INTO questions
                    (pdf_id, question_text, question_type, correct_answer, options,
                     explanation, topic, difficulty)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                ''', (q['pdf_id'], q['question_text'], q['question_type'],
                      q['correct_answer'], options_json, q.get('explanation'),
                      q.get('topic'), q.get('difficulty', 'medium')))
                count += 1
            return count

    def get_question(self, question_id: int) -> Optional[Dict]:
        """Get a specific question by ID"""
        with self.db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT * FROM questions WHERE id = ?', (question_id,))
            row = cursor.fetchone()
            if row:
                question = dict(row)
                if question['options']:
                    question['options'] = json.loads(question['options'])
                return question
            return None

    def get_random_question(self, pdf_id: int, difficulty: str = None,
                           exclude_recent: int = 20) -> Optional[Dict]:
        """Get a random question, avoiding recently asked ones"""
        with self.db.get_connection() as conn:
            cursor = conn.cursor()

            # Build query with optional difficulty filter
            query = '''
                SELECT * FROM questions
                WHERE pdf_id = ?
            '''
            params = [pdf_id]

            if difficulty:
                query += ' AND difficulty = ?'
                params.append(difficulty)

            # Exclude recently asked questions
            if exclude_recent > 0:
                query += '''
                    AND id NOT IN (
                        SELECT question_id FROM answer_history
                        WHERE pdf_id = ?
                        ORDER BY answered_date DESC
                        LIMIT ?
                    )
                '''
                params.extend([pdf_id, exclude_recent])

            query += ' ORDER BY RANDOM() LIMIT 1'

            cursor.execute(query, params)
            row = cursor.fetchone()

            if row:
                question = dict(row)
                if question['options']:
                    question['options'] = json.loads(question['options'])
                return question
            return None

    def update_question_stats(self, question_id: int, is_correct: bool):
        """Update question statistics after being answered"""
        with self.db.get_connection() as conn:
            cursor = conn.cursor()
            if is_correct:
                cursor.execute('''
                    UPDATE questions
                    SET times_asked = times_asked + 1,
                        times_correct = times_correct + 1,
                        last_asked = CURRENT_TIMESTAMP
                    WHERE id = ?
                ''', (question_id,))
            else:
                cursor.execute('''
                    UPDATE questions
                    SET times_asked = times_asked + 1,
                        last_asked = CURRENT_TIMESTAMP
                    WHERE id = ?
                ''', (question_id,))

    def get_question_count(self, pdf_id: int) -> int:
        """Get total number of questions for a PDF"""
        with self.db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT COUNT(*) as count FROM questions WHERE pdf_id = ?
            ''', (pdf_id,))
            return cursor.fetchone()['count']

    def get_questions_by_topic(self, pdf_id: int) -> Dict[str, int]:
        """Get question count grouped by topic"""
        with self.db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT topic, COUNT(*) as count
                FROM questions
                WHERE pdf_id = ?
                GROUP BY topic
            ''', (pdf_id,))
            return {row['topic']: row['count'] for row in cursor.fetchall()}


# ═══════════════════════════════════════════════════════════════════
# 💾 GAME SAVE OPERATIONS
# ═══════════════════════════════════════════════════════════════════

class GameSaveManager:
    """Handles game save operations"""

    def __init__(self, db: Database):
        self.db = db

    def create_save(self, pdf_id: int, save_name: str, player_hp: int,
                   player_max_hp: int, player_level: int, current_encounter: int,
                   score: int = 0, active_powerups: Dict = None,
                   current_enemy: Dict = None, game_state: Dict = None) -> int:
        """Create a new game save"""
        with self.db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO game_saves
                (pdf_id, save_name, player_hp, player_max_hp, player_level,
                 current_encounter, score, active_powerups, current_enemy, game_state)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (pdf_id, save_name, player_hp, player_max_hp, player_level,
                  current_encounter, score, json.dumps(active_powerups or {}),
                  json.dumps(current_enemy or {}), json.dumps(game_state or {})))
            return cursor.lastrowid

    def update_save(self, save_id: int, **kwargs):
        """Update an existing save"""
        with self.db.get_connection() as conn:
            cursor = conn.cursor()

            # Convert dict fields to JSON
            for key in ['active_powerups', 'current_enemy', 'game_state']:
                if key in kwargs and isinstance(kwargs[key], dict):
                    kwargs[key] = json.dumps(kwargs[key])

            set_clause = ', '.join([f"{k} = ?" for k in kwargs.keys()])
            set_clause += ', last_played = CURRENT_TIMESTAMP'
            values = list(kwargs.values()) + [save_id]

            cursor.execute(f'''
                UPDATE game_saves
                SET {set_clause}
                WHERE id = ?
            ''', values)

    def get_save(self, save_id: int) -> Optional[Dict]:
        """Get a game save by ID"""
        with self.db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT * FROM game_saves WHERE id = ?', (save_id,))
            row = cursor.fetchone()
            if row:
                save = dict(row)
                # Parse JSON fields
                for key in ['active_powerups', 'current_enemy', 'game_state']:
                    if save.get(key):
                        save[key] = json.loads(save[key])
                return save
            return None

    def get_saves_for_pdf(self, pdf_id: int) -> List[Dict]:
        """Get all saves for a specific PDF"""
        with self.db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT * FROM game_saves
                WHERE pdf_id = ? AND is_active = TRUE
                ORDER BY last_played DESC
            ''', (pdf_id,))
            saves = []
            for row in cursor.fetchall():
                save = dict(row)
                for key in ['active_powerups', 'current_enemy', 'game_state']:
                    if save.get(key):
                        save[key] = json.loads(save[key])
                saves.append(save)
            return saves

    def delete_save(self, save_id: int):
        """Mark a save as inactive"""
        with self.db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                UPDATE game_saves SET is_active = FALSE WHERE id = ?
            ''', (save_id,))


# ═══════════════════════════════════════════════════════════════════
# 📊 STATISTICS OPERATIONS
# ═══════════════════════════════════════════════════════════════════

class StatisticsManager:
    """Handles statistics and answer history"""

    def __init__(self, db: Database):
        self.db = db

    def record_answer(self, question_id: int, pdf_id: int, user_answer: str,
                     is_correct: bool, time_taken: int = None, session_id: int = None):
        """Record an answer in the history"""
        with self.db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO answer_history
                (question_id, pdf_id, session_id, user_answer, is_correct, time_taken_seconds)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', (question_id, pdf_id, session_id, user_answer, is_correct, time_taken))

    def create_session(self, pdf_id: int) -> int:
        """Create a new statistics session"""
        with self.db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO statistics (pdf_id) VALUES (?)
            ''', (pdf_id,))
            return cursor.lastrowid

    def update_session(self, session_id: int, **kwargs):
        """Update session statistics"""
        with self.db.get_connection() as conn:
            cursor = conn.cursor()
            set_clause = ', '.join([f"{k} = ?" for k in kwargs.keys()])
            values = list(kwargs.values()) + [session_id]
            cursor.execute(f'''
                UPDATE statistics SET {set_clause} WHERE id = ?
            ''', values)

    def get_overall_stats(self, pdf_id: int) -> Dict:
        """Get overall statistics for a PDF"""
        with self.db.get_connection() as conn:
            cursor = conn.cursor()

            # Overall accuracy
            cursor.execute('''
                SELECT
                    COUNT(*) as total_answers,
                    SUM(CASE WHEN is_correct THEN 1 ELSE 0 END) as correct_answers
                FROM answer_history WHERE pdf_id = ?
            ''', (pdf_id,))
            accuracy_row = cursor.fetchone()

            # Total time played
            cursor.execute('''
                SELECT SUM(time_played_seconds) as total_time
                FROM statistics WHERE pdf_id = ?
            ''', (pdf_id,))
            time_row = cursor.fetchone()

            # Total score
            cursor.execute('''
                SELECT SUM(total_score) as total_score
                FROM statistics WHERE pdf_id = ?
            ''', (pdf_id,))
            score_row = cursor.fetchone()

            # Games completed
            cursor.execute('''
                SELECT COUNT(*) as completed_games
                FROM statistics WHERE pdf_id = ? AND game_completed = TRUE
            ''', (pdf_id,))
            games_row = cursor.fetchone()

            total = accuracy_row['total_answers'] or 0
            correct = accuracy_row['correct_answers'] or 0

            return {
                'total_answers': total,
                'correct_answers': correct,
                'accuracy': (correct / total * 100) if total > 0 else 0,
                'total_time_seconds': time_row['total_time'] or 0,
                'total_score': score_row['total_score'] or 0,
                'completed_games': games_row['completed_games'] or 0
            }

    def get_topic_performance(self, pdf_id: int) -> List[Dict]:
        """Get performance broken down by topic"""
        with self.db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT
                    q.topic,
                    COUNT(ah.id) as attempts,
                    SUM(CASE WHEN ah.is_correct THEN 1 ELSE 0 END) as correct,
                    AVG(CASE WHEN ah.is_correct THEN 100.0 ELSE 0 END) as accuracy
                FROM answer_history ah
                JOIN questions q ON ah.question_id = q.id
                WHERE ah.pdf_id = ?
                GROUP BY q.topic
                ORDER BY accuracy DESC
            ''', (pdf_id,))
            return [dict(row) for row in cursor.fetchall()]

    def get_weak_areas(self, pdf_id: int, threshold: float = 60.0) -> List[Dict]:
        """Identify topics/questions where user struggles"""
        with self.db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT
                    q.topic,
                    q.difficulty,
                    COUNT(ah.id) as attempts,
                    SUM(CASE WHEN ah.is_correct THEN 1 ELSE 0 END) as correct,
                    AVG(CASE WHEN ah.is_correct THEN 100.0 ELSE 0 END) as accuracy
                FROM answer_history ah
                JOIN questions q ON ah.question_id = q.id
                WHERE ah.pdf_id = ? AND q.times_asked >= 3
                GROUP BY q.topic, q.difficulty
                HAVING accuracy < ?
                ORDER BY accuracy ASC
            ''', (pdf_id, threshold))
            return [dict(row) for row in cursor.fetchall()]

    def get_recent_activity(self, pdf_id: int, limit: int = 20) -> List[Dict]:
        """Get recent answer history"""
        with self.db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT
                    ah.*,
                    q.question_text,
                    q.topic,
                    q.difficulty
                FROM answer_history ah
                JOIN questions q ON ah.question_id = q.id
                WHERE ah.pdf_id = ?
                ORDER BY ah.answered_date DESC
                LIMIT ?
            ''', (pdf_id, limit))
            return [dict(row) for row in cursor.fetchall()]


# ═══════════════════════════════════════════════════════════════════
# 🚀 INITIALIZE DATABASE SINGLETON
# ═══════════════════════════════════════════════════════════════════

# Create global database instance
db = Database()
pdf_manager = PDFManager(db)
question_manager = QuestionManager(db)
save_manager = GameSaveManager(db)
stats_manager = StatisticsManager(db)
