import frappe, urllib, json # type: ignore
from frappe import _ # type: ignore
from frappe.utils import getdate,format_date, get_first_day, get_last_day # type: ignore
from datetime import datetime

@frappe.whitelist(allow_guest=True)
def response(message, data, status_code):
    '''method to generates responses of an API
       args:
            message : response message string
            data : json object of the data
            success : True or False depending on the API response
            status_code : status of the request'''
    frappe.clear_messages()
    frappe.local.response["message"] = message
    frappe.local.response["data"] = data if data else None
    frappe.local.response["status_code"] = status_code
    frappe.local.response["http_status_code"] = status_code


def validate_columns(doctype, columns):
	'''method to validate if the columns requested in the API are valid columns of the doctype
	   args:
	        doctype : name of the doctype
	        columns : list of columns to be validated'''
	validated_columns = []
	valid_columns = [field.fieldname for field in frappe.get_meta(doctype).fields]
	for column in columns:
		if column in valid_columns or column == 'name':
			validated_columns.append(column)
	return validated_columns


@frappe.whitelist()
def check_serial_no():
    
	query = "SELECT mobile_screen FROM `tabMobile Screen Allow` WHERE `user`='{}'".format(frappe.session.user)
	return frappe.db.sql(query,as_dict=1)


@frappe.whitelist(methods=["GET"])
def get_master_list(doctype,search_text=None,start=None,limit=None):
	reply = {}
	reply['message']=''
	reply['status_code'] = 200
	reply['data']=[]
	try:
		pagination=False
		if start:
			pagination=True
			start = int(start)
		limit = int(limit) if limit else 20
		if pagination:
			master_list = frappe.get_list(doctype, fields=["name"], or_filters=[["name", "LIKE", "%{}%".format(search_text)]] if search_text else [], order_by="creation desc", start=start, page_length=limit,pluck="name")
			db_count = len(frappe.get_list(doctype, order_by="creation desc"))
		else:
			master_list = frappe.get_list(doctype, fields=["name"], or_filters=[["name", "LIKE", "%{}%".format(search_text)]] if search_text else [], order_by="creation desc",pluck="name")

		if not master_list:
			reply['message'] = _("No records found")
			frappe.local.response["http_status_code"] = 204
			reply['status_code'] = 204
			return reply

		if pagination:
			if len(master_list) == limit and db_count != start + limit:
				data = master_list
				reply['start'] = start + limit
			else:
				data = master_list
				reply['start'] = None
			reply['data'] = data
			frappe.local.response["http_status_code"] = 200
			reply['message'] = _("Records fetched successfully")

		else:
			reply['data'] = master_list
			frappe.local.response["http_status_code"] = 200
			reply['message'] = _("Records fetched successfully")

	except frappe.exceptions.DoesNotExistError:
		reply['message'] = _("Doctype: {} does not exist").format(doctype)
		frappe.local.response["http_status_code"] = 404
		reply['status_code'] = 404

	except Exception as e:
		reply['message'] = _('Error fetching master list: {}').format(str(e))
		frappe.log_error(title="erp_mobile.api.masterdata.get_master_list_limited",message=frappe.get_traceback(True))
		frappe.local.response["http_status_code"] = 500
		reply['status_code'] = 500

	frappe.local.response['data'] = reply['data']
	frappe.local.response['message'] = reply['message']
	frappe.local.response['start'] = reply.get('start')
	frappe.local.response['status_code'] = reply['status_code']
	# return reply


# http://192.168.11.66:8017/api/method/erp_mobile.api.masterdata.get_user_profile?user=ravi.patel@mantratec.com
@frappe.whitelist(methods=["GET"],allow_guest=True)
def get_user_profile(user):
	try:
		user = frappe.get_doc("User",user)
		data = {
			"full_name": user.full_name,
			"email": user.email,
			"employee_code": frappe.db.get_value("Employee",{"user_id":user.email},"name"),
			"designation": frappe.db.get_value("Employee",{"user_id":user.email},"designation"),
			"gender": user.gender,
			"phone": user.phone,
			"mobile_no": user.mobile_no,
			"image": (frappe.utils.get_url() + urllib.parse.quote(user.user_image) if user.user_image else ''),
			"birth_date": user.get_formatted("birth_date"),
		}
		return response(_("User profile fetched successfully"), data, 200)
	except frappe.exceptions.DoesNotExistError:
		return response(_("User does not exist"), None, 404)
	except Exception as e:
		frappe.log_error(title="erp_mobile.api.masterdata.get_user_profile",message=frappe.get_traceback(True))
		return response(_('Error fetching user profile: {}').format(str(e)), None, 500)


