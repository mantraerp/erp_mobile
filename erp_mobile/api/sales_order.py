import frappe
from frappe.utils import getdate, format_date
from erp_mobile.api.masterdata import response

@frappe.whitelist(allow_guest=True,methods="GET")
def get_so_status():
    status = [field.options for field in frappe.get_meta("Sales Order").fields if field.fieldname == "status"][0].split("\n")
    status.remove("")
    status =  status
    response("Sales Order status fetched successfully", status, 200)

@frappe.whitelist(allow_guest=True, methods="GET")
def get_sales_orders(from_date=None, to_date=None, customer=None, start=None,status=None,search_string=None):
    try:
        frappe.set_user("Administrator")
        filters = {}
        if from_date and to_date:
            filters["transaction_date"] = ["between", [getdate(from_date,True), getdate(to_date,True)]]
        if customer:
            filters["customer"] = customer
        if status:
            filters["status"] = ["in", [status]]
        or_filters = []
        if search_string:
            or_filters.append(["name", "like", f"%{search_string}%"])
            or_filters.append(["customer_name", "like", f"%{search_string}%"])

        pagination=False
        if start:
            pagination=True
            start = int(start)
        limit = 10
        if pagination and not status:
            sales_orders = frappe.get_list(
                "Sales Order",
                filters=filters,
                fields=["name", "customer","customer_name", "transaction_date", "status", "grand_total", "currency","docstatus"],
                order_by="transaction_date desc",
                or_filters=or_filters,
                limit_start=start,
                limit_page_length=limit
            )
            db_count = frappe.db.count("Sales Order")
        else:
            sales_orders = frappe.get_list(
                "Sales Order",
                filters=filters,
                fields=["name", "customer", "customer_name","transaction_date", "status", "grand_total","currency","docstatus"],
                or_filters=or_filters,
                order_by="transaction_date desc"
            )
        if not sales_orders:
            return response("No Sales Orders found", None, 200)
        for so in sales_orders:
            so["transaction_date"] = format_date(so["transaction_date"])
        if pagination:
            if len(sales_orders) == limit  and db_count > (start + limit):
                data = {
                    "sales_orders": sales_orders,
                    "next_start": start + limit
                }
                return response("Sales Orders fetched successfully", data, 200)
            else:
                data = {
                    "sales_orders": sales_orders,
                    "start": None
                }
        else:
            return response("Sales Orders fetched successfully", {"sales_orders":sales_orders}, 200)
    except Exception as e:
        frappe.log_error(title="Error fetching Sales Orders", message=frappe.get_traceback(True))
        return response(f"Error fetching Sales Orders: {str(e)}", None, 500)
    

@frappe.whitelist(allow_guest=True,methods="GET")
def so_details(so_name):
    try:
        sales_order = frappe.get_doc("Sales Order", so_name)
        if not sales_order:
            return response("Sales Order not found", None, 404)
        return response("Sales Order details fetched successfully", sales_order.as_dict(), 200)
    except frappe.exceptions.DoesNotExistError:
        return response("Sales Order does not exist", None, 404)
    except Exception as e:
        frappe.log_error(message=frappe.get_traceback(True),title="Error fetching Sales Order details")
        return response(f"Error fetching Sales Order details: {str(e)}", None, 500)