# menu/templatetags/menu_tags.py
from typing import Dict, List, Optional

from django import template
from django.db.models import Prefetch
from django.http import HttpRequest

from menu.models import MenuItem

register = template.Library()


@register.inclusion_tag("menu/menu.html", takes_context=True)
def draw_menu(context: dict, menu_name: str):
    """
    {% draw_menu 'main_menu' %}

    Требования:
    - 1 запрос к БД на меню:
      MenuItem.objects.filter(menu__name=menu_name).select_related('parent', 'menu')
    - активный пункт определяется по request.path
    - всё выше активного — раскрыто, плюс первый уровень детей под активным.
    """
    request: HttpRequest = context["request"]

    # РОВНО один запрос к БД для конкретного меню.
    items = list(
        MenuItem.objects.filter(menu__name=menu_name)
        .select_related("parent", "menu")
        .order_by("parent_id", "order", "id")
    )

    if not items:
        return {"menu_tree": [], "menu_name": menu_name, "request": request}

    # Индексы: по id и по parent_id
    items_by_id: Dict[int, MenuItem] = {item.id: item for item in items}
    children_map: Dict[Optional[int], List[MenuItem]] = {}

    for item in items:
        parent_id = item.parent_id
        children_map.setdefault(parent_id, []).append(item)

    # Определяем активный пункт по текущему пути
    current_path = request.path
    active_item: Optional[MenuItem] = None

    # Сначала резолвим URL для всех, чтобы не вызывать get_url по тысяче раз в шаблоне
    item_urls: Dict[int, str] = {}
    for item in items:
        url = item.get_url()
        item_urls[item.id] = url
        if url == current_path and active_item is None:
            active_item = item

    # Собираем множество id, которые должны быть "раскрыты"
    open_ids = set()
    if active_item:
        # все предки + сам активный
        node = active_item
        while node is not None:
            open_ids.add(node.id)
            node = node.parent

        # первый уровень детей активного тоже раскрыт
        for child in children_map.get(active_item.id, []):
            open_ids.add(child.id)

    # Строим дерево: каждый узел = dict с item, url, is_active, is_open, children
    def build_node(item: MenuItem):
        node_children = []
        if item.id in open_ids:
            # грузим только первый уровень детей, если узел открыт
            for child in children_map.get(item.id, []):
                node_children.append(build_node(child))

        return {
            "item": item,
            "url": item_urls[item.id],
            "is_active": bool(active_item and item.id == active_item.id),
            "is_open": item.id in open_ids,
            "children": node_children,
        }

    # Корни — у кого parent_id is None
    roots = children_map.get(None, [])

    menu_tree = [build_node(root) for root in roots]

    return {
        "menu_tree": menu_tree,
        "menu_name": menu_name,
        "request": request,
    }
