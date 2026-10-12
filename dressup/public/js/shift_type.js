/**
 * Shift Type – "Recheck Skipped Attendance" button
 *
 * Adds an Actions-group button to Shift Type that lets HR managers preview
 * and fix Employee Checkins that were incorrectly skipped because a
 * duplicate auto-Absent attendance already existed when the biometric
 * punches arrived late.
 */

frappe.ui.form.on("Shift Type", {
	refresh(frm) {
		if (!frm.doc.__islocal && frm.doc.enable_auto_attendance) {
			frm.add_custom_button(
				__("Recheck Skipped Attendance"),
				() => _show_recheck_dialog(frm),
				__("Actions")
			);
		}
	},
});

function _show_recheck_dialog(frm) {
	const today = frappe.datetime.get_today();
	const seven_days_ago = frappe.datetime.add_days(today, -7);

	const dialog = new frappe.ui.Dialog({
		title: __("Recheck Skipped Attendance"),
		fields: [
			{
				fieldname: "from_date",
				label: __("From Date"),
				fieldtype: "Date",
				default: seven_days_ago,
				reqd: 1,
			},
			{
				fieldname: "to_date",
				label: __("To Date"),
				fieldtype: "Date",
				default: today,
				reqd: 1,
			},
			{
				fieldname: "employee",
				label: __("Employee"),
				fieldtype: "Link",
				options: "Employee",
			},
			{
				fieldname: "preview_only",
				label: __("Preview only (dry run)"),
				fieldtype: "Check",
				default: 1,
			},
		],
		primary_action_label: __("Run"),
		primary_action(values) {
			dialog.hide();
			_call_recheck(frm, values, values.preview_only ? 1 : 0);
		},
	});
	dialog.show();
}

function _call_recheck(frm, values, dry_run) {
	frappe.call({
		method: "dressup.skipped_attendance.recheck_skipped_attendance",
		args: {
			shift_type: frm.doc.name,
			from_date: values.from_date,
			to_date: values.to_date,
			employee: values.employee || undefined,
			dry_run: dry_run,
		},
		freeze: true,
		freeze_message: dry_run
			? __("Scanning skipped checkins…")
			: __("Fixing skipped checkins…"),
		callback(r) {
			if (!r.message) return;
			_show_results(frm, r.message, values);
			frm.reload_doc();
		},
	});
}

function _show_results(frm, result, values) {
	const esc = frappe.utils.escape_html;
	let html = "";

	// --- To Fix / Fixed section ---
	if (result.to_fix && result.to_fix.length) {
		const heading = result.dry_run
			? __("Will be fixed ({0})", [result.to_fix.length])
			: __("Fixed ({0})", [result.to_fix.length]);
		html += _build_table(heading, result.to_fix, "green");
	}

	// --- Untouched section ---
	if (result.untouched && result.untouched.length) {
		html += _build_table(
			__("Left as-is ({0})", [result.untouched.length]),
			result.untouched,
			"orange"
		);
	}

	// --- Failed section ---
	if (result.failed && result.failed.length) {
		html += _build_table(
			__("Failed ({0})", [result.failed.length]),
			result.failed,
			"red"
		);
	}

	// --- Process message ---
	if (result.process_message) {
		html += `<p style="margin-top:12px"><strong>${esc(result.process_message)}</strong></p>`;
	}

	if (!html) {
		html = `<p>${__("No skipped checkins found.")}</p>`;
	}

	const msg_dialog = frappe.msgprint({
		title: result.dry_run
			? __("Preview — Skipped Attendance")
			: __("Result — Skipped Attendance"),
		message: html,
		indicator: result.failed && result.failed.length ? "orange" : "green",
		wide: true,
	});

	// In preview mode, offer a "Fix Now" button if there's something to fix
	if (result.dry_run && result.to_fix && result.to_fix.length) {
		msg_dialog.set_primary_action(__("Fix Now"), () => {
			msg_dialog.hide();
			_call_recheck(frm, values, 0);
		});
	}
}

function _build_table(heading, rows, color) {
	const esc = frappe.utils.escape_html;
	let table = `
		<h5 style="margin-top:15px;color:var(--text-${color})">
			${esc(heading)}
		</h5>
		<table class="table table-bordered table-condensed" style="margin-top:5px">
			<thead>
				<tr>
					<th>${__("Employee")}</th>
					<th>${__("Employee Name")}</th>
					<th>${__("Date")}</th>
					<th>${__("Checkins")}</th>
					<th>${__("Attendance")}</th>
					<th>${__("Status / Remark")}</th>
				</tr>
			</thead>
			<tbody>`;

	for (const row of rows) {
		const att_link = row.attendance
			? `<a href="/app/attendance/${encodeURIComponent(row.attendance)}"
				target="_blank">${esc(row.attendance)}</a>`
			: "—";
		table += `
			<tr>
				<td>${esc(row.employee)}</td>
				<td>${esc(row.employee_name)}</td>
				<td>${esc(row.date)}</td>
				<td>${esc(String(row.checkins))}</td>
				<td>${att_link}</td>
				<td>${esc(row.status)}</td>
			</tr>`;
	}

	table += "</tbody></table>";
	return table;
}
