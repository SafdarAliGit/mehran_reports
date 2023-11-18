import frappe
from frappe import _


def execute(filters=None):
    columns = get_columns()
    data = get_data(filters)
    return columns, data


def decimal_format(value, decimals):
    formatted_value = "{:.{}f}".format(value, decimals)
    return formatted_value


def get_columns():
    columns = [
        {
            "label": _("Sales Order No"),
            "fieldname": "sales_order_no",
            "fieldtype": "Link",
            "options": 'Sales Order'
        },
        {
            "label": _("Posting Date"),
            "fieldname": "posting_date",
            "fieldtype": "Date",
            "width": 150
        },
        {
            "label": _("Customer"),
            "fieldname": "customer",
            "fieldtype": "Link",
            "options": "Customer",
            "width": 150
        },
        {
            "label": _("Item"),
            "fieldname": "item_code",
            "fieldtype": "Link",
            "options": "Item",
            "width": 150
        }
        ,
        {
            "label": _("Sales Order Qty"),
            "fieldname": "so_qty",
            "fieldtype": "Data",
            "width": 150
        }
        ,
        {
            "label": _("DN Qty"),
            "fieldname": "dn_qty",
            "fieldtype": "Data",
            "width": 150
        }
        ,
        {
            "label": _("Balance"),
            "fieldname": "balance",
            "fieldtype": "Data",
            "width": 150
        }

    ]
    return columns


def get_conditions(filters, doctype):
    conditions = []

    if filters.get("from_date"):
        conditions.append(f"`tab{doctype}`.transaction_date >= %(from_date)s")
    if filters.get("to_date"):
        conditions.append(f"`tab{doctype}`.transaction_date <= %(to_date)s")
    if filters.get("customer"):
        conditions.append(f"`tab{doctype}`.customer = %(customer)s")

    return " AND ".join(conditions)


def get_data(filters):
    data = []
    sales_analytics = """SELECT 
            `tabSales Order`.transaction_date AS posting_date,
            `tabSales Order`.customer,
            `tabSales Order`.name AS sales_order_no,
            `tabSales Order Item`.item_code,
            SUM(`tabSales Order Item`.qty) AS so_qty,
            (
                SELECT COALESCE(SUM(`tabDelivery Note Item`.qty),0)
                FROM `tabDelivery Note Item`,`tabDelivery Note`
                WHERE `tabSales Order`.name = `tabDelivery Note Item`.against_sales_order AND `tabSales Order Item`.item_code  =  `tabDelivery Note Item`.item_code AND `tabDelivery Note`.name = `tabDelivery Note Item`.parent AND `tabDelivery Note`.docstatus <= 1
            ) AS dn_qty
            
        FROM 
            `tabSales Order`, `tabSales Order Item`
        WHERE 
            `tabSales Order`.name = `tabSales Order Item`.parent
            AND 
            `tabSales Order`.docstatus <= 1
            AND 
            {conditions}
        GROUP BY 
            `tabSales Order`.name, `tabSales Order Item`.item_code
    """.format(conditions=get_conditions(filters, "Sales Order"))
    sales_analytics_result = frappe.db.sql(sales_analytics, filters, as_dict=1)
    for dt in sales_analytics_result:
        dt.update({"balance":dt.get('so_qty') -dt.get('dn_qty') })
    filtered_data = [entry for entry in sales_analytics_result if entry['balance'] != 0]
    data.extend(filtered_data)
    return data


