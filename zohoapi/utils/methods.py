from datetime import datetime, timedelta, timezone,date
from ..serializers import (
    InvoiceDataSerializer,
    SalesOrderSerializer,
    InvoiceDataGetSerializer,
    PurchaseOrderSerializer,
    ZohoCustomerSerializer,
    ZohoVendorSerializer,
    SalesOrderLineItemSerializer,
    PurchaseOrderLineItemSerializer,
    ClientInvoiceSerializer,
    ClientInvoiceLineItemSerializer,
    BillSerializer,
    BillLineItemSerializer,
    PurchaseOrderGetSerializer,
)
from zohoapi.models import (
    Vendor,
    SalesOrder,
    PurchaseOrder,
    InvoiceData,
    Bill,
    ClientInvoice,
    AccessToken,
    ZohoCustomer,
    ZohoVendor,
    SalesOrderLineItem,
    PurchaseOrderLineItem,
    ClientInvoiceLineItem,
    BillLineItem,
    Deal,
    Company,
    Contact,
    Entity,
    GmSheet,
    Offering
)
from api.utils.methods import create_user_permission_for_role
from time import sleep
from rest_framework import status
import json
from django.utils import timezone
import environ
import os
import pdfkit
import requests
from decimal import Decimal
from typing import List, Dict
import re
from django.core.mail import EmailMessage
from operationsBackend import settings
import base64
from django.template.loader import render_to_string
from io import BytesIO
from api.models import  Profile, Role, User
from rest_framework.response import Response
from django.db.models import Q
from decimal import Decimal
from django.db.models.fields.related import ManyToManyField
from django.db import transaction
import random
import string
from api.models import Pmo
from api.serializers import get_exchange_rate

env = environ.Env()
wkhtmltopdf_path = os.environ.get(
    "WKHTMLTOPDF_PATH", r"C:\Program Files\wkhtmltopdf\bin\wkhtmltopdf.exe"
)
pdfkit_config = pdfkit.configuration(wkhtmltopdf=f"{wkhtmltopdf_path}")


def process_line_item_custom_fields(line_items):
    """
    Processes each line item to check for a 'Due Date' custom field, formats the date,
    and updates the item_custom_fields and custom_field_hash accordingly.

    Args:
        line_items (list): List of line items, where each line item is a dictionary.

    Returns:
        list: Updated list of line items with processed custom fields.
    """
    for line_item in line_items:
        # Check if 'item_custom_fields' exists and has elements
        updated_item_custom_fields = []
        custom_field_hash = {}
        if (
            "item_custom_fields" in line_item
            and len(line_item["item_custom_fields"]) > 0
        ):
            # Initialize an empty list to hold modified custom fields
            # Initialize custom field hash dictionary

            # Process each custom field in 'item_custom_fields'
            for current_custom_field in line_item["item_custom_fields"]:
                # Check if the label is "Due Date"
                if current_custom_field["label"] == "Due Date":
                    due_date_unformatted = current_custom_field["value"]

                    # Format the due date as dd/mm/yyyy
                    due_date_formatted = datetime.strptime(
                        due_date_unformatted, "%Y-%m-%d"
                    ).strftime("%d/%m/%Y")

                    # Add the formatted and unformatted dates to the hash
                    custom_field_hash["cf_due_date"] = due_date_formatted  # dd/mm/yyyy
                    custom_field_hash["cf_due_date_unformatted"] = (
                        due_date_unformatted  # yyyy-mm-dd
                    )

                    # Update the current custom field with the desired structure
                    updated_custom_field = {
                        "field_id": "2913550000002942017",
                        "customfield_id": "2913550000002942017",
                        "index": 1,
                        "label": "Due Date",
                        "api_name": "cf_due_date",
                        "data_type": "date",
                        "placeholder": "cf_due_date",
                        "value": due_date_unformatted,
                    }

                    # Append the updated custom field to the list
                    updated_item_custom_fields.append(updated_custom_field)
                else:
                    # If not "Due Date", just append the field as it is
                    updated_item_custom_fields.append(current_custom_field)

            # Attach the modified custom fields list and custom field hash to the line item
            line_item["item_custom_fields"] = updated_item_custom_fields
            line_item["custom_field_hash"] = custom_field_hash

    return line_items


def get_purchase_order_totals(line_items):
    total = 0
    sub_total = 0
    sub_total_inclusive_of_tax = 0
    tax_total = 0
    total_quantity = 0
    total_invoiced_quantity = 0
    print("runniing0")
    for line_item in line_items:
        print("runniing-1")
        # Accessing values from dictionary
        item_total = float(line_item.get("item_total", 0))
        item_sub_total = float(line_item.get("item_sub_total", 0))
        item_quantity = float(line_item.get("quantity", 0))
        quantity_invoiced = float(line_item.get("quantity_invoiced", 0))
        print("runniing1")
        # Calculate tax amount for the item
        item_tax = item_total - item_sub_total

        # Calculate sub_total inclusive of tax
        # item_sub_total_inclusive_of_tax = item_sub_total + item_tax
        print("runniing")
        # Aggregate totals
        total += item_total
        sub_total += item_sub_total
        # sub_total_inclusive_of_tax += item_sub_total_inclusive_of_tax
        # tax_total += item_tax
        total_quantity += item_quantity
        total_invoiced_quantity += quantity_invoiced

    # Round all monetary values to 2 decimal places
    return {
        "total": round(total, 2),
        "sub_total": round(sub_total, 2),
        "sub_total_inclusive_of_tax": round(sub_total_inclusive_of_tax, 2),
        "tax_total": round(tax_total, 2),
        "total_quantity": total_quantity,
        "total_invoiced_quantity": total_invoiced_quantity,
    }


def get_purchase_order_instance_totals(line_items):
    total = 0
    sub_total = 0
    sub_total_inclusive_of_tax = 0
    tax_total = 0
    total_quantity = 0
    total_invoiced_quantity = 0

    for line_item in line_items:
        # Accessing values from dictionary
        item_total = float(line_item.item_total or 0)
        # item_sub_total = float(line_item.item_sub_total or 0)
        item_quantity = float(line_item.quantity or 0)
        quantity_invoiced = float(line_item.quantity_billed or 0)

        # Calculate tax amount for the item
        # item_tax = item_total - item_sub_total

        # Calculate sub_total inclusive of tax
        # item_sub_total_inclusive_of_tax = item_sub_total + item_tax

        # Aggregate totals
        total += item_total
        # sub_total += item_sub_total
        # sub_total_inclusive_of_tax += item_sub_total_inclusive_of_tax
        # tax_total += item_tax
        total_quantity += item_quantity
        total_invoiced_quantity += quantity_invoiced

    # Round all monetary values to 2 decimal places
    return {
        "total": round(total, 2),
        "sub_total": round(sub_total, 2),
        "sub_total_inclusive_of_tax": round(sub_total_inclusive_of_tax, 2),
        "tax_total": round(tax_total, 2),
        "total_quantity": total_quantity,
        "total_invoiced_quantity": total_invoiced_quantity,
    }


