import frappe # type: ignore
from frappe import _ # type: ignore



@frappe.whitelist()
def check_serial_no():
    
	frappe.log_error("title",str(frappe.session.user))
	query = "SELECT mobile_screen FROM `tabMobile Screen Allow` WHERE `user`='{}'".format(frappe.session.user)
	return frappe.db.sql(query,as_dict=1)


@frappe.whitelist()
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