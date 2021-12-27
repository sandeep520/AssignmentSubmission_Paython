from django.db import models
from datetime import datetime

# Create your models here.


class CourseSem(models.Model):
    course = models.CharField(max_length=50)

    def __str__(self):
        return self.course


class Teacher(models.Model):
    first_name = models.CharField(max_length=50)
    last_name = models.CharField(max_length=50)
    email = models.CharField(max_length=100)
    password = models.CharField(max_length=50)

    def __str__(self):
        return self.first_name

    def signup(self):
        self.save()

    @staticmethod
    def get_teacher_by_email(email):
        try:
            return Teacher.objects.get(email=email)
        except:
            return False


class Subject(models.Model):
    sub_name = models.CharField(max_length=50)
    credit = models.IntegerField(default=0)
    course = models.ForeignKey(CourseSem, on_delete=models.CASCADE)
    assign_teacher = models.ForeignKey(Teacher, on_delete=models.CASCADE)

    def __str__(self):
        return self.sub_name

    @staticmethod
    def get_subjects_by_course(course_name):
        return Subject.objects.filter(course=course_name)


class Student(models.Model):
    roll_no = models.PositiveIntegerField(max_length=3)
    first_name = models.CharField(max_length=50)
    last_name = models.CharField(max_length=50)
    email = models.CharField(max_length=100)
    password = models.CharField(max_length=50)
    course = models.ForeignKey(CourseSem, on_delete=models.CASCADE)

    def __str__(self):
        return str(self.id)

    def signup(self):
        self.save()

    @staticmethod
    def get_user_by_email(email):
        try:
            return Student.objects.get(email=email)
        except:
            return False

    @staticmethod
    def get_students_by_course(course_name):
        try:
            return Student.objects.filter(course=course_name)
        except:
            return False


class Assignment(models.Model):
    title = models.CharField(max_length=100)
    Description = models.CharField(max_length=500, null=True)
    file_url = models.FileField(null=True)
    subject = models.ForeignKey(Subject, on_delete=models.CASCADE)
    teacher = models.ForeignKey(Teacher, on_delete=models.CASCADE)
    start_date = models.DateTimeField()
    end_date = models.DateTimeField()
    course = models.ForeignKey(CourseSem, on_delete=models.CASCADE)
    total_points = models.PositiveIntegerField(default=50)

    def __str__(self):
        return str(self.id)

    @staticmethod
    def get_assignments_by_course(course_name):
        return Assignment.objects.filter(course=course_name)

    def save_assignment(self):
        self.save()


class Solution(models.Model):
    st_id = models.ForeignKey(Student, on_delete=models.CASCADE)
    subject = models.ForeignKey(Subject, on_delete=models.CASCADE)
    que_ass_id = models.ForeignKey(Assignment, on_delete=models.CASCADE)
    submit_date = models.DateTimeField()
    ans_url = models.FileField()
    status = models.BooleanField(default=False)
    marks = models.PositiveIntegerField(null=True)
    done_status = models.CharField(max_length=100)

    def __str__(self):
        return str(self.id)

    def save_solution(self):
        self.save()


class Attendancedetails(models.Model):
    st_id = models.ForeignKey(Student, on_delete=models.CASCADE)
    attendance_date = models.DateTimeField()
    subject_id = models.ForeignKey(Subject, on_delete=models.DO_NOTHING)
    created_at = models.DateTimeField(default=datetime.now, blank=True)
    status = models.BooleanField(default=0)
    # updated_at = models.DateTimeField(default=datetime.now, blank=True)


class midtermmarks(models.Model):
    st_id = models.ForeignKey(Student, on_delete=models.CASCADE)
    subject_id = models.ForeignKey(Subject, on_delete=models.DO_NOTHING)
    outofmid = models.PositiveIntegerField()
    midtermmark = models.PositiveIntegerField()
    outofinternal = models.PositiveIntegerField()
    internalmarks = models.PositiveIntegerField()
    month = models.CharField(max_length=50)
    year = models.CharField(max_length=50)
