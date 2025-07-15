from logging import exception

from odoo import api, fields, models
from dateutil.relativedelta import relativedelta
from odoo.exceptions import UserError, ValidationError
from odoo.tools.float_utils import float_compare, float_is_zero

class TestModel(models.Model):
    _name = "estate.property"
    _description = "table of real estate properties"
    _order = "id desc"

    name = fields.Char(required=True)
    description = fields.Text()
    postcode = fields.Char()
    active = fields.Boolean(default=True)
    date_availability = fields.Date(copy=False, default=fields.Date.today() + relativedelta(months=3))
    expected_price = fields.Float(required=True)
    selling_price = fields.Float(readonly=True, copy=False)
    best_price = fields.Float(compute="_compute_best")
    bedrooms = fields.Integer(default=2)
    living_area = fields.Integer(string='Living Area (sqm)')
    facades = fields.Integer()
    garage = fields.Boolean()
    garden = fields.Boolean()
    garden_area = fields.Integer(string='Garden Area (sqm)')
    garden_orientation = fields.Selection(
        string='Orientation',
        selection=[('north', 'North'), ('east', 'East'), ('south', 'South'), ('west', 'West')],
        help="Which direction is the garden facing.")
    total_area = fields.Integer(compute="_compute_total")
    state = fields.Selection(
        string='Status',
        selection=[('new', 'New'), ('offer received', 'Offer Received'), ('offer accepted', 'Offer Accepted'), ('sold', 'Sold'), ('cancelled', 'Cancelled')],
        default = 'new',
        required=True,
        copy=False)
    salesperson_id = fields.Many2one('res.users', string='Salesperson', index=True, default=lambda self: self.env.user)
    buyer_id = fields.Many2one('res.partner', string='Buyer', index=True, readonly=True)
    tag_ids = fields.Many2many("estate.property.tag", string="Tags")
    offer_ids = fields.One2many("estate.property.offer", "property_id", string="Offers")
    property_type_id = fields.Many2one("estate.property.type", string="Type")

    _sql_constraints = [
        ('check_expected_price', 'CHECK(expected_price > 0)','Expected price must be a positive number.'),
        ('check_selling_price', 'CHECK(selling_price > 0)','Selling price must be a positive number.')
    ]


    @api.depends('garden_area', 'living_area')
    def _compute_total(self):
        for line in self:
            line.total_area = line.garden_area + line.living_area

    @api.depends("offer_ids.price")
    def _compute_best(self):
        for record in self:
            if record.offer_ids:
                record.best_price = max(l.price for l in record.offer_ids)
            else:
                record.best_price = 0

    @api.onchange("garden")
    def _onchange_partner_id(self):
        if self.garden == True:
            self.garden_area = 10
            self.garden_orientation = "north"
        else:
            self.garden_area = None
            self.garden_orientation = None 

    @api.constrains('selling_price')
    def _check_selling_price(self):
        for record in self:
            if not (float_is_zero(record.selling_price, precision_rounding=0.01) or float_compare(record.selling_price, (record.expected_price*0.9), precision_rounding = 0.01) >= 0):
                raise ValidationError("The selling price must be at least 90% of the expected price!")

    @api.ondelete(at_uninstall=False)
    def _unlink_if_not_new_or_cancelled(self):
        for record in self:
            if not record.state in ('cancelled', 'new'):
                raise UserError('Only new and cancelled properties may be deleted.')

    def action_sell(self):
        for record in self:
            if record.state != "cancelled":
                record.state = "sold"
            else:
                raise UserError('Cancelled properties cannot be sold.')
        return True

    def action_cancel(self):
        for record in self:
            if record.state != "sold":
                record.state = "cancelled"
            else:
                raise UserError('Sold properties cannot be cancelled.')
        return True

    def offer_made(self):
        if self.state == 'new':
            self.state = 'offer received'