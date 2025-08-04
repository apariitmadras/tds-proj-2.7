# /// script
# requires-python = ">=3.11"
# dependencies = [
#   "fastapi",
#   "python-multipart",
#   "uvicorn",
#   "google-genai",
# ]
# ///
from fastapi import FastAPI, File, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from google import genai
import os

app = FastAPI()
app.add_middleware(CORSMiddleware, allow_origins=["*"])  # Allow requests from anywhere

# Extra CORS control (kept verbatim from the original)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

def task_breakdown(task: str):
    """Break a complex task into smaller programmable steps with Gemini Flash."""
    client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))
    prompt_path = os.path.join("prompts", "abdul_task_breakdown.txt")
    with open(prompt_path) as f:
        prompt = f.read()

    response = client.models.generate_content(
        model="gemini-2.0-flash-lite",
        contents=[task, prompt],
    )
    # Persist for inspection
    with open("abdul_breaked_task.txt", "w") as f:
        f.write(response.text)
    return response.text

@app.get("/")
async def root():
    return {"message": "Hello!"}

# Accepts:  curl -X POST "http://127.0.0.1:8000/api/" -F "file=@question.txt"
@app.post("/api/")
async def upload_file(file: UploadFile = File(...)):
    try:
        text = (await file.read()).decode("utf-8")
        breakdown = task_breakdown(text)
        print(breakdown)
        return {"filename": file.filename, "content": text}
    except Exception as e:
        return JSONResponse(status_code=400, content={"error": str(e)})

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
