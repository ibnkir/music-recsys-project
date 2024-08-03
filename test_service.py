"""
Вспомогательное FastAPI-приложение для тестирования рекомендательного сервиса.

Реализованы следующие функции:
    - /top_recs - получение рекомендаций по умолчанию из числа топ-треков;
    - /offline_recs - получение персональных рекомендаций только по оффлайн-истории пользователя;
    - /add_online - добавление одного события в онлайн-историю пользователя;
    - /blended_recs - получение смешанных персональных рекомендаций по оффлайн- и онлайн-истории пользователя;

Для запуска сервисов выполните 4 команды (по одному на каждый сервис) в 4-х разных терминалах, 
находясь в папке проекта:
    uvicorn recommendations_service:app
    uvicorn events_service:app --port 8020
    uvicorn features_service:app --port 8010
    uvicorn test_service:app --port 8030

Далее выполните тестовые запросы с помощью следующих ссылок:
    - Получение топ-10 рекомендаций по умолчанию
    http://localhost:8030/top_recs?k=10
    - Получение первых 10 персональных рекомендаций только по оффлайн-истории пользователя с user_id=617032 
    http://localhost:8030/offline_recs?user_id=617032&k=10
    - Добавление item_id=99262 в онлайн-историю пользователя с user_id=617032 
    http://localhost:8030/add_online?user_id=617032&item_id=99262
    - Добавление item_id=590303 в онлайн-историю пользователя с user_id=617032 
    http://localhost:8030/add_online?user_id=617032&item_id=590303
    - Добавление item_id=597196 в онлайн-историю пользователя с user_id=617032 
    http://localhost:8030/add_online?user_id=617032&item_id=597196
    - Получение первых 10 смешанных персональных рекомендаций по оффлайн- и онлайн-истории пользователя с user_id=617032 
    http://localhost:8030/blended_recs?user_id=617032&k=10
"""

import numpy as np
import pandas as pd
from fastapi import FastAPI
import requests
import json
import logging
from contextlib import asynccontextmanager


# Настраиваем логирование
logger = logging.getLogger('test_service_logs')

stream_handler = logging.StreamHandler()
stream_handler.setLevel(logging.INFO)

logging.basicConfig(level=logging.INFO,
                    format='%(asctime)s %(levelname)s %(module)s, %(funcName)s, %(message)s',
                    handlers=[logging.FileHandler("test_service.log", mode='w'),
                              stream_handler])


@asynccontextmanager
async def lifespan(app: FastAPI):
    # код ниже (до yield) выполнится только один раз при запуске сервиса
    logger.info('Started')
    yield
    # этот код выполнится только один раз при остановке сервиса
    logger.info("Finished")


# Создаём приложение FastAPI
app = FastAPI(title="tests", lifespan=lifespan)


# Задаем url-адреса трех веб-сервисов
# Основной сервис для получения оффлайн- и онлайн-рекомендаций
recommendations_url = "http://127.0.0.1:8000"
# Вспомогательный сервис для получения рекомендаций по умолчанию на основе топ-треков
features_store_url = "http://127.0.0.1:8010"
# Вспомогательный сервис для хранения и получения последних онлайн-событий пользователя
events_store_url = "http://127.0.0.1:8020"

# Общий заголовок для всех http-запросов
headers = {"Content-type": "application/json", "Accept": "text/plain"}


# Обращение к корневому url (для диагонстики)
@app.get("/")
def read_root():
    logger.info("Test service is working")
    return {"message": "Test service is working"}


# Получение рекомендаций по умолчанию из числа топ-треков
@app.get("/top_recs")
async def top_recs(k: int = 10):
    """
    Возвращает ids k топ-треков
    """
    params = {'k': k}
    resp = requests.post(recommendations_url + "/recommendations_default", headers=headers, params=params)
    if resp.status_code == 200:
        resp = resp.json()
        print(resp)
        logger.info(f"top-{k} popular tracks: {resp['recs']}")
    else:
        print(f"Error, status code: {resp.status_code}") 
        logger.info(f"Error, status code: {resp.status_code}")
    
    return resp

# Получение персональных рекомендаций только по оффлайн-истории
@app.get("/offline_recs")
async def offline_recs(user_id: int = 617032, k: int = 10):
    params = {'user_id': user_id, 'k': k}
    resp = requests.post(recommendations_url + "/recommendations_offline", headers=headers, params=params)
    if resp.status_code == 200:
        resp = resp.json()
        print(resp)
        logger.info(f"{k} offline recommendations for user_id={user_id}: {resp['recs']}")
    else:
        print(f"Error, status code: {resp.status_code}") 
        logger.info(f"Error, status code: {resp.status_code}")
    
    return resp
    

# Добавление одного события в онлайн-историю пользователя
@app.get("/add_online")
async def add_online(user_id: int, item_id: int):
    params = {"user_id": user_id, "item_id": item_id}
    resp = requests.post(events_store_url + "/put", headers=headers, params=params)
    if resp.status_code == 200:
        resp = resp.json()
        print(f"Successfully added item_id={item_id} to user_id={user_id} online history")    
        logger.info(f"Successfully added item_id={item_id} to user_id={user_id} online history")
    else:
        print(f"Error, status code: {resp.status_code}") 
    
    return resp


# Получение смешанных персональных рекомендаций по оффлайн- и онлайн-истории пользователя
# (на нечетных местах - оффлайн-рекомендации, на четных - онлайн)
@app.get("/blended_recs")
async def blended_recs(user_id: int = 617032, k: int = 10):
    params = {"user_id": user_id, 'k': k}
    resp = requests.post(recommendations_url + "/recommendations", headers=headers, params=params)
    if resp.status_code == 200:
        resp = resp.json()
        print(f"{k} blended recommendations for user_id={user_id}: {resp['recs']}")
        logger.info(f"{k} blended recommendations for user_id={user_id}: {resp['recs']}")
    else:
        print(f"Error, status code: {resp.status_code}") 
    
    return resp

