"""
ELSE View Definition
Author: Peter Collins

The meat of the application is defined here. The business logic of each view is housed in a named class.
Class based views are utilized which define actions for GET and POST requests or both in some cases.
Small messages are returned using the HttpResponse method while for more complex views a template is rendered.
"""

import xlrd
import datetime
from django.shortcuts import render
from django.http import HttpResponse
from django.views import View
from evaluations.models import Instructor, Course, Student, Enrollment
from evaluations.models import Status, Question, TextResponse, NumberResponse, Response
from evaluations.registration_parser import RegistrationParser
from django.core.mail import send_mail


"""
The Administration view provides the functionality to manage the ELSE system.
"""
class Administration(View):

    """
    The send_survey method generates a link with a secure token for each student and sends emails.
    """
    def send_survey(self):
        domain = "https://p1collins.pythonanywhere.com/"
        sender = "scu.engr.evaluations@gmail.com"
        students = Student.objects.all()
        for student in students:
            link = domain + "students/" + student.id + "/" + student.token
            send_mail("Survey", link, "scu.engr.evaluations@gmail.com", [student.email])

    """
    The send_responses method generates a link with a secure token for each instructors and sends emails.
    """
    def send_responses(self):
        instructors = Instructor.objects.all()
        domain = "https://p1collins.pythonanywhere.com/"
        sender = "scu.engr.evaluations@gmail.com"
        for instructor in instructors:
            link = domain + "instructors/" + instructor.last_name + "/" + instructor.token
            send_mail("Feedback", link, "scu.engr.evaluations@gmail.com", [instructor.email])

    """
    The GET method of the Administration view queries information about the system. The system status,
    database record counts, and list of questions are retreived from the database and passed to the template
    for rendering. The method accepts a request object and returns a rendered template response.
    """
    def get(self, request):
        status = Status.objects.filter(id=1).first()
        active = False
        populated = False
        if status:
            active = status.active
            populated = status.populated
        context = {
            "instructors": len(Instructor.objects.all()),
            "courses": len(Course.objects.all()),
            "students": len(Student.objects.all()),
            "enrollments": len(Enrollment.objects.all()),
            "responses": len(Enrollment.objects.filter(evaluated=True)),
            "active": active,
            "populated": populated,
            "questions": Question.objects.all()
        }
        return render(request, "administration.html", context)

    """
    The POST method of the Administration view handles starting and stopping the collection period.
    Safety checks are built in to prevent starting without an imported roster or set questions. In addition,
    surveys cannot be stopped which have not been started. On start and stop of the survey collection period
    the appropriate emails are called to send emails. The method takes in a request object and returns a HttpResponse
    message.
    """
    def post(self, request):
        admin_action = request.POST.get("admin-action", None)
        if not Status.objects.filter(id=1).first():
            return HttpResponse("Error a registration roster has not been imported. <br><a href=''>Continue</a>")
        status = Status.objects.get(id=1)
        if not status.populated:
            return HttpResponse("Error a registration roster has not been imported. <br><a href=''>Continue</a>")
        if len(Question.objects.all()) == 0:
            return HttpResponse("Error no questions created. <br><a href=''>Continue</a>")
        if status.active:
            if admin_action == "Start":
                return HttpResponse("Error a collection period is already active. <br><a href=''>Continue</a>")
            elif admin_action == "Stop":
                Status.objects.filter(id=1).update(active=False)
                self.send_responses()
                return HttpResponse("The survey responses have been sent to instructors and the collection period has ended. <br><a href=''>Continue</a>")
        else:
            if admin_action == "Start":
                Status.objects.filter(id=1).update(active=True)
                self.send_survey()
                return HttpResponse("The survey has been sent to students and the collection period has begun. <br><a href=''>Continue</a>")
            elif admin_action == "Stop":
                return HttpResponse("Error no collection period is active. <br><a href=''>Continue</a>")
        return HttpResponse("An unknown error has occured. <br><a href=''>Continue</a>")

