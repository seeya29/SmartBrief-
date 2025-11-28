"""
Feedback System for SmartBrief v3
Collects and analyzes user feedback to improve summarization quality.
"""

import json
import os
import pandas as pd
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
import logging

logger = logging.getLogger(__name__)

class FeedbackCollector:
    """
    Collects and manages user feedback for the summarization system.
    
    Features:
    - Feedback collection with ratings and comments
    - Category-specific feedback (summary quality, intent detection, urgency)
    - Analytics and reporting
    - Export/import functionality
    """
    
    def __init__(self, feedback_file: str = 'feedback_data.json'):
        self.feedback_file = feedback_file
        self.feedback_data = self._load_feedback_data()
        
        # Feedback categories
        self.feedback_categories = {
            'summary_quality': 'How well does the summary capture the message?',
            'intent_detection': 'How accurate is the intent classification?',
            'urgency_level': 'How accurate is the urgency assessment?',
            'context_usage': 'How well does the system use conversation context?',
            'platform_optimization': 'How well is the summary optimized for the platform?'
        }
        
        # Rating scale
        self.rating_scale = {
            -1: 'Poor/Incorrect',
            0: 'Neutral/Acceptable',
            1: 'Good/Correct'
        }
    
    def _load_feedback_data(self) -> Dict:
        """Load feedback data from file."""
        if os.path.exists(self.feedback_file):
            try:
                with open(self.feedback_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except Exception as e:
                logger.error(f"Error loading feedback data: {e}")
        
        return {
            'feedback_entries': [],
            'summary_stats': {
                'total_feedback': 0,
                'positive_feedback': 0,
                'negative_feedback': 0,
                'neutral_feedback': 0
            },
            'category_stats': {},
            'platform_stats': {},
            'user_stats': {},
            'metadata': {
                'created': datetime.now().isoformat(),
                'last_updated': datetime.now().isoformat()
            }
        }
    
    def _save_feedback_data(self):
        """Save feedback data to file."""
        try:
            self.feedback_data['metadata']['last_updated'] = datetime.now().isoformat()
            with open(self.feedback_file, 'w', encoding='utf-8') as f:
                json.dump(self.feedback_data, f, indent=2, ensure_ascii=False)
        except Exception as e:
            logger.error(f"Error saving feedback data: {e}")
    
    def collect_feedback(self, 
                        message_id: str,
                        user_id: str,
                        platform: str,
                        original_text: str,
                        generated_summary: str,
                        feedback_score: int,
                        feedback_comment: str = "",
                        category_ratings: Dict[str, int] = None) -> bool:
        """
        Collect feedback for a summarization result.
        
        Args:
            message_id: Unique identifier for the message
            user_id: User who provided feedback
            platform: Platform where message originated
            original_text: Original message text
            generated_summary: Generated summary
            feedback_score: Overall feedback score (-1, 0, 1)
            feedback_comment: Optional comment
            category_ratings: Ratings for specific categories
            
        Returns:
            Success status
        """
        try:
            # Validate feedback score
            if feedback_score not in [-1, 0, 1]:
                logger.error(f"Invalid feedback score: {feedback_score}")
                return False
            
            # Create feedback entry
            feedback_entry = {
                'feedback_id': f"fb_{datetime.now().timestamp()}",
                'message_id': message_id,
                'user_id': user_id,
                'platform': platform,
                'original_text': original_text,
                'generated_summary': generated_summary,
                'feedback_score': feedback_score,
                'feedback_comment': feedback_comment,
                'category_ratings': category_ratings or {},
                'timestamp': datetime.now().isoformat(),
                'feedback_version': '1.0'
            }
            
            # Add to feedback entries
            self.feedback_data['feedback_entries'].append(feedback_entry)
            
            # Update summary stats
            self._update_summary_stats(feedback_score)
            
            # Update category stats
            if category_ratings:
                self._update_category_stats(category_ratings)
            
            # Update platform stats
            self._update_platform_stats(platform, feedback_score)
            
            # Update user stats
            self._update_user_stats(user_id, feedback_score)
            
            # Save data
            self._save_feedback_data()
            
            logger.info(f"Feedback collected for message {message_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error collecting feedback: {e}")
            return False
    
    def _update_summary_stats(self, feedback_score: int):
        """Update overall summary statistics."""
        stats = self.feedback_data['summary_stats']
        stats['total_feedback'] += 1
        
        if feedback_score > 0:
            stats['positive_feedback'] += 1
        elif feedback_score < 0:
            stats['negative_feedback'] += 1
        else:
            stats['neutral_feedback'] += 1
    
    def _update_category_stats(self, category_ratings: Dict[str, int]):
        """Update category-specific statistics."""
        if 'category_stats' not in self.feedback_data:
            self.feedback_data['category_stats'] = {}
        
        for category, rating in category_ratings.items():
            if category not in self.feedback_data['category_stats']:
                self.feedback_data['category_stats'][category] = {
                    'total': 0,
                    'positive': 0,
                    'negative': 0,
                    'neutral': 0,
                    'average': 0.0
                }
            
            cat_stats = self.feedback_data['category_stats'][category]
            cat_stats['total'] += 1
            
            if rating > 0:
                cat_stats['positive'] += 1
            elif rating < 0:
                cat_stats['negative'] += 1
            else:
                cat_stats['neutral'] += 1
            
            # Update average
            cat_stats['average'] = (cat_stats['positive'] - cat_stats['negative']) / cat_stats['total']
    
    def _update_platform_stats(self, platform: str, feedback_score: int):
        """Update platform-specific statistics."""
        if 'platform_stats' not in self.feedback_data:
            self.feedback_data['platform_stats'] = {}
        
        if platform not in self.feedback_data['platform_stats']:
            self.feedback_data['platform_stats'][platform] = {
                'total': 0,
                'positive': 0,
                'negative': 0,
                'neutral': 0,
                'satisfaction_rate': 0.0
            }
        
        plat_stats = self.feedback_data['platform_stats'][platform]
        plat_stats['total'] += 1
        
        if feedback_score > 0:
            plat_stats['positive'] += 1
        elif feedback_score < 0:
            plat_stats['negative'] += 1
        else:
            plat_stats['neutral'] += 1
        
        # Update satisfaction rate
        plat_stats['satisfaction_rate'] = plat_stats['positive'] / plat_stats['total']
    
    def _update_user_stats(self, user_id: str, feedback_score: int):
        """Update user-specific statistics."""
        if 'user_stats' not in self.feedback_data:
            self.feedback_data['user_stats'] = {}
        
        if user_id not in self.feedback_data['user_stats']:
            self.feedback_data['user_stats'][user_id] = {
                'total_feedback': 0,
                'positive_feedback': 0,
                'negative_feedback': 0,
                'neutral_feedback': 0,
                'engagement_score': 0.0
            }
        
        user_stats = self.feedback_data['user_stats'][user_id]
        user_stats['total_feedback'] += 1
        
        if feedback_score > 0:
            user_stats['positive_feedback'] += 1
        elif feedback_score < 0:
            user_stats['negative_feedback'] += 1
        else:
            user_stats['neutral_feedback'] += 1
        
        # Update engagement score
        user_stats['engagement_score'] = user_stats['positive_feedback'] / user_stats['total_feedback']
    
    def get_feedback_analytics(self) -> Dict:
        """Get comprehensive feedback analytics."""
        analytics = {
            'overall_metrics': self.feedback_data.get('summary_stats', {}),
            'category_performance': self.feedback_data.get('category_stats', {}),
            'platform_performance': self.feedback_data.get('platform_stats', {}),
            'user_engagement': self.feedback_data.get('user_stats', {}),
            'recent_feedback': self._get_recent_feedback(days=7),
            'improvement_suggestions': self._generate_improvement_suggestions()
        }
        
        # Calculate additional metrics
        total_feedback = analytics['overall_metrics'].get('total_feedback', 0)
        if total_feedback > 0:
            positive = analytics['overall_metrics'].get('positive_feedback', 0)
            analytics['overall_metrics']['satisfaction_rate'] = positive / total_feedback
            
            # Calculate trend (last 7 days vs previous 7 days)
            analytics['trends'] = self._calculate_trends()
        
        return analytics
    
    def _get_recent_feedback(self, days: int = 7) -> List[Dict]:
        """Get recent feedback entries."""
        cutoff_date = datetime.now() - timedelta(days=days)
        recent_feedback = []
        
        for entry in self.feedback_data.get('feedback_entries', []):
            try:
                entry_date = datetime.fromisoformat(entry['timestamp'])
                if entry_date > cutoff_date:
                    recent_feedback.append(entry)
            except:
                continue
        
        return recent_feedback
    
    def _calculate_trends(self) -> Dict:
        """Calculate feedback trends."""
        now = datetime.now()
        last_7_days = now - timedelta(days=7)
        previous_7_days = now - timedelta(days=14)
        
        recent_feedback = []
        previous_feedback = []
        
        for entry in self.feedback_data.get('feedback_entries', []):
            try:
                entry_date = datetime.fromisoformat(entry['timestamp'])
                if entry_date > last_7_days:
                    recent_feedback.append(entry)
                elif entry_date > previous_7_days:
                    previous_feedback.append(entry)
            except:
                continue
        
        # Calculate satisfaction rates
        recent_positive = sum(1 for fb in recent_feedback if fb['feedback_score'] > 0)
        recent_total = len(recent_feedback)
        recent_rate = recent_positive / recent_total if recent_total > 0 else 0
        
        previous_positive = sum(1 for fb in previous_feedback if fb['feedback_score'] > 0)
        previous_total = len(previous_feedback)
        previous_rate = previous_positive / previous_total if previous_total > 0 else 0
        
        trend = recent_rate - previous_rate
        
        return {
            'recent_satisfaction_rate': recent_rate,
            'previous_satisfaction_rate': previous_rate,
            'trend': trend,
            'trend_direction': 'improving' if trend > 0.05 else 'declining' if trend < -0.05 else 'stable'
        }
    
    def _generate_improvement_suggestions(self) -> List[str]:
        """Generate suggestions for improvement based on feedback."""
        suggestions = []
        
        # Check category performance
        category_stats = self.feedback_data.get('category_stats', {})
        for category, stats in category_stats.items():
            if stats.get('average', 0) < -0.2:  # Poor performance
                suggestions.append(f"Improve {category.replace('_', ' ')} - currently underperforming")
        
        # Check platform performance
        platform_stats = self.feedback_data.get('platform_stats', {})
        for platform, stats in platform_stats.items():
            if stats.get('satisfaction_rate', 0) < 0.6:  # Low satisfaction
                suggestions.append(f"Review {platform} optimization - low user satisfaction")
        
        # Check overall trends
        trends = self._calculate_trends()
        if trends.get('trend_direction') == 'declining':
            suggestions.append("Overall satisfaction is declining - review recent changes")
        
        # Check feedback volume
        total_feedback = self.feedback_data.get('summary_stats', {}).get('total_feedback', 0)
        if total_feedback < 10:
            suggestions.append("Collect more user feedback to improve system accuracy")
        
        return suggestions
    
    def get_platform_feedback_summary(self, platform: str) -> Dict:
        """Get feedback summary for a specific platform."""
        platform_stats = self.feedback_data.get('platform_stats', {}).get(platform, {})
        
        # Get platform-specific feedback entries
        platform_feedback = [
            entry for entry in self.feedback_data.get('feedback_entries', [])
            if entry.get('platform') == platform
        ]
        
        return {
            'platform': platform,
            'total_feedback': platform_stats.get('total', 0),
            'satisfaction_rate': platform_stats.get('satisfaction_rate', 0.0),
            'positive_feedback': platform_stats.get('positive', 0),
            'negative_feedback': platform_stats.get('negative', 0),
            'neutral_feedback': platform_stats.get('neutral', 0),
            'recent_comments': [
                entry.get('feedback_comment', '') 
                for entry in platform_feedback[-5:] 
                if entry.get('feedback_comment')
            ]
        }
    
    def export_feedback_data(self, output_file: str) -> bool:
        """Export feedback data to file."""
        try:
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(self.feedback_data, f, indent=2, ensure_ascii=False)
            logger.info(f"Feedback data exported to {output_file}")
            return True
        except Exception as e:
            logger.error(f"Error exporting feedback data: {e}")
            return False
    
    def import_feedback_data(self, input_file: str) -> bool:
        """Import feedback data from file."""
        try:
            with open(input_file, 'r', encoding='utf-8') as f:
                imported_data = json.load(f)
            
            # Merge with existing data
            existing_entries = self.feedback_data.get('feedback_entries', [])
            imported_entries = imported_data.get('feedback_entries', [])
            
            # Avoid duplicates based on feedback_id
            existing_ids = {entry.get('feedback_id') for entry in existing_entries}
            new_entries = [
                entry for entry in imported_entries 
                if entry.get('feedback_id') not in existing_ids
            ]
            
            self.feedback_data['feedback_entries'].extend(new_entries)
            
            # Recalculate stats
            self._recalculate_all_stats()
            
            # Save merged data
            self._save_feedback_data()
            
            logger.info(f"Imported {len(new_entries)} new feedback entries")
            return True
            
        except Exception as e:
            logger.error(f"Error importing feedback data: {e}")
            return False
    
    def _recalculate_all_stats(self):
        """Recalculate all statistics from feedback entries."""
        # Reset stats
        self.feedback_data['summary_stats'] = {
            'total_feedback': 0,
            'positive_feedback': 0,
            'negative_feedback': 0,
            'neutral_feedback': 0
        }
        self.feedback_data['category_stats'] = {}
        self.feedback_data['platform_stats'] = {}
        self.feedback_data['user_stats'] = {}
        
        # Recalculate from all entries
        for entry in self.feedback_data.get('feedback_entries', []):
            feedback_score = entry.get('feedback_score', 0)
            platform = entry.get('platform', 'unknown')
            user_id = entry.get('user_id', 'unknown')
            category_ratings = entry.get('category_ratings', {})
            
            self._update_summary_stats(feedback_score)
            self._update_platform_stats(platform, feedback_score)
            self._update_user_stats(user_id, feedback_score)
            
            if category_ratings:
                self._update_category_stats(category_ratings)


class FeedbackEnhancedSummarizer:
    """
    Enhanced summarizer that integrates with the feedback system.
    """
    
    def __init__(self, context_file: str = 'message_context.json', feedback_file: str = 'feedback_data.json'):
        from smart_summarizer_v3 import SmartSummarizerV3
        
        self.summarizer = SmartSummarizerV3(context_file=context_file)
        self.feedback_collector = FeedbackCollector(feedback_file=feedback_file)
    
    def summarize(self, message_data: Dict, use_context: bool = True) -> Dict:
        """Summarize message and prepare for feedback collection."""
        result = self.summarizer.summarize(message_data, use_context=use_context)
        
        # Add feedback-ready metadata
        result['feedback_ready'] = True
        result['message_id'] = message_data.get('message_id', f"msg_{datetime.now().timestamp()}")
        
        return result
    
    def collect_feedback(self, message_id: str, user_id: str, platform: str, 
                        original_text: str, generated_summary: str, 
                        feedback_score: int, feedback_comment: str = "",
                        category_ratings: Dict[str, int] = None) -> bool:
        """Collect feedback for a summarization result."""
        return self.feedback_collector.collect_feedback(
            message_id=message_id,
            user_id=user_id,
            platform=platform,
            original_text=original_text,
            generated_summary=generated_summary,
            feedback_score=feedback_score,
            feedback_comment=feedback_comment,
            category_ratings=category_ratings
        )
    
    def get_feedback_analytics(self) -> Dict:
        """Get feedback analytics."""
        return self.feedback_collector.get_feedback_analytics()


# Example usage and testing
if __name__ == "__main__":
    print("🔄 Testing Feedback System...")
    
    # Initialize feedback collector
    collector = FeedbackCollector('test_feedback.json')
    
    # Test feedback collection
    success = collector.collect_feedback(
        message_id='test_msg_1',
        user_id='test_user',
        platform='whatsapp',
        original_text='Hey! Can you send me those photos?',
        generated_summary='❓ Request for photos',
        feedback_score=1,
        feedback_comment='Good summary!',
        category_ratings={
            'summary_quality': 1,
            'intent_detection': 1,
            'urgency_level': 0
        }
    )
    
    print(f"✅ Feedback collection: {'Success' if success else 'Failed'}")
    
    # Test analytics
    analytics = collector.get_feedback_analytics()
    print(f"📊 Total feedback entries: {analytics['overall_metrics']['total_feedback']}")
    print(f"📈 Satisfaction rate: {analytics['overall_metrics'].get('satisfaction_rate', 0):.1%}")
    
    # Test enhanced summarizer
    enhanced = FeedbackEnhancedSummarizer('test_context.json', 'test_feedback.json')
    
    test_message = {
        'user_id': 'test_user',
        'platform': 'email',
        'message_text': 'Please review the quarterly report by Friday.',
        'timestamp': datetime.now().isoformat(),
        'message_id': 'enhanced_test_1'
    }
    
    result = enhanced.summarize(test_message)
    print(f"📝 Enhanced summary: {result['summary']}")
    print(f"🔄 Feedback ready: {result['feedback_ready']}")
    
    print("✅ Feedback System tests completed!")
