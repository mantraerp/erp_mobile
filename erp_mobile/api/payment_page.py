
import frappe
from erp_mobile.api.masterdata import response
from frappe import _
from frappe.utils import getdate,nowdate
import calendar



@frappe.whitelist(allow_guest=True, methods=["GET"])
def get_payment_entries(bank_account=None):
    try:
        if not bank_account:
            return response("Bank Account is required", None, 400)

        # Fetch allowed modes of payment for this bank account
        mode_of_payment = [
            d.mode_of_payment
            for d in frappe.db.get_all(
                "Mode of Payment Setting", 
                filters={"parent": bank_account},
                fields=["mode_of_payment"]
            )
        ] or []

        # Fetch all approved payment entries for this bank account
        query = """
            SELECT 
                name, party, party_name, status, remarks,
                base_paid_amount_after_tax AS amount,
                workflow_state, custom_approved_by
            FROM `tabPayment Entry`
            WHERE (custom_unique_batch_number IS NULL OR custom_unique_batch_number = "")
              AND workflow_state = 'Approved'
              AND payment_type = 'Pay'
              AND bank_account = %s
              AND mode_of_payment IN %s
            ORDER BY modified DESC
        """
        entries = frappe.db.sql(query, (bank_account, tuple(mode_of_payment)), as_dict=True)

        if not entries:
            return response("No payment entries found", {"payment_entries": []}, 200)

        return response("Payment entries fetched successfully", {
            "payment_entries": entries
        }, 200)

    except Exception as e:
        frappe.log_error(frappe.get_traceback(), "get_payment_entries Error")
        return response(f"Error: {str(e)}", None, 500)




@frappe.whitelist(allow_guest=True, methods=["GET"])
def get_payment_entry_detail(payment_entry=None):
    try:
        if not payment_entry:
            return response("Payment Entry name is required", None, 400)

        doc = frappe.get_doc("Payment Entry", payment_entry)
        refs = [{
            "reference_doctype": r.reference_doctype,
            "reference_name": r.reference_name,
            "allocated_amount": r.allocated_amount
        } for r in doc.references]

        return response("Payment entry details fetched", {
            "id": doc.name,
            "party": doc.party,
            "party_name": doc.party_name,
            "remarks": doc.remarks,
            "paid_amount": doc.paid_amount,
            "workflow_state": doc.workflow_state,
            "references": refs
        }, 200)

    except Exception as e:
        frappe.log_error(frappe.get_traceback(), "get_payment_entry_detail Error")
        return response(f"Error: {str(e)}", None, 500)



@frappe.whitelist(allow_guest=True, methods=["POST"])
def cancel_payment_entries():
    try:
        data = frappe.form_dict
        entry_ids = frappe.parse_json(data.get("payment_entry_ids"))
        if not entry_ids:
            return response("No entries provided", None, 400)

        for pid in entry_ids:
            if frappe.db.exists("Payment Entry", pid):
                frappe.db.set_value("Payment Entry", pid, "workflow_state", "Cancelled")
        frappe.db.commit()

        return response("Payment entries cancelled successfully", None, 200)
    except Exception as e:
        frappe.log_error(frappe.get_traceback(), "cancel_payment_entries Error")
        return response(f"Error: {str(e)}", None, 500)


@frappe.whitelist(allow_guest=True, methods=["POST"])
def hold_salary_slip():
    try:
        salary_slip_id = frappe.form_dict.get("salary_slip_id")
        if not salary_slip_id:
            return response("Salary Slip ID is required", None, 400)

        frappe.db.set_value("Salary Slip", salary_slip_id, "custom_payment_status", "Hold")
        frappe.db.commit()
        return response("Salary Slip set to Hold", None, 200)
    except Exception as e:
        frappe.log_error(frappe.get_traceback(), "hold_salary_slip Error")
        return response(f"Error: {str(e)}", None, 500)



@frappe.whitelist(allow_guest=True, methods=["GET"])
def get_banks():
    """
    Return all active Banks.
    """
    try:
        banks = frappe.get_all(
            "Bank",
            fields=["bank_name"],
            order_by="bank_name asc"
        )

        if not banks:
            return response("No banks found", {"banks": []}, 200)

        return response("Banks fetched successfully", {"banks": banks}, 200)

    except Exception as e:
        frappe.log_error(frappe.get_traceback(), "get_banks Error")
        return response(f"Error fetching banks: {str(e)}", None, 500)


