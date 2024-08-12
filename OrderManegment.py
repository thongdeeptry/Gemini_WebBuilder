import json
import os

def listFiles(Projectname: str):
    return os.listdir(Projectname)

def getBiggestID(Projectname: str):
    return str(len(listFiles(Projectname)))

def id2blockName(Projectname: str, pageName:str, id: int):
    id = str(id)
    blockName = ""
    with open(f"./Projects/{Projectname}/bloksData/{pageName}/order.json") as f:
        blocks = json.load(f)
        for block in blocks:
            if id == str(block["id"]):
                blockName = block["blockName"]
                break
    return blockName

def blockName2id(Projectname: str, pageName:str, blockName: str):
    block_id = None
    with open(f"./Projects/{Projectname}/bloksData/{pageName}/order.json") as f:
        blocks = json.load(f)
        for block in blocks:
            if blockName == block["blockName"]:
                block_id = block["id"]
                break
    return block_id

def manageOrder(dir_path: str, Projectname: str, pageName: str, block: str):
    id = getBiggestID(dir_path)
    with open(f"{dir_path}/{id}", "w") as new_file:
        pass  # Creates an empty file

    with open(f"./Projects/{Projectname}/bloksData/{pageName}/order.json", "r") as f:
        data = json.load(f)

    new_block = {"id": int(id), "blockName": block}
    data.append(new_block)

    with open(f"./Projects/{Projectname}/bloksData/{pageName}/order.json", "w") as f:
        json.dump(data, f, indent=4)

def deleteOrder(dir_path: str, Projectname: str, pageName:str, id: int):
    block = id2blockName(Projectname,pageName, id)
    with open(f"./Projects/{Projectname}/bloksData/{pageName}/order.json") as f:
        data = json.load(f)

    data = [item for item in data if not (item["id"] == id and item["blockName"] == block)]

    with open(f"./Projects/{Projectname}/bloksData/order.json", "w") as f:
        json.dump(data, f, indent=4)

# Example Usage

