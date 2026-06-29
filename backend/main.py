"""Entrypoint do backend: sobe o servidor ASGI do ARIS.

Uso: cd backend && python main.py  (ou: uvicorn aris.api.gateway:app --reload)
"""

import uvicorn

if __name__ == "__main__":
    uvicorn.run("aris.api.gateway:app", host="127.0.0.1", port=8000, reload=True)
