from langchain_core.messages import ToolMessage
from langgraph.constants import END
from langgraph.graph import StateGraph
from langgraph.prebuilt import tools_condition

from app.agents.assistants import update_flight_runnable, update_flight_sensitive_tools, update_flight_safe_tools, \
    book_car_rental_runnable, book_car_rental_safe_tools, book_car_rental_sensitive_tools, book_hotel_runnable, \
    book_hotel_safe_tools, book_hotel_sensitive_tools, book_excursion_runnable, book_excursion_safe_tools, \
    book_excursion_sensitive_tools, CtripAssistant, CompleteOrEscalate
from app.agents.entry import create_entry_node
from app.agents.models import ToFlightBookingAssistant, ToBookCarRental, ToHotelBookingAssistant, ToBookExcursion
from app.tools.handler import create_tool_node_with_fallback


def route_to_workflow(state: dict) -> str:
    """
    如果在子工作流委托状态中，直接路由到栈顶对应的工作流；
    否则回到主助理。
    """
    dialog_state = state.get("dialog_state")
    if not dialog_state:
        return "primary_assistant"
    return dialog_state[-1]


"""
构建子图
"""

def pop_dialog_state(state: dict) -> dict:
    """弹出对话栈顶，所有子助理共享此节点。"""
    messages = []
    if state["messages"][-1].tool_calls:
        messages.append(
            ToolMessage(
                content="正在恢复对话。请回顾之前的对话并根据需要协助用户。",
                tool_call_id=state["messages"][-1].tool_calls[0]["id"],
            )
        )
    return {"dialog_state": "pop", "messages": messages}


# 航班助手的 子工作流
def build_flight_graph(builder: StateGraph) -> StateGraph: # 创建完一个子工作流还需要创建下一个子工作流
    """构建 航班预订助理的子工作流图"""
    # 添加入口节点，当需要更新或取消航班时使用
    builder.add_node(
        "enter_update_flight",
        create_entry_node("Flight Updates & Booking Assistant", "update_flight"),  # 创建入口节点，指定助理名称和新对话状态
    )
    builder.add_node("update_flight", CtripAssistant(update_flight_runnable))  # 添加处理航班更新的实际节点
    builder.add_edge("enter_update_flight", "update_flight")  # 连接入口节点到实际处理节点

    # 添加敏感工具和安全工具的节点
    builder.add_node(
        "update_flight_sensitive_tools",
        create_tool_node_with_fallback(update_flight_sensitive_tools),  # 敏感工具节点，包含可能修改数据的操作
    )
    builder.add_node(
        "update_flight_safe_tools",
        create_tool_node_with_fallback(update_flight_safe_tools),  # 安全工具节点，通常只读查询
    )

    def route_update_flight(state: dict):
        route = tools_condition(state)
        if route == END:
            return END
        tool_calls = state["messages"][-1].tool_calls
        did_cancel = any(tc["name"] == CompleteOrEscalate.__name__ for tc in tool_calls)
        if did_cancel:
            return "leave_skill"
        if any(tc["name"] == ToBookCarRental.__name__ for tc in tool_calls):
            return "enter_book_car_rental"
        if any(tc["name"] == ToHotelBookingAssistant.__name__ for tc in tool_calls):
            return "enter_book_hotel"
        if any(tc["name"] == ToBookExcursion.__name__ for tc in tool_calls):
            return "enter_book_excursion"
        safe_tool_names = [t.name for t in update_flight_safe_tools]
        if all(tc["name"] in safe_tool_names for tc in tool_calls):
            return "update_flight_safe_tools"
        return "update_flight_sensitive_tools"

    builder.add_edge("update_flight_sensitive_tools", "update_flight")
    builder.add_edge("update_flight_safe_tools", "update_flight")

    builder.add_conditional_edges(
        "update_flight",
        route_update_flight,
        [
            "update_flight_sensitive_tools",
            "update_flight_safe_tools",
            "enter_book_car_rental",
            "enter_book_hotel",
            "enter_book_excursion",
            "leave_skill",
            END,
        ],
    )

    # 此节点被所有子助理共享 — 弹出对话栈并根据栈顶状态路由
    builder.add_node("leave_skill", pop_dialog_state)
    builder.add_conditional_edges(
        "leave_skill",
        route_to_workflow,
        {
            "primary_assistant",
            "update_flight",
            "book_car_rental",
            "book_hotel",
            "book_excursion",
        },
    )
    return builder


