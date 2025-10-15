import frappe # type: ignore
from frappe import _ # type: ignore
# 192.168.11.66:8017/api/method/erp_mobile.api.serial_no.track_serial_number?serial_no=SN-00001
#Serial Number traking which when this serial number is used
@frappe.whitelist(allow_guest=True)
def track_serial_number(serial_no):

    reply={}
    reply['message']=""
    reply['success']=True
    reply['status_code']=200
    reply['serial_data'] = []
    reply['sub_serial_data'] = []
    reply['data']=[]
    reply['last_transaction'] = []

    query = " SELECT * FROM `tabSerial No` WHERE name = '{}'".format(serial_no)
    sn_info = frappe.db.sql(query, as_dict=True)

    if not sn_info:
        reply["message"] = "Serial Number Not Found In the System"
        reply["success"] = False
        reply["status_code"] = 404
        return reply


    sn_results = []
    sn_obj = {}

    if sn_info:
        serial_info = sn_info[0]
        sn_obj["serial_no"] = serial_info["name"]
        sn_obj["item_code"] = serial_info["item_code"]
        sn_obj["item_name"] = serial_info["item_name"]
        sn_obj["warehouse"] = serial_info["warehouse"]
        sn_obj["warranty_expiry_date"] = serial_info["warranty_expiry_date"]
        sn_obj["amc_expiry_date"] = serial_info["amc_expiry_date"]
        sn_obj['status'] = serial_info['status']
        sn_obj['description'] = serial_info['description']
        sn_results.append(sn_obj)
    reply['serial_data'] = sn_results

    query = " SELECT name, sub_item_code FROM `tabSub Serial No` WHERE parent_serial_no = '{}'".format(serial_no)
    sub_sn_results = frappe.db.sql(query,as_dict=True)

    sub_srn_result = []

    for sub_sn_info in sub_sn_results:
        sub_sn_obj = {
            "sub_serial_number": sub_sn_info["name"],
            "sub_item_code": sub_sn_info["sub_item_code"]
        }
        sub_srn_result.append(sub_sn_obj)
    reply['sub_serial_data'] = sub_srn_result
    

    query = "SELECT sbb.name as bundle_name,sbb.voucher_type, sbb.item_code, sbb.voucher_no,sbb.type_of_transaction FROM `tabSerial and Batch Entry` sbbi JOIN `tabSerial and Batch Bundle` sbb ON sbbi.parent = sbb.name WHERE sbb.docstatus != 2  AND sbbi.serial_no = '{}'".format(serial_no)
    results = frappe.db.sql(query,as_dict=True)

    return_result = []
    for row in results:
        voucher_type = row['voucher_type']
        voucher_no = row['voucher_no']
        type_of_transaction = row['type_of_transaction']
        item_code = row['item_code']
        if not voucher_type and not voucher_no:
            continue
        
        query = f"SELECT name as document_name FROM `tab{voucher_type}` WHERE name = %s"
        results = frappe.db.sql(query,voucher_no,as_dict=True)

        if not results:
            reply["message"] = ""
            reply["success"] = False
            reply["status_code"] = 404
            return reply

        for i in results:
            obj = {}
            posting_date = 'transaction_date' if voucher_type in ['Purchase Order','Sales Order','Material Request'] else ('' if voucher_type=='Pick List' else 'posting_date')
            obj['document']= voucher_type
            obj['document_name']= i['document_name']
            obj['posting_date'] = frappe.db.get_value(voucher_type,i['document_name'],posting_date) if posting_date else ''

            if voucher_type == "Delivery Note":
                # query = "SELECT customer,customer_name,is_return From `tabDelivery Note` WHERE name= '{}'".format(i['document_name'])
                # results = frappe.db.sql(query)
                
                dn_customer = frappe.db.get_value("Delivery Note", i['document_name'], "customer")
                dn_customer_name = frappe.db.get_value("Delivery Note", i['document_name'], "customer_name")
                dn_is_return = frappe.db.get_value("Delivery Note", i['document_name'], "is_return")

                if not dn_customer_name:
                    dn_customer_name = frappe.db.get_value("Customer", dn_customer, "customer_name")

                obj['dn_customer'] = dn_customer
                obj['dn_customer_name'] = dn_customer_name

                if dn_is_return:
                    obj['dn_return'] = dn_is_return
                    obj['return_text'] = "Return" 

        
                link_doc = "SELECT item_code, against_sales_order, custom_warranty_time_periodin_months, custom_rd_service_time_period, against_sales_invoice FROM `tabDelivery Note Item` AS dni JOIN `tabDelivery Note` AS dn ON dn.name = dni.parent WHERE dni.parent = '{}' AND dn.is_return = 0 AND item_code = '{}'".format(i['document_name'],item_code)
                link_query = frappe.db.sql(link_doc,as_dict=True)

                # dn_warranty_time_period = link_query[0]['custom_warranty_time_periodin_months'] if link_query else ''
                # dn_rd_service_time_period = link_query[0]['custom_rd_service_time_period'] if link_query else ''
                # item_code = link_query[0]['item_code'] if link_query else ''

                # obj["dn_warranty_time_period"] = dn_warranty_time_period
                # obj["dn_rd_service_time_period"] = dn_rd_service_time_period

                linked_documents = set()

                for link in link_query:
                    so_date = frappe.db.get_value("Sales Order", link.against_sales_order, "transaction_date") if link.against_sales_order else ''
                    si_date = frappe.db.get_value("Sales Invoice", link.against_sales_invoice, "posting_date") if link.against_sales_invoice else ''

                    if link.against_sales_order:
                        so_customer = frappe.db.get_value("Sales Order", link.against_sales_order, "customer")
                        so_customer_name = frappe.db.get_value("Sales Order", link.against_sales_order, "customer_name")

                        if not so_customer_name:
                            so_customer_name = frappe.db.get_value("Customer", so_customer, "customer_name")

                        item_warranty = "SELECT item_code,custom_warranty_time_periodin_months,custom_rd_service_time_period FROM `tabSales Order Item` WHERE parent = '{}' AND item_code = '{}'".format(link.against_sales_order,link.item_code)
                        item_result = frappe.db.sql(item_warranty,as_dict=True)

                        so_warranty_time_period = item_result[0]['custom_warranty_time_periodin_months'] if item_result else ''
                        so_rd_service_time_period = item_result[0]['custom_rd_service_time_period'] if item_result else ''
                        item_code = item_result[0]['item_code'] if item_result else ''
 
                        key = ("Sales Order", link.against_sales_order,link.item_code)
                        if key not in linked_documents:
                            results = {
                                "document": "Sales Order",
                                "document_name": link.against_sales_order,
                                "posting_date": so_date,
                                "delivey_note":i['document_name'],
                                "so_customer": so_customer,
                                "so_customer_name": so_customer_name,
                                "so_item_code" : item_code,
                                "so_warranty_time_period" : so_warranty_time_period,
                                "so_rd_service_time_period" : so_rd_service_time_period
                            }
                            return_result.append(results)
                            linked_documents.add(key)

                    if link.against_sales_invoice:
                        si_customer = frappe.db.get_value("Sales Invoice", link.against_sales_invoice, "customer")
                        si_customer_name = frappe.db.get_value("Sales Invoice", link.against_sales_invoice, "customer_name")
                        
                        if not si_customer_name:
                            si_customer_name = frappe.db.get_value("Customer", si_customer, "customer_name")

                        item_warranty = "SELECT item_code, custom_warranty_time_periodin_months,custom_rd_service_time_period FROM `tabSales Invoice Item` WHERE parent = '{}' AND item_code = '{}'".format(link.against_sales_invoice,link.item_code)
                        item_result = frappe.db.sql(item_warranty,as_dict=True)

                        si_warranty_time_period = item_result[0]['custom_warranty_time_periodin_months'] if item_result else ''
                        si_rd_service_time_period = item_result[0]['custom_rd_service_time_period'] if item_result else ''
                        item_code = item_result[0]['item_code'] if item_result else ''

                        key = ("Sales Invoice", link.against_sales_invoice,link.item_code)
                        if key not in linked_documents:
                            results = {
                                "document": "Sales Invoice",
                                "document_name": link.against_sales_invoice,
                                "posting_date": si_date,
                                "delivey_note":i['document_name'],
                                "si_customer": si_customer,
                                "si_customer_name" : si_customer_name,
                                "si_item_code" : item_code,
                                "si_warranty_time_period" : si_warranty_time_period,
                                "si_rd_service_time_period" : si_rd_service_time_period
                            }
                            
                            # if dn_is_return:
                            #     results["dn_return"] = dn_is_return
                            #     results["return_text"] = "Return"
                            return_result.append(results)
                            linked_documents.add(key)

            if voucher_type == "Stock Entry":
                if type_of_transaction == "Outward":
                        obj['type_of_transaction'] = "Internal Transfer"
                else:
                    obj['type_of_transaction'] = type_of_transaction
            
           
            quality_inspection = "SELECT DISTINCT name,report_date,status FROM `tabQuality Inspection` WHERE `reference_name` = '{}'".format(i['document_name'])
            qi_results = frappe.db.sql(quality_inspection,as_dict=True)

            inspection_key = set()
            if qi_results:
                for qi in qi_results:
                    key = ("Quality Inspection", qi["name"],qi["report_date"])
                    if not key in inspection_key:
                        results = {
                            "document": "Quality Inspection",
                            "document_name" : qi["name"],
                            "posting_date" : qi["report_date"],
                            "status" : qi["status"]
                        }
                        return_result.append(results)
                        inspection_key.add(key)
                        
        priority = {
            "Purchase Receipt": 1,
            "Stock Entry": 2,
            "Subcontracting Receipt": 3,
            "Sales Order": 4,
            "Pick List" : 5,
            "Delivery Note": 6,
            "Sales Invoice": 7
        }

        return_result.append(obj)
        return_result = sorted(return_result, key=lambda x: priority.get(x["document"], 99))
        
        latest_doc = None
        latest_date = None

        for r in return_result:
            if r['posting_date']:
                pd = frappe.utils.getdate(r["posting_date"])
                if not latest_date or pd > latest_date:
                    latest_date = pd
                    latest_doc = r

        last_transaction = None
        if latest_doc:
            last_transaction = {
                "voucher_type": latest_doc.get("document"),
                "voucher_no": latest_doc.get("document_name")
            }

    reply['data'] = return_result
    reply['last_transaction'] = last_transaction
    return reply


