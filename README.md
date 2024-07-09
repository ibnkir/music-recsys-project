# Подготовка виртуальной машины

## Склонируйте репозиторий

Склонируйте репозиторий проекта:

```
git clone git@github.com:practicum-mle/mle-recsys-project.git
```

## Активируйте виртуальное окружение

Используйте то же самое виртуальное окружение, что и созданное для работы с уроками. Если его не существует, то его следует создать.

Создать новое виртуальное окружение можно командой:

```
python3 -m venv env_recsys_start
```

После его инициализации следующей командой

```
. env_recsys_start/bin/activate
```

установите в него необходимые Python-пакеты следующей командой

```
pip install -r requirements.txt
```

### Скачайте файлы с данными

Для начала работы понадобится три файла с данными:
- [tracks.parquet](https://storage.yandexcloud.net/mle-data/ym/tracks.parquet)
- [catalog_names.parquet](https://storage.yandexcloud.net/mle-data/ym/catalog_names.parquet)
- [interactions.parquet](https://storage.yandexcloud.net/mle-data/ym/interactions.parquet)
 
Скачайте их в директорию локального репозитория. Для удобства вы можете воспользоваться командой wget:

```
wget https://storage.yandexcloud.net/mle-data/ym/tracks.parquet

wget https://storage.yandexcloud.net/mle-data/ym/catalog_names.parquet

wget https://storage.yandexcloud.net/mle-data/ym/interactions.parquet
```

## Запустите Jupyter Lab

Запустите Jupyter Lab в командной строке

```
jupyter lab --ip=0.0.0.0 --no-browser
```

# Предобработка данных

Код для предварительной обработки данных находится в файле `part_1_preprocess_eda.ipynb`.

# Расчёт рекомендаций

Код для расчёта рекомендаций находится в файле `part_2_recs.ipynb`.

<*укажите здесь значения полученных метрик для оффлайн-рекомендаций*>

# Инструкции для тестирования сервиса

Код сервиса рекомендаций находится в файле `recommendations_service.py`.

<*укажите здесь необходимые шаги для запуска сервиса рекомендаций*>

Код для тестирования сервиса находится в файле `part_3_test.ipynb`.

<*укажите здесь необходимые шаги для тестирования сервиса рекомендаций*>
