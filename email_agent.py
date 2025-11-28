"""
Simple Email Agent for classification
This replaces the missing email_agent.py file with basic classification functionality.
"""

import re
from typing import Dict, List

class EmailAgent:
    """Simple email classification agent."""
    
    def __init__(self):
        self.categories = {
            'work': [
                'meeting', 'project', 'deadline', 'task', 'report', 'presentation',
                'client', 'colleague', 'manager', 'team', 'office', 'business'
            ],
            'personal': [
                'family', 'friend', 'birthday', 'vacation', 'weekend', 'dinner',
                'party', 'wedding', 'holiday', 'personal'
            ],
            'financial': [
                'invoice', 'payment', 'bill', 'receipt', 'transaction', 'bank',
                'credit', 'debit', 'purchase', 'order', 'refund', 'money'
            ],
            'promotional': [
                'sale', 'offer', 'discount', 'deal', 'promotion', 'coupon',
                'limited time', 'special offer', 'save', 'free', 'buy now'
            ],
            'newsletter': [
                'newsletter', 'weekly', 'monthly', 'digest', 'update', 'news',
                'blog', 'article', 'subscribe', 'unsubscribe'
            ],
            'security': [
                'security', 'password', 'login', 'verify', 'authentication',
                'suspicious', 'alert', 'breach', 'unauthorized', 'account'
            ],
            'urgent': [
                'urgent', 'asap', 'immediately', 'emergency', 'critical',
                'important', 'priority', 'deadline today', 'now'
            ]
        }
    
    def classify(self, text: str) -> str:
        """
        Classify email text into categories.
        
        Args:
            text (str): Email text to classify
            
        Returns:
            str: Category name
        """
        if not text:
            return 'general'
        
        text_lower = text.lower()
        category_scores = {}
        
        # Score each category based on keyword matches
        for category, keywords in self.categories.items():
            score = 0
            for keyword in keywords:
                if keyword in text_lower:
                    score += 1
            category_scores[category] = score
        
        # Return category with highest score, or 'general' if no matches
        if max(category_scores.values()) > 0:
            return max(category_scores, key=category_scores.get)
        else:
            return 'general'
    
    def get_confidence(self, text: str, category: str) -> float:
        """
        Get confidence score for a classification.
        
        Args:
            text (str): Email text
            category (str): Predicted category
            
        Returns:
            float: Confidence score between 0 and 1
        """
        if not text or category not in self.categories:
            return 0.0
        
        text_lower = text.lower()
        keywords = self.categories[category]
        matches = sum(1 for keyword in keywords if keyword in text_lower)
        
        # Simple confidence based on keyword density
        confidence = min(matches / len(keywords), 1.0)
        return confidence
    
    def extract_entities(self, text: str) -> Dict:
        """
        Extract basic entities from email text.
        
        Args:
            text (str): Email text
            
        Returns:
            dict: Extracted entities
        """
        entities = {
            'emails': [],
            'phones': [],
            'dates': [],
            'urls': [],
            'money': []
        }
        
        if not text:
            return entities
        
        # Email addresses
        email_pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
        entities['emails'] = re.findall(email_pattern, text)
        
        # Phone numbers (simple pattern)
        phone_pattern = r'\b\d{3}[-.]?\d{3}[-.]?\d{4}\b'
        entities['phones'] = re.findall(phone_pattern, text)
        
        # URLs
        url_pattern = r'http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\$$\$$,]|(?:%[0-9a-fA-F][0-9a-fA-F]))+'
        entities['urls'] = re.findall(url_pattern, text)
        
        # Money amounts
        money_pattern = r'\$\d+(?:,\d{3})*(?:\.\d{2})?'
        entities['money'] = re.findall(money_pattern, text)
        
        # Simple date patterns
        date_patterns = [
            r'\b\d{1,2}/\d{1,2}/\d{4}\b',  # MM/DD/YYYY
            r'\b\d{1,2}-\d{1,2}-\d{4}\b',  # MM-DD-YYYY
            r'\b\w+ \d{1,2}, \d{4}\b'      # Month DD, YYYY
        ]
        
        for pattern in date_patterns:
            entities['dates'].extend(re.findall(pattern, text))
        
        return entities
    
    def summarize(self, text: str, max_sentences: int = 3) -> str:
        """
        Create a simple summary of the email text.
        
        Args:
            text (str): Email text to summarize
            max_sentences (int): Maximum sentences in summary
            
        Returns:
            str: Summary text
        """
        if not text:
            return "No content to summarize."
        
        # Split into sentences
        sentences = re.split(r'[.!?]+', text)
        sentences = [s.strip() for s in sentences if s.strip()]
        
        if len(sentences) <= max_sentences:
            return '. '.join(sentences) + '.'
        
        # Simple scoring: prefer sentences with important keywords
        important_words = [
            'important', 'urgent', 'deadline', 'meeting', 'please',
            'need', 'required', 'asap', 'today', 'tomorrow'
        ]
        
        scored_sentences = []
        for sentence in sentences:
            score = len(sentence.split())  # Base score on length
            
            # Boost score for important keywords
            for word in important_words:
                if word.lower() in sentence.lower():
                    score += 10
            
            scored_sentences.append((sentence, score))
        
        # Sort by score and take top sentences
        scored_sentences.sort(key=lambda x: x[1], reverse=True)
        top_sentences = [s[0] for s in scored_sentences[:max_sentences]]
        
        return '. '.join(top_sentences) + '.'
