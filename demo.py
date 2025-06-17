import asyncio
import json
import random
from websockets.asyncio.client import connect


ACTIONS = [
    "UP",
    "DOWN",
    "LEFT",
    "RIGHT",
    "STAY",
    "BOMB"
]

WEIGHTS = [
    10,
    10,
    10,
    10,
    3,
    1
]


async def hello1(uri: str, id: int):
    async with connect(uri) as websocket:
        while True:
            data = await websocket.recv()
            data = json.loads(data)
            print(f"{id}: {data}")

            await asyncio.sleep(1)

            action = random.choices(ACTIONS, weights=WEIGHTS, k=1)
            print(f"{id}: {action}")
            await websocket.send('{"action": "' + action[0] + '"}')


async def main():
    game_id = 176

    cred = [
        f"wss://course.af.shvarev.com/ws/{game_id}?token=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiIxQGV4YW1wbGUuY29tIiwiZXhwIjoxNzUwMDMyNzQ5fQ.ngJYwbwqup28UP-ONB70f_IIhcemVGRYbSjqNrOAaYc",
        f"wss://course.af.shvarev.com/ws/{game_id}?token=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiIzQGV4YW1wbGUuY29tIiwiZXhwIjoxNzUwMDM0MzYyfQ.hLEEoDsXECi7RpkN4iBKwsWGzrq_Yq8SRl-UUIEtOWM",
        # f"wss://course.af.shvarev.com/ws/{game_id}?token=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiIyQGV4YW1wbGUuY29tIiwiZXhwIjoxNzUwMDMzMjMzfQ.trqhPqstAsZ-QVIVX7iUqLf1eYF2ljxqEOBv44qxT1g",
    ]

    await asyncio.gather(
        hello1(cred[0], 0),
        hello1(cred[1], 1),
        # hello1(cred[2], 2),
    )


if __name__ == "__main__":
    asyncio.run(main())
