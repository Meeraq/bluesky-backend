from django.urls import path, include
from . import views
from .views import (
    DownloadInvoice,
    DownloadAttatchedInvoice,
    FilteredPurchaseOrderView,
    ContactDetailView,
    CompanyDetailView,
    DealDetailView,
    DealFileUploadView,
    CompanyListCreateView,
    ContactListCreateView,
    DealListCreateView,
    ZohoCustomerListCreateView,
    ZohoCustomerUpdateView,
    BankDetailsListView,
    PaymentListCreateView,
    PaymentsExportView,
    DownloadPaymentReceipt,
    PaymentUpdateView,
    DownloadSalesOrder,
    SalesOrderLineItemListAPIView,
    DeleteCustomerAPIView,
    DownloadCreditNotesAPIView,
    FilteredPurchaseOrderViewExcel,
)

from .apis import (
    InvoiceListCreateAPIView,
    InvoiceUpdatesListAPIView,
    PurchaseOrderListView,
    PurchaseOrderExportView,
    InvoiceRetrieveDestroyView,
    InvoiceStatusUpdateView,
    ClientInvoiceListCreateView,
    ClientInvoiceRetrieveUpdateView,
    VendorsListView,
    ZohoVendorsListView,
    VendorDetailView,
    VendorUpdateView,
    SalesOrdersListView,
    DownloadInvoicePdf,
    V2DownloadAttachedInvoice,
    PurchaseOrderAndInvoicesView,
    InvoicesWithStatusView,
    TotalRevenueView,
    SalesOrderInvoiceListView,
    LineItemsDetailExcelView,
    InvoiceListCreateAPIView,
    InvoiceRetrieveDestroyView,
    InvoiceStatusUpdateView,
    InvoiceUpdatesListAPIView,
    V2DownloadAttachedInvoice,
    DownloadInvoicePdf,
    PurchaseOrderAndInvoicesView,
    InvoicesWithStatusView,
    TotalRevenueView,
    SalesOrderInvoiceListView,
    LineItemsDetailExcelView,
    ClientInvoiceRetrieveUpdateView,
    VendorsListView,
    ZohoVendorsListView,
    VendorDetailView,
    VendorUpdateView,
    SalesOrdersListView,
    CoachingPurchaseOrderCreateView,
    InvoicesExportView,
    InvoiceAgingReportView,
    InvoiceAgingDetailView,
)


import environ


env = environ.Env()

