"""Profile photo upload: the processing pipeline and the API.

IDs (PH-...) match docs/test-cases.md.
"""

import io
import os

import pytest
from django.core.files.storage import default_storage
from django.core.files.uploadedfile import SimpleUploadedFile
from django.urls import reverse
from PIL import Image

from profiles.models import Profile
from profiles.photos import MAX_UPLOAD_BYTES, TOO_LARGE, WRONG_TYPE

PHOTO_URL = reverse("profiles:my-photo")
ME_URL = reverse("profiles:my-profile")

GPS_TAG = 0x8825  # EXIF "GPSInfo"
ORIENTATION_TAG = 0x0112


@pytest.fixture(autouse=True)
def media_root(settings, tmp_path):
    """Save uploads into a temp folder, never the real backend/media/."""
    settings.MEDIA_ROOT = tmp_path
    return tmp_path


@pytest.fixture
def alice(make_student):
    user = make_student("alice")
    Profile.objects.create(user=user)
    return user


@pytest.fixture
def bob(make_student):
    user = make_student("bob")
    Profile.objects.create(user=user)
    return user


def image_upload(width=800, height=600, fmt="JPEG", name="photo.jpg", noise=False, exif=None, mode="RGB"):
    """An in-memory image file, like a browser would send."""
    if noise:
        # Random pixels barely compress: the worst case for file size.
        image = Image.frombytes(mode, (width, height), os.urandom(width * height * len(mode)))
    else:
        image = Image.new(mode, (width, height), "#3366aa")
    buffer = io.BytesIO()
    kwargs = {"exif": exif} if exif is not None else {}
    image.save(buffer, format=fmt, **({"quality": 95} if fmt == "JPEG" else {}), **kwargs)
    return SimpleUploadedFile(name, buffer.getvalue(), content_type=f"image/{fmt.lower()}")


def gps_exif(orientation=None):
    exif = Image.Exif()
    exif[0x010F] = "PhoneMaker"  # camera make
    gps = exif.get_ifd(GPS_TAG)
    gps[1] = "N"
    gps[2] = (33.0, 25.0, 30.0)  # latitude
    gps[3] = "W"
    gps[4] = (94.0, 2.0, 50.0)  # longitude
    if orientation:
        exif[ORIENTATION_TAG] = orientation
    return exif


def stored(name):
    with default_storage.open(name) as f:
        data = f.read()
    return data, Image.open(io.BytesIO(data))


def upload(client, file):
    return client.post(PHOTO_URL, {"photo": file}, format="multipart")


