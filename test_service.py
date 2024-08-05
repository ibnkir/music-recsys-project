"""
Вспомогательный скрипт для тестирования рекомендательного сервиса.

Основные реализованные функции:
- top_recs() - получение рекомендаций по умолчанию из числа топ-треков;
- offline_recs() - получение персональных рекомендаций только по оффлайн-истории пользователя;
- add_online() - добавление одного события в онлайн-историю пользователя;
- online_recs() - получение персональных рекомендаций только по онлайн-истории пользователя;
- blended_recs() - получение смешанных персональных рекомендаций по оффлайн- и онлайн-истории пользователя;

Для запуска и тестирования см. инструкции в файле README.md
"""

import numpy as np
import pandas as pd
import requests
import json
import logging
import sys
import argparse
import configparser


# Настраиваем логирование
logger = logging.getLogger('test_service_logs')

stream_handler = logging.StreamHandler()
stream_handler.setLevel(logging.INFO)

logging.basicConfig(level=logging.INFO,
                    format='%(asctime)s %(levelname)s %(module)s, %(funcName)s, %(message)s',
                    handlers=[logging.FileHandler("test_service.log", mode='a'),
                              stream_handler])


# Создаем парсер конфигурационного файла
config = configparser.ConfigParser()
config.read("config.ini")  

# Читаем url-адреса всех сервисов из конфигурационного файла
# Основной сервис для получения оффлайн- и онлайн-рекомендаций
recommendations_url = config["urls"]["recommendations_url"] # "http://127.0.0.1:8000"
# Вспомогательный сервис для получения рекомендаций по умолчанию на основе топ-треков
features_store_url = config["urls"]["features_store_url"] # "http://127.0.0.1:8010"
# Вспомогательный сервис для хранения и получения последних онлайн-событий пользователя
events_store_url = config["urls"]["events_store_url"] # "http://127.0.0.1:8020"


# Общий заголовок для всех http-запросов
headers = {"Content-type": "application/json", "Accept": "text/plain"}


# Получение рекомендаций по умолчанию из числа топ-треков
def top_recs(k: int = 10):
    """
    Возвращает ids k топ-треков
    """
    params = {'k': k}
    resp = requests.post(recommendations_url + "/recommendations_default", headers=headers, params=params)
    if resp.status_code == 200:
        resp = resp.json()
        logger.info(f"top-{k} popular tracks: {resp['recs']}")
    else:
        logger.info(f"Error, status code: {resp.status_code}")
    

# Получение персональных рекомендаций только по оффлайн-истории
def offline_recs(user_id: int = 617032, k: int = 10):
    params = {'user_id': user_id, 'k': k}
    resp = requests.post(recommendations_url + "/recommendations_offline", headers=headers, params=params)
    if resp.status_code == 200:
        resp = resp.json()
        logger.info(f"{k} offline recommendations for user_id={user_id}: {resp['recs']}")
    else:
        logger.info(f"Error, status code: {resp.status_code}")
    
    return resp
    

# Добавление одного события в онлайн-историю пользователя
def add_online(user_id: int, item_id: int):
    params = {"user_id": user_id, "item_id": item_id}
    resp = requests.post(events_store_url + "/put", headers=headers, params=params)
    if resp.status_code == 200:
        resp = resp.json()
        logger.info(f"Successfully added item_id={item_id} to user_id={user_id} online history")
    else:
        logger.info(f"Error, status code: {resp.status_code}")
    
    return resp


# Получение персональных рекомендаций только по оффлайн-истории
def online_recs(user_id: int = 617032, k: int = 10):
    params = {'user_id': user_id, 'k': k}
    resp = requests.post(recommendations_url + "/recommendations_online", headers=headers, params=params)
    if resp.status_code == 200:
        resp = resp.json()
        logger.info(f"{k} online recommendations for user_id={user_id}: {resp['recs']}")
    else:
        logger.info(f"Error, status code: {resp.status_code}")
    
    return resp


# Получение смешанных персональных рекомендаций по оффлайн- и онлайн-истории пользователя
# (на нечетных местах - оффлайн-рекомендации, на четных - онлайн)
def blended_recs(user_id: int = 617032, k: int = 10):
    params = {"user_id": user_id, 'k': k}
    resp = requests.post(recommendations_url + "/recommendations", headers=headers, params=params)
    if resp.status_code == 200:
        resp = resp.json()
        logger.info(f"{k} blended recommendations for user_id={user_id}: {resp['recs']}")
    else:
        logger.info(f"Error, status code: {resp.status_code}")
    
    return resp


if __name__ == "__main__":
  
    # Создаем парсер для чтения аргументов, передаваемых из командной строки при запуске файла
    parser = argparse.ArgumentParser()
    
    if len(sys.argv) == 1: 
        top_recs() # Нет аргументов, выдаем треки по умолчанию
    else:
        if sys.argv[1] == '--offline':
            parser.add_argument ('-user_id', '--user_id')
            parser.add_argument ('-k', '--k')
            namespace = parser.parse_args(sys.argv[2:])
            if namespace.user_id is None: 
                logger.info(f"Error, wrong parameters")
            elif namespace.k is None:
                offline_recs(namespace.user_id)
            else: 
                offline_recs(namespace.user_id, namespace.k)

        elif sys.argv[1] == '--add_online':
            parser.add_argument ('-user_id', '--user_id')
            parser.add_argument ('-item_id', '--item_id')
            namespace = parser.parse_args(sys.argv[2:])
            if namespace.user_id and namespace.item_id:
                add_online(namespace.user_id, namespace.item_id)
            else:
                logger.info(f"Error, wrong parameters")
            
        elif sys.argv[1] == '--online':
            parser.add_argument ('-user_id', '--user_id')
            parser.add_argument ('-k', '--k')
            namespace = parser.parse_args(sys.argv[2:])
            if namespace.user_id is None:
                logger.info(f"Error, wrong parameters")
            elif namespace.k is None:
                online_recs(namespace.user_id)
            else: 
                online_recs(namespace.user_id, namespace.k)

        elif sys.argv[1] == '--blended':
            parser.add_argument ('-user_id', '--user_id')
            parser.add_argument ('-k', '--k')
            namespace = parser.parse_args(sys.argv[2:])
            if namespace.user_id is None:
                logger.info(f"Error, wrong parameters")
            elif namespace.k is None:
                blended_recs(namespace.user_id)
            else:
                blended_recs(namespace.user_id, namespace.k)
        
        else:
            logger.info(f"Error, wrong parameters")
