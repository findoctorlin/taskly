from argparse import ArgumentParser
from datetime import datetime
from tabulate import tabulate
from typing import Literal, Callable, Generator
import json
import os
import sys


def main() -> None:
    supported_queries: dict[str, dict] = get_supported_queries() # 冒号:是Type Hinting(类型注解)，表示var的类型

    querie, args = get_querie(supported_queries)

    DATABASE_PATH: str = os.path.expanduser("~/taskly.json") # 表示DATABASE_PATH的类型是str

    database: dict[str, dict] = load_database(DATABASE_PATH)

    try:
        querie(database, **args)
    except KeyError:
        sys.exit("No task found with the provided ID")

    save_database(database, DATABASE_PATH)


def add_task(database: dict[str, dict], description: str) -> None: # description是具体要记录的TODO，作为参数传给database
    today: str = datetime.today().isoformat()
    id: str = str(int(max("0", *database.keys())) + 1) # *是unpacking操作符，可以独立得到database的key值
    database[id] = {
        "description": description,
        "status": "todo",
        "created-at": today,
        "updated-at": today,
    }
    list_task({id: database[id]})


def delete_task(database: dict[str, dict], id: str) -> None:
    list_task({id: database[id]})
    del database[id]


def update_task(database: dict[str, dict], id: str, description: str) -> None:
    database[id]["description"] = description
    database[id]["updated-at"] = datetime.today().isoformat()
    list_task({id: database[id]})


def list_task(
    database: dict[str, dict],
    status: Literal["all", "done", "in-progress", "todo"] = "all",
) -> None:
    DATETIME_FORMAT: str = "%d/%m/%Y %H:%M:%S"

    table: Generator = (
        {
            "Id": id,
            "Description": properties["description"],
            "Status": properties["status"],
            "Created At": datetime.fromisoformat(properties["created-at"]).strftime(
                DATETIME_FORMAT
            ),
            "Updated At": datetime.fromisoformat(properties["updated-at"]).strftime(
                DATETIME_FORMAT
            ),
        }
        for id, properties in sorted(database.items(), key=lambda t: t[0])
        if status == "all" or status == properties["status"]
    )

    print(
        tabulate(table, tablefmt="rounded_grid", headers="keys") or "Nothing to display"
    )


def mark_in_progress_task(database: dict[str, dict], id: str) -> None:
    database[id]["status"] = "in-progress"
    database[id]["updated-at"] = datetime.today().isoformat()
    list_task({id: database[id]})


def mark_done_task(database: dict[str, dict], id: str) -> None:
    database[id]["status"] = "done"
    database[id]["updated-at"] = datetime.today().isoformat()
    list_task({id: database[id]})


def load_database(path: str) -> dict[str, dict]: #load路径数据进入一个database
    try:
        with open(path) as f:
            database = json.load(f)
    except FileNotFoundError:
        database = {}
    return database


def save_database(database: dict[str, dict], path: str) -> None:
    with open(path, "w") as f:
        json.dump(database, f, indent=4) #将database写入JSON文件


def get_supported_queries() -> dict[str, dict]:
    return {
        "add": {
            "target": add_task,
            "help": "Add a new task to your task list",
            "args": [
                {"name_or_flags": ["description"], "help": "Description of the task"}
            ],
        },
        "delete": {
            "target": delete_task,
            "help": "Delete a task from your task list",
            "args": [
                {
                    "name_or_flags": ["id"],
                    "help": "ID of the task you want to delete",
                }
            ],
        },
        "update": {
            "target": update_task,
            "help": "Update the description of a task",
            "args": [
                {
                    "name_or_flags": ["id"],
                    "help": "ID of the task to update",
                },
                {
                    "name_or_flags": ["description"],
                    "help": "New description for the task",
                },
            ],
        },
        "list": {
            "target": list_task,
            "help": "List all tasks or filter them by status",
            "args": [
                {
                    "name_or_flags": ["--status", "-s"],
                    "help": "Filter tasks by status (default is 'all')",
                    "choices": ["all", "done", "todo", "in-progress"],
                    "type": str.lower,
                    "default": "all",
                }
            ],
        },
        "mark-in-progress": {
            "target": mark_in_progress_task,
            "help": "Mark a task as 'in-progress'",
            "args": [{"name_or_flags": ["id"], "help": "ID of the task"}],
        },
        "mark-done": {
            "target": mark_done_task,
            "help": "Mark a task as 'done'",
            "args": [{"name_or_flags": ["id"], "help": "ID of the task"}],
        },
    }


def get_querie(supported_queries: dict[str, dict]) -> tuple[Callable, dict]:
    parser: ArgumentParser = ArgumentParser(
        description="A CLI application to efficiently manage your tasks"
    )
    sub_parsers = parser.add_subparsers(title="commands", dest="command", required=True) # 添加子命令如add delete update...

    for name, properties in supported_queries.items():
        p = sub_parsers.add_parser(name, help=properties["help"]) //name如add, list, delete...
        for arg in properties["args"]:
            p.add_argument(*arg.pop("name_or_flags"), **arg) # arg.pop("name_or_flags") 从字典中移除并返回 name_or_flags 的值，即 ["--status", "-s"]。
                                                             # * 这个列表解包成单独的元素，即 --status 和 -s, 这两个元素作为位置参数传递给add_argument()
                                                             # ** 把整个dict解包传递给add_argument()
                                                             # 最终相当于p.add_argument("--status", "-s", help="Filter tasks by status (default is 'all')", choices=["all", "done", "todo", "in-progress"], type=str.lower, default="all")

    '''
    解析用户输入
    '''
    args: dict = parser.parse_args().__dict__ # parser.parse_args() 解析用户输入的命令行参数
    querie: Callable = supported_queries[args.pop("command")]["target"]

    return querie, args


if __name__ == "__main__":
    main()
