/**
 * Attendance List View – "Recheck Skipped Attendance" Bulk Tool
 *
 * Adds an inner button to Attendance list view to allow HR users to bulk scan
 * and fix skipped checkins for a date range in-place without cancelling documents.
 */

frappe.listview_settings["Attendance"] = frappe.listview_settings["Attendance"] || {};

const _existing_attendance_onload = frappe.listview_settings["Attendance"].onload;

frappe.listview_settings["Attendance"].onload = function (listview) {
	if (_existing_attendance_onload) {
		_existing_attendance_onload.call(this, listview);
	}

	listview.page.add_inner_button(
		__("Recheck Skipped Attendance"),
		() => _show_bulk_dialog(listview),
		__("Actions")
	);

	listview.page.add_inner_button(
		__("Fix All Attendance by Checkins"),
		() => _show_fix_all_dialog(listview),
		__("Actions")
	);
};

function _show_bulk_dialog(listview) {
	const today = frappe.datetime.get_today();
	const seven_days_ago = frappe.datetime.add_days(today, -7);

	const dialog = new frappe.ui.Dialog({
		title: __("Recheck Skipped Attendance"),
		fields: [
			{
				fieldname: "mode_info",
				fieldtype: "HTML",
				options: `
					<div style="padding: 8px; background: #e8f4fd; border-radius: 4px; margin-bottom: 12px;">
						<p style="margin: 0; color: #1f4e78; font-size: 13px;">
							<strong>💡 Two Modes Available:</strong><br>
							<span style="font-size: 12px;">
							• <strong>Skipped Checkins Only:</strong> Faster, only checks Employee Checkins with skip flag<br>
							• <strong>All Absent Records:</strong> Comprehensive, checks all Absent attendance with any checkins
							</span>
						</p>
					</div>
				`
			},
			{
				fieldname: "check_mode",
				label: __("Check Mode"),
				fieldtype: "Select",
				options: [
					"Skipped Checkins Only",
					"All Absent Records"
				],
				default: "All Absent Records",
				description: __("Choose which records to check")
			},
			{
				fieldname: "section_break_1",
				fieldtype: "Section Break"
			},
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
				fieldname: "column_break_1",
				fieldtype: "Column Break"
			},
			{
				fieldname: "shift_type",
				label: __("Shift Type"),
				fieldtype: "Link",
				options: "Shift Type",
			},
			{
				fieldname: "employee",
				label: __("Employee"),
				fieldtype: "Link",
				options: "Employee",
			},
			{
				fieldname: "section_break_2",
				fieldtype: "Section Break"
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
			const check_all = values.check_mode === "All Absent Records" ? 1 : 0;
			_call_bulk_recheck(listview, values, values.preview_only ? 1 : 0, check_all);
		},
	});
	dialog.show();
}

function _call_bulk_recheck(listview, values, dry_run, check_all) {
	frappe.call({
		method: "dressup.skipped_attendance.recheck_skipped_attendance",
		args: {
			shift_type: values.shift_type || undefined,
			from_date: values.from_date,
			to_date: values.to_date,
			employee: values.employee || undefined,
			dry_run: dry_run,
			check_all: check_all || 0,
		},
		freeze: true,
		freeze_message: dry_run
			? __("Scanning attendance records…")
			: __("Updating attendance records in-place…"),
		callback(r) {
			if (!r.message) return;
			_show_bulk_results(listview, r.message, values, check_all);
			if (!dry_run) {
				listview.refresh();
			}
		},
	});
}

