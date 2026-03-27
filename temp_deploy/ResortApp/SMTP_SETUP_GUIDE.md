# SMTP Email Configuration Guide

## Overview
The Resort Management System automatically sends booking confirmation emails when bookings are created. To enable this feature, you must configure SMTP settings in your `.env` or `.env.production` file.

## Quick Setup

### Step 1: Choose Your Email Provider

#### Option A: Gmail (Recommended for Testing)
1. **Enable 2-Step Verification:**
   - Go to https://myaccount.google.com/security
   - Enable "2-Step Verification"

2. **Generate App Password:**
   - Go to https://myaccount.google.com/apppasswords
   - Select "Mail" and "Other (Custom name)"
   - Enter "Resort Management System"
   - Copy the 16-character password (no spaces)

3. **Configure .env:**
```bash
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=your-email@gmail.com
SMTP_PASSWORD=xxxx xxxx xxxx xxxx  # Your 16-char app password
SMTP_FROM_EMAIL=noreply@elysianretreat.com
SMTP_FROM_NAME=Elysian Retreat
SMTP_USE_TLS=true
```

#### Option B: Custom SMTP Server
```bash
SMTP_HOST=smtp.yourdomain.com
SMTP_PORT=587
SMTP_USER=your-username
SMTP_PASSWORD=your-password
SMTP_FROM_EMAIL=noreply@yourdomain.com
SMTP_FROM_NAME=Your Resort Name
SMTP_USE_TLS=true
```

### Step 2: Add to Environment File

**On Production Server:**
```bash
cd /var/www/resort/Resort_first/ResortApp

# Edit .env.production (or create if it doesn't exist)
sudo nano .env.production
```

Add the SMTP configuration:
```bash
# SMTP Email Configuration
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=your-email@gmail.com
SMTP_PASSWORD=your-app-password
SMTP_FROM_EMAIL=noreply@elysianretreat.com
SMTP_FROM_NAME=Elysian Retreat
SMTP_USE_TLS=true
```

**For Local Development:**
```bash
cd ResortApp
# Copy .env.example to .env
cp .env.example .env
# Edit .env and add SMTP settings
nano .env
```

### Step 3: Restart Backend Service

```bash
sudo systemctl restart resort.service
# OR
sudo systemctl restart resort-backend.service

# Verify it's running
sudo systemctl status resort.service
```

### Step 4: Test Email Sending

1. Create a test booking through the dashboard
2. Check the guest's email inbox
3. Check backend logs for email sending status:
```bash
sudo journalctl -u resort.service -n 50 --no-pager | grep -i email
```

## Common SMTP Providers

### Gmail
```bash
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USE_TLS=true
```

### Outlook/Hotmail
```bash
SMTP_HOST=smtp-mail.outlook.com
SMTP_PORT=587
SMTP_USE_TLS=true
```

### Yahoo
```bash
SMTP_HOST=smtp.mail.yahoo.com
SMTP_PORT=587
SMTP_USE_TLS=true
```

### Custom SMTP (SendGrid, Mailgun, etc.)
```bash
SMTP_HOST=smtp.sendgrid.net
SMTP_PORT=587
SMTP_USER=apikey
SMTP_PASSWORD=your-api-key
SMTP_USE_TLS=true
```

## Troubleshooting

### Email Not Sending

1. **Check Environment Variables:**
```bash
cd /var/www/resort/Resort_first/ResortApp
cat .env.production | grep SMTP
```

2. **Check Backend Logs:**
```bash
sudo journalctl -u resort.service -n 100 | grep -i "email\|smtp"
```

3. **Verify SMTP Configuration:**
   - Ensure `SMTP_USER` and `SMTP_PASSWORD` are set
   - For Gmail, use App Password (not regular password)
   - Check firewall allows outbound SMTP traffic (port 587)

4. **Test SMTP Connection:**
```python
# Test script (run in Python shell)
import smtplib
from email.mime.text import MIMEText

smtp_host = 'smtp.gmail.com'
smtp_port = 587
username = 'your-email@gmail.com'
password = 'your-app-password'

try:
    server = smtplib.SMTP(smtp_host, smtp_port)
    server.starttls()
    server.login(username, password)
    print("✅ SMTP connection successful!")
    server.quit()
except Exception as e:
    print(f"❌ SMTP connection failed: {e}")
```

### Common Errors

**"SMTP not configured"**
- Solution: Add SMTP settings to `.env.production`

**"Authentication failed"**
- Solution: Use App Password for Gmail (not regular password)
- Solution: Verify username and password are correct

**"Connection refused"**
- Solution: Check firewall allows port 587
- Solution: Verify SMTP host and port are correct

**"Email sent but not received"**
- Solution: Check spam/junk folder
- Solution: Verify recipient email address is correct
- Solution: Check SMTP provider's sending limits

## Security Best Practices

1. **Never commit .env files to Git** (already in .gitignore)
2. **Use App Passwords** instead of main account passwords
3. **Restrict file permissions:**
   ```bash
   sudo chmod 600 /var/www/resort/Resort_first/ResortApp/.env.production
   sudo chown www-data:www-data /var/www/resort/Resort_first/ResortApp/.env.production
   ```
4. **Use environment-specific configurations** (.env for dev, .env.production for prod)

## Email Template Preview

When a booking is created, guests receive an email with:
- ✅ Formatted Booking ID (BK-000001 or PK-000001)
- ✅ Guest name and mobile
- ✅ Room numbers and types
- ✅ Check-in and check-out dates
- ✅ Stay duration (nights)
- ✅ Room charges breakdown
- ✅ Tax (5%)
- ✅ Grand Total
- ✅ Important resort information

## Notes

- ✅ Email sending is **automatic** when booking is created
- ✅ Email failures are **logged but don't prevent booking creation**
- ✅ Works for both **regular** and **package** bookings
- ✅ Email includes **all booking details** in professional HTML format