# http://192.168.11.66:8017/api/method/erp_mobile.api.masterdata.get_salary_slips?employee_code=HR-EMP-01644&from_date=01-03-2025&to_date=28-09-2025
@frappe.whitelist(methods="GET")
def get_salary_slips(employee_code,from_date,to_date):
	try:
		filters={}
		filters["employee"]=employee_code
		filters["start_date"]=["between",[getdate(from_date,True),getdate(to_date,True)]]
		filters["end_date"]=["between",[getdate(from_date,True),getdate(to_date,True)]]
		filters["docstatus"]=1
		fields = ['name','employee_name','employee as employee_code','start_date','end_date','total_working_days','payment_days','payroll_frequency','salary_structure','gross_pay','net_pay','rounded_total as round_net','total_in_words','total_deduction','current_month_income_tax','bank_name','bank_account_no','custom_payment_status as payment_status']
		fields = validate_columns("Salary Slip",fields)
		salary_slips = frappe.db.get_all("Salary Slip",filters=filters,fields=fields,order_by="creation desc",limit_page_length=50)
		if not salary_slips:
			return response(_("No records found"), None, 200)
		for s in salary_slips:

			s["earnings"] = frappe.db.get_all("Salary Detail",filters={"parent":s.name,"parentfield":"earnings"},fields=["salary_component","amount"])
			print(s.name)
			s["deductions"] = frappe.db.get_all("Salary Detail",filters={"parent":s.name,"parentfield":"deductions"},fields=["salary_component","amount"])
			s['start_date'] = format_date(s['start_date'])
			s['end_date'] = format_date(s['end_date'])
		return response(_("Records fetched successfully"), salary_slips, 200)
	except Exception as e:
		frappe.log_error(title="erp_mobile.api.masterdata.get_salary_slips",message=frappe.get_traceback(True))
		return response(_('Error fetching salary slips: {}').format(str(e)), None, 500)


# http://192.168.11.66:8017/api/method/erp_mobile.api.masterdata.download_salary_slip?salary_slip=Sal Slip/HR-EMP-01603/00001
@frappe.whitelist(methods="GET", allow_guest=True)
def download_salary_slip(salary_slip):
	try:
		pdf = frappe.attach_print('Salary Slip', salary_slip, file_name=salary_slip, password=None)
		frappe.local.response["http_status_code"] = 200
		frappe.local.response['type'] = 'download'
		frappe.local.response['filename'] = pdf.get('fname')
		frappe.local.response['filecontent'] = pdf.get('fcontent')
	except frappe.exceptions.DoesNotExistError:
		return response(_("Salary Slip does not exist"), None, 404)
	except Exception as e:
		frappe.log_error(title="erp_mobile.api.masterdata.download_salary_slip",message=frappe.get_traceback(True))
		return response(_('Error fetching salary slip PDF: {}').format(str(e)), None, 500)


