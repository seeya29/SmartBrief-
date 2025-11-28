from datetime import datetime

def generate_daily_brief(data, top_n=10):
    brief = []
    brief.append("=" * 50)
    brief.append(f"🤖 AI ASSISTANT - DAILY INBOX BRIEF")
    brief.append(f"📅 {datetime.now().strftime('%A, %B %d, %Y')}")
    brief.append("=" * 50)
    brief.append("")
    brief.append(f"📊 SUMMARY:")
    brief.append(f"   • Total messages: {len(data)}")
    brief.append(f"   • High priority: {len([x for x in data if 'HIGH' in x['priority_level']])}")
    brief.append(f"   • Unread: {len([x for x in data if x['read_status'] == 'unread'])}")
    brief.append("")

    brief.append(f"🔥 TOP {top_n} PRIORITY ITEMS:")
    brief.append("-" * 50)
    for i, item in enumerate(data[:top_n], 1):
        brief.append(f"{i}. {item['priority_level']} | {item['sender']}")
        brief.append(f"   📧 {item['subject']}")
        for point in item['key_points']:
            brief.append(f"      • {point}")
        # Handle timestamp as either string or datetime object
        timestamp = item['timestamp']
        if isinstance(timestamp, str):
            try:
                # Try to parse the string as datetime
                timestamp_obj = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
                timestamp_str = timestamp_obj.strftime('%m/%d %H:%M')
            except:
                # If parsing fails, use the string as is
                timestamp_str = str(timestamp)
        else:
            # If it's already a datetime object
            timestamp_str = timestamp.strftime('%m/%d %H:%M')
        
        brief.append(f"   ⏰ {timestamp_str} | Type: {item['message_type']}")
        brief.append("")
    
    return "\n".join(brief)
