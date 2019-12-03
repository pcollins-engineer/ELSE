"""
ELSE Model Definition
Author: Peter Collins

In order to perform CRUD operations with the database we utilize Django models. The defintions
can be found below.
"""

from django.db import models


class Status(models.Model):
    active = models.BooleanField(default=False)
    populated = models.BooleanField(default=False)


class Student(models.Model):
    id = models.CharField(max_length=16, primary_key=True)
    email = models.CharField(max_length=256)
    token = models.CharField(max_length=64)


class Instructor(models.Model):
    email = models.CharField(max_length=256, primary_key=True)
    last_name = models.CharField(max_length=256)
    token = models.CharField(max_length=64)


class Course(models.Model):
    id = models.PositiveIntegerField(primary_key=True)
    instructor = models.ForeignKey(Instructor, on_delete=models.CASCADE)
    students = models.ManyToManyField(Student, through="Enrollment")
    title = models.CharField(max_length=256)
    campus = models.CharField(max_length=256)
    token = models.CharField(max_length=64)
    component = models.CharField(max_length=8)
    grade_base = models.CharField(max_length=8)
    subject = models.CharField(max_length=4)
    catalog = models.CharField(max_length=4)
    career = models.CharField(max_length=4)
    course_type = models.CharField(max_length=2)
    term = models.PositiveSmallIntegerField()
    section = models.PositiveSmallIntegerField()
    total_enrollment = models.PositiveSmallIntegerField()
    units = models.PositiveSmallIntegerField()
    location = models.PositiveSmallIntegerField()
    session = models.PositiveSmallIntegerField()
    combined = models.BooleanField()


class Enrollment(models.Model):
    student = models.ForeignKey(Student, on_delete=models.CASCADE)
    course = models.ForeignKey(Course, on_delete=models.CASCADE)
    grade = models.CharField(max_length=2, null=True, blank=True)
    token = models.CharField(max_length=64)
    drop_date = models.DateField(null=True, blank=True, default="")
    add_date = models.DateField()
    dropped = models.BooleanField()
    evaluated = models.BooleanField(default=False)


class Question(models.Model):
    RESPONSE_TYPES = [
        ("TXT", "Text"),
        ("NUM", "Number")
    ]
    prompt = models.CharField(max_length=1000)
    response_type = models.CharField(max_length=3, choices=RESPONSE_TYPES)


class Response(models.Model):
    enrollment = models.ForeignKey(Enrollment, on_delete=models.CASCADE)
    question = models.ForeignKey(Question, on_delete=models.CASCADE)


class TextResponse(Response, models.Model):
    feedback = models.CharField(max_length=1000)


class NumberResponse(Response, models.Model):
    feedback = models.PositiveSmallIntegerField()
