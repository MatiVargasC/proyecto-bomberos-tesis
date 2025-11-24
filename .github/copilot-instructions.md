**Project Overview**
- **Stack:** Django 5 project with a single app `gestion` and SQLite (`db.sqlite3`).
- **Purpose:** Manage firefighter shifts/guardias and simple reporting/dashboard UI.

**Big-picture architecture**
- **Entry points:** `manage.py` for dev tasks; `bomberos_project/urls.py` includes Django auth at `/accounts/` and mounts the app `gestion` at the root (`path('', include('gestion.urls'))`).
- **App boundaries:** `gestion` contains models (`Bombero`, `Guardia`, `Emergencia`), views (index, historial, reportes), and `gestion/urls.py` that defines UI routes. Templates live in `templates/` (project-level) and use `APP_DIRS=True`.
- **Data flow:** requests -> `gestion.views` -> ORM models (`Bombero`, `Guardia`) -> templates. Authentication is handled by Django's built-in auth views mounted at `/accounts/` with a local `templates/registration/login.html` override.

**Key files to read first**
- `bomberos_project/settings.py` — templating, static files, DB config, login redirects.
- `bomberos_project/urls.py` — where `/accounts/` and the app are mounted.
- `gestion/models.py` — domain models: `Bombero` (OneToOne `User`), `Guardia` (hora_inicio/hora_fin), `Emergencia`.
- `gestion/views.py` — business logic: `index` handles check-in/check-out, uses `request.user.bombero` and Django `messages`.
- `gestion/urls.py` and `templates/gestion/*.html` — routing names and template expectations.

**Developer workflows & useful commands**
- Create and activate a virtualenv, install Django 5 if needed: `python -m venv .venv; .venv\Scripts\Activate.ps1; pip install -r requirements.txt` (there may be no `requirements.txt`).
- Run dev server: `python manage.py runserver`
- DB tasks: `python manage.py makemigrations` then `python manage.py migrate` (DB is SQLite `db.sqlite3` in project root).
- Create admin: `python manage.py createsuperuser` and visit `/admin/`.
- Tests: `python manage.py test` (no tests currently provided in `gestion/tests.py`).

**Project-specific patterns & gotchas**
- **`request.user.bombero` is assumed**: views expect a `Bombero` instance linked to `User` via a OneToOne `user` field. When creating users in tests or scripts, create a `Bombero` instance or the view will return an error message.
- **Form POST contract in `index` view:** form sends `name="accion"` with values `'check-in'` or `'check-out'`. Any code modifying forms must preserve those names.
- **Templates and naming mismatches:**
  - `templates/gestion/reportes_avanzados.html` exists, but `gestion.views.reportes_avanzados_view` calls `render(request, 'reportes_avanzados.html', ...)` (no `gestion/` prefix). Use the app-directory template path or adjust the view/template consistently.
  - `base.html` links `{% url 'reportes' %}` but `gestion/urls.py` names the route `reportes_avanzados`. When changing URL names, update `base.html` or vice-versa; tests and templates assume specific names.
- **Settings quirks to be aware of (do not change without testing):**
  - `settings.py` contains two `BASE_DIR` definitions (one using `pathlib.Path`, then later redefined with `os.path.dirname`). Be careful when constructing filesystem paths in new code — use the project pattern in the target file.
  - There's a likely typo `USE_I1N` (should be `USE_I18N`) — search/confirm before relying on i18n settings.
  - `DEBUG = True` and `SECRET_KEY` are present in settings; production hardening is outside current scope but keep in mind.
- **Static files:** `TEMPLATES['DIRS']` uses `BASE_DIR / 'templates'`. Static files are intended under `static/` and `STATICFILES_DIRS` is set — use `{% load static %}` in templates (already used in `base.html`).
- **Authorization UI:** admin menu in `base.html` is shown when `user.is_superuser or user.is_staff` — use those flags for gating admin functionality.

**How to modify safely**
- When changing view/template names or URL names, update both `gestion/urls.py` and `templates/base.html` (and any template `url` tags) to keep lookups consistent.
- Preserve the `login_required` decorators and messages usage in views unless implementing a new auth flow.
- When creating fixtures/tests, always create a `Bombero` for the user (e.g., `Bombero.objects.create(user=user, rut='...', nombre='...')`).

**Quick examples pulled from code**
- Check-in flow (from `gestion/views.py`): POST `accion=check-in` -> `Guardia.objects.create(bombero=bombero, fecha=hoy, hora_inicio=timezone.now().time())`.
- Template lookup pitfall: `render(request, 'reportes_avanzados.html')` vs file at `templates/gestion/reportes_avanzados.html` — prefer `gestion/reportes_avanzados.html` or move/adjust the view.

If anything here is unclear or you'd like me to adjust tone/level of detail (e.g., include suggested fixes for the URL/template mismatches and settings typos), tell me and I will iterate.
