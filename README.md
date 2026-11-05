# 9th IT4D Conference invitations

This mailer sends the invitation for the 9th IT4D Conference, themed “AI in Learning and Beyond.” It personalizes the greeting from each recipient’s `Name` and `Email` columns, embeds `images/logo/logo_it4d.png`, and links to the conference registration page.

## Before sending

- Check the recipient list at `csv/extra.csv` (`Name,Email` columns). Change `RECIPIENTS_PATH` in `script.py` if a different list should receive the invitation.
- To send over Gmail SMTP, put `APP_EMAIL` and `APP_PASSWORD` in the ignored `.env` file. The app password is preferred when both passwords are configured. If you have no app password, `EMAIL_PASSWORD` can be used as a fallback.
- If neither password is configured, the mailer uses Gmail OAuth with `credentials.json` and saves its token in `token.json`.
- `.env.example` shows the supported configuration names. Keep real passwords in `.env`, not in the example file.
- Review `templates/index.html` and the registration link before sending.

Run from the project folder:

```bash
python script.py
```

Successful and failed deliveries are appended to `sent.csv` and `failed.csv`.
