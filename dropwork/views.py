from django.shortcuts import render, redirect, reverse
from django.http import HttpResponse
from django.contrib.auth.hashers import check_password
from .models import CourseSem, Student, Subject, Assignment, Teacher, Solution, Attendancedetails, midtermmarks
from django.contrib.auth.forms import UserCreationForm
from django.core.mail import send_mail
from django.conf import settings
from django.core.files.storage import FileSystemStorage
import datetime
import pytz
from json import dumps
from django.utils.encoding import smart_bytes
from django.core.signing import Signer
from django.core import signing

from io import StringIO
from xhtml2pdf import pisa
from django.template.loader import get_template
from django.template import Context
from django.http import HttpResponse
from html import escape

from django.views.generic import View
from django.utils import timezone
# from .render import Render
from django.contrib import messages


# Create your views here.
def home(request):
    return render(request, 'home.html')


def signupstudent(request):
    if request.method == 'GET':
        courses = CourseSem.objects.all()
        return render(request, 'signup_student.html', {'courses': courses})
    else:
        postData = request.POST
        firstname = postData.get('firstname')
        lastname = postData.get('lastname')
        email = postData.get('email')
        password = postData.get('pass')
        course = postData.get('courses')
        roll_no = postData.get('rollno')

        course_id = CourseSem.objects.get(pk=course)
        student = Student(roll_no=roll_no, first_name=firstname,
                          last_name=lastname, email=email, password=password, course=course_id)
        student.signup()
        return render(request, 'signin.html')


def signin(request):
    if request.method == 'GET':
        return render(request, 'signin.html')
    else:
        email = request.POST.get('email')
        password = request.POST.get('pass')
        user = Student.get_user_by_email(email)
        error_msg = None

        if user:
           # flag = check_password(password , user.password)
            if password == user.password:
                request.session['student_id'] = user.id
                return redirect('student_dashboard')
            else:
                error_msg = 'Email or Password invalid !!'
        else:
            error_msg = 'Email or Password invalid !!'

        return render(request, 'signin.html', {'error': error_msg})


def student_dashboard(request):
    student_id = request.session.get('student_id')
    if student_id:
        student = Student.objects.get(id=student_id)
        subjects = Subject.objects.filter(course=student.course)

        total_assigns = {}
        for sub in subjects:
            sub_assigns = Assignment.objects.filter(subject=sub).count()
            total_assigns[sub.sub_name] = sub_assigns
        for data in total_assigns:
            print(data)
        return render(request, 'student_dashboaed.html', {'subjects': subjects, 'total_assigns': total_assigns, 'student': student})
    else:
        return redirect('signin')


def view_assignments_student(request):
    student_id = request.session.get('student_id')
    if student_id:
        student = Student.objects.get(id=student_id)
        subjects = Subject.objects.filter(course=student.course)

        sub_id = request.GET.get('subject')
        if sub_id:
            sub_title = Subject.objects.get(id=sub_id)
            assignments = Assignment.objects.filter(subject=sub_id)
        else:
            sub_title = None
            assignments = Assignment.objects.filter(course=student.course)
        sub_list = []
        total_assigns = []
        for sub in subjects:
            sub_list.append(str(sub))
            assigns = Assignment.objects.filter(subject=sub).count()
            total_assigns.append(assigns)

        return render(request, 'view_assign_student.html', {'subjects': subjects, 'assignments': assignments, 'sub_list': dumps(sub_list), 'assign_count': dumps(total_assigns), 'sub': sub_title})
    else:
        return redirect('signin')


def upload_solution(request):
    if request.method == 'GET':
        student_id = request.session.get('student_id')
        student = Student.objects.get(id=student_id)
        subjects = Subject.objects.filter(course=student.course)
        assign_obj = None
        sub_id = request.GET.get('subject')
        assign_id = request.GET.get('assign')
        if sub_id:
            assignments = Assignment.objects.filter(subject=sub_id)
        else:
            assignments = Assignment.objects.filter(course=student.course)
        if assign_id:
            assign_obj = Assignment.objects.get(id=assign_id)
            request.session['assign_id'] = assign_obj.id
        solu_ids = []
        solu_status_ids = []
        student_solutions = Solution.objects.filter(st_id=student_id)
        for solu in student_solutions:
            solu_ids.append(solu.que_ass_id.id)
            if solu.status:
                solu_status_ids.append(solu.que_ass_id.id)

        return render(request, 'upload_solution.html', {'subjects': subjects, 'assignments': assignments, 'assign_obj': assign_obj, 'solutions': solu_ids, 'solution_status': solu_status_ids})
    else:
        student_id = request.session.get('student_id')
        student = Student.objects.get(id=student_id)
        subjects = Subject.objects.filter(course=student.course)

        assign_id = request.session.get('assign_id')
        assign_obj = Assignment.objects.get(id=assign_id)

        ans_url = request.FILES['uploadFile']

        st_id = Student.objects.get(pk=student_id)
        que_ass_id = Assignment.objects.get(pk=assign_id)

        done_status = 'In Time'
        utc = pytz.UTC
        now_date = utc.localize(datetime.datetime.now())
        if(now_date > que_ass_id.end_date):
            done_status = 'Late'
        msg = "Solution for " + que_ass_id.title+" uploaded successfully..."
        solution = Solution(st_id=st_id, subject=assign_obj.subject, que_ass_id=que_ass_id,
                            submit_date=datetime.datetime.now(), ans_url=ans_url, done_status=done_status)
        solution.save_solution()
        messages.success(request, msg)

        return redirect(reverse('upload_solution') + '?subject=' + str(assign_obj.subject.id))


