import { useEffect, useRef, useState, type ChangeEvent } from "react";
import { apiDelete, apiUpload, errorMessage, fieldErrors } from "../api/client";
import type { MyProfile } from "../api/types";
import { Alert, Avatar, Button } from "./ui";

// Same rules as the backend (profiles/photos.py); checked here first so
// students get the message instantly instead of after a 10 MB upload.
const MAX_BYTES = 10 * 1024 * 1024;
const ALLOWED_TYPES = ["image/jpeg", "image/png", "image/webp", "image/heic", "image/heif"];
// Some browsers report HEIC files with an empty type, so also go by extension.
const ALLOWED_EXTENSIONS = /\.(jpe?g|png|webp|heic|heif)$/i;
const TOO_LARGE = "That photo is too large. The maximum size is 10 MB.";
const WRONG_TYPE = "Please upload a JPG, PNG, WebP or HEIC photo.";

function checkFile(file: File): string | null {
  if (!ALLOWED_TYPES.includes(file.type) && !ALLOWED_EXTENSIONS.test(file.name)) return WRONG_TYPE;
  if (file.size > MAX_BYTES) return TOO_LARGE;
  return null;
}

/**
 * Profile photo on the edit page: choose -> preview -> upload, or remove.
 * Uploads straight away (separately from "Save changes"), since the server
 * processes the photo and returns the new URLs.
 */
export default function PhotoUpload({
  name,
  photoUrl,
  onChange,
}: {
  name: string;
  photoUrl: string | null;
  /** Called with the updated profile after an upload or removal. */
  onChange: (profile: MyProfile) => void;
}) {
  const inputRef = useRef<HTMLInputElement>(null);
  const [file, setFile] = useState<File | null>(null);
  const [preview, setPreview] = useState<string | null>(null);
  const [previewFailed, setPreviewFailed] = useState(false);
  const [busy, setBusy] = useState<"upload" | "remove" | null>(null);
  const [error, setError] = useState("");

  // Free the preview's memory when it's replaced or the page closes.
  useEffect(() => () => {
    if (preview) URL.revokeObjectURL(preview);
  }, [preview]);

  function choose(e: ChangeEvent<HTMLInputElement>) {
    const chosen = e.target.files?.[0];
    e.target.value = ""; // so choosing the same file again still fires onChange
    if (!chosen) return;
    const problem = checkFile(chosen);
    setError(problem ?? "");
    if (problem) return clearSelection();
    setFile(chosen);
    setPreviewFailed(false);
    setPreview(URL.createObjectURL(chosen));
  }

  function clearSelection() {
    setFile(null);
    setPreview(null);
  }

  async function upload() {
    if (!file) return;
    const form = new FormData();
    form.append("photo", file);
    setBusy("upload");
    setError("");
    try {
      onChange(await apiUpload<MyProfile>("/api/profiles/me/photo/", form));
      clearSelection();
    } catch (err) {
      setError(fieldErrors(err).photo ?? errorMessage(err));
    } finally {
      setBusy(null);
    }
  }

  async function remove() {
    setBusy("remove");
    setError("");
    try {
      onChange(await apiDelete<MyProfile>("/api/profiles/me/photo/"));
    } catch (err) {
      setError(errorMessage(err));
    } finally {
      setBusy(null);
    }
  }

  return (
    <div className="space-y-3" data-testid="photo-upload">
      <p className="text-sm font-medium">Profile photo</p>
      <div className="flex flex-col items-start gap-5 sm:flex-row sm:items-center">
        {preview && !previewFailed ? (
          <img
            src={preview}
            alt="Preview of your new photo"
            data-testid="photo-preview"
            onError={() => setPreviewFailed(true)}
            className="h-20 w-20 shrink-0 rounded-full bg-sand object-cover"
          />
        ) : preview ? (
          // e.g. HEIC in Chrome: the server can read it even if the browser can't show it.
          <div className="flex h-20 w-20 shrink-0 items-center justify-center rounded-full bg-sand p-2 text-center text-[10px] text-muted">
            No preview
          </div>
        ) : (
          <Avatar name={name} src={photoUrl} size="lg" />
        )}

        <div className="space-y-2">
          <input
            ref={inputRef}
            type="file"
            name="photo"
            accept="image/jpeg,image/png,image/webp,image/heic,image/heif,.heic,.heif"
            onChange={choose}
            // Visually hidden (the buttons open it) but still in the page,
            // so keyboards, screen readers and the UI tests can reach it.
            className="sr-only"
            aria-label="Choose a profile photo"
          />
          <div className="flex flex-wrap gap-2">
            {file ? (
              <>
                <Button type="button" onClick={upload} loading={busy === "upload"}>
                  {busy === "upload" ? "Uploading…" : "Upload photo"}
                </Button>
                <Button type="button" variant="ghost" onClick={clearSelection} disabled={!!busy}>
                  Cancel
                </Button>
              </>
            ) : (
              <>
                <Button type="button" variant="ghost" className="border border-line"
                  onClick={() => inputRef.current?.click()} disabled={!!busy}>
                  {photoUrl ? "Change photo" : "Choose photo"}
                </Button>
                {photoUrl && (
                  <Button type="button" variant="ghost" onClick={remove} loading={busy === "remove"}>
                    Remove photo
                  </Button>
                )}
              </>
            )}
          </div>
          <p className="text-xs text-muted">
            {file ? file.name : "JPG, PNG, WebP or HEIC, up to 10 MB. Location data is removed."}
          </p>
        </div>
      </div>
      {error && <Alert>{error}</Alert>}
    </div>
  );
}
