from rest_framework import serializers
from django.db import transaction
from .models import (
    InvoiceData,
    Vendor,
    InvoiceStatusUpdate,
    ZohoCustomer,
    ZohoVendor,
    SalesOrder,
    SalesOrderLineItem,
    PurchaseOrder,
    PurchaseOrderLineItem,
    Bill,
    BillLineItem,
    ClientInvoice,
    ClientInvoiceLineItem,
    Company,
    Deal,
    Contact,
    Entity,
    BankDetails,
    Payment,
    CreditNote,
)
from zohoapi.utils.common import (
    get_financial_year,
    get_invoice_data_for_pdf,
    update_invoice_status_and_balance,
)
from datetime import datetime
from api.utils.email import send_mail_templates_with_attachment
from django.template.loader import render_to_string
import requests
import pdfkit
import base64
from api.utils.constants import pdfkit_config
import json
from api.tasks import scheduled_send_mail_templates

# from zohoapi.views import get_po_quantity_invoices
import environ


env = environ.Env()


class BankDetailsSerializer(serializers.ModelSerializer):
    class Meta:
        model = BankDetails
        fields = "__all__"


class InvoiceDataSerializer(serializers.ModelSerializer):
    class Meta:
        model = InvoiceData
        fields = "__all__"


class BillSummarySerializer(serializers.ModelSerializer):
    class Meta:
        model = Bill
        fields = ["status", "currency_symbol", "bill_number", "exchange_rate"]


class InvoiceDataGetSerializer(serializers.ModelSerializer):
    bill = BillSummarySerializer(read_only=True)

    class Meta:
        model = InvoiceData
        fields = [
            "id",
            "vendor_id",
            "vendor_name",
            "vendor_email",
            "purchase_order_id",
            "purchase_order_no",
            "currency_code",
            "currency_symbol",
            "invoice_number",
            "created_at",
            "total",
            "exchange_rate",
            "invoice_date",
            "approver_email",
            "status",
            "attatched_invoice",
            "line_items",
            "entity",
            "bill",  # Added bill field
        ]


class InvoiceDataEditSerializer(serializers.ModelSerializer):
    class Meta:
        model = InvoiceData
        fields = [
            "invoice_number",
            "line_items",
            "customer_notes",
            "total",
            "invoice_date",
            "signature",
            "tin_number",
            "type_of_code",
            "iban",
            "swift_code",
            "attatched_invoice",
        ]


class VendorDepthOneSerializer(serializers.ModelSerializer):
    class Meta:
        model = Vendor
        fields = "__all__"
        depth = 1


class VendorSerializer(serializers.ModelSerializer):
    class Meta:
        model = Vendor
        fields = "__all__"

    def to_representation(self, instance):
        data = super().to_representation(instance)
        data["zoho_vendor"] = (
            ZohoVendorSerializer(instance.zoho_vendor).data
            if instance.zoho_vendor
            else None
        )
        return data


class InvoiceStatusUpdateGetSerializer(serializers.ModelSerializer):
    username = serializers.CharField(source="user.username", read_only=True)

    class Meta:
        model = InvoiceStatusUpdate
        fields = ["id", "status", "comment", "username", "created_at"]


class VendorEditSerializer(serializers.ModelSerializer):
    class Meta:
        model = Vendor
        fields = ["name", "phone", "is_upload_invoice_allowed", "is_msme"]


class LimitedVendorSerializer(serializers.ModelSerializer):
    class Meta:
        model = Vendor
        fields = ["name", "email"]  # Only include the necessary fields


class VendorFinancesSerializer(serializers.Serializer):
    id = serializers.IntegerField()
    vendor_id = serializers.CharField()
    vendor_name = serializers.CharField()
    po_amount = serializers.DecimalField(max_digits=10, decimal_places=2)
    invoiced_amount = serializers.DecimalField(max_digits=10, decimal_places=2)
    paid_amount = serializers.DecimalField(max_digits=10, decimal_places=2)
    pending_amount = serializers.DecimalField(max_digits=10, decimal_places=2)
    currency_symbol = serializers.CharField(allow_null=True)
    currency_code = serializers.CharField(allow_null=True)


