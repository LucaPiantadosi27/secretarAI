#!/usr/bin/env python3
"""Test script to verify Google Calendar API access."""

import os
import sys
from datetime import datetime, timedelta

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from src.integrations.google_client import GoogleWorkspaceClient

def test_calendar_access():
    """Test direct access to Google Calendar."""
    print("=" * 60)
    print("Google Calendar Access Test")
    print("=" * 60)
    
    try:
        # Initialize client
        print("\n1. Initializing Google Workspace Client...")
        client = GoogleWorkspaceClient()
        print("   ✓ Client initialized")
        
        # Check if service_calendar exists
        print("\n2. Checking calendar service...")
        if client.service_calendar is None:
            print("   ✗ FAILED: service_calendar is None")
            print("   This means authentication didn't include calendar scope")
            return False
        print("   ✓ Calendar service is available")
        
        # Check credentials
        print("\n3. Checking credentials...")
        if client.creds is None:
            print("   ✗ FAILED: No credentials found")
            return False
        print(f"   ✓ Credentials valid: {client.creds.valid}")
        print(f"   ✓ Credentials expired: {client.creds.expired}")
        if hasattr(client.creds, 'scopes'):
            print(f"   ✓ Scopes: {client.creds.scopes}")
        
        # Try to list calendars
        print("\n4. Listing available calendars...")
        try:
            calendar_list = client.service_calendar.calendarList().list().execute()
            calendars = calendar_list.get('items', [])
            print(f"   ✓ Found {len(calendars)} calendar(s)")
            for cal in calendars:
                print(f"     - {cal.get('summary')} (ID: {cal.get('id')})")
        except Exception as e:
            print(f"   ✗ Failed to list calendars: {e}")
            return False
        
        # Try to get events from primary calendar
        print("\n5. Fetching events from primary calendar...")
        try:
            now = datetime.utcnow().isoformat() + 'Z'
            time_max = (datetime.utcnow() + timedelta(days=30)).isoformat() + 'Z'
            
            events_result = client.service_calendar.events().list(
                calendarId='primary',
                timeMin=now,
                timeMax=time_max,
                maxResults=10,
                singleEvents=True,
                orderBy='startTime'
            ).execute()
            
            events = events_result.get('items', [])
            print(f"   ✓ Found {len(events)} event(s) in the next 30 days")
            
            if events:
                print("\n   Events:")
                for event in events:
                    start = event['start'].get('dateTime', event['start'].get('date'))
                    summary = event.get('summary', 'No title')
                    print(f"     - {start}: {summary}")
            else:
                print("   ℹ No events found in the next 30 days")
                print("   This is normal if your calendar is empty")
        
        except Exception as e:
            print(f"   ✗ Failed to fetch events: {e}")
            print(f"   Error type: {type(e).__name__}")
            import traceback
            traceback.print_exc()
            return False
        
        # Test the list_calendar_events method
        print("\n6. Testing list_calendar_events method...")
        try:
            result = client.list_calendar_events(days=7)
            print(f"   ✓ Method returned: {result[:100]}...")
        except Exception as e:
            print(f"   ✗ Method failed: {e}")
            return False
        
        print("\n" + "=" * 60)
        print("✓ ALL TESTS PASSED - Calendar access is working!")
        print("=" * 60)
        return True
        
    except Exception as e:
        print(f"\n✗ FATAL ERROR: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_calendar_access()
    sys.exit(0 if success else 1)
