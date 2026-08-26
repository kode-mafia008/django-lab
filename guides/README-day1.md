---
title: "Day 1 — GitHub Setup and Your First Branch"
subtitle: "Personal Access Tokens, SSH keys, cloning django-lab, and pushing your own Django project"
author: "Django Practical Lab — daily guide series"
date: "Day 1 of the Django Framework Backend Development course"
---

# Before you start

## What this document is

This is the Day 1 lab sheet. It covers exactly two things:

1. **Getting your machine authenticated with GitHub** — twice, once with a Personal Access Token and once with an SSH key, so that you understand both and can fall back to either.
2. **The Day 1 exercise** — clone `django-lab`, branch off `main`, build a Django project inside a virtual environment, and push it to your own branch.

Everything here is meant to be run. Every command is written to be typed verbatim, and every expected output is the real output, not a paraphrase.

## Conventions

| Marker | Meaning |
| --- | --- |
| **TYPE** | Type this exactly. |
| **EXPECT** | What should appear. If you see something else, stop and fix it before moving on. |
| **CHECKPOINT** | A verifiable state. Nobody moves on until everyone reaches it. |
| **IF IT FAILS** | The most likely causes, in order of likelihood. |
| **WHY** | The reasoning. Skip on a first pass, read it before the exam. |

Shell prompts are shown as `$` for macOS and Linux and `>` for Windows PowerShell. **Do not type the prompt character.**

Throughout this document, replace:

| Placeholder | With |
| --- | --- |
| `<first_name>` | Your own first name, lowercase, no spaces — `dharmendra`, `priya`, `arjun` |
| `<github-username>` | Your GitHub username |
| `<your-email>` | The email address on your GitHub account |

## What you need before Step 1

| Requirement | How to check |
| --- | --- |
| A GitHub account | Log in at <https://github.com> |
| Git installed | `git --version` → `git version 2.39.0` or newer |
| Python 3.12 | `python3 --version` on macOS/Linux, `python --version` on Windows |
| Access to the `django-lab` repo | Open <https://github.com/kode-mafia008/django-lab> — you must be able to see it |

If `git --version` fails:

- **macOS** — `xcode-select --install`, or `brew install git`
- **Windows** — install Git for Windows from <https://git-scm.com/download/win>. Accept the defaults; they include Git Credential Manager, which you will need in Part 1.
- **Linux (Debian/Ubuntu)** — `sudo apt update && sudo apt install git`

\newpage

# Part 0 — One-time Git identity

Git stamps every commit with a name and an email. Set them once, before your first commit, or your commits will be attributed to the wrong person — or rejected outright.

**TYPE**

```bash
git config --global user.name  "Your Full Name"
git config --global user.email "<your-email>"
```

**TYPE** — verify:

```bash
git config --global --list
```

**EXPECT**

```
user.name=Your Full Name
user.email=you@example.com
init.defaultBranch=main
```

**WHY** — the email is what GitHub uses to link a commit to your profile. If it does not match a verified email on your GitHub account, your commits appear on the repo but not on your contribution graph, and they show up with a faceless grey avatar.

Also set the default branch name so new repos you create later start on `main` rather than `master`:

```bash
git config --global init.defaultBranch main
```

> **CHECKPOINT 0** — `git config --global user.email` prints an email that appears under **GitHub → Settings → Emails** as verified.

\newpage

# Part 1 — Authenticating with a Personal Access Token (PAT)

## 1.1 Why a PAT exists

On **13 August 2021** GitHub stopped accepting account passwords for Git operations over HTTPS. If you clone over HTTPS today and type your GitHub password when prompted, you get:

```
remote: Support for password authentication was removed on August 13, 2021.
fatal: Authentication failed for 'https://github.com/kode-mafia008/django-lab.git/'
```

A Personal Access Token is the replacement. It is a long random string that acts as a password **for Git only**, with the following advantages:

- It can be given a narrow set of permissions — read only, or one repository only.
- It expires on a date you choose.
- It can be revoked individually without changing your account password or disturbing your other machines.

## 1.2 Classic vs fine-grained

GitHub offers two kinds. Both work for this lab.

| | **Tokens (classic)** | **Fine-grained tokens** |
| --- | --- | --- |
| Scope | All repos you can access | Pick specific repositories |
| Permissions | Coarse (`repo` = everything) | Per-resource (Contents, Issues, Pull requests…) |
| Max lifetime | Can be set to no expiry | Maximum 1 year |
| Org repos | Works immediately | May need an org admin to approve |
| Use when | You want it working in 60 seconds | You want least privilege |

**Recommendation for this class:** create a **fine-grained** token scoped to `django-lab` only. It is the habit you want in a real job. If your fine-grained token is stuck "pending approval", fall back to classic.