@pytest.mark.django_db
class TestPhotoProcessing:
    def test_ph01_large_photo_is_resized_and_compressed(self, client_for, alice):
        # 6.75 MP of random noise saved at quality 95: ~7.5 MB, and the
        # hardest kind of picture to compress.
        response = upload(client_for(alice), image_upload(3000, 2250, noise=True))

        assert response.status_code == 200, response.data
        alice.profile.refresh_from_db()
        data, image = stored(alice.profile.photo.name)
        assert len(data) < 1024 * 1024
        assert max(image.size) <= 1080
        assert image.size == (1080, 810)  # aspect ratio kept
        assert image.format == "JPEG" and image.mode == "RGB"

    def test_ph02_thumbnail_is_created(self, client_for, alice):
        upload(client_for(alice), image_upload(1600, 900))

        alice.profile.refresh_from_db()
        data, thumb = stored(alice.profile.photo_thumbnail.name)
        assert thumb.size == (200, 200)  # square crop for avatars
        assert thumb.format == "JPEG"
        assert len(data) < 30 * 1024

    def test_ph03_gps_and_exif_are_removed(self, client_for, alice):
        upload(client_for(alice), image_upload(exif=gps_exif()))

        alice.profile.refresh_from_db()
        for name in (alice.profile.photo.name, alice.profile.photo_thumbnail.name):
            data, image = stored(name)
            assert len(image.getexif()) == 0
            assert b"Exif" not in data and b"PhoneMaker" not in data
            assert not image.info.get("xmp") and not image.info.get("icc_profile")

    def test_ph04_orientation_is_fixed(self, client_for, alice):
        # Sideways phone photo: pixels 800x600, EXIF says "rotate 90°".
        upload(client_for(alice), image_upload(800, 600, exif=gps_exif(orientation=6)))

        alice.profile.refresh_from_db()
        _, image = stored(alice.profile.photo.name)
        assert image.size == (600, 800)

    @pytest.mark.parametrize("fmt,name", [("PNG", "photo.png"), ("WEBP", "photo.webp")])
    def test_ph05_png_and_webp_are_accepted(self, client_for, alice, fmt, name):
        response = upload(client_for(alice), image_upload(fmt=fmt, name=name, mode="RGBA"))

        assert response.status_code == 200, response.data
        alice.profile.refresh_from_db()
        assert stored(alice.profile.photo.name)[1].mode == "RGB"

    def test_ph06_heic_is_accepted(self, client_for, alice):
        pytest.importorskip("pillow_heif")
        response = upload(client_for(alice), image_upload(fmt="HEIF", name="IMG_0001.HEIC"))

        assert response.status_code == 200, response.data

    def test_ph07_file_name_is_random(self, client_for, alice):
        upload(client_for(alice), image_upload(name="alice_selfie.jpg"))

        alice.profile.refresh_from_db()
        name = alice.profile.photo.name
        assert "alice" not in name and "selfie" not in name
        assert len(os.path.basename(name)) == len("0123456789abcdef0123456789abcdef.jpg")


@pytest.mark.django_db
class TestPhotoValidation:
    def test_ph08_over_10mb_is_rejected(self, client_for, alice):
        # Not even an image: proves the size check runs before Pillow.
        big = SimpleUploadedFile("big.jpg", b"\0" * (MAX_UPLOAD_BYTES + 1), content_type="image/jpeg")

        response = upload(client_for(alice), big)

        assert response.status_code == 400
        assert response.data["photo"] == [TOO_LARGE]
        alice.profile.refresh_from_db()
        assert not alice.profile.photo

    def test_ph09_non_image_named_jpg_is_rejected(self, client_for, alice):
        fake = SimpleUploadedFile("photo.jpg", b"%PDF-1.4 not really a photo", content_type="image/jpeg")

        response = upload(client_for(alice), fake)

        assert response.status_code == 400
        assert response.data["photo"] == [WRONG_TYPE]

    def test_ph10_gif_is_rejected(self, client_for, alice):
        response = upload(client_for(alice), image_upload(fmt="GIF", name="photo.gif", mode="P"))

        assert response.status_code == 400
        assert response.data["photo"] == [WRONG_TYPE]

    def test_ph11_missing_file_is_rejected(self, client_for, alice):
        response = client_for(alice).post(PHOTO_URL, {}, format="multipart")

        assert response.status_code == 400
        assert "photo" in response.data

    def test_ph12_needs_a_profile_first(self, client_for, make_student):
        carol = make_student("carol")  # no profile

        response = upload(client_for(carol), image_upload())

        assert response.status_code == 400


