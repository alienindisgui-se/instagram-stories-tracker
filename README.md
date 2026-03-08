# Instagram Stories Tracker

![AI Assisted](https://img.shields.io/badge/AI%20Assisted-purple?style=for-the-badge)
![Python](https://img.shields.io/badge/python-3670A0?style=for-the-badge&logo=python&logoColor=ffdd54)
![Repo Size](https://img.shields.io/github/repo-size/alienindisgui-se/instagram-stories-tracker?style=for-the-badge&color=blue)
![License](https://img.shields.io/github/license/alienindisgui-se/instagram-stories-tracker?style=for-the-badge&color=green)

![CI](https://img.shields.io/github/actions/workflow/status/alienindisgui-se/instagram-stories-tracker/instagram-stories-tracker.yml?label=CI&logo=github&style=for-the-badge&color=0099FF) ![Every 6h](https://img.shields.io/badge/Schedule-Every%206h-blue?style=for-the-badge&logo=github)

A Python-based system for automated Instagram stories tracking with periodic monitoring, Discord webhook notifications, story media uploads, analytics tracking, and historical data management.

## 🚀 Features

- **📊 Periodic Monitoring**: Stories tracking every 6 hours with new story detection
- **🤖 Automated Execution**: GitHub Actions with scheduled runs and manual triggers
- **💬 Discord Notifications**: Batched embed reports with story media uploads and user statistics
- **📈 Analytics Tracking**: Total stories, daily counts, average per day, tracking days
- **🔒 Security-First**: Cloudflare bypass with cloudscraper, error handling, and retries
- **🔄 Historical Data**: JSON-based storage with automatic story ID tracking and deduplication
- **📱 API Integration**: Reliable data fetching using Instapeep API with mobile-like headers

## 🏗️ Architecture

```
instagram-stories-tracker/
├── scripts/
│   ├── instagram_stories_tracker.py     # Main tracker script
├── config/
│   ├── instagram_stories_config.json    # Usernames configuration
├── data/
│   ├── instagram_stories_history.json   # Historical story IDs
│   └── instagram_stories_analytics.json # User analytics data
├── requirements/
│   └── requirements-instagram.txt       # Python dependencies
└── .github/workflows/
    └── instagram-stories-tracker.yml    # GitHub Actions automation
```

## 🛠️ Setup Instructions

### Prerequisites

- Python 3.11+
- GitHub repository (for automation)
- Discord server (for notifications)

## ⚙️ Configuration

### Environment Variables

| Variable | Required | Description |
|----------|----------|-------------|
| `INSTAGRAM_STORIES_DISCORD_WEBHOOK` | Yes | Discord webhook URL for notifications |

### Configuration Files

#### `config/instagram_stories_config.json`
```json
{
  "usernames": [
    "username1",
    "username2"
  ]
}
```

#### `.env`
```env
INSTAGRAM_STORIES_DISCORD_WEBHOOK=https://discord.com/api/webhooks/your/webhook/id
```

## 📊 Data Structure

The system stores story data in JSON files:

#### `data/instagram_stories_history.json`
```json
{
  "username1": ["story_id1","story_id2"],
  "username2": ["story_id3"]
}
```

#### `data/instagram_stories_analytics.json`
```json
{
  "username1": {
    "total_stories": 150,
    "daily_counts": {"2026-03-08": 5},
    "first_seen": "2026-03-01",
    "last_seen": "2026-03-08"
  }
}
```

## 🤖 GitHub Actions Automation

### Scheduled Workflows

| Workflow | Schedule | Description |
|----------|----------|-------------|
| Stories Tracker | `0 0,6,12,18 * * *` | Runs every 6 hours at 00:00, 06:00, 12:00, 18:00 UTC |

### Required GitHub Secrets

1. **INSTAGRAM_STORIES_DISCORD_WEBHOOK**: Discord webhook URL
2. **GITHUB_TOKEN**: Automatically provided by GitHub Actions

### Manual Execution

The workflow supports manual triggering via the GitHub Actions UI.

## 💬 Discord Integration

### Notification Format

The system sends rich embed notifications with:

- **Title**: New Stories from @{username}
- **Color**: Blue (`0x5814783`)
- **Content**: Number of new stories, user stats
- **Attachments**: Story media files (images/videos)

### Example Notification

```
📸 Instagram New Stories from @username

Found 3 new stories

[attached media]

User Report: 150 total stories | 5.0 avg/day | 30 days tracked
```

## 🔒 Security Considerations

### Rate Limiting

- **Request retries**: Up to 3 attempts with delays
- **Cloudflare bypass**: Uses cloudscraper for anti-bot measures
- **Error handling**: Graceful failures and logging

### API Security

- **Instapeep API**: Third-party API for story fetching
- **User-Agent**: Browser simulation
- **Headers**: Proper HTTP headers for requests

## 📱 API Method

The system uses Instapeep API endpoint:

```
https://instapeep.com/api/stories/{username}
```

With cloudscraper for requests.

## 🚀 Usage

### Manual Execution

```bash
python scripts/instagram_stories_tracker.py
```

## 🔧 Troubleshooting

### Common Issues

#### "Configuration file not found"
- Ensure `config/instagram_stories_config.json` exists
- Check file path and permissions

#### "Discord webhook returned non-204 status"
- Verify webhook URL is correct
- Check Discord server permissions

#### "Failed to fetch data"
- Check username spelling
- Verify accounts have stories
- Check network connectivity

#### "Media upload failed"
- Check file size (8MB limit)
- Verify Discord permissions

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

---

**Note**: This tool is for educational and monitoring purposes only. Ensure compliance with Instagram's Terms of Service when using this system.