def process_po_line_item_data(line_items_data, is_edit=False):
    try:
        for line_item in line_items_data:
            if not is_edit:
                line_item["line_item_id"] = random.randint(1000000, 999999999)
            line_item["item_total"] = line_item["item_sub_total"]
            line_item["quantity_cancelled"] = 0.0
            line_item["quantity_billed"] = 0.0
            line_item["discount"] = 0.0
        return line_items_data
    except Exception as e:
        print(str(e))
        return None


def create_custom_field_data(custom_fields):
    """
    Create custom_field_hash from request custom_fields

    Args:
        custom_fields (list): List of custom field dictionaries from request

    Returns:
        dict: Formatted custom_field_hash
    """
    custom_field_hash = {}

    # Convert the custom_fields list to custom_field_hash
    if custom_fields:
        for field in custom_fields:
            # Check if required keys exist
            if "api_name" in field and "value" in field:
                api_name = field["api_name"]
                value = field["value"]

                # Add to custom_field_hash
                custom_field_hash[api_name] = value

    return custom_field_hash


def get_line_items_details(invoices):
    res = {}
    for invoice in invoices:
        for line_item in invoice.line_items:
            if line_item["line_item_id"] in res:
                res[line_item["line_item_id"]] += line_item["quantity_input"]
            else:
                res[line_item["line_item_id"]] = line_item["quantity_input"]
    return res


def calculate_total_cost(items):
    return (
        sum(item["hours"] * item["coach"] * item["price"] for item in items)
        if items
        else 0
    )


def calculate_total_revenue(items):
    return (
        sum(item["hours"] * item["units"] * item["fees"] for item in items)
        if items
        else 0
    )


def fetch_sales_orders_of_project(project_id, project_type):
    try:
        if project_type in ["CAAS", "COD"]:
            project_filter = {"caas_project__id": project_id}
        else:
            project_filter = {"schedular_project__id": project_id}
        sales_orders = SalesOrder.objects.filter(**project_filter)
        return SalesOrderSerializer(sales_orders, many=True).data
    except Exception as e:
        print(str(e))
        return []


def fetch_purchase_orders_of_project(project_id, project_type, all_po_id):
    if project_type == "SEEQ":
        purchase_order_filter = Q(purchaseorder_id__in=all_po_id) | Q(
            schedular_project_id=project_id
        )
    else:
        purchase_order_filter = Q(purchaseorder_id__in=all_po_id) | Q(
            caas_project_id=project_id
        )

    return PurchaseOrder.objects.filter(purchase_order_filter).distinct()





def calculate_financials_data(
    sales_orders: List[Dict],
    purchase_orders: List[Dict],
    expense_po_ids: List[str] = [],
) -> Dict:
    total, invoiced_amount, not_invoiced_amount, paid_amount = (
        Decimal("0.0"),
        Decimal("0.0"),
        Decimal("0.0"),
        Decimal("0.0"),
    )
    currency_code, currency_symbol = None, None
    for sales_order in sales_orders:
        total += Decimal(sales_order["total"]) * Decimal(sales_order["exchange_rate"])
        if not currency_code:
            currency_code = sales_order["currency_code"]
            currency_symbol = sales_order["currency_symbol"]
        invoiced_amount += sum(
            Decimal(invoice["total"]) * Decimal(sales_order["exchange_rate"])
            for invoice in sales_order["invoices"]
        )
        not_invoiced_amount += (
            Decimal(sales_order["total"]) * Decimal(sales_order["exchange_rate"])
        ) - invoiced_amount
        paid_amount += sum(
            Decimal(invoice["total"]) * Decimal(sales_order["exchange_rate"])
            for invoice in sales_order["invoices"]
            if invoice["status"] == "paid"
        )

    purchase_order_cost, purchase_billed_amount, purchase_paid_amount = (
        Decimal("0.0"),
        Decimal("0.0"),
        Decimal("0.0"),
    )
    expense_order_cost, expense_billed_amount, expense_paid_amount = (
        Decimal("0.0"),
        Decimal("0.0"),
        Decimal("0.0"),
    )
    purchase_all_bills_paid = []
    for purchase_order in purchase_orders:
        purchase_order_cost += Decimal(str(purchase_order["total"])) * Decimal(
            purchase_order["exchange_rate"]
        )
        if purchase_order["purchaseorder_id"] in expense_po_ids:
            expense_order_cost += Decimal(str(purchase_order["total"])) * Decimal(
                purchase_order["exchange_rate"]
            )
        for bill in purchase_order["bills"]:
            purchase_billed_amount += Decimal(str(bill["total"])) * Decimal(
                purchase_order["exchange_rate"]
            )
            if purchase_order["purchaseorder_id"] in expense_po_ids:
                expense_billed_amount += Decimal(str(bill["total"])) * Decimal(
                    purchase_order["exchange_rate"]
                )

            if bill["status"] == "paid":
                purchase_paid_amount += Decimal(str(bill["total"])) * Decimal(
                    purchase_order["exchange_rate"]
                )
                purchase_all_bills_paid.append(True)
                if purchase_order["purchaseorder_id"] in expense_po_ids:
                    expense_paid_amount += Decimal(str(bill["total"])) * Decimal(
                        purchase_order["exchange_rate"]
                    )
            else:
                purchase_all_bills_paid.append(False)

    profit_percentage = (
        ((paid_amount - purchase_paid_amount) / paid_amount) * 100
        if paid_amount > 0
        else 0
    )

    return {
        "total": total,
        "invoiced_amount": invoiced_amount,
        "paid_amount": paid_amount,
        "currency_code": currency_code,
        "currency_symbol": currency_symbol,
        "purchase_order_cost": purchase_order_cost,
        "purchase_billed_amount": purchase_billed_amount,
        "purchase_paid_amount": purchase_paid_amount,
        "purchase_all_bills_paid": purchase_all_bills_paid,
        "profit_generated": (paid_amount - purchase_paid_amount),
        "profit_percentage": profit_percentage,
        "expense_order_cost": expense_order_cost,
        "expense_billed_amount": expense_billed_amount,
        "expense_paid_amount": expense_paid_amount,
    }


def get_purchase_order_ids_for_project(project_id, project_type):
    purchase_orders = []
    if project_type == "skill_training" or project_type == "SEEQ":
        purchase_orders = PurchaseOrder.objects.filter(
            schedular_project__id=project_id
        ).values_list("purchaseorder_id")
    elif project_type == "CAAS" or project_type == "COD":
        purchase_orders = PurchaseOrder.objects.filter(
            caas_project__id=project_id
        ).values_list("purchaseorder_id")
    purchase_order_ids = list(purchase_orders)
    return purchase_order_ids


