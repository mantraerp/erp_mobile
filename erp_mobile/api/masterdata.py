import frappe # type: ignore
from frappe import _ # type: ignore



@frappe.whitelist()
def check_serial_no():
    
	frappe.log_error("title",str(frappe.session.user))
	query = "SELECT mobile_screen FROM `tabMobile Screen Allow` WHERE `user`='{}'".format(frappe.session.user)
	return frappe.db.sql(query,as_dict=1)