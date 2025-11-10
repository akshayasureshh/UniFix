from django.urls import path, include
from rest_framework.routers import DefaultRouter
from rest_framework_nested import routers
from . import views

router = DefaultRouter()

router.register(r'issues', views.IssueViewSet, basename='issue')
router.register(r'comments', views.CommentViewSet, basename='comment')
router.register(r'categories', views.CategoryViewSet, basename='category')
router.register(r'locations', views.LocationViewSet, basename='location')
router.register(r'auth', views.AuthViewSet, basename='auth')

urlpatterns = [
      path('', include(router.urls)),
]
