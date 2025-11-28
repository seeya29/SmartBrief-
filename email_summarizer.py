import re
from typing import Dict, List

def clean_text_for_summary(text: str) -> str:
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

def extract_key_sentences(text: str, max_sentences: int = 3) -> List[str]:
    """Extract key sentences from email body."""
    if not text:
        return []
    
    # Clean the text
    clean_text = clean_text_for_summary(text)
    
    # Split into sentences
    sentences = re.split(r'[.!?]+', clean_text)
    sentences = [s.strip() for s in sentences if s.strip()]
    
    # Simple scoring based on length and keywords
    scored_sentences = []
    for sentence in sentences:
        score = 0
        # Longer sentences get higher scores
        score += len(sentence.split()) * 0.1
        # Sentences with important keywords get bonus
        important_words = ['urgent', 'important', 'deadline', 'meeting', 'please', 'need', 'must', 'should']
        for word in important_words:
            if word.lower() in sentence.lower():
                score += 2
        scored_sentences.append((sentence, score))
    
    # Sort by score and take top sentences
    scored_sentences.sort(key=lambda x: x[1], reverse=True)
    key_sentences = [s[0] for s in scored_sentences[:max_sentences]]
    
    return key_sentences

def generate_email_summary(email: Dict, max_length: int = 150) -> str:
    """Generate a concise summary of an email."""
    subject = email.get('subject', 'No Subject')
    body = email.get('body', '')
    
    # Clean and summarize body
    clean_body = clean_text_for_summary(body)
    
    if not clean_body:
        return f"Subject: {subject}"
    
    # Extract key sentences
    key_sentences = extract_key_sentences(clean_body, max_sentences=2)
    
    if key_sentences:
        summary = ' '.join(key_sentences)
        # Truncate if too long
        if len(summary) > max_length:
            summary = summary[:max_length-3] + "..."
        return summary
    else:
        # Fallback: take first few words
        words = clean_body.split()[:20]
        summary = ' '.join(words)
        if len(summary) > max_length:
            summary = summary[:max_length-3] + "..."
        return summary

def format_email_display(email: Dict) -> Dict:
    """Format email for display with proper subject and summary."""
    # Ensure subject exists
    subject = email.get('subject', '')
    if not subject or subject.strip() == '':
        # Generate a subject from the first few words of the body
        body = email.get('body', '')
        clean_body = clean_text_for_summary(body)
        words = clean_body.split()[:5]
        subject = ' '.join(words) if words else 'No Subject'
        email['subject'] = subject
    
    # Generate summary
    summary = generate_email_summary(email)
    email['summary'] = summary
    
    return email
