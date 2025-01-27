# RQ integration for Dishka

[![PyPI version](https://badge.fury.io/py/dishka_rq.svg)](https://pypi.python.org/pypi/dishka_rq)
[![Supported versions](https://img.shields.io/pypi/pyversions/dishka_rq.svg)](https://pypi.python.org/pypi/dishka_rq)
[![License](https://img.shields.io/github/license/prepin/dishka_rq)](https://github.com/prepin/dishka_rq/blob/master/LICENSE)

This package provides integration of [Dishka](http://github.com/reagento/dishka/) DI framework and [RQ](https://github.com/rq/rq) task queue manager.

## Features


* **Automatic Scope Management**: Handles REQUEST and SESSION scopes per RQ job execution.
* **Dependency Injection**: Injects dependencies into task handlers via:
  * Subclassed `DishkaWorker` for auto-injection.
  * `@inject` decorator for manual setup with standard RQ workers.

## Installation

Install using `pip`

```sh
pip install dishka_rq
```

Or with `uv`

```sh
uv add dishka_rq
```

## Usage

### Method 1: Using `DishkaWorker` Subclass


1. **Set Up Providers and Container**

Define your Dishka providers and container as usual:

```python
from dishka import Provider, Scope, provide, make_container

class StrProvider(Provider):
    @provide(scope=Scope.REQUEST)
    def hello(self) -> str:
        return "Hello"

provider = StrProvider()
container = make_container(provider)
```

2. **Annotate Task Dependencies**

Use `FromDishka[...]` to mark injected parameters:

```python
from dishka import FromDishka

def hello_world(hello: FromDishka[str]):
    return f"{hello} world!"
```

3. **Run worker**

Start an RQ worker with DishkaWorker:

```python
from dishka_rq import DishkaWorker
from redis import Redis

conn = Redis()
queues = ["default"]
worker = DishkaWorker(container=container, queues=queues, connection=conn)
worker.work(with_scheduler=True)
```

```python
python run_worker.py
```

### Method 2: Using @inject Decorator

If you don't need autoinjection or do not want to use custom DishkaWorker subclass.

1. **Set Up Providers and Container**

Same as Method 1.

2. **Decorate Task Functions**

Use `@inject` and annotate dependencies:

```python
from dishka_rq import inject, FromDishka

@inject
def hello_world(hello: FromDishka[str]):
    return f"{hello} world!"
```

3. **Configure Standard RQ Worker**

Attach Dishka to an RQ worker:

```python
from dishka_rq import setup_dishka
from rq import Worker
from redis import Redis

worker = Worker(queues=["default"], connection=Redis())
setup_dishka(worker, container)

worker.work(with_scheduler=True)
```

## Requirements:

* Python 3.10+
* Dishka >= 1.4.2
* RQ >= 2.0
