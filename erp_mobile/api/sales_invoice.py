import frappe
from erp_mobile.api.masterdata import response
from frappe.utils import getdate, format_date

@frappe.whitelist(allow_guest=True, methods="GET")
def get_si_status():
    status = [field.options for field in frappe.get_meta("Sales Invoice").fields if field.fieldname == "status"][0].split("\n")
    status.remove("")
    status =  status
    return response("Sales Invoice status fetched successfully", status, 200)

@frappe.whitelist(allow_guest=True, methods="GET")
def get_sales_invoices(from_date=None, to_date=None, customer=None, start=None,status=None, search_string=None):
    try:
        frappe.set_user("Administrator")
        filters = {}
        if from_date and to_date:
            filters["posting_date"] = ["between", [getdate(from_date,True), getdate(to_date,True)]]
        if customer:
            filters["customer"] = customer
        if status:
            filters["status"] = status
        or_filters = []
        if search_string:
            or_filters.append(["name", "like", f"%{search_string}%"])
            or_filters.append(["customer_name", "like", f"%{search_string}%"])

        pagination=False
        if start:
            pagination=True
            start = int(start)
        limit = 10
        if pagination:
            sales_invoices = frappe.get_list(
                "Sales Invoice",
                filters=filters,
                fields=["name", "customer","customer_name", "posting_date", "status", "grand_total", "currency","docstatus"],
                or_filters=or_filters,
                order_by="posting_date desc",
                limit_start=start,
                limit_page_length=limit
            )
            db_count = frappe.db.count("Sales Invoice")
        else:
            sales_invoices = frappe.get_list(
                "Sales Invoice",
                filters=filters,
                or_filters=or_filters,
                fields=["name", "customer", "customer_name","posting_date", "status", "grand_total","currency","docstatus"],
                order_by="posting_date desc"
            )
        if not sales_invoices:
            return response("No Sales Invoices found", None, 200)
        for si in sales_invoices:
            si["posting_date"] = format_date(si["posting_date"])
        if pagination:
            if len(sales_invoices) == limit  and db_count > (start + limit):
                data = {
                    "sales_invoices": sales_invoices,
                    "next_start": start + limit
                }
                return response("Sales Invoices fetched successfully", data, 200)
            else:
                data = {
                    "sales_invoices": sales_invoices,
                    "next_start": None
                }
                return response("Sales Invoices fetched successfully", data, 200)
        else:
            return response("Sales Invoices fetched successfully", {"sales_invoices": sales_invoices}, 200)
    except Exception as e:
        frappe.log_error(message=frappe.get_traceback(with_context=True), title="Error in get_sales_invoices")
        return response(str(e), None, 500)
    

@frappe.whitelist(allow_guest=True, methods="GET")
def get_sales_invoice_details(sales_invoice):
    try:
        frappe.set_user("Administrator")
        if not sales_invoice:
            return response("Sales Invoice is required", None, 400)
        si = frappe.get_doc("Sales Invoice", sales_invoice)
        if not si:
            return response("Sales Invoice not found", None, 404)
        si_data = si.as_dict()
        return response("Sales Invoice details fetched successfully", si_data, 200)
    except Exception as e:
        frappe.log_error(message=frappe.get_traceback(with_context=True), title="Error in get_sales_invoice_details")
        return response(str(e), None, 500)