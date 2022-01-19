from django.core.management.base import BaseCommand
from django.db import IntegrityError
from app.models import Profile, Question, Answer, Tag, Like
from faker import Faker

fake = Faker()

DEFAULT_PROFILES_TOTAL = 100
DEFAULT_QUESTIONS_TOTAL = 1000
DEFAULT_ANSWERS_TOTAL = 10000
DEFAULT_TAGS_TOTAL = 500

DEFAULT_PASSWORD = 'fake_pwd'  # Password to be set for profiles
DEFAULT_TAGS_LIMIT = 3  # Max tags per question


class Command(BaseCommand):
    help = 'Add fake data to the database'
    requires_migrations_checks = True

    def add_arguments(self, parser):
        parser.add_argument('-p', '--profiles', type=int, help='Indicates the number of profiles to be created')
        parser.add_argument('-q', '--questions', type=int, help='Indicates the number of questions to be created')
        parser.add_argument('-a', '--answers', type=int, help='Indicates the number of answers to be created')
        parser.add_argument('-t', '--tags', type=int, help='Indicates the number of tags to be created')
        parser.add_argument('--tags_limit', type=str, help='Indicates the limit of tags per question')
        parser.add_argument('--password', type=str, help='Defines password for created profiles')

    def create_tags(self, total):
        i = 0
        while i < total:
            tag_name = fake.word().lower()
            obj, created = Tag.objects.get_or_create(name=tag_name)
            if created:
                i += 1

    def create_profiles(self, total, password):
        i = 0
        while i < total:
            profile = fake.simple_profile()
            try:
                Profile.objects.create_profile(
                    username=profile['username'], email=profile['mail'],
                    nickname=profile['name'], password=password)
                i += 1
            except IntegrityError:
                continue

    def create_questions(self, total, tags_limit):
        profiles_list = list(Profile.objects.all())
        tag_names_list = [tag.name for tag in Tag.objects.all()]
        likes_limit = int(len(profiles_list) / 10)
        i = 0
        while i < total:
            author = fake.random.choice(profiles_list)
            tags = fake.random.sample(tag_names_list, fake.random.randint(0, tags_limit))
            title = fake.sentence()
            text = fake.text(500)
            try:
                question = Question.objects.create_question(
                    author=author, title=title, text=text, tag_names=tags)
                i += 1
            except IntegrityError:
                continue
            rating = fake.random.randint(-likes_limit, likes_limit)
            is_positive = bool(rating > 0)
            like_authors = fake.random.sample(profiles_list, abs(rating))
            likes = list()
            for like_author in like_authors:
                likes.append(Like(author=like_author, content_object=question,
                                  is_positive=is_positive))
            Like.objects.bulk_create(likes, 1000)
            question.rating = rating
            question.author.reputation += rating
            question.author.save()
            question.save()

    def create_answers(self, total):
        profiles_list = list(Profile.objects.all())
        questions_list = list(Question.objects.all())
        likes_limit = int(len(profiles_list) / 50)
        i = 0
        while i < total:
            question = fake.random.choice(questions_list)
            author = fake.random.choice(profiles_list)
            text = fake.text(300)
            answer = Answer.objects.create(question=question, author=author, text=text)
            i += 1
            rating = fake.random.randint(-likes_limit, likes_limit)
            is_positive = bool(rating > 0)
            like_authors = fake.random.sample(profiles_list, abs(rating))
            likes = list()
            for like_author in like_authors:
                likes.append(Like(author=like_author, content_object=answer,
                                  is_positive=is_positive))
            Like.objects.bulk_create(likes, 1000)
            answer.rating = rating
            answer.author.reputation += rating
            answer.author.save()
            answer.save()

    def handle(self, *args, **options):
        profiles_total = options['profiles'] if (options['profiles'] is not None) else DEFAULT_PROFILES_TOTAL
        questions_total = options['questions'] if (options['questions'] is not None) else DEFAULT_QUESTIONS_TOTAL
        answers_total = options['answers'] if (options['answers'] is not None) else DEFAULT_ANSWERS_TOTAL
        tags_total = options['tags'] if (options['tags'] is not None) else DEFAULT_TAGS_TOTAL
        tags_limit = options['tags_limit'] if (options['tags_limit'] is not None) else DEFAULT_TAGS_LIMIT
        password = options['password'] if (options['password'] is not None) else DEFAULT_PASSWORD

        print(f'Creating {profiles_total} new profiles')
        self.create_profiles(profiles_total, password)
        print('Profiles created')

        print(f'Creating {tags_total} new tags')
        self.create_tags(tags_total)
        print('Tags created')

        print(f'Creating {questions_total} new questions')
        self.create_questions(questions_total, tags_limit)
        print('Questions created')

        print(f'Creating {answers_total} new answers')
        self.create_answers(answers_total)
        print('Answers created')

        print('Fake database data created')
