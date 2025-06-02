from pydantic import BaseModel

class ToDoItem(BaseModel):
    title: str
    completed: bool = False
