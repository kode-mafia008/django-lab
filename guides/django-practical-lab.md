---
title: "Django Practical Lab"
subtitle: "Foundation & Django Core — Modules 1–7, 30 contact hours"
author: "Trainer's live-demo script and student lab manual"
date: "Django 5.2 LTS · Python 3.12"
---

# Before you start

## What this document is

This is the **keyboard companion** to the Django Framework Backend Development course. Where the trainer guide answers *how do I teach this*, this document answers *what exactly do I type, in what order, and what should appear on screen*.

It covers the first seven modules — the Foundation phase (Modules 1–3) and the Django Core phase (Modules 4–7) — which together are 30 of the course's 62 contact hours. By the end of Session 7 you and the class will have built the same working application, from an empty folder to a database-backed Django site with three kinds of model relationship.

Everything here is meant to be run. Every command has been written to be typed verbatim, and every expected output is the real output, not a paraphrase.

## Who reads what

| You are | Read it as |
| --- | --- |
| The trainer, running a live session | A script. Follow the demos in order, keep this on your second screen, and type on the projector while the class types along. |
| A student | A lab manual. Work through it at your own pace; the checkpoints tell you whether you are still on track. |
| A student who missed a session | A catch-up. Each session ends with a Git checkpoint tag you can jump to. |

Trainer-only material — timing, what to say, what to deliberately break — is marked **`TRAINER`** and can be ignored by students.

## Conventions

| Marker | Meaning |
| --- | --- |
| **TYPE** | Type this exactly. Do not copy-paste — the typos are part of the lesson. |
| **EXPECT** | What should appear. If you see something else, stop and fix it before moving on. |
| **BREAK IT** | A deliberate error. Cause it, read the message, then undo it. |
| **CHECKPOINT** | A verifiable state. Nobody moves on until everyone reaches it. |
| **IF IT FAILS** | The three most likely causes, in order of likelihood. |
| **`TRAINER`** | Guidance for the person at the front of the room. |

Shell prompts are shown as `$` for macOS and Linux and `>` for Windows PowerShell. Do not type the prompt character. Python REPL lines start with `>>>`, which you also do not type.

## The one stack, pinned

Every machine in the room runs the same versions. This is not a preference — it removes an entire class of support ticket from the next 30 hours.

| Component | Version | Check with |
| --- | --- | --- |
| Python | 3.12.x | `python3 --version` |
| Django | 5.2 LTS | `python -m django --version` |
| Database | SQLite (bundled) | nothing to install |
| Editor | VS Code | `code --version` |
| Git | 2.30+ | `git --version` |

> **`TRAINER`** — Confirm the current Django LTS on <https://www.djangoproject.com/download/> before term starts. If it has moved on, change the pin here and in the install command in Demo 3.5, and nothing else in this document needs to change.

## The project we build

One project, all seven sessions: a **library catalogue**. It is chosen because it reaches all three relationship types without inventing new subject matter.

By the end of Session 7 the data model looks like this:

```
Author ──1:1──> AuthorProfile      (one-to-one)
  │
  │ 1:M
  ↓
 Book ──M:M──> Genre               (many-to-many)
```

| Model | Fields | Introduced |
| --- | --- | --- |
| `Author` | `name`, `bio` | Session 6 |
| `Book` | `title`, `year`, `price`, `cover`, `author` | Session 6 |
| `AuthorProfile` | `author`, `website`, `country` | Session 7 |
| `Genre` | `name`, `books` | Session 7 |

## Session map

| Session | Module | Hours | You will finish with |
| --- | --- | --- | --- |
| 1 | M1 · Web & Backend | 6 | A verified machine, and HTTP understood by observation |
| 2 | M2 · Python Fundamentals | 4 | Working Python: functions, loops, conditionals |
| 3 | M3 · Advanced Python | 4 | A virtual environment with Django installed |
| 4 | M4 · OOP & Django Fundamentals | 4 | A running Django site with your own URLs |
| 5 | M5 · Templates & Static Files | 4 | Real HTML pages with a shared layout and CSS |
| 6 | M6 · Models & Database | 4 | A database, an admin panel, and CRUD |
| 7 | M7 · ORM & Relationships | 4 | All three relationship types, queried both ways |

\newpage

# Session 1 — Web & Backend Development

**Module 1 · 6 hours · no prerequisite**

The goal of this session is not to write Django. It is to make HTTP *visible*, so that everything built in Sessions 4–7 lands on top of something the class has actually observed rather than been told about.

> **`TRAINER`** — Budget: 90 min demos, 60 min setup lab, 75 min Python warm-up, breaks and open/close fill the rest. The setup lab is the part that must not be cut; nobody leaves with an unverified laptop.

---

## Demo 1.1 — Read a real request · 20 min

**Goal.** See that a single page is dozens of separate request–response pairs.

**Do this, on the projector:**

1. Open any content-heavy site — a news site works well.
2. Open DevTools: **F12**, or **Cmd**+**Option**+**I** on macOS.
3. Click the **Network** tab.
4. Tick **Disable cache**. Leave it ticked for the rest of the course.
5. Reload the page.

**EXPECT** — Dozens of rows appear. Point at the columns: Name, Status, Type, Size, Time.

**Now click the very first row** (the document itself) and read aloud, in this order:

| Panel | Point at | Say |
| --- | --- | --- |
| Headers → General | `Request URL`, `Request Method: GET`, `Status Code: 200` | "Three things: where, what verb, and how it went." |
| Headers → Request Headers | `Host`, `User-Agent`, `Accept` | "The browser describing itself and what it wants." |
| Headers → Response Headers | `Content-Type: text/html` | "The server saying what it is sending back." |
| Response | the raw HTML | "This text is the entire response body." |

**Then filter to `Fetch/XHR`** and click something interactive on the page — a menu, a "load more" button.

**EXPECT** — A new request appears with no page reload, and its response is JSON, not HTML.

> **`TRAINER`** — Say: *"That is an API. In Module 11 you will build one. Same picture, different response format."* Then move on — do not explain APIs yet.

---

## Demo 1.2 — `file://` is not a website · 10 min

**Goal.** Kill the belief that opening an HTML file in a browser is "running a website".

**TYPE** — in an empty folder:

```bash
mkdir -p ~/code/http-demo && cd ~/code/http-demo
echo '<h1>Hello from a real server</h1>' > index.html
```

Now open `index.html` by double-clicking it.

**EXPECT** — The address bar reads `file:///Users/…/index.html`. Open DevTools → Network and reload: there is no status code, because there was no server.

**TYPE:**

```bash
python3 -m http.server 8000
```

**EXPECT:**

```
Serving HTTP on :: port 8000 (http://[::]:8000/) ...
```

Open <http://localhost:8000> and reload with the Network tab open.

**EXPECT** — Same page, but now with `Status 200`, a `Content-Type` header, and a line in the terminal:

```
::1 - - [24/Aug/2026 10:14:22] "GET / HTTP/1.1" 200 -
```

> **`TRAINER`** — That terminal line is the point of the demo. Say: *"Every request you make now writes a line on the server. That is what a backend is — a program that is listening."*

Leave this server running for Demo 1.3.

---

## Demo 1.3 — The raw HTTP message · 25 min

**Goal.** Show that an HTTP message is plain text a human can read.

**TYPE** — in a *second* terminal, leaving the server from 1.2 running:

```bash
curl -v http://localhost:8000/
```

**EXPECT** — Lines starting with `>` are the request your machine sent; lines starting with `<` are the response:

```
> GET / HTTP/1.1
> Host: localhost:8000
> User-Agent: curl/8.4.0
> Accept: */*
>
< HTTP/1.1 200 OK
< Server: SimpleHTTP/0.6 Python/3.12.2
< Content-type: text/html
< Content-Length: 34
<
<h1>Hello from a real server</h1>
```

Walk the class through it line by line:

- `GET` — the method, the verb of the sentence
- `/` — the path
- `HTTP/1.1` — the protocol version
- the blank line — the separator between headers and body
- `200 OK` — the status line
- the last line — the body

**Now provoke the status codes.**

**TYPE:**

```bash
curl -i http://localhost:8000/does-not-exist.html
```

**EXPECT** — `HTTP/1.0 404 File not found`

**TYPE:**

```bash
curl -i -X POST http://localhost:8000/
```

**EXPECT** — `HTTP/1.0 501 Unsupported method ('POST')`

**TYPE** — just the status code, nothing else:

```bash
curl -s -o /dev/null -w "%{http_code}\n" http://localhost:8000/
```

**EXPECT** — `200`

> **`TRAINER`** — Now put the rule on the board and make them say it back: **4xx is your fault, 5xx is the server's fault.** Ask which one their typo in `does-not-exist.html` caused. Then stop the server with **Ctrl**+**C**.

---

## Demo 1.4 — What HTTPS hides · 15 min

**Goal.** HTTPS is not a different protocol. It is the same message inside an encrypted tube.

**TYPE:**

```bash
curl -v https://www.djangoproject.com/ 2>&1 | head -30
```

**EXPECT** — Before any HTTP appears, there is a TLS handshake:

```
* TLSv1.3 (OUT), TLS handshake, Client hello (1):
* TLSv1.3 (IN), TLS handshake, Server hello (2):
* SSL connection using TLSv1.3 / AEAD-AES128-GCM-SHA256
* Server certificate:
*  subject: CN=djangoproject.com
*  issuer: C=US; O=Let's Encrypt; CN=R11
```

…and *then* the familiar `> GET / HTTP/2` request, unchanged.

**Now in the browser:** click the padlock in the address bar → *Connection is secure* → *Certificate is valid*.

Point at three things: who it was issued **to**, who issued it, and when it **expires**.

> **`TRAINER`** — Close with the sentence that Module 13 will need: *"Encryption proves the tube is private. It does not prove the other end deserves your trust — a phishing site can have a perfectly valid certificate. Proving who someone is, is a separate problem called authentication."*

---

## Lab 1.5 — Verify every machine · 60 min

Nobody leaves this session with an unverified laptop. Every student runs all five commands and shows you the output.

**TYPE:**

```bash
python3 --version          # expect Python 3.12.x
python3 -m venv --help     # must print help, not an error
python3 -m pip --version   # pip present
git --version              # expect 2.30 or newer
code --version             # VS Code CLI on PATH
```

Then create the working folder that every later session assumes:

```bash
mkdir -p ~/code
cd ~/code
```

**IF IT FAILS** — the five failures you will actually see:

| Symptom | Cause | Fix |
| --- | --- | --- |
| `python` opens the Microsoft Store | Windows execution alias shadows the real install | Reinstall from python.org with **Add python.exe to PATH** ticked, then turn off the aliases in Settings → Apps → App execution aliases |
| `activate` refuses to run in PowerShell | Execution policy | `Set-ExecutionPolicy -Scope CurrentUser RemoteSigned`, or use `venv\Scripts\activate.bat` from `cmd.exe` |
| `error: externally-managed-environment` | Installing into Homebrew Python outside a venv | Do **not** use `--break-system-packages`. This is exactly the problem Session 3 solves — say so and move on |
| `django-admin: command not found` | Installed into a different interpreter than the one on PATH | Use `python -m django` and `python -m pip` everywhere. Make it a house rule from today |
| Weird SQLite or `__pycache__` errors later | Project folder inside OneDrive or iCloud Drive | Move it to `~/code` or `C:\code`. Enforce this now, before anything is created |

**CHECKPOINT 1** — Every student can show `python3 --version` returning 3.12.x, and has an empty `~/code` folder.

---

## Lab 1.6 — Python warm-up (diagnostic) · 75 min

These are deliberately not Django. Their purpose is to tell the trainer, before Session 2 begins, who can already write a loop.

Create `~/code/warmup.py` and solve these in pairs:

```python
# 1 — Print 1 to 50. Print "Fizz" for multiples of 3, "Buzz" for multiples
#     of 5, and "FizzBuzz" for multiples of both.

# 2 — Given prices = [120, 340, 89, 560, 210], print the total, the
#     average, and the largest.

# 3 — Ask the user for a word. Print it reversed, then say whether it is
#     a palindrome.

# 4 — Count how many times each letter appears in a sentence.

# 5 — Given these two parallel lists, print only the books published
#     after 2000, sorted by year.
titles = ["Dune", "Cloud Atlas", "Emma", "The Road", "It"]
years  = [1965, 2004, 1815, 2006, 1986]

# STRETCH — a tiny library in memory: add a book, list all books,
# search by title. Keep everything in a list of dictionaries.
```

> **`TRAINER`** — Walk the room. Note who is stuck on exercise 1 versus who reaches the stretch goal; that ratio decides how much of Session 2 you spend on loops. Say this about the stretch goal: *"In Session 6 the same thing gets a real database and eighty per cent of this code disappears. That is what a framework is for."*

---

## Session 1 close

