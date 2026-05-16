# Nexus Arena

Módulo de Odoo 18 para la **gestión integral de torneos de eSports**: videojuegos, torneos, inscripciones, partidas y clasificaciones, con facturación automática y notificaciones internas.

---

## 1. Descripción

Nexus Arena es un módulo desarrollado en Odoo que cubre el ciclo completo de un torneo de eSports:

- Catálogo de **videojuegos** sobre los que se compite.
- **Torneos** con formato (liga / eliminación directa / doble eliminación), modalidad (presencial / online / híbrido), premios y cuota de inscripción.
- **Inscripciones** de jugadores o equipos, con facturación automática de la cuota al confirmar.
- **Partidas** organizadas por fases (grupos, cuartos, semifinal, final, tercer puesto) con cálculo automático del ganador.
- **Clasificación final** (standings) con sistema de puntos 3-1-0 y generación de facturas de premio.
- Integración con `res.partner` para representar a participantes (jugadores individuales y equipos).
- **Roles** (Administrador, Organizador, Participante) con reglas de acceso adecuadas.

---

## 2. Stack y arranque

El proyecto se ejecuta con **Docker Compose** usando las imágenes oficiales de Odoo y PostgreSQL.

### Requisitos
- Docker y Docker Compose.

### Servicios (`docker-compose.yml`)
- **web**: `odoo:latest` en el puerto `8069` (modo `--dev=all`).
- **db**: `postgres:latest` con `POSTGRES_USER=odoo`, `POSTGRES_PASSWORD=odoo`, expuesto en el puerto `5433` del host.

### Arranque
```bash
docker compose up -d
```

