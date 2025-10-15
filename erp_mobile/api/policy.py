import frappe
from erp_mobile.api.masterdata import response
from frappe.utils import getdate, format_date

@frappe.whitelist(allow_guest=True, methods="GET")
def get_policies():
    try:
        frappe.set_user("Administrator")
        policies = frappe.get_list(
            "Policy",
            fields=["name","policy_name","policy_no___endorsement_no as policy_no","insurance_company","expired","renew"],
        )
        if not policies:
            return response("No Policies found", None, 200)
        return response("Policies fetched successfully", policies, 200)
    except Exception as e:
        frappe.log_error(message=frappe.get_traceback(with_context=True), title="Error while fetching policies")
        return response("Error while fetching policies", None, 500)

@frappe.whitelist(allow_guest=True, methods="GET")
def get_policy_details(policy):
    try:
        frappe.set_user("Administrator")
        pol = frappe.get_doc("Policy", policy)
        pol_data = pol.as_dict()
        return response("Policy details fetched successfully", pol_data, 200)
    except frappe.exceptions.DoesNotExistError:
        return response("Policy does not exist", None, 404)
    except Exception as e:
        frappe.log_error(message=frappe.get_traceback(with_context=True), title="Error while fetching policy details")
        return response("Error while fetching policy details", None, 500)