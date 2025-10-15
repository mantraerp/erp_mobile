import frappe
from erp_mobile.api.masterdata import response
from frappe import _
from frappe.utils import format_date, getdate


@frappe.whitelist(allow_guest=True, methods="GET")
def get_pr_status():
    status = [field.options for field in frappe.get_meta("Purchase Receipt").fields if field.fieldname == "status"][0].split("\n")
    status.remove("")
    status =  status
    return response("Purchase Receipt status fetched successfully", status, 200)

@frappe.whitelist(allow_guest=True, methods="GET")
def get_purchase_receipts(from_date=None, to_date=None, supplier=None, start=None,status=None,search_string=None):
    try:
        frappe.set_user("Administrator")
        filters = {}
        if from_date and to_date:
            filters["posting_date"] = ["between", [getdate(from_date,True), getdate(to_date,True)]]
        if supplier:
            filters["supplier"] = supplier
        if status:
            filters["status"] = status
        or_filters = []
        if search_string:
            or_filters.append(["name", "like", f"%{search_string}%"])
            or_filters.append(["supplier_name", "like", f"%{search_string}%"])

        pagination=False
        if start:
            pagination=True
            start = int(start)
        limit = 10
        if pagination:
            purchase_receipts = frappe.get_list(
                "Purchase Receipt",
                filters=filters,
                fields=["name", "supplier","supplier_name", "posting_date", "status", "grand_total", "currency","docstatus"],
                order_by="posting_date desc",
                or_filters=or_filters,
                limit_start=start,
                limit_page_length=limit
            )
            db_count = frappe.db.count("Purchase Receipt")
        else:
            purchase_receipts = frappe.get_list(
                "Purchase Receipt",
                filters=filters,
                fields=["name", "supplier", "supplier_name","posting_date", "status", "grand_total","currency","docstatus"],
                or_filters=or_filters,
                order_by="posting_date desc"
            )
        if not purchase_receipts:
            return response("No Purchase Receipts found", None, 200)
        for pr in purchase_receipts:
            pr["posting_date"] = format_date(pr["posting_date"])
        if pagination:
            if len(purchase_receipts) == limit  and db_count > (start + limit):
                data = {
                    "purchase_receipts": purchase_receipts,
                    "next_start": start + limit
                }
                return response("Purchase Receipts fetched successfully", data, 200)
            else:
                data = {
                    "purchase_receipts": purchase_receipts,
                    "next_start": None
                }
                return response("Purchase Receipts fetched successfully", data, 200)
        return response("Purchase Receipts fetched successfully", {"purchase_receipts": purchase_receipts}, 200)
    except Exception as e:
        frappe.log_error(title="Error fetching Purchase Receipts", message=frappe.get_traceback(True))
        return response(f"Error fetching Purchase Receipts: {str(e)}", None, 500)
    

@frappe.whitelist(allow_guest=True, methods=["GET"])
def get_purchase_receipt_details(purchase_receipt):
    try:
        frappe.set_user("Administrator")
        pr = frappe.get_doc("Purchase Receipt", purchase_receipt)
        return response("Purchase Receipt details fetched successfully", pr.as_dict(), 200)
    except Exception as e:
        frappe.log_error(title="Error fetching Purchase Receipt details", message=frappe.get_traceback(True))
        return response(f"Error fetching Purchase Receipt details: {str(e)}", None, 500)