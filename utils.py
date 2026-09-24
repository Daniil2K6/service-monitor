"""Вспомогательные функции безопасного ввода."""


def input_int(prompt: str) -> int:
    """Запросить у пользователя целое число.

    При некорректном вводе запрос повторяется.
    """
    while True:
        try:
            return int(input(prompt))
        except ValueError:
            print("  Введите число.")


def input_str(prompt: str) -> str:
    """Запросить у пользователя непустую строку.

    Пустой ввод не принимается, запрос повторяется.
    """
    while True:
        value = input(prompt).strip()
        if value:
            return value
        print("  Значение не может быть пустым.")
