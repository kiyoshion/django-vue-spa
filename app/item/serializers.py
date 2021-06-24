
from django.db.models import Count, Prefetch, Q
from rest_framework import serializers
from rest_framework.serializers import ImageField
from .models import Item, Comment, Like, Tag
from user.models import CustomUser

class AuthorSerializer(serializers.ModelSerializer):
  avatar = ImageField(read_only=True)

  class Meta:
    model = CustomUser
    fields = ['id', 'username', 'avatar']

class AuthorListSerializer(serializers.ListSerializer):
  child = AuthorSerializer()

class CommentSerializer(serializers.ModelSerializer):
  author = AuthorSerializer()

  class Meta:
    model = Comment
    fields = ['id', 'body', 'created_at', 'author']

class CommentListSerializer(serializers.ListSerializer):
  child = CommentSerializer()

class LikeSerializer(serializers.ModelSerializer):
  user = AuthorSerializer()

  class Meta:
    model = Like
    fields = ['user']

class TagSerializer(serializers.ModelSerializer):
  id = serializers.IntegerField(required=False)
  class Meta:
    model = Tag
    fields = ['id', 'name']

class TagListSerializer(serializers.ListSerializer):
  child = TagSerializer()

class ItemSerializer(serializers.ModelSerializer):
  image_thumbnail = ImageField(read_only=True)
  author = serializers.CharField(read_only=True)
  comments = CommentListSerializer()
  comment__count = serializers.IntegerField(read_only=True)
  likes__count = serializers.IntegerField(read_only=True)
  current_islike = serializers.IntegerField(read_only=True)
  hasTags = TagListSerializer()

  class Meta:
    model = Item
    fields = ['id', 'title', 'body', 'created_at', 'author', 'image_thumbnail', 'comments', 'comment__count', 'likes__count', 'current_islike', 'hasTags']

  def create(self, validated_data):
    return Item.objects.create(**validated_data)

class ItemListSerializer(serializers.ListSerializer):
  child = ItemSerializer()

  # def create(self, request, *args, **kwargs):
  #   item = Item(author=self.request.user)
  #   serializer = ItemSerializer(item, data=request.data)
  #   serializer.is_valid(raise_exception=True)
  #   serializer.save(commti=False)
  #   serializer.save()
  #   tags = self.request.POST['tags'].split(',')

  #   if tags:
  #     for tag_name in tags:
  #       tag_name = tag_name.strip()
  #       if tag_name != '':
  #         exist = Tag.objects.filter(name=tag_name).first()
  #         if exist:
  #           serializer.tags.add(exist)
  #         else:
  #           serializer.tags.create(name=tag_name)
  #   return Response(serializer.data, status.HTTP_201_CREATED)