class ProjectWiseFinanceSerializer(serializers.Serializer):
    id = serializers.IntegerField()
    project_name = serializers.CharField()
    po_amount = serializers.DecimalField(max_digits=10, decimal_places=2)
    invoiced_amount = serializers.DecimalField(max_digits=10, decimal_places=2)
    paid_amount = serializers.DecimalField(max_digits=10, decimal_places=2)
    currency_symbol = serializers.CharField()


class ZohoCustomerSerializer(serializers.ModelSerializer):
    is_so_available = serializers.SerializerMethodField()

    class Meta:
        model = ZohoCustomer
        fields = "__all__"

    def get_is_so_available(self, obj):
        return SalesOrder.objects.filter(zoho_customer=obj).exists()


class ZohoVendorSerializer(serializers.ModelSerializer):
    class Meta:
        model = ZohoVendor
        fields = "__all__"


class SalesOrderSerializer(serializers.ModelSerializer):
    class Meta:
        model = SalesOrder
        fields = "__all__"


class SalesOrderGetSerializer(serializers.ModelSerializer):
    cf_invoicing_type = serializers.SerializerMethodField()
    gm_sheet_number = serializers.SerializerMethodField()
    deal_name = serializers.SerializerMethodField()

    class Meta:
        model = SalesOrder
        fields = [
            "id",
            "cf_invoicing_type",
            "salesorder_id",
            "salesorder_number",
            "date",
            "status",
            "customer_name",
            "customer_id",
            "invoiced_status",
            "paid_status",
            "order_status",
            "total_quantity",
            "created_date",
            "sub_total",
            "total",
            "currency_code",
            "gm_sheet_number",
            "salesperson_name",
            "deal_name",
            "entity",
            "exchange_rate",
        ]

    def get_cf_invoicing_type(self, obj):
        # Implement logic to compute the first custom field value based on obj
        return obj.custom_field_hash.get("cf_invoicing_type", "")

    def get_deal_name(self, obj):
        # Implement logic to compute the first custom field value based on obj
        deal = Deal.objects.filter(sales_order__id=obj.id).first()
        if deal:
            return deal.deal_name
        else:
            return ""

    def get_gm_sheet_number(self, obj):
        # Implement logic to compute the first custom field value based on obj
        return obj.gm_sheet.gmsheet_number if obj.gm_sheet else None


class SalesOrderLineItemSerializer(serializers.ModelSerializer):

    class Meta:
        model = SalesOrderLineItem
        fields = "__all__"


class SalesOrderLineItemListSerializer(serializers.ModelSerializer):
    sales_order_id = serializers.SerializerMethodField()
    sales_order_number = serializers.SerializerMethodField()
    client_name = serializers.SerializerMethodField()
    project_type = serializers.SerializerMethodField()
    project_name = serializers.SerializerMethodField()
    total = serializers.SerializerMethodField()
    currency_symbol = serializers.SerializerMethodField()
    due_date = serializers.DateField(read_only=True)

    class Meta:
        model = SalesOrderLineItem
        fields = [
            "sales_order_id",
            "sales_order_number",
            "line_item_id",
            "client_name",
            "description",
            "due_date",
            "project_type",
            "project_name",
            "total",
            "currency_symbol",
        ]

    def get_sales_order_id(self, obj):
        sales_order = obj.salesorder_set.first()  # Get the first related SalesOrder
        return sales_order.salesorder_id if sales_order else None

    def get_sales_order_number(self, obj):
        sales_order = obj.salesorder_set.first()
        return sales_order.salesorder_number if sales_order else None

    def get_client_name(self, obj):
        sales_order = obj.salesorder_set.first()
        return (
            sales_order.zoho_customer.contact_name
            if sales_order and sales_order.zoho_customer
            else None
        )

    def get_currency_symbol(self, obj):
        sales_order = obj.salesorder_set.first()
        return sales_order.currency_symbol if sales_order else None

    def get_project_type(self, obj):
        sales_order = obj.salesorder_set.first()
        if sales_order:
            if sales_order.caas_project:
                return "Coaching"
            elif sales_order.schedular_project is not None:
                return "Skill Training"
        return None

    def get_project_name(self, obj):
        sales_order = obj.salesorder_set.first()
        if sales_order:
            if sales_order.caas_project:
                return sales_order.caas_project.name
            elif sales_order.schedular_project is not None:
                return sales_order.schedular_project.name
        return None

    def get_total(self, obj):
        return obj.item_total or 0.0


