# Copyright (c) 2026, Prime Technology of Bangladesh and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import get_datetime, now_datetime, get_link_to_form


class JobApplicantInvitation(Document):
	def validate(self):
		self.validate_times()
		self.validate_online_mode()
		self.validate_duplicate_invitation()

	def on_submit(self):
		if self.status == "Draft":
			self.status = "Sent"

	def validate_times(self):
		if self.interview_time and self.interview_end_time:
			if self.interview_time >= self.interview_end_time:
				frappe.throw(_("Interview Start Time must be before End Time."))

	def validate_online_mode(self):
		if self.interview_mode != "In-Person" and not self.meeting_link:
			frappe.throw(_("Meeting Link is required for Online/Phone interviews."))

	def validate_duplicate_invitation(self):
		# Avoid duplicate active invitations for the same applicant and same round
		duplicates = frappe.get_all(
			"Job Applicant Invitation",
			filters={
				"job_applicant": self.job_applicant,
				"interview_round": self.interview_round,
				"status": ["not in", ["Cancelled", "Declined"]],
				"name": ["!=", self.name or ""],
				"docstatus": ["<", 2]
			}
		)
		if duplicates:
			frappe.throw(
				_("An active interview invitation already exists for applicant {0} and round {1}: {2}").format(
					frappe.bold(self.applicant_name or self.job_applicant),
					frappe.bold(self.interview_round),
					frappe.bold(get_link_to_form("Job Applicant Invitation", duplicates[0].name))
				)
			)

	@frappe.whitelist()
	def send_invitation_email(self):
		if not self.applicant_email:
			frappe.throw(_("Applicant does not have a valid email address."))

		# Render the print format to attach as PDF
		# Defaulting to standard print format or "Invitation Letter"
		print_format = "Invitation Letter"
		
		# Generate Email body
		subject = _("Interview Invitation: {0} for {1}").format(self.interview_round, self.job_opening or self.designation or "Position")
		
		meeting_info = ""
		if self.interview_mode != "In-Person" and self.meeting_link:
			meeting_info = f"<p><strong>Meeting Link:</strong> <a href='{self.meeting_link}'>{self.meeting_link}</a></p>"
		else:
			meeting_info = f"<p><strong>Venue:</strong> {self.venue or ''}</p>"

		message = f"""
		<p>Dear {self.applicant_name or 'Candidate'},</p>
		<p>We are pleased to invite you for an interview for the position of <strong>{self.job_opening or self.designation or 'Position'}</strong>.</p>
		<p><strong>Interview Details:</strong></p>
		<ul>
			<li><strong>Round:</strong> {self.interview_round}</li>
			<li><strong>Date:</strong> {self.interview_date}</li>
			<li><strong>Time:</strong> {self.interview_time} to {self.interview_end_time}</li>
			<li><strong>Mode:</strong> {self.interview_mode}</li>
		</ul>
		{meeting_info}
		<p>Please find the formal invitation letter attached to this email.</p>
		<p>Please RSVP to confirm your availability.</p>
		<p>Best regards,</p>
		<p>HR Team<br>DressUp Manufacturing</p>
		"""

		try:
			# Attach PDF of the invitation letter
			attachments = []
			try:
				pdf_content = frappe.attach_print(
					self.doctype, self.name, print_format=print_format
				)
				attachments.append({
					"fname": f"Interview_Invitation_{self.name}.pdf",
					"fcontent": pdf_content
				})
			except Exception as e:
				frappe.log_error(message=frappe.get_traceback(), title="Invitation PDF Generation Error")
				# Send without attachment if PDF generation fails
				pass

			frappe.sendmail(
				recipients=[self.applicant_email],
				subject=subject,
				message=message,
				attachments=attachments,
				reference_doctype=self.doctype,
				reference_name=self.name
			)

			self.db_set("email_sent", 1)
			self.db_set("email_sent_on", now_datetime())
			if self.status == "Draft":
				self.db_set("status", "Sent")

			frappe.msgprint(_("Invitation Email sent successfully to {0}").format(self.applicant_email), indicator="green")
		except Exception as e:
			frappe.log_error(message=frappe.get_traceback(), title="Invitation Email Sending Error")
			frappe.throw(_("Failed to send invitation email. Please check your email configuration."))

	@frappe.whitelist()
	def update_rsvp(self, rsvp_status):
		if rsvp_status not in ["Confirmed", "Declined", "Pending"]:
			frappe.throw(_("Invalid RSVP Status."))

		self.db_set("rsvp_status", rsvp_status)
		self.db_set("rsvp_date", now_datetime())

		if rsvp_status == "Confirmed":
			self.db_set("status", "Confirmed")
			# Auto create the Interview record in HRMS if not already created
			self.create_hrms_interview()
		elif rsvp_status == "Declined":
			self.db_set("status", "Declined")

	@frappe.whitelist()
	def create_hrms_interview(self):
		if self.interview:
			# Interview already exists and linked
			return self.interview

		# Check if an active interview already exists for this applicant and round
		existing_interview = frappe.db.exists(
			"Interview",
			{
				"job_applicant": self.job_applicant,
				"interview_round": self.interview_round,
				"docstatus": ["<", 2]
			}
		)

		if existing_interview:
			self.db_set("interview", existing_interview)
			frappe.msgprint(_("Linked to existing HRMS Interview: {0}").format(existing_interview))
			return existing_interview

		# Create new HRMS Interview doc
		try:
			interview = frappe.new_doc("Interview")
			interview.job_applicant = self.job_applicant
			interview.interview_round = self.interview_round
			interview.scheduled_on = self.interview_date
			interview.from_time = self.interview_time
			interview.to_time = self.interview_end_time
			interview.designation = self.designation
			interview.job_opening = self.job_opening
			interview.resume_link = frappe.db.get_value("Job Applicant", self.job_applicant, "resume_link")

			# Add Panel Members to interview details child table
			for member in self.interview_panel:
				# HRMS Interview Detail child table needs 'interviewer' field which is user ID
				# Let's get User ID from Employee document
				user_id = frappe.db.get_value("Employee", member.employee, "user_id")
				if user_id:
					interview.append("interview_details", {
						"interviewer": user_id
					})
				else:
					# If user_id is not set, try using employee email
					employee_email = frappe.db.get_value("Employee", member.employee, "personal_email") or frappe.db.get_value("Employee", member.employee, "company_email")
					if employee_email:
						# Try to find user with this email
						user_from_email = frappe.db.get_value("User", {"email": employee_email}, "name")
						if user_from_email:
							interview.append("interview_details", {
								"interviewer": user_from_email
							})

			interview.insert(ignore_permissions=True)
			
			# Submit the interview so it becomes official in HRMS
			# (In HRMS, submittable Interviews represent scheduled/active rounds)
			# Let's save it as Draft first, so HR can submit/review it.
			
			self.db_set("interview", interview.name)
			frappe.msgprint(_("HRMS Interview {0} created and linked successfully.").format(get_link_to_form("Interview", interview.name)), indicator="green")
			return interview.name
		except Exception as e:
			frappe.log_error(message=frappe.get_traceback(), title="Auto-Create Interview Error")
			frappe.msgprint(_("Could not auto-create HRMS Interview. Please check logs."))
			return None
