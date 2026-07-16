from app import create_app
print("Création de l'application...")

app = create_app()
print("Application créée :", app)
if __name__ == "__main__":
    app.run()