class V2SalesOrderLineItemSerializer(serializers.ModelSerializer):
    # Explicitly declare quantity and quantity_invoiced fields as IntegerField
    quantity = serializers.IntegerField()
    quantity_invoiced = serializers.IntegerField()
    tax_percentage = serializers.IntegerField()
    rate = serializers.DecimalField(
        max_digits=19, decimal_places=6, coerce_to_string=False
    )

    class Meta:
        model = SalesOrderLineItem
        fields = "__all__"


class PurchaseOrderSerializer(serializers.ModelSerializer):
    class Meta:
        model = PurchaseOrder
        fields = "__all__"

    def to_representation(self, instance):
        data = super().to_representation(instance)
        data["line_items"] = PurchaseOrderLineItemSerializer(
            instance.po_line_items, many=True
        ).data
        data["entity_details"] = EntitySerializer(instance.entity).data
        return data


class OPEPurchaseOrderSerializer(serializers.ModelSerializer):
    class Meta:
        model = PurchaseOrder
        fields = "__all__"

    def to_representation(self, instance):
        project_type = None
        project_id = None
        project_name = None

        if instance.caas_project:
            project_type = "caas"
            project_id = instance.caas_project.id
            project_name = instance.caas_project.name
        elif instance.schedular_project:
            project_type = "skill_training"
            project_id = instance.schedular_project.id
            project_name = instance.schedular_project.name

        # Get associated client invoice if it exists
        client_invoice = ClientInvoice.objects.filter(purchase_orders=instance).first()

        # Build the response data structure
        entry = {
            "id": instance.id,
            "purchaseorder_id": instance.purchaseorder_id,
            "purchase_order_number": instance.purchaseorder_number,
            "project": (
                {"type": project_type, "id": project_id, "name": project_name}
                if project_id
                else None
            ),
            "facilitator_name": instance.vendor_name if instance.vendor_name else None,
            "raised_amount": {
                "currency_symbol": instance.currency_symbol,
                "total": instance.total,
            },
            "po_status": instance.status,
            "client_invoice": None,
        }

        # Add client invoice details if it exists
        if client_invoice:
            entry["client_invoice"] = {
                "invoice_number": client_invoice.invoice_number,
                "total": client_invoice.total,
                "status": client_invoice.status,
                "currency_symbol": client_invoice.currency_symbol,
                "invoiced_date": client_invoice.date,
                "payment_date": client_invoice.last_payment_date,
            }

        entry["line_items"] = PurchaseOrderLineItemSerializer(
            instance.po_line_items, many=True
        ).data
        return entry


class PurchaseOrderGetSerializer(serializers.ModelSerializer):
    cf_invoice_approver_s_email = serializers.SerializerMethodField()
    sales_orders = serializers.SerializerMethodField()

    class Meta:
        model = PurchaseOrder
        fields = [
            "id",
            "cf_invoice_approver_s_email",
            "purchaseorder_id",
            "purchaseorder_number",
            "date",
            "created_time",
            "reference_number",
            "status",
            "billed_status",
            "vendor_name",
            "vendor_id",
            "currency_id",
            "currency_code",
            "currency_symbol",
            "exchange_rate",
            "total_quantity",
            "salesorder_id",
            "total",
            "tax_total",
            "po_type",
            "is_billed_to_client",
            "sales_orders",
        ]

    def get_cf_invoice_approver_s_email(self, obj):
        return obj.custom_field_hash.get("cf_invoice_approver_s_email", "")

    def get_sales_orders(self, obj):
        """
        Get related sales orders for the project
        """
        try:

            return []
            # return sales_orders
        except Exception as e:
            print(f"Error fetching related sales orders: {str(e)}")
            return []

    def to_representation(self, instance):
        data = super().to_representation(instance)
        data["entity_name"] = (
            "singapore"
            if instance.entity and instance.entity.id != int(env("INDIA_ENTITY_ID"))
            else "india"
        )
        return data


class PurchaseOrderLineItemSerializer(serializers.ModelSerializer):
    class Meta:
        model = PurchaseOrderLineItem
        fields = "__all__"


class BillSerializer(serializers.ModelSerializer):
    class Meta:
        model = Bill
        fields = "__all__"


