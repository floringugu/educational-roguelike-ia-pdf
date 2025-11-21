"""
Flask Application for Educational Roguelike Game
Main server with routes for game, PDF upload, and statistics
"""
import uuid
from dotenv import load_dotenv # Necesario para cargar las claves API

load_dotenv() # Carga el .env al iniciar
from flask import Flask, render_template, request, jsonify, send_file, session
from werkzeug.utils import secure_filename
import logging
from pathlib import Path
import os

import config
from database import pdf_manager, question_manager, save_manager, stats_manager
from pdf_processor import PDFProcessor, PDFManager as PDFMgr, allowed_file, save_uploaded_file
from question_generator import QuestionGenerator, process_pdf_and_generate_questions
from game_engine import GameEngine, validate_pdf_ready
from stats_exporter import StatsExporter, LearningAnalyzer, export_stats_for_pdf

# ═══════════════════════════════════════════════════════════════════
# 🚀 FLASK APP INITIALIZATION
# ═══════════════════════════════════════════════════════════════════

app = Flask(__name__)
app.secret_key = config.SECRET_KEY
app.config['MAX_CONTENT_LENGTH'] = config.MAX_CONTENT_LENGTH

@app.before_request
def make_session_permanent():
    session.permanent = True
    if 'user_id' not in session:
        session['user_id'] = str(uuid.uuid4())

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Store active game sessions (in-memory)
# In production, use Redis or database
game_sessions = {}


# ═══════════════════════════════════════════════════════════════════
# 🏠 PAGE ROUTES
# ═══════════════════════════════════════════════════════════════════

@app.route('/')
def index():
    """Home page - show available PDFs"""
    pdfs = pdf_manager.get_all_pdfs()

    # Enrich with question counts
    for pdf in pdfs:
        pdf['question_count'] = question_manager.get_question_count(pdf['id'])
        pdf['ready_to_play'] = pdf['question_count'] >= config.MIN_QUESTIONS_TO_START

    return render_template('index.html', pdfs=pdfs)


@app.route('/upload')
def upload_page():
    """PDF upload page"""
    return render_template('upload.html')


@app.route('/game/<int:pdf_id>')
def game_page(pdf_id):
    """Game page for a specific PDF"""
    pdf_info = pdf_manager.get_pdf(pdf_id)

    if not pdf_info:
        return "PDF not found", 404

    # Check if ready to play
    is_ready, message = validate_pdf_ready(pdf_id)

    question_count = question_manager.get_question_count(pdf_id)

    return render_template(
        'game.html',
        pdf=pdf_info,
        ready=is_ready,
        message=message,
        question_count=question_count
    )


@app.route('/stats/<int:pdf_id>')
def stats_page(pdf_id):
    """Statistics page for a specific PDF"""
    pdf_info = pdf_manager.get_pdf(pdf_id)

    if not pdf_info:
        return "PDF not found", 404

    # Get overall stats
    overall = stats_manager.get_overall_stats(pdf_id)
    topic_performance = stats_manager.get_topic_performance(pdf_id)
    weak_areas = stats_manager.get_weak_areas(pdf_id)

    # Get learning insights
    analyzer = LearningAnalyzer(pdf_id)
    insights = analyzer.get_learning_insights()

    return render_template(
        'stats.html',
        pdf=pdf_info,
        overall=overall,
        topics=topic_performance,
        weak_areas=weak_areas,
        insights=insights
    )


@app.route('/saves/<int:pdf_id>')
def saves_page(pdf_id):
    """Saved games page"""
    pdf_info = pdf_manager.get_pdf(pdf_id)

    if not pdf_info:
        return "PDF not found", 404

    saves = save_manager.get_saves_for_pdf(pdf_id)

    return render_template('saves.html', pdf=pdf_info, saves=saves)


# ═══════════════════════════════════════════════════════════════════
# 📤 PDF UPLOAD & PROCESSING API
# ═══════════════════════════════════════════════════════════════════

