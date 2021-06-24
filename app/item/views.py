from .forms import CreateItemForm
from django.shortcuts import redirect
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import ListView, DetailView, CreateView, DeleteView, UpdateView
from django.urls import reverse_lazy
from django.http.response import JsonResponse
from django.conf import settings
from django.db.models import Count, Prefetch, Q
from django.core.exceptions import FieldError
from .models import Item, Tag, Comment, Like

from django_filters import rest_framework as filters
from rest_framework import status, views, generics
from rest_framework.exceptions import ValidationError
from rest_framework.response import Response

from rest_framework.serializers import ImageField

from django.shortcuts import get_object_or_404

from .serializers import ItemSerializer

class ItemFitler(filters.FilterSet):
  class Meta:
    model = Item
    fields = ['id', 'title', 'author', 'created_at']

class ItemListCreateAPIView(generics.ListCreateAPIView):
  serializer_class = ItemSerializer
  values = {
    'origin': ('id', 'title', 'body', 'created_at', 'author_id', 'author_id__username', 'author_id__avatar', 'image', 'likes__user_id', 'likes__user_id__avatar'),
    'comment': ('id', 'body', 'created_at', 'item_id', 'author_id', 'author_id__username', 'author_id__avatar'),
      'like': ('id', 'created_at', 'user_id', 'user_id__avatar', 'user_id__username')
    }
  queryset = (
    Item.objects.all()
      .select_related('author')
      .prefetch_related(
        Prefetch(
          'comment_set',
          queryset=Comment.objects.all().select_related('author').order_by('-created_at').only(*values['comment']),
          to_attr='comments'
          )
        )
      .prefetch_related(
        Prefetch(
          'likes',
          queryset=Like.objects.all().select_related('user').order_by('-created_at').only(*values['like']),
          to_attr='islike'
          )
      )
      .prefetch_related(
        Prefetch(
          'tags',
          queryset=Tag.objects.all(),
          to_attr='hasTags'
          )
      )
      .annotate(
        Count('comment'),
        Count('likes'),
      )
      .only(*values['origin'])
  )

  def get_queryset(self):
    q = self.queryset.order_by('-created_at')
    if self.request.user.is_authenticated:
      q = q.annotate(current_islike=Count('likes', filter=Q(likes__user=self.request.user)))
    if 'sort' in self.request.GET and self.request.GET.get('sort') != 'created_at':
      sort = self.request.GET.get('sort')
      try:
        q = q.annotate(sort=Count(sort)).order_by('-sort', '-created_at')
      except FieldError:
        q = q
    return q

  # def get(self, request, *args, **kwargs):
  #   filterset = ItemFitler(request.query_params, queryset=self.get_queryset())
  #   if not filterset.is_valid():
  #     raise ValidationError(filterset.errors)
  #   serializer = ItemSerializer(instance=filterset.qs, many=True)
  #   return Response(serializer.data, status.HTTP_200_OK)

  def perform_create(self, serializer):
    serializer.save(author=self.request.user)
    tags = self.request.POST['tags'].split(',')

    if tags:
      for tag_name in tags:
        tag_name = tag_name.strip()
        if tag_name != '':
          exist = Tag.objects.filter(name=tag_name).first()
          if exist:
            serializer.tags.add(exist)
          else:
            serializer.tags.create(name=tag_name)


  # def post(self, request, *args, **kwargs):
  #   serializer = ItemSerializer(data=request.data)
  #   serializer.is_valid(raise_exception=True)
  #   serializer.save(commti=False)
  #   serializer.author = self.request.user
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

