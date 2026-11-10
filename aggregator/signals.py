"""Conservative descriptive signals; never interpret them as residential seller leads."""
import json
from datetime import datetime, timezone

def build_signals(records):
    out=[]
    for r in records:
        p=r["payload"]; source=r["source"]; explanation="Official-source event retained for research; manually verify context."
        entity=""; geography=""; kind="context"
        if source=="sec":
            entity=p.get("company",""); kind="corporate_filing"
            form=p.get("form","")
            explanation=f"{entity} filed SEC form {form} on {p.get('filed','unknown date')}. Review the filing itself; do not infer property availability."
            score=0.0
        elif source=="illinois_warn":
            kind="reported_labor_notice"
            entity=next((v for k,v in p.items() if "company" in k.lower()),"")
            geography=next((v for k,v in p.items() if "city" in k.lower()),"")
            explanation="Illinois WARN monthly report entry. A notice is not proof of property distress, ownership, or seller intent."
            score=0.0
        elif source=="campd":
            kind="power_sector_emissions_observation"
            entity=str(p.get("facilityName") or p.get("facilityId") or "EPA facility")
            geography=str(p.get("state") or "")
            explanation="EPA CAMPD emissions observation. Environmental data is not a property condition report or a residential lead."
            score=0.0
        else:
            continue
        out.append({"source":source,"source_id":r["source_id"],"signal_type":kind,
            "signal_date":r.get("published_at"),"entity":entity,"geography":geography,
            "score":score,"explanation":explanation,"source_url":r["source_url"],
            "created_at":datetime.now(timezone.utc).isoformat()})
    return out