class BillGetSerializer(serializers.ModelSerializer):
    cf_invoice = serializers.SerializerMethodField()

    class Meta:
        model = Bill
        fields = [
            "id",
            "cf_invoice",
            "bill_id",
            "bill_number",
            "vendor_name",
            "vendor_id",
            "status",
            "date",
            "reference_number",
            "currency_symbol",
            "currency_code",
        ]

    def get_cf_invoice(self, obj):
        # Implement logic to compute the first custom field value based on obj
        return obj.custom_field_hash.get("cf_invoice", "")


class BillLineItemSerializer(serializers.ModelSerializer):
    class Meta:
        model = BillLineItem
        fields = "__all__"


class ClientInvoiceSerializer(serializers.ModelSerializer):
    class Meta:
        model = ClientInvoice
        fields = "__all__"


class ClientInvoiceGetSerializer(serializers.ModelSerializer):
    cf_ctt_batch = serializers.SerializerMethodField()
    einvoice_status = serializers.SerializerMethodField()
    irn_no = serializers.SerializerMethodField()
    purchaseorder_id = serializers.CharField(
        source="purchase_order.purchaseorder_id", allow_null=True
    )

    class Meta:
        model = ClientInvoice
        fields = [
            "id",
            "invoice_id",
            "invoice_number",
            "date",
            "customer_name",
            "currency_symbol",
            "status",
            "total",
            "credits_applied",
            "balance",
            "payment_made",
            "salesorder_number",
            "salesperson_name",
            "salesperson_id",
            "created_date",
            "cf_ctt_batch",
            "einvoice_status",
            "irn_no",
            "bank_detail",
            "purchaseorder_id",
            "exchange_rate",
            "currency_code",
        ]

    def get_cf_ctt_batch(self, obj):
        # Implement logic to compute the first custom field value based on obj
        return (
            obj.custom_field_hash.get("cf_ctt_batch", "").split(", ") if obj else None
        )

    def get_einvoice_status(self, obj):
        if (
            obj
            and hasattr(obj, "einvoice_details")
            and isinstance(obj.einvoice_details, dict)
        ):
            return obj.einvoice_details.get("status", "")
        return None

    def get_irn_no(self, obj):
        if (
            obj
            and hasattr(obj, "einvoice_details")
            and isinstance(obj.einvoice_details, dict)
        ):
            return obj.einvoice_details.get("inv_ref_num", "")
        return None

    def to_representation(self, instance):
        data = super().to_representation(instance)
        data["entity"] = (
            instance.sales_order.entity.id
            if instance.sales_order and instance.sales_order.entity
            else None
        )
        return data


class ClientInvoiceLineItemSerializer(serializers.ModelSerializer):
    class Meta:
        model = ClientInvoiceLineItem
        fields = "__all__"


class V2ClientInvoiceLineItemSerializer(serializers.ModelSerializer):
    quantity = serializers.IntegerField()

    class Meta:
        model = ClientInvoiceLineItem
        fields = "__all__"


class V2InvoiceCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = InvoiceData
        fields = "__all__"

    def validate_invoice_number(self, value):
        request_data = self.context["request"].data
        invoice_date = datetime.strptime(
            request_data["invoice_date"], "%Y-%m-%d"
        ).date()
        start_year, end_year = get_financial_year(invoice_date)
        invoices = InvoiceData.objects.filter(
            vendor_id=request_data["vendor_id"],
            invoice_number=request_data["invoice_number"],
            invoice_date__range=(f"{start_year}-04-01", f"{end_year}-03-31"),
        )
        if invoices.exists():
            raise serializers.ValidationError("Invoice number should be unique.")
        return value

    def add_hsn_sac_to_vendor(self):
        vendor_id = self.context["request"].data.get("vendor_id", None)
        hsn_or_sac = self.context["request"].data.get("hsn_or_sac", None)
        if vendor_id and hsn_or_sac:
            vendor = Vendor.objects.get(vendor_id=vendor_id)
            vendor.name = self.validated_data["vendor_name"]
            vendor.phone = self.validated_data["phone"]
            vendor.save()

    def create(self, validated_data):
        self.add_hsn_sac_to_vendor()
        instance = super().create(validated_data)
        self.send_email_to_approver(instance)
        return instance

    def send_email_to_approver(self, invoice):
        approver_email = invoice.approver_email
        hsn_or_sac = None
        try:
            hsn_or_sac = Vendor.objects.get(vendor_id=invoice.vendor_id).hsn_or_sac
        except Exception as e:
            pass
        invoice_data = get_invoice_data_for_pdf(
            InvoiceDataSerializer(invoice).data, hsn_or_sac
        )
        scheduled_send_mail_templates.delay(
            "vendors/add_invoice.html",
            [
                (
                    approver_email
                    if env("ENVIRONMENT") == "PRODUCTION"
                    else "tech@meeraq.com"
                )
            ],
            f"Action Needed: Approval Required for Invoice - {invoice_data['vendor_name']}  + {invoice_data['invoice_number']}",
            {**invoice_data, "link": env("CAAS_APP_URL")},
            [],
        )