## 1.3 Create a fine-grained token

1. Click your avatar (top right) → **Settings**.
2. Scroll to the bottom of the left sidebar → **Developer settings**.
3. **Personal access tokens** → **Fine-grained tokens**.
   Direct link: <https://github.com/settings/personal-access-tokens/new>
4. Fill in:

   | Field | Value |
   | --- | --- |
   | **Token name** | `django-lab-laptop` — name it after *what it is used by*, not what it does. When you rotate, you will know which machine to update. |
   | **Expiration** | 90 days. Not "No expiration". |
   | **Description** | `Day 1 lab — clone and push django-lab` |
   | **Resource owner** | `kode-mafia008` (or your own account if you forked) |
   | **Repository access** | **Only select repositories** → pick `django-lab` |

5. Expand **Repository permissions** and set:

   | Permission | Level | Why |
   | --- | --- | --- |
   | **Contents** | **Read and write** | Required to clone and to push commits |
   | **Metadata** | Read-only | Auto-selected, cannot be turned off |
   | **Pull requests** | Read and write | Only if you will open PRs from the CLI |

   Leave everything else at **No access**.

6. Click **Generate token**.

## 1.4 Copy the token — you get one chance

**EXPECT** — a green box containing a string beginning `github_pat_`:

```
github_pat_11ABCDEFG0abcdefghijklmn_OPqrstuvwxyz1234567890ABCDEFGHIJKLMNOP
```

Copy it now. The moment you navigate away, GitHub will never show it again — you would have to delete the token and make a new one.

> **Classic token variant:** at <https://github.com/settings/tokens/new>, tick the top-level **`repo`** scope (this grants full control of your repositories), set an expiry, and generate. Classic tokens begin `ghp_`.

## 1.5 Where to put the token — and where not to

**Do not** paste the token into the remote URL:

```bash
# WRONG — never do this
git clone https://github_pat_ABC123@github.com/kode-mafia008/django-lab.git
```

That writes the token in plaintext into `.git/config`, into your shell history, and into any screenshot you take of your terminal. Anybody who sees it has push access to the repo until you notice.

Instead, let Git store it in your operating system's credential store.

**TYPE** — macOS:

```bash
git config --global credential.helper osxkeychain
```

**TYPE** — Windows PowerShell (Git Credential Manager ships with Git for Windows):

```powershell
git config --global credential.helper manager
```

**TYPE** — Linux, with `libsecret` (preferred, encrypted at rest):

```bash
sudo apt install libsecret-1-0 libsecret-1-dev
sudo make -C /usr/share/doc/git/contrib/credential/libsecret
git config --global credential.helper \
  /usr/share/doc/git/contrib/credential/libsecret/git-credential-libsecret
```

**TYPE** — Linux fallback, memory cache for one day (nothing written to disk):

```bash
git config --global credential.helper "cache --timeout=86400"
```

**WHY** — with a helper configured, Git prompts you for the token exactly once. Every subsequent `push` and `pull` reads it back from the keychain silently.

## 1.6 Use the token

The token is entered at the **password** prompt the first time you talk to GitHub over HTTPS. You will do this for real in Part 4, but here is the shape of it:

```
Username for 'https://github.com': <github-username>
Password for 'https://<github-username>@github.com': github_pat_11ABC...
```

Note that terminals do not echo the password field — the cursor will not move as you paste. That is normal. Paste and press Enter.

## 1.7 Test the token without cloning anything

**TYPE** — macOS/Linux:

```bash
git ls-remote https://github.com/kode-mafia008/django-lab.git HEAD
```

**EXPECT** — a prompt for username and password on first run, then:

```
4c4374e...	HEAD
```

Any 40-character hash followed by `HEAD` means the token is accepted and stored.

> **CHECKPOINT 1** — running `git ls-remote` a *second* time prints the hash with **no prompt**. That proves the credential helper saved the token.

## 1.8 Rotating and revoking

| Situation | What to do |
| --- | --- |
| Token expired | Generate a new one, then clear the stale credential (below) and push again to be re-prompted |
| Token leaked (pasted in Slack, committed to a repo) | **Settings → Developer settings → the token → Delete.** Do it first, apologise second. Deleting is instant and cannot be undone. |
| Changed laptops | Make a *new* token for the new machine. Never copy a token between machines — the point of naming it after the device is that you can revoke one without breaking the other. |

Clearing a stale credential:

```bash
# macOS
git credential-osxkeychain erase <<< $'protocol=https\nhost=github.com\n'

# Windows
cmdkey /delete:LegacyGeneric:target=git:https://github.com

# Linux cache helper
git credential-cache exit
```

