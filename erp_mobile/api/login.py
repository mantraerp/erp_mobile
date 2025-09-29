import frappe # type: ignore
from frappe.twofactor import ( # type: ignore
	authenticate_for_2factor,
	confirm_otp_token,
	should_run_2fa,
)
from frappe.sessions import get_expiry_in_seconds # type: ignore
from frappe.auth import LoginManager # type: ignore

@frappe.whitelist(methods='POST', allow_guest=True)
def login(user,pwd):
	reply = {}
	reply['message']=''
	reply['status_code'] = 200
	reply['data']=[]
	try:
		login_manager = LoginManager()
		login_manager.authenticate(user=user,pwd=pwd)
		if should_run_2fa(user):
			authenticate_for_2factor(user)
			reply['message']= "Verification code has been sent to your registered email address."
			frappe.local.response["http_status_code"] = 200
			reply['status_code'] = 200
		else:
			login_manager.post_login()
			screens = frappe.get_all("Mobile Screen Allow",filters={"user": frappe.session.user},pluck="mobile_screen")
			allowed_screens = frappe.get_all("Mobile Screen",filters={"name": ["in", screens]},pluck="display_title")
			reply['message']='Logged In sucessfully'
			frappe.local.response['sid'] = frappe.session.sid
			frappe.local.response['max_age'] = get_expiry_in_seconds()
			frappe.local.response["allowed_screens"] = allowed_screens
			frappe.local.response["http_status_code"] = 200
			reply['status_code'] = 200

	except frappe.exceptions.AuthenticationError as e:
		reply['message']=f'Incorrect login credentials. {str(e)}'
		frappe.local.response["http_status_code"] = 401
		reply['status_code'] = 401

	except frappe.exceptions.SecurityException as e:
		reply['message']=f'Login failed. {str(e)}'
		frappe.local.response["http_status_code"] = 429
		reply['status_code'] = 429

	except Exception as e:
		frappe.log_error(frappe.get_traceback(True))
		reply['message']='User not able to login. {}'.format(str(e))
		frappe.local.response["http_status_code"] = 500
		reply['status_code'] = 500

	return reply


@frappe.whitelist(allow_guest=True,methods="POST")
def verify_code(user,pwd,otp,tmp_id):
	reply = {}
	reply['message']=''
	reply['status_code'] = 200
	reply['data']=[]
	try:
		login_manager = LoginManager()
		login_manager.authenticate(user=user,pwd=pwd)
		confirm_otp_token(login_manager,otp,tmp_id)
		login_manager.post_login()
		screens = frappe.get_all("Mobile Screen Allow",filters={"user": frappe.session.user},pluck="mobile_screen")
		allowed_screens = frappe.get_all("Mobile Screen",filters={"name": ["in", screens]},pluck="display_title")
		reply['message']='Logged In successfully'
		frappe.local.response['sid'] = frappe.session.sid
		frappe.local.response['max_age'] = get_expiry_in_seconds()
		frappe.local.response["allowed_screens"] = allowed_screens
		frappe.local.response["http_status_code"] = 200
		reply['status_code'] = 200

	except frappe.exceptions.AuthenticationError as e:
		reply['message']=f'Incorrect verification code. {str(e)}'
		frappe.local.response["http_status_code"] = 401
		reply['status_code'] = 401

	except Exception as e:
		frappe.log_error(frappe.get_traceback(True))
		reply['message']='User not able to login. {}'.format(str(e))
		frappe.local.response["http_status_code"] = 500
		reply['status_code'] = 500

	return reply