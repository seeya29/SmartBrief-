import pandas as pd
import json
import os
from datetime import datetime, timedelta
import email
from email.header import decode_header
import imaplib
import ssl
from typing import List, Dict, Optional
import re
import logging

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class EmailReader:
    """Enhanced email reader with proper Gmail IMAP integration."""
    
    def __init__(self, use_mock=True):
        self.use_mock = use_mock
        self.imap_server = None
        self.connection = None
    
    def connect_imap(self, email_address: str, password: str, imap_server: str = None) -> bool:
        """Connect to IMAP server for live email reading with improved Gmail support."""
        try:
            # Auto-detect IMAP server if not provided
            if not imap_server:
                domain = email_address.split('@')[1].lower()
                if 'gmail' in domain:
                    imap_server = 'imap.gmail.com'
                elif 'outlook' in domain or 'hotmail' in domain or 'live' in domain:
                    imap_server = 'outlook.office365.com'
                elif 'yahoo' in domain:
                    imap_server = 'imap.mail.yahoo.com'
                else:
                    logger.warning(f"Unknown email provider for {domain}. Please specify IMAP server.")
                    return False
            
            logger.info(f"Attempting to connect to {imap_server} for {email_address}")
            
            # Create SSL context with proper settings
            context = ssl.create_default_context()
            
            # For Gmail, we might need to be less strict about SSL
            if 'gmail' in imap_server:
                context.check_hostname = False
                context.verify_mode = ssl.CERT_NONE
            
            # Connect to server with timeout
            self.connection = imaplib.IMAP4_SSL(imap_server, 993, ssl_context=context)
            self.connection.login(email_address, password)
            
            # Test connection by selecting INBOX
            status, message_count = self.connection.select('INBOX')
            if status == 'OK':
                logger.info(f"✅ Successfully connected to {imap_server}")
                logger.info(f"📧 Found {message_count[0].decode()} total messages")
                return True
            else:
                logger.error(f"❌ Failed to select INBOX: {status}")
                return False
            
        except imaplib.IMAP4.error as e:
            logger.error(f"❌ IMAP protocol error: {e}")
            logger.error("💡 For Gmail: Make sure you're using an App Password, not your regular password")
            logger.error("💡 Enable 2-Step Verification and generate an App Password at: https://myaccount.google.com/apppasswords")
            return False
        except Exception as e:
            logger.error(f"❌ IMAP connection failed: {e}")
            return False
    
    def fetch_live_emails(self, folder='INBOX', limit=50, search_criteria='ALL') -> List[Dict]:
        """Fetch emails from live IMAP connection with improved error handling."""
        if not self.connection:
            logger.error("❌ No IMAP connection established")
            return []
        
        try:
            # Select folder
            status, message_count = self.connection.select(folder)
            if status != 'OK':
                logger.error(f"❌ Failed to select folder {folder}: {message_count}")
                return []
            
            total_messages = int(message_count[0].decode())
            logger.info(f"📁 Selected folder {folder} with {total_messages} messages")
            
            # Search for emails with different strategies
            search_strategies = [
                ('UNSEEN', 'unread messages'),
                ('RECENT', 'recent messages'), 
                ('ALL', 'all messages')
            ]
            
            email_ids = []
            for criteria, description in search_strategies:
                try:
                    status, messages = self.connection.search(None, criteria)
                    if status == 'OK' and messages[0]:
                        email_ids = messages[0].split()
                        logger.info(f"📧 Found {len(email_ids)} {description}")
                        break
                except Exception as e:
                    logger.warning(f"⚠️ Search failed for {criteria}: {e}")
                    continue
            
            if not email_ids:
                logger.warning("📭 No emails found with any search criteria")
                return []
            
            # Get recent emails (limit) - take from the end for most recent
            if len(email_ids) > limit:
                recent_emails = email_ids[-limit:]
                logger.info(f"📧 Processing {limit} most recent emails")
            else:
                recent_emails = email_ids
                logger.info(f"📧 Processing all {len(recent_emails)} emails")
            
            emails = []
            failed_count = 0
            
            for i, email_id in enumerate(recent_emails):
                try:
                    logger.info(f"📥 Fetching email {i+1}/{len(recent_emails)} (ID: {email_id.decode()})")
                    
                    # Fetch email with proper flags
                    status, msg_data = self.connection.fetch(email_id, '(RFC822)')
                    
                    if status != 'OK' or not msg_data or not msg_data[0]:
                        logger.warning(f"⚠️ Failed to fetch email {email_id}: {status}")
                        failed_count += 1
                        continue
                        
                    email_body = msg_data[0][1]
                    if not email_body:
                        logger.warning(f"⚠️ Empty email body for {email_id}")
                        failed_count += 1
                        continue
                    
                    email_message = email.message_from_bytes(email_body)
                    
                    # Parse email with better error handling
                    parsed_email = self._parse_email_message(email_message, email_id.decode())
                    if parsed_email:
                        emails.append(parsed_email)
                        logger.info(f"✅ Successfully parsed: {parsed_email['subject'][:50]}...")
                    else:
                        failed_count += 1
                        
                except Exception as e:
                    logger.error(f"⚠️ Error processing email {email_id}: {e}")
                    failed_count += 1
                    continue
            
            logger.info(f"✅ Successfully fetched {len(emails)} emails from {folder}")
            if failed_count > 0:
                logger.warning(f"⚠️ Failed to process {failed_count} emails")
                
            return emails
            
        except Exception as e:
            logger.error(f"❌ Error fetching emails: {e}")
            return []
    
    def _parse_email_message(self, email_message, email_id: str) -> Optional[Dict]:
        """Parse email message object into structured data with better error handling."""
        try:
            # Get subject with proper decoding
            subject_header = email_message.get("Subject", "")
            subject = self._decode_header(subject_header) if subject_header else "No Subject"
            
            # Get sender with proper decoding
            from_header = email_message.get("From", "")
            sender = self._decode_header(from_header) if from_header else "Unknown Sender"
            
            # Extract just email address from sender if it contains name
            sender_email = self._extract_email_address(sender)
            
            # Get date
            date_str = email_message.get("Date", "")
            try:
                received_date = self._parse_date(date_str) if date_str else datetime.now()
            except Exception as e:
                logger.warning(f"Date parsing failed for {email_id}: {e}")
                received_date = datetime.now()
            
            # Get body with improved extraction
            body = self._extract_email_body(email_message)
            
            # Check for attachments
            has_attachments = self._has_attachments(email_message)
            has_image_attachments = self._check_image_attachments(email_message)
            
            # Get message ID for better tracking
            message_id = email_message.get("Message-ID", f"email_{email_id}")
            
            parsed_email = {
                'id': f"email_{email_id}",
                'message_id': message_id,
                'subject': subject,
                'sender': sender,
                'sender_email': sender_email,
                'body': body,
                'date': received_date.isoformat() if hasattr(received_date, 'isoformat') else str(received_date),
                'raw_date': date_str,
                'label': 'inbox',
                'has_attachments': has_attachments,
                'has_image_attachments': has_image_attachments,
                'word_count': len(body.split()) if body else 0,
                'to': self._decode_header(email_message.get("To", "")),
                'cc': self._decode_header(email_message.get("CC", "")),
                'folder': 'INBOX'
            }
            
            return parsed_email
            
        except Exception as e:
            logger.error(f"⚠️ Error parsing email message {email_id}: {e}")
            return None
    
    def _extract_email_address(self, sender_text: str) -> str:
        """Extract email address from sender string."""
        if not sender_text:
            return ""
        
        # Look for email in angle brackets
        email_match = re.search(r'<([^>]+)>', sender_text)
        if email_match:
            return email_match.group(1)
        
        # Look for standalone email
        email_match = re.search(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b', sender_text)
        if email_match:
            return email_match.group(0)
        
        return sender_text
    
    def _has_attachments(self, email_message) -> bool:
        """Check if email has any attachments."""
        if not email_message.is_multipart():
            return False
            
        for part in email_message.walk():
            disposition = part.get("Content-Disposition")
            if disposition and "attachment" in disposition:
                return True
                
        return False
    
    def _check_image_attachments(self, email_message) -> bool:
        """Check if email has image attachments."""
        if not email_message.is_multipart():
            return False
            
        for part in email_message.walk():
            content_type = part.get_content_type()
            if content_type and content_type.startswith('image/'):
                disposition = part.get("Content-Disposition")
                if disposition and "attachment" in disposition:
                    return True
                    
        return False
    
    def _decode_header(self, header) -> str:
        """Decode email header with improved error handling."""
        if not header:
            return ""
        
        try:
            decoded_parts = decode_header(header)
            decoded_string = ""
            
            for part, encoding in decoded_parts:
                if isinstance(part, bytes):
                    # Try different encodings
                    encodings_to_try = [encoding, 'utf-8', 'iso-8859-1', 'windows-1252']
                    for enc in encodings_to_try:
                        if enc:
                            try:
                                decoded_string += part.decode(enc)
                                break
                            except (UnicodeDecodeError, LookupError):
                                continue
                    else:
                        # If all encodings fail, use error handling
                        decoded_string += part.decode('utf-8', errors='replace')
                else:
                    decoded_string += str(part)
            
            return decoded_string.strip()
        except Exception as e:
            logger.warning(f"Header decode error: {e}")
            return str(header)
    
    def _parse_date(self, date_str: str) -> datetime:
        """Parse email date string with multiple format support."""
        try:
            from email.utils import parsedate_to_datetime
            return parsedate_to_datetime(date_str)
        except Exception as e:
            # Fallback parsing methods
            try:
                # Try common date formats
                formats = [
                    '%a, %d %b %Y %H:%M:%S %z',
                    '%d %b %Y %H:%M:%S %z',
                    '%a, %d %b %Y %H:%M:%S',
                    '%d %b %Y %H:%M:%S'
                ]
                
                for fmt in formats:
                    try:
                        return datetime.strptime(date_str, fmt)
                    except ValueError:
                        continue
                        
            except Exception:
                pass
            
            logger.warning(f"Could not parse date: {date_str}")
            return datetime.now()
    
    def _extract_email_body(self, email_message) -> str:
        """Extract text body from email message with improved handling."""
        body = ""
        
        try:
            if email_message.is_multipart():
                # Handle multipart messages
                for part in email_message.walk():
                    content_type = part.get_content_type()
                    content_disposition = str(part.get("Content-Disposition", ""))
                    
                    # Skip attachments
                    if "attachment" in content_disposition:
                        continue
                    
                    if content_type == "text/plain":
                        payload = part.get_payload(decode=True)
                        if payload:
                            charset = part.get_content_charset() or 'utf-8'
                            try:
                                body = payload.decode(charset)
                            except (UnicodeDecodeError, LookupError):
                                body = payload.decode('utf-8', errors='replace')
                        break
                    elif content_type == "text/html" and not body:
                        # Fallback to HTML if no plain text
                        payload = part.get_payload(decode=True)
                        if payload:
                            charset = part.get_content_charset() or 'utf-8'
                            try:
                                html_body = payload.decode(charset)
                            except (UnicodeDecodeError, LookupError):
                                html_body = payload.decode('utf-8', errors='replace')
                            body = self._strip_html(html_body)
            else:
                # Handle single part messages
                payload = email_message.get_payload(decode=True)
                if payload:
                    if isinstance(payload, bytes):
                        charset = email_message.get_content_charset() or 'utf-8'
                        try:
                            body = payload.decode(charset)
                        except (UnicodeDecodeError, LookupError):
                            body = payload.decode('utf-8', errors='replace')
                    else:
                        body = str(payload)
            
            # Clean up body
            body = self._clean_email_body(body)
            
        except Exception as e:
            logger.error(f"⚠️ Error extracting email body: {e}")
            body = f"Could not extract email body: {str(e)}"
        
        return body
    
    def _strip_html(self, html_text: str) -> str:
        """Remove HTML tags and entities."""
        import re
        
        # Remove HTML tags
        clean = re.compile('<.*?>')
        text = re.sub(clean, '', html_text)
        
        # Replace common HTML entities
        html_entities = {
            '&nbsp;': ' ',
            '&amp;': '&',
            '&lt;': '<',
            '&gt;': '>',
            '&quot;': '"',
            '&#39;': "'",
            '&hellip;': '...'
        }
        
        for entity, replacement in html_entities.items():
            text = text.replace(entity, replacement)
        
        return text
    
    def _clean_email_body(self, body: str) -> str:
        """Clean email body text."""
        if not body:
            return ""
        
        # Remove excessive whitespace
        body = re.sub(r'\n\s*\n', '\n\n', body)
        body = re.sub(r' +', ' ', body)
        body = re.sub(r'\t+', ' ', body)
        
        # Remove common email signatures and disclaimers
        patterns_to_remove = [
            r'--\s*\n.*$',  # Email signature
            r'From:.*?Subject:.*?\n',  # Forwarded email headers
            r'-----Original Message-----.*$',  # Outlook signatures
            r'This email.*confidential.*$',  # Confidentiality notices
        ]
        
        for pattern in patterns_to_remove:
            body = re.sub(pattern, '', body, flags=re.DOTALL | re.MULTILINE)
        
        # Limit length for processing
        if len(body) > 3000:
            body = body[:3000] + "... [truncated for processing]"
        
        return body.strip()
    
    def create_enhanced_mock_emails(self) -> List[Dict]:
        """Create enhanced mock emails with realistic content."""
        mock_emails = [
            # Work/Business Emails
            {
                'id': 'email_001',
                'subject': 'URGENT: Server Downtime Scheduled for Tonight',
                'sender': 'IT Operations <ops-team@company.com>',
                'sender_email': 'ops-team@company.com',
                'body': '''Hi Team,

We have scheduled emergency server maintenance tonight from 11 PM to 3 AM EST. 
Please complete all critical tasks by 10 PM. 

The following services will be affected:
- Email server
- File sharing system
- Development environment

Please plan accordingly. Contact me immediately if you have concerns.

Best regards,
Operations Team''',
                'date': (datetime.now() - timedelta(hours=2)).isoformat(),
                'label': 'work',
                'has_attachments': False,
                'has_image_attachments': False,
                'word_count': 45,
                'to': 'team@company.com',
                'cc': '',
                'folder': 'INBOX'
            },
            {
                'id': 'email_002',
                'subject': 'Weekly Team Meeting - Tomorrow 2 PM',
                'sender': 'Sarah Manager <sarah.manager@company.com>',
                'sender_email': 'sarah.manager@company.com',
                'body': '''Hello everyone,

Reminder about our weekly team meeting tomorrow at 2 PM in Conference Room B.

Agenda:
1. Project status updates
2. Q4 planning discussion
3. New team member introduction

Please bring your project reports. 

Thanks,
Sarah''',
                'date': (datetime.now() - timedelta(hours=5)).isoformat(),
                'label': 'meeting',
                'has_attachments': False,
                'has_image_attachments': False,
                'word_count': 32,
                'to': 'team@company.com',
                'cc': '',
                'folder': 'INBOX'
            },
            {
                'id': 'email_003',
                'subject': 'Invoice #12345 - Payment Due in 3 Days',
                'sender': 'Billing Department <billing@vendor.com>',
                'sender_email': 'billing@vendor.com',
                'body': '''Dear Customer,

This is a friendly reminder that Invoice #12345 for $2,450.00 is due in 3 days (March 15th).

Invoice Details:
- Amount: $2,450.00
- Due Date: March 15, 2024
- Payment Method: Bank transfer or credit card

Please process payment to avoid late fees.

Customer Service Team''',
                'date': (datetime.now() - timedelta(hours=8)).isoformat(),
                'label': 'financial',
                'has_attachments': True,
                'has_image_attachments': False,
                'word_count': 41,
                'to': 'customer@company.com',
                'cc': '',
                'folder': 'INBOX'
            },
            {
                'id': 'email_004',
                'subject': 'Security Alert: Unusual Login Activity',
                'sender': 'Security Team <security@company.com>',
                'sender_email': 'security@company.com',
                'body': '''SECURITY ALERT

We detected unusual login activity on your account:

- Login from: Unknown device
- Location: New York, NY  
- Time: Today at 3:47 AM
- IP: 192.168.1.100

If this was not you, please:
1. Change your password immediately
2. Contact IT support
3. Review your account activity

Security Team''',
                'date': (datetime.now() - timedelta(minutes=45)).isoformat(),
                'label': 'security',
                'has_attachments': False,
                'has_image_attachments': False,
                'word_count': 38,
                'to': 'user@company.com',
                'cc': 'it-support@company.com',
                'folder': 'INBOX'
            },
            {
                'id': 'email_005',
                'subject': '🎉 50% OFF Everything - Limited Time!',
                'sender': 'Online Store <deals@onlinestore.com>',
                'sender_email': 'deals@onlinestore.com',
                'body': '''🛍️ MEGA SALE ALERT! 🛍️

Get 50% OFF everything in our store this weekend only!

✅ Free shipping on orders over $50
✅ Extended return policy
✅ Exclusive member prices

Use code: SAVE50

Shop now before items sell out!

Happy Shopping!''',
                'date': (datetime.now() - timedelta(hours=12)).isoformat(),
                'label': 'promotional',
                'has_attachments': False,
                'has_image_attachments': True,
                'word_count': 28,
                'to': 'customer@email.com',
                'cc': '',
                'folder': 'INBOX'
            },
            {
                'id': 'email_006',
                'subject': 'Re: Project Alpha - Need Your Input ASAP',
                'sender': 'John Colleague <john.colleague@company.com>',
                'sender_email': 'john.colleague@company.com',
                'body': '''Hi,

Thanks for the project update. I reviewed the documents and have a few questions:

1. Can we move the deadline to next Friday?
2. Do we have budget for additional resources?
3. Who will handle the client presentation?

This is quite urgent as the client meeting is tomorrow. Please get back to me ASAP.

Thanks,
John''',
                'date': (datetime.now() - timedelta(hours=1)).isoformat(),
                'label': 'urgent',
                'has_attachments': False,
                'has_image_attachments': False,
                'word_count': 45,
                'to': 'user@company.com',
                'cc': '',
                'folder': 'INBOX'
            },
            {
                'id': 'email_007',
                'subject': 'Your Monthly Newsletter - Tech Trends',
                'sender': 'Tech Blog <newsletter@techblog.com>',
                'sender_email': 'newsletter@techblog.com',
                'body': '''📱 This Month in Technology

Top stories this month:
• AI developments in healthcare
• New smartphone releases
• Cybersecurity best practices

Read full articles on our website.

Unsubscribe | Update preferences

Tech Blog Team''',
                'date': (datetime.now() - timedelta(days=1)).isoformat(),
                'label': 'newsletter',
                'has_attachments': False,
                'has_image_attachments': False,
                'word_count': 25,
                'to': 'subscriber@email.com',
                'cc': '',
                'folder': 'INBOX'
            },
            {
                'id': 'email_008',
                'subject': 'Lunch meeting today - 12:30 PM',
                'sender': 'Important Client <client@importantcorp.com>',
                'sender_email': 'client@importantcorp.com',
                'body': '''Hi,

Looking forward to our lunch meeting today at 12:30 PM at The Blue Restaurant.

I'll bring the contract documents for review. Please confirm if you're still available.

Best regards,
Michael Chen
Important Corp''',
                'date': (datetime.now() - timedelta(minutes=30)).isoformat(),
                'label': 'meeting',
                'has_attachments': False,
                'has_image_attachments': False,
                'word_count': 30,
                'to': 'user@company.com',
                'cc': '',
                'folder': 'INBOX'
            },
            {
                'id': 'email_009',
                'subject': 'Project Screenshots for Review',
                'sender': 'Design Team <design-team@company.com>',
                'sender_email': 'design-team@company.com',
                'body': '''Hi Team,

I've attached the latest screenshots of our UI design for the new project. Please review them and provide feedback by tomorrow.

The images show the new dashboard layout and mobile responsive views.

Let me know what you think!

Best regards,
Design Team''',
                'date': (datetime.now() - timedelta(hours=1)).isoformat(),
                'label': 'work',
                'has_attachments': True,
                'has_image_attachments': True,
                'word_count': 35,
                'to': 'team@company.com',
                'cc': '',
                'folder': 'INBOX'
            }
        ]
        
        return mock_emails
    
    def load_emails(self, email_address=None, password=None, limit=50) -> pd.DataFrame:
        """Main method to load emails (mock or live) with proper error handling."""
        if self.use_mock:
            logger.info("📂 Loading mock emails...")
            emails = self.create_enhanced_mock_emails()
        else:
            if not email_address or not password:
                logger.error("❌ Email credentials required for live connection")
                logger.info("📂 Falling back to mock emails...")
                emails = self.create_enhanced_mock_emails()
            else:
                logger.info("📡 Connecting to live email...")
                if self.connect_imap(email_address, password):
                    emails = self.fetch_live_emails(limit=limit)
                    if not emails:
                        logger.warning("⚠️ No emails fetched, falling back to mock emails")
                        emails = self.create_enhanced_mock_emails()
                else:
                    logger.warning("⚠️ Connection failed, falling back to mock emails")
                    emails = self.create_enhanced_mock_emails()
        
        # Convert to DataFrame
        if emails:
            df = pd.DataFrame(emails)
            
            # Ensure all required columns exist
            required_columns = ['id', 'subject', 'sender', 'body', 'date', 'label']
            for col in required_columns:
                if col not in df.columns:
                    if col == 'date':
                        df[col] = datetime.now().isoformat()
                    elif col == 'label':
                        df[col] = 'general'
                    else:
                        df[col] = f'Unknown {col}'
            
            logger.info(f"✅ Successfully loaded {len(df)} emails")
            return df
        else:
            logger.warning("📭 No emails to load")
            return pd.DataFrame()
    
    def close_connection(self):
        """Close IMAP connection safely."""
        if self.connection:
            try:
                self.connection.close()
                self.connection.logout()
                logger.info("✅ IMAP connection closed successfully")
            except Exception as e:
                logger.warning(f"⚠️ Error closing connection: {e}")
            finally:
                self.connection = None

    def test_connection(self, email_address: str, password: str) -> Dict:
        """Test Gmail connection and return detailed status."""
        test_result = {
            'success': False,
            'message': '',
            'details': [],
            'suggestions': []
        }
        
        try:
            # Test connection
            if self.connect_imap(email_address, password):
                # Try to fetch a small number of emails to verify full functionality
                test_emails = self.fetch_live_emails(limit=5)
                
                if test_emails:
                    test_result['success'] = True
                    test_result['message'] = f'✅ Connection successful! Found {len(test_emails)} recent emails.'
                    test_result['details'] = [
                        f'Connected to Gmail for {email_address}',
                        f'Fetched {len(test_emails)} test emails',
                        'All systems working correctly'
                    ]
                else:
                    test_result['message'] = '⚠️ Connected but no emails found'
                    test_result['details'] = ['Connection established', 'No emails retrieved - inbox may be empty']
                    
                self.close_connection()
            else:
                test_result['message'] = '❌ Connection failed'
                test_result['suggestions'] = [
                    'Verify your email address and App Password',
                    'Make sure 2-Step Verification is enabled on your Google account',
                    'Generate a new App Password at: https://myaccount.google.com/apppasswords',
                    'Check if "Less secure app access" is turned off (use App Password instead)'
                ]
                
        except Exception as e:
            test_result['message'] = f'❌ Connection error: {str(e)}'
            test_result['suggestions'] = [
                'Check your internet connection',
                'Verify Gmail IMAP is enabled in your Gmail settings',
                'Try generating a new App Password'
            ]
        
        return test_result

# Usage examples
if __name__ == "__main__":
    # Mock usage
    reader = EmailReader(use_mock=True)
    mock_emails = reader.load_emails()
    print(f"Mock emails loaded: {len(mock_emails)}")
    
    # Live usage example (commented out)
    """
    reader = EmailReader(use_mock=False)
    live_emails = reader.load_emails(
        email_address="your-email@gmail.com",
        password="your-app-password",
        limit=5
    )
    reader.close_connection()
    """
