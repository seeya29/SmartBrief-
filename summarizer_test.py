"""
Comprehensive Test Suite for SmartBrief v3
Tests all components including context awareness, intent detection, and platform optimization.
"""

import unittest
import json
import os
import tempfile
from datetime import datetime, timedelta
from smart_summarizer_v3 import SmartSummarizerV3, summarize_message
from summaryflow_v3 import summarize_message as flow_summarize
from context_loader import ContextLoader
from feedback_system import FeedbackCollector, FeedbackEnhancedSummarizer

class TestSmartSummarizerV3(unittest.TestCase):
    """Test cases for SmartSummarizerV3 core functionality."""
    
    def setUp(self):
        """Set up test environment."""
        # Use temporary files for testing
        self.temp_dir = tempfile.mkdtemp()
        self.context_file = os.path.join(self.temp_dir, 'test_context.json')
        self.summarizer = SmartSummarizerV3(context_file=self.context_file)
        
        # Test messages
        self.test_messages = [
            {
                'user_id': 'alice',
                'platform': 'whatsapp',
                'message_text': 'Hey! Can you send me those photos from yesterday?',
                'timestamp': '2025-08-07T10:00:00Z',
                'message_id': 'test_msg_1'
            },
            {
                'user_id': 'bob',
                'platform': 'email',
                'message_text': 'Please review the quarterly budget proposal attached. Need feedback by Friday.',
                'timestamp': '2025-08-07T09:00:00Z',
                'message_id': 'test_msg_2'
            },
            {
                'user_id': 'charlie',
                'platform': 'slack',
                'message_text': 'The server is down! This is critical - customers can\'t access the system.',
                'timestamp': '2025-08-07T11:00:00Z',
                'message_id': 'test_msg_3'
            }
        ]
    
    def tearDown(self):
        """Clean up test environment."""
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def test_basic_summarization(self):
        """Test basic message summarization."""
        message = self.test_messages[0]
        result = self.summarizer.summarize(message, use_context=False)
        
        self.assertIsInstance(result, dict)
        self.assertIn('summary', result)
        self.assertIn('intent', result)
        self.assertIn('urgency', result)
        self.assertIn('confidence', result)
        self.assertIsInstance(result['confidence'], float)
        self.assertGreaterEqual(result['confidence'], 0.0)
        self.assertLessEqual(result['confidence'], 1.0)
    
    def test_intent_detection(self):
        """Test intent detection accuracy."""
        test_cases = [
            ('What time is the meeting?', 'question'),
            ('Can you send me the report?', 'request'),
            ('Any update on the project?', 'follow_up'),
            ('The system is not working!', 'complaint'),
            ('Thanks for your help!', 'appreciation'),
            ('This is urgent - need immediate response!', 'urgent'),
            ('How are you doing?', 'social'),
            ('FYI - meeting moved to 3 PM', 'informational')
        ]
        
        for message_text, expected_intent in test_cases:
            message = {
                'user_id': 'test_user',
                'platform': 'email',
                'message_text': message_text,
                'timestamp': datetime.now().isoformat()
            }
            
            result = self.summarizer.summarize(message, use_context=False)
            self.assertEqual(result['intent'], expected_intent, 
                           f"Failed for message: '{message_text}'. Expected: {expected_intent}, Got: {result['intent']}")
    
    def test_urgency_analysis(self):
        """Test urgency level detection."""
        test_cases = [
            ('This is urgent! Need response ASAP!', 'high'),
            ('Please review when you have time', 'low'),
            ('Can you get back to me by tomorrow?', 'medium'),
            ('EMERGENCY: Server is down!', 'high'),
            ('FYI - just letting you know', 'low')
        ]
        
        for message_text, expected_urgency in test_cases:
            message = {
                'user_id': 'test_user',
                'platform': 'email',
                'message_text': message_text,
                'timestamp': datetime.now().isoformat()
            }
            
            result = self.summarizer.summarize(message, use_context=False)
            self.assertEqual(result['urgency'], expected_urgency,
                           f"Failed for message: '{message_text}'. Expected: {expected_urgency}, Got: {result['urgency']}")
    
    def test_platform_optimization(self):
        """Test platform-specific summary optimization."""
        message_text = "Hey! Can you send me those vacation photos from last weekend? I need them for my Instagram story ASAP!"
        
        platforms_and_limits = [
            ('whatsapp', 50),
            ('email', 100),
            ('slack', 60),
            ('instagram', 40)
        ]
        
        for platform, max_length in platforms_and_limits:
            message = {
                'user_id': 'test_user',
                'platform': platform,
                'message_text': message_text,
                'timestamp': datetime.now().isoformat()
            }
            
            result = self.summarizer.summarize(message, use_context=False)
            summary_length = len(result['summary'])
            
            self.assertLessEqual(summary_length, max_length,
                               f"Summary too long for {platform}: {summary_length} > {max_length}")
            self.assertTrue(result['platform_optimized'])
    
    def test_context_awareness(self):
        """Test context-aware summarization."""
        # First message
        msg1 = {
            'user_id': 'alice',
            'platform': 'whatsapp',
            'message_text': 'Can you send me those photos?',
            'timestamp': '2025-08-07T10:00:00Z',
            'message_id': 'context_test_1'
        }
        
        # Second message (follow-up)
        msg2 = {
            'user_id': 'alice',
            'platform': 'whatsapp',
            'message_text': 'Any update on those photos? Need them urgently!',
            'timestamp': '2025-08-07T10:30:00Z',
            'message_id': 'context_test_2'
        }
        
        # Process first message
        result1 = self.summarizer.summarize(msg1, use_context=True)
        self.assertFalse(result1['context_used'])  # No prior context
        
        # Process second message
        result2 = self.summarizer.summarize(msg2, use_context=True)
        self.assertTrue(result2['context_used'])  # Should use context from first message
        self.assertEqual(result2['intent'], 'follow_up')  # Should detect as follow-up
    
    def test_batch_processing(self):
        """Test batch message processing."""
        results = self.summarizer.batch_summarize(self.test_messages, use_context=True)
        
        self.assertEqual(len(results), len(self.test_messages))
        
        for result in results:
            self.assertIn('summary', result)
            self.assertIn('intent', result)
            self.assertIn('urgency', result)
            self.assertIn('confidence', result)
    
    def test_statistics_tracking(self):
        """Test statistics tracking functionality."""
        # Process some messages
        for message in self.test_messages:
            self.summarizer.summarize(message, use_context=True)
        
        stats = self.summarizer.get_stats()
        
        self.assertEqual(stats['processed'], len(self.test_messages))
        self.assertIn('platforms', stats)
        self.assertIn('intents', stats)
        self.assertIn('urgency_levels', stats)
        self.assertGreaterEqual(stats['unique_users'], 1)
    
    def test_context_persistence(self):
        """Test context data persistence across sessions."""
        message = self.test_messages[0]
        
        # Process message with first summarizer instance
        result1 = self.summarizer.summarize(message, use_context=True)
        
        # Create new summarizer instance with same context file
        new_summarizer = SmartSummarizerV3(context_file=self.context_file)
        
        # Check if context was loaded
        context = new_summarizer.get_user_context(message['user_id'], message['platform'])
        self.assertGreater(len(context), 0)
    
    def test_convenience_function(self):
        """Test the convenience summarize_message function."""
        message = self.test_messages[0]
        result = summarize_message(message, use_context=False)
        
        self.assertIsInstance(result, dict)
        self.assertIn('summary', result)
        self.assertIn('intent', result)
        self.assertIn('urgency', result)


