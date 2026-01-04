from django.urls import path

from . import views

app_name = "hardware"

urlpatterns = [
    path("", views.HomeView.as_view(), name="home"),
    path("despre/", views.AboutView.as_view(), name="despre"),
    path("info/", views.info, name="info"),
    path("log/", views.log_view, name="log"),
    path("produse/", views.ProductsListView.as_view(), name="products"),
    path(
        "categorii/<slug:slug>/",
        views.CategoryDetailView.as_view(),
        name="category_detail",
    ),
    path(
        "branduri/<slug:slug>/",
        views.BrandProductsView.as_view(),
        name="brand_detail",
    ),
    path("produse/adauga/", views.ProductCreateView.as_view(), name="product_create"),
    path("catalog/", views.ProductsListView.as_view(), name="catalog"),
    path(
        "catalog/categorie/<slug:slug>/",
        views.CategoryDetailView.as_view(),
        name="catalog_by_category",
    ),
    path(
        "catalog/brand/<slug:slug>/",
        views.BrandProductsView.as_view(),
        name="catalog_by_brand",
    ),
    path("produs/<slug:slug>/", views.ProductDetailView.as_view(), name="product_detail"),
    path("promotii/", views.PromotionView.as_view(), name="promotii"),
    path("cart/", views.cart_detail, name="cart"),
    path("cart/add/<slug:slug>/", views.cart_add, name="cart_add"),
    path("cart/update/<slug:slug>/", views.cart_update, name="cart_update"),
    path("cart/remove/<slug:slug>/", views.cart_remove, name="cart_remove"),
    path("contact/", views.ContactView.as_view(), name="contact"),
    path("tutoriale/", views.TutorialsListView.as_view(), name="tutoriale"),
    path(
        "tutoriale/<slug:slug>/",
        views.TutorialDetailView.as_view(),
        name="tutorial_detail",
    ),
]
