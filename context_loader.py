"""
Context Loader for SmartBrief v3
Manages conversation history and context for improved summarization.
"""

import json
import os
import pandas as pd
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
import logging

logger = logging.getLogger(__name__)

class ContextLoader:
    """
    Manages conversation context and history for the summarization system.
    
    Features:
    - Load past messages from JSON or CSV storage
    - Context-aware message retrieval
    - User analytics and patterns
    - Message similarity search
    - Data export/import functionality
    """
    
    def __init__(self, json_file: str = 'conversation_history.json', 
                 csv_file: str = 'message_history.csv', 
                 max_context_days: int = 30):
        self.json_file = json_file
        self.csv_file = csv_file
        self.max_context_days = max_context_days
        
        # Load existing data
        self.conversation_data = self._load_json_data()
        self.message_history = self._load_csv_data()
        
        # Context cache for performance
        self.context_cache = {}
        self.cache_expiry = {}
    
    def _load_json_data(self) -> Dict:
        """Load conversation data from JSON file."""
        if os.path.exists(self.json_file):
            try:
                with open(self.json_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except Exception as e:
                logger.error(f"Error loading JSON data: {e}")
        
        return {
            'conversations': {},
            'user_profiles': {},
            'metadata': {
                'created': datetime.now().isoformat(),
                'last_updated': datetime.now().isoformat()
            }
        }
    
    def _save_json_data(self):
        """Save conversation data to JSON file."""
        try:
            self.conversation_data['metadata']['last_updated'] = datetime.now().isoformat()
            with open(self.json_file, 'w', encoding='utf-8') as f:
                json.dump(self.conversation_data, f, indent=2, ensure_ascii=False)
        except Exception as e:
            logger.error(f"Error saving JSON data: {e}")
    
    def _load_csv_data(self) -> pd.DataFrame:
        """Load message history from CSV file."""
        if os.path.exists(self.csv_file):
            try:
                return pd.read_csv(self.csv_file)
            except Exception as e:
                logger.error(f"Error loading CSV data: {e}")
        
        # Create empty DataFrame with required columns
        return pd.DataFrame(columns=[
            'message_id', 'user_id', 'platform', 'message_text', 
            'timestamp', 'intent', 'urgency', 'summary', 'context_used'
        ])
    
    def _save_csv_data(self):
        """Save message history to CSV file."""
        try:
            self.message_history.to_csv(self.csv_file, index=False)
        except Exception as e:
            logger.error(f"Error saving CSV data: {e}")
    
    def load_past_messages(self, user_id: str, platform: str, limit: int = 3) -> List[Dict]:
        """
        Load past 3 messages from the same user for context.
        
        Args:
            user_id: User identifier
            platform: Platform name
            limit: Number of past messages to load
            
        Returns:
            List of past messages
        """
        # Try CSV first for recent messages
        if not self.message_history.empty:
            user_messages = self.message_history[
                (self.message_history['user_id'] == user_id) &
                (self.message_history['platform'] == platform)
            ].sort_values('timestamp', ascending=False).head(limit)
            
            if not user_messages.empty:
                return user_messages.to_dict('records')
        
        # Fallback to JSON conversation data
        conversation_key = f"{user_id}_{platform}"
        conversations = self.conversation_data.get('conversations', {})
        
        if conversation_key in conversations:
            messages = conversations[conversation_key]
            # Return most recent messages
            return messages[-limit:] if messages else []
        
        return []
    
    def add_message(self, message: Dict, analysis: Dict = None):
        """
        Add a message to the context storage.
        
        Args:
            message: Message dictionary with user_id, platform, message_text, etc.
            analysis: Optional analysis results (intent, urgency, summary, etc.)
        """
        try:
            user_id = message.get('user_id', 'unknown')
            platform = message.get('platform', 'unknown')
            message_id = message.get('message_id', f"msg_{datetime.now().timestamp()}")
            
            # Add to JSON conversation data
            conversation_key = f"{user_id}_{platform}"
            
            if 'conversations' not in self.conversation_data:
                self.conversation_data['conversations'] = {}
            
            if conversation_key not in self.conversation_data['conversations']:
                self.conversation_data['conversations'][conversation_key] = []
            
            conversation_entry = {
                'message_id': message_id,
                'message_text': message.get('message_text', ''),
                'timestamp': message.get('timestamp', datetime.now().isoformat()),
                'analysis': analysis or {}
            }
            
            self.conversation_data['conversations'][conversation_key].append(conversation_entry)
            
            # Keep only recent messages (within max_context_days)
            cutoff_date = datetime.now() - timedelta(days=self.max_context_days)
            self.conversation_data['conversations'][conversation_key] = [
                entry for entry in self.conversation_data['conversations'][conversation_key]
                if datetime.fromisoformat(entry['timestamp']) > cutoff_date
            ]
            
            # Add to CSV history
            csv_entry = {
                'message_id': message_id,
                'user_id': user_id,
                'platform': platform,
                'message_text': message.get('message_text', ''),
                'timestamp': message.get('timestamp', datetime.now().isoformat()),
                'intent': analysis.get('intent', '') if analysis else '',
                'urgency': analysis.get('urgency', '') if analysis else '',
                'summary': analysis.get('summary', '') if analysis else '',
                'context_used': analysis.get('context_used', False) if analysis else False
            }
            
            # Convert to DataFrame row and append
            new_row = pd.DataFrame([csv_entry])
            self.message_history = pd.concat([self.message_history, new_row], ignore_index=True)
            
            # Update user profile
            self._update_user_profile(user_id, platform, message, analysis)
            
            # Clear cache for this user-platform combination
            cache_key = f"{user_id}_{platform}"
            if cache_key in self.context_cache:
                del self.context_cache[cache_key]
                del self.cache_expiry[cache_key]
            
            # Save data
            self._save_json_data()
            self._save_csv_data()
            
            logger.info(f"Added message {message_id} for {user_id} on {platform}")
            
        except Exception as e:
            logger.error(f"Error adding message: {e}")
    
    def _update_user_profile(self, user_id: str, platform: str, message: Dict, analysis: Dict = None):
        """Update user profile with message patterns."""
        if 'user_profiles' not in self.conversation_data:
            self.conversation_data['user_profiles'] = {}
        
        if user_id not in self.conversation_data['user_profiles']:
            self.conversation_data['user_profiles'][user_id] = {
                'platforms': {},
                'message_patterns': {
                    'intents': {},
                    'urgency_levels': {},
                    'common_topics': []
                },
                'activity_stats': {
                    'total_messages': 0,
                    'first_seen': datetime.now().isoformat(),
                    'last_seen': datetime.now().isoformat()
                }
            }
        
        profile = self.conversation_data['user_profiles'][user_id]
        
        # Update platform usage
        if platform not in profile['platforms']:
            profile['platforms'][platform] = 0
        profile['platforms'][platform] += 1
        
        # Update activity stats
        profile['activity_stats']['total_messages'] += 1
        profile['activity_stats']['last_seen'] = datetime.now().isoformat()
        
        # Update patterns if analysis is available
        if analysis:
            intent = analysis.get('intent', '')
            urgency = analysis.get('urgency', '')
            
            if intent:
                if intent not in profile['message_patterns']['intents']:
                    profile['message_patterns']['intents'][intent] = 0
                profile['message_patterns']['intents'][intent] += 1
            
            if urgency:
                if urgency not in profile['message_patterns']['urgency_levels']:
                    profile['message_patterns']['urgency_levels'][urgency] = 0
                profile['message_patterns']['urgency_levels'][urgency] += 1
    
    def get_context(self, user_id: str, platform: str, limit: int = 3) -> List[Dict]:
        """
        Get conversation context for a user-platform combination.
        
        Args:
            user_id: User identifier
            platform: Platform name
            limit: Maximum number of context messages to return
            
        Returns:
            List of context messages
        """
        cache_key = f"{user_id}_{platform}"
        
        # Check cache first
        if cache_key in self.context_cache:
            cache_time = self.cache_expiry.get(cache_key, datetime.min)
            if datetime.now() - cache_time < timedelta(minutes=5):  # 5-minute cache
                return self.context_cache[cache_key][:limit]
        
        # Load from storage
        context_messages = self.load_past_messages(user_id, platform, limit)
        
        # Cache the result
        self.context_cache[cache_key] = context_messages
        self.cache_expiry[cache_key] = datetime.now()
        
        return context_messages
    
    def get_user_analytics(self, user_id: str) -> Dict:
        """
        Get analytics for a specific user.
        
        Args:
            user_id: User identifier
            
        Returns:
            User analytics dictionary
        """
        profile = self.conversation_data.get('user_profiles', {}).get(user_id, {})
        
        if not profile:
            return {'error': 'User not found'}
        
        # Get message history for this user
        user_messages = self.message_history[self.message_history['user_id'] == user_id]
        
        analytics = {
            'basic_stats': {
                'total_messages': len(user_messages),
                'platforms': profile.get('platforms', {}),
                'first_seen': profile.get('activity_stats', {}).get('first_seen', ''),
                'last_seen': profile.get('activity_stats', {}).get('last_seen', '')
            },
            'message_patterns': profile.get('message_patterns', {}),
            'recent_activity': self._get_recent_activity(user_id),
            'platform_preferences': self._analyze_platform_preferences(user_messages),
            'communication_style': self._analyze_communication_style(user_messages)
        }
        
        return analytics
    
    def _get_recent_activity(self, user_id: str, days: int = 7) -> Dict:
        """Get recent activity for a user."""
        cutoff_date = datetime.now() - timedelta(days=days)
        user_messages = self.message_history[
            (self.message_history['user_id'] == user_id) &
            (pd.to_datetime(self.message_history['timestamp']) > cutoff_date)
        ]
        
        return {
            'messages_last_7_days': len(user_messages),
            'platforms_used': user_messages['platform'].unique().tolist(),
            'most_common_intent': user_messages['intent'].mode().iloc[0] if not user_messages['intent'].empty else 'unknown',
            'average_urgency': user_messages['urgency'].mode().iloc[0] if not user_messages['urgency'].empty else 'low'
        }
    
    def _analyze_platform_preferences(self, user_messages: pd.DataFrame) -> Dict:
        """Analyze user's platform preferences."""
        if user_messages.empty:
            return {}
        
        platform_counts = user_messages['platform'].value_counts()
        total_messages = len(user_messages)
        
        preferences = {}
        for platform, count in platform_counts.items():
            preferences[platform] = {
                'message_count': int(count),
                'percentage': round((count / total_messages) * 100, 1),
                'most_common_intent': user_messages[user_messages['platform'] == platform]['intent'].mode().iloc[0] if not user_messages[user_messages['platform'] == platform]['intent'].empty else 'unknown'
            }
        
        return preferences
    
    def _analyze_communication_style(self, user_messages: pd.DataFrame) -> Dict:
        """Analyze user's communication style."""
        if user_messages.empty:
            return {}
        
        # Calculate average message length
        message_lengths = user_messages['message_text'].str.len()
        avg_length = message_lengths.mean() if not message_lengths.empty else 0
        
        # Determine communication style
        if avg_length < 50:
            style = 'concise'
        elif avg_length < 150:
            style = 'moderate'
        else:
            style = 'detailed'
        
        # Analyze urgency patterns
        urgency_counts = user_messages['urgency'].value_counts()
        most_common_urgency = urgency_counts.index[0] if not urgency_counts.empty else 'low'
        
        return {
            'average_message_length': round(avg_length, 1),
            'communication_style': style,
            'urgency_tendency': most_common_urgency,
            'context_usage_rate': (user_messages['context_used'].sum() / len(user_messages)) * 100 if len(user_messages) > 0 else 0
        }
    
    def search_similar_messages(self, query_text: str, limit: int = 5) -> List[Dict]:
        """
        Search for messages similar to the query text.
        
        Args:
            query_text: Text to search for
            limit: Maximum number of results
            
        Returns:
            List of similar messages with similarity scores
        """
        if self.message_history.empty:
            return []
        
        query_words = set(query_text.lower().split())
        similar_messages = []
        
        for _, row in self.message_history.iterrows():
            message_text = str(row['message_text']).lower()
            message_words = set(message_text.split())
            
            # Simple Jaccard similarity
            intersection = len(query_words.intersection(message_words))
            union = len(query_words.union(message_words))
            
            if union > 0:
                similarity = intersection / union
                
                if similarity > 0.1:  # Minimum similarity threshold
                    similar_messages.append({
                        'message_id': row['message_id'],
                        'user_id': row['user_id'],
                        'platform': row['platform'],
                        'message_text': row['message_text'],
                        'timestamp': row['timestamp'],
                        'similarity': similarity,
                        'intent': row['intent'],
                        'urgency': row['urgency']
                    })
        
        # Sort by similarity and return top results
        similar_messages.sort(key=lambda x: x['similarity'], reverse=True)
        return similar_messages[:limit]
    
    def export_data(self, output_file: str, format: str = 'json') -> bool:
        """
        Export conversation data to file.
        
        Args:
            output_file: Output file path
            format: Export format ('json' or 'csv')
            
        Returns:
            Success status
        """
        try:
            if format.lower() == 'json':
                export_data = {
                    'conversations': self.conversation_data,
                    'message_history': self.message_history.to_dict('records'),
                    'export_timestamp': datetime.now().isoformat()
                }
                
                with open(output_file, 'w', encoding='utf-8') as f:
                    json.dump(export_data, f, indent=2, ensure_ascii=False)
                    
            elif format.lower() == 'csv':
                self.message_history.to_csv(output_file, index=False)
            else:
                logger.error(f"Unsupported export format: {format}")
                return False
            
            logger.info(f"Data exported to {output_file} in {format} format")
            return True
            
        except Exception as e:
            logger.error(f"Error exporting data: {e}")
            return False
    
    def import_data(self, input_file: str, format: str = 'json') -> bool:
        """
        Import conversation data from file.
        
        Args:
            input_file: Input file path
            format: Import format ('json' or 'csv')
            
        Returns:
            Success status
        """
        try:
            if format.lower() == 'json':
                with open(input_file, 'r', encoding='utf-8') as f:
                    import_data = json.load(f)
                
                # Merge conversation data
                if 'conversations' in import_data:
                    imported_conversations = import_data['conversations'].get('conversations', {})
                    existing_conversations = self.conversation_data.get('conversations', {})
                    
                    for key, messages in imported_conversations.items():
                        if key in existing_conversations:
                            # Merge messages, avoiding duplicates
                            existing_ids = {msg.get('message_id') for msg in existing_conversations[key]}
                            new_messages = [msg for msg in messages if msg.get('message_id') not in existing_ids]
                            existing_conversations[key].extend(new_messages)
                        else:
                            existing_conversations[key] = messages
                    
                    self.conversation_data['conversations'] = existing_conversations
                
                # Merge message history
                if 'message_history' in import_data:
                    imported_df = pd.DataFrame(import_data['message_history'])
                    
                    # Avoid duplicates based on message_id
                    existing_ids = set(self.message_history['message_id'].tolist())
                    new_messages = imported_df[~imported_df['message_id'].isin(existing_ids)]
                    
                    self.message_history = pd.concat([self.message_history, new_messages], ignore_index=True)
                    
            elif format.lower() == 'csv':
                imported_df = pd.read_csv(input_file)
                
                # Avoid duplicates
                existing_ids = set(self.message_history['message_id'].tolist())
                new_messages = imported_df[~imported_df['message_id'].isin(existing_ids)]
                
                self.message_history = pd.concat([self.message_history, new_messages], ignore_index=True)
            else:
                logger.error(f"Unsupported import format: {format}")
                return False
            
            # Save merged data
            self._save_json_data()
            self._save_csv_data()
            
            logger.info(f"Data imported from {input_file}")
            return True
            
        except Exception as e:
            logger.error(f"Error importing data: {e}")
            return False
    
    def cleanup_old_data(self, days: int = None):
        """
        Clean up old conversation data.
        
        Args:
            days: Number of days to keep (default: max_context_days)
        """
        if days is None:
            days = self.max_context_days
        
        cutoff_date = datetime.now() - timedelta(days=days)
        
        # Clean JSON conversations
        conversations = self.conversation_data.get('conversations', {})
        for key, messages in conversations.items():
            self.conversation_data['conversations'][key] = [
                msg for msg in messages
                if datetime.fromisoformat(msg['timestamp']) > cutoff_date
            ]
        
        # Clean CSV history
        self.message_history = self.message_history[
            pd.to_datetime(self.message_history['timestamp']) > cutoff_date
        ]
        
        # Save cleaned data
        self._save_json_data()
        self._save_csv_data()
        
        logger.info(f"Cleaned up data older than {days} days")
    
    def get_statistics(self) -> Dict:
        """Get overall statistics about the context data."""
        total_conversations = len(self.conversation_data.get('conversations', {}))
        total_messages = len(self.message_history)
        unique_users = len(self.conversation_data.get('user_profiles', {}))
        
        platform_stats = self.message_history['platform'].value_counts().to_dict() if not self.message_history.empty else {}
        intent_stats = self.message_history['intent'].value_counts().to_dict() if not self.message_history.empty else {}
        
        return {
            'total_conversations': total_conversations,
            'total_messages': total_messages,
            'unique_users': unique_users,
            'platform_distribution': platform_stats,
            'intent_distribution': intent_stats,
            'data_range': {
                'oldest_message': self.message_history['timestamp'].min() if not self.message_history.empty else None,
                'newest_message': self.message_history['timestamp'].max() if not self.message_history.empty else None
            }
        }


# Example usage and testing
if __name__ == "__main__":
    print("🔄 Testing Context Loader...")
    
    # Initialize context loader
    loader = ContextLoader('test_conversations.json', 'test_history.csv')
    
    # Test adding messages with context scenario
    test_messages = [
        {
            'user_id': 'alice_work',
            'platform': 'email',
            'message_text': 'I will send the quarterly report tonight after the meeting.',
            'timestamp': '2025-08-07T09:00:00Z',
            'message_id': 'test_msg_1'
        },
        {
            'user_id': 'alice_work',
            'platform': 'email',
            'message_text': 'Hey, did the report get done?',
            'timestamp': '2025-08-07T16:45:00Z',
            'message_id': 'test_msg_2'
        }
    ]
    
    test_analyses = [
        {
            'intent': 'informational',
            'urgency': 'low',
            'summary': 'User will send report tonight',
            'context_used': False
        },
        {
            'intent': 'check_progress',
            'urgency': 'medium',
            'summary': 'User is following up on report status',
            'context_used': True
        }
    ]
    
    # Add messages
    for message, analysis in zip(test_messages, test_analyses):
        loader.add_message(message, analysis)
    
    print("✅ Messages added successfully")
    
    # Test context retrieval
    context = loader.get_context('alice_work', 'email')
    print(f"📋 Retrieved {len(context)} context messages")
    
    # Test past messages loading
    past_messages = loader.load_past_messages('alice_work', 'email', 3)
    print(f"📚 Loaded {len(past_messages)} past messages")
    
    # Test user analytics
    analytics = loader.get_user_analytics('alice_work')
    print(f"📊 User analytics: {analytics['basic_stats']['total_messages']} total messages")
    
    # Test statistics
    stats = loader.get_statistics()
    print(f"📈 Overall stats: {stats['total_messages']} messages, {stats['unique_users']} users")
    
    print("✅ Context Loader tests completed!")
