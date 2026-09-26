"""Точка запуска ServiceMonitor: меню и вывод данных."""

from checker import (
    collect_results,
    count_available,
    percent_available,
    search_services,
    sort_services,
)
from monitor import Monitor
from service import Service
from storage import (
    delete_service,
    load_groups,
    load_services,
    save_service,
)
from utils import input_int, input_str


def print_stats(monitor: Monitor) -> None:
    """Вывести сводку по всем проверкам."""
    results = collect_results(monitor.services)
    if not results:
        return
    available = count_available(results)
    percent = percent_available(results)
    print(
        f"Проверок всего: {len(results)}, "
        f"доступных: {available} ({percent}%)"
    )


def list_services(services: list[Service]) -> None:
    """Вывести сервисы с группой и последним результатом."""
    print("\n=== Список сервисов ===\n")
    if not services:
        print("  Список сервисов пуст.\n")
        return

    for service in sort_services(services):
        group_name = service.group.name if service.group else "—"
        print(f"  {service.name}")
        print(f"    URL: {service.url}")
        print(f"    Группа: {group_name}")
        print(f"    Описание: {service.description}")
        last = service.last_check()
        if last is not None:
            print(
                f"    Проверок: {len(service.checks)}, "
                f"последний: {last}"
            )
        print()


def show_groups(monitor: Monitor) -> None:
    """Показать группы и входящие в них сервисы."""
    print("\n=== Группы сервисов ===\n")
    if not monitor.groups:
        print("  Групп нет.\n")
        return

    for group in sorted(monitor.groups, key=lambda g: g.name):
        print(f"  {group.name}")
        if group.description:
            print(f"    {group.description}")
        if group.services:
            names = ", ".join(
                s.name for s in sort_services(group.services)
            )
            print(f"    Сервисы: {names}")
        else:
            print("    Сервисов нет")
        print()


def choose_service(services: list[Service]) -> Service | None:
    """Показать нумерованный список и вернуть выбранный сервис."""
    if not services:
        print("  Список сервисов пуст.")
        return None

    ordered = sort_services(services)
    print("\nДоступные сервисы:")
    for index, service in enumerate(ordered, 1):
        print(f"  {index}. {service.name}")

    choice = input_int("\nВведите номер сервиса: ")
    if 1 <= choice <= len(ordered):
        return ordered[choice - 1]

    print("  Неверный номер.")
    return None


def print_menu() -> None:
    """Вывести главное меню."""
    print("\n=== ServiceMonitor ===\n")
    print("1. Проверить все сервисы")
    print("2. Проверить сервис выборочно")
    print("3. Показать список сервисов")
    print("4. Показать группы и их сервисы")
    print("5. Найти сервис по названию")
    print("6. Добавить сервис")
    print("7. Удалить сервис")
    print("8. Выход\n")


def main() -> None:
    """Точка запуска приложения."""
    print("\n=== ServiceMonitor ===")
    groups = load_groups()
    monitor = Monitor(load_services(groups), groups)
    monitor.check_all()
    print_stats(monitor)

    while True:
        print_menu()
        choice = input("Выберите действие: ").strip()

        if choice == "1":
            monitor.check_all()
            print_stats(monitor)

        elif choice == "2":
            service = choose_service(monitor.services)
            if service is not None:
                monitor.check_one(service)

        elif choice == "3":
            list_services(monitor.services)

        elif choice == "4":
            show_groups(monitor)

        elif choice == "5":
            query = input_str("Введите часть названия: ")
            found = search_services(monitor.services, query)
            if found:
                list_services(found)
            else:
                print("\n  Ничего не найдено.")

        elif choice == "6":
            print("\nДобавление нового сервиса:")
            name = input_str("  Название: ")
            url = input_str("  URL для проверки: ")
            description = input("  Описание: ").strip()
            group_name = input_str("  Группа: ")
            group = monitor.get_or_create_group(group_name)
            new_service = Service(name, url, description, group)
            if save_service(new_service):
                monitor.add_service(new_service)
                print(
                    f"  Сервис '{name}' добавлен "
                    f"в группу '{group_name}'."
                )
            else:
                print(f"  Сервис '{name}' уже существует.")

        elif choice == "7":
            service = choose_service(monitor.services)
            if service is not None:
                if delete_service(service.name):
                    monitor.remove_service(service)
                    print(f"  Сервис '{service.name}' удалён.")
                else:
                    print("  Не удалось удалить файл сервиса.")

        elif choice == "8":
            print("\nДо свидания!")
            break

        else:
            print("\n  Неверный выбор. Попробуйте снова.")


if __name__ == "__main__":
    main()
