#!/usr/bin/python3

import psycopg2 as pg
from configparser import ConfigParser
import json
import requests as req
import os
import time

def download_image(image_uri, output_dir, year, file_name, retry_limit, sleep_time):
    img_url = "https://www.nasa.gov/sites/default/files" + image_uri

    file_output_dir = output_dir + "/" + year
    os.makedirs(name =file_output_dir, exist_ok=True)

    for i in range(retry_limit):
        res = req.get(url=img_url,stream=True)
        if res.status_code != 200:
            print(f"Cannot download ${img_url}. Trying in {sleep_time} seconds...")
            time.sleep(sleep_time)
            continue
        with open(file_output_dir + "/" + file_name, "wb") as f:
            for chunk in res:
                f.write(chunk)
        return True
    return False


def save_to_db(cursor, nid, name, time, type, description, uri, width, height, stored_path, data):
    cursor.execute("execute img_insert (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)", (nid, name, description, uri, stored_path, width, height, type, time, data))


def save_items_from_page(cursor, img_dir, skip, limit, retry_limit, sleep_time):
    page_url = "https://www.nasa.gov/api/2/ubernode/" + "_search?from=" + str(skip) + "&size=" + str(limit)\
               + "&sort=promo-date-time:asc"

    json_res = download_page(page_url, retry_limit, sleep_time)

    if json_res is None:
        print(f"Failed to load page, skip: {skip}, limit: {limit}")

    hits = json_res['hits']
    total = hits['total']

    for hit in hits['hits']:
        source = hit['_source']

        try:
            nid = source['nid']
            name = source['title']
            time = source['promo-date-time']
            type = source['ubernode-type']
            description = source['image-feature-caption']
            uri = source['master-image']['uri']
            width = source['master-image']['width']
            height = source['master-image']['height']

            year = time[0:4]
            month = time[6:7]
            day = time[9:10]
            # starts with public://, it starts with /
            inner_uri = uri[8:]

            file_name = year + "_" + month + "_" + day + "__" + nid + "__" + os.path.basename(inner_uri)
        except:
            print(f"Parse error: {json.dumps(source)}")
            continue

        if download_image(inner_uri, img_dir, year, file_name, retry_limit, sleep_time):
            save_to_db(cursor, nid, name, time, type, description, inner_uri, width, height, "/" + year + "/" + file_name, json.dumps(source))
        else:
            print(f"Failed to download an image with uri {inner_uri}")

    return total


def download_page(page_url, retry_limit, sleep_time):
    json_res = None
    for i in range(retry_limit):
        res = req.get(page_url)

        if res.status_code != 200:
            print(f'Cannot connect to {page_url}, trying in {sleep_time} seconds...')
            time.sleep(sleep_time)
            continue

        json_res = json.loads(res.content.decode('utf-8'))
        break
    return json_res


def connect(config):
    schema = config.get('database', 'schema')
    return pg.connect(
        dbname=config.get('database', 'database'),
        user=config.get('database', 'user'),
        host=config.get('database', 'host'),
        password=config.get('database', 'password'),
        port=config.get('database', 'port'),
        options=f'-c search_path={schema}',
    )


if __name__ == '__main__':
    parser = ConfigParser()
    parser.read('config.ini')

    img_dir = parser.get(section='application', option='destination', fallback='./images')
    os.makedirs(name=img_dir, exist_ok=True)

    page_size = parser.getint(section='application', option='page_size', fallback=100)
    sleep_time = parser.getint(section='application', option='retry_sleep_seconds', fallback=5)
    retry_limit = parser.getint(section='application', option='retry_limit', fallback=10)

    conn = None
    try:
        conn = connect(parser)

        cur = conn.cursor()
        cur.execute("prepare img_insert as insert into images(nid, name, description, uri, stored_uri, width, height,"
                    " type, time, all_data) values( " +
                    "$1, $2, $3, $4, $5, $6, $7, $8, $9, $10)")

        has_more = True
        downloaded = 0
        while has_more:
            total = save_items_from_page(cur, img_dir, downloaded, page_size, retry_limit, sleep_time)

            downloaded += page_size
            if downloaded >= total:
                downloaded = total
                has_more = False

            print(f"Downloaded {downloaded} out of {total} ({str(round(downloaded/total * 100, 2))}%)")
            conn.commit()

        cur.close()

        print("FINISHED")
    finally:
        if conn is not None:
            conn.close()
