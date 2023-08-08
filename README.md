# GeneNetwork Auth

[![GeneNetwork Auth CI
badge](https://ci.genenetwork.org/badge/gn-auth.svg)](https://ci.genenetwork.org/jobs/gn-auth)
[![GeneNetwork Auth pylint CI
badge](https://ci.genenetwork.org/badge/gn-auth-pylint.svg)](https://ci.genenetwork.org/jobs/gn-auth-pylint)
[![GeneNetwork Auth mypy CI badge](https://ci.genenetwork.org/badge/gn-auth-mypy.svg)](https://ci.genenetwork.org/jobs/gn-auth-mypy)

This project is for the GeneNetwork Authentication/Authorisation server to be
used across the entire suite of the GeneNetwork services.

## Configuration

## Installation

## Migrations

**NOTE**: Do not create migration scripts manually. Use the processes indicated below.

### Authentication/Authorisation Migrations

The migration scripts for the authentication and authorisation system are in the *migrations/auth* folder in the root of the repository.

To create an new migration script for the, do:

```bash
$ yoyo new -m "<description of the migration>" ./migrations/auth/
```

The command will ask whether you want to save the migration configuration, e.g.

```bash
$ yoyo new --config=yoyo.auth.ini -m "testing a new migration"
Error: could not open editor!
Created file ./migrations/auth/20221103_02_HBzwk-testing-a-new-migration.py
Save migration configuration to yoyo.ini?
This is saved in plain text and contains your database password.

Answering 'y' means you do not have to specify the migration source or database connection for future runs [yn]:
```

If you specify `y` then a file named yoyo.ini will be created in your current working directory, and you can refer to it to avoid providing the `./migrations/auth` explicitly.

Now you can open and edit the scripts to provide the appropriate SQL statements to update or rollback your schema.

### Running the Migrations

To apply the migrations, you can do something like:

```bash
$ yoyo apply --database="sqlite:////tmp/test-auth.db" ./migrations/auth/

[20221103_01_js9ub-initialise-the-auth-entic-oris-ation-database]
Shall I apply this migration? [Ynvdaqjk?]: Y

[20221103_02_sGrIs-create-user-credentials-table]
Shall I apply this migration? [Ynvdaqjk?]: Y

[20221108_01_CoxYh-create-the-groups-table]
Shall I apply this migration? [Ynvdaqjk?]: Y

[20221108_02_wxTr9-create-privileges-table]
Shall I apply this migration? [Ynvdaqjk?]: Y

...
```

If you have previously initialised the yoyo config file, you can put the database uri in the configuration file and just provide it to avoid the prompt to save the configuration.

As a convenience, and to enable the CI/CD to apply the migrations automatically, I have provided a flask cli command that can be run with:

```bash
$ export FLASK_APP=main.py
$ flask apply-migrations
```

This expects that the following two configuration variables are set in the application:

* `AUTH_MIGRATIONS`: path to the migration scripts
* `AUTH_DB`: path to the sqlite database file (will be created if absent)

To enable you to run the OAuth2 server without HTTPS, you need to setup the
following environment variable(s):

* `export AUTHLIB_INSECURE_TRANSPORT=true`: Allows you to run the Authlib server
  without HTTPS on your development machine.

## Running

### Development

To run the application during development:

```sh
export FLASK_DEBUG=1
export FLASK_APP="main.py"
export AUTHLIB_INSECURE_TRANSPORT=true
export GN_AUTH_CONF="${HOME}/genenetwork/configs/gn_auth_conf.py"
flask run --port=8081
```

replace the `GN_AUTH_CONF` file with the correct path for your environment.

### Production

You can run the application on production with GUnicorn with something like:

```sh
gunicorn --bind 0.0.0.0:8081 --workers 6 --keep-alive 6000 --max-requests 10 \
	--max-requests-jitter 5 --timeout 1200 wsgi:app
```

## Checks

Running checks ensures the code is good, and the application actually does what
it is expected to do.

The checks we do are
- Lint-checks
- Type-checks
- Unit tests

### Linting

```bash
pylint *py tests gn_auth scripts
```

### Type-Checking

```bash
mypy --show-error-codes .
```

### Running Tests

```bash
export AUTHLIB_INSECURE_TRANSPORT=true
pytest -k unit_test
```

## OAuth2

This application acts as an OAuth2 server, allowing the client applications to
authenticate and access the API endpoints with the appropriate authorisation
levels.
