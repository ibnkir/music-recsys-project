"""FastAPI-приложение для получения оффлайн- и онлайн-рекомендаций.

Для запуска сервиса с помощью uvicorn выполните команду в терминале, находясь корневой папке проекта:
uvicorn recommendations_service:app

Для просмотра документации API и совершения тестовых запросов через 
Swagger UI перейти в браузере по ссылке  http://127.0.0.1:8000/docs

Можно отправить запрос в терминале:
curl http://127.0.0.1:8000/recommendation?user_id=100&k=10

Также для отправки запросов можно написать короткий скрипт с использованием библиотеки requests
"""

import logging
from fastapi import FastAPI
from contextlib import asynccontextmanager
import pandas as pd
import requests


logger = logging.getLogger("uvicorn.error")

features_store_url = "http://127.0.0.1:8010"
events_store_url = "http://127.0.0.1:8020"


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
        if type == "personal":
            self._recs[type] = self._recs[type].set_index("user_id")
        logger.info(f"Loaded")

    def get(self, user_id: int, k: int=100):
        """
        Возвращает список рекомендаций для пользователя
        """

        try:
            recs = self._recs["personal"].loc[user_id]
            recs = recs["item_id"].to_list()[:k]
            self._stats["request_personal_count"] += 1
        except KeyError:
            recs = self._recs["default"]
            recs = recs["item_id"].to_list()[:k]
            self._stats["request_default_count"] += 1
        except:
            logger.error("No recommendations found")
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
        'final_recommendations_feat.parquet',
        columns=["user_id", "item_id", "rank"],
    )
    rec_store.load(
        "default",
        'top_recs.parquet', 
        columns=["item_id", "rank"],
    )

    yield
    # этот код выполнится только один раз при остановке сервиса
    rec_store.stats()
    logger.info("Stopping")
    

# создаём приложение FastAPI
app = FastAPI(title="recommendations", lifespan=lifespan)


@app.post("/recommendations_offline")
async def recommendations_offline(user_id: int, k: int = 100):
    """
    Возвращает список оффлайн-рекомендаций длиной k для пользователя user_id
    """

    recs = rec_store.get(user_id, k)

    return {"recs": recs}


'''
# Начальная версия ф-ции recommendations_online: получаем рекомендации по 1 последнему событию
@app.post("/recommendations_online")
async def recommendations_online(user_id: int, k: int = 100):
    """
    Возвращает список онлайн-рекомендаций длиной k для пользователя user_id
    """

    headers = {"Content-type": "application/json", "Accept": "text/plain"}

    # получаем последнее событие пользователя
    params = {"user_id": user_id, "k": 1}
    resp = requests.post(events_store_url + "/get", headers=headers, params=params)
    events = resp.json()
    events = events["events"]

    # получаем список похожих объектов
    if len(events) > 0:
        item_id = events[0]
        params = {"item_id": item_id, "k": k}
        resp = requests.post(features_store_url +"/similar_items", headers=headers, params=params) 
        item_similar_items = resp.json()
        item_similar_items = item_similar_items['item_id_2']
        recs = item_similar_items[:k]
    else:
        recs = []

    return {"recs": recs}
'''

# Конечная версия recommendations_online: получаем рекомендации по 3-м последним событиям
def dedup_ids(ids):
    """
    Дедублицирует список идентификаторов, оставляя только первое вхождение
    """
    seen = set()
    ids = [id for id in ids if not (id in seen or seen.add(id))]

    return ids

@app.post("/recommendations_online")
async def recommendations_online(user_id: int, k: int = 100):
    """
    Возвращает список онлайн-рекомендаций длиной k для пользователя user_id по его 3-м последним событиям
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
    # для старта это приемлемый подход
    combined = list(zip(items, scores))
    combined = sorted(combined, key=lambda x: x[1], reverse=True)
    combined = [item for item, _ in combined]

    # удаляем дубликаты, чтобы не выдавать одинаковые рекомендации
    recs = dedup_ids(combined)

    return {"recs": recs}


# Объединяем offline- и online-рекомендации (blending),
# первые помещаем на четные места выходного списка, вторые - на четные
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
            recs_blended.append(recs_offline[offline_idx])
            offline_idx += 1
        else:
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

