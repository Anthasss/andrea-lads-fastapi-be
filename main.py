from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import requests
from bs4 import BeautifulSoup
import re
import datetime
from dotenv import load_dotenv
import os
import psycopg2

load_dotenv()

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "https://andrea-lads.vercel.app"
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

DATABASE_URL = os.getenv("DATABASE_URL")


@app.get("/")
def read_root():
    return {"Hello": "World"}


@app.get("/scrape")
def scrape_lads():

    conn = None
    cur = None

    try:
        conn = psycopg2.connect(DATABASE_URL)
        cur = conn.cursor()

        url = "https://www.lapakgaming.com/id-id/love-and-deepspace"
        headers = {"User-Agent": "Mozilla/5.0"}

        res = requests.get(
            url,
            headers=headers,
            timeout=30
        )

        soup = BeautifulSoup(res.text, "lxml")

        text = soup.get_text()

        match = re.search(
            r"(\d+)\s*item dibeli hari ini",
            text
        )

        if not match:
            return {
                "status": "failed",
                "message": "data not found"
            }

        value = int(match.group(1))

        today = datetime.date.today()

        cur.execute(
            """
            INSERT INTO sales_data
            (value, scrape_date, scraped_at)

            VALUES (%s, %s, %s)

            ON CONFLICT (scrape_date)
            DO UPDATE SET
                value = EXCLUDED.value,
                scraped_at = EXCLUDED.scraped_at
            """,
            (
                value,
                today,
                datetime.datetime.now()
            )
        )

        conn.commit()

        return {
            "status": "success",
            "sell_count": value
        }

    except Exception as e:
        return {
            "status": "error",
            "message": str(e)
        }

    finally:
        if cur:
            cur.close()

        if conn:
            conn.close()

@app.get("/data")
def fetch_data():

    conn = None
    cur = None

    try:
        conn = psycopg2.connect(DATABASE_URL)
        cur = conn.cursor()

        cur.execute("""
            SELECT
                value,
                scrape_date,
                scraped_at
            FROM sales_data
            ORDER BY scrape_date DESC
        """)

        rows = cur.fetchall()

        data = []

        for row in rows:
            data.append({
                "value": row[0],
                "scrape_date": row[1],
                "scraped_at": row[2]
            })

        return {
            "status": "success",
            "data": data
        }

    except Exception as e:
        return {
            "status": "error",
            "message": str(e)
        }

    finally:
        if cur:
            cur.close()

        if conn:
            conn.close()