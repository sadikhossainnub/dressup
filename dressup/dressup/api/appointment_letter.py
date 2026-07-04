import frappe
from frappe.utils import flt
from frappe.utils.safe_exec import safe_eval

@frappe.whitelist()
def get_calculated_salary_components(salary_structure, basic_amount):
	basic_amount = flt(basic_amount)
	structure = frappe.get_doc("Salary Structure", salary_structure)

	# Build context matching how ERPNext evaluates Salary Structure formulas/conditions
	context = {"base": basic_amount, "basic": basic_amount}

	# Pre-seed all known component abbreviations to 0 to prevent NameErrors in evaluations
	for abbr in frappe.get_all("Salary Component", pluck="salary_component_abbr"):
		if abbr:
			context.setdefault(abbr, 0.0)

	components = []
	gross_salary = 0.0

	# Process earnings first, then deductions
	for component_type, table_field in [("Earning", "earnings"), ("Deduction", "deductions")]:
		for row in structure.get(table_field) or []:
			try:
				# Evaluate condition
				if row.condition:
					# Use safe_eval for condition
					condition_eval = safe_eval(row.condition, None, context)
					if not condition_eval:
						continue

				# Calculate amount
				amount = 0.0
				if row.amount_based_on_formula and row.formula:
					amount = flt(safe_eval(row.formula, None, context))
				else:
					amount = flt(row.amount)

				# Store in context for subsequent components/formulas
				context[row.abbr] = amount

				components.append({
					"salary_component": row.salary_component,
					"abbr": row.abbr,
					"component_type": component_type,
					"formula": row.formula or "",
					"condition": row.condition or "",
					"amount": amount,
				})

				if component_type == "Earning":
					gross_salary += amount

			except Exception as e:
				frappe.throw(
					f"Error evaluating component '{row.salary_component}' ({row.abbr}): {str(e)}",
					title="Salary Component Evaluation Error"
				)

	return {
		"components": components,
		"gross_salary": gross_salary
	}
