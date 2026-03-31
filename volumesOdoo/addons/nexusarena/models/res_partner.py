from odoo import models, fields

class ResPartner(models.Model):
    #Usamos el modelo default contactos de Odoo y a partir de ahí añadimos el resto de campos
    #que nos interesen, en nuestro caso, los relacionados con los participantes de eSports

    _inherit = 'res.partner' # Heredamos de el modelo

    #CCampos
    es_participante= fields.Boolean(string="Es Participante de eSports", default=False, required=True)

    nick = fields.Char(string="Nick / Nombre Equipo", required=True)

    plataforma = fields.Selection([
        ('pc', 'PC'), ('console', 'Consola'), ('mobile', 'Móvil')
    ], string="Plataforma", required=True)

    experiencia = fields.Selection([
        ('amateur', 'Amateur'), ('pro', 'Profesional'), ('semi', 'Semiprofesional')
    ], string="Nivel de Experiencia", required=True)

    total_victorias = fields.Integer(string="Victorias Totales", default=0, required=True)