class V2InvoiceStatusUpdateSerializer(serializers.ModelSerializer):
    comment = serializers.CharField(write_only=True, required=False)

    class Meta:
        model = InvoiceData
        fields = [
            "status",
            "comment",
        ]

    def validate_status(self, value):
        if value not in ["rejected", "approved"]:
            raise serializers.ValidationError("Invalid status")
        return value

    def update(self, instance, validated_data):
        new_status = validated_data.get("status")
        comment = validated_data.get("comment", "")
        user = self.context["request"].user

        # Update the invoice status
        instance.status = new_status
        instance.save()

        # Create an approval record
        InvoiceStatusUpdate.objects.create(
            invoice=instance,
            status=new_status,
            comment=comment,
            user=user,
        )

        # Send the appropriate email
        self.send_updates(instance, new_status, comment, user)

        return instance

    def send_updates(self, invoice, new_status, comment, user):
        # Get vendor information
        vendor = Vendor.objects.get(vendor_id=invoice.vendor_id)
        invoice_data = get_invoice_data_for_pdf(
            InvoiceDataSerializer(invoice).data, vendor.hsn_or_sac
        )
        zoho_vendor = ZohoVendor.objects.get(contact_id=invoice.vendor_id)

        if new_status == "approved":
            email_body_message = render_to_string(
                "vendors/approve_invoice.html",
                {
                    **invoice_data,
                    "comment": comment,
                    "approved_by": user.username,
                    "entity_info": {
                        f"This payment will be processed through {zoho_vendor.entity.name}"
                    },
                },
            )
            send_mail_templates_with_attachment(
                "invoice_pdf.html",
                json.loads(env("FINANCE_EMAIL")),
                f"Meeraq | Invoice Approved - {invoice_data['purchase_order_no']} + {invoice_data['vendor_name']} ",
                {"invoice": invoice_data},
                email_body_message,
                [env("BCC_EMAIL")],
                vendor.is_upload_invoice_allowed,
            )
        else:
            send_mail_to = (
                invoice.vendor_email
                if env("ENVIRONMENT") == "PRODUCTION"
                else "tech@meeraq.com"
            )
            scheduled_send_mail_templates.delay(
                "vendors/reject_invoice.html",
                [send_mail_to],
                "Meeraq - Invoice Rejected",
                {"vendor_name": invoice.vendor_name, "comment": comment},
                [],
            )


class V2VendorDetailSerializer(serializers.ModelSerializer):
    user_data = serializers.SerializerMethodField()
    organization = serializers.SerializerMethodField()
    zoho_vendor = serializers.SerializerMethodField()

    class Meta:
        model = Vendor
        fields = ["vendor_id", "user_data", "organization", "zoho_vendor"]

    def get_user_data(self, obj):
        return VendorDepthOneSerializer(obj).data

    # def get_organization(self, obj):
    #     return get_organization_data()

    # def get_zoho_vendor(self, obj):
    #     user_data = self.get_user_data(obj)
    #     if user_data:
    #         return get_vendor(obj.vendor_id)
    #     return None


class V2InvoiceDataPDFSerializer(serializers.ModelSerializer):
    pdf = serializers.SerializerMethodField()

    class Meta:
        model = InvoiceData
        fields = ["id", "vendor_id", "invoice_number", "pdf"]

    def get_pdf(self, obj):
        vendor = Vendor.objects.get(vendor_id=obj.vendor_id)
        invoice_serializer_data = InvoiceDataSerializer(obj).data
        invoice_data = get_invoice_data_for_pdf(
            invoice_serializer_data, vendor.hsn_or_sac
        )
        image_base64 = self.get_image_base64(invoice_data.get("signature"))
        email_message = render_to_string(
            "invoice_pdf.html",
            {"invoice": invoice_data, "image_base64": image_base64},
        )
        pdf = pdfkit.from_string(email_message, False, configuration=pdfkit_config)
        return pdf

    def get_image_base64(self, image_url):
        try:
            image_response = requests.get(image_url)
            image_response.raise_for_status()
            return base64.b64encode(image_response.content).decode("utf-8")
        except Exception:
            return None


