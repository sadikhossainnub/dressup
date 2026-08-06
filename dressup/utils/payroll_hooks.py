def fix_payroll_payable_party(doc, method):
    for row in doc.accounts:
        if row.account == "Payroll Payable - DU" and not row.party:
            row.party_type = "Company"
            row.party = "Dress Up"
