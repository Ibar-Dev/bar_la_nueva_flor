			- Se crean y ejecutan pruebas unitarias para `app.py`:
				- Archivo: test_app.py
				- Pruebas: conexión a la base de datos, obtención de datos iniciales, guardar compra válida y manejo de error por producto inexistente.
				- Resultado: OK, todas las funciones principales pasan las pruebas.
		- Se crean y ejecutan pruebas unitarias para `database_setup.py`:
			- Archivo: test_database_setup.py
			- Pruebas: creación de tablas y datos iniciales.

			# Gestor de Stock para Bar 🍻

			![Python](https://img.shields.io/badge/Python-3.8%2B-blue?logo=python)
			![Eel](https://img.shields.io/badge/Eel-frontend%2Fbackend-green)
			![SQLite](https://img.shields.io/badge/SQLite-DB-lightgrey?logo=sqlite)
			![Estado](https://img.shields.io/badge/Estado-Completo%20y%20Funcional-brightgreen)

			Aplicación de escritorio para la gestión de stock en un bar, desarrollada en Python usando Eel (frontend web con backend Python) y SQLite como base de datos local. Permite registrar compras, proveedores y productos, y facilita el control de inventario.

			---

			## Tabla de Contenidos
			- [Características](#características)
			- [Instalación](#instalación)
			- [Uso](#uso)
			- [Pruebas](#pruebas)
			- [Empaquetado y Distribución](#empaquetado-y-distribución)
			- [Estructura del Proyecto](#estructura-del-proyecto)
			- [Roadmap](#roadmap)
			- [Notas Técnicas](#notas-técnicas)
			- [Bitácora de Cambios](#bitácora-de-cambios)
			- [Licencia](#licencia)
			- [Contacto](#contacto)

			---

			## Características
			- Interfaz web moderna y responsiva (HTML5 + TailwindCSS)
			- Backend en Python 3.8+ con Eel
			- Base de datos local SQLite (no requiere instalación adicional)
			- Registro de compras, productos y proveedores
			- Comparador de precios (estático en MVP1)
			- Pruebas unitarias para backend y base de datos
			- Empaquetado en ejecutable standalone para Windows

			## Instalación
			1. Clona el repositorio:
				 ```bash
				 git clone https://github.com/Ibar-Dev/bar_la_nueva_flor.git
				 cd bar_la_nueva_flor
				 ```
			2. Crea un entorno virtual (opcional pero recomendado):
				 ```bash
				 python -m venv .venv
				 source .venv/bin/activate  # En Windows: .venv\Scripts\activate
				 ```
			3. Instala las dependencias:
				 ```bash
				 pip install -r requirements.txt
				 ```
			4. (Opcional) Ejecuta el script de base de datos:
				 ```bash
				 python database_setup.py
				 ```

			## Uso
			- **Modo desarrollo:**
				```bash
				python app.py
				```
				Esto abrirá la interfaz web y permitirá registrar compras.

			- **Modo ejecutable:**
				Si ya tienes el ejecutable (`dist/app.exe`), simplemente ejecútalo:
				```bash
				dist/app.exe
				```

			## Pruebas
			Ejecuta las pruebas unitarias con:
			```bash
			python -m unittest test_database_setup.py
			python -m unittest test_app.py
			```
			O bien, usa `pytest` si lo prefieres.

			## Empaquetado y Distribución
			Para generar el ejecutable standalone (Windows):
			```bash
			pip install pyinstaller
			pyinstaller --onefile --add-data "web;web" --hidden-import=eel app.py
			```
			El ejecutable estará en la carpeta `dist/`.

			**Notas:**
			- Probar el ejecutable en un entorno limpio antes de distribuir.
			- Si necesitas un instalador gráfico, considera Inno Setup o NSIS.

			## Estructura del Proyecto
			```
			/bar_la_nueva_flor/
			├── web/
			│   └── index.html         # Interfaz de usuario (frontend)
			├── .gitignore             # Ignora archivos innecesarios y entornos
			├── app.py                 # Motor principal (backend y arranque Eel)
			├── database_setup.py      # Script para crear la base de datos y poblarla
			├── requirements.txt       # Dependencias Python
			└── stock.db               # Base de datos SQLite (autogenerada)
			```

			## Roadmap
			- Alertas y comparador de precios dinámicos (actualmente estáticos en el MVP 1)
			- Gestión de usuarios y permisos
			- Exportación de datos a CSV/Excel
			- Instalador multiplataforma

			## Notas Técnicas
			- **Eel** permite crear una interfaz web moderna y multiplataforma, ejecutada como app de escritorio.
			- **SQLite** es suficiente para persistencia local y no requiere instalación adicional.
			- La comunicación entre JS y Python se realiza mediante funciones expuestas con `@eel.expose`.
			- El archivo `database_setup.py` es idempotente: puede ejecutarse varias veces sin duplicar datos.
			- El frontend usa TailwindCSS vía CDN para evitar dependencias adicionales.
			- El archivo `.gitignore` excluye la base de datos, entornos virtuales y archivos temporales.

			## Bitácora de Cambios

			### 2025-11-19: Comprobación Final Integral del Proyecto
			**Estado del Proyecto: ✅ COMPLETO Y FUNCIONAL**
			- Estructura validada y archivos clave presentes
			- Pruebas unitarias: 100% PASADAS
			- Ejecutable funcional y flujo end-to-end validado
			- Compatibilidad: Windows x86-64

			### 2025-11-17: MVP y Testing Inicial
			- MVP funcional: registro de compras y proveedores
			- Interfaz web conectada a backend Python via Eel
			- Base de datos SQLite con estructura relacional
			- Ejecutable generado con PyInstaller
			- Política de validación automática establecida

			## Licencia
			Este proyecto se distribuye bajo la licencia MIT. Consulta el archivo `LICENSE` para más detalles.

			## Contacto
			Desarrollado por [Ibar-Dev](https://github.com/Ibar-Dev)


## Dependencias

- `eel` (ver `requirements.txt`).
- `sqlite3` viene incluido con Python estándar (no agregar a requirements.txt).

## Ejecutable e Instalación

Para distribución a usuarios finales, se recomienda empaquetar la app con PyInstaller:

1. Instalar PyInstaller en el entorno virtual:
	```bash
	pip install pyinstaller
	```
2. Generar el ejecutable:
	```bash
	pyinstaller --onefile --add-data "web;web" app.py
	```
	- El flag `--add-data` asegura que la carpeta web se incluya en el ejecutable.
	- El ejecutable estará en `dist/app.exe` (Windows).

Notas:
- Probar el ejecutable en un entorno limpio antes de distribuir.
- Si se requiere un instalador gráfico, considerar herramientas como Inno Setup o NSIS.

---
Fin de bitácora.