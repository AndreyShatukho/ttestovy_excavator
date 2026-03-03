from django import forms
from django.utils import timezone

from .models import Forklift, Incident


class DateTimeLocalInput(forms.DateTimeInput):
    input_type = "datetime-local"

    def __init__(self, *args, **kwargs):
        kwargs.setdefault("format", "%Y-%m-%dT%H:%M")
        super().__init__(*args, **kwargs)


class ForkliftForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field_name, field in self.fields.items():
            if field_name == "is_active":
                field.widget.attrs["class"] = "form-check-input"
            else:
                field.widget.attrs["class"] = "form-control"

    class Meta:
        model = Forklift
        fields = ("brand", "number", "capacity", "is_active")


class IncidentForm(forms.ModelForm):
    class Meta:
        model = Incident
        fields = ("started_at", "resolved_at", "description")
        widgets = {
            "started_at": DateTimeLocalInput(),
            "resolved_at": DateTimeLocalInput(),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["started_at"].input_formats = ["%Y-%m-%dT%H:%M"]
        self.fields["resolved_at"].input_formats = ["%Y-%m-%dT%H:%M"]
        self.fields["started_at"].widget.attrs["class"] = "form-control"
        self.fields["resolved_at"].widget.attrs["class"] = "form-control"
        self.fields["description"].widget.attrs["class"] = "form-control"
        if not self.instance.pk:
            self.initial.setdefault(
                "started_at",
                timezone.localtime().strftime("%Y-%m-%dT%H:%M"),
            )

    def clean(self):
        cleaned_data = super().clean()
        started_at = cleaned_data.get("started_at")
        resolved_at = cleaned_data.get("resolved_at")

        if started_at and resolved_at and resolved_at < started_at:
            self.add_error(
                "resolved_at",
                "Дата решения не может быть раньше даты начала.",
            )
        return cleaned_data
