"""
Registration Parser
Author: Peter Collins

The registration parser uses the xlrd Python package in order to parse the provided Excel registration
roster file. The parser iterates over the data and creates instances of Django models in order to populate
the database.
"""
import random
import string
from django.core.exceptions import ValidationError
from evaluations.models import Student, Instructor, Course, Enrollment
import logging
import datetime
import xlrd


class RegistrationParser():

    """
    The constructor accepts the path to an Excel registration roster file and parses relevant information.
    """

    def __init__(self, excel_file_path):
        self.workbook = xlrd.open_workbook(excel_file_path)
        self.sheet = self.workbook.sheet_by_index(0)
        self.fields = self.sheet.row_values(0)

    """
    The generate_token method generates a random 64 character ASCII string to be used as secure tokens for
    authenticating students and instructors.
    """

    def generate_token(self):
        return "".join(random.choice(string.ascii_letters) for i in range(64))

    """
    The parse_all method is the primary method of the parser. The method iterates over all rows in the Excel
    spreadsheet and serializes the data into a format the Django models will understand. In each iteration
    a database lookup is performed to see if a record already exists, if not a token is generated and an object
    instance is created. The method takes no parameter and returns no values.
    """

    def parse_all(self):
        for index in range(1, self.sheet.nrows):
            try:
                entry = dict(zip(self.fields, self.sheet.row_values(index)))
                student_data, instructor_data, course_data, enrollment_data = self.parse_entry(
                    entry
                )
                student = Student.objects.filter(id=student_data["id"]).first()
                if not student:
                    student = Student(
                        **student_data, token=self.generate_token())
                    student.full_clean()
                    student.save()
                instructor = Instructor.objects.filter(
                    email=instructor_data["email"]).first()
                if not instructor:
                    instructor = Instructor(
                        **instructor_data, token=self.generate_token())
                    instructor.full_clean()
                    instructor.save()
                course = Course.objects.filter(id=course_data["id"]).first()
                if not course:
                    course = Course(
                        **course_data, instructor=instructor, token=self.generate_token())
                    course.full_clean()
                    course.save()
                enrollment = Enrollment(
                    **enrollment_data, student=student, course=course, token=self.generate_token()
                )
                enrollment.full_clean()
                enrollment.save()
            except ValidationError as ve:
                logging.error(ve)
            except Exception as e:
                print(e)

    """
    The parse_entry method normalizes data from a spreadsheet row (zipped with column headers) into a tuple
    of dictonaries which the Django models can readily accept. The method accepts a parameter of a dict row
    entry and returns a tuple of dicts containing normalized data.
    """

    def parse_entry(self, entry):
        student_data = dict(
            id=entry["Student ID"],
            email=entry["Student Email"]
        )
        instructor_data = dict(
            last_name=entry["Instructor"],
            email=entry["Instructor Email"]
        )
        course_data = dict(
            id=int(entry["Class Nbr"]),
            term=int(entry["Term"]),
            subject=entry["Subject"],
            catalog=entry["Catalog"].strip(),
            title=entry["Title"],
            section=int(entry["Section"]),
            total_enrollment=int(entry["Tot Enrl"]),
            units=int(entry["Unit Taken"]),
            campus=entry["Campus"],
            location=int(entry["Location"]),
            combined=entry["Comb Sect"] == "C",
            career=entry["Career"],
            component=entry["Component"],
            session=int(entry["Session"]),
            course_type=entry["Class Type"],
            grade_base=entry["Grade Base"]
        )
        drop_date = self.parse_date(entry["Drop Dt"])
        add_date = self.parse_date(entry["Add Dt"])
        enrollment_data = dict(
            grade=entry["Grade"],
            drop_date=drop_date,
            add_date=add_date,
            dropped=drop_date != None
        )
        return student_data, instructor_data, course_data, enrollment_data

    """
    The parse_data method is a helper method to format dates given Excels unique method of representation.
    The method accepts an Excel formatted data as a parameter and returns a Python datetime object.
    """

    def parse_date(self, excel_date):
        if excel_date == "":
            return None
        xlrd_date = xlrd.xldate_as_tuple(
            excel_date, self.workbook.datemode
        )
        return datetime.datetime(*xlrd_date).strftime("%Y-%m-%d")
