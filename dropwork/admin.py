from django.contrib import admin
from .models import CourseSem, Teacher, Subject, Student, Assignment, Solution

# Register your models here.


class AdminCourse(admin.ModelAdmin):
    list_display = ['id', 'course']


class AdminTeacher(admin.ModelAdmin):
    list_display = ['id', 'first_name', 'last_name', 'email', 'password']


class AdminSubject(admin.ModelAdmin):
    list_display = ['id', 'sub_name', 'credit', 'course', 'assign_teacher']


class AdminStudent(admin.ModelAdmin):
    list_display = ['id', 'roll_no', 'first_name',
                    'last_name', 'email', 'password', 'course']


class AdminAssignment(admin.ModelAdmin):
    list_display = ['id', 'title', 'Description', 'file_url', 'subject',
                    'teacher', 'start_date', 'end_date', 'course', 'total_points']


class AdminSolution(admin.ModelAdmin):
    list_display = ['id', 'st_id', 'subject', 'que_ass_id',
                    'ans_url', 'submit_date', 'status', 'marks', 'done_status']


# class AdminAttendance(admin.ModelAdmin):
#     list_display = ['id', 'st_id',
#                     'attendance_date', 'first_name', 'last_name']

#     def first_name(self, obj):
#         return obj.st_id.first_name

#     def last_name(self, obj):
#         return obj.st_id.last_name


admin.site.register(CourseSem, AdminCourse)
admin.site.register(Teacher, AdminTeacher)
admin.site.register(Subject, AdminSubject)
admin.site.register(Student, AdminStudent)
admin.site.register(Assignment, AdminAssignment)
admin.site.register(Solution, AdminSolution)
# admin.site.register(Attendance, AdminAttendance)