**CHECKPOINT 1 — every student can:**

1. Point at a request in DevTools and read its method, path and status.
2. Explain what `python3 -m http.server` did that double-clicking the file did not.
3. Say which of `4xx` and `5xx` is the client's fault.
4. Show a verified Python 3.12 installation.

\newpage

# Session 2 — Python Fundamentals

**Module 2 · 4 hours · builds on Session 1**

Everything in this session reappears inside Django. Keep the mapping table on screen and point at it whenever a student asks why they are learning Python instead of Django.

| Today | Where it comes back | Session |
| --- | --- | --- |
| A function that takes an argument and returns a value | A view: `def book_list(request): return HttpResponse(...)` | 4 |
| Dictionary | The template context, `request.POST`, JSON payloads | 5, 6 |
| `for` loop | `{% for book in books %}` in a template | 5 |
| `if` and truthiness | `{% if books %}` | 5 |
| String formatting | `__str__` on every model | 6 |
| Keyword arguments | `models.CharField(max_length=200, blank=True)` | 6 |
| Comparison operators | `Book.objects.filter(year__gt=2000)` | 7 |

---

## Demo 2.1 — Names are labels, not boxes · 20 min

**Goal.** Kill the "variable is a box" model before it causes four later bugs.

**TYPE** — in the REPL (`python3`):

```python
>>> a = [1, 2, 3]
>>> b = a
>>> id(a) == id(b)
True
>>> a.append(4)
>>> b
[1, 2, 3, 4]
```

> **`TRAINER`** — Stop here. Let the surprise land before explaining. Ask: *"I changed `a`. Why did `b` change?"*

Then draw the label model on the board: two labels, one object. Now show the separation:

```python
>>> b = b + [5]
>>> id(a) == id(b)
False
>>> a
[1, 2, 3, 4]
>>> b
[1, 2, 3, 4, 5]
```

**Say:** `append` changed the object both names point at. `b + [5]` built a *new* object and moved only the label `b` onto it.

---

## Demo 2.2 — Types, operators, and the two-equals rule · 25 min

**TYPE:**

```python
>>> 7 / 2          # true division — always a float
3.5
>>> 7 // 2         # floor division — throws away the remainder
3
>>> 7 % 2          # the remainder itself
1
>>> type(7 / 2)
<class 'float'>

>>> name = "Dune"
>>> year = 1965
>>> f"{name} was published in {year}"
'Dune was published in 1965'

>>> "5" + 1
Traceback (most recent call last):
  File "<stdin>", line 1, in <module>
TypeError: can only concatenate str (not "int") to str
>>> int("5") + 1
6
```

> **`TRAINER`** — That `TypeError` is the single most useful error in Session 2. Say: *"`input()` always gives you a string. So does an HTML form in Session 5, and so does an API request in Module 11. Converting text to the type you need is a job you will do for the rest of your career."*

**The two-equals rule:**

```python
>>> x = 5          # one equals: make it so
>>> x == 5         # two equals: is it so?
True
>>> x is 5         # DO NOT use `is` for values
<stdin>:1: SyntaxWarning: "is" with 'int' literal.
```

**Say:** `==` asks *same value*. `is` asks *same object*. Use `is` only with `None`, `True` and `False`.

---

## Demo 2.3 — Truthiness and the `elif` bug · 25 min

**TYPE** — the complete list of falsy values, and nothing else is falsy:

```python
>>> bool(False), bool(None), bool(0), bool(0.0)
(False, False, False, False)
>>> bool(""), bool([]), bool({}), bool(())
(False, False, False, False)
>>> bool("0"), bool([0]), bool(" ")
(True, True, True)
```

> **`TRAINER`** — Point at that last line. `"0"` is a *string* and therefore truthy. This bites in Session 5, when form input arrives as text.

**BREAK IT** — write this in a file and run it:

```python
# grades_broken.py
score = 95

if score >= 90:
    grade = "A"
if score >= 75:
    grade = "B"
if score >= 60:
    grade = "C"

print(grade)
```

**EXPECT** — `C`. A score of 95 gets a C.

**Ask the class why**, then fix it:

```python
# grades_fixed.py
score = 95

if score >= 90:
    grade = "A"
elif score >= 75:
    grade = "B"
else:
    grade = "C"

print(grade)     # A
```

**Say:** With `elif`, the first match wins and the rest never run. With three separate `if`s, all three run and the last one wins.

---

## Demo 2.4 — Loops · 30 min

**Goal.** Teach `for` as "one item at a time, in order", not as "repeat N times".

**TYPE:**

```python
>>> books = ["Dune", "Emma", "It"]
>>> for book in books:
...     print(book)
...
Dune
Emma
It

>>> for i, book in enumerate(books, start=1):
...     print(i, book)
...
1 Dune
2 Emma
3 It

>>> list(range(1, 10))
[1, 2, 3, 4, 5, 6, 7, 8, 9]
```

> **`TRAINER`** — Do not let anyone take `range` on faith. Making them print it settles the off-by-one question permanently: **start included, stop excluded** — the same rule as slicing.

**Now show the Django version side by side**, without explaining it:

```python
# Python — today
for book in books:
    print(book)
```

```django
{# Django template — Session 5 #}
{% for book in books %}
  <li>{{ book }}</li>
{% endfor %}
```

**Say:** *"Same mechanism, different punctuation. You already know this."*

**When to reach for `while`:** only when the number of repeats is unknown — waiting on a condition, retrying, reading until end of input. If a collection exists, `for` is the answer.

---

## Demo 2.5 — Functions, and the shape of a Django view · 30 min

**TYPE:**

```python
>>> def grade(score, curve=0):
...     total = score + curve
...     return "A" if total >= 90 else "B"
...
>>> grade(88)
'B'
>>> grade(88, curve=5)
'A'
```

Name the parts on the board: `def`, the name, the **parameters** (`score`, `curve`, which has a default). At the call site, `88` and `curve=5` are the **arguments**.

**BREAK IT** — the most common beginner bug in the whole course:

```python
>>> def add(a, b):
...     print(a + b)          # print, not return
...
>>> result = add(2, 3)
5
>>> print(result)
None
```

> **`TRAINER`** — Say it twice: **`return` hands a value back to the caller. `print` draws text on a screen.** A Django view that prints instead of returning gives the browser a blank page and the student a twenty-minute mystery.

**Now put the two shapes side by side:**

```python
# Any Python function
def grade(score, curve=0):
    total = score + curve
    return "A" if total >= 90 else "B"

# A Django view — Session 4
def book_list(request):
    books = Book.objects.all()
    return render(request, "catalog/book_list.html", {"books": books})
```

**Say:** *"Something goes in, something comes back. Django calls the second one for you, once per request. That is the only difference."*

---

## Lab 2.6 — Exercises · 60 min

Create `~/code/lab02.py`.

```python
# A — Temperature converter.
#     Ask for °C and print °F. Then wrap the maths in a function that
#     takes a value and RETURNS the converted number. Notice what changed.

# B — Library fine calculator. Days overdue -> fine.
#       0 days      : free
#       1-7 days    : 5 per day
#       8-30 days   : 10 per day
#       over 30     : 10 per day plus a flat 100
#     Use if/elif/else. Then test the boundaries: 0, 1, 7, 8, 30, 31.

# C — Given titles = ["Dune", "Emma", "It", "Hamlet"], print each with
#     its position using enumerate. Then print only titles longer than
#     three characters.

# D — Write is_valid_isbn(code) that returns True when code is exactly
#     13 characters and all digits. Return a bool. Do not print inside it.

# E — TRAP HUNT. Predict the output BEFORE you run it.
def add_book(title, shelf=[]):
    shelf.append(title)
    return shelf

print(add_book("Dune"))
print(add_book("Emma"))
```

**EXPECT** for E:

```
['Dune']
['Dune', 'Emma']
```

> **`TRAINER`** — Explain E with the label diagram from Demo 2.1: the default list is created **once**, when the function is defined, not on each call. Both calls append to the same object. The fix:
>
> ```python
> def add_book(title, shelf=None):
>     if shelf is None:
>         shelf = []
>     shelf.append(title)
>     return shelf
> ```

---

## Session 2 close

**CHECKPOINT 2 — every student can:**

1. Write a function that takes a list of numbers and returns the largest, with no `print` inside it.
2. Say which of these are falsy: `0`, `"0"`, `[]`, `[0]`, `None`, `" "`.
3. Explain why `a = [1,2]; b = a; b.append(3)` changes `a`.
4. Say what a function returns when it has no `return` statement.

\newpage

# Session 3 — Advanced Python Fundamentals

**Module 3 · 4 hours · builds on Session 2**

This session ends with Django installed. Protect the last hour: the virtual environment work in Demo 3.6 is what makes Sessions 4–7 possible, and it is the first thing that gets squeezed when the containers demo overruns.

---

## Demo 3.1 — Four containers, four jobs · 45 min

**Goal.** Choosing a container is a design decision. Give the class the decision rule before the details.

> **Order matters → `list` · Never changes → `tuple` · Uniqueness matters → `set` · Look up by name → `dict`**

**TYPE — list:**

```python
>>> books = ["Dune", "Emma", "It"]
>>> books[0]
'Dune'
>>> books.append("Hamlet")
>>> books
['Dune', 'Emma', 'It', 'Hamlet']
>>> books[1:3]
['Emma', 'It']
>>> len(books)
4
```

**TYPE — tuple:**

```python
>>> point = (27.7172, 85.3240)
>>> point[0]
27.7172
>>> point.append(1)
Traceback (most recent call last):
  File "<stdin>", line 1, in <module>
AttributeError: 'tuple' object has no attribute 'append'
```

**Say:** A tuple is a fixed-size record. Because it cannot change, it can be used as a dictionary key — a list cannot.

**TYPE — set:**

```python
>>> genres = {"sci-fi", "classic", "horror"}
>>> genres.add("sci-fi")          # already there
>>> genres
{'sci-fi', 'classic', 'horror'}   # unchanged, silently
>>> "classic" in genres
True
>>> tags = ["a", "b", "a", "c", "b"]
>>> set(tags)
{'a', 'b', 'c'}
```

**TYPE — dict, and give it the star billing:**

```python
>>> book = {"title": "Dune", "year": 1965, "in_stock": True}
>>> book["title"]
'Dune'
>>> book["publisher"]
Traceback (most recent call last):
  File "<stdin>", line 1, in <module>
KeyError: 'publisher'
>>> book.get("publisher")          # returns None, no exception
>>> book.get("publisher", "unknown")
'unknown'
>>> for key, value in book.items():
...     print(key, "=", value)
...
title = Dune
year = 1965
in_stock = True
```

> **`TRAINER`** — Say this and mean it: *"This is not one of four equal options. A dictionary is the shape of the web. JSON is a dictionary. An HTML form submission is a dictionary. A template context is a dictionary. An API response is a dictionary. Learn this one properly and half of Django stops looking new."*

**BREAK IT** — mutating a list while looping over it:

```python
>>> nums = [1, 2, 3, 4, 5, 6]
>>> for n in nums:
...     if n % 2 == 0:
...         nums.remove(n)
...
>>> nums
[1, 3, 5]        # looks right...
>>> nums = [2, 2, 3]
>>> for n in nums:
...     if n % 2 == 0:
...         nums.remove(n)
...
>>> nums
[2, 3]           # ...but it silently skipped one
```

**Say:** No error, wrong answer — worse than a crash. Loop over a copy (`for n in nums[:]`) or build a new list.

---

## Demo 3.2 — Exception handling, and reading a traceback · 30 min

**Goal.** The transferable skill here is reading tracebacks, not `try`/`except` syntax. Do that first.

**BREAK IT** — cause a real error and read it together:

```python
>>> int("abc")
Traceback (most recent call last):
  File "<stdin>", line 1, in <module>
ValueError: invalid literal for int() with base 10: 'abc'
```

**Read it bottom-up:**

1. **Last line first** — the exception type (`ValueError`) and the message.
2. **Then scan upward** for the topmost file that is *yours*, not Django's or Python's.
3. That is where to look.

**Now the control flow:**

```python
def read_year(text):
    try:
        year = int(text)
    except ValueError:
        print(f"'{text}' is not a number")
        return None
    else:
        print("Parsed cleanly")
        return year
    finally:
        print("This runs either way")
```

```python
>>> read_year("1965")
Parsed cleanly
This runs either way
1965
>>> read_year("abc")
'abc' is not a number
This runs either way
```

**The one rule:** catch the narrowest exception you can name.

```python
try:
    ...
except Exception:      # too wide — hides typos and bugs for weeks
    pass

except:                # worse — catches Ctrl+C, so you cannot stop the program
    pass
```

---

## Demo 3.3 — Modules and packages · 25 min

**Goal.** An import is a path on disk. A dot is a folder boundary; the last segment is a name inside a file.

