import frappe
from erp_mobile.api.masterdata import response
from frappe.utils import formatdate

@frappe.whitelist(allow_guest=True,methods=['GET']) 
def get_holidays(employee_code):
    try:
        data = frappe.db.get_values("Employee", {"name": employee_code}, ["holiday_list", "company"],as_dict=True)
        if not data:
            return response("Employee Not Found", None,200)
        holiday_list,company = data[0].holiday_list,data[0].company
        if not holiday_list:
            holiday_list = frappe.db.get_value("Company", company, "default_holiday_list")
        if not holiday_list:
            return response("No Holiday List Assigned", None,200)
        holiday_list_data = frappe.get_all("Holiday", filters={"parent": holiday_list}, fields=["holiday_date", "description"])
        for holiday in holiday_list_data:
            holiday["holiday_date"] = formatdate(holiday["holiday_date"])
        return response("Success",holiday_list_data,200)
    except Exception as e:
        frappe.log_error(message=frappe.get_traceback(with_context=True), title="Error in fetching holidays")
        return response("Error while fetching holidays", None,500)