def my_score(request):
    student_id = request.session.get('student_id')
    student = Student.objects.get(id=student_id)
    st_solutions = Solution.objects.filter(
        st_id=student_id).filter(status=True)
    all_marks = []
    all_assign = []
    for solu in st_solutions:
        all_assign.append(solu.que_ass_id.title)
        all_marks.append(solu.marks)
    total_report = []
    total_assigns = Assignment.objects.filter(course=student.course)
    uploaded_count = Solution.objects.filter(
        st_id=student_id).filter(status=False).count()
    completed = Solution.objects.filter(st_id=student_id).filter(status=True)
    remaining_count = total_assigns.count() - (uploaded_count + completed.count())
    total_report.extend([uploaded_count, completed.count(), remaining_count])

    total_marks_report = []
    total_marks = 0
    received_marks = 0
    for assign in total_assigns:
        total_marks += assign.total_points
    for assign in completed:
        received_marks += assign.marks
    total_marks_report.extend([total_marks, received_marks])

    subjects = Subject.objects.filter(course=student.course)
    sub_id = request.GET.get('subject')
    if sub_id:
        sub = Subject.objects.get(id=sub_id)
    else:
        sub = None
    sub_marks = []
    sub_assign = []
    total_sub_report = []
    total_sub_marks_report = []
    total_sub_assigns = []
    if sub_id:
        st_solutions = Solution.objects.filter(
            st_id=student_id).filter(subject=sub_id).filter(status=True)
        for solu in st_solutions:
            sub_assign.append(solu.que_ass_id.title)
            sub_marks.append(solu.marks)
        total_sub_assigns = Assignment.objects.filter(subject=sub_id)
        sub_uploaded_count = Solution.objects.filter(st_id=student_id).filter(
            subject=sub_id).filter(status=False).count()
        sub_completed = Solution.objects.filter(
            st_id=student_id).filter(subject=sub_id).filter(status=True)
        sub_remaining_count = total_sub_assigns.count(
        ) - (sub_uploaded_count + sub_completed.count())
        total_sub_report.extend(
            [sub_uploaded_count, sub_completed.count(), sub_remaining_count])

        total_sub_marks = 0
        received_sub_marks = 0
        for assign in total_sub_assigns:
            total_sub_marks += assign.total_points
        for assign in sub_completed:
            received_sub_marks += assign.marks
        total_sub_marks_report.extend([total_sub_marks, received_sub_marks])

    else:
        pass

    return render(request, 'my_score.html', {'subjects': subjects, 'marks': dumps(all_marks), 'assignments': dumps(all_assign), 'reports': dumps(total_report), 'total_assigns': total_assigns.count(), 'total_marks_report': total_marks_report, 'sub_marks': dumps(sub_marks), 'sub_assign': dumps(sub_assign), 'sub_reports': dumps(total_sub_report), 'sub': sub, 'total_sub_marks_report': total_sub_marks_report, 'total_sub_assigns': len(total_sub_assigns)})


def my_solutions(request):
    student_id = request.session.get('student_id')
    if student_id:
        student = Student.objects.get(id=student_id)
        subjects = Subject.objects.filter(course=student.course)

        solutions = Solution.objects.filter(st_id=student.id)
        sub_id = request.GET.get('subject')
        if sub_id:
            subject = Subject.objects.get(id=sub_id)
            solutions = Solution.objects.filter(
                st_id=student.id).filter(subject=subject)

        solu_status_ids = []
        student_solutions = Solution.objects.filter(st_id=student_id)
        for solu in student_solutions:
            if solu.status:
                solu_status_ids.append(solu.id)

        solu_id = request.GET.get('del_ass_id')
        if solu_id:
            Solution.objects.filter(id=solu_id).delete()
            return redirect(reverse('my_solutions'))

        return render(request, 'my_solutions.html', {'subjects': subjects, 'solutions': solutions, 'solu_status': solu_status_ids})
    else:
        return redirect('signin')


