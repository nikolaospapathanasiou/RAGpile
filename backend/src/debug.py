import debugpy
import uvicorn
from watchfiles import run_process

DEBUG_PORT = 5678


def start():
    uvicorn.run("app:app", host="0.0.0.0", port=8000, reload=False)


if __name__ == "__main__":
    print(f"Debugger listening on port {DEBUG_PORT}...")
    debugpy.listen(("0.0.0.0", DEBUG_PORT))  # Allow remote connections
    run_process("./", target=start)  # Watch for file changes
