import os

from waitress import serve

from app import create_app


app = create_app()


if __name__ == "__main__":
    host = os.getenv(
        "HOST",
        "127.0.0.1"
    )

    port = int(
        os.getenv(
            "PORT",
            "5000"
        )
    )

    threads = int(
        os.getenv(
            "WAITRESS_THREADS",
            "8"
        )
    )

    serve(
        app,
        host=host,
        port=port,
        threads=threads
    )