"""
The Parser view provides the functionality to populate the database with a provided roster.
"""
class Parser(View):
    """
    The save_uploaded_file method takes a file object and writes it to disk in chunks. The method
    has advtanges over writing the entire file to disk at once in case an incredibly large file
    is uploaded. The file is always written to be 'registration-roster.xlsx' and overwrites the
    file if it exists.
    """
    def save_uploaded_file(self, f):
        with open("registration-roster.xlsx", "wb+") as destination:
            for chunk in f.chunks():
                destination.write(chunk)

    """
    The flush_db method removes all model instances from the database except questions. The method
    takes no parameters and returns no value.
    """
    def flush_db(self):
        Student.objects.all().delete()
        Instructor.objects.all().delete()
        Course.objects.all().delete()
        Enrollment.objects.all().delete()
        TextResponse.objects.all().delete()
        NumberResponse.objects.all().delete()

    """
    The POST method of the Parser view handles parsing a given registration roster Excel file. A number of
    safety checks are built into this method. A roster cannot be parsed if a collection period is active.
    An error is given if no file is provided. An error is given if the file cannot be written. The 
    RegistrationParser class is used for the actual parsing of the file. The status is updated to populated
    as true upon a successful parse and a success message is returned. The method accepts a request object with
    a FILES array attribute containing key 'registration-roster' and returns an HttpResponse message.
    """
    def post(self, request):
        status = Status.objects.filter(id=1).first()
        if status:
            if status.active:
                return HttpResponse("Error a collection period is active. <br><a href='/administration'>Continue</a>")
        else:
            Status.objects.create(id=1)
        roster_file = request.FILES.get("registration-roster", False)
        if not roster_file:
            return HttpResponse("No registration roster file uploaded. <br><a href='/administration'>Continue</a>")
        try:
            self.save_uploaded_file(roster_file)
        except Exception:
            return HttpResponse("Error writing registration roster file. <br><a href='/administration'>Continue</a>")
        try:
            self.flush_db()
            rp = RegistrationParser("registration-roster.xlsx")
            rp.parse_all()
        except Exception:
            return HttpResponse("Error parsing registration roster file. <br><a href='/administration'>Continue</a>")
        Status.objects.filter(id=1).update(populated=True)
        return HttpResponse("Registration roster successfully imported. <br><a href='/administration'>Continue</a>")


class Students(View):
    def get(self, request, student_id, token):
        student = Student.objects.filter(id=student_id).first()
        if not student or token != student.token:
            return HttpResponse("Invalid Request")
        is_active = False
        status = Status.objects.filter(id=1).first()
        if status:
            is_active = status.active
        if not is_active:
            return HttpResponse("Error no collection period is active.")

        unevaluated_enrollments = Enrollment.objects.filter(
            student=student, evaluated=False)
        if len(unevaluated_enrollments) == 0:
            return HttpResponse("No additional T.A.'s to evaluate.")
        context = {
            "student": student,
            "unevaluated_enrollments": unevaluated_enrollments
        }

        return render(request, "students.html", context)


class Instructors(View):
    def get(self, request, last_name, token):
        instructor = Instructor.objects.filter(
            last_name=last_name, token=token).first()
        if not instructor or token != instructor.token:
            return HttpResponse("Invalid Request")
        is_active = False
        status = Status.objects.filter(id=1).first()
        if status:
            is_active = status.active
        if is_active:
            return HttpResponse("Error collection period still active.")

        context = {
            "instructor": instructor,
            "courses": Course.objects.filter(instructor=instructor)
        }

        return render(request, "instructors.html", context)


class Feedback(View):
    def get(self, request, last_name, course_id, token):
        course = Course.objects.filter(id=course_id).first()
        if not course or course.token != token:
            return HttpResponse("Invalid Request")
        instructor = course.instructor
        if instructor.last_name != last_name:
            return HttpResponse("Invalid Request")
        is_active = False
        status = Status.objects.filter(id=1).first()
        if status:
            is_active = status.active
        if is_active:
            return HttpResponse("Error collection period still active.")
        questions = Question.objects.all()
        results = []
        for question in questions:
            feedback = []
            if question.response_type == "TXT":
                responses = TextResponse.objects.filter(question=question)
                for response in responses:
                    if response.enrollment.course == course:
                        feedback.append(response.feedback)
            elif question.response_type == "NUM":
                responses = NumberResponse.objects.filter(question=question)
                for response in responses:
                    if response.enrollment.course == course:
                        feedback.append(response.feedback)
            result = {
                "question": question,
                "feedback": feedback
            }
            results.append(result)
        context = {
            "results": results
        }
        link = "/instructors/" + instructor.last_name + "/" + instructor.token
        if len(results) == 0:
            return HttpResponse("No feedback. <br><a href='" + link + "'>Continue</a>")
        return render(request, "feedback.html", context)