**TYPE** — split the lab code into two files:

```bash
mkdir -p ~/code/importdemo/library
cd ~/code/importdemo
touch library/__init__.py
```

`library/utils.py`:

```python
def slugify(title):
    return title.lower().replace(" ", "-")

MAX_LOAN_DAYS = 14
```

`main.py`:

```python
from library.utils import slugify, MAX_LOAN_DAYS

print(slugify("Cloud Atlas"))     # cloud-atlas
print(MAX_LOAN_DAYS)              # 14
```

**TYPE:**

```bash
python3 main.py
```

**EXPECT:**

```
cloud-atlas
14
```

**Map it to disk, out loud:**

```
from library.utils import slugify
     └─ folder  └─ file  └─ name inside the file
```

**BREAK IT:**

```bash
mv library/__init__.py library/init.py
python3 main.py
```

**EXPECT** — on some setups this still works (implicit namespace packages), on others it fails. Either way, restore it and state the rule: *put `__init__.py` in every package folder; Django's `startapp` does it for you, and you will see the file in Session 4.*

```bash
mv library/init.py library/__init__.py
```

**Never do this:**

```python
from library.utils import *     # pulls in every name blindly, shadows your own
```

---

## Demo 3.4 — File handling · 20 min

**TYPE:**

```python
# write
with open("books.txt", "w", encoding="utf-8") as f:
    f.write("Dune\n")
    f.write("Emma\n")

# read
with open("books.txt", "r", encoding="utf-8") as f:
    for line in f:
        print(line.strip())
```

**EXPECT:**

```
Dune
Emma
```

**Two things to insist on:**

| Rule | Why |
| --- | --- |
| Always use `with` | The file is closed even if the code inside raises. No `close()` to forget. |
| Always pass `encoding="utf-8"` | The platform default differs between Windows and macOS, producing bugs that appear on exactly one student's laptop. |

**BREAK IT** — the destructive mode:

```python
>>> with open("books.txt", "w", encoding="utf-8") as f:
...     pass
...
>>> open("books.txt").read()
''
```

**Say:** `"w"` truncates the file the moment it opens, before a single write. `"a"` appends. Demonstrate the data loss once, on a throwaway file, and nobody forgets.

---

## Demo 3.5 — Virtual environments · 40 min

**Goal.** This is the most important demo in Session 3. Do not compress it.

**Set up the problem first.** Ask: *"Two projects on this laptop need two different Django versions. There is one system Python. What now?"*

**TYPE:**

```bash
cd ~/code
mkdir -p library
cd library
python3 -m venv venv
```

**Activate it — macOS and Linux:**

```bash
source venv/bin/activate
```

**Activate it — Windows PowerShell:**

```powershell
venv\Scripts\Activate.ps1
```

**Activate it — Windows cmd.exe:**

```
venv\Scripts\activate.bat
```

**EXPECT** — the shell prompt gains a prefix:

```
(venv) $
```

**Prove it worked:**

```bash
which python          # macOS / Linux
where python          # Windows
```

**EXPECT** — a path *inside your project*:

```
/Users/you/code/library/venv/bin/python
```

**Now install Django into this environment only:**

```bash
python -m pip install "django==5.2.*"
python -m django --version
```

**EXPECT:**

```
5.2.x
```

**Record the environment so it can be reproduced:**

```bash
python -m pip freeze > requirements.txt
cat requirements.txt
```

**EXPECT:**

```
asgiref==3.8.1
Django==5.2.x
sqlparse==0.5.x
```

**BREAK IT** — the error every student will hit at least once:

```bash
deactivate
python -m django --version
```

**EXPECT:**

```
No module named django
```

Reactivate and it works again.

> **`TRAINER`** — This is the single most common support ticket for the remaining 40 hours. Teach the tell, and make it a reflex: **before reading a single line of code, look at the prompt for `(venv)`.** If it is not there, that is the bug.

| Command | When |
| --- | --- |
| `python3 -m venv venv` | Once, per project |
| `source venv/bin/activate` | Every new terminal window |
| `python -m pip install X` | Installs into the active venv only |
| `python -m pip freeze > requirements.txt` | After adding a package |
| `python -m pip install -r requirements.txt` | On another machine |
| `deactivate` | Step back out |

**Never commit `venv/`.** It holds compiled binaries for one operating system and is often larger than the whole project. `requirements.txt` is the portable artefact.

---

## Demo 3.6 — Object-oriented programming preview · 25 min

**Goal.** Just enough to make Session 4 continuous rather than new. Three words: a **class** is a blueprint, an **object** is one thing built from it, and `self` is "this particular one".

**TYPE** — `~/code/library/oop_preview.py`:

```python
class Book:
    def __init__(self, title, year):    # runs when you create one
        self.title = title              # attribute: data on THIS object
        self.year = year

    def is_classic(self):               # method: behaviour
        return self.year < 1980

    def __str__(self):                  # how it prints
        return f"{self.title} ({self.year})"


dune = Book("Dune", 1965)
emma = Book("Emma", 1815)
road = Book("The Road", 2006)

print(dune)                  # Dune (1965)
print(dune.is_classic())     # True
print(road.is_classic())     # False
print(emma.title)            # Emma
```

**BREAK IT** — leave out `self`:

```python
class Book:
    def is_classic():        # no self
        return True

b = Book()
b.is_classic()
```

**EXPECT:**

```
TypeError: Book.is_classic() takes 0 positional arguments but 1 was given
```

> **`TRAINER`** — The "1" in that message *is* the object. Decoding this sentence now means they can decode it in Session 4 when it comes from a Django class.

**Now put the Django version on screen and stop talking:**

```python
# Session 6 — same shape
class Book(models.Model):
    title = models.CharField(max_length=200)
    year  = models.IntegerField()

    def __str__(self):
        return f"{self.title} ({self.year})"
```

**Say:** *"Identical shape. The only difference is that Django's version knows how to save itself to a database. That is Session 6."*

---

## Session 3 close

**CHECKPOINT 3 — this one is a gate. Nobody starts Session 4 without it.**

```bash
cd ~/code/library
source venv/bin/activate        # or venv\Scripts\Activate.ps1
python -m django --version      # 5.2.x
cat requirements.txt            # Django is listed
```

1. An activated venv with Django installed, proven on your own machine.
2. A `requirements.txt` in `~/code/library/`.
3. Correct container for: a shopping cart, GPS coordinates, the set of tags across a blog, a JSON response.
4. Read a traceback aloud and identify which line is *your* code.

\newpage

# Session 4 — OOP & Django Fundamentals

**Module 4 · 4 hours · builds on Sessions 2 and 3 · hard prerequisite for everything after**

This is the pivot session. By the end, every student has a running server answering their own URL with their own text. Protect the last 90 minutes.

> **`TRAINER`** — Also teach Demo 4.9 (Git) today. This is the first session where students own something worth losing, and the official Git module is ten sessions away.

---

## Demo 4.1 — Inheritance: why Django works at all · 25 min

**Goal.** Convert Django from magic into arithmetic.

**TYPE:**

```python
class Animal:
    def __init__(self, name):
        self.name = name

    def speak(self):
        return "..."

    def describe(self):
        return f"{self.name} says {self.speak()}"


class Dog(Animal):          # Dog IS AN Animal
    def speak(self):        # override just this one method
        return "Woof"


class Cat(Animal):
    def speak(self):
        return "Meow"


for pet in [Dog("Rex"), Cat("Tom"), Animal("Thing")]:
    print(pet.describe())
```

**EXPECT:**

```
Rex says Woof
Tom says Meow
Thing says ...
```

**Two things happened, and both have names:**

- **Inheritance** — `Dog` never defined `__init__` or `describe`, but has both.
- **Polymorphism** — one call site, `pet.describe()`, produced three different results. The caller never asked what type it was holding.

**Now the payoff.** Write this on the board:

```python
class Book(models.Model):
    title = models.CharField(max_length=200)
    year  = models.IntegerField()
```

**Ask:** *"Three lines. Where does `Book.objects.all()` come from? Where does `.save()` come from? Who wrote them?"*

**Say:** *"Nobody in this room. `models.Model` did — thousands of lines, tested by millions of deployments. Inheritance is the mechanism by which a framework gives you things. Every Django class you subclass this course — Model, Form, ListView, Serializer — is this same deal."*

---

## Demo 4.2 — Create the project · 20 min

**TYPE:**

```bash
cd ~/code/library
source venv/bin/activate          # ALWAYS. Check for (venv).
django-admin startproject config .
```

> The trailing dot means **here**. Without it you get `library/config/` nested one level deeper and everyone loses track of which folder they are in.

**TYPE:**

```bash
ls -la
```

**EXPECT:**

```
config/
manage.py
requirements.txt
venv/
```

**TYPE:**

```bash
python manage.py runserver
```

**EXPECT:**

```
Watching for file changes with StatReloader
Performing system checks...

System check identified no issues (0 silenced).

You have 18 unapplied migration(s). Your project may not work properly
until you apply the migrations for app(s): admin, auth, contenttypes, sessions.
Run 'python manage.py migrate' to apply them.

Django version 5.2.x, using settings 'config.settings'
Starting development server at http://127.0.0.1:8000/
Quit the server with CONTROL-C.
```

Open <http://127.0.0.1:8000/>.

**EXPECT** — the rocket page: *"The install worked successfully! Congratulations!"*

> **`TRAINER`** — Celebrate this. It is the first visible win of the course. Then point at the unapplied-migrations warning and say: *"That is not an error, and we will fix it in Session 6. Ignore it for now."*

**Now tour every generated file.** Students who never got the tour spend the rest of the course afraid of `settings.py`.

| File | What it is for | How often you edit it |
| --- | --- | --- |
| `manage.py` | Your entry point for every command | Never |
| `config/settings.py` | Database, installed apps, templates, static, secrets | Often |
| `config/urls.py` | The front door — routes requests to apps | Often |
| `config/wsgi.py` / `asgi.py` | How a production server starts your app | At deployment |
| `config/__init__.py` | Marks the folder importable — Demo 3.3 | Never |

---

## Demo 4.3 — Create an app, and register it · 15 min

**Say the difference first.** A **project** is configuration and assembly. An **app** is a self-contained feature area that could, in principle, be lifted out and dropped into a different project. The test is portability: *could I hand this app to another team?*

**TYPE** — stop the server with **Ctrl**+**C** first:

```bash
python manage.py startapp catalog
ls catalog
```

**EXPECT:**

```
__init__.py  admin.py  apps.py  migrations  models.py  tests.py  views.py
```

> Two files are conspicuously **absent**: `urls.py` and a `templates/` folder. Django does not create them, and students assume that means they are not allowed to. Say out loud that you create both by hand, every time.

**Now register the app** in `config/settings.py`:

```python
INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "catalog",                      # <-- yours
]
```

> **`TRAINER`** — Point at the six that came free and name what each does: admin (Session 6), auth (Module 9), sessions (Module 9), staticfiles (Session 5). That is the "batteries included" claim from Session 1, made concrete.

**BREAK IT** — leave `catalog` out and templates will not be found in Session 5, models will be invisible to migrations in Session 6, and none of the error messages will mention the real cause. Make it a two-step ritual: **`startapp` is not finished until the app is in `INSTALLED_APPS`.**

---

## Demo 4.4 — Your first view · 20 min

**TYPE** — `catalog/views.py`:

```python
from django.http import HttpResponse


def book_list(request):
    return HttpResponse("<h1>All books</h1>")
```

**TYPE** — create `catalog/urls.py` **by hand**:

```python
from django.urls import path

from . import views

urlpatterns = [
    path("books/", views.book_list, name="book-list"),
]
```

**TYPE** — wire the app into `config/urls.py`:

```python
from django.contrib import admin
from django.urls import include, path

urlpatterns = [
    path("admin/", admin.site.urls),
    path("catalog/", include("catalog.urls")),
]
```

**TYPE:**

```bash
python manage.py runserver
```

Open <http://127.0.0.1:8000/catalog/books/>.

**EXPECT** — a page reading **All books**.

**CHECKPOINT 4a** — every student sees their own text at their own URL. Do not move on until this is true for everyone.

---

## Demo 4.5 — How the URL was resolved · 20 min

**Goal.** The two things students consistently miss.

Trace the path `/catalog/books/` out loud, pointing at the files:

| Step | File | What happens |
| --- | --- | --- |
| 1 | `config/urls.py` | Patterns are tried **top to bottom**. `admin/` does not match. |
| 2 | `config/urls.py` | `catalog/` matches. `include()` **strips the matched prefix**. |
| 3 | — | The remainder handed on is `books/` — *not* the full path. |
| 4 | `catalog/urls.py` | `books/` matches. `views.book_list` is called. |

**BREAK IT** — the double-prefix bug. Change `catalog/urls.py` to:

```python
path("catalog/books/", views.book_list, name="book-list"),
```

Reload <http://127.0.0.1:8000/catalog/books/>.

**EXPECT** — a yellow debug page, and the useful part is the list:

```
Using the URLconf defined in config.urls, Django tried these URL patterns,
in this order:

  1. admin/
  2. catalog/ catalog/books/ [name='book-list']

The current path, catalog/books/, didn't match any of these.
```

> **`TRAINER`** — Teaching them to read that list is teaching them to never need you for a 404 again. The real URL became `/catalog/catalog/books/`. Undo the change.

---

## Demo 4.6 — Capturing a value from the URL · 20 min

**TYPE** — add to `catalog/views.py`:

```python
def book_detail(request, pk):
    return HttpResponse(f"<h1>Book number {pk}</h1>")
```

**TYPE** — add to `catalog/urls.py`:

```python
urlpatterns = [
    path("books/", views.book_list, name="book-list"),
    path("books/<int:pk>/", views.book_detail, name="book-detail"),
]
```

Open <http://127.0.0.1:8000/catalog/books/12/>.

**EXPECT** — **Book number 12**

**The path converters:**

| Converter | Matches | Arrives as | Use for |
| --- | --- | --- | --- |
| `<int:pk>` | digits | `int` | primary keys — the default choice |
| `<str:name>` | any text except `/` | `str` | usernames, short labels |
| `<slug:slug>` | letters, digits, hyphen, underscore | `str` | readable URLs: `/books/dune-1965/` |
| `<uuid:id>` | a formatted UUID | `UUID` | when ids must not be guessable |
| `<path:rest>` | any text **including** `/` | `str` | rare, greedy — put it last |

**BREAK IT** — rename the view's parameter while the URL still says `pk`:

```python
def book_detail(request, id):      # was pk
```

**EXPECT:**

```
TypeError: book_detail() got an unexpected keyword argument 'pk'
```

**Say:** The converter's name and the parameter name must match exactly. Undo it.

---

## Demo 4.7 — The MVT cycle · 20 min

Draw this on the board and have a student redraw it from memory. Every debugging conversation for the rest of the course starts with *"which box are we in?"*

```
                                    ┌──────────────┐
   request ──> middleware ──> urls.py ──> │  THE VIEW    │ ──> models.py ──> database
   GET /books/12/                         │              │ <──   one row  <──
                                          │ the only     │
                                          │ place a      │
                                          │ decision is  │
                                          │ made         │
                                          └──────┬───────┘
                                                 │ context = {"book": book}
                                                 ↓
                                          ┌──────────────┐
   response <── middleware <───────────── │ THE TEMPLATE │
   200 OK, text/html                      │ fills blanks │
                                          └──────────────┘
```

**Two sentences to repeat all course:**

1. **The view is the only place a decision gets made.** If your template contains a decision, or your model contains a redirect, you are in the wrong box.
2. Other frameworks call this MVC. Django's *view* is MVC's controller; Django's *template* is MVC's view. The names differ, the boxes do not. Do not spend ten minutes on this.

**The debugging protocol — put it on the wall:**

| Symptom | Box | Open this file first |
| --- | --- | --- |
| 404 | routing | `urls.py` |
| 500 | logic | `views.py` |
| Blank page | rendering | the template, or a missing `return` |
| Wrong data | data | `models.py`, or the query in the view |

---

## Demo 4.8 — Two deliberate errors · 15 min

**BREAK IT 1** — delete the `return`:

```python
def book_list(request):
    HttpResponse("<h1>All books</h1>")     # no return
```

**EXPECT:**

```
ValueError: The view catalog.views.book_list didn't return an HttpResponse
object. It returned None instead.
```

**Say:** *"That is Session 2, Demo 2.5. `return` versus `print`. Same bug, new costume."*

**BREAK IT 2** — return a plain string:

```python
def book_list(request):
    return "<h1>All books</h1>"
```

**EXPECT:**

```
AttributeError: 'str' object has no attribute 'get'
```

**Say:** Every view must return a **response object**, always. Restore the working version.

---

## Demo 4.9 — Git, ten sessions early · 25 min

> **`TRAINER`** — The syllabus places Git at Module 14. That leaves students with 52 hours of unbacked work. Teach these five commands today; the official module then covers branching and pull requests on people who already have muscle memory.

**TYPE** — write the ignore file **first**, before `git add`:

`~/code/library/.gitignore`

```gitignore
# environments
venv/
.venv/

# python artefacts
__pycache__/
*.py[cod]

# secrets
.env

# the database and user uploads
db.sqlite3
db.sqlite3-journal
media/

# collected static
staticfiles/

# editor and OS noise
.vscode/
.idea/
.DS_Store
```

**TYPE:**

```bash
cd ~/code/library
git init
git status
```

**EXPECT** — a short, clean list. `venv/` must **not** appear. If it does, the `.gitignore` is in the wrong folder.

```bash
git config user.name  "Your Name"
git config user.email "you@example.com"

git add .
git commit -m "Session 4: Django project with catalog app and first URLs"
git log --oneline
```

**Commit message standard**, enforced from today:

| Good | Bad |
| --- | --- |
| `Add Book and Author models` | `update` |
| `Fix double-prefix bug in catalog URLs` | `fixed stuff` |
| `Wire catalog app into project URLs` | `asdf`, `final v2` |

The test: *could a teammate read your log and understand what happened this week without opening a single file?*

**Tag the checkpoint** so students who fall behind can catch up:

```bash
git tag session-4-complete
```

---

## Lab 4.10 — Three URLs of your own · 30 min

Every student adds three more working URLs to their `catalog` app:

1. `/catalog/authors/` — returns "All authors"
2. `/catalog/authors/<int:pk>/` — returns "Author number N"
3. `/catalog/about/` — returns a short paragraph of HTML about the library

Each one needs a view function, a `path()` entry with a `name=`, and a verified page in the browser.

---

## Session 4 close

**CHECKPOINT 4 — nobody leaves without these:**

1. `runserver` running with no errors.
2. Your own URL returning your own text.
3. A second URL that captures a number and shows it back.
4. Point at the four MVT boxes and say what each one does.
5. A first commit pushed, and `git status` clean.

**Common failures, in order of likelihood:**

| Symptom | Cause |
| --- | --- |
| `ModuleNotFoundError: No module named 'django'` | venv not activated — check the prompt |
| App's templates or models invisible | app missing from `INSTALLED_APPS` |
| 404 on a URL you just added | double prefix, or missing trailing slash |
| `view must be a callable` | you passed `views.book_list()` with parentheses |
| Changes not taking effect | the server needs a restart after some edits |

\newpage

# Session 5 — Templates & Static Files

**Module 5 · 4 hours · builds on Session 4**

The rule for the whole session: **the template language is deliberately weak.** It can fill in blanks, loop, and branch. That is all. Every time a student wants something a template cannot do, the answer is the same — *compute it in the view and pass the result in.*

---

## Demo 5.1 — From `HttpResponse` to a real template · 25 min

**TYPE** — create the folders. The repeated app name is not a typo:

```bash
cd ~/code/library
mkdir -p catalog/templates/catalog
```

**Why the repetition?** Every app's `templates/` folder is merged into one shared pool. The inner `catalog/` folder is a namespace that stops your `book_list.html` colliding with another app's. Say this now; it is the most confusing convention in Django.

**TYPE** — `catalog/templates/catalog/book_list.html`:

```html
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <title>All books</title>
</head>
<body>
  <h1>All books</h1>
  <ul>
    <li>Dune</li>
    <li>Emma</li>
  </ul>
</body>
</html>
```

**TYPE** — `catalog/views.py`:

```python
from django.shortcuts import render


def book_list(request):
    return render(request, "catalog/book_list.html")
```

Reload <http://127.0.0.1:8000/catalog/books/>.

**EXPECT** — the same page, now served from a real HTML file.

**BREAK IT** — misspell the template name:

```python
return render(request, "catalog/book_lst.html")
```

**EXPECT** — `TemplateDoesNotExist at /catalog/books/`, and below it the genuinely useful part:

```
Template-loader postmortem
Django tried loading these templates, in this order:

Using engine django:
  * django.template.loaders.filesystem.Loader: /Users/you/code/library/templates/catalog/book_lst.html (Source does not exist)
  * django.template.loaders.app_directories.Loader: /Users/you/code/library/catalog/templates/catalog/book_lst.html (Source does not exist)
```

> **`TRAINER`** — Read that list aloud. It shows every path Django tried, in order. Three causes cover almost every occurrence: app missing from `INSTALLED_APPS`, missing namespace folder, or a typo. Undo the typo.

---

## Demo 5.2 — Passing data to the template · 30 min

**Goal.** The context is a dictionary — which is why Session 3 gave dictionaries the star billing. Everything the template can see arrived in that dict, and nothing else exists.

**TYPE** — `catalog/views.py`:

```python
from django.shortcuts import render


def book_list(request):
    books = ["Dune", "Emma", "It"]
    context = {
        "page_title": "All books",
        "books": books,
        "total": len(books),        # compute HERE, not in the template
    }
    return render(request, "catalog/book_list.html", context)
```

**TYPE** — `catalog/templates/catalog/book_list.html`:

```html
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <title>{{ page_title }}</title>
</head>
<body>
  <h1>{{ page_title }} ({{ total }})</h1>

  <ul>
  {% for book in books %}
    <li>{{ forloop.counter }}. {{ book|upper }}</li>
  {% empty %}
    <li>No books yet.</li>
  {% endfor %}
  </ul>
</body>
</html>
```

**EXPECT:**

```
All books (3)
  1. DUNE
  2. EMMA
  3. IT
```

**The three pieces of syntax — that is the entire language:**

- `{{ ... }}` — **output a value.** `{{ book.title }}`. Dots walk attributes, dictionary keys and list indexes.
- `{% ... %}` — **run a tag.** `{% for %}`, `{% if %}`, `{% extends %}`. Every block tag needs its `{% end... %}`.
- A pipe character — **apply a filter**, transforming the value on its way out: `{{ title|upper }}`, `{{ price|floatformat:2 }}`.

**BREAK IT** — the silent failure. Add this line:

```html
<p>{{ page_titel }}</p>
```

**EXPECT** — nothing. No error, no warning, an empty paragraph.

> **`TRAINER`** — This design choice is deliberate: a missing value should not take down a page. But it means typo'd variable names are annoying to find. Say: *"When a variable renders as empty, the question is never 'what's wrong with the template'. It is 'was that key actually in the dict?'"*

**Show `{% empty %}` working** by setting `books = []` in the view. It replaces the "if the list is empty" wrapper students would otherwise write.

**Useful filters:**

```django
{{ published|date:"j M Y" }}      {# formats a date                    #}
{{ bio|default:"—" }}             {# substitutes for empty values       #}
{{ books|length }}                {# counts                             #}
{{ blurb|truncatewords:20 }}      {# shortens text                      #}
{{ price|floatformat:2 }}         {# fixes decimal places               #}
{{ n }} book{{ n|pluralize }}     {# adds "s" only when needed          #}
{{ notes|linebreaks }}            {# newlines become paragraphs         #}
```

Filters chain left to right: `{{ blurb|default:"No description"|truncatewords:20 }}`.

---

## Demo 5.3 — Autoescaping, and why it protects you · 15 min

**TYPE** — in the view, make one of the "titles" hostile:

```python
books = ["Dune", "<script>alert('xss')</script>", "It"]
```

Reload.

**EXPECT** — the script tag appears as **visible text** on the page. No alert box.

**View source** and you will see Django escaped it:

```html
<li>2. &LT;SCRIPT&GT;ALERT(&#X27;XSS&#X27;)&LT;/SCRIPT&GT;</li>
```

**Now turn the protection off:**

```html
<li>{{ book|safe }}</li>
```

**EXPECT** — the alert box fires.

> **`TRAINER`** — The lesson, stated precisely: **`|safe` is a promise you are making about that data.** You may only make it about markup you generated yourself, never about anything a user typed. Remove `|safe` and the hostile string before moving on.

---

## Demo 5.4 — Template inheritance · 40 min

**Goal.** Build it in the right order — write a second page first, notice the duplication, *then* extract the base. Refactoring toward inheritance in front of them teaches why it exists.

**TYPE** — first add a second page so the duplication is real. `catalog/views.py`:

```python
def about(request):
    return render(request, "catalog/about.html")
```

`catalog/urls.py`:

```python
path("about/", views.about, name="about"),
```

`catalog/templates/catalog/about.html` — copy the whole of `book_list.html` and change the body. Now point at the two files: the `<html>`, `<head>`, `<title>` and any nav are identical.

**Now extract it.** `catalog/templates/catalog/base.html`:

```html
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>{% block title %}Library{% endblock title %}</title>
</head>
<body>
  <nav>
    <a href="{% url 'book-list' %}">Books</a>
    <a href="{% url 'about' %}">About</a>
  </nav>

  <main>
    {% block content %}{% endblock content %}
  </main>

  <footer>Library Catalogue &middot; built in class</footer>
</body>
</html>
```

**Rewrite** `catalog/templates/catalog/book_list.html` entirely:

```html
{% extends "catalog/base.html" %}

{% block title %}{{ page_title }}{% endblock title %}

{% block content %}
  <h1>{{ page_title }} ({{ total }})</h1>
  <ul>
  {% for book in books %}
    <li>{{ forloop.counter }}. {{ book }}</li>
  {% empty %}
    <li>No books yet.</li>
  {% endfor %}
  </ul>
{% endblock content %}
```

**And** `catalog/templates/catalog/about.html`:

```html
{% extends "catalog/base.html" %}

{% block title %}About{% endblock title %}

{% block content %}
  <h1>About this library</h1>
  <p>A small catalogue built during the Django course.</p>
{% endblock content %}
```

**EXPECT** — both pages now carry the same nav and footer, and the child files contain no `<html>` or `<head>` at all.

**Three rules, in the order they cause problems:**

| Rule | What happens if you break it |
| --- | --- |
| `{% extends %}` must be the **first** template tag in the file | `TemplateSyntaxError` |
| Content **outside** a block is silently discarded | Nothing renders, no error at all |
| The block name must exist in the parent | Same — silence |

**BREAK IT** — put a stray `<p>hello</p>` between the two blocks in `about.html`. It does not appear. Delete it.

**Note `{% url 'book-list' %}`** in the nav. That is why every `path()` got a `name=` in Session 4. Hard-coding `/catalog/books/` works today and breaks silently the day you change a prefix.

---

## Demo 5.5 — Static files: CSS and JavaScript · 30 min

**TYPE:**

```bash
cd ~/code/library
mkdir -p catalog/static/catalog
```

`catalog/static/catalog/style.css`:

```css
:root { --ink: #14201c; --accent: #0b6b4a; --line: #dce4df; }

* { box-sizing: border-box; }

body {
  margin: 0;
  font: 16px/1.6 system-ui, -apple-system, "Segoe UI", sans-serif;
  color: var(--ink);
}

nav {
  display: flex;
  gap: 20px;
  padding: 16px 24px;
  border-bottom: 1px solid var(--line);
}

nav a { color: var(--accent); text-decoration: none; font-weight: 600; }
nav a:hover { text-decoration: underline; }

main { max-width: 720px; margin: 0 auto; padding: 32px 24px; }

h1 { font-size: 1.8rem; letter-spacing: -0.02em; }

ul { padding-left: 1.2em; }
li { margin: 6px 0; }

footer {
  border-top: 1px solid var(--line);
  padding: 16px 24px;
  font-size: 0.85rem;
  color: #667;
}
```

`catalog/static/catalog/app.js`:

```javascript
console.log("Library catalogue loaded");
```

**TYPE** — wire them into `catalog/templates/catalog/base.html`. The `{% load static %}` line must be the **first** line of the file:

```html
{% load static %}
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>{% block title %}Library{% endblock title %}</title>
  <link rel="stylesheet" href="{% static 'catalog/style.css' %}">
</head>
<body>
  <nav>
    <a href="{% url 'book-list' %}">Books</a>
    <a href="{% url 'about' %}">About</a>
  </nav>

  <main>
    {% block content %}{% endblock content %}
  </main>

  <footer>Library Catalogue &middot; built in class</footer>

  <script src="{% static 'catalog/app.js' %}"></script>
</body>
</html>
```

**EXPECT** — a styled page. **Prove it loaded:** DevTools → Network → filter CSS. Status **200**. Console shows *Library catalogue loaded*.

**BREAK IT** — delete the `{% load static %}` line:

**EXPECT:**

```
TemplateSyntaxError: Invalid block tag on line 6: 'static'.
Did you forget to register or load this tag?
```

> **`TRAINER`** — Loads are **not** inherited. Every template file that uses `{% static %}` must load it itself, including children of a base that already did. Restore the line.

**Two things students always ask:**

- *Why not just write `/static/catalog/style.css`?* Because `{% static %}` asks the framework where the file actually is, which is what makes hashed cache-busting filenames and a CDN possible later without editing a single template.
- *Why is the `<script>` at the end of `<body>`?* So the HTML exists by the time the script runs.

---

## Demo 5.6 — Reusable partials with `{% include %}` · 20 min

**`extends` and `include` are not interchangeable:**

| Tag | Direction | Use for | How often per page |
| --- | --- | --- | --- |
| `{% extends %}` | your page goes **inside** a shell | the site-wide layout | once |
| `{% include %}` | a fragment goes **into** your page | cards, form rows, nav items | as often as you like |

**TYPE** — `catalog/templates/catalog/_book_card.html`. The leading underscore is a convention marking it as a fragment, not a page:

```html
<li class="card">
  <strong>{{ book }}</strong>
</li>
```

**Use it** in `book_list.html`:

```html
{% for book in books %}
  {% include "catalog/_book_card.html" with book=book only %}
{% empty %}
  <li>No books yet.</li>
{% endfor %}
```

**Say:** the `only` keyword stops the partial silently depending on whatever else happens to be in the context — which makes it genuinely reusable.

---

## Lab 5.7 — Style your own pages · 35 min

1. Add a third page — `/catalog/authors/` — using `{% extends %}`.
2. Give the nav a highlighted "current page" style.
3. Add one `{% include %}` partial used on at least two pages.
4. Make the page readable on a phone-width window.

---

## Session 5 close

```bash
git add .
git commit -m "Session 5: base template, static CSS/JS, reusable partials"
git tag session-5-complete
```

**CHECKPOINT 5 — every student can:**

1. Show a `base.html` with a nav, plus two child pages that share it.
2. Show a stylesheet loading with a **200** in the Network tab.
3. Show a list rendered with `{% for %}` that says something sensible when empty.
4. Explain why the template folder is `templates/catalog/` and not just `templates/`.

\newpage

# Session 6 — Models & the Database

**Module 6 · 4 hours · builds on Session 4 · hard prerequisite for Session 7 onward**

**The one idea:** a model class is a **table**, an instance is a **row**, an attribute is a **column**.

---

## Demo 6.1 — Your first models · 35 min

**TYPE** — `catalog/models.py`:

```python
from django.db import models


class Author(models.Model):
    name = models.CharField(max_length=120)
    bio = models.TextField(blank=True)          # optional TEXT: blank only

    def __str__(self):
        return self.name


class Book(models.Model):
    title = models.CharField(max_length=200)
    year = models.IntegerField()
    price = models.DecimalField(max_digits=8, decimal_places=2)
    published = models.DateField(null=True, blank=True)   # optional DATE: both
    added_on = models.DateTimeField(auto_now_add=True)    # set once, at creation

    class Meta:
        ordering = ["-year", "title"]

    def __str__(self):
        return f"{self.title} ({self.year})"
```

**`null` versus `blank` — the pair everyone gets wrong:**

| | `blank=False` | `blank=True` |
| --- | --- | --- |
| **`null=False`** | the default: required everywhere | **correct for optional TEXT** — stores `""` |
| **`null=True`** | almost never what you want | **correct for optional DATES, NUMBERS, FKs** |

- `null` controls whether the **database** column accepts `NULL`.
- `blank` controls whether a **form** accepts an empty value.

**Never use `null=True` on a `CharField` or `TextField`** — you would then have two kinds of empty (`""` and `NULL`) to test for in every query and every template, for no benefit.

**Field choices that matter:**

| Need | Use | Never use | Why |
| --- | --- | --- | --- |
| Short text | `CharField(max_length=…)` | `TextField` | `max_length` gives free validation |
| Long text | `TextField()` | — | renders as a textarea |
| **Money** | `DecimalField(max_digits, decimal_places)` | **`FloatField`** | floats lose cents |
| Created timestamp | `DateTimeField(auto_now_add=True)` | `auto_now` | set once |
| Updated timestamp | `DateTimeField(auto_now=True)` | `auto_now_add` | rewritten on every save |

**Prove the money point:**

```python
>>> 0.1 + 0.2
0.30000000000000004
```

---

## Demo 6.2 — Migrations: the three states · 40 min

**Goal.** This is the highest-value demo in Session 6. There are **three separate things** that can disagree with each other, and every migration command moves information between them:

```
  1. models.py           2. migrations/          3. the database
  what you WANT     ──>  the ordered history ──> actual tables
  (you edit this)        (Django writes it)      + django_migrations
                                                   (which records what ran)
       └──── makemigrations ────┘  └──── migrate ────┘
```

**TYPE:**

```bash
python manage.py makemigrations
```

**EXPECT:**

```
Migrations for 'catalog':
  catalog/migrations/0001_initial.py
    + Create model Author
    + Create model Book
```

**Now OPEN that file.** It is ordinary Python — `CreateModel`, `AddField`, `AlterField`. Not magic.

**TYPE** — the thirty most valuable seconds in the module:

```bash
python manage.py sqlmigrate catalog 0001
```

**EXPECT:**

```sql
BEGIN;
--
-- Create model Author
--
CREATE TABLE "catalog_author" (
    "id" integer NOT NULL PRIMARY KEY AUTOINCREMENT,
    "name" varchar(120) NOT NULL,
    "bio" text NOT NULL
);
--
-- Create model Book
--
CREATE TABLE "catalog_book" (
    "id" integer NOT NULL PRIMARY KEY AUTOINCREMENT,
    "title" varchar(200) NOT NULL,
    "year" integer NOT NULL,
    "price" decimal NOT NULL,
    "published" date NULL,
    "added_on" datetime NOT NULL
);
COMMIT;
```

> **`TRAINER`** — Read it aloud. Point at three things: the `id` column nobody asked for (the primary key), the table name `catalog_book` (app label + model name), and `"published" date NULL` versus `"year" integer NOT NULL` — that is `null=True` made visible.

**TYPE:**

```bash
python manage.py migrate
```

**EXPECT** — all 18 built-in migrations plus yours:

```
Operations to perform:
  Apply all migrations: admin, auth, catalog, contenttypes, sessions
Running migrations:
  Applying contenttypes.0001_initial... OK
  ...
  Applying catalog.0001_initial... OK
  Applying sessions.0001_initial... OK
```

**TYPE:**

```bash
python manage.py showmigrations catalog
```

**EXPECT:**

```
catalog
 [X] 0001_initial
```

**Now demonstrate the gap that causes "no such column".** Add a field to `Book`:

```python
isbn = models.CharField(max_length=13, blank=True)
```

```bash
python manage.py makemigrations
python manage.py showmigrations catalog
```

**EXPECT:**

```
catalog
 [X] 0001_initial
 [ ] 0002_book_isbn        <-- written but NOT applied
```

Visit any page that touches `Book` and you will get `OperationalError: no such column`. Then:

```bash
python manage.py migrate
```

**BREAK IT** — the prompt everyone panics at. Add a **non-nullable** field with no default:

```python
pages = models.IntegerField()
```

```bash
python manage.py makemigrations
```

**EXPECT:**

```
It is impossible to add a non-nullable field 'pages' to book without
specifying a default. This is because the database needs something to
populate existing rows.
Please select a fix:
 1) Provide a one-off default now
 2) Quit and manually define a default in models.py
Select an option:
```

**Say:** *"This is Django being careful, not Django failing."* Choose option **2**.

Then **delete the `pages` line entirely** — it was only a demonstration, and leaving it would add a migration that the rest of this document does not expect. In a real project you would instead give it `default=0` or `null=True` and re-run `makemigrations`.

> **`TRAINER`** — State the two forbidden acts plainly, because both are permanently damaging:
>
> - **Never delete a migration file that has already been applied.** The database still remembers it in `django_migrations`, so the two now disagree forever.
> - **Never edit an applied migration.** To undo, migrate *backwards* to an earlier number, then make a new one forwards:
>
> ```bash
> python manage.py migrate catalog 0001    # backwards to 0001
> ```
>
> **Migration files are source code. Commit them.**

---

## Demo 6.3 — SQLite is one file · 15 min

**TYPE:**

```bash
ls -lh db.sqlite3
```

