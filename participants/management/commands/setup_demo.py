from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from participants.models import Participant

class Command(BaseCommand):
    help = 'Sets up initial demo staff account and sample participants for testing.'

    def handle(self, *args, **options):
        
        # Create default staff user
        admin_user, created = User.objects.get_or_create(username='anshrajpoot')
        if created:
            admin_user.set_password('Ansh@123')
            admin_user.is_staff = True
            admin_user.is_superuser = True
            admin_user.save()
            self.stdout.write(self.style.SUCCESS("Created staff account: username='admin', password='admin123'"))
        else:
            self.stdout.write(self.style.WARNING("Staff account 'admin' already exists."))

        # Create sample participants
        sample_data = [
            {'name': 'Rahul Sharma', 'email': 'rahul@college.edu', 'roll_number': '23CSE101'},
            {'name': 'Priya Patel', 'email': 'priya@college.edu', 'roll_number': '23ECE044'},
            {'name': 'Aman Verma', 'email': 'aman@college.edu', 'roll_number': '23ME105'},
            {'name': 'Sneha Gupta', 'email': 'sneha@college.edu', 'roll_number': '23IT088'},
        ]

        count = 0
        for pdata in sample_data:
            p, p_created = Participant.objects.get_or_create(
                roll_number=pdata['roll_number'],
                defaults={'name': pdata['name'], 'email': pdata['email']}
            )
            if p_created:
                count += 1

        self.stdout.write(self.style.SUCCESS(f"Successfully created {count} sample participants with QR codes."))
