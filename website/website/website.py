"""Bar La Nueva Flor — Sitio web de la cafetería-restaurante de barrio."""

import reflex as rx


# ──────────────────────────────────────────────
# Datos del menú
# ──────────────────────────────────────────────

DESAYUNOS = [
    ("☕ Café con leche", "Café recién hecho con leche entera o desnatada", "1,20 €"),
    ("🥐 Tostada con tomate", "Pan de pueblo tostado con tomate natural y aceite de oliva", "2,00 €"),
    ("🥚 Huevos revueltos", "Huevos revueltos con jamón serrano y tostada", "4,50 €"),
    ("🥞 Bocadillo de tortilla", "Tortilla española casera en barra crujiente", "3,00 €"),
    ("🍊 Zumo natural", "Zumo de naranja recién exprimido", "1,80 €"),
    ("🧇 Desayuno completo", "Café + tostada + zumo natural", "4,00 €"),
]

COMIDA = [
    ("🍲 Menú del día", "Primer plato, segundo plato, postre y bebida incluida", "10,50 €"),
    ("🥗 Ensalada mixta", "Lechuga, tomate, cebolla, aceitunas y atún", "4,50 €"),
    ("🍝 Pasta del día", "Pasta con salsa casera según disponibilidad", "6,50 €"),
    ("🥩 Carne a la plancha", "Filete de ternera o pechuga de pollo con guarnición", "8,00 €"),
    ("🐟 Pescado del día", "Pescado fresco a la plancha con patatas", "8,50 €"),
    ("🍮 Postre casero", "Flan casero, arroz con leche o fruta del tiempo", "2,00 €"),
]


# ──────────────────────────────────────────────
# Componentes reutilizables
# ──────────────────────────────────────────────

def navbar() -> rx.Component:
    return rx.box(
        rx.hstack(
            rx.heading(
                "🌸 Bar La Nueva Flor",
                size="6",
                color="white",
                font_weight="bold",
            ),
            rx.spacer(),
            rx.hstack(
                rx.link("Inicio", href="#inicio", color="white", font_weight="500"),
                rx.link("Menú", href="#menu", color="white", font_weight="500"),
                rx.link("Horario", href="#horario", color="white", font_weight="500"),
                rx.link("Contacto", href="#contacto", color="white", font_weight="500"),
                spacing="6",
                display=["none", "none", "flex"],
            ),
            width="100%",
            align="center",
        ),
        background_color="#c0392b",
        padding="1rem 2rem",
        position="sticky",
        top="0",
        z_index="100",
        box_shadow="0 2px 8px rgba(0,0,0,0.2)",
        id="inicio",
    )


def hero() -> rx.Component:
    return rx.box(
        rx.vstack(
            rx.heading(
                "Bar La Nueva Flor",
                size="9",
                color="white",
                text_align="center",
                font_weight="bold",
            ),
            rx.text(
                "Sabor casero en el corazón del barrio",
                size="6",
                color="#f8d7c4",
                text_align="center",
                font_style="italic",
            ),
            rx.hstack(
                rx.badge(
                    "🕖 07:00 – 16:00",
                    color_scheme="orange",
                    size="3",
                    padding="0.5rem 1rem",
                    font_size="1rem",
                ),
                rx.badge(
                    "🍳 Desayunos y Comidas",
                    color_scheme="orange",
                    size="3",
                    padding="0.5rem 1rem",
                    font_size="1rem",
                ),
                spacing="4",
                flex_wrap="wrap",
                justify="center",
            ),
            rx.button(
                "Ver nuestro menú →",
                on_click=rx.call_script(
                    "document.getElementById('menu').scrollIntoView({behavior:'smooth'})"
                ),
                background_color="#e67e22",
                color="white",
                size="3",
                padding="0.75rem 2rem",
                border_radius="2rem",
                font_weight="bold",
                _hover={"background_color": "#d35400", "transform": "scale(1.03)"},
                cursor="pointer",
            ),
            spacing="6",
            align="center",
            justify="center",
        ),
        background="linear-gradient(135deg, #922b21 0%, #c0392b 50%, #e74c3c 100%)",
        min_height="60vh",
        display="flex",
        align_items="center",
        justify_content="center",
        padding="4rem 2rem",
    )


