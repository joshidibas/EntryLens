# InsightFace Colab Setup

This folder documents the temporary Google Colab inference endpoint used by Labs for the `InsightFace (Colab)` model option.

## What Runs Where

- `entrylens-frontend/` stays local in this repo
- `entrylens-api/` stays local in this repo
- Google Colab runs the temporary InsightFace image-to-embedding endpoint
- Supabase stays the persistence and similarity-search layer

The frontend does **not** call Colab directly. EntryLens API calls Colab using:

- `INSIGHTFACE_COLAB_URL`
- `INSIGHTFACE_COLAB_TOKEN`
- `INSIGHTFACE_TIMEOUT_SECONDS`

## VS Code Reality Check

Google Colab itself does not run "inside VS Code" as a native runtime in this repo.

The practical workflow is:

1. Use VS Code to edit this repository and your notes.
2. Open a notebook in Google Colab in the browser.
3. Run the notebook there.
4. Copy the Colab endpoint URL/token back into this repo's `.env`.

If you want a notebook-like experience entirely inside VS Code later, that is a separate path using the Jupyter extension and a local Python environment, not Google Colab.

## What You Need To Do

### Step 1: Create a Colab notebook

Create a new notebook in Google Colab named something like:

- `entrylens-insightface-endpoint.ipynb`

### Step 2: Install notebook packages in Colab

Run a setup cell like this:

```python
!pip install insightface==0.7.3 onnxruntime==1.17.1 pillow fastapi uvicorn pyngrok python-multipart
```

### Step 3: Add the Colab endpoint code

Use a notebook cell like this as the starting point:

```python
import base64
import io
from typing import Any

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from PIL import Image
import uvicorn

app = FastAPI(title="EntryLens InsightFace Colab")

AUTH_TOKEN = "replace-this-with-a-long-random-string"


class EmbedRequest(BaseModel):
    image_base64: str
    image_extension: str | None = None


def decode_image(image_base64: str) -> Image.Image:
    raw = base64.b64decode(image_base64)
    return Image.open(io.BytesIO(raw)).convert("RGB")


def extract_embedding_from_image(image: Image.Image) -> dict[str, Any]:
    # Replace this placeholder with the real InsightFace app/model call.
    # Return a 512-length embedding list.
    raise NotImplementedError("Wire InsightFace model loading here")


@app.post("/")
async def embed(request: EmbedRequest):
    try:
        image = decode_image(request.image_base64)
        result = extract_embedding_from_image(image)
        return {
            "face_detected": True,
            "embedding": result["embedding"],
            "bbox": result.get("bbox"),
            "confidence": result.get("confidence"),
        }
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc
```

### Step 4: Expose the Colab endpoint

Use a tunnel so your local API can call the notebook runtime.

One common pattern in Colab is:

```python
from pyngrok import ngrok
import threading

public_url = ngrok.connect(8000, "http")
print("Public URL:", public_url)

thread = threading.Thread(
    target=uvicorn.run,
    kwargs={"app": app, "host": "0.0.0.0", "port": 8000},
    daemon=True,
)
thread.start()
```

Copy the printed public URL.

### Step 5: Set repo env vars locally

Add these to your local `.env` in the repo root:

```env
INSIGHTFACE_COLAB_URL=https://your-colab-tunnel-url.ngrok-free.app/
INSIGHTFACE_COLAB_TOKEN=replace-this-with-the-same-long-random-string
INSIGHTFACE_TIMEOUT_SECONDS=20
```

If you add auth enforcement in the Colab notebook, keep the token in sync with the backend.

## Recommended First Bring-Up Sequence

1. Run the notebook in Colab.
2. Confirm it returns JSON from the public URL.
3. Update local `.env`.
4. Restart the local FastAPI server.
5. Open Labs.
6. Choose `InsightFace (Colab)` from the model dropdown.
7. Test Enroll first.
8. Test Identify second.

## Minimum Manual Checks

Before touching the app UI, test the Colab endpoint manually with a REST client or PowerShell.

Expected response shape:

```json
{
  "face_detected": true,
  "embedding": [0.1, 0.2, 0.3],
  "bbox": null,
  "confidence": null
}
```

The backend currently expects the InsightFace path to return a **512-length numeric embedding**.

## Important Limitations

- Colab URLs are temporary.
- Colab runtimes sleep.
- This is for Labs experimentation first, not production hosting.
- You still need to apply the Supabase SQL changes before InsightFace samples can be stored and searched cleanly.

## Local Repo Changes That Depend On This

The local API now looks for these settings in `.env.example`:

- `INSIGHTFACE_COLAB_URL`
- `INSIGHTFACE_COLAB_TOKEN`
- `INSIGHTFACE_TIMEOUT_SECONDS`

The local Labs UI now exposes the `InsightFace (Colab)` model option for Local Recognition.