urlpatterns = [
    path(
        "get-purchase-orders/<int:vendor_id>/",
        views.get_purchase_orders,
        name="get_purchase_orders",
    ),
    path(
        "get_invoices_with_status/<str:vendor_id>/<str:purchase_order_id>/",
        views.get_invoices_with_status,
    ),
    path(
        "total-revenue/<vendor_id>/",
        views.get_total_revenue,
        name="get_total_revenue",
    ),
    # Other URL patterns for your app
    path(
        "get-purchase-order-data/<str:purchaseorder_id>/",
        views.get_purchase_order_data,
        name="get_purchase_order_data",
    ),
    path("add-invoice-data/", views.add_invoice_data, name="add_invoice_data"),
    path("edit-invoice/<int:invoice_id>/", views.edit_invoice),
    path(
        "delete-invoice/<int:invoice_id>/",
        views.delete_invoice,
        name="get_invoice_data",
    ),
    path(
        "po-and-invoices/<str:purchase_order_id>/",
        views.get_purchase_order_and_invoices,
    ),
    # path("update-vendor-id-to-coaches/", views.update_vendor_id),
    path("export-invoice-data/", views.export_invoice_data),
    path("download-invoice/<int:record_id>/", DownloadInvoice.as_view()),
    path(
        "download-client-invoice/<int:record_id>/",
        views.DownloadClientInvoice.as_view(),
    ),
    path(
        "download-attatched-invoice/<int:record_id>/",
        DownloadAttatchedInvoice.as_view(),
    ),
    path("vendors/", views.get_all_vendors),
    path("zoho-vendors/", views.get_zoho_vendors),
    path(
        "get-all-purchase-orders/",
        views.get_all_purchase_orders,
        name="get_all_purchase_orders",
    ),
    path(
        "pmo/purchase-orders/",
        views.get_all_purchase_orders_for_pmo,
        name="get_all_purchase_orders",
    ),
    path(
        "get-all-invoices/",
        views.get_all_invoices,
        name="get_all_invoices",
    ),
    path(
        "get-invoice/<int:invoice_id>/",
        views.get_invoice,
        name="get_invoice",
    ),
    path(
        "pmo/invoices/",
        views.get_invoices_for_pmo,
        name="get_all_invoices",
    ),
    path(
        "pmo/pending-invoices/",
        views.get_pending_invoices_for_pmo,
        name="get_pending_invoices_for_pmo",
    ),
    path(
        "sales/invoices/",
        views.get_invoices_for_sales,
        name="get_all_invoices",
    ),
    path("edit-vendor/<int:vendor_id>/", views.edit_vendor, name="edit_vendor"),
    path(
        "vendors/update-invoice-allowed/<int:vendor_id>/",
        views.update_invoice_allowed,
        name="update_invoice_allowed",
    ),
    path(
        "invoices/<str:status>/",
        views.get_invoices_by_status,
        name="get_invoices_by_status",
    ),
    path(
        "invoices/founders/<str:status>/",
        views.get_invoices_by_status_for_founders,
        name="get_invoices_by_status_for_founders",
    ),
    path(
        "invoices/<int:invoice_id>/update_status/",
        views.update_invoice_status,
    ),
    path(
        "invoices/<int:invoice_id>/updates/",
        views.get_invoice_updates,
        name="get_invoice_updates",
    ),
    path(
        "vendor/<str:vendor_id>/",
        views.get_vendor_details_from_zoho,
        name="get_vendor_details_from_zoho",
    ),
    # path(
    #     "purchase-order/create/<str:user_type>/<int:facilitator_pricing_id>/",
    #     views.create_purchase_order_api,
    #     name="create_purchase_order",
    # ),
    path(
        "po-number/",
        views.get_po_number_to_create,
        name="get_po_number_to_create",
    ),

    path(
        "so-number/",
        views.get_so_number_to_create,
        name="get_so_number_to_create",
    ),
    path(
        "credit-note-number/<str:brand>/",
        views.get_credit_note_number_to_create,
        name="get_credit_note_number_to_create",
    ),
    path(
        "purchase-order/status/<str:purchase_order_id>/<str:status>/",
        views.update_purchase_order_status,
        name="update_purchase_order_status",
    ),
    path(
        "purchase-order/outside/create/",
        views.create_purchase_order_for_outside_vendors,
    ),
    path(
        "invoices-data/",
        views.get_all_the_invoices_counts,
        name="get_all_the_invoices_counts",
    ),
    path(
        "get-individual-vendor-data/<int:vendor_id>/",
        views.get_individual_vendor_data,
        name="get_individual_vendor_data",
    ),
    path(
        "get-invoices-for-vendor/<int:vendor_id>/<str:purchase_order_id>/",
        views.get_invoices_for_vendor,
        name="get_invoices_for_vendor",
    ),
    path(
        "get-all-sales-orders/",
        views.get_all_sales_orders,
        name="get_all_sales_orders",
    ),
    path(
        "sales-orders/<str:sales_person_id>/",
        views.get_sales_persons_sales_orders,
        name="get_sales_persons_sales_orders",
    ),
    path(
        "sales-order/<int:id>/download/",
        DownloadSalesOrder.as_view(),
    ),
    path(
        "get-sales-order-data/<str:salesorder_id>/",
        views.get_sales_order_data,
        name="get_sales_order_data",
    ),
    path(
        "sales-order-details/purcahse-order/<str:purchaseorder_id>/",
        views.get_sales_order_data_from_purchase_order_id,
    ),
    path(
        "customers/",
        views.get_customers,
        name="get_customers",
    ),
    path(
        "customer-details/<str:customer_id>/",
        views.get_customer_details,
        name="get_customer_details",
    ),
    path(
        "create-invoice/",
        views.create_invoice,
        name="create_invoice",
    ),
    path(
        "edit-so-invoice/<str:invoice_id>/",
        views.edit_so_invoice,
        name="edit_so_invoice",
    ),
    path(
        "sales-order/create/",
        views.create_sales_order,
        name="create_sales_order",
    ),
    path(
        "sales-order/edit/<str:sales_order_id>/",
        views.edit_sales_order,
        name="edit_sales_order",
    ),
    path(
        "get-all-client-invoices/",
        views.get_all_client_invoices,
        name="get_all_client_invoices",
    ),
    path(
        "get-client-invoices/",
        views.get_client_invoices,
        name="get_client_invoices",
    ),
    path(
        "get-client-invoice-data/<str:invoice_id>/",
        views.get_client_invoice_data,
        name="get_client_invoice_data",
    ),
    path(
        "client-invoice/status/<str:invoice_id>/<str:status>/",
        views.update_client_invoice_status,
        name="update_client_invoice_status",
    ),
    path(
        "update-sales-order-status/<str:sales_order_id>/<str:status>/",
        views.update_sales_order_status,
        name="update_sales_order_status",
    ),
    path(
        "get-all-invoices-of-sales-order/<str:sales_order_id>/",
        views.get_all_invoices_of_sales_order,
        name="get_all_invoices_of_sales_order",
    ),
    path(
        "get-handovers-so/<int:user_id>/<str:user_type>/",
        views.get_handovers_so,
        name="get_handovers_so",
    ),
    path(
        "get-total-so-created-count/<str:sales_person_id>/",
        views.get_total_so_created_count,
        name="get_total_so_created_count",
    ),
    path(
        "get-handovers-count/<str:sales_person_id>/",
        views.get_handovers_count,
        name="get_handovers_count",
    ),
    path(
        "sales-orders-with-due-invoices/<str:sales_person_id>/",
        views.sales_orders_with_due_invoices,
        name="sales_orders_with_due_invoices",
    ),
    path("line-items/", views.get_line_items, name="get_line_items"),
    path(
        "get-ctt-revenue-data/", views.get_ctt_revenue_data, name="get_ctt_revenue_data"
    ),
    path(
        "get-meeraq-revenue-data/",
        views.get_meeraq_revenue_data,
        name="get_meeraq_revenue_data",
    ),
    path(
        "get-line-items-detail-in-excel/",
        views.get_line_items_detail_in_excel,
        name="get_line_items_detail_in_excel",
    ),
    path("vendor/update-msme/<int:vendor_id>/", views.update_vendor_msme),
    path(
        "edit-purchase-order/<str:po_id>/",
        views.edit_purchase_order,
        name="edit_purchase_order",
    ),
    path(
        "get-po-client-invoice/",
        FilteredPurchaseOrderView.as_view(),
        name="get-po-client-invoice",
    ),
    path(
        "get-po-client-invoice-excel/",
        FilteredPurchaseOrderViewExcel.as_view(),
        name="get-po-client-invoice-excel",
    ),
    path(
        "pipelines/",
        views.get_pipelines_data,
    ),
    path(
        "companies/", CompanyListCreateView.as_view(), name="company-list-create"
    ),  # GET all, POST create
    path(
        "companies/<str:account_id>/",
        CompanyDetailView.as_view(),
        name="company-detail",
    ),  # GET, PUT, DELETE specific company
    # Contact URLs
    path(
        "contacts/", ContactListCreateView.as_view(), name="contact-list-create"
    ),  # GET all, POST create
    path(
        "contacts/<str:contact_id>/", ContactDetailView.as_view(), name="contact-detail"
    ),  # GET, PUT, DELETE specific contact
    # Deal URLs
    path(
        "deals/", DealListCreateView.as_view(), name="deal-list-create"
    ),  # GET all, POST create
    path("deals/<str:deal_id>/", DealDetailView.as_view(), name="deal-detail"),
    path(
        "deals/upload-file/<str:deal_id>/",
        DealFileUploadView.as_view(),
        name="deal-file-upload",
    ),
    path(
        "entities/", views.EntityListCreateView.as_view(), name="entity-list-create"
    ),  # For list and create
    path(
        "entities/<int:pk>/",
        views.EntityRetrieveUpdateDestroyView.as_view(),
        name="entity-detail",
    ),  # For retrieve, update, and delete
    path("v2/customers/", ZohoCustomerListCreateView.as_view()),
    path(
        "v2/customers/<int:pk>/",
        ZohoCustomerUpdateView.as_view(),
        name="zoho-customer-update",
    ),
    path("bank-details/", BankDetailsListView.as_view(), name="bank-details-list"),
    path("payments/", PaymentListCreateView.as_view(), name="payment-list-create"),
    path("payments/export/", PaymentsExportView.as_view(), name="payment-export"),
    path("payments/<int:pk>/", PaymentUpdateView.as_view()),
    path("payments/<int:id>/download/", DownloadPaymentReceipt.as_view()),
    path(
        "v2/line-items/",
        SalesOrderLineItemListAPIView.as_view(),
        name="line-items-list",
    ),
    path(
        "credit-notes/",
        views.CreditNoteListCreateView.as_view(),
        name="credit-note-list-create",
    ),
    path(
        "credit-notes/<int:pk>/",
        views.CreditNoteDetailView.as_view(),
        name="credit-note-detail",
    ),
    path(
        "credit-note/<int:credit_note_id>/download/",
        views.CreditNoteView.as_view(),
        name="credit-note-detail",
    ),
    path(
        "delete-zoho-customer/<int:customer_id>/",
        DeleteCustomerAPIView.as_view(),
        name="delete-zoho-customer",
    ),
    path(
        "download-credit-note/",
        DownloadCreditNotesAPIView.as_view(),
        name="download-credit-note",
    ),
    path("bills/", views.BillListCreateAPIView.as_view(), name="bill-list-create"),
    path(
        "bills/<int:pk>/",
        views.BillRetrieveUpdateDestroyAPIView.as_view(),
        name="bill-detail",
    ),
    path(
        "download-po/<str:purchase_order_id>/",
        views.generate_purchase_order_pdf,
        name="bill-detail",
    ),
    path("bills/<str:bill_id>/pdf/", views.generate_bill_pdf, name="generate_bill_pdf"),
    path("vendor/login/data/<str:vendor_id>/", views.get_vendor_login_data),
    path("v2/purchaseorders/", PurchaseOrderListView.as_view()),
    path("v2/purchaseorders/export/", PurchaseOrderExportView.as_view()),
    path("v2/invoices/", InvoiceListCreateAPIView.as_view()),
    path("v2/invoices/export/", InvoicesExportView.as_view()),
    path("v2/invoices/<int:pk>/", InvoiceRetrieveDestroyView.as_view()),
    path("v2/invoices/<int:pk>/update-status/", InvoiceStatusUpdateView.as_view()),
    path("v2/invoices/<int:invoice_id>/updates/", InvoiceUpdatesListAPIView.as_view()),
    path(
        "v2/invoices/<int:invoice_id>/download-attatched-invoice/",
        V2DownloadAttachedInvoice.as_view(),
    ),
    path("v2/invoices/<int:pk>/download/", DownloadInvoicePdf.as_view()),
    path(
        "v2/purchaseorders/<int:purchase_order_id>/invoices/",
        PurchaseOrderAndInvoicesView.as_view(),
    ),
    path(
        "v2/purchaseorders/<str:purchase_order_id>/vendor/<str:vendor_id>/status/",
        InvoicesWithStatusView.as_view(),
    ),
    path("v2/vendor/<int:vendor_id>/revenue/", TotalRevenueView.as_view()),
    path(
        "v2/sales-orders/<str:sales_order_id>/invoices/zoho/",
        SalesOrderInvoiceListView.as_view(),
    ),
    path("v2/line-items/detail/excel/", LineItemsDetailExcelView.as_view()),
    path("v2/clientinvoices/", ClientInvoiceListCreateView.as_view()),
    path(
        "v2/clientinvoices/<int:invoice_id>/", ClientInvoiceRetrieveUpdateView.as_view()
    ),
    path("v2/vendors/", VendorsListView.as_view()),
    path("v2/vendors/zoho/", ZohoVendorsListView.as_view()),
    path("v2/vendor-details/<int:pk>/", VendorDetailView.as_view()),
    path("v2/vendors/<int:id>/update/", VendorUpdateView.as_view()),
    path(
        "v2/purchase-order/create/<str:project_type>/<int:project_id>/",
        CoachingPurchaseOrderCreateView.as_view(),
    ),
    path(
        "v2/invoice-aging-report/",
        InvoiceAgingReportView.as_view(),
        name="invoice-aging-report",
    ),
    path(
        "v2/invoice-aging-detail/",
        InvoiceAgingDetailView.as_view(),
        name="invoice-aging-detail",
    ),
    path("gmsheet/maxNumber/", views.max_gmsheet_number, name="max_gmsheet_number"),
    path("v2/salesorders/", SalesOrdersListView.as_view()),
    path(
        "gmsheet-detail/", views.GMSheetDetailAPIView.as_view(), name="gmsheet-detail"
    ),
    path("create-vendor/", views.create_vendor, name="create_vendor"),
    path("create-assets/", views.create_asset),
    path("assets/", views.get_all_assets),
    path("delete-asset/", views.delete_asset, name="delete_asset"),
    path("update-asset/", views.update_asset, name="update_asset"),
     path("asset/maxNumber/", views.max_asset_number, name="max_asset_number"),
]
