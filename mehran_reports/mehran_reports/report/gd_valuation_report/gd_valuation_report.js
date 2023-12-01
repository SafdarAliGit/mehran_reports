// Copyright (c) 2023, Tech Ventures and contributors
// For license information, please see license.txt
/* eslint-disable */

frappe.query_reports["GD Valuation Report"] = {
    "filters": [
        {
			label: __("From Date"),
			fieldname: "from_date",
			fieldtype: "Date",
			default: frappe.datetime.add_months(frappe.datetime.get_today(), -1),
			reqd: 1
		},
		{
			label: __("To Date"),
			fieldname: "to_date",
			fieldtype: "Date",
			default: frappe.datetime.get_today(),
			reqd: 1
		},
        {
            label: __("Item Code"),
            fieldname: "item_code",
            fieldtype: "Link",
            options: "Item",
			default: "001",
			reqd: 0
        }
    ],
};

