import django_filters
from django.db.models import Q
from zohoapi.models import (
    InvoiceData,
    PurchaseOrder,
    ClientInvoice,
    SalesOrder,
    Payment,
    SalesOrderLineItem,
    Company,
    Contact,
)
from django_filters import rest_framework as filters
import json
import environ
from datetime import datetime

env = environ.Env()


class InvoiceListFilter(django_filters.FilterSet):
    caas_project_id = filters.NumberFilter(method="filter_by_caas_project_id")
    schedular_project_id = filters.NumberFilter(method="filter_by_schedular_project_id")
    status = filters.CharFilter(method="filter_by_status")
    usertype = filters.CharFilter(method="filter_by_usertype")
    vendor_name = filters.CharFilter(method="filter_multi_value")
    invoice_status = filters.CharFilter(method="filter_multi_value")
    approver_email = filters.CharFilter(method="filter_multi_value")

    class Meta:
        model = InvoiceData
        fields = [
            "caas_project_id",
            "schedular_project_id",
            "status",
        ]

    def filter_by_caas_project_id(self, queryset, name, value):
        purchase_order_ids = PurchaseOrder.objects.filter(
            caas_project__id=value
        ).values_list("purchaseorder_id", flat=True)
        return queryset.filter(purchase_order_id__in=purchase_order_ids)

    def filter_by_schedular_project_id(self, queryset, name, value):
        purchase_order_ids = PurchaseOrder.objects.filter(
            schedular_project__id=value
        ).values_list("purchaseorder_id", flat=True)
        return queryset.filter(purchase_order_id__in=purchase_order_ids)

    def filter_by_usertype(self, queryset, name, value):
        if value == "pmo":
            pmos_allowed = json.loads(env("PMOS_ALLOWED_TO_VIEW_ALL_INVOICES_AND_POS"))
            if value and self.request.user.username not in pmos_allowed:
                return queryset.filter(
                    approver_email__iexact=self.request.user.username
                )
            return queryset
        return queryset


    def filter_by_status(self, queryset, name, value):
        status_filters = {
            "in_review": Q(bill__isnull=True, status="in_review"),
            "approved": Q(bill__isnull=True, status="approved"),
            "rejected": Q(bill__isnull=True, status="rejected"),
            "accepted": Q(bill__isnull=False) & ~Q(bill__status="paid"),
            "paid": Q(bill__isnull=False, bill__status="paid"),
        }
        if value == "all":
            return queryset
        filter_condition = status_filters.get(value)
        if filter_condition:
            queryset = queryset.filter(filter_condition)
        return queryset

    def filter_json_field(self, queryset, name, value):
        values = value.split(",")
        query = Q()
        for val in values:
            query |= Q(**{f"{name}__contains": val})
        return queryset.filter(query)

    def filter_multi_value(self, queryset, name, value):
        values = value.split(",")
        query = Q()
        for val in values:
            if val:
                query |= Q(**{f"{name}__icontains": val})
        return queryset.filter(query)


class PurchaseOrderListFilter(django_filters.FilterSet):
    caas_project_id = filters.NumberFilter(field_name="caas_project__id")
    schedular_project_id = filters.NumberFilter(field_name="schedular_project__id")
    vendor_id = filters.NumberFilter(field_name="vendor_id")
    status = filters.CharFilter(field_name="status")
    pmo = filters.BooleanFilter(method="filter_by_pmo")
    vendor_name = filters.CharFilter(method="filter_multi_value")
    status = filters.CharFilter(method="filter_multi_value")
    billed_status = filters.CharFilter(method="filter_multi_value")

    class Meta:
        model = PurchaseOrder
        fields = [
            "caas_project_id",
            "schedular_project_id",
            "vendor_id",
            "pmo",
            "status",
        ]

    def filter_by_pmo(self, queryset, name, value):
        if value:

            pmos_allowed = json.loads(
                env("PMOS_ALLOWED_TO_VIEW_ALL_INVOICES_AND_POS")
            )

            if value and self.request.user.username not in pmos_allowed:
                return queryset.filter(
                    custom_field_hash__cf_invoice_approver_s_email__iexact=self.request.user.username
                )
            return queryset
        return queryset

    def filter_json_field(self, queryset, name, value):
        values = value.split(",")
        query = Q()
        for val in values:
            query |= Q(**{f"{name}__contains": val})
        return queryset.filter(query)

    def filter_multi_value(self, queryset, name, value):
        values = value.split(",")
        query = Q()
        for val in values:
            if val:
                query |= Q(**{f"{name}__icontains": val})
        return queryset.filter(query)


