import streamlit as st
import pandas as pd
import json
import os
from datetime import datetime, timedelta
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import re

# Import your modules with proper error handling
try:
    from email_reader import EmailReader
    from priority_model import Prioritizer
    from smart_metrics import extract_email_metrics
    from sentiment import analyze_sentiment
    from tts import read_text, stop_speech
    from briefing import generate_daily_brief
    from credentials_manager import get_email_credentials, manage_credentials
    from email_summarizer import format_email_display, generate_email_summary
    
    # Create a wrapper function for load_emails to maintain compatibility
    def load_emails():
        """Load emails using the EmailReader class."""
        email_reader = EmailReader(use_mock=True)
        return email_reader.load_emails()
        
except ImportError as e:
    st.error(f"Missing required modules: {e}")
    st.stop()

# Set page config
st.set_page_config(
    page_title="Smart Inbox Assistant", 
    page_icon="📬", 
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for better UI
st.markdown("""
<style>
.email-card {
    border: 1px solid #ddd;
    border-radius: 10px;
    padding: 15px;
    margin: 10px 0;
    background-color: #f9f9f9;
    color: #333333;
}
.urgent { border-left: 5px solid #ff4444; }
.meeting { border-left: 5px solid #4444ff; }
.financial { border-left: 5px solid #44ff44; }
.important { border-left: 5px solid #ffaa44; }
.promotional { border-left: 5px solid #ff44ff; }
.newsletter { border-left: 5px solid #44ffff; }
.security { border-left: 5px solid #ff8844; }
.general { border-left: 5px solid #888888; }

.confidence-high { background-color: #e6ffe6; }
.confidence-medium { background-color: #fff3e6; }
.confidence-low { background-color: #ffe6e6; }

/* Fix for white text on white background */
.stMarkdown, .stText, .stDataFrame {
    color: #333333 !important;
}

/* Ensure all text in white containers is visible */
.css-1kyxreq, .css-12oz5g7 {
    color: #333333 !important;
}
</style>
""", unsafe_allow_html=True)

# Initialize session state
if 'emails_processed' not in st.session_state:
    st.session_state.emails_processed = False
if 'processed_emails' not in st.session_state:
    st.session_state.processed_emails = []
if 'current_page' not in st.session_state:
    st.session_state.current_page = 0
if 'filter_tag' not in st.session_state:
    st.session_state.filter_tag = 'ALL'
if 'sort_by' not in st.session_state:
    st.session_state.sort_by = 'Priority Score'
if 'email_credentials' not in st.session_state:
    st.session_state.email_credentials = None

# Simple Priority Tagger class (inline implementation)
class SimplePriorityTagger:
    def __init__(self):
        self.feedback_file = 'tagging_feedback.json'
        self.load_feedback()
    
    def load_feedback(self):
        """Load feedback data from file."""
        if os.path.exists(self.feedback_file):
            try:
                with open(self.feedback_file, 'r') as f:
                    self.feedback_data = json.load(f)
            except:
                self.feedback_data = {
                    'tag_corrections': {},
                    'sender_preferences': {},
                    'confidence_scores': {}
                }
        else:
            self.feedback_data = {
                'tag_corrections': {},
                'sender_preferences': {},
                'confidence_scores': {}
            }
    
    def save_feedback(self):
        """Save feedback data to file."""
        try:
            with open(self.feedback_file, 'w') as f:
                json.dump(self.feedback_data, f, indent=2)
        except Exception as e:
            st.error(f"Error saving feedback: {e}")
    
    def tag_email(self, email):
        """Tag an email with priority category."""
        subject = email.get('subject', '').lower()
        body = email.get('body', '').lower()
        sender = email.get('sender', '').lower()
        
        full_text = f"{subject} {body}"
        
        # Initialize scores
        scores = {
            'URGENT': 0.0,
            'MEETING': 0.0,
            'FINANCIAL': 0.0,
            'IMPORTANT': 0.0,
            'PROMOTIONAL': 0.0,
            'NEWSLETTER': 0.0,
            'SECURITY': 0.0,
            'GENERAL': 0.1
        }
        
        reasoning = []
        
        # Urgent keywords
        urgent_keywords = ['urgent', 'asap', 'immediately', 'emergency', 'critical', 'deadline']
        urgent_score = sum(1 for keyword in urgent_keywords if keyword in full_text)
        if urgent_score > 0:
            scores['URGENT'] += urgent_score * 0.3
            reasoning.append(f"Urgent keywords found ({urgent_score})")
        
        # Meeting keywords
        meeting_keywords = ['meeting', 'schedule', 'appointment', 'conference', 'call', 'zoom']
        meeting_score = sum(1 for keyword in meeting_keywords if keyword in full_text)
        if meeting_score > 0:
            scores['MEETING'] += meeting_score * 0.2
            reasoning.append(f"Meeting keywords found ({meeting_score})")
        
        # Financial keywords
        financial_keywords = ['invoice', 'payment', 'bill', 'transaction', 'account', 'financial']
        financial_score = sum(1 for keyword in financial_keywords if keyword in full_text)
        if financial_score > 0:
            scores['FINANCIAL'] += financial_score * 0.25
            reasoning.append(f"Financial keywords found ({financial_score})")
        
        # Security keywords
        security_keywords = ['security', 'password', 'alert', 'suspicious', 'breach', 'verify']
        security_score = sum(1 for keyword in security_keywords if keyword in full_text)
        if security_score > 0:
            scores['SECURITY'] += security_score * 0.3
            reasoning.append(f"Security keywords found ({security_score})")
        
        # Promotional keywords
        promo_keywords = ['offer', 'sale', 'discount', 'deal', 'promotion', 'limited time']
        promo_score = sum(1 for keyword in promo_keywords if keyword in full_text)
        if promo_score > 0:
            scores['PROMOTIONAL'] += promo_score * 0.15
            reasoning.append(f"Promotional keywords found ({promo_score})")
        
        # Newsletter indicators
        newsletter_keywords = ['newsletter', 'weekly', 'monthly', 'updates', 'news']
        newsletter_score = sum(1 for keyword in newsletter_keywords if keyword in full_text)
        if newsletter_score > 0 or 'unsubscribe' in full_text:
            scores['NEWSLETTER'] += 0.2
            reasoning.append("Newsletter indicators found")
        
        # Sender-based scoring
        if sender:
            if any(term in sender for term in ['ceo', 'manager', 'director', 'admin']):
                scores['IMPORTANT'] += 0.3
                reasoning.append("Important sender detected")
            elif any(term in sender for term in ['noreply', 'no-reply', 'automated']):
                scores['NEWSLETTER'] += 0.2
                reasoning.append("Automated sender detected")
        
        # Apply learned preferences
        sender_prefs = self.feedback_data.get('sender_preferences', {})
        if sender in sender_prefs:
            preferred_tag = sender_prefs[sender]
            scores[preferred_tag] += 0.4
            reasoning.append(f"Learned preference for sender: {preferred_tag}")
        
        # Find the tag with highest score
        best_tag = max(scores.keys(), key=lambda k: scores[k])
        confidence = min(scores[best_tag], 1.0)
        
        # Features for display
        features_detected = {
            'word_count': len(full_text.split()),
            'has_attachments': bool(email.get('attachments')),
            'time_urgency': urgent_score
        }
        
        return {
            'tag': best_tag,
            'confidence': confidence,
            'reasoning': reasoning,
            'all_scores': scores,
            'features_detected': features_detected
        }
    
    def process_feedback(self, email_id, correct_tag, predicted_tag, sender, feedback_quality=1.0):
        """Process user feedback for learning."""
        # Store correction with consistent format
        self.feedback_data['tag_corrections'][email_id] = {
            'correct': correct_tag,
            'predicted': predicted_tag,
            'sender': sender,
            'timestamp': datetime.now().isoformat(),
            'quality': feedback_quality
        }
        
        # Update sender preferences
        if sender and correct_tag != predicted_tag:
            self.feedback_data['sender_preferences'][sender] = correct_tag
        
        self.save_feedback()

# Simple Smart Suggestions Module
class SimpleSmartSuggestionsModule:
    def __init__(self):
        self.usage_stats = {'user_preferences': {}, 'tag_preferences': {}}
    
    def generate_suggestions(self, email, tag, confidence):
        """Generate smart suggestions for an email."""
        suggestions = []
        
        if tag == 'URGENT':
            suggestions.extend([
                {'text': 'Reply immediately', 'action': 'reply_urgent', 'estimated_time': '5 min', 'confidence': 0.9},
                {'text': 'Add to high priority list', 'action': 'high_priority', 'estimated_time': '1 min', 'confidence': 0.8},
                {'text': 'Set reminder in 1 hour', 'action': 'reminder_1h', 'estimated_time': '1 min', 'confidence': 0.7}
            ])
        elif tag == 'MEETING':
            suggestions.extend([
                {'text': 'Add to calendar', 'action': 'add_calendar', 'estimated_time': '2 min', 'confidence': 0.9},
                {'text': 'Accept meeting invite', 'action': 'accept_meeting', 'estimated_time': '1 min', 'confidence': 0.8},
                {'text': 'Request agenda', 'action': 'request_agenda', 'estimated_time': '3 min', 'confidence': 0.6}
            ])
        elif tag == 'FINANCIAL':
            suggestions.extend([
                {'text': 'Review and approve', 'action': 'review_financial', 'estimated_time': '10 min', 'confidence': 0.8},
                {'text': 'Forward to accounting', 'action': 'forward_accounting', 'estimated_time': '2 min', 'confidence': 0.9},
                {'text': 'Add to expenses tracker', 'action': 'track_expense', 'estimated_time': '3 min', 'confidence': 0.7}
            ])
        elif tag == 'PROMOTIONAL':
            suggestions.extend([
                {'text': 'Archive (promotional)', 'action': 'archive_promo', 'estimated_time': '1 min', 'confidence': 0.9},
                {'text': 'Unsubscribe', 'action': 'unsubscribe', 'estimated_time': '2 min', 'confidence': 0.7},
                {'text': 'Save offer for later', 'action': 'save_offer', 'estimated_time': '1 min', 'confidence': 0.5}
            ])
        else:
            suggestions.extend([
                {'text': 'Quick reply', 'action': 'quick_reply', 'estimated_time': '3 min', 'confidence': 0.6},
                {'text': 'Archive', 'action': 'archive', 'estimated_time': '1 min', 'confidence': 0.8},
                {'text': 'Set reminder for tomorrow', 'action': 'reminder_tomorrow', 'estimated_time': '1 min', 'confidence': 0.7}
            ])
        
        return suggestions[:3]  # Return top 3 suggestions
    
    def execute_suggestion(self, email, action):
        """Execute a suggestion action."""
        # Update usage stats
        self.usage_stats['user_preferences'][action] = self.usage_stats['user_preferences'].get(action, 0) + 1
        
        # Simulate action execution
        action_responses = {
            'reply_urgent': {'success': True, 'message': 'Urgent reply template prepared'},
            'high_priority': {'success': True, 'message': 'Added to high priority list'},
            'add_calendar': {'success': True, 'message': 'Calendar event created'},
            'archive_promo': {'success': True, 'message': 'Email archived to promotional folder'},
            'quick_reply': {'success': True, 'message': 'Quick reply template ready'},
            'archive': {'success': True, 'message': 'Email archived'},
        }
        
        return action_responses.get(action, {'success': False, 'message': 'Action not implemented'})

# Initialize components
@st.cache_data
def initialize_components():
    """Initialize all AI components."""
    try:
        from priority_model import Prioritizer
        prioritizer = Prioritizer()
    except ImportError:
        # Create a simple fallback prioritizer
        class SimplePrioritizer:
            def prioritize_emails(self, emails):
                # Simple scoring based on tag and confidence
                scored_emails = []
                for email in emails:
                    score = 0.5  # Base score
                    tag = email.get('tag', 'GENERAL')
                    confidence = email.get('tag_confidence', 0.5)
                    
                    # Tag-based scoring
                    tag_scores = {
                        'URGENT': 1.0,
                        'SECURITY': 0.9,
                        'MEETING': 0.8,
                        'FINANCIAL': 0.7,
                        'IMPORTANT': 0.6,
                        'GENERAL': 0.4,
                        'PROMOTIONAL': 0.2,
                        'NEWSLETTER': 0.1
                    }
                    
                    score = tag_scores.get(tag, 0.5) * confidence
                    scored_emails.append((score, email))
                
                # Sort by score descending
                scored_emails.sort(key=lambda x: x[0], reverse=True)
                return scored_emails
        
        prioritizer = SimplePrioritizer()
    
    return {
        'prioritizer': prioritizer,
        'tagger': SimplePriorityTagger(),
        'suggestions': SimpleSmartSuggestionsModule()
    }

components = initialize_components()

# Function to clean text for display and TTS
def clean_text_for_summary(text):
    """Clean HTML and simplify links in text."""
    if not text:
        return ""
    # Replace HTML tags with spaces
    text = re.sub(r'<[^>]+>', ' ', text)
    # Replace links with a placeholder
    text = re.sub(r'https?://\S+', '[Link]', text)
    # Replace multiple spaces with a single space
    text = re.sub(r'\s+', ' ', text)
    return text.strip()

# Sidebar Configuration
st.sidebar.title("🤖 Smart Inbox Settings")

# Email credentials management
st.sidebar.subheader("📧 Email Configuration")

# Check if we have credentials in secrets
has_secrets = False
try:
    if hasattr(st, 'secrets') and 'email' in st.secrets and 'app_password' in st.secrets:
        has_secrets = True
        st.sidebar.success("✅ Email credentials found in secrets")
except:
    pass

if not has_secrets:
    with st.sidebar.expander("🔐 Email Credentials", expanded=True):
        email_address = st.text_input("Email Address", key="email_input")
        app_password = st.text_input("App Password", type="password", key="password_input")
        provider = st.selectbox("Provider", ["gmail", "outlook", "yahoo"], key="provider_input")
        
        if st.button("💾 Save Credentials", key="save_creds"):
            if email_address and app_password:
                st.session_state.email_credentials = {
                    'email_address': email_address,
                    'password': app_password,
                    'provider': provider
                }
                st.success("✅ Credentials saved for this session!")
            else:
                st.error("❌ Please fill in all fields")

# Email source selection
email_source = st.sidebar.radio(
    "Email Source",
    ["Live Email", "Mock Emails"],
    help="Select your email source"
)

# Filters and sorting
st.sidebar.subheader("📊 Display Options")
st.session_state.filter_tag = st.sidebar.selectbox(
    "Filter by Tag",
    ['ALL', 'URGENT', 'MEETING', 'FINANCIAL', 'IMPORTANT', 'PROMOTIONAL', 'NEWSLETTER', 'SECURITY', 'GENERAL']
)

st.session_state.sort_by = st.sidebar.selectbox(
    "Sort by",
    ['Priority Score', 'Confidence', 'Date', 'Sender']
)

# Processing options
st.sidebar.subheader("🎛️ Processing Options")
show_reasoning = st.sidebar.checkbox("Show Tag Reasoning", value=True)
show_suggestions = st.sidebar.checkbox("Show Smart Suggestions", value=True)
auto_play_tts = st.sidebar.checkbox("Auto-play TTS for high priority", value=False)

# Main title
st.title("📬 Smart Inbox Assistant")
st.markdown("*AI-Powered Email Processing with Priority Tagging & Smart Suggestions*")

# Email loading section
col1, col2, col3 = st.columns([2, 1, 1])

with col1:
    if st.button("🔄 Load & Process Emails"):
        with st.spinner("Loading and processing emails..."):
            try:
                # Load emails based on source
                if email_source == "Live Email":
                    # Get credentials
                    credentials = None
                    if has_secrets:
                        credentials = {
                            'email_address': st.secrets['email'],
                            'password': st.secrets['app_password']
                        }
                    elif st.session_state.email_credentials:
                        credentials = st.session_state.email_credentials
                    
                    if credentials:
                        st.info(f"📡 Connecting to {credentials['email_address']}...")
                        email_reader = EmailReader(use_mock=False)
                        
                        if email_reader.connect_imap(credentials['email_address'], credentials['password']):
                            emails = email_reader.fetch_live_emails(limit=20)
                            email_reader.close_connection()
                            
                            if emails:
                                emails_df = pd.DataFrame(emails)
                                st.success(f"✅ Loaded {len(emails_df)} emails from {credentials['email_address']}")
                            else:
                                st.warning("⚠️ No emails found. Using mock emails.")
                                emails_df = pd.DataFrame(EmailReader(use_mock=True).create_enhanced_mock_emails())
                        else:
                            st.error("❌ Failed to connect to email server. Using mock emails.")
                            emails_df = pd.DataFrame(EmailReader(use_mock=True).create_enhanced_mock_emails())
                    else:
                        st.warning("⚠️ No email credentials provided. Using mock emails.")
                        emails_df = pd.DataFrame(EmailReader(use_mock=True).create_enhanced_mock_emails())
                else:
                    # Load mock emails
                    emails_df = pd.DataFrame(EmailReader(use_mock=True).create_enhanced_mock_emails())
                    st.success(f"✅ Loaded {len(emails_df)} mock emails")
                
                # Process each email
                processed_emails = []
                
                progress_bar = st.progress(0)
                for idx, (_, email_row) in enumerate(emails_df.iterrows()):
                    email_dict = email_row.to_dict()
                    
                    # Extract metrics (with fallback)
                    body = email_dict.get('body', '')
                    subject = email_dict.get('subject', 'No Subject')
                    full_text = f"{subject} {body}"
                    
                    # AI Analysis with error handling
                    try:
                        metrics = extract_email_metrics(full_text)
                    except:
                        metrics = {'intent': 'general', 'urgency': 'low', 'has_deadline': False}
                    
                    try:
                        sentiment_score = analyze_sentiment(body)
                    except:
                        sentiment_score = 0.0
                    
                    # Priority tagging
                    tag_result = components['tagger'].tag_email(email_dict)
                    
                    # Create enriched email
                    enriched_email = {
                        **email_dict,
                        'sentiment_score': sentiment_score,
                        'metrics': metrics,
                        'tag': tag_result['tag'],
                        'tag_confidence': tag_result['confidence'],
                        'tag_reasoning': tag_result['reasoning'],
                        'all_scores': tag_result['all_scores'],
                        'features_detected': tag_result['features_detected']
                    }
                    
                    processed_emails.append(enriched_email)
                    progress_bar.progress((idx + 1) / len(emails_df))
                
                # Prioritize emails
                prioritized_emails = components['prioritizer'].prioritize_emails(processed_emails)
                
                # Store in session state
                st.session_state.processed_emails = prioritized_emails
                st.session_state.emails_processed = True
                st.session_state.current_page = 0
                
                st.success(f"✅ Successfully processed {len(processed_emails)} emails!")
                
            except Exception as e:
                st.error(f"❌ Error processing emails: {e}")
                st.error("Please check your email credentials and try again.")

with col2:
    if st.button("📄 Generate Brief"):
        if st.session_state.emails_processed:
            try:
                top_emails = [email for _, email in st.session_state.processed_emails[:10]]
                
                # Add required fields for briefing
                for i, email in enumerate(top_emails):
                    email['priority_level'] = 'HIGH' if i < 3 else 'MEDIUM' if i < 7 else 'LOW'
                    email['priority_score'] = st.session_state.processed_emails[i][0]
                    email['read_status'] = 'unread'
                    email['message_type'] = email.get('metrics', {}).get('intent', 'general')
                    email['timestamp'] = email.get('date', datetime.now())
                    
                    # Key points
                    key_points = []
                    if email.get('metrics', {}).get('has_deadline'):
                        key_points.append("⏰ Contains deadline")
                    if email.get('metrics', {}).get('urgency') == 'high':
                        key_points.append("🔥 High urgency")
                    if email.get('tag') == 'URGENT':
                        key_points.append("🚨 Tagged as urgent")
                    if email.get('sentiment_score', 0) < -0.1:
                        key_points.append("😟 Negative sentiment")
                    
                    email['key_points'] = key_points if key_points else ["📧 Standard email"]
                
                brief = generate_daily_brief(top_emails)
                st.text_area("Daily Brief", brief, height=200)
                
                if st.button("🔊 Read Brief Aloud"):
                    try:
                        read_text(brief)
                    except:
                        st.error("Text-to-speech not available")
            except Exception as e:
                st.error(f"Error generating brief: {e}")
        else:
            st.warning("Please process emails first")

with col3:
    if st.button("🛑 Stop Speech"):
        try:
            stop_speech()
            st.success("Speech stopped")
        except:
            st.info("No speech to stop")

# Display processed emails if available
if st.session_state.emails_processed:
    
    # Statistics dashboard
    st.subheader("📊 Email Analytics Dashboard")
    
    # Create metrics
    total_emails = len(st.session_state.processed_emails)
    tag_counts = {}
    confidence_levels = {'High': 0, 'Medium': 0, 'Low': 0}
    
    for score, email in st.session_state.processed_emails:
        tag = email.get('tag', 'GENERAL')
        tag_counts[tag] = tag_counts.get(tag, 0) + 1
        
        confidence = email.get('tag_confidence', 0)
        if confidence > 0.7:
            confidence_levels['High'] += 1
        elif confidence > 0.4:
            confidence_levels['Medium'] += 1
        else:
            confidence_levels['Low'] += 1
    
    # Display metrics
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Total Emails", total_emails)
    col2.metric("Urgent Emails", tag_counts.get('URGENT', 0))
    col3.metric("High Confidence", confidence_levels['High'])
    if total_emails > 0:
        avg_score = sum(score for score, _ in st.session_state.processed_emails) / total_emails
        col4.metric("Avg Priority Score", f"{avg_score:.2f}")
    else:
        col4.metric("Avg Priority Score", "0.00")
    
    # Charts
    col1, col2 = st.columns(2)
    
    with col1:
        if tag_counts:
            # Tag distribution
            fig_tags = px.pie(
                values=list(tag_counts.values()),
                names=list(tag_counts.keys()),
                title="Email Distribution by Tag"
            )
            st.plotly_chart(fig_tags, use_container_width=True)
    
    with col2:
        # Confidence levels
        fig_conf = px.bar(
            x=list(confidence_levels.keys()),
            y=list(confidence_levels.values()),
            title="Tagging Confidence Levels",
            color=list(confidence_levels.values()),
            color_continuous_scale="RdYlGn"
        )
        st.plotly_chart(fig_conf, use_container_width=True)
    
    # Filter and sort emails
    filtered_emails = st.session_state.processed_emails
    
    if st.session_state.filter_tag != 'ALL':
        filtered_emails = [(score, email) for score, email in filtered_emails 
                          if str(email.get('tag', 'GENERAL')).upper() == st.session_state.filter_tag.upper()]
    
    # Sort emails
    if st.session_state.sort_by == 'Priority Score':
        filtered_emails.sort(key=lambda x: x[0], reverse=True)
    elif st.session_state.sort_by == 'Confidence':
        filtered_emails.sort(key=lambda x: x[1].get('tag_confidence', 0), reverse=True)
    elif st.session_state.sort_by == 'Date':
        filtered_emails.sort(key=lambda x: x[1].get('date', datetime.now()), reverse=True)
    elif st.session_state.sort_by == 'Sender':
        filtered_emails.sort(key=lambda x: x[1].get('sender', ''))
    
    # Pagination
    EMAILS_PER_PAGE = 10
    total_pages = max(1, (len(filtered_emails) + EMAILS_PER_PAGE - 1) // EMAILS_PER_PAGE)
    
    # Ensure current page is valid
    if st.session_state.current_page >= total_pages:
        st.session_state.current_page = max(0, total_pages - 1)

    # Top Pagination Controls
    col1, col2, col3 = st.columns([1, 2, 1])
    with col1:
        if st.session_state.current_page > 0:
            if st.button("⬅️ Previous", key="prev_top_btn"):
                st.session_state.current_page -= 1
                st.rerun()
    with col2:
        st.write(f"Page {st.session_state.current_page + 1} of {total_pages} ({len(filtered_emails)} total emails)")
    with col3:
        if st.session_state.current_page < total_pages - 1:
            if st.button("Next ➡️", key="next_top_btn"):
                st.session_state.current_page += 1
                st.rerun()

    # Display emails
    start_idx = st.session_state.current_page * EMAILS_PER_PAGE
    end_idx = min(start_idx + EMAILS_PER_PAGE, len(filtered_emails))
    page_emails = filtered_emails[start_idx:end_idx]

    st.subheader(f"📧 Emails ({start_idx + 1}-{end_idx} of {len(filtered_emails)})")

    # Email display loop
    for email_idx, (priority_score, email) in enumerate(page_emails):
        email_id = email.get('id', f'email_{start_idx + email_idx}')
        subject = email.get('subject', 'No Subject')
        sender = email.get('sender', 'Unknown Sender')
        body = email.get('body', 'No body provided.')
        tag = email.get('tag', 'GENERAL')
        confidence = email.get('tag_confidence', 0.0)
        
        # Determine confidence class
        conf_class = 'high' if confidence > 0.7 else 'medium' if confidence > 0.4 else 'low'
        
        # Create email card
        with st.container():
            # Sanitize sender email to prevent errors
            display_sender = str(sender).replace('@', ' (at) ') if '@' in str(sender) else str(sender)
            
            st.markdown(f"""
            <div class="email-card {tag.lower()} confidence-{conf_class}">
                <h4>📧 {subject}</h4>
                <p><strong>From:</strong> {display_sender}</p>
                <p><strong>Priority Score:</strong> {priority_score:.2f} | <strong>Tag:</strong> {tag} | <strong>Confidence:</strong> {confidence:.1%}</p>
            </div>
            """, unsafe_allow_html=True)
            
            # Email summary
            summary = body[:200] + "..." if len(body) > 200 else body
            st.markdown(f"<div style='color: #333333; font-weight: 500; background-color: #f5f5f5; padding: 10px; border-radius: 5px;'><strong>Summary:</strong> {summary}</div>", unsafe_allow_html=True)
            
            # Show reasoning if enabled
            if show_reasoning:
                reasoning = email.get('tag_reasoning', [])
                if reasoning:
                    st.markdown(f"<div style='color: #333333; font-weight: 500; background-color: #fff0f5; padding: 8px; border-radius: 5px; margin-top: 5px;'><strong>Tagging Reasoning:</strong> {', '.join(reasoning)}</div>", unsafe_allow_html=True)
            
            # Features detected
            features = email.get('features_detected', {})
            if features:
                feature_text = []
                if features.get('time_urgency', 0) > 0:
                    feature_text.append(f"⏰ Time urgency: {features['time_urgency']}")
                if features.get('has_attachments'):
                    feature_text.append("📎 Has attachments")
                feature_text.append(f"📝 {features.get('word_count', 0)} words")
                
                if feature_text:
                    st.markdown(f"<div style='color: #333333; font-weight: 500; background-color: #f0f7ff; padding: 8px; border-radius: 5px; margin-top: 5px;'><strong>Features:</strong> {' | '.join(feature_text)}</div>", unsafe_allow_html=True)
            
            # Action buttons
            col1, col2, col3, col4, col5 = st.columns(5)
            
            with col1:
                # Sanitize key for button
                button_key = f"read_{email_id}_{start_idx + email_idx}".replace('@', '_at_').replace('.', '_dot_')
                if st.button(f"🔊 Read", key=button_key):
                    try:
                        tts_body = clean_text_for_summary(body)
                        read_text(f"Email from {display_sender}. Subject: {subject}. {tts_body}")
                    except:
                        st.error("Text-to-speech not available")
            
            with col2:
                # Tag correction
                safe_email_id = str(email_id).replace('@', '_at_').replace('.', '_dot_')
                tag_key = f"tag_{safe_email_id}_{start_idx + email_idx}"
                new_tag = st.selectbox(
                    "Correct Tag",
                    ['URGENT', 'MEETING', 'FINANCIAL', 'IMPORTANT', 'PROMOTIONAL', 'NEWSLETTER', 'SECURITY', 'GENERAL'],
                    index=['URGENT', 'MEETING', 'FINANCIAL', 'IMPORTANT', 'PROMOTIONAL', 'NEWSLETTER', 'SECURITY', 'GENERAL'].index(tag),
                    key=tag_key
                )
                
                if new_tag != tag:
                    update_key = f"update_tag_{safe_email_id}_{start_idx + email_idx}"
                    if st.button(f"✅ Update", key=update_key):
                        components['tagger'].process_feedback(email_id, new_tag, tag, sender)
                        st.success(f"Tag updated from {tag} to {new_tag}")
                        # Update the email in session state
                        for i, (score, em) in enumerate(st.session_state.processed_emails):
                            if em.get('id') == email_id:
                                st.session_state.processed_emails[i] = (score, {**em, 'tag': new_tag})
                                break
                        st.rerun()
            
            with col3:
                # Feedback buttons
                safe_email_id = str(email_id).replace('@', '_at_').replace('.', '_dot_')
                good_key = f"good_{safe_email_id}_{start_idx + email_idx}"
                if st.button(f"👍 Good", key=good_key):
                    components['tagger'].process_feedback(email_id, tag, tag, sender)
                    st.success("Positive feedback recorded!")
            
            with col4:
                # Summary feedback
                st.write("Summary helpful?")
                col4a, col4b = st.columns(2)
                safe_email_id = str(email_id).replace('@', '_at_').replace('.', '_dot_')
                
                with col4a:
                    helpful_key = f"summary_good_{safe_email_id}_{start_idx + email_idx}"
                    if st.button(f"👍", key=helpful_key):
                        st.success("✅")
                
                with col4b:
                    not_helpful_key = f"summary_bad_{safe_email_id}_{start_idx + email_idx}"
                    if st.button(f"👎", key=not_helpful_key):
                        st.success("❌")
            
            # Smart suggestions
            if show_suggestions:
                with col5:
                    safe_email_id = str(email_id).replace('@', '_at_').replace('.', '_dot_')
                    suggest_key = f"suggest_{safe_email_id}_{start_idx + email_idx}"
                    if st.button(f"💡 Actions", key=suggest_key):
                        suggestions = components['suggestions'].generate_suggestions(email, tag, confidence)
                        
                        st.write("**Smart Suggestions:**")
                        for i, suggestion in enumerate(suggestions[:3]):
                            suggestion_text = suggestion['text']
                            suggestion_time = suggestion.get('estimated_time', '')
                            suggestion_confidence = suggestion.get('confidence', 0)
                            
                            time_text = f" (⏱️ {suggestion_time})" if suggestion_time else ""
                            confidence_text = f" ({int(suggestion_confidence * 100)}%)" if suggestion_confidence else ""
                            
                            col_a, col_b = st.columns([3, 1])
                            with col_a:
                                st.write(f"• {suggestion_text}{time_text}{confidence_text}")
                            with col_b:
                                exec_key = f"exec_{safe_email_id}_{start_idx + email_idx}_{i}"
                                if st.button(f"Execute", key=exec_key):
                                    result = components['suggestions'].execute_suggestion(email, suggestion['action'])
                                    if result['success']:
                                        st.success(result['message'])
                                    else:
                                        st.error(result['message'])
            
            st.markdown("---")
    
    # Bottom Pagination Controls
    col1, col2, col3 = st.columns([1, 2, 1])
    with col1:
        if st.session_state.current_page > 0:
            if st.button("⬅️ Previous", key="prev_bottom_btn"):
                st.session_state.current_page -= 1
                st.rerun()
    
    with col2:
        st.write(f"Page {st.session_state.current_page + 1} of {total_pages}")
    
    with col3:
        if st.session_state.current_page < total_pages - 1:
            if st.button("Next ➡️", key="next_bottom_btn"):
                st.session_state.current_page += 1
                st.rerun()
    
    # Analytics section
    st.markdown("---")
    st.subheader("💡 Learning Analytics")
    
    # Load and display feedback stats
    if os.path.exists('tagging_feedback.json'):
        try:
            with open('tagging_feedback.json', 'r') as f:
                feedback_data = json.load(f)
            
            col1, col2, col3 = st.columns(3)
            
            corrections = feedback_data.get('tag_corrections', {})
            sender_prefs = feedback_data.get('sender_preferences', {})
            
            col1.metric("Total Corrections", len(corrections))
            col2.metric("Learned Senders", len(sender_prefs))
            
            if corrections:
                recent_corrections = list(corrections.values())[-5:]
                accuracy_scores = [c.get('quality', 0) for c in recent_corrections]
                if accuracy_scores:
                    avg_quality = sum(accuracy_scores) / len(accuracy_scores)
                    col3.metric("Recent Quality", f"{avg_quality:.1f}")
        except Exception as e:
            st.error(f"Error loading feedback data: {e}")
    
    # Show smart suggestion usage if available
    suggestion_stats = components['suggestions'].usage_stats
    if suggestion_stats.get('user_preferences'):
        st.subheader("📈 Action Usage Statistics")
        
        action_counts = suggestion_stats['user_preferences']
        if action_counts:
            # Create a simple bar chart of most used actions
            action_data = [{"Action": action.replace('_', ' ').title(), "Count": count} 
                          for action, count in sorted(action_counts.items(), 
                                                    key=lambda x: x[1], 
                                                    reverse=True)]
            if action_data:
                df_actions = pd.DataFrame(action_data)
                st.bar_chart(df_actions.set_index("Action"))

else:
    # Welcome screen
    st.markdown("""
    ## Welcome to Smart Inbox Assistant! 🎉
    
    This intelligent email management system will help you:
    
    ### 🎯 **Priority Tagging**
    - Automatically categorize emails (Urgent, Meeting, Financial, etc.)
    - Learn from your feedback to improve accuracy
    - Show confidence levels and reasoning for each tag
    
    ### 🤖 **Smart Suggestions**
    - Get contextual action suggestions for each email
    - Quick reply templates and calendar integration
    - Time estimates for each suggested action
    
    ### 🧠 **Adaptive Learning**
    - System learns from your tag corrections
    - Builds sender preferences over time
    - Improves prioritization based on your feedback
    
    ### 🔊 **Accessibility Features**
    - Text-to-speech for email content
    - Voice briefings for daily summaries
    - Audio feedback for high-priority items
    
    ---
    
    **Getting Started:**
    1. Configure your email credentials in the sidebar
    2. Choose your email source (Live Email or Mock Emails)
    3. Click "Load & Process Emails" to begin
    4. Provide feedback to improve the system
    
    Ready to revolutionize your inbox management? Let's get started! 🚀
    """)
    
    # Quick stats if available
    if os.path.exists('tagging_feedback.json'):
        try:
            with open('tagging_feedback.json', 'r') as f:
                feedback_data = json.load(f)
            
            st.subheader("📈 System Learning Progress")
            col1, col2, col3 = st.columns(3)
            
            corrections = feedback_data.get('tag_corrections', {})
            sender_prefs = feedback_data.get('sender_preferences', {})
            
            col1.metric("Total Corrections", len(corrections))
            col2.metric("Learned Senders", len(sender_prefs))
            col3.metric("Learning Sessions", len(set(c.get('timestamp', '')[:10] for c in corrections.values())))
        except Exception as e:
            st.info("No learning data available yet. Start processing emails to build your personalized assistant!")

# Footer
st.markdown("---")
st.markdown("""
<div style='text-align: center; color: #666;'>
    <p>Smart Inbox Assistant v2.0 | Powered by AI Priority Tagging & Feedback Learning</p>
    <p>💡 Tip: Regular feedback helps the system learn your preferences better!</p>
</div>
""", unsafe_allow_html=True)
