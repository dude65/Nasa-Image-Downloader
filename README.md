# Nasa-Image-Downloader
This project allows you to download and manage your images from public NASA image gallery.

## Prerequisites
 - `Python 3.6+`, modules `requests` and `psycopg2`
 - `PostgreSQL 9.4+` database
    1. create database, e.g. `nasa`
    2. create schema, e.g. `images`
    3. run this command as admin: ``CREATE EXTENSION "uuid-ossp";``
    4. run `init.sql` to create table

## Run
In order to run the script, it is necessary to configure `config.ini` at first.
Then it is possible to run the python script via `python3 images_download.py` or via `./images_download.py` in Linux or
or Mac OS system.
