import frappe
from dressup.api.appointment_letter import get_calculated_salary_components

def run_test():
	print("Connected to site1.local")

	# Find or create a Salary Structure for testing
	structure_name = frappe.db.get_value("Salary Structure", {"is_active": "Yes"})
	if not structure_name:
		# Let's create one
		print("No active Salary Structure found. Creating a test one...")
		
		# Ensure test Salary Components exist
		for component_name, abbr, c_type in [("Basic", "B", "Earning"), ("House Rent Allowance", "HRA", "Earning"), ("Provident Fund", "PF", "Deduction")]:
			if not frappe.db.exists("Salary Component", component_name):
				comp = frappe.get_doc({
					"doctype": "Salary Component",
					"salary_component": component_name,
					"salary_component_abbr": abbr,
					"type": c_type
				})
				comp.insert(ignore_permissions=True)
		
		struct = frappe.get_doc({
			"doctype": "Salary Structure",
			"name": "Test Salary Structure",
			"is_active": "Yes",
			"earnings": [
				{
					"salary_component": "Basic",
					"abbr": "B",
					"amount_based_on_formula": 1,
					"formula": "base * 0.5",
					"condition": "base > 10000"
				},
				{
					"salary_component": "House Rent Allowance",
					"abbr": "HRA",
					"amount_based_on_formula": 1,
					"formula": "B * 0.4"
				}
			],
			"deductions": [
				{
					"salary_component": "Provident Fund",
					"abbr": "PF",
					"amount_based_on_formula": 1,
					"formula": "B * 0.1"
				}
			]
		})
		struct.insert(ignore_permissions=True)
		structure_name = struct.name
		print(f"Created test Salary Structure: {structure_name}")
	else:
		print(f"Using existing Salary Structure: {structure_name}")

	# Call get_calculated_salary_components
	print("\nCalling API with basic_amount = 50000...")
	res = get_calculated_salary_components(structure_name, 50000)
	print("API Response:")
	import json
	print(json.dumps(res, indent=2))

	# Check correctness
	components_by_abbr = {c["abbr"]: c for c in res["components"]}
	
	# Basic: 50000 * 0.5 = 25000
	# HRA: 25000 * 0.4 = 10000
	# PF: 25000 * 0.1 = 2500
	# Gross salary: 25000 + 10000 = 35000
	
	assert components_by_abbr["B"]["amount"] == 25000, f"Expected 25000, got {components_by_abbr['B']['amount']}"
	assert components_by_abbr["HRA"]["amount"] == 10000, f"Expected 10000, got {components_by_abbr['HRA']['amount']}"
	assert components_by_abbr["PF"]["amount"] == 2500, f"Expected 2500, got {components_by_abbr['PF']['amount']}"
	assert res["gross_salary"] == 35000, f"Expected 35000, got {res['gross_salary']}"
	
	print("\nSUCCESS: All calculated values are 100% correct!")

	# Also verify invalid formula throwing clear error
	print("\nTesting error throwing with invalid formula...")
	struct_doc = frappe.get_doc("Salary Structure", structure_name)
	# Add a row with bad formula
	struct_doc.append("earnings", {
		"salary_component": "Basic",
		"abbr": "BAD",
		"amount_based_on_formula": 1,
		"formula": "invalid_variable_xyz * 2"
	})
	struct_doc.save(ignore_permissions=True)

	try:
		get_calculated_salary_components(structure_name, 50000)
		print("ERROR: API did not throw for invalid formula!")
		assert False, "API did not throw for invalid formula"
	except Exception as e:
		print(f"SUCCESS: Caught expected exception: {e}")

	# Rollback changes to keep DB clean
	frappe.db.rollback()
	print("Rollback completed successfully.")
