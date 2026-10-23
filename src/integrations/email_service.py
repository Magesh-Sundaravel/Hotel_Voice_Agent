import logging
from email.message import EmailMessage

import aiosmtplib

from src.config import settings

logger = logging.getLogger(__name__)


class EmailService:
    """Service to send reservation confirmation emails to guests."""

    def __init__(
        self,
        smtp_host: str | None = None,
        smtp_port: int | None = None,
        smtp_user: str | None = None,
        smtp_password: str | None = None,
        from_email: str | None = None,
    ):
        self.smtp_host = smtp_host or settings.SMTP_HOST
        self.smtp_port = smtp_port or settings.SMTP_PORT
        self.smtp_user = smtp_user or settings.SMTP_USER
        self.smtp_password = smtp_password or settings.SMTP_PASSWORD
        self.from_email = from_email or settings.SMTP_FROM_EMAIL or "prenotazioni@sinahotels.com"

    async def send_email(
        self,
        to_email: str,
        subject: str,
        body: str,
        html_body: str | None = None,
    ) -> bool:
        """Sends an email message to the specified recipient."""
        message = EmailMessage()
        message["From"] = self.from_email
        message["To"] = to_email
        message["Subject"] = subject
        message.set_content(body)
        if html_body:
            message.add_alternative(html_body, subtype="html")

        if not self.smtp_host or not self.smtp_user:
            logger.info(
                "[SIMULATED EMAIL] To: %s | Subject: %s",
                to_email,
                subject,
            )
            return True

        try:
            await aiosmtplib.send(
                message,
                hostname=self.smtp_host,
                port=self.smtp_port,
                username=self.smtp_user,
                password=self.smtp_password,
                start_tls=True,
            )
            logger.info("Email sent to %s: %s", to_email, subject)
            return True
        except (aiosmtplib.SMTPException, OSError, ValueError) as e:
            logger.error("Failed to send email to %s: %s", to_email, e)
            return False

    async def send_room_booking_confirmation(
        self,
        to_email: str,
        guest_name: str,
        reference_code: str,
        room_category: str,
        check_in_date: str,
        check_out_date: str,
        guests_count: int,
        total_price: int | None = None,
        room_number: str | None = None,
        special_requests: str | None = None,
    ) -> bool:
        """Sends a luxury Italian confirmation email for hotel room bookings."""
        subject = f"Conferma Prenotazione {reference_code} - Sina Bernini Bristol"

        price_str = f"€{total_price}" if total_price else "Tariffa confermata alla reception"
        room_str = f"Camera {room_number}" if room_number else "Assegnata al check-in"
        notes_str = (
            f"<p><strong>Note speciali:</strong> {special_requests}</p>" if special_requests else ""
        )

        html_content = f"""
<!DOCTYPE html>
<html>
<head>
  <meta charset="utf-8">
  <title>{subject}</title>
  <style>
    body {{ font-family: 'Helvetica Neue', Helvetica, Arial, sans-serif; background-color: #f7f5f0; margin: 0; padding: 20px; }}
    .container {{ max-width: 600px; margin: 0 auto; background: #ffffff; border-radius: 8px; border: 1px solid #e0d8c8; overflow: hidden; }}
    .header {{ background-color: #1a2930; color: #f7f5f0; padding: 30px; text-align: center; }}
    .header h1 {{ margin: 0; font-size: 24px; font-weight: 300; letter-spacing: 2px; text-transform: uppercase; }}
    .header p {{ margin: 5px 0 0 0; font-size: 13px; color: #c5a059; letter-spacing: 1px; }}
    .content {{ padding: 30px; color: #333333; line-height: 1.6; }}
    .booking-card {{ background: #faf8f5; border-left: 4px solid #c5a059; padding: 15px 20px; margin: 20px 0; }}
    .booking-card table {{ width: 100%; border-collapse: collapse; }}
    .booking-card td {{ padding: 6px 0; font-size: 14px; }}
    .booking-card td.label {{ color: #777; width: 40%; }}
    .booking-card td.val {{ font-weight: bold; color: #1a2930; }}
    .footer {{ background: #faf8f5; padding: 20px; text-align: center; font-size: 12px; color: #888; border-top: 1px solid #eee; }}
  </style>
</head>
<body>
  <div class="container">
    <div class="header">
      <h1>Sina Bernini Bristol</h1>
      <p>Autograph Collection • Roma</p>
    </div>
    <div class="content">
      <p>Gentile <strong>{guest_name}</strong>,</p>
      <p>È un vero piacere confermarLe la prenotazione del Suo soggiorno presso il nostro hotel in Piazza Barberini.</p>

      <div class="booking-card">
        <table>
          <tr><td class="label">Codice Prenotazione:</td><td class="val">{reference_code}</td></tr>
          <tr><td class="label">Tipologia Camera:</td><td class="val">{room_category}</td></tr>
          <tr><td class="label">Assegnazione:</td><td class="val">{room_str}</td></tr>
          <tr><td class="label">Check-in:</td><td class="val">{check_in_date} (dalle ore 15:00)</td></tr>
          <tr><td class="label">Check-out:</td><td class="val">{check_out_date} (entro le ore 12:00)</td></tr>
          <tr><td class="label">Ospiti:</td><td class="val">{guests_count}</td></tr>
          <tr><td class="label">Importo Totale:</td><td class="val">{price_str}</td></tr>
        </table>
      </div>

      {notes_str}

      <p><strong>Informazioni per il Suo arrivo:</strong></p>
      <p>Il nostro Concierge e la Reception sono a Sua completa disposizione 24 ore su 24 per organizzare transfer privati, prenotazioni presso il Rooftop Restaurant <em>The Flair</em> o trattamenti rilassanti presso la <em>Sina Spa</em>.</p>

      <p>A presto a Roma,<br><em>La Direzione & Concierge, Sina Bernini Bristol</em></p>
    </div>
    <div class="footer">
      Sina Bernini Bristol — Piazza Barberini 23, 00187 Roma (RM), Italia<br>
      Telefono: +39 06 4883051 | Email: {self.from_email}
    </div>
  </div>
</body>
</html>
"""

        plain_text = f"""
Gentile {guest_name},

Confermiamo con piacere la Sua prenotazione presso Sina Bernini Bristol (Roma).

Dettagli Prenotazione:
- Codice di Riferimento: {reference_code}
- Tipologia: {room_category} ({room_str})
- Check-in: {check_in_date} (dalle 15:00)
- Check-out: {check_out_date} (entro le 12:00)
- Numero Ospiti: {guests_count}
- Totale Soggiorno: {price_str}

Indirizzo: Piazza Barberini 23, Roma
Telefono: +39 06 4883051

Cordiali saluti,
Sina Bernini Bristol Reception
"""

        message = EmailMessage()
        message["From"] = self.from_email
        message["To"] = to_email
        message["Subject"] = subject
        message.set_content(plain_text)
        message.add_alternative(html_content, subtype="html")

        if not self.smtp_host or not self.smtp_user:
            logger.info(
                "[SIMULATED EMAIL] To: %s | Subject: %s | Reference: %s",
                to_email,
                subject,
                reference_code,
            )
            return True

        try:
            await aiosmtplib.send(
                message,
                hostname=self.smtp_host,
                port=self.smtp_port,
                username=self.smtp_user,
                password=self.smtp_password,
                start_tls=True,
            )
            logger.info("Confirmation email sent to %s for booking %s", to_email, reference_code)
            return True
        except (aiosmtplib.SMTPException, OSError, ValueError) as e:
            logger.error("Failed to send confirmation email to %s: %s", to_email, e)
            return False
