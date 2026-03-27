# Email Configuration Guide

This application automatically sends booking confirmation emails to guests after successful bookings (room bookings and package bookings).

## SMTP Configuration

To enable email sending, configure the following environment variables in your `.env` file or environment:

### Required Environment Variables

```bash
# SMTP Server Configuration
SMTP_HOST=smtp.gmail.com          # Your SMTP server (Gmail, Outlook, etc.)
SMTP_PORT=587                     # SMTP port (587 for TLS, 465 for SSL)
SMTP_USER=your-email@gmail.com    # Your SMTP username/email
SMTP_PASSWORD=your-app-password   # Your SMTP password or app password
SMTP_USE_TLS=true                 # Use TLS (true) or SSL (false)

# Email Settings (Optional)
SMTP_FROM_EMAIL=noreply@elysianretreat.com  # Sender email address
SMTP_FROM_NAME=Elysian Retreat              # Sender display name
```

## Gmail Configuration

If using Gmail:

1. **Enable 2-Factor Authentication** on your Google account
2. **Generate an App Password**:
   - Go to: https://myaccount.google.com/apppasswords
   - Select "Mail" and "Other (Custom name)"
   - Generate the password
   - Use this app password as `SMTP_PASSWORD`

3. **Configuration**:
   ```bash
   SMTP_HOST=smtp.gmail.com
   SMTP_PORT=587
   SMTP_USER=your-email@gmail.com
   SMTP_PASSWORD=your-16-char-app-password
   SMTP_USE_TLS=true
   ```

## Outlook/Hotmail Configuration

```bash
SMTP_HOST=smtp-mail.outlook.com
SMTP_PORT=587
SMTP_USER=your-email@outlook.com
SMTP_PASSWORD=your-password
SMTP_USE_TLS=true
```

## Testing Email Configuration

After configuration:

1. Restart your application
2. Make a test booking through the userend
3. Check the application logs for email sending status
4. Verify that the confirmation email is received

## Troubleshooting

### Email Not Sending

1. **Check Logs**: Look for `[Email]` messages in application logs
2. **Verify Credentials**: Ensure SMTP_USER and SMTP_PASSWORD are correct
3. **Check Firewall**: Ensure SMTP port (587 or 465) is not blocked
4. **Test SMTP Connection**: Try sending a test email manually

### Email Configuration Not Set

If SMTP is not configured, the application will:
- Continue to function normally
- Log email attempts but not send them
- Not throw errors that would break bookings

## Production Deployment

For production:

1. Set environment variables in your deployment environment
2. Use a production email service (SendGrid, Mailgun, AWS SES, etc.)
3. Ensure proper security for email credentials
4. Monitor email delivery rates

## Email Template

The booking confirmation email includes:
- Guest name
- Booking confirmation number
- Check-in and check-out dates
- Room details
- Important information about the stay
- Contact information

Email templates are HTML-formatted and responsive for both desktop and mobile viewing.

