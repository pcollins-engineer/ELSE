"""ELSE URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/2.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path
import evaluations.views

urlpatterns = [
    path("admin/", admin.site.urls),
    path("administration/", evaluations.views.Administration.as_view()),
    path("parser", evaluations.views.Parser.as_view()),
    path("questions", evaluations.views.Questions.as_view()),
    path("students/<slug:student_id>/<slug:token>",
         evaluations.views.Students.as_view()),
    path("instructors/<slug:last_name>/<slug:token>",
         evaluations.views.Instructors.as_view()),
    path("survey/<slug:student_id>/<slug:course_id>/<slug:token>",
         evaluations.views.Survey.as_view()),
    path("feedback/<slug:last_name>/<slug:course_id>/<slug:token>",
         evaluations.views.Feedback.as_view()),
]
