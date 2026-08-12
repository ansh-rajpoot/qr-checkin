# TechPass - Django QR-Based Event Check-In System

A modular, production-style **QR-Based Event Check-In System** built using Python, Django, SQLite, and WebRTC Browser Camera API (`html5-qrcode`).

Designed for college technical team projects, hackathons, and interviews to showcase clean architecture, UUID token security, responsive camera integration, and real-time backend verification.

---

## Key Features

1. **Participant Registration**:
   - Clean registration form for participants (Name, Email, Roll Number).
   - Form validation preventing duplicate roll numbers.

2. **Automatic QR Code Generation**:
   - Generates a unique UUID `qr_token` for every participant upon saving.
   - Creates a high-resolution QR PNG image using Python `qrcode` and `Pillow`.

3. **QR View & Download**:
   - Dedicated participant page displaying their digital ticket pass and a 1-click download button.

4. **In-Browser Camera Scanner App (`/scanner/`)**:
   - Built as an independent, decoupled Django app (`scanner`).
   - Uses device camera natively in the browser via JavaScript (`html5-qrcode`). No app installation needed.
   - Camera selector (front/back), audio chime feedback, and manual token entry fallback.

5. **Secure Check-In API (`POST /scanner/api/check-in/`)**:
   - Validates scanned QR token against Django backend.
   - Prevents duplicate check-ins by updating `attended = True` and recording exact `checked_in_at` timestamp.
   - Prevents token tampering by verifying UUIDs server-side.

6. **Real-Time Result Feedback**:
   - Visual card & sound cues:
     - **Green (`Check-in Successful`)**: Participant identified and marked present.
     - **Yellow (`Already Checked In`)**: Duplicate scan detected; timestamp displayed.
     - **Red (`Invalid QR Code`)**: Unknown or invalid QR token.

7. **Admin Attendance Dashboard (`/participants/dashboard/`)**:
   - Restricted to staff users (`@login_required` + `@user_passes_test(is_staff)`).
   - Real-time event statistics: Total Registered, Checked-In Count/%, Pending Count.
   - Live search (Name, Roll Number, Email) and filter tabs (`All`, `Attended`, `Not Attended`).

---

## Tech Stack

- **Backend Framework**: Django 6.x / Python 3.14
- **Database**: SQLite3
- **QR Generation**: Python `qrcode` + `Pillow`
- **Frontend**: HTML5, CSS3, JavaScript (ES6+), Bootstrap 5, Bootstrap Icons
- **Browser Camera Scanner**: `html5-qrcode` library (WebRTC Camera Stream)

---

## Project Structure

```text
qr-checkin/
│
├── manage.py                   # Django management script
├── db.sqlite3                  # SQLite database file
├── requirements.txt            # Python dependencies
├── README.md                   # System documentation
│
├── config/                     # Core Django configuration package
│   ├── __init__.py
│   ├── settings.py             # Project settings (INSTALLED_APPS, STATIC, MEDIA)
│   ├── urls.py                 # Main URL routing (includes app urls)
│   ├── asgi.py
│   └── wsgi.py
│
├── participants/               # Participants App (Registration, Models, Dashboard)
│   ├── migrations/
│   ├── templates/participants/
│   │   ├── register.html       # Public registration page
│   │   ├── qr_detail.html      # QR pass view and download page
│   │   └── dashboard.html      # Staff admin metrics and search dashboard
│   ├── admin.py                # Django Admin registration
│   ├── apps.py
│   ├── forms.py                # Registration form & validation
│   ├── models.py               # Participant model & QR generation logic
│   ├── urls.py                 # Participant app URLs
│   ├── views.py                # Registration, QR detail, and Dashboard views
│   └── tests.py                # Unit tests for participant app
│
├── scanner/                    # Scanner App (Browser Camera & Check-in API)
│   ├── migrations/
│   ├── templates/scanner/
│   │   └── scanner.html        # Live camera viewfinder page
│   ├── static/scanner/js/
│   │   └── scanner.js          # Camera stream, Web Audio chime, & fetch API handler
│   ├── admin.py
│   ├── apps.py
│   ├── models.py
│   ├── urls.py                 # Scanner app URLs
│   ├── views.py                # Scanner page & check_in_api views
│   └── tests.py                # Unit tests for scanner app & check-in API
│
├── templates/                  # Global templates
│   ├── base.html               # Master layout with navbar & message alerts
│   └── login.html              # Staff login page
│
├── static/                     # Global static assets
│   ├── css/
│   │   └── custom.css          # Design system & scanner styling
│   └── js/
│       └── html5-qrcode.min.js # Bundled HTML5 QR Scanner library
│
└── media/                      # Media root directory
    └── qr_codes/               # Dynamically generated participant QR images
```

---

