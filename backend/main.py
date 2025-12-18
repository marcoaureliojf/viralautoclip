"""FastAPI应用入口点"""

import logging
import os
from typing import Optional
from fastapi import FastAPI, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, FileResponse
from fastapi.staticfiles import StaticFiles

# 导入配置管理
from .core.config import settings, get_logging_config, get_api_key

# 配置日志
logging_config = get_logging_config()
logging.basicConfig(
    level=getattr(logging, logging_config["level"]),
    format=logging_config["format"],
    handlers=[
        logging.StreamHandler(),  # 输出到控制台
        logging.FileHandler(logging_config["file"])  # 输出到文件
    ]
)

logger = logging.getLogger(__name__)

# 使用统一的API路由注册
from .api.v1 import api_router
from .core.database import engine
from .models.base import Base

# Create FastAPI app
app = FastAPI(
    title="AutoClip API",
    description="AI视频切片处理API",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# Create database tables
@app.on_event("startup")
async def startup_event():
    logger.info("启动AutoClip API服务...")
    # 导入所有模型以确保表被创建
    from .models.bilibili import BilibiliAccount, UploadRecord
    Base.metadata.create_all(bind=engine)
    logger.info("数据库表创建完成")
    
    # 加载API密钥到环境变量
    api_key = get_api_key()
    if api_key:
        import os
        os.environ["DASHSCOPE_API_KEY"] = api_key
        logger.info("API密钥已加载到环境变量")
    else:
        logger.warning("未找到API密钥配置")
    
    # 启动WebSocket网关服务 - 已禁用，使用新的简化进度系统
    # from .services.websocket_gateway_service import websocket_gateway_service
    # await websocket_gateway_service.start()
    # logger.info("WebSocket网关服务已启动")
    logger.info("WebSocket网关服务已禁用，使用新的简化进度系统")

@app.on_event("shutdown")
async def shutdown_event():
    """应用关闭事件"""
    logger.info("正在关闭AutoClip API服务...")
    # WebSocket网关服务已禁用
    # from .services.websocket_gateway_service import websocket_gateway_service
    # await websocket_gateway_service.stop()
    # logger.info("WebSocket网关服务已停止")
    logger.info("WebSocket网关服务已禁用")

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include unified API routes
app.include_router(api_router, prefix="/api/v1")

# 添加独立的video-categories端点
from .utils.i18n import t

@app.get("/api/v1/video-categories")
async def get_video_categories(lang: Optional[str] = Query("zh", description="Language for category names and descriptions")):
    """获取视频分类配置."""
    return {
        "categories": [
            {
                "value": "default",
                "name": t("cat_default", lang),
                "description": t("cat_default_desc", lang),
                "icon": "🎬",
                "color": "#4facfe"
            },
            {
                "value": "knowledge",
                "name": t("cat_knowledge", lang),
                "description": t("cat_knowledge_desc", lang),
                "icon": "📚",
                "color": "#52c41a"
            },
            {
                "value": "entertainment",
                "name": t("cat_entertainment", lang),
                "description": t("cat_entertainment_desc", lang),
                "icon": "🎮",
                "color": "#722ed1"
            },
            {
                "value": "business",
                "name": t("cat_business", lang),
                "description": t("cat_business_desc", lang),
                "icon": "💼",
                "color": "#fa8c16"
            },
            {
                "value": "experience",
                "name": t("cat_experience", lang),
                "description": t("cat_experience_desc", lang),
                "icon": "🌟",
                "color": "#eb2f96"
            },
            {
                "value": "opinion",
                "name": t("cat_opinion", lang),
                "description": t("cat_opinion_desc", lang),
                "icon": "💭",
                "color": "#13c2c2"
            },
            {
                "value": "speech",
                "name": t("cat_speech", lang),
                "description": t("cat_speech_desc", lang),
                "icon": "🎤",
                "color": "#f5222d"
            }
        ]
    }

# 导入统一错误处理中间件
from .core.error_middleware import global_exception_handler

# 注册全局异常处理器
# 注册全局异常处理器
app.add_exception_handler(Exception, global_exception_handler)

# 挂载前端静态文件
frontend_dist = "/app/frontend/dist"
if os.path.exists(frontend_dist):
    # 挂载assets目录
    app.mount("/assets", StaticFiles(directory=f"{frontend_dist}/assets"), name="assets")
    
    # 挂载其他静态文件（如果有）
    # app.mount("/static", StaticFiles(directory=f"{frontend_dist}/static"), name="static")

    # 处理SPA路由 - 这必须是最后一个路由
    @app.get("/{full_path:path}")
    async def serve_spa(full_path: str):
        # 如果是API路径但未匹配到（404），仍然返回404而不是index.html
        if full_path.startswith("api/"):
            return JSONResponse(status_code=404, content={"detail": "API endpoint not found"})
            
        # 否则返回index.html
        return FileResponse(f"{frontend_dist}/index.html")
else:
    logger.warning(f"前端静态文件目录不存在: {frontend_dist}")

if __name__ == "__main__":
    import uvicorn
    import sys
    
    # 默认端口
    port = 8000
    
    # 检查命令行参数
    if len(sys.argv) > 1:
        for i, arg in enumerate(sys.argv):
            if arg == "--port" and i + 1 < len(sys.argv):
                try:
                    port = int(sys.argv[i + 1])
                except ValueError:
                    logger.error(f"无效的端口号: {sys.argv[i + 1]}")
                    port = 8000
    
    logger.info(f"启动服务器，端口: {port}")
    uvicorn.run(app, host="0.0.0.0", port=port)