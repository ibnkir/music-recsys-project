"""
Вспомогательное FastAPI-приложение для получения онлайн-рекомендаций на основе треков с похожими жанрами.

Основные обрабатываемые запросы:
- /similar_items - получение требуемого кол-ва объектов, похожих на заданный.

Для запуска и тестирования см. инструкции в файле README.md
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


# Обращение к корневому url для проверки работоспособности сервиса
@app.get("/")
def read_root():
    return {"message": "Features service is working"}


@app.post("/similar_items")
async def recommendations(item_id: int, k: int = 10):
    """
    Возвращает список похожих объектов длиной k для item_id
    """
    i2i = sim_items_store.get(item_id, k)
    return i2i