def get_current_financial_year():
    today = datetime.today()
    current_year = today.year
    financial_year_start = datetime(
        current_year, 4, 1
    )  # Financial year starts from April 1st
    if today < financial_year_start:
        financial_year = str(current_year - 1)[2:] + "-" + str(current_year)[2:]
    else:
        financial_year = str(current_year)[2:] + "-" + str(current_year + 1)[2:]
    return financial_year


def generate_new_po_number(
    po_list, regex_to_match, production=True
):
    # pattern to match the purchase order number
    pattern = rf"^{regex_to_match}\d+$"
    # Filter out purchase orders with the desired format
    filtered_pos = [
        po for po in po_list if re.match(pattern, po["purchaseorder_number"])
    ]
    latest_number = 0
    # Finding the latest number for each year
    for po in filtered_pos:
        print(po["purchaseorder_number"].split("/"))
        if production:
            _, _, _, _, po_number = po["purchaseorder_number"].split("/")
            
        else:
            _, _, _, _, _, po_number = po["purchaseorder_number"].split("/")
            
        latest_number = max(latest_number, int(po_number))
    # Generating the new purchase order number
    new_number = latest_number + 1
    new_po_number = f"{regex_to_match}{str(new_number).zfill(4)}"
    return new_po_number


def generate_new_ctt_po_number(
    po_list, regex_to_match, production=True, is_india_entity=True
):
    # pattern to match the purchase order number
    pattern = rf"^{regex_to_match}\d+$"
    # Filter out purchase orders with the desired format
    filtered_pos = [
        po for po in po_list if re.match(pattern, po["purchaseorder_number"])
    ]
    latest_number = 0
    # Finding the latest number for each year
    for po in filtered_pos:
        print(po["purchaseorder_number"].split("/"))
        if production:
            if is_india_entity:
                _, _, _,  po_number = po["purchaseorder_number"].split("/")
            else:  
                _, _, _, _, po_number = po["purchaseorder_number"].split("/")
        else:
            if is_india_entity:
                _, _, _, _, po_number = po["purchaseorder_number"].split("/")
            else:
                _, _, _, _, _, po_number = po["purchaseorder_number"].split("/")
        latest_number = max(latest_number, int(po_number))
    # Generating the new purchase order number
    new_number = latest_number + 1
    new_po_number = f"{regex_to_match}{str(new_number).zfill(4)}"
    return new_po_number


def generate_new_so_number(so_list, regex_to_match, production, entity):
    # Pattern to match the sales order number based on entity
    pattern = rf"^{regex_to_match}\d+$"
    # Filter out sales orders with the desired format
    filtered_sos = [so for so in so_list if re.match(pattern, so["salesorder_number"])]
    latest_number = 0
    # Finding the latest number for each year
    for so in filtered_sos:
        if production:
            parts = so["salesorder_number"].split("/")
            so_number = parts[-1]
        else:
            parts = so["salesorder_number"].split("/")
            so_number = parts[-1]
        latest_number = max(latest_number, int(so_number))
    # Generate the new sales order number with leading zeroes
    new_number = latest_number + 1
    new_so_number = f"{regex_to_match}{str(new_number).zfill(4)}"
    return new_so_number


def generate_new_invoice_number(invoice_list):
    # Get the current year and month in YYMM format
    current_year_month = datetime.now().strftime("%y%m")
    # Filter the invoice list to only include those from the current month
    current_month_invoices = [
        inv for inv in invoice_list if inv["invoice_number"][:4] == current_year_month
    ]
    # If there are no invoices for the current month, start with 1
    if not current_month_invoices:
        return f"{current_year_month}0001"
    # Otherwise, find the maximum number and increment it by 1
    max_number = max(int(inv["invoice_number"][4:]) for inv in current_month_invoices)
    new_number = max_number + 1
    # Format the new number with leading zeroes
    formatted_new_number = str(new_number).zfill(4)
    return f"{current_year_month}{formatted_new_number}"


def get_current_month_start_and_end_date():
    # Get the current year and month
    current_year = datetime.now().year
    current_month = datetime.now().month

    # Calculate the first day of the current month
    first_day_of_month = datetime(current_year, current_month, 1)

    # Calculate the last day of the current month
    if current_month == 12:
        last_day_of_month = datetime(current_year + 1, 1, 1) - timedelta(days=1)
    else:
        last_day_of_month = datetime(current_year, current_month + 1, 1) - timedelta(
            days=1
        )

    # Format dates as strings in 'YYYY-MM-DD' format
    created_date_start = first_day_of_month.strftime("%Y-%m-%d")
    created_date_end = last_day_of_month.strftime("%Y-%m-%d")

    return created_date_start, created_date_end




def calculate_financials_from_orders(sales_orders, purchase_orders):
    financials = calculate_financials_data(sales_orders, purchase_orders)

    gm_sheets = GmSheet.objects.filter(
        salesorder__in=[sales_order["id"] for sales_order in sales_orders]
    ).distinct()
    expected_revenue, expected_cost = Decimal("0.0"), Decimal("0.0")
    expected_currency = None
    expected_profitability = Decimal("0.0")

    for gm_sheet in gm_sheets:
        expected_currency = gm_sheet.currency
        offering = Offering.objects.filter(is_won=True, gm_sheet=gm_sheet).first()
        if offering:
            expected_revenue += Decimal(
                calculate_total_revenue(offering.revenue_structure)
            )
            expected_cost += Decimal(calculate_total_cost(offering.cost_structure))
            expected_profitability = Decimal(offering.gross_margin)

    return {
        **financials,
        "expected_currency": expected_currency,
        "expected_cost": expected_cost,
        "expected_revenue": expected_revenue,
        "expected_profitability": expected_profitability,
    }







def filter_invoice_data(invoices):
    try:
        filtered_invoices = []
        for invoice in invoices:
          
            filtered_invoices.append(invoice)
        return filtered_invoices
    except Exception as e:
        print(str(e))
        return None

def fetch_invoices_db():
    # all_bills = BillGetSerializer(Bill.objects.all(), many=True).data
    invoices = InvoiceData.objects.all()
    # Use the serializer that includes the bill relationship
    invoice_serializer = InvoiceDataGetSerializer(invoices, many=True)
    # Return the serialized data - the bill relationship is already included by the serializer
    return invoice_serializer.data

