from rest_framework import generics, filters
from rest_framework.response import Response
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.exceptions import APIException
from django.db.models import (
    Q,
    Subquery,
    OuterRef,
    Sum,
    F,
    DecimalField,
    Case,
    When,
    Value,
    DecimalField,
    CharField,
    IntegerField,
)
from django.db.models.functions import (
    ExtractDay,
    ExtractMonth,
    ExtractYear,
    Concat,
    Cast,
)
from rest_framework import status
from django.http import HttpResponse
from decimal import Decimal
from .serializers import (
    LimitedVendorSerializer,
    ProjectWiseFinanceSerializer,
    InvoiceDataGetSerializer,
    V2InvoiceCreateSerializer,
    V2VendorDetailSerializer,
    V2InvoiceStatusUpdateSerializer,
    VendorFinancesSerializer,
    VendorSerializer,
    InvoiceStatusUpdateGetSerializer,
    VendorEditSerializer,
    ZohoVendorSerializer,
    SalesOrderGetSerializer,
    SalesOrderSerializer,
    PurchaseOrderGetSerializer,
    ClientInvoiceGetSerializer,
    V2InvoiceDataPDFSerializer,
    InvoiceDataSerializer,
    V2PurchaseOrderAndInvoicesSerializer,
    ClientInvoiceSerializer,
    PurchaseOrderSerializer,
    # TotalRevenueSerializer,
    InvoiceAgingReportSerializer,
    InvoiceAgingDetailSerializer,
)
from zohoapi.filters import (
    InvoiceListFilter,
    PurchaseOrderListFilter,
    ClientInvoiceListFilter,
    SalesOrderListFilter,
)
from rest_framework.views import APIView
from api.utils.methods import get_subordinates_of_a_user_in_role
from zohoapi.utils.methods import (
    fetch_and_process_invoices,
    create_purchase_order,
    create_payload_data,

)
from django.shortcuts import get_object_or_404
from zohoapi.utils.common import SerializerByMethodMixin, get_styles
from .models import (
    InvoiceData,
    Vendor,
    InvoiceStatusUpdate,
    ZohoVendor,
    PurchaseOrder,
    SalesOrder,
    Bill,
    ClientInvoice,
    SalesOrderLineItem,
)
from api.models import Profile, Role
from io import BytesIO
import requests
import pandas as pd
import environ
import os
from django.http import HttpResponse
import pdfkit
from api.permissions import IsInRoles
from django.db import transaction
from django.contrib.auth.models import User
import random
import string
import json
from api.utils.pagination import CustomPageNumberPagination
import io
import xlsxwriter
from datetime import timezone, datetime, date, timedelta

env = environ.Env()

wkhtmltopdf_path = os.environ.get(
    "WKHTMLTOPDF_PATH", r"C:\Program Files\wkhtmltopdf\bin\wkhtmltopdf.exe"
)

pdfkit_config = pdfkit.configuration(wkhtmltopdf=f"{wkhtmltopdf_path}")


class ZohoVendorsListView(generics.ListAPIView):
    permission_classes = [IsAuthenticated, IsInRoles("finance", "ctt_pmo", "pmo")]
    queryset = ZohoVendor.objects.all()
    serializer_class = ZohoVendorSerializer


class VendorsListView(generics.ListAPIView):
    permission_classes = [IsAuthenticated, IsInRoles("pmo", "finance", "superadmin")]
    queryset = Vendor.objects.all()
    serializer_class = VendorSerializer


class VendorUpdateView(generics.UpdateAPIView):
    permission_classes = [IsAuthenticated, IsInRoles("pmo", "superadmin", "finance")]
    queryset = Vendor.objects.all()
    serializer_class = VendorEditSerializer
    lookup_field = "id"


class VendorDetailView(generics.RetrieveAPIView):
    permission_classes = [IsAuthenticated, IsInRoles("pmo", "finance", "superadmin")]
    queryset = Vendor.objects.all()
    serializer_class = V2VendorDetailSerializer





class PurchaseOrderListView(generics.ListAPIView):
    permission_classes = [IsAuthenticated]
    queryset = PurchaseOrder.objects.all()

    serializer_class = PurchaseOrderGetSerializer
    filter_backends = [DjangoFilterBackend, filters.SearchFilter]
    filterset_class = PurchaseOrderListFilter
    search_fields = [
        "purchaseorder_number",
        "vendor_name",
        "total",
        "reference_number",
        "custom_field_hash__cf_invoice_approver_s_email",
    ]
    pagination_class = CustomPageNumberPagination


