---
title: Property Sentence Labeler
emoji: 🏷️
colorFrom: blue
colorTo: green
sdk: streamlit
sdk_version: 1.53.0
app_file: app.py
pinned: false
license: mit
---

# Property Sentence Labeler

A production-ready web application for labeling property-specific sentences with multi-user support, database persistence, and Google OAuth authentication.

## Features

- 🔐 Google OAuth authentication
- 👥 Multi-user support with isolated workspaces
- 💾 SQLite database for persistent storage
- 🎯 Word-level annotation (Subject/Property/Object)
- 📊 Real-time progress tracking
- 🔄 Auto-save functionality
- 📥 JSON export

## Usage

1. Login with your Google account
2. Select a property to label
3. Read sentences and assign labels
4. Mark specific words as Subject, Property, or Object
5. Navigate through sentences
6. Export your progress

## Configuration

This Space requires Google OAuth credentials to be configured in the Space settings.

### Required Secrets:

- `GOOGLE_CLIENT_ID`: Your Google OAuth Client ID
- `GOOGLE_CLIENT_SECRET`: Your Google OAuth Client Secret
- `GOOGLE_REDIRECT_URI`: Your Space URL (e.g., `https://huggingface.co/spaces/YOUR_USERNAME/YOUR_SPACE_NAME`)

### Database Storage:

Enable **persistent storage** in Space settings to preserve user data across restarts.

## Local Development

See the repository README for local setup instructions.
