"""
Вспомогательное FastAPI-приложение для сохранения и получения последних онлайн-событий, 
необходимых для генерации персональных онлайн-рекомендаций.

Основные обрабатываемые запросы:
- /put - сохраняет пару значений user_id, item_id как событие, 
- /get - возвращает требуемое кол-во онлайн-событий для заданного пользователя,
начиная с самых последних.

Для запуска сервиса с помощью uvicorn выполните команду, находясь в корневой папке проекта:
uvicorn events_service:app --port 8020

Для запуска и тестирования см. инструкции в файле README.md
"""

import pandas as pd
from fastapi import FastAPI


# Класс-хранилище онлайн-событий 
class EventStore:
    """
    Класс для сохранения и получения последних онлайн-событий,
    необходимых для генерации персональных онлайн-рекомендаций.
    """

    def __init__(self, max_events_per_user=10):

        self.events = {}
        self.max_events_per_user = max_events_per_user

    def put(self, user_id, item_id):
        """
        Сохраняет событие
        """
        user_events = self.events.get(user_id, [])
        self.events[user_id] = [item_id] + user_events[: self.max_events_per_user]

    def get(self, user_id, k):
        """
        Возвращает последние онлайн-события пользователя
        """
        user_events = self.events.get(user_id, [])[: min(k, self.max_events_per_user)]

        return user_events


# Создаем хранилище событий
events_store = EventStore()

# Создаём приложение FastAPI
app = FastAPI(title="events")


# Обращение к корневому url для проверки работоспособности сервиса
@app.get("/")
def read_root():
    return {"message": "Events service is working"}


# Сохранение одного события
@app.post("/put")
async def put(user_id: int, item_id: int):
    """
    Сохраняет событие для user_id, item_id
    """
    events_store.put(user_id, item_id)
    return {"result": "ok"}


# Получение онлайн-событий, начиная с самого последнего
@app.post("/get")
async def get(user_id: int, k: int = 10):
    """
    Возвращает список последних k событий для пользователя user_id
    """
    events = events_store.get(user_id, k)
    return {"events": events}