def menu_card(emoji_name: str, description: str, price: str) -> rx.Component:
    return rx.box(
        rx.vstack(
            rx.hstack(
                rx.text(emoji_name, size="4", font_weight="bold", color="#2c3e50"),
                rx.spacer(),
                rx.badge(price, color_scheme="green", size="2"),
                width="100%",
                align="center",
            ),
            rx.text(description, size="2", color="#7f8c8d"),
            spacing="2",
            align="start",
            width="100%",
        ),
        background_color="white",
        border_radius="0.75rem",
        padding="1.25rem",
        box_shadow="0 2px 8px rgba(0,0,0,0.08)",
        border="1px solid #f0e6e6",
        _hover={
            "box_shadow": "0 4px 16px rgba(192,57,43,0.15)",
            "border_color": "#c0392b",
            "transform": "translateY(-2px)",
        },
        transition="all 0.2s ease",
        width="100%",
    )


def menu_section() -> rx.Component:
    return rx.box(
        rx.vstack(
            rx.heading(
                "🍽️ Nuestro Menú",
                size="8",
                color="#c0392b",
                text_align="center",
                font_weight="bold",
            ),
            rx.text(
                "Cocina casera elaborada con productos frescos de temporada",
                size="4",
                color="#7f8c8d",
                text_align="center",
            ),
            rx.divider(color="#c0392b", margin_y="1rem"),
            # Desayunos
            rx.box(
                rx.vstack(
                    rx.hstack(
                        rx.heading("☕ Desayunos", size="6", color="#2c3e50"),
                        rx.text("Servido de 07:00 a 12:00", size="2", color="#95a5a6"),
                        align="baseline",
                        spacing="4",
                        flex_wrap="wrap",
                    ),
                    rx.grid(
                        *[menu_card(n, d, p) for n, d, p in DESAYUNOS],
                        columns=rx.breakpoints(initial="1", sm="2", lg="3"),
                        spacing="4",
                        width="100%",
                    ),
                    spacing="4",
                    width="100%",
                ),
                width="100%",
            ),
            rx.divider(margin_y="1.5rem"),
            # Comida
            rx.box(
                rx.vstack(
                    rx.hstack(
                        rx.heading("🍲 Comida del Día", size="6", color="#2c3e50"),
                        rx.text("Servido de 12:00 a 16:00", size="2", color="#95a5a6"),
                        align="baseline",
                        spacing="4",
                        flex_wrap="wrap",
                    ),
                    rx.grid(
                        *[menu_card(n, d, p) for n, d, p in COMIDA],
                        columns=rx.breakpoints(initial="1", sm="2", lg="3"),
                        spacing="4",
                        width="100%",
                    ),
                    spacing="4",
                    width="100%",
                ),
                width="100%",
            ),
            spacing="6",
            max_width="1100px",
            width="100%",
            margin="0 auto",
        ),
        background_color="#fdf6f0",
        padding="4rem 2rem",
        id="menu",
    )


