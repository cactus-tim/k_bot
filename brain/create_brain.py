import json
from openai import OpenAI
import os
import re
from dotenv import load_dotenv

from database.req import get_user, update_user
from hands.hands import mamba_parsing_dialogs
from instance import client


async def gpt_assystent_mes(thread_id,  assistant_id, mes="давай начнем"):
    message = client.beta.threads.messages.create(
        thread_id=thread_id,
        role="user",
        content=mes
    )

    run = client.beta.threads.runs.create_and_poll(
        thread_id=thread_id,
        assistant_id=assistant_id,
    )

    messages = client.beta.threads.messages.list(thread_id=thread_id)
    data = messages.data[0].content[0].text.value.strip()
    if not data:
        pass
        # raise ContentError
    else:
        return data


async def create_brain(user_id, prompt):
    user = await get_user(user_id)
    dialogs = await mamba_parsing_dialogs(user_id)
    filename = "dialogs.txt"
    with open(filename, "wb") as file:
        file.write(dialogs.encode())
    vector_store = client.beta.vector_stores.create(
        name=f"dialogs_{user_id}"
    )
    with open(filename, "rb") as file_stream:
        file_batch = client.beta.vector_stores.file_batches.upload_and_poll(
            vector_store_id=vector_store.id,
            files=[file_stream]
        )
    if file_batch.status != 'completed':
        # TODO: raise some error with message to user and to admin
        pass
    os.remove(filename)
    assistant = client.beta.assistants.create(
        name=f"brain_{user_id}",
        instructions=prompt,
        model="gpt-4o",
        tools=[{"type": "file_search"}],
    )
    assistant = client.beta.assistants.update(
        assistant_id=assistant.id,
        tool_resources={"file_search": {"vector_store_ids": [vector_store.id]}},
    )
    await update_user(user_id, {'brain_id': assistant.id})



