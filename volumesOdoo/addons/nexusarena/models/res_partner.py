from odoo import models, fields


class ResPartner(models.Model):
    #Usamos el modelo contactos de Odoo y a partir de ahí añadimos el resto de campos
    #que nos interesen, en nuestro caso, los relacionados con los participantes

    # Datos competitivos de un participante
    tipo_jugador = fields.Selection([
        ('jugador', 'Jugador Individual'),
        ('equipo', 'Equipo Competitivo'),
    ], string="Tipo de Jugador")

    nick = fields.Char(string="Nick / Nombre Equipo")

    pais_origen = fields.Char(string="País de Origen")

    plataforma = fields.Selection([
        ('pc', 'PC'), ('console', 'Consola'), ('mobile', 'Móvil')
    ], string="Plataforma")

    experiencia = fields.Selection([
        ('amateur', 'Amateur'), ('pro', 'Profesional'), ('semi', 'Semiprofesional')
    ], string="Nivel de Experiencia", required=True)

    #Lo que pone en el enunciado de "para equipos", todavía no se hacerlo
    #entonces de momento no lo pongo, pero la idea sería que si el tipo de jugador es "equipo", 
    #entonces aparezca un campo para añadir los miembros del equipo, que podrían ser otros contactos de Odoo, 
    #y si el tipo de jugador es "jugador individual", entonces ese campo no aparezca.

    #Campo calculado para una proxima entrega
    #total_participaciones
    #total_victorias