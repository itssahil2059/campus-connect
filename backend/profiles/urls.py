from django.urls import path
from rest_framework.routers import SimpleRouter

from .views import AnswersView, MyPhotoView, MyProfileView, ProfileViewSet, QuestionViewSet

app_name = "profiles"

# A router generates the list (/profiles/) and detail (/profiles/<id>/) URLs
# for each viewset.
router = SimpleRouter()
router.register("profiles", ProfileViewSet, basename="profile")
router.register("questions", QuestionViewSet, basename="question")

urlpatterns = [
    # Listed before the router so "me" is never treated as an id.
    path("profiles/me/", MyProfileView.as_view(), name="my-profile"),
    path("profiles/me/photo/", MyPhotoView.as_view(), name="my-photo"),
    path("answers/", AnswersView.as_view(), name="answers"),
] + router.urls
