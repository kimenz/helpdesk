import base64
import logging

import werkzeug

import odoo.http as http
from odoo.http import request

from odoo.addons.helpdesk_mgmt.controllers.main import HelpdeskTicketController

_logger = logging.getLogger(__name__)


class HelpdeskTicketControllerInherit(HelpdeskTicketController):

    def _get_partner(self):
        partner_id = http.request.env.user.partner_id
        while partner_id.parent_id:
            partner_id = partner_id.parent_id
        return partner_id

    @http.route("/ticket/close", type="http", auth="user")
    def support_ticket_close(self, **kw):
        """Close the support ticket"""
        values = {
            field_name: int(field_value) if field_name.endswith("_id") else field_value
            for field_name, field_value in kw.items()
        }
        ticket = (
            http.request.env["helpdesk.ticket"]
            .sudo()
            .search([("id", "=", values["ticket_id"])])
        )
        ticket.stage_id = values.get("stage_id")

        return werkzeug.utils.redirect(f"/my/ticket/{str(ticket.id)}")

    @http.route("/new/ticket", type="http", auth="user", website=True)
    def create_new_ticket(self, **kw):
        categories = http.request.env["helpdesk.ticket.category"].search(
            [("active", "=", True)]
        )
        partner_id = self._get_partner()
        locations = http.request.env["fsm.location"].sudo().search(
            [
                ("active", "=", True),
                ("owner_id", "=", partner_id.id),
                ("equipment_ids", "!=", False),
            ]
        )
        equipments_ids = http.request.env["fsm.equipment"].search(
            [("active", "=", True), ("owned_by_id", "=", partner_id.id)], order="name"
        )

        email = http.request.env.user.email
        name = http.request.env.user.name
        return http.request.render(
            "helpdesk_mgmt.portal_create_ticket",
            {
                "categories": categories,
                "email": email,
                "name": name,
                "locations": locations,
                "equipments_ids": equipments_ids,
            },
        )

    @http.route("/submitted/ticket", type="http", auth="user", website=True, csrf=True)
    def submit_ticket(self, **kw):
        category = http.request.env["helpdesk.ticket.category"].browse(
            int(kw.get("category"))
        )
        vals = {
            "company_id": category.company_id.id or http.request.env.user.company_id.id,
            "category_id": category.id,
            "description": kw.get("description"),
            "name": kw.get("subject"),
            "attachment_ids": False,
            "channel_id": request.env["helpdesk.ticket.channel"]
            .sudo()
            .search([("name", "=", "Web")])
            .id,
            "partner_id": request.env.user.partner_id.id,
            "partner_name": request.env.user.partner_id.name,
            "partner_email": request.env.user.partner_id.email,
            "fsm_location_id": int(kw.get("locations")),
            "fsm_equipment_id": int(kw.get("equipments")),
        }
        new_ticket = request.env["helpdesk.ticket"].sudo().create(vals)
        new_ticket.message_subscribe(partner_ids=request.env.user.partner_id.ids)
        if kw.get("attachment"):
            for c_file in request.httprequest.files.getlist("attachment"):
                data = c_file.read()
                if c_file.filename:
                    request.env["ir.attachment"].sudo().create(
                        {
                            "name": c_file.filename,
                            "datas": base64.b64encode(data),
                            "res_model": "helpdesk.ticket",
                            "res_id": new_ticket.id,
                        }
                    )
        return werkzeug.utils.redirect(f"/my/ticket/{new_ticket.id}")