## Installation & Setup

1. **Clone or Navigate to Project Directory**:
   ```bash
   cd qr-checkin
   ```

2. **Create & Activate Virtual Environment**:
   ```bash
   python3 -m venv venv
   source venv/bin/activate        # On macOS/Linux
   # or: venv\Scripts\activate     # On Windows
   ```

3. **Install Required Packages**:
   ```bash
   pip install -r requirements.txt
   ```

4. **Run Database Migrations**:
   ```bash
   python manage.py makemigrations
   python manage.py migrate
   ```

5. **Create a Superuser (Staff Member)**:
   ```bash
   python manage.py createsuperuser
   ```

6. **Start the Development Server**:
   ```bash
   python manage.py runserver
   ```
   Access the app at: `http://127.0.0.1:8000/`

---

## How It Works

### 1. Participant Registration Flow
1. User visits `/participants/register/` and submits Name, Email, and Roll Number.
2. Django validates form inputs and checks for unique `roll_number`.
3. Model `save()` generates a secure UUID4 token (`qr_token`) and calls `generate_qr_code()`.
4. `qrcode.make()` constructs the QR image, saves PNG to `media/qr_codes/`, and updates `qr_code_image`.
5. User is redirected to `/participants/<qr_token>/` to view and download their ticket.

### 2. Camera QR Scanning Flow
1. Authorized staff logs in and visits `/scanner/`.
2. Browser requests WebRTC camera permission and initializes `html5-qrcode`.
3. Staff points camera at participant's QR code.
4. `scanner.js` detects the QR string, extracts the UUID token using regex, and sends a `POST` JSON request to `/scanner/api/check-in/` with CSRF token.

### 3. Backend Verification & Attendance Logic
1. `check_in_api` receives `{"token": "<uuid>"}`.
2. Django searches for `Participant.objects.get(qr_token=token_uuid)`.
3. If not found: returns `{"success": false, "message": "Invalid QR code"}`.
4. If found & `attended == True`: returns `{"success": false, "message": "Participant has already checked in", ...}` without modifying database.
5. If found & `attended == False`: updates `participant.attended = True`, sets `participant.checked_in_at = timezone.now()`, saves model, and returns `{"success": true, "message": "Check-in successful", ...}`.

---

## API Documentation

### `POST /scanner/api/check-in/`

**Headers**:
- `Content-Type: application/json`
- `X-CSRFToken: <csrftoken>`

**Request Body**:
```json
{
  "token": "c7a31b4e-9d22-488f-a32e-18d2d9b62c45"
}
```

**Success Response (200 OK)**:
```json
{
  "success": true,
  "message": "Check-in successful",
  "participant": {
    "name": "Rahul Sharma",
    "roll_number": "23CSE101",
    "email": "rahul@college.edu"
  },
  "checked_in_at": "Aug 12, 2026 at 08:30 PM"
}
```

**Duplicate Check-in Response (200 OK)**:
```json
{
  "success": false,
  "message": "Participant has already checked in",
  "participant": {
    "name": "Rahul Sharma",
    "roll_number": "23CSE101",
    "email": "rahul@college.edu"
  },
  "checked_in_at": "Aug 12, 2026 at 08:15 PM"
}
```

**Invalid Token Response (200 OK)**:
```json
{
  "success": false,
  "message": "Invalid QR code"
}
```

---

## Database Schema (`Participant` Model)

| Field Name | Type | Options / Description |
| :--- | :--- | :--- |
| `id` | BigAutoField | Primary Key (Internal) |
| `name` | CharField(150) | Participant's Full Name |
| `email` | EmailField | Participant Email |
| `roll_number` | CharField(50) | Unique Registration / Roll Number |
| `qr_token` | UUIDField | Unique UUID4 Security Token (`db_index=True`) |
| `qr_code_image` | ImageField | Path to generated QR PNG image in `media/` |
| `attended` | BooleanField | Check-in status (`default=False`) |
| `checked_in_at` | DateTimeField | Timestamp of check-in (`null=True`) |
| `created_at` | DateTimeField | Timestamp of registration (`auto_now_add=True`) |

---

## Running Unit Tests

Run the full Django test suite with:

```bash
python manage.py test
```

Expected output:
```text
Found 7 test(s).
Creating test database for alias 'default'...
System check identified no issues (0 silenced).
.......
----------------------------------------------------------------------
Ran 7 tests in 0.45s

OK
```

---

## Future Extensibility

The system follows a modular app architecture allowing simple addition of future features without refactoring:
- `events/`: Manage multiple events/conferences with separate participant lists.
- `notifications/`: Send automated WhatsApp/Email QR passes upon registration.
- `certificates/`: Issue automated completion certificates for attended participants.
- `reports/`: Export attendance reports as PDF/Excel files.
