from datetime import timedelta

from django.db import models
from django.utils import timezone


class Forklift(models.Model):
    brand = models.CharField("Марка погрузчика", max_length=255)
    number = models.CharField("Номер погрузчика", max_length=100, unique=True)
    capacity = models.DecimalField(
        "Грузоподъемность",
        max_digits=10,
        decimal_places=3,
    )
    is_active = models.BooleanField("Активен", default=True)
    modified_at = models.DateTimeField("Время и дата изменения", auto_now=True)
    updated_by = models.CharField("Пользователь", max_length=255)

    class Meta:
        verbose_name = "Погрузчик"
        verbose_name_plural = "Погрузчики"
        ordering = ("number",)

    def __str__(self) -> str:
        return f"{self.number} ({self.brand})"


class Incident(models.Model):
    forklift = models.ForeignKey(
        Forklift,
        on_delete=models.CASCADE,
        related_name="incidents",
        verbose_name="Погрузчик",
    )
    started_at = models.DateTimeField("Дата и время установления проблемы")
    resolved_at = models.DateTimeField(
        "Дата и время решения проблемы",
        null=True,
        blank=True,
    )
    description = models.TextField("Описание проблемы")

    class Meta:
        verbose_name = "Простой"
        verbose_name_plural = "Простои"
        ordering = ("-started_at",)

    def __str__(self) -> str:
        return f"{self.forklift.number}: {self.started_at:%d.%m.%Y %H:%M}"

    @property
    def downtime(self) -> timedelta:
        end_time = self.resolved_at or timezone.now()
        return max(end_time - self.started_at, timedelta())

    @property
    def downtime_hhmm(self) -> str:
        total_seconds = int(self.downtime.total_seconds())
        hours, remainder = divmod(total_seconds, 3600)
        minutes = remainder // 60
        return f"{hours:02d}:{minutes:02d}"