def register_teacher(request):
    if request.method == 'GET':
        return render(request, 'teacher/register_teacher.html')
    else:
        postData = request.POST
        firstname = postData.get('firstname')
        lastname = postData.get('lastname')
        email = postData.get('email')
        password = postData.get('pass')

        teacher = Teacher(first_name=firstname,
                          last_name=lastname, email=email, password=password)
        teacher.signup()
        return render(request, 'teacher/teacher_signin.html')


def teacher_signin(request):
    if request.method == 'GET':
        return render(request, 'teacher/teacher_signin.html')

    else:
        email = request.POST.get('email')
        password = request.POST.get('pass')
        teacher = Teacher.get_teacher_by_email(email)
        error_msg = None

        if teacher:
           # flag = check_password(password , user.password)
            if password == teacher.password:
                request.session['teacher_name'] = teacher.first_name
                request.session['teacher_id'] = teacher.id
                request.session['teacher_email'] = teacher.email
                try:
                    del request.session['subject_id']
                except:
                    pass
                return redirect('teacher_dashboard')
            else:
                error_msg = 'Email or Password invalid !!'
                return render(request, 'teacher/teacher_signin.html', {'error': error_msg})

        else:
            error_msg = 'Email or Password invalid !!'

        return render(request, 'teacher/teacher_signin.html', {'error': error_msg})


def teacher_dashboard(request):
    request.session['subject_id'] = None
    return render(request, 'teacher/dashboard.html')


def upload_assignments(request):
    t_id = request.session.get('teacher_id')
    if t_id:
        if request.method == 'GET':
            t_name = request.session.get('teacher_name')
            teacher_subjects = Subject.objects.filter(assign_teacher=t_id)
            return render(request, 'teacher/upload_assignments.html', {'subjects': teacher_subjects})
        else:
            teacher_subjects = Subject.objects.filter(assign_teacher=t_id)

            postData = request.POST
            title = postData.get('title')
            description = postData.get('description')
            file_url = request.FILES['file_url']
            start_date = postData.get('startDate')
            end_date = postData.get('endDate')
            subject = postData.get('subject')
            points = postData.get('points')

            teacher = Teacher.objects.get(pk=t_id)
            sub_id = Subject.objects.get(pk=subject)
            #print(title,description,file_url,start_date,end_date,subject, t_id, sub_id.course)

            assign = Assignment(title=title, Description=description, file_url=file_url, start_date=start_date,
                                end_date=end_date, total_points=points, subject=sub_id, teacher=teacher, course=sub_id.course)
            assign.save_assignment()
            success_msg = 'New Assignment of ' + sub_id.sub_name + ' uploaded successfully...'

            students_emails = []
            students = Student.objects.filter(course=sub_id.course)
            for st in students:
                students_emails.append(str(st.email))

            mail_subject = "Dropwork - New Assignment"
            message = teacher.first_name + " " + teacher.last_name + " have uploaded a new assignment for the subject of " + \
                sub_id.sub_name+". \nAssignment Title : "+title+"\nTotal Points : "+points
            email_from = settings.EMAIL_HOST_USER
            recipient_list = students_emails
            send_mail(mail_subject, message, email_from, recipient_list)

            return render(request, 'teacher/upload_assignments.html', {'subjects': teacher_subjects, 'msg': success_msg})
    else:
        return redirect('teacher_signin')


def logout(request):
    request.session.clear()
    return redirect('signin')


def view_solution(request):

    if request.method == 'GET':
        t_name = request.session.get('teacher_name')
        t_id = request.session.get('teacher_id')
        teacher_subjects = Subject.objects.filter(assign_teacher=t_id)

        sub_id = request.session.get('subject_id')
        msg = None
        if sub_id:
            assignments = Assignment.objects.filter(subject=sub_id)
            if assignments.count() == 0:
                msg = "There is no any assignments of selected subject..."
        else:
            assignments = None

        assign_id = request.GET.get('assign')
        if assign_id:
            solutions = Solution.objects.filter(que_ass_id=assign_id)
        else:
            solutions = None
        solu_id = request.GET.get('solu_id')
        marks = request.GET.get('marks')
        if solu_id and marks:
            solu_obj = Solution.objects.get(id=solu_id)
            solu_obj.marks = marks
            solu_obj.status = True
            solu_obj.save(update_fields=['marks', 'status'])

            mail_subject = "Dropwork - Assigned Marks"
            message = "Your assignment is checked... You have got "+marks+" marks out of " + \
                str(solu_obj.que_ass_id.total_points) + \
                " for "+str(solu_obj.que_ass_id.title)+"."
            email_from = settings.EMAIL_HOST_USER
            recipient_list = [str(solu_obj.st_id.email)]
            send_mail(mail_subject, message, email_from, recipient_list)

            return redirect(reverse('view_solution') + '?assign=' + str(solu_obj.que_ass_id))

        return render(request, 'teacher/view_solutions.html', {'subjects': teacher_subjects, 'assignments': assignments, 'solutions': solutions, 'msg': msg})
    else:
        sub_id = request.POST.get('subject')
        request.session['subject_id'] = sub_id
        return redirect('view_solution')