#  http://192.168.11.66:8017/api/method/erp_mobile.api.masterdata.get_attendance?employee_code=MN001723&from_date=09-03-2024&to_date=09-03-2025
@frappe.whitelist(methods="GET",allow_guest=True)
def get_attendance(employee_code, from_date, to_date):
	try:
		filters = {}
		filters["employee"] = employee_code
		filters["attendance_date"] = ["between", [getdate(from_date, True), getdate(to_date, True)]]
		filters["docstatus"] = 1
		fields = ['name', 'employee_name', 'attendance_date','employee as employee_code', 'attendance_date', 'status','leave_type','custom_minop_status as minop_status']
		fields = validate_columns("Attendance", fields)
		attendance_records = frappe.db.get_all("Attendance", filters=filters, fields=fields, order_by="attendance_date desc")

		if not attendance_records:
			return response(_("No records found"), None, 200)
		attendance_count = {
			"Present": sum(1 for record in attendance_records if record['status'] == 'Present'),
			"Absent": sum(1 for record in attendance_records if record['status'] == 'Absent'),
			"On Leave": sum(1 for record in attendance_records if record['status'] == 'On Leave'),
			"Half Day": sum(1 for record in attendance_records if record['status'] == 'Half Day'),
			"Holiday": sum(1 for record in attendance_records if record['status'] == 'Holiday'),
		}
		attendance_count["Total Days"] = len(attendance_records)
		for record in attendance_records:
			record['attendance_date'] = format_date(record['attendance_date'])
		frappe.local.response['attendance_count'] = attendance_count
		return response(_("Records fetched successfully"), attendance_records, 200)
	except (ValueError, TypeError):
		return response(_("Invalid month or year"), None, 400)
	except Exception as e:
		frappe.log_error(title="erp_mobile.api.masterdata.get_attendance", message=frappe.get_traceback(True))
		return response(_('Error fetching attendance records: {}').format(str(e)), None, 500)

# http://192.168.11.66:8017/api/method/erp_mobile.api.masterdata.get_expences?employee_code=HR-EMP-00036&from_date=01-03-2024&to_date=09-08-2025
@frappe.whitelist(methods="GET")
def get_expences(employee_code, from_date, to_date):
	try:
		filters={}
		filters["employee"]=employee_code
		filters["expense_date"]=["between",[getdate(from_date,True),getdate(to_date,True)]]
		filters["docstatus"]= ['in', [0,1]]
		fields = ['name','posting_date','employee_name','employee as employee_code','custom_expense_grouping','total_claimed_amount as total_amount','status','company']
		fields = validate_columns("Expense Claim",fields)
		expence_list = frappe.db.get_list("Expense Claim",filters=filters,fields=fields)
		if not expence_list:
			return response(_("No records found"), None, 200)
		for e in expence_list:
			e['posting_date'] = format_date(e['posting_date'])
			expences = frappe.db.get_all("Expense Claim Detail",filters={"parent":e.name},fields=['expense_type','description','amount','sanctioned_amount','cost_center','expense_date'])
			for es in expences:
				es['expense_date'] = format_date(es['expense_date'])
				es['description'] = frappe.utils.strip_html_tags(es['description']) if es['description'] else None
			e['expenses'] = expences
		return response(_("Records fetched successfully"), expence_list, 200)
	except Exception as e:
		frappe.log_error(title="erp_mobile.api.masterdata.get_expences",message=frappe.get_traceback(True))
		return response(_('Error fetching expense claims: {}').format(str(e)), None, 500)


@frappe.whitelist(methods="POST",allow_guest=True)
def create_expense_claim():
	try:
		data = json.loads(frappe.request.get_data())
		if not any([data.get("employee"), data.get("custom_expense_grouping"), data.get("expense_approver"), data.get("expenses")]):
			return response(_("Employee, Custom Expense Grouping, Expense Approver, and Expenses are mandatory fields"), None, 400)

		expense_claim = frappe.new_doc("Expense Claim")
		expense_claim.update({
			"employee": data.get("employee"),
			"custom_expense_grouping": data.get("custom_expense_grouping"),
			"expense_approver": data.get("expense_approver"),
			"expenses": data.get("expenses"),
			"payable_account": "Creditors - MSIPL",

		})
		expense_claim.insert(ignore_permissions=True)
		return response(_("Expense Claim {} created successfully").format(expense_claim.name), {"expense_claim": expense_claim.name}, 201)
	except frappe.exceptions.MandatoryError as e:
		return response(_('Mandatory fields are missing: {}').format(str(e)), None, 400)
	except frappe.exceptions.ValidationError as e:
		frappe.log_error(title="erp_mobile.api.masterdata.create_expense_claim",message=frappe.get_traceback(True))
		return response(_('{}').format(str(e)), None, 400)
	except Exception as e:
		frappe.log_error(title="erp_mobile.api.masterdata.create_expense_claim",message=frappe.get_traceback(True))
		return response(_('{}').format(str(e)), None, 500)