class V2PurchaseOrderAndInvoicesSerializer(serializers.Serializer):
    purchase_order = serializers.JSONField()
    invoices = InvoiceDataSerializer(many=True)


class EntitySerializer(serializers.ModelSerializer):
    class Meta:
        model = Entity
        fields = "__all__"


class CompanySerializer(serializers.ModelSerializer):
    class Meta:
        model = Company
        fields = "__all__"


class ContactSerializer(serializers.ModelSerializer):
    class Meta:
        model = Contact
        fields = "__all__"


class DealSerializer(serializers.ModelSerializer):
    class Meta:
        model = Deal
        fields = "__all__"


class DealSerializerDepthOne(serializers.ModelSerializer):
    class Meta:
        model = Deal
        fields = "__all__"
        depth = 1

    def to_representation(self, instance):
        data = super().to_representation(instance)
        company = Company.objects.filter(account_id=data["account_name"]["id"]).first()
        contact = Contact.objects.filter(contact_id=data["contact_name"]["id"]).first()
        data["company_id"] = company.id if company else None
        data["contact_id"] = contact.id if contact else None

        if not instance.deal_file:
            data.pop("deal_file", None)

        return data


class PaymentSerializer(serializers.ModelSerializer):
    customer_name = serializers.CharField(
        source="customer.contact_name", allow_null=True
    )
    invoice_number = serializers.CharField(
        source="client_invoice.invoice_number", allow_null=True
    )
    deposit_to_name = serializers.CharField(
        source="deposit_to.display_name", allow_null=True
    )
    debited_from_name = serializers.CharField(
        source="debited_from.display_name", allow_null=True
    )
    bill_number = serializers.CharField(source="bill.bill_number", allow_null=True)
    vendor_name = serializers.CharField(
        source="bill.zoho_vendor.contact_name", allow_null=True
    )

    class Meta:
        model = Payment
        fields = "__all__"


class PaymentCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Payment
        fields = "__all__"

    @transaction.atomic
    def create(self, validated_data):
        # Generate a unique payment number before saving
        last_payment = (
            Payment.objects.filter(type=validated_data["type"]).order_by("id").last()
        )
        if last_payment:
            last_number = int(last_payment.payment_number.split("PAY")[-1])
            new_number = last_number + 1
        else:
            new_number = 1
        validated_data["payment_number"] = (
            f"PAY{new_number:05d}"  # Format with zero-padding
        )

        payment = super().create(validated_data)
        if payment.type == "credit":
            self._update_related_invoice_and_sales_order(payment)
        elif payment.type == "debit":
            self._update_related_bill_and_purchase_order(payment)
        return payment

    @transaction.atomic
    def update(self, instance, validated_data):
        payment = super().update(instance, validated_data)
        if payment.type == "credit":
            self._update_related_invoice_and_sales_order(payment)
        elif payment.type == "debit":
            self._update_related_bill_and_purchase_order(payment)
        return payment

    def _update_related_bill_and_purchase_order(self, payment):
        bill = payment.bill
        # Update Invoice
        if bill:

            bill.status = "paid"  # Adjust to the appropriate status
            bill.billed_status = "paid"
            # for purchase_order in bill.purchase_orders.all():
            # quantiy_invocied_in_items = get_po_quantity_invoices(
            #     bill.bill_line_items.all()
            # )
            #     for line_item in purchase_order.po_line_items.all():
            #         if line_item.line_item_id in quantiy_invocied_in_items:

            #             if line_item.quantity_billed  == line_item.quantity
            #                 line_item.save()

            bill.save()

    def _update_related_invoice_and_sales_order(self, payment):
        invoice = payment.client_invoice
        # Update Invoice
        if invoice:
            payments_serialized_data = PaymentSerializer(
                Payment.objects.filter(client_invoice=invoice), many=True
            ).data
            invoice.status = "paid"  # Adjust to the appropriate status
            invoice.last_payment_date = (
                payment.date
            )  # Set to payment date or other relevant date field
            invoice.payment_made = payment.amount
            invoice.payments = payments_serialized_data
            invoice.save()
            invoice = update_invoice_status_and_balance(invoice)
            # Update Sales Order
            sales_order = invoice.sales_order
            if sales_order:
                sales_order.invoices = ClientInvoiceGetSerializer(
                    ClientInvoice.objects.filter(sales_order=sales_order), many=True
                ).data
                sales_order.save()


