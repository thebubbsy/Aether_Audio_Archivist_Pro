from textual import work
import asyncio

class MyClass:
    @work
    async def my_method(self):
        return "done"

obj = MyClass()
print(f"Type: {type(obj.my_method)}")
print(f"Dir: {dir(obj.my_method)}")