class Survey(View):
    def get(self, request, student_id, course_id, token):
        student = Student.objects.filter(id=student_id).first()
        course = Course.objects.filter(id=course_id).first()
        link = "/students/" + student.id + "/" + student.token
        if not student or not course:
            return HttpResponse("Invalid Request")
        enrollment = Enrollment.objects.filter(
            student=student, course=course).first()
        if not enrollment or token != enrollment.token:
            return HttpResponse("Invalid Request")
        if enrollment.evaluated:
            return HttpResponse("Error survey already completed. <br><a href='" + link + "'>Continue</a>")
        is_active = False
        status = Status.objects.filter(id=1).first()
        if status:
            is_active = status.active
        if not is_active:
            return HttpResponse("Error no collection period is active.")
        context = {
            "student": student,
            "questions": Question.objects.all(),
            "enrollment": enrollment
        }
        return render(request, "survey.html", context)

    def post(self, request, student_id, course_id, token):
        student = Student.objects.filter(id=student_id).first()
        course = Course.objects.filter(id=course_id).first()
        link = "/students/" + student.id + "/" + student.token
        if not student or not course:
            return HttpResponse("Invalid Request")
        enrollment = Enrollment.objects.filter(
            student=student, course=course).first()
        if not enrollment or token != enrollment.token:
            return HttpResponse("Invalid Request")
        if enrollment.evaluated:
            return HttpResponse("Error survey already completed. <br><a href='" + link + "'>Continue</a>")
        is_active = False
        status = Status.objects.filter(id=1).first()
        if status:
            is_active = status.active
        if not is_active:
            return HttpResponse("Error no collection period is active.")
        for element in request.POST:
            if "response" in element:
                question_id = element.split("-")[1]
                question = Question.objects.filter(id=question_id).first()
                if question:
                    if question.response_type == "TXT":
                        TextResponse.objects.create(
                            enrollment=enrollment, question=question, feedback=request.POST[element])
                    elif question.response_type == "NUM":
                        NumberResponse.objects.create(
                            enrollment=enrollment, question=question, feedback=request.POST[element])
        Enrollment.objects.filter(
            student=student, course=course).update(evaluated=True)
        return HttpResponse("Survey responses saved. <br><a href='" + link + "'>Continue</a>")


class Questions(View):
    def post(self, request):
        status = Status.objects.filter(id=1).first()
        if status and status.active:
            return HttpResponse("Error questions cannot be modified while a collection period is active. <br><a href='/administration'>Continue</a>")
        question_types = ["NUM", "TXT"]
        question_actions = ["Save", "Delete"]
        question_prompt = request.POST.get("question-prompt", None)
        question_type = request.POST.get("question-type", None)
        question_action = request.POST.get("question-action", None)
        question_id = request.POST.get("question-id", None)
        if not question_action in question_actions or question_prompt == "":
            return HttpResponse("Error invalid action or empty prompt. <br><a href='/administration'>Continue</a>")
        if question_action == "Delete":
            question = Question.objects.filter(id=question_id).first()
            if question:
                question.delete()
                return HttpResponse("Question deleted. <br><a href='/administration'>Continue</a>")
            else:
                return HttpResponse("Error target question not found. <br><a href='/administration'>Continue</a>")
        if question_action == "Save":
            if not question_type in question_types:
                return HttpResponse("Error invalid question type. <br><a href='/administration'>Continue</a>")
            Question.objects.create(
                prompt=question_prompt, response_type=question_type)
            return HttpResponse("Question saved. <br><a href='/administration'>Continue</a>")
        return HttpResponse("An unknown error has occured. <br><a href='/administration'>Continue</a>")
