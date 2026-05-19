from fastapi import APIRouter, Query
from typing import Optional
from src.services.keepcon import KeepconService

router = APIRouter()
service = KeepconService()

@router.get("/data")
def get_keepcon_data(
    days: int = Query(1, description="Días hacia atrás a consultar"),
    sentiment: Optional[str] = Query(None, description="Filtro de sentimiento (positivo, negativo, neutral, todos)"),
    source: Optional[str] = Query(None, description="Filtro de red social (twitter, facebook, instagram)"),
    influencer: Optional[str] = Query(None, description="Filtro influencer (todos, influencer, no_influencer)")
):
    """
    Obtiene los datos de Keepcon desde el CSV. Si no hay datos suficientes para los días solicitados,
    dispara la obtención automática hacia la API de Keepcon.
    """
    try:
        data = service.get_dashboard_data(
            days_filter=days,
            sentiment_filter=sentiment,
            source_filter=source,
            influencer_filter=influencer,
        )
        return {
            "status": "success",
            "metrics": service.build_metrics(data),
            "filters": {"days": days, "sentiment": sentiment or "todos", "source": source or "todas", "influencer": influencer or "todos"},
            "data": data
        }
    except Exception as e:
        import traceback
        traceback.print_exc()
        return {"status": "error", "message": str(e), "data": [], "metrics": {}}

@router.post("/refresh")
def refresh_keepcon_data(
    days: int = Query(1, description="Días hacia atrás a actualizar")
):
    """
    Refresca los datos del día actual llamando a la API de Keepcon.
    Se ejecuta de forma sincrónica para devolver confirmación, o en background.
    Lo haremos sincrónico para el botón de refresh.
    """
    try:
        result = service.refresh_latest(days_filter=days)
        new_records = result["new_records"]
        status_updates = result.get("status_updates", 0)
        metadata_updates = result.get("metadata_updates", 0)
        profile_updates = result.get("profile_updates", 0)
        if new_records or status_updates or metadata_updates or profile_updates:
            message = (
                f"Keepcon actualizado: {new_records} nuevas, "
                f"{status_updates} cambios de estado, "
                f"{metadata_updates} metadata y {profile_updates} perfil."
            )
        else:
            message = "Keepcon actualizado: no se encontraron registros nuevos ni cambios de estado."
        return {"status": "success", "message": message, **result}
    except Exception as e:
        return {"status": "error", "message": str(e)}

@router.get("/diagnostics/content")
def diagnose_keepcon_content(
    content_id: str = Query(..., description="ID de contenido Keepcon a inspeccionar"),
    created_at: Optional[str] = Query(None, description="Fecha de creación aproximada para acotar la búsqueda")
):
    """
    Diagnóstico de solo lectura para comparar los campos de estado que devuelve Keepcon.
    No modifica el CSV ni recalcula sentimiento.
    """
    try:
        return {"status": "success", **service.diagnose_content(content_id=content_id, created_at=created_at)}
    except Exception as e:
        return {"status": "error", "message": str(e)}