class PurchaseOrderExportView(PurchaseOrderListView):
    pagination_class = None

    def get(self, request, *args, **kwargs):
        queryset = self.filter_queryset(self.get_queryset())

        output = io.BytesIO()
        workbook = xlsxwriter.Workbook(output)
        worksheet = workbook.add_worksheet("Purchase Orders")

        styles = get_styles(workbook)

        # Helper functions
        def format_date(date_obj):
            if isinstance(date_obj, datetime):
                return date_obj.astimezone(timezone.utc).replace(tzinfo=None)
            elif isinstance(date_obj, date):
                return datetime.combine(date_obj, datetime.min.time())
            return None

        # Headers
        headers = [
            "PO Number",
            "Invoice Approver Email",
            "Date",
            "Created Time",
            "Reference Number",
            "Status",
            "Billed Status",
            "Vendor Name",
            "Currency Symbol",
            "Exchange Rate",
            "Total Quantity",
            "Total",
            "Tax Total",
            "Payment",
        ]

        # Set column widths
        column_widths = {
            0: 15,  # PO Number
            1: 35,  # Invoice Approver Email
            2: 15,  # Date
            3: 20,  # Created Time
            4: 20,  # Reference Number
            5: 15,  # Status
            6: 15,  # Billed Status
            7: 30,  # Vendor Name
            8: 12,  # Currency Symbol
            9: 15,  # Exchange Rate
            10: 15,  # Total Quantity
            11: 15,  # Total
            12: 15,  # Tax Total
            13: 15,
        }

        for col, width in column_widths.items():
            worksheet.set_column(col, col, width)

        # Write headers
        for col, header in enumerate(headers):
            worksheet.write(0, col, header, styles["header_style"])

        # Write data rows
        for row, po in enumerate(queryset, start=1):
            worksheet.write(row, 0, po.purchaseorder_number, styles["cell_style"])
            worksheet.write(
                row,
                1,
                po.custom_field_hash.get("cf_invoice_approver_s_email", ""),
                styles["cell_style"],
            )

            # Handle date
            if po.date:
                date_value = format_date(po.date)
                if date_value:
                    worksheet.write_datetime(row, 2, date_value, styles["date_style"])
                else:
                    worksheet.write(row, 2, "", styles["cell_style"])
            else:
                worksheet.write(row, 2, "", styles["cell_style"])

            # Handle created_time
            if po.created_time:
                datetime_value = format_date(po.created_time)
                worksheet.write_datetime(
                    row, 3, datetime_value, styles["datetime_style"]
                )
            else:
                worksheet.write(row, 3, "", styles["cell_style"])

            worksheet.write(row, 4, po.reference_number, styles["cell_style"])
            worksheet.write(row, 5, po.status, styles["cell_style"])
            worksheet.write(row, 6, po.billed_status, styles["cell_style"])
            worksheet.write(row, 7, po.vendor_name, styles["cell_style"])
            worksheet.write(row, 8, po.currency_symbol, styles["cell_style"])
            worksheet.write(row, 9, float(po.exchange_rate), styles["number_style"])
            worksheet.write(row, 10, po.total_quantity, styles["number_style"])
            worksheet.write(row, 11, float(po.total), styles["number_style"])
            worksheet.write(row, 12, float(po.tax_total), styles["number_style"])

            worksheet.write(
                row,
                13,
                (
                    "Singapore"
                    if po.entity and po.entity.id != int(env("INDIA_ENTITY_ID"))
                    else "India"
                ),
                styles["number_style"],
            )

        # Add autofilter
        worksheet.autofilter(0, 0, len(queryset), len(headers) - 1)

        # Freeze panes to keep headers visible
        worksheet.freeze_panes(1, 0)

        workbook.close()

        # Create the HttpResponse
        output.seek(0)
        filename = f'purchase_orders_{datetime.now().strftime("%d%m%Y")}.xlsx'
        response = HttpResponse(
            output.read(),
            content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        )
        response["Content-Disposition"] = f'attachment; filename="{filename}"'

        return response


class InvoiceListCreateAPIView(SerializerByMethodMixin, generics.ListCreateAPIView):
    permission_classes = [IsAuthenticated]
    serializer_map = {
        "GET": InvoiceDataGetSerializer,
        "POST": V2InvoiceCreateSerializer,
    }
    filter_backends = [DjangoFilterBackend, filters.SearchFilter]
    filterset_class = InvoiceListFilter
    search_fields = [
        "invoice_number",
        "purchase_order_no",
        "vendor_name",
        "approver_email",
    ]
    pagination_class = CustomPageNumberPagination

    def get_queryset(self):
        if self.request.method == "GET":
            # Use select_related to efficiently fetch the related bill
            queryset = InvoiceData.objects.all().select_related("bill")
        elif self.request.method == "POST":
            # Customize the queryset for create action if needed
            queryset = InvoiceData.objects.all()

        return queryset

    def get_serializer_context(self):
        return {"request": self.request}


class InvoicesExportView(InvoiceListCreateAPIView):
    pagination_class = None

    def get(self, request, *args, **kwargs):
        queryset = self.filter_queryset(self.get_queryset())

        output = io.BytesIO()
        workbook = xlsxwriter.Workbook(output)
        worksheet = workbook.add_worksheet("Invoices")

        # Define styles
        styles = get_styles(workbook)

        # Write headers
        headers, column_widths = self.get_headers_and_widths()
        self.write_headers(worksheet, headers, styles["header_style"], column_widths)

        # Write data rows
        self.write_data_rows(worksheet, queryset, styles)

        # Finalize workbook
        worksheet.autofilter(0, 0, len(queryset), len(headers) - 1)
        worksheet.freeze_panes(1, 0)
        workbook.close()

        # Prepare the response
        output.seek(0)
        filename = f'invoices_{datetime.now().strftime("%Y%m%d_%H%M%S")}.xlsx'
        response = HttpResponse(
            output.read(),
            content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        )
        response["Content-Disposition"] = f'attachment; filename="{filename}"'
        return response

    @staticmethod
    def get_headers_and_widths():
        headers = [
            "Vendor Name",
            "Vendor Email",
            "Purchase Order No",
            "Currency Symbol",
            "Invoice Number",
            "Created At",
            "Total",
            "Invoice Date",
            "Approver Email",
            "Status",
            "Bill Number",  # Added Bill Number column
        ]
        column_widths = {
            0: 30,
            1: 35,
            2: 20,
            3: 15,
            4: 20,
            5: 20,
            6: 15,
            7: 20,
            8: 30,
            9: 15,
            10: 20,  # Width for Bill Number column
        }
        return headers, column_widths

    @staticmethod
    def write_headers(worksheet, headers, header_style, column_widths):
        for col, header in enumerate(headers):
            worksheet.write(0, col, header, header_style)
            worksheet.set_column(col, col, column_widths.get(col, 15))

    def write_data_rows(self, worksheet, queryset, styles):
        for row, invoice in enumerate(queryset, start=1):
            worksheet.write(row, 0, invoice.vendor_name, styles["cell_style"])
            worksheet.write(row, 1, invoice.vendor_email, styles["cell_style"])
            worksheet.write(row, 2, invoice.purchase_order_no, styles["cell_style"])
            worksheet.write(row, 3, invoice.currency_symbol, styles["cell_style"])
            worksheet.write(row, 4, invoice.invoice_number, styles["cell_style"])

            # Write date fields
            self.write_date(
                worksheet,
                row,
                5,
                invoice.created_at,
                styles["date_style"],
                styles["cell_style"],
            )
            self.write_date(
                worksheet,
                row,
                7,
                invoice.invoice_date,
                styles["date_style"],
                styles["cell_style"],
            )

            # Write remaining fields
            worksheet.write(row, 6, invoice.total, styles["number_style"])
            worksheet.write(row, 8, invoice.approver_email, styles["cell_style"])

            # Write status using the bill relationship
            status = self.get_invoice_status(
                {
                    "bill": {"status": invoice.bill.status} if invoice.bill else None,
                    "status": invoice.status,
                }
            )
            worksheet.write(row, 9, status, styles["cell_style"])

            # Write bill number if available
            bill_number = invoice.bill.bill_number if invoice.bill else ""
            worksheet.write(row, 10, bill_number, styles["cell_style"])

    @staticmethod
    def write_date(worksheet, row, col, date_obj, date_style, cell_style):
        if date_obj:
            date_value = InvoicesExportView.format_date(date_obj)
            if date_value:
                worksheet.write_datetime(row, col, date_value, date_style)
            else:
                worksheet.write(row, col, "", cell_style)
        else:
            worksheet.write(row, col, "", cell_style)

    @staticmethod
    def format_date(date_obj):
        if isinstance(date_obj, datetime):
            return date_obj.astimezone(timezone.utc).replace(tzinfo=None)
        elif isinstance(date_obj, date):
            return datetime.combine(date_obj, datetime.min.time())
        return None

    @staticmethod
    def get_invoice_status(invoice):
        if invoice.get("bill"):
            if invoice["bill"].get("status") == "paid":
                return "Paid"
            else:
                return "Accepted"
        # Default to the status in the invoice, if available
        status = invoice.get("status", "").replace("_", " ").title()
        return status


