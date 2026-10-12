/**
 * Attendance – "Recheck Skipped Checkin" button on Absent records
 *
 * If an Attendance is marked Absent (e.g. auto-marked due to delayed biometric sync),
 * allows HR to recheck checkins and update the Attendance in-place to Present / Half Day
 * without cancelling the document.
 */

frappe.ui.form.on("Attendance", {
	refresh(frm) {
		if (!frm.doc.__islocal && frm.doc.docstatus === 1 && frm.doc.status === "Absent") {
			frm.add_custom_button(
				__("Recheck Skipped Checkin"),
				() => _recheck_single_attendance(frm),
				__("Actions")
			);
		}
	},
});

function _recheck_single_attendance(frm) {
	frappe.call({
		method: "dressup.skipped_attendance.recheck_single_attendance",
		args: {
			attendance_name: frm.doc.name,
			dry_run: 1,
		},
		freeze: true,
		freeze_message: __("Checking biometric logs…"),
		callback(r) {
			const res = r.message;
			if (!res) return;

			if (!res.found) {
				frappe.msgprint({
					title: __("No Skipped Checkins"),
					message: res.message,
					indicator: "orange",
				});
				return;
			}

			const esc = frappe.utils.escape_html;
			const html = `
				<div style="font-size: 13px; line-height: 1.6;">
					<p><strong>${__("Found {0} check-in log(s)", [res.checkin_count])}</strong> ${__("for this date.")}</p>
					<table class="table table-bordered table-condensed" style="margin-top: 10px;">
						<tr>
							<th style="width: 40%;">${__("Current Status")}</th>
							<td><span class="indicator-pill red">${esc(res.current_status)}</span></td>
						</tr>
						<tr>
							<th>${__("Calculated Status")}</th>
							<td><span class="indicator-pill green"><strong>${esc(res.new_status)}</strong></span></td>
						</tr>
						<tr>
							<th>${__("Working Hours")}</th>
							<td><strong>${esc(String(res.working_hours))} hrs</strong></td>
						</tr>
						<tr>
							<th>${__("Shift")}</th>
							<td>${esc(res.shift || "—")}</td>
						</tr>
						<tr>
							<th>${__("In Time / Out Time")}</th>
							<td>${esc(res.in_time || "—")} &nbsp;➔&nbsp; ${esc(res.out_time || "—")}</td>
						</tr>
					</table>
					<p style="color: var(--text-muted); margin-top: 8px;">
						<em>${__("Updating will modify this Attendance record in-place and link the check-in logs.")}</em>
					</p>
				</div>
			`;

			const d = new frappe.ui.Dialog({
				title: __("Update Attendance from Checkins"),
				fields: [
					{
						fieldtype: "HTML",
						fieldname: "preview_html",
						options: html,
					},
				],
				primary_action_label: __("Update Attendance"),
				primary_action() {
					d.hide();
					_apply_single_update(frm);
				},
			});
			d.show();
		},
	});
}

function _apply_single_update(frm) {
	frappe.call({
		method: "dressup.skipped_attendance.recheck_single_attendance",
		args: {
			attendance_name: frm.doc.name,
			dry_run: 0,
		},
		freeze: true,
		freeze_message: __("Updating Attendance…"),
		callback(r) {
			const res = r.message;
			if (res && res.success) {
				frappe.show_alert({
					message: res.message,
					indicator: "green",
				}, 5);
				frm.reload_doc();
			}
		},
	});
}
