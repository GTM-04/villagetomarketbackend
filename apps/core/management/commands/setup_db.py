"""
Django management command to run database migrations.
"""

from django.core.management import call_command
from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = 'Run database migrations'

    def handle(self, *args, **options):
        self.stdout.write('Running migrations...')
        call_command('makemigrations')
        call_command('migrate')
        self.stdout.write(self.style.SUCCESS('Migrations completed successfully'))
