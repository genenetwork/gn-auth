# GeneNetwork Auth

[![GeneNetwork Auth CI
badge](https://ci.genenetwork.org/badge/gn-auth.svg)](https://ci.genenetwork.org/jobs/gn-auth)
[![GeneNetwork Auth pylint CI
badge](https://ci.genenetwork.org/badge/gn-auth-pylint.svg)](https://ci.genenetwork.org/jobs/gn-auth-pylint)
[![GeneNetwork Auth mypy CI badge](https://ci.genenetwork.org/badge/gn-auth-mypy.svg)](https://ci.genenetwork.org/jobs/gn-auth-mypy)

This project is for the GeneNetwork Authentication/Authorisation server to be
used across the entire suite of the GeneNetwork services.

## Configuration

The recommended way to pass configuration values to the application is via a
configuration file passed in via the `GN_AUTH_CONF` environment variable. This
variable simply holds the path to the configuration file, e.g.
```sh
export GN_AUTH_CONF="${HOME}/genenetwork/configs/gn_auth_conf.py"
```

The settings in the file above will override
[the default settings](./gn_auth/settings.py).

**NOTE**: For development purposes, you can override any of the settings in the
default configuration or the `GN_AUTH_CONF` file by setting an environment
variable of the same name as the variable you wish to override.
/Please note that this is included to help with debugging - you should not use this live./

### Configuration Variables

| Variable | Used By/For | Description |
| ---- | ---- | ---- |
| `LOGLEVEL` | Logging system events | Useful for logging system events and debugging. The acceptable values are `DEBUG`, `INFO`, `WARNING`, `ERROR` and `CRITICAL`. The default value is `WARNING` which will log out all warnings, errors and critical conditions. |
| `SECRET_KEY` | Flask | Used by flask to securely sign session cookies. See https://flask.palletsprojects.com/en/2.3.x/config/#SECRET_KEY. This setting is mandatory. If not provided, the system will not start. It is not provided by default, on purpose, to force the end-user to provide the value and prevent subtle bugs that can be experienced (especially with sessions) if this value is not set up. It would also be a **HUGE** security hole to provide a default value for this setting. |
| `SQL_URI` | MariaDB connections | Used to connect to the MariaDB server |
| `AUTH_DB` | SQLite connections | Used to connect to the Authentication/Authorisation database |
| `AUTH_MIGRATIONS` | Migrations | Relative (to the repo root) path to the migration scripts for the auth(entic/oris)ation database |
| `OAUTH2_SCOPE` | Supported OAuth2 scope for the application. |

There are a few other variables we can set, if we want to customise, or troubleshoot token generation. These are:

| Variable | Used By/For | Description |
| ---- | ---- | ---- |
| `OAUTH2_ACCESS_TOKEN_GENERATOR` | Generating new access tokens. | A string value that points to the function that generates the access token. e.g. `OAUTH2_ACCESS_TOKEN_GENERATOR='the_project.tokens.generate_token'`. |
| `OAUTH2_REFRESH_TOKEN_GENERATOR` | Generating refresh tokens. | Similar to the `OAUTH2_ACCESS_TOKEN_GENERATOR` setting above, except this setting relates to the refresh token. |
| `OAUTH2_TOKEN_EXPIRES_IN` | Limiting token expiry time. | This can be set to limit the amount of time a token is valid for. It can be a dict object or import string. |

## Installation

The recommended way to install the application is using GNU Guix[^gnu-guix]. You
could, hypothetically, safely install and run the application using Python's
Distutils, but we have not tested that (hence you'd be on your own).

The first step is to install GNU Guix[^gnu-guix] on your system. If you are
already using some other Linux distribution, install Guix as a package manager
on your system.

Once you have Guix installed on your computer, you can now start **gn-auth** in
one of three ways:

* Using a development shell/environment (`guix shell ...`)
* As a system container (mostly for deployments (`guix system container ...`))
* Using a guix profile

### Guix Shell

This is the recommended way to start **gn-auth** if you intend to do any
development on **gn-auth**. To do this, you need to be inside the **gn-auth**
repository:

```sh
cd "${HOME}/genenetwork-projects/gn-auth"
guix shell --container --network \
  --share=<path-to-shareable-directory>=<path-of-share-in-shell> \
  --development --file=guix.scm
```

The `--network` option allows the container to share the host network, and you
can access the application with something like "http://localhost:<port>".

The `--development` option installs all the dependencies in the shell that you
need for development - including those which won't be in production but are
needed for dev-work.

The `--share` and `--expose` options are used to expose specific directories on
the host system to your container. The `--expose` option exposes the specified
directory in **read-only** mode. You cannot write to such a share. The `--share`
option allows the shared directory to be writable from the shell.

The `--share` and `--expose` options can be repeated expose as many directories
to the shell as are needed.

The `--container` option creates a container environment completely isolated
from the rest of your system. This is the recommended way to do your
development. Without the option, your host environment bleeds into your shell.

Since providing the `--container` option isolates your shell, it means you will
not have access to some command in the host within the shell environment. A lot
of the times, this is a non-issue, and you can get by without them. If, however,
you find yourself in one of the vanishingly-small instances where you require
to leak your host environment into your development environment, then you know
to simply omit the option.

### Guix System Container

Guix system containers are an entirely different beast from the development
containers we mentioned in the section above.

You can think of `guix shell --container ...` invocation as simply creating an
isolated shell environment, but otherwise using the same kernel as the rest of
your host system.

A guix system container, `guix system container ...` on the other hand, creates
a proper system container complete with it's own separate operating-system
kernel.

System containers are useful for deployment, not so much day-to-day development.

### Guix Profile

You can install **gn-auth** package into a profile with something like:
```sh
guix package --install-from-file=guix.scm --profile="${HOME}/opt/gn-auth"
```

You can then source that profile to run the application:

```sh
source ~/opt/gn-auth/etc/profile
flask run --port=8081
```

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


------

[^gnu-guix]: We consider the use of [GNU Guix](https://guix.gnu.org/) as a
package manager in this documentation, but there is nothing preventing you from
using it as your operating system of choice for the entire system should you so
choose.
