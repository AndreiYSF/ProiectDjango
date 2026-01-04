from django.urls import path

from .views import blog_home, post_detail

app_name = "core"

urlpatterns = [
    path("", blog_home, name="blog_home"),
    path("<int:pk>/", post_detail, name="post_detail"),
]
