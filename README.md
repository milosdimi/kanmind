# KanMind – Backend

REST API for **KanMind**, a kanban project management tool.
Users can register, create boards, invite members, manage tasks
(status, priority, assignee, reviewer, due date) and comment on tasks.

This repository contains **only the backend**. The frontend (Vanilla JS)
is provided separately by the Developer Akademie and talks to this API.

Built with **Django** and **Django REST Framework**, using token authentication.

---

## Table of contents

- [Tech stack](#tech-stack)
- [Requirements](#requirements)
- [Installation](#installation)
- [Run the server](#run-the-server)
- [Connect the frontend](#connect-the-frontend)
- [Guest login](#guest-login)
- [Authentication](#authentication)
- [API endpoints](#api-endpoints)
- [Permissions](#permissions)
- [Special notes](#special-notes)
- [Run the tests](#run-the-tests)
- [Project structure](#project-structure)

---

## Tech stack

| Package               | Purpose                              |
|-----------------------|--------------------------------------|
| Django                | Web framework, ORM, admin            |
| djangorestframework   | REST API, serializers, token auth    |
| django-cors-headers   | Allows requests from the frontend    |
| coverage              | Test coverage report                 |
| pycodestyle           | PEP 8 check                          |

Exact versions are listed in [`requirements.txt`](requirements.txt).

## Requirements

- Python **3.12 or newer** (developed with Python 3.14)
- Git

## Installation

```bash
# 1. Clone the repository
git clone https://github.com/milosdimi/kanmind.git
cd kanmind

# 2. Create a virtual environment
python -m venv env

# 3. Activate it
env\Scripts\activate          # Windows
source env/bin/activate       # macOS / Linux

# 4. Install the dependencies
pip install -r requirements.txt

# 5. Create the database (this also creates the guest user)
python manage.py migrate

# 6. Optional: create an admin account for /admin/
python manage.py createsuperuser
```

The SQLite database (`db.sqlite3`) is **not** part of the repository.
It is created locally by `python manage.py migrate`.

## Run the server

```bash
python manage.py runserver
```

- API: <http://127.0.0.1:8000/api/>
- Admin panel: <http://127.0.0.1:8000/admin/>

**Secret key:** for local development a fallback key is used. For any
real deployment set your own key in the environment variable
`DJANGO_SECRET_KEY` and switch `DEBUG` off in `core/settings.py`.

## Connect the frontend

1. Start this backend (see above). The frontend expects the API at
   `http://127.0.0.1:8000/api/`.
2. Open the frontend project in VS Code and start `index.html` with the
   **Live Server** extension.
3. CORS is enabled for `http://127.0.0.1:5500` and `http://localhost:5500`
   (the default Live Server addresses). If your Live Server uses another
   port, add it to `CORS_ALLOWED_ORIGINS` in `core/settings.py`.

## Guest login

The frontend has a "Guest log in" button. The matching user is created
automatically by a data migration when you run `python manage.py migrate`:

| Email              | Password    |
|--------------------|-------------|
| `kevin@kovacsi.de` | `asdasdasd` |

## Authentication

Registration and login return a token. Every other request must send it
in the `Authorization` header:

```
Authorization: Token <your-token>
```

Requests without a valid token are answered with `401 Unauthorized`.

## API endpoints

All endpoints start with `/api/`.

### Authentication

| Method | Endpoint         | Description                          |
|--------|------------------|--------------------------------------|
| POST   | `/registration/` | Create an account, returns a token   |
| POST   | `/login/`        | Log in with email and password       |

### Boards

| Method | Endpoint                | Description                                   |
|--------|-------------------------|-----------------------------------------------|
| GET    | `/boards/`              | Boards the user owns or is a member of        |
| POST   | `/boards/`              | Create a board (the user becomes the owner)   |
| GET    | `/boards/{board_id}/`   | Board with members and tasks                  |
| PATCH  | `/boards/{board_id}/`   | Change title and/or members                   |
| DELETE | `/boards/{board_id}/`   | Delete the board with all tasks and comments  |
| GET    | `/email-check/?email=`  | Find a registered user by email               |

### Tasks

| Method | Endpoint                   | Description                         |
|--------|----------------------------|-------------------------------------|
| GET    | `/tasks/assigned-to-me/`   | Tasks where the user is assignee    |
| GET    | `/tasks/reviewing/`        | Tasks where the user is reviewer    |
| POST   | `/tasks/`                  | Create a task on a board            |
| PATCH  | `/tasks/{task_id}/`        | Update a task                       |
| DELETE | `/tasks/{task_id}/`        | Delete a task                       |

Allowed values: status `to-do`, `in-progress`, `review`, `done`;
priority `low`, `medium`, `high`.

### Comments

| Method | Endpoint                                   | Description              |
|--------|--------------------------------------------|--------------------------|
| GET    | `/tasks/{task_id}/comments/`               | Comments of a task       |
| POST   | `/tasks/{task_id}/comments/`               | Add a comment            |
| DELETE | `/tasks/{task_id}/comments/{comment_id}/`  | Delete a comment         |

## Permissions

| Action                                   | Allowed for                         |
|------------------------------------------|-------------------------------------|
| Registration, login                      | everyone                            |
| All other endpoints                      | logged-in users only                |
| View / update a board                    | board owner or member               |
| Delete a board                           | board owner only                    |
| Create / update a task                   | board owner or member               |
| Delete a task                            | task creator or board owner         |
| Read / write comments                    | board owner or member               |
| Delete a comment                         | comment author only                 |

Status codes follow the documentation: `400` invalid data, `401` not
logged in, `403` no permission, `404` object not found.

## Special notes

- **Email instead of username:** users log in with their email. Internally
  the email is also used as Django `username` and is stored in lower case.
- **Full name:** `fullname` is split at the first space into `first_name`
  and `last_name` (e.g. "Anna Maria Muster" → "Anna" / "Maria Muster").
- **Board owner and members:** the creator of a board becomes its owner
  but is not added to `members` automatically. The owner always has full
  access anyway.
- **Different response formats:** `PATCH /boards/{id}/` answers with
  `owner_data` and `members_data`; `PATCH /tasks/{id}/` answers without
  `board` and `comments_count` (as required by the API documentation).
- **Tasks cannot change their board.** Sending the current board id is
  accepted, a different board id returns `400`.
- **Assignee and reviewer** must be the owner or a member of the board.
- **Creating a task** checks in this order: invalid board id `400`,
  unknown board `404`, not a member `403`, then the task data `400`.
- **Only PATCH** is offered for updates; `PUT` returns `405`.

## Run the tests

```bash
# run all tests
python manage.py test

# run the tests and measure the coverage
coverage run manage.py test
coverage report

# PEP 8 check (migrations are generated by Django and excluded)
python -m pycodestyle --exclude=env,migrations .
```

The test suite covers every endpoint including the error cases and
reaches **100 % coverage**. The coverage settings are in `.coveragerc`.

## Project structure

```
kanmind/
├── core/                    # project settings and central URL routing
├── auth_app/                # registration and login
│   ├── api/                 # serializers, views, urls
│   ├── migrations/          # data migration for the guest user
│   └── tests/
├── kanban_app/              # boards, tasks and comments
│   ├── api/                 # serializers, views, urls, permissions, utils
│   ├── migrations/
│   ├── models.py            # Board, Task, Comment
│   ├── admin.py
│   └── tests/
├── manage.py
├── requirements.txt
└── .coveragerc
```
