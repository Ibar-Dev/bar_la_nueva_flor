# Bar La Nueva Flor — Sitio Web

Sitio web de la cafetería-restaurante de barrio **Bar La Nueva Flor**, desarrollado con [Reflex](https://reflex.dev).

## Descripción

Cafetería-restaurante de barrio que sirve desayunos y comidas del día.  
**Horario:** 07:00 – 16:00 (lunes a viernes) | 08:00 – 14:00 (sábados)

## Secciones

- **Hero** — Nombre del bar, eslogan y horario de apertura
- **Menú** — Desayunos (07:00–12:00) y Comida del día (12:00–16:00)
- **Horario y Ubicación** — Horario detallado e información del local
- **Pie de página** — Datos de contacto

## Tecnología

- [Reflex](https://reflex.dev) — Framework Python para aplicaciones web reactivas
- Radix UI / Tailwind CSS (via Reflex)

## Desarrollo local

```bash
cd website
pip install -r requirements.txt
reflex run
```

Abre [http://localhost:3000](http://localhost:3000) en el navegador.

## Exportar a producción

```bash
reflex export
```

Genera `frontend.zip` y `backend.zip` listos para desplegar.
