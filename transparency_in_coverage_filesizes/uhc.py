import requests
import json
import sqlite3
import asyncio
import aiohttp

# Create a SQLite table of URLs and filesizes
con = sqlite3.connect("./uhc_data.db")
cur = con.cursor()
cur.execute("CREATE TABLE IF NOT EXISTS in_network_files(url PRIMARY KEY UNIQUE, size)")

print("Downloading UHC's blob file containing all URLs...")
resp = requests.get("https://transparency-in-coverage.uhc.com/api/v1/uhc/blobs/")
print("Finished.")

urls = [file["downloadUrl"] for file in resp.json()['blobs']]

async def fetch_url_sizes(table, urls):
    """
    Simple async function for getting all the file sizes in a list of urls
    and writing those to a SQLite table
    """
    
    session = aiohttp.ClientSession()
    fs = [session.head(url) for url in urls]

    for f in asyncio.as_completed(fs):
        resp = await f
        url = str(resp.url)
        size = int(resp.headers.get("content-length", -1))
        cur.execute(f"""INSERT OR IGNORE INTO {table} VALUES ("{url}", {size})""")
        con.commit()
        
    await session.close()

print("Fetching URLs and their sizes...")    
asyncio.run(fetch_url_sizes("in_network_files", urls))
total = cur.execute("SELECT SUM(size) FROM in_network_files").fetchone()[0]
#This is crazy!
print(f"Total filesize in GB: {total//1_000_000_000}")
