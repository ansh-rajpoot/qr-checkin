from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth import login, logout
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth.decorators import login_required, user_passes_test
from django.db.models import Q
from .models import Participant
from .forms import ParticipantRegistrationForm

def staff_check(user):
    return user.is_authenticated and user.is_staff

def register_participant(request):
    """
    Public registration page for participants.
    Validates form data, creates Participant model, auto-generates QR code,
    and redirects to the QR detail display page.
    """
    if request.method == 'POST':
        form = ParticipantRegistrationForm(request.POST)
        if form.is_valid():
            participant = form.save()
            messages.success(request, f"Registration successful for {participant.name}!")
            return redirect('qr_detail', qr_token=participant.qr_token)
        else:
            messages.error(request, "Please correct the errors below.")
    else:
        form = ParticipantRegistrationForm()

    return render(request, 'participants/register.html', {
        'form': form
    })

def participant_qr_detail(request, qr_token):
    """
    Participant view page to display and download their assigned QR code.
    """
    participant = get_object_or_404(Participant, qr_token=qr_token)
    return render(request, 'participants/qr_detail.html', {
        'participant': participant
    })

@login_required
@user_passes_test(staff_check)
def admin_dashboard(request):
    """
    Staff / Admin dashboard displaying real-time event check-in metrics,
    participant table, search query filtering, and attendance status filter.
    """
    query = request.GET.get('q', '').strip()
    status_filter = request.GET.get('status', 'all')

    participants_list = Participant.objects.all()

    # Search filter
    if query:
        participants_list = participants_list.filter(
            Q(name__icontains=query) |
            Q(email__icontains=query) |
            Q(roll_number__icontains=query)
        )

    # Status filter
    if status_filter == 'attended':
        participants_list = participants_list.filter(attended=True)
    elif status_filter == 'not_attended':
        participants_list = participants_list.filter(attended=False)

    # Metrics calculation
    total_participants = Participant.objects.count()
    total_attended = Participant.objects.filter(attended=True).count()
    total_not_attended = total_participants - total_attended
    attendance_rate = round((total_attended / total_participants * 100), 1) if total_participants > 0 else 0

    context = {
        'participants': participants_list,
        'total_participants': total_participants,
        'total_attended': total_attended,
        'total_not_attended': total_not_attended,
        'attendance_rate': attendance_rate,
        'query': query,
        'status_filter': status_filter,
    }
    return render(request, 'participants/dashboard.html', context)

def staff_login(request):
    """
    Staff login view for accessing scanner and dashboard.
    """
    if request.user.is_authenticated and request.user.is_staff:
        return redirect('scanner_page')

    if request.method == 'POST':
        form = AuthenticationForm(request, data=request.POST)
        if form.is_valid():
            user = form.get_user()
            if user.is_staff:
                login(request, user)
                messages.success(request, f"Welcome back, {user.username}!")
                next_url = request.GET.get('next', 'scanner_page')
                return redirect(next_url)
            else:
                messages.error(request, "Access restricted. Staff privileges required.")
        else:
            messages.error(request, "Invalid username or password.")
    else:
        form = AuthenticationForm()

    return render(request, 'login.html', {'form': form})

def staff_logout(request):
    """
    Staff logout view.
    """
    logout(request)
    messages.info(request, "You have been logged out.")
    return redirect('login')
