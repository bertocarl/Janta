from django.http import HttpResponse
from django.shortcuts import render, redirect
from django.contrib.auth import login, authenticate
from .forms import SignupForm
from django.contrib.sites.shortcuts import get_current_site
from django.utils.encoding import force_bytes, force_text
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.template.loader import render_to_string
from .tokens import account_activation_token
from django.contrib.auth.models import User
from django.core.mail import EmailMessage
from django.contrib.auth.decorators import login_required

def home(request):
    return render(request,'index.html')

def signup(request):
    if request.method == 'POST':
        form = SignupForm(request.POST)
        if form.is_valid():
            user = form.save(commit=False)
            user.is_active = False
            user.save()
            current_site = get_current_site(request)
            mail_subject = 'Activate your Janta account.'
            message = render_to_string('acc_active_email.html', {
                'user': user,
                'domain': current_site.domain,
                'uid':urlsafe_base64_encode(force_bytes(user.pk)),
                'token':account_activation_token.make_token(user),
            })
            to_email = form.cleaned_data.get('email')
            email = EmailMessage(
                        mail_subject, message, to=[to_email]
            )
            email.send()
            return HttpResponse('Please confirm your email address to complete the registration')
    else:
        form = SignupForm()
    return render(request, 'signup.html', {'form': form})

def activate(request, uidb64, token):
    try:
        uid = force_text(urlsafe_base64_decode(uidb64))
        user = User.objects.get(pk=uid)
    except(TypeError, ValueError, OverflowError, User.DoesNotExist):
        user = None
    if user is not None and account_activation_token.check_token(user, token):
        user.is_active = True
        user.save()
        login(request, user)
        # return redirect('home')
        return HttpResponse('Thank you for your email confirmation. Now you can login your account.')
    else:
        return HttpResponse('Activation link is invalid!')

@login_required(login_url='/accounts/login/')
def profile(request):
    current_user = request.user
    current_user_id=request.user.id
    form=CommentForm()
    comments=Comment.objects.all()
    comment_number=len(comments)
    print(current_user)
    # print(current_user_id)

    post_id = None
    if request.method == 'GET':
        post_id = request.GET.get('post_id')

    likes = 0
    if post_id:
        post = Post.objects.get(id=int(post_id))
        if post:
            likes = post.likes + 1
            post.likes =  likes
            post.save()
            print(likes)

        return redirect('profile.html')

    try:
        profile = Profile.objects.get(username=current_user)
        posts = Post.objects.filter(username_id=current_user_id)
        title = profile.name
        username = profile.username
        post_number= len(posts)
        # print(post_number)

    except ObjectDoesNotExist:
        return redirect('edit-profile')


    return render(request,"profile.html",{"profile":profile,"posts":posts,"form":form,"post_number":post_number,"title":title,"username":username,"comments":comments,"comment_number":comment_number})


@login_required(login_url='/accounts/login/')
def edit_profile(request):
    current_user=request.user
    if request.method =='POST':
        form=ProfileForm(request.POST,request.FILES)
        if form.is_valid():
            profile=form.save(commit=False)
            profile.username = current_user
            profile.save()

    else:
        form=ProfileForm()

    return render(request,'edit_profile.html',{"form":form})

def comment(request):
    print("AJAX is working")

    comment = request.GET.get('comment')
    post = request.GET.get('post')
    username = request.user

    comment = Comment(comment=comment,post=post,username=username)
    comment.save()

    recent_comment= f'{Comment.objects.all().last().comment}'
    recent_comment_user = f'{Comment.objects.all().last().username}'
    data= {
        'recent_comment': recent_comment,
        'recent_comment_user':recent_comment_user
    }

    return JsonResponse(data)


@login_required(login_url='/accounts/login/')
def like(request):
    post_id = None
    if request.method == 'GET':
        post_id = request.GET.get('post_id')

    likes = 0
    if post_id:
        post = Post.objects.get(id=int(post_id))
        if post:
            likes = post.likes + 1
            post.likes =  likes
            post.save()
            print(likes)
    return HttpResponse(likes)

@login_required(login_url='/accounts/login/')
def search_results(request):
    if 'user' in request.GET and request.GET["user"]:
        search_term = request.GET.get("user")
        searched_users = Profile.search_profile(search_term)
        message=f"{search_term}"

        return render(request,'search.html',{"message":message,"users":searched_users})

    else:
        message="You haven't searched for any term"
        return render(request,'search.html',{"message":message})

@login_required(login_url='/accounts/login/')
def userprofile(request,profile_id):
    current_user=request.user
    form =CommentForm()
    comments=Comment.objects.all()

    try:
        all_posts=Post.objects.all()
        profile = Profile.objects.get(id=profile_id)
        prof_username = profile.username
        posts = Post.objects.filter(username=prof_username)
    except:
        raise ObjectDoesNotExist()
    return render(request,"user-profile.html",{"profile":profile,"posts":posts,"form":form,"comments":comments})


@login_required(login_url='/accounts/login/')
def change_profile(request,username):
    current_user = request.user
    if request.method == 'POST':
        form = ProfileForm(request.POST,request.FILES)
        if form.is_valid():
            caption = form.save(commit=False)
            caption.username = current_user
            caption.save()
        return redirect('index')
    elif Profile.objects.get(username=current_user):
        profile = Profile.objects.get(username=current_user)
        form = ProfileForm(instance=profile)
    else:
        form = ProfileForm()

    return render(request,'change_profile.html',{"form":form})
