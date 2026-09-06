"""Placeholder data — and the contract the backend has to satisfy.

This module exists so the UI can be reviewed and clicked through before a
single model is written. It is also the **handoff document**: the shape of
these dictionaries is exactly what each template reads, so a real view is
"correct" when its context matches what is here.

Delete this file on the day the backend lands. Nothing in `templates/` imports
it — only `urls.py` does, on one line per route.

Shape summary
-------------
post          id, author, created_at, text, media, likes, comments, shares,
              liked, saved
author/person id, username, name, avatar, bio, followers, following, is_following
comment       id, author, created_at, text, likes, replies
conversation  id, person, last_message, unread, updated_at
message       id, mine, text, sent_at   (pass as `thread_messages`, never
              `messages` — that name belongs to django.contrib.messages)
weather       city, temp_c, summary, icon, updated_at
ai turn       role ("you" | "assistant"), text
"""

CURRENT_USER = {
    "id": 1,
    "username": "menuka",
    "name": "Menuka",
    "avatar": "M",
    "bio": "Project manager. Ships things.",
    "followers": 128,
    "following": 92,
}

PEOPLE = [
    {"id": 2, "username": "himanshu", "name": "Himanshu", "avatar": "H",
     "bio": "Team lead", "followers": 341, "following": 180, "is_following": True},
    {"id": 3, "username": "kaushal", "name": "Kaushal", "avatar": "K",
     "bio": "Backend", "followers": 96, "following": 140, "is_following": False},
    {"id": 4, "username": "suraj", "name": "Suraj", "avatar": "S",
     "bio": "Frontend and UI", "followers": 212, "following": 88, "is_following": True},
    {"id": 5, "username": "bidhya", "name": "Bidhya", "avatar": "B",
     "bio": "QA", "followers": 74, "following": 61, "is_following": False},
]

PROFILE = {
    "id": 4,
    "username": "suraj",
    "name": "Suraj",
    "avatar": "S",
    "bio": "Frontend and UI. Building PalShare one component at a time.",
    "followers": 212,
    "following": 88,
    "is_following": True,
    "is_private": False,
    "is_me": False,
    "joined": "March 2026",
    "post_count": 34,
}

POSTS = [
    {
        "id": 1,
        "author": PEOPLE[0],
        "created_at": "2 hours ago",
        "text": "Hour three and PalShare has working authentication. Feed next.",
        "media": [{"kind": "image", "alt": "Screenshot of the login page"}],
        "likes": 24, "comments": 5, "shares": 2,
        "liked": True, "saved": False,
    },
    {
        "id": 2,
        "author": PEOPLE[2],
        "created_at": "4 hours ago",
        "text": "Component library first, pages second. Everything below is one card "
                "template used eleven times.",
        "media": [],
        "likes": 41, "comments": 12, "shares": 6,
        "liked": False, "saved": True,
    },
    {
        "id": 3,
        "author": PEOPLE[1],
        "created_at": "yesterday",
        "text": "Posts API is live: list, detail, create, like, unlike. Contract is in demo.py.",
        "media": [{"kind": "image", "alt": "API response"},
                  {"kind": "image", "alt": "Swagger UI"}],
        "likes": 18, "comments": 3, "shares": 1,
        "liked": False, "saved": False,
    },
]

COMMENTS = [
    {"id": 1, "author": PEOPLE[3], "created_at": "1 hour ago", "likes": 3,
     "text": "Tested on mobile — the composer needs more room on small screens.",
     "replies": [
         {"id": 2, "author": PEOPLE[2], "created_at": "50 minutes ago", "likes": 1,
          "text": "Fixed, it stacks under 640px now."},
     ]},
    {"id": 3, "author": PEOPLE[1], "created_at": "40 minutes ago", "likes": 0,
     "text": "Shipping the like endpoint after lunch.", "replies": []},
]

CONVERSATIONS = [
    {"id": 1, "person": PEOPLE[0], "last_message": "Standup in ten minutes",
     "unread": 2, "updated_at": "09:41"},
    {"id": 2, "person": PEOPLE[2], "last_message": "Sent you the card markup",
     "unread": 0, "updated_at": "09:12"},
    {"id": 3, "person": PEOPLE[3], "last_message": "Found a bug in search",
     "unread": 0, "updated_at": "yesterday"},
]

MESSAGES = [
    {"id": 1, "mine": False, "text": "Are the profile pages ready to wire up?", "sent_at": "09:31"},
    {"id": 2, "mine": True, "text": "Templates are in. They read profile.username and profile.posts.", "sent_at": "09:33"},
    {"id": 3, "mine": False, "text": "Perfect. Standup in ten minutes", "sent_at": "09:41"},
]

WEATHER = {
    "city": "Kathmandu",
    "temp_c": 24,
    "summary": "Partly cloudy",
    "icon": "⛅",
    "updated_at": "09:40",
}

AI_TURNS = [
    {"role": "you", "text": "Write a caption for a photo of the team at hour ten."},
    {"role": "assistant", "text": "Two hours left, eleven people, one repository. "
                                  "Whatever happens next, it compiles."},
]
