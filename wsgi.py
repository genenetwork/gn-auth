"""WSGI application entry-point."""
from gn_auth import create_app

app = create_app()

if __name__ == "__main__":
    app.run()
