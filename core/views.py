from django.shortcuts import render

from .models import Post


def blog_home(request):
    posts = Post.objects.order_by("-created_at")
    return render(request, "core/post_list.html", {"posts": posts})
