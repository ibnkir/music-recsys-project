"""
Главное FastAPI-приложение для получения оффлайн- и онлайн-рекомендаций.

Основные обрабатываемые запросы:
- /recommendations_default - получение рекомендаций по умолчанию из числа топ-треков,
- /recommendations_offline - получение персональных рекомендаций только по оффлайн-истории пользователя,
- /recommendations_online - получение персональных рекомендаций только по онлайн-истории пользователя,
- /recommendations - получение смешанных рекомендаций по оффлайн- и онлайн-истории пользователя.

Для запуска и тестирования см. инструкции в файле README.md
"""

import logging
from fastapi import FastAPI
from contextlib import asynccontextmanager
import pandas as pd
import requests
import configparser


# Создаем логгер
logger = logging.getLogger("uvicorn.error")

# Создаем парсер конфигурационного файла
config = configparser.ConfigParser()
config.read("config.ini")  

# Читаем url-адреса двух вспомогательных сервисов из конфигурационного файла
# Вспомогательный сервис для получения рекомендаций по умолчанию на основе топ-треков
features_store_url = config["urls"]["features_store_url"] # "http://127.0.0.1:8010"
# Вспомогательный сервис для хранения и получения последних онлайн-событий пользователя
events_store_url = config["urls"]["events_store_url"] # "http://127.0.0.1:8020"


# Объявляем специальный класс для работы с оффлайн-рекомендациями
class Recommendations:
    """
    Класс для работы с оффлайн-рекомендациями
    """
    def __init__(self):
        self._recs = {"personal": None, "default": None}
        self._stats = {
            "request_personal_count": 0,
            "request_default_count": 0,
        }

    def load(self, type, path, **kwargs):
        """
        Загружает рекомендации из файла
        """
        logger.info(f"Loading recommendations, type: {type}")
        self._recs[type] = pd.read_parquet(path, **kwargs)
        logger.info(f"Loaded")

    def get(self, user_id: int, k: int=100):
        """
        Возвращает список рекомендаций для пользователя
        """
        
        # Добавляем обработку исключений для общего случая
        # (у нас все рекомендации должны быть обязательно загружены, без них сервис не запустится,
        # поэтому KeyError можно не проверять)
        try: 
            recs = self._recs["personal"].query('user_id == @user_id') 
            if len(recs) > 0:
                recs = recs["item_id"].to_list()[:k]
                self._stats["request_personal_count"] += 1
            else:
                recs = self._recs["default"]
                recs = recs["item_id"].to_list()[:k]
                self._stats["request_default_count"] += 1
        except Exception as e:
            logger.error(f"{e}, no recommendations found")
            recs = []

        return recs

    def get_default(self, k: int=100):
        """
        Возвращает список рекомендаций по умолчанию
        """

        # Добавляем обработку исключений для общего случая
        # (у нас все рекомендации должны быть обязательно загружены, без них сервис не запустится,
        # поэтому KeyError можно не проверять)
        try:
            recs = self._recs["default"]
            recs = recs["item_id"].to_list()[:k]
            self._stats["request_default_count"] += 1
        except Exception as e:
            logger.error(f"{e}, no recommendations found")
            recs = []

        return recs

    def stats(self):
        logger.info("Stats for recommendations")
        for name, value in self._stats.items():
            logger.info(f"{name:<30} {value} ")


# Создаем объект для работы с рекомендациями
rec_store = Recommendations()


@asynccontextmanager
async def lifespan(app: FastAPI):
    # код ниже (до yield) выполнится только один раз при запуске сервиса
    logger.info("Starting")

    # Загружаем рекомендации из файлов
    rec_store.load(
        "personal",
        "recommendations.parquet",
        columns=["user_id", "item_id", "rank"],
    )
    rec_store.load(
        "default",
        'top_popular.parquet', 
        columns=["item_id", "rank"],
    )
    logger.info("Ready!")
    yield
    # этот код выполнится только один раз при остановке сервиса
    rec_store.stats()
    logger.info("Stopping")
    

