"""Точка запуска ServiceMonitor: меню и вывод данных."""

from checker import sort_services
from monitor import Monitor
from service import Service
from storage import delete_service, load_services, save_service
from utils import input_int, input_str


def list_services(services: list[Service]) -> None:
    """Вывести список сервисов по названию, без проверки."""
    print("\n=== Список сервисов ===\n")
    if not services:
        print("  Список сервисов пуст.\n")
        return

    for service in sort_services(services):
        print(f"  {service.name}")
        print(f"    URL: {service.url}")
        print(f"    Описание: {service.description}")
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
    print("4. Найти сервис по названию")
    print("5. Добавить сервис")
    print("6. Удалить сервис")
    print("7. Выход\n")


def main() -> None:
    """Точка запуска приложения."""
    print("\n=== ServiceMonitor ===")
    monitor = Monitor(load_services())
    monitor.check_all()

    while True:
        print_menu()
        choice = input("Выберите действие: ").strip()

        if choice == "1":
            monitor.check_all()

        elif choice == "2":
            service = choose_service(monitor.services)
            if service is not None:
                monitor.check_one(service)

        elif choice == "3":
            list_services(monitor.services)

        elif choice == "4":
            query = input_str("Введите часть названия: ")
            found = monitor.find(query)
            if found:
                list_services(found)
            else:
                print("\n  Ничего не найдено.")

        elif choice == "5":
            print("\nДобавление нового сервиса:")
            name = input_str("  Название: ")
            url = input_str("  URL для проверки: ")
            description = input("  Описание: ").strip()
            new_service = Service(name, url, description)
            if save_service(new_service):
                monitor.add(new_service)
                print(f"  Сервис '{name}' добавлен.")
            else:
                print(f"  Сервис '{name}' уже существует.")

        elif choice == "6":
            service = choose_service(monitor.services)
            if service is not None:
                if delete_service(service.name):
                    monitor.remove(service)
                    print(f"  Сервис '{service.name}' удалён.")
                else:
                    print("  Не удалось удалить файл сервиса.")

        elif choice == "7":
            print("\nДо свидания!")
            break

        else:
            print("\n  Неверный выбор. Попробуйте снова.")


if __name__ == "__main__":
    main()
