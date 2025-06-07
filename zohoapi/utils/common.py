from datetime import datetime, timedelta, date
from num2words import num2words
from django.db.models import Case, When, Value, F, DateField
from django.db.models.functions import Cast
import environ
from django.db import transaction
from django.db.models import Sum
from decimal import Decimal
import logging

logger = logging.getLogger(__name__)



env = environ.Env()


class SerializerByMethodMixin:
    def get_serializer_class(self, *args, **kwargs):
        return self.serializer_map.get(self.request.method, self.serializer_class)


def get_subtotal_excluding_tax(line_items):
    res = 0
    for line_item in line_items:
        try:
            quantity = float(line_item.get("quantity_input", 0) or 0)
            rate = float(line_item.get("rate", 0) or 0)
            res += round(quantity * rate, 2)
        except (ValueError, TypeError):
            continue
    return res


def get_financial_year(date):
    if date.month >= 4:
        return date.year, date.year + 1
    else:
        return date.year - 1, date.year


def get_tax(line_item, taxt_type):
    tax_based_on_type = next(
        (
            item
            for item in line_item.get("line_item_taxes", [])
            if taxt_type in item.get("tax_name", "")
        ),
        None,
    )
    percentage = (
        float(tax_based_on_type["tax_name"].split("(")[-1].split("%")[0])
        if tax_based_on_type
        else 0
    )
    return f"{percentage}%" if percentage else ""


def add_45_days(date_str):
    date = datetime.strptime(date_str, "%Y-%m-%d")
    new_date = date + timedelta(days=45)
    new_date_str = new_date.strftime("%Y-%m-%d")
    return new_date_str


def get_line_items_for_template(line_items):

    if not line_items:
        return []

    res = [*line_items]
    for line_item in res:
        # Get values with defaults of 0 for None/null values
        quantity = float(line_item.get("quantity_input", 0) or 0)
        rate = float(line_item.get("rate", 0) or 0)
        tax_percentage = float(line_item.get("tax_percentage", 0) or 0)

        # Calculate quantity_mul_rate
        line_item["quantity_mul_rate"] = round(quantity * rate, 2)

        # Calculate quantity_mul_rate_include_tax
        line_item["quantity_mul_rate_include_tax"] = round(
            quantity * rate * (1 + tax_percentage / 100), 2
        )

        # Calculate tax_amount
        line_item["tax_amount"] = round((quantity * rate * tax_percentage) / 100, 2)

        # Calculate different tax types
        line_item["cgst_tax"] = get_tax(line_item, "CGST") or 0
        line_item["sgst_tax"] = get_tax(line_item, "SGST") or 0
        line_item["igst_tax"] = get_tax(line_item, "IGST") or 0

    return res


def get_invoice_data_for_pdf(serialized_data, hsn_or_sac):
    is_india_entity = env("INDIA_ENTITY_ID") == serialized_data["entity"]
    line_items = get_line_items_for_template(serialized_data["line_items"])
    invoice_date = datetime.strptime(
        serialized_data["invoice_date"], "%Y-%m-%d"
    ).strftime("%d-%m-%Y")
    due_date = datetime.strptime(
        add_45_days(serialized_data["invoice_date"]), "%Y-%m-%d"
    ).strftime("%d-%m-%Y")
    invoice_data = {
        **serialized_data,
        "invoice_date": invoice_date,
        "due_date": due_date,
        "line_items": line_items,
        "sub_total_excluding_tax": get_subtotal_excluding_tax(
            serialized_data["line_items"]
        ),
        "hsn_or_sac": hsn_or_sac if hsn_or_sac else "-",
        "is_india_entity": is_india_entity,
    }
    return invoice_data


