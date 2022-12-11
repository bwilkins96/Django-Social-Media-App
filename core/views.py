from django.shortcuts import render, redirect
from django.contrib.auth.models import User, auth
from django.contrib import messages
from django.http import HttpResponse
from django.contrib.auth.decorators import login_required
from itertools import chain
from .models import Profile, Post, LikePost, FollowersCount
import time
import random

def sort_posts(posts):
    sorted = False

    while not sorted:
        sorted = True

        for i in range(len(posts)-1):
            created_at = posts[i].created_at
            created_at_2 = posts[i+1].created_at
            
            if created_at > created_at_2:
                temp = posts[i+1]
                posts[i+1] = posts[i]
                posts[i] = temp

                sorted = False
  
    return posts

def get_suggestions(request, user_following):
    all_users = User.objects.all()
    user_following_all = []

    for user in user_following:
        user_list = User.objects.get(username=user.user)
        user_following_all.append(user_list)

    new_suggestions_list = [x for x in list(all_users) if (x not in list(user_following_all))]
    current_user = User.objects.filter(username=request.user.username)
    final_suggestions_list = [x for x in list(new_suggestions_list) if (x not in list(current_user))]
    random.shuffle(final_suggestions_list)

    username_profiles = []
    username_profiles_list = []

    for user in final_suggestions_list:
        username_profiles.append(user.id)

    for id in username_profiles:
        profile_lists = Profile.objects.filter(id_user=id)
        username_profiles_list.append(profile_lists)

    return list(chain(*username_profiles_list))

# Create your views here.
@login_required(login_url='signin')
def index(request):
    user_object = User.objects.get(username=request.user.username)
    user_profile = Profile.objects.get(user=user_object)
    user_following = FollowersCount.objects.filter(follower=request.user.username)

    user_following_list = []
    feed = []

    user_posts = Post.objects.filter(user=request.user.username)
    feed.append(user_posts)

    for user in user_following:
        user_following_list.append(user.user)

    for username in user_following_list:
        feed_posts = Post.objects.filter(user=username)
        feed.append(feed_posts)

    posts = list(chain(*feed))
    posts = sort_posts(posts)
    
    # if (len(posts) > 50):
    #     posts = posts[:50]

    # user suggestions
    suggestions_profiles = get_suggestions(request, user_following)

    context = {
        'user_profile': user_profile,
        'posts': posts,
        'suggestions': suggestions_profiles[:4]
        }
    return render(request, 'index.html', context)

@login_required(login_url='signin')
def profile(request, pk):
    user_object = User.objects.get(username=pk)
    user_profile = Profile.objects.get(user=user_object)
    user_posts = Post.objects.filter(user=pk)
    user_posts_length = len(user_posts)
    user_followers = len(FollowersCount.objects.filter(user=pk))
    user_following = len(FollowersCount.objects.filter(follower=pk))

    follower = request.user.username
    user = pk

    if FollowersCount.objects.filter(follower=follower, user=user).first():
        button_text = 'Unfollow'
    else:
        button_text = 'Follow'

    if user_posts_length > 0:
        random_post = random.choice(user_posts)
    else:
        random_post = None

    context = {
        'user_object': user_object,
        'user_profile': user_profile,
        'user_posts': user_posts,
        'user_posts_length': user_posts_length,
        'user_followers': user_followers,
        'user_following': user_following,
        'button_text': button_text,
        'display_post': random_post
        }
    return render(request, 'profile.html', context)

@login_required(login_url='signin')
def follow(request):
    if request.method == 'POST':
        follower = request.POST['follower']
        user = request.POST['user']
        current_follower = FollowersCount.objects.filter(follower=follower, user=user).first()

        if current_follower:
            current_follower.delete()
        else:
            current_follower = FollowersCount.objects.create(follower=follower, user=user)
            current_follower.save()
        
        return redirect(f'/profile/{user}')
    else:
        return redirect('/')