@app.route('/api/upload', methods=['POST'])
def upload_pdf():
    """Upload and process a PDF file"""
    try:
        if 'file' not in request.files:
            return jsonify({'error': 'No file provided'}), 400

        file = request.files['file']

        if file.filename == '':
            return jsonify({'error': 'No file selected'}), 400

        if not allowed_file(file.filename):
            return jsonify({'error': 'Only PDF files are allowed'}), 400

        # Save file
        filepath = save_uploaded_file(file)

        # Process PDF
        pdf_mgr = PDFMgr()
        result = pdf_mgr.process_and_store_pdf(filepath)

        return jsonify({
            'success': True,
            'pdf_id': result['pdf_id'],
            'title': result['title'],
            'num_pages': result['num_pages'],
            'estimated_questions': result['estimated_questions'],
            'message': 'PDF uploaded successfully'
        })

    except Exception as e:
        logger.error(f"Upload error: {str(e)}")
        return jsonify({'error': str(e)}), 500


@app.route('/api/generate-questions/<int:pdf_id>', methods=['POST'])
def generate_questions(pdf_id):
    """Generate questions from a PDF using Claude API"""
    try:
        data = request.get_json() or {}
        num_questions = data.get('num_questions', config.QUESTIONS_PER_BATCH)

        # Get PDF info
        pdf_info = pdf_manager.get_pdf(pdf_id)
        if not pdf_info:
            return jsonify({'error': 'PDF not found'}), 404

        # Check if already processed
        existing_count = question_manager.get_question_count(pdf_id)
        if existing_count >= num_questions:
            return jsonify({
                'success': True,
                'message': f'Already have {existing_count} questions',
                'questions_generated': 0,
                'total_questions': existing_count
            })

        # Re-process PDF to get text
        pdf_processor = PDFProcessor()
        extracted = pdf_processor.extract_text_from_pdf(pdf_info['filepath'])

        # Generate questions
        result = process_pdf_and_generate_questions(
            pdf_id=pdf_id,
            text=extracted['text'],
            chunks=extracted['chunks'],
            num_questions=num_questions
        )

        return jsonify({
            'success': True,
            'questions_generated': result['questions_generated'],
            'questions_saved': result['questions_saved'],
            'cost_estimate': result['cost_estimate'],
            'message': f"Generated {result['questions_saved']} questions"
        })

    except Exception as e:
        logger.error(f"Question generation error: {str(e)}")
        return jsonify({'error': str(e)}), 500


@app.route('/api/pdf/<int:pdf_id>/estimate', methods=['GET'])
def estimate_cost(pdf_id):
    """Estimate cost of generating questions for a PDF"""
    try:
        pdf_info = pdf_manager.get_pdf(pdf_id)
        if not pdf_info:
            return jsonify({'error': 'PDF not found'}), 404

        num_questions = request.args.get('num_questions', config.QUESTIONS_PER_BATCH, type=int)

        generator = QuestionGenerator()
        estimate = generator.estimate_cost(pdf_info['total_chars'], num_questions)

        return jsonify({
            'success': True,
            'estimate': estimate,
            'pdf_chars': pdf_info['total_chars']
        })

    except Exception as e:
        logger.error(f"Cost estimation error: {str(e)}")
        return jsonify({'error': str(e)}), 500


# ═══════════════════════════════════════════════════════════════════
# 🎮 GAME API
# ═══════════════════════════════════════════════════════════════════

@app.route('/api/game/new/<int:pdf_id>', methods=['POST'])
def new_game(pdf_id):
    """Start a new game"""
    try:
        # Check if PDF has enough questions
        is_ready, message = validate_pdf_ready(pdf_id)
        if not is_ready:
            return jsonify({'error': message}), 400

        # Create game engine
        game = GameEngine(pdf_id)
        state = game.new_game()

        # Store in session
        session_key = f"game_{pdf_id}_{session.get('user_id', 'default')}"
        game_sessions[session_key] = game

        return jsonify({
            'success': True,
            'game_status': game.get_game_status(),
            'message': 'New game started!'
        })

    except Exception as e:
        logger.error(f"New game error: {str(e)}")
        return jsonify({'error': str(e)}), 500


@app.route('/api/game/status/<int:pdf_id>', methods=['GET'])
def game_status(pdf_id):
    """Get current game status"""
    try:
        session_key = f"game_{pdf_id}_{session.get('user_id', 'default')}"

        if session_key not in game_sessions:
            return jsonify({'active': False})

        game = game_sessions[session_key]
        status = game.get_game_status()

        return jsonify(status)

    except Exception as e:
        logger.error(f"Game status error: {str(e)}")
        return jsonify({'error': str(e)}), 500


