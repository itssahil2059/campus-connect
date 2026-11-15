from django.db import transaction
from django.db.models import Q
from rest_framework import status, viewsets
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import Answer, Profile, Question
from .serializers import (
    AnswerSerializer,
    MyProfileSerializer,
    PublicProfileSerializer,
    QuestionSerializer,
)


class MyProfileView(APIView):
    """GET / PUT /api/profiles/me/ — the logged-in user's own profile.

    GET returns 404 until the profile exists, which tells the frontend to
    send the user to profile setup. PUT creates it the first time.
    """

    def get(self, request):
        profile = Profile.objects.filter(user=request.user).first()
        if profile is None:
            return Response(
                {"detail": "Profile not set up yet."}, status=status.HTTP_404_NOT_FOUND
            )
        return Response(MyProfileSerializer(profile).data)

    def put(self, request):
        profile = Profile.objects.filter(user=request.user).first()
        # instance=None -> serializer.save() creates; otherwise it updates.
        serializer = MyProfileSerializer(profile, data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save(user=request.user)
        return Response(
            serializer.data,
            status=status.HTTP_200_OK if profile else status.HTTP_201_CREATED,
        )


# Query param -> Profile JSON field. Each can repeat; all must match.
TAG_FILTERS = {"interest": "interests", "like": "likes", "dislike": "dislikes"}
MAX_QUERY_LENGTH = 100


def filter_profiles(queryset, params):
    """Narrow profiles by the search/filter query params (all ANDed together).

    ?q=        text in username, college or bio (case-insensitive)
    ?college=  text in college name
    ?interest= / ?like= / ?dislike=   exact tag; repeat for "has all of these"
    """
    q = params.get("q", "").strip()[:MAX_QUERY_LENGTH]
    if q:
        queryset = queryset.filter(
            Q(user__username__icontains=q)
            | Q(user__college_name__icontains=q)
            | Q(bio__icontains=q)
        )

    college = params.get("college", "").strip()[:MAX_QUERY_LENGTH]
    if college:
        queryset = queryset.filter(user__college_name__icontains=college)

    for param, field in TAG_FILTERS.items():
        # Tags are stored lowercased (see TagListField), so match that way.
        tags = [t.strip().lower() for t in params.getlist(param) if t.strip()]
        if tags:
            # Postgres JSON "contains" (@>): the list includes every tag.
            queryset = queryset.filter(**{f"{field}__contains": tags})

    return queryset


class ProfileViewSet(viewsets.ReadOnlyModelViewSet):
    """GET /api/profiles/ and /api/profiles/<id>/ — other students' profiles.

    Only verified, active users, and never yourself. The list can be narrowed
    with search/filter query params; see filter_profiles().
    """

    serializer_class = PublicProfileSerializer
    # Only match numeric ids, so /api/profiles/me/ never reaches this viewset.
    lookup_value_regex = r"\d+"

    def get_queryset(self):
        queryset = (
            Profile.objects.filter(user__is_active=True, user__is_edu_verified=True)
            .exclude(user=self.request.user)
            .select_related("user")  # one query instead of one per profile
            .order_by("-updated_at")
        )
        if self.action == "list":
            queryset = filter_profiles(queryset, self.request.query_params)
        return queryset


class QuestionViewSet(viewsets.ReadOnlyModelViewSet):
    """GET /api/questions/ — the questionnaire."""

    queryset = Question.objects.all()
    serializer_class = QuestionSerializer


class AnswersView(APIView):
    """GET / POST /api/answers/ — the logged-in user's questionnaire answers.

    POST takes a list, e.g. [{"question": 1, "choice": "Night owl"}, ...], and
    saves each one, replacing any earlier answer to the same question.
    """

    def get(self, request):
        answers = Answer.objects.filter(user=request.user).order_by("question__order")
        return Response(AnswerSerializer(answers, many=True).data)

    def post(self, request):
        serializer = AnswerSerializer(data=request.data, many=True)
        serializer.is_valid(raise_exception=True)

        # All or nothing: if one save fails, none are kept.
        with transaction.atomic():
            for item in serializer.validated_data:
                Answer.objects.update_or_create(
                    user=request.user,
                    question=item["question"],
                    defaults={"choice": item["choice"]},
                )

        return self.get(request)
