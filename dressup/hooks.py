app_name = "dressup"
app_title = "DressUp"
app_publisher = "Prime Technology of Bangladesh"
app_description = "DressUp Manufacturing"
app_email = "info@primetechbd.xyz"
app_license = "gpl-3.0"

fixtures = [
	{
		"doctype": "Custom Field",
		"filters": [["module", "=", "DressUp"]],
	},
	{
		"doctype": "Role",
		"filters": [["name", "in", ["Barcode Label Manager", "DressUp Manager", "Discount Approver", "PO Approver"]]]
	},
	{
		"dt": "Print Format",
		"filters": [
			["name", "in", ["POS Thermal Receipt"]]
		]
	},
	{
		"doctype": "Customer Group",
		"filters": [["name", "in", ["Employee"]]],
	},
]


# Apps
# ------------------

# required_apps = []

# Each item in the list will be shown as an app in the apps page
# add_to_apps_screen = [
# 	{
# 		"name": "dressup",
# 		"logo": "/assets/dressup/logo.png",
# 		"title": "DressUp",
# 		"route": "/dressup",
# 		"has_permission": "dressup.api.permission.has_app_permission"
# 	}
# ]

# Includes in <head>
# ------------------

# include js, css files in header of desk.html
# app_include_css = "/assets/dressup/css/dressup.css"
app_include_js = ["/assets/dressup/js/list_created_by.js"]

# include js, css files in header of web template
# web_include_css = "/assets/dressup/css/dressup.css"
# web_include_js = "/assets/dressup/js/dressup.js"

# include custom scss in every website theme (without file extension ".scss")
# website_theme_scss = "dressup/public/scss/website"

# include js, css files in header of web form
# webform_include_js = {"doctype": "public/js/doctype.js"}
# webform_include_css = {"doctype": "public/css/doctype.css"}

# include js in page
# page_js = {"page" : "public/js/file.js"}

# include js in doctype views
doctype_js = {
	"Quality Inspection": "public/js/quality_inspection.js",
	"BOM": "public/js/bom.js",
	"Work Order": "public/js/work_order.js",
	"Job Applicant": "public/js/job_applicant.js",
	"Stock Entry": "public/js/stock_entry.js",
	"Appointment Letter": "public/js/appointment_letter.js",
	# Create Customer button + View Customer link on Employee form
	"Employee": "public/js/employee_customer_button.js",
	# Overrides erpnext.utils.update_child_items to add Discount % and Discount Amount
	# columns in the "Update Items" dialog. Loaded after ERPNext's utils.js so it
	# correctly replaces the function.
	"Sales Order": [
		"public/js/sales_order_update_items_override.js",
		"public/js/sales_order_approval.js",
	],
	"Purchase Order": "public/js/purchase_order_approval.js",
}
doctype_list_js = {
	"BOM": "public/js/bom_list.js",
	"Job Card": "public/js/job_card_list.js",
}
# doctype_tree_js = {"doctype" : "public/js/doctype_tree.js"}
# doctype_calendar_js = {"doctype" : "public/js/doctype_calendar.js"}

# Svg Icons
# ------------------
# include app icons in desk
# app_include_icons = "dressup/public/icons.svg"

# Home Pages
# ----------

# application home page (will override Website Settings)
# home_page = "login"

# website user home page (by Role)
# role_home_page = {
# 	"Role": "home_page"
# }

# Generators
# ----------

# automatically create page for each record of this doctype
# website_generators = ["Web Page"]

# Jinja
# ----------

# add methods and filters to jinja environment
jinja = {
	"methods": ["dressup.barcode_label_print.utils.get_barcode_base64"],
# 	"filters": "dressup.utils.jinja_filters"
}

# Installation
# ------------

# before_install = "dressup.install.before_install"
after_install = "dressup.setup.after_install"
after_migrate = "dressup.setup.after_migrate"

# Uninstallation
# ------------

# before_uninstall = "dressup.uninstall.before_uninstall"
# after_uninstall = "dressup.uninstall.after_uninstall"

# Integration Setup
# ------------------
# To set up dependencies/integrations with other apps
# Name of the app being installed is passed as an argument

# before_app_install = "dressup.utils.before_app_install"
# after_app_install = "dressup.utils.after_app_install"

# Integration Cleanup
# -------------------
# To clean up dependencies/integrations with other apps
# Name of the app being uninstalled is passed as an argument

# before_app_uninstall = "dressup.utils.before_app_uninstall"
# after_app_uninstall = "dressup.utils.after_app_uninstall"

# Desk Notifications
# ------------------
# See frappe.core.notifications.get_notification_config

# notification_config = "dressup.notifications.get_notification_config"

# Permissions
# -----------
# Permissions evaluated in scripted ways

# permission_query_conditions = {
# 	"Event": "frappe.desk.doctype.event.event.get_permission_query_conditions",
# }
#
# has_permission = {
# 	"Event": "frappe.desk.doctype.event.event.has_permission",
# }

# DocType Class
# ---------------
# Override standard doctype classes

override_doctype_class = {
	"Quality Inspection": "dressup.dressup.custom_quality_inspection.CustomQualityInspection",
	"Shipping Rule": "dressup.dressup.custom_shipping_rule.CustomShippingRule"
}

# Document Events
# ---------------
# Hook on document methods and events