def build_car_graph(builder: StateGraph) -> StateGraph:
    # 租车助理 的子工作流
    # 添加入口节点，当需要预订租车时使用
    builder.add_node(
        "enter_book_car_rental",
        create_entry_node("Car Rental Assistant", "book_car_rental"),  # 创建入口节点，指定助理名称和新对话状态
    )
    builder.add_node("book_car_rental", CtripAssistant(book_car_rental_runnable))  # 添加处理租车预订的实际节点
    builder.add_edge("enter_book_car_rental", "book_car_rental")  # 连接入口节点到实际处理节点

    # 添加安全工具和敏感工具的节点
    builder.add_node(
        "book_car_rental_safe_tools",
        create_tool_node_with_fallback(book_car_rental_safe_tools),  # 安全工具节点，通常只读查询
    )
    builder.add_node(
        "book_car_rental_sensitive_tools",
        create_tool_node_with_fallback(book_car_rental_sensitive_tools),  # 敏感工具节点，包含可能修改数据的操作
    )

    def route_book_car_rental(state: dict):
        route = tools_condition(state)
        if route == END:
            return END
        tool_calls = state["messages"][-1].tool_calls
        did_cancel = any(tc["name"] == CompleteOrEscalate.__name__ for tc in tool_calls)
        if did_cancel:
            return "leave_skill"
        if any(tc["name"] == ToFlightBookingAssistant.__name__ for tc in tool_calls):
            return "enter_update_flight"
        if any(tc["name"] == ToHotelBookingAssistant.__name__ for tc in tool_calls):
            return "enter_book_hotel"
        if any(tc["name"] == ToBookExcursion.__name__ for tc in tool_calls):
            return "enter_book_excursion"
        safe_toolnames = [t.name for t in book_car_rental_safe_tools]
        if all(tc["name"] in safe_toolnames for tc in tool_calls):
            return "book_car_rental_safe_tools"
        return "book_car_rental_sensitive_tools"

    builder.add_edge("book_car_rental_sensitive_tools", "book_car_rental")
    builder.add_edge("book_car_rental_safe_tools", "book_car_rental")

    builder.add_conditional_edges(
        "book_car_rental",
        route_book_car_rental,
        [
            "book_car_rental_safe_tools",
            "book_car_rental_sensitive_tools",
            "enter_update_flight",
            "enter_book_hotel",
            "enter_book_excursion",
            "leave_skill",
            END,
        ],
    )
    return builder


