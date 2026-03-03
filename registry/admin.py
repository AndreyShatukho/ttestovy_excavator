from django.contrib import admin

from .models import Forklift, Incident


@admin.register(Forklift)
class ForkliftAdmin(admin.ModelAdmin):
    list_display = ("id", "number", "brand", "capacity", "is_active", "modified_at", "updated_by")
    search_fields = ("number", "brand")
    list_filter = ("is_active",)


@admin.register(Incident)
class IncidentAdmin(admin.ModelAdmin):
    list_display = ("id", "forklift", "started_at", "resolved_at", "downtime_hhmm")
    search_fields = ("forklift__number", "description")
