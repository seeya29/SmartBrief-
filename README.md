Smart Inbox Brief AI

Smart Inbox Brief AI is an intelligent email assistant that automatically fetches, summarizes, prioritizes, and analyzes emails. It uses Natural Language Processing (NLP), Sentiment Analysis, Reinforcement Learning, and Visualization tools to provide users with a concise and prioritized view of their inbox.

🚀 Features

Email Fetching & Setup: Securely fetches emails using stored credentials.

Summarization: Extracts concise summaries of long emails.

Priority Scoring: Ranks emails based on importance using a reinforcement learning model.

Sentiment Analysis: Detects the sentiment of incoming emails (positive, negative, neutral).

Smart Suggestions: Recommends actions and tags for incoming emails.

Interactive Dashboard: Streamlit-powered UI to view, search, and manage emails.

Smart Brief (Demo App): Lightweight demo (demo_streamlit_app.py) that showcases email briefing and summarization.

Feedback System: Users can provide feedback to improve prioritization and tagging.

Text-to-Speech (TTS): Converts important emails into speech for accessibility.

Visual Analytics: Graphical insights into email trends, priorities, and feedback.

📂 Project Structure
smart-inbox-ai2/
│── briefing.py              # Generates daily/weekly email briefs
│── context_loader.py        # Loads and manages email context
│── credentials_manager.py   # Handles secure email login credentials
│── dashboard.py             # Full-featured Streamlit dashboard
│── demo_streamlit_app.py    # Lightweight demo app for Smart Brief
│── email_agent.py           # Core email processing agent
│── email_reader.py          # Reads and preprocesses emails
│── email_summarizer.py      # Summarizes emails
│── feedback_system.py       # Manages user feedback
│── priority_model.py        # Priority scoring model with reinforcement learning
│── sentiment.py             # Sentiment analysis
│── smart_metrics.py         # Metrics and analytics
│── smart_suggestions.py     # Suggests tags/actions
│── smart_summarizer_v3.py   # Advanced summarizer
│── tts.py                   # Text-to-Speech engine
│── visualizations.py        # Generates insights & plots
│── main.py                  # Main entry point
│── requirements.txt         # Python dependencies
│── README.md                # Project documentation
│── *.json / *.csv           # Context, history, feedback storage

⚙️ Installation

Clone this repository:

git clone https://github.com/yourusername/smart-inbox-ai.git
cd smart-inbox-ai2


Install dependencies:

pip install -r requirements.txt


Setup email credentials (via credentials_manager.py).

▶️ Usage

Run the full dashboard:

streamlit run dashboard.py


Run the Smart Brief demo app:

streamlit run demo_streamlit_app.py


Run the core agent:

python main.py

📊 Example Output

Summarized Inbox with priority scores

Sentiment tags (😊 Positive | 😐 Neutral | 😞 Negative)

Feedback loop improving prioritization

Visual graphs of email trends

Demo app showing concise daily/weekly briefs

🧠 Tech Stack

Python (NLP, ML, RL)

Streamlit (Dashboard UI)

TextBlob / Custom NLP models (Sentiment & Summarization)

Matplotlib / Seaborn (Visualizations)

TTS Engine (Accessibility)

📌 Future Improvements

Multi-language summarization support

Gmail/Outlook API integration

Advanced reinforcement learning for personalization

Mobile-friendly dashboard

**SummaryFlow v3 API**
- File: `summaryflow_v3.py`
- Purpose: Classifies message `type`, `intent`, `urgency` and extracts entities.
- Usage:
  - Python: `from summaryflow_v3 import summarize_message`
  - Call with payload:
    - `{ "user_id": "abc123", "platform": "whatsapp", "message_id": "m001", "message_text": "Hey, please confirm tomorrow's 5 PM meeting with Priya.", "timestamp": "2025-11-20T14:00:00Z" }`
- Output structure:
  - `{ "summary_id": "s_...", "user_id": "abc123", "platform": "whatsapp", "message_id": "m001", "summary": "User wants confirmation for a 5 PM meeting with Priya tomorrow.", "type": "meeting", "intent": "confirm_meeting", "urgency": "medium", "entities": { "person": ["Priya"], "datetime": "2025-11-21T17:00:00Z" }, "generated_at": "2025-11-20T14:00:02Z" }`