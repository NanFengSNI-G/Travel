from langchain_community.chat_models import ChatTongyi

from app.core.config import DASHSCOPE_API_KEY

llm = ChatTongyi(
    model="deepseek-v4-flash",
    dashscope_api_key=DASHSCOPE_API_KEY,
)
