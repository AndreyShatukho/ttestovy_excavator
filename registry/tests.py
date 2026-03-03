from datetime import timedelta

from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from .models import Forklift, Incident


class RegistryTests(TestCase):
    def setUp(self):
        self.forklift = Forklift.objects.create(
            brand="Toyota",
            number="FL-001",
            capacity="1.500",
            updated_by="Test User",
        )

    def test_search_is_case_insensitive(self):
        response = self.client.get(reverse("registry:forklift_list"), {"q": "fl-0"})
        self.assertContains(response, "FL-001")

    def test_delete_forklift_with_incidents_is_forbidden(self):
        Incident.objects.create(
            forklift=self.forklift,
            started_at=timezone.now(),
            description="Engine issue",
        )
        self.client.post(reverse("registry:forklift_delete", args=[self.forklift.pk]))
        self.assertTrue(Forklift.objects.filter(pk=self.forklift.pk).exists())

    def test_open_incident_downtime_uses_current_time(self):
        incident = Incident.objects.create(
            forklift=self.forklift,
            started_at=timezone.now() - timedelta(hours=2, minutes=10),
            description="Battery issue",
        )
        self.assertTrue(incident.downtime.total_seconds() >= 7800)

    def test_open_incident_with_future_start_is_rejected(self):
        future_start = timezone.localtime(timezone.now() + timedelta(hours=1)).strftime(
            "%Y-%m-%dT%H:%M"
        )
        response = self.client.post(
            reverse("registry:incident_create", args=[self.forklift.pk]),
            {
                "started_at": future_start,
                "resolved_at": "",
                "description": "Future incident",
            },
        )
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Дата начала не может быть позже текущего времени.")
        self.assertEqual(Incident.objects.count(), 0)
