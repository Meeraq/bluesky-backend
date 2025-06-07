from celery import shared_task
from .models import (
    Vendor,
    InvoiceData,
    ZohoCustomer,
    ZohoVendor,
    PurchaseOrder,
    SalesOrder,
    ClientInvoice,
    Bill,
    Contact,
    Company,
    Deal,
)
from .serializers import (
    InvoiceDataSerializer,
)

import pytz
from datetime import datetime, timedelta, timezone
import time
import requests
import environ
from time import sleep
from api.utils.email import send_mail_templates
from zohoapi.utils.methods import (
    get_access_token,
    filter_invoice_data,
    create_or_update_company,
    create_or_update_deals,
    create_or_update_contacts,
    zoho_api_request,
    zoho_api_request_all,
)
from zohoapi.utils.common import update_invoice_status_and_balance
import logging

logger = logging.getLogger(__name__)

env = environ.Env()




@shared_task
def weekly_invoice_approval_reminder():
    try:
        access_token_purchase_data = get_access_token(env("ZOHO_REFRESH_TOKEN"))
        if access_token_purchase_data:
            all_bills = Bill.objects.all()
            invoices = InvoiceData.objects.all()
            invoices = filter_invoice_data(invoices)
            invoice_serializer = InvoiceDataSerializer(invoices, many=True)
            all_invoices = []
            for invoice in invoice_serializer.data:
                matching_bill = next(
                    (
                        bill
                        for bill in all_bills
                        if (
                            bill.get(env("INVOICE_FIELD_NAME"))
                            == invoice["invoice_number"]
                            and bill.get("vendor_id") == invoice["vendor_id"]
                            and bill.get("date") == invoice["invoice_date"]
                        )
                    ),
                    None,
                )
                all_invoices.append({**invoice, "bill": matching_bill})
            invoices_in_review = []
            for invoice in all_invoices:
                if invoice["status"] == "in_review" and not invoice["bill"]:
                    datetime_obj = datetime.strptime(
                        invoice["created_at"], "%Y-%m-%dT%H:%M:%S.%fZ"
                    )
                    generated_date = datetime_obj.strftime("%d-%m-%Y")
                    invoices_in_review.append(
                        {**invoice, "generated_date": generated_date}
                    )
            if len(invoices_in_review) > 0:
                send_mail_templates(
                    "vendors/weekly_invoice_approval_reminder.html",
                    [
                        (
                            "pmocoaching@meeraq.com"
                            if env("ENVIRONMENT") == "PRODUCTION"
                            else "tech@meeraq.com"
                        )
                    ],
                    "Pending Invoices: Your Approval Needed",
                    {"invoices": invoices_in_review, "link": env("CAAS_APP_URL")},
                    [env("BCC_EMAIL_RAJAT_SUJATA")],
                )
    except Exception as e:
        print(str(e))
        pass


def filter_objects_by_date(objects, days):
    current_date = datetime.now()
    start_date = current_date - timedelta(days=days)
    filtered_objects = [
        obj
        for obj in objects
        if datetime.strptime(obj["date"], "%Y-%m-%d") >= start_date
    ]
    return filtered_objects



ACCOUNT_FIELDS = (
    "Account_Name,Description,$currency_symbol,Website,Phone,"
    "Billing_Country,Billing_Street,Billing_City,Billing_State,Billing_Code,"
    "Last_Activity_Time,Record_Image,$locked_for_me,$zia_visions,Modified_Time,"
    "Created_Time,$followed,$editable,$zia_owner_assignment,$approval_state,"
    "Owner,Modified_By,Created_By,Tag"
)

CONTACT_FIELDS = (
    "First_Name,Last_Name,Full_Name,Title,Email,Phone,Mobile,Home_Phone,"
    "Mailing_Street,Mailing_City,Mailing_State,Mailing_Country,Mailing_Zip,"
    "Description,$currency_symbol,Last_Activity_Time,Record_Image,$locked_for_me,"
    "$zia_visions,Modified_Time,Created_Time,$followed,$editable,"
    "$zia_owner_assignment,$approval_state,Email_Opt_Out,Unsubscribed_Mode,"
    "Unsubscribed_Time,Record_Creation_Source_ID__s,Owner,Modified_By,"
    "Created_By,Account_Name,Tag"
)

DEAL_FIELDS = (
    "Deal_Name,Description,Closing_Date,Last_Activity_Time,Stage,Amount,"
    "Pipeline,$currency_symbol,$locked_for_me,$editable,$followed,$approval_state,"
    "Record_Creation_Source_ID__s,Modified_Time,Created_Time,Owner,Modified_By,"
    "Account_Name,Secondary_Contacts,Associated_Products,Contact_Name,Layout,"
    "Created_By,Tag,$has_more"
)