class TestContextLoader(unittest.TestCase):
    """Test cases for ContextLoader functionality."""
    
    def setUp(self):
        """Set up test environment."""
        self.temp_dir = tempfile.mkdtemp()
        self.json_file = os.path.join(self.temp_dir, 'test_context.json')
        self.csv_file = os.path.join(self.temp_dir, 'test_history.csv')
        self.loader = ContextLoader(
            json_file=self.json_file,
            csv_file=self.csv_file,
            max_context_days=30
        )
    
    def tearDown(self):
        """Clean up test environment."""
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def test_message_storage(self):
        """Test message storage and retrieval."""
        message = {
            'user_id': 'test_user',
            'platform': 'whatsapp',
            'message_text': 'Test message',
            'timestamp': datetime.now().isoformat(),
            'message_id': 'test_msg_1'
        }
        
        analysis = {
            'intent': 'question',
            'urgency': 'medium',
            'summary': 'Test summary',
            'context_used': False
        }
        
        # Add message
        self.loader.add_message(message, analysis)
        
        # Retrieve context
        context = self.loader.get_context('test_user', 'whatsapp', limit=5)
        self.assertEqual(len(context), 1)
        self.assertEqual(context[0]['message_text'], 'Test message')
    
    def test_user_analytics(self):
        """Test user analytics generation."""
        # Add multiple messages for a user
        for i in range(3):
            message = {
                'user_id': 'analytics_user',
                'platform': 'email',
                'message_text': f'Test message {i+1}',
                'timestamp': datetime.now().isoformat(),
                'message_id': f'analytics_msg_{i+1}'
            }
            
            analysis = {
                'intent': 'question' if i % 2 == 0 else 'request',
                'urgency': 'low',
                'summary': f'Summary {i+1}',
                'context_used': False
            }
            
            self.loader.add_message(message, analysis)
        
        # Get analytics
        analytics = self.loader.get_user_analytics('analytics_user')
        
        self.assertIn('basic_stats', analytics)
        self.assertEqual(analytics['basic_stats']['total_messages'], 3)
        self.assertIn('email', analytics['basic_stats']['platforms'])
    
    def test_similarity_search(self):
        """Test message similarity search."""
        messages = [
            ('user1', 'whatsapp', 'Can you send me photos?', 'msg1'),
            ('user1', 'whatsapp', 'Please share the images', 'msg2'),
            ('user2', 'email', 'Meeting at 3 PM', 'msg3')
        ]
        
        for user_id, platform, text, msg_id in messages:
            message = {
                'user_id': user_id,
                'platform': platform,
                'message_text': text,
                'timestamp': datetime.now().isoformat(),
                'message_id': msg_id
            }
            
            self.loader.add_message(message)
        
        # Search for similar messages
        similar = self.loader.search_similar_messages('send photos', limit=5)
        
        self.assertGreater(len(similar), 0)
        self.assertIn('similarity', similar[0])
        self.assertGreater(similar[0]['similarity'], 0)
    
    def test_data_export_import(self):
        """Test data export and import functionality."""
        # Add test data
        message = {
            'user_id': 'export_user',
            'platform': 'slack',
            'message_text': 'Export test message',
            'timestamp': datetime.now().isoformat(),
            'message_id': 'export_msg_1'
        }
        
        self.loader.add_message(message)
        
        # Export data
        export_file = os.path.join(self.temp_dir, 'export_test.json')
        success = self.loader.export_data(export_file, format='json')
        self.assertTrue(success)
        self.assertTrue(os.path.exists(export_file))
        
        # Create new loader and import data
        new_json_file = os.path.join(self.temp_dir, 'new_context.json')
        new_csv_file = os.path.join(self.temp_dir, 'new_history.csv')
        new_loader = ContextLoader(json_file=new_json_file, csv_file=new_csv_file)
        
        import_success = new_loader.import_data(export_file, format='json')
        self.assertTrue(import_success)
        
        # Verify imported data
        context = new_loader.get_context('export_user', 'slack')
        self.assertGreater(len(context), 0)


