import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import logging
from config.settings import settings

logger = logging.getLogger(__name__)

class EmailService:
    def __init__(self):
        # In a real app, these would come from settings. 
        # Using dummy structure for the example implementation to avoid crashes.
        self.smtp_server = getattr(settings, 'smtp_server', 'smtp.gmail.com')
        self.smtp_port = getattr(settings, 'smtp_port', 587)
        self.smtp_username = getattr(settings, 'smtp_username', 'hr@example.com')
        self.smtp_password = getattr(settings, 'smtp_password', 'dummy_password')

    def send_shortlist_email(
        self, 
        candidate_name: str, 
        candidate_email: str, 
        job_title: str,
        hr_email: str = None,
        hr_app_password: str = None
    ):
        """Sends an email to a shortlisted candidate using specific or global credentials."""
        
        # Use specific HR credentials if provided, otherwise fallback to global ENV
        sender_email = hr_email or self.smtp_username
        sender_password = hr_app_password or self.smtp_password
        
        if not candidate_email or candidate_email == "Unknown":
            logger.warning(f"Cannot send email to {candidate_name}: target Email address missing.")
            return False
            
        subject = f"Interview Invitation: {job_title} at ExampleCorp"
        
        html_body = f"""
        <html>
            <body style="font-family: Arial, sans-serif; color: #333; line-height: 1.6;">
                <h2 style="color: #2563eb;">Congratulations, {candidate_name}!</h2>
                <p>We are thrilled to let you know that your resume has been shortlisted for the <strong>{job_title}</strong> position.</p>
                <p>Our recruitment team reviewed your profile and was very impressed with your background and skills.</p>
                <p>A recruiter will reach out to you shortly to schedule the next steps, including a brief introductory call with the hiring manager.</p>
                <br/>
                <p>Best regards,</p>
                <p><strong>The Talent Acquisition Team</strong><br/>ExampleCorp</p>
            </body>
        </html>
        """
        
        msg = MIMEMultipart()
        msg['From'] = sender_email
        msg['To'] = candidate_email
        msg['Subject'] = subject
        msg.attach(MIMEText(html_body, 'html'))
        
        try:
            if not sender_email or not sender_password:
                logger.warning(f"SMTP credentials not configured. Skipping email to {candidate_email}.")
                return False

            logger.info(f"Sending email to {candidate_email} for {job_title} via {sender_email}...")
            server = smtplib.SMTP(self.smtp_server, self.smtp_port)
            server.starttls()
            server.login(sender_email, sender_password)
            server.send_message(msg)
            server.quit()
            logger.info(f"Successfully sent email to {candidate_email}")
            return True
        except Exception as e:
            logger.error(f"Failed to send email to {candidate_email}: {e}")
            return False