def reject_solution(request):
    t_id = request.session.get('teacher_id')
    if t_id:
        if request.method == 'GET':
            solu_id = request.GET.get('solu')
            solution = Solution.objects.get(id=solu_id)
            return render(request, 'teacher/reject_solution.html', {'solution': solution})
        else:
            solu_id = request.POST.get('solu_id')
            message = request.POST.get('message')
            solution = Solution.objects.get(id=solu_id)
            que_ass_id = solution.que_ass_id
            mail_subject = "Dropwork - Rejected Solution"
            message = "Your solution is rejected by " + solution.subject.assign_teacher.first_name + " " + solution.subject.assign_teacher.last_name + \
                "\nAssignment Title : " + solution.que_ass_id.title + "\nSubject : " + \
                solution.subject.sub_name + "\nReason : \n" + message + "."
            email_from = settings.EMAIL_HOST_USER
            recipient_list = [str(solution.st_id.email)]
            send_mail(mail_subject, message, email_from, recipient_list)

            Solution.objects.filter(id=solu_id).delete()
            return redirect(reverse('view_solution') + '?assign=' + str(que_ass_id))
    else:
        return redirect('teacher_signin')


def all_students(request):
    t_id = request.session.get('teacher_id')
    if t_id:
        teacher_subjects = Subject.objects.filter(assign_teacher=t_id)
        courses = set()
        for sub in teacher_subjects:
            courses.add(str(sub.course.course))
        course_name = request.GET.get('course')
        if course_name:
            course_id = CourseSem.objects.get(course=course_name)
            students = Student.objects.filter(course=course_id)
        else:
            students = None
        return render(request, 'teacher/all_students.html', {'courses': courses, 'students': students, 'course_name': course_name})
    else:
        return redirect('teacher_signin')


def view_students(request):
    student_id = request.session.get('student_id')
    student = Student.objects.get(id=student_id)
    classmates = Student.objects.filter(course=student.course)
    return render(request, 'view_students.html', {'classmates': classmates})


def subject_list(request):
    student_id = request.session.get('student_id')
    student = Student.objects.get(id=student_id)
    subjects = Subject.objects.filter(course=student.course)
    print(subjects)
    assign_list = []
    for sub in subjects:
        assign_count = Assignment.objects.filter(subject=sub).count()
        assign_list.append(assign_count)
    return render(request, 'subject_list.html', {'subjects': subjects, 'assign_list': assign_list})


def todo_list(request):
    student_id = request.session.get('student_id')
    student = Student.objects.get(id=student_id)
    que_assigns = Assignment.objects.filter(course=student.course)
    ans_assigns = Solution.objects.filter(st_id=student)
    ans_assigns_ids = []
    for ans in ans_assigns:
        ans_assigns_ids.append(ans.que_ass_id.id)
    todo_assigns = []
    for que in que_assigns:
        if que.id not in ans_assigns_ids:
            todo_assigns.append(que)

    return render(request, 'to-do_list.html', {'todo_list': todo_assigns})


def update_profile(request):
    student_id = request.session.get('student_id')
    if student_id:
        student = Student.objects.get(id=student_id)
        courses = CourseSem.objects.all()
        if request.method == 'GET':
            msg = None
            return render(request, 'update_profile.html', {'student': student, 'courses': courses, 'msg': msg})
        else:
            first_name = request.POST.get('firstname')
            last_name = request.POST.get('lastname')
            email = request.POST.get('email')
            course_id = request.POST.get('courses')
            roll_no = request.POST.get('roll_no')

            course_obj = CourseSem.objects.get(id=course_id)
            student = Student.objects.get(id=student_id)
            student.first_name = first_name
            student.last_name = last_name
            student.email = email
            student.course = course_obj
            student.roll_no = roll_no
            student.save(update_fields=[
                         'first_name', 'last_name', 'email', 'course', 'roll_no'])
            msg = "Your profile is upldated successfully..."

            return render(request, 'update_profile.html', {'student': student, 'courses': courses, 'msg': msg})
    else:
        return redirect('signin')


