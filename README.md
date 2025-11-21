# DeerUtsav Invitations

Simple Python script to send personalized invitation emails for DeerUtsav 10.0.

Getting started

- Configure environment variables (used with `python-decouple`). Create a `.env` file in the project root with:

```
APP_EMAIL=your.email@example.com
APP_PASSWORD=your-email-password-or-app-password
```

- Prepare your data and images in the existing `csv/` and `images/` folders. The template is at `templates/index.html`.

- Run the script:

```bash
python script.py
```

Notes
- Large binary images in `images/` may make the repository large. If you plan to keep many high-resolution invitation images in the repo, consider using Git LFS.
- The script writes runtime files `sent.csv` and `failed.csv` to the project root; those files are ignored by `.gitignore`.