class InvoiceRetrieveDestroyView(generics.RetrieveDestroyAPIView):
    queryset = InvoiceData.objects.all()
    serializer_class = InvoiceDataGetSerializer
    permission_classes = [IsAuthenticated, IsInRoles("pmo", "finance", "sales")]

    def get_queryset(self):
        # Use select_related to efficiently fetch the related bill in a single query
        return InvoiceData.objects.select_related("bill")


class InvoiceUpdatesListAPIView(generics.ListAPIView):
    permission_classes = [
        IsAuthenticated,
        IsInRoles("pmo", "finance", "vendor", "superadmin"),
    ]
    serializer_class = InvoiceStatusUpdateGetSerializer

    def get_queryset(self):
        invoice_id = self.kwargs.get("invoice_id")
        return InvoiceStatusUpdate.objects.filter(invoice_id=invoice_id)


class InvoiceStatusUpdateView(generics.UpdateAPIView):
    queryset = InvoiceData.objects.all()
    serializer_class = V2InvoiceStatusUpdateSerializer
    permission_classes = [IsAuthenticated, IsInRoles("pmo", "finance")]


class SalesOrdersListView(generics.ListAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class = SalesOrderGetSerializer
    queryset = SalesOrder.objects.all()
    filter_backends = [DjangoFilterBackend, filters.SearchFilter]
    filterset_class = SalesOrderListFilter
    search_fields = [
        "salesorder_number",
        "customer_name",
        "total",
        "reference_number",
        "custom_field_hash__cf_invoice_approver_s_email",
    ]
    pagination_class = CustomPageNumberPagination

    def get_queryset(self):
        user_type = self.request.query_params.get("usertype")
        user_id = self.request.query_params.get("user_id")
        sales_order_filter = Q(added_by__id=user_id)
        if user_id == "all":
            sales_order_filter = Q()
        elif user_id and user_type and self.request.user.id == int(user_id):
            role = Role.objects.get(name=user_type)
            filter_subordinates = get_subordinates_of_a_user_in_role(
                "SalesOrder", self.request.user, role
            )
            if filter_subordinates:
                sales_order_filter |= filter_subordinates

        queryset = SalesOrder.objects.filter(sales_order_filter)
        return queryset


class ClientInvoiceRetrieveUpdateView(generics.RetrieveUpdateAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class = ClientInvoiceSerializer
    lookup_field = "invoice_id"  # This will be used to fetch the invoice by ID

    def retrieve(self, request, *args, **kwargs):
        invoice_id = kwargs.get("invoice_id")
        client_invoice = ClientInvoice.objects.filter(invoice_id=invoice_id).first()
        
        if client_invoice:
            serializer = self.get_serializer(client_invoice)
            return Response(serializer.data, status=status.HTTP_200_OK)
        else:
            return Response(
                {"error": "Failed to fetch invoice data"},
                status=status.HTTP_404_NOT_FOUND,
            )







class ClientInvoiceListCreateView(SerializerByMethodMixin, generics.ListCreateAPIView):
    permission_classes = [IsAuthenticated]
    queryset = ClientInvoice.objects.all()
    filter_backends = [DjangoFilterBackend, filters.SearchFilter]
    filterset_class = ClientInvoiceListFilter
    serializer_map = {
        "GET": ClientInvoiceGetSerializer,
        "POST": ClientInvoiceSerializer,
    }
    search_fields = [
        "invoice_number",
        "customer_name",
        "total",
        "salesorder_number",
        "custom_field_hash__cf_ctt_batch",
        "sales_order__custom_field_hash__cf_ctt_batch",
    ]
    pagination_class = CustomPageNumberPagination

    def get_queryset(self):
        user_id = self.request.query_params.get("user_id")
        user_type = self.request.query_params.get("usertype")
        client_invoices_filter = Q(sales_order__added_by__id=user_id)
        if user_id == "all":
            client_invoices_filter = Q()
        elif user_id and user_type and self.request.user.id == int(user_id):
            role = Role.objects.get(name=user_type)
            filter_subordinates = get_subordinates_of_a_user_in_role(
                "ClientInvoice", self.request.user, role
            )
            if filter_subordinates:
                sales_order_filter |= filter_subordinates
        queryset = ClientInvoice.objects.filter(client_invoices_filter)
        return queryset


class DownloadInvoicePdf(generics.RetrieveAPIView):
    queryset = InvoiceData.objects.all()
    serializer_class = V2InvoiceDataPDFSerializer
    permission_classes = [IsAuthenticated, IsInRoles("pmo", "vendor", "finance")]

    def retrieve(self, request, *args, **kwargs):
        instance = self.get_object()
        serializer = self.get_serializer(instance)
        pdf = serializer.data.get("pdf")
        response = HttpResponse(pdf, content_type="application/pdf")
        response["Content-Disposition"] = (
            f'attachment; filename={f"{instance.invoice_number}_invoice.pdf"}'
        )
        return response


class V2DownloadAttachedInvoice(generics.RetrieveAPIView):
    permission_classes = [IsAuthenticated, IsInRoles("pmo", "vendor", "finance")]
    queryset = InvoiceData.objects.all()
    serializer_class = InvoiceDataSerializer
    lookup_field = "id"
    lookup_url_kwarg = "record_id"

    def retrieve(self, request, *args, **kwargs):
        try:
            invoice = self.get_object()
            serializer = self.get_serializer(invoice)
            response = requests.get(serializer.data["attatched_invoice"])
            if response.status_code == 200:
                file_content = response.content
                content_type = response.headers.get("Content-Type", "application/pdf")
                file_response = HttpResponse(file_content, content_type=content_type)
                file_response["Content-Disposition"] = (
                    f'attachment; filename="{invoice.invoice_number}_invoice.pdf"'
                )
                return file_response
            else:
                return HttpResponse(
                    "Failed to download the file", status=response.status_code
                )
        except Exception as e:
            print(str(e))
            return Response(
                {"error": "Failed to download invoice."},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )


class PurchaseOrderAndInvoicesView(generics.RetrieveAPIView):
    permission_classes = [IsAuthenticated, IsInRoles("vendor", "pmo", "finance")]
    lookup_field = "purchase_order_id"
    serializer_class = V2PurchaseOrderAndInvoicesSerializer

    def get_queryset(self):
        purchase_order_id = self.kwargs.get("purchase_order_id")
        purchase_order = PurchaseOrder.objects.get(purchaseorder_id= purchase_order_id)
        if purchase_order:
            invoices = InvoiceData.objects.filter(purchase_order_id=purchase_order_id)
            return {"purchase_order": purchase_order, "invoices": invoices}
        return None

    def retrieve(self, request, *args, **kwargs):
        data = self.get_queryset()
        if data:
            serializer = self.get_serializer(data)
            return Response(serializer.data, status=status.HTTP_200_OK)
        else:
            return Response(
                {
                    "error": "Failed to fetch purchase order data or invalid purchase order ID."
                },
                status=status.HTTP_400_BAD_REQUEST,
            )


class InvoicesWithStatusView(generics.RetrieveAPIView):
    permission_classes = [IsAuthenticated, IsInRoles("vendor", "pmo", "finance")]
    lookup_field = "vendor_id"
    queryset = InvoiceData.objects.none()

    def retrieve(self, request, *args, **kwargs):
        vendor_id = kwargs.get("vendor_id")
        purchase_order_id = kwargs.get("purchase_order_id", "all")
        invoice_res, http_status = fetch_and_process_invoices(
            vendor_id, purchase_order_id
        )
        return Response(invoice_res, status=http_status)


class TotalRevenueView(generics.GenericAPIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, vendor_id):
        try:
            invoices = InvoiceData.objects.filter(vendor_id=vendor_id)
            total_revenue = sum(invoice.total for invoice in invoices)
            return Response({"total_revenue": total_revenue})
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)


class SalesOrderInvoiceListView(generics.GenericAPIView):
    permission_classes = [IsAuthenticated]
    queryset = SalesOrder.objects.all()

    def get(self, request, sales_order_id):
        try:
            # Fetch sales order data
            sales_order =  SalesOrder.objects.get(salesorder_id=sales_order_id)
            if not sales_order:
                return Response(
                    {"error": "Failed to fetch sales order data"},
                    status=status.HTTP_404_NOT_FOUND,
                )
   
            # Fetch all client invoices
            invoices = [
              ClientInvoice.objects.get(invoice_id=client_invoice["invoice_id"])
                for client_invoice in sales_order.get("invoices", [])
            ]
            return Response(invoices, status=status.HTTP_200_OK)

        except Exception as e:
            print(str(e))
            return Response(
                {"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class LineItemsDetailExcelView(generics.GenericAPIView):
    permission_classes = [AllowAny]

    def get(self, request, *args, **kwargs):
        # Fetch line items
        line_items = SalesOrderLineItem.objects.filter(salesorder__isnull=False)
        data = line_items.values(
            "salesorder__salesorder_number",
            "description",
            "rate",
            "quantity",
            "quantity_invoiced",
            "tax_percentage",
            "item_total",
        )
        df = pd.DataFrame(data)
        df = df.rename(
            columns={
                "salesorder__salesorder_number": "Sales Order Number",
                "description": "Items and description",
                "rate": "Rate",
                "quantity": "Quantity",
                "quantity_invoiced": "Quantity Invoiced",
                "tax_percentage": "Tax Percentage",
                "item_total": "Item Total",
            }
        )

        # Convert Quantity and Quantity Invoiced columns to floating-point numbers
        df["Quantity"] = df["Quantity"].astype(float)
        df["Quantity Invoiced"] = df["Quantity Invoiced"].astype(float)

        # Round the floating-point numbers to integers
        df["Quantity"] = df["Quantity"].round(0).astype(int)
        df["Quantity Invoiced"] = df["Quantity Invoiced"].round(0).astype(int)

        # Save the DataFrame to an Excel file in-memory
        excel_data = BytesIO()
        df.to_excel(excel_data, index=False)
        excel_data.seek(0)

        # Create the response with the Excel file
        response = HttpResponse(
            excel_data.read(),
            content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        )
        response["Content-Disposition"] = (
            f"attachment; filename=line_items_details.xlsx"
        )

        return response





class UpdateVendorMsmeView(generics.GenericAPIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, vendor_id):
        try:
            # Retrieve the vendor
            vendor = Vendor.objects.get(id=vendor_id)

            # Update the MSME status
            is_msme = request.data.get("is_msme", None)
            vendor.is_msme = is_msme
            vendor.save()

            return Response(
                {"message": "MSME status updated successfully!"},
                status=status.HTTP_200_OK,
            )
        except Vendor.DoesNotExist:
            return Response(
                {"error": "Vendor not found"}, status=status.HTTP_404_NOT_FOUND
            )
        except Exception as e:
            print(str(e))
            return Response(
                {"error": "Failed to update MSME status"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )


class DeleteInvoiceView(generics.DestroyAPIView):
    queryset = InvoiceData.objects.all()
    permission_classes = [IsAuthenticated, IsInRoles("vendor", "finance", "pmo")]

    def delete(self, request, *args, **kwargs):
        try:
            invoice = get_object_or_404(self.get_queryset(), id=kwargs["invoice_id"])
            invoice.delete()
            return Response(status=status.HTTP_204_NO_CONTENT)
        except InvoiceData.DoesNotExist:
            return Response(status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            print(str(e))
            return Response(
                {"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class EditVendorExistingView(generics.UpdateAPIView):
    queryset = Vendor.objects.all()
    permission_classes = [
        IsAuthenticated,
        IsInRoles("pmo", "vendor", "superadmin", "finance"),
    ]
    lookup_field = "id"

    def put(self, request, *args, **kwargs):
        try:
            vendor = self.get_object()
            data = request.data
            email = data.get("email", "").strip().lower()
            vendor_id = data.get("vendor", "")
            phone = data.get("phone", "")

            existing_user = (
                User.objects.filter(username=email)
                .exclude(username=vendor.email)
                .first()
            )
            if existing_user:
                return Response(
                    {"error": "User with this email already exists."},
                    status=status.HTTP_400_BAD_REQUEST,
                )

            vendor_details = self.get_vendor(vendor_id)
            name = vendor_details["contact_name"]

            vendor.user.user.username = email
            vendor.user.user.email = email
            vendor.user.user.save()

            vendor.email = email
            vendor.name = name
            vendor.phone = phone
            vendor.vendor_id = vendor_id
            vendor.save()

            return Response(
                {"message": "Vendor updated successfully!"}, status=status.HTTP_200_OK
            )

        except Vendor.DoesNotExist:
            return Response(
                {"error": "Vendor not found."}, status=status.HTTP_404_NOT_FOUND
            )
        except Exception as e:
            print(str(e))
            return Response(
                {"error": "Failed to update vendor"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

    def get_vendor(self, vendor_id):
        # Replace with actual implementation of get_vendor
        # This is a placeholder to demonstrate where your existing logic goes.
        return {
            "contact_name": "Vendor Name",  # Example response
            # Add more fields as needed based on your logic
        }


class UpdateInvoiceAllowedView(generics.UpdateAPIView):
    queryset = Vendor.objects.all()
    serializer_class = VendorEditSerializer
    permission_classes = [IsAuthenticated, IsInRoles("pmo", "superadmin", "finance")]
    lookup_field = "id"

    def put(self, request, *args, **kwargs):
        try:
            vendor = self.get_object()
        except Vendor.DoesNotExist:
            return Response(status=status.HTTP_404_NOT_FOUND)

        serializer = self.get_serializer(vendor, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class CoachingPurchaseOrderCreateView(generics.GenericAPIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, *args, **kwargs):
        try:
            purchaseorder_created, purchase_order = create_purchase_order(
                request,
            )
            if purchaseorder_created and purchase_order:
                return Response(
                    {"message": "Purchase Order created successfully."},
                    status=status.HTTP_201_CREATED,
                )
            else:
                return Response(
                    {"error": "Failed to create Purchase Order."},
                    status=status.HTTP_500_INTERNAL_SERVER_ERROR,
                )

        except Exception as e:
            print(str(e))
            return Response(
                {"error": "An error occurred during Purchase Order creation."},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )


class UpdateVendorMsmeView(generics.GenericAPIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, vendor_id):
        try:
            # Retrieve the vendor
            vendor = Vendor.objects.get(id=vendor_id)
            # Update the MSME status
            is_msme = request.data.get("is_msme", None)
            vendor.is_msme = is_msme
            vendor.save()
            return Response(
                {"message": "MSME status updated successfully!"},
                status=status.HTTP_200_OK,
            )
        except Vendor.DoesNotExist:
            return Response(
                {"error": "Vendor not found"}, status=status.HTTP_404_NOT_FOUND
            )
        except Exception as e:
            print(str(e))
            return Response(
                {"error": "Failed to update MSME status"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )


class DeleteInvoiceView(generics.DestroyAPIView):
    queryset = InvoiceData.objects.all()
    permission_classes = [IsAuthenticated, IsInRoles("vendor", "finance", "pmo")]

    def delete(self, request, *args, **kwargs):
        try:
            invoice = get_object_or_404(self.get_queryset(), id=kwargs["invoice_id"])
            invoice.delete()
            return Response(status=status.HTTP_204_NO_CONTENT)
        except InvoiceData.DoesNotExist:
            return Response(status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            print(str(e))
            return Response(
                {"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class EditVendorExistingView(generics.UpdateAPIView):
    queryset = Vendor.objects.all()
    permission_classes = [
        IsAuthenticated,
        IsInRoles("pmo", "vendor", "superadmin", "finance"),
    ]
    lookup_field = "id"

    def put(self, request, *args, **kwargs):
        try:
            vendor = self.get_object()
            data = request.data
            email = data.get("email", "").strip().lower()
            vendor_id = data.get("vendor", "")
            phone = data.get("phone", "")

            existing_user = (
                User.objects.filter(username=email)
                .exclude(username=vendor.email)
                .first()
            )
            if existing_user:
                return Response(
                    {"error": "User with this email already exists."},
                    status=status.HTTP_400_BAD_REQUEST,
                )

            vendor_details = self.get_vendor(vendor_id)
            name = vendor_details["contact_name"]

            vendor.user.user.username = email
            vendor.user.user.email = email
            vendor.user.user.save()

            vendor.email = email
            vendor.name = name
            vendor.phone = phone
            vendor.vendor_id = vendor_id
            vendor.save()

            return Response(
                {"message": "Vendor updated successfully!"}, status=status.HTTP_200_OK
            )

        except Vendor.DoesNotExist:
            return Response(
                {"error": "Vendor not found."}, status=status.HTTP_404_NOT_FOUND
            )
        except Exception as e:
            print(str(e))
            return Response(
                {"error": "Failed to update vendor"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

    def get_vendor(self, vendor_id):
        # Replace with actual implementation of get_vendor
        # This is a placeholder to demonstrate where your existing logic goes.
        return {
            "contact_name": "Vendor Name",  # Example response
            # Add more fields as needed based on your logic
        }


class UpdateInvoiceAllowedView(generics.UpdateAPIView):
    queryset = Vendor.objects.all()
    serializer_class = VendorEditSerializer
    permission_classes = [IsAuthenticated, IsInRoles("pmo", "superadmin", "finance")]
    lookup_field = "id"

    def put(self, request, *args, **kwargs):
        try:
            vendor = self.get_object()
        except Vendor.DoesNotExist:
            return Response(status=status.HTTP_404_NOT_FOUND)

        serializer = self.get_serializer(vendor, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)





class InvoiceAgingReportView(generics.ListAPIView):
    serializer_class = InvoiceAgingReportSerializer
    filter_backends = [DjangoFilterBackend]
    filterset_class = ClientInvoiceListFilter

    def safe_sum(self, field_name, data):
        from decimal import Decimal

        total = Decimal("0")
        for item in data:
            # Handle None values by treating them as 0
            value = item.get(field_name) or Decimal("0")
            total += value
        return total

    def get_queryset(self):
        # Get current date
        today = datetime.now().date()

        # Get sorting parameters from request
        sort_field = self.request.query_params.get("sort_field", "customer_name")
        sort_order = self.request.query_params.get("sort_order", "asc")
        search = self.request.query_params.get("search", "")

        # Map frontend field names to database fields if needed
        field_mapping = {
            "customer_name": "customer_name",
            "current": "current",
            "days_1_15": "days_1_15",
            "days_16_30": "days_16_30",
            "days_31_45": "days_31_45",
            "days_over_45": "days_over_45",
            "total": "total",
        }

        # Get the actual database field name
        db_sort_field = field_mapping.get(sort_field, "customer_name")

        # Calculate aging brackets with exchange rate applied
        # include search also

        queryset = (
            ClientInvoice.objects.filter(
                status__in=[
                    "overdue",
                    "sent",
                    "partially_paid",
                ],  # Only include unpaid/open invoices
                customer_name__icontains=search,
            )
            .values(
                "customer_name",  # Group by customer
            )
            .annotate(
                current=Sum(
                    Case(
                        When(
                            due_date__gte=today, then=F("balance") * F("exchange_rate")
                        ),
                        default=Value(0),
                        output_field=DecimalField(max_digits=15, decimal_places=2),
                    )
                ),
                days_1_15=Sum(
                    Case(
                        When(
                            due_date__lt=today,
                            due_date__gte=today - timedelta(days=15),
                            then=F("balance") * F("exchange_rate"),
                        ),
                        default=Value(0),
                        output_field=DecimalField(max_digits=15, decimal_places=2),
                    )
                ),
                days_16_30=Sum(
                    Case(
                        When(
                            due_date__lt=today - timedelta(days=15),
                            due_date__gte=today - timedelta(days=30),
                            then=F("balance") * F("exchange_rate"),
                        ),
                        default=Value(0),
                        output_field=DecimalField(max_digits=15, decimal_places=2),
                    )
                ),
                days_31_45=Sum(
                    Case(
                        When(
                            due_date__lt=today - timedelta(days=30),
                            due_date__gte=today - timedelta(days=45),
                            then=F("balance") * F("exchange_rate"),
                        ),
                        default=Value(0),
                        output_field=DecimalField(max_digits=15, decimal_places=2),
                    )
                ),
                days_over_45=Sum(
                    Case(
                        When(
                            due_date__lt=today - timedelta(days=45),
                            then=F("balance") * F("exchange_rate"),
                        ),
                        default=Value(0),
                        output_field=DecimalField(max_digits=15, decimal_places=2),
                    )
                ),
                total=Sum(
                    F("balance") * F("exchange_rate")
                ),  # Total outstanding balance with exchange rate
                # Original amounts without exchange rate (if needed for reference)
                original_current=Sum(
                    Case(
                        When(due_date__gte=today, then=F("balance")),
                        default=Value(0),
                        output_field=DecimalField(max_digits=15, decimal_places=2),
                    )
                ),
                original_total=Sum("balance"),
            )
        )

        # Apply ordering based on sort parameters
        if sort_order.lower() == "desc":
            queryset = queryset.order_by(f"-{db_sort_field}")
        else:
            queryset = queryset.order_by(db_sort_field)

        return queryset

    def list(self, request, *args, **kwargs):
        if request.query_params.get("download") == "excel":
            return self.download_excel(request)
        queryset = self.filter_queryset(self.get_queryset())
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            response = self.get_paginated_response(serializer.data)
            # Calculate totals for all values
            all_data = self.filter_queryset(self.get_queryset())
            totals = {
                "total_count": all_data.count(),
                "current": self.safe_sum("current", all_data),
                "days_1_15": self.safe_sum("days_1_15", all_data),
                "days_16_30": self.safe_sum("days_16_30", all_data),
                "days_31_45": self.safe_sum("days_31_45", all_data),
                "days_over_45": self.safe_sum("days_over_45", all_data),
                "total": self.safe_sum("total", all_data),
                # Original totals without exchange rate (if needed)
                "original_current": self.safe_sum("original_current", all_data),
                "original_total": self.safe_sum("original_total", all_data),
            }
            # Add totals to response
            response.data["totals"] = totals
            # Add sort information to response for frontend reference
            response.data["sort_info"] = {
                "field": request.query_params.get("sort_field", "customer_name"),
                "order": request.query_params.get("sort_order", "asc"),
            }
            return response
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)

    def download_excel(self, request):
        # Get filtered queryset
        queryset = self.filter_queryset(self.get_queryset())
        # Create a workbook and add a worksheet
        output = BytesIO()
        workbook = xlsxwriter.Workbook(output)
        worksheet = workbook.add_worksheet("Invoice Aging Report")

        # Add styles
        header_format = workbook.add_format(
            {
                "bold": True,
                "bg_color": "#f0f0f0",
                "border": 1,
                "align": "center",
                "valign": "vcenter",
                "text_wrap": True,
            }
        )

        cell_format = workbook.add_format({"border": 1})

        number_format = workbook.add_format(
            {"num_format": "#,##0.00", "border": 1, "align": "right"}
        )

        customer_format = workbook.add_format(
            {"border": 1, "align": "left", "bold": True}
        )

        total_format = workbook.add_format(
            {
                "bold": True,
                "num_format": "#,##0.00",
                "border": 1,
                "align": "right",
                "bg_color": "#f0f0f0",
            }
        )

        total_label_format = workbook.add_format(
            {"bold": True, "border": 1, "align": "left", "bg_color": "#f0f0f0"}
        )

        # Define headers
        headers = [
            "Customer Name",
            "Current",
            "1-15 Days",
            "16-30 Days",
            "31-45 Days",
            "> 45 Days",
            "Total",
        ]

        # Write headers
        for col, header in enumerate(headers):
            worksheet.write(0, col, header, header_format)

        # Auto-fit columns
        worksheet.set_column(0, 0, 40)  # Customer Name
        worksheet.set_column(1, 6, 15)  # Amount columns

        # Write data rows
        row = 1
        for item in queryset:
            worksheet.write(row, 0, item["customer_name"], customer_format)
            worksheet.write(row, 1, float(item["current"] or 0), number_format)
            worksheet.write(row, 2, float(item["days_1_15"] or 0), number_format)
            worksheet.write(row, 3, float(item["days_16_30"] or 0), number_format)
            worksheet.write(row, 4, float(item["days_31_45"] or 0), number_format)
            worksheet.write(row, 5, float(item["days_over_45"] or 0), number_format)
            worksheet.write(row, 6, float(item["total"] or 0), number_format)
            row += 1

        # Calculate totals
        all_data = self.filter_queryset(self.get_queryset())

        total_current = float(self.safe_sum("current", all_data) or 0)
        total_days_1_15 = float(self.safe_sum("days_1_15", all_data) or 0)
        total_days_16_30 = float(self.safe_sum("days_16_30", all_data) or 0)
        total_days_31_45 = float(self.safe_sum("days_31_45", all_data) or 0)
        total_days_over_45 = float(self.safe_sum("days_over_45", all_data) or 0)
        total_total = float(self.safe_sum("total", all_data) or 0)

        # Write totals row
        total_row = row
        worksheet.write(total_row, 0, "TOTAL", total_label_format)
        worksheet.write(total_row, 1, total_current, total_format)
        worksheet.write(total_row, 2, total_days_1_15, total_format)
        worksheet.write(total_row, 3, total_days_16_30, total_format)
        worksheet.write(total_row, 4, total_days_31_45, total_format)
        worksheet.write(total_row, 5, total_days_over_45, total_format)
        worksheet.write(total_row, 6, total_total, total_format)

        # Add a chart
        chart = workbook.add_chart({"type": "column"})

        # Configure the chart
        chart.add_series(
            {
                "name": "Aging Report",
                "categories": [
                    "Invoice Aging Report",
                    0,
                    1,
                    0,
                    5,
                ],  # Headers for age buckets
                "values": [
                    "Invoice Aging Report",
                    total_row,
                    1,
                    total_row,
                    5,
                ],  # Total values
                "data_labels": {"value": True, "num_format": "#,##0.00"},
            }
        )

        chart.set_title({"name": "Invoice Aging Summary"})
        chart.set_x_axis({"name": "Age Bucket"})
        chart.set_y_axis({"name": "Amount"})

        # Insert the chart into the worksheet
        worksheet.insert_chart(
            "A" + str(total_row + 3), chart, {"x_scale": 1.5, "y_scale": 1}
        )

        # Get current date for filename
        today_str = datetime.now().strftime("%Y-%m-%d")

        # Close the workbook
        workbook.close()

        # Create response with the Excel file
        output.seek(0)
        response = HttpResponse(
            output.read(),
            content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        )

        # Set filename
        filename = f"Invoice_Aging_Report_{today_str}.xlsx"
        response["Content-Disposition"] = f'attachment; filename="{filename}"'

        return response


class InvoiceAgingDetailView(generics.ListAPIView):
    serializer_class = InvoiceAgingDetailSerializer
    filter_backends = [DjangoFilterBackend]
    filterset_class = ClientInvoiceListFilter

    def get_queryset(self):
        # Get current date
        today = datetime.now().date()
        # Get age bucket from query params (current, days_1_15, days_16_30, days_31_45, days_over_45)
        age_bucket = self.request.query_params.get("age_bucket", "days_over_45")
        # Define date ranges based on age bucket
        if age_bucket == "current":
            date_filter = Q(due_date__gte=today)
        elif age_bucket == "days_1_15":
            date_filter = Q(due_date__lt=today) & Q(
                due_date__gte=today - timedelta(days=15)
            )
        elif age_bucket == "days_16_30":
            date_filter = Q(due_date__lt=today - timedelta(days=15)) & Q(
                due_date__gte=today - timedelta(days=30)
            )
        elif age_bucket == "days_31_45":
            date_filter = Q(due_date__lt=today - timedelta(days=30)) & Q(
                due_date__gte=today - timedelta(days=45)
            )
        else:  # days_over_45 (default)
            date_filter = Q(due_date__lt=today - timedelta(days=45))

        # Get sorting parameters
        sort_field = self.request.query_params.get("sort_field", "due_date")
        sort_order = self.request.query_params.get("sort_order", "desc")

        # Map frontend field names to database fields
        field_mapping = {
            "due_date": "due_date",
            "invoice_number": "invoice_number",
            "status": "status",
            "customer_name": "customer_name",
            "age": "age_days",
            "amount": "amount",
            "balance_due": "balance_due",
        }

        # Get the database field for sorting
        db_sort_field = field_mapping.get(sort_field, "due_date")

        queryset = (
            ClientInvoice.objects.filter(
                status__in=[
                    "overdue",
                    "sent",
                    "partially_paid",
                ],  # Include relevant statuses
            )
            .filter(date_filter)
            .annotate(
                # Calculate day difference using extract
                day_diff=ExtractDay(Value(today)) - ExtractDay(F("due_date")),
                month_diff=ExtractMonth(Value(today)) - ExtractMonth(F("due_date")),
                year_diff=ExtractYear(Value(today)) - ExtractYear(F("due_date")),
                # Manually calculate age_days
                age_days=Case(
                    When(due_date__isnull=True, then=Value(0)),
                    default=(
                        (ExtractYear(Value(today)) - ExtractYear(F("due_date"))) * 365
                        + (ExtractMonth(Value(today)) - ExtractMonth(F("due_date")))
                        * 30
                        + (ExtractDay(Value(today)) - ExtractDay(F("due_date")))
                    ),
                    output_field=IntegerField(),
                ),
                # Create properly formatted age string
                age=Concat(
                    Cast(
                        Case(
                            When(due_date__isnull=True, then=Value(0)),
                            default=(
                                (ExtractYear(Value(today)) - ExtractYear(F("due_date")))
                                * 365
                                + (
                                    ExtractMonth(Value(today))
                                    - ExtractMonth(F("due_date"))
                                )
                                * 30
                                + (ExtractDay(Value(today)) - ExtractDay(F("due_date")))
                            ),
                            output_field=IntegerField(),
                        ),
                        output_field=CharField(),
                    ),
                    Value(" Days"),
                    output_field=CharField(),
                ),
                amount=F("total")
                * Case(
                    When(exchange_rate__isnull=True, then=Value(1.0)),
                    default=F("exchange_rate"),
                    output_field=DecimalField(max_digits=15, decimal_places=2),
                ),
                balance_due=F("balance")
                * Case(
                    When(exchange_rate__isnull=True, then=Value(1.0)),
                    default=F("exchange_rate"),
                    output_field=DecimalField(max_digits=15, decimal_places=2),
                ),
            )
        )

        # Apply search filter if provided
        search_query = self.request.query_params.get("search", "")
        if search_query:
            queryset = queryset.filter(
                Q(customer_name__icontains=search_query)
                | Q(invoice_number__icontains=search_query)
            )

        # Apply ordering
        if sort_order.lower() == "desc":
            queryset = queryset.order_by(f"-{db_sort_field}")
        else:
            queryset = queryset.order_by(db_sort_field)

        return queryset

    def list(self, request, *args, **kwargs):
        if request.query_params.get("download") == "excel":
            return self.download_excel(request)

        queryset = self.filter_queryset(self.get_queryset())
        page = self.paginate_queryset(queryset)

        if page is not None:
            serializer = self.get_serializer(page, many=True)
            response = self.get_paginated_response(serializer.data)

            # Calculate totals for all values in the filtered queryset
            try:
                totals = {
                    "total_count": queryset.count(),
                    "total_amount": sum(
                        item.amount for item in queryset if item.amount is not None
                    ),
                    "total_balance_due": sum(
                        item.balance_due
                        for item in queryset
                        if item.balance_due is not None
                    ),
                }
            except Exception as e:
                # Fallback method if the above fails
                totals = {
                    "total_count": queryset.count(),
                    "total_amount": queryset.aggregate(Sum("amount"))["amount__sum"]
                    or 0,
                    "total_balance_due": queryset.aggregate(Sum("balance_due"))[
                        "balance_due__sum"
                    ]
                    or 0,
                }

            # Add the totals to the response
            response.data["totals"] = totals

            # Add bucket info to response
            response.data["bucket_info"] = {
                "bucket": request.query_params.get("age_bucket", "days_over_45")
            }

            return response

        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)

    def download_excel(self, request):
        """Generate and download Excel file with invoice aging data"""
        # Get filtered queryset
        queryset = self.filter_queryset(self.get_queryset())

        # Create a workbook and add a worksheet
        output = BytesIO()
        workbook = xlsxwriter.Workbook(output)
        worksheet = workbook.add_worksheet("Invoice Aging Detail")

        # Add styles
        header_format = workbook.add_format(
            {
                "bold": True,
                "bg_color": "#f0f0f0",
                "border": 1,
                "align": "center",
                "valign": "vcenter",
                "text_wrap": True,
            }
        )

        date_format = workbook.add_format({"num_format": "yyyy-mm-dd", "border": 1})

        number_format = workbook.add_format(
            {"num_format": "#,##0.00", "border": 1, "align": "right"}
        )

        text_format = workbook.add_format({"border": 1, "align": "left"})

        total_format = workbook.add_format(
            {
                "bold": True,
                "num_format": "#,##0.00",
                "border": 1,
                "align": "right",
                "bg_color": "#f0f0f0",
            }
        )

        # Define headers
        headers = [
            "Date",
            "Invoice Number",
            "Status",
            "Customer Name",
            "Age (Days)",
            "Amount",
            "Balance Due",
        ]

        # Write headers
        for col, header in enumerate(headers):
            worksheet.write(0, col, header, header_format)

        # Auto-fit columns
        worksheet.set_column(0, 0, 12)  # Date
        worksheet.set_column(1, 1, 18)  # Invoice Number
        worksheet.set_column(2, 2, 15)  # Status
        worksheet.set_column(3, 3, 30)  # Customer Name
        worksheet.set_column(4, 4, 10)  # Age
        worksheet.set_column(5, 5, 15)  # Amount
        worksheet.set_column(6, 6, 15)  # Balance Due

        # Write data rows
        row = 1
        for item in queryset:
            worksheet.write(row, 0, item.due_date, date_format)
            worksheet.write(row, 1, item.invoice_number, text_format)
            worksheet.write(row, 2, item.status, text_format)
            worksheet.write(row, 3, item.customer_name, text_format)
            worksheet.write(row, 4, item.age_days, number_format)
            worksheet.write(row, 5, float(item.amount or 0), number_format)
            worksheet.write(row, 6, float(item.balance_due or 0), number_format)
            row += 1

        # Write totals row
        total_row = row
        worksheet.write(total_row, 3, "TOTAL", total_format)

        # Calculate totals
        total_amount = sum(float(item.amount or 0) for item in queryset)
        total_balance_due = sum(float(item.balance_due or 0) for item in queryset)

        worksheet.write(total_row, 5, total_amount, total_format)
        worksheet.write(total_row, 6, total_balance_due, total_format)

        # Get current date for filename
        today_str = datetime.now().strftime("%Y-%m-%d")
        age_bucket = request.query_params.get("age_bucket", "days_over_45")

        # Close the workbook
        workbook.close()

        # Create response with the Excel file
        output.seek(0)
        response = HttpResponse(
            output.read(),
            content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        )

        # Set filename
        filename = f"Invoice_Aging_Detail_{age_bucket}_{today_str}.xlsx"
        response["Content-Disposition"] = f'attachment; filename="{filename}"'

        return response
