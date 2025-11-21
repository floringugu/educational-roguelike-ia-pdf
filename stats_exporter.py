"""
Statistics Exporter for Educational Roguelike
Exports learning statistics in multiple formats (JSON, CSV, Markdown)
"""

import json
import csv
from datetime import datetime
from typing import Dict, List
from pathlib import Path
import logging

import config
from database import stats_manager, question_manager, pdf_manager

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class StatsExporter:
    """Export statistics in various formats"""

    def __init__(self, pdf_id: int):
        self.pdf_id = pdf_id
        self.export_dir = config.EXPORT_DIR

    def export_all_formats(self, filename_base: str = None) -> Dict[str, str]:
        """
        Export statistics in all available formats

        Returns:
            Dict mapping format to filepath
        """
        if not filename_base:
            pdf_info = pdf_manager.get_pdf(self.pdf_id)
            pdf_title = pdf_info['title'] if pdf_info else f"pdf_{self.pdf_id}"
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            filename_base = f"{pdf_title}_{timestamp}"

        # Sanitize filename
        filename_base = "".join(c for c in filename_base if c.isalnum() or c in (' ', '-', '_')).strip()

        results = {}

        # Export JSON
        try:
            json_path = self.export_json(filename_base)
            results['json'] = json_path
            logger.info(f"Exported JSON to {json_path}")
        except Exception as e:
            logger.error(f"JSON export failed: {str(e)}")

        # Export CSV
        try:
            csv_path = self.export_csv(filename_base)
            results['csv'] = csv_path
            logger.info(f"Exported CSV to {csv_path}")
        except Exception as e:
            logger.error(f"CSV export failed: {str(e)}")

        # Export Markdown
        try:
            md_path = self.export_markdown(filename_base)
            results['markdown'] = md_path
            logger.info(f"Exported Markdown to {md_path}")
        except Exception as e:
            logger.error(f"Markdown export failed: {str(e)}")

        return results

    def export_json(self, filename: str = None) -> str:
        """Export complete statistics as JSON"""
        data = self._gather_all_stats()

        if not filename:
            filename = f"stats_{self.pdf_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"

        filepath = self.export_dir / f"{filename}.json"

        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)

        return str(filepath)

    def export_csv(self, filename: str = None) -> str:
        """Export statistics as CSV"""
        if not filename:
            filename = f"stats_{self.pdf_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"

        filepath = self.export_dir / f"{filename}.csv"

        # Get topic performance data
        topic_performance = stats_manager.get_topic_performance(self.pdf_id)

        with open(filepath, 'w', newline='', encoding='utf-8') as f:
            if not topic_performance:
                # Write empty file with headers
                writer = csv.writer(f)
                writer.writerow(['Topic', 'Attempts', 'Correct', 'Accuracy (%)'])
                return str(filepath)

            fieldnames = ['Topic', 'Attempts', 'Correct', 'Accuracy (%)']
            writer = csv.DictWriter(f, fieldnames=fieldnames)

            writer.writeheader()
            for topic in topic_performance:
                writer.writerow({
                    'Topic': topic.get('topic', 'Unknown'),
                    'Attempts': topic.get('attempts', 0),
                    'Correct': topic.get('correct', 0),
                    'Accuracy (%)': f"{topic.get('accuracy', 0):.1f}"
                })

        return str(filepath)

    def export_markdown(self, filename: str = None) -> str:
        """Export statistics as formatted Markdown report"""
        if not filename:
            filename = f"report_{self.pdf_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"

        filepath = self.export_dir / f"{filename}.md"

        # Gather all stats
        data = self._gather_all_stats()

        # Build markdown report
        report = self._build_markdown_report(data)

        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(report)

        return str(filepath)

    def _gather_all_stats(self) -> Dict:
        """Gather all statistics for export"""
        # Get PDF info
        pdf_info = pdf_manager.get_pdf(self.pdf_id)

        # Get overall stats
        overall = stats_manager.get_overall_stats(self.pdf_id)

        # Get topic performance
        topic_performance = stats_manager.get_topic_performance(self.pdf_id)

        # Get weak areas
        weak_areas = stats_manager.get_weak_areas(self.pdf_id)

        # Get recent activity
        recent_activity = stats_manager.get_recent_activity(self.pdf_id, limit=50)

        # Question count and topics
        question_count = question_manager.get_question_count(self.pdf_id)
        questions_by_topic = question_manager.get_questions_by_topic(self.pdf_id)

        return {
            'export_date': datetime.now().isoformat(),
            'pdf_info': {
                'id': self.pdf_id,
                'title': pdf_info['title'] if pdf_info else f"PDF {self.pdf_id}",
                'filename': pdf_info['filename'] if pdf_info else 'Unknown',
                'num_pages': pdf_info['num_pages'] if pdf_info else 0,
                'upload_date': pdf_info['upload_date'] if pdf_info else None
            },
            'overall_stats': {
                'total_answers': overall['total_answers'],
                'correct_answers': overall['correct_answers'],
                'accuracy_percent': round(overall['accuracy'], 2),
                'total_time_seconds': overall['total_time_seconds'],
                'total_time_formatted': self._format_time(overall['total_time_seconds']),
                'total_score': overall['total_score'],
                'completed_games': overall['completed_games']
            },
            'questions': {
                'total_questions': question_count,
                'questions_by_topic': questions_by_topic
            },
            'topic_performance': [
                {
                    'topic': t.get('topic', 'Unknown'),
                    'attempts': t.get('attempts', 0),
                    'correct': t.get('correct', 0),
                    'accuracy': round(t.get('accuracy', 0), 2)
                }
                for t in topic_performance
            ],
            'weak_areas': [
                {
                    'topic': w.get('topic', 'Unknown'),
                    'difficulty': w.get('difficulty', 'unknown'),
                    'attempts': w.get('attempts', 0),
                    'correct': w.get('correct', 0),
                    'accuracy': round(w.get('accuracy', 0), 2)
                }
                for w in weak_areas
            ],
            'recent_activity': [
                {
                    'question_text': a.get('question_text', ''),
                    'topic': a.get('topic', 'Unknown'),
                    'difficulty': a.get('difficulty', 'unknown'),
                    'user_answer': a.get('user_answer', ''),
                    'is_correct': a.get('is_correct', False),
                    'answered_date': a.get('answered_date', '')
                }
                for a in recent_activity[:20]  # Limit to last 20
            ]
        }

    def _build_markdown_report(self, data: Dict) -> str:
        """Build a formatted Markdown report"""
        pdf_info = data['pdf_info']
        overall = data['overall_stats']
        topics = data['topic_performance']
        weak = data['weak_areas']

        report = f"""# 📊 Learning Statistics Report

**PDF:** {pdf_info['title']}
**Generated:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

---

## 🎯 Overall Performance

| Metric | Value |
|--------|-------|
| **Total Questions Answered** | {overall['total_answers']} |
| **Correct Answers** | {overall['correct_answers']} |
| **Overall Accuracy** | {overall['accuracy_percent']:.1f}% |
| **Total Study Time** | {overall['total_time_formatted']} |
| **Total Score** | {overall['total_score']:,} |
| **Games Completed** | {overall['completed_games']} |

"""

        # Progress bar for accuracy
        accuracy = overall['accuracy_percent']
        if accuracy >= 80:
            emoji = "🌟"
            comment = "Excellent!"
        elif accuracy >= 60:
            emoji = "👍"
            comment = "Good job!"
        else:
            emoji = "📚"
            comment = "Keep studying!"

        report += f"**Performance:** {emoji} {comment}\n\n---\n\n"

        # Topic Performance
        if topics:
            report += "## 📚 Performance by Topic\n\n"
            report += "| Topic | Attempts | Correct | Accuracy |\n"
            report += "|-------|----------|---------|----------|\n"

            for topic in topics:
                accuracy_bar = self._create_bar(topic['accuracy'], 100)
                report += f"| {topic['topic']} | {topic['attempts']} | {topic['correct']} | {topic['accuracy']:.1f}% {accuracy_bar} |\n"

            report += "\n---\n\n"

        # Weak Areas
        if weak:
            report += "## ⚠️ Areas Needing Improvement\n\n"
            report += "Focus your study on these topics:\n\n"
            report += "| Topic | Difficulty | Accuracy |\n"
            report += "|-------|------------|----------|\n"

            for area in weak[:5]:  # Top 5 weak areas
                report += f"| {area['topic']} | {area['difficulty'].capitalize()} | {area['accuracy']:.1f}% |\n"

            report += "\n---\n\n"

        # Study Recommendations
        report += "## 💡 Study Recommendations\n\n"

        if overall['accuracy_percent'] < 60:
            report += "- 📖 Review fundamental concepts\n"
            report += "- 🎯 Focus on accuracy over speed\n"
            report += "- 🔄 Repeat challenging topics\n"
        elif overall['accuracy_percent'] < 80:
            report += "- 🎯 Good progress! Keep practicing\n"
            report += "- 📊 Focus on weak areas identified above\n"
            report += "- 🧠 Try harder difficulty questions\n"
        else:
            report += "- 🌟 Excellent mastery!\n"
            report += "- 🚀 Challenge yourself with advanced topics\n"
            report += "- 📝 Consider teaching others to reinforce learning\n"

        report += "\n---\n\n"

        # Footer
        report += f"*Report generated by Educational Roguelike Game*  \n"
        report += f"*Export Date: {data['export_date']}*\n"

        return report

    def _format_time(self, seconds: int) -> str:
        """Format seconds into human-readable time"""
        if not seconds:
            return "0 minutes"

        hours = seconds // 3600
        minutes = (seconds % 3600) // 60
        secs = seconds % 60

        parts = []
        if hours > 0:
            parts.append(f"{hours}h")
        if minutes > 0:
            parts.append(f"{minutes}m")
        if secs > 0 and hours == 0:
            parts.append(f"{secs}s")

        return " ".join(parts) if parts else "0s"

    def _create_bar(self, value: float, max_value: float, length: int = 10) -> str:
        """Create a text-based progress bar"""
        filled = int((value / max_value) * length)
        bar = "█" * filled + "░" * (length - filled)
        return f"`{bar}`"