That is the whole database. Open it in the VS Code SQLite extension, or in [DB Browser for SQLite](https://sqlitebrowser.org/).

**Point at the tables Django created:**

| Table | Where it came from |
| --- | --- |
| `catalog_author`, `catalog_book` | your models |
| `auth_user`, `auth_group`, `auth_permission` | `django.contrib.auth` |
| `django_session` | `django.contrib.sessions` |
| `django_migrations` | the record of which migrations have run |

**Open `django_migrations`** and show the rows. Once students see that the database itself remembers, "why did it say *No changes detected*?" answers itself — and deleting migration files stops looking like a fix.

**Two things to say now, not later:**

- **`db.sqlite3` does not belong in Git.** It is generated, binary, unmergeable, and will eventually hold real user data. It is already in your `.gitignore` from Session 4.
- **Deleting it is a legitimate reset — for now.** When a local database is hopelessly tangled in week two, `rm db.sqlite3 && python manage.py migrate` is a fine recovery. Say clearly that this stops being acceptable the moment real data exists, which is the honest reason migrations matter at all.

---

## Demo 6.4 — CRUD in the shell · 45 min

**TYPE:**

```bash
python manage.py shell
```

**Then, live, with the class calling out what to try next:**

```python
>>> from catalog.models import Author, Book

# ---- CREATE ----
>>> herbert = Author.objects.create(name="Frank Herbert")
>>> herbert
<Author: Frank Herbert>

>>> Book.objects.create(title="Dune", year=1965, price="9.99")
<Book: Dune (1965)>

>>> b = Book(title="Emma", year=1815, price="5.50")
>>> b.save()                      # the two-step form

# ---- READ ----
>>> Book.objects.all()
<QuerySet [<Book: Emma (1815)>, <Book: Dune (1965)>]>
>>> Book.objects.count()
2
>>> Book.objects.get(pk=1)        # exactly one, or an exception
<Book: Dune (1965)>
>>> Book.objects.filter(year__gt=1900)     # a set, possibly empty
<QuerySet [<Book: Dune (1965)>]>
>>> Book.objects.first()
<Book: Emma (1815)>
```

> Notice the ordering: `Emma` comes first because `Meta.ordering = ["-year", "title"]` sorts by year descending... which puts 1965 before 1815. If that surprises you, read the minus sign again — and this is exactly why you check.

**The move that removes the magic:**

```python
>>> print(Book.objects.filter(year__gt=1900).query)
SELECT "catalog_book"."id", "catalog_book"."title", "catalog_book"."year",
       "catalog_book"."price", "catalog_book"."published", "catalog_book"."added_on"
FROM "catalog_book" WHERE "catalog_book"."year" > 1900
ORDER BY "catalog_book"."year" DESC, "catalog_book"."title" ASC
```

```python
# ---- UPDATE ----
>>> b = Book.objects.get(pk=1)
>>> b.year = 1966
>>> b.save()                      # forget this line and NOTHING happens

>>> Book.objects.filter(year=1966).update(year=1965)    # bulk, one statement
1

# ---- DELETE ----
>>> emma = Book.objects.get(title="Emma")
>>> emma.delete()
(1, {'catalog.Book': 1})          # it tells you what it removed
```

**`get()` versus `filter()` — hammer this:**

```python
>>> Book.objects.get(pk=999)
catalog.models.Book.DoesNotExist: Book matching query does not exist.

>>> Book.objects.filter(pk=999)
<QuerySet []>                     # empty, no exception

>>> Book.objects.filter(pk=999).first()
                                  # None
```

| Method | Promises | Raises |
| --- | --- | --- |
| `get()` | exactly one | `DoesNotExist`, `MultipleObjectsReturned` |
| `filter()` | zero or more | never |

**In a view, a missing row is a 404, not a 500:**

```python
from django.shortcuts import get_object_or_404

def book_detail(request, pk):
    book = get_object_or_404(Book, pk=pk)
    return render(request, "catalog/book_detail.html", {"book": book})
```

Exit the shell with **Ctrl**+**D**.

**Now wire real data into the page** — `catalog/views.py`:

```python
from django.shortcuts import get_object_or_404, render

from .models import Book


def book_list(request):
    books = Book.objects.all()
    return render(request, "catalog/book_list.html", {
        "page_title": "All books",
        "books": books,
        "total": books.count(),
    })
```

And in `book_list.html` the loop now yields objects, not strings:

```html
{% for book in books %}
  <li>{{ book.title }} — {{ book.year }} — Rs {{ book.price }}</li>
{% empty %}
  <li>No books yet.</li>
{% endfor %}
```

---

## Demo 6.5 — The admin panel · 35 min

**TYPE:**

```bash
python manage.py createsuperuser
```

Answer the prompts. **EXPECT** — `Superuser created successfully.`

> **`TRAINER`** — Forgetting this command locks students out of `/admin/` with no error that explains why. Put it on the board.

**TYPE** — `catalog/admin.py`. Do the **bare** version first, deliberately:

```python
from django.contrib import admin

from .models import Author, Book

admin.site.register(Author)
admin.site.register(Book)
```

Log in at <http://127.0.0.1:8000/admin/> and look at the Book list.

**EXPECT** — a usable but plain list showing `__str__` for each row.

**BREAK IT** — comment out `__str__` on `Book`, reload:

**EXPECT** — every row reads `Book object (1)`, `Book object (2)`. Useless. Restore `__str__` and make it part of the definition of "finished model".

**Now configure it properly:**

```python
from django.contrib import admin

from .models import Author, Book


@admin.register(Author)
class AuthorAdmin(admin.ModelAdmin):
    list_display = ("name",)
    search_fields = ("name",)


@admin.register(Book)
class BookAdmin(admin.ModelAdmin):
    list_display = ("title", "year", "price", "added_on")
    list_filter = ("year",)
    search_fields = ("title",)
    ordering = ("-year",)
    list_per_page = 25
```

**EXPECT** — the same data, now with sortable columns, a sidebar filter and a search box.

**Two honest sentences about the admin:**

- **It is for staff, not for users.** Never ship it as the customer-facing interface — students will try, because it is free and it works.
- **It is the fastest way to get test data.** For the rest of the course, when you need twenty books to test a list page, this is how.

**Add ten books through the admin now.** Every later demo needs data.

---

## Session 6 close

```bash
git add .
git commit -m "Session 6: Author and Book models, migrations, admin, real data in views"
git tag session-6-complete
```

**CHECKPOINT 6 — this is a gate for Session 7:**

1. Two models of your own, migrated, both with `__str__`.
2. Ten rows created through the admin, and the same rows listed on your own page.
3. Show me the SQL your first migration generated.
4. Explain `makemigrations` versus `migrate` in one sentence each.
5. When would you use `blank=True` *without* `null=True`?

**Common failures:**

| Symptom | Cause |
| --- | --- |
| `No changes detected` | app missing from `INSTALLED_APPS`, or wrong directory |
| `no such table` / `no such column` | a migration was written but never applied |
| `Book object (7)` everywhere | no `__str__` |
| Attribute changed but the row did not | forgot `.save()` |
| Locked out of `/admin/` | never ran `createsuperuser` |

\newpage

# Session 7 — ORM & Relationships

**Module 7 · 4 hours · builds on Session 6 · the hardest session in the course**

**The one idea:** a relationship is **a column that holds another table's id**. Once students can point at where the id physically lives, three concepts become one concept with three arrangements.

> **`TRAINER`** — Teach them in the order **one-to-many → many-to-many → one-to-one**, not the syllabus's order. One-to-many is the common case; one-to-one only makes sense as a constrained version of it. Keep the SQLite viewer open the whole session: every claim you make should be visible as a real column or a real table.

---

## Demo 7.1 — QuerySets are lazy · 30 min

**Goal.** A QuerySet does not touch the database when you create it.

**TYPE:**

```bash
python manage.py shell
```

```python
>>> from catalog.models import Book
>>> qs = Book.objects.all()                    # no SQL yet
>>> qs = qs.filter(year__gt=1900)              # still no SQL
>>> qs = qs.exclude(price=0)                   # still nothing
>>> qs = qs.order_by("title")                  # still nothing
>>> print(qs.query)                            # look, but do not run
SELECT ... FROM "catalog_book" WHERE ("catalog_book"."year" > 1900
AND NOT ("catalog_book"."price" = 0)) ORDER BY "catalog_book"."title" ASC
```

**One combined query is waiting.** It runs the moment something needs the actual rows:

```python
>>> for b in qs:          # <-- NOW the SQL runs, once
...     print(b)
```

| Triggers evaluation | Stays lazy |
| --- | --- |
| iterating in a `for` loop | `.filter()` `.exclude()` `.order_by()` |
| `len(qs)`, `list(qs)`, `bool(qs)` | `.all()` |
| `{% for %}` in a template | slicing without a step: `qs[2:5]` |
| indexing: `qs[0]` | chaining any of the above |

**These hit the database immediately** — they return a value, not a QuerySet:

```
.get()  .count()  .exists()  .first()  .last()  .create()  .aggregate()  .delete()  .update()
```

**Practical consequence:**

```python
>>> len(Book.objects.all())        # loads every row into Python, then counts
>>> Book.objects.count()           # asks the database to count. Do this.

>>> if len(Book.objects.all()) > 0:     # wasteful
>>> if Book.objects.exists():           # correct
```

---

## Demo 7.2 — Filtering and searching · 30 min

**Field lookups use a double underscore:** `field__lookup`. The `__` is Django's separator for "go one level deeper", and it means the same thing whether it introduces a comparison or crosses a relationship.

```python
>>> Book.objects.filter(year=1965)                      # exact (the default)
>>> Book.objects.filter(title__icontains="du")          # LIKE '%du%', case-insensitive
>>> Book.objects.filter(year__gte=2000)                 # >=
>>> Book.objects.filter(year__in=[1965, 1984])          # IN (...)
>>> Book.objects.filter(year__range=(1950, 1999))       # BETWEEN
>>> Book.objects.filter(published__isnull=True)         # IS NULL
>>> Book.objects.filter(title__startswith="D")          # LIKE 'D%'
>>> Book.objects.filter(added_on__year=2026)            # date part
```

| Lookup | SQL |
| --- | --- |
| `exact` | `= ?` |
| `iexact` | case-insensitive `=` |
| `contains` / `icontains` | `LIKE '%…%'` |
| `gt` `gte` `lt` `lte` | `>` `>=` `<` `<=` |
| `in` | `IN (…)` |
| `range` | `BETWEEN … AND …` |
| `isnull` | `IS NULL` |
| `startswith` / `endswith` | `LIKE 'x%'` / `LIKE '%x'` |

**Now build a real search box.** `catalog/views.py`:

```python
from django.db.models import Q
from django.shortcuts import render

from .models import Book


def book_search(request):
    q = request.GET.get("q", "").strip()
    books = Book.objects.all()
    if q:
        books = books.filter(
            Q(title__icontains=q) | Q(author__name__icontains=q)
        )
    return render(request, "catalog/search.html", {"books": books, "q": q})
```

`catalog/urls.py`:

```python
path("search/", views.book_search, name="book-search"),
```

`catalog/templates/catalog/search.html`:

```html
{% extends "catalog/base.html" %}

{% block title %}Search{% endblock title %}

{% block content %}
  <h1>Search</h1>
  <form method="get">
    <input name="q" value="{{ q }}" placeholder="Title or author">
    <button type="submit">Search</button>
  </form>

  <ul>
  {% for book in books %}
    <li>{{ book.title }} — {{ book.year }}</li>
  {% empty %}
    <li>Nothing matched "{{ q }}".</li>
  {% endfor %}
  </ul>
{% endblock content %}
```

**Two things to say:**

- **`method="get"`, not `post`.** A search is a read, and the URL stays shareable and bookmarkable. That is Session 1's rule about GET.
- **`Q` exists for one reason: `OR`.** `AND` is free — just chain, or pass two keyword arguments: `filter(year__gte=1950, price__lt=20)`.

> The `author__name` lookup in that query does not work yet. That is Demo 7.3.

---

## Demo 7.3 — One-to-many: the `ForeignKey` · 40 min

**Set up the problem first.** *One author writes many books. Where do we record which author wrote a given book?* Let the class propose answers. Someone will suggest a list of book ids on the author — take it seriously, then show why the id goes on the **many** side.

**TYPE** — `catalog/models.py`:

```python
class Book(models.Model):
    title = models.CharField(max_length=200)
    year = models.IntegerField()
    price = models.DecimalField(max_digits=8, decimal_places=2)
    published = models.DateField(null=True, blank=True)
    added_on = models.DateTimeField(auto_now_add=True)

    author = models.ForeignKey(
        Author,
        on_delete=models.CASCADE,
        related_name="books",
        null=True,                 # existing rows have no author yet
        blank=True,
    )

    class Meta:
        ordering = ["-year", "title"]

    def __str__(self):
        return f"{self.title} ({self.year})"
```

```bash
python manage.py makemigrations
python manage.py sqlmigrate catalog 0003
```

**EXPECT** — the new column, and the constraint:

```sql
ALTER TABLE "catalog_book" ADD COLUMN "author_id" bigint NULL
    REFERENCES "catalog_author" ("id") DEFERRABLE INITIALLY DEFERRED;
CREATE INDEX "catalog_book_author_id_..." ON "catalog_book" ("author_id");
```

```bash
python manage.py migrate
```

**Now open `catalog_book` in the SQLite viewer.** There is a new `author_id` column. Open `catalog_author`: there is **no** `books` column. That asymmetry is the entire lesson.

```
catalog_author                  catalog_book
┌────┬────────────────┐         ┌────┬───────────────┬───────────┐
│ id │ name           │         │ id │ title         │ author_id │
├────┼────────────────┤         ├────┼───────────────┼───────────┤
│  1 │ Frank Herbert  │ <────── │  1 │ Dune          │     1     │
│  2 │ Jane Austen    │ <────── │  2 │ Dune Messiah  │     1     │  the same id,
└────┴────────────────┘ <────── │  3 │ Emma          │     2     │  repeated —
                                └────┴───────────────┴───────────┘  that IS the "many"
```

**Assign authors** in the admin, then query both directions:

```python
>>> from catalog.models import Author, Book
>>> book = Book.objects.get(title="Dune")

>>> book.author                       # FORWARD  -> one object
<Author: Frank Herbert>
>>> book.author.name
'Frank Herbert'

>>> herbert = Author.objects.get(name="Frank Herbert")
>>> herbert.books.all()               # REVERSE  -> a QuerySet
<QuerySet [<Book: Dune Messiah (1969)>, <Book: Dune (1965)>]>
>>> herbert.books.count()
2
```

> **`TRAINER`** — There is no `books` column on the author table. `herbert.books.all()` is Django running `SELECT … WHERE author_id = 1` on your behalf. Students who see that the reverse direction is a *query*, not a stored list, understand the N+1 problem in Demo 7.6 immediately.

**Without `related_name`** you get `herbert.book_set.all()`. It works and reads badly. Always set `related_name`.

**`on_delete` is required, and the choice matters.** Django refuses to let you declare a `ForeignKey` without saying what happens to the children when the parent is deleted — there is no safe default.

| `on_delete=` | Deleting the author… | Use when |
| --- | --- | --- |
| `CASCADE` | deletes their books too | the child cannot exist alone |
| `PROTECT` | refuses, raising an error | the data matters; deletion should be deliberate |
| `SET_NULL` | keeps the books, sets `author_id` to `NULL` | the child is still meaningful alone (needs `null=True`) |
| `SET_DEFAULT` | reassigns to a default | you have an "Unknown author" row |

**Now the search from Demo 7.2 works.** Reload `/catalog/search/` and search for an author's name.

---

## Demo 7.4 — Many-to-many · 35 min

**Set up the problem the same way.** *A book has several genres; a genre covers many books. Where does the id go now?* Neither side works — and that impossibility is what forces a **third table**.

**TYPE** — add to `catalog/models.py`:

```python
class Genre(models.Model):
    name = models.CharField(max_length=60, unique=True)

    class Meta:
        ordering = ["name"]

    def __str__(self):
        return self.name
```

…and add the field to `Book`:

```python
    genres = models.ManyToManyField(Genre, related_name="books", blank=True)
```

```bash
python manage.py makemigrations
python manage.py sqlmigrate catalog 0004
```

**EXPECT** — Django creates a table you did not ask for:

```sql
CREATE TABLE "catalog_book_genres" (
    "id" integer NOT NULL PRIMARY KEY AUTOINCREMENT,
    "book_id" bigint NOT NULL REFERENCES "catalog_book" ("id"),
    "genre_id" bigint NOT NULL REFERENCES "catalog_genre" ("id")
);
CREATE UNIQUE INDEX ... ON "catalog_book_genres" ("book_id", "genre_id");
```

```bash
python manage.py migrate
```

**Open `catalog_book_genres` in the SQLite viewer.** This is the moment many-to-many becomes obvious:

```
catalog_book        catalog_book_genres         catalog_genre
┌────┬────────┐     ┌─────────┬──────────┐      ┌────┬─────────┐
│ id │ title  │     │ book_id │ genre_id │      │ id │ name    │
├────┼────────┤     ├─────────┼──────────┤      ├────┼─────────┤
│  1 │ Dune   │ ──> │    1    │    10    │ ──>  │ 10 │ sci-fi  │
│  2 │ Emma   │ ──> │    1    │    11    │ ──>  │ 11 │ classic │
└────┴────────┘     │    2    │    11    │      └────┴─────────┘
                    └─────────┴──────────┘
                    one row = one link. Dune is in two genres,
                    so it has two rows.
```

**Say:** *"A cell cannot hold a list."* Students arriving from spreadsheets genuinely expect a comma-separated genre column. Ask them how they would find every sci-fi book in that version.

**Manage the links — never touch the join table directly:**

```python
>>> from catalog.models import Book, Genre
>>> scifi = Genre.objects.create(name="sci-fi")
>>> classic = Genre.objects.create(name="classic")
>>> dune = Book.objects.get(title="Dune")

>>> dune.genres.add(scifi, classic)
>>> dune.genres.all()
<QuerySet [<Genre: classic>, <Genre: sci-fi>]>

>>> scifi.books.all()                    # the reverse direction
<QuerySet [<Book: Dune (1965)>]>

>>> dune.genres.remove(classic)
>>> dune.genres.set([scifi, classic])    # replace the whole set
>>> dune.genres.count()
2
>>> dune.genres.clear()                  # remove all links
```

**Note there is no `on_delete`.** Deleting either side just removes the links.

**BREAK IT** — `.add()` on an unsaved object:

```python
>>> ghost = Book(title="Ghost", year=2000, price="1.00")
>>> ghost.genres.add(scifi)
ValueError: "<Book: Ghost (2000)>" needs to have a value for field "id"
before this many-to-many relationship can be used.
```

**Say:** a link stores two ids, so both objects must exist in the database first. Save, then link.

---

## Demo 7.5 — One-to-one · 20 min

**Frame it as a special case:** a `OneToOneField` is a `ForeignKey` with a uniqueness constraint, so the many side can only ever hold one row per parent. The useful question is *why would you want that*, and there is one dominant answer — **extending a model you do not own**.

**TYPE** — add to `catalog/models.py`:

```python
class AuthorProfile(models.Model):
    author = models.OneToOneField(
        Author, on_delete=models.CASCADE, related_name="profile"
    )
    website = models.URLField(blank=True)
    country = models.CharField(max_length=60, blank=True)

    def __str__(self):
        return f"Profile of {self.author.name}"
```

```bash
python manage.py makemigrations && python manage.py migrate
```

**Check the generated SQL** — the only difference from a `ForeignKey` is one word:

```sql
"author_id" bigint NOT NULL UNIQUE REFERENCES "catalog_author" ("id")
```

```python
>>> from catalog.models import Author, AuthorProfile
>>> herbert = Author.objects.get(name="Frank Herbert")
>>> AuthorProfile.objects.create(author=herbert, country="United States")

>>> herbert.profile                  # one object, NOT a QuerySet
<AuthorProfile: Profile of Frank Herbert>
>>> herbert.profile.country
'United States'
```

**BREAK IT** — an author with no profile:

```python
>>> austen = Author.objects.get(name="Jane Austen")
>>> austen.profile
catalog.models.Author.profile.RelatedObjectDoesNotExist:
Author has no profile.
```

> **`TRAINER`** — This raises rather than returning `None`, which is why real projects create the profile automatically — with a signal, or in the registration view. **Module 9 needs exactly this pattern** for adding fields to Django's built-in `User`, so plant it here.

**Defensive access:**

```python
>>> getattr(austen, "profile", None)
>>> # or in a template, which swallows the error silently:
>>> # {{ author.profile.country|default:"—" }}
```

---

## Demo 7.6 — The N+1 problem · 35 min

**Goal.** The single most valuable performance lesson in the course, and the one that shows up in code review at their first job.

**TYPE** — turn on SQL logging so the queries are visible. Add to the **bottom** of `config/settings.py`:

```python
LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "handlers": {"console": {"class": "logging.StreamHandler"}},
    "loggers": {
        "django.db.backends": {"handlers": ["console"], "level": "DEBUG"},
    },
}
```

**TYPE** — in the shell:

```python
>>> from catalog.models import Book
>>> for b in Book.objects.all():
...     print(b.title, "-", b.author.name if b.author else "—")
```

**EXPECT** — one `SELECT` for the books, then **one more `SELECT` per book**:

```
(0.000) SELECT ... FROM "catalog_book" ORDER BY ...
(0.000) SELECT ... FROM "catalog_author" WHERE "catalog_author"."id" = 1
(0.000) SELECT ... FROM "catalog_author" WHERE "catalog_author"."id" = 2
(0.000) SELECT ... FROM "catalog_author" WHERE "catalog_author"."id" = 1
...
```

**Say:** 10 books → 11 queries. 5,000 books → 5,001. Fast in development with three rows; fatal in production.

**Now fix it:**

```python
>>> for b in Book.objects.select_related("author"):
...     print(b.title, "-", b.author.name if b.author else "—")
```

**EXPECT** — exactly **one** query, with a `JOIN`:

```
(0.000) SELECT "catalog_book".*, "catalog_author".* FROM "catalog_book"
LEFT OUTER JOIN "catalog_author" ON ("catalog_book"."author_id" = "catalog_author"."id")
```

**And for many-to-many, use the other one:**

```python
>>> for b in Book.objects.prefetch_related("genres"):
...     print(b.title, [g.name for g in b.genres.all()])
```

**EXPECT** — exactly **two** queries, regardless of how many books there are.

| Use | For | Queries | How |
| --- | --- | --- | --- |
| `select_related("author")` | `ForeignKey`, `OneToOne` — **one** related object | 1 | SQL `JOIN` |
| `prefetch_related("genres")` | `ManyToMany`, reverse FK — **many** related objects | 2 | second query, joined in Python |

**The memory trick:** *one object → `select_related`; many objects → `prefetch_related`.*

**Apply it to the real view** — `catalog/views.py`:

```python
def book_list(request):
    books = Book.objects.select_related("author").prefetch_related("genres")
    return render(request, "catalog/book_list.html", {
        "page_title": "All books",
        "books": books,
        "total": books.count(),
    })
```

> **`TRAINER`** — Turn the logging off again before Session 8; it is very noisy. Comment out the `LOGGING` block, or install [django-debug-toolbar](https://django-debug-toolbar.readthedocs.io/), which shows the query count as a panel on the page instead.

---

## Demo 7.7 — Crossing relationships in queries · 25 min

**The same `__` syntax crosses tables:**

```python
>>> Book.objects.filter(author__name__icontains="herbert")
>>> Book.objects.filter(genres__name="sci-fi")
>>> Author.objects.filter(books__year__gte=2000)
```

**BREAK IT** — the duplicate-rows surprise:

```python
>>> Author.objects.filter(books__year__gte=1900)
<QuerySet [<Author: Frank Herbert>, <Author: Frank Herbert>]>
```

**Say:** that is what a `JOIN` does — one row per matching book. The fix:

```python
>>> Author.objects.filter(books__year__gte=1900).distinct()
<QuerySet [<Author: Frank Herbert>]>
```

**Aggregation — one summary number for the whole set:**

```python
>>> from django.db.models import Count, Avg, Max, Sum
>>> Book.objects.aggregate(Avg("price"), Max("year"), Count("id"))
{'price__avg': Decimal('14.500000'), 'year__max': 2006, 'id__count': 10}
```

**Annotation — one extra number attached to each row:**

```python
>>> authors = Author.objects.annotate(n=Count("books")).order_by("-n")
>>> for a in authors:
...     print(a.name, a.n)
Frank Herbert 2
Jane Austen 1
```

Now `{{ author.n }}` works in a template — computed by the database, in one query, instead of counting in a Python loop.

> **Say both sentences, because students mix these up constantly:**
> **`aggregate`** = one row of answers for everything. **`annotate`** = one answer attached to each row.

---

## Lab 7.8 — All three, in your own project · 40 min

Every student must demonstrate:

1. A `ForeignKey`, migrated, with `related_name` and a deliberate `on_delete` choice.
2. A `ManyToManyField`, migrated, with the join table visible in the SQLite viewer.
3. A `OneToOneField`, migrated.
4. Each one queried in **both** directions in the shell, with output pasted into a text file.
5. One page showing the query count before and after `select_related`.

---

## Session 7 close

```bash
git add .
git commit -m "Session 7: FK, M2M and 1:1 relationships, search, query optimisation"
git tag session-7-complete
```

**CHECKPOINT 7 — the hardest gate in the course:**

1. Draw where the id physically lives for a one-to-many, and for a many-to-many.
2. Query a relationship forward and in reverse.
3. Show the query count with and without `select_related`.
4. When does a QuerySet actually hit the database?
5. What is the difference between `aggregate` and `annotate`?

**Common failures:**

| Symptom | Cause |
| --- | --- |
| `TypeError: __init__() missing 1 required positional argument: 'on_delete'` | every `ForeignKey` needs `on_delete` |
| Duplicate rows after filtering across a relation | that is a `JOIN`; add `.distinct()` |
| `needs to have a value for field "id"` | `.add()` on an unsaved object |
| `RelatedObjectDoesNotExist` | one-to-one with no row on the other side |
| Page mysteriously slow | N+1; add `select_related` / `prefetch_related` |
| `author.book_set` and confusion about the name | you did not set `related_name` |

\newpage

# Appendix A — The finished code

This is the complete state of the project at the end of Session 7. Use it to diff against a stuck student's copy.

## Project tree

```
~/code/library/
├── .gitignore
├── db.sqlite3                  (ignored by git)
├── manage.py
├── requirements.txt
├── venv/                       (ignored by git)
├── config/
│   ├── __init__.py
│   ├── asgi.py
│   ├── settings.py
│   ├── urls.py
│   └── wsgi.py
└── catalog/
    ├── __init__.py
    ├── admin.py
    ├── apps.py
    ├── models.py
    ├── tests.py
    ├── urls.py
    ├── views.py
    ├── migrations/
    │   ├── __init__.py
    │   ├── 0001_initial.py
    │   ├── 0002_book_isbn.py
    │   ├── 0003_book_author.py
    │   ├── 0004_genre_book_genres.py
    │   └── 0005_authorprofile.py
    ├── static/
    │   └── catalog/
    │       ├── app.js
    │       └── style.css
    └── templates/
        └── catalog/
            ├── _book_card.html
            ├── about.html
            ├── base.html
            ├── book_detail.html
            ├── book_list.html
            └── search.html
```

## `catalog/models.py`

```python
from django.db import models


class Author(models.Model):
    name = models.CharField(max_length=120)
    bio = models.TextField(blank=True)

    class Meta:
        ordering = ["name"]

    def __str__(self):
        return self.name


class AuthorProfile(models.Model):
    author = models.OneToOneField(
        Author, on_delete=models.CASCADE, related_name="profile"
    )
    website = models.URLField(blank=True)
    country = models.CharField(max_length=60, blank=True)

    def __str__(self):
        return f"Profile of {self.author.name}"


class Genre(models.Model):
    name = models.CharField(max_length=60, unique=True)

    class Meta:
        ordering = ["name"]

    def __str__(self):
        return self.name


class Book(models.Model):
    title = models.CharField(max_length=200)
    year = models.IntegerField()
    price = models.DecimalField(max_digits=8, decimal_places=2)
    isbn = models.CharField(max_length=13, blank=True)
    published = models.DateField(null=True, blank=True)
    added_on = models.DateTimeField(auto_now_add=True)

    author = models.ForeignKey(
        Author,
        on_delete=models.CASCADE,
        related_name="books",
        null=True,
        blank=True,
    )
    genres = models.ManyToManyField(Genre, related_name="books", blank=True)

    class Meta:
        ordering = ["-year", "title"]

    def __str__(self):
        return f"{self.title} ({self.year})"
```

## `catalog/views.py`

```python
from django.db.models import Q
from django.shortcuts import get_object_or_404, render

from .models import Book


def book_list(request):
    books = Book.objects.select_related("author").prefetch_related("genres")
    return render(request, "catalog/book_list.html", {
        "page_title": "All books",
        "books": books,
        "total": books.count(),
    })


def book_detail(request, pk):
    book = get_object_or_404(
        Book.objects.select_related("author").prefetch_related("genres"), pk=pk
    )
    return render(request, "catalog/book_detail.html", {"book": book})


def book_search(request):
    q = request.GET.get("q", "").strip()
    books = Book.objects.select_related("author")
    if q:
        books = books.filter(
            Q(title__icontains=q) | Q(author__name__icontains=q)
        ).distinct()
    return render(request, "catalog/search.html", {"books": books, "q": q})


def about(request):
    return render(request, "catalog/about.html")
```

## `catalog/urls.py`

```python
from django.urls import path

from . import views

urlpatterns = [
    path("books/", views.book_list, name="book-list"),
    path("books/<int:pk>/", views.book_detail, name="book-detail"),
    path("search/", views.book_search, name="book-search"),
    path("about/", views.about, name="about"),
]
```

## `config/urls.py`

```python
from django.contrib import admin
from django.urls import include, path

urlpatterns = [
    path("admin/", admin.site.urls),
    path("catalog/", include("catalog.urls")),
]
```

## `catalog/admin.py`

```python
from django.contrib import admin

from .models import Author, AuthorProfile, Book, Genre


@admin.register(Author)
class AuthorAdmin(admin.ModelAdmin):
    list_display = ("name",)
    search_fields = ("name",)


@admin.register(Book)
class BookAdmin(admin.ModelAdmin):
    list_display = ("title", "author", "year", "price", "added_on")
    list_filter = ("year", "genres")
    search_fields = ("title", "author__name")
    filter_horizontal = ("genres",)
    ordering = ("-year",)
    list_per_page = 25


admin.site.register(Genre)
admin.site.register(AuthorProfile)
```

## `requirements.txt`

```
asgiref==3.8.1
Django==5.2.*
sqlparse==0.5.3
```

\newpage

# Appendix B — Recovery and catch-up

## Git checkpoints

Each session ends with a tag. A student who fell behind can jump forward:

```bash
git stash                        # park whatever is broken
git checkout session-6-complete  # jump to a known-good state
```

| Tag | State |
| --- | --- |
| `session-4-complete` | Django project, catalog app, first URLs and views |
| `session-5-complete` | Base template, static CSS/JS, partials |
| `session-6-complete` | Author and Book models, migrations, admin, real data |
| `session-7-complete` | All three relationships, search, query optimisation |

## The nuclear resets, in increasing severity

```bash
# 1. Environment is confused
deactivate
source venv/bin/activate
python -m pip install -r requirements.txt

# 2. Database is tangled (acceptable ONLY while there is no real data)
rm db.sqlite3
python manage.py migrate
python manage.py createsuperuser

# 3. Migrations are tangled but the database matters
python manage.py showmigrations          # see what is applied
python manage.py migrate catalog 0002    # roll BACKWARDS to a good state
#    then delete only the UNAPPLIED migration files, fix models.py,
#    and run makemigrations again

# 4. Everything is lost
git checkout session-6-complete
```

## Error triage table

Pin this next to the projector.

| Message | Almost always means | Demo |
| --- | --- | --- |
| `ModuleNotFoundError: No module named 'django'` | venv not activated — check the prompt | 3.5 |
| `TemplateDoesNotExist` | wrong path, missing namespace folder, or app not installed | 5.1 |
| `Invalid block tag 'static'` | `{% load static %}` missing from that file | 5.5 |
| `no such table` / `no such column` | a migration was written but never applied | 6.2 |
| `No changes detected` | app missing from `INSTALLED_APPS` | 4.3 |
| `Book object (7)` everywhere | no `__str__` on the model | 6.5 |
| `DoesNotExist` | `get()` where `get_object_or_404` belonged | 6.4 |
| `didn't return an HttpResponse object` | the view has no `return` | 4.8 |
| `'str' object has no attribute 'get'` | the view returned a string, not a response | 4.8 |
| `got an unexpected keyword argument 'pk'` | URL converter name and view parameter disagree | 4.6 |
| `missing 1 required positional argument: 'on_delete'` | every `ForeignKey` needs `on_delete` | 7.3 |
| `needs to have a value for field "id"` | `.add()` on an unsaved object | 7.4 |
| `RelatedObjectDoesNotExist` | one-to-one with no row on the other side | 7.5 |
| `takes 0 positional arguments but 1 was given` | a method defined without `self` | 3.6 |
| The page is mysteriously slow | N+1 queries | 7.6 |

\newpage

# Appendix C — Command reference

| Command | Does | First used |
| --- | --- | --- |
| `python3 -m venv venv` | create the virtual environment | Demo 3.5 |
| `source venv/bin/activate` | activate it — macOS/Linux | Demo 3.5 |
| `venv\Scripts\Activate.ps1` | activate it — Windows PowerShell | Demo 3.5 |
| `python -m pip install -r requirements.txt` | reproduce an environment | Demo 3.5 |
| `python -m pip freeze > requirements.txt` | record yours | Demo 3.5 |
| `django-admin startproject config .` | create the project **here** | Demo 4.2 |
| `python manage.py startapp catalog` | create an app (then add to `INSTALLED_APPS`) | Demo 4.3 |
| `python manage.py runserver` | the development server | Demo 4.2 |
| `python manage.py runserver 8001` | a different port | — |
| `python manage.py makemigrations` | write a migration from model changes | Demo 6.2 |
| `python manage.py sqlmigrate catalog 0001` | **print the SQL** without running it | Demo 6.2 |
| `python manage.py migrate` | apply migrations | Demo 6.2 |
| `python manage.py migrate catalog 0001` | migrate **backwards** | Demo 6.2 |
| `python manage.py showmigrations` | what is applied and what is not | Demo 6.2 |
| `python manage.py createsuperuser` | an admin account | Demo 6.5 |
| `python manage.py shell` | a REPL with your models loaded | Demo 6.4 |
| `python manage.py dbshell` | a SQL prompt on your database | — |
| `python manage.py check` | find configuration problems | — |
| `git status` | which of the four areas your changes are in | Demo 4.9 |
| `git log --oneline` | read the history | Demo 4.9 |
| `git tag session-N-complete` | mark a known-good state | Demo 4.9 |

\newpage

# Appendix D — Official documentation

Everything in this lab is checkable against these. The `/en/stable/` path always resolves to the current Django release, so teach students to type `stable` rather than a version number.

## Django

- Documentation home — <https://docs.djangoproject.com/en/stable/>
- Tutorial, parts 1–8 — <https://docs.djangoproject.com/en/stable/intro/tutorial01/>
- URL dispatcher — <https://docs.djangoproject.com/en/stable/topics/http/urls/>
- Writing views — <https://docs.djangoproject.com/en/stable/topics/http/views/>
- Template language — <https://docs.djangoproject.com/en/stable/ref/templates/language/>
- All template tags and filters — <https://docs.djangoproject.com/en/stable/ref/templates/builtins/>
- Static files — <https://docs.djangoproject.com/en/stable/howto/static-files/>
- Models — <https://docs.djangoproject.com/en/stable/topics/db/models/>
- Model field reference — <https://docs.djangoproject.com/en/stable/ref/models/fields/>
- Migrations — <https://docs.djangoproject.com/en/stable/topics/migrations/>
- Making queries — <https://docs.djangoproject.com/en/stable/topics/db/queries/>
- QuerySet API — <https://docs.djangoproject.com/en/stable/ref/models/querysets/>
- Field lookups — <https://docs.djangoproject.com/en/stable/ref/models/querysets/#field-lookups>
- Many-to-one examples — <https://docs.djangoproject.com/en/stable/topics/db/examples/many_to_one/>
- Many-to-many examples — <https://docs.djangoproject.com/en/stable/topics/db/examples/many_to_many/>
- One-to-one examples — <https://docs.djangoproject.com/en/stable/topics/db/examples/one_to_one/>
- Database optimization — <https://docs.djangoproject.com/en/stable/topics/db/optimization/>
- Aggregation — <https://docs.djangoproject.com/en/stable/topics/db/aggregation/>
- The admin site — <https://docs.djangoproject.com/en/stable/ref/contrib/admin/>
- `manage.py` commands — <https://docs.djangoproject.com/en/stable/ref/django-admin/>
- Settings reference — <https://docs.djangoproject.com/en/stable/ref/settings/>
- Versions and support timeline — <https://www.djangoproject.com/download/>

## Python

- The Python tutorial — <https://docs.python.org/3/tutorial/>
- Data structures — <https://docs.python.org/3/tutorial/datastructures.html>
- Errors and exceptions — <https://docs.python.org/3/tutorial/errors.html>
- Modules and packages — <https://docs.python.org/3/tutorial/modules.html>
- Classes — <https://docs.python.org/3/tutorial/classes.html>
- `venv` — <https://docs.python.org/3/library/venv.html>
- PEP 8 style guide — <https://peps.python.org/pep-0008/>

## HTTP, tools, and further reading

- MDN, HTTP overview — <https://developer.mozilla.org/en-US/docs/Web/HTTP/Guides/Overview>
- MDN, status codes — <https://developer.mozilla.org/en-US/docs/Web/HTTP/Reference/Status>
- MDN, request methods — <https://developer.mozilla.org/en-US/docs/Web/HTTP/Reference/Methods>
- Pro Git, the free book — <https://git-scm.com/book/en/v2>
- DB Browser for SQLite — <https://sqlitebrowser.org/>
- django-debug-toolbar — <https://django-debug-toolbar.readthedocs.io/>

---

*End of Foundation & Django Core. Sessions 8–15 — forms, authentication, class-based views, Django REST Framework, API security, Git workflow and the capstone — continue in the second half of the course.*
