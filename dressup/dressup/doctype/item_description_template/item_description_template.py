# Copyright (c) 2026, Prime Technology of Bangladesh and contributors
# For license information, please see license.txt

import re
import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import cstr, escape_html
from jinja2 import TemplateSyntaxError
from jinja2.sandbox import SandboxedEnvironment
import jinja2.meta

FIELD_KEY_PATTERN = re.compile(r"^[a-z_][a-z0-9_]*$")


class ItemDescriptionTemplate(Document):
	def validate(self):
		self.validate_template_syntax()
		self.validate_fields()

	def validate_template_syntax(self):
		"""Validate that template_html is valid Jinja syntax using SandboxedEnvironment."""
		if not self.template_html:
			frappe.throw(_("Template HTML is required."), title=_("Validation Error"))

		try:
			env = SandboxedEnvironment()
			env.parse(self.template_html)
		except TemplateSyntaxError as e:
			frappe.throw(
				_("Jinja template syntax error at line {0}: {1}").format(e.lineno, e.message),
				title=_("Invalid Jinja Syntax")
			)
		except Exception as e:
			frappe.throw(
				_("Invalid Jinja template: {0}").format(str(e)),
				title=_("Invalid Jinja Syntax")
			)

	def validate_fields(self):
		"""Validate that field_key matches ^[a-z_][a-z0-9_]*$ and is unique within the template."""
		seen_keys = set()
		for idx, row in enumerate(self.fields or [], start=1):
			row_key = getattr(row, "field_key", None) or (row.get("field_key") if isinstance(row, dict) else "")
			row_idx = getattr(row, "idx", None) or (row.get("idx") if isinstance(row, dict) else idx)
			if not row_key:
				frappe.throw(
					_("Row #{0}: Field Key is required.").format(row_idx),
					title=_("Invalid Field Key")
				)
			key = str(row_key).strip()
			if not FIELD_KEY_PATTERN.match(key):
				frappe.throw(
					_("Row #{0}: Field Key '{1}' is invalid. Must be lowercase alphanumeric with underscores starting with a letter or underscore (e.g. 'kameez_body').").format(row_idx, key),
					title=_("Invalid Field Key")
				)
			if key in seen_keys:
				frappe.throw(
					_("Row #{0}: Duplicate Field Key '{1}' in template.").format(row_idx, key),
					title=_("Duplicate Field Key")
				)
			seen_keys.add(key)
			if hasattr(row, "field_key"):
				row.field_key = key
			elif isinstance(row, dict):
				row["field_key"] = key


def get_rendered_description(template, values_dict, item_doc=None):
	"""
	Render template HTML with escaped user values and item context.
	Missing values render as empty strings without raising errors.
	"""
	if isinstance(template, str):
		template = frappe.get_cached_doc("Item Description Template", template)

	template_html = getattr(template, "template_html", None) or (template.get("template_html") if isinstance(template, dict) else "") or ""
	template_name = getattr(template, "name", None) or (template.get("name") if isinstance(template, dict) else "") or "Template"

	# Inspect undeclared variables from template so they default to empty string
	env = SandboxedEnvironment()
	try:
		ast = env.parse(template_html)
		undeclared = jinja2.meta.find_undeclared_variables(ast)
	except Exception:
		undeclared = set()

	# Base context initializes all template variables to empty string
	context = {var_name: "" for var_name in undeclared}

	# Populate defaults from template fields if defined
	fields_list = getattr(template, "fields", None) or (template.get("fields") if isinstance(template, dict) else None)
	if fields_list:
		for f in fields_list:
			f_key = getattr(f, "field_key", None) or (f.get("field_key") if isinstance(f, dict) else None)
			f_default = getattr(f, "default_value", None) or (f.get("default_value") if isinstance(f, dict) else None)
			if f_key:
				context[f_key] = escape_html(cstr(f_default or ""))

	# Include standard Item attributes (escaped)
	if item_doc:
		for attr in ("item_code", "item_name", "brand", "item_group"):
			val = getattr(item_doc, attr, None) if not isinstance(item_doc, dict) else item_doc.get(attr)
			if val is not None:
				context[attr] = escape_html(cstr(val))

	# Apply user-entered values (HTML escaped)
	if values_dict:
		if isinstance(values_dict, dict):
			for k, v in values_dict.items():
				context[k] = escape_html(cstr(v if v is not None else ""))
		else:
			for row in values_dict:
				if isinstance(row, dict):
					k = row.get("field_key")
					v = row.get("value")
				else:
					k = getattr(row, "field_key", None)
					v = getattr(row, "value", None)
				if k:
					context[k] = escape_html(cstr(v if v is not None else ""))

	try:
		return frappe.render_template(template_html, context)
	except Exception as e:
		frappe.throw(
			_("Error rendering Item Description Template '{0}': {1}").format(template_name, str(e)),
			title=_("Template Render Error")
		)


def item_before_save(doc, method=None):
	"""
	Item before_save doc_events hook:
	Renders description_template into doc.description (and web_long_description if enabled).
	"""
	template_name = doc.get("description_template")
	if not template_name or not doc.get("regenerate_description"):
		return

	try:
		template = frappe.get_cached_doc("Item Description Template", template_name)
	except frappe.DoesNotExistError:
		return

	if not template or not template.enabled:
		return

	rendered_html = get_rendered_description(
		template=template,
		values_dict=doc.get("description_values") or [],
		item_doc=doc
	)

	doc.description = rendered_html
	if template.update_web_description:
		doc.web_long_description = rendered_html
