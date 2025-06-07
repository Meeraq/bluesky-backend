from django.db import models
from django.utils import timezone
from api.models import (
    Profile,
    Employee,
    Sales,
    Organisation,
    Pmo,
    HR,
    validate_pdf_extension,
)
from django.contrib.auth.models import User
from datetime import datetime


class Entity(models.Model):
    name = models.TextField(blank=True)
    billing_address = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)


class BankDetails(models.Model):
    PAYMENT_NETWORK_CHOICES = [
        ("FAST", "FAST"),
        ("SWIFT", "SWIFT"),
    ]
    display_name = models.CharField(max_length=255, default="", null=True, blank=True)
    # Common fields
    account_holder = models.CharField(max_length=255)
    account_number = models.CharField(max_length=50)
    bank_name = models.CharField(max_length=255)
    bank_address = models.TextField()

    # Fields for Singapore-to-Singapore (FAST) payments
    payment_network = models.CharField(
        max_length=10, choices=PAYMENT_NETWORK_CHOICES, null=True, blank=True
    )
    bank_code = models.CharField(max_length=10, null=True, blank=True)

    # Fields for International (SWIFT) payments
    swift_bic = models.CharField(max_length=11, null=True, blank=True)

    def __str__(self):
        return f"{self.account_holder} - {self.bank_name} ({self.payment_network or 'International'})"



class Vendor(models.Model):
    user = models.OneToOneField(Profile, on_delete=models.CASCADE, blank=True)
    profile_pic = models.ImageField(upload_to="post_images", blank=True)
    name = models.CharField(max_length=155)
    phone = models.CharField(max_length=25)
    email = models.EmailField()
    vendor_id = models.CharField(max_length=255, blank=True, default="")
    hsn_or_sac = models.IntegerField(blank=True, default=0, null=True)
    is_upload_invoice_allowed = models.BooleanField(default=False)
    updated_at = models.DateTimeField(auto_now=True)
    active_inactive = models.BooleanField(default=True)
    is_msme = models.BooleanField(default=None, null=True, blank=True)

    def __str__(self):
        return self.name


class Assets(models.Model):
    STATUS_CHOICES = [
        ("idle", "Idle"),
        ("assigned", "Assigned"),
        ("lost", "Lost"),
        ("damaged", "Damaged"),
    ]
    asset_id = models.CharField(max_length=10, blank=True, null=True)
    name = models.CharField(max_length=255, default="", blank=True)
    category = models.CharField(max_length=255, default="", blank=True)
    assigned_to = models.ForeignKey(
        Employee, on_delete=models.SET_NULL, blank=True, null=True
    )
    update_at = models.DateTimeField(auto_now=True)
    description = models.TextField(blank=True, null=True, max_length=255)
    status = models.CharField(max_length=255, choices=STATUS_CHOICES, default="idle")
    updates = models.JSONField(default=list, blank=True)
    serial_number = models.CharField(max_length=255, default="", blank=True)
    asset_location = models.CharField(max_length=255, default="", blank=True)
    purchase_date = models.DateTimeField(null=True, blank=True)
    due_date = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)


class Benchmark(models.Model):
    year = models.CharField(max_length=9, default=str(datetime.now().year))
    project_type = models.JSONField(default=dict, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True) 


class GmSheet(models.Model):
    DEAL_STATUS_CHOICES = [
        ("pending", "Pending"),
        ("won", "Won"),
        ("lost", "Lost"),
        ("deferred", "Deferred"),
    ]
    client_name = models.TextField(blank=True, null=True)
    project_type = models.CharField(max_length=255, blank=True, null=True)
    product_type = models.CharField(max_length=255, blank=True, null=True, default="")
    currency = models.CharField(max_length=255, blank=True, null=True)
    project_name = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    gmsheet_number = models.CharField(max_length=20, blank=True, null=True)
    other_details = models.TextField(blank=True, null=True)
    sales = models.ForeignKey(Sales, null=True, on_delete=models.SET_NULL)
    is_accepted = models.BooleanField(default=False)
    deal_status = models.CharField(
        max_length=255, choices=DEAL_STATUS_CHOICES, default="pending"
    )
    benchmark = models.ForeignKey(Benchmark, null=True, on_delete=models.SET_NULL)
    participant_level = models.CharField(max_length=255, blank=True, null=True)
    start_date = models.DateField(null=True, blank=True)
    rate_card = models.BooleanField(default=False)
    added_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)

    def _str_(self):
        return f"{self.client_name} for {self.product_type}"


class Offering(models.Model):
    MODE_CHOICES = [
        ("in_person", "In Person"),
        ("virtual", "Virtual"),
        ("hybrid", "Hybrid"),
    ]
    gm_sheet = models.ForeignKey(GmSheet, on_delete=models.CASCADE)
    mode = models.CharField(
        max_length=100, choices=MODE_CHOICES, blank=True, null=True, default=""
    )
    revenue_structure = models.JSONField(default=list, blank=True, null=True)
    cost_structure = models.JSONField(default=list, blank=True, null=True)
    gross_margin = models.CharField(max_length=100, blank=True, null=True)
    is_won = models.BooleanField(default=False)
    total_profit = models.CharField(max_length=100, blank=True, null=True)


class HandoverDetails(models.Model):

    DELIVERY_MODE_CHOICES = [
        ("online", "Online"),
        ("hybrid", "Hybrid"),
        ("offline", "Offline"),
    ]

    INVOICE_STATUS_CHOICES = [
        ("yes", "Yes"),
        ("no", "No"),
        ("billed", "Billed"),
        ("partially_billed", "Partially Billed"),
    ]
    sales = models.ForeignKey(Sales, on_delete=models.SET_NULL, blank=True, null=True)
    organisation = models.ForeignKey(Organisation, null=True, on_delete=models.SET_NULL)
    pmo = models.ForeignKey(Pmo, null=True, on_delete=models.SET_NULL)
    hr = models.ManyToManyField(HR, blank=True)
    delivery_mode = models.CharField(
        max_length=255, choices=DELIVERY_MODE_CHOICES, blank=True, null=True
    )
    project_duration = models.CharField(max_length=255, blank=True, null=True)
    po_number = models.CharField(max_length=255, blank=True, null=True)
    participant_count = models.IntegerField(default=0, blank=True, null=True)
    coach_fee = models.CharField(max_length=255, blank=True, null=True)
    invoice_status = models.CharField(
        max_length=255, choices=INVOICE_STATUS_CHOICES, blank=True, null=True
    )
    reporting_requirements = models.TextField(blank=True, null=True)
    coach_names = models.TextField(blank=True, null=True)
    poc_contact_details = models.TextField(blank=True, null=True)
    audience_level = models.JSONField(max_length=255, blank=True, null=True)
    project_structure = models.JSONField(default=list, blank=True, null=True)
    sales_order_ids = models.JSONField(default=list, blank=True, null=True)
    # sales_order_nos = models.JSONField(default=list, blank=True, null=True)
    total_coaching_hours = models.DecimalField(
        max_digits=12, decimal_places=2, default=0, blank=True, null=True
    )
    tentative_start_date = models.DateField(blank=True, null=True)
    pre_assessment = models.BooleanField(blank=True, default=True)
    post_assessment = models.BooleanField(blank=True, default=True)
    nudges = models.BooleanField(blank=True, default=True)
    end_of_program_certification = models.BooleanField(default=False, blank=True)
    out_of_pocket_expenses = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    project_name = models.CharField(max_length=255, blank=True, null=True)
    is_accepted = models.BooleanField(default=False, blank=True)
    is_drafted = models.BooleanField(default=False, blank=True)
    gm_sheet = models.FileField(upload_to="gm_sheets/", blank=True, null=True)
    proposals = models.FileField(upload_to="proposals/", blank=True, null=True)
    nudge_details = models.TextField(blank=True, null=True)
    billing_instructions = models.TextField(blank=True, null=True)
    course_name = models.TextField(blank=True, null=True)
    details_of_delivery = models.TextField(blank=True, null=True)
    pre_post_assessment_details = models.TextField(blank=True, null=True)
    other_feedback = models.TextField(blank=True, null=True)
    assessment_details = models.TextField(blank=True, null=True)
    session_details = models.TextField(blank=True, null=True)
    problem_statement = models.TextField(blank=True, null=True)
    location = models.TextField(blank=True, null=True)
    program_duration = models.TextField(blank=True, null=True)
    major_language = models.TextField(blank=True, null=True)
    background = models.TextField(blank=True, null=True)
    batch_size = models.IntegerField(default=0, blank=True, null=True)
    number_of_batches = models.IntegerField(default=0, blank=True, null=True)
    reading_material = models.BooleanField(default=False, blank=True)
    stickon = models.BooleanField(default=False, blank=True)
    ready_recknor = models.BooleanField(default=False, blank=True)
    workbook_requirement = models.BooleanField(default=False, blank=True)
    certificates = models.BooleanField(default=False, blank=True)
    client_feedback_forms = models.BooleanField(default=False, blank=True)
    design_walkthrough = models.BooleanField(default=False, blank=True)
    is_rate_for_coaches = models.BooleanField(default=False, blank=True)
    rate_for_coaches = models.TextField(blank=True, null=True)
    is_cost_for_support_staff = models.BooleanField(default=False, blank=True)
    cost_for_support_staff = models.TextField(blank=True, null=True)
    is_cost_for_games = models.BooleanField(default=False, blank=True)
    cost_for_games = models.TextField(blank=True, null=True)
    is_design_cost = models.BooleanField(default=False, blank=True)
    design_cost = models.TextField(blank=True, null=True)
    payment_terms = models.TextField(blank=True, null=True)
    cost_of_checkins = models.TextField(blank=True, null=True)
    pre_assessment_competencies = models.TextField(blank=True, null=True)
    post_assessment_competencies = models.TextField(blank=True, null=True)
    program_details = models.TextField(blank=True, null=True)
    added_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)

    class Meta:
        verbose_name = "Handover Detail"
        verbose_name_plural = "Handover Details"

class InvoiceData(models.Model):
    INVOICE_STATUS_CHOICES = (
        ("in_review", "In Review"),
        ("approved", "Approved"),
        ("rejected", "Rejected"),
    )
    bill = models.ForeignKey("Bill", on_delete=models.SET_NULL, default=None, blank=True, null=True)
    type_of_code_choices = [("IBAN", "iban"), ("SWIFT_CODE", "swift_code")]
    vendor_id = models.CharField(max_length=200, default=None)
    vendor_name = models.CharField(max_length=200, default=None, blank=True)
    vendor_email = models.CharField(max_length=200, default=None, blank=True)
    vendor_billing_address = models.TextField(default=None, blank=True)
    vendor_gst = models.CharField(max_length=200, default=None, blank=True)
    vendor_pan = models.CharField(max_length=255, default="", blank=True)
    vendor_phone = models.CharField(max_length=200, default=None, blank=True)
    purchase_order_id = models.CharField(max_length=200, default=None)
    purchase_order_no = models.CharField(max_length=200, default=None)
    currency_code = models.CharField(max_length=255, default="", blank=True)
    currency_symbol = models.CharField(max_length=255, default="", blank=True)
    invoice_number = models.CharField(max_length=200, default=None)
    line_items = models.JSONField(default=list)
    customer_name = models.CharField(max_length=200, default=None, blank=True)
    customer_notes = models.TextField(blank=True, default=None)
    customer_gst = models.CharField(max_length=200, default=None, blank=True)
    customer_address = models.TextField(default=None, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    total = models.DecimalField(default=0, decimal_places=2, max_digits=20)
    exchange_rate = models.DecimalField(
        max_digits=15, decimal_places=6, null=True, blank=True
    )
    purchase_order_reference = models.ForeignKey(
        "PurchaseOrder", on_delete=models.SET_NULL, default=None, blank=True, null=True
    )
    adjustment = models.DecimalField(default=0, decimal_places=2, max_digits=20, blank=True)
    adjustment_description = models.CharField(max_length=255, default="", blank=True)
    is_oversea_account = models.BooleanField(default=False)
    tin_number = models.CharField(max_length=255, default="", blank=True)
    type_of_code = models.CharField(max_length=50, default="", blank=True)
    iban = models.CharField(max_length=255, default="", blank=True)
    swift_code = models.CharField(max_length=255, default="", blank=True)
    invoice_date = models.DateField(blank=True, default=None)
    beneficiary_name = models.CharField(max_length=255, default="")
    bank_name = models.CharField(max_length=255, default="")
    account_number = models.CharField(max_length=255, default="")
    ifsc_code = models.CharField(max_length=11, default="")
    signature = models.ImageField(upload_to="vendors-signature", default="", blank=True)
    attatched_invoice = models.FileField(
        upload_to="pdf_files",
        blank=True,
        default="",
        validators=[validate_pdf_extension],
    )
    status = models.CharField(
        max_length=50, choices=INVOICE_STATUS_CHOICES, default="in_review"
    )
    approver_email = models.EmailField(default="", blank=True)
    tax_names = models.JSONField(default=list, blank=True)
    entity = models.ForeignKey(
        "Entity",
        null=True,
        on_delete=models.SET_NULL,
    )

    def __str__(self):
        return f"{self.invoice_number}"

    class Meta:
        ordering = ["-created_at"]


class AccessToken(models.Model):
    refresh_token = models.CharField(max_length=255, unique=True, null=True)
    access_token = models.CharField(max_length=255)
    expires_in = models.IntegerField()  # Store the expiration time in seconds
    created_at = models.DateTimeField(auto_now_add=True)

    def is_expired(self):
        return timezone.now() >= self.created_at + timezone.timedelta(
            seconds=self.expires_in
        )

    def __str__(self):
        return self.access_token


class PoReminder(models.Model):
    vendor = models.ForeignKey(Vendor, on_delete=models.CASCADE)
    purchase_order_id = models.CharField(max_length=200, default=None)
    purchase_order_no = models.CharField(max_length=200, default=None)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.vendor.name} for {self.purchase_order_no}"


class InvoiceStatusUpdate(models.Model):
    invoice = models.ForeignKey(
        InvoiceData, related_name="approvals", on_delete=models.CASCADE
    )
    status = models.CharField(
        max_length=50, choices=InvoiceData.INVOICE_STATUS_CHOICES, default="in_review"
    )
    comment = models.TextField(blank=True)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.invoice.invoice_number} - {self.status} by {self.user.username}"



class LineItems(models.Model):
    sales_order_id = models.CharField(max_length=200, default=None)
    sales_order_number = models.CharField(max_length=200, default=None)
    line_item_id = models.CharField(max_length=200, default=None)
    client_name = models.CharField(max_length=200, default=None, blank=True)
    line_item_description = models.TextField(default=None, blank=True)
    due_date = models.DateField(blank=True, default=None)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)