def filter_purchase_order_data(purchase_orders):
    try:
        filtered_purchase_orders = []
        for order in purchase_orders:
            purchaseorder_number = order.get("purchaseorder_number", "").strip()
            created_time_str = order.get("created_time", "").strip()
            if created_time_str:
                created_time = datetime.strptime(
                    created_time_str, "%Y-%m-%dT%H:%M:%S%z"
                )
              
                filtered_purchase_orders.append(order)

        return filtered_purchase_orders
    except Exception as e:
        print(str(e))
        return None




def generate_access_token_from_refresh_token(refresh_token):
    token_url = env("ZOHO_TOKEN_URL")
    client_id = env("ZOHO_CLIENT_ID")
    client_secret = env("ZOHO_CLIENT_SECRET")
    # Payload for requesting access token
    token_payload = {
        "refresh_token": refresh_token,
        "client_id": client_id,
        "client_secret": client_secret,
        "redirect_uri": env("REDIRECT_URI"),
        "grant_type": "refresh_token",
    }
    token_response = requests.post(token_url, params=token_payload)

    token_data = token_response.json()
    if "access_token" in token_data:
        return token_data["access_token"]
    else:
        return None


def get_vendor_hsn_or_sac(vendor_id):
    vendor = Vendor.objects.filter(vendor_id=vendor_id).first()
    return vendor.hsn_or_sac if vendor else ""




def filter_objects_by_date(objects, days):
    current_date = datetime.now()
    start_date = current_date - timedelta(days=days)
    filtered_objects = [
        obj
        for obj in objects
        if datetime.strptime(obj["date"], "%Y-%m-%d") >= start_date
    ]
    return filtered_objects





def map_bill_to_invoice(bill_instance,invoice_number=None):
    try:
  
        invoice = InvoiceData.objects.get(invoice_number=invoice_number)
        invoice.bill = bill_instance
        invoice.save()
    except Exception as e:
        print(str(e))
        print(
            "error assigning invoice to bill",
            bill_instance,
        )



def fetch_and_filter_purchase_orders(vendor_id):
    try:
        vendor = ZohoVendor.objects.get(contact_id=vendor_id)

        purchase_orders = PurchaseOrder.objects.filter(zoho_vendor=vendor)
        return (
            PurchaseOrderSerializer(purchase_orders, many=True).data,
            status.HTTP_200_OK,
        )
    except Exception as e:
        print(str(e))
        return {"error": "Failed to load"}, status.HTTP_400_BAD_REQUEST


def fetch_and_process_invoices(vendor_id, purchase_order_id):
    try:
        filter_kwargs = (
            {"vendor_id": vendor_id}
            if purchase_order_id == "all"
            else {"purchase_order_id": purchase_order_id}
        )
        invoices = InvoiceData.objects.filter(**filter_kwargs).select_related('bill')
        invoices = filter_invoice_data(invoices)
        purchase_order_ids = [inv.purchase_order_id for inv in invoices]
        purchase_orders = {
            po.purchaseorder_id: po
            for po in PurchaseOrder.objects.filter(
                purchaseorder_id__in=purchase_order_ids
            ).select_related("entity")
        }
        vendor_hsn_sac = {
            vendor.vendor_id: vendor.hsn_or_sac
            for vendor in Vendor.objects.filter(
                vendor_id__in={inv.vendor_id for inv in invoices}
            )
        }
        invoice_res = []
        for invoice in invoices:
            invoice_data = InvoiceDataSerializer(invoice).data
            purchase_order = purchase_orders.get(invoice.purchase_order_id)
            if not purchase_order:
                continue
            if invoice.bill:
                matching_bill = BillSerializer(invoice.bill).data
            else:
                matching_bill = None
            hsn_or_sac = vendor_hsn_sac.get(invoice_data["vendor_id"], "")
            invoice_res.append(
                {**invoice_data, "bill": matching_bill, "hsn_or_sac": hsn_or_sac}
            )
        return invoice_res, status.HTTP_200_OK
    except Exception as e:
        print(str(e))
        # Add proper error logging here
        return [], status.HTTP_500_INTERNAL_SERVER_ERROR
    
def create_singapore_purchase_order(request, JSONString, entity):
    try:
        line_items_data = process_line_item_custom_fields(JSONString["line_items"])
        line_items_data = process_po_line_item_data(line_items_data)
        if "shipment_date" in JSONString and not JSONString["shipment_date"]:
            JSONString["shipment_date"] = None

        JSONString["discount"] = 0.0
        serializer = PurchaseOrderSerializer(data=JSONString)

        if serializer.is_valid():
            po_instance = serializer.save()
            vendor = ZohoVendor.objects.get(contact_id=po_instance.vendor_id)
            po_instance.zoho_vendor = vendor
            po_instance.save()
            po_instance.purchaseorder_id = f"BSC-{po_instance.id}"
            po_instance.created_time = datetime.now()
            po_instance.created_date = datetime.now().date()
            rate = get_exchange_rate(vendor.currency_code, "INR")
            po_instance.associated_contact_persons = [
                {
                    "contact_person_id": vendor.contact_id,
                    "contact_person_name": vendor.contact_name,
                    "first_name": vendor.first_name,
                    "last_name": vendor.last_name,
                    "contact_person_email": vendor.email,
                    "phone": vendor.phone,
                    "mobile": vendor.mobile,
                }
            ]
            po_instance.contact_persons = [vendor.contact_id]
            po_instance.vendor_name = vendor.contact_name
            po_instance.entity = entity
            po_instance.status = "draft"
            po_instance.vendor_name = vendor.contact_name
          
            line_item_totals = get_purchase_order_totals(line_items_data)
            po_instance.total = line_item_totals["total"]
            po_instance.sub_total = line_item_totals["sub_total"]
            po_instance.sub_total_inclusive_of_tax = line_item_totals[
                "sub_total_inclusive_of_tax"
            ]
            po_instance.tax_total = line_item_totals["tax_total"]
            po_instance.total_quantity = line_item_totals["total_quantity"]
            po_instance.current_sub_status = "draft"
       
            po_instance.created_time = datetime.now()
            po_instance.last_modified_time = datetime.now()
            po_instance.exchange_rate = rate
         
            po_instance.custom_field_hash = create_custom_field_data(
                po_instance.custom_fields
            )
            po_instance.save()

            for index, line_item in enumerate(line_items_data):
             
                line_item_serializer = PurchaseOrderLineItemSerializer(data=line_item)

                if line_item_serializer.is_valid():
                    instance = line_item_serializer.save()
                    po_instance.po_line_items.add(instance)
        
            return po_instance
        else:
            return None

    except Exception as e:
        print(str(e))
        return None


