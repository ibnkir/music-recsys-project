"""FastAPI-приложение для получения онлайн-рекомендаций на основе похожих треков.

Для запуска сервиса с помощью uvicorn выполните команду, находясь в корневой папке проекта:
uvicorn features_service:app --port 8010

Для просмотра документации API и совершения тестовых запросов через 
Swagger UI перейти в браузере по ссылке  http://127.0.0.1:8010/docs

Можно отправить запрос в терминале:
curl http://127.0.0.1:8010/similar_items?user_id=17245&k=10

Для отправки запросов программно с помощью библиотеки requests используйте 
соответствующий скрипт в ноутбуке part_3_test.ipynb
"""

import logging
from contextlib import asynccontextmanager
import pandas as pd
from fastapi import FastAPI


logger = logging.getLogger("uvicorn.error")


class SimilarItems:
    """
    Класс для поиска похожих айтемов, необходимых для генерации онлайн-рекомендаций
    """

    def __init__(self):

        self._similar_items = None

    def load(self, path, **kwargs):
        """
        Загружаем данные из файла
        """
        logger.info(f"Loading data, type: {type}")
        self._similar_items = pd.read_parquet(path, **kwargs) 
        #self._similar_items = self._similar_items.set_index('item_id_1')
        logger.info(f"Loaded")

    def get(self, item_id: int, k: int = 10):
        """
        Возвращает список похожих объектов
        """
        try:
            i2i = self._similar_items.query('item_id_1 == @item_id') #.loc[item_id].head(k)
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
        'similar.parquet', 
        columns=["item_id_1", "item_id_2", "score"],
    )
    logger.info("Ready!")
    # код ниже выполнится только один раз при остановке сервиса
    yield


# Создаём приложение FastAPI
app = FastAPI(title="features", lifespan=lifespan)


@app.get("/")
def read_root():
    return {"message": "Features Service is working"}


@app.post("/similar_items")
async def recommendations(item_id: int, k: int = 10):
    """
    Возвращает список похожих объектов длиной k для item_id
    """
    i2i = sim_items_store.get(item_id, k)
    return i2i