class ZohoCustomer(models.Model):
    contact_id = models.CharField(max_length=50, blank=True, null=True)
    contact_name = models.CharField(max_length=255, blank=True, null=True)
    company_name = models.CharField(max_length=255, blank=True, null=True)
    first_name = models.CharField(max_length=255, blank=True, null=True)
    last_name = models.CharField(max_length=255, blank=True, null=True)
    designation = models.CharField(max_length=255, blank=True, null=True)
    department = models.CharField(max_length=255, blank=True, null=True)
    website = models.CharField(max_length=255, blank=True, null=True)
    is_bcy_only_contact = models.BooleanField(default=False)
    is_credit_limit_migration_completed = models.BooleanField(default=False)
    language_code = models.CharField(max_length=10, blank=True, null=True)
    language_code_formatted = models.CharField(max_length=255, blank=True, null=True)
    contact_salutation = models.CharField(max_length=255, blank=True, null=True)
    email = models.EmailField(blank=True, null=True)
    phone = models.CharField(max_length=20, blank=True, null=True)
    mobile = models.CharField(max_length=20, blank=True, null=True)
    invited_by = models.CharField(max_length=255, blank=True, null=True)
    portal_status = models.CharField(max_length=20, blank=True, null=True)
    portal_status_formatted = models.CharField(max_length=255, blank=True, null=True)
    is_client_review_asked = models.BooleanField(default=False)
    has_transaction = models.BooleanField(default=False)
    contact_type = models.CharField(max_length=50, blank=True, null=True)
    customer_sub_type = models.CharField(max_length=50, blank=True, null=True)
    customer_sub_type_formatted = models.CharField(
        max_length=255, blank=True, null=True
    )
    owner_id = models.CharField(max_length=50, blank=True, null=True)
    owner_name = models.CharField(max_length=255, blank=True, null=True)
    source = models.CharField(max_length=50, blank=True, null=True)
    source_formatted = models.CharField(max_length=255, blank=True, null=True)
    documents = models.JSONField(blank=True, null=True)
    twitter = models.CharField(max_length=255, blank=True, null=True)
    facebook = models.CharField(max_length=255, blank=True, null=True)
    zoho_customer = models.BooleanField(default=False)
    is_linked_with_zohocrm = models.BooleanField(default=False)
    primary_contact_id = models.CharField(max_length=50, blank=True, null=True)
    zcrm_account_id = models.CharField(max_length=50, blank=True, null=True)
    zcrm_contact_id = models.CharField(max_length=50, blank=True, null=True)
    crm_owner_id = models.CharField(max_length=50, blank=True, null=True)
    payment_terms = models.IntegerField(default=0)
    payment_terms_label = models.CharField(max_length=255, blank=True, null=True)
    credit_limit_exceeded_amount = models.DecimalField(
        max_digits=15, decimal_places=2, default=0, blank=True, null=True
    )
    currency_id = models.CharField(max_length=50, blank=True, null=True)
    currency_code = models.CharField(max_length=10, blank=True, null=True)
    currency_symbol = models.CharField(max_length=10, blank=True, null=True)
    price_precision = models.IntegerField(default=2, blank=True, null=True)
    exchange_rate = models.CharField(max_length=50, blank=True, null=True)
    can_show_customer_ob = models.BooleanField(default=False)
    can_show_customer_ob_formatted = models.BooleanField(default=False)
    can_show_vendor_ob = models.BooleanField(default=False)
    can_show_vendor_ob_formatted = models.BooleanField(default=False)
    branch_id = models.CharField(max_length=50, blank=True, null=True)
    branch_name = models.CharField(max_length=255, blank=True, null=True)
    opening_balance_amount = models.DecimalField(
        max_digits=15, decimal_places=2, default=0, blank=True, null=True
    )
    opening_balance_amount_formatted = models.CharField(
        max_length=50, blank=True, null=True
    )
    opening_balance_amount_bcy = models.CharField(max_length=50, blank=True, null=True)
    opening_balance_amount_bcy_formatted = models.CharField(
        max_length=50, blank=True, null=True
    )
    outstanding_ob_receivable_amount = models.DecimalField(
        max_digits=15, decimal_places=2, default=0, blank=True, null=True
    )
    outstanding_ob_receivable_amount_formatted = models.CharField(
        max_length=50, blank=True, null=True
    )
    outstanding_ob_payable_amount = models.DecimalField(
        max_digits=15, decimal_places=2, default=0, blank=True, null=True
    )
    outstanding_ob_payable_amount_formatted = models.CharField(
        max_length=50, blank=True, null=True
    )
    outstanding_receivable_amount = models.DecimalField(
        max_digits=15, decimal_places=2, default=0, blank=True, null=True
    )
    outstanding_receivable_amount_formatted = models.CharField(
        max_length=50, blank=True, null=True
    )
    outstanding_receivable_amount_bcy = models.DecimalField(
        max_digits=15, decimal_places=2, default=0, blank=True, null=True
    )
    outstanding_receivable_amount_bcy_formatted = models.CharField(
        max_length=50, blank=True, null=True
    )
    outstanding_payable_amount = models.DecimalField(
        max_digits=15, decimal_places=2, default=0, blank=True, null=True
    )
    outstanding_payable_amount_formatted = models.CharField(
        max_length=50, blank=True, null=True
    )
    outstanding_payable_amount_bcy = models.DecimalField(
        max_digits=15, decimal_places=2, default=0, blank=True, null=True
    )
    outstanding_payable_amount_bcy_formatted = models.CharField(
        max_length=50, blank=True, null=True
    )
    unused_credits_receivable_amount = models.DecimalField(
        max_digits=15, decimal_places=2, default=0, blank=True, null=True
    )
    unused_credits_receivable_amount_formatted = models.CharField(
        max_length=50, blank=True, null=True
    )
    unused_credits_receivable_amount_bcy = models.DecimalField(
        max_digits=15, decimal_places=2, default=0, blank=True, null=True
    )
    unused_credits_receivable_amount_bcy_formatted = models.CharField(
        max_length=50, blank=True, null=True
    )
    unused_credits_payable_amount = models.DecimalField(
        max_digits=15, decimal_places=2, default=0, blank=True, null=True
    )
    unused_credits_payable_amount_formatted = models.CharField(
        max_length=50, blank=True, null=True
    )
    unused_credits_payable_amount_bcy = models.DecimalField(
        max_digits=15, decimal_places=2, default=0, blank=True, null=True
    )
    unused_credits_payable_amount_bcy_formatted = models.CharField(
        max_length=50, blank=True, null=True
    )
    unused_retainer_payments = models.DecimalField(
        max_digits=15, decimal_places=2, default=0, blank=True, null=True
    )
    unused_retainer_payments_formatted = models.CharField(
        max_length=50, blank=True, null=True
    )
    status = models.CharField(max_length=20, blank=True, null=True)
    status_formatted = models.CharField(max_length=255, blank=True, null=True)
    payment_reminder_enabled = models.BooleanField(default=True)
    is_sms_enabled = models.BooleanField(default=True)
    is_portal_enabled = models.BooleanField(default=False)
    is_consent_agreed = models.BooleanField(default=False)
    consent_date = models.DateField(blank=True, null=True)
    is_client_review_settings_enabled = models.BooleanField(default=False)
    custom_fields = models.JSONField(blank=True, null=True)
    cf_meeraq_ctt = models.CharField(max_length=255, blank=True, null=True)
    cf_meeraq_ctt_unformatted = models.CharField(max_length=255, blank=True, null=True)
    custom_field_hash = models.JSONField(blank=True, null=True)
    is_taxable = models.BooleanField(default=True)
    tax_id = models.CharField(max_length=50, blank=True, null=True)
    tds_tax_id = models.CharField(max_length=50, blank=True, null=True)
    tax_name = models.CharField(max_length=255, blank=True, null=True)
    tax_name_formatted = models.CharField(max_length=255, blank=True, null=True)
    tax_percentage = models.DecimalField(
        max_digits=5, decimal_places=2, blank=True, null=True
    )
    country_code = models.CharField(max_length=10, blank=True, null=True)
    country_code_formatted = models.CharField(max_length=10, blank=True, null=True)
    place_of_contact = models.CharField(max_length=50, blank=True, null=True)
    place_of_contact_formatted = models.CharField(max_length=255, blank=True, null=True)
    gst_no = models.CharField(max_length=50, blank=True, null=True)
    pan_no = models.CharField(max_length=50, blank=True, null=True)
    trader_name = models.CharField(max_length=255, blank=True, null=True)
    legal_name = models.CharField(max_length=255, blank=True, null=True)
    vat_reg_no = models.CharField(max_length=50, blank=True, null=True)
    udyam_reg_no = models.CharField(max_length=50, blank=True, null=True)
    msme_type = models.CharField(max_length=50, blank=True, null=True)
    msme_type_formatted = models.CharField(max_length=255, blank=True, null=True)
    tax_treatment = models.CharField(max_length=50, blank=True, null=True)
    tax_treatment_formatted = models.CharField(max_length=255, blank=True, null=True)
    tax_reg_no = models.CharField(max_length=50, blank=True, null=True)
    contact_category = models.CharField(max_length=50, blank=True, null=True)
    contact_category_formatted = models.CharField(max_length=255, blank=True, null=True)
    gst_treatment = models.CharField(max_length=50, blank=True, null=True)
    gst_treatment_formatted = models.CharField(max_length=255, blank=True, null=True)
    is_linked_with_contact = models.BooleanField(default=False)
    sales_channel = models.CharField(max_length=50, blank=True, null=True)
    ach_supported = models.BooleanField(default=False)
    portal_receipt_count = models.IntegerField(default=0, blank=True, null=True)
    opening_balances = models.JSONField(blank=True, null=True)
    allow_parent_for_payment_and_view = models.BooleanField(default=False)
    tax_info_list = models.JSONField(blank=True, null=True)
    entity_address_id = models.CharField(max_length=50, blank=True, null=True)
    billing_address = models.JSONField(blank=True, null=True)
    shipping_address = models.JSONField(blank=True, null=True)
    contact_persons = models.JSONField(blank=True, null=True)
    addresses = models.JSONField(blank=True, null=True)
    pricebook_id = models.CharField(max_length=50, blank=True, null=True)
    pricebook_name = models.CharField(max_length=255, blank=True, null=True)
    associated_with_square = models.BooleanField(default=False)
    can_add_card = models.BooleanField(default=False)
    can_add_bank_account = models.BooleanField(default=False)
    cards = models.JSONField(blank=True, null=True)
    checks = models.JSONField(blank=True, null=True)
    bank_accounts = models.JSONField(blank=True, null=True)
    vpa_list = models.JSONField(blank=True, null=True)
    notes = models.TextField(blank=True, null=True)
    created_time = models.DateTimeField(blank=True, null=True)
    created_date = models.DateField(blank=True, null=True)
    created_date_formatted = models.CharField(max_length=20, blank=True, null=True)
    created_by_name = models.CharField(max_length=255, blank=True, null=True)
    last_modified_time = models.DateTimeField(blank=True, null=True)
    tags = models.JSONField(blank=True, null=True)
    zohopeople_client_id = models.CharField(max_length=50, blank=True, null=True)
    customer_currency_summaries = models.JSONField(blank=True, null=True)
    entity = models.ForeignKey(Entity, null=True, on_delete=models.SET_NULL)

    class Meta:
        ordering = ["-created_time"]

    def __str__(self):
        return self.contact_name


