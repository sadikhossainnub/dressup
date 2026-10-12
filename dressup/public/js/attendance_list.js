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
};

function _show_bulk_dialog(listview) {
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
				fieldname: "preview_only",
				label: __("Preview only (dry run)"),
				fieldtype: "Check",
				default: 1,
			},
		],
		primary_action_label: __("Run"),
		primary_action(values) {
			dialog.hide();
			_call_bulk_recheck(listview, values, values.preview_only ? 1 : 0);
		},
	});
	dialog.show();
}

function _call_bulk_recheck(listview, values, dry_run) {
	frappe.call({
		method: "dressup.skipped_attendance.recheck_skipped_attendance",
		args: {
			shift_type: values.shift_type || undefined,
			from_date: values.from_date,
			to_date: values.to_date,
			employee: values.employee || undefined,
			dry_run: dry_run,
		},
		freeze: true,
		freeze_message: dry_run
			? __("Scanning skipped checkins…")
			: __("Updating attendance records in-place…"),
		callback(r) {
			if (!r.message) return;
			_show_bulk_results(listview, r.message, values);
			if (!dry_run) {
				listview.refresh();
			}
		},
	});
}

function _show_bulk_results(listview, result, values) {
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

	if (result.dry_run && result.to_fix && result.to_fix.length) {
		msg_dialog.set_primary_action(__("Fix Now (In-Place)"), () => {
			msg_dialog.hide();
			_call_bulk_recheck(listview, values, 0);
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