def amount_convert_to_words(amount, currency_code):
    """
    Convert a numeric amount to words including currency.

    Args:
    amount (float): The amount to convert to words.
    currency_code (str): The currency code, e.g., 'USD', 'EUR'.

    Returns:
    str: The amount in words including currency.
    """
    # Define currency and sub-currency names based on currency code
    currency_names = {
        "AED": ("United Arab Emirates dirham", "fils"),
        "AFN": ("Afghan afghani", "pul"),
        "ALL": ("Albanian lek", "qindarka"),
        "AMD": ("Armenian dram", "luma"),
        "ANG": ("Netherlands Antillean guilder", "cent"),
        "AOA": ("Angolan kwanza", "cêntimo"),
        "ARS": ("Argentine peso", "centavo"),
        "AUD": ("Australian dollar", "cent"),
        "AWG": ("Aruban florin", "cent"),
        "AZN": ("Azerbaijani manat", "qəpik"),
        "BAM": ("Bosnia and Herzegovina convertible mark", "fening"),
        "BBD": ("Barbadian dollar", "cent"),
        "BDT": ("Bangladeshi taka", "poisha"),
        "BGN": ("Bulgarian lev", "stotinka"),
        "BHD": ("Bahraini dinar", "fils"),
        "BIF": ("Burundian franc", ""),
        "BMD": ("Bermudian dollar", "cent"),
        "BND": ("Brunei dollar", "cent"),
        "BOB": ("Bolivian boliviano", "centavo"),
        "BRL": ("Brazilian real", "centavo"),
        "BSD": ("Bahamian dollar", "cent"),
        "BTN": ("Bhutanese ngultrum", "chhertum"),
        "BWP": ("Botswana pula", "thebe"),
        "BYN": ("Belarusian ruble", "kapeyka"),
        "BZD": ("Belize dollar", "cent"),
        "CAD": ("Canadian dollar", "cent"),
        "CDF": ("Congolese franc", "centime"),
        "CHF": ("Swiss franc", "rappen"),
        "CLP": ("Chilean peso", "centavo"),
        "CNY": ("Chinese yuan", "fen"),
        "COP": ("Colombian peso", "centavo"),
        "CRC": ("Costa Rican colón", "céntimo"),
        "CUP": ("Cuban peso", "centavo"),
        "CVE": ("Cape Verdean escudo", "centavo"),
        "CZK": ("Czech koruna", "haléř"),
        "DJF": ("Djiboutian franc", ""),
        "DKK": ("Danish krone", "øre"),
        "DOP": ("Dominican peso", "centavo"),
        "DZD": ("Algerian dinar", "centime"),
        "EGP": ("Egyptian pound", "piastre"),
        "ERN": ("Eritrean nakfa", "cent"),
        "ETB": ("Ethiopian birr", "santim"),
        "EUR": ("Euro", "cent"),
        "FJD": ("Fijian dollar", "cent"),
        "FKP": ("Falkland Islands pound", "pence"),
        "FOK": ("Faroese króna", "oyra"),
        "GBP": ("British pound", "pence"),
        "GEL": ("Georgian lari", "tetri"),
        "GGP": ("Guernsey pound", "pence"),
        "GHS": ("Ghanaian cedi", "pesewa"),
        "GIP": ("Gibraltar pound", "pence"),
        "GMD": ("Gambian dalasi", "butut"),
        "GNF": ("Guinean franc", ""),
        "GTQ": ("Guatemalan quetzal", "centavo"),
        "GYD": ("Guyanese dollar", "cent"),
        "HKD": ("Hong Kong dollar", "cent"),
        "HNL": ("Honduran lempira", "centavo"),
        "HRK": ("Croatian kuna", "lipa"),
        "HTG": ("Haitian gourde", "centime"),
        "HUF": ("Hungarian forint", "fillér"),
        "IDR": ("Indonesian rupiah", "sen"),
        "ILS": ("Israeli new shekel", "agora"),
        "IMP": ("Isle of Man pound", "pence"),
        "INR": ("Indian rupee", "paise"),
        "IQD": ("Iraqi dinar", "fils"),
        "IRR": ("Iranian rial", "dinar"),
        "ISK": ("Icelandic króna", "aurar"),
        "JEP": ("Jersey pound", "pence"),
        "JMD": ("Jamaican dollar", "cent"),
        "JOD": ("Jordanian dinar", "fils"),
        "JPY": ("Japanese yen", ""),
        "KES": ("Kenyan shilling", "cent"),
        "KGS": ("Kyrgyzstani som", "tyiyn"),
        "KHR": ("Cambodian riel", "sen"),
        "KID": ("Kiribati dollar", "cent"),
        "KMF": ("Comorian franc", ""),
        "KRW": ("South Korean won", "jeon"),
        "KWD": ("Kuwaiti dinar", "fils"),
        "KYD": ("Cayman Islands dollar", "cent"),
        "KZT": ("Kazakhstani tenge", "tiyn"),
        "LAK": ("Lao kip", "att"),
        "LBP": ("Lebanese pound", "piastre"),
        "LKR": ("Sri Lankan rupee", "cent"),
        "LRD": ("Liberian dollar", "cent"),
        "LSL": ("Lesotho loti", "sente"),
        "LYD": ("Libyan dinar", "dirham"),
        "MAD": ("Moroccan dirham", "centime"),
        "MDL": ("Moldovan leu", "ban"),
        "MGA": ("Malagasy ariary", "iraimbilanja"),
        "MKD": ("Macedonian denar", "deni"),
        "MMK": ("Burmese kyat", "pya"),
        "MNT": ("Mongolian tögrög", "möngö"),
        "MOP": ("Macanese pataca", "avo"),
        "MRU": ("Mauritanian ouguiya", "khoums"),
        "MUR": ("Mauritian rupee", "cent"),
        "MVR": ("Maldivian rufiyaa", "laari"),
        "MWK": ("Malawian kwacha", "tambala"),
        "MXN": ("Mexican peso", "centavo"),
        "MYR": ("Malaysian ringgit", "sen"),
        "MZN": ("Mozambican metical", "centavo"),
        "NAD": ("Namibian dollar", "cent"),
        "NGN": ("Nigerian naira", "kobo"),
        "NIO": ("Nicaraguan córdoba", "centavo"),
        "NOK": ("Norwegian krone", "øre"),
        "NPR": ("Nepalese rupee", "paise"),
        "NZD": ("New Zealand dollar", "cent"),
        "OMR": ("Omani rial", "baisa"),
        "PAB": ("Panamanian balboa", "centésimo"),
        "PEN": ("Peruvian sol", "céntimo"),
        "PGK": ("Papua New Guinean kina", "toea"),
        "PHP": ("Philippine peso", "centavo"),
        "PKR": ("Pakistani rupee", "paisa"),
        "PLN": ("Polish zloty", "grosz"),
        "PYG": ("Paraguayan guaraní", ""),
        "QAR": ("Qatari riyal", "dirham"),
        "RON": ("Romanian leu", "ban"),
        "RSD": ("Serbian dinar", "para"),
        "RUB": ("Russian ruble", "kopeyka"),
        "RWF": ("Rwandan franc", ""),
        "SAR": ("Saudi riyal", "halala"),
        "SBD": ("Solomon Islands dollar", "cent"),
        "SCR": ("Seychellois rupee", "cent"),
        "SDG": ("Sudanese pound", "piastre"),
        "SEK": ("Swedish krona", "öre"),
        "SGD": ("Singapore dollar", "cent"),
        "SHP": ("Saint Helena pound", "pence"),
        "SLE": ("Sierra Leonean leone", "cent"),
        "SLL": ("Sierra Leonean leone", "cent"),
        "SOS": ("Somali shilling", "cent"),
        "SRD": ("Surinamese dollar", "cent"),
        "SSP": ("South Sudanese pound", "piaster"),
        "STN": ("São Tomé and Príncipe dobra", "cêntimo"),
        "SYP": ("Syrian pound", "piastre"),
        "SZL": ("Eswatini lilangeni", "cent"),
        "THB": ("Thai baht", "satang"),
        "TJS": ("Tajikistani somoni", "diram"),
        "TMT": ("Turkmenistani manat", "tenge"),
        "TND": ("Tunisian dinar", "millime"),
        "TOP": ("Tongan paʻanga", "seniti"),
        "TRY": ("Turkish lira", "kuruş"),
        "TTD": ("Trinidad and Tobago dollar", "cent"),
        "TVD": ("Tuvaluan dollar", "cent"),
        "TWD": ("New Taiwan dollar", "cent"),
        "TZS": ("Tanzanian shilling", "cent"),
        "UAH": ("Ukrainian hryvnia", "kopiyka"),
        "UGX": ("Ugandan shilling", "cent"),
        "USD": ("United States dollar", "cent"),
        "UYU": ("Uruguayan peso", "centésimo"),
        "UZS": ("Uzbekistani som", "tiyin"),
        "VES": ("Venezuelan bolívar", "céntimo"),
        "VND": ("Vietnamese dong", "hào"),
        "VUV": ("Vanuatu vatu", ""),
        "WST": ("Samoan tala", "sene"),
        "XAF": ("Central African CFA franc", ""),
        "XCD": ("East Caribbean dollar", "cent"),
        "XOF": ("West African CFA franc", ""),
        "XPF": ("CFP franc", ""),
        "YER": ("Yemeni rial", "fils"),
        "ZAR": ("South African rand", "cent"),
        "ZMW": ("Zambian kwacha", "ngwee"),
        "ZWL": ("Zimbabwean dollar", "cent"),
    }

    currency, sub_currency = currency_names.get(
        currency_code, ("currency", "sub-currency")
    )

    # Split the amount into the whole number and the fractional part
    whole_part = int(amount)
    fractional_part = round((amount - whole_part) * 100)

    # Convert the whole number part to words
    words = f"{currency} {num2words(whole_part)}"

    # If there's a fractional part, convert it to words as well
    if fractional_part > 0 or amount % 1 != 0:
        words += f" and {num2words(fractional_part)} {sub_currency}"

    return words