class ZohoVendor(models.Model):
    contact_id = models.CharField(max_length=100, blank=True, null=True)
    contact_name = models.CharField(max_length=255, blank=True, null=True)
    company_name = models.CharField(max_length=255, blank=True, null=True)
    first_name = models.CharField(max_length=255, blank=True, null=True)
    last_name = models.CharField(max_length=255, blank=True, null=True)
    designation = models.CharField(max_length=255, blank=True, null=True)
    department = models.CharField(max_length=255, blank=True, null=True)
    website = models.CharField(max_length=255, blank=True, null=True)
    is_bcy_only_contact = models.BooleanField(default=False)
    is_credit_limit_migration_completed = models.BooleanField(default=False)
    language_code = models.CharField(max_length=10, blank=True, null=True)
    language_code_formatted = models.CharField(max_length=50, blank=True, null=True)
    contact_salutation = models.CharField(max_length=100, blank=True, null=True)
    email = models.EmailField(blank=True, null=True)
    phone = models.CharField(max_length=20, blank=True, null=True)
    mobile = models.CharField(max_length=20, blank=True, null=True)
    invited_by = models.CharField(max_length=255, blank=True, null=True)
    portal_status = models.CharField(max_length=20, blank=True, null=True)
    portal_status_formatted = models.CharField(max_length=20, blank=True, null=True)
    is_client_review_asked = models.BooleanField(default=False)
    has_transaction = models.BooleanField(default=False)
    contact_type = models.CharField(max_length=20, blank=True, null=True)
    customer_sub_type = models.CharField(max_length=20, blank=True, null=True)
    customer_sub_type_formatted = models.CharField(max_length=20, blank=True, null=True)
    owner_id = models.CharField(max_length=100, blank=True, null=True)
    owner_name = models.CharField(max_length=255, blank=True, null=True)
    source = models.CharField(max_length=50, blank=True, null=True)
    source_formatted = models.CharField(max_length=50, blank=True, null=True)
    documents = models.JSONField(default=list, blank=True, null=True)
    twitter = models.CharField(max_length=255, blank=True, null=True)
    facebook = models.CharField(max_length=255, blank=True, null=True)
    zoho_customer = models.BooleanField(default=False)
    is_linked_with_zohocrm = models.BooleanField(default=False)
    zoho_customer = models.BooleanField(default=False)
    primary_contact_id = models.CharField(max_length=100, blank=True, null=True)
    zcrm_vendor_id = models.CharField(max_length=100, blank=True, null=True)
    crm_owner_id = models.CharField(max_length=100, blank=True, null=True)
    payment_terms = models.IntegerField(default=0, blank=True, null=True)
    payment_terms_label = models.CharField(max_length=50, blank=True, null=True)
    credit_limit_exceeded_amount = models.DecimalField(
        max_digits=15, decimal_places=2, default=0.00, blank=True, null=True
    )
    credit_limit_exceeded_amount_formatted = models.CharField(
        max_length=20, blank=True, null=True
    )
    currency_id = models.CharField(max_length=100, blank=True, null=True)
    currency_code = models.CharField(max_length=10, blank=True, null=True)
    currency_symbol = models.CharField(max_length=10, blank=True, null=True)
    price_precision = models.IntegerField(blank=True, null=True)
    exchange_rate = models.DecimalField(
        max_digits=15, decimal_places=6, blank=True, null=True
    )
    can_show_customer_ob = models.BooleanField(default=False)
    can_show_customer_ob_formatted = models.BooleanField(default=False)
    can_show_vendor_ob = models.BooleanField(default=False)
    can_show_vendor_ob_formatted = models.BooleanField(default=False)
    branch_id = models.CharField(max_length=100, blank=True, null=True)
    branch_name = models.CharField(max_length=255, blank=True, null=True)
    opening_balance_amount = models.DecimalField(
        max_digits=15, decimal_places=2, default=0.00, blank=True, null=True
    )
    opening_balance_amount_formatted = models.CharField(
        max_length=20, blank=True, null=True
    )
    opening_balance_amount_bcy = models.CharField(max_length=20, blank=True, null=True)
    opening_balance_amount_bcy_formatted = models.CharField(
        max_length=20, blank=True, null=True
    )
    outstanding_ob_receivable_amount = models.DecimalField(
        max_digits=15, decimal_places=2, default=0.00, blank=True, null=True
    )
    outstanding_ob_receivable_amount_formatted = models.CharField(
        max_length=20, blank=True, null=True
    )
    outstanding_ob_payable_amount = models.DecimalField(
        max_digits=15, decimal_places=2, default=0.00, blank=True, null=True
    )
    outstanding_ob_payable_amount_formatted = models.CharField(
        max_length=20, blank=True, null=True
    )
    outstanding_receivable_amount = models.DecimalField(
        max_digits=15, decimal_places=2, default=0.00, blank=True, null=True
    )
    outstanding_receivable_amount_formatted = models.CharField(
        max_length=20, blank=True, null=True
    )
    outstanding_receivable_amount_bcy = models.DecimalField(
        max_digits=15, decimal_places=2, default=0.00, blank=True, null=True
    )
    outstanding_receivable_amount_bcy_formatted = models.CharField(
        max_length=20, blank=True, null=True
    )
    outstanding_payable_amount = models.DecimalField(
        max_digits=15, decimal_places=2, default=0.00, blank=True, null=True
    )
    outstanding_payable_amount_formatted = models.CharField(
        max_length=20, blank=True, null=True
    )
    outstanding_payable_amount_bcy = models.DecimalField(
        max_digits=15, decimal_places=2, default=0.00, blank=True, null=True
    )
    outstanding_payable_amount_bcy_formatted = models.CharField(
        max_length=20, blank=True, null=True
    )
    unused_credits_receivable_amount = models.DecimalField(
        max_digits=15, decimal_places=2, default=0.00, blank=True, null=True
    )
    unused_credits_receivable_amount_formatted = models.CharField(
        max_length=20, blank=True, null=True
    )
    unused_credits_receivable_amount_bcy = models.DecimalField(
        max_digits=15, decimal_places=2, default=0.00, blank=True, null=True
    )
    unused_credits_receivable_amount_bcy_formatted = models.CharField(
        max_length=20, blank=True, null=True
    )
    unused_credits_payable_amount = models.DecimalField(
        max_digits=15, decimal_places=2, default=0.00, blank=True, null=True
    )
    unused_credits_payable_amount_formatted = models.CharField(
        max_length=20, blank=True, null=True
    )
    unused_credits_payable_amount_bcy = models.DecimalField(
        max_digits=15, decimal_places=2, default=0.00, blank=True, null=True
    )
    unused_credits_payable_amount_bcy_formatted = models.CharField(
        max_length=20, blank=True, null=True
    )
    unused_retainer_payments = models.DecimalField(
        max_digits=15, decimal_places=2, default=0.00, blank=True, null=True
    )
    unused_retainer_payments_formatted = models.CharField(
        max_length=20, blank=True, null=True
    )
    status = models.CharField(max_length=20, blank=True, null=True)
    status_formatted = models.CharField(max_length=20, blank=True, null=True)
    payment_reminder_enabled = models.BooleanField(default=False)
    is_sms_enabled = models.BooleanField(default=False)
    is_portal_enabled = models.BooleanField(default=False)
    is_consent_agreed = models.BooleanField(default=False)
    consent_date = models.DateField(blank=True, null=True)
    is_client_review_settings_enabled = models.BooleanField(default=False)
    custom_fields = models.JSONField(default=dict, blank=True, null=True)
    custom_field_hash = models.JSONField(default=dict, blank=True, null=True)
    tax_id = models.CharField(max_length=100, blank=True, null=True)
    tds_tax_id = models.CharField(max_length=100, blank=True, null=True)
    tax_name = models.CharField(max_length=100, blank=True, null=True)
    tax_name_formatted = models.CharField(max_length=100, blank=True, null=True)
    tax_percentage = models.DecimalField(
        max_digits=10, decimal_places=6, blank=True, null=True
    )
    country_code = models.CharField(max_length=10, blank=True, null=True)
    country_code_formatted = models.CharField(max_length=10, blank=True, null=True)
    place_of_contact = models.CharField(max_length=100, blank=True, null=True)
    place_of_contact_formatted = models.CharField(max_length=100, blank=True, null=True)
    gst_no = models.CharField(max_length=50, blank=True, null=True)
    pan_no = models.CharField(max_length=50, blank=True, null=True)
    trader_name = models.CharField(max_length=255, blank=True, null=True)
    legal_name = models.CharField(max_length=255, blank=True, null=True)
    vat_reg_no = models.CharField(max_length=50, blank=True, null=True)
    udyam_reg_no = models.CharField(max_length=50, blank=True, null=True)
    msme_type = models.CharField(max_length=50, blank=True, null=True)
    msme_type_formatted = models.CharField(max_length=50, blank=True, null=True)
    tax_treatment = models.CharField(max_length=50, blank=True, null=True)
    tax_treatment_formatted = models.CharField(max_length=50, blank=True, null=True)
    tax_reg_no = models.CharField(max_length=50, blank=True, null=True)
    contact_category = models.CharField(max_length=50, blank=True, null=True)
    contact_category_formatted = models.CharField(max_length=50, blank=True, null=True)
    gst_treatment = models.CharField(max_length=50, blank=True, null=True)
    gst_treatment_formatted = models.CharField(max_length=50, blank=True, null=True)
    is_linked_with_contact = models.BooleanField(default=False)
    sales_channel = models.CharField(max_length=50, blank=True, null=True)
    ach_supported = models.BooleanField(default=False)
    portal_receipt_count = models.IntegerField(default=0, blank=True, null=True)
    opening_balances = models.JSONField(default=list, blank=True, null=True)
    allow_parent_for_payment_and_view = models.BooleanField(default=False)
    tax_info_list = models.JSONField(default=list, blank=True, null=True)
    entity_address_id = models.CharField(max_length=100, blank=True, null=True)
    billing_address = models.JSONField(default=dict, blank=True, null=True)
    shipping_address = models.JSONField(default=dict, blank=True, null=True)
    contact_persons = models.JSONField(default=list, blank=True, null=True)
    addresses = models.JSONField(default=list, blank=True, null=True)
    pricebook_id = models.CharField(max_length=100, blank=True, null=True)
    pricebook_name = models.CharField(max_length=255, blank=True, null=True)
    default_templates = models.JSONField(default=dict, blank=True, null=True)
    associated_with_square = models.BooleanField(default=False)
    can_add_card = models.BooleanField(default=False)
    can_add_bank_account = models.BooleanField(default=True)
    cards = models.JSONField(default=list, blank=True, null=True)
    checks = models.JSONField(default=list, blank=True, null=True)
    bank_accounts = models.JSONField(default=list, blank=True, null=True)
    vpa_list = models.JSONField(default=list, blank=True, null=True)
    notes = models.TextField(blank=True, null=True)
    created_time = models.DateTimeField(blank=True, null=True)
    created_date = models.DateField(blank=True, null=True)
    created_date_formatted = models.CharField(max_length=20, blank=True, null=True)
    created_by_name = models.CharField(max_length=255, blank=True, null=True)
    last_modified_time = models.DateTimeField(blank=True, null=True)
    tags = models.JSONField(default=list, blank=True, null=True)
    zohopeople_client_id = models.CharField(max_length=100, blank=True, null=True)
    vendor_currency_summaries = models.JSONField(default=list, blank=True, null=True)
    entity = models.ForeignKey(Entity, null=True, on_delete=models.SET_NULL)
    class Meta:
        ordering = ["-created_time"]

    def __str__(self):
        return self.contact_name


class SalesOrderLineItem(models.Model):
    line_item_id = models.CharField(max_length=100, blank=True, null=True)
    variant_id = models.CharField(max_length=100, blank=True, null=True)
    item_id = models.CharField(max_length=100, blank=True, null=True)
    product_id = models.CharField(max_length=100, blank=True, null=True)
    attribute_name1 = models.CharField(max_length=255, blank=True, null=True)
    attribute_name2 = models.CharField(max_length=255, blank=True, null=True)
    attribute_name3 = models.CharField(max_length=255, blank=True, null=True)
    attribute_option_name1 = models.CharField(max_length=255, blank=True, null=True)
    attribute_option_name2 = models.CharField(max_length=255, blank=True, null=True)
    attribute_option_name3 = models.CharField(max_length=255, blank=True, null=True)
    attribute_option_data1 = models.CharField(max_length=255, blank=True, null=True)
    attribute_option_data2 = models.CharField(max_length=255, blank=True, null=True)
    attribute_option_data3 = models.CharField(max_length=255, blank=True, null=True)
    is_combo_product = models.BooleanField(default=False)
    sku = models.CharField(max_length=100, blank=True, null=True)
    name = models.CharField(max_length=255, blank=True, null=True)
    group_name = models.CharField(max_length=255, blank=True, null=True)
    description = models.TextField(blank=True, null=True)
    item_order = models.IntegerField(default=1, blank=True, null=True)
    bcy_rate = models.DecimalField(
        max_digits=15, decimal_places=2, blank=True, null=True
    )
    bcy_rate_formatted = models.CharField(max_length=20, blank=True, null=True)
    rate = models.DecimalField(max_digits=15, decimal_places=2, blank=True, null=True)
    rate_formatted = models.CharField(max_length=20, blank=True, null=True)
    sales_rate = models.DecimalField(
        max_digits=15, decimal_places=2, blank=True, null=True
    )
    sales_rate_formatted = models.CharField(max_length=20, blank=True, null=True)
    quantity = models.DecimalField(
        max_digits=19, decimal_places=6, blank=True, null=True
    )
    unit = models.CharField(max_length=50, blank=True, null=True)
    pricebook_id = models.CharField(max_length=100, blank=True, null=True)
    header_id = models.CharField(max_length=100, blank=True, null=True)
    header_name = models.CharField(max_length=255, blank=True, null=True)
    discount_amount = models.DecimalField(
        max_digits=15, decimal_places=2, default=0.00, blank=True, null=True
    )
    discount_amount_formatted = models.CharField(max_length=20, blank=True, null=True)
    discount = models.DecimalField(
        max_digits=10, decimal_places=6, default=0.00, blank=True, null=True
    )
    discounts = models.JSONField(default=list, blank=True, null=True)
    gst_treatment_code = models.CharField(max_length=50, blank=True, null=True)
    tax_id = models.CharField(max_length=100, blank=True, null=True)
    tax_name = models.CharField(max_length=100, blank=True, null=True)
    tax_type = models.CharField(max_length=50, blank=True, null=True)
    tax_percentage = models.DecimalField(
        max_digits=10, decimal_places=6, blank=True, null=True
    )
    line_item_taxes = models.JSONField(default=list, blank=True, null=True)
    item_total = models.DecimalField(
        max_digits=15, decimal_places=2, blank=True, null=True
    )
    item_total_formatted = models.CharField(max_length=20, blank=True, null=True)
    item_sub_total = models.DecimalField(
        max_digits=15, decimal_places=2, blank=True, null=True
    )
    item_sub_total_formatted = models.CharField(max_length=20, blank=True, null=True)
    item_total_inclusive_of_tax = models.DecimalField(
        max_digits=15, decimal_places=2, blank=True, null=True
    )
    item_total_inclusive_of_tax_formatted = models.CharField(
        max_length=20, blank=True, null=True
    )
    product_type = models.CharField(max_length=50, blank=True, null=True)
    line_item_type = models.CharField(max_length=50, blank=True, null=True)
    item_type = models.CharField(max_length=50, blank=True, null=True)
    item_type_formatted = models.CharField(max_length=50, blank=True, null=True)
    hsn_or_sac = models.CharField(max_length=20, blank=True, null=True)
    is_invoiced = models.BooleanField(default=False, blank=True, null=True)
    tags = models.JSONField(default=list, blank=True, null=True)
    image_name = models.CharField(max_length=255, blank=True, null=True)
    image_type = models.CharField(max_length=50, blank=True, null=True)
    image_document_id = models.CharField(max_length=100, blank=True, null=True)
    document_id = models.CharField(max_length=100, blank=True, null=True)
    item_custom_fields = models.JSONField(default=list, blank=True, null=True)
    custom_field_hash = models.JSONField(default=dict, blank=True, null=True)
    quantity_invoiced = models.DecimalField(
        max_digits=19, decimal_places=6, default=0.00, blank=True, null=True
    )
    quantity_backordered = models.DecimalField(
        max_digits=19, decimal_places=6, default=0.00, blank=True, null=True
    )
    quantity_cancelled = models.DecimalField(
        max_digits=19, decimal_places=6, default=0.00, blank=True, null=True
    )
    is_fulfillable = models.DecimalField(
        max_digits=15, decimal_places=2, default=0.00, blank=True, null=True
    )
    project_id = models.CharField(max_length=100, blank=True, null=True)
    is_booking_amount = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.id} Line Item {self.line_item_id} - {self.description}"


