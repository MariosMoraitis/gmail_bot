# Gmail Automation Bot

Automatically delete old emails from specified senders in your Gmail inbox. This bot runs on a schedule and displays activity via a web dashboard.

## Features

- 🗑️ **Auto-delete old emails** - Removes emails older than 5 days from configured senders
- 📊 **Web Dashboard** - Monitor bot activity and connection status in real-time
- 🔄 **Scheduled runs** - Runs daily to keep your inbox clean
- 🐳 **Docker ready** - Easy deployment with Docker Compose
- **Coming Soon** - More functions on the way, feel free to make suggestion and collaborate!

## Quick Start

### Prerequisites

- Docker & Docker Compose
- Gmail account with [2-factor authentication enabled](https://myaccount.google.com/security)
- [Gmail App Password](https://myaccount.google.com/apppasswords)

### Installation

1. Clone the repository:
```bash
git clone <repo-url>
cd gmail_automation
```

2. Create `.env` file with your Gmail credentials:
```bash
echo "EMAIL=your-email@gmail.com" > .env
echo "PASSWORD=your-app-password" >> .env
```

3. Create `senders.json` with email addresses to monitor:
```json
{
    "to_be_deleted": [
        "newsletter@example.com",
        "promo@shop.com",
        "noreply@service.com"
    ]
}
```

4. Initialize other files:
```bash
echo '{"connected": false, "timestamp": ""}' > status.json
touch log.txt
```

5. Start the bot:
```bash
docker compose up -d --build
```

Access the dashboard at `http://localhost:5002`

## Linux Server Setup (or on Windows with WSL 😉)

On a Linux server with Docker installed:

```bash
git clone <repo-url>
cd gmail_automation

# Create config files
nano .env              # Add EMAIL and PASSWORD
nano senders.json      # Add email list
echo '{"connected": false, "timestamp": ""}' > status.json
touch log.txt

# Start bot
docker compose up -d --build

# View logs
docker compose logs -f gmail_scheduler
```

Update `docker-compose.yml` to use `.env` instead of `/etc/bot/.env` if needed.

## Architecture

- **scheduler.py** - Runs deletion task on schedule
- **bot.py** - Connects to Gmail and deletes old emails
- **app.py** - Flask web server for dashboard
- **templates/index.html** - Dashboard UI

## Configuration

### Email Delete Schedule

Edit `scheduler.py` to change frequency:

```python
schedule.every().day.do(run_delete_old_emails)      # Daily
schedule.every(6).hours.do(run_delete_old_emails)   # Every 6 hours
schedule.every(1).minutes.do(run_delete_old_emails) # Every minute (testing)
```

### Delete Threshold

Change age in `bot.py`:
```python
cutoff_date = datetime.now(timezone.utc) - timedelta(days=5)  # Change 5 to desired days
```

## Environment Variables

| Variable | Description |
|----------|-------------|
| `EMAIL` | Your Gmail address |
| `PASSWORD` | Your Gmail App Password (not your regular password) |

## Security

- ✅ App password stored in `.env` (not committed)
- ✅ Credentials not logged
- ✅ IMAP over SSL/TLS
- ✅ Senders list customizable
- ⚠  Suggestion, move `.env` at a new directory under `\etc`, so only `sudo` users can access it (see `docker-compose.yml` for configuration!)

## Troubleshooting

### Not connected to Gmail
- Verify EMAIL and PASSWORD in `.env`
- Enable 2FA and use App Password (not regular password)
- Check `docker compose logs gmail_scheduler`

### Docker issues
```bash
docker compose down
docker system prune -f
docker compose up -d --build
```

## License

MIT