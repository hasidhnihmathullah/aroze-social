from django.shortcuts import render, redirect, get_object_or_404
from django.http import JsonResponse
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.models import User
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_POST
from django.db import IntegrityError
from .models import Profile, Post, Comment, Follow

def index(request):
    posts = Post.objects.all().select_related('author', 'author__profile').prefetch_related('likes', 'comments', 'comments__author')

    if request.method == 'POST':
        if 'login' in request.POST:
            u = request.POST.get('username', '').strip()
            p = request.POST.get('password', '').strip()
            user = authenticate(request, username=u, password=p)
            if user:
                login(request, user)
            return redirect('index')

        elif 'register' in request.POST:
            u = request.POST.get('username', '').strip()
            p = request.POST.get('password', '').strip()
            bio = request.POST.get('bio', '').strip()

            if u and p:
                if User.objects.filter(username__iexact=u).exists():
                    # If already registered, attempt login directly
                    user = authenticate(request, username=u, password=p)
                    if user:
                        login(request, user)
                else:
                    try:
                        user = User.objects.create_user(username=u, password=p)
                        if bio:
                            user.profile.bio = bio
                            user.profile.save()
                        login(request, user)
                    except IntegrityError:
                        pass
            return redirect('index')

    following_ids = []
    suggestions = []
    if request.user.is_authenticated:
        following_ids = list(Follow.objects.filter(follower=request.user).values_list('following_id', flat=True))
        suggestions = User.objects.exclude(id=request.user.id).exclude(id__in=following_ids)[:5]
    else:
        suggestions = User.objects.all()[:5]

    return render(request, 'index.html', {
        'posts': posts,
        'suggestions': suggestions,
        'following_ids': following_ids,
    })

@login_required
@require_POST
def create_post(request):
    content = request.POST.get('content', '').strip()
    image = request.FILES.get('image', None)

    if content or image:
        post = Post.objects.create(author=request.user, content=content, image=image)
        return JsonResponse({
            'status': 'success',
            'post': {
                'id': post.id,
                'author': post.author.username,
                'content': post.content,
                'image_url': post.image.url if post.image else '',
                'created_at': 'Just now',
                'likes_count': 0,
            }
        })
    return JsonResponse({'status': 'error', 'message': 'Post content cannot be empty.'}, status=400)

@login_required
def toggle_like(request, post_id):
    post = get_object_or_404(Post, id=post_id)
    if request.user in post.likes.all():
        post.likes.remove(request.user)
        liked = False
    else:
        post.likes.add(request.user)
        liked = True

    return JsonResponse({
        'status': 'success',
        'liked': liked,
        'total_likes': post.total_likes
    })

@login_required
@require_POST
def add_comment(request, post_id):
    post = get_object_or_404(Post, id=post_id)
    text = request.POST.get('text', '').strip()
    if text:
        comment = Comment.objects.create(post=post, author=request.user, text=text)
        return JsonResponse({
            'status': 'success',
            'comment': {
                'author': comment.author.username,
                'text': comment.text,
                'created_at': 'Just now'
            }
        })
    return JsonResponse({'status': 'error', 'message': 'Comment cannot be empty.'}, status=400)

@login_required
def toggle_follow(request, user_id):
    target_user = get_object_or_404(User, id=user_id)
    if target_user == request.user:
        return JsonResponse({'status': 'error', 'message': 'You cannot follow yourself.'}, status=400)

    record = Follow.objects.filter(follower=request.user, following=target_user)
    if record.exists():
        record.delete()
        following = False
    else:
        Follow.objects.create(follower=request.user, following=target_user)
        following = True

    return JsonResponse({
        'status': 'success',
        'following': following,
        'followers_count': target_user.followers_set.count()
    })

def user_logout(request):
    logout(request)
    return redirect('index')