class LearningAnalyzer:
    """Analyze learning patterns and provide insights"""

    def __init__(self, pdf_id: int):
        self.pdf_id = pdf_id

    def get_learning_insights(self) -> Dict:
        """Generate learning insights and recommendations"""
        overall = stats_manager.get_overall_stats(self.pdf_id)
        topics = stats_manager.get_topic_performance(self.pdf_id)
        weak_areas = stats_manager.get_weak_areas(self.pdf_id, threshold=70)

        insights = {
            'overall_level': self._assess_level(overall['accuracy']),
            'strong_topics': [],
            'weak_topics': [],
            'recommendations': []
        }

        # Identify strong and weak topics
        if topics:
            sorted_topics = sorted(topics, key=lambda x: x.get('accuracy', 0), reverse=True)

            # Strong topics (top 3 with >80% accuracy)
            insights['strong_topics'] = [
                t['topic'] for t in sorted_topics[:3]
                if t.get('accuracy', 0) > 80 and t.get('attempts', 0) >= 3
            ]

            # Weak topics (bottom 3 with <70% accuracy)
            insights['weak_topics'] = [
                t['topic'] for t in sorted_topics[-3:]
                if t.get('accuracy', 0) < 70 and t.get('attempts', 0) >= 3
            ]

        # Generate recommendations
        if overall['accuracy'] < 50:
            insights['recommendations'].append("Start with easier questions to build confidence")
            insights['recommendations'].append("Review the source material before playing")
        elif overall['accuracy'] < 70:
            insights['recommendations'].append("Focus on weak topics identified above")
            insights['recommendations'].append("Take time to read explanations for wrong answers")
        else:
            insights['recommendations'].append("Challenge yourself with harder difficulties")
            insights['recommendations'].append("Try to complete a full game without errors")

        if insights['weak_topics']:
            insights['recommendations'].append(f"Extra study needed: {', '.join(insights['weak_topics'][:2])}")

        return insights

    def _assess_level(self, accuracy: float) -> str:
        """Assess learning level based on accuracy"""
        if accuracy >= 90:
            return "Expert"
        elif accuracy >= 80:
            return "Advanced"
        elif accuracy >= 70:
            return "Intermediate"
        elif accuracy >= 60:
            return "Beginner"
        else:
            return "Novice"

    def suggest_next_questions(self, limit: int = 5) -> List[Dict]:
        """
        Suggest questions for focused study using spaced repetition

        Returns questions from weak areas
        """
        weak_areas = stats_manager.get_weak_areas(self.pdf_id, threshold=70)

        if not weak_areas:
            return []

        # Get questions from weak topics
        suggestions = []
        for area in weak_areas[:3]:  # Top 3 weak areas
            # This is a placeholder - in a full implementation,
            # you'd use the spaced repetition algorithm
            topic = area.get('topic')
            difficulty = area.get('difficulty')

            # Get questions matching this topic and difficulty
            # (simplified version)
            suggestions.append({
                'topic': topic,
                'difficulty': difficulty,
                'reason': f"Accuracy in this area: {area.get('accuracy', 0):.1f}%"
            })

        return suggestions[:limit]


# ═══════════════════════════════════════════════════════════════════
# 🚀 UTILITY FUNCTIONS
# ═══════════════════════════════════════════════════════════════════

def export_stats_for_pdf(pdf_id: int, format: str = 'all') -> Dict:
    """
    Quick export function

    Args:
        pdf_id: PDF ID
        format: 'json', 'csv', 'markdown', or 'all'

    Returns:
        Dict with export paths
    """
    exporter = StatsExporter(pdf_id)

    if format == 'all':
        return exporter.export_all_formats()
    elif format == 'json':
        return {'json': exporter.export_json()}
    elif format == 'csv':
        return {'csv': exporter.export_csv()}
    elif format == 'markdown':
        return {'markdown': exporter.export_markdown()}
    else:
        raise ValueError(f"Unknown format: {format}")
