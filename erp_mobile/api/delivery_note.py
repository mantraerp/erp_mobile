import frappe
from erp_mobile.api.masterdata import response
from frappe.utils import getdate, format_date

@frappe.whitelist(allow_guest=True, methods="GET")
def get_dn_status():
    status = [field.options for field in frappe.get_meta("Delivery Note").fields if field.fieldname == "status"][0].split("\n")
    status.remove("")
    status =  status
    return response("Delivery Note status fetched successfully", status, 200)

@frappe.whitelist(allow_guest=True, methods="GET")
def get_delivery_notes(from_date=None, to_date=None, customer=None, start=None,status=None,search_string=None):
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
            delivery_notes = frappe.get_list(
                "Delivery Note",
                filters=filters,
                fields=["name", "customer","customer_name", "posting_date", "status", "grand_total", "currency","docstatus"],
                order_by="posting_date desc",
                or_filters=or_filters,
                limit_start=start,
                limit_page_length=limit
            )
            db_count = frappe.db.count("Delivery Note")
        else:
            delivery_notes = frappe.get_list(
                "Delivery Note",
                filters=filters,
                fields=["name", "customer", "customer_name","posting_date", "status", "grand_total","currency","docstatus"],
                or_filters=or_filters,
                order_by="posting_date desc"
            )
        if not delivery_notes:
            return response("No Delivery Notes found", None, 200)
        for dn in delivery_notes:
            dn["posting_date"] = format_date(dn["posting_date"])
        if pagination:
            if len(delivery_notes) == limit  and db_count > (start + limit):
                data = {
                    "delivery_notes": delivery_notes,
                    "next_start": start + limit
                }
                return response("Delivery Notes fetched successfully", data, 200)
            else:
                data = {
                    "delivery_notes": delivery_notes,
                    "next_start": None
                }
                return response("Delivery Notes fetched successfully", data, 200)
        else:
            return response("Delivery Notes fetched successfully", {"delivery_notes": delivery_notes}, 200)
    except Exception as e:
        frappe.log_error(message=frappe.get_traceback(), title="Error in get_delivery_notes")
        return response("An error occurred while fetching Delivery Notes", str(e), 500)
    
@frappe.whitelist(allow_guest=True, methods="GET")
def get_delivery_note_details(delivery_note):
    try:
        frappe.set_user("Administrator")
        dn = frappe.get_doc("Delivery Note", delivery_note)
        dn_data = dn.as_dict()
        return response("Delivery Note details fetched successfully", dn_data, 200)
    except frappe.exceptions.DoesNotExistError:
        return response("Delivery Note does not exist", None, 404)
    except Exception as e:
        frappe.log_error(message=frappe.get_traceback(), title="Error in get_delivery_note_details")
        return response("An error occurred while fetching Delivery Note details", str(e), 500)