\newpage

# Part 2 — Authenticating with an SSH key

## 2.1 Why bother, if the PAT works

An SSH key is a **key pair**: a private key that never leaves your machine, and a public key you hand to GitHub. Authentication happens by proving you hold the private key — the secret itself is never transmitted, so there is nothing on the wire for anyone to capture.

| | PAT over HTTPS | SSH key |
| --- | --- | --- |
| Secret sent to GitHub | Yes, every request | Never |
| Expires | Yes, you set a date | No, until you delete it |
| Works behind restrictive corporate firewalls | Usually (port 443) | Sometimes blocked (port 22) — see 2.9 |
| Convenient for CI/servers | Yes | Yes (deploy keys) |
| Setup effort | Lower | Slightly higher, once |

Learn both. Use SSH on your own laptop, PAT in CI and on shared machines.

## 2.2 Check for an existing key first

**TYPE**

```bash
ls -al ~/.ssh
```

**EXPECT** — either `No such file or directory` (you have no keys — continue to 2.3), or a listing like:

```
-rw-------  1 you  staff   464 Aug 26 09:10 id_ed25519
-rw-r--r--  1 you  staff   103 Aug 26 09:10 id_ed25519.pub
```

A `.pub` file paired with a file of the same name **is** an existing key. You may reuse it — skip to 2.6. Files named `id_rsa` are an older algorithm; generate a new `ed25519` key rather than reusing them.

## 2.3 Generate the key

**TYPE** — the same command on macOS, Linux, and Windows PowerShell:

```bash
ssh-keygen -t ed25519 -C "<your-email>"
```

**EXPECT** — three prompts:

```
Generating public/private ed25519 key pair.
Enter file in which to save the key (/Users/you/.ssh/id_ed25519):
```

Press **Enter** to accept the default path. Do not invent a filename unless you already have a key you want to keep.

```
Enter passphrase (empty for no passphrase):
Enter same passphrase again:
```

**Type a passphrase.** Do not leave it blank.

**WHY the flags:**

- `-t ed25519` — the algorithm. Ed25519 keys are shorter, faster, and stronger than the 2048-bit RSA keys you will see in older tutorials. GitHub has supported them since 2015.
- `-C "<your-email>"` — a comment baked into the public key. It is purely a label, so that when you look at a list of five keys on GitHub you can tell which is which.

**WHY the passphrase** — the private key is a file. If your laptop is stolen or your backup drive is found, a passphrase-less key is immediately usable by whoever holds it. With a passphrase, the file is encrypted at rest. Section 2.5 makes sure you only type it once per login, so the convenience cost is near zero.

**EXPECT** — a randomart image and two new files:

```
Your identification has been saved in /Users/you/.ssh/id_ed25519
Your public key has been saved in /Users/you/.ssh/id_ed25519.pub
The key fingerprint is:
SHA256:aBcD1234... your.email@example.com
```

| File | Contains | Share it? |
| --- | --- | --- |
| `id_ed25519` | Private key | **Never.** Not in a repo, not in Slack, not in a screenshot. |
| `id_ed25519.pub` | Public key | Yes — this is the one you paste into GitHub. |

The `.pub` extension is the only thing distinguishing them in a directory listing. Read the filename twice before you copy anything.

## 2.4 Fix permissions (macOS and Linux)

SSH refuses to use a private key that other users on the machine can read.

**TYPE**

```bash
chmod 700 ~/.ssh
chmod 600 ~/.ssh/id_ed25519
chmod 644 ~/.ssh/id_ed25519.pub
```

## 2.5 Load the key into the agent

`ssh-agent` holds your decrypted private key in memory so you type the passphrase once per session instead of once per `git push`.

### macOS

**TYPE** — create or edit `~/.ssh/config`:

```bash
touch ~/.ssh/config
```

Add these lines to it:

```
Host github.com
  AddKeysToAgent yes
  UseKeychain yes
  IdentityFile ~/.ssh/id_ed25519
```

**TYPE** — start the agent and add the key to the macOS keychain:

```bash
eval "$(ssh-agent -s)"
ssh-add --apple-use-keychain ~/.ssh/id_ed25519
```

**EXPECT**

```
Agent pid 51234
Identity added: /Users/you/.ssh/id_ed25519 (your.email@example.com)
```

`UseKeychain yes` plus `--apple-use-keychain` means the passphrase is stored in the macOS Keychain and the key is loaded automatically after every reboot. You will not be asked again.

### Windows (PowerShell, run as Administrator once)

**TYPE**

```powershell
Set-Service -Name ssh-agent -StartupType Automatic
Start-Service ssh-agent
ssh-add "$env:USERPROFILE\.ssh\id_ed25519"
```

