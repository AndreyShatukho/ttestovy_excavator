from django.contrib import messages
from django.http import HttpRequest, HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse

from .forms import ForkliftForm, IncidentForm
from .models import Forklift, Incident


def _editor_name(request: HttpRequest) -> str:
    if request.user.is_authenticated:
        full_name = request.user.get_full_name().strip()
        return full_name or request.user.get_username()
    return request.headers.get("X-User", "Неизвестный пользователь")


def _build_list_context(request: HttpRequest) -> dict:
    query = request.GET.get("q", "").strip()
    selected_id = request.GET.get("selected")

    forklifts = Forklift.objects.all()
    if query:
        forklifts = forklifts.filter(number__icontains=query)

    selected_forklift = None
    if selected_id:
        selected_forklift = forklifts.filter(pk=selected_id).first()
    if selected_forklift is None:
        selected_forklift = forklifts.first()

    incidents = (
        selected_forklift.incidents.all() if selected_forklift else Incident.objects.none()
    )

    incident_action = request.GET.get("incident_action")
    incident_id = request.GET.get("incident_id")
    forklift_action = request.GET.get("forklift_action")
    forklift_id = request.GET.get("forklift_id")
    forklift_form = None
    forklift_form_action = None
    forklift_modal_title = None
    incident_form = None
    incident_form_action = None
    incident_modal_title = None

    if forklift_action == "new":
        forklift_form = ForkliftForm()
        forklift_form_action = reverse("registry:forklift_create")
        forklift_modal_title = "Добавить погрузчик"
    elif forklift_action == "edit" and forklift_id:
        editing_forklift = forklifts.filter(pk=forklift_id).first() or Forklift.objects.filter(
            pk=forklift_id
        ).first()
        if editing_forklift:
            forklift_form = ForkliftForm(instance=editing_forklift)
            forklift_form_action = reverse("registry:forklift_update", args=[editing_forklift.pk])
            forklift_modal_title = f"Изменить {editing_forklift.number}"

    if selected_forklift and incident_action == "new":
        incident_form = IncidentForm()
        incident_form_action = reverse("registry:incident_create", args=[selected_forklift.pk])
        incident_modal_title = f"Регистрация инцидента — {selected_forklift.number}"
    elif selected_forklift and incident_action == "edit" and incident_id:
        incident = (
            Incident.objects.filter(pk=incident_id, forklift_id=selected_forklift.pk)
            .select_related("forklift")
            .first()
        )
        if incident:
            incident_form = IncidentForm(instance=incident)
            incident_form_action = reverse("registry:incident_update", args=[incident.pk])
            incident_modal_title = f"Изменение инцидента — {selected_forklift.number}"

    return {
        "query": query,
        "forklifts": forklifts,
        "selected_forklift": selected_forklift,
        "incidents": incidents,
        "forklift_form": forklift_form,
        "forklift_form_action": forklift_form_action,
        "forklift_modal_title": forklift_modal_title,
        "incident_form": incident_form,
        "incident_form_action": incident_form_action,
        "incident_modal_title": incident_modal_title,
    }


def forklift_list(request: HttpRequest) -> HttpResponse:
    context = _build_list_context(request)
    return render(request, "registry/forklift_list.html", context)


def forklift_create(request: HttpRequest) -> HttpResponse:
    if request.method != "POST":
        return redirect(reverse("registry:forklift_list") + "?forklift_action=new")

    form = ForkliftForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        forklift = form.save(commit=False)
        forklift.updated_by = _editor_name(request)
        forklift.save()
        messages.success(request, "Погрузчик успешно добавлен.")
        return redirect(reverse("registry:forklift_list") + f"?selected={forklift.pk}")

    context = _build_list_context(request)
    context["forklift_form"] = form
    context["forklift_form_action"] = reverse("registry:forklift_create")
    context["forklift_modal_title"] = "Добавить погрузчик"
    return render(request, "registry/forklift_list.html", context)


def forklift_update(request: HttpRequest, pk: int) -> HttpResponse:
    forklift = get_object_or_404(Forklift, pk=pk)
    if request.method != "POST":
        return redirect(
            reverse("registry:forklift_list")
            + f"?selected={forklift.pk}&forklift_action=edit&forklift_id={forklift.pk}"
        )

    form = ForkliftForm(request.POST or None, instance=forklift)
    if request.method == "POST" and form.is_valid():
        forklift = form.save(commit=False)
        forklift.updated_by = _editor_name(request)
        forklift.save()
        messages.success(request, "Изменения сохранены.")
        return redirect(reverse("registry:forklift_list") + f"?selected={forklift.pk}")

    context = _build_list_context(request)
    context["forklift_form"] = form
    context["forklift_form_action"] = reverse("registry:forklift_update", args=[forklift.pk])
    context["forklift_modal_title"] = f"Изменить {forklift.number}"
    return render(request, "registry/forklift_list.html", context)


def forklift_delete(request: HttpRequest, pk: int) -> HttpResponse:
    forklift = get_object_or_404(Forklift, pk=pk)
    if request.method == "POST":
        if forklift.incidents.exists():
            messages.error(
                request,
                "Удаление запрещено: для погрузчика зарегистрированы простои.",
            )
            return redirect(reverse("registry:forklift_list") + f"?selected={forklift.pk}")
        forklift.delete()
        messages.success(request, "Погрузчик удален.")
    return redirect("registry:forklift_list")


def incident_create(request: HttpRequest, forklift_pk: int) -> HttpResponse:
    forklift = get_object_or_404(Forklift, pk=forklift_pk)
    if request.method != "POST":
        return redirect(
            reverse("registry:forklift_list")
            + f"?selected={forklift.pk}&incident_action=new"
        )

    form = IncidentForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        incident = form.save(commit=False)
        incident.forklift = forklift
        incident.save()
        messages.success(request, "Инцидент зарегистрирован.")
        return redirect(reverse("registry:forklift_list") + f"?selected={forklift.pk}")

    context = _build_list_context(request)
    context["selected_forklift"] = forklift
    context["incidents"] = forklift.incidents.all()
    context["incident_form"] = form
    context["incident_form_action"] = reverse("registry:incident_create", args=[forklift.pk])
    context["incident_modal_title"] = f"Регистрация инцидента — {forklift.number}"
    return render(request, "registry/forklift_list.html", context)


def incident_update(request: HttpRequest, pk: int) -> HttpResponse:
    incident = get_object_or_404(Incident, pk=pk)
    if request.method != "POST":
        return redirect(
            reverse("registry:forklift_list")
            + f"?selected={incident.forklift_id}&incident_action=edit&incident_id={incident.pk}"
        )

    form = IncidentForm(request.POST or None, instance=incident)
    if request.method == "POST" and form.is_valid():
        form.save()
        messages.success(request, "Инцидент обновлен.")
        return redirect(
            reverse("registry:forklift_list") + f"?selected={incident.forklift_id}"
        )

    context = _build_list_context(request)
    context["selected_forklift"] = incident.forklift
    context["incidents"] = incident.forklift.incidents.all()
    context["incident_form"] = form
    context["incident_form_action"] = reverse("registry:incident_update", args=[incident.pk])
    context["incident_modal_title"] = f"Изменение инцидента — {incident.forklift.number}"
    return render(request, "registry/forklift_list.html", context)


def incident_delete(request: HttpRequest, pk: int) -> HttpResponse:
    incident = get_object_or_404(Incident, pk=pk)
    forklift_pk = incident.forklift_id
    if request.method == "POST":
        incident.delete()
        messages.success(request, "Информация о простое удалена.")
    return redirect(reverse("registry:forklift_list") + f"?selected={forklift_pk}")
