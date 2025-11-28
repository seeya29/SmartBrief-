"""
SmartBrief v3 - Context-Aware, Platform-Agnostic Message Summarizer
Enhanced version with context intelligence, intent detection, and urgency analysis.
"""

import json
import os
import re
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
import logging

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class SmartSummarizerV3:
    """
    Advanced message summarizer with context awareness and platform optimization.
    
    Features:
    - Context-aware summarization using conversation history
    - Platform-specific optimization (WhatsApp, Email, Slack, etc.)
    - Intent detection (question, request, follow-up, complaint, etc.)
    - Urgency analysis with confidence scoring
    - Embeddable design for integration into existing systems
    """
    
    def __init__(self, context_file: str = 'message_context.json', max_context_messages: int = 3, confidence_threshold: float = 0.6):
        self.context_file = context_file
        self.max_context_messages = max_context_messages
        self.confidence_threshold = confidence_threshold
        
        # Load existing context
        self.context_data = self._load_context()
        
        # Platform-specific settings
        self.platform_configs = {
            'whatsapp': {
                'max_summary_length': 50,
                'emoji_friendly': True,
                'casual_tone': True,
                'abbreviations': True
            },
            'email': {
                'max_summary_length': 100,
                'emoji_friendly': False,
                'casual_tone': False,
                'abbreviations': False
            },
            'slack': {
                'max_summary_length': 75,
                'emoji_friendly': True,
                'casual_tone': True,
                'abbreviations': True
            },
            'teams': {
                'max_summary_length': 80,
                'emoji_friendly': False,
                'casual_tone': False,
                'abbreviations': False
            },
            'instagram': {
                'max_summary_length': 40,
                'emoji_friendly': True,
                'casual_tone': True,
                'abbreviations': True
            },
            'discord': {
                'max_summary_length': 60,
                'emoji_friendly': True,
                'casual_tone': True,
                'abbreviations': True
            }
        }
        
        # Intent patterns
        self.intent_patterns = {
            'question': [
                r'\?', r'\bwhat\b', r'\bhow\b', r'\bwhen\b', r'\bwhere\b', 
                r'\bwhy\b', r'\bwhich\b', r'\bwho\b', r'\bcan you\b', r'\bcould you\b'
            ],
            'request': [
                r'\bplease\b', r'\bcould you\b', r'\bwould you\b', r'\bcan you\b',
                r'\bneed\b', r'\brequire\b', r'\bwant\b', r'\bsend me\b'
            ],
            'follow_up': [
                r'\bfollow.?up\b', r'\bupdate\b', r'\bstatus\b', r'\bprogress\b',
                r'\bany news\b', r'\bhow.?s it going\b', r'\bheard back\b', r'\bdid.*get done\b'
            ],
            'complaint': [
                r'\bissue\b', r'\bproblem\b', r'\berror\b', r'\bbug\b', r'\bwrong\b',
                r'\bnot working\b', r'\bbroken\b', r'\bfailed\b', r'\bdisappointed\b'
            ],
            'appreciation': [
                r'\bthank\b', r'\bthanks\b', r'\bappreciate\b', r'\bgreat\b',
                r'\bawesome\b', r'\bexcellent\b', r'\bgood job\b', r'\bwell done\b'
            ],
            'urgent': [
                r'\burgent\b', r'\basap\b', r'\bemergency\b', r'\bcritical\b',
                r'\bimmediately\b', r'\bright now\b', r'\bdeadline today\b'
            ],
            'social': [
                r'\bhey\b', r'\bhi\b', r'\bhello\b', r'\bhow are you\b',
                r'\bwhat.?s up\b', r'\bhang out\b', r'\bmeet up\b', r'\bparty\b'
            ],
            'informational': [
                r'\bfyi\b', r'\bfor your information\b', r'\bjust letting you know\b',
                r'\bheads up\b', r'\bnotice\b', r'\bannouncement\b'
            ],
            'confirmation': [
                r'\bconfirm\b', r'\bconfirmed\b', r'\byes\b', r'\bokay\b', r'\bgot it\b',
                r'\bunderstood\b', r'\bagree\b', r'\bsounds good\b'
            ],
            'schedule': [
                r'\bmeeting\b', r'\bappointment\b', r'\bschedule\b', r'\bcalendar\b',
                r'\btime\b', r'\bdate\b', r'\btomorrow\b', r'\bnext week\b'
            ],
            'check_progress': [
                r'\bprogress\b', r'\bstatus\b', r'\bhow.?s.*going\b', r'\bupdate\b',
                r'\bdone\b', r'\bfinished\b', r'\bcomplete\b', r'\bready\b'
            ]
        }
        
        # Urgency indicators
        self.urgency_indicators = {
            'high': [
                r'\burgent\b', r'\basap\b', r'\bemergency\b', r'\bcritical\b',
                r'\bimmediately\b', r'\bright now\b', r'\bdeadline today\b',
                r'\bnow\b', r'\btoday\b', r'\bpls respond\b'
            ],
            'medium': [
                r'\bsoon\b', r'\bquickly\b', r'\bpriority\b', r'\bimportant\b',
                r'\bdeadline\b', r'\bby tomorrow\b', r'\bthis week\b'
            ],
            'low': [
                r'\bwhen you can\b', r'\bno rush\b', r'\bwhenever\b',
                r'\bno hurry\b', r'\btake your time\b'
            ]
        }
        
        # Statistics tracking
        self.stats = {
            'processed': 0,
            'context_used': 0,
            'platforms': {},
            'intents': {},
            'urgency_levels': {},
            'unique_users': set()
        }
    
    def _load_context(self) -> Dict:
        """Load conversation context from file."""
        if os.path.exists(self.context_file):
            try:
                with open(self.context_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    # Clean old messages (older than 30 days)
                    self._cleanup_old_context(data)
                    return data
            except Exception as e:
                logger.error(f"Error loading context: {e}")
        
        return {'conversations': {}, 'user_profiles': {}}
    
    def _save_context(self):
        """Save conversation context to file."""
        try:
            with open(self.context_file, 'w', encoding='utf-8') as f:
                json.dump(self.context_data, f, indent=2, ensure_ascii=False)
        except Exception as e:
            logger.error(f"Error saving context: {e}")
    
    def _cleanup_old_context(self, data: Dict):
        """Remove messages older than 30 days."""
        cutoff_date = datetime.now() - timedelta(days=30)
        cutoff_timestamp = cutoff_date.timestamp()
        
        conversations = data.get('conversations', {})
        for user_platform, messages in conversations.items():
            # Filter out old messages
            data['conversations'][user_platform] = [
                msg for msg in messages
                if datetime.fromisoformat(msg.get('timestamp', '1970-01-01T00:00:00')).timestamp() > cutoff_timestamp
            ]
    
    def _get_context_key(self, user_id: str, platform: str) -> str:
        """Generate context key for user-platform combination."""
        return f"{user_id}_{platform}"
    
    def _extract_context(self, user_id: str, platform: str) -> List[Dict]:
        """Extract relevant context messages for a user-platform combination."""
        context_key = self._get_context_key(user_id, platform)
        conversations = self.context_data.get('conversations', {})
        
        if context_key in conversations:
            # Return last N messages
            messages = conversations[context_key]
            return messages[-self.max_context_messages:] if messages else []
        
        return []
    
    def _store_message_context(self, message_data: Dict):
        """Store message in context for future reference."""
        user_id = message_data.get('user_id', 'unknown')
        platform = message_data.get('platform', 'unknown')
        context_key = self._get_context_key(user_id, platform)
        
        # Initialize if not exists
        if 'conversations' not in self.context_data:
            self.context_data['conversations'] = {}
        
        if context_key not in self.context_data['conversations']:
            self.context_data['conversations'][context_key] = []
        
        # Add message to context
        context_message = {
            'message_text': message_data.get('message_text', ''),
            'timestamp': message_data.get('timestamp', datetime.now().isoformat()),
            'message_id': message_data.get('message_id', f"msg_{datetime.now().timestamp()}")
        }
        
        self.context_data['conversations'][context_key].append(context_message)
        
        # Keep only recent messages
        if len(self.context_data['conversations'][context_key]) > self.max_context_messages * 2:
            self.context_data['conversations'][context_key] = \
                self.context_data['conversations'][context_key][-self.max_context_messages * 2:]
        
        self._save_context()
    
    def _classify_intent(self, text: str, context_messages: List[Dict] = None) -> tuple:
        """Classify the intent of the message with context awareness."""
        text_lower = text.lower()
        intent_scores = {}
        
        # Base intent scoring
        for intent, patterns in self.intent_patterns.items():
            score = 0
            for pattern in patterns:
                matches = len(re.findall(pattern, text_lower))
                score += matches
            
            if score > 0:
                intent_scores[intent] = score
        
        # Context-aware intent adjustment
        if context_messages:
            # Check for follow-up patterns
            follow_up_keywords = ['update', 'status', 'progress', 'done', 'finished']
            if any(keyword in text_lower for keyword in follow_up_keywords):
                # Look for related topics in previous messages
                for prev_msg in context_messages:
                    prev_text = prev_msg.get('message_text', '').lower()
                    # Simple keyword overlap check
                    current_words = set(text_lower.split())
                    prev_words = set(prev_text.split())
                    overlap = len(current_words.intersection(prev_words))
                    
                    if overlap > 1:  # Some topic continuity
                        intent_scores['follow_up'] = intent_scores.get('follow_up', 0) + 2
                        intent_scores['check_progress'] = intent_scores.get('check_progress', 0) + 1
        
        if intent_scores:
            best_intent = max(intent_scores.keys(), key=lambda k: intent_scores[k])
            max_score = intent_scores[best_intent]
            confidence = min(1.0, max_score / 3.0)  # Normalize confidence
            return best_intent, confidence
        
        return 'informational', 0.3  # Default intent
    
    def _analyze_urgency(self, text: str, context_messages: List[Dict] = None) -> tuple:
        """Analyze the urgency level of the message with context awareness."""
        text_lower = text.lower()
        urgency_scores = {'high': 0, 'medium': 0, 'low': 0}
        
        for level, patterns in self.urgency_indicators.items():
            for pattern in patterns:
                matches = len(re.findall(pattern, text_lower))
                urgency_scores[level] += matches
        
        # Context-aware urgency adjustment
        if context_messages:
            # Check for escalating urgency
            previous_texts = [msg.get('message_text', '').lower() for msg in context_messages]
            urgency_words = ['urgent', 'asap', 'immediately', 'critical', 'deadline']
            
            current_urgency_count = sum(1 for word in urgency_words if word in text_lower)
            previous_urgency_count = sum(sum(1 for word in urgency_words if word in text) for text in previous_texts)
            
            if current_urgency_count > previous_urgency_count:
                urgency_scores['high'] += 1  # Escalating urgency
        
        # Determine urgency level
        if urgency_scores['high'] > 0:
            return 'high', min(1.0, urgency_scores['high'] / 2.0)
        elif urgency_scores['medium'] > 0:
            return 'medium', min(1.0, urgency_scores['medium'] / 2.0)
        elif urgency_scores['low'] > 0:
            return 'low', min(1.0, urgency_scores['low'] / 2.0)
        else:
            # Default urgency based on message characteristics
            if len(text) < 50:
                return 'low', 0.4
            elif '?' in text or any(word in text_lower for word in ['need', 'want', 'require']):
                return 'medium', 0.5
            else:
                return 'low', 0.3
    
    def _analyze_context(self, current_message: Dict, context_messages: List[Dict]) -> List[str]:
        """Analyze conversation context for insights."""
        insights = []
        
        if not context_messages:
            return insights
        
        current_text = current_message.get('message_text', '').lower()
        
        # Look for conversation patterns
        recent_messages = context_messages[-3:] if len(context_messages) >= 3 else context_messages
        
        # Check for follow-up patterns
        follow_up_keywords = ['update', 'status', 'any news', 'heard back', 'follow up', 'did.*get done']
        if any(re.search(keyword, current_text) for keyword in follow_up_keywords):
            insights.append("This appears to be a follow-up to previous conversation")
        
        # Check for escalating urgency
        previous_texts = [msg.get('message_text', '').lower() for msg in recent_messages]
        urgency_words = ['urgent', 'asap', 'immediately', 'critical', 'deadline']
        
        current_urgency = sum(1 for word in urgency_words if word in current_text)
        previous_urgency = sum(sum(1 for word in urgency_words if word in text) for text in previous_texts)
        
        if current_urgency > previous_urgency:
            insights.append("Urgency level has increased compared to previous messages")
        
        # Check for topic continuity
        if recent_messages:
            last_message_text = recent_messages[-1].get('message_text', '').lower()
            
            # Simple keyword overlap check
            current_words = set(re.findall(r'\b\w+\b', current_text))
            last_words = set(re.findall(r'\b\w+\b', last_message_text))
            
            overlap = len(current_words.intersection(last_words))
            if overlap > 2:
                insights.append("Continues previous conversation topic")
        
        # Check for sentiment shift
        positive_words = ['thanks', 'great', 'good', 'excellent', 'appreciate']
        negative_words = ['problem', 'issue', 'wrong', 'error', 'disappointed']
        
        current_positive = sum(1 for word in positive_words if word in current_text)
        current_negative = sum(1 for word in negative_words if word in current_text)
        
        if current_positive > 0 and len(recent_messages) > 0:
            insights.append("Positive sentiment detected - possibly expressing gratitude")
        elif current_negative > 0:
            insights.append("Negative sentiment detected - may indicate frustration")
        
        return insights
    
    def _generate_summary(self, text: str, platform: str, intent: str, urgency: str, context_insights: List[str]) -> str:
        """Generate platform-optimized summary."""
        config = self.platform_configs.get(platform, self.platform_configs['email'])
        max_length = config['max_summary_length']
        
        # Base summary generation
        sentences = re.split(r'[.!?]+', text.strip())
        sentences = [s.strip() for s in sentences if s.strip()]
        
        if not sentences:
            return "Empty message"
        
        # Take the first sentence as base summary
        base_summary = sentences[0]
        
        # Add context-aware prefixes
        if context_insights:
            if "follow-up" in context_insights[0].lower():
                base_summary = "Follow-up: " + base_summary
            elif "continues previous" in context_insights[0].lower():
                base_summary = "Continuing: " + base_summary
        
        # Add intent-specific context
        if intent == 'check_progress':
            base_summary = "User is checking progress on " + base_summary.lower()
        elif intent == 'follow_up':
            base_summary = "User is following up on " + base_summary.lower()
        
        # Add intent/urgency indicators based on platform
        if config['emoji_friendly']:
            emoji_map = {
                'question': '❓',
                'request': '🙏',
                'urgent': '🚨',
                'appreciation': '🙏',
                'complaint': '⚠️',
                'social': '👋',
                'follow_up': '🔄',
                'check_progress': '📊'
            }
            
            if intent in emoji_map:
                base_summary = emoji_map[intent] + ' ' + base_summary
        
        # Truncate to platform limits
        if len(base_summary) > max_length:
            base_summary = base_summary[:max_length-3] + '...'
        
        # Platform-specific adjustments
        if config['casual_tone'] and platform in ['whatsapp', 'slack', 'discord', 'instagram']:
            base_summary = base_summary.replace('Please', 'Pls').replace('you', 'u')
        
        return base_summary
    
    def _generate_reasoning(self, intent: str, urgency: str, context_used: bool, context_insights: List[str], platform: str) -> List[str]:
        """Generate reasoning for the analysis."""
        reasoning = []
        
        reasoning.append(f"Classified as '{intent}' intent based on message patterns")
        reasoning.append(f"Urgency level: '{urgency}' based on keyword analysis")
        reasoning.append(f"Platform-optimized for {platform}")
        
        if context_used:
            reasoning.append(f"Used conversation context ({len(context_insights)} insights)")
            for insight in context_insights[:2]:  # Show top 2 insights
                reasoning.append(f"Context: {insight}")
        else:
            reasoning.append("No conversation context available")
        
        return reasoning
    
    def _update_stats(self, user_id: str, platform: str, intent: str, urgency: str):
        """Update processing statistics."""
        self.stats['processed'] += 1
        self.stats['unique_users'].add(user_id)
        
        if platform not in self.stats['platforms']:
            self.stats['platforms'][platform] = 0
        self.stats['platforms'][platform] += 1
        
        if intent not in self.stats['intents']:
            self.stats['intents'][intent] = 0
        self.stats['intents'][intent] += 1
        
        if urgency not in self.stats['urgency_levels']:
            self.stats['urgency_levels'][urgency] = 0
        self.stats['urgency_levels'][urgency] += 1
    
    def summarize(self, message_data: Dict, use_context: bool = True) -> Dict:
        """
        Summarize a single message with context awareness.
        
        Args:
            message_data: Dictionary containing message information
            use_context: Whether to use conversation context
            
        Returns:
            Dictionary with summary and analysis results
        """
        try:
            # Extract message details
            user_id = message_data.get('user_id', 'unknown')
            platform = message_data.get('platform', 'email')
            message_text = message_data.get('message_text', '')
            timestamp = message_data.get('timestamp', datetime.now().isoformat())
            
            # Get context if requested
            context = []
            context_used = False
            
            if use_context:
                context = self._extract_context(user_id, platform)
                context_used = len(context) > 0
                if context_used:
                    self.stats['context_used'] += 1
            
            # Analyze message with context
            intent, intent_confidence = self._classify_intent(message_text, context)
            urgency, urgency_confidence = self._analyze_urgency(message_text, context)
            
            # Analyze context insights
            context_insights = self._analyze_context(message_data, context)
            
            # Generate summary
            summary = self._generate_summary(message_text, platform, intent, urgency, context_insights)
            
            # Determine message type
            message_type = self._determine_message_type(intent, urgency, context_insights)
            
            # Calculate overall confidence
            overall_confidence = (intent_confidence + urgency_confidence) / 2
            
            # Generate reasoning
            reasoning = self._generate_reasoning(intent, urgency, context_used, context_insights, platform)
            
            # Store message in context for future use
            self._store_message_context(message_data)
            
            # Update statistics
            self._update_stats(user_id, platform, intent, urgency)
            
            result = {
                'summary': summary,
                'type': message_type,
                'intent': intent,
                'urgency': urgency,
                'confidence': overall_confidence,
                'context_used': context_used,
                'platform_optimized': True,
                'reasoning': reasoning,
                'metadata': {
                    'intent_confidence': intent_confidence,
                    'urgency_confidence': urgency_confidence,
                    'context_messages_used': len(context),
                    'platform': platform,
                    'timestamp': timestamp,
                    'context_insights': context_insights
                }
            }
            
            logger.info(f"Summarized message for {user_id} on {platform}: {summary}")
            return result
            
        except Exception as e:
            logger.error(f"Error summarizing message: {e}")
            return {
                'summary': 'Error processing message',
                'type': 'error',
                'intent': 'unknown',
                'urgency': 'low',
                'confidence': 0.0,
                'context_used': False,
                'platform_optimized': False,
                'reasoning': [f'Error: {str(e)}'],
                'metadata': {}
            }
    
    def _determine_message_type(self, intent: str, urgency: str, context_insights: List[str]) -> str:
        """Determine message type based on intent, urgency, and context."""
        if urgency == 'high':
            return 'urgent'
        elif intent == 'follow_up' or intent == 'check_progress':
            return 'follow-up'
        elif intent == 'question':
            return 'inquiry'
        elif intent == 'request':
            return 'request'
        elif intent == 'complaint':
            return 'complaint'
        elif intent == 'appreciation':
            return 'appreciation'
        elif intent == 'confirmation':
            return 'confirmation'
        elif intent == 'schedule':
            return 'scheduling'
        else:
            return 'general'
    
    def batch_summarize(self, messages: List[Dict], use_context: bool = True) -> List[Dict]:
        """
        Summarize multiple messages in batch.
        
        Args:
            messages: List of message dictionaries
            use_context: Whether to use conversation context
            
        Returns:
            List of summary results
        """
        results = []
        
        for i, message in enumerate(messages):
            result = self.summarize(message, use_context)
            results.append(result)
        
        logger.info(f"Batch summarized {len(messages)} messages")
        return results
    
    def get_user_context(self, user_id: str, platform: str) -> List[Dict]:
        """Get conversation context for a specific user and platform."""
        return self._extract_context(user_id, platform)
    
    def get_stats(self) -> Dict:
        """Get processing statistics."""
        stats = self.stats.copy()
        stats['unique_users'] = len(stats['unique_users'])
        stats['context_usage_rate'] = (stats['context_used'] / max(1, stats['processed']))
        stats['total_context_entries'] = stats['context_used']
        return stats
    
    def reset_stats(self):
        """Reset processing statistics."""
        self.stats = {
            'processed': 0,
            'context_used': 0,
            'platforms': {},
            'intents': {},
            'urgency_levels': {},
            'unique_users': set()
        }

    def export_config(self) -> Dict:
        """Export current configuration."""
        return {
            'max_context_messages': self.max_context_messages,
            'confidence_threshold': self.confidence_threshold,
            'platform_configs': self.platform_configs,
            'intent_patterns': self.intent_patterns,
            'urgency_indicators': self.urgency_indicators
        }

    def update_config(self, config: Dict):
        """Update configuration."""
        if 'max_context_messages' in config:
            self.max_context_messages = config['max_context_messages']
        if 'confidence_threshold' in config:
            self.confidence_threshold = config['confidence_threshold']
        if 'platform_configs' in config:
            self.platform_configs.update(config['platform_configs'])


def summarize_message(message_text: str, platform: str = 'email', user_id: str = 'default') -> Dict:
    """
    Standalone function for quick message summarization.
    
    Args:
        message_text: The message to summarize
        platform: Platform type (email, whatsapp, slack, etc.)
        user_id: User identifier
        
    Returns:
        Summary result dictionary
    """
    summarizer = SmartSummarizerV3()
    
    message = {
        'user_id': user_id,
        'platform': platform,
        'message_text': message_text,
        'timestamp': datetime.now().isoformat()
    }
    
    return summarizer.summarize(message, use_context=False)


# Example usage and testing
if __name__ == "__main__":
    # Initialize summarizer
    summarizer = SmartSummarizerV3()
    
    # Test messages with context scenario
    test_messages = [
        {
            'user_id': 'alice_work',
            'platform': 'email',
            'message_text': 'I will send the quarterly report tonight after the meeting.',
            'timestamp': '2025-08-07T09:00:00Z'
        },
        {
            'user_id': 'alice_work',
            'platform': 'email',
            'message_text': 'Hey, did the report get done?',
            'timestamp': '2025-08-07T16:45:00Z'
        },
        {
            'user_id': 'bob_friend',
            'platform': 'whatsapp',
            'message_text': 'yo whats up? party tonight at 8pm, u coming?',
            'timestamp': '2025-08-07T14:30:00Z'
        },
        {
            'user_id': 'customer_insta',
            'platform': 'instagram',
            'message_text': 'love ur latest post! 😍 where did u get that dress?',
            'timestamp': '2025-08-07T11:15:00Z'
        }
    ]
    
    # Test batch processing
    results = summarizer.batch_summarize(test_messages, use_context=True)
    
    # Display results
    for i, (message, result) in enumerate(zip(test_messages, results)):
        print(f"\n--- Message {i+1} ({message['platform']}) ---")
        print(f"Original: {message['message_text']}")
        print(f"Summary: {result['summary']}")
        print(f"Type: {result['type']} | Intent: {result['intent']} | Urgency: {result['urgency']}")
        print(f"Confidence: {result['confidence']:.2f}")
        print(f"Context Used: {result['context_used']}")
        print("Reasoning:")
        for reason in result['reasoning']:
            print(f"  - {reason}")
    
    # Show statistics
    print(f"\n--- Statistics ---")
    stats = summarizer.get_stats()
    print(f"Processed: {stats['processed']}")
    print(f"Context Usage Rate: {stats['context_usage_rate']:.1%}")
    print(f"Platforms: {stats['platforms']}")
    print(f"Intents: {stats['intents']}")
    print(f"Urgency Levels: {stats['urgency_levels']}")