def my_subjects(request):
    t_id = request.session.get('teacher_id')
    if t_id:
        teacher_subjects = Subject.objects.filter(assign_teacher=t_id)
        return render(request, 'teacher/my_subject.html', {'subjects': teacher_subjects})
    else:
        return redirect('teacher_signin')


def forgot_password_student(request):
    if request.method == 'GET':
        return render(request, 'forgot_password_student.html')
    else:
        forget_email = request.POST.get('forget_email')
        student = Student.get_user_by_email(forget_email)
        msg = None
        if student:
            encoded_mail = signing.dumps(str(student.email))
            mail_subject = "Dropwork - Forgot Password"
            message = "open link for reset pasword : \n http://127.0.0.1:8000/reset_password_student?e=" + encoded_mail
            email_from = settings.EMAIL_HOST_USER
            recipient_list = [str(student.email)]
            send_mail(mail_subject, message, email_from, recipient_list)

            msg = 'You will receive an email for reset your password on your registered email ID...'
        else:
            msg = 'Please enter registered email...'

        return render(request, 'forgot_password_student.html', {'msg': msg})


def reset_password_student(request):
    msg = None
    if request.method == 'GET':
        email = request.GET.get('e')
        decoded_email = signing.loads(email)
        request.session['decoded_email'] = decoded_email
        return render(request, 'reset_password_student.html', {'msg': msg})
    else:
        new_pass = request.POST.get('password')
        student = Student.objects.get(
            email=request.session.get('decoded_email'))
        student.password = new_pass
        student.save(update_fields=['password'])
        msg = "Password reseted successfully..."
        return render(request, 'reset_password_student.html', {'msg': msg})


def assignment_reports(request):
    t_id = request.session.get('teacher_id')
    if t_id:
        if request.method == 'GET':
            teacher_subjects = Subject.objects.filter(assign_teacher=t_id)
            sub_id = request.session.get('subject_id')
            msg = None
            if sub_id:
                assignments = Assignment.objects.filter(subject=sub_id)
                if assignments.count() == 0:
                    msg = "There is no any assignments of selected subject..."
            else:
                assignments = None

            assign_id = request.GET.get('assign')
            if assign_id:
                assignment = Assignment.objects.get(id=assign_id)
            else:
                assignment = None
            completed_students = Solution.objects.filter(
                que_ass_id=assign_id).filter(status=True)
            uploaded_students = Solution.objects.filter(
                que_ass_id=assign_id).filter(status=False)
            remaining_students = []
            all_solutions = Solution.objects.filter(que_ass_id=assign_id)
            for solu in all_solutions:
                if (solu not in completed_students) and (solu not in uploaded_students):
                    remaining_students.append(solu)
            reports = []
            completed_count = Solution.objects.filter(
                que_ass_id=assign_id).filter(status=True).count()
            uploaded_count = Solution.objects.filter(
                que_ass_id=assign_id).filter(status=False).count()
            remaining_count = len(remaining_students)
            reports.extend([completed_count, uploaded_count, remaining_count])
            return render(request, 'teacher/assignment_reports.html', {'subjects': teacher_subjects, 'assignments': assignments, 'assign_obj': assignment, 'completed': completed_students, 'uploaded': uploaded_students, 'remaining': remaining_students, 'reports': reports, 'msg': msg})
        else:
            sub_id = request.POST.get('subject')
            request.session['subject_id'] = sub_id
            return redirect('assignment_reports')

    else:
        return redirect(request, 'teacher/teacher_signin.html')