salesorder_line_item_due_date_case = Case(
    When(custom_field_hash__cf_due_date_unformatted__isnull=True, then=Value(None)),
    When(
        custom_field_hash__cf_due_date_unformatted__regex=r"^\d{4}-\d{2}-\d{2}$",
        then=Cast(
            F("custom_field_hash__cf_due_date_unformatted"), output_field=DateField()
        ),
    ),
    default=Value(None),
    output_field=DateField(),
)


def get_styles(workbook):
    return {
        "header_style": workbook.add_format(
            {
                "bold": True,
                "font_size": 12,
                "font_name": "Arial",
                "bg_color": "#4F81BD",
                "font_color": "white",
                "align": "center",
                "valign": "vcenter",
                "border": 1,
                "border_color": "#2E75B6",
            }
        ),
        "cell_style": workbook.add_format(
            {
                "font_name": "Arial",
                "align": "left",
                "border": 1,
                "border_color": "#D9D9D9",
            }
        ),
        "number_style": workbook.add_format(
            {
                "font_name": "Arial",
                "align": "right",
                "border": 1,
                "border_color": "#D9D9D9",
            }
        ),
        "date_style": workbook.add_format(
            {
                "num_format": "dd-MM-yyyy",
                "font_name": "Arial",
                "align": "center",
            }
        ),
        "datetime_style": workbook.add_format(
            {
                "num_format": "DD-MM-YYYY hh:mm:ss",
                "font_name": "Arial",
                "align": "center",
            }
        ),
    }


