# How this website is updated

The site has two parts, kept separate on purpose:

| | Code | Content |
|---|---|---|
| What | app.py, templates, CSS, design images (static/images) | Tiles, series, brands, furniture products and all uploaded photos (static/data, static/uploads) |
| Changed by | Developers, on their own PC | Staff, on the live site at /tiles/manage and /upload |
| Lives in | GitHub, copied to the server on every push | The live server only (plus backups) |

## Changing the code
1. Edit the code on your PC.
2. `git add .` then `git commit -m "what changed"` then `git push`.
3. GitHub (Actions tab) uploads the changed code to cPanel and restarts the site in about a minute.
   Content folders are never uploaded, so products and photos on the live site are never touched.

## Adding or editing products
Always do it on the live site (/tiles/manage, /upload). Never upload static/data or static/uploads from a PC.

## Working with real content on your PC
Download static/data and static/uploads from the server (cPanel File Manager, or the latest backup in ~/backups)
and put them in your local copy. They are ignored by Git, so they will not be pushed.

## Deploy settings (GitHub > Settings > Secrets and variables > Actions)
Secrets: SSH_HOST, SSH_USER, SSH_PORT, SSH_KEY (private key of a key authorised in cPanel > SSH Access).
Variables: DEPLOY_ON_PUSH = true (turns on automatic deploys), APP_DIR and SITE_URL only if they change.
Test anytime without changing anything: Actions > "Deploy website to cPanel" > Run workflow > mode "check".

## Backups
A cPanel cron job saves static/data and static/uploads to ~/backups on the 1st and 16th of each month and keeps the last 4.
To restore, extract the wanted backup over the app folder in cPanel File Manager.
