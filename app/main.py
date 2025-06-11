# from fastapi import FastAPI
from app.core.config import settings

from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.responses import FileResponse
import subprocess
import os
import uuid
from pydantic import BaseModel
import logging
from fastapi.middleware.cors import CORSMiddleware

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)

app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.PROJECT_VERSION
)

# 添加无限制 CORS 中间件
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 允许所有来源（生产环境建议指定具体域名）
    allow_credentials=True,
    allow_methods=["*"],  # 允许所有方法（GET/POST等）
    allow_headers=["*"],  # 允许所有请求头
)

@app.get("/")
async def hello():
    return {"message": "Hello FastAPI🚀"}

class TextToSpeechRequest(BaseModel):
    text: str
    
def cleanup_files(*files):
    """清理临时文件的辅助函数"""
    for file_path in files:
        try:
            if os.path.exists(file_path):
                os.remove(file_path)
                logger.info(f"Cleaned up: {file_path}")
        except Exception as e:
            logger.warning(f"Error cleaning up {file_path}: {str(e)}")

@app.post("/convert/tts")
async def convert_text_to_speech(request: TextToSpeechRequest, background_tasks: BackgroundTasks):
    temp_id = str(uuid.uuid4())
    temp_aiff = f"/tmp/{temp_id}.aiff"
    temp_wav = f"/tmp/{temp_id}.wav"
    
    try:
        # 生成AIFF文件
        logger.info(f"生成AIFF文件: {temp_aiff}")
        say_cmd = ["say", "-o", temp_aiff, request.text]
        say_result = subprocess.run(say_cmd, capture_output=True, text=True)
        
        if say_result.returncode != 0 or not os.path.exists(temp_aiff):
            error_msg = f"语音合成失败: {say_result.stderr}"
            logger.error(error_msg)
            raise HTTPException(status_code=500, detail=error_msg)

        # 转换为WAV格式
        logger.info(f"转换为WAV文件: {temp_wav}")
        ffmpeg_cmd = [
            "ffmpeg", "-i", temp_aiff,
            "-acodec", "pcm_s16le",
            "-ar", "44100",
            "-ac", "1",
            "-y",
            temp_wav
        ]
        
        # 添加详细的FFmpeg日志输出
        ffmpeg_result = subprocess.run(
            ffmpeg_cmd, 
            capture_output=True, 
            text=True,
            encoding="utf-8"
        )
        
        if ffmpeg_result.returncode != 0 or not os.path.exists(temp_wav):
            error_msg = f"WAV转换失败: {ffmpeg_result.stderr}"
            logger.error(error_msg)
            raise HTTPException(status_code=500, detail=error_msg)
        
        # 注册文件清理任务（在文件传输完成后执行）
        background_tasks.add_task(cleanup_files, temp_aiff, temp_wav)
        
        # 返回文件响应
        return FileResponse(
            temp_wav,
            media_type="audio/wav",
            filename="output.wav"
        )

    except Exception as e:
        # 立即清理出错的临时文件
        cleanup_files(temp_aiff, temp_wav)
        logger.exception(f"处理过程中出错: {str(e)}")
        raise HTTPException(status_code=500, detail=f"内部错误: {str(e)}")