def student_reports(request):
    t_id = request.session.get('teacher_id')
    if t_id:
        if request.method == 'GET':
            teacher_subjects = Subject.objects.filter(assign_teacher=t_id)
            sub_id = request.GET.get('subject')
            roll_no = request.GET.get('rollno')
            msg = None
            student = None
            reports = []
            completed = []
            uploaded = []
            remaining = []
            marks = []
            assigns = []
            total_marks_report = []
            if sub_id:
                subject = Subject.objects.get(id=sub_id)
                try:
                    student = Student.objects.filter(
                        course=subject.course).get(roll_no=roll_no)
                except:
                    msg = "student not exist with this roll number in " + \
                        str(subject.course)+"..."

                total_assigns = Assignment.objects.filter(subject=subject)
                completed = Solution.objects.filter(subject=subject).filter(
                    st_id=student).filter(status=True)
                uploaded = Solution.objects.filter(subject=subject).filter(
                    st_id=student).filter(status=False)
                remaining_count = total_assigns.count() - (completed.count() + uploaded.count())
                reports.extend(
                    [total_assigns.count(), completed.count(), uploaded.count(), remaining_count])

                total = []
                complete_upload = []
                for assign in total_assigns:
                    total.append(assign.title)
                for assign in completed:
                    complete_upload.append(assign.que_ass_id.title)
                for assign in uploaded:
                    complete_upload.append(assign.que_ass_id.title)
                for assign in total_assigns:
                    if assign.title not in complete_upload:
                        remaining.append(assign)

                total_marks = 0
                received_marks = 0
                for assign in total_assigns:
                    total_marks += assign.total_points
                for assign in completed:
                    received_marks += assign.marks
                total_marks_report.extend([total_marks, received_marks])

                st_solutions = Solution.objects.filter(
                    subject=subject).filter(st_id=student).filter(status=True)
                for solu in st_solutions:
                    marks.append(solu.marks)
                    assigns.append(solu.que_ass_id.title)

            return render(request, 'teacher/student_reports.html', {'subjects': teacher_subjects, 'student': student, 'msg': msg, 'reports': reports, 'completed': completed, 'uploaded': uploaded, 'remaining': remaining, 'assigns': dumps(assigns), 'marks': dumps(marks), 'js_reports': dumps(reports[1:]), 'total_marks': total_marks_report, 'sub_id': sub_id})

    else:
        return redirect(request, 'teacher/teacher_signin.html')


def my_assignments(request):
    t_id = request.session.get('teacher_id')
    if t_id:
        teacher = Teacher.objects.get(id=t_id)
        subjects = Subject.objects.filter(assign_teacher=t_id)

        assignments = Assignment.objects.filter(teacher=teacher)
        sub_id = request.GET.get('subject')
        if sub_id:
            subject = Subject.objects.get(id=sub_id)
            assignments = Assignment.objects.filter(
                teacher=teacher).filter(subject=subject)

        ass_id = request.GET.get('del_ass_id')
        if ass_id:
            Assignment.objects.filter(id=ass_id).delete()
            return redirect(reverse('my_assignments'))

        return render(request, 'teacher/my_assignments.html', {'subjects': subjects, 'assignments': assignments})
    else:
        return redirect(request, 'teacher/teacher_signin.html')


def logout_teacher(request):
    del request.session['teacher_name']
    del request.session['teacher_id']
    del request.session['teacher_email']
    if request.session['subject_id']:
        del request.session['subject_id']
    return redirect('teacher_signin')


def forgot_password_teacher(request):
    if request.method == 'GET':
        return render(request, 'teacher/forgot_password_teacher.html')
    else:
        forget_email = request.POST.get('forget_email')
        teacher = Teacher.get_teacher_by_email(forget_email)
        msg = None
        if teacher:
            encoded_mail = signing.dumps(str(teacher.email))
            mail_subject = "Dropwork - Forgot Password"
            message = "open link for reset pasword : \n http://127.0.0.1:8000/reset_password_teacher?e=" + encoded_mail
            email_from = settings.EMAIL_HOST_USER
            recipient_list = [str(teacher.email)]
            send_mail(mail_subject, message, email_from, recipient_list)

            msg = 'You will receive an email for reset your password on your registered email ID...'
        else:
            msg = 'Please enter registered email...'

        return render(request, 'teacher/forgot_password_teacher.html', {'msg': msg})


def reset_password_teacher(request):
    msg = None
    if request.method == 'GET':
        email = request.GET.get('e')
        decoded_email = signing.loads(email)
        request.session['decoded_email'] = decoded_email
        return render(request, 'teacher/reset_password_teacher.html', {'msg': msg})
    else:
        new_pass = request.POST.get('password')
        teacher = Teacher.objects.get(
            email=request.session.get('decoded_email'))
        teacher.password = new_pass
        teacher.save(update_fields=['password'])
        msg = "Password reseted successfully..."
        return render(request, 'teacher/reset_password_teacher.html', {'msg': msg})


