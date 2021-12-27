from django.urls import path
from . import views
from .views import Pdf

urlpatterns = [
    # main
    path('home/', views.home, name='home'),

    # students urls
    path('signupstudent/', views.signupstudent, name='studentsignup'),
    path('signin', views.signin, name='signin'),
    path('student_dashboard/', views.student_dashboard, name='student_dashboard'),
    path('view_assign_student/', views.view_assignments_student,
         name='view_assign_student'),
    path('upload_solution/', views.upload_solution, name='upload_solution'),
    path('view_students/', views.view_students, name='view_students'),
    path('my_score/', views.my_score, name='my_score'),
    path('subject_list/', views.subject_list, name='subject_list'),
    path('todo_list/', views.todo_list, name='todo_list'),
    path('my_solutions/', views.my_solutions, name='my_solutions'),
    path('logout', views.logout, name='logout'),
    path('update_profile', views.update_profile, name='update_profile'),
    path('forgot_password_student', views.forgot_password_student,
         name='forgot_password_student'),
    path('reset_password_student', views.reset_password_student,
         name='reset_password_student'),
    path('edit_my_solutions/', views.edit_my_solutions, name='edit_my_solutions'),

    # teachers urls
    path('teacher_signin', views.teacher_signin, name='teacher_signin'),
    path('register_teacher', views.register_teacher, name='register_teacher'),
    path('teacher_dashboard/', views.teacher_dashboard, name='teacher_dashboard'),
    path('upload_assignments/', views.upload_assignments,
         name='upload_assignments'),
    path('my_assignments/', views.my_assignments, name='my_assignments'),
    path('view_solution/', views.view_solution, name='view_solution'),
    path('reject_solution/', views.reject_solution, name='reject_solution'),
    path('all_students/', views.all_students, name='all_students'),
    path('my_subjects/', views.my_subjects, name='my_subjects'),
    path('forgot_password_teacher', views.forgot_password_teacher,
         name='forgot_password_teacher'),
    path('reset_password_teacher', views.reset_password_teacher,
         name='reset_password_teacher'),
    path('assignment_reports/', views.assignment_reports,
         name='assignment_reports'),
    path('student_reports/', views.student_reports, name='student_reports'),
    path('logout_teacher', views.logout_teacher, name='logout'),
    path('update_profile_teacher', views.update_profile_teacher,
         name='update_profile_teacher'),
    path('render/pdf/', Pdf.as_view()),
    path('edit_my_assignments/', views.edit_my_assignments,
         name='edit_my_assignments'),
    path('attendance/', views.attendance, name='attendance'),
    path('attendance_reports/', views.attendance_reports,
         name='view_attendance_reports'),
    path('midtermmarks/', views.midterm, name='midtermmarks'),
]