**EXPECT**

```
Identity added: C:\Users\you\.ssh\id_ed25519 (your.email@example.com)
```

### Linux

**TYPE**

```bash
eval "$(ssh-agent -s)"
ssh-add ~/.ssh/id_ed25519
```

The agent dies when the terminal closes. To have it start with your shell, add `eval "$(ssh-agent -s)" > /dev/null` to `~/.bashrc` or `~/.zshrc`, or install `keychain`.

**TYPE** — confirm the key is loaded, on any platform:

```bash
ssh-add -l
```

**EXPECT**

```
256 SHA256:aBcD1234... your.email@example.com (ED25519)
```

## 2.6 Copy the public key

**TYPE** — macOS:

```bash
pbcopy < ~/.ssh/id_ed25519.pub
```

**TYPE** — Windows PowerShell:

```powershell
Get-Content "$env:USERPROFILE\.ssh\id_ed25519.pub" | Set-Clipboard
```

**TYPE** — Linux:

```bash
xclip -selection clipboard < ~/.ssh/id_ed25519.pub
# or, if xclip is not installed, print it and copy by hand:
cat ~/.ssh/id_ed25519.pub
```

**EXPECT** — a single line, on the clipboard, of this shape:

```
ssh-ed25519 AAAAC3NzaC1lZDI1NTE5AAAAIH0kL2m... your.email@example.com
```

It must be **one line**. If your editor wrapped it across several lines when pasting, that is a display artifact — but if you introduced a real newline, GitHub will reject it as invalid.

## 2.7 Add the public key to GitHub

1. Avatar → **Settings** → **SSH and GPG keys**.
   Direct link: <https://github.com/settings/ssh/new>
2. **New SSH key**.
3. Fill in:

   | Field | Value |
   | --- | --- |
   | **Title** | `MacBook Air — lab` — again, name it after the machine |
   | **Key type** | **Authentication Key** |
   | **Key** | Paste the clipboard contents |

4. **Add SSH key**. Confirm your GitHub password if prompted.

> A key of type **Signing Key** is for verifying commit signatures, not for pushing. If you pick the wrong type, pushes will still fail with `Permission denied (publickey)`.

## 2.8 Test the connection

**TYPE**

```bash
ssh -T git@github.com
```

**EXPECT** — on first connection, a host verification prompt:

```
The authenticity of host 'github.com (140.82.121.4)' can't be established.
ED25519 key fingerprint is SHA256:+DiY3wvvV6TuJJhbpZisF/zLDA0zPMSvHdkr4UvCOqU.
Are you sure you want to continue connecting (yes/no/fingerprint)?
```

**Do not type `yes` reflexively.** Compare the fingerprint against GitHub's published list at <https://docs.github.com/authentication/keeping-your-account-and-data-secure/githubs-ssh-key-fingerprints>. GitHub's Ed25519 fingerprint is:

```
SHA256:+DiY3wvvV6TuJJhbpZisF/zLDA0zPMSvHdkr4UvCOqU
```

If it matches, type `yes`. If it does not match, stop — something is intercepting your connection.

**EXPECT** — then:

```
Hi <github-username>! You've successfully authenticated, but GitHub does not provide shell access.
```

That sentence about shell access is **success**, not an error. GitHub does not give you a login shell; the SSH connection exists only to carry Git traffic.

> **CHECKPOINT 2** — `ssh -T git@github.com` greets you by your own GitHub username.

## 2.9 If port 22 is blocked

On many corporate and campus networks, outbound port 22 is closed. Symptom:

```
ssh: connect to host github.com port 22: Connection timed out
```

GitHub runs the same SSH service on port 443, which is never blocked because it is the HTTPS port. Add this to `~/.ssh/config`:

```
Host github.com
  Hostname ssh.github.com
  Port 443
  User git
  IdentityFile ~/.ssh/id_ed25519
```

Then re-run `ssh -T git@github.com`. The greeting is identical.

\newpage

# Part 3 — Choosing between HTTPS and SSH

Every GitHub repository has two URLs for the same content:

| Protocol | URL for this repo | Authenticates with |
| --- | --- | --- |
| HTTPS | `https://github.com/kode-mafia008/django-lab.git` | Your PAT |
| SSH | `git@github.com:kode-mafia008/django-lab.git` | Your SSH key |

Note the shape difference: SSH has no `//`, and a **colon** rather than a slash between the host and the owner.

You configured both in Parts 1 and 2, so either will work. Pick one for the clone in Part 4.

**Switching an existing clone from one to the other** — this does not touch your files or your commits, only the address Git dials:

