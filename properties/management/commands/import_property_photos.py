import base64
import mimetypes
from pathlib import Path

from django.core.management.base import BaseCommand, CommandError

from properties.models import Property, PropertyImage

ALLOWED_EXTENSIONS = {'.jpg', '.jpeg', '.png', '.webp'}


class Command(BaseCommand):
    help = (
        'Reads every image in a folder and stores it on a Property as a base64 '
        'data URL (PropertyImage.image_url), so it persists in the database '
        'instead of the filesystem.'
    )

    def add_arguments(self, parser):
        parser.add_argument('folder', help='Path to a folder of images.')
        parser.add_argument('property', help='Property id or slug to attach the images to.')
        parser.add_argument(
            '--replace', action='store_true',
            help='Delete existing images on the property before adding the new ones.',
        )
        parser.add_argument(
            '--dry-run', action='store_true',
            help='List what would be imported without writing to the database.',
        )

    def handle(self, *args, **options):
        folder = Path(options['folder']).expanduser()
        if not folder.is_dir():
            raise CommandError(f'Not a folder: {folder}')

        property_ref = options['property']
        prop = (
            Property.objects.filter(pk=property_ref).first()
            if property_ref.isdigit()
            else Property.objects.filter(slug=property_ref).first()
        )
        if prop is None:
            raise CommandError(f'Property not found: {property_ref}')

        files = sorted(
            p for p in folder.iterdir()
            if p.is_file() and p.suffix.lower() in ALLOWED_EXTENSIONS
        )
        if not files:
            raise CommandError(f'No images found in {folder}')

        self.stdout.write(f'Property: {prop.id} - {prop.title}')
        self.stdout.write(f'Found {len(files)} image(s) in {folder}')

        if options['dry_run']:
            for f in files:
                self.stdout.write(f'  would import: {f.name}')
            return

        if options['replace']:
            deleted, _ = prop.images.all().delete()
            self.stdout.write(f'Deleted {deleted} existing image(s).')

        start_order = prop.images.count()
        has_main = prop.images.filter(is_main=True).exists()

        created = 0
        for index, path in enumerate(files):
            content_type = mimetypes.guess_type(path.name)[0] or 'image/jpeg'
            encoded = base64.b64encode(path.read_bytes()).decode('ascii')
            data_url = f'data:{content_type};base64,{encoded}'

            PropertyImage.objects.create(
                property=prop,
                image_url=data_url,
                caption=path.stem,
                order=start_order + index,
                is_main=(not has_main and index == 0),
            )
            created += 1

        self.stdout.write(self.style.SUCCESS(f'Imported {created} image(s) into "{prop.title}".'))
