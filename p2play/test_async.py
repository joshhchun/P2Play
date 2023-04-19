import asyncio


async def read_file(file_name):
    with open(file_name, 'rb') as f:
        text = f.read()
    print("Done reading file")

    with open("new_text.txt", "wb") as f:
        f.write(text)
    print("Done writing file")

async def add(x, y):
    print(f"Add {x} + {y}")
    return x + y
    

async def main():
    file_name = "/Users/joshchun/Downloads/IMG_0063.MOV"
    asyncio.create_task(read_file(file_name))
    print("hi")

if __name__ == '__main__':
    asyncio.run(main())
    
