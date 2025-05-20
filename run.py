import os
import subprocess
import sys

def install_requirements():
    try:
        import pygame
        import tkinter
        import pandas
        print("[✓] Зависимости уже установлены.")
    except ImportError:
        print("[...] Устанавливаем зависимости...")
        subprocess.check_call([sys.executable, "-m", "pip", "install", "-r", "requirements.txt"])

def initialize_db():
    print("[✓] Инициализируем базу данных...")
    subprocess.run([sys.executable, "db.py"], check=True)

def run_game():
    print("[✓] Запускаем игру...")
    # Запускаем игру и ждем её завершения
    result = subprocess.run([sys.executable, "MineSweeper.py"])
    # Можно проверить результат выполнения
    if result.returncode != 0:
        print("Игра завершилась с ошибкой.")
    else:
        print("Игра успешно завершена.")

if __name__ == "__main__":
    install_requirements()
    initialize_db()
    run_game()