class Pdf(View):
    def get(self, request):
        sub_id = request.GET.get('subject')
        roll_no = request.GET.get('rollno')
        msg = None
        student = None
        reports = []
        completed = []
        uploaded = []
        remaining = []
        marks = []
        assigns = []
        total_marks_report = []
        if sub_id:
            subject = Subject.objects.get(id=sub_id)
            try:
                student = Student.objects.filter(
                    course=subject.course).get(roll_no=roll_no)
            except:
                msg = "student not exist with this roll number in " + \
                    str(subject.course)+"..."

            total_assigns = Assignment.objects.filter(subject=subject)
            completed = Solution.objects.filter(subject=subject).filter(
                st_id=student).filter(status=True)
            uploaded = Solution.objects.filter(subject=subject).filter(
                st_id=student).filter(status=False)
            remaining_count = total_assigns.count() - (completed.count() + uploaded.count())
            reports.extend(
                [total_assigns.count(), completed.count(), uploaded.count(), remaining_count])

            total = []
            complete_upload = []
            for assign in total_assigns:
                total.append(assign.title)
            for assign in completed:
                complete_upload.append(assign.que_ass_id.title)
            for assign in uploaded:
                complete_upload.append(assign.que_ass_id.title)
            for assign in total_assigns:
                if assign.title not in complete_upload:
                    remaining.append(assign)

            total_marks = 0
            received_marks = 0
            for assign in total_assigns:
                total_marks += assign.total_points
            for assign in completed:
                received_marks += assign.marks
            total_marks_report.extend([total_marks, received_marks])

            st_solutions = Solution.objects.filter(
                subject=subject).filter(st_id=student)
            for solu in st_solutions:
                marks.append(solu.marks)
                assigns.append(solu.que_ass_id.title)

        today = timezone.now()
        params = {
            'today': today,
            'student': student, 'msg': msg, 'reports': reports, 'completed': completed,
            'uploaded': uploaded, 'remaining': remaining, 'assigns': dumps(assigns), 'marks': dumps(marks),
            'js_reports': dumps(reports[1:]), 'total_marks': total_marks_report,
            'request': request
        }
        return Render.render('pdf.html', params)


def update_profile_teacher(request):
    t_id = request.session.get('teacher_id')
    if t_id:
        teacher = Teacher.objects.get(id=t_id)
        if request.method == 'GET':
            msg = None
            return render(request, 'teacher/update_profile_teacher.html', {'teacher': teacher, 'msg': msg})
        else:
            first_name = request.POST.get('firstname')
            last_name = request.POST.get('lastname')
            email = request.POST.get('email')

            teacher.first_name = first_name
            teacher.last_name = last_name
            teacher.email = email
            teacher.save(update_fields=['first_name', 'last_name', 'email'])
            msg = "Your profile is upldated successfully..."

            return render(request, 'teacher/update_profile_teacher.html', {'teacher': teacher, 'msg': msg})
    else:
        return redirect(request, 'teacher/teacher_signin.html')


def edit_my_solutions(request):
    if request.method == 'GET':
        student_id = request.session.get('student_id')
        student = Student.objects.get(id=student_id)
        solu_id = request.GET.get('edit_sol_id')
        if solu_id:
            request.session['edit_sol_id'] = solu_id

        return render(request, 'edit_my_solutions.html')
    else:
        student_id = request.session.get('student_id')
        student = Student.objects.get(id=student_id)
        solu_id = request.session.get('edit_sol_id')
        solution = Solution.objects.get(id=solu_id)
        solution.ans_url = request.FILES['uploadFile']
        solution.save(update_fields=['ans_url'])
        msg = "Solution of " + solution.que_ass_id.title + " edited successfully..."
        messages.success(request, msg)

        return redirect(reverse('my_solutions'))


def edit_my_assignments(request):
    t_id = request.session.get('teacher_id')
    teacher = Teacher.objects.get(id=t_id)
    if request.method == 'GET':
        ass_id = request.GET.get('edit_ass_id')
        if ass_id:
            request.session['edit_ass_id'] = ass_id
            assign = Assignment.objects.get(id=ass_id)

        return render(request, 'teacher/edit_my_assignments.html', {'assign': assign})
    else:
        ass_id = request.session.get('edit_ass_id')
        assign = Assignment.objects.get(id=ass_id)

        assign.title = request.POST.get('title')
        assign.Description = request.POST.get('description')
        assign.file_url = request.FILES['file_url']
        assign.start_date = request.POST.get('startDate')
        assign.end_date = request.POST.get('endDate')
        assign.total_points = request.POST.get('points')
        assign.save(update_fields=[
                    'title', 'Description', 'start_date', 'total_points', 'end_date', 'file_url'])
        msg = assign.title + " of " + assign.subject.sub_name + " edited successfully..."
        messages.success(request, msg)

        return redirect(reverse('my_assignments'))

# Edited by hiren


