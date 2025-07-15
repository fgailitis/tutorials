from odoo import api, fields, models

class PropertyType(models.Model):
    _name = "estate.property.type"
    _description = "table of property types"
    _order = "sequence, name"

    name = fields.Char(required=True)
    sequence = fields.Integer('Sequence', default=1, help="Used to order stages. Lower is better.")
    property_ids = fields.One2many("estate.property", 'property_type_id', string="Property")
    offer_ids = fields.One2many("estate.property.offer", 'property_type_id', string = "Offers")
    offer_count = fields.Integer(compute="_compute_offer_count")


    _sql_constraints = [('unique_name', 'unique(name)', 'Name of the type must be unique!')]




    @api.depends("offer_ids")
    def _compute_offer_count(self):
        for record in self:
            count = 0
            for id in record.offer_ids:
                count += 1
            record.offer_count = count