doc_events = {
	"*": {
		"on_update": "dressup.utils.workflow_tracker.track_workflow_action"
	},
	"BOM": {
		"before_cancel": "dressup.utils.linked_cancel.cancel_linked_documents"
	},
	"Work Order": {
		"after_insert": "dressup.dressup.doctype.pre_production_sample.pre_production_sample.link_work_order_to_pps",
		"before_cancel": "dressup.utils.linked_cancel.cancel_linked_documents"
	},
	"Pre Production Sample": {
		"before_cancel": "dressup.utils.linked_cancel.cancel_linked_documents"
	},
	"Sales Order": {
		# Discount Approval: check for extra discounts on every save
		"validate": "dressup.dressup.custom_scripts.sales_order.check_extra_discount",
		# Notify approvers after submit if pending
		"on_submit": "dressup.dressup.custom_scripts.sales_order.notify_approvers_on_submit",
	},
	"Sales Invoice": {
		"before_submit": "dressup.dressup.loyalty_auto_assign.auto_assign_loyalty_program",
		"on_submit": "dressup.dressup.loyalty_auto_assign.create_custom_loyalty_point_entry",
		# Discount Approval guard: block if source SO discount is not approved
		"validate": "dressup.dressup.custom_scripts.discount_approval_guard.block_if_not_approved",
	},
	"Delivery Note": {
		# Discount Approval guard: block if source SO discount is not approved
		"validate": "dressup.dressup.custom_scripts.discount_approval_guard.block_if_not_approved",
	},
	"Stock Entry": {
		"on_submit": "dressup.dressup.doctype.pre_production_sample.pre_production_sample.link_stock_entry_to_pps",
		"on_cancel": "dressup.dressup.doctype.pre_production_sample.pre_production_sample.unlink_stock_entry_from_pps",
		"on_trash": "dressup.dressup.doctype.pre_production_sample.pre_production_sample.unlink_stock_entry_from_pps"
	},
	"Purchase Order": {
		"validate": "dressup.dressup.custom_scripts.purchase_order.fetch_purpose_from_material_request",
		# Set approval status to Pending and notify PO Approvers after submit
		"on_submit": "dressup.dressup.custom_scripts.purchase_order.notify_approvers_on_submit",
	},
	"Purchase Receipt": {
		"validate": "dressup.dressup.custom_scripts.purchase_order.validate_po_approval_guard",
	},
	"Purchase Invoice": {
		"validate": "dressup.dressup.custom_scripts.purchase_order.validate_po_approval_guard",
	}
}

# Scheduled Tasks
# ---------------

scheduler_events = {
	"daily": [
		"dressup.dressup.loyalty_downgrade.check_loyalty_tier_downgrade",
	],
}

# Testing
# -------

# before_tests = "dressup.install.before_tests"

# Overriding Methods
# ------------------------------
#
# override_whitelisted_methods = {
# 	"frappe.desk.doctype.event.event.get_events": "dressup.event.get_events"
# }

# Compatibility shim: normalises 'args' ↔ 'ctx' keyword for get_item_details
# so the call works regardless of client JS version vs ERPNext server version.
# Ref: https://github.com/frappe/erpnext/issues/51345
override_whitelisted_methods = {
	"erpnext.stock.get_item_details.get_item_details": "dressup.overrides.item_details_fix.get_item_details",
	"erpnext.controllers.accounts_controller.update_child_qty_rate": "dressup.overrides.update_child_qty_rate_override.update_child_qty_rate",
	"erpnext.accounts.doctype.loyalty_program.loyalty_program.get_loyalty_program_details_with_points": "dressup.dressup.loyalty_auto_assign.custom_get_loyalty_program_details_with_points",
	"erpnext.accounts.doctype.sales_invoice.sales_invoice.get_loyalty_program_details_with_points": "dressup.dressup.loyalty_auto_assign.custom_get_loyalty_program_details_with_points",
}
#
# each overriding function accepts a `data` argument;
# generated from the base implementation of the doctype dashboard,
# along with any modifications made in other Frappe apps
# override_doctype_dashboards = {
# 	"Task": "dressup.task.get_dashboard_data"
# }

# exempt linked doctypes from being automatically cancelled
#
# auto_cancel_exempted_doctypes = ["Auto Repeat"]

# Ignore links to specified DocTypes when deleting documents
# -----------------------------------------------------------

ignore_links_on_delete = ["BOM"]

# Request Events
# ----------------
# before_request = ["dressup.utils.before_request"]
# after_request = ["dressup.utils.after_request"]

# Job Events
# ----------
# before_job = ["dressup.utils.before_job"]
# after_job = ["dressup.utils.after_job"]

# User Data Protection
# --------------------

# user_data_fields = [
# 	{
# 		"doctype": "{doctype_1}",
# 		"filter_by": "{filter_by}",
# 		"redact_fields": ["{field_1}", "{field_2}"],
# 		"partial": 1,
# 	},
# 	{
# 		"doctype": "{doctype_2}",
# 		"filter_by": "{filter_by}",
# 		"partial": 1,
# 	},
# 	{
# 		"doctype": "{doctype_3}",
# 		"strict": False,
# 	},
# 	{
# 		"doctype": "{doctype_4}"
# 	}
# ]

# Authentication and authorization
# --------------------------------

# auth_hooks = [
# 	"dressup.auth.validate"
# ]

# Automatically update python controller files with type annotations for this app.
# export_python_type_annotations = True

# default_log_clearing_doctypes = {
# 	"Logging DocType Name": 30  # days to retain logs
# }

