"""
SmartBrief v3 - Interactive Streamlit Demo
Comprehensive demo application showcasing all features of the context-aware summarizer.
"""

import streamlit as st
import pandas as pd
import json
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
import tempfile
import os
from smart_summarizer_v3 import SmartSummarizerV3, summarize_message
from context_loader import ContextLoader
from feedback_system import FeedbackCollector

# Page configuration
st.set_page_config(
    page_title="SmartBrief v3 Demo",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS - Fixed visibility and styling issues
st.markdown("""
<style>
.metric-card {
    background-color: #f8f9fa;
    color: #212529;
    padding: 1rem;
    border-radius: 0.5rem;
    border-left: 4px solid #1f77b4;
    margin: 0.5rem 0;
    box-shadow: 0 2px 4px rgba(0,0,0,0.1);
}
.intent-high { 
    border-left-color: #dc3545; 
    background-color: #fff5f5;
}
.intent-medium { 
    border-left-color: #ffc107; 
    background-color: #fffbf0;
}
.intent-low { 
    border-left-color: #28a745; 
    background-color: #f8fff8;
}
.platform-whatsapp { 
    background-color: #e8f5e8; 
    color: #155724;
}
.platform-email { 
    background-color: #e8e8f5; 
    color: #383d41;
}
.platform-slack { 
    background-color: #f5e8f5; 
    color: #721c24;
}
.platform-teams { 
    background-color: #e8f4f8; 
    color: #0c5460;
}
.platform-instagram { 
    background-color: #ffe8f5; 
    color: #856404;
}
.platform-discord { 
    background-color: #f0e8ff; 
    color: #6f42c1;
}
.feedback-positive { 
    background-color: #d4edda; 
    border-color: #c3e6cb; 
    color: #155724;
}
.feedback-negative { 
    background-color: #f8d7da; 
    border-color: #f5c6cb; 
    color: #721c24;
}
.stButton > button {
    background-color: #007bff;
    color: white;
    border: none;
    border-radius: 0.25rem;
    padding: 0.5rem 1rem;
}
.stButton > button:hover {
    background-color: #0056b3;
}
</style>
""", unsafe_allow_html=True)

# Initialize session state
if 'summarizer' not in st.session_state:
    st.session_state.summarizer = SmartSummarizerV3()
if 'processed_messages' not in st.session_state:
    st.session_state.processed_messages = []
if 'feedback_collector' not in st.session_state:
    st.session_state.feedback_collector = FeedbackCollector()
if 'context_loader' not in st.session_state:
    st.session_state.context_loader = ContextLoader()
if 'feedback_submitted' not in st.session_state:
    st.session_state.feedback_submitted = {}
if 'current_analysis' not in st.session_state:
    st.session_state.current_analysis = None
if 'current_message' not in st.session_state:
    st.session_state.current_message = None
if 'last_selected_platform' not in st.session_state:
    st.session_state.last_selected_platform = None
if 'current_message_text' not in st.session_state:
    st.session_state.current_message_text = None

def load_sample_messages():
    """Load sample messages for demonstration with different platform styles."""
    return [
        # Email style - formal
        {
            'user_id': 'alice_work',
            'platform': 'email',
            'message_text': 'Hi team, please review the quarterly budget proposal attached. Need feedback by Friday for the board meeting.',
            'timestamp': '2025-08-07T09:00:00Z',
            'message_id': 'msg_001'
        },
        # WhatsApp style - casual
        {
            'user_id': 'bob_friend',
            'platform': 'whatsapp',
            'message_text': 'yo whats up? party tonight at 8pm, u coming?',
            'timestamp': '2025-08-07T14:30:00Z',
            'message_id': 'msg_002'
        },
        # Follow-up email
        {
            'user_id': 'alice_work',
            'platform': 'email',
            'message_text': 'Hey, did the report get done? The board meeting is tomorrow!',
            'timestamp': '2025-08-07T16:45:00Z',
            'message_id': 'msg_003'
        },
        # Slack style - work urgent
        {
            'user_id': 'customer_support',
            'platform': 'slack',
            'message_text': 'The login system is down again. Multiple customers are complaining. This is urgent!',
            'timestamp': '2025-08-07T11:15:00Z',
            'message_id': 'msg_004'
        },
        # Instagram DM style - casual with emojis
        {
            'user_id': 'fashion_influencer',
            'platform': 'instagram',
            'message_text': 'love ur latest post! 😍 where did u get that dress?',
            'timestamp': '2025-08-07T08:20:00Z',
            'message_id': 'msg_005'
        },
        # Teams style - professional
        {
            'user_id': 'project_manager',
            'platform': 'teams',
            'message_text': 'Can we schedule a quick standup for tomorrow at 10 AM? Need to discuss the sprint planning.',
            'timestamp': '2025-08-07T17:10:00Z',
            'message_id': 'msg_006'
        },
        # WhatsApp follow-up
        {
            'user_id': 'bob_friend',
            'platform': 'whatsapp',
            'message_text': 'did u see my message about the party? need headcount for food!',
            'timestamp': '2025-08-07T18:00:00Z',
            'message_id': 'msg_007'
        }
    ]

def create_analytics_charts(messages, results):
    """Create analytics charts from processed messages and results."""
    if not results or not messages:
        return None, None, None, None
    
    # Combine message and result data
    combined_data = []
    for message, result in zip(messages, results):
        combined_data.append({
            'platform': message['platform'],
            'user_id': message['user_id'],
            'intent': result['intent'],
            'urgency': result['urgency'],
            'type': result['type'],
            'confidence': result['confidence'],
            'context_used': result['context_used']
        })
    
    df = pd.DataFrame(combined_data)
    
    # Intent distribution
    intent_counts = df['intent'].value_counts()
    fig_intent = px.pie(
        values=intent_counts.values,
        names=intent_counts.index,
        title="Intent Distribution",
        color_discrete_sequence=px.colors.qualitative.Set3
    )
    
    # Urgency distribution
    urgency_counts = df['urgency'].value_counts()
    urgency_colors = {'high': '#ff4444', 'medium': '#ffaa44', 'low': '#44ff44'}
    fig_urgency = px.bar(
        x=urgency_counts.index,
        y=urgency_counts.values,
        title="Urgency Levels",
        color=urgency_counts.index,
        color_discrete_map=urgency_colors
    )
    
    # Platform distribution
    platform_counts = df['platform'].value_counts()
    fig_platform = px.bar(
        x=platform_counts.index,
        y=platform_counts.values,
        title="Messages by Platform",
        color=platform_counts.index,
        color_discrete_sequence=px.colors.qualitative.Pastel
    )
    
    # Message type distribution
    type_counts = df['type'].value_counts()
    fig_types = px.bar(
        x=type_counts.index,
        y=type_counts.values,
        title="Message Types",
        color=type_counts.index,
        color_discrete_sequence=px.colors.qualitative.Dark2
    )
    
    return fig_intent, fig_urgency, fig_platform, fig_types

def display_message_result(message, result, index):
    """Display a message and its analysis result with feedback option."""
    with st.container():
        # Create columns for layout
        col1, col2 = st.columns([2, 1])
        
        with col1:
            # Message content with better visibility
            st.markdown(f"""
            <div class="metric-card platform-{message['platform']}">
                <h4>📱 {message['platform'].title()} - {message['user_id']}</h4>
                <p><strong>Message:</strong> {message['message_text']}</p>
                <p><strong>Summary:</strong> {result['summary']}</p>
                <p><strong>Type:</strong> {result['type'].title()}</p>
            </div>
            """, unsafe_allow_html=True)
        
        with col2:
            # Analysis results with better visibility
            urgency_color = {'high': '🔴', 'medium': '🟡', 'low': '🟢'}[result['urgency']]
            
            st.markdown(f"""
            <div class="metric-card intent-{result['urgency']}">
                <p><strong>🎯 Intent:</strong> {result['intent'].title()}</p>
                <p><strong>{urgency_color} Urgency:</strong> {result['urgency'].title()}</p>
                <p><strong>🎲 Confidence:</strong> {result['confidence']:.2f}</p>
                <p><strong>🧠 Context:</strong> {'Yes' if result['context_used'] else 'No'}</p>
            </div>
            """, unsafe_allow_html=True)
        
        # Expandable reasoning and feedback
        with st.expander(f"🔍 Analysis Details & Feedback - Message {index + 1}"):
            col_details, col_feedback = st.columns([1, 1])
            
            with col_details:
                st.write("**Reasoning:**")
                for reason in result['reasoning']:
                    st.write(f"• {reason}")
                
                if result.get('platform_optimized'):
                    st.success("✅ Platform-optimized summary generated")
                
                st.json({
                    'intent': result['intent'],
                    'urgency': result['urgency'],
                    'type': result['type'],
                    'confidence': result['confidence'],
                    'context_used': result['context_used']
                })
            
            with col_feedback:
                st.write("**📝 Provide Feedback:**")
                
                # Check if feedback already submitted for this message
                feedback_key = f"feedback_{index}_{message.get('message_id', index)}"
                
                if feedback_key not in st.session_state.feedback_submitted:
                    # Create a form for feedback to prevent disappearing
                    with st.form(f"feedback_form_{index}"):
                        feedback_score = st.selectbox(
                            "Rate this summary:",
                            options=[1, 0, -1],
                            format_func=lambda x: {1: "👍 Good", 0: "😐 Neutral", -1: "👎 Poor"}[x],
                            key=f"feedback_score_{index}"
                        )
                        
                        feedback_comment = st.text_area(
                            "Optional comment:",
                            key=f"feedback_comment_{index}",
                            height=60
                        )
                        
                        # Category ratings
                        st.write("**Category Ratings:**")
                        summary_rating = st.selectbox(
                            "Summary Quality:",
                            options=[1, 0, -1],
                            format_func=lambda x: {1: "Good", 0: "Neutral", -1: "Poor"}[x],
                            key=f"summary_rating_{index}"
                        )
                        
                        intent_rating = st.selectbox(
                            "Intent Detection:",
                            options=[1, 0, -1],
                            format_func=lambda x: {1: "Good", 0: "Neutral", -1: "Poor"}[x],
                            key=f"intent_rating_{index}"
                        )
                        
                        urgency_rating = st.selectbox(
                            "Urgency Assessment:",
                            options=[1, 0, -1],
                            format_func=lambda x: {1: "Good", 0: "Neutral", -1: "Poor"}[x],
                            key=f"urgency_rating_{index}"
                        )
                        
                        # Submit button inside form
                        submitted = st.form_submit_button("Submit Feedback")
                        
                        if submitted:
                            success = st.session_state.feedback_collector.collect_feedback(
                                message_id=message.get('message_id', f'msg_{index}'),
                                user_id=message['user_id'],
                                platform=message['platform'],
                                original_text=message['message_text'],
                                generated_summary=result['summary'],
                                feedback_score=feedback_score,
                                feedback_comment=feedback_comment,
                                category_ratings={
                                    'summary_quality': summary_rating,
                                    'intent_detection': intent_rating,
                                    'urgency_level': urgency_rating
                                }
                            )
                            
                            if success:
                                st.success("✅ Feedback submitted successfully!")
                                # Store in context loader as well
                                st.session_state.context_loader.add_message(message, result)
                                # Mark as submitted
                                st.session_state.feedback_submitted[feedback_key] = True
                                st.rerun()
                            else:
                                st.error("❌ Failed to submit feedback")
                else:
                    st.success("✅ Feedback already submitted for this message!")

def get_platform_sample_message(platform):
    """Get a sample message for the selected platform."""
    platform_samples = {
        'whatsapp': "yo whats up? party tonight at 8pm, u coming?",
        'email': "Hi team, please review the quarterly budget proposal attached. Need feedback by Friday for the board meeting.",
        'slack': "The login system is down again. Multiple customers are complaining. This is urgent!",
        'teams': "Can we schedule a quick standup for tomorrow at 10 AM? Need to discuss the sprint planning.",
        'instagram': "love ur latest post! 😍 where did u get that dress?",
        'discord': "anyone up for a gaming session tonight? new update dropped!"
    }
    return platform_samples.get(platform, "Enter your message here...")

# Main app
def main():
    st.title("🤖 SmartBrief v3 - Interactive Demo")
    st.markdown("*Context-Aware, Platform-Agnostic Message Summarization with Feedback Loop*")
    
    # Sidebar
    st.sidebar.title("🎛️ Demo Controls")
    
    # Demo mode selection
    demo_mode = st.sidebar.radio(
        "Select Demo Mode:",
        ["Single Message", "Batch Processing", "Upload JSON", "Context Analysis", "Feedback Analytics", "Performance Test"],
        key="demo_mode_radio"
    )
    
    # Platform filter
    platforms = ['All', 'whatsapp', 'email', 'slack', 'teams', 'instagram', 'discord']
    selected_platform = st.sidebar.selectbox("Filter by Platform:", platforms)
    
    # Context settings
    st.sidebar.subheader("🧠 Context Settings")
    use_context = st.sidebar.checkbox("Use Context Awareness", value=True)
    max_context = st.sidebar.slider("Max Context Messages", 1, 10, 3)
    
    # Update summarizer settings
    st.session_state.summarizer.max_context_messages = max_context
    
    # Main content area
    if demo_mode == "Single Message":
        st.header("📝 Single Message Analysis")
        
        col1, col2 = st.columns([2, 1])
        
        with col1:
            # Input form
            with st.form("single_message_form"):
                user_id = st.text_input("User ID:", value="demo_user")
                
                platform_options = ['whatsapp', 'email', 'slack', 'teams', 'instagram', 'discord', 'custom']
                platform = st.selectbox("Platform:", platform_options, key="platform_select")
                
                if st.session_state.last_selected_platform is None:
                    st.session_state.last_selected_platform = platform
                if st.session_state.current_message_text is None:
                    st.session_state.current_message_text = get_platform_sample_message(platform)
                
                if st.session_state.last_selected_platform != platform:
                    if platform == 'custom':
                        st.session_state.current_message_text = "Enter your custom message here..."
                    else:
                        st.session_state.current_message_text = get_platform_sample_message(platform)
                    st.session_state.last_selected_platform = platform
                
                if platform == 'custom':
                    # Custom platform input
                    custom_platform = st.text_input("Custom Platform Name:", value="my_platform")
                    message_text = st.text_area("Message Text:", 
                        value=st.session_state.current_message_text,
                        height=100,
                        key="custom_message_text")
                    # Use custom platform name for processing
                    selected_platform = custom_platform if custom_platform else "custom"
                else:
                    message_text = st.text_area("Message Text:", 
                        value=st.session_state.current_message_text,
                        height=100,
                        key=f"message_text_{platform}")
                    selected_platform = platform
                
                if message_text != st.session_state.current_message_text:
                    st.session_state.current_message_text = message_text
                
                if platform != 'custom':
                    platform_styles = {
                        'whatsapp': "💬 Casual, informal, with abbreviations and emojis",
                        'email': "📧 Formal, professional, structured communication",
                        'slack': "💼 Work-focused, direct, often urgent",
                        'teams': "🏢 Professional, meeting-oriented, collaborative",
                        'instagram': "📸 Social, visual-focused, emoji-heavy",
                        'discord': "🎮 Gaming/community focused, casual, group-oriented"
                    }
                    st.info(f"**{platform.title()} Style:** {platform_styles.get(platform, '')}")
                
                submitted = st.form_submit_button("🔍 Analyze Message")
            
            # Process and store results in session state to persist across reruns
            if submitted and message_text and message_text not in ["Enter your message here...", "Enter your custom message here..."]:
                message_data = {
                    'user_id': user_id,
                    'platform': selected_platform,
                    'message_text': message_text,
                    'timestamp': datetime.now().isoformat(),
                    'message_id': f'single_{datetime.now().timestamp()}'
                }
                
                with st.spinner("Analyzing message..."):
                    result = st.session_state.summarizer.summarize(message_data, use_context=use_context)
                
                # Store in session state to persist
                st.session_state.current_message = message_data
                st.session_state.current_analysis = result
                
                st.success("✅ Analysis Complete!")
            elif submitted and message_text in ["Enter your message here...", "Enter your custom message here..."]:
                st.warning("⚠️ Please enter a valid message to analyze.")
            
            # Display results if they exist in session state
            if st.session_state.current_message and st.session_state.current_analysis:
                display_message_result(st.session_state.current_message, st.session_state.current_analysis, 0)
                
                # Add a button to clear results
                if st.button("🗑️ Clear Results"):
                    st.session_state.current_message = None
                    st.session_state.current_analysis = None
                    st.rerun()
        
        with col2:
            st.subheader("📊 Quick Stats")
            stats = st.session_state.summarizer.get_stats()
            
            st.metric("Messages Processed", stats['processed'])
            st.metric("Context Usage Rate", f"{stats['context_usage_rate']:.1%}")
            st.metric("Unique Users", stats['unique_users'])
            
            if stats['platforms']:
                st.write("**Platform Distribution:**")
                for platform, count in stats['platforms'].items():
                    st.write(f"• {platform}: {count}")
            
            if stats['intents']:
                st.write("**Intent Distribution:**")
                for intent, count in stats['intents'].items():
                    st.write(f"• {intent}: {count}")
    
    elif demo_mode == "Batch Processing":
        st.header("📦 Batch Message Processing")
        
        # Load sample messages
        sample_messages = load_sample_messages()
        
        # Filter by platform if selected
        if selected_platform != 'All':
            sample_messages = [msg for msg in sample_messages if msg['platform'] == selected_platform]
        
        st.write(f"**Sample Dataset:** {len(sample_messages)} messages")
        
        # Show sample messages preview
        with st.expander("📋 Preview Sample Messages"):
            for i, msg in enumerate(sample_messages[:3]):
                st.write(f"**{i+1}. {msg['platform'].title()}** ({msg['user_id']}): {msg['message_text']}")
        
        if st.button("🚀 Process All Messages"):
            with st.spinner("Processing messages..."):
                results = st.session_state.summarizer.batch_summarize(sample_messages, use_context=use_context)
            
            st.success(f"✅ Processed {len(results)} messages!")
            
            # Store results for analytics
            st.session_state.processed_messages = list(zip(sample_messages, results))
            
            # Display results
            st.subheader("📋 Processing Results")
            
            for i, (message, result) in enumerate(st.session_state.processed_messages):
                display_message_result(message, result, i)
                st.markdown("---")
            
            # Analytics - Fixed to pass both messages and results
            st.subheader("📊 Analytics Dashboard")
            
            fig_intent, fig_urgency, fig_platform, fig_types = create_analytics_charts(sample_messages, results)
            
            if fig_intent:
                col1, col2 = st.columns(2)
                
                with col1:
                    st.plotly_chart(fig_intent, use_container_width=True)
                    st.plotly_chart(fig_platform, use_container_width=True)
                
                with col2:
                    st.plotly_chart(fig_urgency, use_container_width=True)
                    st.plotly_chart(fig_types, use_container_width=True)
    
    elif demo_mode == "Upload JSON":
        st.header("📁 Upload Your Own Messages")
        
        uploaded_file = st.file_uploader(
            "Choose a JSON file with your messages",
            type=['json'],
            help="Upload a JSON file containing an array of message objects"
        )
        
        if uploaded_file is not None:
            try:
                messages = json.load(uploaded_file)
                
                if not isinstance(messages, list):
                    st.error("JSON file must contain an array of message objects")
                    return
                
                st.success(f"✅ Loaded {len(messages)} messages from file")
                
                # Validate message format
                required_fields = ['user_id', 'platform', 'message_text']
                valid_messages = []
                
                for i, msg in enumerate(messages):
                    if all(field in msg for field in required_fields):
                        if 'timestamp' not in msg:
                            msg['timestamp'] = datetime.now().isoformat()
                        if 'message_id' not in msg:
                            msg['message_id'] = f'uploaded_{i}'
                        valid_messages.append(msg)
                    else:
                        st.warning(f"Message {i+1} missing required fields: {required_fields}")
                
                if valid_messages:
                    st.write(f"**Valid Messages:** {len(valid_messages)}")
                    
                    # Show sample
                    with st.expander("📋 Preview Messages"):
                        st.json(valid_messages[:3])
                    
                    if st.button("🔍 Analyze Uploaded Messages"):
                        with st.spinner("Processing uploaded messages..."):
                            results = st.session_state.summarizer.batch_summarize(valid_messages, use_context=use_context)
                        
                        st.success("✅ Analysis Complete!")
                        
                        # Display results
                        for i, (message, result) in enumerate(zip(valid_messages, results)):
                            display_message_result(message, result, i)
                            if i < len(valid_messages) - 1:
                                st.markdown("---")
                        
                        # Analytics for uploaded messages
                        st.subheader("📊 Analytics Dashboard")
                        fig_intent, fig_urgency, fig_platform, fig_types = create_analytics_charts(valid_messages, results)
                        
                        if fig_intent:
                            col1, col2 = st.columns(2)
                            
                            with col1:
                                st.plotly_chart(fig_intent, use_container_width=True)
                                st.plotly_chart(fig_platform, use_container_width=True)
                            
                            with col2:
                                st.plotly_chart(fig_urgency, use_container_width=True)
                                st.plotly_chart(fig_types, use_container_width=True)
                        
                        # Download results
                        results_json = json.dumps(results, indent=2, default=str)
                        st.download_button(
                            label="💾 Download Results (JSON)",
                            data=results_json,
                            file_name=f"smartbrief_results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
                            mime="application/json"
                        )
                
            except json.JSONDecodeError:
                st.error("Invalid JSON file. Please check the format.")
            except Exception as e:
                st.error(f"Error processing file: {str(e)}")
        
        # Show expected format
        st.subheader("📋 Expected JSON Format")
        st.code("""
[
  {
    "user_id": "user123",
    "platform": "whatsapp",
    "message_text": "Hey! How are you doing?",
    "timestamp": "2025-08-07T10:00:00Z",
    "message_id": "optional_id"
  },
  {
    "user_id": "user456",
    "platform": "email",
    "message_text": "Please review the attached document.",
    "timestamp": "2025-08-07T11:00:00Z"
  }
]
        """, language="json")
    
    elif demo_mode == "Context Analysis":
        st.header("🧠 Context Awareness Demo")
        
        st.write("This demo shows how SmartBrief v3 uses conversation context to improve analysis.")
        
        # Predefined conversation flow
        conversation_flow = [
            {
                'user_id': 'demo_user',
                'platform': 'email',
                'message_text': 'I will send the quarterly report tonight after the meeting.',
                'timestamp': '2025-08-07T09:00:00Z',
                'step': 1,
                'description': 'Initial commitment'
            },
            {
                'user_id': 'demo_user',
                'platform': 'email',
                'message_text': 'Hey, did the report get done?',
                'timestamp': '2025-08-07T16:45:00Z',
                'step': 2,
                'description': 'Follow-up question'
            },
            {
                'user_id': 'demo_user',
                'platform': 'email',
                'message_text': 'The board meeting is tomorrow and we still need the report ASAP!',
                'timestamp': '2025-08-07T18:00:00Z',
                'step': 3,
                'description': 'Urgent escalation'
            }
        ]
        
        st.subheader("📱 Conversation Flow")
        
        # Process conversation step by step
        for msg in conversation_flow:
            st.write(f"**Step {msg['step']}: {msg['description']}**")
            
            col1, col2 = st.columns([2, 1])
            
            with col1:
                st.write(f"💬 Message: *{msg['message_text']}*")
            
            with col2:
                if st.button(f"Analyze Step {msg['step']}", key=f"analyze_{msg['step']}"):
                    result = st.session_state.summarizer.summarize(msg, use_context=True)
                    
                    st.write(f"**Summary:** {result['summary']}")
                    st.write(f"**Type:** {result['type']} | **Intent:** {result['intent']} | **Urgency:** {result['urgency']}")
                    st.write(f"**Context Used:** {'Yes' if result['context_used'] else 'No'}")
                    
                    if result['context_used']:
                        st.success("🧠 Context awareness active!")
                    
                    with st.expander("Detailed Analysis"):
                        for reason in result['reasoning']:
                            st.write(f"• {reason}")
            
            st.markdown("---")
        
        # Context statistics
        st.subheader("📊 Context Statistics")
        context_stats = st.session_state.summarizer.get_stats()
        
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Total Context Entries", context_stats['total_context_entries'])
        with col2:
            st.metric("Context Usage Rate", f"{context_stats['context_usage_rate']:.1%}")
        with col3:
            st.metric("Unique Users", context_stats['unique_users'])
    
    elif demo_mode == "Feedback Analytics":
        st.header("📊 Feedback Analytics Dashboard")
        
        # Get feedback analytics
        analytics = st.session_state.feedback_collector.get_feedback_analytics()
        
        # Overall metrics
        st.subheader("📈 Overall Performance")
        
        col1, col2, col3, col4 = st.columns(4)
        
        overall_metrics = analytics.get('overall_metrics', {})
        
        with col1:
            st.metric("Total Feedback", overall_metrics.get('total_feedback', 0))
        with col2:
            st.metric("Positive Feedback", overall_metrics.get('positive_feedback', 0))
        with col3:
            st.metric("Negative Feedback", overall_metrics.get('negative_feedback', 0))
        with col4:
            satisfaction_rate = overall_metrics.get('satisfaction_rate', 0)
            st.metric("Satisfaction Rate", f"{satisfaction_rate:.1%}")
        
        # Platform performance
        st.subheader("🔧 Platform Performance")
        
        platform_performance = analytics.get('platform_performance', {})
        if platform_performance:
            platform_df = pd.DataFrame.from_dict(platform_performance, orient='index')
            
            fig_platform_satisfaction = px.bar(
                x=platform_df.index,
                y=platform_df['satisfaction_rate'],
                title="Satisfaction Rate by Platform",
                labels={'x': 'Platform', 'y': 'Satisfaction Rate'}
            )
            
            st.plotly_chart(fig_platform_satisfaction, use_container_width=True)
        else:
            st.info("No platform feedback data available yet. Process some messages and provide feedback!")
        
        # Category performance
        st.subheader("📋 Category Performance")
        
        category_performance = analytics.get('category_performance', {})
        if category_performance:
            category_df = pd.DataFrame.from_dict(category_performance, orient='index')
            
            fig_category_performance = px.bar(
                x=category_df.index,
                y=category_df['average'],
                title="Average Rating by Category",
                labels={'x': 'Category', 'y': 'Average Rating'}
            )
            
            st.plotly_chart(fig_category_performance, use_container_width=True)
        else:
            st.info("No category feedback data available yet.")
        
        # Recent feedback
        st.subheader("📝 Recent Feedback")
        
        recent_feedback = analytics.get('recent_feedback', [])
        if recent_feedback:
            for feedback in recent_feedback[-5:]:  # Show last 5
                feedback_class = "feedback-positive" if feedback.get('feedback_score', 0) > 0 else "feedback-negative" if feedback.get('feedback_score', 0) < 0 else ""
                
                with st.expander(f"Feedback from {feedback.get('user_id', 'Unknown')} - {feedback.get('platform', 'Unknown')}"):
                    st.markdown(f"""
                    <div class="{feedback_class}" style="padding: 10px; border-radius: 5px; margin: 5px 0;">
                        <p><strong>Original:</strong> {feedback.get('original_text', '')[:100]}...</p>
                        <p><strong>Summary:</strong> {feedback.get('generated_summary', '')}</p>
                        <p><strong>Score:</strong> {feedback.get('feedback_score', 0)}</p>
                        {f"<p><strong>Comment:</strong> {feedback.get('feedback_comment', '')}</p>" if feedback.get('feedback_comment') else ""}
                    </div>
                    """, unsafe_allow_html=True)
        else:
            st.info("No recent feedback available.")
        
        # Improvement suggestions
        st.subheader("💡 Improvement Suggestions")
        
        suggestions = analytics.get('improvement_suggestions', [])
        if suggestions:
            for suggestion in suggestions:
                st.write(f"• {suggestion}")
        else:
            st.success("✅ No specific improvements needed based on current feedback!")
    
    elif demo_mode == "Performance Test":
        st.header("🚀 Performance Testing")
        
        st.write("Test SmartBrief v3 performance with different message volumes and platform types.")
        
        # Performance test settings
        col1, col2 = st.columns(2)
        
        with col1:
            test_size = st.selectbox("Test Size:", [10, 50, 100, 500, 1000])
            test_platforms = st.multiselect(
                "Platforms to Test:", 
                ['whatsapp', 'email', 'slack', 'teams', 'instagram'],
                default=['whatsapp', 'email']
            )
        
        with col2:
            include_context = st.checkbox("Include Context Processing", value=True)
            show_progress = st.checkbox("Show Progress", value=True)
        
        if st.button("🏃‍♂️ Run Performance Test"):
            # Generate test messages
            import random
            
            test_messages = []
            sample_texts = [
                "Can you help me with this urgent issue?",
                "Thanks for your help yesterday!",
                "Meeting scheduled for tomorrow at 2 PM",
                "The system is not working properly",
                "Please review the attached document",
                "What time should we meet?",
                "FYI - server maintenance tonight",
                "Any updates on the project status?",
                "yo whats up? party tonight!",
                "love ur latest post! 😍 where did u get that dress?",
                "Hey, did the report get done?",
                "This is urgent - need response ASAP!"
            ]
            
            for i in range(test_size):
                platform = random.choice(test_platforms)
                text = random.choice(sample_texts)
                
                test_messages.append({
                    'user_id': f'test_user_{i % 20}',  # 20 different users
                    'platform': platform,
                    'message_text': f"{text} (Test message {i+1})",
                    'timestamp': (datetime.now() - timedelta(minutes=i)).isoformat(),
                    'message_id': f'perf_test_{i}'
                })
            
            # Run performance test
            import time
            
            start_time = time.time()
            
            if show_progress:
                progress_bar = st.progress(0)
                status_text = st.empty()
                
                results = []
                for i, message in enumerate(test_messages):
                    result = st.session_state.summarizer.summarize(message, use_context=include_context)
                    results.append(result)
                    
                    # Update progress
                    progress = (i + 1) / len(test_messages)
                    progress_bar.progress(progress)
                    status_text.text(f"Processing message {i+1}/{len(test_messages)}")
            else:
                with st.spinner("Running performance test..."):
                    results = st.session_state.summarizer.batch_summarize(test_messages, use_context=include_context)
            
            end_time = time.time()
            processing_time = end_time - start_time
            
            # Display results
            st.success("✅ Performance Test Complete!")
            
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                st.metric("Messages Processed", len(results))
            with col2:
                st.metric("Total Time", f"{processing_time:.2f}s")
            with col3:
                st.metric("Avg per Message", f"{processing_time/len(results)*1000:.1f}ms")
            with col4:
                st.metric("Messages/Second", f"{len(results)/processing_time:.1f}")
            
            # Performance breakdown
            st.subheader("📊 Performance Breakdown")
            
            # Calculate distributions from messages and results
            intent_counts = {}
            urgency_counts = {}
            type_counts = {}
            platform_counts = {}
            
            for result in results:
                intent_counts[result['intent']] = intent_counts.get(result['intent'], 0) + 1
                urgency_counts[result['urgency']] = urgency_counts.get(result['urgency'], 0) + 1
                type_counts[result['type']] = type_counts.get(result['type'], 0) + 1
            
            for message in test_messages:
                platform_counts[message['platform']] = platform_counts.get(message['platform'], 0) + 1
            
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                st.write("**Intent Distribution:**")
                for intent, count in intent_counts.items():
                    st.write(f"• {intent}: {count}")
            
            with col2:
                st.write("**Urgency Distribution:**")
                for urgency, count in urgency_counts.items():
                    st.write(f"• {urgency}: {count}")
            
            with col3:
                st.write("**Type Distribution:**")
                for msg_type, count in type_counts.items():
                    st.write(f"• {msg_type}: {count}")
            
            with col4:
                st.write("**Platform Distribution:**")
                for platform, count in platform_counts.items():
                    st.write(f"• {platform}: {count}")
            
            # Accuracy metrics
            st.subheader("📈 Accuracy Metrics")
            
            high_confidence = sum(1 for r in results if r['confidence'] > 0.7)
            context_usage = sum(1 for r in results if r['context_used'])
            
            col1, col2, col3 = st.columns(3)
            
            with col1:
                st.metric("High Confidence", f"{high_confidence/len(results):.1%}")
            with col2:
                st.metric("Context Usage", f"{context_usage/len(results):.1%}")
            with col3:
                avg_confidence = sum(r['confidence'] for r in results) / len(results)
                st.metric("Avg Confidence", f"{avg_confidence:.2f}")
            
            # Performance test analytics charts
            st.subheader("📊 Performance Test Analytics")
            fig_intent, fig_urgency, fig_platform, fig_types = create_analytics_charts(test_messages, results)
            
            if fig_intent:
                col1, col2 = st.columns(2)
                
                with col1:
                    st.plotly_chart(fig_intent, use_container_width=True)
                    st.plotly_chart(fig_platform, use_container_width=True)
                
                with col2:
                    st.plotly_chart(fig_urgency, use_container_width=True)
                    st.plotly_chart(fig_types, use_container_width=True)
    
    # Footer
    st.markdown("---")
    st.markdown("""
    <div style='text-align: center; color: #666;'>
        <p>🤖 SmartBrief v3 - Context-Aware Message Summarization</p>
        <p>Built with Streamlit • Powered by Advanced NLP • Enhanced with Feedback Loop</p>
        <p>Features: Multi-Platform Support • Context Awareness • Intent Detection • Urgency Analysis • Feedback Learning</p>
    </div>
    """, unsafe_allow_html=True)

if __name__ == "__main__":
    main()
