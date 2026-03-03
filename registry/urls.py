from django.urls import path

from . import views

app_name = "registry"

urlpatterns = [
    path("", views.forklift_list, name="forklift_list"),
    path("forklifts/new/", views.forklift_create, name="forklift_create"),
    path("forklifts/<int:pk>/edit/", views.forklift_update, name="forklift_update"),
    path("forklifts/<int:pk>/delete/", views.forklift_delete, name="forklift_delete"),
    path(
        "forklifts/<int:forklift_pk>/incidents/new/",
        views.incident_create,
        name="incident_create",
    ),
    path("incidents/<int:pk>/edit/", views.incident_update, name="incident_update"),
    path("incidents/<int:pk>/delete/", views.incident_delete, name="incident_delete"),
]