```bash
# check what you currently have
git remote -v

# HTTPS -> SSH
git remote set-url origin git@github.com:kode-mafia008/django-lab.git

# SSH -> HTTPS
git remote set-url origin https://github.com/kode-mafia008/django-lab.git
```

\newpage

# Part 4 — Clone the lab and branch off `main`

## 4.1 Pick a working directory

Do **not** clone into a folder that is already inside another Git repository, and avoid cloud-synced folders (Dropbox, OneDrive, iCloud Drive) — the sync client fights with Git over the `.git` directory and corrupts it.

**TYPE**

```bash
mkdir -p ~/code
cd ~/code
```

## 4.2 Clone

**TYPE** — SSH:

```bash
git clone git@github.com:kode-mafia008/django-lab.git
```

**TYPE** — or HTTPS (you will be prompted for username + PAT on first use):

```bash
git clone https://github.com/kode-mafia008/django-lab.git
```

**EXPECT**

```
Cloning into 'django-lab'...
remote: Enumerating objects: 84, done.
remote: Counting objects: 100% (84/84), done.
remote: Compressing objects: 100% (60/60), done.
Receiving objects: 100% (84/84), 214.51 KiB | 3.42 MiB/s, done.
Resolving deltas: 100% (12/12), done.
```

**TYPE**

```bash
cd django-lab
git status
```

**EXPECT**

```
On branch main
Your branch is up to date with 'origin/main'.

nothing to commit, working tree clean
```

**IF IT FAILS**

| Message | Cause | Fix |
| --- | --- | --- |
| `Permission denied (publickey)` | SSH key not added to GitHub, or agent not running | `ssh-add -l`; redo 2.5–2.7 |
| `Support for password authentication was removed` | You typed your account password | Use the PAT as the password (1.6) |
| `Repository not found` | Typo, or your account lacks access | Open the URL in a browser while logged in |
| `fatal: destination path 'django-lab' already exists` | You already cloned it | `cd django-lab` and continue |

## 4.3 Make sure `main` is current

Even on a fresh clone, run this. It becomes muscle memory, and on Day 2 it will matter.

**TYPE**

```bash
git switch main
git pull origin main
```

**EXPECT**

```
Already up to date.
```

**WHY** — branching from a stale `main` means your branch is missing commits everyone else already has. When you later open a pull request, the diff shows unrelated changes and merge conflicts appear that have nothing to do with your work.

## 4.4 Create your branch

The naming convention for this course is:

```
{first_name}/day1
```

- First name only, **lowercase**, no spaces, no surname.
- A forward slash, then the literal text `day1` — no space, no capital D, no `Day-1`.

| Student | Branch |
| --- | --- |
| Dharmendra | `dharmendra/day1` |
| Priya | `priya/day1` |
| Arjun Kumar | `arjun/day1` |

**TYPE**

```bash
git switch -c <first_name>/day1
```

**EXPECT**

```
Switched to a new branch 'dharmendra/day1'
```

**TYPE** — confirm:

```bash
git branch
```

**EXPECT** — an asterisk marks the branch you are on:

```
* dharmendra/day1
  main
```

**WHY the slash** — Git stores branches as files under `.git/refs/heads/`, so `dharmendra/day1` is literally the file `day1` inside a directory `dharmendra`. This gives you a per-student namespace: on Day 2 you create `dharmendra/day2` alongside it, and GitHub's branch list groups them together.

> **Consequence worth knowing:** because `dharmendra` must be a *directory*, you can never also have a branch simply named `dharmendra`. If you do, Git refuses with `cannot lock ref ... 'refs/heads/dharmendra' exists`. Delete the plain-named branch first: `git branch -d dharmendra`.

> **CHECKPOINT 3** — `git branch` shows `* <first_name>/day1`, and `git log --oneline -1` shows the same commit as `main`.

\newpage

# Part 5 — Build the Django project on your branch

Everything from here happens **on your branch**. Run `git branch` and confirm the asterisk is on `<first_name>/day1` before you continue.

## 5.1 Create the virtual environment

**TYPE** — macOS/Linux:

```bash
python3 -m venv venv
```

**TYPE** — Windows PowerShell:

```powershell
python -m venv venv
```

**EXPECT** — no output, and a new `venv/` directory.

**WHY** — a virtual environment is a private copy of Python and its packages, belonging to this project alone. Without it, `pip install django` installs into your system Python, and the next project that needs a different Django version breaks this one. Every Python project gets its own venv. No exceptions.

## 5.2 Activate it

**TYPE** — macOS/Linux:

```bash
source venv/bin/activate
```

**TYPE** — Windows PowerShell:

```powershell
venv\Scripts\Activate.ps1
```

**EXPECT** — your prompt gains a prefix:

```
(venv) $
```

**IF IT FAILS on Windows** with `running scripts is disabled on this system`:

```powershell
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
```

Then activate again.

**TYPE** — prove you are inside the venv:

```bash
which python      # macOS/Linux
where.exe python  # Windows
```

**EXPECT** — a path *inside* your project, not `/usr/bin/python3`:

```
/Users/you/code/django-lab/venv/bin/python
```

> The `(venv)` prefix disappears when you close the terminal. Every new terminal session needs `source venv/bin/activate` again. Forgetting this is the single most common cause of "but I installed Django already".

## 5.3 Upgrade pip

**TYPE**

```bash
python -m pip install --upgrade pip
```

## 5.4 Install Django

The repo already ships a pinned `requirements.txt`. Install from it, so the whole class runs identical versions:

**TYPE**

```bash
pip install -r requirements.txt
```

**EXPECT**

```
Successfully installed Django-5.2.17 asgiref-3.12.1 sqlparse-0.6.0
```

If your Day 1 task was to start from nothing instead, install Django directly:

```bash
pip install django
```

**TYPE** — verify either way:

```bash
python -m django --version
```

**EXPECT**

```
5.2.17
```

## 5.5 Create the Django project

**TYPE**

```bash
django-admin startproject day1_project
```

**EXPECT** — no output, and this structure:

```
day1_project/
├── manage.py
└── day1_project/
    ├── __init__.py
    ├── asgi.py
    ├── settings.py
    ├── urls.py
    └── wsgi.py
```

**WHY the doubled name** — the outer `day1_project/` is just a folder; the inner one is the Python package holding your settings. Passing a trailing `.` (`django-admin startproject day1_project .`) creates the project in the current directory instead, without the outer wrapper. Do not do that here — `django-lab` already contains a `config/` project at its root, and you would collide with it.

**TYPE** — run it:

```bash
cd day1_project
python manage.py runserver
```

**EXPECT**

```
Watching for file changes with StatReloader
Performing system checks...

System check identified no issues (0 silenced).

You have 18 unapplied migration(s). ...
Django version 5.2.17, using settings 'day1_project.settings'
Starting development server at http://127.0.0.1:8000/
Quit the server with CONTROL-C.
```

Open <http://127.0.0.1:8000/> in a browser. You should see the Django rocket launch page.

The unapplied-migrations warning is expected on a brand new project and is not an error.

Press **Ctrl+C** to stop the server, then return to the repo root:

```bash
cd ..
```

## 5.6 Freeze the dependencies

**TYPE**

```bash
pip freeze > requirements.txt
```

**TYPE** — look at what you just wrote:

```bash
cat requirements.txt
```

**EXPECT**

```
asgiref==3.12.1
Django==5.2.17
sqlparse==0.6.0
```

**WHY `pip freeze`** — it records the *exact* version of every installed package, including the ones Django pulled in itself. `Django==5.2.17` rather than `Django`, so that when the trainer clones your branch in six months, pip installs the same code you ran today rather than whatever is newest.

> **`pip freeze` records whatever is in the venv right now.** If you ran it with the venv deactivated, you will get a hundred lines of unrelated system packages. Check the `(venv)` prefix, check the output, and re-run it if it looks wrong.

## 5.7 The rule: commit `requirements.txt`, never commit `venv/`

**TYPE**

```bash
git status
```

**EXPECT** — `venv/` must **not** appear:

```
On branch dharmendra/day1
Untracked files:
  (use "git add <file>..." to include in what will be committed)
	day1_project/

nothing added to commit but untracked files present
```

`venv/` is absent because the repo's `.gitignore` already lists it. Confirm:

**TYPE**

```bash
git check-ignore -v venv/
```

**EXPECT**

```
.gitignore:2:venv/	venv/
```

**WHY you never commit a venv:**

| Reason | Detail |
| --- | --- |
| It is not portable | It contains compiled binaries built for *your* OS and CPU. A classmate on Windows cannot use your macOS venv. |
| It is huge | Several thousand files, tens of megabytes, for something reproducible from three lines of text. |
| It hides the truth | With a venv committed, nobody notices when `requirements.txt` drifts out of date — until CI, on a clean machine, fails. |
| It bloats history forever | Git keeps every version of every file. Committing a venv once makes the repo permanently larger, even after you delete it. |

`requirements.txt` is the *recipe*; `venv/` is the *cake*. Ship the recipe.

**IF `venv/` DOES appear in `git status`** — your `.gitignore` is missing the entry, or you already staged it. Fix it before committing:

```bash
git rm -r --cached venv          # unstage, keep the files on disk
echo "venv/" >> .gitignore
git status                       # venv/ should now be gone from the list
```