@app.route('/api/game/question/<int:pdf_id>', methods=['GET'])
def get_question(pdf_id):
    """Get next question for the game"""
    try:
        session_key = f"game_{pdf_id}_{session.get('user_id', 'default')}"

        if session_key not in game_sessions:
            return jsonify({'error': 'No active game'}), 400

        game = game_sessions[session_key]
        question = game.get_question()

        if not question:
            return jsonify({'error': 'No questions available'}), 404

        # Don't send correct answer to client!
        safe_question = {
            'id': question['id'],
            'question_text': question['question_text'],
            'question_type': question['question_type'],
            'options': question['options'],
            'topic': question.get('topic'),
            'difficulty': question.get('difficulty')
        }

        return jsonify(safe_question)

    except Exception as e:
        logger.error(f"Get question error: {str(e)}")
        return jsonify({'error': str(e)}), 500


@app.route('/api/game/answer/<int:pdf_id>', methods=['POST'])
def answer_question(pdf_id):
    """Submit an answer to a question"""
    try:
        session_key = f"game_{pdf_id}_{session.get('user_id', 'default')}"

        if session_key not in game_sessions:
            return jsonify({'error': 'No active game'}), 400

        data = request.get_json()
        question_id = data.get('question_id')
        user_answer = data.get('answer')

        if not question_id or user_answer is None:
            return jsonify({'error': 'Missing question_id or answer'}), 400

        # Get correct answer from database
        question = question_manager.get_question(question_id)
        if not question:
            return jsonify({'error': 'Question not found'}), 404

        # Process answer
        game = game_sessions[session_key]
        result = game.answer_question(question_id, user_answer, question['correct_answer'])

        # Add explanation and correct answer to result
        result['explanation'] = question['explanation']
        result['correct_answer'] = question['correct_answer']

        # Get updated game status
        result['game_status'] = game.get_game_status()

        return jsonify(result)

    except Exception as e:
        logger.error(f"Answer question error: {str(e)}")
        return jsonify({'error': str(e)}), 500


@app.route('/api/game/use-powerup/<int:pdf_id>', methods=['POST'])
def use_powerup(pdf_id):
    """Use a powerup from inventory"""
    try:
        session_key = f"game_{pdf_id}_{session.get('user_id', 'default')}"

        if session_key not in game_sessions:
            return jsonify({'error': 'No active game'}), 400

        data = request.get_json()
        powerup_id = data.get('powerup_id')

        if not powerup_id:
            return jsonify({'error': 'Missing powerup_id'}), 400

        game = game_sessions[session_key]
        result = game.use_powerup(powerup_id)

        return jsonify(result)

    except ValueError as e:
        return jsonify({'error': str(e)}), 400
    except Exception as e:
        logger.error(f"Use powerup error: {str(e)}")
        return jsonify({'error': str(e)}), 500


@app.route('/api/game/save/<int:pdf_id>', methods=['POST'])
def save_game(pdf_id):
    """Save current game"""
    try:
        session_key = f"game_{pdf_id}_{session.get('user_id', 'default')}"

        if session_key not in game_sessions:
            return jsonify({'error': 'No active game'}), 400

        data = request.get_json() or {}
        save_name = data.get('save_name', f"Save {session.get('user_id', 'default')}")

        game = game_sessions[session_key]
        save_id = game.save_game(save_name)

        return jsonify({
            'success': True,
            'save_id': save_id,
            'message': 'Game saved successfully'
        })

    except Exception as e:
        logger.error(f"Save game error: {str(e)}")
        return jsonify({'error': str(e)}), 500