def update_invoice_status_and_balance(client_invoice):
    """
    Updates the invoice balance and status based on payments made and credit notes applied.
    Args:
        client_invoice: A ClientInvoice instance to update
    Returns:
        The updated ClientInvoice instance
    """
    with transaction.atomic():
        # Calculate total payments for this invoice
        payments = client_invoice.payment_set.filter(type="credit")
        total_payments = payments.aggregate(Sum("amount"))["amount__sum"] or Decimal("0.00")

        # Calculate total credit notes for this invoice
        credit_notes = client_invoice.creditnote_set.all()
        total_credit_notes = Decimal("0.00")
        
        for credit_note in credit_notes:
            try:
                # Convert to string first to ensure proper Decimal conversion
                credit_note_amount = str(credit_note.amount).strip()
                if credit_note_amount:  # Check if not empty
                    total_credit_notes += Decimal(credit_note_amount)
            except Exception as e:
                # Log the problematic value with more context
                logger.error(
                    f"Invalid credit note amount: invoice_id={client_invoice.id}, "
                    f"credit_note_id={credit_note.id}, amount={credit_note.amount}, error={str(e)}"
                )
                # Skip this credit note

        # Update the credits_applied field
        client_invoice.credits_applied = total_credit_notes
        client_invoice.credits_applied_formatted = format_currency(
            total_credit_notes, client_invoice.currency_symbol
        )
        
        # Update the balance
        if client_invoice.total:
            # Ensure client_invoice.total is also a Decimal
            invoice_total = Decimal(str(client_invoice.total))
            
            # Subtract both payments and credit notes from the total
            client_invoice.balance = (
                invoice_total - total_payments - total_credit_notes
            )
            client_invoice.balance_formatted = format_currency(
                client_invoice.balance, client_invoice.currency_symbol
            )

            # Update payment_made field (includes both direct payments and credit notes)
            client_invoice.payment_made = total_payments
            client_invoice.payment_made_formatted = format_currency(
                total_payments + total_credit_notes, client_invoice.currency_symbol
            )

        # Update the status based on balance and due date
        today = date.today()

        if client_invoice.balance <= Decimal("0.01"):  # Small threshold for rounding errors
            client_invoice.status = "paid"
            client_invoice.status_formatted = "Paid"
        elif client_invoice.due_date and client_invoice.due_date < today:
            client_invoice.status = "overdue"
            client_invoice.status_formatted = "Overdue"
        elif total_payments > Decimal("0.00") and client_invoice.balance > Decimal("0.01"):
            client_invoice.status = "partially_paid"
            client_invoice.status_formatted = "Partially Paid"
        
        # Save the changes
        client_invoice.save()
        logger.info(f"Updated invoice {client_invoice.id}: status={client_invoice.status}, balance={client_invoice.balance}")
        return client_invoice

def format_currency(amount, currency_symbol):
    """
    Formats the amount with the appropriate currency symbol
    Args:
        amount: Decimal amount to format
        currency_symbol: Currency symbol to use
    Returns:
        Formatted currency string
    """
    if not amount:
        return f"{currency_symbol}0.00"
    return f"{currency_symbol}{amount:,.2f}"
