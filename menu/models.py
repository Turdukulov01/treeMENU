from django.db import models
from django.urls import reverse, NoReverseMatch


class Menu(models.Model):
    """
    Контейнер меню. Например: main_menu, footer_menu и т.д.
    """
    name = models.CharField(
        max_length=100,
        unique=True,
        help_text="Системное имя меню. Используется в template tag {% draw_menu 'name' %}",
    )
    title = models.CharField(
        max_length=200,
        blank=True,
        help_text="Человекочитаемое название (для админки)",
    )

    class Meta:
        verbose_name = "Меню"
        verbose_name_plural = "Меню"

    def __str__(self) -> str:
        return self.title or self.name


class MenuItem(models.Model):
    """
    Пункт меню. Обычное дерево через parent (adjacency list).
    """
    menu = models.ForeignKey(
        Menu,
        related_name="items",
        on_delete=models.CASCADE,
        verbose_name="Меню",
    )
    parent = models.ForeignKey(
        "self",
        related_name="children",
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        verbose_name="Родительский пункт",
    )
    title = models.CharField(
        max_length=200,
        verbose_name="Название пункта",
    )
    url = models.CharField(
        max_length=255,
        blank=True,
        help_text="Явный URL (например /contacts/). Если указан named_url, он приоритетнее.",
    )
    named_url = models.CharField(
        max_length=100,
        blank=True,
        help_text="Имя url из urls.py (reverse). Например: 'contacts:list'",
    )
    order = models.PositiveIntegerField(
        default=0,
        verbose_name="Порядок",
    )

    class Meta:
        verbose_name = "Пункт меню"
        verbose_name_plural = "Пункты меню"
        ordering = ("menu", "parent__id", "order", "id")

    def __str__(self) -> str:
        return self.title

    def get_url(self) -> str:
        """
        - если есть named_url -> reverse(named_url)
        - иначе берём url как есть
        - если пусто -> '#'
        """
        if self.named_url:
            try:
                return reverse(self.named_url)
            except NoReverseMatch:
                if self.url:
                    return self.url
                return "#"
        if self.url:
            return self.url
        return "#"