@frappe.whitelist(allow_guest=True, methods=["GET"])
def get_bank_accounts(bank=None):
    """
    Return all Bank Accounts.
    Optionally filter by Bank name.
    """
    try:
        filters = {}
        if bank:
            filters["bank"] = bank

        accounts = frappe.get_all(
            "Bank Integration",
            filters=filters,
            fields=[
                "name"
            ],
       
        )
         

        if not accounts:
            return response("No bank accounts found", {"bank_accounts": []}, 200)

        return response("Bank accounts fetched successfully", {"bank_accounts": accounts}, 200)

    except Exception as e:
        frappe.log_error(frappe.get_traceback(), "get_bank_accounts Error")
        return response(f"Error fetching bank accounts: {str(e)}", None, 500)


@frappe.whitelist(allow_guest=True, methods=["GET"])
def get_salary_slips(payroll_entry=None):
    """
    Fetch Salary Slips for a given month, filtered by:
    - Payroll Entry submitted
    - Salary Slip not yet paid (custom_payment_status not 'Success' or 'Hold')
    """
    try:
        # Step 1: Build Payroll Entry filters
        

        # Step 3: Get Salary Slips for these Payroll Entries
        salary_slips = frappe.db.sql("""
            SELECT 
                employee AS party,
                employee_name AS party_name,
                net_pay AS base_paid_amount_after_tax,
                bank_name,
                bank_account_no,
                posting_date,
                name,
                payroll_entry
            FROM `tabSalary Slip`
            WHERE payroll_entry = %s
              AND docstatus = 1
              AND custom_payment_status NOT IN ('Success','Hold')
        """, (payroll_entry,), as_dict=True)
        if not salary_slips:
            return response("No Payroll Entries found", {"salary_slips": []}, 200)
        return response("Salary Slips fetched successfully", {"salary_slips": salary_slips}, 200)

    except Exception as e:
        frappe.log_error(frappe.get_traceback(), "get_salary_slips Error")
        return {"message": f"Error fetching salary slips: {str(e)}", "salary_slips": []}


@frappe.whitelist(allow_guest=True, methods=["GET"])
def get_payroll_entries(month=None):
    """
    Fetch submitted Payroll Entries filtered by month and additional conditions.
    """
    try:
        filters = {
            "status": "Submitted",
            "custom_salary_slip_file_generated": 0,
            "custom_payroll_entry_approved": 1
        }

        if month:
            # Map month name to month number
            month_map = {
                "January": 1, "February": 2, "March": 3, "April": 4,
                "May": 5, "June": 6, "July": 7, "August": 8,
                "September": 9, "October": 10, "November": 11, "December": 12
            }

            month_number = month_map.get(month, 1)
            year = int(nowdate().split("-")[0])  # current year

            # Get number of days in the month (handles leap year automatically)
            days_in_month = calendar.monthrange(year, month_number)[1]

            start_date = f"{year}-{month_number:02d}-01"
            end_date = f"{year}-{month_number:02d}-{days_in_month:02d}"

            # Add date filters
            filters["start_date"] = [">=", start_date]
            filters["end_date"] = ["<=", end_date]  

        payroll_entries = frappe.get_all(
            "Payroll Entry",
            filters=filters,
            fields=["name"],
            order_by="creation desc"
        )

        if not payroll_entries:
            return response("No Payroll Entries found", {"payroll_entries": []}, 200)

        return response("Payroll Entries fetched successfully", {"payroll_entries": payroll_entries}, 200)

    except Exception as e:
        frappe.log_error(frappe.get_traceback(), "get_payroll_entries Error")
        return response(f"Error fetching payroll entries: {str(e)}", None, 500)


@frappe.whitelist(allow_guest=True, methods=["GET"])
def get_payroll_months():
    """
    Return static month list (January to December).
    """
    try:
        months = [
            "January",
            "February",
            "March",
            "April",
            "May",
            "June",
            "July",
            "August",
            "September",
            "October",
            "November",
            "December",
        ]

        return response("Months fetched successfully", {"months": months}, 200)

    except Exception as e:
        frappe.log_error(frappe.get_traceback(), "get_payroll_months Error")
        return response(f"Error fetching payroll months: {str(e)}", None, 500)
