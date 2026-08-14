import uuid
import re
import qrcode
from io import BytesIO
from django.db import models
from django.core.files.base import ContentFile

class Participant(models.Model):
    name = models.CharField(max_length=150, help_text="Full Name of the Participant")
    email = models.EmailField(help_text="Contact Email Address")
    roll_number = models.CharField(max_length=50, unique=True, help_text="Unique Roll / Registration Number")
    qr_token = models.UUIDField(default=uuid.uuid4, unique=True, editable=False, db_index=True)
    qr_code_image = models.ImageField(upload_to='qr_codes/', blank=True, null=True)
    attended = models.BooleanField(default=False, help_text="Attendance Status")
    checked_in_at = models.DateTimeField(blank=True, null=True, help_text="Timestamp when participant checked in")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.name} ({self.roll_number})"

    def save(self, *args, **kwargs):
        # Ensure qr_token is created
        if not self.qr_token:
            self.qr_token = uuid.uuid4()

        # Automatically generate QR Code image if not present or missing from storage
        if not self.qr_code_image or not self.qr_code_image.storage.exists(self.qr_code_image.name):
            self.generate_qr_code()

        super().save(*args, **kwargs)

    def generate_qr_code(self):
        """
        Generates a QR Code image encoding the unique qr_token UUID
        and saves it to the qr_code_image ImageField.
        """
        qr = qrcode.QRCode(
            version=1,
            error_correction=qrcode.constants.ERROR_CORRECT_M,
            box_size=10,
            border=4,
        )
        # Encode the unique UUID token string into the QR code
        qr.add_data(str(self.qr_token))
        qr.make(fit=True)

        img = qr.make_image(fill_color="#0f172a", back_color="#ffffff")
        buffer = BytesIO()
        img.save(buffer, format='PNG')
        safe_roll = re.sub(r'[^a-zA-Z0-9_-]', '_', str(self.roll_number))
        filename = f"qr_{safe_roll}_{self.qr_token.hex[:8]}.png"
        self.qr_code_image.save(filename, ContentFile(buffer.getvalue()), save=False)

