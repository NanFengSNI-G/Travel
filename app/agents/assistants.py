from datetime import datetime

from langchain_core.prompts import ChatPromptTemplate
from langchain_core.runnables import Runnable, RunnableConfig

from langgraph.config import get_stream_writer

from app.agents.models import ToFlightBookingAssistant, ToBookCarRental, ToHotelBookingAssistant, ToBookExcursion, CompleteOrEscalate
from app.agents.llm import llm
from app.agents.state import State
from app.tools.cars import search_car_rentals, book_car_rental, update_car_rental, cancel_car_rental
from app.tools.flights import fetch_user_flight_information, search_flights, update_ticket_to_new_flight, cancel_ticket
from app.tools.hotels import search_hotels, book_hotel, update_hotel, cancel_hotel
from app.tools.retriever import lookup_policy
from app.tools.trips import search_trip_recommendations, book_excursion, update_excursion, cancel_excursion


# ── CtripAssistant 节点包装器 ───────────────────────────────────────

class CtripAssistant:
    def __init__(self, runnable: Runnable):
        self.runnable = runnable

    def __call__(self, state: State, config: RunnableConfig):
        writer = get_stream_writer()
        while True:
            full_content = ""
            last_chunk = None
            for chunk in self.runnable.stream(state):
                last_chunk = chunk
                if chunk.content and isinstance(chunk.content, str):
                    full_content += chunk.content
                    writer(("token", chunk.content))

            if not last_chunk.tool_calls and (
                    not full_content
                    or isinstance(full_content, list)
                    and not full_content[0].get("text")
            ):
                messages = state["messages"] + [("user", "请提供一个真实的输出作为回应。")]
                state = {**state, "messages": messages}
            else:
                break

        if last_chunk.content != full_content:
            last_chunk.content = full_content
        return {'messages': last_chunk}


# ── 主助理 ───────────────────────────────────────────────────────────

primary_assistant_prompt = ChatPromptTemplate.from_messages(
    [
        (
            "system",
            "您是携程瑞士航空公司的客户服务助理。"
            "您的主要职责是搜索航班信息和公司政策以回答客户的查询。"
            "如果客户请求更新或取消航班、预订租车、预订酒店或获取旅行推荐，请通过调用相应的工具将任务委派给合适的专门助理。您自己无法进行这些类型的更改。"
            "只有专门助理才有权限为用户执行这些操作。"
            "用户并不知道有不同的专门助理存在，因此请不要提及他们；只需通过函数调用来安静地委派任务。"
            "向客户提供详细的信息，并且在确定信息不可用之前总是复查数据库。"
            "在搜索时，请坚持不懈。如果第一次搜索没有结果，请扩大查询范围。"
            "如果搜索无果，请扩大搜索范围后再放弃。"
            "\n\n当前用户的航班信息:\n<Flights>\n{user_info}\n</Fllights>"
            "\n当前时间: {time}.",
        ),
        ("placeholder", "{messages}"),
    ]
).partial(time=datetime.now())

primary_assistant_tools = [
    search_flights,
    lookup_policy,
]

assistant_runnable = primary_assistant_prompt | llm.bind_tools(
    primary_assistant_tools
    + [
        ToFlightBookingAssistant,
        ToBookCarRental,
        ToHotelBookingAssistant,
        ToBookExcursion,
    ]
)


# ── 航班预订助理 ───────────────────────────────────────────────────

flight_booking_prompt = ChatPromptTemplate.from_messages(
    [
        (
            "system",
            "您是专门处理航班查询，改签和预定的助理。"
            "当用户需要帮助更新他们的预订时，主助理会将工作委托给您。"
            "如果用户同时还需要预订酒店、租车或游览等其他服务，请调用相应的转交工具将任务委派给合适的专门助理。"
            "请与客户确认更新后的航班详情，并告知他们任何额外费用。"
            "在搜索时，请坚持不懈。如果第一次搜索没有结果，请扩大查询范围。"
            "如果您需要更多信息或客户改变主意，请将任务升级回主助理。"
            "请记住，在相关工具成功使用后，预订才算完成。"
            "\n\n当前用户的航班信息:\n<Flights>\n{user_info}\n</Flights>"
            "\n当前时间: {time}."
            "\n\n如果用户需要帮助，并且您的工具都不适用，则"
            '“CompleteOrEscalate”对话给主助理。不要浪费用户的时间。不要编造无效的工具或功能。',
        ),
        ("placeholder", "{messages}"),
    ]
).partial(time=datetime.now())

update_flight_safe_tools = [search_flights]
update_flight_sensitive_tools = [update_ticket_to_new_flight, cancel_ticket]
update_flight_tools = update_flight_safe_tools + update_flight_sensitive_tools
update_flight_runnable = flight_booking_prompt | llm.bind_tools(
    update_flight_tools + [
        ToBookCarRental,
        ToHotelBookingAssistant,
        ToBookExcursion,
        CompleteOrEscalate,
    ]
)


# ── 酒店预订助理 ───────────────────────────────────────────────────

