from django.shortcuts import get_object_or_404, render

from .models import Post


def blog_home(request):
    posts = Post.objects.order_by("-created_at")
    return render(request, "core/post_list.html", {"posts": posts})


def post_detail(request, pk):
    post = get_object_or_404(Post, pk=pk)
    return render(request, "core/post_detail.html", {"post": post})
