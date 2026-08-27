import base64
import binascii
import mimetypes
import uuid

from django.core.files.base import ContentFile
from django.core.management.base import BaseCommand
from django.db.models import Q

from properties.models import PropertyImage


class Command(BaseCommand):
    help = 'Move legacy data URL property images from image_url into image_file.'

    def handle(self, *args, **options):
        migrated = 0
        skipped = 0

        images = PropertyImage.objects.filter(
            Q(image_file__isnull=True) | Q(image_file=''),
            image_url__startswith='data:image/',
        )
        for image in images.iterator():
            try:
                header, encoded = image.image_url.split(',', 1)
                content_type = header.split(';', 1)[0].replace('data:', '')
                ext = mimetypes.guess_extension(content_type) or '.jpg'
                filename = f'{uuid.uuid4()}{ext}'
                image.image_file.save(filename, ContentFile(base64.b64decode(encoded)), save=False)
                image.image_url = ''
                image.save(update_fields=['image_file', 'image_url'])
                migrated += 1
            except (ValueError, TypeError, binascii.Error):
                skipped += 1

        self.stdout.write(self.style.SUCCESS(f'Migrated {migrated} image(s). Skipped {skipped}.'))