Luego abre [http://localhost:8069](http://localhost:8069), crea la base de datos y **marca el check "Cargar datos demo"** para tener participantes, torneos, inscripciones, partidas y standings ya cargados.

Tras crear la base de datos, instala el módulo **Nexus Arena** desde *Apps* (puede que tengas que pulsar "Actualizar lista de aplicaciones").

---

## 3. Estructura del módulo

```
volumesOdoo/addons/nexusarena/
├── __init__.py
├── __manifest__.py
├── models/
│   ├── esports_game.py          # Catálogo de videojuegos
│   ├── esports_tournament.py    # Modelo principal de torneos
│   ├── esports_registration.py  # Inscripciones + factura de cuota
│   ├── esports_match.py         # Partidas + cálculo de ganador + enlaces de bracket
│   ├── esports_standing.py      # Clasificación + factura de premio
│   └── res_partner.py           # Extensión de contactos (jugadores/equipos)
├── wizards/
│   └── generate_bracket_wizard.py  # Wizard de generación automática del bracket
├── views/
│   ├── esports_game_views.xml
│   ├── esports_tournament_views.xml
│   ├── esports_registration_views.xml
│   ├── esports_match_views.xml         # Incluye vista calendar
│   ├── esports_standing_views.xml
│   ├── res_partner_views.xml
│   ├── generate_bracket_wizard_views.xml # Formulario del wizard
│   └── nexusarena_menus.xml
├── security/
│   ├── groups.xml               # 3 grupos: admin, organizador, participante
│   ├── ir.model.access.csv      # Permisos CRUD por grupo (incluye el wizard)
│   └── rules.xml                # Reglas de registro para participante
└── demo/
    └── nexusarena_demo.xml      # 20 participantes, 5 juegos, 4 torneos, 15 inscripciones, 10 partidas, 8 standings
```

---

## 4. Modelos

| Modelo | Descripción |
|---|---|
| `esports.game` | Videojuego (nombre, género, desarrollador, modalidad, logo). |
| `esports.tournament` | Torneo (formato, modalidad, fechas, premios, cuota, estado). |
| `esports.registration` | Inscripción de un participante en un torneo. |
| `esports.match` | Partida entre dos participantes en una fase. |
| `esports.standing` | Posición final de un participante con estadísticas y premio. |
| `res.partner` (extendido) | Participante (jugador o equipo) con campos de eSports. |

Todos los modelos relevantes heredan `mail.thread` para chatter y notificaciones.

---

## 5. Flujo de uso

1. Crear/elegir un **videojuego**.
2. Crear un **torneo** en estado *Borrador*, con cuota y premios.
3. Pulsar **"Abrir inscripciones"** → estado *Inscripciones Abiertas*.
4. Crear **inscripciones** y pulsar **"Confirmar inscripción"** en cada una; al confirmar se genera **automáticamente una factura** de venta para la cuota y se vincula a la inscripción.
5. Pulsar **"Iniciar torneo"** (requiere ≥ 2 inscripciones confirmadas) → estado *En Curso*.
6. Crear **partidas**, asignar fase y participantes, e ir registrando resultados con **"Registrar resultado"** (la partida queda *Finalizada* y se recalcula el ganador).
7. Crear o ajustar **clasificaciones** (`esports.standing`) con la posición final de cada participante.
8. Pulsar **"Finalizar torneo"** (todas las partidas deben estar cerradas) → estado *Finalizado*.
9. Desde cada standing, pulsar **"Generar factura de premio"** para emitir el reembolso correspondiente.

---

## 6. Roles y seguridad

| Rol | Grupo Odoo | Capacidades principales |
|---|---|---|
| **Administrador** | `nexusarena.group_tourney_admin` | CRUD total. Único que puede editar/eliminar torneos finalizados o cancelados. |
| **Organizador** | `nexusarena.group_tourney_organizer` | Crear/editar torneos, inscripciones, partidas y videojuegos. No puede eliminar. Standings y facturas en solo lectura. |
| **Participante** | `nexusarena.group_tourney_participant` | Solo lectura. Reglas de registro restrictivas (ver "Extras"). |

Las reglas (`security/rules.xml`) limitan al participante a:
- Ver **solo sus propias inscripciones**.
- Ver torneos según la regla ampliada descrita en la sección de extras.

---

## 7. Decisiones propias / Funcionalidades extra

> Importante: estas funcionalidades **no estaban exigidas literalmente por el enunciado** pero se han añadido por considerarse mejoras lógicas o necesarias. El detalle original está en [`extras_modulo.txt`](extras_modulo.txt).

### 7.1. Visibilidad de torneos para el participante (regla de registro ampliada)
El enunciado decía que el participante "solo puede ver los torneos públicos". Se ha interpretado de forma **más restrictiva y lógica**: el participante solo ve los torneos con **inscripciones abiertas** (donde puede apuntarse) y los **en curso en los que está inscrito** (para seguir su progreso). Los torneos finalizados, cancelados o en borrador no le son de utilidad y no los ve.

Además, se ha **ampliado** la regla para que un participante pueda ver un torneo **privado** si ya está inscrito en él, sin importar si está en *Inscripciones Abiertas*, *En Curso* o *Finalizado*. Así, si un organizador crea un torneo privado e inscribe manualmente a un jugador, ese jugador puede acceder al torneo sin necesidad de que sea público.

### 7.2. Notificaciones internas en la bandeja de Discuss
El botón **"Notificar participantes"** publica el mensaje en el chatter del torneo vía `mail.message` (eso es lo obligatorio). Como **extra**, el mismo botón envía la notificación **directamente a la bandeja de entrada de Discuss** de cada participante inscrito que tenga cuenta de usuario en Odoo, para que reciba el aviso sin entrar al torneo.

### 7.3. Botón "Cancelar torneo"
El enunciado solo pide los tres botones de transición de estado (Abrir inscripciones, Iniciar, Finalizar). Se ha añadido un botón de **cancelación con diálogo de confirmación** para torneos que no llegan a celebrarse, que además **bloquea su edición posterior** igual que los finalizados.

### 7.4. Botón "Iniciar partida"
El enunciado lista *en juego* como estado de una partida pero no exige botón para activarlo. Se ha añadido para hacer la transición *programada → en juego* de forma explícita, lo que permite mostrar correctamente el color verde en la lista cuando una partida está activa.

### 7.5. Enlace a la factura de cuota desde la inscripción
Al confirmar una inscripción se genera automáticamente una factura de venta (eso lo pide el enunciado). Como **extra**, se añadió el campo Many2one `factura_id` en `esports.registration` que guarda la referencia a la factura y la muestra en el formulario como **enlace clicable**. El campo solo aparece cuando la factura existe.

### 7.6. Fórmula de puntos acumulados (sistema 3-1-0)
El campo *puntos acumulados* de `esports.standing` se calcula con el **sistema estándar de fútbol**: 3 puntos por victoria, 1 por empate, 0 por derrota. El enunciado pide el campo pero no especifica fórmula; esta implementación es una decisión propia.

### 7.7. Campo `resultado` reutilizado como marcador legible
El modelo `esports.match` declaraba originalmente un campo `resultado` de tipo `Integer` que no se usaba en ninguna parte de la lógica (no tenía `compute`, ni se leía en `action_register_result`, ni influía en el cálculo del ganador). Se ha decidido **reutilizarlo en lugar de borrarlo**: ahora es un `Char` **calculado y almacenado** que muestra el marcador en formato legible `"X - Y"` (por ejemplo `"5 - 0"`) a partir de `puntuacion_local` y `puntuacion_visitante`.

- Mientras la partida está **programada** (sin jugar), el campo aparece vacío para no mostrar un engañoso `"0 - 0"`.
- En cuanto la partida pasa a *en juego*, *finalizada* o *walkover*, se rellena automáticamente con el marcador real.
- Al ser un `compute`, Odoo lo marca como solo lectura en el formulario sin necesidad de atributos adicionales.

Esto da una representación rápida del resultado en la lista y el calendario de partidas sin tener que mirar las dos puntuaciones por separado.

---

## 8. Ampliaciones opcionales del enunciado

> El enunciado del proyecto incluye un apartado de **ampliaciones opcionales** que no son obligatorias para superar la práctica pero que aportan valor al módulo. Se han implementado las dos siguientes.

### 8.1. Vista de calendario en el modelo de partidas

Se ha añadido una **vista de tipo `calendar`** a `esports.match` para visualizar de un vistazo el calendario del torneo (partidas programadas por día). La vista está definida en [`views/esports_match_views.xml`](volumesOdoo/addons/nexusarena/views/esports_match_views.xml) (`view_esports_match_calendar`) y se enlaza en la acción de Partidas, por lo que aparece como modo de vista adicional junto a la lista y al formulario.

**Detalles técnicos:**
- Eje temporal: `date_start="fecha_hora_programada"` (campo `Datetime` de la partida).
- Modo por defecto: `mode="month"`, con filtros laterales por **torneo**, **fase** y **estado**.
- Color por torneo (`color="torneo_id"`), para distinguir visualmente partidas de torneos distintos.
- Sin creación rápida (`quick_create="0"`), ya que las partidas requieren rellenar varios campos obligatorios.
- **Mejora añadida**: se ha añadido un campo `display_name` calculado en `esports.match` para que cada evento del calendario muestre `"<Fase>: <Local> vs <Visitante>"` en lugar del identificador interno `esports.match,<id>`.

Acceso: *Nexus Arena → Competición → Partidas → vista Calendario*.

### 8.2. Wizard para generar automáticamente el cuadro de eliminatorias (bracket)

Se ha implementado un **asistente (wizard)** que genera de forma automática todas las partidas del cuadro de eliminatorias a partir de los participantes inscritos y confirmados en el torneo, evitando que el organizador tenga que crear cada partida manualmente y emparejar a los jugadores a mano.

**Cómo se usa:**
1. El torneo debe estar en estado **En Curso** y con formato **Eliminación Directa** o **Doble Eliminación**.
2. Debe haber **exactamente 2, 4 u 8 inscripciones confirmadas** (potencias de 2 admitidas en la primera versión).
3. En el formulario del torneo aparece el botón **"Generar bracket"** en el header (solo para admin/organizador). Al pulsarlo se abre el wizard.
4. El wizard muestra los participantes confirmados, una vista previa de la estructura propuesta y varias opciones:
   - **Modo de emparejamiento**: *Por seed* (1 vs N, 2 vs N-1, ...) o *Aleatorio*.
   - **Fecha y hora primera ronda**: se programa para todas las partidas iniciales.
   - **Incluir partida por el 3er puesto**: checkbox opcional.
   - **Eliminar partidas existentes**: limpia las partidas previas del torneo (aborta si alguna está finalizada).
5. Al confirmar, el wizard crea las partidas y abre la lista filtrada por el torneo para revisarlas.

**Estructura generada según el nº de participantes:**

| N | Partidas creadas |
|---|---|
| 2 | 1 final |
| 4 | 2 semifinales + 1 final + (opcional) 1 tercer puesto |
| 8 | 4 cuartos + 2 semifinales + 1 final + (opcional) 1 tercer puesto |

Las rondas posteriores a la primera se generan como **placeholders** (sin participantes asignados todavía).

**Detalles técnicos:**
- Implementado como `TransientModel` `esports.bracket.wizard` en [`wizards/generate_bracket_wizard.py`](volumesOdoo/addons/nexusarena/wizards/generate_bracket_wizard.py).
- El **seed estándar** sigue la regla 1 vs N, 4 vs 5, 3 vs 6, 2 vs 7, de forma que los favoritos solo se cruzan en la final.
- Vista del wizard en [`views/generate_bracket_wizard_views.xml`](volumesOdoo/addons/nexusarena/views/generate_bracket_wizard_views.xml); acceso CRUD en `security/ir.model.access.csv` para `group_tourney_admin` y `group_tourney_organizer`.
- El botón usa `context="{'active_model': 'esports.tournament', 'active_id': id}"` y un `default_get` que precarga el torneo y sugiere la fecha de inicio del torneo a las 12:00.

### 8.3. Mejora propia sobre el wizard: propagación automática de ganadores y perdedores

> Esta mejora **no estaba en el enunciado** y se ha añadido por iniciativa propia para completar el flujo del bracket.

Cuando el wizard genera el cuadro, cada partida queda **enlazada** internamente con la partida a la que pasa su ganador (y, en el caso de las semifinales, con la partida del 3er puesto a la que pasa su perdedor). Al pulsar **"Registrar resultado"** en una partida del bracket, el sistema:

1. Determina ganador y perdedor a partir de las puntuaciones.
2. **Rechaza el empate** si la partida pertenece al bracket (en eliminatoria no puede haber empate).
3. Escribe automáticamente al **ganador** en el slot correcto (local o visitante) de la siguiente partida.
4. Si la partida es semifinal y existe partida de 3er puesto, escribe al **perdedor** en su slot correspondiente.
5. Publica en el chatter del torneo un mensaje del tipo *"Ganador propagado: Lobos pasa a la siguiente ronda (Final)"*.

De esta forma, conforme se van registrando resultados, las rondas posteriores se rellenan solas sin intervención manual.

**Implementación:**
- Cuatro campos nuevos en `esports.match`: `siguiente_partida_id`, `siguiente_slot`, `partida_tercer_puesto_id`, `tercer_puesto_slot`.
- El wizard crea las partidas **en orden inverso** (final → semifinales → cuartos) para poder enlazar cada ronda con la siguiente en una sola pasada de `create`.
- La propagación se realiza en `action_register_result` de `esports.match`.

---

## 9. Datos demo

El módulo incluye un archivo `demo/nexusarena_demo.xml` con datos preparados:
- **20 participantes** (mezcla de equipos competitivos y jugadores individuales).
- **5 videojuegos** (LoL, Valorant, EA FC 25, Street Fighter 6, Fortnite).
- **4 torneos** en distintos estados.
- **15 inscripciones**, **10 partidas** y **8 clasificaciones**.

Para cargarlos basta con marcar **"Cargar datos demo"** al crear la base de datos en Odoo.

---

## 10. Usuarios de prueba

Definidos en [`backup/contraseñas.txt`](../backup/contraseñas.txt):

| Usuario | Rol |
|---|---|
| `admin` | Administrador de Torneos |
| `organizador` | Organizador |
| `participante` | Participante |

**Contraseña para todos: `123`**

---

## 11. Backup

En la carpeta `backup/` hay un volcado de la base de datos (`nexusarena_2026-05-07_08-45-20.zip`) para poder restaurar el estado del proyecto sin tener que recrearlo desde cero. Se restaura desde el gestor de bases de datos de Odoo (`http://localhost:8069/web/database/manager`).

---

## 12. Documentación adicional

En la carpeta `documentos_adicionales/`:
- `NexusArena_Enunciado_Proyecto.pdf` — Enunciado original del proyecto.
- `Entidad relación1.png` / `Entidad relación2.png` — Diagramas E/R del modelo de datos.
- `extras_modulo.txt` — Fichero original con el detalle de las decisiones propias (sección 7 de este README).
- `README.md` — Este documento.
