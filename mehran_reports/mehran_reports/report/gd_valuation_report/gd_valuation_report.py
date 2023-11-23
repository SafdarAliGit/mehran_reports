# my_custom_app.my_custom_app.report.daily_activity_report.daily_activity_report.py
import frappe
from frappe import _


def execute(filters=None):
    if not filters:
        filters = {}
    data = []
    columns = get_columns()
    data = get_data(filters)

    return columns, data


def get_columns():
    columns = [
        {
            "label": _("Date"),
            "fieldname": "posting_date",
            "fieldtype": "Date",
            "width": 150
        },
        {
            "label": _("Supplier"),
            "fieldname": "supplier",
            "fieldtype": "Link",
            "options": "Supplier",
            "width": 180
        },
        {
            "label": _("Item"),
            "fieldname": "item_name",
            "fieldtype": "Link",
            "options": "Item",
            "width": 180
        },
        {
            "label": _("Batch"),
            "fieldname": "batch_no",
            "fieldtype": "Data",
            "width": 180
        },
        {
            "label": _("Quantity"),
            "fieldname": "qty",
            "fieldtype": "Float",
            "width": 180
        },
        {
            "label": _("Rate"),
            "fieldname": "rate",
            "fieldtype": "Currency",
            "width": 180
        },
        {
            "label": _("CD"),
            "fieldname": "cd_rate",
            "fieldtype": "Currency",
            "width": 180

        },
        {
            "label": _("RD"),
            "fieldname": "rd_rate",
            "fieldtype": "Currency",
            "width": 180
        },
        {
            "label": _("ACD"),
            "fieldname": "acd_rate",
            "fieldtype": "Currency",
            "width": 180
        },
        {
            "label": _("Cost Rate"),
            "fieldname": "cost_rate",
            "fieldtype": "Currency",
            "width": 180
        },
        {
            "label": _("GST"),
            "fieldname": "gst_rate",
            "fieldtype": "Currency",
            "width": 180
        },
        {
            "label": _("AST"),
            "fieldname": "ast_rate",
            "fieldtype": "Currency",
            "width": 180
        },

        {
            "label": _("Gross Rate"),
            "fieldname": "gross_rate",
            "fieldtype": "Currency",
            "width": 180
        },

        {
            "label": _("Grand Total"),
            "fieldname": "grand_total",
            "fieldtype": "Currency",
            "width": 180
        }
    ]
    return columns

def get_conditions(filters):
    conditions = []
    if filters.get("from_date"):
        conditions.append(f"pi.posting_date >= %(from_date)s")
    if filters.get("to_date"):
        conditions.append(f"pi.posting_date <= %(to_date)s")
    if filters.get("item_code"):
        conditions.append(f"pii.item_code = %(item_code)s")
    return " AND ".join(conditions)


def get_data(filters):
    data = []

    pi_query = """
            SELECT
                pi.posting_date,
                pi.supplier,
                pii.item_name,
                pii.batch_no,
                pii.qty,
                pii.rate,
                pii.rate * COALESCE(ptc.CD, 0)/100 AS cd_rate,
                pii.rate * COALESCE(ptc.RD, 0)/100 AS rd_rate,
                pii.rate * COALESCE(ptc.ACD, 0)/100 AS acd_rate,
                (pii.rate + pii.rate * COALESCE(ptc.CD, 0)/100 + pii.rate * COALESCE(ptc.RD, 0)/100 + pii.rate * COALESCE(ptc.ACD, 0)/100) AS cost_rate,
                ((pii.rate + pii.rate * COALESCE(ptc.CD, 0)/100 + pii.rate * COALESCE(ptc.RD, 0)/100 + pii.rate * COALESCE(ptc.ACD, 0)/100) * COALESCE(ptc.GST, 0)/100) AS gst_rate,
                ((pii.rate + pii.rate * COALESCE(ptc.CD, 0)/100 + pii.rate * COALESCE(ptc.RD, 0)/100 + pii.rate * COALESCE(ptc.ACD, 0)/100) * COALESCE(ptc.AST, 0)/100) AS ast_rate,
                ((pii.rate + pii.rate * COALESCE(ptc.CD, 0)/100 + pii.rate * COALESCE(ptc.RD, 0)/100 + pii.rate * COALESCE(ptc.ACD, 0)/100) + ((pii.rate + pii.rate * COALESCE(ptc.CD, 0)/100 + pii.rate * COALESCE(ptc.RD, 0)/100 + pii.rate * COALESCE(ptc.ACD, 0)/100) * COALESCE(ptc.GST, 0)/100) + ((pii.rate + pii.rate * COALESCE(ptc.CD, 0)/100 + pii.rate * COALESCE(ptc.RD, 0)/100 + pii.rate * COALESCE(ptc.ACD, 0)/100) * COALESCE(ptc.AST, 0)/100)) AS gross_rate,
                (((pii.rate + pii.rate * COALESCE(ptc.CD, 0)/100 + pii.rate * COALESCE(ptc.RD, 0)/100 + pii.rate * COALESCE(ptc.ACD, 0)/100) + ((pii.rate + pii.rate * COALESCE(ptc.CD, 0)/100 + pii.rate * COALESCE(ptc.RD, 0)/100 + pii.rate * COALESCE(ptc.ACD, 0)/100) * COALESCE(ptc.GST, 0)/100) + ((pii.rate + pii.rate * COALESCE(ptc.CD, 0)/100 + pii.rate * COALESCE(ptc.RD, 0)/100 + pii.rate * COALESCE(ptc.ACD, 0)/100) * COALESCE(ptc.AST, 0)/100))*pii.qty) AS grand_total
            FROM
                `tabPurchase Invoice` pi
            LEFT JOIN
                `tabPurchase Invoice Item` pii ON pi.name = pii.parent
            LEFT JOIN
                (
                    SELECT
                        parent,
                        MAX(CASE WHEN idx = 1 THEN rate ELSE 0 END) AS CD,
                        MAX(CASE WHEN idx = 2 THEN rate ELSE 0 END) AS RD,
                        MAX(CASE WHEN idx = 3 THEN rate ELSE 0 END) AS ACD,
                        MAX(CASE WHEN idx = 4 THEN rate ELSE 0 END) AS GST,
                        MAX(CASE WHEN idx = 5 THEN rate ELSE 0 END) AS AST,
                        MAX(CASE WHEN idx = 6 THEN rate ELSE 0 END) AS ITI
                    FROM
                        `tabPurchase Taxes and Charges`
                    GROUP BY
                        parent
                ) ptc ON pi.name = ptc.parent
            WHERE
                 pi.docstatus = 1 AND {conditions} 
            """.format(conditions=get_conditions(filters))
    pi_result = frappe.db.sql(pi_query, filters, as_dict=1)

    data.extend(pi_result)
    return data