def create_purchase_order(request, update_kwargs=None):
    try:
        entity = None
        
        entity = (
            Entity.objects.get(request.data.get("entity"))
        )
        JSONString = json.loads(request.data.get("JSONString"))
        
        po_instance = create_singapore_purchase_order(request, JSONString, entity)
        if po_instance:
            if update_kwargs:
                for key, value in update_kwargs.items():
                    field = PurchaseOrder._meta.get_field(key)
                    if isinstance(field, ManyToManyField):
                        getattr(po_instance, key).set(value)
                    else:
                        setattr(po_instance, key, value)
                po_instance.save()
        if po_instance:
            return PurchaseOrderSerializer(po_instance).data, po_instance

        else:
            return None, None
    except Exception as e:
        print(str(e))
        return None, None


def create_payload_data(data):
    return {
        "contact_name": data.get("name", ""),
        "company_name": data.get("company_name", ""),
        "contact_type": "vendor",
        "currency_id": data.get("currency", ""),
        "payment_terms": 0,
        "payment_terms_label": "Due on Receipt",
        "credit_limit": 0,
        "billing_address": {
            "attention": data.get("attention", ""),
            "address": data.get("address", ""),
            "street2": "",
            "city": data.get("city", ""),
            "state": data.get("state", ""),
            "zip": data.get("zip_code", ""),
            "country": data.get("country", ""),
            "fax": "",
            "phone": "",
        },
        "shipping_address": {
            "attention": data.get("shipping_attention", ""),
            "address": data.get("shipping_address", ""),
            "street2": "",
            "city": data.get("shipping_city", ""),
            "state": data.get("shipping_state", ""),
            "zip": data.get("shipping_zip_code", ""),
            "country": data.get("shipping_country", ""),
            "fax": "",
            "phone": "",
        },
        "contact_persons": [
            {
                "first_name": data.get("first_name", ""),
                "last_name": data.get("last_name", ""),
                "mobile": data.get("phone", ""),
                "email": data.get("email", ""),
                "salutation": "",
                "is_primary_contact": True,
            }
        ],
        "default_templates": {},
        "custom_fields": [
            {"customfield_id": data.get("customfield_id", ""), "value": ""}
        ],
        "language_code": "en",
        "tags": [{"tag_id": data.get("tag_id", ""), "tag_option_id": ""}],
        "gst_no": data.get("gstn_uni", ""),
        "gst_treatment": data.get("gst_treatment", ""),
        "place_of_contact": data.get("place_of_contact", ""),
        "pan_no": data.get("pan", ""),
        "tds_tax_id": data.get("tds", ""),
        "bank_accounts": [],
        "documents": [],
    }




def get_revenue_data(start_date, end_date):
    try:
        if start_date:
            start_date = datetime.strptime(start_date, "%Y-%m-%d").date()
        if end_date:
            end_date = datetime.strptime(end_date, "%Y-%m-%d").date()

        filters = Q()
        if start_date and end_date:
            filters &= Q(created_date__range=[start_date, end_date])

        sales_orders = SalesOrder.objects.filter(filters).distinct()

        data = {}
        total = 0
        monthly_sales_order = {}

        for sales_order in sales_orders:
            so_date = sales_order.created_date.strftime("%m/%Y")
            monthly_sales_order[so_date] = monthly_sales_order.get(so_date, 0) + 1

            if so_date not in data:
                data[so_date] = {"total_amount": 0, "total_invoiced": 0}

            # Handle potential None values for total and exchange_rate
            so_total = sales_order.total or 0
            so_exchange_rate = sales_order.exchange_rate or 1  # Default to 1 if None
            
            order_amount = so_total * so_exchange_rate
            data[so_date]["total_amount"] += order_amount
            total += order_amount

            client_invoices = ClientInvoice.objects.filter(sales_order=sales_order)
            for client_invoice in client_invoices:
                ci_date = client_invoice.created_date.strftime("%m/%Y")
                if ci_date not in data:
                    data[ci_date] = {"total_amount": 0, "total_invoiced": 0}

                # Handle potential None values for client invoice
                ci_total = client_invoice.total or 0
                ci_exchange_rate = client_invoice.exchange_rate or 1  # Default to 1 if None
                
                data[ci_date]["total_invoiced"] += (ci_total * ci_exchange_rate)

        result = [
            {
                "month": month,
                "total_amount": round(values["total_amount"], 2),
                "total_invoiced": round(values["total_invoiced"], 2),
            }
            for month, values in data.items()
        ]

        monthly_sales_orders_total = [
            {
                "title": month,
                "total": value,
            }
            for month, value in monthly_sales_order.items()
        ]

        return {
            "result": result,
            "total": round(total, 2),
            "monthly_sales_orders_total": monthly_sales_orders_total,
        }

    except Exception as e:
        print(str(e))
        return {"error": "Failed to get data"}


def calculate_purchase_order_amounts(purchase_orders):
    """Calculate total amounts from purchase orders."""
    vendor_po_amounts = {}
    for po in purchase_orders:
        if po["status"] not in ["draft", "cancelled"]:
            vendor_id = po["vendor_id"]
            total_amount = Decimal(po["total"])
            if vendor_id in vendor_po_amounts:
                vendor_po_amounts[vendor_id] += total_amount
            else:
                vendor_po_amounts[vendor_id] = total_amount
    return vendor_po_amounts


def calculate_invoice_amounts(invoices):
    """Calculate invoiced and paid amounts."""
    vendor_invoice_amounts = {}
    for invoice in invoices:
        vendor_id = invoice["vendor_id"]
        invoiced_amount = Decimal(invoice["total"])
        paid_amount = (
            Decimal(invoice["total"])
            if invoice["bill"] and invoice["bill"]["status"] == "paid"
            else Decimal(0)
        )
        currency_symbol = (
            invoice["bill"]["currency_symbol"]
            if invoice["bill"]
            else invoice["currency_symbol"]
        )

        if vendor_id in vendor_invoice_amounts:
            vendor_invoice_amounts[vendor_id]["invoiced_amount"] += invoiced_amount
            vendor_invoice_amounts[vendor_id]["paid_amount"] += paid_amount
            vendor_invoice_amounts[vendor_id]["currency_symbol"] = (
                currency_symbol
                if not vendor_invoice_amounts[vendor_id]["currency_symbol"]
                else vendor_invoice_amounts[vendor_id]["currency_symbol"]
            )
        else:
            vendor_invoice_amounts[vendor_id] = {
                "invoiced_amount": invoiced_amount,
                "paid_amount": paid_amount,
                "currency_symbol": currency_symbol,
                "currency_code": invoice.get("currency_code", ""),
            }
    return vendor_invoice_amounts


