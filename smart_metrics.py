import re
import emoji

# Note: spacy is optional - will fallback to regex if not available
try:
    import spacy
    nlp = spacy.load("en_core_web_sm")
    USE_SPACY = True
except (ImportError, OSError):
    print("spaCy model not found. Using regex-based fallback.")
    USE_SPACY = False


def detect_emoji_sentiment(text):
    """
    Returns sentiment based on emoji presence.
    
    Args:
        text (str): Text to analyze
        
    Returns:
        str: 'positive', 'negative', 'neutral', or 'none'
    """
    if not text:
        return "none"
        
    # Check if any emojis are present
    has_emoji = False
    for char in text:
        if char in emoji.EMOJI_DATA:
            has_emoji = True
            break
    
    if not has_emoji:
        return "none"
    
    # Positive emojis
    positive_emojis = ["😃", "😊", "👍", "🎉", "❤️", "😍", "🔥", "✅", "💯", "🚀"]
    if any(emo in text for emo in positive_emojis):
        return "positive"
    
    # Negative emojis
    negative_emojis = ["😢", "😡", "👎", "😞", "😠", "💔", "😰", "😨", "❌", "⚠️"]
    if any(emo in text for emo in negative_emojis):
        return "negative"
    
    # If has emojis but none specifically positive/negative
    return "neutral"


def detect_deadline(text):
    """
    Extracts time-based urgency phrases from text.
    
    Args:
        text (str): Text to analyze
        
    Returns:
        list or None: List of deadline phrases found, or None if none found
    """
    if not text:
        return None
        
    # Extended regex patterns for deadline detection
    deadline_patterns = [
        r"by [\w\s]{1,20}",
        r"before [\w\s]{1,20}", 
        r"due [\w\s]{1,20}",
        r"deadline [\w\s]{1,20}",
        r"until [\w\s]{1,20}",
        r"by end of [\w\s]{1,20}",
        r"no later than [\w\s]{1,20}",
        r"asap",
        r"immediately",
        r"urgent",
        r"today",
        r"tomorrow",
        r"this week",
        r"next week",
        r"eod",  # end of day
        r"cob",  # close of business
    ]
    
    time_phrases = []
    lower_text = text.lower()
    
    for pattern in deadline_patterns:
        matches = re.findall(pattern, lower_text)
        time_phrases.extend(matches)
    
    return time_phrases if time_phrases else None


def detect_intent(text):
    """
    Classifies intent of the email based on keywords and patterns.
    
    Args:
        text (str): Text to analyze
        
    Returns:
        str: Intent category
    """
    if not text:
        return "general"
        
    lower_text = text.lower()
    
    # Task/Action requests
    task_keywords = [
        "please do", "complete", "submit", "send", "provide", 
        "deliver", "finish", "prepare", "review", "approve",
        "sign", "fill out", "update", "create", "make"
    ]
    if any(word in lower_text for word in task_keywords):
        return "task"
    
    # Questions/Requests
    question_keywords = [
        "can you", "could you", "would you", "will you", 
        "please", "request", "need", "require", "ask"
    ]
    question_patterns = [r"\?", r"how to", r"what is", r"when", r"where", r"why"]
    if (any(word in lower_text for word in question_keywords) or 
        any(re.search(pattern, lower_text) for pattern in question_patterns)):
        return "request"
    
    # Updates/Information sharing
    update_keywords = [
        "update", "news", "announcement", "information", "fyi", 
        "heads up", "notice", "alert", "status", "progress"
    ]
    if any(word in lower_text for word in update_keywords):
        return "update"
    
    # Reminders
    reminder_keywords = [
        "reminder", "don't forget", "remember", "upcoming", 
        "scheduled", "due", "deadline", "meeting"
    ]
    if any(word in lower_text for word in reminder_keywords):
        return "reminder"
    
    # Invitations/Events
    invitation_keywords = [
        "invited", "invitation", "join", "attend", "event", 
        "meeting", "webinar", "conference", "party"
    ]
    if any(word in lower_text for word in invitation_keywords):
        return "invitation"
    
    # Confirmations
    confirmation_keywords = [
        "confirm", "confirmation", "verified", "received", 
        "acknowledged", "approved", "accepted"
    ]
    if any(word in lower_text for word in confirmation_keywords):
        return "confirmation"
    
    # Complaints/Issues
    complaint_keywords = [
        "problem", "issue", "error", "wrong", "mistake", 
        "complaint", "dissatisfied", "unhappy", "bug"
    ]
    if any(word in lower_text for word in complaint_keywords):
        return "complaint"
    
    return "general"


def detect_urgency_level(text):
    """
    Determines urgency level of the email.
    
    Args:
        text (str): Text to analyze
        
    Returns:
        str: 'high', 'medium', or 'low'
    """
    if not text:
        return "low"
        
    lower_text = text.lower()
    
    # High urgency indicators
    high_urgency = [
        "urgent", "asap", "immediately", "emergency", "critical",
        "important", "priority", "rush", "deadline", "today"
    ]
    if any(word in lower_text for word in high_urgency):
        return "high"
    
    # Medium urgency indicators  
    medium_urgency = [
        "soon", "tomorrow", "this week", "please", "need", 
        "required", "meeting", "deadline"
    ]
    if any(word in lower_text for word in medium_urgency):
        return "medium"
    
    return "low"


def extract_email_metrics(text):
    """
    Extract all metrics from email text.
    
    Args:
        text (str): Email text to analyze
        
    Returns:
        dict: Dictionary containing all extracted metrics
    """
    return {
        "intent": detect_intent(text),
        "urgency": detect_urgency_level(text),
        "deadlines": detect_deadline(text),
        "emoji_sentiment": detect_emoji_sentiment(text),
        "has_deadline": detect_deadline(text) is not None,
        "word_count": len(text.split()) if text else 0,
        "char_count": len(text) if text else 0
    }


# Example usage and testing
if __name__ == "__main__":
    test_emails = [
        "Please submit the report by tomorrow! 😃",
        "Can you help me with this urgent issue ASAP?",
        "Meeting reminder: Don't forget about our 3 PM meeting today",
        "FYI: The project status has been updated 📊",
        "I have a complaint about the service quality 😡"
    ]
    
    print("Testing email metrics extraction:")
    print("=" * 50)
    
    for i, email in enumerate(test_emails, 1):
        print(f"\nEmail {i}: {email}")
        metrics = extract_email_metrics(email)
        for key, value in metrics.items():
            print(f"  {key}: {value}")
        print("-" * 30)