@shared_task
def update_zoho_bigin_data():
    try:
        print("Starting Zoho Bigin data sync")
        start_time = time.time()
        # Initialize counters for logging
        stats = {
            "accounts_processed": 0,
            "contacts_processed": 0,
            "deals_processed": 0,
            "accounts_updated": 0,
            "contacts_updated": 0,
            "deals_updated": 0,
            "accounts_created": 0,
            "contacts_created": 0,
            "deals_created": 0,
            "errors": 0,
        }
        # Process Accounts/Companies
        page = 1
        per_page = 200  # Zoho's recommended batch size
        while True:
            try:
                print(page, "Accounts")
                accounts_response = zoho_api_request(
                    "GET",
                    f"Accounts?fields={ACCOUNT_FIELDS}&page={page}&per_page={per_page}",
                )
                if not accounts_response.get("data"):
                    break
                for account in accounts_response["data"]:
                    try:
                        company = Company.objects.filter(
                            account_id=account["id"]
                        ).first()
                        if company:
                            stats["accounts_updated"] += 1
                        else:
                            stats["accounts_created"] += 1
                        create_or_update_company(account["id"])
                        stats["accounts_processed"] += 1
                    except Exception as e:
                        print(f"Error processing account {account.get('id')}: {str(e)}")
                        stats["errors"] += 1
                if len(accounts_response["data"]) < per_page:
                    break
                page += 1
            except Exception as e:
                print(f"Error fetching accounts page {page}: {str(e)}")
                stats["errors"] += 1
                break
        # Process Contacts
        page = 1
        while True:
            try:
                print(page, "Contacts")
                contacts_response = zoho_api_request(
                    "GET",
                    f"Contacts?fields={CONTACT_FIELDS}&page={page}&per_page={per_page}",
                )
                if not contacts_response.get("data"):
                    break
                for contact in contacts_response["data"]:
                    try:
                        contact_obj = Contact.objects.filter(
                            contact_id=contact["id"]
                        ).first()
                        if contact_obj:
                            stats["contacts_updated"] += 1
                        else:
                            stats["contacts_created"] += 1
                        create_or_update_contacts(contact["id"])
                        stats["contacts_processed"] += 1
                    except Exception as e:
                        print(f"Error processing contact {contact.get('id')}: {str(e)}")
                        stats["errors"] += 1
                if len(contacts_response["data"]) < per_page:
                    break
                page += 1
            except Exception as e:
                print(f"Error fetching contacts page {page}: {str(e)}")
                stats["errors"] += 1
                break
        # Process Deals
        page = 1
        while True:
            try:
                print(page, "Deals")
                deals_response = zoho_api_request(
                    "GET",
                    f"Deals?fields={DEAL_FIELDS}&page={page}&per_page={per_page}",
                    None,
                    True,  # Using v1 API for deals
                )
                if not deals_response.get("data"):
                    break
                for deal in deals_response["data"]:
                    try:
                        deal_obj = Deal.objects.filter(deal_id=deal["id"]).first()
                        if deal_obj:
                            stats["deals_updated"] += 1
                        else:
                            stats["deals_created"] += 1
                        create_or_update_deals(deal["id"])
                        stats["deals_processed"] += 1

                    except Exception as e:
                        print(f"Error processing deal {deal.get('id')}: {str(e)}")
                        stats["errors"] += 1
                if len(deals_response["data"]) < per_page:
                    break
                page += 1
            except Exception as e:
                print(f"Error fetching deals page {page}: {str(e)}")
                stats["errors"] += 1
                break
        execution_time = time.time() - start_time
        print(
            f"Zoho Bigin sync completed in {execution_time:.2f} seconds\n"
            f"Accounts: {stats['accounts_processed']} processed "
            f"({stats['accounts_created']} created, {stats['accounts_updated']} updated)\n"
            f"Contacts: {stats['contacts_processed']} processed "
            f"({stats['contacts_created']} created, {stats['contacts_updated']} updated)\n"
            f"Deals: {stats['deals_processed']} processed "
            f"({stats['deals_created']} created, {stats['deals_updated']} updated)\n"
            f"Errors: {stats['errors']}"
        )
    except Exception as e:
        print(f"Fatal error in sync_zoho_bigin_data: {str(e)}")


@shared_task
def sync_deleted_records():
    """
    Fetches deleted records from Zoho CRM (or Bigin) for each module and
    marks matching local records as deleted.
    """
    modules_to_sync = [
        ("Accounts", Company, "account_id"),
        ("Contacts", Contact, "contact_id"),
        ("Pipelines", Deal, "deal_id"),
    ]

    # Ensure correct format: YYYY-MM-DDTHH:MM:SSZ

    for module_name, model_class, id_field in modules_to_sync:
        try:
            # *** Check your documentation for the correct param name ***
            # For example, Zoho CRM's param might be "last_modified_time"
            response = zoho_api_request_all(
                "GET",
                f"{module_name}/deleted",
                # params={"deleted_time": yesterday}  # or "since": ...
            )
        except Exception as e:
            print(f"Error fetching deleted {module_name}: {e}")
            continue

        data = response
        if not data:
            print(f"No deleted records for {module_name} in Zoho.")
            continue

        # Extract Zoho IDs from the response
        deleted_ids = [record.get("id") for record in data if "id" in record]
        print("No of Deleted Ids", len(deleted_ids))
        if not deleted_ids:
            print(f"No valid 'id' found in deleted records for {module_name}.")
            continue

        # Update local records that match these Zoho IDs
        filter_kwargs = {f"{id_field}__in": deleted_ids}
        deleted_count = model_class.objects.filter(**filter_kwargs).update(
            is_deleted=True
        )
        print(f"Marked {deleted_count} local {module_name} records as deleted.")


@shared_task
def update_client_invoice_status_and_amounts():
    """
    Scheduled task to update all invoice statuses and balances.
    This ensures that overdue statuses are updated even when no payment activity occurs.
    Returns:
    """ 
    # Get all invoices that aren't already marked as paid
    invoices = ClientInvoice.objects.exclude(status="paid").filter(due_date__lte=datetime.now())
    for invoice in invoices:
        try:
           
            update_invoice_status_and_balance(invoice)
           
        except Exception as e:
            logger.error(f"Error updating invoice {invoice.invoice_id}: {str(e)}")
            continue