# 酒店预订助理
def builder_hotel_graph(builder: StateGraph) -> StateGraph:
    # 添加入口节点，当需要预订酒店时使用
    builder.add_node(
        "enter_book_hotel",
        create_entry_node("酒店预订助理", "book_hotel"),  # 创建入口节点，指定助理名称和新对话状态
    )
    builder.add_node("book_hotel", CtripAssistant(book_hotel_runnable))  # 添加处理酒店预订的实际节点
    builder.add_edge("enter_book_hotel", "book_hotel")  # 连接入口节点到实际处理节点

    # 添加安全工具和敏感工具的节点
    builder.add_node(
        "book_hotel_safe_tools",
        create_tool_node_with_fallback(book_hotel_safe_tools),  # 安全工具节点，通常只读查询
    )
    builder.add_node(
        "book_hotel_sensitive_tools",
        create_tool_node_with_fallback(book_hotel_sensitive_tools),  # 敏感工具节点，包含可能修改数据的操作
    )

    def route_book_hotel(state: dict):
        route = tools_condition(state)
        if route == END:
            return END
        tool_calls = state["messages"][-1].tool_calls
        did_cancel = any(tc["name"] == CompleteOrEscalate.__name__ for tc in tool_calls)
        if did_cancel:
            return "leave_skill"
        if any(tc["name"] == ToFlightBookingAssistant.__name__ for tc in tool_calls):
            return "enter_update_flight"
        if any(tc["name"] == ToBookCarRental.__name__ for tc in tool_calls):
            return "enter_book_car_rental"
        if any(tc["name"] == ToBookExcursion.__name__ for tc in tool_calls):
            return "enter_book_excursion"
        safe_toolnames = [t.name for t in book_hotel_safe_tools]
        if all(tc["name"] in safe_toolnames for tc in tool_calls):
            return "book_hotel_safe_tools"
        return "book_hotel_sensitive_tools"

    builder.add_edge("book_hotel_sensitive_tools", "book_hotel")
    builder.add_edge("book_hotel_safe_tools", "book_hotel")

    builder.add_conditional_edges(
        "book_hotel",
        route_book_hotel,
        [
            "leave_skill",
            "book_hotel_safe_tools",
            "book_hotel_sensitive_tools",
            "enter_update_flight",
            "enter_book_car_rental",
            "enter_book_excursion",
            END,
        ],
    )
    return builder


# 构建一个旅游产品的子图
def builder_excursion_graph(builder: StateGraph) -> StateGraph:
    # 添加入口节点，当需要预订游览或获取旅行推荐时使用
    builder.add_node(
        "enter_book_excursion",
        create_entry_node("旅行推荐助理", "book_excursion"),  # 创建入口节点，指定助理名称和新对话状态
    )
    builder.add_node("book_excursion", CtripAssistant(book_excursion_runnable))  # 添加处理游览预订的实际节点
    builder.add_edge("enter_book_excursion", "book_excursion")  # 连接入口节点到实际处理节点

    # 添加安全工具和敏感工具的节点
    builder.add_node(
        "book_excursion_safe_tools",
        create_tool_node_with_fallback(book_excursion_safe_tools),  # 安全工具节点，通常只读查询
    )
    builder.add_node(
        "book_excursion_sensitive_tools",
        create_tool_node_with_fallback(book_excursion_sensitive_tools),  # 敏感工具节点，包含可能修改数据的操作
    )

    def route_book_excursion(state: dict):
        route = tools_condition(state)
        if route == END:
            return END
        tool_calls = state["messages"][-1].tool_calls
        did_cancel = any(tc["name"] == CompleteOrEscalate.__name__ for tc in tool_calls)
        if did_cancel:
            return "leave_skill"
        if any(tc["name"] == ToFlightBookingAssistant.__name__ for tc in tool_calls):
            return "enter_update_flight"
        if any(tc["name"] == ToBookCarRental.__name__ for tc in tool_calls):
            return "enter_book_car_rental"
        if any(tc["name"] == ToHotelBookingAssistant.__name__ for tc in tool_calls):
            return "enter_book_hotel"
        safe_toolnames = [t.name for t in book_excursion_safe_tools]
        if all(tc["name"] in safe_toolnames for tc in tool_calls):
            return "book_excursion_safe_tools"
        return "book_excursion_sensitive_tools"

    builder.add_edge("book_excursion_sensitive_tools", "book_excursion")
    builder.add_edge("book_excursion_safe_tools", "book_excursion")

    builder.add_conditional_edges(
        "book_excursion",
        route_book_excursion,
        [
            "book_excursion_safe_tools",
            "book_excursion_sensitive_tools",
            "enter_update_flight",
            "enter_book_car_rental",
            "enter_book_hotel",
            "leave_skill",
            END,
        ],
    )
    return builder
