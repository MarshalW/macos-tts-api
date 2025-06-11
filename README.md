# macOS TTS api

将 macos 系统 TTS 功能封装成 api 接口：

```bash
curl -o test.wav -X POST "http://localhost:7760/convert/tts" \
  -H "Content-Type: application/json" \
  -d '{"text": "李在明还强调，要警惕社会充满厌恶情绪，进而出现分裂对抗。"}'
```

启动服务：

```bash
git clone https://github.com/MarshalW/macos-tts-api.git
cd macos-tts-api
# 安装依赖
pip install -r requirements.txt

uvicorn app.main:app --host 0.0.0.0 --port 7760 --reload
```

效果：

<video controls>
  <source src="https://raw.githubusercontent.com/MarshalW/macos-tts-api/refs/heads/main/example.mp4" type="video/mp4">
  Your browser does not support the video tag.
</video>