def attendance(request):
    t_id = request.session.get('teacher_id')
    teacher = Teacher.objects.get(id=t_id)
    if t_id:
        teacher_subjects = Subject.objects.filter(assign_teacher=t_id)
        students = Student.objects.filter(course=1)
        if request.method == 'GET':
            return render(request, 'teacher/attendance.html', {"students": students, "subjects": teacher_subjects})
        else:
            date = request.POST.get('startDate')
            subject_id = request.POST.get('subject')
            subject = Subject.objects.get(pk=subject_id)
            status = []
            print(subject.id)
            for st in students:
                status.append(request.POST.get(st.first_name))
            for i in range(0, len(students)):
                attendance = Attendancedetails(
                    st_id=students[i], attendance_date=date, subject_id=subject, status=status[i])
                attendance.save()
            return render(request, 'teacher/attendance.html', {"students": students, "subjects": teacher_subjects})
    else:
        return redirect('teacher_signin')


def attendance_reports(request):
    t_id = request.session.get('teacher_id')
    teacher = Teacher.objects.get(id=t_id)
    if t_id:
        teacher_subjects = Subject.objects.filter(assign_teacher=t_id)

        if request.method == 'GET':
            return render(request, 'teacher/attendance_reports.html', {"subjects": teacher_subjects})
        else:
            roll_no = request.POST.get('rollno')
            subject_id = request.POST.get('subject')
            subject = Subject.objects.get(pk=subject_id)
            student = Student.objects.get(roll_no=roll_no)

            reports = []
            total_lectures = Attendancedetails.objects.filter(
                subject_id=subject.id).count()
            present_count = Attendancedetails.objects.filter(
                st_id=student.id).filter(status=1).count()
            absent_count = total_lectures - present_count
            reports.extend([total_lectures, present_count, absent_count])
            return render(request, 'teacher/attendance_reports.html', {"student": student, "subjects": teacher_subjects, "reports": reports, 'js_reports': dumps(reports[1:])})
    else:
        return redirect('teacher_signin')


def midterm(request):
    t_id = request.session.get('teacher_id')
    teacher = Teacher.objects.get(id=t_id)
    if t_id:
        teacher_subjects = Subject.objects.filter(assign_teacher=t_id)
        students = Student.objects.filter(course=1)
        monthlist = ['JAN', 'FEB', 'MAR', 'APR', 'MAY', 'JUN',
                     'JUL', 'AUG', 'SEP', 'OCT', 'NOV', 'DEC']
        yearlist = [2020, 2021, 2022, 2023]
        if request.method == 'GET':
            return render(request, 'teacher/midtermmarks.html', {"students": students, "subjects": teacher_subjects, "month": monthlist, "year": yearlist})
        else:
            outofmid = midtermmark = outofinternal = internalmarks = []
            subject_id = request.POST.get('subject')
            month = request.POST.get('month')
            year = request.POST.get('year')
            subject = Subject.objects.get(pk=subject_id)
            all_date = midtermmarks.objects.filter(subject_id=subject_id)
            error_msg = None
            for i in all_date:
                if i.month == month and i.year == year:
                    error_msg = "Marks are already entered for this term"
                else:
                    for st in students:
                        outofmid.append(request.POST.get(
                            "oom"+str(st.roll_no)))
                        midtermmark.append(
                            request.POST.get("mm"+str(st.roll_no)))
                        outofinternal.append(
                            request.POST.get("ooi"+str(st.roll_no)))
                        internalmarks.append(
                            request.POST.get("im"+str(st.roll_no)))
                    for i in range(0, len(students)):
                        midterm = midtermmarks(
                            st_id=students[i], month=month, year=year, subject_id=subject, outofmid=outofmid[i], midtermmark=midtermmark[i], outofinternal=outofinternal[i], internalmarks=internalmarks[i])
                        midterm.save()

            return render(request, 'teacher/midtermmarks.html', {"students": students, "subjects": teacher_subjects, "error_msg": error_msg,  "month": monthlist, "year": yearlist})
    else:
        return redirect('midtermmarks')

# st_ids = sub_ids = months = years = []
#             for i in all_data:
#                 st_ids.append(i.st_id)
#                 sub_ids.append(i.subject_id)
#                 months.append(i.month)
#                 years.append(i.year)

#             for st in students:
#                 outofmid.append(request.POST.get(
#                     "oom"+str(st.roll_no)))
#                 midtermmark.append(
#                     request.POST.get("mm"+str(st.roll_no)))
#                 outofinternal.append(
#                     request.POST.get("ooi"+str(st.roll_no)))
#                 internalmarks.append(
#                     request.POST.get("im"+str(st.roll_no)))
#             for i in range(0, len(students)):
#                 if students[i].id in st_ids and subject_id in sub_ids and month in months and year in years:
#                     break
#                 else:
#                     midterm = midtermmarks(
#                         st_id=students[i], month=month, year=year, subject_id=subject, outofmid=outofmid[i], midtermmark=midtermmark[i], outofinternal=outofinternal[i], internalmarks=internalmarks[i])
#                     midterm.save()