#Track the batch details
@frappe.whitelist(allow_guest=True)
def track_batch_details(batch_no):
    reply={}
    reply['message']=""
    reply['success']=True
    reply['status_code']=200
    reply['batch_data'] = []
    reply['data']=[]

    query = " SELECT * FROM `tabBatch` WHERE name = '{}'".format(batch_no)
    bn_info = frappe.db.sql(query, as_dict=True)

    if not bn_info:
        reply["message"] = "Batch Number Not Found In the System"
        reply["success"] = False
        reply["status_code"] = 404
        return reply
    
    btc_results = []
    btc_obj = {}

    if bn_info:
        batch_info  = bn_info[0]
        btc_obj["batch_no"] = batch_info["name"]
        btc_obj["item_code"] = batch_info["item"]
        btc_obj["item_name"] = batch_info["item_name"]
        btc_obj["batch_qty"] = batch_info["batch_qty"]
        btc_obj["manufacturing_date"] = batch_info["manufacturing_date"]
        btc_obj["expiry_date"] = batch_info["expiry_date"]
        btc_obj["source_document_type"] = batch_info["reference_doctype"]
        btc_obj["reference_name"] = batch_info["reference_name"]
        btc_results.append(btc_obj)
    reply['batch_data'] = btc_results
    

    query = "SELECT DISTINCT sbb.name as bundle_name,sbb.voucher_type, sbb.item_code, sbb.voucher_no,sbb.type_of_transaction FROM `tabSerial and Batch Entry` sbbi JOIN `tabSerial and Batch Bundle` sbb ON sbbi.parent = sbb.name WHERE sbb.docstatus != 2  AND sbbi.batch_no = '{}'".format(batch_no)
    results = frappe.db.sql(query,as_dict=True)

    return_result = []

    for row in results:
        voucher_type = row['voucher_type']
        voucher_no = row['voucher_no']
        type_of_transaction = row['type_of_transaction']
        # item_code = row['item_code']

        query = f"SELECT name as document_name FROM `tab{voucher_type}` WHERE name = %s"
        results = frappe.db.sql(query,voucher_no,as_dict=True)

        if not results:
            reply["message"] = ""
            reply["success"] = False
            reply["status_code"] = 404
            return reply

        for i in results:
            obj = {}
            posting_date = 'transaction_date' if voucher_type in ['Purchase Order','Sales Order','Material Request'] else ('' if voucher_type=='Pick List' else 'posting_date')
            obj['document']= voucher_type
            obj['document_name']= i['document_name']
            obj['posting_date'] = frappe.db.get_value(voucher_type,i['document_name'],posting_date) if posting_date else ''            

            if voucher_type == "Stock Entry":
                if type_of_transaction == "Outward":
                    obj['type_of_transaction'] = "Internal Transfer"
                else:
                    obj['type_of_transaction'] = type_of_transaction

        priority = {
            "Purchase Receipt": 1,
            "Stock Entry": 2,
            "Subcontracting Receipt": 3,
            "Pick List" : 5,
            "Delivery Note": 6,
        }

        return_result.append(obj)
        return_result = sorted(return_result, key=lambda x: priority.get(x["document"], 99))
        
    reply['data'] = return_result
    return reply

@frappe.whitelist(allow_guest=True)
def check_serial_or_batch(number):
    serial_exists = frappe.db.exists("Serial No", number)
    if serial_exists:
        return {
            "type": "serial"
        }

    batch_exists = frappe.db.exists("Batch", number)
    if batch_exists:
        return {
            "type": "batch"
        }
    
    return {
        "type": None
    }