class SalesOrder(models.Model):
    zoho_customer = models.ForeignKey(
        ZohoCustomer, on_delete=models.SET_NULL, blank=True, null=True, default=None
    )
    so_line_items = models.ManyToManyField(SalesOrderLineItem, blank=True)
    gm_sheet = models.ForeignKey(
        GmSheet, on_delete=models.SET_NULL, blank=True, null=True, default=None
    )
    salesorder_id = models.CharField(max_length=100, blank=True, null=True)
    documents = models.JSONField(default=list, blank=True, null=True)
    crm_owner_id = models.CharField(max_length=100, blank=True, null=True)
    crm_custom_reference_id = models.CharField(max_length=100, blank=True, null=True)
    zcrm_potential_id = models.CharField(max_length=100, blank=True, null=True)
    zcrm_potential_name = models.CharField(max_length=255, blank=True, null=True)
    salesorder_number = models.CharField(max_length=255, blank=True, null=True)
    date = models.DateField(blank=True, null=True)
    date_formatted = models.CharField(max_length=20, blank=True, null=True)
    offline_created_date_with_time = models.CharField(
        max_length=100, blank=True, null=True
    )
    offline_created_date_with_time_formatted = models.CharField(
        max_length=20, blank=True, null=True
    )
    tracking_url = models.CharField(max_length=255, blank=True, null=True)
    has_discount = models.BooleanField(default=False)
    is_pre_gst = models.BooleanField(default=False)
    invoice_conversion_type = models.CharField(max_length=20, blank=True, null=True)
    status = models.CharField(max_length=20, blank=True, null=True)
    status_formatted = models.CharField(max_length=20, blank=True, null=True)
    color_code = models.CharField(max_length=20, blank=True, null=True)
    current_sub_status_id = models.CharField(max_length=100, blank=True, null=True)
    current_sub_status = models.CharField(max_length=20, blank=True, null=True)
    current_sub_status_formatted = models.CharField(
        max_length=20, blank=True, null=True
    )
    sub_statuses = models.JSONField(default=list, blank=True, null=True)
    shipment_date = models.DateField(blank=True, null=True)
    shipment_date_formatted = models.CharField(max_length=20, blank=True, null=True)
    reference_number = models.CharField(max_length=255, blank=True, null=True)
    customer_id = models.CharField(max_length=100, blank=True, null=True)
    customer_name = models.CharField(max_length=255, blank=True, null=True)
    currency_formatter = models.JSONField(default=dict, blank=True, null=True)
    contact_persons = models.JSONField(default=list, blank=True, null=True)
    contact_persons_associated = models.JSONField(default=list, blank=True, null=True)
    contact_person_details = models.JSONField(default=list, blank=True, null=True)
    source = models.CharField(max_length=50, blank=True, null=True)
    gst_no = models.CharField(max_length=50, blank=True, null=True)
    contact_category = models.CharField(max_length=50, blank=True, null=True)
    gst_treatment = models.CharField(max_length=50, blank=True, null=True)
    gst_treatment_formatted = models.CharField(max_length=50, blank=True, null=True)
    tax_treatment = models.CharField(max_length=50, blank=True, null=True)
    tax_treatment_formatted = models.CharField(max_length=50, blank=True, null=True)
    place_of_supply = models.CharField(max_length=50, blank=True, null=True)
    place_of_supply_formatted = models.CharField(max_length=50, blank=True, null=True)
    tax_specification = models.CharField(max_length=50, blank=True, null=True)
    is_taxable = models.BooleanField(default=False)
    has_shipping_address = models.BooleanField(default=True)
    currency_id = models.CharField(max_length=100, blank=True, null=True)
    currency_code = models.CharField(max_length=10, blank=True, null=True)
    currency_symbol = models.CharField(max_length=10, blank=True, null=True)
    exchange_rate = models.DecimalField(
        max_digits=15, decimal_places=6, blank=True, null=True
    )
    is_fba_shipment_created = models.BooleanField(default=False)
    is_discount_before_tax = models.BooleanField(default=True)
    discount_type = models.CharField(max_length=20, blank=True, null=True)
    estimate_id = models.CharField(max_length=100, blank=True, null=True)
    delivery_method = models.CharField(max_length=100, blank=True, null=True)
    delivery_method_id = models.CharField(max_length=100, blank=True, null=True)
    is_inclusive_tax = models.BooleanField(default=False)
    tax_rounding = models.CharField(max_length=50, blank=True, null=True)
    tds_override_preference = models.CharField(max_length=50, blank=True, null=True)
    order_status = models.CharField(max_length=20, blank=True, null=True)
    order_status_formatted = models.CharField(max_length=20, blank=True, null=True)
    invoiced_status = models.CharField(max_length=20, blank=True, null=True)
    invoiced_status_formatted = models.CharField(max_length=20, blank=True, null=True)
    paid_status = models.CharField(max_length=20, blank=True, null=True)
    paid_status_formatted = models.CharField(max_length=20, blank=True, null=True)
    account_identifier = models.CharField(max_length=100, blank=True, null=True)
    integration_id = models.CharField(max_length=100, blank=True, null=True)
    has_qty_cancelled = models.BooleanField(default=False)
    is_reverse_charge_applied = models.BooleanField(default=False)
    shipping_details = models.JSONField(default=dict, blank=True, null=True)
    created_by_email = models.EmailField(blank=True, null=True)
    created_by_name = models.CharField(max_length=255, blank=True, null=True)
    branch_id = models.CharField(max_length=100, blank=True, null=True)
    branch_name = models.CharField(max_length=255, blank=True, null=True)
    total_quantity = models.DecimalField(
        max_digits=19, decimal_places=6, blank=True, null=True
    )
    total_quantity_formatted = models.CharField(max_length=20, blank=True, null=True)
    is_portal_enabled = models.BooleanField(default=False)
    is_data_redacted = models.BooleanField(default=False)
    can_fetch_redacted_data = models.BooleanField(default=False)
    can_edit_marketplace_tax = models.BooleanField(default=False)
    entity_tags = models.CharField(max_length=255, blank=True, null=True)
    submitter_id = models.CharField(max_length=100, blank=True, null=True)
    approver_id = models.CharField(max_length=100, blank=True, null=True)
    submitted_date = models.CharField(max_length=100, blank=True, null=True)
    submitted_date_formatted = models.CharField(max_length=20, blank=True, null=True)
    submitted_by = models.CharField(max_length=100, blank=True, null=True)
    submitted_by_name = models.CharField(max_length=255, blank=True, null=True)
    submitted_by_email = models.EmailField(blank=True, null=True)
    submitted_by_photo_url = models.CharField(max_length=255, blank=True, null=True)
    price_precision = models.IntegerField(blank=True, null=True)
    is_emailed = models.BooleanField(default=False)
    purchaseorders = models.JSONField(default=list, blank=True, null=True)
    billing_address_id = models.CharField(max_length=100, blank=True, null=True)
    billing_address = models.JSONField(default=dict, blank=True, null=True)
    shipping_address_id = models.CharField(max_length=100, blank=True, null=True)
    shipping_address = models.JSONField(default=dict, blank=True, null=True)
    is_test_order = models.BooleanField(default=False)
    notes = models.TextField(blank=True, null=True)
    terms = models.TextField(blank=True, null=True)
    payment_terms = models.IntegerField(default=0, blank=True, null=True)
    payment_terms_label = models.CharField(max_length=100, blank=True, null=True)
    custom_fields = models.JSONField(default=list, blank=True, null=True)
    custom_field_hash = models.JSONField(default=dict, blank=True, null=True)
    template_id = models.CharField(max_length=100, blank=True, null=True)
    template_name = models.CharField(max_length=255, blank=True, null=True)
    page_width = models.CharField(max_length=20, blank=True, null=True)
    page_height = models.CharField(max_length=20, blank=True, null=True)
    orientation = models.CharField(max_length=20, blank=True, null=True)
    template_type = models.CharField(max_length=20, blank=True, null=True)
    template_type_formatted = models.CharField(max_length=20, blank=True, null=True)
    created_time = models.DateTimeField(blank=True, null=True)
    created_time_formatted = models.CharField(max_length=20, blank=True, null=True)
    last_modified_time = models.DateTimeField(blank=True, null=True)
    last_modified_time_formatted = models.CharField(
        max_length=20, blank=True, null=True
    )
    created_by_id = models.CharField(max_length=100, blank=True, null=True)
    created_date = models.DateField(blank=True, null=True)
    created_date_formatted = models.CharField(max_length=20, blank=True, null=True)
    last_modified_by_id = models.CharField(max_length=100, blank=True, null=True)
    attachment_name = models.CharField(max_length=255, blank=True, null=True)
    can_send_in_mail = models.BooleanField(default=False)
    salesperson_id = models.CharField(max_length=100, blank=True, null=True)
    salesperson_name = models.CharField(max_length=255, blank=True, null=True)
    merchant_id = models.CharField(max_length=100, blank=True, null=True)
    merchant_name = models.CharField(max_length=255, blank=True, null=True)
    merchant_gst_no = models.CharField(max_length=50, blank=True, null=True)
    pickup_location_id = models.CharField(max_length=100, blank=True, null=True)
    discount = models.DecimalField(
        max_digits=15, decimal_places=2, blank=True, null=True
    )
    discount_applied_on_amount = models.DecimalField(
        max_digits=15, decimal_places=2, blank=True, null=True
    )
    is_adv_tracking_in_package = models.BooleanField(default=False)
    shipping_charge_tax_id = models.CharField(max_length=100, blank=True, null=True)
    shipping_charge_tax_name = models.CharField(max_length=255, blank=True, null=True)
    shipping_charge_tax_type = models.CharField(max_length=50, blank=True, null=True)
    shipping_charge_tax_percentage = models.CharField(
        max_length=10, blank=True, null=True
    )
    shipping_charge_tax_exemption_id = models.CharField(
        max_length=100, blank=True, null=True
    )
    shipping_charge_tax_exemption_code = models.CharField(
        max_length=50, blank=True, null=True
    )
    shipping_charge_sac_code = models.CharField(max_length=50, blank=True, null=True)
    shipping_charge_tax = models.CharField(max_length=50, blank=True, null=True)
    bcy_shipping_charge_tax = models.CharField(max_length=50, blank=True, null=True)
    shipping_charge_exclusive_of_tax = models.DecimalField(
        max_digits=15, decimal_places=2, blank=True, null=True
    )
    shipping_charge_inclusive_of_tax = models.DecimalField(
        max_digits=15, decimal_places=2, blank=True, null=True
    )
    shipping_charge_tax_formatted = models.CharField(
        max_length=20, blank=True, null=True
    )
    shipping_charge_exclusive_of_tax_formatted = models.CharField(
        max_length=20, blank=True, null=True
    )
    shipping_charge_inclusive_of_tax_formatted = models.CharField(
        max_length=20, blank=True, null=True
    )
    shipping_charge = models.DecimalField(
        max_digits=15, decimal_places=2, blank=True, null=True
    )
    shipping_charge_formatted = models.CharField(max_length=20, blank=True, null=True)
    bcy_shipping_charge = models.DecimalField(
        max_digits=15, decimal_places=2, blank=True, null=True
    )
    adjustment = models.DecimalField(
        max_digits=15, decimal_places=2, blank=True, null=True
    )
    adjustment_formatted = models.CharField(max_length=20, blank=True, null=True)
    bcy_adjustment = models.DecimalField(
        max_digits=15, decimal_places=2, blank=True, null=True
    )
    adjustment_description = models.CharField(max_length=255, blank=True, null=True)
    roundoff_value = models.DecimalField(
        max_digits=15, decimal_places=2, blank=True, null=True
    )
    roundoff_value_formatted = models.CharField(max_length=20, blank=True, null=True)
    transaction_rounding_type = models.CharField(max_length=20, blank=True, null=True)
    sub_total = models.DecimalField(
        max_digits=15, decimal_places=2, blank=True, null=True
    )
    sub_total_formatted = models.CharField(max_length=20, blank=True, null=True)
    bcy_sub_total = models.DecimalField(
        max_digits=15, decimal_places=2, blank=True, null=True
    )
    sub_total_inclusive_of_tax = models.DecimalField(
        max_digits=15, decimal_places=2, blank=True, null=True
    )
    sub_total_inclusive_of_tax_formatted = models.CharField(
        max_length=20, blank=True, null=True
    )
    sub_total_exclusive_of_discount = models.DecimalField(
        max_digits=15, decimal_places=2, blank=True, null=True
    )
    sub_total_exclusive_of_discount_formatted = models.CharField(
        max_length=20, blank=True, null=True
    )
    discount_total = models.DecimalField(
        max_digits=15, decimal_places=2, blank=True, null=True
    )
    discount_total_formatted = models.CharField(max_length=20, blank=True, null=True)
    bcy_discount_total = models.DecimalField(
        max_digits=15, decimal_places=2, blank=True, null=True
    )
    discount_percent = models.DecimalField(
        max_digits=10, decimal_places=6, blank=True, null=True
    )
    tax_total = models.DecimalField(
        max_digits=15, decimal_places=2, blank=True, null=True
    )
    tax_total_formatted = models.CharField(max_length=20, blank=True, null=True)
    bcy_tax_total = models.DecimalField(
        max_digits=15, decimal_places=2, blank=True, null=True
    )
    total = models.DecimalField(max_digits=15, decimal_places=2, blank=True, null=True)
    total_formatted = models.CharField(max_length=20, blank=True, null=True)
    computation_type = models.CharField(max_length=20, blank=True, null=True)
    bcy_total = models.DecimalField(
        max_digits=15, decimal_places=2, blank=True, null=True
    )
    reverse_charge_tax_total = models.DecimalField(
        max_digits=15, decimal_places=2, blank=True, null=True
    )
    reverse_charge_tax_total_formatted = models.CharField(
        max_length=20, blank=True, null=True
    )
    taxes = models.JSONField(default=list, blank=True, null=True)
    tds_summary = models.JSONField(default=list, blank=True, null=True)
    invoices = models.JSONField(default=list, blank=True, null=True)
    contact = models.JSONField(default=dict, blank=True, null=True)
    balance = models.DecimalField(
        max_digits=15, decimal_places=2, blank=True, null=True
    )
    balance_formatted = models.CharField(max_length=20, blank=True, null=True)
    approvers_list = models.JSONField(default=list, blank=True, null=True)
    referred_by = models.CharField(max_length=225, blank=True, null=True)
    linkedin_profile = models.CharField(max_length=225, blank=True, null=True)
    background = models.CharField(max_length=225, blank=True, null=True)
    designation = models.CharField(max_length=225, blank=True, null=True)
    companies_worked_in = models.CharField(max_length=225, blank=True, null=True)
    performance_evaluation = models.CharField(max_length=225, blank=True, null=True)
    location = models.CharField(max_length=225, blank=True, null=True)
    credential = models.CharField(max_length=225, blank=True, null=True)
    pmo_remarks = models.TextField(blank=True, null=True)
    finance_remarks = models.TextField(blank=True, null=True)
    entity = models.ForeignKey(Entity, null=True, on_delete=models.SET_NULL)
    project_name = models.TextField(blank=True, null=True)
    added_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)

    class Meta:
        ordering = ["-created_time"]

    def __str__(self):
        return f"Sales Order {self.salesorder_number} {self.salesorder_id}"


class ClientInvoiceLineItem(models.Model):
    line_item_id = models.CharField(max_length=255, blank=True, null=True)
    item_id = models.CharField(max_length=255, blank=True, null=True)
    sku = models.CharField(max_length=255, blank=True, null=True)
    item_order = models.IntegerField(blank=True, null=True)
    product_type = models.CharField(max_length=255, blank=True, null=True)
    has_product_type_mismatch = models.BooleanField(
        default=False, blank=True, null=True
    )
    has_invalid_hsn = models.BooleanField(default=False, blank=True, null=True)
    name = models.CharField(max_length=255, blank=True, null=True)
    internal_name = models.CharField(max_length=255, blank=True, null=True)
    description = models.TextField(blank=True, null=True)
    unit = models.CharField(max_length=255, blank=True, null=True)
    quantity = models.DecimalField(
        max_digits=19, decimal_places=6, blank=True, null=True
    )
    discount_amount = models.DecimalField(
        max_digits=10, decimal_places=2, blank=True, null=True
    )
    discount_amount_formatted = models.CharField(max_length=255, blank=True, null=True)
    discount = models.DecimalField(
        max_digits=10, decimal_places=2, blank=True, null=True
    )
    discounts = models.JSONField(default=list, blank=True, null=True)
    bcy_rate = models.DecimalField(
        max_digits=10, decimal_places=2, blank=True, null=True
    )
    bcy_rate_formatted = models.CharField(max_length=255, blank=True, null=True)
    rate = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)
    rate_formatted = models.CharField(max_length=255, blank=True, null=True)
    account_id = models.CharField(max_length=255, blank=True, null=True)
    account_name = models.CharField(max_length=255, blank=True, null=True)
    header_id = models.CharField(max_length=255, blank=True, null=True)
    header_name = models.CharField(max_length=255, blank=True, null=True)
    pricebook_id = models.CharField(max_length=255, blank=True, null=True)
    item_total_inclusive_of_tax = models.DecimalField(
        max_digits=10, decimal_places=2, blank=True, null=True
    )
    item_total_inclusive_of_tax_formatted = models.CharField(
        max_length=255, blank=True, null=True
    )
    tax_id = models.CharField(max_length=255, blank=True, null=True)
    tax_name = models.CharField(max_length=255, blank=True, null=True)
    tax_type = models.CharField(max_length=255, blank=True, null=True)
    tax_percentage = models.DecimalField(
        max_digits=5, decimal_places=2, blank=True, null=True
    )
    gst_treatment_code = models.CharField(max_length=255, blank=True, null=True)
    item_total = models.DecimalField(
        max_digits=10, decimal_places=2, blank=True, null=True
    )
    item_total_formatted = models.CharField(max_length=255, blank=True, null=True)
    item_custom_fields = models.JSONField(default=dict, blank=True, null=True)
    pricing_scheme = models.CharField(max_length=255, blank=True, null=True)
    tags = models.JSONField(default=list, blank=True, null=True)
    documents = models.JSONField(default=list, blank=True, null=True)
    hsn_or_sac = models.CharField(max_length=255, blank=True, null=True)
    image_document_id = models.CharField(max_length=255, blank=True, null=True)
    reverse_charge_tax_id = models.CharField(max_length=255, blank=True, null=True)
    line_item_taxes = models.JSONField(default=list, blank=True, null=True)
    bill_id = models.CharField(max_length=255, blank=True, null=True)
    bill_item_id = models.CharField(max_length=255, blank=True, null=True)
    project_id = models.CharField(max_length=255, blank=True, null=True)
    time_entry_ids = models.JSONField(default=list, blank=True, null=True)
    expense_id = models.CharField(max_length=255, blank=True, null=True)
    item_type = models.CharField(max_length=255, blank=True, null=True)
    item_type_formatted = models.CharField(max_length=255, blank=True, null=True)
    expense_receipt_name = models.CharField(max_length=255, blank=True, null=True)
    sales_rate = models.CharField(max_length=255, blank=True, null=True)
    sales_rate_formatted = models.CharField(max_length=255, blank=True, null=True)
    salesorder_item_id = models.CharField(max_length=255, blank=True, null=True)
    can_show_in_task_table = models.BooleanField(default=False, blank=True, null=True)
    cost_amount = models.DecimalField(
        max_digits=10, decimal_places=2, blank=True, null=True
    )
    cost_amount_formatted = models.CharField(max_length=255, blank=True, null=True)
    markup_percent = models.DecimalField(
        max_digits=5, decimal_places=2, blank=True, null=True
    )
    markup_percent_formatted = models.CharField(max_length=255, blank=True, null=True)

    class Meta:
        db_table = "line_items"


