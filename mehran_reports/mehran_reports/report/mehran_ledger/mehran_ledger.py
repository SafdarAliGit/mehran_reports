# my_custom_app.my_custom_app.report.daily_activity_report.daily_activity_report.py
import frappe
from frappe import _


def execute(filters=None):
    columns = get_columns()
    data = get_data(filters)
    return columns, data


def get_columns():
    columns = [
        {
            "label": _("Posting Date"),
            "fieldname": "posting_date",
            "fieldtype": "Date",
            "width": 120
        },
        {
            "label": _("Inv/Pay #"),
            "fieldname": "voucher_no",
            "fieldtype": "Dynamic Link",
            "options": "voucher_type",
            "width": 180,
            "hidden": 0,
        },
        {
            "label": _("Commercial Inv#"),
            "fieldname": "commercial_invoice_no",
            "fieldtype": "Data",
            "width": 180
        },

        {
            "label": _("PO#"),
            "fieldname": "po_no",
            "fieldtype": "Data",
            "width": 180
        },
        {
            "label": _("DC#"),
            "fieldname": "dc_no",
            "fieldtype": "Data",
            "width": 180
        },
        {
            "label": _("GST"),
            "fieldname": "gst_tax_amount",
            "fieldtype": "Currency",
            "width": 120
        },
        {
            "label": _("Cartage"),
            "fieldname": "cartage_tax_amount",
            "fieldtype": "Currency",
            "width": 120
        },

        {
            "label": _("Net Total"),
            "fieldname": "net_total",
            "fieldtype": "Currency",
            "width": 200
        },

        {
            "label": _("Grand Total"),
            "fieldname": "debit",
            "fieldtype": "Currency",
            "width": 200
        },
        {
            "label": _("Paid Amount"),
            "fieldname": "credit",
            "fieldtype": "Currency",
            "width": 200
        },

        {
            "label": _("Balance"),
            "fieldname": "balance",
            "fieldtype": "Currency",
            "width": 200
        }

    ]
    return columns


def get_conditions(filters, doctype):
    conditions = []

    if filters.get("from_date"):
        conditions.append(f"`tab{doctype}`.posting_date >= %(from_date)s")
    if filters.get("to_date"):
        conditions.append(f"`tab{doctype}`.posting_date <= %(to_date)s")
    if filters.get("customer"):
        conditions.append(f"`tab{doctype}`.party = %(customer)s")

    return " AND ".join(conditions)


def get_data(filters):
    data = []

    gl_entry = """ SELECT
                        `tabGL Entry`.posting_date,
                        `tabGL Entry`.voucher_no,
                        `tabGL Entry`.account,
                        ROUND(`tabGL Entry`.debit_in_account_currency,2) AS debit
                    FROM
                        `tabGL Entry`
                    WHERE
                         `tabGL Entry`.is_cancelled = 0 
                         AND `tabGL Entry`.voucher_type ='Sales Invoice'
                         AND `tabGL Entry`.party_type = 'Customer'
                         AND {conditions}
                    ORDER BY 
                        `tabGL Entry`.posting_date
                """.format(conditions=get_conditions(filters, "GL Entry"))

    gl_entry_result = frappe.db.sql(gl_entry, filters, as_dict=1)

    for dt in gl_entry_result:
        sales_invoice = """ SELECT
                                `tabSales Invoice`.commercial_invoice_no,
                                `tabSales Invoice`.po_no,
                                `tabSales Invoice`.dc_no,
                                ROUND(`tabSales Invoice`.net_total,2) AS net_total,
                                ROUND(`tabSales Taxes and Charges`.tax_amount,2) AS tax_amount,
                                `tabSales Taxes and Charges`.account_head
                            FROM
                                `tabSales Invoice`
                            LEFT JOIN
                                `tabSales Taxes and Charges`
                            ON
                                `tabSales Invoice`.name = `tabSales Taxes and Charges`.parent
                            WHERE
                                 `tabSales Invoice`.docstatus = 1
                                 AND (`tabSales Invoice`.name = %(voucher_no)s)
                        """
        payment_entry = """ SELECT
                                ROUND(`tabPayment Entry Reference`.allocated_amount,2) AS allocated_amount
                            FROM
                                `tabPayment Entry`,`tabPayment Entry Reference`
                            WHERE
                                 `tabPayment Entry Reference`.parent = `tabPayment Entry`.name AND `tabPayment Entry`.docstatus = 1
                                 AND (`tabPayment Entry Reference`.reference_name = %(voucher_no)s)
                        """
        sales_invoice_result = frappe.db.sql(sales_invoice, {"voucher_no": dt.get("voucher_no")}, as_dict=1)
        payment_entry_result = frappe.db.sql(payment_entry, {"voucher_no": dt.get("voucher_no")}, as_dict=1)

        for item in sales_invoice_result:
            if item.get('account_head') == "GST - S&B":
                dt.update({"gst_tax_amount": item.get("tax_amount")})
            elif item.get('account_head') == "CARTAGE - S&B":
                dt.update({"cartage_tax_amount": item.get("tax_amount")})

        if sales_invoice_result:
            result_dict = sales_invoice_result[0]

            dt.update({
                "commercial_invoice_no": result_dict.get("commercial_invoice_no"),
                "po_no": result_dict.get("po_no"),
                "dc_no": result_dict.get("dc_no"),
                "net_total": result_dict.get("net_total"),
            })

        if payment_entry_result:
            payment_entry_result_dict = payment_entry_result[0]
            dt.update({"credit": payment_entry_result_dict.get("allocated_amount", 0)})

        dt.update({"balance": dt.get("debit", 0) - dt.get("credit", 0)})

    # gl_entry_result = [gle for gle in gl_entry_result if gle["debit"] != 0 and gle["credit"] != 0]
    data.extend(gl_entry_result)
    return data