class FacilitatorMonthlyPOSerializer(serializers.Serializer):
    facilitator_name = serializers.CharField()
    jan = serializers.DecimalField(max_digits=12, decimal_places=2)
    feb = serializers.DecimalField(max_digits=12, decimal_places=2)
    mar = serializers.DecimalField(max_digits=12, decimal_places=2)
    apr = serializers.DecimalField(max_digits=12, decimal_places=2)
    may = serializers.DecimalField(max_digits=12, decimal_places=2)
    jun = serializers.DecimalField(max_digits=12, decimal_places=2)
    jul = serializers.DecimalField(max_digits=12, decimal_places=2)
    aug = serializers.DecimalField(max_digits=12, decimal_places=2)
    sep = serializers.DecimalField(max_digits=12, decimal_places=2)
    oct = serializers.DecimalField(max_digits=12, decimal_places=2)
    nov = serializers.DecimalField(max_digits=12, decimal_places=2)
    dec = serializers.DecimalField(max_digits=12, decimal_places=2)
    total = serializers.DecimalField(max_digits=12, decimal_places=2)
    percentage = serializers.DecimalField(max_digits=5, decimal_places=2)


class CreditNoteSerializer(serializers.ModelSerializer):
    customer_details = ZohoCustomerSerializer(source="customer", read_only=True)
    invoice_details = ClientInvoiceSerializer(source="client_invoice", read_only=True)

    class Meta:
        model = CreditNote
        fields = [
            "id",
            "brand",
            "customer",
            "customer_details",
            "credit_note_number",
            "client_invoice",
            "invoice_details",
            "currency_code",
            "amount",
            "terms_and_conditions",
            "customer_notes",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["created_at", "updated_at"]

    def to_representation(self, instance):
        data = super().to_representation(instance)

        data["currency_code"] = instance.client_invoice.currency_code
        data["invoice_id"] = instance.client_invoice.id

        return data


class V2BillSerializer(serializers.ModelSerializer):
    bill_line_items = BillLineItemSerializer(many=True, read_only=True)

    class Meta:
        model = Bill
        fields = "__all__"

    def create(self, validated_data):
        line_items_data = self.context.get("line_items", [])
        bill = Bill.objects.create(**validated_data)

        for item_data in line_items_data:
            line_item = BillLineItem.objects.create(**item_data)
            bill.bill_line_items.add(line_item)

        return bill

    def update(self, instance, validated_data):
        line_items_data = self.context.get("line_items", [])

        # Update Bill instance fields
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()

        # Update line items if provided
        if line_items_data:
            instance.bill_line_items.clear()
            for item_data in line_items_data:
                line_item = BillLineItem.objects.create(**item_data)
                instance.bill_line_items.add(line_item)

        return instance


class InvoiceAgingReportSerializer(serializers.Serializer):
    customer_name = serializers.CharField()
    current = serializers.DecimalField(max_digits=15, decimal_places=2)
    days_1_15 = serializers.DecimalField(max_digits=15, decimal_places=2)
    days_16_30 = serializers.DecimalField(max_digits=15, decimal_places=2)
    days_31_45 = serializers.DecimalField(max_digits=15, decimal_places=2)
    days_over_45 = serializers.DecimalField(max_digits=15, decimal_places=2)
    total = serializers.DecimalField(max_digits=15, decimal_places=2)


class InvoiceAgingDetailSerializer(serializers.ModelSerializer):
    age = serializers.CharField()
    age_days = serializers.IntegerField()
    balance_due = serializers.DecimalField(max_digits=15, decimal_places=2)
    amount = serializers.DecimalField(max_digits=15, decimal_places=2)

    class Meta:
        model = ClientInvoice
        fields = [
            "id",
            "due_date",
            "invoice_number",
            "status",
            "customer_name",
            "age_days",
            "age",
            "amount",
            "balance_due",
        ]
