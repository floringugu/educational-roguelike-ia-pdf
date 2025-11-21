"""
Question Generation module using Grok API (xAI)
Generates high-quality educational questions from PDF content
FREE TIER AVAILABLE - More accessible than Claude
"""

import json
import logging
from typing import List, Dict, Optional
from openai import OpenAI

import config
from database import question_manager

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class QuestionGenerator:
    """Generates questions using Grok API (xAI)"""

    def __init__(self, api_key: str = None):
        self.api_key = api_key or config.XAI_API_KEY
        if not self.api_key:
            raise ValueError("XAI_API_KEY not found in environment variables")

        # Grok API uses OpenAI-compatible format
        self.client = OpenAI(
            api_key=self.api_key,
            base_url="https://api.x.ai/v1"
        )
        self.model = config.GROK_MODEL

    def generate_questions_from_text(
        self,
        text: str,
        num_questions: int = 10,
        difficulty: str = 'mixed',
        topic: str = None
    ) -> List[Dict]:
        """
        Generate questions from text using Grok API

        Args:
            text: Source text to generate questions from
            num_questions: Number of questions to generate
            difficulty: 'easy', 'medium', 'hard', or 'mixed'
            topic: Optional topic/subject area

        Returns:
            List of question dictionaries
        """
        prompt = self._build_prompt(text, num_questions, difficulty, topic)

        try:
            logger.info(f"Generating {num_questions} questions (difficulty: {difficulty})")

            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {
                        "role": "system",
                        "content": "You are an expert educational content creator specializing in creating high-quality study questions. Always respond with valid JSON only."
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                temperature=config.TEMPERATURE,
                max_tokens=config.MAX_TOKENS
            )

            # Extract JSON from response
            response_text = response.choices[0].message.content
            questions = self._parse_response(response_text)

            logger.info(f"Successfully generated {len(questions)} questions")

            return questions

        except Exception as e:
            logger.error(f"Error generating questions: {str(e)}")
            raise

    def _build_prompt(
        self,
        text: str,
        num_questions: int,
        difficulty: str,
        topic: str = None
    ) -> str:
        """Build optimized prompt for Grok API"""

        difficulty_guidance = {
            'easy': 'Focus on basic recall and simple comprehension. Questions should test fundamental understanding.',
            'medium': 'Mix of recall and application. Questions should require understanding and some analysis.',
            'hard': 'Focus on analysis, synthesis, and critical thinking. Questions should be challenging.',
            'mixed': 'Create a balanced mix: 40% easy, 40% medium, 20% hard questions.'
        }

        topic_context = f"\n\nFocus specifically on the topic: {topic}" if topic else ""

        prompt = f"""Generate {num_questions} educational questions based on the following text.

DIFFICULTY LEVEL: {difficulty}
{difficulty_guidance.get(difficulty, difficulty_guidance['mixed'])}{topic_context}

SOURCE TEXT:
{text[:8000]}

REQUIREMENTS:
1. Generate EXACTLY {num_questions} questions
2. Create a mix of question types:
   - Multiple choice questions (4 options, only one correct)
   - True/False questions
3. For multiple choice questions:
   - The correct answer should not be obvious
   - Distractors (wrong answers) should be plausible and test common misconceptions
   - Avoid "all of the above" or "none of the above" options
4. Include a clear explanation for why the answer is correct
5. Classify each question's difficulty as 'easy', 'medium', or 'hard'
6. Extract or infer a topic/subject for each question
7. Questions should test understanding, not just memorization
8. Avoid trivial questions or those with obvious answers

OUTPUT FORMAT:
Return ONLY a valid JSON array. Each question should have this exact structure:

[
  {{
    "question_text": "The question text here?",
    "question_type": "multiple_choice",
    "correct_answer": "The correct answer",
    "options": ["Option A", "Option B", "Option C", "Option D"],
    "explanation": "Why this answer is correct and why others are wrong",
    "topic": "Topic or subject area",
    "difficulty": "easy|medium|hard"
  }},
  {{
    "question_text": "Another question here?",
    "question_type": "true_false",
    "correct_answer": "true",
    "options": ["true", "false"],
    "explanation": "Explanation of the answer",
    "topic": "Topic area",
    "difficulty": "medium"
  }}
]

IMPORTANT:
- Return ONLY the JSON array, no other text
- Ensure valid JSON formatting
- For true/false questions, correct_answer should be exactly "true" or "false" (lowercase)
- For multiple choice, correct_answer should exactly match one of the options

Generate the questions now:"""

        return prompt

    def _parse_response(self, response_text: str) -> List[Dict]:
        """Parse Grok's response and extract questions"""

        try:
            # Try to find JSON in the response
            # Sometimes LLMs add explanation text, so we need to extract JSON

            # Look for JSON array pattern
            start_idx = response_text.find('[')
            end_idx = response_text.rfind(']')

            if start_idx == -1 or end_idx == -1:
                raise ValueError("No JSON array found in response")

            json_str = response_text[start_idx:end_idx + 1]

            # Parse JSON
            questions = json.loads(json_str)

            # Validate and clean questions
            validated_questions = []
            for q in questions:
                if self._validate_question(q):
                    validated_questions.append(self._clean_question(q))
                else:
                    logger.warning(f"Skipping invalid question: {q.get('question_text', 'unknown')}")

            return validated_questions

        except json.JSONDecodeError as e:
            logger.error(f"JSON parse error: {str(e)}")
            logger.error(f"Response text: {response_text[:500]}")
            raise ValueError(f"Failed to parse questions from response: {str(e)}")

    def _validate_question(self, question: Dict) -> bool:
        """Validate that a question has all required fields"""

        required_fields = [
            'question_text',
            'question_type',
            'correct_answer',
            'explanation'
        ]

        # Check required fields
        for field in required_fields:
            if field not in question or not question[field]:
                return False

        # Validate question type
        if question['question_type'] not in ['multiple_choice', 'true_false']:
            return False

        # Validate multiple choice has options
        if question['question_type'] == 'multiple_choice':
            if 'options' not in question or len(question['options']) < 2:
                return False
            if question['correct_answer'] not in question['options']:
                return False

        # Validate true/false
        if question['question_type'] == 'true_false':
            if question['correct_answer'].lower() not in ['true', 'false']:
                return False

        return True

    def _clean_question(self, question: Dict) -> Dict:
        """Clean and normalize a question"""

        # Ensure lowercase for true/false
        if question['question_type'] == 'true_false':
            question['correct_answer'] = question['correct_answer'].lower()
            question['options'] = ['true', 'false']

        # Set default difficulty if not present
        if 'difficulty' not in question or question['difficulty'] not in config.DIFFICULTY_LEVELS:
            question['difficulty'] = 'medium'

        # Set default topic if not present
        if 'topic' not in question:
            question['topic'] = 'General'

        # Trim whitespace
        question['question_text'] = question['question_text'].strip()
        question['correct_answer'] = question['correct_answer'].strip()
        question['explanation'] = question['explanation'].strip()

        return question

    def estimate_cost(self, text_length: int, num_questions: int) -> Dict:
        """
        Estimate API cost for generating questions

        Returns:
            Dict with estimated costs
        """
        # Rough estimates for Grok API
        input_tokens = (text_length / 4) + 500  # Text + prompt
        output_tokens = num_questions * config.AVG_OUTPUT_TOKENS_PER_QUESTION

        # Grok pricing (update based on current xAI pricing)
        input_cost = (input_tokens / 1_000_000) * config.COST_PER_1M_INPUT_TOKENS
        output_cost = (output_tokens / 1_000_000) * config.COST_PER_1M_OUTPUT_TOKENS

        total_cost = input_cost + output_cost

        return {
            'estimated_input_tokens': int(input_tokens),
            'estimated_output_tokens': int(output_tokens),
            'estimated_total_tokens': int(input_tokens + output_tokens),
            'estimated_cost_usd': round(total_cost, 4),
            'input_cost_usd': round(input_cost, 4),
            'output_cost_usd': round(output_cost, 4)
        }


