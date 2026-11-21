"""UI test: profile photo upload. ID (UI-...) matches docs/test-cases.md."""

import pytest
from PIL import Image
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC

from profiles.models import Profile

from helpers import click_button, log_in_as  # tests_ui/helpers.py

pytestmark = pytest.mark.django_db(transaction=True)


@pytest.fixture
def media(settings, tmp_path):
    """Uploads go to a temp folder, served at /media/ by the test server."""
    settings.MEDIA_ROOT = tmp_path / "media"
    settings.ROOT_URLCONF = "media_urls"  # tests_ui/media_urls.py
    return settings.MEDIA_ROOT


def test_ui30_upload_photo_and_see_it_on_profile(page, wait, alice, media, tmp_path):
    Profile.objects.filter(user=alice).update(date_of_birth="2004-03-15")
    photo = tmp_path / "IMG_2041.jpg"
    Image.new("RGB", (2400, 1600), "#c0563f").save(photo, quality=95)
    log_in_as(page, alice, "/profile/edit")

    # Choose a file: the preview appears before anything is uploaded.
    wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "input[type=file]"))).send_keys(str(photo))
    wait.until(EC.visibility_of_element_located((By.CSS_SELECTOR, "[data-testid=photo-preview]")))
    click_button(wait, "Upload photo")
    wait.until(EC.element_to_be_clickable((By.XPATH, "//button[normalize-space()='Change photo']")))

    # Open "View my profile": the processed photo is shown and actually loads.
    page.find_element(By.LINK_TEXT, "View my profile").click()
    img = wait.until(EC.visibility_of_element_located((By.CSS_SELECTOR, "article img[alt=alice]")))
    wait.until(lambda _: page.execute_script("return arguments[0].naturalWidth", img) > 0)

    alice.profile.refresh_from_db()
    assert img.get_attribute("src").endswith(f"/media/{alice.profile.photo.name}")
    assert page.execute_script("return arguments[0].naturalWidth", img) == 1080