function _show_bulk_results(listview, result, values, check_all) {
	const esc = frappe.utils.escape_html;
	let html = "";

	if (result.to_fix && result.to_fix.length) {
		const heading = result.dry_run
			? __("Will be updated in-place ({0})", [result.to_fix.length])
			: __("Updated in-place ({0})", [result.to_fix.length]);
		html += _build_table(heading, result.to_fix, "green");
	}

	if (result.untouched && result.untouched.length) {
		html += _build_table(
			__("Left as-is ({0})", [result.untouched.length]),
			result.untouched,
			"orange"
		);
	}

	if (result.failed && result.failed.length) {
		html += _build_table(
			__("Failed ({0})", [result.failed.length]),
			result.failed,
			"red"
		);
	}

	if (result.process_message) {
		html += `<p style="margin-top:12px"><strong>${esc(result.process_message)}</strong></p>`;
	}

	if (!html) {
		html = `<p>${__("No records found to process.")}</p>`;
	}

	const msg_dialog = frappe.msgprint({
		title: result.dry_run
			? __("Preview — Recheck Attendance")
			: __("Result — Recheck Attendance"),
		message: html,
		indicator: result.failed && result.failed.length ? "orange" : "green",
		wide: true,
	});

	if (result.dry_run && result.to_fix && result.to_fix.length) {
		msg_dialog.set_primary_action(__("Fix Now (In-Place)"), () => {
			msg_dialog.hide();
			_call_bulk_recheck(listview, values, 0, check_all);
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

// ============================================================================
// New Feature: Fix All Attendance by Checkins
// ============================================================================

function _show_fix_all_dialog(listview) {
	const today = frappe.datetime.get_today();
	const seven_days_ago = frappe.datetime.add_days(today, -7);

	const dialog = new frappe.ui.Dialog({
		title: __("Fix All Attendance by Checkins"),
		fields: [
			{
				fieldname: "description",
				fieldtype: "HTML",
				options: `
					<div style="padding: 10px; background: #f8f9fa; border-radius: 4px; margin-bottom: 15px;">
						<p style="margin: 0; color: #495057;">
							<strong>📋 ${__("This tool checks ALL attendance records")}</strong><br>
							${__("It will compare attendance status with actual check-in/out logs and fix mismatches.")}
						</p>
					</div>
				`
			},
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
				fieldname: "column_break_1",
				fieldtype: "Column Break"
			},
			{
				fieldname: "employee",
				label: __("Employee"),
				fieldtype: "Link",
				options: "Employee",
			},
			{
				fieldname: "department",
				label: __("Department"),
				fieldtype: "Link",
				options: "Department",
			},
			{
				fieldname: "section_break_1",
				fieldtype: "Section Break"
			},
			{
				fieldname: "shift_type",
				label: __("Shift Type"),
				fieldtype: "Link",
				options: "Shift Type",
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
			_call_fix_all_attendance(listview, values, values.preview_only ? 1 : 0);
		},
	});
	dialog.show();
}

function _call_fix_all_attendance(listview, values, dry_run) {
	frappe.call({
		method: "dressup.skipped_attendance.recheck_all_attendance",
		args: {
			from_date: values.from_date,
			to_date: values.to_date,
			employee: values.employee || undefined,
			department: values.department || undefined,
			shift_type: values.shift_type || undefined,
			dry_run: dry_run,
		},
		freeze: true,
		freeze_message: dry_run
			? __("Scanning all attendance records…")
			: __("Fixing attendance records based on checkins…"),
		callback(r) {
			if (!r.message) return;
			_show_fix_all_results(listview, r.message, values);
			if (!dry_run) {
				listview.refresh();
			}
		},
	});
}

function _show_fix_all_results(listview, result, values) {
	const esc = frappe.utils.escape_html;
	let html = "";

	if (result.to_fix && result.to_fix.length) {
		const heading = result.dry_run
			? __("Will be fixed ({0})", [result.to_fix.length])
			: __("Fixed ({0})", [result.to_fix.length]);
		html += _build_table(heading, result.to_fix, "green");
	}

	if (result.untouched && result.untouched.length) {
		html += _build_table(
			__("Already Correct / Kept as-is ({0})", [result.untouched.length]),
			result.untouched,
			"blue"
		);
	}

	if (result.failed && result.failed.length) {
		html += _build_table(
			__("Failed ({0})", [result.failed.length]),
			result.failed,
			"red"
		);
	}

	if (result.process_message) {
		html += `<p style="margin-top:12px"><strong>${esc(result.process_message)}</strong></p>`;
	}

	if (!html) {
		html = `<p>${__("No attendance records found.")}</p>`;
	}

	const msg_dialog = frappe.msgprint({
		title: result.dry_run
			? __("Preview — Fix Attendance by Checkins")
			: __("Result — Fix Attendance by Checkins"),
		message: html,
		indicator: result.failed && result.failed.length ? "orange" : "green",
		wide: true,
	});

	if (result.dry_run && result.to_fix && result.to_fix.length) {
		msg_dialog.set_primary_action(__("Fix Now"), () => {
			msg_dialog.hide();
			_call_fix_all_attendance(listview, values, 0);
		});
	}
}
