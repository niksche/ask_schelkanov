from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from app.models import Question, Answer, Tag

CONFIRMATION = 'remove database'

class Command(BaseCommand):
    help = 'Remove all data from the database'
    requires_migrations_checks = True

    def add_arguments(self, parser):
        parser.add_argument('--yes', help='Remove confirmation dialogue')

    def drop_db(self):
        Answer.objects.all().delete()
        Question.objects.all().delete()
        Tag.objects.all().delete()
        User.objects.all().delete()

    def handle(self, *args, **options):
        no_confirm = options['yes']

        if not no_confirm:
            check = input('Are you sure you want to DROP database? '
                          'This action will WIPE all the data.\n'
                          f'Type "{CONFIRMATION}" to proceed: ')
            if check != CONFIRMATION:
                print('Abort')
                return

        print('Removing all data from the database')
        self.drop_db()
        print('All records removed')
