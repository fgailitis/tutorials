from odoo import api, fields, models
from dateutil.relativedelta import relativedelta
from odoo.exceptions import UserError, ValidationError
from odoo.tools.float_utils import float_compare, float_is_zero

class PropertyOffer(models.Model):
    _name = "estate.property.offer"
    _description = "table of property offers"
    _order = "price desc"

    price = fields.Float(required=True)
    status = fields.Selection(
        string='Status',
        selection=[('accepted', 'Accepted'), ('refused', 'Refused')],
        copy=False,
        readonly=True)
    partner_id = fields.Many2one('res.partner', string='Buyer', index=True,required=True)
    property_id = fields.Many2one('estate.property', string = 'Property', required=True)
    validity = fields.Integer(string="Validity (days)", default=7)
    date_deadline = fields.Date(compute="_compute_deadline_date", inverse="_inverse_deadline_date")
    property_type_id = fields.Many2one("estate.property.type", stored=True, related = "property_id.property_type_id")


    _sql_constraints = [
        ('check_price', 'CHECK(price > 0)','Price must be a positive number.')
    ]


    @api.depends('validity')
    def _compute_deadline_date(self):
        for record in self:
            if record.create_date:
                record.date_deadline = record.create_date.date() + relativedelta(days=record.validity)
            else:
                record.date_deadline = fields.Date.today() + relativedelta(days=record.validity)

    def _inverse_deadline_date(self):
        for record in self:
            if record.date_deadline:
                if record.create_date:
                    base_date = record.create_date.date()
                else:
                    base_date = fields.Date.today()
                record.validity = (record.date_deadline - base_date).days
            else:
               record.validity = 0


    @api.model
    def create(self, vals):
        self.env['estate.property'].browse(vals['property_id']).offer_made()
        if not (float_is_zero(self.env['estate.property'].browse(vals['property_id']).best_price, precision_rounding=0.01) or float_compare(vals.get('price', 0.01), self.env['estate.property'].browse(vals['property_id']).best_price, precision_rounding = 0.01) >= 1):
            raise UserError('Price must be greater than the current best offer.')
        return super(PropertyOffer, self).create(vals)

    def action_accept(self):
        for record in self:
            if record.status != "refused" and not record.property_id.buyer_id:
                record.status = "accepted"
                record.property_id.state = "offer accepted"
                record.property_id.buyer_id = record.partner_id
                record.property_id.selling_price = record.price
            elif record.property_id.buyer_id:
                raise UserError('Another offer has already been accepted.')
            else:
                raise UserError('This offer has already been refused.')
        return True
    def action_refuse(self):
        for record in self:
            if record.status != "accepted":
                record.status = "refused"
            else:
                raise UserError('This offer has already been accepted.')
        return True