class ClientInvoice(models.Model):
    bank_detail = models.ForeignKey(
        BankDetails, on_delete=models.SET_NULL, blank=True, null=True, default=None
    )
    zoho_customer = models.ForeignKey(
        ZohoCustomer, on_delete=models.SET_NULL, blank=True, null=True, default=None
    )
    sales_order = models.ForeignKey(
        SalesOrder, on_delete=models.SET_NULL, blank=True, null=True, default=None
    )
    purchase_orders = models.ManyToManyField(
        "PurchaseOrder", blank=True
    )
    client_invoice_line_items = models.ManyToManyField(
        ClientInvoiceLineItem, blank=True
    )
    invoice_id = models.CharField(max_length=100, null=True, blank=True)
    invoice_number = models.CharField(max_length=100, null=True, blank=True)
    date = models.DateField(null=True, blank=True)
    date_formatted = models.CharField(max_length=20, blank=True)
    due_date = models.DateField(null=True, blank=True)
    due_date_formatted = models.CharField(max_length=20, blank=True)
    offline_created_date_with_time = models.CharField(max_length=100, blank=True)
    customer_id = models.CharField(max_length=100, null=True, blank=True)
    customer_name = models.CharField(max_length=255, null=True, blank=True)
    cf_meeraq_ctt = models.CharField(max_length=100, null=True, blank=True)
    cf_meeraq_ctt_unformatted = models.CharField(max_length=100, null=True, blank=True)
    email = models.EmailField(null=True, blank=True)
    currency_id = models.CharField(max_length=100, null=True, blank=True)
    invoice_source = models.CharField(max_length=100, null=True, blank=True)
    invoice_source_formatted = models.CharField(max_length=100, null=True, blank=True)
    currency_code = models.CharField(max_length=10, null=True, blank=True)
    currency_symbol = models.CharField(max_length=10, null=True, blank=True)
    currency_name_formatted = models.CharField(max_length=100, null=True, blank=True)
    status = models.CharField(max_length=20, null=True, blank=True)
    status_formatted = models.CharField(max_length=20, null=True, blank=True)
    custom_fields = models.JSONField(default=list, null=True, blank=True)
    custom_field_hash = models.JSONField(default=dict, null=True, blank=True)
    recurring_invoice_id = models.CharField(max_length=100, blank=True, null=True)
    place_of_supply = models.CharField(max_length=50, null=True, blank=True)
    place_of_supply_formatted = models.CharField(max_length=50, null=True, blank=True)
    payment_terms = models.IntegerField(null=True, blank=True)
    payment_terms_label = models.CharField(max_length=100, null=True, blank=True)
    payment_reminder_enabled = models.BooleanField(default=False)
    payment_made = models.DecimalField(
        max_digits=15, decimal_places=2, null=True, blank=True
    )
    payment_made_formatted = models.CharField(max_length=20, null=True, blank=True)
    crm_owner_id = models.CharField(max_length=100, blank=True, null=True)
    crm_custom_reference_id = models.CharField(max_length=100, blank=True, null=True)
    zcrm_potential_id = models.CharField(max_length=100, blank=True, null=True)
    zcrm_potential_name = models.CharField(max_length=255, blank=True, null=True)
    next_retry_date = models.CharField(max_length=100, blank=True, null=True)
    next_retry_date_formatted = models.CharField(max_length=20, blank=True, null=True)
    next_retry_number = models.IntegerField(default=0)
    reference_number = models.CharField(max_length=255, null=True, blank=True)
    is_inventory_valuation_pending = models.BooleanField(default=False)
    due_days = models.CharField(max_length=100, blank=True, null=True)
    lock_details = models.JSONField(default=dict, null=True, blank=True)
    credits = models.JSONField(default=list, null=True, blank=True)
    journal_credits = models.JSONField(default=list, null=True, blank=True)
    exchange_rate = models.DecimalField(
        max_digits=15, decimal_places=6, null=True, blank=True
    )
    is_autobill_enabled = models.BooleanField(default=False)
    inprocess_transaction_present = models.BooleanField(default=False)
    allow_partial_payments = models.BooleanField(default=False)
    price_precision = models.IntegerField(null=True, blank=True)
    sub_total = models.DecimalField(
        max_digits=15, decimal_places=2, null=True, blank=True
    )
    sub_total_formatted = models.CharField(max_length=20, null=True, blank=True)
    tax_total = models.DecimalField(
        max_digits=15, decimal_places=2, null=True, blank=True
    )
    tax_total_formatted = models.CharField(max_length=20, null=True, blank=True)
    discount_total = models.DecimalField(
        max_digits=15, decimal_places=2, null=True, blank=True
    )
    discount_total_formatted = models.CharField(max_length=20, null=True, blank=True)
    discount_percent = models.DecimalField(
        max_digits=10, decimal_places=6, null=True, blank=True
    )
    discount = models.DecimalField(
        max_digits=15, decimal_places=2, null=True, blank=True
    )
    discount_applied_on_amount = models.DecimalField(
        max_digits=15, decimal_places=2, null=True, blank=True
    )
    discount_type = models.CharField(max_length=20, null=True, blank=True)
    tds_override_preference = models.CharField(max_length=50, null=True, blank=True)
    is_discount_before_tax = models.BooleanField(default=True)
    adjustment = models.DecimalField(
        max_digits=15, decimal_places=2, null=True, blank=True
    )
    adjustment_formatted = models.CharField(max_length=20, null=True, blank=True)
    adjustment_description = models.CharField(max_length=255, null=True, blank=True)
    shipping_charge_tax_id = models.CharField(max_length=100, blank=True, null=True)
    shipping_charge_tax_name = models.CharField(max_length=255, blank=True, null=True)
    shipping_charge_tax_type = models.CharField(max_length=50, blank=True, null=True)
    shipping_charge_tax_percentage = models.CharField(
        max_length=10, blank=True, null=True
    )
    shipping_charge_tax_exemption_id = models.CharField(
        max_length=100, blank=True, null=True
    )
    shipping_charge_tax_exemption_code = models.CharField(
        max_length=50, blank=True, null=True
    )
    shipping_charge_sac_code = models.CharField(max_length=50, blank=True, null=True)
    shipping_charge_tax = models.CharField(max_length=50, blank=True, null=True)
    bcy_shipping_charge_tax = models.CharField(max_length=50, blank=True, null=True)
    shipping_charge_exclusive_of_tax = models.DecimalField(
        max_digits=15, decimal_places=2, null=True, blank=True
    )
    shipping_charge_inclusive_of_tax = models.DecimalField(
        max_digits=15, decimal_places=2, null=True, blank=True
    )
    shipping_charge_tax_formatted = models.CharField(
        max_length=20, blank=True, null=True
    )
    shipping_charge_exclusive_of_tax_formatted = models.CharField(
        max_length=20, null=True, blank=True
    )
    shipping_charge_inclusive_of_tax_formatted = models.CharField(
        max_length=20, null=True, blank=True
    )
    shipping_charge = models.DecimalField(
        max_digits=15, decimal_places=2, null=True, blank=True
    )
    shipping_charge_formatted = models.CharField(max_length=20, null=True, blank=True)
    bcy_shipping_charge = models.DecimalField(
        max_digits=15, decimal_places=2, null=True, blank=True
    )
    bcy_adjustment = models.DecimalField(
        max_digits=15, decimal_places=2, null=True, blank=True
    )
    bcy_sub_total = models.DecimalField(
        max_digits=15, decimal_places=2, null=True, blank=True
    )
    bcy_discount_total = models.DecimalField(
        max_digits=15, decimal_places=2, null=True, blank=True
    )
    bcy_tax_total = models.DecimalField(
        max_digits=15, decimal_places=2, null=True, blank=True
    )
    bcy_total = models.DecimalField(
        max_digits=15, decimal_places=2, null=True, blank=True
    )
    is_reverse_charge_applied = models.BooleanField(default=False)
    total = models.DecimalField(max_digits=15, decimal_places=2, null=True, blank=True)
    total_formatted = models.CharField(max_length=20, null=True, blank=True)
    balance = models.DecimalField(
        max_digits=15, decimal_places=2, null=True, blank=True
    )
    balance_formatted = models.CharField(max_length=20, null=True, blank=True)
    write_off_amount = models.DecimalField(
        max_digits=15, decimal_places=2, null=True, blank=True
    )
    write_off_amount_formatted = models.CharField(max_length=20, null=True, blank=True)
    roundoff_value = models.DecimalField(
        max_digits=15, decimal_places=2, null=True, blank=True
    )
    roundoff_value_formatted = models.CharField(max_length=20, null=True, blank=True)
    transaction_rounding_type = models.CharField(max_length=20, null=True, blank=True)
    reference_invoice_type = models.CharField(max_length=100, null=True, blank=True)
    is_inclusive_tax = models.BooleanField(default=False)
    sub_total_inclusive_of_tax = models.DecimalField(
        max_digits=15, decimal_places=2, null=True, blank=True
    )
    sub_total_inclusive_of_tax_formatted = models.CharField(
        max_length=20, null=True, blank=True
    )
    tax_specification = models.CharField(max_length=50, null=True, blank=True)
    gst_no = models.CharField(max_length=50, null=True, blank=True)
    gst_treatment = models.CharField(max_length=50, null=True, blank=True)
    gst_treatment_formatted = models.CharField(max_length=50, null=True, blank=True)
    tax_reg_no = models.CharField(max_length=50, null=True, blank=True)
    contact_category = models.CharField(max_length=50, null=True, blank=True)
    tax_treatment = models.CharField(max_length=50, null=True, blank=True)
    tax_treatment_formatted = models.CharField(max_length=50, null=True, blank=True)
    tax_rounding = models.CharField(max_length=50, null=True, blank=True)
    taxes = models.JSONField(default=list, null=True, blank=True)
    filed_in_vat_return_id = models.CharField(max_length=100, null=True, blank=True)
    filed_in_vat_return_name = models.CharField(max_length=100, null=True, blank=True)
    filed_in_vat_return_type = models.CharField(max_length=100, null=True, blank=True)
    gst_return_details = models.JSONField(default=dict, null=True, blank=True)
    reverse_charge_tax_total = models.DecimalField(
        max_digits=15, decimal_places=2, null=True, blank=True
    )
    reverse_charge_tax_total_formatted = models.CharField(
        max_length=20, null=True, blank=True
    )
    tds_calculation_type = models.CharField(max_length=50, null=True, blank=True)
    can_send_invoice_sms = models.BooleanField(default=False)
    payment_expected_date = models.CharField(max_length=100, null=True, blank=True)
    payment_expected_date_formatted = models.CharField(
        max_length=20, null=True, blank=True
    )
    payment_discount = models.DecimalField(
        max_digits=15, decimal_places=2, null=True, blank=True
    )
    payment_discount_formatted = models.CharField(max_length=20, null=True, blank=True)
    stop_reminder_until_payment_expected_date = models.BooleanField(default=False)
    last_payment_date = models.CharField(max_length=100, null=True, blank=True)
    last_payment_date_formatted = models.CharField(max_length=20, null=True, blank=True)
    autobill_status = models.CharField(max_length=50, null=True, blank=True)
    autobill_status_formatted = models.CharField(max_length=50, null=True, blank=True)
    ach_supported = models.BooleanField(default=False)
    ach_payment_initiated = models.BooleanField(default=False)
    payment_options = models.JSONField(default=dict, null=True, blank=True)
    payments = models.JSONField(default=list, null=True, blank=True)
    reader_offline_payment_initiated = models.BooleanField(default=False)
    is_square_transaction = models.BooleanField(default=False)
    contact_persons = models.JSONField(default=list, null=True, blank=True)
    contact_persons_associated = models.JSONField(default=list, null=True, blank=True)
    attachment_name = models.CharField(max_length=255, null=True, blank=True)
    documents = models.JSONField(default=list, null=True, blank=True)
    computation_type = models.CharField(max_length=20, null=True, blank=True)
    tds_summary = models.JSONField(default=list, null=True, blank=True)
    debit_notes = models.JSONField(default=list, null=True, blank=True)
    deliverychallans = models.JSONField(default=list, null=True, blank=True)
    bills = models.JSONField(default=list, null=True, blank=True)
    ewaybills = models.JSONField(default=list, null=True, blank=True)
    dispatch_from_address = models.JSONField(default=dict, null=True, blank=True)
    is_eway_bill_required = models.BooleanField(default=False)
    can_generate_ewaybill_using_irn = models.BooleanField(default=True)
    branch_id = models.CharField(max_length=100, null=True, blank=True)
    branch_name = models.CharField(max_length=255, null=True, blank=True)
    merchant_id = models.CharField(max_length=100, null=True, blank=True)
    merchant_name = models.CharField(max_length=255, null=True, blank=True)
    merchant_gst_no = models.CharField(max_length=50, null=True, blank=True)
    ecomm_operator_id = models.CharField(max_length=100, null=True, blank=True)
    ecomm_operator_name = models.CharField(max_length=255, null=True, blank=True)
    ecomm_operator_gst_no = models.CharField(max_length=50, null=True, blank=True)
    salesorder_id = models.CharField(max_length=100, null=True, blank=True)
    salesorder_number = models.CharField(max_length=255, null=True, blank=True)
    salesorders = models.JSONField(default=list, null=True, blank=True)
    shipping_bills = models.JSONField(default=list, null=True, blank=True)
    unbilled_expenses_count = models.IntegerField(default=0, null=True, blank=True)
    unbilled_bill_items_count = models.IntegerField(default=0, null=True, blank=True)
    has_timesheet_entries = models.BooleanField(default=False)
    is_associated_with_project = models.BooleanField(default=False)
    warn_convert_to_open = models.BooleanField(default=True)
    warn_create_creditnotes = models.BooleanField(default=False)
    contact_persons_details = models.JSONField(default=list, null=True, blank=True)
    contact = models.JSONField(default=dict, null=True, blank=True)
    salesperson_id = models.CharField(max_length=100, null=True, blank=True)
    salesperson_name = models.CharField(max_length=255, null=True, blank=True)
    is_emailed = models.BooleanField(default=False)
    reminders_sent = models.IntegerField(default=0)
    last_reminder_sent_date = models.CharField(max_length=100, null=True, blank=True)
    last_reminder_sent_date_formatted = models.CharField(
        max_length=20, null=True, blank=True
    )
    next_reminder_date_formatted = models.CharField(
        max_length=20, null=True, blank=True
    )
    is_portal_enabled = models.BooleanField(default=False)
    is_viewed_by_client = models.BooleanField(default=False)
    client_viewed_time = models.CharField(max_length=100, null=True, blank=True)
    client_viewed_time_formatted = models.CharField(
        max_length=20, null=True, blank=True
    )
    submitter_id = models.CharField(max_length=100, null=True, blank=True)
    approver_id = models.CharField(max_length=100, null=True, blank=True)
    submitted_date = models.CharField(max_length=100, null=True, blank=True)
    submitted_date_formatted = models.CharField(max_length=20, null=True, blank=True)
    submitted_by = models.CharField(max_length=100, null=True, blank=True)
    submitted_by_name = models.CharField(max_length=255, null=True, blank=True)
    submitted_by_email = models.EmailField(null=True, blank=True)
    submitted_by_photo_url = models.CharField(max_length=255, null=True, blank=True)
    template_id = models.CharField(max_length=100, null=True, blank=True)
    template_name = models.CharField(max_length=255, null=True, blank=True)
    template_type = models.CharField(max_length=20, null=True, blank=True)
    template_type_formatted = models.CharField(max_length=20, null=True, blank=True)
    notes = models.TextField(null=True, blank=True)
    terms = models.TextField(null=True, blank=True)
    billing_address = models.JSONField(default=dict, null=True, blank=True)
    shipping_address = models.JSONField(default=dict, null=True, blank=True)
    einvoice_details = models.JSONField(default=dict, null=True, blank=True)
    invoice_url = models.CharField(max_length=255, null=True, blank=True)
    subject_content = models.TextField(null=True, blank=True)
    can_send_in_mail = models.BooleanField(default=False)
    created_time = models.DateTimeField(null=True, blank=True)
    last_modified_time = models.DateTimeField(null=True, blank=True)
    created_date = models.DateField(null=True, blank=True)
    created_date_formatted = models.CharField(max_length=20, null=True, blank=True)
    created_by_id = models.CharField(max_length=100, null=True, blank=True)
    created_by_name = models.CharField(max_length=255, null=True, blank=True)
    last_modified_by_id = models.CharField(max_length=100, null=True, blank=True)
    page_width = models.CharField(max_length=20, null=True, blank=True)
    page_height = models.CharField(max_length=20, null=True, blank=True)
    orientation = models.CharField(max_length=20, null=True, blank=True)
    is_backorder = models.BooleanField(default=False)
    sales_channel = models.CharField(max_length=50, null=True, blank=True)
    sales_channel_formatted = models.CharField(max_length=50, null=True, blank=True)
    is_pre_gst = models.BooleanField(default=False)
    type_formatted = models.CharField(max_length=50, null=True, blank=True)
    type = models.CharField(max_length=50, null=True, blank=True)
    color_code = models.CharField(max_length=20, null=True, blank=True)
    current_sub_status_id = models.CharField(max_length=100, null=True, blank=True)
    current_sub_status = models.CharField(max_length=50, null=True, blank=True)
    current_sub_status_formatted = models.CharField(
        max_length=50, null=True, blank=True
    )
    sub_statuses = models.JSONField(default=list, null=True, blank=True)
    reason_for_debit_note = models.CharField(max_length=50, null=True, blank=True)
    reason_for_debit_note_formatted = models.CharField(
        max_length=50, null=True, blank=True
    )
    estimate_id = models.CharField(max_length=100, null=True, blank=True)
    is_client_review_settings_enabled = models.BooleanField(default=False)
    is_taxable = models.BooleanField(default=True)
    unused_credits_receivable_amount = models.DecimalField(
        max_digits=15, decimal_places=2, null=True, blank=True
    )
    unused_credits_receivable_amount_formatted = models.CharField(
        max_length=20, null=True, blank=True
    )
    unused_retainer_payments = models.DecimalField(
        max_digits=15, decimal_places=2, null=True, blank=True
    )
    unused_retainer_payments_formatted = models.CharField(
        max_length=20, null=True, blank=True
    )
    credits_applied = models.DecimalField(
        max_digits=15, decimal_places=2, null=True, blank=True
    )
    credits_applied_formatted = models.CharField(max_length=20, null=True, blank=True)
    tax_amount_withheld = models.DecimalField(
        max_digits=15, decimal_places=2, null=True, blank=True
    )
    tax_amount_withheld_formatted = models.CharField(
        max_length=20, null=True, blank=True
    )
    is_cloneable = models.BooleanField(default=True)
    can_send_in_mail_state = models.BooleanField(default=False)
    schedule_time = models.CharField(max_length=100, null=True, blank=True)
    schedule_time_formatted = models.CharField(max_length=20, null=True, blank=True)
    no_of_copies = models.IntegerField(default=1, null=True, blank=True)
    show_no_of_copies = models.BooleanField(default=True)
    auto_reminders_configured = models.BooleanField(default=False)
    customer_default_billing_address = models.JSONField(
        default=dict, null=True, blank=True
    )
    can_send_comment_notification = models.BooleanField(default=False)
    reference_invoice = models.JSONField(default=dict, null=True, blank=True)
    includes_package_tracking_info = models.BooleanField(default=False)
    approvers_list = models.JSONField(default=list, null=True, blank=True)
    qr_code = models.JSONField(default=dict, null=True, blank=True)
    entity = models.ForeignKey(Entity, null=True, on_delete=models.SET_NULL)

    class Meta:
        ordering = ["-created_time"]

    def __str__(self):
        return f"Invoice {self.invoice_number}"


