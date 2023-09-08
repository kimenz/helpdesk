# Copyright (C) 2019 - TODAY, Open Source Integrators
# Copyright (C) 2022 - TODAY, Popsolutions
# Copyright (C) 2022 - TODAY, Mateus ONunes
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

import re
from odoo import fields, models


class HelpdeskTicket(models.Model):
    _inherit = "helpdesk.ticket"

    fsm_equipment_id = fields.Many2one("fsm.equipment", string="FSM Equipment")

    def action_create_order(self):
        """
        This function returns an action that displays a full FSM Order
        form when creating an FSM Order from a ticket.
        """
        action = self.env["ir.actions.actions"]._for_xml_id(
            "fieldservice.action_fsm_operation_order"
        )
        # 1 = Maintenance, 3 = Repair
        order_type = 1 if self.type_id.id == 1 else 3
        
        # description witout html tags using regex
        description = re.sub('<[^<]+?>', '', self.description)
        
        # override the context to get rid of the default filtering
        action["context"] = {
            "default_ticket_id": self.id,
            "default_priority": self.priority,
            "default_location_id": self.fsm_location_id.id,
            "default_equipment_id": self.fsm_equipment_id.id,
            "type": order_type,
            "default_type": order_type,
            "default_customer_id": self.partner_id.id,
            "default_team_id": self.team_id.fsm_team_id[0].id,
            "default_description": description,
        }
        res = self.env.ref("fieldservice.fsm_order_form", False)
        action["views"] = [(res and res.id or False, "form")]
        return action
