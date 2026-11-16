# 📰 PR Clippings Filer

**Name, file and send press & social media clippings in seconds, not hours.**

A one-click Mac app for PR consultancies, communications teams and social media agencies that turns a pile of
screenshots into a consistently named, client-organised, ready-to-send clippings folder.

---

## The problem

Every PR consultancy and social media firm has the same recurring chore. Coverage lands (an article, an Instagram
post, a TikTok, a LinkedIn mention, a print page) and someone has to:

1. Screenshot or save it, which leaves files called `Screenshot 2026-11-12 at 10.42.17.png`.
2. Rename every file by hand into the agency's convention, e.g. `2026-11-12_Acme_Instagram_01.png`.
3. Put it in the right client folder.
4. Zip the folder and email it to the client, the account lead or whoever builds the monthly coverage report.

It's repetitive, it's error-prone (typos in client names, inconsistent dates, overwritten files) and it eats hours
each month. That time gets spent by people who should be doing PR, not file management. And the tools that automate
it are usually expensive media-monitoring suites that are overkill for small teams.

## What it does

| Step | PR Clippings Filer |
| --- | --- |
| **Rename** | Applies your naming convention to every clipping at once, using `{date}`, `{client}`, `{note}`, `{n}` |
| **Date** | Uses each file's own saved date, so a clipping captured last Tuesday is dated last Tuesday |
| **Never overwrite** | Numbers files automatically (`_01`, `_02`, …) and skips names that already exist |
| **File** | Saves into your chosen folder, optionally inside a subfolder per client |
| **Send** | One button zips the client folder and emails it through the Mail app |
| **Remember** | Keeps your naming pattern, folder and recipient between sessions |

Example: client `Acme`, note `Instagram`, pattern `{date}_{client}_{note}_{n}` gives

```
Screenshot 2026-11-12 at 10.42.17.png   ->  Acme/2026-11-12_Acme_Instagram_01.png
Screenshot 2026-11-12 at 10.44.03.png   ->  Acme/2026-11-12_Acme_Instagram_02.png
press-cutting.pdf                       ->  Acme/2026-11-12_Acme_Instagram_03.pdf
```

Accepts screenshots, images and PDFs.

## Built for non-technical teams

- **One double-click.** The Mac app includes its own Python, so there's nothing to install and no Terminal.
- **Private by design.** Everything runs on your own Mac at `localhost`. Clippings never go to a server or a third-party
  service. Email goes through your own Mail app account.
- **No accounts, no subscriptions, no dependencies.** Python standard library only.

## Getting started

### For users (the Mac app)

1. Unzip **PR Clippings Filer.zip** and drag **PR Clippings Filer** to Applications or the Desktop.
2. First launch only: macOS will say it can't verify the developer. Open **System Settings → Privacy & Security**,
   scroll down and click **Open Anyway**.
3. Double-click it. The app opens in your browser.
4. The first time you email a folder, allow the app to control **Mail**. You need an email account set up in Mail.
5. To stop it, click **Quit PR Clippings Filer** at the bottom of the page.

**Sharing the app:** send `PR Clippings Filer.zip` by **AirDrop**, Google Drive, Dropbox or WeTransfer.
Avoid email: many providers block apps inside zips. Unzip by double-clicking. Don't re-zip with third-party tools.

### For developers (run from source)

```bash
python3 clippings_filer.py   # opens http://localhost:8000
```

### Build the Mac app

```bash
./build.sh
```

This downloads a pinned, checksum-verified standalone Python
([python-build-standalone](https://github.com/astral-sh/python-build-standalone)) for both Apple Silicon and Intel
into `vendor/`. It then builds `PR Clippings Filer.app` and a shareable `PR Clippings Filer.zip` (about 33 MB) in `dist/`,
verifies the code signature of both the app and a test extraction of the zip, and copies both to your Desktop.
Re-run it after changing `clippings_filer.py`.

How the app stays robust on other Macs: the bundle is never modified at runtime. On first launch the bundled Python
for that Mac's chip and the app code are copied to `~/Library/Application Support/PR Clippings Filer`, and run from there.
Logs go to `~/Library/Logs/PRClippingsFiler.log`.

### Custom app icon

```bash
python3 make_icon.py path/to/picture.png   # needs Pillow: pip install pillow
./build.sh
```

`make_icon.py` removes the picture's plain background, places it on a rounded pink tile and writes `AppIcon.icns`,
which `build.sh` uses automatically. Icon files and source images are git-ignored, because stock artwork usually
needs a licence and shouldn't go in the repo.

## Project layout

```
clippings_filer.py   the app: local web UI + rename/file/zip/email logic
launch.sh            Mac app launcher: installs the runtime copy on first launch, starts the app, opens the browser
build.sh             builds the self-contained .app and the shareable .zip
make_icon.py         turns any picture into the app icon (AppIcon.icns)
```

## Requirements & limitations

- macOS for the app and the email button. The renamer itself runs anywhere Python 3.8+ does.
- Email sends from the Mac **Mail** app. Large folders can exceed your provider's attachment limit (often 20–25 MB).
- The app isn't notarised by Apple, so step 2 above is needed once per Mac.
- Uses port 8000 on your Mac.

## Roadmap ideas

- Optional upload to a shared drive (Google Drive / SharePoint) instead of email
- A monthly coverage-report export (CSV / PDF contact sheet)
- Outlook support
