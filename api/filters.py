import django_filters
from django.db.models import Q
from .models import  Tickets
from django_filters import rest_framework as filters
from zohoapi.models import GmSheet

class TicketFilter(django_filters.FilterSet):
    usertype = django_filters.CharFilter(method="filter_by_usertype")
    user_id = django_filters.CharFilter(field_name="user__id", lookup_expr="icontains")
    status = django_filters.CharFilter(field_name="status", lookup_expr="icontains")
    raise_to = django_filters.CharFilter(field_name="raise_to", lookup_expr="icontains")
    priority = django_filters.CharFilter(field_name="priority", lookup_expr="icontains")
    is_sla_breached = django_filters.BooleanFilter(field_name="is_sla_breached")

    # Date range filters
    created_at__gte = django_filters.DateFilter(
        field_name="created_at", lookup_expr="gte"
    )
    created_at__lte = django_filters.DateFilter(
        field_name="created_at", lookup_expr="lte"
    )
    resolution_date__gte = django_filters.DateFilter(
        field_name="resolution_date", lookup_expr="gte"
    )
    resolution_date__lte = django_filters.DateFilter(
        field_name="resolution_date", lookup_expr="lte"
    )
    sla_due_date__gte = django_filters.DateFilter(
        field_name="sla_due_date", lookup_expr="gte"
    )
    sla_due_date__lte = django_filters.DateFilter(
        field_name="sla_due_date", lookup_expr="lte"
    )

    class Meta:
        model = Tickets
        fields = [
            "usertype",
            "user_id",
            "raise_to",
            "status",
            "priority",
            "is_sla_breached",
            "created_at__gte",
            "created_at__lte",
            "resolution_date__gte",
            "resolution_date__lte",
            "sla_due_date__gte",
            "sla_due_date__lte",
        ]

    def filter_by_usertype(self, queryset, name, value):
        if value == "superadmin":
            return queryset
        else:
            return queryset.filter(user_type=value)


      
class GmSheetListFilter(django_filters.FilterSet):
    project_type = filters.BaseInFilter(field_name="project_type", lookup_expr="in")
    deal_status = filters.BaseInFilter(field_name="deal_status", lookup_expr="in")
    participant_level = filters.BaseInFilter(
        field_name="participant_level", lookup_expr="in"
    )
    status = filters.CharFilter(method="filter_status")

    class Meta:
        model = GmSheet
        fields = ["project_type", "deal_status", "participant_level"]

    def filter_status(self, queryset, name, value):
        status_values = value.split(",")
        query = Q()
        if "Accepted" in status_values:
            query |= Q(is_accepted=True)
        if "Pending" in status_values:
            query |= Q(is_accepted=False)
        if not query:
            return queryset
        return queryset.filter(query)