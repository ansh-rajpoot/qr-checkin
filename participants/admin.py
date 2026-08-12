from django.contrib import admin
from .models import Participant

@admin.register(Participant)
class ParticipantAdmin(admin.ModelAdmin):
    list_display = ('name', 'roll_number', 'email', 'attended', 'checked_in_at', 'created_at')
    list_filter = ('attended', 'created_at')
    search_fields = ('name', 'email', 'roll_number', 'qr_token')
    readonly_fields = ('qr_token', 'created_at', 'checked_in_at', 'qr_code_image')
    ordering = ('-created_at',)
