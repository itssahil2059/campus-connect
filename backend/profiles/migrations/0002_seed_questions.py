"""Data migration: load the starter questionnaire questions."""

from django.db import migrations

QUESTIONS = [
    (
        "What are you mainly looking for?",
        ["New friends", "Study partners", "Dating", "Not sure yet"],
    ),
    (
        "Your ideal weekend?",
        ["Out with a big group", "Small hangout", "Outdoors", "Staying in"],
    ),
    (
        "How do you like to study?",
        ["Quiet library", "Coffee shop", "Group study", "Last-minute cram"],
    ),
    ("What's your sleep schedule?", ["Early bird", "Night owl", "Depends on the day"]),
    (
        "How often do you want to meet up in person?",
        ["A few times a week", "Weekends", "Once in a while"],
    ),
]


def add_questions(apps, schema_editor):
    # Use the historical model from `apps`, not a direct import, so this
    # migration keeps working even if the model changes later.
    Question = apps.get_model("profiles", "Question")
    for order, (text, choices) in enumerate(QUESTIONS, start=1):
        Question.objects.create(text=text, choices=choices, order=order)


def remove_questions(apps, schema_editor):
    Question = apps.get_model("profiles", "Question")
    Question.objects.filter(text__in=[text for text, _ in QUESTIONS]).delete()


class Migration(migrations.Migration):
    dependencies = [("profiles", "0001_initial")]

    operations = [migrations.RunPython(add_questions, remove_questions)]