class ClientInvoiceListFilter(django_filters.FilterSet):
    caas_project_id = filters.NumberFilter(field_name="sales_order__caas_project__id")
    schedular_project_id = filters.NumberFilter(
        field_name="sales_order__schedular_project__id"
    )
    salesperson_id = filters.CharFilter(field_name="salesperson_id")
    salesorder_id = filters.CharFilter(field_name="salesorder_id")
    participant_email = filters.CharFilter(
        field_name="zoho_customer__email", lookup_expr="icontains"
    )
    batch_name = filters.CharFilter(
        field_name="custom_field_hash__cf_ctt_batch", lookup_expr="icontains"
    )
    usertype = filters.CharFilter(method="filter_by_usertype")
    invoice_number = filters.CharFilter(method="filter_multi_value")
    customer_name = filters.CharFilter(method="filter_multi_value")
    status = filters.CharFilter(method="filter_multi_value")
    salesorder_number = filters.CharFilter(method="filter_multi_value")
    radio_filter = filters.CharFilter(method="filter_by_radio")
    entity__name = filters.BaseInFilter(field_name="entity__name", lookup_expr="in")

    class Meta:
        model = ClientInvoice
        fields = [
            "caas_project_id",
            "schedular_project_id",
            "salesperson_id",
            "salesorder_id",
            "participant_email",
            "batch_name",
            "entity__name",
        ]


    def filter_by_radio(self, queryset, name, value):
        if value == "CTT":
            return queryset.filter(
                Q(salesorder_number__icontains="CTT")
                | Q(salesorder_number__icontains="ctt")
                | Q(salesorder_number__icontains="Ctt")
            )
        elif value == "Meeraq":
            return queryset.filter(
                Q(salesorder_number__icontains="Meeraq")
                | Q(salesorder_number__icontains="meeraq")
                | Q(salesorder_number__icontains="Meeraq")
            )
        elif value == "other":
            return queryset.filter(
                ~(
                    Q(salesorder_number__icontains="CTT")
                    | Q(salesorder_number__icontains="Meeraq")
                    | Q(salesorder_number__icontains="MRQ")
                )
            )

    def filter_json_field(self, queryset, name, value):
        values = value.split(",")
        query = Q()
        for val in values:
            query |= Q(**{f"{name}__contains": val})
        return queryset.filter(query)

    def filter_multi_value(self, queryset, name, value):
        values = value.split(",")
        query = Q()
        for val in values:
            if val:
                query |= Q(**{f"{name}__icontains": val})
        return queryset.filter(query)


class SalesOrderListFilter(django_filters.FilterSet):
    caas_project_id = filters.NumberFilter(field_name="caas_project__id")
    schedular_project_id = filters.NumberFilter(field_name="schedular_project__id")
    salesperson_id = filters.NumberFilter(field_name="salesperson_id")
    status = filters.BaseInFilter(field_name="status", lookup_expr="in")
    batch = filters.CharFilter(method="filter_by_batch")
    participant_email = filters.CharFilter(
        field_name="zoho_customer__email", lookup_expr="icontains"
    )
    batch_name = filters.CharFilter(
        field_name="custom_field_hash__cf_ctt_batch", lookup_expr="icontains"
    )
    ctt = filters.BooleanFilter(method="filter_by_ctt")
    start_date = filters.CharFilter(method="filter_by_start_date")
    end_date = filters.CharFilter(method="filter_by_end_date")
    customer_name = filters.CharFilter(method="filter_multi_value")
    invoiced_status = filters.CharFilter(method="filter_multi_value")
    salesperson_name = filters.CharFilter(method="filter_multi_value")
    entity__name = filters.BaseInFilter(field_name="entity__name", lookup_expr="in")

    class Meta:
        model = SalesOrder
        fields = [
            "caas_project_id",
            "schedular_project_id",
            "salesperson_id",
            "status",
            "batch",
            "ctt",
            "participant_email",
            "batch_name",
            "entity__name",
        ]

    def filter_by_ctt(self, queryset, name, value):
        if value:
            return queryset.filter(
                Q(salesorder_number__icontains="CTT")
                | Q(salesorder_number__icontains="ctt")
                | Q(salesorder_number__icontains="Ctt")
            )
        else:
            return queryset.filter(
                ~(
                    Q(salesorder_number__icontains="CTT")
                    | Q(salesorder_number__icontains="ctt")
                    | Q(salesorder_number__icontains="Ctt")
                )
            )

    def filter_by_start_date(self, queryset, name, value):
        if value:
            formatted_date = datetime.strptime(value, "%d/%m/%Y").strftime("%Y-%m-%d")
            return queryset.filter(date__gte=formatted_date)
        else:
            return queryset

    def filter_by_end_date(self, queryset, name, value):
        if value:
            formatted_date = datetime.strptime(value, "%d/%m/%Y").strftime("%Y-%m-%d")
            return queryset.filter(date__lte=formatted_date)
        else:
            return queryset

    def filter_json_field(self, queryset, name, value):
        values = value.split(",")
        query = Q()
        for val in values:
            query |= Q(**{f"{name}__contains": val})
        return queryset.filter(query)

    def filter_multi_value(self, queryset, name, value):
        values = value.split(",")
        query = Q()
        for val in values:
            if val:
                query |= Q(**{f"{name}__icontains": val})
        return queryset.filter(query)


