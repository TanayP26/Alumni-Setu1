# Alumni Setu

**Alumni Setu** is an all-in-one platform for alumni networking, mentorship, job boards, and events.

## Quick Start

1. Clone the repository:
git clone https://github.com/TanayP26/Alumni-Setu1.git
cd Alumni-Setu1
2. Create a `.env` file from the example and fill in your credentials:
cp env.example .env
3. Set up a Python virtual environment and activate it:
python -m venv venv
source venv/bin/activate # Windows: venv\Scripts\activate
4. Install dependencies:
pip install -r requirements.txt
5. Set up the database and apply migrations:
flask db upgrade
6. Run the application locally:
flask run

7. Open http://localhost:5000 in your browser.

## Development

After modifying models, generate and apply migrations:
flask db migrate -m "Describe your change"
flask db upgrade

Commit the migration files:

git add migrations/
git commit -m "Add migration for your change"
git push
## Deployment

This project uses GitHub Actions to deploy on every push to the `main` branch—running migrations and starting the app.

The deployment workflow:

- Checks out code
- Sets environment variables
- Installs dependencies
- Runs `flask db upgrade` to apply migrations
- Starts the app with Gunicorn

### Important

Add following secrets in your GitHub repository settings under **Settings > Secrets and variables > Actions**:

- `DATABASE_URL` - your database connection string
- `SECRET_KEY` - Flask secret key
- `JWT_SECRET_KEY` - JWT authentication secret
- `MAIL_USERNAME` and `MAIL_PASSWORD` - for sending emails (optional)

## Notes

- Keep `migrations/` folder tracked in Git, as it stores all migration history.
- Do not edit migration files manually unless you are sure.
- Always back up your database before applying migrations, especially in production.

---

Happy coding and connecting with Alumni!

*Your Team*