def prepare_response(vendors, vendor_po_amounts, vendor_invoice_amounts):
    """Prepare the response data."""
    res = []
    for vendor in vendors:
        vendor_id = vendor.vendor_id
        res.append(
            {
                "id": vendor.id,
                "vendor_id": vendor_id,
                "vendor_name": vendor.name,
                "po_amount": round(vendor_po_amounts.get(vendor_id, Decimal(0)), 2),
                "invoiced_amount": round(
                    vendor_invoice_amounts.get(
                        vendor_id, {"invoiced_amount": Decimal(0)}
                    )["invoiced_amount"],
                    2,
                ),
                "paid_amount": round(
                    vendor_invoice_amounts.get(vendor_id, {"paid_amount": Decimal(0)})[
                        "paid_amount"
                    ],
                    2,
                ),
                "currency_symbol": (
                    vendor_invoice_amounts[vendor_id]["currency_symbol"]
                    if vendor_id in vendor_invoice_amounts
                    else None
                ),
                "currency_code": (
                    vendor_invoice_amounts[vendor_id]["currency_code"]
                    if vendor_id in vendor_invoice_amounts
                    else None
                ),
                "pending_amount": round(
                    vendor_invoice_amounts.get(
                        vendor_id, {"invoiced_amount": Decimal(0)}
                    )["invoiced_amount"]
                    - vendor_invoice_amounts.get(
                        vendor_id, {"paid_amount": Decimal(0)}
                    )["paid_amount"],
                    2,
                ),
            }
        )
    return res


def get_owner_details():
    return json.loads(env("ZOHO_OWNER"))


def get_access_token(refresh_token, bigin=False):
    try:
        access_token_object = AccessToken.objects.get(refresh_token=refresh_token)
        if not access_token_object.is_expired():
            return access_token_object.access_token
        else:
            new_access_token = generate_access_token_from_refresh_token(
                refresh_token, bigin
            )
            if new_access_token:
                access_token_object.access_token = new_access_token
                access_token_object.created_at = timezone.now()
                access_token_object.save()
            return new_access_token
    except:
        new_access_token = generate_access_token_from_refresh_token(
            refresh_token, bigin
        )
        if new_access_token:
            access_token_instance = AccessToken(
                access_token=new_access_token,
                refresh_token=refresh_token,
                expires_in=3600,
            )
            access_token_instance.save()
        return new_access_token


def zoho_api_request(method, endpoint, data=None, v1=False,params={}):
    """
    Make a request to the Zoho Bigin API.
    """

    access_token = get_access_token(env("ZOHO_API_BIGIN_REFRESH_TOKEN"), True)
    headers = {
        "Authorization": f"Zoho-oauthtoken {access_token}",
        "Content-Type": "application/json",
    }
    url = f"{ env('ZOHO_API_BIGIN_BASE_URL_V1') if v1 else env('ZOHO_API_BIGIN_BASE_URL')}{endpoint}"
    response = requests.request(method, url, headers=headers, json=data, params=params)
    # print(response.json())
    response.raise_for_status()
    return response.json()

def zoho_api_request_all(method, endpoint, data=None, v1=False, params=None, per_page=200):
    """
    Make a request to the Zoho Bigin API, automatically handling pagination
    to return all pages of results in a single list.

    :param method: The HTTP method (e.g., "GET", "POST").
    :param endpoint: The Zoho Bigin API endpoint (e.g. "Deals", "Deals/deleted").
    :param data: A dictionary of data to send with POST/PUT requests.
    :param v1: Whether to use the V1 base URL or the default base URL.
    :param params: Query parameters to include in the request.
    :param per_page: How many records to retrieve per page (max is often 200).
    :return: A list of all records across all pages.
    """
    if params is None:
        params = {}

    access_token = get_access_token(env("ZOHO_API_BIGIN_REFRESH_TOKEN"), True)
    headers = {
        "Authorization": f"Zoho-oauthtoken {access_token}",
        "Content-Type": "application/json",
    }
    base_url = env('ZOHO_API_BIGIN_BASE_URL_V1') if v1 else env('ZOHO_API_BIGIN_BASE_URL')

    all_records = []
    page = 1

    while True:
        # Merge the current `params` with the pagination params
        merged_params = {
            **params,
            "page": page,
            "per_page": per_page
        }

        url = f"{base_url}{endpoint}"
        response = requests.request(method, url, headers=headers, json=data, params=merged_params)
        response.raise_for_status()

        json_response = response.json()

        # Grab the data key, which should be a list
        data_chunk = json_response.get("data", [])
        all_records.extend(data_chunk)

        # Check pagination info
        info = json_response.get("info", {})
        more_records = info.get("more_records", False)

        if not more_records:
            # No more pages to fetch
            break

        page += 1

    return all_records


