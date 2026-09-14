import smtplib
from config import EMAIL_ADDRESS, EMAIL_PASSWORD

print("Email:", EMAIL_ADDRESS)
print("Password length:", len(EMAIL_PASSWORD))

try:
    with smtplib.SMTP_SSL("smtp.gmail.com", 465) as smtp:
        smtp.login(EMAIL_ADDRESS, EMAIL_PASSWORD)

    print("SUCCESS: Gmail login is working!")

except smtplib.SMTPAuthenticationError:
    print("FAILED: Gmail rejected the email or App Password.")

except Exception as e:
    print("ERROR:", e)