import frappe
from erp_mobile.api.masterdata import response
from frappe import _
from frappe.utils.user import get_user_fullname

@frappe.whitelist(allow_guest=True,methods="GET")
def get_activity_logs(doctype, name):
    """
    Return a JSON list of timeline activity items for a given document
    """
    try:
        doc = frappe.get_doc(doctype, name)
        doc_info = {
            "comments": frappe.get_all("Comment", filters={"reference_doctype": doctype, "reference_name": name}, order_by="creation asc",fields=["*"]),
            "versions": frappe.get_all("Version", filters={"ref_doctype": doctype, "docname": name}, order_by="creation asc", fields=["data", "creation", "owner"])
        }

        activity = []

        if doc.creation:
            activity.append({
                "timestamp": doc.creation,
                "content": f"{get_user_fullname(doc.owner)} created this"
            })

        if doc.modified:
            activity.append({
                "timestamp": doc.modified,
                "content": f"{get_user_fullname(doc.modified_by)} last edited this"
            })

        for comment in doc_info.get("comments", []):
            if comment.comment_type == "Workflow":
                content = f"Status changed to {comment.content} by {get_user_fullname(comment.owner)}"
                activity.append({
                    "timestamp": comment.creation,
                    "content": content
                })
        versions = []
        for version in doc_info.get("versions", []):
            creation = version.get("creation")
            owner = version.get("owner")
            version = frappe.parse_json(version.data)
            changes = version.get("changed")
            filtered = [item for item in changes if item[0] in ["status"]]
            if filtered:
                versions.append({"status":filtered, "creation":creation, "owner":get_user_fullname(owner)})

        print(versions)
        for entry in versions:
            changes = ", ".join([f"{o} to {n}" for f, o, n in entry["status"]])
            activity.append({"timestamp": entry["creation"], "content": f"{entry['owner']} updated status from ({changes})".replace("(", "").replace(")", "")})

        activity = sorted(activity, key=lambda x: x['timestamp'], reverse=True)
        for act in activity:
            act["timestamp"] = frappe.utils.format_datetime(act["timestamp"])
        return response(_("Activity logs fetched successfully"), activity, 200)
    except Exception as e:
        frappe.log_error(title="Error fetching activity logs", message=frappe.get_traceback(True))
        return response(f"Error fetching activity logs: {str(e)}", None, 500)