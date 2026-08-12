import json
import re
import uuid
from django.shortcuts import render
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from django.views.decorators.csrf import csrf_protect
from django.contrib.auth.decorators import login_required, user_passes_test
from django.utils import timezone
from participants.models import Participant

def staff_check(user):
    return user.is_authenticated and user.is_staff

@login_required
@user_passes_test(staff_check)
def scanner_page(request):
    """
    Renders the browser-based camera QR code scanner page.
    Restricted to authenticated staff members.
    """
    return render(request, 'scanner/scanner.html')

@csrf_protect
@require_POST
@login_required
@user_passes_test(staff_check)
def check_in_api(request):
    """
    API endpoint processing scanned QR codes.
    Accepts JSON body {"token": "..."} or POST form data.
    Verifies participant token, updates check-in status safely,
    and returns standardized JSON responses.
    """
    try:
        # Parse JSON body or POST form data
        if request.content_type == 'application/json':
            data = json.loads(request.body.decode('utf-8'))
        else:
            data = request.POST

        raw_token = data.get('token', '').strip()

        if not raw_token:
            return JsonResponse({
                'success': False,
                'message': 'Missing token'
            }, status=400)

        # Extract UUID string from input (handles raw UUIDs or URLs containing UUIDs)
        uuid_pattern = r'[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12}'
        match = re.search(uuid_pattern, raw_token)

        if not match:
            return JsonResponse({
                'success': False,
                'message': 'Invalid QR code format'
            })

        token_uuid_str = match.group(0)

        try:
            token_uuid = uuid.UUID(token_uuid_str)
        except ValueError:
            return JsonResponse({
                'success': False,
                'message': 'Invalid QR code'
            })

        # Fetch participant matching the QR token
        try:
            participant = Participant.objects.get(qr_token=token_uuid)
        except Participant.DoesNotExist:
            return JsonResponse({
                'success': False,
                'message': 'Invalid QR code'
            })

        # Case 2 — Already checked in
        if participant.attended:
            formatted_time = participant.checked_in_at.strftime('%b %d, %Y at %I:%M %p') if participant.checked_in_at else 'Earlier'
            return JsonResponse({
                'success': False,
                'message': 'Participant has already checked in',
                'participant': {
                    'name': participant.name,
                    'roll_number': participant.roll_number,
                    'email': participant.email,
                },
                'checked_in_at': formatted_time
            })

        # Case 1 — Valid participant and not checked in
        participant.attended = True
        participant.checked_in_at = timezone.now()
        participant.save()

        formatted_time = participant.checked_in_at.strftime('%b %d, %Y at %I:%M %p')

        return JsonResponse({
            'success': True,
            'message': 'Check-in successful',
            'participant': {
                'name': participant.name,
                'roll_number': participant.roll_number,
                'email': participant.email,
            },
            'checked_in_at': formatted_time
        })

    except json.JSONDecodeError:
        return JsonResponse({
            'success': False,
            'message': 'Malformed JSON request'
        }, status=400)
    except Exception as e:
        return JsonResponse({
            'success': False,
            'message': 'Server error processing check-in'
        }, status=500)
