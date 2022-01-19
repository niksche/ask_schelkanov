from os import path
from django.contrib.contenttypes.fields import GenericForeignKey, GenericRelation
from django.contrib.contenttypes.models import ContentType
from django.db import models
from django.conf import settings
from django.core.exceptions import ValidationError, FieldError
from django.contrib.auth.models import User


class ProfileManager(models.Manager):
    def get_top(self, count):
        return self.order_by('-reputation')[:count]

    def create_profile(self, username, email, nickname, password, avatar=None):
        user = User.objects.create_user(username, email, password)
        return self.create(user=user, nickname=nickname, avatar=avatar)


class Profile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    nickname = models.CharField(max_length=30, unique=True)
    reputation = models.IntegerField(default=0)
    avatar = models.ImageField(upload_to='uploads')
    objects = ProfileManager()

    def update_profile(self, username=None, email=None, nickname=None, avatar=None):
        user_modified = False
        profile_modified = False
        if username and self.user.username != username:
            self.user.username = username
            user_modified = True
        if email and self.user.email != email:
            self.user.email = email
            user_modified = True
        if nickname and self.nickname != nickname:
            self.nickname = nickname
            profile_modified = True
        if avatar and self.avatar != avatar:
            self.avatar = avatar
            profile_modified = True
        if user_modified:
            self.user.save()
        if profile_modified:
            self.save()

    def __str__(self):
        return self.nickname


class LikeManager(models.Manager):
    def add_like(self, author, content_object, is_positive):
        rating_delta = 1 if is_positive else (-1)
        likes = content_object.likes.filter(author=author)
        if not likes:
            self.create(author=author, content_object=content_object, is_positive=is_positive)
        elif not likes.filter(is_positive=is_positive).exists():
            # Flip sign
            likes.update(is_positive=is_positive)
            rating_delta *= 2
        else:
            # Like has already been set
            rating_delta = 0

        if rating_delta:
            content_object.author.reputation += rating_delta
            content_object.author.save()
            content_object.rating += rating_delta
            content_object.save()
        return content_object.rating

    def remove_like(self, author, content_object):
        likes = content_object.likes.filter(author=author)
        if likes:
            if likes.filter(is_positive=True).exists():
                content_object.rating -= 1
            else:
                content_object.rating += 1
            likes.delete()
            content_object.save()
        return content_object.rating

    def like_sign(self, profile, content_object):
        likes = content_object.likes.filter(author=profile)
        if not likes:
            return 0
        elif likes.filter(is_positive=True).exists():
            return 1
        else:
            return -1


class Like(models.Model):
    content_type = models.ForeignKey(ContentType, on_delete=models.CASCADE)
    object_id = models.PositiveIntegerField(db_index=True)
    content_object = GenericForeignKey('content_type', 'object_id')

    author = models.ForeignKey(Profile, on_delete=models.CASCADE)
    is_positive = models.BooleanField(default=True)

    objects = LikeManager()

    def __str__(self):
        return f'#{self.object_id} {self.author} ({self.is_positive})'


class TagManager(models.Manager):
    def get_top(self, quantity):
        top_tags = [{'tag': None, 'count': 0} for _ in range(quantity)]
        for tag in self.all():
            tag_count = Question.objects.filter(tags=tag).count()
            if top_tags[-1]['count'] < quantity:
                top_tags[-1]['tag'] = tag
                top_tags[-1]['count'] = tag_count
                top_tags.sort(key=lambda x: x['count'], reverse=True)

        result_clean = [x['tag'] for x in top_tags if x['tag'] is not None]
        return result_clean


class Tag(models.Model):
    name = models.CharField(max_length=30, unique=True)
    objects = TagManager()

    def __str__(self):
        return self.name


class QuestionManager(models.Manager):
    def get_new(self):
        return self.order_by('-creation_dt')

    def get_hot(self):
        return self.order_by('-rating')

    def get_tagged(self, tag_name):
        return self.filter(tags__name=tag_name)

    def create_question(self, author, title, text, tag_names):
        q = self.create(author=author, title=title, text=text)
        q.add_tags(tag_names)
        return q


class Question(models.Model):
    author = models.ForeignKey(Profile, on_delete=models.CASCADE)
    title = models.CharField(max_length=140)
    text = models.CharField(max_length=1000)
    tags = models.ManyToManyField(Tag, blank=True)
    likes = GenericRelation(Like, related_query_name='question')
    creation_dt = models.DateTimeField(auto_now_add=True, db_index=True)
    rating = models.IntegerField(default=0, db_index=True)
    is_open = models.BooleanField(default=True)

    objects = QuestionManager()

    def __str__(self):
        return self.title

    def add_tags(self, tag_names):
        for name in tag_names:
            self.tags.add(Tag.objects.get_or_create(name=name)[0])
        self.save()

    def add_like(self, from_profile, is_positive=True):
        Like.objects.add_like(author=from_profile, content_object=self, is_positive=is_positive)

    def get_like_sign(self, profile):
        return Like.objects.like_sign(profile=profile, content_object=self)

    class Meta:
        ordering = ['-creation_dt']


class Answer(models.Model):
    question = models.ForeignKey(Question, on_delete=models.CASCADE)
    author = models.ForeignKey(Profile, on_delete=models.CASCADE)
    text = models.CharField(max_length=1000)
    rating = models.IntegerField(default=0)
    likes = GenericRelation(Like, related_query_name='question')
    creation_dt = models.DateTimeField(auto_now_add=True)
    is_right = models.BooleanField(default=False)

    def __str__(self):
        return f'#{self.question} by {self.author}'

    def add_like(self, from_profile, is_positive=True):
        Like.objects.add_like(author=from_profile, content_object=self, is_positive=is_positive)

    def get_like_sign(self, profile):
        return Like.objects.like_sign(profile=profile, content_object=self)

    def set_right(self, from_profile, is_right=True):
        if from_profile != self.question.author:
            return False
        self.is_right = is_right
        self.save()
        return True

    class Meta:
        ordering = ['-rating']
