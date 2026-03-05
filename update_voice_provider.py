#!/usr/bin/env python3
"""Script to update VOICE_PROVIDER in .env file to use Gemini."""

import os
import re

env_path = ".env"

if not os.path.exists(env_path):
    print(f"Error: {env_path} not found!")
    exit(1)

# Read the file
with open(env_path, 'r', encoding='utf-8') as f:
    content = f.read()

# Replace VOICE_PROVIDER value
# Match: VOICE_PROVIDER="whisper" or VOICE_PROVIDER="gemini" or VOICE_PROVIDER=whisper
updated_content = re.sub(
    r'VOICE_PROVIDER\s*=\s*["\']?whisper["\']?',
    'VOICE_PROVIDER="gemini"',
    content,
    flags=re.IGNORECASE
)

# If no match found, it might be missing or commented, add it
if updated_content == content:
    print("VOICE_PROVIDER not found or already set to gemini. Adding/updating...")
    # Check if it exists but is commented
    if re.search(r'#\s*VOICE_PROVIDER', content):
        updated_content = re.sub(
            r'#\s*VOICE_PROVIDER\s*=.*',
            'VOICE_PROVIDER="gemini"',
            content
        )
    else:
        # Add it in the Voice Transcription section
        if "# ========== Voice Transcription ==========" in content:
            updated_content = re.sub(
                r'(# ========== Voice Transcription ==========\s*\n)',
                r'\1VOICE_PROVIDER="gemini"\n',
                content
            )
        else:
            # Append at the end
            updated_content = content + '\nVOICE_PROVIDER="gemini"\n'

# Write back
with open(env_path, 'w', encoding='utf-8') as f:
    f.write(updated_content)

print("✓ Updated VOICE_PROVIDER to 'gemini' in .env")
print("✓ Restart the bot for changes to take effect")
