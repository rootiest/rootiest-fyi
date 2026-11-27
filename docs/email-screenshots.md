# Rootiest Mail guide: screenshot list

Every picture in the mail guide, and how to take it again after an app changes its look. The pages already point at these files.
Until a file exists, the page shows a placeholder in its place.

## How to take and store them

- **Where they go:** `site/email/shots/<id>.png`. Pages link them as `../shots/<id>.png` (the index as `shots/<id>.png`), so the
  file name must match the id exactly.
- **The file in the repo is the source.** Keep only the finished, cropped and cleaned PNG. Don't commit the uncropped originals:
  they show the very details the crop removes. To update a picture, take it again from the recipe below and replace the file.
- **Account:** use a test account, or your own with the details below hidden. A test RootiestID in the `mail` group with a lowercase
  username (for example `sam`) makes the hiding step much shorter.
- **Hide:** addresses other than a placeholder like `sam@rootiest.org`, real names, folder names you'd rather not show, message
  subjects and senders, calendar and contact names, and every password or secret. Paint over with a solid block. Blurring a secret
  is not enough.
- **Size:** crop tightly to the part the caption talks about. Desktop shots at 100% zoom, roughly 1000 to 1400 px wide after the crop.
  Phone shots at the phone's own resolution, cropped to the relevant part of the screen. PNG, run through `oxipng` or similar.
- **Theme:** take every shot twice, in light mode and in dark mode, with everything else the same (state, crop, hidden
  details). The light one is `<id>.png`, the dark one `<id>-dark.png`. The page shows the one that matches the reader's system
  theme; until the dark file exists everyone sees the light one. `scripts/build.py` lists the shots still missing their dark
  version (`no dark screenshot:`). For apps without a dark mode, the light file alone is fine.
- **Alt text and captions** are already in the pages. If a new picture shows something different, update the page's `alt` and
  `figcaption` too.

## The shots

| id | Page | What to capture | Device | Crop | Hide |
|---|---|---|---|---|---|
| `webmail-login` | webmail | webmail.rootiest.dev sign-in page, signed out, light mode (the page's own theme menu, top right): the Rootiest Mail logo and the **Sign in with SSO** button | workstation (browser) | the sign-in box with the Website, Help and version links below it | nothing personal on this screen |
| `webmail-inbox` | webmail | the main mail screen in light mode: the left bar, folder list, message list and an open message (a "Welcome to Rootiest Mail" message to yourself works well) | workstation (browser) | the whole app window, browser chrome cut off | message previews, subjects and senders you'd rather not show; paint them over with the row's own background |
| `webmail-filter` | webmail | Settings → Filters → **New rule**: From contains `news@example.com`, **Move to folder** ticked with `Newsletters` | workstation (browser) | the New rule dialog | folder names other than the example (only the picked folder shows once the list is closed) |
| `webmail-out-of-office` | webmail | Settings → Out of office, scrolled so Reply automatically, Reply to, From, Until, Subject and Message all show; leave it off (the page saves as you go) | workstation (browser) | from Reply automatically down to the Message box | nothing personal with the default text |
| `app-password-list` | app-passwords | webmail.rootiest.dev Settings → Password & sign-in, scrolled to **App passwords**, with the **New app password** button and the list | workstation (browser) | the App passwords section | descriptions of your real app passwords |
| `app-password-create` | app-passwords | the same section after **New app password**: App name "Thunderbird on my laptop", More options left closed, the **Create** button | workstation (browser) | the form | nothing personal with the example name |
| `app-password-created` | app-passwords | the box right after Create, showing the new app password with its copy button and **Done** | workstation (browser) | the box | **the app password: paint it over completely**, then delete that app password straight away |
| `thunderbird-setup` | thunderbird | Thunderbird's "Set up your existing email address" screen with Your full name, Email address and Password filled | workstation (Thunderbird) | the form | real name (use "Sam Example"), the address (use the test account), password dots are fine |
| `thunderbird-found` | thunderbird | the next screen: configuration found, IMAP selected, mx.rootiest.dev for incoming and outgoing, **Done** button | workstation (Thunderbird) | the found-settings panel and the Done button | the address |
| `thunderbird-calendar` | thunderbird | New Calendar → On the Network, with Username and Location `https://mx.rootiest.dev/dav/cal/` filled | workstation (Thunderbird) | the dialog | the address |
| `thunderbird-android-address` | thunderbird-android | Thunderbird for Android's first account screen with the address typed in | phone (Android) | the form area, status bar cut off | the address |
| `thunderbird-android-found` | thunderbird-android | the screen showing the incoming and outgoing servers it found (mx.rootiest.dev) | phone (Android) | the server details | the address |
| `thunderbird-android-password` | thunderbird-android | the password screen with the box filled (dots) | phone (Android) | the form area | the address |
| `masked-address-list` | addresses | webmail.rootiest.dev Settings → Password & sign-in, scrolled to **Masked addresses**, with one address listed (description e.g. "Newsletter sign-up", a website filled) and the create form below it | workstation (browser) | the Masked addresses section: the list and the create form | your real masked addresses (make a fresh one for the shot, delete it after) |
| `davx5-login` | calendars-contacts | DAVx⁵ add account → Login with URL and user name, with Base URL `https://mx.rootiest.dev/` and the user name filled | phone (Android) | the form | the address |
| `ios-mail-other` | apple | iPhone Settings → Apps → Mail → Mail Accounts → Add Account → Other, showing **Add Mail Account** | phone (iPhone) | the list | other accounts on the device |
| `ios-mail-servers` | apple | the New Account screen after Next: IMAP selected, Incoming and Outgoing Mail Server both filled with mx.rootiest.dev | phone (iPhone) | both server sections | name, address, description |
| `macos-mail-servers` | apple | Mac Mail → Add Account → Other Mail Account, the second step with Account Type IMAP and both servers filled | Mac | the dialog | name and address |
| `outlook-new-imap` | outlook | new Outlook → Add account → IMAP advanced settings form with the servers, ports and SSL/TLS filled | Windows PC | the form | the address |
| `outlook-classic-add` | outlook | classic Outlook File → Add Account with the address typed and Advanced options visible | Windows PC | the dialog | the address |

## Devices you may not have

The iPhone, Mac and Outlook shots need devices that may not be on hand. Those pictures can wait: the steps are written to work
without them, and the placeholders stay until someone with the device takes them using the recipe above.

## After an app update

When a screen changes (a new Thunderbird, a webmail upgrade, a new iOS), retake its shots and check the steps on the page still
match the labels. The webmail labels, `app-password-*` and `masked-address-list` included, come from Bulwark's English strings, so
check them after every webmail upgrade.