@app.route('/api/game/load/<int:save_id>', methods=['POST'])
def load_game(save_id):
    """Load a saved game"""
    try:
        save_data = save_manager.get_save(save_id)
        if not save_data:
            return jsonify({'error': 'Save not found'}), 404

        pdf_id = save_data['pdf_id']

        # Create game engine and load
        game = GameEngine(pdf_id)
        state = game.load_game(save_id)

        if not state:
            return jsonify({'error': 'Failed to load game'}), 500

        # Store in session
        session_key = f"game_{pdf_id}_{session.get('user_id', 'default')}"
        game_sessions[session_key] = game

        return jsonify({
            'success': True,
            'pdf_id': pdf_id,
            'game_status': game.get_game_status(),
            'message': 'Game loaded successfully'
        })

    except Exception as e:
        logger.error(f"Load game error: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/game/delete-save/<int:save_id>', methods=['DELETE'])
def delete_save_route(save_id):
    """Delete a saved game"""
    try:

        save_manager.delete_save(save_id)
        
        return jsonify({
            'success': True, 
            'message': 'Save deleted successfully'
        })
    except Exception as e:
        logger.error(f"Delete save error: {str(e)}")
        return jsonify({'error': str(e)}), 500


# ═══════════════════════════════════════════════════════════════════
# 📊 STATISTICS API
# ═══════════════════════════════════════════════════════════════════

@app.route('/api/stats/<int:pdf_id>', methods=['GET'])
def get_stats(pdf_id):
    """Get statistics for a PDF"""
    try:
        overall = stats_manager.get_overall_stats(pdf_id)
        topics = stats_manager.get_topic_performance(pdf_id)
        weak = stats_manager.get_weak_areas(pdf_id)

        return jsonify({
            'overall': overall,
            'topics': topics,
            'weak_areas': weak
        })

    except Exception as e:
        logger.error(f"Get stats error: {str(e)}")
        return jsonify({'error': str(e)}), 500


@app.route('/api/stats/export/<int:pdf_id>/<format>', methods=['GET'])
def export_stats(pdf_id, format):
    """Export statistics in specified format"""
    try:
        if format not in ['json', 'csv', 'markdown', 'all']:
            return jsonify({'error': 'Invalid format'}), 400

        result = export_stats_for_pdf(pdf_id, format)

        return jsonify({
            'success': True,
            'files': result
        })

    except Exception as e:
        logger.error(f"Export stats error: {str(e)}")
        return jsonify({'error': str(e)}), 500


@app.route('/api/stats/download/<path:filename>')
def download_export(filename):
    """Download an exported statistics file"""
    try:
        filepath = config.EXPORT_DIR / filename

        if not filepath.exists():
            return "File not found", 404

        return send_file(filepath, as_attachment=True)

    except Exception as e:
        logger.error(f"Download error: {str(e)}")
        return "Error downloading file", 500


# ═══════════════════════════════════════════════════════════════════
# 🔧 UTILITY ROUTES
# ═══════════════════════════════════════════════════════════════════

@app.route('/api/pdfs', methods=['GET'])
def get_pdfs():
    """Get list of all PDFs"""
    try:
        pdfs = pdf_manager.get_all_pdfs()

        # Enrich with question counts
        for pdf in pdfs:
            pdf['question_count'] = question_manager.get_question_count(pdf['id'])
            pdf['ready_to_play'] = pdf['question_count'] >= config.MIN_QUESTIONS_TO_START

        return jsonify(pdfs)

    except Exception as e:
        logger.error(f"Get PDFs error: {str(e)}")
        return jsonify({'error': str(e)}), 500


@app.route('/api/config', methods=['GET'])
def get_config():
    """Get game configuration for frontend"""
    return jsonify({
        'enemy_types': config.ENEMY_TYPES,
        'boss_types': config.BOSS_TYPES,
        'powerups': config.POWERUPS,
        'total_encounters': config.TOTAL_ENCOUNTERS,
        'player_max_hp': config.PLAYER_MAX_HP,
        'animation_durations': config.ANIMATION_DURATIONS,
        'colors': config.COLORS
    })


@app.errorhandler(413)
def too_large(e):
    """Handle file too large error"""
    return jsonify({'error': 'File too large. Maximum size is 16MB.'}), 413


@app.errorhandler(500)
def internal_error(e):
    """Handle internal server error"""
    logger.error(f"Internal error: {str(e)}")
    return jsonify({'error': 'Internal server error'}), 500


# ═══════════════════════════════════════════════════════════════════
# 🚀 RUN APPLICATION
# ═══════════════════════════════════════════════════════════════════

if __name__ == '__main__':
    logger.info("Starting Educational Roguelike Game Server")
    logger.info(f"Server running on {config.HOST}:{config.PORT}")

    app.run(
        host=config.HOST,
        port=config.PORT,
        debug=config.DEBUG
    )
