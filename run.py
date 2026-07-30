import os
from app import create_app

print("Création de l'application...")

app = create_app()

print("Application créée :", app)


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))

    app.run(
        host="0.0.0.0",
        port=port
    )