class TestFeedbackSystem(unittest.TestCase):
    """Test cases for FeedbackSystem functionality."""
    
    def setUp(self):
        """Set up test environment."""
        self.temp_dir = tempfile.mkdtemp()
        self.feedback_file = os.path.join(self.temp_dir, 'test_feedback.json')
        self.collector = FeedbackCollector(feedback_file=self.feedback_file)
    
    def tearDown(self):
        """Clean up test environment."""
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def test_feedback_collection(self):
        """Test feedback collection and storage."""
        success = self.collector.collect_feedback(
            message_id='test_msg_1',
            user_id='test_user',
            platform='whatsapp',
            original_text='Test message',
            generated_summary='Test summary',
            feedback_score=1,
            feedback_comment='Good summary',
            category_ratings={
                'summary_quality': 1,
                'intent_detection': 1,
                'urgency_level': 0
            }
        )
        
        self.assertTrue(success)
        
        # Check if feedback was stored
        self.assertGreater(len(self.collector.feedback_data['feedback_entries']), 0)
    
    def test_feedback_analytics(self):
        """Test feedback analytics generation."""
        # Add multiple feedback entries
        for i in range(5):
            self.collector.collect_feedback(
                message_id=f'test_msg_{i}',
                user_id='test_user',
                platform='whatsapp',
                original_text=f'Test message {i}',
                generated_summary=f'Test summary {i}',
                feedback_score=1 if i % 2 == 0 else -1,
                category_ratings={'summary_quality': 1 if i % 2 == 0 else -1}
            )
        
        analytics = self.collector.get_feedback_analytics()
        
        self.assertIn('overall_metrics', analytics)
        self.assertEqual(analytics['overall_metrics']['total_feedback'], 5)
        self.assertGreater(analytics['overall_metrics']['positive_feedback'], 0)
    
    def test_platform_feedback_summary(self):
        """Test platform-specific feedback summary."""
        # Add feedback for specific platform
        self.collector.collect_feedback(
            message_id='platform_test_1',
            user_id='test_user',
            platform='email',
            original_text='Email test',
            generated_summary='Email summary',
            feedback_score=1,
            category_ratings={'summary_quality': 1}
        )
        
        summary = self.collector.get_platform_feedback_summary('email')
        
        self.assertIn('total_feedback', summary)
        self.assertEqual(summary['total_feedback'], 1)
        self.assertIn('satisfaction_rate', summary)
    
    def test_feedback_enhanced_summarizer(self):
        """Test feedback-enhanced summarizer integration."""
        context_file = os.path.join(self.temp_dir, 'enhanced_context.json')
        enhanced = FeedbackEnhancedSummarizer(
            context_file=context_file,
            feedback_file=self.feedback_file
        )
        
        message = {
            'user_id': 'enhanced_user',
            'platform': 'whatsapp',
            'message_text': 'Test enhanced summarizer',
            'timestamp': datetime.now().isoformat()
        }
        
        # Summarize message
        result = enhanced.summarize(message)
        self.assertIn('feedback_ready', result)
        self.assertTrue(result['feedback_ready'])
        
        # Collect feedback
        success = enhanced.collect_feedback(
            message_id=result['message_id'],
            user_id='enhanced_user',
            platform='whatsapp',
            original_text=message['message_text'],
            generated_summary=result['summary'],
            feedback_score=1
        )
        
        self.assertTrue(success)


