from fastapi import APIRouter
from app.services.crawler_service import mk_crawler
from app.services.GPT_service import summarize_news
from pydantic import BaseModel
from typing import Dict, Any, List

import redis
import json
import os

router = APIRouter()

# Redis 연결 설정 (환경변수 사용)
REDIS_HOST = os.getenv("REDIS_HOST", "localhost")
rd = redis.Redis(host=REDIS_HOST, port=6379, db=0, decode_responses=True)

class news_resp(BaseModel):
    message: str
    summarized_news: List[Dict[str, Any]]


@router.get("/news", response_model=news_resp)
def get_news():
    # 1. Redis에서 'news' 키 조회
    cached_news = rd.get("news")
    
    if cached_news:
        try:
            # 캐시된 데이터가 있으면 반환
            summarized_news = json.loads(cached_news)
            return news_resp(message="뉴스 캐시 조회 성공", summarized_news=summarized_news)
        except json.JSONDecodeError:
            pass # 디코딩 에러 시 새로 불러오도록 패스

    # 2. 캐시가 없거나 만료된 경우: 크롤링 및 요약 수행
    news_json = mk_crawler()
    summarized_news = summarize_news(news_json)

    # 3. Redis에 저장 (6시간 = 21600초 유효)
    # 한글 깨짐 방지를 위해 ensure_ascii=False
    rd.set("news", json.dumps(summarized_news, ensure_ascii=False), ex=21600)

    return news_resp(message="뉴스 업데이트 성공", summarized_news=summarized_news)