@pytest.mark.django_db
class TestPhotoFiles:
    def test_ph13_replacing_deletes_old_files(self, client_for, alice, django_capture_on_commit_callbacks):
        client = client_for(alice)
        with django_capture_on_commit_callbacks(execute=True):
            upload(client, image_upload())
        alice.profile.refresh_from_db()
        old = (alice.profile.photo.name, alice.profile.photo_thumbnail.name)

        with django_capture_on_commit_callbacks(execute=True):
            upload(client, image_upload(fmt="PNG", name="new.png"))

        alice.profile.refresh_from_db()
        assert alice.profile.photo.name not in old
        assert all(not default_storage.exists(name) for name in old)
        assert default_storage.exists(alice.profile.photo.name)
        assert default_storage.exists(alice.profile.photo_thumbnail.name)

    def test_ph14_remove_deletes_files(self, client_for, alice, django_capture_on_commit_callbacks):
        client = client_for(alice)
        with django_capture_on_commit_callbacks(execute=True):
            upload(client, image_upload())
        alice.profile.refresh_from_db()
        old = (alice.profile.photo.name, alice.profile.photo_thumbnail.name)

        with django_capture_on_commit_callbacks(execute=True):
            response = client.delete(PHOTO_URL)

        assert response.status_code == 200
        assert response.data["photo_url"] is None and response.data["thumbnail_url"] is None
        assert all(not default_storage.exists(name) for name in old)

    def test_ph15_deleting_account_deletes_files(self, client_for, alice, django_capture_on_commit_callbacks):
        with django_capture_on_commit_callbacks(execute=True):
            upload(client_for(alice), image_upload())
        alice.profile.refresh_from_db()
        names = (alice.profile.photo.name, alice.profile.photo_thumbnail.name)
        assert all(default_storage.exists(name) for name in names)

        with django_capture_on_commit_callbacks(execute=True):
            alice.delete()

        assert all(not default_storage.exists(name) for name in names)


@pytest.mark.django_db
class TestPhotoPermissions:
    def test_ph16_login_required(self, api_client):
        assert upload(api_client, image_upload()).status_code == 401
        assert api_client.delete(PHOTO_URL).status_code == 401

    def test_ph17_cannot_change_someone_elses_photo(self, client_for, alice, bob, django_capture_on_commit_callbacks):
        with django_capture_on_commit_callbacks(execute=True):
            upload(client_for(alice), image_upload())
        alice.profile.refresh_from_db()
        alice_photo = alice.profile.photo.name
        bob_client = client_for(bob)

        # The upload URL has no user id: it is always "my" photo...
        with django_capture_on_commit_callbacks(execute=True):
            upload(bob_client, image_upload())
            bob_client.delete(PHOTO_URL)
        # ...and Alice's public profile URL is read-only.
        alice_url = reverse("profiles:profile-detail", kwargs={"pk": alice.profile.pk})
        put = bob_client.put(alice_url, {"photo": image_upload()}, format="multipart")
        delete = bob_client.delete(alice_url)

        assert put.status_code == 405 and delete.status_code == 405
        alice.profile.refresh_from_db()
        assert alice.profile.photo.name == alice_photo
        assert default_storage.exists(alice_photo)


@pytest.mark.django_db
class TestPhotoUrls:
    def test_ph18_urls_are_null_without_photo(self, client_for, alice):
        data = client_for(alice).get(ME_URL).data

        assert data["photo_url"] is None and data["thumbnail_url"] is None

    def test_ph19_urls_appear_in_profile_responses(self, client_for, alice, bob):
        upload(client_for(alice), image_upload())
        alice.profile.refresh_from_db()

        mine = client_for(alice).get(ME_URL).data
        theirs = client_for(bob).get(reverse("profiles:profile-list")).data[0]

        for data in (mine, theirs):
            assert data["photo_url"] == f"/media/{alice.profile.photo.name}"
            assert data["thumbnail_url"] == f"/media/{alice.profile.photo_thumbnail.name}"

    def test_ph20_thumbnail_in_connections_and_chats(self, client_for, alice, bob):
        from connections.models import Connection

        upload(client_for(alice), image_upload())
        alice.profile.refresh_from_db()
        Connection.objects.create(from_user=alice, to_user=bob, status="accepted")

        friends = client_for(bob).get(reverse("connections:connection-list")).data
        assert friends[0]["user"]["thumbnail_url"] == alice.profile.photo_thumbnail.url

    def test_ph21_can_view_own_profile(self, client_for, alice):
        url = reverse("profiles:profile-detail", kwargs={"pk": alice.profile.pk})

        assert client_for(alice).get(url).status_code == 200
