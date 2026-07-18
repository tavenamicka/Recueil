import shutil
import tempfile
from pathlib import Path
from uuid import uuid4

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, UploadFile
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.db.session import get_db
from app.schemas.import_ import ImportStatus, ImportTxtStarted, MediaOut
from app.services.import_service import get_job, run_txt_import
from app.services.media_service import save_media

router = APIRouter(prefix="/import", tags=["import"], dependencies=[Depends(get_current_user)])


@router.post("/txt", response_model=ImportTxtStarted, status_code=202)
async def import_txt(background_tasks: BackgroundTasks, file: UploadFile):
    if not file.filename.lower().endswith(".txt"):
        raise HTTPException(
            status_code=400,
            detail="Seuls les fichiers .txt (export WhatsApp) sont acceptés pour cet import.",
        )

    job_id = uuid4().hex
    tmp_path = Path(tempfile.gettempdir()) / f"recueil-import-{job_id}.txt"
    with tmp_path.open("wb") as out:
        shutil.copyfileobj(file.file, out)

    background_tasks.add_task(run_txt_import, job_id, tmp_path)
    return ImportTxtStarted(job_id=job_id)


@router.get("/txt/{job_id}", response_model=ImportStatus)
def import_txt_status(job_id: str):
    job = get_job(job_id)
    if job is None:
        raise HTTPException(status_code=404, detail="Import introuvable.")
    return job


@router.post("/media", response_model=MediaOut, status_code=201)
def import_media(file: UploadFile, db: Session = Depends(get_db)):
    return save_media(db, file)
