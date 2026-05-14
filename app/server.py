import uvicorn


def run(host: str = "127.0.0.1", port: int = 8000) -> None:
    uvicorn.run("app.main:app", host=host, port=port, reload=False)


if __name__ == "__main__":
    run()
