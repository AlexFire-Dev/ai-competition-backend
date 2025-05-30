import os
import uuid
import aiofiles
from fastapi import APIRouter, UploadFile, HTTPException
from fastapi.responses import FileResponse

router = APIRouter()
MEDIA_DIR = "media"


@router.post("/uploadfile")
async def create_upload_file(file: UploadFile):
    file_name = str(uuid.uuid4())
    extension = file.filename.split('.')[1]

    async with aiofiles.open(f"{MEDIA_DIR}/{file_name}.{extension}", 'wb') as out_file:
        content = await file.read()
        await out_file.write(content)

    result = {
        "status": "ok",
        "original_file": f"/loadfile/{file_name}.{extension}"
    }

    return result


@router.get("/loadfile/{file_path}", response_class=FileResponse)
async def load_file(file_path: str):
    full_path = os.path.join(MEDIA_DIR, file_path)
    if not os.path.isfile(full_path):
        raise HTTPException(404, "No such file")

    return FileResponse(
        path=full_path,
        media_type="application/octet-stream",
        filename=os.path.basename(full_path),
    )
