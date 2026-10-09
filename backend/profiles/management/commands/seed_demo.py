"""python manage.py seed_demo — add sample verified students for local demos.

Safe to run more than once: existing demo users are updated, not duplicated.
Never run this against production.
"""

from django.core.management.base import BaseCommand

from profiles.models import Answer, Profile, Question
from users.models import CustomUser

DEMO_PASSWORD = "demo-Pass-2026"

DEMO_STUDENTS = [
    ("maya", 2027, "Bio major, pre-med. Always down for a sunrise hike or a long study session with good coffee.",
     ["hiking", "biology", "coffee", "photography"], ["sunrises", "iced lattes"], ["loud libraries"]),
    ("jordan", 2026, "CS senior building side projects. Ask me about my mechanical keyboard collection.",
     ["coding", "gaming", "keyboards", "basketball"], ["hackathons", "pizza"], ["slow wifi"]),
    ("priya", 2028, "Psych + dance. Looking for people to try every food spot in town with.",
     ["dance", "food", "psychology", "music"], ["street tacos", "k-pop"], ["8am classes"]),
    ("diego", 2027, "Business major, part-time barista. Weekend soccer player.",
     ["soccer", "coffee", "entrepreneurship"], ["sunday league", "espresso"], ["group projects"]),
    ("hannah", 2026, "English lit, writing a novel slowly. Board game nights are my thing.",
     ["writing", "board games", "reading", "film"], ["rainy days", "used bookstores"], ["spoilers"]),
    ("sam", 2029, "Freshman in engineering, new to Texarkana — show me around!",
     ["robotics", "running", "anime", "cooking"], ["late-night ramen"], ["humidity"]),
]


class Command(BaseCommand):
    help = "Create sample verified students with profiles for local demos."

    def handle(self, *args, **options):
        questions = list(Question.objects.all())

        for i, (username, year, bio, interests, likes, dislikes) in enumerate(DEMO_STUDENTS):
            user, _ = CustomUser.objects.update_or_create(
                username=username,
                defaults={
                    "school_email": f"{username}@tamut.edu",
                    "college_name": "Texas A&M University–Texarkana",
                    "graduation_year": year,
                    "is_active": True,
                    "is_edu_verified": True,
                },
            )
            user.set_password(DEMO_PASSWORD)
            user.save()

            Profile.objects.update_or_create(
                user=user,
                defaults={"bio": bio, "interests": interests, "likes": likes, "dislikes": dislikes},
            )
            # Spread answers across the choices so users differ.
            for q in questions:
                Answer.objects.update_or_create(
                    user=user, question=q, defaults={"choice": q.choices[(i + q.id) % len(q.choices)]}
                )

        self.stdout.write(self.style.SUCCESS(
            f"Seeded {len(DEMO_STUDENTS)} demo students (password: {DEMO_PASSWORD})."
        ))
