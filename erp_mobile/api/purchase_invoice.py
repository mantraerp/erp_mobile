import frappe
from erp_mobile.api.masterdata import response
from frappe import _
from frappe.utils import format_date, getdate

@frappe.whitelist(allow_guest=True, methods="GET")
def get_pi_status():
    status = [field.options for field in frappe.get_meta("Purchase Invoice").fields if field.fieldname == "status"][0].split("\n")
    status.remove("")
    status =  status
    return response("Purchase Invoice status fetched successfully", status, 200)


@frappe.whitelist(allow_guest=True, methods="GET")
def get_purchase_invoices(from_date=None, to_date=None, supplier=None, start=None,status=None):
    try:
        frappe.set_user("Administrator")
        filters = {}
        if from_date and to_date:
            filters["posting_date"] = ["between", [getdate(from_date,True), getdate(to_date,True)]]
        if supplier:
            filters["supplier"] = supplier
        if status:
            filters["status"] = status

        pagination=False
        if start:
            pagination=True
            start = int(start)
        limit = 10
        if pagination:
            purchase_invoices = frappe.get_list(
                "Purchase Invoice",
                filters=filters,
                fields=["name", "supplier","supplier_name", "posting_date", "status", "grand_total", "currency","docstatus"],
                order_by="posting_date desc",
                limit_start=start,
                limit_page_length=limit
            )
            db_count = frappe.db.count("Purchase Invoice")
        else:
            purchase_invoices = frappe.get_list(
                "Purchase Invoice",
                filters=filters,
                fields=["name", "supplier", "supplier_name","posting_date", "status", "grand_total","currency","docstatus"],
                order_by="posting_date desc"
            )
        if not purchase_invoices:
            return response("No Purchase Invoices found", None, 200)
        for pi in purchase_invoices:
            pi["posting_date"] = format_date(pi["posting_date"])
        if pagination:
            if len(purchase_invoices) == limit  and db_count > (start + limit):
                data = {
                    "purchase_invoices": purchase_invoices,
                    "next_start": start + limit
                }
                return response("Purchase Invoices fetched successfully", data, 200)
            else:
                data = {
                    "purchase_invoices": purchase_invoices,
                    "next_start": None
                }
                return response("Purchase Invoices fetched successfully", data, 200)
        else:
            return response("Purchase Invoices fetched successfully", {"purchase_invoices": purchase_invoices}, 200)
    except Exception as e:
        frappe.log_error(title="Error fetching Purchase Invoices", message=frappe.get_traceback(True))
        return response(f"Error fetching Purchase Invoices: {str(e)}", None, 500)
    

@frappe.whitelist(allow_guest=True,methods="GET")
def get_purchase_invoice_details(purchase_invoice):
    try:
        frappe.set_user("Administrator")
        pi = frappe.get_doc("Purchase Invoice", purchase_invoice)
        return response("Purchase Invoice details fetched successfully", pi.as_dict(), 200)
    except frappe.exceptions.DoesNotExistError:
        return response("Purchase Invoice does not exist", None, 404)
    except Exception as e:
        frappe.log_error(title="Error fetching Purchase Invoice details", message=frappe.get_traceback(True))
        return response(f"Error fetching Purchase Invoice details: {str(e)}", None, 500)
