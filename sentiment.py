from textblob import TextBlob

def analyze_sentiment(text):
    """
    Analyze sentiment of text using TextBlob.
    
    Args:
        text: Input text to analyze
        
    Returns:
        float: Sentiment polarity score (-1 to 1)
    """
    blob = TextBlob(text)
    return round(blob.sentiment.polarity, 2)

def get_sentiment_label(polarity):
    """
    Convert polarity score to human-readable label.
    
    Args:
        polarity: Sentiment polarity score
        
    Returns:
        str: Sentiment label
    """
    if polarity > 0.1:
        return 'positive'
    elif polarity < -0.1:
        return 'negative'
    else:
        return 'neutral'

def analyze_sentiment_detailed(text):
    """
    Detailed sentiment analysis with polarity and subjectivity.
    
    Args:
        text: Input text to analyze
        
    Returns:
        dict: Detailed sentiment analysis
    """
    blob = TextBlob(text)
    polarity = round(blob.sentiment.polarity, 2)
    subjectivity = round(blob.sentiment.subjectivity, 2)
    
    return {
        'polarity': polarity,
        'subjectivity': subjectivity,
        'label': get_sentiment_label(polarity),
        'confidence': abs(polarity)
    }

# Example usage
if __name__ == "__main__":
    test_texts = [
        "I love this product! It's amazing!",
        "This is terrible. I hate it.",
        "The weather is okay today.",
        "Thanks for your help! Really appreciate it.",
        "The system is broken and not working properly."
    ]
    
    print("🔍 Sentiment Analysis Examples:")
    for text in test_texts:
        sentiment = analyze_sentiment_detailed(text)
        print(f"Text: {text}")
        print(f"Sentiment: {sentiment['label']} (polarity: {sentiment['polarity']}, confidence: {sentiment['confidence']})")
        print("---")