class ItemRetriveUpdateDestroyAPIView(views.APIView):
  values = {
  'origin': ('id', 'title', 'body', 'created_at', 'author_id', 'author_id__username', 'author_id__avatar', 'image', 'likes__user_id', 'likes__user_id__avatar'),
  'comment': ('id', 'body', 'created_at', 'item_id', 'author_id', 'author_id__username', 'author_id__avatar'),
    'like': ('id', 'created_at', 'user_id', 'user_id__avatar', 'user_id__username')
  }
  queryset = (
    Item.objects.all()
      .select_related('author')
      .prefetch_related(
        Prefetch(
          'comment_set',
          queryset=Comment.objects.all().select_related('author').order_by('-created_at').only(*values['comment']),
          to_attr='comments'
          )
        )
      .prefetch_related(
        Prefetch(
          'likes',
          queryset=Like.objects.all().select_related('user').order_by('-created_at').only(*values['like']),
          to_attr='islike'
          )
      )
      .prefetch_related(
        Prefetch(
          'tags',
          queryset=Tag.objects.all(),
          to_attr='hasTags'
          )
      )
      .annotate(
        Count('comment'),
        Count('likes'),
      )
      .only(*values['origin'])
  )

  def get_queryset(self):
    q = self.queryset
    if self.request.user.is_authenticated:
      q = q.annotate(current_islike=Count('likes', filter=Q(likes__user=self.request.user)))
    return q

  def get(self, request, pk, *args, **kwargs):
    item = get_object_or_404(self.get_queryset(), pk=pk)
    serializer = ItemSerializer(instance=item)
    return Response(serializer.data, status.HTTP_200_OK)

  def put(self, request, pk, *args, **kwargs):
    item = get_object_or_404(Item, pk=pk)
    serializer = ItemSerializer(instance=item, data=request.data)
    serializer.is_valid(raise_exception=True)
    serializer.save(commit=False)
    serializer.save()

    # Remove current tags
    current_tags = serializer.tags.all()
    for current_tag in current_tags:
      serializer.tags.remove(current_tag)
      if current_tag.item_set.count() == 0:
        current_tag.delete()

    # Add or Create request tags
    tags = self.request.POST['tags'].split(',')
    if tags:
      for tag_name in tags:
        tag_name = tag_name.strip()
        if tag_name != '':
          exist = Tag.objects.filter(name=tag_name).first()
          if exist:
            serializer.tags.add(exist)
          else:
            serializer.tags.create(name=tag_name)

    return Response(serializer.data, status.HTTP_200_OK)

  def patch(self, request, pk, *args, **kwargs):
    item = get_object_or_404(Item, pk=pk)
    serializer = ItemSerializer(instance=item, data=request.data, partial=True)
    serializer.is_valid(raise_exception=True)
    serializer.save()
    return Response(serializer.data, status.HTTP_200_OK)

  def delete(self, request, pk, *args, **kwargs):
    item = get_object_or_404(Item, pk=pk)
    item.delete()
    return Response(status.HTTP_204_NO_CONTENT)

'''
def create_comment(request, pk):

  if request.method == 'POST':
    item = Item.objects.get(pk=pk)
    comment = Comment(body=request.POST.get('comment'), author=request.user, item=item)
    comment.save()
    return redirect('item.detail', pk=pk)

def delete_item(request, pk):

  if request.method == 'POST':
    item = Item.objects.get(pk=pk)
    if item.author == request.user:
      item.delete()
      data = {"msg": 'ok'}
    else:
      data = {"msg": 'ng'}

  return JsonResponse(data)

def like(request, pk):
  if request.method == 'POST':
    item = Item.objects.get(pk=pk)
    like = item.likes.filter(user=request.user)
    flg = like.exists()
    if flg:
      like.delete()
    else:
      l = Like(user=request.user, item=item)
      l.save()
      item.likes.add(l)
    cnt_all = item.likes.count()
    cnt_current = like.count()
    data = {
      "cntAll": cnt_all,
      "cntCurrent": cnt_current
      }
  else:
    data = { "msg": 'Bad method' }

  return JsonResponse(data)

class IndexView(ItemList):
  template_name = 'index.html'

  def get_queryset(self):
    return super().get_queryset()[:3]

index = IndexView.as_view()

class HomeView(ItemList):
  template_name = 'home.html'

  def get_context_data(self, **kwargs):
    context = super().get_context_data(**kwargs)

    items = self.get_queryset()
    myitems = items.filter(author=self.request.user)
    context['myitems'] = myitems

    mylikes = items.filter(likes__user=self.request.user).order_by('-likes__created_at')
    context['mylikes'] = mylikes

    mycomments = Comment.objects.filter(author=self.request.user).select_related('author').order_by('-created_at')
    context['mycomments'] = mycomments

    try:
      hero = myitems.first()
      context['hero'] = hero.getThumbnailImage()
    except (Item.DoesNotExist, AttributeError):
      context['hero'] = settings.STATIC_URL + 'img/bg-0.jpg'

    return context

class ItemTagList(ListView):
  template_name = 'item/tag_list.html'
  paginate_by = 6
  queryset = (
    Item.objects.all()
      .select_related('author')
      .prefetch_related(
        Prefetch(
          'comment_set',
          queryset=Comment.objects.all().select_related('author').order_by('-created_at'),
          to_attr='comments'
          )
        )
      .prefetch_related(
        Prefetch(
          'likes',
          queryset=Like.objects.all().select_related('user').order_by('-created_at'),
          to_attr='islike'
          )
      )
      .annotate(
        Count('comment'),
        Count('likes'),
      )
  )

  def get_queryset(self):
    q = self.queryset.filter(tags__id=self.kwargs['pk']).order_by('-created_at')
    if self.request.user.is_authenticated:
      q = q.annotate(currentuser_islike=Count('likes', filter=Q(likes__user=self.request.user)))
    if 'sort' in self.request.GET and self.request.GET.get('sort') != 'created_at':
      sort = self.request.GET.get('sort')
      try:
        q = q.annotate(sort=Count(sort)).order_by('-sort', '-created_at')
      except FieldError:
        q = q
    return q

  def get_context_data(self, **kwargs):
      context = super().get_context_data(**kwargs)
      tag_name = Tag.objects.get(pk=self.kwargs['pk'])
      context['tag_id'] = self.kwargs['pk']
      context['tag_name'] = tag_name
      return context
'''