# создаём приложение FastAPI
app = FastAPI(title="recommendations", lifespan=lifespan)


# Обращение к корневому url для проверки работоспособности сервиса
@app.get("/")
def read_root():
    return {"message": "Recommendations service is working"}


# Получение персональных рекомендаций пользователя только по его оффлайн-истории
@app.post("/recommendations_offline")
async def recommendations_offline(user_id: int, k: int = 100):
    """
    Возвращает список оффлайн-рекомендаций длиной k для пользователя user_id
    """
    recs = rec_store.get(user_id, k)
    return {"recs": recs}


# Получение рекомендаций по умолчанию из числа топ-треков
@app.post("/recommendations_default")
async def recommendations_default(k: int = 100):
    """
    Возвращает список рекомендаций по умолчанию длиной k
    """
    recs = rec_store.get_default(k)
    return {"recs": recs}


# Функции для получения онлайн-рекомендаций

# Вспомогательная функция
def dedup_ids(ids):
    """
    Дедублицирует список идентификаторов, оставляя только первое вхождение
    """
    seen = set()
    ids = [id for id in ids if not (id in seen or seen.add(id))]

    return ids

# Получение онлайн-рекомендаций
@app.post("/recommendations_online")
async def recommendations_online(user_id: int, k: int = 50):
    """
    Возвращает список онлайн-рекомендаций длиной k для пользователя user_id по его 3-м последним онлайн-событиям
    """
    headers = {"Content-type": "application/json", "Accept": "text/plain"}

    # получаем список последних событий пользователя, возьмём три последних
    params = {"user_id": user_id, "k": 3}
    resp = requests.post(events_store_url + "/get", headers=headers, params=params)
    events = resp.json()
    events = events['events']

    # получаем список айтемов, похожих на последние три, с которыми взаимодействовал пользователь
    items = []
    scores = []
    for item_id in events:
        # для каждого item_id получаем список похожих в item_similar_items
        params = {"item_id": item_id, "k": k}
        resp = requests.post(features_store_url +"/similar_items", headers=headers, params=params)
        item_similar_items = resp.json()
        items += item_similar_items["item_id_2"]
        scores += item_similar_items["score"]
    
    # сортируем похожие объекты по scores в убывающем порядке
    combined = list(zip(items, scores))
    combined = sorted(combined, key=lambda x: x[1], reverse=True)
    combined = [item for item, _ in combined]

    # удаляем дубликаты, чтобы не выдавать одинаковые рекомендации
    recs = dedup_ids(combined)[:k]

    return {"recs": recs}


# Получение смешанных offline- и online-рекомендаций,
# первые помещаем на четные места выходного списка (начиная с нулевой позиции), 
# вторые - на нечетные
@app.post("/recommendations")
async def recommendations(user_id: int, k: int = 100):
    """
    Возвращает список рекомендаций длиной k для пользователя user_id
    """

    recs_offline = await recommendations_offline(user_id, k)
    recs_online = await recommendations_online(user_id, k)

    recs_offline = recs_offline["recs"]
    recs_online = recs_online["recs"]

    recs_blended = []

    min_length = min(len(recs_offline), len(recs_online))
    offline_idx = online_idx = 0
    
    # чередуем элементы из списков, пока позволяет минимальная длина
    for i in range(2 * min_length):
        if i % 2 == 0:
            # Оффлайн-рекомендации на четных позициях (начиная с нулевой)
            recs_blended.append(recs_offline[offline_idx])
            offline_idx += 1
        else:
            # Онлайн-рекомендации на нечетных позициях
            recs_blended.append(recs_online[online_idx])
            online_idx += 1

    # добавляем оставшиеся элементы в конец
    if len(recs_offline) >= len(recs_online):
        recs_blended.extend(recs_offline[offline_idx:])
    else:
        recs_blended.extend(recs_online[online_idx:])

    # удаляем дубликаты
    recs_blended = dedup_ids(recs_blended)
    
    # оставляем только первые k рекомендаций
    recs_blended = recs_blended[:k]

    return {"recs": recs_blended}