book_hotel_prompt = ChatPromptTemplate.from_messages(
    [
        (
            "system",
            "您是专门处理酒店预订的助理。"
            "当用户需要帮助预订酒店时，主助理会将工作委托给您。"
            "如果用户同时还需要航班预订、租车或游览等其他服务，请调用相应的转交工具将任务委派给合适的专门助理。"
            "根据用户的偏好搜索可用酒店，并与客户确认预订详情。"
            "在搜索时，请坚持不懈。如果第一次搜索没有结果，请扩大查询范围。"
            "如果您需要更多信息或客户改变主意，请将任务升级回主助理。"
            "请记住，在相关工具成功使用后，预订才算完成。"
            "\n当前时间: {time}."
            "\n\n如果用户需要帮助，并且您的工具都不适用，则"
            '“CompleteOrEscalate”对话给主助理。不要浪费用户的时间。不要编造无效的工具或功能。'
            "\n\n以下是一些你应该CompleteOrEscalate的例子：\n"
            " - '这个季节的天气怎么样？'\n"
            " - '我再考虑一下，可能单独预订'\n"
            " - '我需要弄清楚我在那里的交通方式'\n"
            " - '哦，等等，我还没预订航班，我会先订航班'\n"
            " - '酒店预订已确认'",
        ),
        ("placeholder", "{messages}"),
    ]
).partial(time=datetime.now())

book_hotel_safe_tools = [search_hotels]
book_hotel_sensitive_tools = [book_hotel, update_hotel, cancel_hotel]
book_hotel_tools = book_hotel_safe_tools + book_hotel_sensitive_tools
book_hotel_runnable = book_hotel_prompt | llm.bind_tools(
    book_hotel_tools + [
        ToFlightBookingAssistant,
        ToBookCarRental,
        ToBookExcursion,
        CompleteOrEscalate,
    ]
)


# ── 租车预订助理 ───────────────────────────────────────────────────

book_car_rental_prompt = ChatPromptTemplate.from_messages(
    [
        (
            "system",
            "您是专门处理租车预订的助理。"
            "当用户需要帮助预订租车时，主助理会将工作委托给您。"
            "如果用户同时还需要航班预订、酒店预订或游览等其他服务，请调用相应的转交工具将任务委派给合适的专门助理。"
            "根据用户的偏好搜索可用租车，并与客户确认预订详情。"
            "在搜索时，请坚持不懈。如果第一次搜索没有结果，请扩大查询范围。"
            "如果您需要更多信息或客户改变主意，请将任务升级回主助理。"
            "请记住，在相关工具成功使用后，预订才算完成。"
            "\n当前时间: {time}."
            "\n\n如果用户需要帮助，并且您的工具都不适用，则"
            '“CompleteOrEscalate”对话给主助理。不要浪费用户的时间。不要编造无效的工具或功能。'
            "\n\n以下是一些你应该CompleteOrEscalate的例子：\n"
            " - '这个季节的天气怎么样？'\n"
            " - '有哪些航班可供选择？'\n"
            " - '我再考虑一下，可能单独预订'\n"
            " - '哦，等等，我还没预订航班，我会先订航班'\n"
            " - '租车预订已确认'",
        ),
        ("placeholder", "{messages}"),
    ]
).partial(time=datetime.now())

book_car_rental_safe_tools = [search_car_rentals]
book_car_rental_sensitive_tools = [
    book_car_rental,
    update_car_rental,
    cancel_car_rental,
]
book_car_rental_tools = book_car_rental_safe_tools + book_car_rental_sensitive_tools
book_car_rental_runnable = book_car_rental_prompt | llm.bind_tools(
    book_car_rental_tools + [
        ToFlightBookingAssistant,
        ToHotelBookingAssistant,
        ToBookExcursion,
        CompleteOrEscalate,
    ]
)


# ── 游览预订助理 ───────────────────────────────────────────────────

book_excursion_prompt = ChatPromptTemplate.from_messages(
    [
        (
            "system",
            "您是专门处理旅行推荐的助理。"
            "当用户需要帮助预订推荐的旅行时，主助理会将工作委托给您。"
            "如果用户同时还需要航班预订、酒店预订或租车等其他服务，请调用相应的转交工具将任务委派给合适的专门助理。"
            "根据用户的偏好搜索可用的旅行推荐，并与客户确认预订详情。"
            "如果您需要更多信息或客户改变主意，请将任务升级回主助理。"
            "在搜索时，请坚持不懈。如果第一次搜索没有结果，请扩大查询范围。"
            "请记住，在相关工具成功使用后，预订才算完成。"
            "\n当前时间: {time}."
            "\n\n如果用户需要帮助，并且您的工具都不适用，则"
            '“CompleteOrEscalate”对话给主助理。不要浪费用户的时间。不要编造无效的工具或功能。'
            "\n\n以下是一些你应该CompleteOrEscalate的例子：\n"
            " - '我再考虑一下，可能单独预订'\n"
            " - '我需要弄清楚我在那里的交通方式'\n"
            " - '哦，等等，我还没预订航班，我会先订航班'\n"
            " - '游览预订已确认！'",
        ),
        ("placeholder", "{messages}"),
    ]
).partial(time=datetime.now())

book_excursion_safe_tools = [search_trip_recommendations]
book_excursion_sensitive_tools = [book_excursion, update_excursion, cancel_excursion]
book_excursion_tools = book_excursion_safe_tools + book_excursion_sensitive_tools
book_excursion_runnable = book_excursion_prompt | llm.bind_tools(
    book_excursion_tools + [
        ToFlightBookingAssistant,
        ToBookCarRental,
        ToHotelBookingAssistant,
        CompleteOrEscalate,
    ]
)
