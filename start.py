import uvicorn, os

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8000))
    is_render = os.environ.get("RENDER") == "true"
    uvicorn.run("main:app", host="0.0.0.0", port=port, reload=not is_render)