def create_or_update_contacts(zoho_id, request=None):
    try:
        # Fetch the contact data from Zoho
        response = zoho_api_request("GET", f"Contacts/{zoho_id}")
        zoho_data = response.get("data", [])[
            0
        ]  # Assuming response contains 'data' with a list of contacts

        # Check if the contact already exists in the local database
        contact = Contact.objects.filter(contact_id=zoho_id).first()

        # Define the owner, created_by, and modified_by fields
        owner_data = zoho_data.get("Owner")
        modified_by_data = zoho_data.get("Modified_By")
        created_by_data = zoho_data.get("Created_By")
        account_name_data = zoho_data.get("Account_Name")

        # Get last_activity_date safely whether request exists or not
        last_activity_date = None
        if request and hasattr(request, "data"):
            last_activity_date = request.data.get("Last_Activity_Date")

        # If the contact exists, update it; otherwise, create a new one
        if contact:
            # Update existing contact fields
            contact.first_name = zoho_data.get("First_Name", contact.first_name)
            contact.last_name = zoho_data.get("Last_Name", contact.last_name)
            contact.full_name = zoho_data.get("Full_Name", contact.full_name)
            contact.title = zoho_data.get("Title", contact.title)
            contact.email = zoho_data.get("Email", contact.email)
            contact.phone = zoho_data.get("Phone", contact.phone)
            contact.mobile = zoho_data.get("Mobile", contact.mobile)
            contact.home_phone = zoho_data.get("Home_Phone", contact.home_phone)
            contact.mailing_street = zoho_data.get(
                "Mailing_Street", contact.mailing_street
            )
            contact.mailing_city = zoho_data.get("Mailing_City", contact.mailing_city)
            contact.mailing_state = zoho_data.get(
                "Mailing_State", contact.mailing_state
            )
            contact.mailing_country = zoho_data.get(
                "Mailing_Country", contact.mailing_country
            )
            contact.mailing_zip = zoho_data.get("Mailing_Zip", contact.mailing_zip)
            contact.description = zoho_data.get("Description", contact.description)
            contact.currency_symbol = zoho_data.get(
                "$currency_symbol", contact.currency_symbol
            )
            contact.last_activity_time = zoho_data.get("Last_Activity_Time")
            contact.record_image = zoho_data.get("Record_Image")
            contact.locked_for_me = zoho_data.get(
                "$locked_for_me", contact.locked_for_me
            )
            contact.zia_visions = zoho_data.get("$zia_visions", contact.zia_visions)
            contact.modified_time = zoho_data.get(
                "Modified_Time", contact.modified_time
            )
            contact.created_time = zoho_data.get("Created_Time", contact.created_time)
            contact.followed = zoho_data.get("$followed", contact.followed)
            contact.editable = zoho_data.get("$editable", contact.editable)
            contact.zia_owner_assignment = zoho_data.get(
                "$zia_owner_assignment", contact.zia_owner_assignment
            )
            contact.approval_state = zoho_data.get(
                "$approval_state", contact.approval_state
            )
            contact.email_opt_out = zoho_data.get(
                "Email_Opt_Out", contact.email_opt_out
            )
            contact.unsubscribed_mode = zoho_data.get(
                "Unsubscribed_Mode", contact.unsubscribed_mode
            )
            contact.unsubscribed_time = zoho_data.get(
                "Unsubscribed_Time", contact.unsubscribed_time
            )
            contact.record_creation_source_id = zoho_data.get(
                "Record_Creation_Source_ID__s", contact.record_creation_source_id
            )
            contact.tags = zoho_data.get("Tag", contact.tags)
            contact.last_activity_date = (
                last_activity_date or contact.last_activity_date
            )
            # Update nested fields
            contact.owner = owner_data
            contact.modified_by = modified_by_data
            contact.created_by = created_by_data
            contact.account_name = account_name_data
            # Save the updated contact
            contact.save()
        else:
            # Create a new contact
            contact = Contact.objects.create(
                contact_id=zoho_id,
                first_name=zoho_data.get("First_Name"),
                last_name=zoho_data.get("Last_Name"),
                full_name=zoho_data.get("Full_Name"),
                title=zoho_data.get("Title"),
                email=zoho_data.get("Email"),
                phone=zoho_data.get("Phone"),
                mobile=zoho_data.get("Mobile"),
                home_phone=zoho_data.get("Home_Phone"),
                mailing_street=zoho_data.get("Mailing_Street"),
                mailing_city=zoho_data.get("Mailing_City"),
                mailing_state=zoho_data.get("Mailing_State"),
                mailing_country=zoho_data.get("Mailing_Country"),
                mailing_zip=zoho_data.get("Mailing_Zip"),
                description=zoho_data.get("Description"),
                currency_symbol=zoho_data.get("$currency_symbol", "Rs."),
                last_activity_time=zoho_data.get("Last_Activity_Time"),
                record_image=zoho_data.get("Record_Image"),
                locked_for_me=zoho_data.get("$locked_for_me", False),
                zia_visions=zoho_data.get("$zia_visions"),
                modified_time=zoho_data.get("Modified_Time"),
                created_time=zoho_data.get("Created_Time"),
                followed=zoho_data.get("$followed", False),
                editable=zoho_data.get("$editable", True),
                zia_owner_assignment=zoho_data.get(
                    "$zia_owner_assignment", "owner_recommendation_unavailable"
                ),
                approval_state=zoho_data.get("$approval_state", "approved"),
                email_opt_out=zoho_data.get("Email_Opt_Out", False),
                unsubscribed_mode=zoho_data.get("Unsubscribed_Mode"),
                unsubscribed_time=zoho_data.get("Unsubscribed_Time"),
                record_creation_source_id=zoho_data.get(
                    "Record_Creation_Source_ID__s", "0"
                ),
                tags=zoho_data.get("Tag", []),
                last_activity_date=last_activity_date,
                owner=owner_data,
                modified_by=modified_by_data,
                created_by=created_by_data,
                account_name=account_name_data,
            )

        print(
            f"Contact {'updated' if contact else 'created'} successfully in the local database."
        )
    except Exception as e:
        print(f"Error while creating or updating contact: {str(e)} {zoho_id}")


def create_or_update_company(zoho_id, request=None):
    try:
        # Fetch the company data from Zoho
        response = zoho_api_request("GET", f"Accounts/{zoho_id}")
        zoho_data = response.get("data", [])[
            0
        ]  # Assuming response contains 'data' with a list of companies

        # Check if the company already exists in the local database
        company = Company.objects.filter(account_id=zoho_id).first()

        # Define the owner, created_by, and modified_by fields
        owner_data = zoho_data.get("Owner")
        modified_by_data = zoho_data.get("Modified_By")
        created_by_data = zoho_data.get("Created_By")

        # If the company exists, update it; otherwise, create a new one
        if company:
            # Update existing company fields
            company.account_name = zoho_data.get("Account_Name", company.account_name)
            company.description = zoho_data.get("Description", company.description)
            company.currency_symbol = zoho_data.get(
                "$currency_symbol", company.currency_symbol
            )
            company.website = zoho_data.get("Website", company.website)
            company.phone = zoho_data.get("Phone", company.phone)
            company.billing_country = zoho_data.get(
                "Billing_Country", company.billing_country
            )
            company.billing_street = zoho_data.get(
                "Billing_Street", company.billing_street
            )
            company.billing_city = zoho_data.get("Billing_City", company.billing_city)
            company.billing_state = zoho_data.get(
                "Billing_State", company.billing_state
            )
            company.billing_code = zoho_data.get("Billing_Code", company.billing_code)
            company.last_activity_time = zoho_data.get("Last_Activity_Time")
            company.record_image = zoho_data.get("Record_Image")
            company.locked_for_me = zoho_data.get(
                "$locked_for_me", company.locked_for_me
            )
            company.zia_visions = zoho_data.get("$zia_visions", company.zia_visions)
            company.modified_time = zoho_data.get(
                "Modified_Time", company.modified_time
            )
            company.created_time = zoho_data.get("Created_Time", company.created_time)
            company.followed = zoho_data.get("$followed", company.followed)
            company.editable = zoho_data.get("$editable", company.editable)
            company.zia_owner_assignment = zoho_data.get(
                "$zia_owner_assignment", company.zia_owner_assignment
            )
            company.approval_state = zoho_data.get(
                "$approval_state", company.approval_state
            )
            company.tags = zoho_data.get("Tag", company.tags)
            company.employee_count = (
                request.data.get("Employee_Count", company.employee_count)
                if request
                else company.employee_count
            )
            company.industry = zoho_data.get("Industry", company.industry)
            company.revenue = (
                request.data.get("Revenue", company.revenue)
                if request
                else company.revenue
            )
            company.headquarters = (
                request.data.get("Headquarters", company.headquarters)
                if request
                else company.headquarters
            )
            # Update foreign keys
            company.owner = owner_data
            company.modified_by = modified_by_data
            company.created_by = created_by_data

            # Save the updated company
            company.save()

        else:
            # Create a new company
            company = Company.objects.create(
                account_id=zoho_id,
                account_name=zoho_data.get("Account_Name"),
                description=zoho_data.get("Description"),
                currency_symbol=zoho_data.get("$currency_symbol", "Rs."),
                website=zoho_data.get("Website"),
                phone=zoho_data.get("Phone"),
                billing_country=zoho_data.get("Billing_Country"),
                billing_street=zoho_data.get("Billing_Street"),
                billing_city=zoho_data.get("Billing_City"),
                billing_state=zoho_data.get("Billing_State"),
                billing_code=zoho_data.get("Billing_Code"),
                last_activity_time=zoho_data.get("Last_Activity_Time"),
                record_image=zoho_data.get("Record_Image"),
                locked_for_me=zoho_data.get("$locked_for_me", False),
                zia_visions=zoho_data.get("$zia_visions"),
                modified_time=zoho_data.get("Modified_Time"),
                created_time=zoho_data.get("Created_Time"),
                followed=zoho_data.get("$followed", False),
                editable=zoho_data.get("$editable", True),
                zia_owner_assignment=zoho_data.get(
                    "$zia_owner_assignment", "owner_recommendation_unavailable"
                ),
                approval_state=zoho_data.get("$approval_state", "approved"),
                tags=zoho_data.get("Tag", []),
                owner=owner_data,
                modified_by=modified_by_data,
                created_by=created_by_data,
                employee_count=zoho_data.get("Employee_Count"),
                industry=zoho_data.get("Industry"),
                revenue=zoho_data.get("Revenue"),
                headquarters=zoho_data.get("Headquarters"),
            )
        print(
            f"Company {'updated' if company else 'created'} successfully in the local database."
        )
    except Exception as e:
        print(f"Error while creating or updating company: {str(e)} {zoho_id}")