class StandardFilterSet(filters.FilterSet):
    """
    Standardized FilterSet with reusable methods for multi-value and JSON field filtering.
    """

    @staticmethod
    def filter_multi_value(queryset, name, value):
        """
        Filters the queryset by applying `icontains` lookup for each value in a comma-separated string.
        """
        values = value.split(",")
        query = Q()
        for val in values:
            if val:
                query |= Q(**{f"{name}__icontains": val})
        return queryset.filter(query)

    @staticmethod
    def filter_json_field(queryset, name, value):
        """
        Filters the queryset by applying `contains` lookup for each value in a comma-separated string
        for JSON fields.
        """
        values = value.split(",")
        query = Q()
        for val in values:
            query |= Q(**{f"{name}__contains": val})
        return queryset.filter(query)


class PaymentFilters(django_filters.FilterSet):
    search = filters.CharFilter(method="filter_search")
    type = filters.CharFilter(field_name="type", lookup_expr="icontains")

    class Meta:
        model = Payment
        fields = ["search"]

    def filter_search(self, queryset, name, value):
        # Define search fields
        search_fields = {
            "payment_number": "icontains",
            "customer__contact_name": "icontains",
            "client_invoice__invoice_number": "icontains",
        }
        # Construct the query
        query = Q()
        for field, lookup in search_fields.items():
            if lookup == "icontains":
                query |= Q(**{f"{field}__icontains": value})

        return queryset.filter(query).distinct()


class SalesOrderLineItemFilter(filters.FilterSet):
    start_date = filters.CharFilter(method="filter_by_start_date")
    end_date = filters.CharFilter(method="filter_by_end_date")
    salesperson_id = filters.CharFilter(method="filter_salesperson_id")
    brand = filters.CharFilter(method="filter_brand")
    tabs = filters.CharFilter(method="filter_tabs")

    class Meta:
        model = SalesOrderLineItem
        fields = ["start_date", "end_date"]

    def filter_by_start_date(self, queryset, name, value):
        print("start_data", value)
        if value:
            return queryset.filter(due_date__gte=value)
        else:
            return queryset

    def filter_by_end_date(self, queryset, name, value):
        print("end_data", value)
        if value:
            return queryset.filter(due_date__lte=value)
        else:
            return queryset

    def filter_salesperson_id(self, queryset, name, value):
        # Define search fields
        return queryset.filter(salesorder__salesperson_id=value).distinct()

    def filter_brand(self, queryset, name, value):
        if value == "ctt":
            return queryset.filter(salesorder__salesorder_number__icontains="ctt")
        else:
            return queryset.exclude(salesorder__salesorder_number__icontains="ctt")

    def filter_tabs(self, queryset, name, value):
        current_date = datetime.now().date()
        if value == "due":
            return queryset.filter(due_date__lte=current_date)
        if value == "upcoming":
            return queryset.filter(due_date__gte=current_date)
        return queryset


class CompanyFilter(filters.FilterSet):
    account_name = django_filters.CharFilter(
        field_name="account_name", lookup_expr="icontains", label="Account Name"
    )
    phone = django_filters.CharFilter(
        field_name="phone", lookup_expr="icontains", label="Phone"
    )
    billing_street = django_filters.CharFilter(
        field_name="billing_street", lookup_expr="icontains", label="Billing Street"
    )
    billing_country = django_filters.CharFilter(
        field_name="billing_country", lookup_expr="icontains", label="Billing Country"
    )
    owner = django_filters.CharFilter(
        field_name="owner", lookup_expr="icontains", label="Owner Email"
    )
    billing_state = django_filters.CharFilter(
        field_name="billing_state", lookup_expr="icontains", label="Billing State"
    )
    website = django_filters.CharFilter(
        field_name="website", lookup_expr="icontains", label="Website"
    )
    industry = django_filters.CharFilter(
        field_name="industry", lookup_expr="icontains", label="Industry"
    )

    class Meta:
        model = Company
        fields = [
            "account_name",
            "phone",
            "billing_street",
            "billing_country",
            "owner",
            "billing_state",
            "website",
        ]


class ContactFilter(filters.FilterSet):
    title = filters.CharFilter(
        field_name="title", lookup_expr="icontains", label="Title"
    )
    email = filters.CharFilter(
        field_name="email", lookup_expr="icontains", label="Email"
    )
    mobile = filters.CharFilter(
        field_name="mobile", lookup_expr="icontains", label="Mobile"
    )
    account_name = filters.CharFilter(
        field_name="account_name", lookup_expr="icontains", label="Account Name"
    )

    class Meta:
        model = Contact
        fields = ["title", "email", "mobile", "account_name"]


class OpePurchaseOrderFilter(filters.FilterSet):

    purchaseorder_number = filters.BaseInFilter(
        field_name="purchaseorder_number", lookup_expr="in"
    )
    vendor_name = filters.BaseInFilter(field_name="vendor_name", lookup_expr="in")
    status = filters.BaseInFilter(field_name="status", lookup_expr="in")

    class Meta:
        model = PurchaseOrder
        fields = ["purchaseorder_number", "vendor_name", "status"]
        