class TestIntegration(unittest.TestCase):
    """Integration tests for the complete system."""
    
    def setUp(self):
        """Set up integration test environment."""
        self.temp_dir = tempfile.mkdtemp()
        self.context_file = os.path.join(self.temp_dir, 'integration_context.json')
        self.feedback_file = os.path.join(self.temp_dir, 'integration_feedback.json')
        
        self.summarizer = SmartSummarizerV3(context_file=self.context_file)
        self.context_loader = ContextLoader(
            json_file=self.context_file,
            csv_file=os.path.join(self.temp_dir, 'integration_history.csv')
        )
        self.feedback_collector = FeedbackCollector(feedback_file=self.feedback_file)
    
    def tearDown(self):
        """Clean up integration test environment."""
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def test_full_workflow(self):
        """Test complete workflow from message to feedback."""
        # Step 1: Process message
        message = {
            'user_id': 'workflow_user',
            'platform': 'email',
            'message_text': 'Please review the quarterly report. Need feedback by Friday for board meeting.',
            'timestamp': datetime.now().isoformat(),
            'message_id': 'workflow_msg_1'
        }
        
        result = self.summarizer.summarize(message, use_context=True)
        
        # Step 2: Store in context
        self.context_loader.add_message(message, result)
        
        # Step 3: Collect feedback
        feedback_success = self.feedback_collector.collect_feedback(
            message_id=message['message_id'],
            user_id=message['user_id'],
            platform=message['platform'],
            original_text=message['message_text'],
            generated_summary=result['summary'],
            feedback_score=1,
            category_ratings={
                'summary_quality': 1,
                'intent_detection': 1,
                'urgency_level': 1
            }
        )
        
        # Verify all steps completed successfully
        self.assertIsInstance(result, dict)
        self.assertIn('summary', result)
        self.assertTrue(feedback_success)
        
        # Verify context storage
        context = self.context_loader.get_context('workflow_user', 'email')
        self.assertGreater(len(context), 0)
        
        # Verify feedback analytics
        analytics = self.feedback_collector.get_feedback_analytics()
        self.assertGreater(analytics['overall_metrics']['total_feedback'], 0)
    
    def test_conversation_flow(self):
        """Test multi-message conversation flow."""
        conversation = [
            {
                'user_id': 'conv_user',
                'platform': 'whatsapp',
                'message_text': 'Can you send me the project files?',
                'timestamp': '2025-08-07T10:00:00Z',
                'message_id': 'conv_msg_1'
            },
            {
                'user_id': 'conv_user',
                'platform': 'whatsapp',
                'message_text': 'I need them for the presentation tomorrow',
                'timestamp': '2025-08-07T10:05:00Z',
                'message_id': 'conv_msg_2'
            },
            {
                'user_id': 'conv_user',
                'platform': 'whatsapp',
                'message_text': 'Any update on those files? Presentation is in 2 hours!',
                'timestamp': '2025-08-07T14:00:00Z',
                'message_id': 'conv_msg_3'
            }
        ]
        
        results = []
        for message in conversation:
            result = self.summarizer.summarize(message, use_context=True)
            self.context_loader.add_message(message, result)
            results.append(result)
        
        # Verify context awareness improved over conversation
        self.assertFalse(results[0]['context_used'])  # First message has no context
        self.assertTrue(results[1]['context_used'])   # Second message uses context
        self.assertTrue(results[2]['context_used'])   # Third message uses context
        
        # Verify urgency escalation
        urgency_levels = [result['urgency'] for result in results]
        # Should show escalation: low/medium -> medium -> high
        self.assertIn('high', urgency_levels[-1:])  # Last message should be high urgency


