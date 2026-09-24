"""Точка запуска ServiceMonitor: меню и вывод данных."""

from checker import (
    check_service_status,
    search_services,
    sort_services,
)
from storage import delete_service, load_services, save_service
from utils import input_int, input_str


def show_all_services(services: list[dict]) -> None:
    """Проверить и вывести статус всех сервисов."""
    print("\n=== Мониторинг сервисов ===\n")
    if not services:
        print("  Список сервисов пуст.\n")
        return

    for service in services:
        check_service_status(service)


def list_services(services: list[dict]) -> None:
    """Вывести список сервисов по названию, без проверки."""
    print("\n=== Список сервисов ===\n")
    if not services:
        print("  Список сервисов пуст.\n")
        return

    for service in sort_services(services):
        print(f"  {service['name']}")
        print(f"    URL: {service['url']}")
        print(f"    Описание: {service.get('description', '')}")
        print()


def choose_service(services: list[dict]) -> dict | None:
    """Показать нумерованный список и вернуть выбранный сервис."""
    if not services:
        print("  Список сервисов пуст.")
        return None

    ordered = sort_services(services)
    print("\nДоступные сервисы:")
    for index, service in enumerate(ordered, 1):
        print(f"  {index}. {service['name']}")

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
    print("4. Найти сервис по названию")
    print("5. Добавить сервис")
    print("6. Удалить сервис")
    print("7. Выход\n")


def main() -> None:
    """Точка запуска приложения."""
    print("\n=== ServiceMonitor ===")
    services = load_services()
    show_all_services(services)

    while True:
        print_menu()
        choice = input("Выберите действие: ").strip()

        if choice == "1":
            show_all_services(services)

        elif choice == "2":
            service = choose_service(services)
            if service is not None:
                print()
                check_service_status(service)

        elif choice == "3":
            list_services(services)

        elif choice == "4":
            query = input_str("Введите часть названия: ")
            found = search_services(services, query)
            if found:
                list_services(found)
            else:
                print("\n  Ничего не найдено.")

        elif choice == "5":
            print("\nДобавление нового сервиса:")
            name = input_str("  Название: ")
            url = input_str("  URL для проверки: ")
            description = input("  Описание: ").strip()
            new_service = {
                "name": name,
                "url": url,
                "description": description,
            }
            if save_service(new_service):
                services.append(new_service)
                print(f"  Сервис '{name}' добавлен.")
            else:
                print(f"  Сервис '{name}' уже существует.")

        elif choice == "6":
            service = choose_service(services)
            if service is not None:
                if delete_service(service["name"]):
                    services.remove(service)
                    print(f"  Сервис '{service['name']}' удалён.")
                else:
                    print("  Не удалось удалить файл сервиса.")

        elif choice == "7":
            print("\nДо свидания!")
            break

        else:
            print("\n  Неверный выбор. Попробуйте снова.")


if __name__ == "__main__":
    main()
