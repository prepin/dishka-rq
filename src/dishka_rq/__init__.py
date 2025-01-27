__all__ = ["DishkaWorker", "setup_dishka", "inject", "FromDishka"]

from dishka import FromDishka

from .rq_integration import DishkaWorker, inject, setup_dishka
