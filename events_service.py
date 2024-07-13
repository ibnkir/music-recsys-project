"""FastAPI-приложение для сохранения и получения последних событий, 
необходимых для генерации онлайн-рекомендаций.

Метод put сохраняет пару значений user_id и item_id как событие, 
метод get возвращает события (первыми — самые последние).

Для запуска uvicorn выполнить команду, находясь в корневой папке проекта:
uvicorn events_service:app --port 8020

Для просмотра документации API и совершения тестовых запросов через 
Swagger UI перейти в браузере по ссылке  http://127.0.0.1:8020/docs

Можно отправить запрос в терминале:
curl http://127.0.0.1:8020/put?user_id=1337055&item_id=17245
curl http://127.0.0.1:8020/get?user_id=1337055

"""

import pandas as pd
from fastapi import FastAPI


class EventStore:
    """
    Класс для сохранения и получения последних событий,
    необходимых для генерации онлайн-рекомендаций.
    """

    def __init__(self, max_events_per_user=10):

        self.events = {}
        self.max_events_per_user = max_events_per_user

    def put(self, user_id, item_id):
        """
        Сохраняет событие
        """

        user_events = self.events.get(user_id)
        self.events[user_id] = [item_id] + user_events[: self.max_events_per_user]

    def get(self, user_id, k):
        """
        Возвращает события для пользователя
        """
        user_events = self.events.get(user_id)[:k]

        return user_events


# Создаем хранилище событий
events_store = EventStore()

# Создаём приложение FastAPI
app = FastAPI(title="events")


@app.post("/put")
async def put(user_id: int, item_id: int):
    """
    Сохраняет событие для user_id, item_id
    """

    events_store.put(user_id, item_id)

    return {"result": "ok"}


@app.post("/get")
async def get(user_id: int, k: int = 10):
    """
    Возвращает список последних k событий для пользователя user_id
    """

    events = events_store.get(user_id, k)

    return {"events": events}
