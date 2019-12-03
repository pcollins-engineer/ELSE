import xlrd
import datetime
import logging
from evaluations.models import Student, Instructor, Course, Enrollment
from django.core.exceptions import ValidationError
import string
import random


class RegistrationParser():

    def __init__(self, excel_file_path):
        # check if file exists?
        self.workbook = xlrd.open_workbook(excel_file_path)
        self.sheet = self.workbook.sheet_by_index(0)
        self.fields = self.sheet.row_values(0)

    def generate_token(self):
        return "".join(random.choice(string.ascii_letters) for i in range(64))

    def parse_all(self):
        for index in range(1, self.sheet.nrows):
            try:
                entry = dict(zip(self.fields, self.sheet.row_values(index)))
                student_data, instructor_data, course_data, enrollment_data = self.parse_entry(
                    entry
                )
                student = Student.objects.filter(id=student_data["id"]).first()
                if not student:
                    student = Student(**student_data, token=self.generate_token())
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

    def parse_date(self, excel_date):
        if excel_date == "":
            return None
        xlrd_date = xlrd.xldate_as_tuple(
            excel_date, self.workbook.datemode
        )
        return datetime.datetime(*xlrd_date).strftime("%Y-%m-%d")