def horario_section() -> rx.Component:
    return rx.box(
        rx.vstack(
            rx.heading(
                "🕐 Horario y Ubicación",
                size="8",
                color="white",
                text_align="center",
                font_weight="bold",
            ),
            rx.hstack(
                # Horario
                rx.box(
                    rx.vstack(
                        rx.heading("Horario de apertura", size="5", color="white"),
                        rx.divider(color="rgba(255,255,255,0.3)"),
                        rx.hstack(
                            rx.text("Lunes – Viernes", color="#f8d7c4", size="3"),
                            rx.spacer(),
                            rx.text("07:00 – 16:00", color="white", size="3", font_weight="bold"),
                            width="100%",
                        ),
                        rx.hstack(
                            rx.text("Sábado", color="#f8d7c4", size="3"),
                            rx.spacer(),
                            rx.text("08:00 – 14:00", color="white", size="3", font_weight="bold"),
                            width="100%",
                        ),
                        rx.hstack(
                            rx.text("Domingo", color="#f8d7c4", size="3"),
                            rx.spacer(),
                            rx.text("Cerrado", color="#e74c3c", size="3", font_weight="bold"),
                            width="100%",
                        ),
                        rx.box(
                            rx.text(
                                "⚡ Cocina caliente desde las 12:00",
                                color="#ffeaa7",
                                size="2",
                                font_style="italic",
                            ),
                            background_color="rgba(255,255,255,0.1)",
                            padding="0.75rem",
                            border_radius="0.5rem",
                            width="100%",
                        ),
                        spacing="4",
                        width="100%",
                    ),
                    background_color="rgba(255,255,255,0.1)",
                    border="1px solid rgba(255,255,255,0.2)",
                    border_radius="1rem",
                    padding="2rem",
                    min_width="280px",
                    flex="1",
                ),
                # Info adicional
                rx.box(
                    rx.vstack(
                        rx.heading("Sobre nosotros", size="5", color="white"),
                        rx.divider(color="rgba(255,255,255,0.3)"),
                        rx.text(
                            "Bar La Nueva Flor es un rincón de barrio con más de 20 años "
                            "sirviendo desayunos y comidas caseras. Nos enorgullece usar "
                            "ingredientes frescos y elaborar platos con el sabor de siempre.",
                            color="#f8d7c4",
                            size="3",
                            line_height="1.7",
                        ),
                        rx.vstack(
                            rx.hstack(
                                rx.text("📍", size="3"),
                                rx.text("Calle del Barrio, 42 — Madrid", color="white", size="3"),
                            ),
                            rx.hstack(
                                rx.text("📞", size="3"),
                                rx.text("91 000 00 00", color="white", size="3"),
                            ),
                            rx.hstack(
                                rx.text("🅿️", size="3"),
                                rx.text("Aparcamiento en la plaza cercana", color="#f8d7c4", size="3"),
                            ),
                            spacing="2",
                            align="start",
                        ),
                        spacing="4",
                        width="100%",
                    ),
                    background_color="rgba(255,255,255,0.1)",
                    border="1px solid rgba(255,255,255,0.2)",
                    border_radius="1rem",
                    padding="2rem",
                    min_width="280px",
                    flex="1",
                ),
                spacing="6",
                flex_wrap="wrap",
                justify="center",
                width="100%",
                max_width="900px",
            ),
            spacing="8",
            align="center",
            width="100%",
        ),
        background="linear-gradient(135deg, #922b21 0%, #c0392b 100%)",
        padding="5rem 2rem",
        id="horario",
    )


def footer() -> rx.Component:
    return rx.box(
        rx.vstack(
            rx.heading("🌸 Bar La Nueva Flor", size="5", color="white"),
            rx.text(
                "Cafetería · Restaurante de barrio · Desayunos y Comidas",
                color="#f8d7c4",
                size="2",
                text_align="center",
            ),
            rx.hstack(
                rx.text("📍 Calle del Barrio, 42", color="#f8d7c4", size="2"),
                rx.text("·", color="#c0392b", size="2"),
                rx.text("📞 91 000 00 00", color="#f8d7c4", size="2"),
                rx.text("·", color="#c0392b", size="2"),
                rx.text("🕖 07:00 – 16:00", color="#f8d7c4", size="2"),
                flex_wrap="wrap",
                justify="center",
                spacing="3",
            ),
            rx.divider(color="rgba(255,255,255,0.15)", margin_y="0.5rem"),
            rx.text(
                "© 2025 Bar La Nueva Flor — Todos los derechos reservados",
                color="rgba(255,255,255,0.4)",
                size="1",
                text_align="center",
            ),
            spacing="3",
            align="center",
        ),
        background_color="#1a0a08",
        padding="2.5rem 2rem",
        id="contacto",
    )


# ──────────────────────────────────────────────
# Página principal
# ──────────────────────────────────────────────

def index() -> rx.Component:
    return rx.box(
        navbar(),
        hero(),
        menu_section(),
        horario_section(),
        footer(),
        font_family="'Segoe UI', system-ui, -apple-system, sans-serif",
        background_color="#fdf6f0",
    )


app = rx.App(
    style={
        "font_family": "'Segoe UI', system-ui, -apple-system, sans-serif",
    }
)
app.add_page(index, route="/")
