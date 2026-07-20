"""Dependency injection."""
from sosad.di.container import Container
from sosad.di.markers import inject
from sosad.di.providers import factory, singleton, value
from sosad.di.scopes import ScopeManager

__all__ = ["Container", "ScopeManager", "factory", "inject", "singleton", "value"]
