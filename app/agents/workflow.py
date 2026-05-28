import uuid

from langchain_core.messages import ToolMessage
from langgraph.checkpoint.memory import MemorySaver
from langgraph.constants import START, END
from langgraph.graph import StateGraph
from langgraph.prebuilt import tools_condition

from app.agents.assistants import CtripAssistant, assistant_runnable, primary_assistant_tools
from app.agents.models import ToFlightBookingAssistant, ToBookCarRental, ToHotelBookingAssistant, \
    ToBookExcursion
from app.agents.children import build_flight_graph, builder_hotel_graph, build_car_graph, \
    builder_excursion_graph, route_to_workflow
from app.tools.flights import fetch_user_flight_information
from app.agents.state import State
from app.tools.handler import create_tool_node_with_fallback, _print_event

# 定义了一个流程图的构建对象
builder = StateGraph(State)


def get_user_info(state: State):
    """
    获取用户的航班信息并更新状态字典。
    参数:
        state (State): 当前状态字典。
    返回:
        dict: 包含用户信息的新状态字典。
    """
    return {"user_info": fetch_user_flight_information.invoke({})}


# fetch_user_info节点首先运行，这意味着我们的助手可以在不采取任何行动的情况下看到用户的航班信息
builder.add_node('fetch_user_info', get_user_info)
builder.add_edge(START, 'fetch_user_info')

# 添加 四个业务助理 的 子工作流
builder = build_flight_graph(builder)
builder = builder_hotel_graph(builder)
builder = build_car_graph(builder)
builder = builder_excursion_graph(builder)

# 添加主助理
builder.add_node('primary_assistant', CtripAssistant(assistant_runnable))
builder.add_node(
    "primary_assistant_tools", create_tool_node_with_fallback(primary_assistant_tools)  # 主助理工具节点，包含各种工具
)


def route_primary_assistant(state: dict):
    """
    根据当前状态 判断路由到 子助手节点。
    :param state: 当前对话状态字典
    :return: 下一步应跳转到的节点名
    """
    route = tools_condition(state)  # 判断下一步的方向
    if route == END:
        return END  # 如果结束条件满足，则返回END
    tool_calls = state["messages"][-1].tool_calls  # 获取最后一条消息中的工具调用
    if tool_calls:
        if tool_calls[0]["name"] == ToFlightBookingAssistant.__name__:
            return "enter_update_flight"  # 跳转至航班预订入口节点
        elif tool_calls[0]["name"] == ToBookCarRental.__name__:
            return "enter_book_car_rental"  # 跳转至租车预订入口节点
        elif tool_calls[0]["name"] == ToHotelBookingAssistant.__name__:
            return "enter_book_hotel"  # 跳转至酒店预订入口节点
        elif tool_calls[0]["name"] == ToBookExcursion.__name__:
            return "enter_book_excursion"  # 跳转至游览预订入口节点
        return "primary_assistant_tools"  # 否则跳转至主助理工具节点
    raise ValueError("无效的路由")  # 如果没有找到合适的工具调用，抛出异常


builder.add_conditional_edges(
    'primary_assistant',
    route_primary_assistant,
    [
        "enter_update_flight",  # 航班 子助手的入口节点
        "enter_book_car_rental",  # 租车 子助手的入口节点
        "enter_book_hotel",   # 酒店 子助手的入口节点
        "enter_book_excursion",   # 旅游景点 子助手的入口节点
        "primary_assistant_tools",  # 主助手的工具： 全网搜索工具，查询企业政策的工具
        END,
    ]
)

builder.add_edge('primary_assistant_tools', 'primary_assistant')


builder.add_conditional_edges("fetch_user_info", route_to_workflow)

memory = MemorySaver()
graph = builder.compile(
    checkpointer=memory,
    interrupt_before=[
        "update_flight_sensitive_tools",
        "book_car_rental_sensitive_tools",
        "book_hotel_sensitive_tools",
        "book_excursion_sensitive_tools",
    ]
)