> **CHECKPOINT 4** — `git status` lists `day1_project/` as untracked and `requirements.txt` as modified, and `venv/` appears nowhere.

\newpage

# Part 6 — Commit and push to your branch

## 6.1 Stage

**TYPE**

```bash
git add day1_project requirements.txt
```

**TYPE** — review exactly what is staged, before committing:

```bash
git status
```

**EXPECT**

```
On branch dharmendra/day1
Changes to be committed:
  (use "git restore --staged <file>..." to unstage)
	new file:   day1_project/manage.py
	new file:   day1_project/day1_project/__init__.py
	new file:   day1_project/day1_project/asgi.py
	new file:   day1_project/day1_project/settings.py
	new file:   day1_project/day1_project/urls.py
	new file:   day1_project/day1_project/wsgi.py
	modified:   requirements.txt
```

Six new files and one modification. If you see hundreds of files, you staged the venv — go back to 5.7.

> `git add .` stages everything, including things you did not mean to. Naming the paths explicitly is the habit worth building.

## 6.2 Commit

**TYPE**

```bash
git commit -m "Day 1: Django project scaffold with venv and pinned requirements"
```

**EXPECT**

```
[dharmendra/day1 a1b2c3d] Day 1: Django project scaffold with venv and pinned requirements
 7 files changed, 142 insertions(+)
```

**WHY the message shape** — present tense, says what the commit *does*, under about 70 characters. `git log --oneline` shows only the first line, so it has to stand alone. "update", "fix", and "asdf" are not commit messages.

## 6.3 Push

**TYPE**

```bash
git push -u origin <first_name>/day1
```

**EXPECT**

```
Enumerating objects: 12, done.
Counting objects: 100% (12/12), done.
Writing objects: 100% (10/10), 3.21 KiB | 3.21 MiB/s, done.
remote:
remote: Create a pull request for 'dharmendra/day1' on GitHub by visiting:
remote:      https://github.com/kode-mafia008/django-lab/pull/new/dharmendra/day1
remote:
To github.com:kode-mafia008/django-lab.git
 * [new branch]      dharmendra/day1 -> dharmendra/day1
branch 'dharmendra/day1' set up to track 'origin/dharmendra/day1'.
```

**WHY `-u`** — short for `--set-upstream`. It links your local branch to the remote one, so from now on plain `git push` and `git pull` know where to go. You only need `-u` on the first push of a branch.

**IF IT FAILS**

| Message | Cause | Fix |
| --- | --- | --- |
| `Permission denied (publickey)` | SSH key not loaded | `ssh-add ~/.ssh/id_ed25519`, retry |
| `Authentication failed` (HTTPS) | PAT expired, wrong, or lacks **Contents: write** | Regenerate the token (1.3), clear the old credential (1.8) |
| `403 Forbidden` | Token is valid but read-only, or you lack write access to the repo | Check the token's Contents permission; ask the trainer to confirm your access |
| `src refspec ... does not match any` | Branch name typo in the push command | `git branch` to see the real name, retype it |
| `Updates were rejected because the remote contains work` | Someone pushed to your branch, or you pushed from another machine | `git pull --rebase origin <first_name>/day1`, then push again |

## 6.4 Verify on GitHub

1. Open <https://github.com/kode-mafia008/django-lab>.
2. Click the branch dropdown (it reads **main**).
3. Select `<first_name>/day1`.
4. Confirm you can see `day1_project/` and that `requirements.txt` contains your pinned versions.
5. Confirm `venv/` is **not** listed.

> **CHECKPOINT 5 — Day 1 complete.** Your branch `<first_name>/day1` exists on GitHub, contains a Django project and a `requirements.txt`, and contains no `venv/`.

## 6.5 Optional — open a pull request

If the trainer asked for one:

```bash
gh pr create --base main --head <first_name>/day1 \
  --title "Day 1 — <Your Name>" \
  --body "Django project scaffold, venv-based, requirements pinned."
```

Or use the `Compare & pull request` button GitHub shows at the top of the repo after a push. Do **not** merge it yourself.

\newpage

# Appendix A — Prove your setup from scratch

A classmate should be able to reproduce your work from your branch alone. Test it yourself:

```bash
cd /tmp
git clone -b <first_name>/day1 git@github.com:kode-mafia008/django-lab.git verify-day1
cd verify-day1/day1_project
python3 -m venv venv
source venv/bin/activate
pip install -r ../requirements.txt
python manage.py runserver
```

If the rocket page loads, your branch is genuinely self-contained. If `pip install` fails or Django is missing, your `requirements.txt` is incomplete — fix it, commit, push.

Clean up: `cd /tmp && rm -rf verify-day1`.

\newpage

# Appendix B — Command cheat sheet

**Setup, once per machine**

