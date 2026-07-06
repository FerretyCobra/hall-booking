"""IT feature management: the catalog, its options, and hall assignments.

Three surfaces, matching the data model:
  * feature_catalog  -> what feature TYPES exist (global)
  * feature_options  -> allowed values for select features (global, IT-managed)
  * hall_features    -> what a specific hall actually has (per-hall)
"""
from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session

from ..database import get_db, transaction
from ..models import FeatureCatalog, FeatureOption, HallFeature, Hall, User
from ..schemas import FeatureIn, FeaturePatch, OptionIn, OptionPatch, HallFeatureIn
from ..security import require_admin
from ..services import audit

router = APIRouter(prefix="/api/admin/features", tags=["admin:features"])

VALUE_TYPES = {"bool", "number", "text", "single_select", "multi_select"}


def _feature_dict(f: FeatureCatalog):
    return {
        "id": f.id, "name": f.name, "value_type": f.value_type, "active": f.active,
        "options": [
            {"id": o.id, "label": o.label, "active": o.active, "sort_order": o.sort_order}
            for o in sorted(f.options, key=lambda o: (o.sort_order, o.label))
        ],
    }


# ---- catalog ----
@router.get("")
def list_features(db: Session = Depends(get_db), user: User = Depends(require_admin)):
    feats = db.query(FeatureCatalog).order_by(FeatureCatalog.name).all()
    return [_feature_dict(f) for f in feats]


@router.post("")
def create_feature(payload: FeatureIn, request: Request,
                   db: Session = Depends(get_db), user: User = Depends(require_admin)):
    if payload.value_type not in VALUE_TYPES:
        raise HTTPException(400, f"value_type must be one of {sorted(VALUE_TYPES)}")
    with transaction(db):
        f = FeatureCatalog(name=payload.name.strip(), value_type=payload.value_type)
        db.add(f)
        db.flush()
        audit.log(db, "feature.create", entity="feature", entity_id=f.id,
                  actor=user.username, actor_ip=request.client.host, detail=f.name)
        fid = f.id
    return _feature_dict(db.get(FeatureCatalog, fid))


@router.patch("/{feature_id}")
def update_feature(feature_id: int, payload: FeaturePatch, request: Request,
                   db: Session = Depends(get_db), user: User = Depends(require_admin)):
    with transaction(db):
        f = db.get(FeatureCatalog, feature_id)
        if not f:
            raise HTTPException(404, "Feature not found.")
        if payload.name is not None:
            f.name = payload.name.strip()
        if payload.value_type is not None:
            if payload.value_type not in VALUE_TYPES:
                raise HTTPException(400, "Invalid value_type.")
            f.value_type = payload.value_type
        if payload.active is not None:
            f.active = payload.active
        audit.log(db, "feature.update", entity="feature", entity_id=f.id,
                  actor=user.username, actor_ip=request.client.host)
    return _feature_dict(db.get(FeatureCatalog, feature_id))


# ---- options ----
@router.post("/{feature_id}/options")
def add_option(feature_id: int, payload: OptionIn, request: Request,
               db: Session = Depends(get_db), user: User = Depends(require_admin)):
    with transaction(db):
        f = db.get(FeatureCatalog, feature_id)
        if not f:
            raise HTTPException(404, "Feature not found.")
        opt = FeatureOption(feature_id=feature_id, label=payload.label.strip(),
                            sort_order=payload.sort_order)
        db.add(opt)
        db.flush()
        audit.log(db, "option.create", entity="option", entity_id=opt.id,
                  actor=user.username, actor_ip=request.client.host,
                  detail=f"{f.name}: {opt.label}")
    return _feature_dict(db.get(FeatureCatalog, feature_id))


@router.patch("/options/{option_id}")
def update_option(option_id: int, payload: OptionPatch, request: Request,
                  db: Session = Depends(get_db), user: User = Depends(require_admin)):
    """Rename survives everywhere (halls reference option_id). Retiring an option
    is a soft-delete (active=False) so halls that use it aren't orphaned."""
    with transaction(db):
        opt = db.get(FeatureOption, option_id)
        if not opt:
            raise HTTPException(404, "Option not found.")
        if payload.label is not None:
            opt.label = payload.label.strip()
        if payload.active is not None:
            opt.active = payload.active
        if payload.sort_order is not None:
            opt.sort_order = payload.sort_order
        fid = opt.feature_id
        audit.log(db, "option.update", entity="option", entity_id=opt.id,
                  actor=user.username, actor_ip=request.client.host)
    return _feature_dict(db.get(FeatureCatalog, fid))


# ---- per-hall assignment ----
@router.get("/hall/{hall_id}")
def hall_features(hall_id: int, db: Session = Depends(get_db),
                  user: User = Depends(require_admin)):
    rows = db.query(HallFeature).filter(HallFeature.hall_id == hall_id).all()
    return [
        {"id": r.id, "feature_id": r.feature_id, "option_id": r.option_id,
         "value": r.value, "quantity": r.quantity}
        for r in rows
    ]


@router.post("/hall/{hall_id}")
def assign_feature(hall_id: int, payload: HallFeatureIn, request: Request,
                   db: Session = Depends(get_db), user: User = Depends(require_admin)):
    with transaction(db):
        if not db.get(Hall, hall_id):
            raise HTTPException(404, "Hall not found.")
        hf = HallFeature(hall_id=hall_id, feature_id=payload.feature_id,
                         option_id=payload.option_id, value=payload.value,
                         quantity=payload.quantity)
        db.add(hf)
        db.flush()
        rid = hf.id
        audit.log(db, "hall_feature.assign", entity="hall", entity_id=hall_id,
                  actor=user.username, actor_ip=request.client.host)
    return {"id": rid}


@router.delete("/hall/assignment/{assignment_id}")
def remove_assignment(assignment_id: int, request: Request,
                      db: Session = Depends(get_db), user: User = Depends(require_admin)):
    with transaction(db):
        hf = db.get(HallFeature, assignment_id)
        if not hf:
            raise HTTPException(404, "Assignment not found.")
        db.delete(hf)
        audit.log(db, "hall_feature.remove", entity="hall", entity_id=hf.hall_id,
                  actor=user.username, actor_ip=request.client.host)
    return {"status": "removed"}