class PurchaseOrderLineItem(models.Model):
    item_id = models.CharField(max_length=100, null=True, blank=True)
    line_item_id = models.CharField(max_length=100, null=True, blank=True)
    salesorder_item_id = models.CharField(max_length=100, null=True, blank=True)
    image_document_id = models.CharField(max_length=100, null=True, blank=True)
    sku = models.CharField(max_length=100, null=True, blank=True)
    account_id = models.CharField(max_length=100, null=True, blank=True)
    account_name = models.CharField(max_length=100, null=True, blank=True)
    name = models.CharField(max_length=100, null=True, blank=True)
    description = models.TextField(blank=True, null=True)
    item_order = models.IntegerField(null=True, blank=True)
    bcy_rate = models.DecimalField(
        max_digits=10, decimal_places=2, null=True, blank=True
    )
    bcy_rate_formatted = models.CharField(max_length=20, null=True, blank=True)
    pricebook_id = models.CharField(max_length=100, null=True, blank=True)
    header_id = models.CharField(max_length=100, null=True, blank=True)
    header_name = models.CharField(max_length=100, null=True, blank=True)
    rate = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    rate_formatted = models.CharField(max_length=20, null=True, blank=True)
    quantity = models.DecimalField(
        max_digits=19, decimal_places=6, blank=True, null=True
    )
    discount = models.DecimalField(
        max_digits=10, decimal_places=2, null=True, blank=True
    )
    discounts = models.JSONField(
        default=list, null=True, blank=True
    )  # New field for discounts
    quantity_cancelled = models.DecimalField(
        max_digits=19, decimal_places=6, blank=True, null=True
    )
    quantity_billed = models.DecimalField(
        max_digits=19, decimal_places=6, blank=True, null=True
    )
    unit = models.CharField(max_length=50, null=True, blank=True)
    item_total = models.DecimalField(
        max_digits=10, decimal_places=2, null=True, blank=True
    )
    item_total_formatted = models.CharField(max_length=20, null=True, blank=True)
    item_total_inclusive_of_tax = models.DecimalField(
        max_digits=10, decimal_places=2, null=True, blank=True
    )
    item_total_inclusive_of_tax_formatted = models.CharField(
        max_length=20, null=True, blank=True
    )
    tax_exemption_id = models.CharField(max_length=100, null=True, blank=True)
    tax_exemption_code = models.CharField(max_length=100, null=True, blank=True)
    gst_treatment_code = models.CharField(max_length=100, null=True, blank=True)
    tax_id = models.CharField(max_length=100, null=True, blank=True)
    tax_name = models.CharField(max_length=100, null=True, blank=True)
    tax_type = models.CharField(max_length=50, null=True, blank=True)
    tax_percentage = models.DecimalField(
        max_digits=5, decimal_places=2, null=True, blank=True
    )
    product_type = models.CharField(max_length=50, null=True, blank=True)
    item_type = models.CharField(max_length=50, null=True, blank=True)
    item_type_formatted = models.CharField(max_length=50, null=True, blank=True)
    line_item_taxes = models.JSONField(default=list, null=True, blank=True)
    hsn_or_sac = models.CharField(max_length=50, null=True, blank=True)
    reverse_charge_tax_id = models.CharField(max_length=100, null=True, blank=True)
    tags = models.JSONField(default=list, null=True, blank=True)
    item_custom_fields = models.JSONField(default=list, null=True, blank=True)
    project_id = models.CharField(max_length=100, null=True, blank=True)
    image_name = models.CharField(max_length=100, null=True, blank=True)
    image_type = models.CharField(max_length=100, null=True, blank=True)
    purchase_request_items = models.JSONField(default=list, null=True, blank=True)

    def __str__(self):
        return self.line_item_id  # or any other field you prefer