```bash
git config --global user.name  "Your Name"
git config --global user.email "you@example.com"
git config --global init.defaultBranch main
git config --global credential.helper osxkeychain     # macOS
ssh-keygen -t ed25519 -C "you@example.com"
ssh-add --apple-use-keychain ~/.ssh/id_ed25519        # macOS
pbcopy < ~/.ssh/id_ed25519.pub                        # then paste into GitHub
ssh -T git@github.com
```

**Every day**

```bash
git switch main
git pull origin main
git switch -c <first_name>/dayN
# ... work ...
git status
git add <paths>
git commit -m "Day N: what this does"
git push -u origin <first_name>/dayN
```

**Virtual environment**

```bash
python3 -m venv venv
source venv/bin/activate          # macOS/Linux
venv\Scripts\Activate.ps1         # Windows
pip install -r requirements.txt
pip freeze > requirements.txt
deactivate
```

**Getting unstuck**

```bash
git remote -v                     # which URL am I using?
git branch                        # which branch am I on?
git log --oneline -5              # what are my last five commits?
git restore <file>                # throw away uncommitted changes to a file
git restore --staged <file>       # unstage, keep the changes
git switch -                      # go back to the previous branch
ssh-add -l                        # is my SSH key loaded?
git check-ignore -v <path>        # why is this file being ignored?
```

\newpage

# Appendix C — Error message index

| You see | It means | Do this |
| --- | --- | --- |
| `Support for password authentication was removed` | You typed your GitHub password | Use a PAT as the password — Part 1 |
| `Authentication failed for 'https://github.com/...'` | Wrong, expired, or under-permissioned PAT | Regenerate (1.3), clear old credential (1.8) |
| `Permission denied (publickey)` | SSH key missing, not loaded, or added to GitHub as a Signing Key | `ssh-add -l`, then 2.5–2.7 |
| `Connection timed out` on port 22 | Firewall blocks SSH | Use port 443 — 2.9 |
| `Host key verification failed` | Server fingerprint changed | Verify against GitHub's published fingerprints before proceeding |
| `WARNING: UNPROTECTED PRIVATE KEY FILE` | Key file is world-readable | `chmod 600 ~/.ssh/id_ed25519` |
| `Repository not found` | Typo, or no access | Open the URL in a logged-in browser |
| `fatal: not a git repository` | You are outside the project folder | `cd django-lab` |
| `src refspec ... does not match any` | Branch name typo | `git branch`, retype |
| `Updates were rejected` | Remote has commits you do not | `git pull --rebase origin <branch>` |
| `cannot lock ref 'refs/heads/<name>'` | A branch named `<name>` blocks `<name>/day1` | `git branch -d <name>` |
| `django-admin: command not found` | venv not activated | `source venv/bin/activate` |
| `ModuleNotFoundError: No module named 'django'` | venv not activated, or Django not installed | Activate, then `pip install -r requirements.txt` |
| `running scripts is disabled on this system` | Windows PowerShell execution policy | `Set-ExecutionPolicy RemoteSigned -Scope CurrentUser` |
| `That port is already in use` | A `runserver` is still running elsewhere | `python manage.py runserver 8001`, or kill the old process |

\newpage

# Appendix D — Trainer notes

**Verifying the class**

```bash
git fetch --all --prune
git branch -r | grep '/day1$' | sed 's|origin/||' | sort
```

That prints one line per student who completed Day 1. Cross-check against the register.

**Reviewing one student's work**

```bash
git switch <first_name>/day1
git log --oneline main..HEAD          # what did they add?
git diff --stat main..HEAD            # how much, and which files?
git ls-tree -r --name-only HEAD | grep -c '^venv/'   # must print 0
```

**Common failure modes seen in the room**

| Symptom | Root cause | Fix at the whiteboard |
| --- | --- | --- |
| Push takes minutes, thousands of objects | `venv/` was committed | `git rm -r --cached venv`, amend, force-push their branch |
| Branch named `Dharmendra/Day1` | Copy-paste from slides without substituting | `git branch -m <first_name>/day1`, delete the remote one, re-push |
| `requirements.txt` has 80 lines | `pip freeze` run outside the venv | Reactivate, re-freeze, amend |
| Commits show a grey avatar on GitHub | `user.email` not verified on their account | Part 0, then `git commit --amend --reset-author` |
| Works on their machine, not on a clean clone | Missing dependency never frozen | Appendix A |

**Time budget** — Parts 0–3 take about 45 minutes with a room of 20 if you demo on the projector and walk the room during 2.3–2.8. Parts 4–6 take about 30 minutes. SSH agent setup on Windows is the single biggest time sink; have the PowerShell commands from 2.5 on a slide.
