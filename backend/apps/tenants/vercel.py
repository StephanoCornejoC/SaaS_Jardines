"""
Integración con la API de Vercel: alta automática del subdominio de cada
jardín nuevo en el proyecto del frontend.

Por qué:
El frontend es UNA sola app en Vercel, servida por subdominio
(`<slug>.miniddo.com`). Para que un jardín nuevo cargue SIN intervención
manual, su subdominio tiene que existir en el proyecto Vercel.
- Un wildcard `*.miniddo.com` lo resolvería, pero Vercel lo restringe al
  plan Pro (~US$20/mes).
- Agregando cada dominio por API nos quedamos en el plan Hobby ($0) y
  escala igual: el alta de jardín registra el subdominio automáticamente.

Config (env vars → settings):
- VERCEL_TOKEN: token de API (Vercel > Account Settings > Tokens).
- VERCEL_PROJECT_ID: id o nombre del proyecto (ej. "saas-jardines").
- VERCEL_TEAM_ID: opcional; solo si el proyecto vive en un team.

Si VERCEL_TOKEN/PROJECT no están seteados (dev/local), es NO-OP: loguea y
retorna sin error, para no bloquear el alta de jardines en desarrollo.

Usa urllib (stdlib) a propósito: cero dependencias nuevas.
"""
import json
import logging
import urllib.error
import urllib.request

from django.conf import settings

logger = logging.getLogger(__name__)

VERCEL_API = "https://api.vercel.com"


def add_domain_to_vercel(domain: str) -> dict:
    """
    Agrega `domain` al proyecto Vercel configurado.

    Idempotente y a prueba de fallos: NUNCA lanza excepción — devuelve un
    dict con el resultado para que el caller lo loguee. Un fallo acá no debe
    tumbar el alta del jardín (el dominio siempre se puede agregar a mano).
    """
    token = getattr(settings, "VERCEL_TOKEN", "") or ""
    project = getattr(settings, "VERCEL_PROJECT_ID", "") or ""

    if not token or not project:
        logger.warning(
            "Vercel: VERCEL_TOKEN/PROJECT_ID no configurados; se omite el alta "
            "automática del dominio %s (agregarlo manual en Vercel).", domain,
        )
        return {"ok": False, "skipped": True, "domain": domain}

    team_id = getattr(settings, "VERCEL_TEAM_ID", "") or ""
    url = f"{VERCEL_API}/v10/projects/{project}/domains"
    if team_id:
        url += f"?teamId={team_id}"

    body = json.dumps({"name": domain}).encode("utf-8")
    req = urllib.request.Request(
        url,
        data=body,
        method="POST",
        headers={
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
        },
    )
    try:
        with urllib.request.urlopen(req, timeout=10) as resp:
            payload = json.loads(resp.read().decode("utf-8"))
        logger.info("Vercel: dominio %s agregado al proyecto %s.", domain, project)
        return {"ok": True, "domain": domain, "response": payload}
    except urllib.error.HTTPError as e:
        detail = e.read().decode("utf-8", "ignore")
        # 409 o "already exists" → el dominio ya estaba: éxito idempotente.
        if e.code == 409 or "already" in detail.lower() or "exists" in detail.lower():
            logger.info("Vercel: dominio %s ya existía (idempotente).", domain)
            return {"ok": True, "domain": domain, "already": True}
        logger.error("Vercel: error %s agregando %s: %s", e.code, domain, detail)
        return {"ok": False, "domain": domain, "status": e.code, "error": detail}
    except Exception as e:  # noqa: BLE001 — a prueba de fallos por diseño
        logger.exception("Vercel: fallo de red agregando %s: %s", domain, e)
        return {"ok": False, "domain": domain, "error": str(e)}
