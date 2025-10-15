import frappe
from erp_mobile.api.masterdata import response
from frappe.utils import getdate, format_date


@frappe.whitelist(allow_guest=True, methods="GET")
def get_po_status():
    status = [field.options for field in frappe.get_meta("Purchase Order").fields if field.fieldname == "status"][0].split("\n")
    status.remove("")
    status =  status
    response("Purchase Order status fetched successfully", status, 200)


@frappe.whitelist(allow_guest=True, methods="GET")
def get_purchase_orders(from_date=None, to_date=None, supplier=None, start=None,status=None,search_string=None):
    try:
        frappe.set_user("Administrator")
        filters = {}
        if from_date and to_date:
            filters["transaction_date"] = ["between", [getdate(from_date,True), getdate(to_date,True)]]
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
            purchase_orders = frappe.get_list(
                "Purchase Order",
                filters=filters,
                fields=["name", "supplier","supplier_name", "transaction_date", "status", "grand_total", "currency","docstatus"],
                order_by="transaction_date desc",
                or_filters=or_filters,
                limit_start=start,
                limit_page_length=limit
            )
            db_count = frappe.db.count("Purchase Order")
        else:
            purchase_orders = frappe.get_list(
                "Purchase Order",
                filters=filters,
                fields=["name", "supplier", "supplier_name","transaction_date", "status", "grand_total","currency","docstatus"],
                or_filters=or_filters,
                order_by="transaction_date desc"
            )
        if not purchase_orders:
            return response("No Purchase Orders found", None, 200)
        for po in purchase_orders:
            po["transaction_date"] = format_date(po["transaction_date"])
        if pagination:
            if len(purchase_orders) == limit  and db_count > (start + limit):
                data = {
                    "purchase_orders": purchase_orders,
                    "start": start + limit
                }
            else:
                data = {
                    "purchase_orders": purchase_orders,
                    "start": None
                }
        else:
            data = {
                "purchase_orders": purchase_orders
            }
        return response("Purchase Orders fetched successfully", data, 200)
    except Exception as e:
        frappe.log_error(message=frappe.get_traceback(with_context=True), title="Error fetching purchase orders")
        return response(f"Failed to fetch purchase orders {str(e)}", None, 500)
    

@frappe.whitelist(allow_guest=True,methods="GET")
def purchase_order_details(purchase_order):
    try:
        po = frappe.get_doc("Purchase Order", purchase_order)
        if not po:
            return response("Purchase Order does not exist", None, 404)
        return response("Purchase Order details fetched successfully", po.as_dict(), 200)
    except frappe.exceptions.DoesNotExistError:
        return response("Purchase Order does not exist", None, 404)
    except Exception as e:
        frappe.log_error(message=frappe.get_traceback(with_context=True), title="Error fetching purchase order details")
        return response(f"Failed to fetch purchase order details {str(e)}", None, 500)