class PurchaseOrder(models.Model):
    zoho_vendor = models.ForeignKey(
        ZohoVendor, on_delete=models.SET_NULL, blank=True, null=True, default=None
    )
    po_line_items = models.ManyToManyField(PurchaseOrderLineItem, blank=True)
    purchaseorder_id = models.CharField(max_length=100, null=True, blank=True)
    branch_id = models.CharField(max_length=100, null=True, blank=True)
    branch_name = models.CharField(max_length=100, null=True, blank=True)
    documents = models.JSONField(default=list, null=True, blank=True)
    crm_owner_id = models.CharField(max_length=100, null=True, blank=True)
    crm_custom_reference_id = models.CharField(max_length=100, null=True, blank=True)
    tax_treatment = models.CharField(max_length=100, null=True, blank=True)
    tax_treatment_formatted = models.CharField(max_length=100, null=True, blank=True)
    gst_no = models.CharField(max_length=100, null=True, blank=True)
    contact_category = models.CharField(max_length=100, null=True, blank=True)
    gst_treatment = models.CharField(max_length=100, null=True, blank=True)
    gst_treatment_formatted = models.CharField(max_length=100, null=True, blank=True)
    purchaseorder_number = models.CharField(max_length=100, null=True, blank=True)
    date = models.DateField(null=True, blank=True)
    date_formatted = models.CharField(max_length=20, null=True, blank=True)
    currency_formatter = models.JSONField(null=True, blank=True)
    client_viewed_time = models.CharField(max_length=100, null=True, blank=True)
    client_viewed_time_formatted = models.CharField(
        max_length=100, null=True, blank=True
    )
    is_viewed_by_client = models.BooleanField(default=False)
    is_pre_gst = models.BooleanField(default=False)
    expected_delivery_date = models.CharField(max_length=100, null=True, blank=True)
    expected_delivery_date_formatted = models.CharField(
        max_length=100, null=True, blank=True
    )
    reference_number = models.CharField(max_length=100, null=True, blank=True)
    status = models.CharField(max_length=100, null=True, blank=True)
    status_formatted = models.CharField(max_length=100, null=True, blank=True)
    order_status = models.CharField(max_length=100, null=True, blank=True)
    order_status_formatted = models.CharField(max_length=100, null=True, blank=True)
    billed_status = models.CharField(max_length=100, null=True, blank=True)
    billed_status_formatted = models.CharField(max_length=100, null=True, blank=True)
    color_code = models.CharField(max_length=100, null=True, blank=True)
    current_sub_status_id = models.CharField(max_length=100, null=True, blank=True)
    current_sub_status = models.CharField(max_length=100, null=True, blank=True)
    current_sub_status_formatted = models.CharField(
        max_length=100, null=True, blank=True
    )
    sub_statuses = models.JSONField(default=list, null=True, blank=True)
    source_of_supply = models.CharField(max_length=100, null=True, blank=True)
    source_of_supply_formatted = models.CharField(max_length=100, null=True, blank=True)
    destination_of_supply = models.CharField(max_length=100, null=True, blank=True)
    destination_of_supply_formatted = models.CharField(
        max_length=100, null=True, blank=True
    )
    vendor_id = models.CharField(max_length=100, null=True, blank=True)
    vendor_name = models.CharField(max_length=100, null=True, blank=True)
    is_portal_enabled = models.BooleanField(default=False)
    contact_persons = models.JSONField(default=list, null=True, blank=True)
    currency_id = models.CharField(max_length=100, null=True, blank=True)
    currency_code = models.CharField(max_length=10, null=True, blank=True)
    currency_symbol = models.CharField(max_length=10, null=True, blank=True)
    exchange_rate = models.DecimalField(
        max_digits=15, decimal_places=6, null=True, blank=True
    )
    delivery_date = models.CharField(max_length=100, null=True, blank=True)
    delivery_date_formatted = models.CharField(max_length=100, null=True, blank=True)
    is_emailed = models.BooleanField(default=False)
    show_convert_to_bill = models.BooleanField(default=True)
    is_inclusive_tax = models.BooleanField(default=False)
    tax_rounding = models.CharField(max_length=100, null=True, blank=True)
    is_reverse_charge_applied = models.BooleanField(default=False)
    is_adv_tracking_in_receive = models.BooleanField(default=False)
    salesorder_id = models.CharField(max_length=100, null=True, blank=True)
    total_quantity = models.DecimalField(
        max_digits=10, decimal_places=2, null=True, blank=True
    )
    total_quantity_formatted = models.CharField(max_length=20, null=True, blank=True)
    tds_calculation_type = models.CharField(max_length=100, null=True, blank=True)
    has_qty_cancelled = models.BooleanField(default=False)
    adjustment = models.DecimalField(
        max_digits=10, decimal_places=2, null=True, blank=True
    )
    adjustment_formatted = models.CharField(max_length=20, null=True, blank=True)
    adjustment_description = models.CharField(max_length=100, null=True, blank=True)
    discount_amount_formatted = models.CharField(max_length=20, null=True, blank=True)
    discount_amount = models.DecimalField(
        max_digits=10, decimal_places=2, null=True, blank=True
    )
    discount = models.DecimalField(
        max_digits=10, decimal_places=2, null=True, blank=True
    )
    discount_applied_on_amount_formatted = models.CharField(
        max_length=20, null=True, blank=True
    )
    discount_applied_on_amount = models.DecimalField(
        max_digits=10, decimal_places=2, null=True, blank=True
    )
    is_discount_before_tax = models.BooleanField(default=True)
    discount_account_id = models.CharField(max_length=100, null=True, blank=True)
    discount_type = models.CharField(max_length=100, null=True, blank=True)
    sub_total = models.DecimalField(
        max_digits=10, decimal_places=2, null=True, blank=True
    )
    sub_total_formatted = models.CharField(max_length=20, null=True, blank=True)
    sub_total_inclusive_of_tax = models.DecimalField(
        max_digits=10, decimal_places=2, null=True, blank=True
    )
    sub_total_inclusive_of_tax_formatted = models.CharField(
        max_length=20, null=True, blank=True
    )
    tax_total = models.DecimalField(
        max_digits=10, decimal_places=2, null=True, blank=True
    )
    tax_total_formatted = models.CharField(max_length=20, null=True, blank=True)
    total = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    total_formatted = models.CharField(max_length=20, null=True, blank=True)
    taxes = models.JSONField(default=list, null=True, blank=True)
    tax_override = models.BooleanField(default=False)
    tds_override_preference = models.CharField(max_length=100, null=True, blank=True)
    tds_summary = models.JSONField(default=list, null=True, blank=True)
    price_precision = models.IntegerField(null=True, blank=True)
    submitted_date = models.CharField(max_length=100, null=True, blank=True)
    submitted_date_formatted = models.CharField(max_length=100, null=True, blank=True)
    submitted_by = models.CharField(max_length=100, null=True, blank=True)
    submitted_by_name = models.CharField(max_length=100, null=True, blank=True)
    submitted_by_email = models.CharField(max_length=100, null=True, blank=True)
    submitted_by_photo_url = models.CharField(max_length=100, null=True, blank=True)
    submitter_id = models.CharField(max_length=100, null=True, blank=True)
    approver_id = models.CharField(max_length=100, null=True, blank=True)
    approvers_list = models.JSONField(default=list, null=True, blank=True)
    billing_address_id = models.CharField(max_length=100, null=True, blank=True)
    billing_address = models.JSONField(null=True, blank=True)
    notes = models.TextField(null=True, blank=True)
    terms = models.TextField(null=True, blank=True)
    payment_terms = models.IntegerField(null=True, blank=True)
    payment_terms_label = models.CharField(max_length=100, null=True, blank=True)
    ship_via = models.CharField(max_length=100, null=True, blank=True)
    ship_via_id = models.CharField(max_length=100, null=True, blank=True)
    attention = models.CharField(max_length=100, null=True, blank=True)
    delivery_org_address_id = models.CharField(max_length=100, null=True, blank=True)
    delivery_customer_id = models.CharField(max_length=100, null=True, blank=True)
    delivery_customer_address_id = models.CharField(
        max_length=100, null=True, blank=True
    )
    delivery_address = models.JSONField(null=True, blank=True)
    custom_fields = models.JSONField(default=list, null=True, blank=True)
    custom_field_hash = models.JSONField(null=True, blank=True)
    attachment_name = models.CharField(max_length=100, null=True, blank=True)
    can_send_in_mail = models.BooleanField(default=False)
    template_id = models.CharField(max_length=100, null=True, blank=True)
    template_name = models.CharField(max_length=100, null=True, blank=True)
    page_width = models.CharField(max_length=100, null=True, blank=True)
    page_height = models.CharField(max_length=100, null=True, blank=True)
    orientation = models.CharField(max_length=100, null=True, blank=True)
    template_type = models.CharField(max_length=100, null=True, blank=True)
    template_type_formatted = models.CharField(max_length=100, null=True, blank=True)
    created_time = models.DateTimeField(null=True, blank=True)
    created_by_id = models.CharField(max_length=100, null=True, blank=True)
    last_modified_time = models.DateTimeField(null=True, blank=True)
    can_mark_as_bill = models.BooleanField(default=False)
    can_mark_as_unbill = models.BooleanField(default=False)
    salesorders = models.JSONField(default=list, null=True, blank=True)
    bills = models.JSONField(default=list, null=True, blank=True)
    is_guest_ctt = models.BooleanField(default=False)
    po_type = models.CharField(max_length=225, null=True, blank=True)
    is_billed_to_client = models.BooleanField(default=False)
    entity = models.ForeignKey(
        Entity,
        null=True,
        on_delete=models.SET_NULL,
    )

    class Meta:
        ordering = ["-created_time"]

    def __str__(self):
        return self.purchaseorder_number


class BillLineItem(models.Model):
    purchaseorder_item_id = models.CharField(max_length=100, null=True, blank=True)
    line_item_id = models.CharField(max_length=100, null=True, blank=True)
    item_id = models.CharField(max_length=100, null=True, blank=True)
    itc_eligibility = models.CharField(max_length=100, null=True, blank=True)
    gst_treatment_code = models.CharField(max_length=100, null=True, blank=True)
    image_document_id = models.CharField(max_length=100, null=True, blank=True)
    sku = models.CharField(max_length=100, null=True, blank=True)
    name = models.CharField(max_length=100, null=True, blank=True)
    account_id = models.CharField(max_length=100, null=True, blank=True)
    account_name = models.CharField(max_length=100, null=True, blank=True)
    description = models.TextField(null=True, blank=True)
    bcy_rate = models.DecimalField(
        max_digits=10, decimal_places=2, null=True, blank=True
    )
    bcy_rate_formatted = models.CharField(max_length=20, null=True, blank=True)
    rate = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    rate_formatted = models.CharField(max_length=20, null=True, blank=True)
    pricebook_id = models.CharField(max_length=100, null=True, blank=True)
    header_id = models.CharField(max_length=100, null=True, blank=True)
    header_name = models.CharField(max_length=100, null=True, blank=True)
    tags = models.JSONField(default=list, null=True, blank=True)
    quantity = models.DecimalField(
        max_digits=19, decimal_places=6, blank=True, null=True
    )
    discount = models.DecimalField(
        max_digits=10, decimal_places=2, null=True, blank=True
    )
    discounts = models.JSONField(default=list, null=True, blank=True)
    markup_percent = models.DecimalField(
        max_digits=10, decimal_places=2, null=True, blank=True
    )
    markup_percent_formatted = models.CharField(max_length=20, null=True, blank=True)
    tax_id = models.CharField(max_length=100, null=True, blank=True)
    tax_exemption_id = models.CharField(max_length=100, null=True, blank=True)
    tax_exemption_code = models.CharField(max_length=100, null=True, blank=True)
    tax_name = models.CharField(max_length=100, null=True, blank=True)
    tax_type = models.CharField(max_length=50, null=True, blank=True)
    tax_percentage = models.DecimalField(
        max_digits=5, decimal_places=2, null=True, blank=True
    )
    line_item_taxes = models.JSONField(default=list, null=True, blank=True)
    item_total = models.DecimalField(
        max_digits=10, decimal_places=2, null=True, blank=True
    )
    item_total_formatted = models.CharField(max_length=20, null=True, blank=True)
    item_total_inclusive_of_tax = models.DecimalField(
        max_digits=10, decimal_places=2, null=True, blank=True
    )
    item_total_inclusive_of_tax_formatted = models.CharField(
        max_length=20, null=True, blank=True
    )
    item_order = models.IntegerField(null=True, blank=True)
    unit = models.CharField(max_length=50, null=True, blank=True)
    product_type = models.CharField(max_length=50, null=True, blank=True)
    item_type = models.CharField(max_length=50, null=True, blank=True)
    item_type_formatted = models.CharField(max_length=50, null=True, blank=True)
    has_product_type_mismatch = models.BooleanField(default=False)
    hsn_or_sac = models.CharField(max_length=50, null=True, blank=True)
    reverse_charge_tax_id = models.CharField(max_length=100, null=True, blank=True)
    image_name = models.CharField(max_length=100, null=True, blank=True)
    image_type = models.CharField(max_length=100, null=True, blank=True)
    is_billable = models.BooleanField(default=False)
    customer_id = models.CharField(max_length=100, null=True, blank=True)
    customer_name = models.CharField(max_length=100, null=True, blank=True)
    project_id = models.CharField(max_length=100, null=True, blank=True)
    project_name = models.CharField(max_length=100, null=True, blank=True)
    invoice_id = models.CharField(max_length=100, null=True, blank=True)
    invoice_number = models.CharField(max_length=100, null=True, blank=True)
    item_custom_fields = models.JSONField(default=list, null=True, blank=True)
    purchase_request_items = models.JSONField(default=list, null=True, blank=True)

    def __str__(self):
        return self.line_item_id


