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
            "label": _("Tax Amount"),
            "fieldname": "tax_amount",
            "fieldtype": "Currency",
            "width": 120
        },

        {
            "label": _("Net Total"),
            "fieldname": "net_total",
            "fieldtype": "Currency",
            "width": 120
        },


        {
            "label": _("Debit"),
            "fieldname": "total_debit",
            "fieldtype": "Currency",
            "width": 120
        },
        {
            "label": _("Credit"),
            "fieldname": "total_credit",
            "fieldtype": "Currency",
            "width": 120
        },

        {
            "label": _("Balance"),
            "fieldname": "balance",
            "fieldtype": "Currency",
            "width": 150
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
                        `tabGL Entry`.debit_in_account_currency AS total_debit
                    FROM
                        `tabGL Entry`
                    WHERE
                         `tabGL Entry`.is_cancelled = 0 
                         AND `tabGL Entry`.voucher_type IN ('Sales Invoice', 'Payment Entry') 
                         AND `tabGL Entry`.party_type = 'Customer'
                         AND {conditions}
                    ORDER BY 
                        `tabGL Entry`.voucher_no
                """.format(conditions=get_conditions(filters, "GL Entry"))

    gl_entry_result = frappe.db.sql(gl_entry, filters, as_dict=1)

    for dt in gl_entry_result:
        sales_invoice = """ SELECT
                                `tabSales Invoice`.tax_id,
                                `tabSales Invoice`.commercial_invoice_no,
                                `tabSales Invoice`.po_no,
                                `tabSales Invoice`.dc_no,
                                `tabSales Invoice`.net_total,
                                `tabSales Taxes and Charges`.tax_amount
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
        sales_invoice_result = frappe.db.sql(sales_invoice, {"voucher_no": dt.get("voucher_no")}, as_dict=1)
        if sales_invoice_result:
            dt.update({"tax_id": sales_invoice_result[0].get("tax_id"),"commercial_invoice_no": sales_invoice_result[0].get("commercial_invoice_no"),"po_no": sales_invoice_result[0].get("po_no"),
                       "dc_no": sales_invoice_result[0].get("dc_no"),"net_total": sales_invoice_result[0].get("net_total"),"tax_amount": sales_invoice_result[0].get("tax_amount")})

    data.extend(gl_entry_result)
    return data
