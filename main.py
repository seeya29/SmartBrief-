#!/usr/bin/env python3
"""
Smart Inbox Assistant - Main Application
Enhanced with SmartBrief v3 context-aware summarization, feedback system, and multi-platform support.
"""

import os
import sys
import json
import logging
from datetime import datetime
from typing import Dict, List, Optional

# Add project root to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Import all modules
from dashboard import create_dashboard
from email_reader import EmailReader
from smart_summarizer_v3 import SmartSummarizerV3, summarize_message
from context_loader import ContextLoader
from feedback_system import FeedbackCollector, FeedbackEnhancedSummarizer
from sentiment import analyze_sentiment_detailed
from priority_model import PriorityModel
from priority_tagging import PriorityTagger
from smart_suggestions import SmartSuggestionsModule
from tts import TextToSpeechEngine
from email_summarizer import EmailSummarizer
from visualizations import create_priority_chart, create_sentiment_chart
from credentials_manager import CredentialsManager

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('smart_inbox.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class SmartInboxAssistant:
    """
    Main Smart Inbox Assistant class with enhanced SmartBrief v3 integration.
    
    Features:
    - Context-aware message summarization
    - Multi-platform support (Email, WhatsApp, Slack, etc.)
    - Intent detection and urgency analysis
    - Feedback learning system
    - Priority tagging and smart suggestions
    - Text-to-speech capabilities
    - Interactive dashboard
    """
    
    def __init__(self, config_file: str = 'config.json'):
        """Initialize the Smart Inbox Assistant."""
        self.config_file = config_file
        self.config = self._load_config()
        
        # Initialize core components
        logger.info("Initializing Smart Inbox Assistant...")
        
        # Credentials manager
        self.credentials_manager = CredentialsManager()
        
        # Email reader
        self.email_reader = EmailReader()
        
        # SmartBrief v3 components
        self.summarizer = SmartSummarizerV3(
            context_file=self.config.get('context_file', 'message_context.json'),
            max_context_messages=self.config.get('max_context_messages', 3)
        )
        
        self.context_loader = ContextLoader(
            json_file=self.config.get('conversation_history_file', 'conversation_history.json'),
            csv_file=self.config.get('message_history_file', 'message_history.csv')
        )
        
        self.feedback_collector = FeedbackCollector(
            feedback_file=self.config.get('feedback_file', 'feedback_data.json')
        )
        
        self.feedback_enhanced_summarizer = FeedbackEnhancedSummarizer(
            context_file=self.config.get('context_file', 'message_context.json'),
            feedback_file=self.config.get('feedback_file', 'feedback_data.json')
        )
        
        # Legacy components (enhanced with new features)
        self.priority_model = PriorityModel()
        self.priority_tagger = PriorityTagger()
        self.smart_suggestions = SmartSuggestionsModule()
        self.tts_engine = TextToSpeechEngine()
        self.email_summarizer = EmailSummarizer()
        
        logger.info("✅ Smart Inbox Assistant initialized successfully!")
    
    def _load_config(self) -> Dict:
        """Load configuration from file."""
        default_config = {
            'context_file': 'message_context.json',
            'conversation_history_file': 'conversation_history.json',
            'message_history_file': 'message_history.csv',
            'feedback_file': 'feedback_data.json',
            'max_context_messages': 3,
            'use_context_awareness': True,
            'enable_feedback_learning': True,
            'supported_platforms': ['email', 'whatsapp', 'slack', 'teams', 'instagram', 'discord'],
            'tts_enabled': True,
            'dashboard_enabled': True
        }
        
        if os.path.exists(self.config_file):
            try:
                with open(self.config_file, 'r') as f:
                    user_config = json.load(f)
                    default_config.update(user_config)
            except Exception as e:
                logger.error(f"Error loading config: {e}")
        
        return default_config
    
    def _save_config(self):
        """Save current configuration to file."""
        try:
            with open(self.config_file, 'w') as f:
                json.dump(self.config, f, indent=2)
        except Exception as e:
            logger.error(f"Error saving config: {e}")
    
    def process_message(self, message_data: Dict, platform: str = 'email') -> Dict:
        """
        Process a single message with enhanced SmartBrief v3 analysis.
        
        Args:
            message_data: Message data dictionary
            platform: Platform type (email, whatsapp, slack, etc.)
            
        Returns:
            Comprehensive analysis results
        """
        try:
            # Ensure platform is set
            message_data['platform'] = platform
            
            # Add timestamp if not present
            if 'timestamp' not in message_data:
                message_data['timestamp'] = datetime.now().isoformat()
            
            # SmartBrief v3 analysis
            logger.info(f"Processing message from {message_data.get('user_id', 'unknown')} on {platform}")
            
            smart_analysis = self.feedback_enhanced_summarizer.summarize(
                message_data, 
                use_context=self.config.get('use_context_awareness', True)
            )
            
            # Legacy analysis for compatibility
            message_text = message_data.get('message_text', '')
            
            # Sentiment analysis
            sentiment_analysis = analyze_sentiment_detailed(message_text)
            
            # Priority analysis
            priority_score = self.priority_model.predict_priority(message_text)
            priority_tag = self.priority_tagger.tag_email({
                'subject': message_data.get('subject', ''),
                'body': message_text,
                'sender': message_data.get('sender', message_data.get('user_id', ''))
            })
            
            # Smart suggestions
            suggestions = self.smart_suggestions.generate_suggestions(
                {
                    'subject': message_data.get('subject', ''),
                    'body': message_text,
                    'sender': message_data.get('sender', message_data.get('user_id', '')),
                    'platform': platform,
                    'tag': priority_tag
                },
                priority_tag,
                smart_analysis['confidence']
            )
            
            # Combine all analysis results
            comprehensive_result = {
                # SmartBrief v3 results
                'summary': smart_analysis['summary'],
                'type': smart_analysis['type'],
                'intent': smart_analysis['intent'],
                'urgency': smart_analysis['urgency'],
                'confidence': smart_analysis['confidence'],
                'context_used': smart_analysis['context_used'],
                'platform_optimized': smart_analysis['platform_optimized'],
                'reasoning': smart_analysis['reasoning'],
                
                # Enhanced analysis
                'sentiment': sentiment_analysis,
                'priority_score': priority_score,
                'priority_tag': priority_tag,
                'suggestions': suggestions,
                
                # Metadata
                'platform': platform,
                'processed_at': datetime.now().isoformat(),
                'feedback_ready': smart_analysis.get('feedback_ready', False),
                'message_id': smart_analysis.get('message_id', message_data.get('message_id')),
                
                # Legacy compatibility
                'smart_analysis': smart_analysis,
                'metadata': smart_analysis.get('metadata', {})
            }
            
            # Store in context for future processing
            self.context_loader.add_message(message_data, comprehensive_result)
            
            logger.info(f"✅ Message processed successfully: {comprehensive_result['summary']}")
            return comprehensive_result
            
        except Exception as e:
            logger.error(f"Error processing message: {e}")
            return {
                'summary': 'Error processing message',
                'type': 'error',
                'intent': 'unknown',
                'urgency': 'low',
                'confidence': 0.0,
                'error': str(e),
                'processed_at': datetime.now().isoformat()
            }
    
    def process_emails(self, limit: int = 10) -> List[Dict]:
        """
        Process recent emails with enhanced analysis.
        
        Args:
            limit: Maximum number of emails to process
            
        Returns:
            List of processed email results
        """
        try:
            logger.info(f"Processing {limit} recent emails...")
            
            # Fetch emails
            emails = self.email_reader.fetch_recent_emails(limit)
            
            if not emails:
                logger.warning("No emails found to process")
                return []
            
            results = []
            for email in emails:
                # Convert email to message format
                message_data = {
                    'user_id': email.get('sender', 'unknown'),
                    'platform': 'email',
                    'message_text': email.get('body', ''),
                    'subject': email.get('subject', ''),
                    'sender': email.get('sender', ''),
                    'timestamp': email.get('date', datetime.now().isoformat()),
                    'message_id': email.get('id', f"email_{datetime.now().timestamp()}")
                }
                
                # Process with enhanced analysis
                result = self.process_message(message_data, 'email')
                result['original_email'] = email  # Keep original email data
                
                results.append(result)
            
            logger.info(f"✅ Processed {len(results)} emails successfully")
            return results
            
        except Exception as e:
            logger.error(f"Error processing emails: {e}")
            return []
    
    def collect_feedback(self, message_id: str, user_id: str, platform: str, 
                        original_text: str, generated_summary: str, 
                        feedback_score: int, feedback_comment: str = "",
                        category_ratings: Dict[str, int] = None) -> bool:
        """
        Collect user feedback for continuous improvement.
        
        Args:
            message_id: Unique message identifier
            user_id: User who provided feedback
            platform: Platform where message originated
            original_text: Original message text
            generated_summary: Generated summary
            feedback_score: Overall feedback score (-1, 0, 1)
            feedback_comment: Optional comment
            category_ratings: Category-specific ratings
            
        Returns:
            Success status
        """
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
    
    def get_analytics(self) -> Dict:
        """Get comprehensive analytics from all components."""
        try:
            # SmartBrief v3 analytics
            summarizer_stats = self.summarizer.get_stats()
            context_stats = self.context_loader.get_statistics()
            feedback_analytics = self.feedback_collector.get_feedback_analytics()
            
            # Smart suggestions analytics
            suggestions_stats = self.smart_suggestions.get_suggestion_stats()
            
            return {
                'summarizer_stats': summarizer_stats,
                'context_stats': context_stats,
                'feedback_analytics': feedback_analytics,
                'suggestions_stats': suggestions_stats,
                'generated_at': datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error generating analytics: {e}")
            return {'error': str(e)}
    
    def speak_summary(self, text: str) -> bool:
        """Convert text to speech using TTS engine."""
        if self.config.get('tts_enabled', True):
            return self.tts_engine.speak(text)
        return False
    
    def run_dashboard(self):
        """Launch the interactive dashboard."""
        if self.config.get('dashboard_enabled', True):
            logger.info("Launching interactive dashboard...")
            try:
                # Import and run Streamlit dashboard
                import subprocess
                import sys
                
                # Run the Streamlit app
                subprocess.run([
                    sys.executable, '-m', 'streamlit', 'run', 
                    'demo_streamlit_app.py', 
                    '--server.port', '8501',
                    '--server.headless', 'false'
                ])
            except Exception as e:
                logger.error(f"Error launching dashboard: {e}")
                # Fallback to basic dashboard
                create_dashboard()
        else:
            logger.info("Dashboard is disabled in configuration")
    
    def run_cli(self):
        """Run the command-line interface."""
        print("🤖 Smart Inbox Assistant - Enhanced with SmartBrief v3")
        print("=" * 60)
        
        while True:
            print("\nAvailable commands:")
            print("1. Process recent emails")
            print("2. Analyze single message")
            print("3. View analytics")
            print("4. Launch dashboard")
            print("5. Test message (demo)")
            print("6. Export data")
            print("7. Settings")
            print("0. Exit")
            
            try:
                choice = input("\nEnter your choice (0-7): ").strip()
                
                if choice == '0':
                    print("👋 Goodbye!")
                    break
                
                elif choice == '1':
                    limit = int(input("Number of emails to process (default 10): ") or "10")
                    results = self.process_emails(limit)
                    
                    print(f"\n📧 Processed {len(results)} emails:")
                    for i, result in enumerate(results[:5], 1):  # Show first 5
                        print(f"\n{i}. {result['summary']}")
                        print(f"   Type: {result['type']} | Intent: {result['intent']} | Urgency: {result['urgency']}")
                        print(f"   Confidence: {result['confidence']:.2f} | Context: {'Yes' if result['context_used'] else 'No'}")
                        
                        if self.config.get('tts_enabled'):
                            speak = input("   Speak summary? (y/n): ").lower() == 'y'
                            if speak:
                                self.speak_summary(result['summary'])
                
                elif choice == '2':
                    print("\n📝 Analyze Single Message")
                    user_id = input("User ID: ") or "demo_user"
                    platform = input("Platform (email/whatsapp/slack/teams/instagram): ") or "email"
                    message_text = input("Message text: ")
                    
                    if message_text:
                        message_data = {
                            'user_id': user_id,
                            'platform': platform,
                            'message_text': message_text,
                            'timestamp': datetime.now().isoformat()
                        }
                        
                        result = self.process_message(message_data, platform)
                        
                        print(f"\n📊 Analysis Results:")
                        print(f"Summary: {result['summary']}")
                        print(f"Type: {result['type']}")
                        print(f"Intent: {result['intent']}")
                        print(f"Urgency: {result['urgency']}")
                        print(f"Confidence: {result['confidence']:.2f}")
                        print(f"Context Used: {'Yes' if result['context_used'] else 'No'}")
                        print(f"Platform Optimized: {'Yes' if result['platform_optimized'] else 'No'}")
                        
                        print(f"\nReasoning:")
                        for reason in result['reasoning']:
                            print(f"  • {reason}")
                        
                        # Feedback collection
                        if result.get('feedback_ready')):
                            collect_feedback = input("\nProvide feedback? (y/n): ").lower() == 'y'
                            if collect_feedback:
                                feedback_score = int(input("Rate summary (1=good, 0=neutral, -1=poor): ") or "0")
                                feedback_comment = input("Optional comment: ")
                                
                                success = self.collect_feedback(
                                    message_id=result['message_id'],
                                    user_id=user_id,
                                    platform=platform,
                                    original_text=message_text,
                                    generated_summary=result['summary'],
                                    feedback_score=feedback_score,
                                    feedback_comment=feedback_comment
                                )
                                
                                if success:
                                    print("✅ Feedback collected successfully!")
                                else:
                                    print("❌ Failed to collect feedback")
                
                elif choice == '3':
                    print("\n📊 Analytics Dashboard")
                    analytics = self.get_analytics()
                    
                    if 'error' not in analytics:
                        print(f"\n📈 Summarizer Stats:")
                        stats = analytics['summarizer_stats']
                        print(f"  Messages Processed: {stats['processed']}")
                        print(f"  Context Usage Rate: {stats['context_usage_rate']:.1%}")
                        print(f"  Unique Users: {stats['unique_users']}")
                        print(f"  Platforms: {list(stats['platforms'].keys())}")
                        
                        print(f"\n🔄 Feedback Analytics:")
                        feedback = analytics['feedback_analytics']['overall_metrics']
                        if feedback.get('total_feedback', 0) > 0:
                            print(f"  Total Feedback: {feedback['total_feedback']}")
                            print(f"  Satisfaction Rate: {feedback.get('satisfaction_rate', 0):.1%}")
                            print(f"  Positive: {feedback['positive_feedback']}")
                            print(f"  Negative: {feedback['negative_feedback']}")
                        else:
                            print("  No feedback data available yet")
                    else:
                        print(f"Error generating analytics: {analytics['error']}")
                
                elif choice == '4':
                    print("\n🚀 Launching Interactive Dashboard...")
                    self.run_dashboard()
                
                elif choice == '5':
                    print("\n🧪 Demo Mode - Testing Sample Messages")
                    
                    demo_messages = [
                        {
                            'user_id': 'alice_work',
                            'platform': 'email',
                            'message_text': 'I will send the quarterly report tonight after the meeting.',
                        },
                        {
                            'user_id': 'alice_work',
                            'platform': 'email',
                            'message_text': 'Hey, did the report get done?',
                        },
                        {
                            'user_id': 'bob_friend',
                            'platform': 'whatsapp',
                            'message_text': 'yo whats up? party tonight at 8pm, u coming?',
                        },
                        {
                            'user_id': 'customer_insta',
                            'platform': 'instagram',
                            'message_text': 'love ur latest post! 😍 where did u get that dress?',
                        }
                    ]
                    
                    for i, message in enumerate(demo_messages, 1):
                        print(f"\n--- Demo Message {i} ({message['platform']}) ---")
                        result = self.process_message(message, message['platform'])
                        
                        print(f"Original: {message['message_text']}")
                        print(f"Summary: {result['summary']}")
                        print(f"Type: {result['type']} | Intent: {result['intent']} | Urgency: {result['urgency']}")
                        print(f"Context Used: {'Yes' if result['context_used'] else 'No'}")
                
                elif choice == '6':
                    print("\n💾 Export Data")
                    export_format = input("Format (json/csv): ").lower() or "json"
                    filename = input(f"Filename (default: export.{export_format}): ") or f"export.{export_format}"
                    
                    try:
                        success = self.context_loader.export_data(filename, export_format)
                        if success:
                            print(f"✅ Data exported to {filename}")
                        else:
                            print("❌ Export failed")
                    except Exception as e:
                        print(f"❌ Export error: {e}")
                
                elif choice == '7':
                    print("\n⚙️ Settings")
                    print(f"Current settings:")
                    print(f"  Context Awareness: {'Enabled' if self.config.get('use_context_awareness') else 'Disabled'}")
                    print(f"  Max Context Messages: {self.config.get('max_context_messages', 3)}")
                    print(f"  TTS Enabled: {'Yes' if self.config.get('tts_enabled') else 'No'}")
                    print(f"  Feedback Learning: {'Enabled' if self.config.get('enable_feedback_learning') else 'Disabled'}")
                    
                    modify = input("\nModify settings? (y/n): ").lower() == 'y'
                    if modify:
                        self.config['use_context_awareness'] = input("Enable context awareness? (y/n): ").lower() == 'y'
                        self.config['max_context_messages'] = int(input("Max context messages (1-10): ") or "3")
                        self.config['tts_enabled'] = input("Enable TTS? (y/n): ").lower() == 'y'
                        self.config['enable_feedback_learning'] = input("Enable feedback learning? (y/n): ").lower() == 'y'
                        
                        self._save_config()
                        print("✅ Settings saved!")
                
                else:
                    print("❌ Invalid choice. Please try again.")
                    
            except KeyboardInterrupt:
                print("\n\n👋 Goodbye!")
                break
            except Exception as e:
                print(f"❌ Error: {e}")
                logger.error(f"CLI error: {e}")

def main():
    """Main entry point for the Smart Inbox Assistant."""
    try:
        # Initialize the assistant
        assistant = SmartInboxAssistant()
        
        # Check command line arguments
        if len(sys.argv) > 1:
            command = sys.argv[1].lower()
            
            if command == 'dashboard':
                assistant.run_dashboard()
            elif command == 'process':
                limit = int(sys.argv[2]) if len(sys.argv) > 2 else 10
                results = assistant.process_emails(limit)
                print(f"Processed {len(results)} emails")
            elif command == 'analytics':
                analytics = assistant.get_analytics()
                print(json.dumps(analytics, indent=2, default=str))
            elif command == 'demo':
                # Quick demo
                result = summarize_message(
                    "Hey, did the report get done? The board meeting is tomorrow!",
                    platform='email',
                    user_id='demo_user'
                )
                print(f"Demo Summary: {result['summary']}")
                print(f"Type: {result['type']} | Intent: {result['intent']} | Urgency: {result['urgency']}")
            else:
                print(f"Unknown command: {command}")
                print("Available commands: dashboard, process, analytics, demo")
        else:
            # Run CLI interface
            assistant.run_cli()
            
    except Exception as e:
        logger.error(f"Fatal error: {e}")
        print(f"❌ Fatal error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
