from app import app

try:
    from database.seed import seed
    seed()
except Exception as exc:
    app.logger.exception("SMARTEDU AUTO SEED ERROR: %s", exc)

application = app

if __name__ == "__main__":
    application.run()