class Bill(models.Model):
    zoho_vendor = models.ForeignKey(
        ZohoVendor, on_delete=models.SET_NULL, blank=True, null=True, default=None
    )
    purchase_orders = models.ManyToManyField(PurchaseOrder, blank=True)
    bill_line_items = models.ManyToManyField(BillLineItem, blank=True)
    bill_id = models.CharField(max_length=100, blank=True, null=True)
    branch_id = models.CharField(max_length=100, blank=True, null=True)
    branch_name = models.CharField(max_length=100, blank=True, null=True)
    purchaseorder_ids = models.JSONField(default=list, blank=True, null=True)
    vendor_id = models.CharField(max_length=100, blank=True, null=True)
    vendor_name = models.CharField(max_length=100, blank=True, null=True)
    source = models.CharField(max_length=100, blank=True, null=True)
    source_of_supply = models.CharField(max_length=100, blank=True, null=True)
    source_of_supply_formatted = models.CharField(max_length=100, blank=True, null=True)
    destination_of_supply = models.CharField(max_length=100, blank=True, null=True)
    destination_of_supply_formatted = models.CharField(
        max_length=100, blank=True, null=True
    )
    can_amend_transaction = models.BooleanField(default=False)
    gst_no = models.CharField(max_length=100, blank=True, null=True)
    reference_invoice_type = models.CharField(max_length=100, blank=True, null=True)
    contact_category = models.CharField(max_length=100, blank=True, null=True)
    gst_treatment = models.CharField(max_length=100, blank=True, null=True)
    gst_treatment_formatted = models.CharField(max_length=100, blank=True, null=True)
    tax_treatment = models.CharField(max_length=100, blank=True, null=True)
    tax_treatment_formatted = models.CharField(max_length=100, blank=True, null=True)
    gst_return_details = models.JSONField(default=dict, blank=True, null=True)
    invoice_conversion_type = models.CharField(max_length=100, blank=True, null=True)
    unused_credits_payable_amount = models.DecimalField(
        max_digits=10, decimal_places=2, blank=True, null=True
    )
    unused_credits_payable_amount_formatted = models.CharField(
        max_length=20, blank=True, null=True
    )
    status = models.CharField(max_length=100, blank=True, null=True)
    status_formatted = models.CharField(max_length=100, blank=True, null=True)
    color_code = models.CharField(max_length=100, blank=True, null=True)
    current_sub_status_id = models.CharField(max_length=100, blank=True, null=True)
    current_sub_status = models.CharField(max_length=100, blank=True, null=True)
    current_sub_status_formatted = models.CharField(
        max_length=100, blank=True, null=True
    )
    sub_statuses = models.JSONField(default=list, blank=True, null=True)
    bill_number = models.CharField(max_length=100, blank=True, null=True)
    date = models.DateField(blank=True, null=True)
    date_formatted = models.CharField(max_length=100, blank=True, null=True)
    is_pre_gst = models.BooleanField(default=False)
    due_date = models.DateField(blank=True, null=True)
    due_date_formatted = models.CharField(max_length=100, blank=True, null=True)
    discount_setting = models.CharField(max_length=100, blank=True, null=True)
    tds_calculation_type = models.CharField(max_length=100, blank=True, null=True)
    is_tds_amount_in_percent = models.BooleanField(default=True)
    tds_percent_formatted = models.CharField(max_length=100, blank=True, null=True)
    tds_percent = models.DecimalField(
        max_digits=5, decimal_places=2, blank=True, null=True
    )
    tds_amount_formatted = models.CharField(max_length=20, blank=True, null=True)
    tds_amount = models.DecimalField(
        max_digits=10, decimal_places=2, blank=True, null=True
    )
    tax_account_id = models.CharField(max_length=100, blank=True, null=True)
    tds_tax_id = models.CharField(max_length=100, blank=True, null=True)
    tds_tax_name = models.CharField(max_length=100, blank=True, null=True)
    tds_section_formatted = models.CharField(max_length=100, blank=True, null=True)
    tds_section = models.CharField(max_length=100, blank=True, null=True)
    payment_terms = models.IntegerField(blank=True, null=True)
    payment_terms_label = models.CharField(max_length=100, blank=True, null=True)
    payment_expected_date = models.DateField(blank=True, null=True)
    payment_expected_date_formatted = models.CharField(
        max_length=100, blank=True, null=True
    )
    reference_number = models.CharField(max_length=100, blank=True, null=True)
    recurring_bill_id = models.CharField(max_length=100, blank=True, null=True)
    due_by_days = models.IntegerField(blank=True, null=True)
    due_in_days = models.CharField(max_length=100, blank=True, null=True)
    due_days = models.CharField(max_length=100, blank=True, null=True)
    currency_id = models.CharField(max_length=100, blank=True, null=True)
    currency_code = models.CharField(max_length=100, blank=True, null=True)
    currency_symbol = models.CharField(max_length=100, blank=True, null=True)
    currency_name_formatted = models.CharField(max_length=100, blank=True, null=True)
    documents = models.JSONField(default=list, blank=True, null=True)
    subject_content = models.CharField(max_length=100, blank=True, null=True)
    price_precision = models.IntegerField(blank=True, null=True)
    exchange_rate = models.DecimalField(
        max_digits=15, decimal_places=6, blank=True, null=True
    )
    custom_fields = models.JSONField(default=list, blank=True, null=True)
    custom_field_hash = models.JSONField(default=dict, blank=True, null=True)
    is_viewed_by_client = models.BooleanField(default=False)
    client_viewed_time = models.CharField(max_length=100, blank=True, null=True)
    client_viewed_time_formatted = models.CharField(
        max_length=100, blank=True, null=True
    )
    is_item_level_tax_calc = models.BooleanField(default=False)
    is_inclusive_tax = models.BooleanField(default=False)
    tax_rounding = models.CharField(max_length=100, blank=True, null=True)
    filed_in_vat_return_id = models.CharField(max_length=100, blank=True, null=True)
    filed_in_vat_return_name = models.CharField(max_length=100, blank=True, null=True)
    filed_in_vat_return_type = models.CharField(max_length=100, blank=True, null=True)
    is_reverse_charge_applied = models.BooleanField(default=False)
    is_uber_bill = models.BooleanField(default=False)
    is_tally_bill = models.BooleanField(default=False)
    track_discount_in_account = models.BooleanField(default=True)
    is_bill_reconciliation_violated = models.BooleanField(default=False)
    submitted_date = models.CharField(max_length=100, blank=True, null=True)
    submitted_date_formatted = models.CharField(max_length=100, blank=True, null=True)
    submitted_by = models.CharField(max_length=100, blank=True, null=True)
    submitted_by_name = models.CharField(max_length=100, blank=True, null=True)
    submitted_by_email = models.CharField(max_length=100, blank=True, null=True)
    submitted_by_photo_url = models.CharField(max_length=100, blank=True, null=True)
    submitter_id = models.CharField(max_length=100, blank=True, null=True)
    approver_id = models.CharField(max_length=100, blank=True, null=True)
    adjustment = models.DecimalField(
        max_digits=10, decimal_places=2, blank=True, null=True
    )
    adjustment_formatted = models.CharField(max_length=100, blank=True, null=True)
    adjustment_description = models.CharField(max_length=100, blank=True, null=True)
    discount_amount_formatted = models.CharField(max_length=100, blank=True, null=True)
    discount_amount = models.DecimalField(
        max_digits=10, decimal_places=2, blank=True, null=True
    )
    discount = models.DecimalField(
        max_digits=10, decimal_places=2, blank=True, null=True
    )
    discount_applied_on_amount_formatted = models.CharField(
        max_length=100, blank=True, null=True
    )
    discount_applied_on_amount = models.DecimalField(
        max_digits=10, decimal_places=2, blank=True, null=True
    )
    is_discount_before_tax = models.BooleanField(default=True)
    discount_account_id = models.CharField(max_length=100, blank=True, null=True)
    discount_account_name = models.CharField(max_length=100, blank=True, null=True)
    discount_type = models.CharField(max_length=100, blank=True, null=True)
    sub_total = models.DecimalField(
        max_digits=10, decimal_places=2, blank=True, null=True
    )
    sub_total_formatted = models.CharField(max_length=100, blank=True, null=True)
    sub_total_inclusive_of_tax = models.DecimalField(
        max_digits=10, decimal_places=2, blank=True, null=True
    )
    sub_total_inclusive_of_tax_formatted = models.CharField(
        max_length=100, blank=True, null=True
    )
    tax_total = models.DecimalField(
        max_digits=10, decimal_places=2, blank=True, null=True
    )
    tax_total_formatted = models.CharField(max_length=100, blank=True, null=True)
    total = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)
    total_formatted = models.CharField(max_length=100, blank=True, null=True)
    payment_made = models.DecimalField(
        max_digits=10, decimal_places=2, blank=True, null=True
    )
    payment_made_formatted = models.CharField(max_length=100, blank=True, null=True)
    vendor_credits_applied = models.DecimalField(
        max_digits=10, decimal_places=2, blank=True, null=True
    )
    vendor_credits_applied_formatted = models.CharField(
        max_length=100, blank=True, null=True
    )
    is_line_item_invoiced = models.BooleanField(default=False)
    purchaseorders = models.JSONField(default=list, blank=True, null=True)
    taxes = models.JSONField(default=list, blank=True, null=True)
    tax_override = models.BooleanField(default=False)
    tds_override_preference = models.CharField(max_length=100, blank=True, null=True)
    tds_summary = models.JSONField(default=list, blank=True, null=True)
    balance = models.DecimalField(
        max_digits=10, decimal_places=2, blank=True, null=True
    )
    balance_formatted = models.CharField(max_length=100, blank=True, null=True)
    unprocessed_payment_amount = models.DecimalField(
        max_digits=10, decimal_places=2, blank=True, null=True
    )
    unprocessed_payment_amount_formatted = models.CharField(
        max_length=100, blank=True, null=True
    )
    billing_address = models.JSONField(default=dict, blank=True, null=True)
    is_portal_enabled = models.BooleanField(default=False)
    payments = models.JSONField(default=list, blank=True, null=True)
    vendor_credits = models.JSONField(default=list, blank=True, null=True)
    journal_credits = models.JSONField(default=list, blank=True, null=True)
    created_time = models.DateTimeField(blank=True, null=True)
    created_by_id = models.CharField(max_length=100, blank=True, null=True)
    last_modified_id = models.CharField(max_length=100, blank=True, null=True)
    last_modified_time = models.DateTimeField(blank=True, null=True)
    warn_create_vendor_credits = models.BooleanField(default=True)
    reference_id = models.CharField(max_length=100, blank=True, null=True)
    notes = models.TextField(blank=True, null=True)
    terms = models.TextField(blank=True, null=True)
    attachment_name = models.CharField(max_length=100, blank=True, null=True)
    open_purchaseorders_count = models.IntegerField(blank=True, null=True)
    un_billed_items = models.JSONField(default=dict, blank=True, null=True)
    template_id = models.CharField(max_length=100, blank=True, null=True)
    template_name = models.CharField(max_length=100, blank=True, null=True)
    page_width = models.CharField(max_length=100, blank=True, null=True)
    page_height = models.CharField(max_length=100, blank=True, null=True)
    orientation = models.CharField(max_length=100, blank=True, null=True)
    template_type = models.CharField(max_length=100, blank=True, null=True)
    template_type_formatted = models.CharField(max_length=100, blank=True, null=True)
    invoices = models.JSONField(default=list, blank=True, null=True)
    is_approval_required = models.BooleanField(default=False)
    can_create_bill_of_entry = models.BooleanField(default=False)
    allocated_landed_costs = models.JSONField(default=list, blank=True, null=True)
    unallocated_landed_costs = models.JSONField(default=list, blank=True, null=True)
    entity_type = models.CharField(max_length=100, blank=True, null=True)
    credit_notes = models.JSONField(default=list, blank=True, null=True)
    reference_bill_id = models.CharField(max_length=100, blank=True, null=True)
    can_send_in_mail = models.BooleanField(default=False)
    approvers_list = models.JSONField(default=list, blank=True, null=True)
    entity = models.ForeignKey(
        Entity,
        null=True,
        on_delete=models.SET_NULL,
    )

    class Meta:
        ordering = ["-created_time"]

    def __str__(self):
        return f"{self.bill_id} -> {self.vendor_name}"


class Company(models.Model):
    """Model to represent company data as received from Zoho."""

    account_name = models.CharField(max_length=255)
    description = models.TextField(null=True, blank=True)
    currency_symbol = models.CharField(max_length=10, default="Rs.")
    website = models.URLField(null=True, blank=True)
    phone = models.CharField(max_length=20, null=True, blank=True)
    billing_country = models.CharField(max_length=100, null=True, blank=True)
    billing_street = models.TextField(null=True, blank=True)
    billing_city = models.CharField(max_length=100, null=True, blank=True)
    billing_state = models.CharField(max_length=100, null=True, blank=True)
    billing_code = models.CharField(max_length=20, null=True, blank=True)
    last_activity_time = models.DateTimeField(null=True, blank=True)
    record_image = models.URLField(null=True, blank=True)
    locked_for_me = models.BooleanField(default=False)
    account_id = models.CharField(max_length=50, unique=True)  # ID from Zoho
    zia_visions = models.TextField(null=True, blank=True)
    modified_time = models.DateTimeField()
    created_time = models.DateTimeField()
    followed = models.BooleanField(default=False)
    editable = models.BooleanField(default=True)
    zia_owner_assignment = models.CharField(max_length=100, null=True, blank=True)
    approval_state = models.CharField(max_length=50, default="approved")
    industry = models.TextField(null=True, blank=True)
    headquarters = models.TextField(null=True, blank=True)
    revenue = models.IntegerField(blank=True, null=True)
    employee_count = models.IntegerField(blank=True, null=True)
    owner = models.JSONField(default=dict, blank=True, null=True)
    modified_by = models.JSONField(default=dict, blank=True, null=True)
    created_by = models.JSONField(default=dict, blank=True, null=True)
    is_deleted = models.BooleanField(default=False)
    tags = models.JSONField(default=list)
    added_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)

    def __str__(self):
        return self.account_name


class Contact(models.Model):

    first_name = models.CharField(max_length=255, null=True, blank=True)
    last_name = models.CharField(max_length=255, null=True, blank=True)
    full_name = models.CharField(max_length=255, null=True, blank=True)
    title = models.CharField(max_length=255, null=True, blank=True)
    email = models.EmailField(null=True, blank=True)
    phone = models.CharField(max_length=20, null=True, blank=True)
    mobile = models.CharField(max_length=20, null=True, blank=True)
    home_phone = models.CharField(max_length=20, null=True, blank=True)
    mailing_street = models.TextField(null=True, blank=True)
    mailing_city = models.CharField(max_length=100, null=True, blank=True)
    mailing_state = models.CharField(max_length=100, null=True, blank=True)
    mailing_country = models.CharField(max_length=100, null=True, blank=True)
    mailing_zip = models.CharField(max_length=20, null=True, blank=True)
    description = models.TextField(null=True, blank=True)
    currency_symbol = models.CharField(max_length=10, default="Rs.")
    last_activity_time = models.DateTimeField(null=True, blank=True)
    record_image = models.URLField(null=True, blank=True)
    locked_for_me = models.BooleanField(default=False)
    contact_id = models.CharField(max_length=50, unique=True)  # ID from Zoho
    zia_visions = models.TextField(null=True, blank=True)
    modified_time = models.DateTimeField()
    created_time = models.DateTimeField()
    followed = models.BooleanField(default=False)
    editable = models.BooleanField(default=True)
    zia_owner_assignment = models.CharField(max_length=100, null=True, blank=True)
    approval_state = models.CharField(max_length=50, default="approved")
    email_opt_out = models.BooleanField(default=False)
    unsubscribed_mode = models.CharField(max_length=50, null=True, blank=True)
    unsubscribed_time = models.DateTimeField(null=True, blank=True)
    record_creation_source_id = models.CharField(max_length=50, null=True, blank=True)
    last_activity_date = models.DateField(null=True, blank=True)
    is_deleted = models.BooleanField(default=False)
    account_name = models.JSONField(
        default=dict, blank=True, null=True
    ) 
    owner = models.JSONField(default=dict, blank=True, null=True)
    modified_by = models.JSONField(default=dict, blank=True, null=True)
    created_by = models.JSONField(default=dict, blank=True, null=True)
    tags = models.JSONField(default=list)
    added_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)

    def __str__(self):
        return self.full_name or f"{self.first_name} {self.last_name}"


class Deal(models.Model):

    deal_name = models.CharField(max_length=255)
    description = models.TextField(null=True, blank=True)
    closing_date = models.DateField(null=True, blank=True)
    last_activity_time = models.DateTimeField(null=True, blank=True)
    stage = models.CharField(max_length=100, null=True, blank=True)
    amount = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    pipeline = models.CharField(max_length=255, null=True, blank=True)
    currency_symbol = models.CharField(max_length=10, default="Rs.")
    locked_for_me = models.BooleanField(default=False)
    editable = models.BooleanField(default=True)
    followed = models.BooleanField(default=False)
    approval_state = models.CharField(max_length=50, default="approved")
    record_creation_source_id = models.CharField(max_length=50, null=True, blank=True)
    deal_id = models.CharField(max_length=50, unique=True)  # ID from Zoho
    has_more_secondary_contacts = models.BooleanField(default=False)
    deal_file = models.FileField(upload_to='deals/files/', null=True, blank=True)
    owner = models.JSONField(default=dict, blank=True, null=True)
    modified_by = models.JSONField(default=dict, blank=True, null=True)
    account_name = models.JSONField(default=dict, blank=True, null=True)
    secondary_contacts = models.JSONField(default=list, blank=True, null=True)
    associated_products = models.JSONField(default=list, blank=True, null=True)
    contact_name = models.JSONField(default=dict, blank=True, null=True)
    layout = models.JSONField(default=dict, blank=True, null=True)
    created_by = models.JSONField(default=dict, blank=True, null=True)
    tags = models.JSONField(default=list, blank=True, null=True)
    modified_time = models.DateTimeField(null=True, blank=True)
    created_time = models.DateTimeField(null=True, blank=True)
    gm_sheet = models.ForeignKey(GmSheet, null=True, on_delete=models.SET_NULL)
    is_deleted = models.BooleanField(default=False)
    sales_order = models.ForeignKey(SalesOrder, null=True, on_delete=models.SET_NULL)
    added_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)

    def __str__(self):
        return self.deal_name


class Payment(models.Model):
    PAYMENT_MODES = [
        ("bank_transfer", "Bank Transfer"),
        ("upi", "UPI"),
        ("credit_card", "Credit Card"),
        ("paypal", "PayPal"),
        ("razorpay", "Razorpay"),
        ("cash", "Cash"),
    ]
    PAYMENT_TYPES = [
        ("credit", "Credit"),
        ("debit", "debit"),
    ]
    client_invoice = models.ForeignKey(
        ClientInvoice, on_delete=models.SET_NULL, default=None, blank=True, null=True
    )
    bill = models.ForeignKey(
        Bill, on_delete=models.SET_NULL, default=None, blank=True, null=True
    )
    customer = models.ForeignKey(
        ZohoCustomer, on_delete=models.SET_NULL, default=None, blank=True, null=True
    )
    type = models.CharField(max_length=50, choices=PAYMENT_TYPES, default="credit")
    deposit_to = models.ForeignKey(BankDetails, on_delete=models.SET_NULL, null=True)
    debited_from = models.ForeignKey(
        BankDetails, on_delete=models.SET_NULL, null=True, related_name="deposit_from"
    )
    payment_number = models.CharField(max_length=50, blank=True, null=True, default="")
    amount = models.DecimalField(default=0, decimal_places=2, max_digits=20)
    bank_charges = models.DecimalField(default=0, decimal_places=2, max_digits=20)
    currency_code = models.CharField(max_length=50, default="", blank=True)
    currency_symbol = models.CharField(max_length=50, default="", blank=True)
    exchange_rate = models.CharField(max_length=50, blank=True, null=True)
    reference_number = models.CharField(
        max_length=255, null=True, blank=True, default=""
    )
    date = models.DateField()
    payment_mode = models.CharField(max_length=20, choices=PAYMENT_MODES)
    attachment = models.FileField(
        upload_to="payment_attachments/", null=True, blank=True
    )
    created_time = models.DateTimeField(auto_now_add=True)
    updated_time = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_time"]


class CreditNote(models.Model):

    customer = models.ForeignKey(
        ZohoCustomer, on_delete=models.SET_NULL, default=None, blank=True, null=True
    )
    credit_note_number = models.TextField(null=True, blank=True)
    client_invoice = models.ForeignKey(
        ClientInvoice, on_delete=models.SET_NULL, default=None, blank=True, null=True
    )
    currency_code = models.CharField(max_length=225, null=True, blank=True)
    amount = models.TextField(null=True, blank=True)
    terms_and_conditions = models.TextField(null=True, blank=True)
    customer_notes = models.TextField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]
