"""
ELSE URL Configuration
Author: Peter Collins

The routing of the various URL endpoints used in the application are defined here. URL's which
require authentication are padded with login_required to redirect users if they are not yet 
authenticated. URL endpoints are linked to view methods from evaluations.views.
"""

from django.contrib import admin
from django.urls import path, include
import evaluations.views
from django.contrib.auth.decorators import login_required

urlpatterns = [
    path("admin/", admin.site.urls),
    path("administration/", login_required(evaluations.views.Administration.as_view())),
    path("parser", login_required(evaluations.views.Parser.as_view())),
    path("questions", login_required(evaluations.views.Questions.as_view())),
    path("students/<slug:student_id>/<slug:token>",
         evaluations.views.Students.as_view()),
    path("instructors/<slug:last_name>/<slug:token>",
         evaluations.views.Instructors.as_view()),
    path("survey/<slug:student_id>/<slug:course_id>/<slug:token>",
         evaluations.views.Survey.as_view()),
    path("feedback/<slug:last_name>/<slug:course_id>/<slug:token>",
         evaluations.views.Feedback.as_view()),
    path("accounts/", include('django.contrib.auth.urls')),
]
