"""FastAPI-приложение для получения онлайн-рекомендаций.

Для запуска uvicorn выполнить команду:
uvicorn features_service:app --port 8010

Для просмотра документации API и совершения тестовых запросов через 
Swagger UI перейти в браузере по ссылке  http://127.0.0.1:8010/docs

Можно отправить запрос в терминале:
curl http://127.0.0.1:8010/similar_items?user_id=17245&k=10


Также для отправки запросов можно выполнить скрипт с использованием библиотеки requests:

import requests

features_store_url = "http://127.0.0.1:8010"

headers = {'Content-type': 'application/json', 'Accept': 'text/plain'}
params = {"item_id": 17245}

resp = requests.post(features_store_url +"/similar_items", headers=headers, params=params)
if resp.status_code == 200:
    similar_items = resp.json()
else:
    similar_items = None
    print(f"status code: {resp.status_code}")
    
print(similar_items)

"""

import logging
from contextlib import asynccontextmanager
import pandas as pd
from fastapi import FastAPI


logger = logging.getLogger("uvicorn.error")


class SimilarItems:

    def __init__(self):

        self._similar_items = None

    def load(self, path, **kwargs):
        """
        Загружаем данные из файла
        """

        logger.info(f"Loading data, type: {type}")
        self._similar_items = pd.read_parquet(path, **kwargs) 
        self._similar_items = self._similar_items.set_index('item_id_1')
        logger.info(f"Loaded")

    def get(self, item_id: int, k: int = 10):
        """
        Возвращает список похожих объектов
        """
        try:
            i2i = self._similar_items.loc[item_id].head(k)
            i2i = i2i[["item_id_2", "score"]].to_dict(orient="list")
        except KeyError:
            logger.error("No recommendations found")
            i2i = {"item_id_2": [], "score": []}

        return i2i


sim_items_store = SimilarItems()


@asynccontextmanager
async def lifespan(app: FastAPI):
    # код ниже (до yield) выполнится только один раз при запуске сервиса
    sim_items_store.load(
        'similar_items.parquet', 
        columns=["item_id_1", "item_id_2", "score"],
    )
    logger.info("Ready!")
    # код ниже выполнится только один раз при остановке сервиса
    yield


# создаём приложение FastAPI
app = FastAPI(title="features", lifespan=lifespan)


@app.post("/similar_items")
async def recommendations(item_id: int, k: int = 10):
    """
    Возвращает список похожих объектов длиной k для item_id
    """

    i2i = sim_items_store.get(item_id, k)

    return i2i