from odoo import fields, models

class PropertyTag(models.Model):
    _name = "estate.property.tag"
    _description = "table of property types"
    _order = "name"

    name = fields.Char(required=True)
    color = fields.Integer()

    _sql_constraints = [('unique_name', 'unique(name)', 'Name of the tag must be unique!')]