def run_performance_test():
    """Run performance benchmarks."""
    print("🚀 Running Performance Tests...")
    
    import time
    
    # Create test environment
    temp_dir = tempfile.mkdtemp()
    context_file = os.path.join(temp_dir, 'perf_context.json')
    summarizer = SmartSummarizerV3(context_file=context_file)
    
    # Generate test messages
    test_messages = []
    for i in range(100):
        test_messages.append({
            'user_id': f'perf_user_{i % 10}',
            'platform': ['whatsapp', 'email', 'slack'][i % 3],
            'message_text': f'Performance test message {i+1} with some content to analyze.',
            'timestamp': datetime.now().isoformat(),
            'message_id': f'perf_msg_{i+1}'
        })
    
    # Single message performance
    start_time = time.time()
    result = summarizer.summarize(test_messages[0])
    single_time = time.time() - start_time
    
    # Batch processing performance
    start_time = time.time()
    batch_results = summarizer.batch_summarize(test_messages[:50])
    batch_time = time.time() - start_time
    
    # Context-aware processing performance
    start_time = time.time()
    context_results = summarizer.batch_summarize(test_messages[50:], use_context=True)
    context_time = time.time() - start_time
    
    print(f"📊 Performance Results:")
    print(f"  Single message: {single_time*1000:.2f}ms")
    print(f"  Batch (50 msgs): {batch_time:.2f}s ({batch_time/50*1000:.2f}ms per message)")
    print(f"  Context-aware (50 msgs): {context_time:.2f}s ({context_time/50*1000:.2f}ms per message)")
    
    # Cleanup
    import shutil
    shutil.rmtree(temp_dir, ignore_errors=True)
    
    print("✅ Performance tests completed!")


if __name__ == '__main__':
    print("🧪 SmartBrief v3 Test Suite")
    print("=" * 50)
    
    # Run unit tests
    unittest.main(argv=[''], exit=False, verbosity=2)
    
    # Run performance tests
    print("\n" + "=" * 50)
    run_performance_test()
    print("\n🎉 All tests completed!")