@login_required(login_url='signin')
def search(request):
    user_object = User.objects.get(username=request.user.username)
    user_profile = Profile.objects.get(user=user_object)

    if request.method == 'POST':
        username = request.POST['username']
        username_objects = User.objects.filter(username__icontains=username)

        username_profiles = []
        username_profiles_list = []

        for user in username_objects:
            username_profiles.append(user.id)

        for id in username_profiles:
            profile_lists = Profile.objects.filter(id_user=id)
            username_profiles_list.append(profile_lists)

        username_profiles_list = list(chain(*username_profiles_list))
    
    context = {
        'user_profile': user_profile, 
        'username': username,
        'username_profiles_list': username_profiles_list
        }
    return render(request, 'search.html', context)

@login_required(login_url='signin')
def upload(request):
    if request.method == 'POST':
        user = request.user.username
        image = request.FILES.get('image_upload')
        caption = request.POST['caption']

        new_post = Post.objects.create(user=user, image=image, caption=caption)
        new_post.save()

    return redirect('/')

@login_required(login_url='signin')
def like_post(request):
    username = request.user.username
    post_id = request.GET.get('post_id')
    post = Post.objects.get(id=post_id)
    like_filter = LikePost.objects.filter(post_id=post_id, username=username).first()
    
    if like_filter == None:
        new_like = LikePost.objects.create(post_id=post_id, username=username)
        new_like.save()
        post.no_of_likes = post.no_of_likes+1
    else:
        like_filter.delete()
        post.no_of_likes = post.no_of_likes-1

    post.save()
    return redirect('/')

@login_required(login_url='signin')
def delete_post(request):
    if request.method == 'POST':
        id = request.POST['post_id']

        try:
            checked = request.POST['checked']
        except:
            checked = None
        
        if checked:
            post = Post.objects.get(id=id)
            post.delete()

        return redirect(f'/profile/{request.user.username}')
    else:
        return redirect('/')

@login_required(login_url='signin')
def settings(request):
    user_profile = Profile.objects.get(user=request.user)

    if request.method == 'POST':
        image = request.FILES.get('image')
        if image == None:
            image = user_profile.profileimg

        bio = request.POST['bio']
        location = request.POST['location']

        user_profile.profileimg = image
        user_profile.bio = bio
        user_profile.location = location
        user_profile.save()

        return redirect('settings')

    return render(request, 'settings.html', {'user_profile': user_profile})

def signup(request):
    if request.method == 'POST':
        username = request.POST['username']
        email = request.POST['email']
        password = request.POST['password']
        password2 = request.POST['password2']

        if password == password2:
            if User.objects.filter(email=email).exists():
                messages.info(request, 'The entered email already has an associated account')
                return redirect('signup')
            elif User.objects.filter(username=username).exists():
                messages.info(request, 'Username Taken')
                return redirect('signup')
            else:
                user = User.objects.create_user(username=username, email=email, password=password)
                user.save()

                # create a profile object for new user
                user_model = User.objects.get(username=username)
                new_profile = Profile.objects.create(user=user_model, id_user=user_model.id)
                new_profile.save()

                # log user in and redirect to settings page
                user_login = auth.authenticate(username=username, password=password)
                auth.login(request, user_login)
                return redirect('settings')

        else:
            messages.info(request, 'Passwords Do Not Match')
            return redirect('signup')

    else:
        return render(request, 'signup.html')

def signin(request):
    if request.method == 'POST':
        username = request.POST['username']
        password = request.POST['password']

        user = auth.authenticate(username=username, password=password)

        if user is not None:
            auth.login(request, user)
            return redirect('/')
        else:
            messages.info(request, 'Credentials Invalid')
            return redirect('/signin')
    else:
        return render(request, 'signin.html')

@login_required(login_url='signin')
def logout(request):
    auth.logout(request)
    return redirect('signin')