def create_or_update_deals(zoho_id):
    try:
        # Fetch the deal data from Zoho
        response = zoho_api_request("GET", f"Deals/{zoho_id}", None, True)
        zoho_data = response.get("data", [])[
            0
        ]  # Assuming response contains 'data' with a list of deals

        # Check if the deal already exists in the local database
        deal = Deal.objects.filter(deal_id=zoho_id).first()

        # Define nested fields
        owner_data = zoho_data.get("Owner")
        modified_by_data = zoho_data.get("Modified_By")
        account_name_data = zoho_data.get("Account_Name")
        contact_name_data = zoho_data.get("Contact_Name")
        layout_data = zoho_data.get("Layout")
        created_by_data = zoho_data.get("Created_By")

        # Update or create the deal
        if deal:
            # Update existing deal fields
            deal.deal_name = zoho_data.get("Deal_Name", deal.deal_name)
            deal.description = zoho_data.get("Description", deal.description)
            deal.closing_date = zoho_data.get("Closing_Date", deal.closing_date)
            deal.last_activity_time = zoho_data.get(
                "Last_Activity_Time", deal.last_activity_time
            )
            deal.stage = zoho_data.get("Stage", deal.stage)
            deal.amount = zoho_data.get("Amount", deal.amount)
            deal.pipeline = zoho_data.get("Pipeline", deal.pipeline)
            deal.currency_symbol = zoho_data.get(
                "$currency_symbol", deal.currency_symbol
            )
            deal.locked_for_me = zoho_data.get("$locked_for_me", deal.locked_for_me)
            deal.editable = zoho_data.get("$editable", deal.editable)
            deal.followed = zoho_data.get("$followed", deal.followed)
            deal.approval_state = zoho_data.get("$approval_state", deal.approval_state)
            deal.record_creation_source_id = zoho_data.get(
                "Record_Creation_Source_ID__s", deal.record_creation_source_id
            )
            deal.has_more_secondary_contacts = zoho_data.get("$has_more", {}).get(
                "Secondary_Contacts", deal.has_more_secondary_contacts
            )
            deal.modified_time = zoho_data.get("Modified_Time", deal.modified_time)
            deal.created_time = zoho_data.get("Created_Time", deal.created_time)
            deal.owner = owner_data
            deal.modified_by = modified_by_data
            deal.account_name = account_name_data
            deal.secondary_contacts = zoho_data.get(
                "Secondary_Contacts", deal.secondary_contacts
            )
            deal.associated_products = zoho_data.get(
                "Associated_Products", deal.associated_products
            )
            deal.contact_name = contact_name_data
            deal.layout = layout_data
            deal.created_by = created_by_data
            deal.tags = zoho_data.get("Tag", deal.tags)

            # Save the updated deal
            deal.save()

        else:
            # Create a new deal
            deal = Deal.objects.create(
                deal_id=zoho_id,
                deal_name=zoho_data.get("Deal_Name"),
                description=zoho_data.get("Description"),
                closing_date=zoho_data.get("Closing_Date"),
                last_activity_time=zoho_data.get("Last_Activity_Time"),
                stage=zoho_data.get("Stage"),
                amount=zoho_data.get("Amount"),
                pipeline=zoho_data.get("Pipeline"),
                currency_symbol=zoho_data.get("$currency_symbol", "Rs."),
                locked_for_me=zoho_data.get("$locked_for_me", False),
                editable=zoho_data.get("$editable", True),
                followed=zoho_data.get("$followed", False),
                approval_state=zoho_data.get("$approval_state", "approved"),
                record_creation_source_id=zoho_data.get(
                    "Record_Creation_Source_ID__s", "0"
                ),
                has_more_secondary_contacts=zoho_data.get("$has_more", {}).get(
                    "Secondary_Contacts", False
                ),
                modified_time=zoho_data.get("Modified_Time"),
                created_time=zoho_data.get("Created_Time"),
                owner=owner_data,
                modified_by=modified_by_data,
                account_name=account_name_data,
                secondary_contacts=zoho_data.get("Secondary_Contacts", []),
                associated_products=zoho_data.get("Associated_Products", []),
                contact_name=contact_name_data,
                layout=layout_data,
                created_by=created_by_data,
                tags=zoho_data.get("Tag", []),
            )

        print(
            f"Deal {'updated' if deal else 'created'} successfully in the local database."
        )
        return deal
    except Exception as e:
        print(f"Error while creating or updating deal: {str(e)} {zoho_id}")



def get_current_financial_year_dates():
    today = date.today()
    financial_year_start_month = 4  # Assuming financial year starts in April
    if today.month < financial_year_start_month:
        financial_year_start_year = today.year - 1
    else:
        financial_year_start_year = today.year
    financial_year_start_date = date(
        financial_year_start_year, financial_year_start_month, 1
    )
    financial_year_end_date = date(
        financial_year_start_year + 1, financial_year_start_month, 1
    ) - timedelta(days=1)
    # Format year as "yy-yy"
    formatted_start_year = financial_year_start_date.strftime("%y")
    formatted_end_year = financial_year_end_date.strftime("%y")
    return f"{formatted_start_year}-{formatted_end_year}"