class QuestionBatchGenerator:
    """Handles batch generation of questions from multiple text chunks"""

    def __init__(self, generator: QuestionGenerator = None):
        self.generator = generator or QuestionGenerator()

    def generate_from_chunks(
        self,
        chunks: List[Dict],
        questions_per_chunk: int = None,
        total_questions: int = None,
        difficulty_distribution: Dict = None
    ) -> List[Dict]:
        """
        Generate questions from multiple text chunks

        Args:
            chunks: List of text chunks from PDF
            questions_per_chunk: Questions per chunk (if None, uses total_questions)
            total_questions: Total questions to generate across all chunks
            difficulty_distribution: Dict like {'easy': 0.4, 'medium': 0.4, 'hard': 0.2}

        Returns:
            List of all generated questions
        """
        if not chunks:
            raise ValueError("No chunks provided")

        # Calculate questions per chunk
        if total_questions:
            questions_per_chunk = max(1, total_questions // len(chunks))
        elif not questions_per_chunk:
            questions_per_chunk = 5

        all_questions = []
        difficulty_dist = difficulty_distribution or {'easy': 0.4, 'medium': 0.4, 'hard': 0.2}

        logger.info(f"Generating questions from {len(chunks)} chunks")

        for i, chunk in enumerate(chunks, 1):
            # Determine difficulty for this chunk
            # Rotate through difficulties based on distribution
            if i % 5 == 1:
                difficulty = 'easy'
            elif i % 5 == 2 or i % 5 == 3:
                difficulty = 'medium'
            elif i % 5 == 4:
                difficulty = 'hard'
            else:
                difficulty = 'mixed'

            try:
                questions = self.generator.generate_questions_from_text(
                    text=chunk['text'],
                    num_questions=questions_per_chunk,
                    difficulty=difficulty
                )

                all_questions.extend(questions)
                logger.info(f"Chunk {i}/{len(chunks)}: Generated {len(questions)} questions")

            except Exception as e:
                logger.error(f"Error generating questions for chunk {i}: {str(e)}")
                continue

            # Stop if we've reached the desired total
            if total_questions and len(all_questions) >= total_questions:
                break

        logger.info(f"Total questions generated: {len(all_questions)}")
        return all_questions

    def save_questions_to_db(self, pdf_id: int, questions: List[Dict]) -> int:
        """
        Save generated questions to database

        Returns:
            Number of questions saved
        """
        questions_data = []

        for q in questions:
            questions_data.append({
                'pdf_id': pdf_id,
                'question_text': q['question_text'],
                'question_type': q['question_type'],
                'correct_answer': q['correct_answer'],
                'options': q.get('options'),
                'explanation': q['explanation'],
                'topic': q.get('topic', 'General'),
                'difficulty': q.get('difficulty', 'medium')
            })

        count = question_manager.add_questions_batch(questions_data)
        logger.info(f"Saved {count} questions to database for PDF {pdf_id}")

        return count


# ═══════════════════════════════════════════════════════════════════
# 🚀 HIGH-LEVEL WORKFLOW FUNCTION
# ═══════════════════════════════════════════════════════════════════

def process_pdf_and_generate_questions(
    pdf_id: int,
    text: str,
    chunks: List[Dict],
    num_questions: int = None
) -> Dict:
    """
    Complete workflow: generate and save questions from PDF

    Args:
        pdf_id: Database ID of the PDF
        text: Full text from PDF
        chunks: Text chunks from PDF
        num_questions: Target number of questions (default: based on game requirements)

    Returns:
        Dict with generation stats
    """
    from database import pdf_manager as db_pdf_manager
    from game_engine import calculate_minimum_questions_needed

    # Get PDF info
    pdf_info = db_pdf_manager.get_pdf(pdf_id)
    if not pdf_info:
        raise ValueError(f"PDF {pdf_id} not found in database")

    # Determine number of questions
    if not num_questions:
        # Calculate minimum questions needed for a full game run
        min_needed = calculate_minimum_questions_needed()

        # Estimate based on text length
        words = len(text.split())
        text_based = max(config.MIN_QUESTIONS_TO_START, min(100, words // 250))

        # Use the maximum to ensure enough questions
        num_questions = max(min_needed, text_based)

        logger.info(f"Generating {num_questions} questions (minimum needed: {min_needed}, text-based: {text_based})")

    # Initialize generators
    generator = QuestionGenerator()
    batch_generator = QuestionBatchGenerator(generator)

    # Estimate cost
    cost_estimate = generator.estimate_cost(len(text), num_questions)
    logger.info(f"Estimated cost: ${cost_estimate['estimated_cost_usd']:.4f}")

    # Generate questions
    questions = batch_generator.generate_from_chunks(
        chunks=chunks,
        total_questions=num_questions
    )

    # Save to database
    saved_count = batch_generator.save_questions_to_db(pdf_id, questions)

    # Mark PDF as processed
    db_pdf_manager.mark_processed(pdf_id)

    return {
        'pdf_id': pdf_id,
        'pdf_title': pdf_info['title'],
        'questions_generated': len(questions),
        'questions_saved': saved_count,
        'cost_estimate': cost_estimate,
        'minimum_needed': calculate_minimum_questions_needed(),
        'success': True
    }
