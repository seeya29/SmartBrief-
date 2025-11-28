import re
from datetime import datetime, timedelta
from typing import Dict, List, Tuple
import json
import os

class SmartSuggestionsModule:
    """AI-powered suggestions for email actions."""
    
    def __init__(self, suggestions_log='suggestions_log.json'):
        self.suggestions_log = suggestions_log
        self.usage_stats = self.load_usage_stats()
        
        # Suggestion templates
        self.suggestion_templates = {
            'URGENT': [
                {'action': 'quick_reply', 'text': '⚡ Quick Reply', 'priority': 'high'},
                {'action': 'set_reminder', 'text': '⏰ Set Reminder (1 hour)', 'priority': 'high'},
                {'action': 'escalate', 'text': '📞 Escalate to Manager', 'priority': 'medium'}
            ],
            'MEETING': [
                {'action': 'add_calendar', 'text': '📅 Add to Calendar', 'priority': 'high'},
                {'action': 'accept_invite', 'text': '✅ Accept Meeting', 'priority': 'high'},
                {'action': 'request_reschedule', 'text': '🔄 Request Reschedule', 'priority': 'medium'},
                {'action': 'prepare_agenda', 'text': '📝 Prepare Agenda', 'priority': 'low'}
            ],
            'FINANCIAL': [
                {'action': 'review_invoice', 'text': '💰 Review Invoice', 'priority': 'high'},
                {'action': 'approve_payment', 'text': '✅ Approve Payment', 'priority': 'high'},
                {'action': 'forward_accounting', 'text': '📤 Forward to Accounting', 'priority': 'medium'},
                {'action': 'schedule_payment', 'text': '⏰ Schedule Payment', 'priority': 'medium'}
            ],
            'PROMOTIONAL': [
                {'action': 'archive', 'text': '📁 Archive Email', 'priority': 'high'},
                {'action': 'unsubscribe', 'text': '🚫 Unsubscribe', 'priority': 'high'},
                {'action': 'save_deal', 'text': '💾 Save Deal for Later', 'priority': 'medium'},
                {'action': 'ignore', 'text': '👁️ Mark as Read', 'priority': 'low'}
            ],
            'SECURITY': [
                {'action': 'verify_sender', 'text': '🔍 Verify Sender', 'priority': 'high'},
                {'action': 'change_password', 'text': '🔐 Change Password', 'priority': 'high'},
                {'action': 'report_phishing', 'text': '⚠️ Report as Phishing', 'priority': 'medium'},
                {'action': 'contact_it', 'text': '💻 Contact IT Support', 'priority': 'medium'}
            ],
            'IMPORTANT': [
                {'action': 'detailed_reply', 'text': '✍️ Draft Detailed Reply', 'priority': 'high'},
                {'action': 'schedule_followup', 'text': '⏰ Schedule Follow-up', 'priority': 'high'},
                {'action': 'flag_priority', 'text': '🚩 Flag as Priority', 'priority': 'medium'},
                {'action': 'delegate', 'text': '👥 Delegate Task', 'priority': 'medium'}
            ],
            'NEWSLETTER': [  'text': '👥 Delegate Task', 'priority': 'medium'}
            ],
            'NEWSLETTER': [
                {'action': 'read_later', 'text': '📖 Save for Later', 'priority': 'high'},
                {'action': 'skim_content', 'text': '👀 Quick Skim', 'priority': 'medium'},
                {'action': 'unsubscribe', 'text': '🚫 Unsubscribe', 'priority': 'low'},
                {'action': 'archive', 'text': '📁 Archive', 'priority': 'low'}
            ],
            'GENERAL': [
                {'action': 'quick_reply', 'text': '⚡ Quick Reply', 'priority': 'medium'},
                {'action': 'read_later', 'text': '📖 Read Later', 'priority': 'medium'},
                {'action': 'archive', 'text': '📁 Archive', 'priority': 'low'},
                {'action': 'ignore', 'text': '👁️ Mark as Read', 'priority': 'low'}
            ]
        }
        
        # Action implementations
        self.action_handlers = {
            'quick_reply': self._generate_quick_reply,
            'detailed_reply': self._generate_detailed_reply,
            'add_calendar': self._create_calendar_entry,
            'set_reminder': self._create_reminder,
            'archive': self._archive_email,
            'unsubscribe': self._handle_unsubscribe,
            'forward_accounting': self._forward_email,
            'schedule_payment': self._schedule_payment,
            'verify_sender': self._verify_sender_authenticity,
            'change_password': self._initiate_password_change,
            'contact_it': self._contact_it_support,
            'flag_priority': self._flag_as_priority,
            'delegate': self._delegate_task,
            'read_later': self._save_for_later,
            'ignore': self._mark_as_read
        }
    
    def load_usage_stats(self) -> Dict:
        """Load suggestion usage statistics."""
        if os.path.exists(self.suggestions_log):
            try:
                with open(self.suggestions_log, 'r') as f:
                    return json.load(f)
            except Exception as e:
                print(f"Error loading usage stats: {e}")
        
        return {
            'action_counts': {},
            'success_rates': {},
            'user_preferences': {},
            'category_effectiveness': {}
        }
    
    def save_usage_stats(self):
        """Save usage statistics."""
        try:
            with open(self.suggestions_log, 'w') as f:
                json.dump(self.usage_stats, f, indent=2)
        except Exception as e:
            print(f"Error saving usage stats: {e}")
    
    def generate_suggestions(self, email: Dict, tag: str, confidence: float) -> List[Dict]:
        """Generate smart suggestions based on email content and tag."""
        base_suggestions = self.suggestion_templates.get(tag, self.suggestion_templates['GENERAL'])
        
        # Analyze email content for context-specific suggestions
        subject = email.get('subject', '').lower()
        body = email.get('body', '').lower()
        sender = email.get('sender', '').lower()
        
        enhanced_suggestions = []
        
        for suggestion in base_suggestions:
            # Create enhanced suggestion with context
            enhanced_suggestion = suggestion.copy()
            enhanced_suggestion.update({
                'confidence': self._calculate_suggestion_confidence(suggestion, email, tag),
                'context': self._generate_context_info(suggestion, email),
                'estimated_time': self._estimate_action_time(suggestion['action']),
                'success_rate': self._get_historical_success_rate(suggestion['action'])
            })
            
            enhanced_suggestions.append(enhanced_suggestion)
        
        # Add dynamic suggestions based on content analysis
        dynamic_suggestions = self._generate_dynamic_suggestions(email, tag)
        enhanced_suggestions.extend(dynamic_suggestions)
        
        # Sort by priority and confidence
        enhanced_suggestions.sort(key=lambda x: (
            -self._priority_score(x['priority']),  # Higher priority first
            -x['confidence'],  # Higher confidence first
            -x.get('success_rate', 0.5)  # Higher success rate first
        ))
        
        # Apply user preference learning
        personalized_suggestions = self._apply_personalization(enhanced_suggestions, sender, tag)
        
        return personalized_suggestions[:5]  # Return top 5 suggestions
    
    def _calculate_suggestion_confidence(self, suggestion: Dict, email: Dict, tag: str) -> float:
        """Calculate confidence score for a suggestion."""
        base_confidence = 0.7
        
        action = suggestion['action']
        body = email.get('body', '').lower()
        subject = email.get('subject', '').lower()
        
        # Action-specific confidence adjustments
        if action == 'add_calendar' and any(word in body + subject for word in ['meeting', 'appointment', 'schedule']):
            base_confidence += 0.2
        
        if action == 'quick_reply' and any(word in body + subject for word in ['question', 'confirm', 'yes/no']):
            base_confidence += 0.15
        
        if action == 'unsubscribe' and 'unsubscribe' in body:
            base_confidence += 0.25
        
        if action == 'archive' and tag in ['PROMOTIONAL', 'NEWSLETTER']:
            base_confidence += 0.1
        
        return min(0.95, base_confidence)
    
    def _generate_context_info(self, suggestion: Dict, email: Dict) -> str:
        """Generate contextual information for the suggestion."""
        action = suggestion['action']
        subject = email.get('subject', '')
        
        context_map = {
            'quick_reply': f"Reply to: {subject[:50]}...",
            'add_calendar': f"Event: {subject}",
            'set_reminder': f"Reminder for: {subject[:30]}...",
            'archive': f"Archive: {subject[:40]}...",
            'unsubscribe': f"From: {email.get('sender', 'Unknown')}",
            'forward_accounting': f"Forward invoice: {subject}",
            'verify_sender': f"Verify: {email.get('sender', 'Unknown')}",
            'delegate': f"Delegate: {subject[:40]}..."
        }
        
        return context_map.get(action, f"Action for: {subject[:30]}...")
    
    def _estimate_action_time(self, action: str) -> str:
        """Estimate time required for action."""
        time_estimates = {
            'quick_reply': '2-5 min',
            'detailed_reply': '10-20 min',
            'add_calendar': '1-2 min',
            'set_reminder': '30 sec',
            'archive': '5 sec',
            'unsubscribe': '30 sec',
            'verify_sender': '2-3 min',
            'change_password': '5-10 min',
            'contact_it': '5-15 min',
            'delegate': '3-5 min',
            'read_later': '5 sec'
        }
        
        return time_estimates.get(action, '2-5 min')
    
    def _get_historical_success_rate(self, action: str) -> float:
        """Get historical success rate for an action."""
        success_rates = self.usage_stats.get('success_rates', {})
        return success_rates.get(action, 0.75)  # Default 75% success rate
    
    def _generate_dynamic_suggestions(self, email: Dict, tag: str) -> List[Dict]:
        """Generate dynamic suggestions based on email content analysis."""
        dynamic_suggestions = []
        body = email.get('body', '').lower()
        subject = email.get('subject', '').lower()
        
        # Meeting time extraction
        time_patterns = [
            r'(\d{1,2}:\d{2}\s?(?:am|pm)?)',
            r'(\d{1,2}\s?(?:am|pm))',
            r'(tomorrow|today|next week|this week)'
        ]
        
        for pattern in time_patterns:
            if re.search(pattern, body + subject, re.IGNORECASE):
                dynamic_suggestions.append({
                    'action': 'extract_meeting_time',
                    'text': '🕐 Extract Meeting Time',
                    'priority': 'high',
                    'confidence': 0.8,
                    'context': 'Time mentioned in email',
                    'estimated_time': '1 min',
                    'success_rate': 0.85
                })
                break
        
        # Contact information extraction
        if re.search(r'(\d{3}[-.]?\d{3}[-.]?\d{4})', body):
            dynamic_suggestions.append({
                'action': 'save_contact',
                'text': '📱 Save Contact Info',
                'priority': 'medium',
                'confidence': 0.75,
                'context': 'Phone number detected',
                'estimated_time': '2 min',
                'success_rate': 0.7
            })
        
        # Document attachment handling
        if any(word in body + subject for word in ['attached', 'attachment', 'document', 'pdf', 'file']):
            dynamic_suggestions.append({
                'action': 'download_attachments',
                'text': '📎 Download Attachments',
                'priority': 'medium',
                'confidence': 0.85,
                'context': 'Attachments mentioned',
                'estimated_time': '1-3 min',
                'success_rate': 0.9
            })
        
        return dynamic_suggestions
    
    def _apply_personalization(self, suggestions: List[Dict], sender: str, tag: str) -> List[Dict]:
        """Apply advanced user preference learning to suggestions."""
        user_prefs = self.usage_stats.get('user_preferences', {})
        sender_prefs = self.usage_stats.get('sender_preferences', {}).get(sender, {})
        tag_prefs = self.usage_stats.get('tag_preferences', {}).get(tag, {})
        
        for suggestion in suggestions:
            action = suggestion['action']
            confidence_boost = 0
            context_info = []
            personalization_sources = []
            
            # Boost based on general user preferences
            if action in user_prefs:
                usage_count = user_prefs[action]
                general_boost = min(0.15, usage_count * 0.015)  # Up to 15% boost
                confidence_boost += general_boost
                if general_boost > 0.05:
                    context_info.append(f"You use this action frequently")
                    personalization_sources.append("your frequently used actions")
            
            # Boost based on sender-specific preferences
            if action in sender_prefs:
                sender_boost = min(0.25, sender_prefs[action] * 0.05)  # Up to 25% boost
                confidence_boost += sender_boost
                if sender_boost > 0.05:
                    context_info.append(f"You prefer this for emails from {sender}")
                    personalization_sources.append(f"your history with {sender}")
            
            # Boost based on tag-specific preferences
            if action in tag_prefs:
                tag_boost = min(0.2, tag_prefs[action] * 0.04)  # Up to 20% boost
                confidence_boost += tag_boost
                if tag_boost > 0.05:
                    context_info.append(f"You often use this for {tag} emails")
                    personalization_sources.append(f"your preferences for {tag} emails")
            
            # Apply the combined boost
            suggestion['confidence'] = min(0.95, suggestion['confidence'] + confidence_boost)
            
            # Add personalization context if significant
            if context_info and confidence_boost > 0.1:
                suggestion['personalized'] = True
                if 'context' not in suggestion:
                    suggestion['context'] = ""
                suggestion['context'] += f" ({' & '.join(context_info)})"
                
                # Add personalization source information
                if personalization_sources:
                    suggestion['personalization_source'] = ", ".join(personalization_sources)
        
        return suggestions
    
    def _priority_score(self, priority: str) -> int:
        """Convert priority string to numeric score."""
        return {'high': 3, 'medium': 2, 'low': 1}.get(priority, 1)
    
    def execute_suggestion(self, email: Dict, action: str) -> Dict:
        """Execute a suggestion action and record detailed usage statistics."""
        if action in self.action_handlers:
            try:
                result = self.action_handlers[action](email)
                
                # Record usage statistics with email data
                self._record_usage(action, success=True, email=email)
                
                return {
                    'success': True,
                    'action': action,
                    'result': result,
                    'message': f"✅ Successfully executed: {action}",
                    'timestamp': datetime.now().isoformat()
                }
            except Exception as e:
                # Record failed usage with email data
                self._record_usage(action, success=False, email=email)
                return {
                    'success': False,
                    'action': action,
                    'error': str(e),
                    'message': f"❌ Failed to execute: {action}",
                    'timestamp': datetime.now().isoformat()
                }
        else:
            return {
                'success': False,
                'action': action,
                'message': f"❌ Unknown action: {action}",
                'timestamp': datetime.now().isoformat()
            }
    
    def _record_usage(self, action: str, success: bool, email: Dict = None):
        """Record action usage for learning with sender and tag preferences."""
        # Update action counts
        action_counts = self.usage_stats.get('action_counts', {})
        action_counts[action] = action_counts.get(action, 0) + 1
        self.usage_stats['action_counts'] = action_counts
        
        # Update success rates
        success_rates = self.usage_stats.get('success_rates', {})
        current_rate = success_rates.get(action, 0.75)
        
        # Weighted average update
        total_uses = action_counts[action]
        new_rate = ((current_rate * (total_uses - 1)) + (1.0 if success else 0.0)) / total_uses
        success_rates[action] = new_rate
        self.usage_stats['success_rates'] = success_rates
        
        # Update user preferences (boost frequently used actions)
        user_prefs = self.usage_stats.get('user_preferences', {})
        if success:
            user_prefs[action] = user_prefs.get(action, 0) + 1
        self.usage_stats['user_preferences'] = user_prefs
        
        # Track sender preferences if email is provided
        if email and 'sender' in email:
            sender = email.get('sender', '')
            sender_prefs = self.usage_stats.get('sender_preferences', {})
            if sender not in sender_prefs:
                sender_prefs[sender] = {}
            if action not in sender_prefs[sender]:
                sender_prefs[sender][action] = 0
            sender_prefs[sender][action] += 1
            self.usage_stats['sender_preferences'] = sender_prefs
        
        # Track tag preferences if email is provided
        if email and 'tag' in email:
            tag = email.get('tag', 'GENERAL')
            tag_prefs = self.usage_stats.get('tag_preferences', {})
            if tag not in tag_prefs:
                tag_prefs[tag] = {}
            if action not in tag_prefs[tag]:
                tag_prefs[tag][action] = 0
            tag_prefs[tag][action] += 1
            self.usage_stats['tag_preferences'] = tag_prefs
        
        self.save_usage_stats()
    
    # Action handler implementations
    def _generate_quick_reply(self, email: Dict) -> str:
        """Generate a quick reply template."""
        subject = email.get('subject', '')
        body = email.get('body', '').lower()
        
        # Simple reply logic based on content
        if any(word in body for word in ['thank', 'thanks']):
            return "You're welcome! Let me know if you need anything else."
        elif any(word in body for word in ['question', '?']):
            return "Thanks for your question. I'll get back to you shortly with more details."
        elif any(word in body for word in ['meeting', 'schedule']):
            return "Thanks for the meeting invite. I'll check my calendar and confirm shortly."
        elif any(word in body for word in ['confirm', 'confirmation']):
            return "Confirmed. Thank you for the update."
        else:
            return "Thank you for your email. I'll review this and get back to you soon."
    
    def _generate_detailed_reply(self, email: Dict) -> str:
        """Generate a detailed reply template."""
        return f"Reply template for: {email.get('subject', 'Email')}\n\n[Your detailed response here]"
    
    def _create_calendar_entry(self, email: Dict) -> str:
        """Create calendar entry from email."""
        subject = email.get('subject', 'Meeting from Email')
        return f"Calendar entry created: {subject}"
    
    def _create_reminder(self, email: Dict) -> str:
        """Create a reminder."""
        return f"Reminder set for: {email.get('subject', 'Email Task')}"
    
    def _archive_email(self, email: Dict) -> str:
        """Archive the email."""
        return f"Email archived: {email.get('id', 'Unknown')}"
    
    def _handle_unsubscribe(self, email: Dict) -> str:
        """Handle unsubscribe action."""
        sender = email.get('sender', 'Unknown')
        return f"Unsubscribe initiated for: {sender}"
    
    def _forward_email(self, email: Dict) -> str:
        """Forward email to appropriate department."""
        return f"Email forwarded: {email.get('subject', 'Email')}"
    
    def _schedule_payment(self, email: Dict) -> str:
        """Schedule payment for invoice."""
        return f"Payment scheduled for invoice in: {email.get('subject', 'Email')}"
    
    def _verify_sender_authenticity(self, email: Dict) -> str:
        """Verify sender authenticity."""
        sender = email.get('sender', 'Unknown')
        return f"Sender verification initiated for: {sender}"
    
    def _initiate_password_change(self, email: Dict) -> str:
        """Initiate password change process."""
        return "Password change process initiated. Check your secure channels."
    
    def _contact_it_support(self, email: Dict) -> str:
        """Contact IT support."""
        return "IT support contacted regarding security concern."
    
    def _flag_as_priority(self, email: Dict) -> str:
        """Flag email as priority."""
        return f"Email flagged as priority: {email.get('id', 'Unknown')}"
    
    def _delegate_task(self, email: Dict) -> str:
        """Delegate task from email."""
        return f"Task delegation initiated for: {email.get('subject', 'Email')}"
    
    def _save_for_later(self, email: Dict) -> str:
        """Save email for later reading."""
        return f"Email saved for later: {email.get('subject', 'Email')}"
    
    def _mark_as_read(self, email: Dict) -> str:
        """Mark email as read."""
        return f"Email marked as read: {email.get('id', 'Unknown')}"
    
    def get_suggestion_stats(self) -> Dict:
        """Get suggestion usage statistics."""
        stats = self.usage_stats.copy()
        stats['total_suggestions_used'] = sum(self.usage_stats.get('action_counts', {}).values())
        stats['most_used_action'] = max(
            self.usage_stats.get('action_counts', {}).items(),
            key=lambda x: x[1],
            default=('none', 0)
        )[0]
        return stats
