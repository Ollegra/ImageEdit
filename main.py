import sys
import os
import shutil
import json
import subprocess
import psutil
import logging
from logging.handlers import RotatingFileHandler
import struct
from pathlib import Path
from PyQt6.QtWidgets import (
    QApplication,
    QMainWindow,
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QPushButton,
    QLabel,
    QMessageBox,
    QInputDialog,
    QSplitter,
    QStatusBar,
    QMenu,
    QFileDialog,
    QProgressBar,
    QTextEdit,
    QScrollArea,
    QTabWidget,
    QPlainTextEdit,
    QDialog,
    QDialogButtonBox,
    QCheckBox,
    QSpinBox,
    QTreeWidget,
    QTreeWidgetItem,
    QHeaderView,
    QComboBox,
    QGroupBox,
    QGridLayout,
    QLineEdit,
    QFormLayout,
    QRadioButton,
)
from PyQt6.QtCore import (
    Qt,
    QThread,
    pyqtSignal,
    QMimeDatabase,
    QDateTime,
    QStandardPaths,
    QUrl,
    QMimeData,
)
from PyQt6.QtGui import (
    QIcon,
    QFont,
    QKeySequence,
    QAction,
    QPixmap,
    QColor,
    QDrag,
    QPainter,
    QPen,
    QBrush,
)
import logging.config

from config_loggin import logger_conf

logging.config.dictConfig(logger_conf)
logger = logging.getLogger("my_py_logger")


# Настройка логирования
def setup_logging():
    """Настройка системы логирования"""
    # Создаем папку для логов в папке приложения
    try:
        # Получаем путь к исполняемому файлу
        if getattr(sys, "frozen", False):
            # Если приложение скомпилировано (exe)
            app_dir = Path(sys.executable).parent
        else:
            # Если запускается как скрипт
            app_dir = Path(__file__).parent

        log_dir = app_dir / "logs"
        log_dir.mkdir(exist_ok=True)
        log_file = log_dir / "file_manager.log"
    except Exception:
        # Если не удается создать в папке приложения, используем временную папку
        import tempfile

        log_dir = Path(tempfile.gettempdir()) / "FileManager"
        log_dir.mkdir(exist_ok=True)
        log_file = log_dir / "file_manager.log"

    # Настраиваем логирование (только в файл, без вывода в консоль)
    logging.basicConfig(
        level=logging.DEBUG,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        handlers=[
            logging.handlers.RotatingFileHandler(
                log_file, maxBytes=1000000, backupCount=5, encoding="utf-8"
            )
        ],
    )

    # Создаем логгер для приложения
    logger = logging.getLogger("FileManager")
    logger.info("Система логирования инициализирована")
    logger.info(f"Лог файл: {log_file}")
    return logger


# Инициализируем логирование
# logger = setup_logging()


def is_path_relative_to(child_path, parent_path):
    """Простая и безопасная функция для проверки, является ли один путь подпутем другого"""
    try:
        # Простое строковое сравнение без рекурсии
        child_str = str(child_path).replace("/", "\\").lower().rstrip("\\")
        parent_str = str(parent_path).replace("/", "\\").lower().rstrip("\\")

        # Убираем лишние слеши
        while "\\\\" in child_str:
            child_str = child_str.replace("\\\\", "\\")
        while "\\\\" in parent_str:
            parent_str = parent_str.replace("\\\\", "\\")

        # Если пути одинаковые
        if child_str == parent_str:
            return True

        # Проверяем, что дочерний путь начинается с родительского + разделитель
        if child_str.startswith(parent_str + "\\"):
            return True

        return False

    except Exception:
        return False


class DragDropTreeWidget(QTreeWidget):
    """Кастомный QTreeWidget с поддержкой drag-and-drop"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.parent_panel = None
        self.drag_start_position = None

        # Настройка drag-and-drop
        self.setDragDropMode(QTreeWidget.DragDropMode.DragDrop)
        self.setDefaultDropAction(Qt.DropAction.CopyAction)
        self.setDragEnabled(True)
        self.setAcceptDrops(True)
        self.setDropIndicatorShown(True)

    def mousePressEvent(self, event):
        """Обработка нажатия мыши для начала drag операции"""
        if event.button() == Qt.MouseButton.LeftButton:
            self.drag_start_position = event.position().toPoint()

            item = self.itemAt(event.position().toPoint())

            # Обрабатываем множественный выбор с Ctrl+Click
            if item and event.modifiers() & Qt.KeyboardModifier.ControlModifier:
                logger.debug(f"Ctrl+Click обнаружен на элементе: {item.text(0)}")

                # Получаем текущее состояние выбора
                was_selected = item.isSelected()
                logger.debug(f"Элемент был выбран: {was_selected}")

                # Ctrl+Click - переключаем выбор элемента без запуска drag
                item.setSelected(not was_selected)

                # Принудительно устанавливаем элемент как текущий для корректной подсветки
                if not was_selected:  # Если элемент стал выбранным
                    self.setCurrentItem(item)

                logger.debug(f"Элемент теперь выбран: {item.isSelected()}")

                # Принудительно обновляем отображение
                self.update()

                # Показываем количество выбранных элементов в статус-баре
                if (
                    hasattr(self, "parent_panel")
                    and self.parent_panel
                    and self.parent_panel.parent_window
                ):
                    selected_count = len(
                        [
                            i
                            for i in self.selectedItems()
                            if i.data(0, Qt.ItemDataRole.UserRole)
                            and i.data(0, Qt.ItemDataRole.UserRole).name != ".."
                        ]
                    )
                    self.parent_panel.parent_window.status_bar.showMessage(
                        f"Выбрано элементов: {selected_count}", 2000
                    )
                    logger.debug(
                        f"Обновлен счетчик выбранных элементов: {selected_count}"
                    )

                # Также вызываем обработчик родительской панели для установки фокуса
                if hasattr(self, "parent_panel") and self.parent_panel:
                    self.parent_panel.on_mouse_press(self, event)

                # Сбрасываем позицию drag, чтобы предотвратить drag при Ctrl+Click
                self.drag_start_position = None
                logger.debug("Ctrl+Click обработан, drag отключен")
                return  # Не вызываем оригинальный обработчик

            # Обрабатываем выбор диапазона с Shift+Click
            elif item and event.modifiers() & Qt.KeyboardModifier.ShiftModifier:
                # Shift+Click - выбираем диапазон от последнего выбранного элемента
                current_item = self.currentItem()
                if current_item:
                    current_index = self.indexOfTopLevelItem(current_item)
                    clicked_index = self.indexOfTopLevelItem(item)

                    if current_index >= 0 and clicked_index >= 0:
                        # Очищаем выбор
                        self.clearSelection()

                        # Выбираем диапазон
                        start_index = min(current_index, clicked_index)
                        end_index = max(current_index, clicked_index)

                        for i in range(start_index, end_index + 1):
                            range_item = self.topLevelItem(i)
                            if range_item:
                                range_item.setSelected(True)

                        # Устанавливаем последний кликнутый элемент как текущий
                        self.setCurrentItem(item)

                # Принудительно обновляем отображение
                self.update()

                # Показываем количество выбранных элементов в статус-баре
                if (
                    hasattr(self, "parent_panel")
                    and self.parent_panel
                    and self.parent_panel.parent_window
                ):
                    selected_count = len(
                        [
                            i
                            for i in self.selectedItems()
                            if i.data(0, Qt.ItemDataRole.UserRole)
                            and i.data(0, Qt.ItemDataRole.UserRole).name != ".."
                        ]
                    )
                    self.parent_panel.parent_window.status_bar.showMessage(
                        f"Выбрано элементов в диапазоне: {selected_count}", 2000
                    )

                # Также вызываем обработчик родительской панели для установки фокуса
                if hasattr(self, "parent_panel") and self.parent_panel:
                    self.parent_panel.on_mouse_press(self, event)

                # Сбрасываем позицию drag для Shift+Click
                self.drag_start_position = None
                return  # Не вызываем оригинальный обработчик

        # Вызываем оригинальный обработчик
        super().mousePressEvent(event)

        # Также вызываем обработчик родительской панели для установки фокуса
        if hasattr(self, "parent_panel") and self.parent_panel:
            self.parent_panel.on_mouse_press(self, event)

    def mouseMoveEvent(self, event):
        """Обработка движения мыши для запуска drag операции"""
        if not (event.buttons() & Qt.MouseButton.LeftButton):
            return

        # Если позиция drag не установлена (например, после Ctrl+Click), не запускаем drag
        if not self.drag_start_position:
            return

        # Проверяем, достаточно ли переместилась мышь для начала drag
        distance = (
            event.position().toPoint() - self.drag_start_position
        ).manhattanLength()
        if distance < QApplication.startDragDistance():
            return

        # Получаем выбранные элементы
        selected_items = self.selectedItems()
        if not selected_items:
            return

        # Фильтруем элементы (исключаем "..")
        valid_items = []
        for item in selected_items:
            path = item.data(0, Qt.ItemDataRole.UserRole)
            if path and hasattr(path, "name") and path.name != "..":
                valid_items.append(item)

        if not valid_items:
            return

        # Начинаем drag операцию
        self.start_drag(valid_items)

    def start_drag(self, items):
        """Начать drag операцию"""
        try:
            logger.info(f"Начинаем drag операцию с {len(items)} элементами")

            # Создаем MIME данные
            mime_data = QMimeData()

            # Создаем список URLs для файлов
            urls = []
            file_paths = []

            for item in items:
                path = item.data(0, Qt.ItemDataRole.UserRole)
                if path:
                    file_url = QUrl.fromLocalFile(str(path))
                    urls.append(file_url)
                    file_paths.append(str(path))
                    logger.debug(f"Добавлен файл для drag: {path}")

            if not urls:
                logger.warning("Нет URL для drag операции")
                return

            # Устанавливаем URLs в MIME данные
            mime_data.setUrls(urls)

            # Также добавляем текстовое представление (пути к файлам)
            mime_data.setText("\n".join(file_paths))

            # Создаем drag объект
            drag = QDrag(self)
            drag.setMimeData(mime_data)

            # Создаем иконку для drag операции
            pixmap = self.create_drag_pixmap(items)
            drag.setPixmap(pixmap)
            drag.setHotSpot(pixmap.rect().center())

            # Запускаем drag операцию
            # Поддерживаем Copy и Move действия
            supported_actions = Qt.DropAction.CopyAction | Qt.DropAction.MoveAction

            # Выполняем drag операцию
            result = drag.exec(supported_actions, Qt.DropAction.CopyAction)

            logger.info(f"Drag операция завершена с результатом: {result}")

        except Exception as e:
            logger.error(f"Ошибка при drag операции: {e}", exc_info=True)

    def create_drag_pixmap(self, items):
        """Создать pixmap для отображения во время drag операции"""
        try:
            # Размеры pixmap
            width = 200
            height = min(len(items) * 20 + 10, 100)  # Ограничиваем высоту

            # Создаем pixmap
            pixmap = QPixmap(width, height)
            pixmap.fill(Qt.GlobalColor.transparent)

            painter = QPainter(pixmap)
            painter.setRenderHint(QPainter.RenderHint.Antialiasing)

            # Настраиваем стиль
            painter.setPen(QPen(Qt.GlobalColor.black, 1))
            painter.setBrush(QBrush(QColor(255, 255, 255, 200)))

            # Рисуем фон
            painter.drawRoundedRect(0, 0, width, height, 5, 5)

            # Рисуем информацию о файлах
            font = painter.font()
            font.setPixelSize(12)
            painter.setFont(font)
            painter.setPen(Qt.GlobalColor.black)

            y_offset = 15
            max_display = min(len(items), 4)  # Показываем максимум 4 файла

            for i in range(max_display):
                item = items[i]
                path = item.data(0, Qt.ItemDataRole.UserRole)
                if path:
                    file_name = path.name
                    if len(file_name) > 25:
                        file_name = file_name[:22] + "..."

                    # Определяем иконку
                    if path.is_dir():
                        icon_text = "📁"
                    else:
                        icon_text = "📄"

                    text = f"{icon_text} {file_name}"
                    painter.drawText(5, y_offset, text)
                    y_offset += 18

            # Если файлов больше 4, показываем "..."
            if len(items) > max_display:
                painter.drawText(5, y_offset, f"... и еще {len(items) - max_display}")

            painter.end()
            return pixmap

        except Exception as e:
            logger.error(f"Ошибка создания drag pixmap: {e}")
            # Возвращаем простой pixmap в случае ошибки
            pixmap = QPixmap(100, 30)
            pixmap.fill(QColor(200, 200, 200, 180))
            painter = QPainter(pixmap)
            painter.drawText(5, 20, f"{len(items)} файл(ов)")
            painter.end()
            return pixmap

    def dragEnterEvent(self, event):
        """Обработка входа drag объекта в область виджета"""
        logger.debug("dragEnterEvent вызван")

        if event.mimeData().hasUrls():
            # Проверяем, есть ли файлы в drag данных
            urls = event.mimeData().urls()
            valid_files = []

            for url in urls:
                if url.isLocalFile():
                    file_path = Path(url.toLocalFile())
                    if file_path.exists():
                        valid_files.append(file_path.name)

            if valid_files:
                event.acceptProposedAction()

                # Показываем информацию о файлах в статус-баре
                if self.parent_panel and hasattr(self.parent_panel, "parent_window"):
                    main_window = self.parent_panel.parent_window
                    if len(valid_files) == 1:
                        info_text = f"📥 Готов принять файл: {valid_files[0]}"
                    else:
                        info_text = f"📥 Готов принять {len(valid_files)} файлов"
                    main_window.status_bar.showMessage(info_text)

                logger.debug("Drag данные приняты (URLs с файлами)")
            else:
                event.ignore()
                logger.debug("Drag данные отклонены (нет валидных файлов)")
        elif event.mimeData().hasText():
            # Проверяем текстовые данные (возможно, пути к файлам)
            text = event.mimeData().text()
            if text and Path(text.strip().split("\n")[0]).exists():
                event.acceptProposedAction()

                # Показываем информацию в статус-баре
                if self.parent_panel and hasattr(self.parent_panel, "parent_window"):
                    main_window = self.parent_panel.parent_window
                    main_window.status_bar.showMessage(
                        "📥 Готов принять файлы из текста"
                    )

                logger.debug("Drag данные приняты (текст с путями)")
            else:
                event.ignore()
                logger.debug("Drag данные отклонены (невалидный текст)")
        else:
            event.ignore()
            logger.debug("Drag данные отклонены (неподдерживаемый формат)")

    def dragMoveEvent(self, event):
        """Обработка движения drag объекта над виджетом"""
        if event.mimeData().hasUrls() or event.mimeData().hasText():
            event.acceptProposedAction()
        else:
            event.ignore()

    def dragLeaveEvent(self, event):
        """Обработка выхода drag объекта из области виджета"""
        # Очищаем статус-бар
        if self.parent_panel and hasattr(self.parent_panel, "parent_window"):
            main_window = self.parent_panel.parent_window
            main_window.status_bar.clearMessage()

        super().dragLeaveEvent(event)

    def dropEvent(self, event):
        """Обработка drop события"""
        logger.info("dropEvent вызван")

        try:
            if not self.parent_panel:
                logger.error("parent_panel не установлен")
                event.ignore()
                return

            # Получаем целевую папку (папка текущей панели)
            target_path = self.parent_panel.current_path
            logger.info(f"Целевая папка для drop: {target_path}")

            # Получаем список файлов из drag данных
            source_files = []

            if event.mimeData().hasUrls():
                # Обрабатываем URL данные
                urls = event.mimeData().urls()
                logger.debug(f"Получено {len(urls)} URLs")

                for url in urls:
                    if url.isLocalFile():
                        file_path = Path(url.toLocalFile())
                        if file_path.exists():
                            source_files.append(file_path)
                            logger.debug(f"Добавлен файл из URL: {file_path}")
                        else:
                            logger.warning(f"Файл не существует: {file_path}")
                    else:
                        logger.warning(f"Не локальный URL: {url}")

            elif event.mimeData().hasText():
                # Обрабатываем текстовые данные
                text = event.mimeData().text()
                logger.debug(f"Получен текст: {text[:100]}...")

                # Разбиваем текст на строки (могут быть пути к файлам)
                lines = text.strip().split("\n")
                for line in lines:
                    line = line.strip()
                    if line:
                        try:
                            file_path = Path(line)
                            if file_path.exists():
                                source_files.append(file_path)
                                logger.debug(f"Добавлен файл из текста: {file_path}")
                            else:
                                logger.warning(
                                    f"Файл не существует (текст): {file_path}"
                                )
                        except Exception as e:
                            logger.warning(
                                f"Не удалось обработать строку '{line}': {e}"
                            )

            if not source_files:
                logger.warning("Нет валидных файлов для drop")
                event.ignore()
                QMessageBox.information(
                    None, "Информация", "Нет валидных файлов для вставки"
                )
                return

            logger.info(f"Найдено {len(source_files)} файлов для drop")

            # Определяем тип операции на основе модификаторов клавиатуры
            # Получаем модификаторы из самого события drop
            modifiers = (
                event.modifiers()
                if hasattr(event, "modifiers")
                else QApplication.keyboardModifiers()
            )

            if modifiers & Qt.KeyboardModifier.ControlModifier:
                # Ctrl = принудительное копирование
                operation = "copy"
                operation_text = "копировать"
                logger.debug("Операция: копирование (Ctrl)")
            elif modifiers & Qt.KeyboardModifier.ShiftModifier:
                # Shift = принудительное перемещение
                operation = "move"
                operation_text = "переместить"
                logger.debug("Операция: перемещение (Shift)")
            else:
                # По умолчанию - копирование
                operation = "copy"
                operation_text = "копировать"
                logger.debug("Операция: копирование (по умолчанию)")

            # Подтверждение операции
            if len(source_files) == 1:
                file_name = source_files[0].name
                message = f"{operation_text.capitalize()} файл '{file_name}' в папку:\n{target_path}?"
            else:
                message = f"{operation_text.capitalize()} {len(source_files)} файлов в папку:\n{target_path}?"

            reply = QMessageBox.question(
                None,
                "Подтверждение операции",
                message,
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            )

            if reply != QMessageBox.StandardButton.Yes:
                logger.info("Операция отменена пользователем")
                event.ignore()
                return

            # Выполняем операцию
            logger.info(f"Выполняем {operation} для {len(source_files)} файлов")

            if len(source_files) == 1:
                # Для одного файла
                source_path = source_files[0]
                target_file_path = target_path / source_path.name

                # Проверяем, не копируем ли файл сам в себя
                try:
                    if source_path.resolve() == target_file_path.resolve():
                        logger.warning("Попытка скопировать файл сам в себя")
                        QMessageBox.warning(
                            None,
                            "Предупреждение",
                            f"Нельзя скопировать файл сам в себя",
                        )
                        event.ignore()
                        return
                except OSError:
                    # Если resolve() не работает, продолжаем
                    pass

                # Проверяем, существует ли файл назначения
                if target_file_path.exists():
                    reply = QMessageBox.question(
                        None,
                        "Файл существует",
                        f"Файл '{source_path.name}' уже существует в папке назначения.\n\nЗаменить?",
                        QMessageBox.StandardButton.Yes
                        | QMessageBox.StandardButton.No
                        | QMessageBox.StandardButton.Cancel,
                    )

                    if reply == QMessageBox.StandardButton.Cancel:
                        logger.info("Операция отменена пользователем")
                        event.ignore()
                        return
                    elif reply == QMessageBox.StandardButton.No:
                        # Предлагаем переименовать
                        new_name, ok = QInputDialog.getText(
                            None,
                            "Переименовать файл",
                            f"Введите новое имя для файла '{source_path.name}':",
                            text=source_path.name,
                        )
                        if ok and new_name and new_name != source_path.name:
                            target_file_path = target_path / new_name
                            # Проверяем, не существует ли файл с новым именем
                            if target_file_path.exists():
                                QMessageBox.warning(
                                    None,
                                    "Ошибка",
                                    f"Файл с именем '{new_name}' тоже существует!",
                                )
                                event.ignore()
                                return
                        else:
                            logger.info("Переименование отменено")
                            event.ignore()
                            return

                # Выполняем операцию с одним файлом
                self.simple_file_operation(operation, source_path, target_file_path)

            else:
                # Для множественных файлов - обрабатываем конфликты
                files_to_process = []
                conflicts = []

                # Сначала проверяем все файлы на конфликты
                for source_path in source_files:
                    target_file_path = target_path / source_path.name

                    # Проверяем, не копируем ли файл сам в себя
                    try:
                        if source_path.resolve() == target_file_path.resolve():
                            logger.warning(
                                f"Пропускаем файл {source_path.name} (копирование сам в себя)"
                            )
                            continue
                    except OSError:
                        pass

                    if target_file_path.exists():
                        conflicts.append((source_path, target_file_path))
                    else:
                        files_to_process.append((source_path, target_file_path))

                # Если есть конфликты, спрашиваем пользователя
                if conflicts:
                    conflict_message = f"Следующие файлы уже существуют:\n\n"
                    for source, target in conflicts[:5]:  # Показываем первые 5
                        conflict_message += f"• {source.name}\n"

                    if len(conflicts) > 5:
                        conflict_message += f"... и еще {len(conflicts) - 5} файлов\n"

                    conflict_message += f"\nЧто делать с существующими файлами?"

                    # Создаем диалог с несколькими вариантами
                    msg_box = QMessageBox()
                    msg_box.setWindowTitle("Конфликт файлов")
                    msg_box.setText(conflict_message)

                    replace_all_btn = msg_box.addButton(
                        "Заменить все", QMessageBox.ButtonRole.YesRole
                    )
                    skip_all_btn = msg_box.addButton(
                        "Пропустить все", QMessageBox.ButtonRole.NoRole
                    )
                    cancel_btn = msg_box.addButton(
                        "Отмена", QMessageBox.ButtonRole.RejectRole
                    )
                    msg_box.setDefaultButton(skip_all_btn)

                    result = msg_box.exec()
                    clicked_button = msg_box.clickedButton()

                    if clicked_button == cancel_btn:
                        logger.info("Операция отменена пользователем")
                        event.ignore()
                        return
                    elif clicked_button == replace_all_btn:
                        # Добавляем конфликтные файлы для замены
                        files_to_process.extend(conflicts)
                    # Если skip_all - просто пропускаем конфликтные файлы

                # Выполняем операции с файлами
                if files_to_process:
                    successful_operations = 0
                    errors = []

                    for source_path, target_file_path in files_to_process:
                        try:
                            self.simple_file_operation(
                                operation, source_path, target_file_path
                            )
                            successful_operations += 1
                        except Exception as e:
                            error_msg = f"{source_path.name}: {str(e)}"
                            errors.append(error_msg)
                            logger.error(f"Ошибка операции с файлом {source_path}: {e}")

                    # Показываем результат
                    if successful_operations > 0:
                        logger.info(
                            f"Успешно обработано {successful_operations} файлов"
                        )

                    if errors:
                        error_message = f"Обработано {successful_operations} из {len(files_to_process)} файлов.\n\nОшибки:\n"
                        error_message += "\n".join(errors[:5])
                        if len(errors) > 5:
                            error_message += f"\n...и еще {len(errors) - 5} ошибок"
                        QMessageBox.warning(None, "Предупреждения", error_message)
                else:
                    QMessageBox.information(
                        None, "Информация", "Нет файлов для обработки"
                    )

            event.acceptProposedAction()
            logger.info("Drop операция принята")

            # Показываем успешное завершение в статус-баре
            if self.parent_panel and hasattr(self.parent_panel, "parent_window"):
                main_window = self.parent_panel.parent_window
                if len(source_files) == 1:
                    main_window.status_bar.showMessage(
                        f"✅ Файл добавлен: {source_files[0].name}", 3000
                    )
                else:
                    main_window.status_bar.showMessage(
                        f"✅ Добавлено {len(source_files)} файлов", 3000
                    )

        except Exception as e:
            logger.error(f"Ошибка при drop операции: {e}", exc_info=True)
            event.ignore()
            QMessageBox.critical(None, "Ошибка", f"Ошибка при вставке файлов: {e}")

    def simple_file_operation(self, operation, source_path, target_path):
        """Простая операция с файлом (fallback)"""
        try:
            if operation == "copy":
                if source_path.is_dir():
                    # Для папок - если целевая папка существует, удаляем её
                    if target_path.exists():
                        shutil.rmtree(str(target_path))
                    shutil.copytree(str(source_path), str(target_path))
                else:
                    shutil.copy2(str(source_path), str(target_path))
                logger.info(f"Файл скопирован: {source_path} -> {target_path}")
            elif operation == "move":
                # Для перемещения - если целевой файл существует, удаляем его
                if target_path.exists():
                    if target_path.is_dir():
                        shutil.rmtree(str(target_path))
                    else:
                        target_path.unlink()
                shutil.move(str(source_path), str(target_path))
                logger.info(f"Файл перемещен: {source_path} -> {target_path}")

            # Обновляем панель
            if self.parent_panel:
                self.parent_panel.refresh()

        except Exception as e:
            logger.error(f"Ошибка простой операции с файлом: {e}")
            # Не показываем QMessageBox здесь, так как это может быть вызвано из цикла
            # Вместо этого поднимаем исключение для обработки на верхнем уровне
            raise Exception(f"Не удалось {operation} файл {source_path.name}: {str(e)}")


class FileSearchThread(QThread):
    """Поток для поиска файлов"""

    progress = pyqtSignal(int)
    progress_text = pyqtSignal(str)
    result_found = pyqtSignal(object)  # Передаем найденный файл
    finished = pyqtSignal(bool, str, int)  # success, message, total_found

    def __init__(self, search_params):
        super().__init__()
        self.search_params = search_params
        self.total_found = 0
        self.processed_dirs = 0
        self.total_dirs = 0

    def run(self):
        try:
            logger.info(f"Запуск поиска: {self.search_params}")

            search_name = self.search_params.get("name", "").lower()
            search_extension = self.search_params.get("extension", "").lower()
            search_content = self.search_params.get("content", "").lower()
            search_paths = self.search_params.get("paths", [])
            search_in_content = self.search_params.get("search_in_content", False)
            case_sensitive = self.search_params.get("case_sensitive", False)

            self.progress_text.emit("Подготовка к поиску...")

            # Подсчитываем общее количество папок для прогресса
            self.total_dirs = self.count_directories(search_paths)

            self.progress_text.emit(f"Поиск в {self.total_dirs} папках...")

            for search_path in search_paths:
                if self.isInterruptionRequested():
                    break

                try:
                    search_root = Path(search_path)
                    if not search_root.exists():
                        continue

                    self.search_in_directory(
                        search_root,
                        search_name,
                        search_extension,
                        search_content,
                        search_in_content,
                        case_sensitive,
                    )

                except Exception as e:
                    logger.error(f"Ошибка поиска в {search_path}: {e}")
                    continue

            self.progress.emit(100)
            self.finished.emit(
                True,
                f"Поиск завершен. Найдено файлов: {self.total_found}",
                self.total_found,
            )

        except Exception as e:
            logger.error(f"Ошибка поиска: {e}", exc_info=True)
            self.finished.emit(False, f"Ошибка поиска: {e}", self.total_found)

    def count_directories(self, search_paths):
        """Подсчет количества директорий для прогресса"""
        total = 0
        for search_path in search_paths:
            try:
                search_root = Path(search_path)
                if search_root.exists():
                    if search_root.is_dir():
                        for _ in search_root.rglob("*"):
                            if self.isInterruptionRequested():
                                return total
                            total += 1
                            if total > 10000:  # Ограничиваем для производительности
                                return total
                    else:
                        total += 1
            except (PermissionError, OSError):
                continue
        return max(total, 1)

    def search_in_directory(
        self,
        directory,
        search_name,
        search_extension,
        search_content,
        search_in_content,
        case_sensitive,
    ):
        """Поиск в конкретной директории"""
        try:
            if directory.is_file():
                # Если это файл, проверяем его
                self.check_file(
                    directory,
                    search_name,
                    search_extension,
                    search_content,
                    search_in_content,
                    case_sensitive,
                )
                return

            # Поиск во всех файлах и поддиректориях
            for item in directory.rglob("*"):
                if self.isInterruptionRequested():
                    return

                try:
                    if item.is_file():
                        self.check_file(
                            item,
                            search_name,
                            search_extension,
                            search_content,
                            search_in_content,
                            case_sensitive,
                        )

                    # Обновляем прогресс
                    self.processed_dirs += 1
                    if self.total_dirs > 0:
                        progress = min(
                            int((self.processed_dirs * 100) / self.total_dirs), 99
                        )
                        self.progress.emit(progress)

                    if (
                        self.processed_dirs % 50 == 0
                    ):  # Обновляем текст каждые 50 файлов
                        self.progress_text.emit(
                            f"Обработано: {self.processed_dirs}, найдено: {self.total_found}"
                        )

                except (PermissionError, OSError):
                    continue

        except (PermissionError, OSError):
            logger.warning(f"Нет доступа к папке: {directory}")

    def check_file(
        self,
        file_path,
        search_name,
        search_extension,
        search_content,
        search_in_content,
        case_sensitive,
    ):
        """Проверка файла на соответствие критериям поиска"""
        try:
            file_name = file_path.name if case_sensitive else file_path.name.lower()
            file_ext = file_path.suffix if case_sensitive else file_path.suffix.lower()

            # Проверка имени файла
            name_match = True
            if search_name:
                if "*" in search_name or "?" in search_name:
                    # Поддержка wildcards
                    import fnmatch

                    pattern = search_name if case_sensitive else search_name.lower()
                    name_match = fnmatch.fnmatch(file_name, pattern)
                else:
                    name_match = search_name in file_name

            # Проверка расширения
            ext_match = True
            if search_extension:
                if search_extension.startswith("."):
                    ext_match = file_ext == search_extension
                else:
                    ext_match = file_ext.endswith("." + search_extension)

            # Проверка содержимого
            content_match = True
            if search_content and search_in_content:
                content_match = self.search_in_file_content(
                    file_path, search_content, case_sensitive
                )

            # Если все критерии совпадают
            if name_match and ext_match and content_match:
                self.total_found += 1

                # Создаем объект результата
                result = {
                    "path": file_path,
                    "name": file_path.name,
                    "size": self.get_file_size(file_path),
                    "modified": self.get_modification_time(file_path),
                    "directory": str(file_path.parent),
                }

                self.result_found.emit(result)

        except Exception as e:
            logger.debug(f"Ошибка проверки файла {file_path}: {e}")

    def search_in_file_content(self, file_path, search_text, case_sensitive):
        """Поиск в содержимом файла"""
        try:
            # Ограичиваем поиск только текстовыми файлами
            text_extensions = {
                ".txt",
                ".py",
                ".js",
                ".html",
                ".css",
                ".json",
                ".xml",
                ".md",
                ".log",
                ".ini",
                ".cfg",
                ".yml",
                ".yaml",
                ".sql",
                ".cs",
                ".java",
                ".cpp",
                ".c",
                ".h",
                ".php",
                ".rb",
            }

            if file_path.suffix.lower() not in text_extensions:
                return True  # Пропускаем нетекстовые файлы

            # Ограничиваем размер файла для поиска (максимум 10 МБ)
            if file_path.stat().st_size > 10 * 1024 * 1024:
                return True

            # Читаем содержимое файла
            encodings = ["utf-8", "cp1251", "latin1"]
            content = None

            for encoding in encodings:
                try:
                    with open(file_path, "r", encoding=encoding) as f:
                        content = f.read()
                    break
                except UnicodeDecodeError:
                    continue
                except Exception:
                    return True  # Если не можем прочитать, пропускаем

            if content is None:
                return True

            # Поиск в содержимом
            if not case_sensitive:
                content = content.lower()

            return search_text in content

        except Exception as e:
            logger.debug(f"Ошибка поиска в содержимом {file_path}: {e}")
            return True

    def get_file_size(self, file_path):
        """Получить размер файла"""
        try:
            return file_path.stat().st_size
        except (OSError, PermissionError):
            return 0

    def get_modification_time(self, file_path):
        """Получить время модификации файла"""
        try:
            return file_path.stat().st_mtime
        except (OSError, PermissionError):
            return 0


class SearchResultsDialog(QDialog):
    """Диалог для отображения результатов поиска"""

    def __init__(self, search_params, parent=None):
        super().__init__(parent)
        self.search_params = search_params
        self.parent_window = parent
        self.search_thread = None
        self.results = []
        self.setup_ui()
        self.start_search()

    def setup_ui(self):
        self.setWindowTitle("Результаты поиска")
        self.setGeometry(150, 150, 900, 600)
        self.setModal(True)

        layout = QVBoxLayout()

        # Информация о поиске
        info_layout = QHBoxLayout()

        self.search_info_label = QLabel("Поиск...")
        self.search_info_label.setStyleSheet(
            "QLabel { font-weight: bold; color: #2E8B57; }"
        )
        info_layout.addWidget(self.search_info_label)

        info_layout.addStretch()

        # Кнопка остановки поиска
        self.stop_button = QPushButton("Остановить")
        self.stop_button.clicked.connect(self.stop_search)
        self.stop_button.setStyleSheet(
            "QPushButton { background-color: #E74C3C; color: white; }"
        )
        info_layout.addWidget(self.stop_button)

        layout.addLayout(info_layout)

        # Прогресс
        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, 100)
        layout.addWidget(self.progress_bar)

        self.progress_label = QLabel("Подготовка...")
        self.progress_label.setStyleSheet("QLabel { color: #666; font-size: 10px; }")
        layout.addWidget(self.progress_label)

        # Результаты
        self.results_tree = QTreeWidget()
        self.results_tree.setHeaderLabels(
            ["Имя файла", "Размер", "Дата изменения", "Папка"]
        )
        self.results_tree.setAlternatingRowColors(True)
        self.results_tree.setSortingEnabled(True)
        self.results_tree.itemDoubleClicked.connect(self.open_file)

        # Настройка колонок
        header = self.results_tree.header()
        header.setStretchLastSection(False)
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.Interactive)
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(3, QHeaderView.ResizeMode.Stretch)

        layout.addWidget(self.results_tree)

        # Статистика
        self.stats_label = QLabel("Найдено файлов: 0")
        self.stats_label.setStyleSheet("QLabel { color: #666; font-size: 10px; }")
        layout.addWidget(self.stats_label)

        # Кнопки
        button_layout = QHBoxLayout()

        self.open_button = QPushButton("Открыть папку")
        self.open_button.clicked.connect(self.open_folder)
        self.open_button.setEnabled(False)
        button_layout.addWidget(self.open_button)

        self.view_button = QPushButton("Просмотр")
        self.view_button.clicked.connect(self.view_file)
        self.view_button.setEnabled(False)
        button_layout.addWidget(self.view_button)

        self.copy_path_button = QPushButton("Копировать путь")
        self.copy_path_button.clicked.connect(self.copy_file_path)
        self.copy_path_button.setEnabled(False)
        button_layout.addWidget(self.copy_path_button)

        button_layout.addStretch()

        self.close_button = QPushButton("Закрыть")
        self.close_button.clicked.connect(self.close)
        button_layout.addWidget(self.close_button)

        layout.addLayout(button_layout)
        self.setLayout(layout)

        # Обработка выбора элементов
        self.results_tree.itemSelectionChanged.connect(self.on_selection_changed)

    def start_search(self):
        """Запустить поиск"""
        self.search_thread = FileSearchThread(self.search_params)
        self.search_thread.progress.connect(self.progress_bar.setValue)
        self.search_thread.progress_text.connect(self.progress_label.setText)
        self.search_thread.result_found.connect(self.add_result)
        self.search_thread.finished.connect(self.search_finished)

        # Обновляем информацию о поиске
        search_info = []
        if self.search_params.get("name"):
            search_info.append(f"имя: '{self.search_params['name']}'")
        if self.search_params.get("extension"):
            search_info.append(f"расширение: '{self.search_params['extension']}'")
        if self.search_params.get("content") and self.search_params.get(
            "search_in_content"
        ):
            search_info.append(f"содержимое: '{self.search_params['content']}'")

        self.search_info_label.setText(f"🔍 Поиск: {', '.join(search_info)}")

        self.search_thread.start()

    def add_result(self, result):
        """Добавить результат в список"""
        self.results.append(result)

        # Форматируем данные для отображения
        file_path = result["path"]
        name = result["name"]
        size = self.format_size(result["size"])

        # Форматируем дату
        try:
            from datetime import datetime

            mod_time = datetime.fromtimestamp(result["modified"])
            date_str = mod_time.strftime("%d.%m.%Y %H:%M")
        except:
            date_str = "Неизвестно"

        directory = result["directory"]

        # Определяем иконку
        if file_path.is_dir():
            icon = "📁"
        else:
            # Используем расширение для определения иконки
            ext = file_path.suffix.lower()
            icon_map = {
                ".txt": "📄",
                ".py": "🐍",
                ".js": "📜",
                ".html": "🌐",
                ".css": "🎨",
                ".json": "🗂️",
                ".xml": "📋",
                ".md": "📝",
                ".jpg": "🖼️",
                ".jpeg": "🖼️",
                ".png": "🖼️",
                ".gif": "🎞️",
                ".mp3": "🎵",
                ".wav": "🎵",
                ".mp4": "🎬",
                ".avi": "🎬",
                ".pdf": "📕",
                ".doc": "📘",
                ".docx": "📘",
                ".xls": "📊",
                ".zip": "📦",
                ".rar": "📦",
                ".7z": "📦",
            }
            icon = icon_map.get(ext, "📄")

        # Создаем элемент дерева
        item = QTreeWidgetItem([f"{icon} {name}", size, date_str, directory])
        item.setData(0, Qt.ItemDataRole.UserRole, file_path)

        self.results_tree.addTopLevelItem(item)

        # Обновляем статистику
        self.stats_label.setText(f"Найдено файлов: {len(self.results)}")

    def search_finished(self, success, message, total_found):
        """Обработка завершения поиска"""
        self.progress_bar.setVisible(False)
        self.progress_label.setText(message)
        self.stop_button.setEnabled(False)

        if success:
            self.search_info_label.setText(f"✅ Поиск завершен успешно")
            self.search_info_label.setStyleSheet(
                "QLabel { font-weight: bold; color: #27AE60; }"
            )
        else:
            self.search_info_label.setText(f"❌ Поиск завершен с ошибками")
            self.search_info_label.setStyleSheet(
                "QLabel { font-weight: bold; color: #E74C3C; }"
            )

        # Автоматически расширяем колонки
        for i in range(self.results_tree.columnCount()):
            self.results_tree.resizeColumnToContents(i)

        self.search_thread = None

    def stop_search(self):
        """Остановить поиск"""
        if self.search_thread and self.search_thread.isRunning():
            self.search_thread.requestInterruption()
            self.stop_button.setEnabled(False)
            self.progress_label.setText("Остановка поиска...")

    def format_size(self, size):
        """Форматировать размер файла"""
        for unit in ["Б", "КБ", "МБ", "ГБ"]:
            if size < 1024:
                return f"{size:.1f} {unit}"
            size /= 1024
        return f"{size:.1f} ТБ"

    def on_selection_changed(self):
        """Обработка изменения выбора"""
        has_selection = bool(self.results_tree.selectedItems())
        self.open_button.setEnabled(has_selection)
        self.view_button.setEnabled(has_selection)
        self.copy_path_button.setEnabled(has_selection)

    def get_selected_file_path(self):
        """Получить путь выбранного файла"""
        selected_items = self.results_tree.selectedItems()
        if selected_items:
            return selected_items[0].data(0, Qt.ItemDataRole.UserRole)
        return None

    def open_folder(self):
        """Открыть папку с файлом"""
        file_path = self.get_selected_file_path()
        if file_path:
            try:
                if self.parent_window:
                    # Открываем папку в активной панели
                    active_panel, _ = self.parent_window.get_active_panel()
                    folder_path = file_path.parent if file_path.is_file() else file_path

                    # Создаем новую вкладку с этой папкой
                    active_panel.add_new_tab(folder_path)

                    self.accept()  # Закрываем диалог
                else:
                    # Если нет родительского окна, открываем в проводнике
                    if sys.platform == "win32":
                        subprocess.run(["explorer", "/select,", str(file_path)])
                    elif sys.platform == "darwin":
                        subprocess.run(["open", "-R", str(file_path)])
                    else:
                        subprocess.run(["xdg-open", str(file_path.parent)])
            except Exception as e:
                QMessageBox.critical(self, "Ошибка", f"Не удалось открыть папку: {e}")

    def view_file(self):
        """Просмотр файла"""
        file_path = self.get_selected_file_path()
        if file_path and file_path.is_file():
            try:
                viewer = FileViewer(file_path, self.parent_window)
                viewer.exec()
            except Exception as e:
                QMessageBox.critical(
                    self, "Ошибка", f"Не удалось просмотреть файл: {e}"
                )

    def open_file(self, item, column):
        """Открытие файла двойным кликом"""
        file_path = item.data(0, Qt.ItemDataRole.UserRole)
        if file_path:
            if file_path.is_file():
                self.view_file()
            else:
                self.open_folder()

    def copy_file_path(self):
        """Копировать путь к файлу в буфер обмена"""
        file_path = self.get_selected_file_path()
        if file_path:
            try:
                clipboard = QApplication.clipboard()
                clipboard.setText(str(file_path))
                self.progress_label.setText(f"Путь скопирован: {file_path}")
            except Exception as e:
                QMessageBox.critical(
                    self, "Ошибка", f"Не удалось скопировать путь: {e}"
                )

    def closeEvent(self, event):
        """Обработка закрытия диалога"""
        if self.search_thread and self.search_thread.isRunning():
            self.search_thread.requestInterruption()
            self.search_thread.wait(1000)
        event.accept()


class SearchDialog(QDialog):
    """Диалог настройки поиска файлов"""

    def __init__(self, current_path, parent=None):
        super().__init__(parent)
        self.current_path = current_path
        self.parent_window = parent
        self.setup_ui()

    def setup_ui(self):
        self.setWindowTitle("Поиск файлов")
        self.setGeometry(200, 200, 500, 400)
        self.setModal(True)

        layout = QVBoxLayout()

        # Критерии поиска
        criteria_group = QGroupBox("Критерии поиска")
        criteria_layout = QFormLayout()

        # Имя файла
        self.name_edit = QInputDialog()
        self.name_line = QLineEdit()
        self.name_line.setPlaceholderText(
            "Введите имя файла или маску (например: *.txt, test*)"
        )
        criteria_layout.addRow("Имя файла:", self.name_line)

        # Расширение
        self.extension_line = QLineEdit()
        self.extension_line.setPlaceholderText("Введите расширение (например: txt, py)")
        criteria_layout.addRow("Расширение:", self.extension_line)

        # Содержимое
        self.content_line = QLineEdit()
        self.content_line.setPlaceholderText("Поиск текста в содержимом файлов")
        criteria_layout.addRow("Содержимое:", self.content_line)

        # Поиск в содержимом
        self.search_content_check = QCheckBox("Искать в содержимом файлов")
        self.search_content_check.setToolTip(
            "Поиск только в текстовых файлах размером до 10 МБ"
        )
        criteria_layout.addRow("", self.search_content_check)

        # Регистр
        self.case_sensitive_check = QCheckBox("Учитывать регистр")
        criteria_layout.addRow("", self.case_sensitive_check)

        criteria_group.setLayout(criteria_layout)
        layout.addWidget(criteria_group)

        # Область поиска
        scope_group = QGroupBox("Область поиска")
        scope_layout = QVBoxLayout()

        # Радио кнопки для выбора области
        self.current_folder_radio = QRadioButton(f"Текущая папка: {self.current_path}")
        self.current_folder_radio.setChecked(True)
        scope_layout.addWidget(self.current_folder_radio)

        self.current_disk_radio = QRadioButton("Весь текущий диск")
        scope_layout.addWidget(self.current_disk_radio)

        self.all_disks_radio = QRadioButton("Все диски")
        scope_layout.addWidget(self.all_disks_radio)

        self.custom_path_radio = QRadioButton("Выбрать папку:")
        scope_layout.addWidget(self.custom_path_radio)

        # Поле для пользовательского пути
        path_layout = QHBoxLayout()
        self.custom_path_line = QLineEdit()
        self.custom_path_line.setEnabled(False)
        self.browse_button = QPushButton("Обзор")
        self.browse_button.setEnabled(False)
        self.browse_button.clicked.connect(self.browse_folder)
        path_layout.addWidget(self.custom_path_line)
        path_layout.addWidget(self.browse_button)
        scope_layout.addLayout(path_layout)

        # Связываем радио кнопку с полем пути
        self.custom_path_radio.toggled.connect(self.custom_path_line.setEnabled)
        self.custom_path_radio.toggled.connect(self.browse_button.setEnabled)

        scope_group.setLayout(scope_layout)
        layout.addWidget(scope_group)

        # Кнопки
        button_layout = QHBoxLayout()

        self.search_button = QPushButton("Начать поиск")
        self.search_button.clicked.connect(self.start_search)
        button_layout.addWidget(self.search_button)

        self.cancel_button = QPushButton("Отмена")
        self.cancel_button.clicked.connect(self.close)
        button_layout.addWidget(self.cancel_button)

        layout.addLayout(button_layout)
        self.setLayout(layout)

        # Фокус на поле имени файла
        self.name_line.setFocus()

    def browse_folder(self):
        """Выбор папки для поиска"""
        folder = QFileDialog.getExistingDirectory(
            self, "Выберите папку для поиска", str(self.current_path)
        )
        if folder:
            self.custom_path_line.setText(folder)

    def start_search(self):
        """Запустить поиск"""
        # Проверяем, что задан хотя бы один критерий
        name = self.name_line.text().strip()
        extension = self.extension_line.text().strip()
        content = self.content_line.text().strip()

        if not name and not extension and not content:
            QMessageBox.warning(
                self, "Предупреждение", "Укажите хотя бы один критерий поиска"
            )
            return

        # Определяем пути для поиска
        search_paths = []

        if self.current_folder_radio.isChecked():
            search_paths = [str(self.current_path)]

        elif self.current_disk_radio.isChecked():
            # Получаем корень диска
            if sys.platform == "win32":
                drive_root = str(self.current_path).split("\\")[0] + "\\"
            else:
                drive_root = "/"
            search_paths = [drive_root]

        elif self.all_disks_radio.isChecked():
            # Получаем все диски
            try:
                partitions = psutil.disk_partitions()
                for partition in partitions:
                    try:
                        # Проверяем доступность диска
                        psutil.disk_usage(partition.mountpoint)
                        search_paths.append(partition.mountpoint)
                    except (PermissionError, OSError):
                        continue
            except Exception:
                search_paths = ["C:\\"] if sys.platform == "win32" else ["/"]

        elif self.custom_path_radio.isChecked():
            custom_path = self.custom_path_line.text().strip()
            if not custom_path:
                QMessageBox.warning(self, "Предупреждение", "Укажите путь для поиска")
                return
            if not Path(custom_path).exists():
                QMessageBox.warning(
                    self, "Предупреждение", "Указанный путь не существует"
                )
                return
            search_paths = [custom_path]

        if not search_paths:
            QMessageBox.warning(
                self, "Предупреждение", "Не удалось определить пути для поиска"
            )
            return

        # Подготавливаем параметры поиска
        search_params = {
            "name": name,
            "extension": extension,
            "content": content,
            "paths": search_paths,
            "search_in_content": self.search_content_check.isChecked()
            and bool(content),
            "case_sensitive": self.case_sensitive_check.isChecked(),
        }

        # Показываем предупреждение для больших областей поиска
        if self.all_disks_radio.isChecked():
            reply = QMessageBox.question(
                self,
                "Подтверждение",
                "Поиск по всем дискам может занять много времени.\n\nПродолжить?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            )
            if reply != QMessageBox.StandardButton.Yes:
                return

        # Закрываем диалог настройки и открываем диалог результатов
        self.accept()

        # Запускаем поиск
        results_dialog = SearchResultsDialog(search_params, self.parent_window)
        results_dialog.exec()


class FileOperationThread(QThread):
    """Поток для выполнения операций с файлами в фоновом режиме"""

    progress = pyqtSignal(int)
    progress_text = pyqtSignal(str)
    finished = pyqtSignal(bool, str)

    def __init__(self, operation, source, destination):
        super().__init__()
        self.operation = operation
        self.source = source
        self.destination = destination
        self.total_files = 0
        self.processed_files = 0
        self.total_size = 0
        self.processed_size = 0

    def count_files_and_size(self, path):
        """Подсчет общего количества файлов и размера"""
        total_files = 0
        total_size = 0

        if os.path.isfile(path):
            try:
                total_size = os.path.getsize(path)
                total_files = 1
            except (OSError, IOError):
                pass
        elif os.path.isdir(path):
            try:
                for root, dirs, files in os.walk(path):
                    total_files += len(files)
                    for file in files:
                        try:
                            file_path = os.path.join(root, file)
                            total_size += os.path.getsize(file_path)
                        except (OSError, IOError):
                            pass
            except (OSError, IOError):
                pass

        return total_files, total_size

    def format_size(self, size):
        """Форматировать размер файла"""
        for unit in ["Б", "КБ", "МБ", "ГБ"]:
            if size < 1024:
                return f"{size:.1f} {unit}"
            size /= 1024
        return f"{size:.1f} ТБ"

    def copy_file_with_progress(self, src, dst):
        """Копирование файла с отслеживанием прогресса"""
        try:
            # Размер файла
            file_size = os.path.getsize(src)

            # Создаем директорию назначения если нужно
            os.makedirs(os.path.dirname(dst), exist_ok=True)

            # Копируем файл по частям с отслеживанием прогресса
            with open(src, "rb") as fsrc, open(dst, "wb") as fdst:
                copied = 0
                chunk_size = 64 * 1024  # 64KB chunks

                while True:
                    chunk = fsrc.read(chunk_size)
                    if not chunk:
                        break

                    fdst.write(chunk)
                    copied += len(chunk)
                    self.processed_size += len(chunk)

                    # Обновляем прогресс
                    if self.total_size > 0:
                        progress = int((self.processed_size * 100) / self.total_size)
                        self.progress.emit(progress)

                    # Проверяем, не была ли операция прервана
                    if self.isInterruptionRequested():
                        return False

            # Копируем метаданные файла
            shutil.copystat(src, dst)
            self.processed_files += 1

            # Обновляем текст прогресса
            self.progress_text.emit(
                f"🚩 Обработано: {self.processed_files}/{self.total_files} файлов ({self.format_size(self.processed_size)}/{self.format_size(self.total_size)})"
            )

            return True

        except Exception as e:
            logger.error(f"🆘 Ошибка копирования файла {src}: {e}")
            return False

    def copy_directory_with_progress(self, src, dst):
        """Копирование директории с отслеживанием прогресса"""
        try:
            # Создаем целевую директорию
            os.makedirs(dst, exist_ok=True)

            # Проходим по всем файлам и поддиректориям
            for root, dirs, files in os.walk(src):
                # Создаем структуру директорий
                rel_path = os.path.relpath(root, src)
                if rel_path != ".":
                    target_dir = os.path.join(dst, rel_path)
                    os.makedirs(target_dir, exist_ok=True)

                # Копируем файлы
                for file in files:
                    if self.isInterruptionRequested():
                        return False

                    src_file = os.path.join(root, file)
                    rel_file_path = os.path.relpath(src_file, src)
                    dst_file = os.path.join(dst, rel_file_path)

                    self.progress_text.emit(f"Копирование: {rel_file_path}")

                    if not self.copy_file_with_progress(src_file, dst_file):
                        return False

            return True

        except Exception as e:
            logger.error(f"🆘 Ошибка копирования директории {src}: {e}")
            return False

    def delete_with_progress(self, path):
        """Удаление с отслеживанием прогресса"""
        try:
            if os.path.isfile(path):
                self.progress_text.emit(f"Удаление файла: {os.path.basename(path)}")
                os.remove(path)
                self.processed_files += 1
                progress = (
                    int((self.processed_files * 100) / self.total_files)
                    if self.total_files > 0
                    else 100
                )
                self.progress.emit(progress)
                return True

            elif os.path.isdir(path):
                # Сначала удаляем все файлы
                for root, dirs, files in os.walk(path, topdown=False):
                    for file in files:
                        if self.isInterruptionRequested():
                            return False

                        file_path = os.path.join(root, file)
                        rel_path = os.path.relpath(file_path, path)
                        self.progress_text.emit(f"Удаление: {rel_path}")

                        try:
                            os.remove(file_path)
                            self.processed_files += 1
                            progress = (
                                int((self.processed_files * 100) / self.total_files)
                                if self.total_files > 0
                                else 100
                            )
                            self.progress.emit(progress)
                        except OSError:
                            pass

                    # Удаляем пустые директории
                    for dir in dirs:
                        try:
                            dir_path = os.path.join(root, dir)
                            os.rmdir(dir_path)
                        except OSError:
                            pass

                # Удаляем саму директорию
                try:
                    os.rmdir(path)
                except OSError:
                    pass

                return True

        except Exception as e:
            logger.error(f"🆘 Ошибка удаления {path}: {e}")
            return False

    def run(self):
        try:
            # Подсчитываем общее количество файлов и размер
            self.total_files, self.total_size = self.count_files_and_size(self.source)

            if self.operation == "copy":
                self.progress_text.emit(f"Подготовка к копированию...")
                self.progress.emit(0)

                if os.path.isdir(self.source):
                    success = self.copy_directory_with_progress(
                        self.source, self.destination
                    )
                else:
                    self.progress_text.emit(
                        f"⏳ Копирование файла: {os.path.basename(self.source)}"
                    )
                    success = self.copy_file_with_progress(
                        self.source, self.destination
                    )

                if success:
                    self.progress.emit(100)
                    self.finished.emit(True, "Копирование завершено успешно")
                else:
                    self.finished.emit(False, "Копирование прервано")

            elif self.operation == "move":
                self.progress_text.emit("Подготовка к перемещению...")
                self.progress.emit(0)

                # Сначала копируем
                if os.path.isdir(self.source):
                    success = self.copy_directory_with_progress(
                        self.source, self.destination
                    )
                else:
                    self.progress_text.emit(
                        f"⏳ Перемещение файла: {os.path.basename(self.source)}"
                    )
                    success = self.copy_file_with_progress(
                        self.source, self.destination
                    )

                # Затем удаляем оригинал
                if success:
                    self.progress_text.emit("⏳ Удаление исходных файлов...")
                    # Сброс счетчиков для удаления
                    self.processed_files = 0
                    success = self.delete_with_progress(self.source)

                if success:
                    self.progress.emit(100)
                    self.finished.emit(True, "Перемещение завершено успешно")
                else:
                    self.finished.emit(False, "Перемещение прервано")

            elif self.operation == "delete":
                self.progress_text.emit("Подготовка к удалению...")
                self.progress.emit(0)

                success = self.delete_with_progress(self.source)

                if success:
                    self.progress.emit(100)
                    self.finished.emit(True, "🚩 Удаление завершено успешно")
                else:
                    self.finished.emit(False, "Удаление прервано")

        except Exception as e:
            self.finished.emit(False, str(e))


class MultipleFileOperationThread(QThread):
    """Поток для выполнения множественных операций с файлами"""

    progress = pyqtSignal(int)
    progress_text = pyqtSignal(str)
    finished = pyqtSignal(bool, str)

    def __init__(self, operation, file_paths, destination_dir):
        super().__init__()
        self.operation = operation
        self.file_paths = file_paths
        self.destination_dir = Path(destination_dir) if destination_dir else None
        self.total_files = len(file_paths)
        self.processed_files = 0
        self.errors = []

    def run(self):
        try:
            self.progress_text.emit(f"Подготовка к {self.operation}...")
            self.progress.emit(0)

            for i, file_path in enumerate(self.file_paths):
                if self.isInterruptionRequested():
                    self.finished.emit(False, "Операция прервана пользователем")
                    return

                try:
                    # Обновляем прогресс
                    progress = int((i * 100) / self.total_files)
                    self.progress.emit(progress)

                    file_name = file_path.name
                    self.progress_text.emit(
                        f"[{i + 1}/{self.total_files}] Обработка: {file_name}"
                    )

                    if self.operation == "copy":
                        if not self.destination_dir:
                            raise Exception(
                                "Не указана папка назначения для копирования"
                            )

                        destination = self.destination_dir / file_name

                        # Проверяем существование файла и спрашиваем о замене
                        if destination.exists():
                            # Для множественных операций автоматически пропускаем существующие файлы
                            self.errors.append(
                                f"{file_name}: файл уже существует (пропущен)"
                            )
                            continue

                        if file_path.is_dir():
                            shutil.copytree(
                                str(file_path), str(destination), dirs_exist_ok=False
                            )
                        else:
                            shutil.copy2(str(file_path), str(destination))

                    elif self.operation == "move":
                        if not self.destination_dir:
                            raise Exception(
                                "Не указана папка назначения для перемещения"
                            )

                        destination = self.destination_dir / file_name

                        # Проверяем существование файла
                        if destination.exists():
                            self.errors.append(
                                f"{file_name}: файл уже существует (пропущен)"
                            )
                            continue

                        shutil.move(str(file_path), str(destination))

                    elif self.operation == "delete":
                        if file_path.is_dir():
                            shutil.rmtree(str(file_path))
                        else:
                            file_path.unlink()

                    self.processed_files += 1

                except Exception as e:
                    error_msg = f"{file_name}: {str(e)}"
                    self.errors.append(error_msg)
                    logger.error(f"🆘 Ошибка обработки файла {file_name}: {e}")

            # Завершаем операцию
            self.progress.emit(100)

            if self.errors:
                error_summary = f"🚩 Обработано {self.processed_files} из {self.total_files} файлов. Ошибки:\n"
                error_summary += "\n".join(self.errors[:10])
                if len(self.errors) > 10:
                    error_summary += f"\n...и еще {len(self.errors) - 10} ошибок"
                self.finished.emit(False, error_summary)
            else:
                self.finished.emit(
                    True, f"🚩 Успешно обработано {self.processed_files} файлов"
                )

        except Exception as e:
            self.finished.emit(False, f"🆘 Критическая ошибка: {str(e)}")


class FileViewer(QDialog):
    """Окно просмотра файлов"""

    def __init__(self, file_path, parent=None):
        super().__init__(parent)
        self.file_path = Path(file_path)
        self.mime_db = QMimeDatabase()
        self.parent_window = parent
        self.file_list = []
        self.current_index = 0
        self.setup_file_list()
        self.setup_ui()
        self.load_file()

    def setup_ui(self):
        self.setWindowTitle(
            f"Просмотр: {self.file_path.name} ({self.current_index + 1}/{len(self.file_list)})"
        )
        self.setGeometry(200, 200, 800, 600)

        layout = QVBoxLayout()

        # Панель навигации
        nav_layout = QHBoxLayout()

        self.prev_button = QPushButton("")
        self.prev_button.setToolTip("Предыдущий файл")
        self.prev_button.setIcon(QIcon(os.path.join("images", "arrow180.png")))
        self.prev_button.clicked.connect(self.prev_file)
        self.prev_button.setShortcut(QKeySequence("Left"))
        self.prev_button.setEnabled(self.current_index > 0)

        self.next_button = QPushButton("")
        self.next_button.setToolTip("Следующий файл")
        self.next_button.setIcon(QIcon(os.path.join("images", "arrow000.png")))
        self.next_button.clicked.connect(self.next_file)
        self.next_button.setShortcut(QKeySequence("Right"))
        self.next_button.setEnabled(self.current_index < len(self.file_list) - 1)

        self.file_info_label = QLabel(
            f"{self.current_index + 1} из {len(self.file_list)}"
        )
        self.file_info_label.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.file_name_label = QLabel(self.file_path.name)
        self.file_name_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.file_name_label.setStyleSheet(
            "QLabel { font-weight: bold; font-size: 12px; }"
        )

        nav_layout.addWidget(self.prev_button)
        nav_layout.addWidget(self.file_info_label)
        nav_layout.addWidget(self.next_button)
        nav_layout.addStretch()

        # Создаем tab widget для разных типов просмотра
        self.tab_widget = QTabWidget()

        # Вкладка для текста
        self.text_tab = QTextEdit()
        self.text_tab.setReadOnly(True)
        self.text_tab.setFont(QFont("Consolas", 10))

        # Вкладка для изображений
        self.image_tab = QScrollArea()
        self.image_label = QLabel()
        self.image_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.image_tab.setWidget(self.image_label)
        self.image_tab.setWidgetResizable(True)

        # Вкладка hex просмотра
        self.hex_tab = QTextEdit()
        self.hex_tab.setReadOnly(True)
        self.hex_tab.setFont(QFont("Consolas", 9))

        layout.addLayout(nav_layout)
        layout.addWidget(self.file_name_label)
        layout.addWidget(self.tab_widget)

        self.button_box = QDialogButtonBox(QDialogButtonBox.StandardButton.Close)

        # Получаем ссылку на саму кнопку и меняем её текст
        close_button = self.button_box.button(QDialogButtonBox.StandardButton.Close)
        close_button.setText("Закрыть")  # Новый текст кнопки

        # Кнопки
        button_box = QDialogButtonBox(QDialogButtonBox.StandardButton.Close)
        close_button = button_box.button(QDialogButtonBox.StandardButton.Close)
        close_button.setText("Закрыть")
        button_box.rejected.connect(self.close)

        self.edit_button = QPushButton("Редактировать")
        self.edit_button.clicked.connect(self.edit_file)
        button_box.addButton(self.edit_button, QDialogButtonBox.ButtonRole.ActionRole)

        layout.addWidget(button_box)
        self.setLayout(layout)

    def load_file(self):
        """Загрузить файл для просмотра"""
        try:
            mime_type = self.mime_db.mimeTypeForFile(str(self.file_path))

            # Проверяем размер файла
            file_size = self.file_path.stat().st_size
            if file_size > 10 * 1024 * 1024:  # 10MB
                # Для больших файлов показываем только информацию
                info_text = f"Файл слишком большой для просмотра\n\n"
                info_text += f"Имя: {self.file_path.name}\n"
                info_text += f"Размер: {self.format_file_size(file_size)}\n"
                info_text += f"Путь: {self.file_path}\n"
                info_text += f"Тип MIME: {mime_type.name()}"

                self.text_tab.setPlainText(info_text)
                self.tab_widget.addTab(self.text_tab, "Информация")
                self.edit_button.setEnabled(False)
                return

            # Текстовые файлы
            if mime_type.name().startswith(
                "text/"
            ) or self.file_path.suffix.lower() in [
                ".py",
                ".js",
                ".html",
                ".css",
                ".json",
                ".xml",
                ".log",
                ".ini",
                ".cfg",
                ".md",
                ".txt",
                ".bat",
                ".sh",
                ".yml",
                ".yaml",
                ".sql",
            ]:
                self.load_text_file()
                self.tab_widget.addTab(self.text_tab, "Текст")
                self.edit_button.setEnabled(True)

            # Изображения
            elif mime_type.name().startswith(
                "image/"
            ) or self.file_path.suffix.lower() in [
                ".jpg",
                ".jpeg",
                ".png",
                ".gif",
                ".bmp",
                ".svg",
                ".ico",
                ".webp",
            ]:
                self.load_image_file()
                self.tab_widget.addTab(self.image_tab, "Изображение")
                self.edit_button.setEnabled(False)

            # Всегда добавляем hex просмотр для небольших файлов
            if file_size < 1024 * 1024:  # Только для файлов меньше 1MB
                self.load_hex_file()
                self.tab_widget.addTab(self.hex_tab, "Hex")

            if self.tab_widget.count() == 1:  # Только hex вкладка
                self.edit_button.setEnabled(False)

        except Exception as e:
            error_text = f"Ошибка загрузки файла: {e}\n\n"
            error_text += f"Имя: {self.file_path.name}\n"
            error_text += f"Путь: {self.file_path}"

            self.text_tab.setPlainText(error_text)
            self.tab_widget.addTab(self.text_tab, "Ошибка")
            self.edit_button.setEnabled(False)

    def format_file_size(self, size):
        """Форматировать размер файла"""
        for unit in ["Б", "КБ", "МБ", "ГБ"]:
            if size < 1024:
                return f"{size:.1f} {unit}"
            size /= 1024
        return f"{size:.1f} ТБ"

    def load_text_file(self):
        """Загрузить текстовый файл"""
        try:
            # Попробуем разные кодировки
            encodings = ["utf-8", "cp1251", "latin1"]
            content = None

            for encoding in encodings:
                try:
                    with open(self.file_path, "r", encoding=encoding) as f:
                        content = f.read()
                    break
                except UnicodeDecodeError:
                    continue

            if content is None:
                # Если не удалось декодировать как текст, читаем как бинарный
                with open(self.file_path, "rb") as f:
                    binary_content = f.read()
                content = binary_content.decode("utf-8", errors="replace")

            self.text_tab.setPlainText(content)

        except Exception as e:
            self.text_tab.setPlainText(f"🆘 Ошибка чтения файла: {e}")

    def load_image_file(self):
        """Загрузить изображение"""
        try:
            pixmap = QPixmap(str(self.file_path))
            if not pixmap.isNull():
                # Масштабируем изображение при необходимости
                if pixmap.width() > 800 or pixmap.height() > 600:
                    pixmap = pixmap.scaled(
                        800,
                        600,
                        Qt.AspectRatioMode.KeepAspectRatio,
                        Qt.TransformationMode.SmoothTransformation,
                    )
                self.image_label.setPixmap(pixmap)
            else:
                self.image_label.setText("Не удалось загрузить изображение")
        except Exception as e:
            self.image_label.setText(f"🆘 Ошибка загрузки изображения: {e}")

    def load_hex_file(self):
        """Загрузить файл в hex формате"""
        try:
            with open(self.file_path, "rb") as f:
                content = f.read(2048)  # Читаем первые 2 килобайта

            hex_content = []
            for i in range(0, len(content), 16):
                chunk = content[i : i + 16]
                hex_part = " ".join(f"{b:02x}" for b in chunk)
                ascii_part = "".join(chr(b) if 32 <= b <= 126 else "." for b in chunk)
                hex_content.append(f"{i:08x}:  {hex_part:<48} {ascii_part}")

            if len(content) == 2048:
                hex_content.append("\n... (показаны первые 2KB)")

            self.hex_tab.setPlainText("\n".join(hex_content))

        except Exception as e:
            self.hex_tab.setPlainText(f"🆘 Ошибка чтения файла: {e}")

    def keyPressEvent(self, event):
        """Обработка нажатий клавиш"""
        if event.key() == Qt.Key.Key_Left:
            self.prev_file()
        elif event.key() == Qt.Key.Key_Right:
            self.next_file()
        elif event.key() == Qt.Key.Key_Escape:
            self.close()
        else:
            super().keyPressEvent(event)

    def setup_file_list(self):
        """Создать список файлов для навигации"""
        try:
            # Получаем все файлы в текущей папке
            parent_dir = self.file_path.parent
            all_files = []

            for file_path in parent_dir.iterdir():
                if file_path.is_file() and self.is_viewable_file(file_path):
                    all_files.append(file_path)

            # Сортируем файлы по имени
            all_files.sort(key=lambda x: x.name.lower())

            self.file_list = all_files

            # Находим индекс текущего файла
            try:
                self.current_index = self.file_list.index(self.file_path)
            except ValueError:
                self.current_index = 0
                if self.file_list:
                    self.file_path = self.file_list[0]

        except Exception as e:
            logger.error(f"🆘 Ошибка создания списка файлов: {e}")
            self.file_list = [self.file_path]
            self.current_index = 0

    def is_viewable_file(self, file_path):
        """Проверить, можно ли просматривать файл"""
        try:
            mime_type = self.mime_db.mimeTypeForFile(str(file_path))

            # Текстовые файлы
            if mime_type.name().startswith("text/") or file_path.suffix.lower() in [
                ".py",
                ".js",
                ".html",
                ".css",
                ".json",
                ".xml",
                ".log",
                ".ini",
                ".cfg",
                ".md",
                ".txt",
                ".bat",
                ".sh",
                ".yml",
                ".yaml",
                ".sql",
            ]:
                return True

            # Изображения
            if mime_type.name().startswith("image/") or file_path.suffix.lower() in [
                ".jpg",
                ".jpeg",
                ".png",
                ".gif",
                ".bmp",
                ".svg",
                ".ico",
                ".webp",
            ]:
                return True

            return False
        except:
            return False

    def prev_file(self):
        """Перейти к предыдущему файлу"""
        if self.current_index > 0:
            self.current_index -= 1
            self.file_path = self.file_list[self.current_index]
            self.update_viewer()

    def next_file(self):
        """Перейти к следующему файлу"""
        if self.current_index < len(self.file_list) - 1:
            self.current_index += 1
            self.file_path = self.file_list[self.current_index]
            self.update_viewer()

    def update_viewer(self):
        """Обновить просмотрщик для нового файла"""
        # Обновляем заголовок и информацию
        self.setWindowTitle(
            f"Просмотр: {self.file_path.name} ({self.current_index + 1}/{len(self.file_list)})"
        )
        self.file_name_label.setText(self.file_path.name)
        self.file_info_label.setText(
            f"{self.current_index + 1} из {len(self.file_list)}"
        )

        # Обновляем кнопки навигации
        self.prev_button.setEnabled(self.current_index > 0)
        self.next_button.setEnabled(self.current_index < len(self.file_list) - 1)

        # Очищаем вкладки
        self.tab_widget.clear()

        # Загружаем новый файл
        self.load_file()

    def edit_file(self):
        """Открыть файл для редактирования"""
        editor = FileEditor(self.file_path, self)
        editor.exec()


class FileEditor(QDialog):
    """Редактор файлов"""

    def __init__(self, file_path, parent=None):
        super().__init__(parent)
        self.file_path = Path(file_path)
        self.original_content = ""
        self.setup_ui()
        self.load_file()

    def setup_ui(self):
        self.setWindowTitle(f"Редактирование: {self.file_path.name}")
        self.setGeometry(150, 150, 900, 700)

        layout = QVBoxLayout()

        # Панель инструментов
        toolbar_layout = QHBoxLayout()

        self.save_button = QPushButton(" Сохранить")
        self.save_button.setToolTip("Сохранить файл")
        self.save_button.setIcon(QIcon(os.path.join("images", "save0.png")))
        self.save_button.clicked.connect(self.save_file)
        self.save_button.setShortcut(QKeySequence("Ctrl+S"))

        self.save_as_button = QPushButton(" Сохранить как...")
        self.save_as_button.setToolTip("Сохранить файл как")
        self.save_as_button.setIcon(QIcon(os.path.join("images", "save.png")))
        self.save_as_button.clicked.connect(self.save_file_as)

        self.find_button = QPushButton(" Найти")
        self.find_button.setToolTip("Найти текст в файле")
        self.find_button.setIcon(QIcon(os.path.join("images", "search.png")))
        self.find_button.clicked.connect(self.find_text)
        self.find_button.setShortcut(QKeySequence("Ctrl+F"))

        # Настройки
        self.word_wrap_checkbox = QCheckBox("Перенос строк")
        self.word_wrap_checkbox.toggled.connect(self.toggle_word_wrap)

        self.font_size_spinbox = QSpinBox()
        self.font_size_spinbox.setRange(8, 32)
        self.font_size_spinbox.setValue(10)
        self.font_size_spinbox.valueChanged.connect(self.change_font_size)

        toolbar_layout.addWidget(self.save_button)
        toolbar_layout.addWidget(self.save_as_button)
        toolbar_layout.addWidget(self.find_button)
        toolbar_layout.addStretch()
        toolbar_layout.addWidget(QLabel("Размер шрифта:"))
        toolbar_layout.addWidget(self.font_size_spinbox)
        toolbar_layout.addWidget(self.word_wrap_checkbox)

        # Текстовый редактор
        self.text_edit = QPlainTextEdit()
        self.text_edit.setFont(QFont("Consolas", 10))
        self.text_edit.textChanged.connect(self.text_changed)

        # Строка состояния
        self.status_label = QLabel("Готов")

        layout.addLayout(toolbar_layout)
        layout.addWidget(self.text_edit)
        layout.addWidget(self.status_label)

        # Кнопки диалога
        button_box = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        close_button = button_box.button(QDialogButtonBox.StandardButton.Cancel)
        close_button.setText("Завершить")
        button_box.accepted.connect(self.accept_changes)
        button_box.rejected.connect(self.reject_changes)

        layout.addWidget(button_box)
        self.setLayout(layout)

    def load_file(self):
        """Загрузить файл для редактирования"""
        try:
            encodings = ["utf-8", "cp1251", "latin1"]

            for encoding in encodings:
                try:
                    with open(self.file_path, "r", encoding=encoding) as f:
                        self.original_content = f.read()
                    self.text_edit.setPlainText(self.original_content)
                    self.status_label.setText(f"Файл загружен ({encoding})")
                    return
                except UnicodeDecodeError:
                    continue

            QMessageBox.warning(
                self, "Предупреждение", "Не удалось определить кодировку файла"
            )

        except Exception as e:
            QMessageBox.critical(self, "Ошибка", f"🆘 Не удалось загрузить файл: {e}")

    def save_file(self):
        """Сохранить файл"""
        try:
            content = self.text_edit.toPlainText()
            with open(self.file_path, "w", encoding="utf-8") as f:
                f.write(content)
            self.original_content = content
            self.status_label.setText("Файл сохранен")
            QMessageBox.information(self, "Успех", "Файл успешно сохранен")
        except Exception as e:
            QMessageBox.critical(self, "Ошибка", f"Не удалось сохранить файл: {e}")

    def save_file_as(self):
        """Сохранить файл как"""
        file_path, _ = QFileDialog.getSaveFileName(
            self, "Сохранить как", str(self.file_path)
        )
        if file_path:
            try:
                content = self.text_edit.toPlainText()
                with open(file_path, "w", encoding="utf-8") as f:
                    f.write(content)
                self.status_label.setText(f"Файл сохранен как {file_path}")
                QMessageBox.information(self, "Успех", "Файл успешно сохранен")
            except Exception as e:
                QMessageBox.critical(self, "Ошибка", f"Не удалось сохранить файл: {e}")

    def find_text(self):
        """Найти текст"""
        text, ok = QInputDialog.getText(self, "Поиск", "Введите текст для поиска:")
        if ok and text:
            cursor = self.text_edit.textCursor()
            found = self.text_edit.find(text)
            if not found:
                QMessageBox.information(self, "Поиск", "Текст не найден")

    def toggle_word_wrap(self, checked):
        """Переключить перенос строк"""
        if checked:
            self.text_edit.setLineWrapMode(QPlainTextEdit.LineWrapMode.WidgetWidth)
        else:
            self.text_edit.setLineWrapMode(QPlainTextEdit.LineWrapMode.NoWrap)

    def change_font_size(self, size):
        """Изменить размер шрифта"""
        font = self.text_edit.font()
        font.setPointSize(size)
        self.text_edit.setFont(font)

    def text_changed(self):
        """Обработка изменения текста"""
        if self.text_edit.toPlainText() != self.original_content:
            self.setWindowTitle(f"*Редактирование: {self.file_path.name}")
        else:
            self.setWindowTitle(f"Редактирование: {self.file_path.name}")

    def accept_changes(self):
        """Принять изменения"""
        if self.text_edit.toPlainText() != self.original_content:
            reply = QMessageBox.question(
                self, "Сохранить изменения?", "Файл был изменен. Сохранить изменения?"
            )
            if reply == QMessageBox.StandardButton.Yes:
                self.save_file()
        self.accept()

    def reject_changes(self):
        """Отклонить изменения"""
        if self.text_edit.toPlainText() != self.original_content:
            reply = QMessageBox.question(
                self, "Отменить изменения?", "Файл был изменен. Отменить изменения?"
            )
            if reply == QMessageBox.StandardButton.Yes:
                self.reject()
        else:
            self.reject()


class ArchiveBrowserDialog(QDialog):
    """Диалог просмотра содержимого архива"""

    def __init__(self, archive_path, parent=None):
        super().__init__(parent)
        self.archive_path = Path(archive_path)
        self.setup_ui()
        self.load_archive_contents()

    def setup_ui(self):
        self.setWindowTitle(f"Просмотр архива: {self.archive_path.name}")
        self.setGeometry(200, 200, 800, 600)
        self.setModal(True)

        layout = QVBoxLayout()

        # Информация об архиве
        info_layout = QHBoxLayout()

        archive_info = QLabel(f"📦 Архив: {self.archive_path.name}")
        archive_info.setStyleSheet("QLabel { font-weight: bold; font-size: 12px; }")
        info_layout.addWidget(archive_info)

        # Размер архива
        try:
            archive_size = self.archive_path.stat().st_size
            size_text = self.format_size(archive_size)
            size_label = QLabel(f"Размер: {size_text}")
            info_layout.addWidget(size_label)
        except:
            pass

        info_layout.addStretch()
        layout.addLayout(info_layout)

        # Список содержимого архива
        self.content_tree = QTreeWidget()
        self.content_tree.setHeaderLabels(
            ["Имя файла", "Размер", "Дата изменения", "Путь"]
        )
        self.content_tree.setAlternatingRowColors(True)

        # Настройка колонок
        header = self.content_tree.header()
        header.setStretchLastSection(False)
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(3, QHeaderView.ResizeMode.Interactive)

        layout.addWidget(self.content_tree)

        # Статистика
        self.stats_label = QLabel("")
        self.stats_label.setStyleSheet("QLabel { color: #666; font-size: 10px; }")
        layout.addWidget(self.stats_label)

        # Кнопки
        button_layout = QHBoxLayout()

        extract_all_button = QPushButton("Извлечь все")
        extract_all_button.setToolTip("Извлечь все файлы из архива")
        extract_all_button.setIcon(QIcon(os.path.join("images", "arhive.png")))
        extract_all_button.clicked.connect(self.extract_all)
        button_layout.addWidget(extract_all_button)

        extract_selected_button = QPushButton("Извлечь выбранное")
        extract_selected_button.setToolTip("Извлечь выбранные файлы из архива")
        extract_selected_button.setIcon(QIcon(os.path.join("images", "arhive1.png")))
        extract_selected_button.clicked.connect(self.extract_selected)
        button_layout.addWidget(extract_selected_button)

        button_layout.addStretch()

        close_button = QPushButton("Закрыть")
        close_button.setToolTip("Закрыть диалог")
        close_button.setIcon(QIcon(os.path.join("images", "close1.png")))
        close_button.clicked.connect(self.close)
        button_layout.addWidget(close_button)

        layout.addLayout(button_layout)
        self.setLayout(layout)

    def format_size(self, size):
        """Форматировать размер файла"""
        for unit in ["Б", "КБ", "МБ", "ГБ"]:
            if size < 1024:
                return f"{size:.1f} {unit}"
            size /= 1024
        return f"{size:.1f} ТБ"

    def load_archive_contents(self):
        """Загрузить содержимое архива"""
        try:
            extension = self.archive_path.suffix.lower()
            file_count = 0
            total_size = 0

            if extension == ".zip":
                import zipfile

                with zipfile.ZipFile(self.archive_path, "r") as zipf:
                    for info in zipf.infolist():
                        if not info.is_dir():
                            # Извлекаем информацию о файле
                            file_name = Path(info.filename).name
                            file_size = info.file_size
                            # Конвертируем дату
                            try:
                                date_time = QDateTime(*info.date_time)
                                date_str = date_time.toString("dd.MM.yyyy hh:mm")
                            except:
                                date_str = "Неизвестно"

                            # Создаем элемент дерева
                            item = QTreeWidgetItem(
                                [
                                    f"📄 {file_name}",
                                    self.format_size(file_size),
                                    date_str,
                                    info.filename,
                                ]
                            )

                            # Сохраняем информацию в элементе
                            item.setData(0, Qt.ItemDataRole.UserRole, info)

                            self.content_tree.addTopLevelItem(item)
                            file_count += 1
                            total_size += file_size

            elif extension == ".rar":
                try:
                    import rarfile

                    with rarfile.RarFile(self.archive_path, "r") as rarf:
                        for info in rarf.infolist():
                            if not info.is_dir():
                                file_name = Path(info.filename).name
                                file_size = info.file_size

                                try:
                                    date_str = info.date_time.strftime("%d.%m.%Y %H:%M")
                                except:
                                    date_str = "Неизвестно"

                                item = QTreeWidgetItem(
                                    [
                                        f"📄 {file_name}",
                                        self.format_size(file_size),
                                        date_str,
                                        info.filename,
                                    ]
                                )

                                item.setData(0, Qt.ItemDataRole.UserRole, info)
                                self.content_tree.addTopLevelItem(item)
                                file_count += 1
                                total_size += file_size

                except ImportError:
                    QMessageBox.warning(
                        self,
                        "Ограничение",
                        "Для работы с RAR архивами требуется установить rarfile.\n"
                        "Используйте: pip install rarfile",
                    )
                    return

            elif extension == ".7z":
                try:
                    import py7zr

                    with py7zr.SevenZipFile(self.archive_path, mode="r") as archive:
                        for info in archive.list():
                            if not info.is_dir:
                                file_name = Path(info.filename).name
                                file_size = (
                                    info.uncompressed
                                    if hasattr(info, "uncompressed")
                                    else 0
                                )

                                try:
                                    date_str = (
                                        info.creationtime.strftime("%d.%m.%Y %H:%M")
                                        if info.creationtime
                                        else "Неизвестно"
                                    )
                                except:
                                    date_str = "Неизвестно"

                                item = QTreeWidgetItem(
                                    [
                                        f"📄 {file_name}",
                                        self.format_size(file_size),
                                        date_str,
                                        info.filename,
                                    ]
                                )

                                item.setData(0, Qt.ItemDataRole.UserRole, info)
                                self.content_tree.addTopLevelItem(item)
                                file_count += 1
                                total_size += file_size

                except ImportError:
                    QMessageBox.warning(
                        self,
                        "Ограничение",
                        "Для работы с 7Z архивами требуется установить py7zr.\n"
                        "Используйте: pip install py7zr",
                    )
                    return
            else:
                QMessageBox.warning(
                    self,
                    "Неподдерживаемый формат",
                    f"Формат {extension} не поддерживается для просмотра",
                )
                return

            # Обновляем статистику
            self.stats_label.setText(
                f"🚩 Файлов: {file_count}, Общий размер: {self.format_size(total_size)}"
            )

        except Exception as e:
            QMessageBox.critical(
                self, "Ошибка", f"Не удалось загрузить содержимое архива: {e}"
            )

    def extract_all(self):
        """Извлечь все файлы из архива"""
        try:
            # Выбираем папку для извлечения
            extract_folder = QFileDialog.getExistingDirectory(
                self, "Выберите папку для извлечения", str(self.archive_path.parent)
            )

            if not extract_folder:
                return

            extract_path = Path(extract_folder) / self.archive_path.stem
            extract_path.mkdir(exist_ok=True)

            extension = self.archive_path.suffix.lower()

            if extension == ".zip":
                import zipfile

                with zipfile.ZipFile(self.archive_path, "r") as zipf:
                    zipf.extractall(extract_path)

            elif extension == ".rar":
                import rarfile

                with rarfile.RarFile(self.archive_path, "r") as rarf:
                    rarf.extractall(extract_path)

            elif extension == ".7z":
                import py7zr

                with py7zr.SevenZipFile(self.archive_path, mode="r") as archive:
                    archive.extractall(extract_path)

            QMessageBox.information(
                self, "Успех", f"Архив извлечен в папку:\n{extract_path}"
            )

        except Exception as e:
            QMessageBox.critical(self, "Ошибка", f"Не удалось извлечь архив: {e}")

    def extract_selected(self):
        """Извлечь выбранные файлы"""
        selected_items = self.content_tree.selectedItems()
        if not selected_items:
            QMessageBox.information(self, "Информация", "Выберите файлы для извлечения")
            return

        try:
            # Выбираем папку для извлечения
            extract_folder = QFileDialog.getExistingDirectory(
                self, "Выберите папку для извлечения", str(self.archive_path.parent)
            )

            if not extract_folder:
                return

            extract_path = Path(extract_folder)
            extension = self.archive_path.suffix.lower()

            if extension == ".zip":
                import zipfile

                with zipfile.ZipFile(self.archive_path, "r") as zipf:
                    for item in selected_items:
                        info = item.data(0, Qt.ItemDataRole.UserRole)
                        if info:
                            zipf.extract(info, extract_path)

            QMessageBox.information(
                self,
                "Успех",
                f"Извлечено {len(selected_items)} файлов в:\n{extract_path}",
            )

        except Exception as e:
            QMessageBox.critical(self, "Ошибка", f"Не удалось извлечь файлы: {e}")


class PropertiesDialog(QDialog):
    """Диалог свойств файла/папки"""

    def __init__(self, path, parent=None):
        super().__init__(parent)
        self.path = Path(path)
        self.setup_ui()
        self.load_properties()

    def setup_ui(self):
        self.setWindowTitle(f"Свойства: {self.path.name}")
        self.setGeometry(200, 200, 500, 600)
        self.setModal(True)

        layout = QVBoxLayout()

        # Основная информация
        general_group = QGroupBox("Общие")
        general_layout = QGridLayout()

        # Название
        general_layout.addWidget(QLabel("Имя:"), 0, 0)
        self.name_label = QLabel(self.path.name)
        self.name_label.setWordWrap(True)
        general_layout.addWidget(self.name_label, 0, 1)

        # Тип
        general_layout.addWidget(QLabel("Тип:"), 1, 0)
        self.type_label = QLabel()
        general_layout.addWidget(self.type_label, 1, 1)

        # Расположение
        general_layout.addWidget(QLabel("Расположение:"), 2, 0)
        self.location_label = QLabel(str(self.path.parent))
        self.location_label.setWordWrap(True)
        general_layout.addWidget(self.location_label, 2, 1)

        # Размер
        general_layout.addWidget(QLabel("Размер:"), 3, 0)
        self.size_label = QLabel()
        general_layout.addWidget(self.size_label, 3, 1)

        general_group.setLayout(general_layout)
        layout.addWidget(general_group)

        # Даты
        dates_group = QGroupBox("Даты")
        dates_layout = QGridLayout()

        dates_layout.addWidget(QLabel("Создан:"), 0, 0)
        self.created_label = QLabel()
        dates_layout.addWidget(self.created_label, 0, 1)

        dates_layout.addWidget(QLabel("Изменен:"), 1, 0)
        self.modified_label = QLabel()
        dates_layout.addWidget(self.modified_label, 1, 1)

        dates_layout.addWidget(QLabel("Доступ:"), 2, 0)
        self.accessed_label = QLabel()
        dates_layout.addWidget(self.accessed_label, 2, 1)

        dates_group.setLayout(dates_layout)
        layout.addWidget(dates_group)

        # Атрибуты
        attributes_group = QGroupBox("Атрибуты")
        attributes_layout = QVBoxLayout()

        self.readonly_checkbox = QCheckBox("Только для чтения")
        self.hidden_checkbox = QCheckBox("Скрытый")
        self.system_checkbox = QCheckBox("Системный")

        attributes_layout.addWidget(self.readonly_checkbox)
        attributes_layout.addWidget(self.hidden_checkbox)
        attributes_layout.addWidget(self.system_checkbox)

        attributes_group.setLayout(attributes_layout)
        layout.addWidget(attributes_group)

        # Подробная информация
        if self.path.is_file():
            details_group = QGroupBox("Подробности")
            details_layout = QGridLayout()

            # MIME тип
            details_layout.addWidget(QLabel("MIME тип:"), 0, 0)
            self.mime_label = QLabel()
            details_layout.addWidget(self.mime_label, 0, 1)

            details_group.setLayout(details_layout)
            layout.addWidget(details_group)

        # Кнопки
        button_box = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Apply
        )
        button_box.accepted.connect(self.accept)
        button_box.button(QDialogButtonBox.StandardButton.Apply).clicked.connect(
            self.apply_changes
        )

        layout.addWidget(button_box)
        self.setLayout(layout)

    def load_properties(self):
        """Загрузить свойства файла/папки"""
        try:
            # Определяем тип
            if self.path.is_dir():
                self.type_label.setText("Папка")
            else:
                mime_db = QMimeDatabase()
                mime_type = mime_db.mimeTypeForFile(str(self.path))
                self.type_label.setText(f"Файл ({mime_type.comment()})")

                if hasattr(self, "mime_label"):
                    self.mime_label.setText(mime_type.name())

            # Размер
            if self.path.is_file():
                size = self.path.stat().st_size
                self.size_label.setText(f"{self.format_size(size)} ({size:,} байт)")
            else:
                # Для папок подсчитываем общий размер
                total_size, file_count, folder_count = self.calculate_folder_size(
                    self.path
                )
                self.size_label.setText(
                    f"{self.format_size(total_size)} ({file_count} файлов, {folder_count} папок)"
                )

            # Даты
            stat_info = self.path.stat()

            created_time = QDateTime.fromSecsSinceEpoch(int(stat_info.st_ctime))
            self.created_label.setText(created_time.toString("dd.MM.yyyy hh:mm:ss"))

            modified_time = QDateTime.fromSecsSinceEpoch(int(stat_info.st_mtime))
            self.modified_label.setText(modified_time.toString("dd.MM.yyyy hh:mm:ss"))

            accessed_time = QDateTime.fromSecsSinceEpoch(int(stat_info.st_atime))
            self.accessed_label.setText(accessed_time.toString("dd.MM.yyyy hh:mm:ss"))

            # Атрибуты
            self.readonly_checkbox.setChecked(not (stat_info.st_mode & 0o200))
            self.hidden_checkbox.setChecked(self.path.name.startswith("."))

            if sys.platform == "win32":
                try:
                    import stat

                    if hasattr(stat_info, "st_file_attributes"):
                        self.system_checkbox.setChecked(
                            bool(
                                stat_info.st_file_attributes
                                & stat.FILE_ATTRIBUTE_SYSTEM
                            )
                        )
                except (AttributeError, ImportError):
                    self.system_checkbox.setEnabled(False)
            else:
                self.system_checkbox.setEnabled(False)

        except Exception as e:
            QMessageBox.critical(self, "Ошибка", f"Не удалось загрузить свойства: {e}")

    def calculate_folder_size(self, folder_path):
        """Подсчитать размер папки"""
        total_size = 0
        file_count = 0
        folder_count = 0

        try:
            for item in folder_path.rglob("*"):
                if item.is_file():
                    try:
                        total_size += item.stat().st_size
                        file_count += 1
                    except (OSError, PermissionError):
                        pass
                elif item.is_dir():
                    folder_count += 1
        except (OSError, PermissionError):
            pass

        return total_size, file_count, folder_count

    def format_size(self, size):
        """Форматировать размер"""
        for unit in ["Б", "КБ", "МБ", "ГБ", "ТБ"]:
            if size < 1024:
                return f"{size:.1f} {unit}"
            size /= 1024
        return f"{size:.1f} ПБ"

    def apply_changes(self):
        """Применить изменения атрибутов"""
        try:
            # Изменяем атрибут "только для чтения"
            current_mode = self.path.stat().st_mode
            if self.readonly_checkbox.isChecked():
                # Убираем права на запись
                new_mode = current_mode & ~0o200
            else:
                # Добавляем права на запись
                new_mode = current_mode | 0o200

            self.path.chmod(new_mode)

            QMessageBox.information(self, "Успех", "Атрибуты файла изменены")

        except Exception as e:
            QMessageBox.critical(self, "Ошибка", f"Не удалось изменить атрибуты: {e}")


class FilePanel(QWidget):
    """Панель файлового менеджера"""

    def __init__(self, parent=None, create_default_tab=True):
        super().__init__(parent)
        self.parent_window = parent
        self.current_path = Path("C:\\")
        # Настройки будут загружены из файла настроек в restore_settings()
        self.color_scheme_enabled = True  # Временное значение до загрузки настроек
        self.sort_column = 0  # Временное значение до загрузки настроек
        self.setup_file_colors()
        self.setup_ui(create_default_tab)
        if create_default_tab:
            self.refresh()

    def setup_file_colors(self):
        """Настройка цветовых схем для различных типов файлов"""
        self.file_colors = {
            # Папки
            "folder": {"color": "#040680", "icon": "📁"},
            # Текстовые файлы
            "text": {"color": "#5D5D5D", "icon": "📄"},
            ".txt": {"color": "#5D5D5D", "icon": "📄"},
            ".md": {"color": "#083FA1", "icon": "📝"},
            ".rtf": {"color": "#5D5D5D", "icon": "📄"},
            # Программирование
            ".py": {"color": "#086DB6", "icon": "🐍"},
            ".js": {"color": "#086DB6", "icon": "📜"},
            ".html": {"color": "#086DB6", "icon": "🌐"},
            ".css": {"color": "#1572B6", "icon": "🎨"},
            ".php": {"color": "#1572B6", "icon": "🐘"},
            ".java": {"color": "#086DB6", "icon": "☕"},
            ".cpp": {"color": "#086DB6", "icon": "⚙️"},
            ".c": {"color": "#086DB6", "icon": "⚙️"},
            ".cs": {"color": "#086DB6", "icon": "🔷"},
            ".go": {"color": "#086DB6", "icon": "🐹"},
            ".rs": {"color": "#086DB6", "icon": "🦀"},
            ".rb": {"color": "#086DB6", "icon": "💎"},
            ".sh": {"color": "#7DE74F", "icon": "🖥️"},
            ".bat": {"color": "#7DE74F", "icon": "🖥️"},
            ".ps1": {"color": "#7DE74F", "icon": "🔵"},
            # Web разработка
            ".json": {"color": "#CB171E", "icon": "🗂️"},
            ".xml": {"color": "#CB171E", "icon": "📋"},
            ".yml": {"color": "#CB171E", "icon": "⚙️"},
            ".yaml": {"color": "#CB171E", "icon": "⚙️"},
            # Изображения
            ".jpg": {"color": "#048D16", "icon": "🖼️"},
            ".jpeg": {"color": "#048D16", "icon": "🖼️"},
            ".png": {"color": "#048D16", "icon": "🖼️"},
            ".gif": {"color": "#048D16", "icon": "🎞️"},
            ".bmp": {"color": "#048D16", "icon": "🖼️"},
            ".svg": {"color": "#048D16", "icon": "🎨"},
            ".ico": {"color": "#048D16", "icon": "🔸"},
            ".webp": {"color": "#048D16", "icon": "🖼️"},
            # Видео
            ".mp4": {"color": "#0F76FD", "icon": "🎬"},
            ".avi": {"color": "#0F76FD", "icon": "🎬"},
            ".mkv": {"color": "#0F76FD", "icon": "🎬"},
            ".mov": {"color": "#0F76FD", "icon": "🎬"},
            ".wmv": {"color": "#0F76FD", "icon": "🎬"},
            ".flv": {"color": "#0F76FD", "icon": "🎬"},
            ".webm": {"color": "#0F76FD", "icon": "🎬"},
            # Аудио
            ".mp3": {"color": "#5F27CD", "icon": "🎵"},
            ".wav": {"color": "#5F27CD", "icon": "🎵"},
            ".flac": {"color": "#5F27CD", "icon": "🎵"},
            ".ogg": {"color": "#5F27CD", "icon": "🎵"},
            ".m4a": {"color": "#5F27CD", "icon": "🎵"},
            ".wma": {"color": "#5F27CD", "icon": "🎵"},
            # Архивы
            ".zip": {"color": "#747D8C", "icon": "📦"},
            ".rar": {"color": "#747D8C", "icon": "📦"},
            ".7z": {"color": "#747D8C", "icon": "📦"},
            ".tar": {"color": "#747D8C", "icon": "📦"},
            ".gz": {"color": "#747D8C", "icon": "📦"},
            ".bz2": {"color": "#747D8C", "icon": "📦"},
            # Документы
            ".pdf": {"color": "#E74C3C", "icon": "📕"},
            ".doc": {"color": "#2B579A", "icon": "📘"},
            ".docx": {"color": "#2B579A", "icon": "📘"},
            ".xls": {"color": "#1D6F42", "icon": "📊"},
            ".xlsx": {"color": "#1D6F42", "icon": "📊"},
            ".ppt": {"color": "#D24726", "icon": "📋"},
            ".pptx": {"color": "#D24726", "icon": "📋"},
            ".odt": {"color": "#2B579A", "icon": "📘"},
            ".ods": {"color": "#1D6F42", "icon": "📊"},
            ".odp": {"color": "#D24726", "icon": "📋"},
            # Базы данных
            ".db": {"color": "#570044", "icon": "🗄️"},
            ".sqlite": {"color": "#570044", "icon": "🗄️"},
            ".sql": {"color": "#570044", "icon": "🗄️"},
            ".mdb": {"color": "#570044", "icon": "🗄️"},
            # Системные
            ".exe": {"color": "#A91E22", "icon": "⚙️"},
            ".msi": {"color": "#A91E22", "icon": "📦"},
            ".deb": {"color": "#A91E22", "icon": "📦"},
            ".rpm": {"color": "#C8102E", "icon": "📦"},
            ".dmg": {"color": "#C8102E", "icon": "💽"},
            ".iso": {"color": "#6E23FA", "icon": "💽"},
            # Конфигурационные
            ".ini": {"color": "#95A5A6", "icon": "⚙️"},
            ".cfg": {"color": "#95A5A6", "icon": "⚙️"},
            ".conf": {"color": "#95A5A6", "icon": "⚙️"},
            ".properties": {"color": "#95A5A6", "icon": "⚙️"},
            # Логи
            ".log": {"color": "#7F8C8D", "icon": "📜"},
            # Шрифты
            ".ttf": {"color": "#D35400", "icon": "🔤"},
            ".otf": {"color": "#D35400", "icon": "🔤"},
            ".woff": {"color": "#D35400", "icon": "🔤"},
            ".woff2": {"color": "#D35400", "icon": "🔤"},
            # По умолчанию
            "default": {"color": "#95A5A6", "icon": "📄"},
        }

    def setup_ui(self, create_default_tab=True):
        layout = QVBoxLayout()

        # Система вкладок
        self.tab_widget = QTabWidget()
        self.tab_widget.setTabsClosable(True)
        self.tab_widget.setMovable(True)
        self.tab_widget.tabCloseRequested.connect(self.close_tab)
        self.tab_widget.currentChanged.connect(self.tab_changed)

        # Кнопки для управления вкладками
        tab_buttons_widget = QWidget()
        tab_buttons_layout = QHBoxLayout()
        tab_buttons_layout.setContentsMargins(0, 0, 0, 0)
        tab_buttons_layout.setSpacing(2)

        # Кнопка выбора по маске
        self.select_mask_button = QPushButton("")
        self.select_mask_button.setIcon(QIcon(os.path.join("images", "asterisk.png")))
        self.select_mask_button.setMaximumWidth(25)
        self.select_mask_button.setToolTip("Выбрать файлы по маске")
        self.select_mask_button.clicked.connect(self.select_files_by_mask)

        # Кнопка для добавления новой вкладки
        self.new_tab_button = QPushButton("")
        self.new_tab_button.setIcon(QIcon(os.path.join("images", "plus.png")))
        self.new_tab_button.setMaximumWidth(25)
        self.new_tab_button.setToolTip("Новая вкладка")
        self.new_tab_button.clicked.connect(self.add_new_tab)

        tab_buttons_layout.addWidget(self.select_mask_button)
        tab_buttons_layout.addWidget(self.new_tab_button)
        tab_buttons_widget.setLayout(tab_buttons_layout)

        self.tab_widget.setCornerWidget(tab_buttons_widget, Qt.Corner.TopRightCorner)

        # Создаем первую вкладку только если требуется
        if create_default_tab:
            self.add_new_tab()

        layout.addWidget(self.tab_widget)
        self.setLayout(layout)

    def create_tab_content(self, path):
        """Создать содержимое вкладки"""
        # Убеждаемся, что path - это объект Path
        if not isinstance(path, Path):
            if isinstance(path, str):
                path = Path(path)
            else:
                path = Path("C:\\")

        tab_widget = QWidget()
        tab_layout = QVBoxLayout()

        # Панель навигации
        nav_layout = QHBoxLayout()

        # Выпадающий список дисков
        drives_combo = QComboBox()
        drives_combo.setMinimumWidth(50)
        drives_combo.setMaximumWidth(120)
        drives_combo.currentTextChanged.connect(
            lambda drive: self.change_drive_tab(self.tab_widget.currentIndex(), drive)
        )
        self.populate_drives_combo(drives_combo)

        path_label = QLabel(str(path))
        path_label.setStyleSheet(
            "QLabel { background-color: #f0f0f0; padding: 5px; border: 1px solid #ccc; border-radius: 10px; }"
        )

        up_button = QPushButton("")
        up_button.setIcon(QIcon(os.path.join("images", "up.png")))
        up_button.setMaximumWidth(30)
        up_button.setToolTip("Перейти в родительскую папку")
        up_button.clicked.connect(
            lambda: self.go_up_tab(self.tab_widget.currentIndex())
        )

        home_button = QPushButton("")
        home_button.setIcon(QIcon(os.path.join("images", "home0.png")))
        home_button.setMaximumWidth(30)
        home_button.setToolTip("Перейти в корень диска")
        home_button.clicked.connect(
            lambda: self.go_home_tab(self.tab_widget.currentIndex())
        )

        # Кнопка для дублирования вкладки
        duplicate_button = QPushButton("")
        duplicate_button.setIcon(QIcon(os.path.join("images", "double.png")))
        duplicate_button.setMaximumWidth(30)
        duplicate_button.setToolTip("Дублировать вкладку")
        duplicate_button.clicked.connect(
            lambda: self.duplicate_tab(self.tab_widget.currentIndex())
        )

        nav_layout.addWidget(drives_combo)
        nav_layout.addWidget(up_button)
        nav_layout.addWidget(home_button)
        nav_layout.addWidget(duplicate_button)
        nav_layout.addWidget(path_label)

        # Информация о диске
        disk_info_layout = QHBoxLayout()
        disk_info_label = QLabel("")
        disk_info_label.setStyleSheet(
            "QLabel { font-size: 12px; font-weight: normal; color: #666; }"
        )
        disk_info_layout.addWidget(disk_info_label)
        disk_info_layout.addStretch()

        # Список файлов с колонками и поддержкой drag-and-drop
        file_list = DragDropTreeWidget()
        file_list.setHeaderLabels(
            ["Имя файла", "Расширение", "Размер", "Дата изменения"]
        )
        file_list.itemDoubleClicked.connect(self.item_double_clicked)
        file_list.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        file_list.customContextMenuRequested.connect(self.show_context_menu)

        # Настройка множественного выбора
        file_list.setSelectionMode(QTreeWidget.SelectionMode.ExtendedSelection)

        # Настройка поведения выбора - выбираем всю строку
        file_list.setSelectionBehavior(QTreeWidget.SelectionBehavior.SelectRows)

        # Дополнительные настройки для корректной работы множественного выбора
        file_list.setUniformRowHeights(
            True
        )  # Ускоряет отрисовку при большом количестве элементов

        # Обработка событий фокуса для определения активной панели
        file_list.focusInEvent = lambda event: self.on_focus_in(file_list, event)
        # mousePressEvent уже обрабатывается в DragDropTreeWidget

        # Включаем всплывающие подсказки для элементов - они будут создаваться при добавлении элементов

        # Настраиваем фокус только для списка файлов
        file_list.setFocusPolicy(Qt.FocusPolicy.StrongFocus)

        # Настройка ширины колонок
        header = file_list.header()
        header.setStretchLastSection(False)
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)  # Имя файла
        header.setSectionResizeMode(
            1, QHeaderView.ResizeMode.ResizeToContents
        )  # Расширение
        header.setSectionResizeMode(
            2, QHeaderView.ResizeMode.ResizeToContents
        )  # Размер
        header.setSectionResizeMode(3, QHeaderView.ResizeMode.ResizeToContents)  # Дата

        # Добавляем сортировку по клику на заголовки
        header.sectionClicked.connect(
            lambda column: self.sort_by_column(column, file_list)
        )
        header.setSectionsClickable(True)

        # Убираем альтернативную подсветку строк
        file_list.setAlternatingRowColors(False)
        file_list.setRootIsDecorated(False)  # Убираем стрелочки для папок

        tab_layout.addLayout(nav_layout)
        tab_layout.addLayout(disk_info_layout)
        tab_layout.addWidget(file_list)
        tab_widget.setLayout(tab_layout)

        # Сохраняем ссылки в виджете для удобного доступа
        tab_widget.path_label = path_label
        tab_widget.file_list = file_list
        tab_widget.current_path = path
        tab_widget.drives_combo = drives_combo
        tab_widget.disk_info_label = disk_info_label

        # Добавляем ссылку на родительскую панель для обработки событий
        file_list.parent_panel = self

        # Инициализация параметров сортировки для каждой вкладки
        tab_widget.sort_column = getattr(self, "sort_column", 0)
        tab_widget.sort_reverse = False

        return tab_widget

    def add_new_tab(self, path=None):
        """Добавить новую вкладку"""
        if path is None:
            path = self.current_path

        # Убеждаемся, что path - это объект Path
        if not isinstance(path, Path):
            if isinstance(path, str):
                path = Path(path)
            else:
                path = Path(self.current_path)

        logger.debug(f"Создание новой вкладки с путем: {path}")

        tab_content = self.create_tab_content(path)

        # Принудительно устанавливаем правильный путь в tab_content
        tab_content.current_path = path

        tab_name = path.name if path.name else path.as_posix()
        if not tab_name or tab_name == ".":
            tab_name = (
                str(path)[:3] if len(str(path)) >= 3 else str(path)
            )  # Например, "C:\"

        index = self.tab_widget.addTab(tab_content, tab_name)

        # НЕ устанавливаем как текущую при восстановлении настроек
        # Это будет сделано отдельно в restore_settings
        if not hasattr(self.parent_window, "_restoring_settings"):
            self.tab_widget.setCurrentIndex(index)

        # Обновляем current_path панели
        self.current_path = path

        # Обновляем содержимое вкладки
        self.refresh_tab(index)

        # Обновляем настройки фокуса для главного окна
        if self.parent_window and hasattr(self.parent_window, "setup_tab_order"):
            self.parent_window.setup_tab_order()

        logger.debug(
            f"Вкладка создана с индексом {index}, путь: {tab_content.current_path}"
        )
        return index

    def close_tab(self, index):
        """Закрыть вкладку"""
        if self.tab_widget.count() > 1:
            self.tab_widget.removeTab(index)
        else:
            # Если остается одна вкладка, не закрываем ее, а сбрасываем на домашний каталог
            self.go_home_tab(index)

    def duplicate_tab(self, index):
        """Дублировать вкладку"""
        if index >= 0:
            current_tab = self.tab_widget.widget(index)
            if current_tab:
                path = current_tab.current_path
                self.add_new_tab(path)

    def tab_changed(self, index):
        """Обработка смены вкладки"""
        if index >= 0:
            current_tab = self.tab_widget.widget(index)
            if current_tab:
                # Проверяем, что current_path установлен корректно
                if hasattr(current_tab, "current_path") and current_tab.current_path:
                    self.current_path = current_tab.current_path
                    logger.debug(
                        f"Переключились на вкладку {index}, путь: {self.current_path}"
                    )
                else:
                    logger.warning(f"Вкладка {index} не имеет корректного current_path")
                    # Используем путь из первого элемента, если доступен
                    if hasattr(current_tab, "path_label") and current_tab.path_label:
                        try:
                            path_from_label = Path(current_tab.path_label.text())
                            current_tab.current_path = path_from_label
                            self.current_path = path_from_label
                            logger.debug(
                                f"Восстановлен путь из метки: {self.current_path}"
                            )
                        except Exception as e:
                            logger.error(f"Ошибка восстановления пути из метки: {e}")

                # Обновляем текущий file_list для совместимости с существующим кодом
                self.file_list = current_tab.file_list

    def get_current_tab(self):
        """Получить текущую вкладку"""
        return self.tab_widget.currentWidget()

    def refresh_tab(self, index):
        """Обновить содержимое вкладки"""
        try:
            tab_widget = self.tab_widget.widget(index)
            if not tab_widget:
                return

            path = tab_widget.current_path
            file_list = tab_widget.file_list
            path_label = tab_widget.path_label

            logger.debug(f"Обновление вкладки {index} с путем: {path}")

            file_list.clear()
            path_label.setText(str(path))

            # Обновляем название вкладки
            tab_name = path.name if path.name else path.as_posix()
            if not tab_name or tab_name == ".":
                tab_name = (
                    str(path)[:3] if len(str(path)) >= 3 else str(path)
                )  # Например, "C:\"
            self.tab_widget.setTabText(index, tab_name)

            # Обновляем current_path панели только если это активная вкладка
            if index == self.tab_widget.currentIndex():
                self.current_path = path

            # Осторожно обновляем комбобокс дисков
            if hasattr(tab_widget, "drives_combo"):
                try:
                    # Только обновляем выбор, не перезагружаем весь список
                    self.update_drives_combo_selection(tab_widget.drives_combo, path)
                except Exception as e:
                    logger.error(f"Ошибка обновления комбобокса: {e}")

            # Обновляем информацию о диске
            if hasattr(tab_widget, "disk_info_label"):
                try:
                    self.update_disk_info(tab_widget, path)
                except Exception as e:
                    logger.error(f"Ошибка обновления информации о диске: {e}")

        except Exception as e:
            logger.error(f"Ошибка обновления вкладки {index}: {e}")

        try:
            # Списки для раздельного добавления папок и файлов
            folders = []
            files = []

            # Добавить родительскую директорию
            if path.parent != path:
                item = QTreeWidgetItem(["📁 ..", "", "", ""])
                item.setData(0, Qt.ItemDataRole.UserRole, path.parent)
                # Жирный шрифт для папок
                font = item.font(0)
                font.setBold(True)
                item.setFont(0, font)
                item.setFont(1, font)
                item.setFont(2, font)
                item.setFont(3, font)
                file_list.addTopLevelItem(item)

            # Собираем папки и файлы отдельно
            for item_path in path.iterdir():
                if item_path.is_dir():
                    folders.append(item_path)
                elif item_path.is_file():
                    files.append(item_path)

            # Добавляем папки (сортированные по имени)
            for folder_path in sorted(folders, key=lambda x: x.name.lower()):
                folder_info = self.file_colors.get(
                    "folder", self.file_colors["default"]
                )
                try:
                    stat_info = folder_path.stat()
                    mod_time = QDateTime.fromSecsSinceEpoch(int(stat_info.st_mtime))
                    date_str = mod_time.toString("dd.MM.yyyy hh:mm")

                    item = QTreeWidgetItem(
                        [
                            f"{folder_info['icon']} {folder_path.name}",
                            "",
                            "<ПАПКА>",
                            date_str,
                        ]
                    )
                    item.setData(0, Qt.ItemDataRole.UserRole, folder_path)

                    # Жирный шрифт для папок
                    font = item.font(0)
                    font.setBold(True)
                    item.setFont(0, font)
                    item.setFont(1, font)
                    item.setFont(2, font)
                    item.setFont(3, font)

                    if self.color_scheme_enabled:
                        item.setForeground(0, QColor(folder_info["color"]))
                        item.setForeground(1, QColor(folder_info["color"]))
                        item.setForeground(2, QColor(folder_info["color"]))
                        item.setForeground(3, QColor(folder_info["color"]))

                    # Устанавливаем подсказку для папки
                    self.set_item_tooltip(item, folder_path)

                    file_list.addTopLevelItem(item)
                except (OSError, PermissionError):
                    item = QTreeWidgetItem(
                        [
                            f"{folder_info['icon']} {folder_path.name}",
                            "",
                            "<ПАПКА>",
                            "Недоступно",
                        ]
                    )
                    item.setData(0, Qt.ItemDataRole.UserRole, folder_path)
                    # Жирный шрифт для папок
                    font = item.font(0)
                    font.setBold(True)
                    item.setFont(0, font)
                    item.setFont(1, font)
                    item.setFont(2, font)
                    item.setFont(3, font)
                    if self.color_scheme_enabled:
                        item.setForeground(0, QColor(folder_info["color"]))

                    # Устанавливаем подсказку для недоступной папки
                    self.set_item_tooltip(item, folder_path)

                    file_list.addTopLevelItem(item)

            # Добавляем файлы (с возможностью сортировки)
            file_items = []
            for file_path in files:
                try:
                    stat_info = file_path.stat()
                    size = self.format_size(stat_info.st_size)
                    mod_time = QDateTime.fromSecsSinceEpoch(int(stat_info.st_mtime))
                    date_str = mod_time.toString("dd.MM.yyyy hh:mm")

                    file_info = self.get_file_info(file_path)
                    extension = file_path.suffix.lower() if file_path.suffix else ""
                    # Убираем расширение из имени файла для отображения
                    display_name = (
                        file_path.stem if file_path.suffix else file_path.name
                    )

                    item = QTreeWidgetItem(
                        [
                            f"{file_info['icon']} {display_name}",
                            extension,
                            size,
                            date_str,
                        ]
                    )
                    item.setData(0, Qt.ItemDataRole.UserRole, file_path)

                    if self.color_scheme_enabled:
                        item.setForeground(0, QColor(file_info["color"]))
                        item.setForeground(1, QColor(file_info["color"]))
                        item.setForeground(2, QColor(file_info["color"]))
                        item.setForeground(3, QColor(file_info["color"]))

                    # Устанавливаем подсказку для файла
                    self.set_item_tooltip(item, file_path)

                    # Сохраняем для сортировки (добавляем расширение)
                    file_items.append(
                        (
                            item,
                            file_path,
                            stat_info.st_size,
                            stat_info.st_mtime,
                            extension,
                        )
                    )
                except (OSError, PermissionError):
                    file_info = self.get_file_info(file_path)
                    extension = file_path.suffix.lower() if file_path.suffix else ""
                    # Убираем расширение из имени файла для отображения
                    display_name = (
                        file_path.stem if file_path.suffix else file_path.name
                    )

                    item = QTreeWidgetItem(
                        [
                            f"{file_info['icon']} {display_name}",
                            extension,
                            "Недоступно",
                            "Недоступно",
                        ]
                    )
                    item.setData(0, Qt.ItemDataRole.UserRole, file_path)
                    if self.color_scheme_enabled:
                        item.setForeground(0, QColor(file_info["color"]))

                    # Устанавливаем подсказку для недоступного файла
                    self.set_item_tooltip(item, file_path)

                    file_items.append((item, file_path, 0, 0, extension))

            # Получаем настройки сортировки для текущей вкладки
            tab_sort_column = getattr(tab_widget, "sort_column", self.sort_column)
            tab_sort_reverse = getattr(tab_widget, "sort_reverse", False)

            # Сортируем файлы согласно выбранному столбцу
            if tab_sort_column == 0:  # По имени
                file_items.sort(
                    key=lambda x: x[1].name.lower(), reverse=tab_sort_reverse
                )
            elif tab_sort_column == 1:  # По расширению
                file_items.sort(key=lambda x: x[4], reverse=tab_sort_reverse)
            elif tab_sort_column == 2:  # По размеру
                file_items.sort(key=lambda x: x[2], reverse=tab_sort_reverse)
            elif tab_sort_column == 3:  # По дате
                file_items.sort(key=lambda x: x[3], reverse=tab_sort_reverse)

            # Обновляем индикатор сортировки в заголовке
            header = file_list.header()
            header.setSortIndicatorShown(True)
            if tab_sort_reverse:
                header.setSortIndicator(tab_sort_column, Qt.SortOrder.DescendingOrder)
            else:
                header.setSortIndicator(tab_sort_column, Qt.SortOrder.AscendingOrder)

            # Добавляем отсортированные файлы
            for item, _, _, _, _ in file_items:
                file_list.addTopLevelItem(item)

        except PermissionError:
            QMessageBox.warning(self, "Ошибка", "Нет доступа к папке")

    def go_up_tab(self, index):
        """Перейти в родительскую папку в указанной вкладке"""
        tab_widget = self.tab_widget.widget(index)
        if tab_widget and tab_widget.current_path.parent != tab_widget.current_path:
            tab_widget.current_path = tab_widget.current_path.parent
            self.current_path = tab_widget.current_path  # Обновляем текущий путь
            self.refresh_tab(index)

    def go_home_tab(self, index):
        """Перейти в корневой каталог текущего диска в указанной вкладке"""
        tab_widget = self.tab_widget.widget(index)
        if tab_widget:
            # Получаем корень текущего диска
            current_path = tab_widget.current_path
            if sys.platform == "win32":
                drive_root = str(current_path).split("\\")[0] + "\\"
                tab_widget.current_path = Path(drive_root)
            else:
                tab_widget.current_path = Path("/")

            self.current_path = tab_widget.current_path  # Обновляем текущий путь
            self.refresh_tab(index)

    def refresh(self):
        """Обновить список файлов в текущей вкладке"""
        current_index = self.tab_widget.currentIndex()
        self.refresh_tab(current_index)

    def format_size(self, size):
        """Форматировать размер файла"""
        for unit in ["Б", "КБ", "МБ", "ГБ"]:
            if size < 1024:
                return f"{size:.1f} {unit}"
            size /= 1024
        return f"{size:.1f} ТБ"

    def get_file_info(self, file_path):
        """Получить информацию о файле (цвет и иконка) на основе расширения"""
        extension = file_path.suffix.lower()

        # Сначала проверяем конкретное расширение
        if extension in self.file_colors:
            return self.file_colors[extension]

        # Затем проверяем общие категории
        mime_db = QMimeDatabase()
        mime_type = mime_db.mimeTypeForFile(str(file_path))

        if mime_type.name().startswith("image/"):
            return self.file_colors.get(".png", self.file_colors["default"])
        elif mime_type.name().startswith("video/"):
            return self.file_colors.get(".mp4", self.file_colors["default"])
        elif mime_type.name().startswith("audio/"):
            return self.file_colors.get(".mp3", self.file_colors["default"])
        elif mime_type.name().startswith("text/"):
            return self.file_colors.get("text", self.file_colors["default"])
        elif "zip" in mime_type.name() or "archive" in mime_type.name():
            return self.file_colors.get(".zip", self.file_colors["default"])

        # По умолчанию
        return self.file_colors["default"]

    def item_double_clicked(self, item, column):
        """Обработка двойного клика по элементу"""
        path = item.data(0, Qt.ItemDataRole.UserRole)
        if path.is_dir():
            # Обновляем путь в текущей вкладке
            current_tab = self.get_current_tab()
            if current_tab:
                current_tab.current_path = path
                self.current_path = path
                self.refresh()
        elif path.is_file():
            # Проверяем, является ли файл архивом
            extension = path.suffix.lower()
            if extension in [".zip", ".rar", ".7z", ".tar", ".gz", ".bz2"]:
                # Для архивов предлагаем выбор действия
                reply = QMessageBox.question(
                    self,
                    "Открыть архив",
                    f"Работать с архивом '{path.name}'?",
                    QMessageBox.StandardButton.Yes
                    | QMessageBox.StandardButton.No
                    | QMessageBox.StandardButton.Cancel,
                )

                # Настраиваем кнопки
                yes_button = QMessageBox.StandardButton.Yes
                no_button = QMessageBox.StandardButton.No
                cancel_button = QMessageBox.StandardButton.Cancel

                # Создаем кастомное сообщение
                msg = QMessageBox(self)
                msg.setWindowTitle("Открыть архив")
                msg.setText(f"Работать с архивом '{path.name}'?")

                # Добавляем кнопки с понятными названиями
                browse_button = msg.addButton(
                    "🗂️ Просмотреть содержимое", QMessageBox.ButtonRole.YesRole
                )
                extract_button = msg.addButton(
                    "📤 Извлечь файлы", QMessageBox.ButtonRole.NoRole
                )
                cancel_button = msg.addButton(
                    "❌ Отмена", QMessageBox.ButtonRole.RejectRole
                )

                msg.setDefaultButton(browse_button)
                result = msg.exec()

                if msg.clickedButton() == browse_button:
                    # Просматриваем содержимое архива как папку
                    self.browse_archive_contents(path)
                elif msg.clickedButton() == extract_button:
                    # Извлекаем архив
                    self.extract_from_archive(path)
                # Если отмена - ничего не делаем
            elif extension in [
                ".jpg",
                ".jpeg",
                ".png",
                ".gif",
                ".bmp",
                ".svg",
                ".ico",
                ".webp",
                ".py",
                ".js",
                ".html",
                ".css",
                ".json",
                ".xml",
                ".log",
                ".ini",
                ".cfg",
                ".md",
                ".txt",
                ".bat",
                ".sh",
                ".yml",
                ".yaml",
                ".sql",
            ]:
                viewer = FileViewer(path, self.parent_window)
                viewer.exec()
            else:
                # Просмотр файла во встроенном просмотрщике
                try:
                    os.startfile(str(path))
                except Exception as e:
                    QMessageBox.warning(
                        self, "Ошибка", f"Ошибка открытия файла {path}: {e}"
                    )

    def go_up(self):
        """Перейти в родительскую папку в текущей вкладке"""
        current_index = self.tab_widget.currentIndex()
        self.go_up_tab(current_index)

    def go_home(self):
        """Перейти в корневой каталог текущего диска в текущей вкладке"""
        current_index = self.tab_widget.currentIndex()
        self.go_home_tab(current_index)

    def get_selected_path(self):
        """Получить путь выбранного элемента"""
        current_tab = self.get_current_tab()
        if current_tab and current_tab.file_list:
            current_item = current_tab.file_list.currentItem()
            if current_item:
                return current_item.data(0, Qt.ItemDataRole.UserRole)
        return None

    def get_selected_paths(self):
        """Получить пути всех выбранных элементов"""
        current_tab = self.get_current_tab()
        if current_tab and current_tab.file_list:
            selected_items = current_tab.file_list.selectedItems()
            paths = []
            for item in selected_items:
                path = item.data(0, Qt.ItemDataRole.UserRole)
                if path and path.name != "..":  # Исключаем родительскую папку
                    paths.append(path)
            return paths
        return []

    def on_focus_in(self, file_list, event):
        """Обработка получения фокуса"""
        # Сбрасываем выделение у другой панели
        if self.parent_window:
            # Устанавливаем активную панель в главном окне
            self.parent_window.active_panel = self
            panel_name = "ЛЕВАЯ" if self == self.parent_window.left_panel else "ПРАВАЯ"
            logger.debug(f"Фокус получила панель: {panel_name}")

            if self == self.parent_window.left_panel:
                other_panel = self.parent_window.right_panel
            else:
                other_panel = self.parent_window.left_panel

            # Обновляем стили панелей
            self.update_panel_styles(active=True)
            other_panel.update_panel_styles(active=False)

        # Вызываем оригинальный обработчик
        QTreeWidget.focusInEvent(file_list, event)

    def on_mouse_press(self, file_list, event):
        """Обработка нажатия мыши"""
        # Устанавливаем активную панель в главном окне
        if self.parent_window:
            self.parent_window.active_panel = self
            panel_name = "ЛЕВАЯ" if self == self.parent_window.left_panel else "ПРАВАЯ"
            logger.debug(f"Клик по панели: {panel_name}")

        # Устанавливаем фокус на панель
        file_list.setFocus()

        # НЕ обрабатываем Ctrl+Click и Shift+Click здесь - это делается в DragDropTreeWidget
        # Просто вызываем оригинальный обработчик
        QTreeWidget.mousePressEvent(file_list, event)

    def update_panel_styles(self, active=True):
        """Обновить стили панели в зависимости от активности"""
        current_tab = self.get_current_tab()
        if current_tab and current_tab.file_list:
            if active:
                current_tab.path_label.setStyleSheet("""
                    QLabel {
                        background-color: white;
                        padding: 2px;
                        border: 1px solid #808080;
                        border-radius: 10px;
                    }
                """)
                current_tab.file_list.setStyleSheet("""
                    QTreeWidget {
                        border: 2px solid #808080;
                        border-radius: 5px;
                        background-color: white;
                    }
                    QTreeWidget::item:selected {
                        background-color: #3498DB;
                        color: white;
                    }
                """)
            else:
                # Неактивная панель - тонкая серая рамка
                current_tab.file_list.setStyleSheet("""
                    QTreeWidget {
                        border: 1px solid #BDC3C7;
                        border-radius: 5px;
                        background-color: #F8F9FA;
                    }
                    QTreeWidget::item:selected {
                        background-color: #BDC3C7;
                        color: black;
                    }
                """)

    def select_files_by_mask(self):
        """Выбрать файлы по маске"""
        mask, ok = QInputDialog.getText(
            self,
            "Выбор файлов по маске",
            "Введите маску (например: *.txt, *.py, test*):",
            text="*.*",
        )

        if not ok or not mask:
            return

        current_tab = self.get_current_tab()
        if not current_tab or not current_tab.file_list:
            return

        import fnmatch

        selected_count = 0

        # Снимаем все выделения
        current_tab.file_list.clearSelection()

        # Проходим по всем элементам и выбираем подходящие
        for i in range(current_tab.file_list.topLevelItemCount()):
            item = current_tab.file_list.topLevelItem(i)
            path = item.data(0, Qt.ItemDataRole.UserRole)

            if path and path.name != "..":
                # Проверяем соответствие маске
                if fnmatch.fnmatch(path.name.lower(), mask.lower()):
                    item.setSelected(True)
                    selected_count += 1

        self.parent_window.status_bar.showMessage(
            f"🚩 Выбрано файлов: {selected_count}", 3000
        )

    def show_context_menu(self, position):
        """Показать контекстное меню"""
        current_tab = self.get_current_tab()
        if not current_tab:
            return

        item = current_tab.file_list.itemAt(position)
        if not item:
            return

        menu = QMenu(self)

        # Получаем выбранный путь
        selected_path = item.data(0, Qt.ItemDataRole.UserRole)

        # Опции просмотра и редактирования
        if selected_path and selected_path.is_file():
            view_action = QAction(
                QIcon(os.path.join("images", "glass.png")), "Просмотр", self
            )
            view_action.triggered.connect(lambda: self.view_file(selected_path))
            menu.addAction(view_action)

            edit_action = QAction(
                QIcon(os.path.join("images", "edit.png")), "Редактировать", self
            )
            edit_action.triggered.connect(lambda: self.edit_file(selected_path))
            menu.addAction(edit_action)

            open_system_action = QAction(
                QIcon(os.path.join("images", "link0.png")),
                "Открыть системным приложением",
                self,
            )
            open_system_action.triggered.connect(
                lambda: self.open_with_system(selected_path)
            )
            menu.addAction(open_system_action)

            menu.addSeparator()

        copy_action = QAction(
            QIcon(os.path.join("images", "copy.png")), "Копировать", self
        )
        copy_action.triggered.connect(lambda: self.parent_window.copy_file(self))
        menu.addAction(copy_action)

        move_action = QAction(
            QIcon(os.path.join("images", "exit.png")), "Переместить", self
        )
        move_action.triggered.connect(lambda: self.parent_window.move_file(self))
        menu.addAction(move_action)

        menu.addSeparator()

        delete_action = QAction(
            QIcon(os.path.join("images", "delete.png")), "Удалить", self
        )
        delete_action.triggered.connect(lambda: self.parent_window.delete_file(self))
        menu.addAction(delete_action)

        menu.addSeparator()

        # VS Code интеграция
        if selected_path:
            if selected_path.is_dir():
                vscode_folder_action = QAction(
                    QIcon(os.path.join("images", "foldervscode1.png")),
                    "Открыть папку в VS Code",
                    self,
                )
                vscode_folder_action.triggered.connect(
                    lambda: self.open_in_vscode(selected_path, is_folder=True)
                )
                menu.addAction(vscode_folder_action)
            else:
                vscode_file_action = QAction(
                    QIcon(os.path.join("images", "vscode.png")),
                    "Открыть файл в VS Code",
                    self,
                )
                vscode_file_action.triggered.connect(
                    lambda: self.open_in_vscode(selected_path, is_folder=False)
                )
                menu.addAction(vscode_file_action)

            # Дополнительная опция - открыть текущую папку в VS Code
            if not selected_path.is_dir():
                vscode_current_folder_action = QAction(
                    QIcon(os.path.join("images", "foldervscode.png")),
                    "Открыть папку (текущую) в VS Code",
                    self,
                )
                vscode_current_folder_action.triggered.connect(
                    lambda: self.open_in_vscode(self.current_path, is_folder=True)
                )
                menu.addAction(vscode_current_folder_action)

        menu.addSeparator()

        # Открыть с помощью
        if selected_path and selected_path.is_file():
            open_with_action = QAction(
                QIcon(os.path.join("images", "magic.png")),
                "Открыть с помощью ▶",
                self,
            )
            open_with_action.triggered.connect(
                lambda: self.open_with_dialog(selected_path)
            )
            menu.addAction(open_with_action)

        # Копировать в буфер обмена
        if selected_path:
            copy_to_clipboard_action = QAction(
                QIcon(os.path.join("images", "copy1.png")),
                "Копировать файл в буфер",
                self,
            )
            copy_to_clipboard_action.triggered.connect(
                lambda: self.copy_to_clipboard(selected_path)
            )
            menu.addAction(copy_to_clipboard_action)

            copy_path_action = QAction(
                QIcon(os.path.join("images", "copy0.png")),
                "Копировать путь в буфер",
                self,
            )
            copy_path_action.triggered.connect(
                lambda: self.copy_path_to_clipboard(selected_path)
            )
            menu.addAction(copy_path_action)

        # Вставить из буфера обмена
        paste_action = QAction(
            QIcon(os.path.join("images", "snippets.png")), "Вставить из буфера", self
        )
        paste_action.triggered.connect(lambda: self.paste_from_clipboard())
        menu.addAction(paste_action)

        # Создать ярлык
        if selected_path and selected_path.is_file():
            create_shortcut_action = QAction(
                QIcon(os.path.join("images", "shortcut.png")), "Создать ярлык", self
            )
            create_shortcut_action.triggered.connect(
                lambda: self.create_shortcut(selected_path)
            )
            menu.addAction(create_shortcut_action)

        # Архивирование
        selected_paths = self.get_selected_paths()
        if selected_paths:
            if len(selected_paths) == 1:
                add_to_zip_action = QAction(
                    QIcon(os.path.join("images", "arhiveadd.png")),
                    "Добавить в архив ZIP",
                    self,
                )
                add_to_zip_action.triggered.connect(
                    lambda: self.add_to_zip_archive(selected_paths)
                )
            else:
                add_to_zip_action = QAction(
                    QIcon(os.path.join("images", "arhiveadd.png")),
                    f"Добавить {len(selected_paths)} элементов в архив ZIP",
                    self,
                )
                add_to_zip_action.triggered.connect(
                    lambda: self.add_to_zip_archive(selected_paths)
                )
            menu.addAction(add_to_zip_action)

        # Извлечение из архива
        if (
            selected_path
            and selected_path.is_file()
            and selected_path.suffix.lower() in [".zip", ".rar", ".7z"]
        ):
            extract_action = QAction(
                QIcon(os.path.join("images", "arhive.png")),
                "Извлечь из архива",
                self,
            )
            extract_action.triggered.connect(
                lambda: self.extract_from_archive(selected_path)
            )
            menu.addAction(extract_action)

        menu.addSeparator()

        rename_action = QAction(
            QIcon(os.path.join("images", "edit0.png")), "Переименовать", self
        )
        rename_action.triggered.connect(lambda: self.rename_file())
        menu.addAction(rename_action)

        new_folder_action = QAction(
            QIcon(os.path.join("images", "folderadd.png")), "Новая папка", self
        )
        new_folder_action.triggered.connect(self.create_folder)
        menu.addAction(new_folder_action)

        new_file_action = QAction(
            QIcon(os.path.join("images", "fileadd.png")),
            "Новый текстовый файл",
            self,
        )
        new_file_action.triggered.connect(self.create_text_file)
        menu.addAction(new_file_action)

        menu.addSeparator()

        # Свойства
        if selected_path:
            properties_action = QAction(
                QIcon(os.path.join("images", "filesearch.png")), "Свойства", self
            )
            properties_action.triggered.connect(
                lambda: self.show_properties(selected_path)
            )
            menu.addAction(properties_action)

        menu.exec(current_tab.file_list.mapToGlobal(position))

        # Добавляем опции для работы с вкладками в контекстное меню
        # menu.addSeparator()

        # new_tab_action = QAction("🗂️ Открыть в новой вкладке", self)
        # new_tab_action.triggered.connect(lambda: self.open_in_new_tab(selected_path))
        # menu.addAction(new_tab_action)

        # if selected_path.is_dir():
        #     duplicate_tab_action = QAction("⧉ Дублировать вкладку здесь", self)
        #     duplicate_tab_action.triggered.connect(
        #         lambda: self.add_new_tab(selected_path)
        #     )
        #     menu.addAction(duplicate_tab_action)

    def rename_file(self):
        """Переименовать файл"""
        selected_path = self.get_selected_path()
        if not selected_path or selected_path.name == "..":
            return

        new_name, ok = QInputDialog.getText(
            self, "Переименовать", "Новое имя:", text=selected_path.name
        )
        if ok and new_name:
            try:
                new_path = selected_path.parent / new_name
                selected_path.rename(new_path)
                self.refresh()
            except Exception as e:
                QMessageBox.critical(self, "Ошибка", f"Не удалось переименовать: {e}")

    def create_folder(self):
        """Создать новую папку"""
        folder_name, ok = QInputDialog.getText(self, "Новая папка", "Имя папки:")
        if ok and folder_name:
            try:
                new_folder = self.current_path / folder_name
                new_folder.mkdir()
                self.refresh()
            except Exception as e:
                QMessageBox.critical(self, "Ошибка", f"Не удалось создать папку: {e}")

    def view_file(self, file_path):
        """Просмотр файла"""
        viewer = FileViewer(file_path, self.parent_window)
        viewer.exec()

    def edit_file(self, file_path):
        """Редактирование файла"""
        editor = FileEditor(file_path, self.parent_window)
        editor.exec()
        self.refresh()  # Обновляем список после возможного редактирования

    def open_with_system(self, file_path):
        """Открыть файл системным приложением"""
        try:
            if sys.platform == "win32":
                os.startfile(str(file_path))
            elif sys.platform == "darwin":
                os.system(f"open '{file_path}'")
            else:
                os.system(f"xdg-open '{file_path}'")
        except Exception as e:
            QMessageBox.critical(self, "Ошибка", f"Не удалось открыть файл: {e}")

    def create_text_file(self):
        """Создать новый текстовый файл"""
        file_name, ok = QInputDialog.getText(
            self, "Новый файл", "Имя файла (с расширением):"
        )
        if ok and file_name:
            try:
                # Если не указано расширение, добавляем .txt
                if "." not in file_name:
                    file_name += ".txt"

                new_file = self.current_path / file_name

                # Проверяем, не существует ли файл
                if new_file.exists():
                    reply = QMessageBox.question(
                        self,
                        "Файл существует",
                        f"Файл {file_name} уже существует. Открыть для редактирования?",
                    )
                    if reply == QMessageBox.StandardButton.Yes:
                        self.edit_file(new_file)
                    return

                # Создаем пустой файл
                new_file.write_text("", encoding="utf-8")
                self.refresh()

                # Предлагаем открыть для редактирования
                reply = QMessageBox.question(
                    self,
                    "Файл создан",
                    f"Файл {file_name} создан. Открыть для редактирования?",
                )
                if reply == QMessageBox.StandardButton.Yes:
                    self.edit_file(new_file)

            except Exception as e:
                QMessageBox.critical(self, "Ошибка", f"Не удалось создать файл: {e}")

    def open_in_new_tab(self, path):
        """Открыть путь в новой вкладке"""
        if path.is_dir():
            self.add_new_tab(path)
        else:
            # Для файлов открываем папку, содержащую файл
            self.add_new_tab(path.parent)

    def open_in_vscode(self, path, is_folder=False):
        """Открыть файл или папку в VS Code"""
        try:
            import subprocess
            import shutil

            # Проверяем, установлен ли VS Code
            vscode_commands = ["code", "code.exe", "code.cmd"]
            vscode_path = None

            for cmd in vscode_commands:
                vscode_path = shutil.which(cmd)
                if vscode_path:
                    break

            if not vscode_path:
                # Пробуем стандартные пути установки VS Code
                possible_paths = [
                    r"C:\Users\{}\AppData\Local\Programs\Microsoft VS Code\Code.exe".format(
                        os.environ.get("USERNAME", "")
                    ),
                    r"C:\Program Files\Microsoft VS Code\Code.exe",
                    r"C:\Program Files (x86)\Microsoft VS Code\Code.exe",
                ]

                for possible_path in possible_paths:
                    if os.path.exists(possible_path):
                        vscode_path = possible_path
                        break

            if not vscode_path:
                QMessageBox.warning(
                    self,
                    "VS Code не найден",
                    "VS Code не найден в системе.\n\n"
                    "Убедитесь, что VS Code установлен и добавлен в PATH,\n"
                    "или установите VS Code с официального сайта:\n"
                    "https://code.visualstudio.com/",
                )
                return

            # Команда для запуска VS Code
            if is_folder:
                # Открываем папку
                command = [vscode_path, str(path)]
                success_message = f"🚩 Папка {path.name} открыта в VS Code"
            else:
                # Открываем файл
                command = [vscode_path, str(path)]
                success_message = f"🚩 Файл {path.name} открыт в VS Code"

            # Запускаем VS Code
            process = subprocess.Popen(
                command,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                creationflags=subprocess.CREATE_NO_WINDOW
                if sys.platform == "win32"
                else 0,
            )

            # Не ждем завершения процесса, так как VS Code должен остаться открытым
            self.parent_window.status_bar.showMessage(success_message, 3000)

        except subprocess.SubprocessError as e:
            QMessageBox.critical(
                self,
                "Ошибка запуска VS Code",
                f"Не удалось запустить VS Code:\n{str(e)}",
            )
        except Exception as e:
            QMessageBox.critical(
                self, "Ошибка", f"Произошла ошибка при открытии в VS Code:\n{str(e)}"
            )

    def sort_by_column(self, column, file_list):
        """Сортировка по столбцу при клике на заголовок"""
        current_tab = self.get_current_tab()
        if not current_tab:
            return

        # Если кликнули по тому же столбцу, меняем направление сортировки
        if getattr(current_tab, "sort_column", 0) == column:
            current_tab.sort_reverse = not getattr(current_tab, "sort_reverse", False)
        else:
            # Если это новый столбец, сортируем по возрастанию
            current_tab.sort_column = column
            current_tab.sort_reverse = False

        # Обновляем глобальные настройки панели
        self.sort_column = current_tab.sort_column
        self.sort_reverse = current_tab.sort_reverse

        # Обновляем визуальный индикатор сортировки в заголовке
        header = file_list.header()
        for i in range(header.count()):
            if i == column:
                if current_tab.sort_reverse:
                    header.setSortIndicator(i, Qt.SortOrder.DescendingOrder)
                else:
                    header.setSortIndicator(i, Qt.SortOrder.AscendingOrder)
            else:
                header.setSortIndicator(i, Qt.SortOrder.AscendingOrder)

        # Показываем индикатор сортировки
        header.setSortIndicatorShown(True)

        # Обновляем содержимое вкладки
        current_index = self.tab_widget.currentIndex()
        self.refresh_tab(current_index)

        # Показываем информацию о сортировке в статус баре
        column_names = ["имени", "расширению", "размеру", "дате"]
        direction = "убыванию" if current_tab.sort_reverse else "возрастанию"
        if column < len(column_names) and self.parent_window:
            self.parent_window.status_bar.showMessage(
                f"🚩 Сортировка по {column_names[column]} по {direction}", 3000
            )

    def populate_drives_combo(self, combo):
        """Заполнить комбобокс доступными дисками и системными папками"""
        combo.clear()

        try:
            # Добавляем системные папки Windows
            system_folders = self.get_system_folders()
            for folder_name, folder_path in system_folders:
                combo.addItem(folder_name, folder_path)

            # Добавляем разделитель
            combo.insertSeparator(combo.count())

            # Получаем все доступные диски
            partitions = psutil.disk_partitions()
            for partition in partitions:
                try:
                    # Проверяем, доступен ли диск
                    usage = psutil.disk_usage(partition.mountpoint)
                    drive_name = partition.device
                    if partition.fstype:
                        drive_label = f"💽 {drive_name} ({partition.fstype})"
                    else:
                        drive_label = f"💽 {drive_name}"

                    combo.addItem(drive_label, partition.device)
                except (PermissionError, OSError):
                    # Диск недоступен, но добавляем его в список
                    combo.addItem(
                        f"💽 {partition.device} (недоступен)", partition.device
                    )

        except Exception as e:
            logger.error(f"🆘 Ошибка получения списка дисков: {e}")
            # Добавляем диск C: по умолчанию
            combo.addItem("💽 C:\\", "C:\\")

    def get_system_folders(self):
        """Получить список системных папок Windows (упрощенная версия)"""
        system_folders = []

        try:
            # Безопасное получение папок пользователя
            try:
                desktop = QStandardPaths.writableLocation(
                    QStandardPaths.StandardLocation.DesktopLocation
                )
                if desktop and Path(desktop).exists():
                    system_folders.append(("🏠 Рабочий стол", desktop))
            except Exception:
                pass

            try:
                documents = QStandardPaths.writableLocation(
                    QStandardPaths.StandardLocation.DocumentsLocation
                )
                if documents and Path(documents).exists():
                    system_folders.append(("📄 Документы", documents))
            except Exception:
                pass

            try:
                downloads = QStandardPaths.writableLocation(
                    QStandardPaths.StandardLocation.DownloadLocation
                )
                if downloads and Path(downloads).exists():
                    system_folders.append(("⬇️ Загрузки", downloads))
            except Exception:
                pass

            # Папка пользователя
            try:
                user_home = str(Path.home())
                if Path(user_home).exists():
                    system_folders.append(("👤 Профиль пользователя", user_home))
            except Exception:
                pass

            # Основные системные папки (только если они существуют)
            system_paths = [
                ("⚙️ Program Files", "C:\\Program Files"),
                ("🪟 Windows", "C:\\Windows"),
            ]

            for name, path in system_paths:
                try:
                    if Path(path).exists():
                        system_folders.append((name, path))
                except Exception:
                    pass

        except Exception as e:
            logger.error(f"🆘 Ошибка получения системных папок: {e}")

        # Если ничего не получилось, добавляем хотя бы домашнюю папку
        if not system_folders:
            try:
                home_path = str(Path.home())
                system_folders.append(("👤 Домашняя папка", home_path))
            except Exception:
                pass

        return system_folders

    def change_drive_tab(self, index, drive_text):
        """Изменить диск в указанной вкладке"""
        try:
            if not drive_text:
                return

            tab_widget = self.tab_widget.widget(index)
            if not tab_widget:
                return

            combo = tab_widget.drives_combo
            if combo.signalsBlocked():
                # Если сигналы заблокированы, это программное изменение - игнорируем
                return

            current_index = combo.currentIndex()
            if current_index >= 0:
                drive_path = combo.itemData(current_index)
                if drive_path:
                    try:
                        new_path = Path(drive_path)
                        if new_path.exists():
                            tab_widget.current_path = new_path
                            self.current_path = tab_widget.current_path
                            self.refresh_tab(index)
                        else:
                            QMessageBox.warning(
                                self, "Ошибка", f"Путь {drive_path} недоступен"
                            )
                            # Возвращаем предыдущий выбор без рекурсии
                            combo.blockSignals(True)
                            self.update_drives_combo_selection(
                                combo, tab_widget.current_path
                            )
                            combo.blockSignals(False)
                    except Exception as e:
                        QMessageBox.critical(
                            self, "Ошибка", f"Не удалось перейти к {drive_path}: {e}"
                        )
                        # Возвращаем предыдущий выбор без рекурсии
                        combo.blockSignals(True)
                        self.update_drives_combo_selection(
                            combo, tab_widget.current_path
                        )
                        combo.blockSignals(False)
        except Exception as e:
            logger.error(f"🆘 Ошибка смены диска: {e}")

    def update_drives_combo_selection(self, combo, current_path):
        """Обновить выбор в комбобоксе дисков согласно текущему пути"""
        try:
            # Блокируем сигналы, чтобы избежать рекурсивных вызовов
            combo.blockSignals(True)

            current_path_str = str(current_path).replace("/", "\\").lower()

            # Ищем точное совпадение
            for i in range(combo.count()):
                item_data = combo.itemData(i)
                if item_data:
                    item_path_str = str(item_data).replace("/", "\\").lower()
                    if item_path_str == current_path_str:
                        combo.setCurrentIndex(i)
                        return

            # Ищем наилучшее совпадение среди родительских папок
            best_match_index = -1
            best_match_length = 0

            for i in range(combo.count()):
                item_data = combo.itemData(i)
                if not item_data:
                    continue

                item_path_str = str(item_data).replace("/", "\\").lower().rstrip("\\")

                # Проверяем, является ли item_path родительским для current_path
                if (
                    current_path_str.startswith(item_path_str + "\\")
                    or current_path_str == item_path_str
                ):
                    # Чем длиннее совпадение, тем более специфичная папка
                    if len(item_path_str) > best_match_length:
                        best_match_length = len(item_path_str)
                        best_match_index = i

            if best_match_index >= 0:
                combo.setCurrentIndex(best_match_index)
                return

            # Если не найдено, ищем диск
            if sys.platform == "win32" and len(current_path_str) >= 2:
                current_drive = current_path_str[:2] + "\\"  # например "c:\"
                for i in range(combo.count()):
                    item_data = combo.itemData(i)
                    if item_data:
                        item_drive = str(item_data).replace("/", "\\").lower()
                        if item_drive == current_drive:
                            combo.setCurrentIndex(i)
                            return

        except Exception as e:
            logger.error(f"Ошибка обновления выбора диска: {e}")
        finally:
            # Всегда разблокируем сигналы
            combo.blockSignals(False)

    def update_disk_info(self, tab_widget, path):
        """Обновить информацию о диске"""
        try:
            # Получаем корень диска
            if sys.platform == "win32":
                drive_root = str(path).split("\\")[0] + "\\"
            else:
                drive_root = "/"

            # Получаем информацию о диске
            usage = psutil.disk_usage(drive_root)

            total_gb = usage.total / (1024**3)
            free_gb = usage.free / (1024**3)
            used_gb = usage.used / (1024**3)
            free_percent = (usage.free / usage.total) * 100

            # Формируем строку с информацией
            info_text = f"💾 {drive_root} - Всего: {total_gb:.1f} ГБ | Свободно: {free_gb:.1f} ГБ ({free_percent:.1f}%) | Занято: {used_gb:.1f} ГБ"

            tab_widget.disk_info_label.setText(info_text)

            # Меняем цвет в зависимости от заполненности
            if free_percent < 10:
                color = "#E74C3C"  # Красный - критически мало места
            elif free_percent < 20:
                color = "#F39C12"  # Оранжевый - мало места
            else:
                color = "#27AE60"  # Зеленый - достаточно места

            tab_widget.disk_info_label.setStyleSheet(
                f"QLabel {{ font-size: 12px; font-weight: bold; color: {color}; }}"
            )

        except Exception as e:
            tab_widget.disk_info_label.setText(f"💾 Информация о диске недоступна: {e}")
            tab_widget.disk_info_label.setStyleSheet(
                "QLabel { font-size: 12px; font-weight: bold; color: #E74C3C; }"
            )

    def set_item_tooltip(self, item, path):
        """Установить всплывающую подсказку для элемента"""
        if not item or not path:
            return

        try:
            if not hasattr(path, "name") or path.name == "..":
                return

            # Формируем текст подсказки
            tooltip_lines = []

            # Основная информация
            if path.is_dir():
                tooltip_lines.append(f"📁 Папка: {path.name}")
                tooltip_lines.append(f"📍 Путь: {path}")

                # Пытаемся посчитать содержимое папки (быстро)
                try:
                    items = list(path.iterdir())
                    folders = sum(1 for item in items if item.is_dir())
                    files = sum(1 for item in items if item.is_file())
                    tooltip_lines.append(
                        f"📂 Содержимое: {folders} папок, {files} файлов"
                    )
                except (PermissionError, OSError):
                    tooltip_lines.append("📂 Содержимое: недоступно")

            else:
                tooltip_lines.append(f"📄 Файл: {path.name}")
                tooltip_lines.append(f"📍 Путь: {path}")

                # Расширение и тип
                if path.suffix:
                    tooltip_lines.append(f"🏷️ Расширение: {path.suffix}")

                # Размер файла
                try:
                    file_size = path.stat().st_size
                    tooltip_lines.append(f"📏 Размер: {self.format_size(file_size)}")
                except (PermissionError, OSError):
                    tooltip_lines.append("📏 Размер: недоступен")

                # MIME тип
                try:
                    from PyQt6.QtCore import QMimeDatabase

                    mime_db = QMimeDatabase()
                    mime_type = mime_db.mimeTypeForFile(str(path))
                    if mime_type.comment():
                        tooltip_lines.append(f"🗂️ Тип: {mime_type.comment()}")
                except:
                    pass

            # Даты
            try:
                stat_info = path.stat()
                from PyQt6.QtCore import QDateTime

                mod_time = QDateTime.fromSecsSinceEpoch(int(stat_info.st_mtime))
                tooltip_lines.append(
                    f"📅 Изменен: {mod_time.toString('dd.MM.yyyy hh:mm:ss')}"
                )

                if hasattr(stat_info, "st_birthtime"):  # macOS
                    birth_time = QDateTime.fromSecsSinceEpoch(
                        int(stat_info.st_birthtime)
                    )
                    tooltip_lines.append(
                        f"📅 Создан: {birth_time.toString('dd.MM.yyyy hh:mm:ss')}"
                    )
                elif hasattr(stat_info, "st_ctime"):  # Windows/Linux
                    create_time = QDateTime.fromSecsSinceEpoch(int(stat_info.st_ctime))
                    tooltip_lines.append(
                        f"📅 Создан: {create_time.toString('dd.MM.yyyy hh:mm:ss')}"
                    )

            except (PermissionError, OSError):
                tooltip_lines.append("📅 Даты: недоступны")

            # Атрибуты файла
            try:
                stat_info = path.stat()
                attributes = []

                if not (stat_info.st_mode & 0o200):  # Только для чтения
                    attributes.append("только чтение")
                if path.name.startswith("."):  # Скрытый файл
                    attributes.append("скрытый")
                if sys.platform == "win32":
                    try:
                        import stat

                        if (
                            hasattr(stat_info, "st_file_attributes")
                            and stat_info.st_file_attributes
                            & stat.FILE_ATTRIBUTE_SYSTEM
                        ):
                            attributes.append("системный")
                    except (AttributeError, ImportError):
                        pass

                if attributes:
                    tooltip_lines.append(f"⚙️ Атрибуты: {', '.join(attributes)}")

            except (PermissionError, OSError, AttributeError):
                pass

            # Устанавливаем подсказку для элемента
            tooltip_text = "\n".join(tooltip_lines)
            item.setToolTip(0, tooltip_text)  # Устанавливаем для первой колонки

        except Exception as e:
            logger.error(f"Ошибка создания подсказки: {e}")
            item.setToolTip(0, f"Ошибка получения информации: {e}")

    def open_with_dialog(self, file_path):
        """Создает подменю 'Открыть с помощью' с приложениями для Windows"""
        logger.info(f"Создание подменю 'Открыть с помощью' для файла: {file_path}")

        try:
            # Проверяем существование файла
            if not file_path.exists():
                QMessageBox.warning(
                    self, "Файл не найден", f"Файл {file_path} не существует"
                )
                return

            # Создаем подменю с приложениями
            menu = QMenu("Открыть с помощью", self)
            menu.setStyleSheet("""
                QMenu {
                    background-color: white;
                    border: 1px solid #cccccc;
                    border-radius: 4px;
                    padding: 5px;
                }
                QMenu::item {
                    padding: 8px 16px;
                    margin: 1px;
                    border-radius: 3px;
                }
                QMenu::item:selected {
                    background-color: #0078d4;
                    color: white;
                }
                QMenu::separator {
                    height: 1px;
                    background: #e1e1e1;
                    margin: 5px 0px;
                }
            """)

            # Получаем приложения, ассоциированные с типом файла
            associated_apps = self.get_file_associations(file_path)

            # Добавляем ассоциированные приложения
            if associated_apps:
                for app_name, app_path, is_default in associated_apps:
                    if is_default:
                        action_text = f"🔸 {app_name} (по умолчанию)"
                    else:
                        action_text = f"📝 {app_name}"

                    action = QAction(action_text, menu)
                    action.triggered.connect(
                        lambda checked, path=app_path: self.launch_application(
                            path, file_path
                        )
                    )
                    menu.addAction(action)

                menu.addSeparator()

            # Получаем популярные приложения
            popular_apps = self.get_popular_applications(file_path)

            # Добавляем популярные приложения
            for app_name, app_path, icon in popular_apps:
                action = QAction(f"{icon} {app_name}", menu)
                action.triggered.connect(
                    lambda checked, path=app_path: self.launch_application(
                        path, file_path
                    )
                )
                menu.addAction(action)

            menu.addSeparator()

            # Добавляем стандартные опции
            browse_action = QAction("📁 Выбрать другую программу...", menu)
            browse_action.triggered.connect(
                lambda: self.browse_for_application(file_path)
            )
            menu.addAction(browse_action)

            properties_action = QAction("⚙️ Свойства файла", menu)
            properties_action.triggered.connect(lambda: self.show_properties(file_path))
            menu.addAction(properties_action)

            # Показываем меню под курсором мыши
            cursor_pos = self.mapFromGlobal(self.cursor().pos())
            menu.exec(self.mapToGlobal(cursor_pos))

        except Exception as e:
            logger.error(
                f"🆘 Ошибка создания подменю 'Открыть с помощью': {e}", exc_info=True
            )
            QMessageBox.critical(self, "Ошибка", f"Не удалось создать подменю: {e}")

    def get_file_associations(self, file_path):
        """Получить приложения, ассоциированные с типом файла"""
        associations = []
        try:
            import winreg

            file_extension = file_path.suffix.lower()
            if not file_extension:
                return associations

            logger.debug(f"Поиск ассоциаций для расширения: {file_extension}")

            # Получаем тип файла из реестра
            try:
                with winreg.OpenKey(winreg.HKEY_CLASSES_ROOT, file_extension) as key:
                    file_type, _ = winreg.QueryValueEx(key, "")
                    logger.debug(f"Тип файла: {file_type}")

                    # Ищем приложение по умолчанию
                    try:
                        with winreg.OpenKey(
                            winreg.HKEY_CLASSES_ROOT,
                            f"{file_type}\\shell\\open\\command",
                        ) as cmd_key:
                            default_command, _ = winreg.QueryValueEx(cmd_key, "")
                            logger.debug(f"Команда по умолчанию: {default_command}")

                            app_path = self.extract_app_path_from_command(
                                default_command
                            )
                            if app_path and Path(app_path).exists():
                                app_name = self.get_app_name_from_path(app_path)
                                associations.append(
                                    (app_name, app_path, True)
                                )  # True = приложение по умолчанию
                    except (FileNotFoundError, OSError):
                        pass

                    # Ищем дополнительные ассоциации в OpenWith
                    try:
                        with winreg.OpenKey(
                            winreg.HKEY_CLASSES_ROOT, f"{file_type}\\shell"
                        ) as shell_key:
                            i = 0
                            while True:
                                try:
                                    action_name = winreg.EnumKey(shell_key, i)
                                    if (
                                        action_name != "open"
                                    ):  # Пропускаем уже обработанное "open"
                                        try:
                                            with winreg.OpenKey(
                                                shell_key, f"{action_name}\\command"
                                            ) as action_cmd_key:
                                                action_command, _ = winreg.QueryValueEx(
                                                    action_cmd_key, ""
                                                )
                                                app_path = (
                                                    self.extract_app_path_from_command(
                                                        action_command
                                                    )
                                                )
                                                if app_path and Path(app_path).exists():
                                                    app_name = (
                                                        self.get_app_name_from_path(
                                                            app_path
                                                        )
                                                    )
                                                    # Проверяем, не добавили ли уже это приложение
                                                    if not any(
                                                        assoc[1] == app_path
                                                        for assoc in associations
                                                    ):
                                                        associations.append(
                                                            (app_name, app_path, False)
                                                        )
                                        except (FileNotFoundError, OSError):
                                            pass
                                    i += 1
                                except OSError:
                                    break
                    except (FileNotFoundError, OSError):
                        pass

            except (FileNotFoundError, OSError):
                logger.debug(f"Ассоциации для {file_extension} не найдены")

            # Также проверяем OpenWithList для дополнительных ассоциаций
            try:
                with winreg.OpenKey(
                    winreg.HKEY_CLASSES_ROOT, f"{file_extension}\\OpenWithList"
                ) as list_key:
                    i = 0
                    while True:
                        try:
                            app_name = winreg.EnumKey(list_key, i)
                            if app_name.endswith(".exe"):
                                # Ищем полный путь к приложению
                                app_path = self.find_application_path(app_name)
                                if app_path and not any(
                                    assoc[1] == app_path for assoc in associations
                                ):
                                    display_name = self.get_app_name_from_path(app_path)
                                    associations.append((display_name, app_path, False))
                            i += 1
                        except OSError:
                            break
            except (FileNotFoundError, OSError):
                pass

        except Exception as e:
            logger.error(f"Ошибка получения ассоциаций файлов: {e}")

        logger.info(f"Найдено {len(associations)} ассоциированных приложений")
        return associations[:10]  # Ограничиваем список

    def get_popular_applications(self, file_path):
        """Получить список популярных приложений для типа файла"""
        file_extension = file_path.suffix.lower()
        mime_db = QMimeDatabase()
        mime_type = mime_db.mimeTypeForFile(str(file_path))

        popular_apps = []

        # Общие приложения для всех файлов
        general_apps = [
            ("Блокнот", "notepad.exe", "📝"),
            ("WordPad", "write.exe", "📄"),
            ("Проводник Windows", "explorer.exe", "📁"),
        ]

        # Специфичные приложения по типу файла
        if mime_type.name().startswith("image/") or file_extension in [
            ".jpg",
            ".jpeg",
            ".png",
            ".gif",
            ".bmp",
            ".ico",
            ".webp",
        ]:
            image_apps = [
                ("Paint", "mspaint.exe", "🎨"),
                ("Paint 3D", "ms-paint:", "🎭"),
                (
                    "Средство просмотра фотографий Windows",
                    'rundll32.exe "C:\\Program Files\\Windows Photo Viewer\\PhotoViewer.dll", ImageView_Fullscreen',
                    "🖼️",
                ),
            ]
            popular_apps.extend(image_apps)

        elif mime_type.name().startswith("text/") or file_extension in [
            ".txt",
            ".log",
            ".ini",
            ".cfg",
        ]:
            text_apps = [
                ("Notepad++", self.find_application_path("notepad++.exe"), "✏️"),
                ("Visual Studio Code", self.find_application_path("Code.exe"), "💻"),
            ]
            popular_apps.extend([app for app in text_apps if app[1]])

        elif file_extension in [".pdf"]:
            pdf_apps = [
                (
                    "Adobe Acrobat Reader",
                    self.find_application_path("AcroRd32.exe"),
                    "📕",
                ),
                ("Microsoft Edge", self.find_application_path("msedge.exe"), "🌐"),
                ("Chrome", self.find_application_path("chrome.exe"), "🌐"),
            ]
            popular_apps.extend([app for app in pdf_apps if app[1]])

        elif file_extension in [".mp3", ".wav", ".flac", ".m4a"]:
            audio_apps = [
                ("Windows Media Player", "wmplayer.exe", "🎵"),
                ("VLC Media Player", self.find_application_path("vlc.exe"), "🎶"),
            ]
            popular_apps.extend([app for app in audio_apps if app[1]])

        elif file_extension in [".mp4", ".avi", ".mkv", ".mov"]:
            video_apps = [
                ("Windows Media Player", "wmplayer.exe", "🎬"),
                ("VLC Media Player", self.find_application_path("vlc.exe"), "🎬"),
            ]
            popular_apps.extend([app for app in video_apps if app[1]])

        elif file_extension in [".zip", ".rar", ".7z"]:
            archive_apps = [
                ("7-Zip", self.find_application_path("7zFM.exe"), "📦"),
                ("WinRAR", self.find_application_path("WinRAR.exe"), "📦"),
            ]
            popular_apps.extend([app for app in archive_apps if app[1]])

        # Добавляем общие приложения
        popular_apps.extend(general_apps)

        # Проверяем существование приложений и возвращаем только существующие
        existing_apps = []
        for app_name, app_path, icon in popular_apps:
            if app_path and (
                Path(app_path).exists()
                or app_path.startswith("ms-")
                or "rundll32.exe" in app_path
            ):
                existing_apps.append((app_name, app_path, icon))

        return existing_apps[:8]  # Ограничиваем количество

    def extract_app_path_from_command(self, command):
        """Извлечь путь к приложению из команды реестра"""
        if not command:
            return None

        # Удаляем кавычки и параметры
        command = command.strip()

        # Если команда начинается с кавычек, извлекаем путь между ними
        if command.startswith('"'):
            end_quote = command.find('"', 1)
            if end_quote != -1:
                return command[1:end_quote]
        else:
            # Если нет кавычек, берем первое слово до пробела
            parts = command.split(" ")
            return parts[0] if parts else None

        return None

    def get_app_name_from_path(self, app_path):
        """Получить имя приложения из пути"""
        if not app_path:
            return "Неизвестное приложение"

        # Красивые имена для популярных приложений
        nice_names = {
            "notepad.exe": "Блокнот",
            "mspaint.exe": "Paint",
            "write.exe": "WordPad",
            "explorer.exe": "Проводник Windows",
            "chrome.exe": "Google Chrome",
            "firefox.exe": "Mozilla Firefox",
            "msedge.exe": "Microsoft Edge",
            "Code.exe": "Visual Studio Code",
            "notepad++.exe": "Notepad++",
            "vlc.exe": "VLC Media Player",
            "winrar.exe": "WinRAR",
            "7zFM.exe": "7-Zip",
            "Photoshop.exe": "Adobe Photoshop",
            "AcroRd32.exe": "Adobe Acrobat Reader",
            "EXCEL.EXE": "Microsoft Excel",
            "WINWORD.EXE": "Microsoft Word",
            "POWERPNT.EXE": "Microsoft PowerPoint",
            "wmplayer.exe": "Windows Media Player",
        }

        app_filename = Path(app_path).name
        return nice_names.get(app_filename, Path(app_path).stem)

    def find_application_path(self, app_filename):
        """Найти полный путь к приложению по имени файла"""
        if not app_filename:
            return None

        try:
            import shutil

            # Сначала проверяем через shutil.which
            app_path = shutil.which(app_filename)
            if app_path and Path(app_path).exists():
                return app_path

            # Проверяем в реестре App Paths
            import winreg

            try:
                with winreg.OpenKey(
                    winreg.HKEY_LOCAL_MACHINE,
                    f"SOFTWARE\\Microsoft\\Windows\\CurrentVersion\\App Paths\\{app_filename}",
                ) as key:
                    app_path, _ = winreg.QueryValueEx(key, "")
                    if app_path and Path(app_path).exists():
                        return app_path
            except (FileNotFoundError, OSError):
                pass

            # Также проверяем WOW6432Node для 32-битных приложений
            try:
                with winreg.OpenKey(
                    winreg.HKEY_LOCAL_MACHINE,
                    f"SOFTWARE\\WOW6432Node\\Microsoft\\Windows\\CurrentVersion\\App Paths\\{app_filename}",
                ) as key:
                    app_path, _ = winreg.QueryValueEx(key, "")
                    if app_path and Path(app_path).exists():
                        return app_path
            except (FileNotFoundError, OSError):
                pass

            # Проверяем стандартные папки
            standard_paths = [
                Path("C:\\Program Files"),
                Path("C:\\Program Files (x86)"),
                Path("C:\\Windows\\System32"),
                Path.home() / "AppData" / "Local" / "Programs",
            ]

            for base_path in standard_paths:
                if base_path.exists():
                    # Ищем рекурсивно (но не слишком глубоко)
                    for app_path in base_path.rglob(app_filename):
                        if app_path.is_file():
                            return str(app_path)

        except Exception as e:
            logger.error(f"Ошибка поиска приложения {app_filename}: {e}")

        return None

    def launch_application(self, app_path, file_path):
        """Запустить приложение с файлом"""
        try:
            logger.info(f"Запуск приложения: {app_path} с файлом: {file_path}")

            # Специальные случаи
            if app_path.startswith("ms-"):
                # Приложения Microsoft Store
                subprocess.Popen([app_path, str(file_path)], shell=True)
            elif "rundll32.exe" in app_path:
                # Специальные команды rundll32
                subprocess.Popen(
                    app_path.replace('""', '"') + f' "{file_path}"', shell=True
                )
            elif app_path == "explorer.exe":
                # Для Explorer открываем папку с файлом и выделяем файл
                subprocess.Popen([app_path, "/select,", str(file_path)])
            else:
                # Обычное приложение
                subprocess.Popen([app_path, str(file_path)])

            self.parent_window.status_bar.showMessage(
                f"🚩 Файл открыт: {self.get_app_name_from_path(app_path)}", 5000
            )
            logger.info(f"Приложение {app_path} успешно запущено")

        except Exception as e:
            logger.error(f"Ошибка запуска приложения {app_path}: {e}")
            QMessageBox.critical(
                self, "Ошибка", f"Не удалось запустить приложение: {e}"
            )

    def browse_for_application(self, file_path):
        """Выбрать другое приложение через диалог"""
        app_path, ok = QFileDialog.getOpenFileName(
            self,
            "Выберите приложение",
            "C:\\Program Files",
            "Исполняемые файлы (*.exe);;Все файлы (*.*)",
        )

        if ok and app_path:
            self.launch_application(app_path, file_path)

    def get_installed_applications(self):
        """Получить список установленных приложений для Windows"""
        apps = []
        try:
            import winreg

            # Поиск в реестре установленных программ
            registry_paths = [
                (
                    winreg.HKEY_LOCAL_MACHINE,
                    r"SOFTWARE\Microsoft\Windows\CurrentVersion\App Paths",
                ),
                (
                    winreg.HKEY_LOCAL_MACHINE,
                    r"SOFTWARE\WOW6432Node\Microsoft\Windows\CurrentVersion\App Paths",
                ),
            ]

            for hkey, path in registry_paths:
                try:
                    with winreg.OpenKey(hkey, path) as key:
                        i = 0
                        while True:
                            try:
                                app_key = winreg.EnumKey(key, i)
                                if app_key.endswith(".exe"):
                                    try:
                                        with winreg.OpenKey(key, app_key) as app_reg:
                                            app_path, _ = winreg.QueryValueEx(
                                                app_reg, ""
                                            )
                                            if Path(app_path).exists():
                                                app_name = self.get_app_name_from_path(
                                                    app_path
                                                )
                                                apps.append((app_name, app_path))
                                    except (FileNotFoundError, OSError):
                                        pass
                                i += 1
                            except OSError:
                                break
                except (FileNotFoundError, OSError):
                    continue

            # Удаляем дубликаты и сортируем
            apps = list(set(apps))
            apps.sort(key=lambda x: x[0].lower())

        except Exception as e:
            logger.warning(f"Ошибка получения списка приложений: {e}")

        return apps[:15]  # Ограничиваем список

    def parse_hdrop_bytes(self, hdrop_data):
        """Парсинг HDROP данных в формате bytes"""
        try:
            logger.debug(f"Получены HDROP данные, размер: {len(hdrop_data)} байт")

            # Читаем заголовок DROPFILES (20 байт)
            if len(hdrop_data) < 20:
                logger.error(
                    f"Недостаточно данных для заголовка DROPFILES: {len(hdrop_data)} байт"
                )
                QMessageBox.warning(
                    self, "Ошибка", "Неверный формат данных в буфере обмена"
                )
                return None

            # Парсим заголовок DROPFILES
            header = struct.unpack("<LLLLL", hdrop_data[:20])
            pfiles_offset = header[0]  # Смещение до списка файлов
            pt_x = header[1]  # Координата X
            pt_y = header[2]  # Координата Y
            fnc = header[3]  # Флаг неклиентской области
            fwide = header[4]  # Флаг Unicode

            logger.debug(
                f"Заголовок DROPFILES: pFiles={pfiles_offset}, pt=({pt_x},{pt_y}), fNC={fnc}, fWide={fwide}"
            )

            # Проверяем корректность смещения
            if pfiles_offset >= len(hdrop_data):
                logger.error(
                    f"Неверное смещение файлов: {pfiles_offset} >= {len(hdrop_data)}"
                )
                QMessageBox.warning(
                    self, "Ошибка", "Неверное смещение данных в буфере обмена"
                )
                return None

            # Получаем данные файлов
            file_data = hdrop_data[pfiles_offset:]
            logger.debug(f"Размер данных файлов: {len(file_data)} байт")

            if fwide:
                # Unicode строки (UTF-16LE)
                logger.debug("Декодируем файлы как UTF-16LE")
                try:
                    file_string = file_data.decode("utf-16le")
                    logger.debug(
                        f"Декодированная строка (первые 200 символов): {repr(file_string[:200])}"
                    )
                except UnicodeDecodeError as e:
                    logger.error(f"Ошибка декодирования UTF-16LE: {e}")
                    file_string = file_data.decode("utf-16le", errors="replace")
            else:
                # ANSI строки
                logger.debug("Декодируем файлы как ANSI (latin1)")
                file_string = file_data.decode("latin1", errors="replace")

            # Разделяем файлы по нулевым символам и очищаем от пустых
            file_list = []
            files_raw = file_string.split("\0")
            for f in files_raw:
                f_clean = f.strip()
                if f_clean and len(f_clean) > 1:  # Игнорируем очень короткие строки
                    file_list.append(f_clean)

            logger.info(f"Найдено {len(file_list)} файлов в буфере обмена (bytes)")
            for i, f in enumerate(file_list[:5]):  # Показываем первые 5 файлов
                logger.debug(f"Файл {i + 1}: {f}")

            if not file_list:
                logger.warning("Список файлов пуст после парсинга bytes")
                QMessageBox.information(
                    self, "Буфер пуст", "В буфере обмена нет файлов"
                )
                return None

            return file_list

        except Exception as parse_error:
            logger.error(f"Ошибка парсинга HDROP bytes: {parse_error}", exc_info=True)
            QMessageBox.critical(
                self, "Ошибка", f"Не удалось прочитать данные из буфера: {parse_error}"
            )
            return None

    def debug_clipboard_formats(self):
        """Диагностика форматов в буфере обмена"""
        try:
            if sys.platform == "win32":
                import win32clipboard
                import win32con

                win32clipboard.OpenClipboard()
                try:
                    logger.debug("=== Диагностика буфера обмена ===")

                    # Перечисляем все доступные форматы
                    format_id = 0
                    formats = []
                    while True:
                        format_id = win32clipboard.EnumClipboardFormats(format_id)
                        if format_id == 0:
                            break
                        try:
                            format_name = win32clipboard.GetClipboardFormatName(
                                format_id
                            )
                        except:
                            format_name = f"Format_{format_id}"
                        formats.append((format_id, format_name))
                        logger.debug(f"Формат {format_id}: {format_name}")

                    # Проверяем наличие CF_HDROP
                    if win32clipboard.IsClipboardFormatAvailable(win32con.CF_HDROP):
                        logger.debug("CF_HDROP доступен")
                        try:
                            data = win32clipboard.GetClipboardData(win32con.CF_HDROP)
                            logger.debug(
                                f"CF_HDROP размер данных: {len(data) if data else 'None'}"
                            )
                            if data and len(data) >= 4:
                                logger.debug(f"Первые 4 байта: {data[:4].hex()}")
                        except Exception as e:
                            logger.debug(f"Ошибка чтения CF_HDROP: {e}")
                    else:
                        logger.debug("CF_HDROP недоступен")

                    logger.debug("=== Конец диагностики ===")

                finally:
                    win32clipboard.CloseClipboard()
        except Exception as e:
            logger.error(f"Ошибка диагностики буфера: {e}")

    def copy_to_clipboard(self, path):
        """Копировать файл в буфер обмена"""
        logger.info(f"Копирование файла в буфер обмена: {path}")

        # Добавляем диагностику перед копированием
        self.debug_clipboard_formats()
        try:
            if sys.platform == "win32":
                # Для Windows копируем файл в системный буфер обмена
                try:
                    import win32clipboard
                    import win32con

                    logger.debug("Используем win32clipboard для копирования")

                    # Открываем буфер обмена
                    win32clipboard.OpenClipboard()
                    try:
                        win32clipboard.EmptyClipboard()

                        # Подготавливаем данные для CF_HDROP
                        file_path = str(path).replace("/", "\\")
                        logger.debug(f"Путь для копирования: {file_path}")

                        # Формируем структуру DROPFILES правильно
                        # Создаем заголовок DROPFILES (20 байт)
                        # Структура: pFiles(4) + pt.x(4) + pt.y(4) + fNC(4) + fWide(4)
                        header_size = 20

                        # Подготавливаем список файлов в UTF-16LE
                        # Файл + null-терминатор + еще один null для завершения списка
                        file_list_unicode = (file_path + "\0" + "\0").encode("utf-16le")

                        # Создаем заголовок DROPFILES
                        dropfiles_header = struct.pack(
                            "<LLLLL",
                            header_size,  # pFiles - смещение до списка файлов (20 байт)
                            0,  # pt.x - координата X (не используется)
                            0,  # pt.y - координата Y (не используется)
                            0,  # fNC - флаг неклиентской области (FALSE)
                            1,  # fWide - флаг Unicode (TRUE)
                        )

                        # Объединяем заголовок и данные
                        hdrop_data = dropfiles_header + file_list_unicode

                        logger.debug(f"Размер HDROP данных: {len(hdrop_data)} байт")
                        logger.debug(f"Заголовок: {dropfiles_header.hex()}")
                        logger.debug(
                            f"Данные файлов: {file_list_unicode.hex()[:100]}..."
                        )

                        # Проверяем корректность данных перед копированием
                        if len(hdrop_data) < 20:
                            raise Exception(
                                f"Некорректный размер HDROP данных: {len(hdrop_data)} байт"
                            )

                        # Копируем в буфер обмена
                        win32clipboard.SetClipboardData(win32con.CF_HDROP, hdrop_data)

                        self.parent_window.status_bar.showMessage(
                            f"🚩 Файл скопирован в буфер обмена", 3000
                        )
                        logger.info(
                            "Файл успешно скопирован в буфер обмена через win32clipboard"
                        )

                    finally:
                        win32clipboard.CloseClipboard()

                    # Диагностика после копирования
                    logger.debug("Диагностика после копирования:")
                    self.debug_clipboard_formats()

                except ImportError:
                    logger.warning("win32clipboard недоступен, используем PowerShell")
                    # Если нет pywin32, используем альтернативный метод через PowerShell
                    try:
                        # Экранируем путь для PowerShell
                        escaped_path = str(path).replace("'", "''")

                        # Используем PowerShell для копирования файла
                        ps_command = f"""
try {{
    Add-Type -AssemblyName System.Windows.Forms
    $files = [System.Collections.Specialized.StringCollection]::new()
    $files.Add('{escaped_path}')
    [System.Windows.Forms.Clipboard]::SetFileDropList($files)
    Write-Output "SUCCESS"
}} catch {{
    Write-Error $_.Exception.Message
    exit 1
}}
"""
                        logger.debug(f"PowerShell команда: {ps_command}")

                        result = subprocess.run(
                            [
                                "powershell",
                                "-WindowStyle",
                                "Hidden",
                                "-Command",
                                ps_command,
                            ],
                            capture_output=True,
                            text=True,
                            creationflags=subprocess.CREATE_NO_WINDOW,
                            timeout=10,
                        )

                        if result.returncode == 0:
                            self.parent_window.status_bar.showMessage(
                                f"🚩 Файл скопирован в буфер обмена", 2000
                            )
                            logger.info(
                                "Файл успешно скопирован в буфер обмена через PowerShell"
                            )
                        else:
                            logger.error(
                                f"🆘 PowerShell ошибка: stdout={result.stdout}, stderr={result.stderr}"
                            )
                            raise Exception(f"PowerShell ошибка: {result.stderr}")

                    except Exception as ps_error:
                        logger.error(f"🆘 PowerShell ошибка: {ps_error}")
                        # Если и PowerShell не работает, копируем путь
                        clipboard = QApplication.clipboard()
                        clipboard.setText(str(path))
                        self.parent_window.status_bar.showMessage(
                            f"🚩 Путь к файлу скопирован в буфер обмена", 3000
                        )
                        logger.info("Путь к файлу скопирован как текст")

            else:
                # Для Linux/macOS - копируем путь, так как файловые операции сложнее
                clipboard = QApplication.clipboard()
                clipboard.setText(str(path))
                self.parent_window.status_bar.showMessage(
                    f"Путь к файлу скопирован в буфер обмена", 2000
                )
                logger.info("Путь к файлу скопирован в буфер обмена (Linux/macOS)")

        except Exception as e:
            logger.error(f"🆘 Ошибка копирования в буфер: {e}", exc_info=True)
            QMessageBox.critical(self, "Ошибка", f"Не удалось скопировать в буфер: {e}")

    def copy_path_to_clipboard(self, path):
        """Копировать путь к файлу в буфер обмена"""
        try:
            clipboard = QApplication.clipboard()
            clipboard.setText(str(path))
            self.parent_window.status_bar.showMessage(
                f"🚩 Путь скопирован: {path}", 3000
            )
        except Exception as e:
            QMessageBox.critical(self, "Ошибка", f"Не удалось скопировать путь: {e}")

    def create_shortcut(self, file_path):
        """Создать ярлык для файла"""
        try:
            if sys.platform == "win32":
                # Для Windows создаем .lnk файл
                try:
                    import winreg
                    import win32com.client

                    # Спрашиваем где создать ярлык
                    shortcut_name, ok = QInputDialog.getText(
                        self,
                        "Создать ярлык",
                        "Имя ярлыка:",
                        text=f"{file_path.stem} - Ярлык",
                    )

                    if not ok or not shortcut_name:
                        return

                    # Создаем ярлык на рабочем столе
                    desktop = Path.home() / "Desktop"
                    if not desktop.exists():
                        desktop = Path.home() / "Рабочий стол"

                    shortcut_path = desktop / f"{shortcut_name}.lnk"

                    shell = win32com.client.Dispatch("WScript.Shell")
                    shortcut = shell.CreateShortCut(str(shortcut_path))
                    shortcut.Targetpath = str(file_path)
                    shortcut.WorkingDirectory = str(file_path.parent)
                    shortcut.save()

                    QMessageBox.information(
                        self,
                        "Успех",
                        f"Ярлык создан на рабочем столе:\n{shortcut_path}",
                    )

                except ImportError:
                    # Если нет win32com, используем альтернативный метод
                    QMessageBox.warning(
                        self,
                        "Ограничение",
                        "Для создания ярлыков требуется установить pywin32.\n"
                        "Используйте: pip install pywin32",
                    )
            else:
                # Для Linux создаем символическую ссылку
                shortcut_name, ok = QInputDialog.getText(
                    self,
                    "Создать ссылку",
                    "Имя ссылки:",
                    text=f"{file_path.stem}_ссылка",
                )

                if ok and shortcut_name:
                    shortcut_path = self.current_path / shortcut_name
                    shortcut_path.symlink_to(file_path)
                    self.refresh()
                    QMessageBox.information(
                        self, "Успех", f"Символическая ссылка создана: {shortcut_name}"
                    )

        except Exception as e:
            QMessageBox.critical(self, "Ошибка", f"Не удалось создать ярлык: {e}")

    def add_to_zip_archive(self, paths):
        """Добавить файлы/папки в ZIP архив"""
        try:
            import zipfile

            # Если передан один путь как Path объект, преобразуем в список
            if isinstance(paths, Path):
                paths = [paths]

            # Генерируем имя архива
            if len(paths) == 1:
                default_name = f"{paths[0].stem}.zip"
            else:
                default_name = f"archive_{len(paths)}_files.zip"

            # Спрашиваем имя архива
            archive_name, ok = QInputDialog.getText(
                self,
                "Создать ZIP архив",
                f"Имя архива для {len(paths)} элемент(ов):",
                text=default_name,
            )

            if not ok or not archive_name:
                return

            if not archive_name.endswith(".zip"):
                archive_name += ".zip"

            archive_path = self.current_path / archive_name

            # Проверяем, не существует ли архив
            if archive_path.exists():
                reply = QMessageBox.question(
                    self,
                    "Файл существует",
                    f"Архив {archive_name} уже существует. Перезаписать?",
                )
                if reply != QMessageBox.StandardButton.Yes:
                    return

            # Создаем архив
            with zipfile.ZipFile(archive_path, "w", zipfile.ZIP_DEFLATED) as zipf:
                for path in paths:
                    if path.is_file():
                        # Добавляем файл с его именем
                        zipf.write(path, path.name)
                    elif path.is_dir():
                        # Архивируем папку рекурсивно
                        for file_path in path.rglob("*"):
                            if file_path.is_file():
                                # Относительный путь от корневой папки
                                arc_name = file_path.relative_to(path.parent)
                                zipf.write(file_path, arc_name)

            self.refresh()

            if len(paths) == 1:
                QMessageBox.information(self, "Успех", f"Архив создан: {archive_name}")
            else:
                QMessageBox.information(
                    self,
                    "Успех",
                    f"Архив создан: {archive_name}\nДобавлено {len(paths)} элементов",
                )

        except Exception as e:
            QMessageBox.critical(self, "Ошибка", f"Не удалось создать архив: {e}")

    def browse_archive_contents(self, archive_path):
        """Просмотреть содержимое архива"""
        try:
            extension = archive_path.suffix.lower()

            # Создаем диалог просмотра архива
            dialog = ArchiveBrowserDialog(archive_path, self)
            dialog.exec()

        except Exception as e:
            QMessageBox.critical(self, "Ошибка", f"Не удалось открыть архив: {e}")

    def extract_from_archive(self, archive_path):
        """Извлечь файлы из архива"""
        try:
            # Определяем тип архива и метод извлечения
            extension = archive_path.suffix.lower()

            # Спрашиваем папку для извлечения
            extract_folder, ok = QInputDialog.getText(
                self, "Извлечь архив", "Папка для извлечения:", text=archive_path.stem
            )

            if not ok or not extract_folder:
                return

            extract_path = self.current_path / extract_folder
            extract_path.mkdir(exist_ok=True)

            if extension == ".zip":
                import zipfile

                with zipfile.ZipFile(archive_path, "r") as zipf:
                    zipf.extractall(extract_path)

            elif extension == ".rar":
                try:
                    import rarfile

                    with rarfile.RarFile(archive_path, "r") as rarf:
                        rarf.extractall(extract_path)
                except ImportError:
                    QMessageBox.warning(
                        self,
                        "Ограничение",
                        "Для работы с RAR архивами требуется установить rarfile.\n"
                        "Используйте: pip install rarfile",
                    )
                    return

            elif extension == ".7z":
                try:
                    import py7zr

                    with py7zr.SevenZipFile(archive_path, mode="r") as archive:
                        archive.extractall(extract_path)
                except ImportError:
                    QMessageBox.warning(
                        self,
                        "Ограничение",
                        "Для работы с 7Z архивами требуется установить py7zr.\n"
                        "Используйте: pip install py7zr",
                    )
                    return
            else:
                QMessageBox.warning(
                    self,
                    "Неподдерживаемый формат",
                    f"Формат {extension} не поддерживается",
                )
                return

            self.refresh()
            QMessageBox.information(
                self, "Успех", f"Архив извлечен в папку: {extract_folder}"
            )

        except Exception as e:
            QMessageBox.critical(self, "Ошибка", f"Не удалось извлечь архив: {e}")

    def paste_from_clipboard(self):
        """Вставить файлы из буфера обмена"""
        logger.info("Начинаем вставку файлов из буфера обмена")
        try:
            if sys.platform == "win32":
                try:
                    import win32clipboard
                    import win32con

                    logger.debug("Используем win32clipboard для вставки")

                    # Открываем буфер обмена
                    win32clipboard.OpenClipboard()

                    try:
                        # Проверяем, есть ли файлы в буфере обмена
                        if win32clipboard.IsClipboardFormatAvailable(win32con.CF_HDROP):
                            logger.debug("Найден формат CF_HDROP в буфере обмена")

                            # Получаем данные из буфера
                            hdrop_data = win32clipboard.GetClipboardData(
                                win32con.CF_HDROP
                            )

                            if hdrop_data is None:
                                logger.warning("Данные CF_HDROP пусты")
                                QMessageBox.information(
                                    self, "Буфер пуст", "В буфере обмена нет файлов"
                                )
                                return

                            logger.debug(f"Тип данных CF_HDROP: {type(hdrop_data)}")

                            # Проверяем тип данных - может быть tuple или bytes
                            if isinstance(hdrop_data, tuple):
                                # Если это tuple, извлекаем файлы напрямую
                                logger.debug("CF_HDROP данные получены как tuple")
                                file_list = list(hdrop_data)
                                logger.info(
                                    f"Найдено {len(file_list)} файлов в буфере обмена (tuple)"
                                )
                                for i, f in enumerate(
                                    file_list[:5]
                                ):  # Показываем первые 5 файлов
                                    logger.debug(f"Файл {i + 1}: {f}")

                                if not file_list:
                                    logger.warning("Список файлов пуст")
                                    QMessageBox.information(
                                        self, "Буфер пуст", "В буфере обмена нет файлов"
                                    )
                                    return

                            elif isinstance(hdrop_data, bytes):
                                # Если это bytes, парсим как раньше
                                logger.debug(
                                    "CF_HDROP данные получены как bytes, парсим структуру"
                                )
                                file_list = self.parse_hdrop_bytes(hdrop_data)
                                if not file_list:
                                    return

                            else:
                                logger.error(
                                    f"Неподдерживаемый тип данных CF_HDROP: {type(hdrop_data)}"
                                )
                                QMessageBox.warning(
                                    self,
                                    "Ошибка",
                                    f"Неподдерживаемый формат данных в буфере обмена: {type(hdrop_data)}",
                                )
                                return

                            # Подтверждение вставки
                            reply = QMessageBox.question(
                                self,
                                "Вставить файлы",
                                f"Вставить {len(file_list)} файл(ов) из буфера обмена в:\n{self.current_path}?",
                            )

                            if reply == QMessageBox.StandardButton.Yes:
                                logger.info("Пользователь подтвердил вставку файлов")
                                # Копируем файлы в текущую папку
                                successful_copies = 0
                                errors = []

                                for file_path in file_list:
                                    try:
                                        source_path = Path(file_path)
                                        logger.debug(
                                            f"Обрабатываем файл: {source_path}"
                                        )

                                        if not source_path.exists():
                                            error_msg = (
                                                f"{source_path.name}: файл не найден"
                                            )
                                            logger.warning(error_msg)
                                            errors.append(error_msg)
                                            continue

                                        target_path = (
                                            self.current_path / source_path.name
                                        )

                                        # Проверяем, не пытаемся ли мы скопировать файл сам в себя
                                        try:
                                            if (
                                                source_path.resolve()
                                                == target_path.resolve()
                                            ):
                                                error_msg = f"{source_path.name}: нельзя скопировать файл сам в себя"
                                                logger.warning(error_msg)
                                                errors.append(error_msg)
                                                continue
                                        except OSError:
                                            # Если не удается получить resolve(), продолжаем
                                            pass

                                        # Если файл существует, спрашиваем о замене
                                        if target_path.exists():
                                            replace_reply = QMessageBox.question(
                                                self,
                                                "Файл существует",
                                                f"Файл {source_path.name} уже существует. Заменить?",
                                                QMessageBox.StandardButton.Yes
                                                | QMessageBox.StandardButton.No
                                                | QMessageBox.StandardButton.Cancel,
                                            )
                                            if (
                                                replace_reply
                                                == QMessageBox.StandardButton.Cancel
                                            ):
                                                logger.info(
                                                    "Пользователь отменил операцию"
                                                )
                                                break
                                            elif (
                                                replace_reply
                                                == QMessageBox.StandardButton.No
                                            ):
                                                error_msg = f"{source_path.name}: файл уже существует (пропущен)"
                                                logger.info(error_msg)
                                                errors.append(error_msg)
                                                continue
                                            # Если Yes, продолжаем копирование

                                        # Выполняем копирование
                                        if source_path.is_dir():
                                            if target_path.exists():
                                                shutil.rmtree(target_path)
                                            shutil.copytree(
                                                str(source_path), str(target_path)
                                            )
                                            logger.info(
                                                f"Папка скопирована: {source_path} -> {target_path}"
                                            )
                                        else:
                                            shutil.copy2(
                                                str(source_path), str(target_path)
                                            )
                                            logger.info(
                                                f"Файл скопирован: {source_path} -> {target_path}"
                                            )

                                        successful_copies += 1

                                    except Exception as e:
                                        error_msg = f"{Path(file_path).name}: {str(e)}"
                                        logger.error(
                                            f"Ошибка копирования файла {file_path}: {e}"
                                        )
                                        errors.append(error_msg)

                                self.refresh()

                                # Показываем результат
                                if successful_copies > 0:
                                    status_msg = (
                                        f"🚩 Вставлено {successful_copies} файл(ов)"
                                    )
                                    self.parent_window.status_bar.showMessage(
                                        status_msg, 3000
                                    )
                                    logger.info(status_msg)

                                if errors:
                                    error_message = (
                                        f"Обработано {successful_copies} файлов.\nОшибки:\n"
                                        + "\n".join(errors[:5])
                                    )
                                    if len(errors) > 5:
                                        error_message += (
                                            f"\n...и еще {len(errors) - 5} ошибок"
                                        )
                                    logger.warning(f"Ошибки при вставке: {errors}")
                                    QMessageBox.warning(
                                        self,
                                        "Предупреждения при вставке",
                                        error_message,
                                    )
                        else:
                            # Проверяем, есть ли текст (возможно, путь к файлу)
                            logger.debug(
                                "CF_HDROP недоступен, проверяем текстовые форматы"
                            )
                            if win32clipboard.IsClipboardFormatAvailable(
                                win32con.CF_UNICODETEXT
                            ):
                                text_data = win32clipboard.GetClipboardData(
                                    win32con.CF_UNICODETEXT
                                )
                                logger.debug(
                                    f"Найден текст в буфере: {text_data[:100] if text_data else 'None'}..."
                                )

                                if (
                                    text_data
                                    and isinstance(text_data, str)
                                    and text_data.strip()
                                ):
                                    path_to_check = text_data.strip()
                                    if Path(path_to_check).exists():
                                        reply = QMessageBox.question(
                                            self,
                                            "Вставить файл",
                                            f"В буфере обмена найден путь к файлу.\nВставить файл:\n{path_to_check}\nв папку:\n{self.current_path}?",
                                        )

                                        if reply == QMessageBox.StandardButton.Yes:
                                            try:
                                                source_path = Path(path_to_check)
                                                target_path = (
                                                    self.current_path / source_path.name
                                                )

                                                if target_path.exists():
                                                    replace_reply = QMessageBox.question(
                                                        self,
                                                        "Файл существует",
                                                        f"Файл {source_path.name} уже существует. Заменить?",
                                                    )
                                                    if (
                                                        replace_reply
                                                        != QMessageBox.StandardButton.Yes
                                                    ):
                                                        return

                                                if source_path.is_dir():
                                                    if target_path.exists():
                                                        shutil.rmtree(target_path)
                                                    shutil.copytree(
                                                        str(source_path),
                                                        str(target_path),
                                                    )
                                                else:
                                                    shutil.copy2(
                                                        str(source_path),
                                                        str(target_path),
                                                    )

                                                self.refresh()
                                                self.parent_window.status_bar.showMessage(
                                                    f"🚩 Файл вставлен: {source_path.name}",
                                                    3000,
                                                )
                                                logger.info(
                                                    f"Файл вставлен из текста: {source_path}"
                                                )
                                            except Exception as copy_error:
                                                logger.error(
                                                    f"Ошибка копирования из текста: {copy_error}"
                                                )
                                                QMessageBox.critical(
                                                    self,
                                                    "Ошибка копирования",
                                                    f"Не удалось скопировать файл: {copy_error}",
                                                )
                                    else:
                                        logger.info(
                                            "В буфере обмена текст, но он не является путем к существующему файлу"
                                        )
                                        QMessageBox.information(
                                            self,
                                            "Буфер пуст",
                                            "В буфере обмена нет файлов для вставки",
                                        )
                                else:
                                    logger.info("В буфере обмена нет текста")
                                    QMessageBox.information(
                                        self,
                                        "Буфер пуст",
                                        "В буфере обмена нет файлов для вставки",
                                    )
                            else:
                                logger.info(
                                    "В буфере обмена нет поддерживаемых форматов"
                                )
                                QMessageBox.information(
                                    self,
                                    "Буфер пуст",
                                    "В буфере обмена нет файлов для вставки",
                                )

                    finally:
                        win32clipboard.CloseClipboard()

                except ImportError:
                    logger.warning(
                        "win32clipboard недоступен, используем fallback через Qt"
                    )
                    # Если нет pywin32, пробуем через Qt
                    clipboard = QApplication.clipboard()
                    text_data = clipboard.text()

                    if (
                        text_data
                        and text_data.strip()
                        and Path(text_data.strip()).exists()
                    ):
                        reply = QMessageBox.question(
                            self,
                            "Вставить файл",
                            f"В буфере обмена найден путь к файлу.\nВставить файл:\n{text_data}\nв папку:\n{self.current_path}?",
                        )

                        if reply == QMessageBox.StandardButton.Yes:
                            try:
                                source_path = Path(text_data.strip())
                                target_path = self.current_path / source_path.name

                                if target_path.exists():
                                    replace_reply = QMessageBox.question(
                                        self,
                                        "Файл существует",
                                        f"Файл {source_path.name} уже существует. Заменить?",
                                    )
                                    if replace_reply != QMessageBox.StandardButton.Yes:
                                        return

                                if source_path.is_dir():
                                    if target_path.exists():
                                        shutil.rmtree(target_path)
                                    shutil.copytree(str(source_path), str(target_path))
                                else:
                                    shutil.copy2(str(source_path), str(target_path))

                                self.refresh()
                                self.parent_window.status_bar.showMessage(
                                    f"🚩 Файл вставлен", 3000
                                )
                                logger.info("Файл вставлен через Qt clipboard")
                            except Exception as copy_error:
                                logger.error(f"Ошибка Qt clipboard: {copy_error}")
                                QMessageBox.critical(
                                    self,
                                    "Ошибка копирования",
                                    f"Не удалось скопировать файл: {copy_error}",
                                )
                    else:
                        QMessageBox.information(
                            self,
                            "Информация",
                            "Для полной поддержки вставки файлов из буфера обмена\n"
                            "рекомендуется установить pywin32:\n"
                            "pip install pywin32",
                        )
            else:
                # Для Linux/macOS - простая реализация через путь в тексте
                logger.info("Используем текстовый буфер для Linux/macOS")
                clipboard = QApplication.clipboard()
                text_data = clipboard.text()

                if text_data and text_data.strip() and Path(text_data.strip()).exists():
                    reply = QMessageBox.question(
                        self,
                        "Вставить файл",
                        f"В буфере обмена найден путь к файлу.\nВставить файл:\n{text_data}\nв папку:\n{self.current_path}?",
                    )

                    if reply == QMessageBox.StandardButton.Yes:
                        try:
                            source_path = Path(text_data.strip())
                            target_path = self.current_path / source_path.name

                            if target_path.exists():
                                replace_reply = QMessageBox.question(
                                    self,
                                    "Файл существует",
                                    f"Файл {source_path.name} уже существует. Заменить?",
                                )
                                if replace_reply != QMessageBox.StandardButton.Yes:
                                    return

                            if source_path.is_dir():
                                if target_path.exists():
                                    shutil.rmtree(target_path)
                                shutil.copytree(str(source_path), str(target_path))
                            else:
                                shutil.copy2(str(source_path), str(target_path))

                            self.refresh()
                            self.parent_window.status_bar.showMessage(
                                f"Файл вставлен", 2000
                            )
                            logger.info("Файл вставлен на Linux/macOS")
                        except Exception as copy_error:
                            logger.error(f"Ошибка на Linux/macOS: {copy_error}")
                            QMessageBox.critical(
                                self,
                                "Ошибка копирования",
                                f"Не удалось скопировать файл: {copy_error}",
                            )
                else:
                    QMessageBox.information(
                        self, "Буфер пуст", "В буфере обмена нет файлов для вставки"
                    )

        except Exception as e:
            logger.error(f"🆘 Общая ошибка вставки из буфера: {e}", exc_info=True)
            QMessageBox.critical(self, "Ошибка", f"Не удалось вставить из буфера: {e}")

    def show_properties(self, path):
        """Показать свойства файла/папки"""
        try:
            dialog = PropertiesDialog(path, self)
            dialog.exec()
        except Exception as e:
            QMessageBox.critical(self, "Ошибка", f"Не удалось показать свойства: {e}")

    def start_manual_drag(self, file_path):
        """Запустить ручную drag операцию для экспорта в другие приложения"""
        try:
            logger.info(f"Запуск ручного drag для файла: {file_path}")

            # Создаем MIME данные
            mime_data = QMimeData()

            # Добавляем URL файла
            file_url = QUrl.fromLocalFile(str(file_path))
            mime_data.setUrls([file_url])

            # Добавляем текстовое представление
            mime_data.setText(str(file_path))

            # Создаем drag объект
            drag = QDrag(self)
            drag.setMimeData(mime_data)

            # Создаем простую иконку для drag
            pixmap = QPixmap(100, 30)
            pixmap.fill(QColor(200, 200, 255, 180))
            painter = QPainter(pixmap)
            painter.setPen(Qt.GlobalColor.black)
            painter.drawText(5, 20, f"📄 {file_path.name}")
            painter.end()

            drag.setPixmap(pixmap)
            drag.setHotSpot(pixmap.rect().center())

            # Запускаем drag операцию
            result = drag.exec(
                Qt.DropAction.CopyAction | Qt.DropAction.MoveAction,
                Qt.DropAction.CopyAction,
            )

            if result == Qt.DropAction.CopyAction:
                self.parent_window.status_bar.showMessage(
                    f"🚩 Файл экспортирован: {file_path.name}", 3000
                )
                logger.info(f"Файл успешно экспортирован через drag: {file_path}")
            else:
                logger.info(f"Drag операция отменена или не принята")

        except Exception as e:
            logger.error(f"🆘 Ошибка ручного drag: {e}", exc_info=True)
            QMessageBox.critical(
                self, "Ошибка", f"Не удалось запустить drag операцию: {e}"
            )


class SettingsManager:
    """Менеджер настроек приложения"""

    def __init__(self):
        # Путь к файлу настроек в папке пользователя
        self.app_data_dir = Path(
            QStandardPaths.writableLocation(
                QStandardPaths.StandardLocation.AppDataLocation
            )
        )
        self.app_data_dir.mkdir(parents=True, exist_ok=True)
        self.settings_file = self.app_data_dir / "file_manager_settings.json"

        # Настройки по умолчанию
        self.default_settings = {
            "window_geometry": [100, 100, 1200, 800],
            "window_maximized": False,
            "color_scheme_enabled": True,
            "sort_column": 3,
            "splitter_sizes": [600, 600],
            "left_panel_tabs": [{"path": "C:\\", "name": "C:\\"}],
            "right_panel_tabs": [{"path": "C:\\", "name": "C:\\"}],
            "left_panel_active_tab": 0,
            "right_panel_active_tab": 0,
        }

    def load_settings(self):
        """Загрузить настройки из файла"""
        try:
            if self.settings_file.exists():
                with open(self.settings_file, "r", encoding="utf-8") as f:
                    settings = json.load(f)
                # Проверяем наличие всех необходимых ключей
                for key, default_value in self.default_settings.items():
                    if key not in settings:
                        settings[key] = default_value
                return settings
        except Exception as e:
            logger.error(f"Ошибка загрузки настроек: {e}")

        return self.default_settings.copy()

    def save_settings(self, settings):
        """Сохранить настройки в файл"""
        try:
            with open(self.settings_file, "w", encoding="utf-8") as f:
                json.dump(settings, f, indent=2, ensure_ascii=False)
        except Exception as e:
            logger.error(f"Ошибка сохранения настроек: {e}")


class DualPanelFileManager(QMainWindow):
    """Главное окно файлового менеджера"""

    def __init__(self):
        super().__init__()
        logger.info("Инициализация FileManager")

        # Включаем поддержку drag-and-drop для всего окна
        self.setAcceptDrops(True)

        # Инициализируем базовые настройки
        self.color_scheme_enabled = True  # Временное значение
        self.sort_column = 0  # Временное значение

        # Загружаем настройки из файла
        try:
            self.settings_manager = SettingsManager()
            self.settings = self.settings_manager.load_settings()
            logger.debug("Настройки загружены")

            # Обновляем настройки из загруженного файла
            self.color_scheme_enabled = self.settings.get("color_scheme_enabled", True)
            self.sort_column = self.settings.get("sort_column", 0)
        except Exception as e:
            logger.error(f"Ошибка загрузки настроек: {e}")
            # Используем настройки по умолчанию
            self.settings = {
                "window_geometry": [100, 100, 1200, 800],
                "window_maximized": False,
                "color_scheme_enabled": True,
                "sort_column": 3,
                "splitter_sizes": [600, 600],
                "left_panel_tabs": [{"path": "C:\\", "name": "C:\\"}],
                "right_panel_tabs": [{"path": "C:\\", "name": "C:\\"}],
                "left_panel_active_tab": 0,
                "right_panel_active_tab": 0,
            }

        # Отслеживание активной панели
        self.active_panel = None

        # Инициализация потоков
        self.file_thread = None

        self.setup_ui()
        self.setup_menu()
        self.setup_shortcuts()
        self.setup_header_sorting()  # Настраиваем сортировку после создания панелей
        self.restore_settings()  # Восстанавливаем настройки после создания интерфейса

        # Настраиваем порядок табуляции
        self.setup_tab_order()

        # Устанавливаем начальный фокус на левой панели
        if self.left_panel.get_current_tab():
            self.left_panel.get_current_tab().file_list.setFocus()
            self.left_panel.update_panel_styles(active=True)
            self.right_panel.update_panel_styles(active=False)
            self.active_panel = self.left_panel

    def setup_ui(self):
        self.setWindowTitle("Файловый менеджер")
        self.setWindowIcon(QIcon(os.path.join("images", "fc02.png")))
        self.setGeometry(100, 100, 1200, 800)
        # self.resize(1200, 800)
        self.setStyleSheet("""
                    QPushButton {
                        background-color: qlineargradient(x1: 0, y1: 0, x2: 0, y2: 1,
                                      stop: 0 #f6f7fa, stop: 1 #dadbde);
                        font-size: 12px;
                        font-weight: bold;
                        padding: 2px 6px;
                        border: 1px solid gray;
                        border-radius: 10px;
                    }
                    QPushButton:pressed {
                        background-color: qlineargradient(x1: 0, y1: 0, x2: 0, y2: 1,
                                      stop: 0 #dadbde, stop: 1 #f6f7fa);
                    }
                    QPushButton:hover {
                        background-color: qlineargradient(x1: 0, y1: 0, x2: 0, y2: 1,
                                      stop: 0 #dadbde, stop: 1 #f6f7fa);
                        color: #4F4F4F;
                    }
                    QTabWidget::tab-bar {
                        alignment: left;
                        
                    }
                    QTabBar::tab {
                        color: gray;
                        font: bold 12px;
                        background: qlineargradient(x1: 0, y1: 0, x2: 0, y2: 1,
                                                    stop: 0 #9E9E9E, stop: 0.4 #C0C0C0,
                                                    stop: 0.5 #C5C4C4, stop: 1.0 #9E9E9E);
                        border: 2px solid #C4C4C3;
                        border-bottom-color: #C2C7CB; /* same as the pane color */
                        border-top-left-radius: 10px;
                        border-top-right-radius: 10px;
                        min-width: 8ex;
                        padding: 2px;
                    }
                    QTabBar::tab:selected, QTabBar::tab:hover {
                        background: qlineargradient(x1: 0, y1: 0, x2: 0, y2: 1,
                                                    stop: 0 #C5C4C4, stop: 0.4 #f4f4f4,
                                                    stop: 0.5 #e7e7e7, stop: 1.0 #C5C4C4);
                        color: #4F4F4F;
                    }
                    QTabBar::tab:selected {
                        border-color: #9B9B9B;
                        border-bottom-color: #C2C7CB; /* same as pane color */
                        margin-left: -4px;
                        margin-right: -4px;
                    }
                    QTabBar::tab:!selected {
                        margin-top: 2px; /* make non-selected tabs look smaller */
                    }
                    
                    QTabBar::tab:first:selected {
                        margin-left: 0; /* the first selected tab has nothing to overlap with on the left */
                    }
                    
                    QTabBar::tab:last:selected {
                        margin-right: 0; /* the last selected tab has nothing to overlap with on the right */
                    }
                    QStatusBar {
                        font-size: 12px;
                        border: 1px solid gray;
                        border-radius: 7px;
                        padding: 2px 2px 2px 2px;
                    }
                    QProgressBar {
                        border: 2px solid grey;
                        border-radius: 5px;
                        text-align: center;
                        height: 10px;
                    }
                    QProgressBar::chunk {
                        background-color: #808080;
                        width: 10px;
                        margin: 0.5px;
                    }
                    QToolTip {
                        background-color: #FCF7ED;
                        color: blue;
                        border: 2px dashed #FF0000;
                        border-radius: 7px;
                        padding: 2px;
                        font: 10pt "Segoe UI";
                    }
                    """)

        # Центральный виджет
        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        # Главный layout
        main_layout = QVBoxLayout()

        # Разделитель для панелей
        self.splitter = QSplitter(Qt.Orientation.Horizontal)

        # Левая и правая панели (создаем без добавления вкладок)
        self.left_panel = FilePanel(self, create_default_tab=False)
        self.right_panel = FilePanel(self, create_default_tab=False)

        self.splitter.addWidget(self.left_panel)
        self.splitter.addWidget(self.right_panel)
        self.splitter.setSizes([600, 600])

        # Панель кнопок
        button_layout = QHBoxLayout()

        self.copy_button = QPushButton("F5 Копировать")
        self.copy_button.clicked.connect(self.copy_selected)

        self.move_button = QPushButton("F6 Переместить")
        self.move_button.clicked.connect(self.move_selected)

        self.delete_button = QPushButton("F8 Удалить")
        self.delete_button.clicked.connect(self.delete_selected)

        self.refresh_button = QPushButton("F2 Обновить")
        self.refresh_button.clicked.connect(self.refresh_panels)

        self.view_button = QPushButton("F3 Просмотр")
        self.view_button.clicked.connect(self.view_selected)

        self.edit_button = QPushButton("F4 Редактировать")
        self.edit_button.clicked.connect(self.edit_selected)

        self.mkdir_button = QPushButton("F7 Новая папка")
        self.mkdir_button.clicked.connect(self.create_folder_selected)

        self.search_button = QPushButton("Ctrl+F Поиск")
        self.search_button.clicked.connect(self.show_search_dialog)

        self.exit_button = QPushButton("F10 Выход")
        self.exit_button.clicked.connect(self.close)

        button_layout.addWidget(self.refresh_button)
        button_layout.addWidget(self.view_button)
        button_layout.addWidget(self.edit_button)
        button_layout.addWidget(self.copy_button)
        button_layout.addWidget(self.move_button)
        button_layout.addWidget(self.mkdir_button)
        button_layout.addWidget(self.delete_button)
        button_layout.addWidget(self.search_button)
        button_layout.addWidget(self.exit_button)

        # Статус бар
        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)

        # Прогресс бар
        self.progress_bar = QProgressBar()
        self.progress_bar.setFixedSize(300, 20)
        self.progress_bar.setAlignment(Qt.AlignmentFlag.AlignRight)
        self.progress_bar.setVisible(False)
        self.progress_bar.setTextVisible(True)
        self.progress_bar.setFormat("%p% - %v/%m")
        self.status_bar.addPermanentWidget(self.progress_bar)

        # Метка для отображения текущей операции
        self.progress_label = QLabel("⏳")
        self.progress_bar.setFixedSize(350, 20)
        self.progress_bar.setAlignment(Qt.AlignmentFlag.AlignLeft)
        self.progress_label.setVisible(False)
        self.status_bar.addWidget(self.progress_label)

        # Метка для отображения информации о drag-and-drop
        self.drag_info_label = QLabel(
            "💡 -  Drag&Drop: Ctrl+Drag - копировать, Shift+Drag - переместить"
        )
        self.drag_info_label.setStyleSheet(
            "QLabel { color: #666; font-size: 11px; border: 2px solid #ccc; }"
        )
        self.status_bar.addPermanentWidget(self.drag_info_label)

        main_layout.addWidget(self.splitter)
        main_layout.addLayout(button_layout)

        central_widget.setLayout(main_layout)

        self.status_bar.showMessage("⏳ Готов")

    def setup_header_sorting(self):
        """Настройка интерактивной сортировки по клику на заголовки"""
        # Сортировка теперь настраивается для каждой вкладки при ее создании
        pass

    def setup_menu(self):
        """Настройка меню"""
        menubar = self.menuBar()

        # Меню файл
        file_menu = menubar.addMenu("Файл")

        view_file_action = QAction(
            QIcon(os.path.join("images", "glass.png")), "Просмотр файла (F3)", self
        )
        view_file_action.triggered.connect(self.view_selected)
        file_menu.addAction(view_file_action)

        edit_file_action = QAction(
            QIcon(os.path.join("images", "edit.png")), "Редактировать файл (F4)", self
        )
        edit_file_action.triggered.connect(self.edit_selected)
        file_menu.addAction(edit_file_action)

        create_folder_action = QAction(
            QIcon(os.path.join("images", "folderadd.png")), "Создать папку (F7)", self
        )
        create_folder_action.triggered.connect(self.create_folder_selected)
        file_menu.addAction(create_folder_action)
        exit_action = QAction(
            QIcon(os.path.join("images", "door.png")), "Выход (Ctrl+Q)", self
        )
        exit_action.setShortcut(QKeySequence("Ctrl+Q"))
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)

        # Меню вид
        view_menu = menubar.addMenu("Вид")

        refresh_action = QAction(
            QIcon(os.path.join("images", "refresh.png")), "Обновить (F2)", self
        )
        refresh_action.triggered.connect(self.refresh_panels)
        view_menu.addAction(refresh_action)

        # Меню настроек
        settings_menu = menubar.addMenu("Настройки")

        self.toggle_colors_action = QAction("Цветовые схемы файлов", self)
        self.toggle_colors_action.setCheckable(True)
        self.toggle_colors_action.setChecked(self.color_scheme_enabled)
        self.toggle_colors_action.triggered.connect(self.toggle_file_colors)
        settings_menu.addAction(self.toggle_colors_action)

        # Настройки сортировки
        sort_menu = settings_menu.addMenu("Сортировка")

        sort_name_action = QAction(
            QIcon(os.path.join("images", "sortalpha.png")), "По имени", self
        )
        sort_name_action.triggered.connect(lambda: self.set_sort_mode(0))
        sort_menu.addAction(sort_name_action)

        sort_ext_action = QAction(
            QIcon(os.path.join("images", "casterisk.png")), "По расширению", self
        )
        sort_ext_action.triggered.connect(lambda: self.set_sort_mode(1))
        sort_menu.addAction(sort_ext_action)

        sort_size_action = QAction(
            QIcon(os.path.join("images", "sort.png")), "По размеру", self
        )
        sort_size_action.triggered.connect(lambda: self.set_sort_mode(2))
        sort_menu.addAction(sort_size_action)

        sort_date_action = QAction(
            QIcon(os.path.join("images", "sorttime.png")), "По дате", self
        )
        sort_date_action.triggered.connect(lambda: self.set_sort_mode(3))
        sort_menu.addAction(sort_date_action)

        # Меню окна
        window_menu = menubar.addMenu("Окно")

        maximize_action = QAction(
            QIcon(os.path.join("images", "maximize2.png")),
            "Максимизировать/Восстановить (Alt+Enter)",
            self,
        )
        maximize_action.triggered.connect(self.toggle_maximize)
        window_menu.addAction(maximize_action)

        fullscreen_action = QAction(
            QIcon(os.path.join("images", "maximize3.png")),
            "Полноэкранный режим (F11)",
            self,
        )
        fullscreen_action.triggered.connect(self.toggle_fullscreen)
        window_menu.addAction(fullscreen_action)

        # Меню вкладок
        tabs_menu = menubar.addMenu("Вкладки")

        new_tab_action = QAction(
            QIcon(os.path.join("images", "addtab.png")), "Новая вкладка", self
        )
        new_tab_action.triggered.connect(self.new_tab_in_active_panel)
        tabs_menu.addAction(new_tab_action)

        close_tab_action = QAction(
            QIcon(os.path.join("images", "close.png")), "Закрыть вкладку", self
        )
        close_tab_action.triggered.connect(self.close_active_tab)
        tabs_menu.addAction(close_tab_action)

        duplicate_tab_action = QAction(
            QIcon(os.path.join("images", "double.png")), "Дублировать вкладку", self
        )
        duplicate_tab_action.triggered.connect(self.duplicate_active_tab)
        tabs_menu.addAction(duplicate_tab_action)

        # Меню поиска
        search_menu = menubar.addMenu("Поиск")

        search_files_action = QAction("Найти файлы (Ctrl+F)", self)
        search_files_action.triggered.connect(self.show_search_dialog)
        search_menu.addAction(search_files_action)

        # Меню помощи
        help_menu = menubar.addMenu("Справка")

        drag_help_action = QAction(
            QIcon(os.path.join("images", "drag.png")),
            "Справка по Drag & Drop",
            self,
        )
        drag_help_action.triggered.connect(self.show_drag_help)
        help_menu.addAction(drag_help_action)

        shortcuts_help_action = QAction(
            QIcon(os.path.join("images", "key_.png")), "Горячие клавиши", self
        )
        shortcuts_help_action.triggered.connect(self.show_shortcuts_help)
        help_menu.addAction(shortcuts_help_action)

    def setup_shortcuts(self):
        """Настройка горячих клавиш"""
        # F2 - Обновить
        refresh_shortcut = QAction(self)
        refresh_shortcut.setShortcut(QKeySequence("F2"))
        refresh_shortcut.triggered.connect(self.refresh_panels)
        self.addAction(refresh_shortcut)

        # F3 - Просмотр
        view_shortcut = QAction(self)
        view_shortcut.setShortcut(QKeySequence("F3"))
        view_shortcut.triggered.connect(self.view_selected)
        self.addAction(view_shortcut)

        # F4 - Редактировать
        edit_shortcut = QAction(self)
        edit_shortcut.setShortcut(QKeySequence("F4"))
        edit_shortcut.triggered.connect(self.edit_selected)
        self.addAction(edit_shortcut)

        # F5 - Копировать
        copy_shortcut = QAction(self)
        copy_shortcut.setShortcut(QKeySequence("F5"))
        copy_shortcut.triggered.connect(self.copy_selected)
        self.addAction(copy_shortcut)

        # F6 - Переместить
        move_shortcut = QAction(self)
        move_shortcut.setShortcut(QKeySequence("F6"))
        move_shortcut.triggered.connect(self.move_selected)
        self.addAction(move_shortcut)

        # F7 - Создать папку
        mkdir_shortcut = QAction(self)
        mkdir_shortcut.setShortcut(QKeySequence("F7"))
        mkdir_shortcut.triggered.connect(self.create_folder_selected)
        self.addAction(mkdir_shortcut)

        # F8 - Удалить
        delete_shortcut = QAction(self)
        delete_shortcut.setShortcut(QKeySequence("F8"))
        delete_shortcut.triggered.connect(self.delete_selected)
        self.addAction(delete_shortcut)

        # Tab - Переключение между панелями
        tab_shortcut = QAction(self)
        tab_shortcut.setShortcut(QKeySequence("Tab"))
        tab_shortcut.triggered.connect(self.switch_panel)
        self.addAction(tab_shortcut)

        # Ctrl+1/2 - Переключение на левую/правую панель
        left_panel_shortcut = QAction(self)
        left_panel_shortcut.setShortcut(QKeySequence("Ctrl+1"))
        left_panel_shortcut.triggered.connect(self.activate_left_panel)
        self.addAction(left_panel_shortcut)

        right_panel_shortcut = QAction(self)
        right_panel_shortcut.setShortcut(QKeySequence("Ctrl+2"))
        right_panel_shortcut.triggered.connect(self.activate_right_panel)
        self.addAction(right_panel_shortcut)

        # Ctrl+Left/Right - Переключение между вкладками в активной панели
        prev_tab_shortcut = QAction(self)
        prev_tab_shortcut.setShortcut(QKeySequence("Ctrl+Left"))
        prev_tab_shortcut.triggered.connect(self.prev_tab_in_active_panel)
        self.addAction(prev_tab_shortcut)

        next_tab_shortcut = QAction(self)
        next_tab_shortcut.setShortcut(QKeySequence("Ctrl+Right"))
        next_tab_shortcut.triggered.connect(self.next_tab_in_active_panel)
        self.addAction(next_tab_shortcut)

        # Горячие клавиши для вкладок
        # Ctrl+T - Новая вкладка
        new_tab_shortcut = QAction(self)
        new_tab_shortcut.setShortcut(QKeySequence("Ctrl+T"))
        new_tab_shortcut.triggered.connect(self.new_tab_in_active_panel)
        self.addAction(new_tab_shortcut)

        # Ctrl+W - Закрыть вкладку
        close_tab_shortcut = QAction(self)
        close_tab_shortcut.setShortcut(QKeySequence("Ctrl+W"))
        close_tab_shortcut.triggered.connect(self.close_active_tab)
        self.addAction(close_tab_shortcut)

        # Ctrl+D - Дублировать вкладку
        duplicate_tab_shortcut = QAction(self)
        duplicate_tab_shortcut.setShortcut(QKeySequence("Ctrl+D"))
        duplicate_tab_shortcut.triggered.connect(self.duplicate_active_tab)
        self.addAction(duplicate_tab_shortcut)

        # F11 - Переключение полноэкранного режима
        fullscreen_shortcut = QAction(self)
        fullscreen_shortcut.setShortcut(QKeySequence("F11"))
        fullscreen_shortcut.triggered.connect(self.toggle_fullscreen)
        self.addAction(fullscreen_shortcut)

        # Alt+Enter - Переключение максимизации
        maximize_shortcut = QAction(self)
        maximize_shortcut.setShortcut(QKeySequence("Alt+Return"))
        maximize_shortcut.triggered.connect(self.toggle_maximize)
        self.addAction(maximize_shortcut)

        # Ctrl+Shift+D - Экспорт выбранного файла через drag-and-drop
        export_drag_shortcut = QAction(self)
        export_drag_shortcut.setShortcut(QKeySequence("Ctrl+Shift+D"))
        export_drag_shortcut.triggered.connect(self.export_selected_via_drag)
        self.addAction(export_drag_shortcut)

        # Ctrl+A - Выбрать все файлы в активной панели
        select_all_shortcut = QAction(self)
        select_all_shortcut.setShortcut(QKeySequence("Ctrl+A"))
        select_all_shortcut.triggered.connect(self.select_all_in_active_panel)
        self.addAction(select_all_shortcut)

        # Ctrl+F - Поиск файлов
        search_shortcut = QAction(self)
        search_shortcut.setShortcut(QKeySequence("Ctrl+F"))
        search_shortcut.triggered.connect(self.show_search_dialog)
        self.addAction(search_shortcut)

    def get_active_panel(self):
        """Получить активную панель"""
        # Используем сохраненную информацию об активной панели
        if self.active_panel:
            if self.active_panel == self.left_panel:
                logger.debug("Активная панель - ЛЕВАЯ (сохранено)")
                return self.left_panel, self.right_panel
            else:
                logger.debug("Активная панель - ПРАВАЯ (сохранено)")
                return self.right_panel, self.left_panel

        # Если не установлена, проверяем фокус
        left_tab = self.left_panel.get_current_tab()
        right_tab = self.right_panel.get_current_tab()

        if left_tab and left_tab.file_list.hasFocus():
            logger.debug("Активная панель - ЛЕВАЯ (по фокусу)")
            self.active_panel = self.left_panel
            return self.left_panel, self.right_panel
        elif right_tab and right_tab.file_list.hasFocus():
            logger.debug("Активная панель - ПРАВАЯ (по фокусу)")
            self.active_panel = self.right_panel
            return self.right_panel, self.left_panel

        # По умолчанию левая панель
        logger.debug("Активная панель - ЛЕВАЯ (по умолчанию)")
        self.active_panel = self.left_panel
        return self.left_panel, self.right_panel

    def get_panel_with_selection(self):
        """Получить панель с выбранными файлами и целевую панель"""
        logger.debug("get_panel_with_selection вызван")

        # Сначала проверяем активную панель
        active_panel, other_panel = self.get_active_panel()

        # Проверяем множественный выбор в активной панели
        active_selected = active_panel.get_selected_paths()
        if active_selected:
            logger.debug(
                f"Найден множественный выбор в активной панели: {len(active_selected)} файлов"
            )
            return active_panel, other_panel

        # Проверяем текущий элемент в активной панели
        active_current = active_panel.get_selected_path()
        if active_current and active_current.name != "..":
            logger.debug(
                f"Найден текущий элемент в активной панели: {active_current.name}"
            )
            return active_panel, other_panel

        # Проверяем другую панель
        other_selected = other_panel.get_selected_paths()
        if other_selected:
            logger.debug(
                f"Найден множественный выбор в другой панели: {len(other_selected)} файлов"
            )
            return other_panel, active_panel

        other_current = other_panel.get_selected_path()
        if other_current and other_current.name != "..":
            logger.debug(
                f"Найден текущий элемент в другой панели: {other_current.name}"
            )
            return other_panel, active_panel

        logger.debug("Нет выбранных файлов")
        # Если ничего не выбрано, возвращаем None
        return None, None

    def copy_selected(self):
        """Копировать выбранный файл"""
        logger.info("copy_selected вызван")
        # Определяем панель с выбранными файлами
        source_panel, target_panel = self.get_panel_with_selection()
        logger.debug(f"source_panel: {source_panel}, target_panel: {target_panel}")
        if source_panel:
            self.copy_file(source_panel, target_panel)
        else:
            QMessageBox.information(
                self, "Информация", "Нет выбранных файлов для копирования"
            )

    def move_selected(self):
        """Переместить выбранный файл"""
        logger.info("move_selected вызван")
        # Определяем панель с выбранными файлами
        source_panel, target_panel = self.get_panel_with_selection()
        if source_panel:
            self.move_file(source_panel, target_panel)
        else:
            QMessageBox.information(
                self, "Информация", "Нет выбранных файлов для перемещения"
            )

    def delete_selected(self):
        """Удалить выбранный файл"""
        logger.info("delete_selected вызван")
        # Определяем панель с выбранными файлами
        source_panel, _ = self.get_panel_with_selection()
        if source_panel:
            self.delete_file(source_panel)
        else:
            QMessageBox.information(
                self, "Информация", "Нет выбранных файлов для удаления"
            )

    def refresh_panels(self):
        """Обновить обе панели"""
        logger.info("refresh_panels вызван")
        self.left_panel.refresh()
        self.right_panel.refresh()
        self.status_bar.showMessage("Панели и список дисков обновлены", 3000)

    def view_selected(self):
        """Просмотр выбранного файла"""
        logger.info("view_selected вызван")
        # Сначала попробуем активную панель
        active_panel, _ = self.get_active_panel()

        # Проверяем, есть ли выбранные файлы в активной панели
        selected_path = active_panel.get_selected_path()

        if not selected_path or selected_path.name == "..":
            # Пробуем найти в любой панели
            source_panel, _ = self.get_panel_with_selection()
            if source_panel:
                selected_path = source_panel.get_selected_path()
            else:
                QMessageBox.information(
                    self, "Информация", "Выберите файл для просмотра"
                )
                return

        if not selected_path.is_file():
            QMessageBox.information(self, "Информация", "Выберите файл для просмотра")
            return

        logger.info(f"Просматриваем файл: {selected_path}")
        viewer = FileViewer(selected_path, self)
        viewer.exec()

    def edit_selected(self):
        """Редактирование выбранного файла"""
        logger.info("edit_selected вызван")
        # Сначала попробуем активную панель
        active_panel, _ = self.get_active_panel()

        # Проверяем, есть ли выбранные файлы в активной панели
        selected_path = active_panel.get_selected_path()

        if not selected_path or selected_path.name == "..":
            # Пробуем найти в любой панели
            source_panel, _ = self.get_panel_with_selection()
            if source_panel:
                selected_path = source_panel.get_selected_path()
                active_panel = source_panel
            else:
                QMessageBox.information(
                    self, "Информация", "Выберите файл для редактирования"
                )
                return

        if not selected_path.is_file():
            QMessageBox.information(
                self, "Информация", "Выберите файл для редактирования"
            )
            return

        logger.info(f"Редактируем файл: {selected_path}")
        editor = FileEditor(selected_path, self)
        editor.exec()
        active_panel.refresh()  # Обновляем панель после редактирования

    def create_folder_selected(self):
        """Создать папку в активной панели"""
        logger.info("create_folder_selected вызван")
        # Для создания папки используем активную панель (по фокусу)
        source_panel, _ = self.get_active_panel()
        logger.debug(f"Создание папки в панели: {source_panel}")
        source_panel.create_folder()

    def toggle_file_colors(self, enabled):
        """Переключить цветовые схемы файлов"""
        self.color_scheme_enabled = enabled
        self.left_panel.color_scheme_enabled = enabled
        self.right_panel.color_scheme_enabled = enabled
        self.refresh_panels()

    def set_sort_mode(self, column):
        """Установить режим сортировки"""
        self.sort_column = column
        self.left_panel.sort_column = column
        self.right_panel.sort_column = column

        # Обновляем настройки сортировки для всех вкладок
        for panel in [self.left_panel, self.right_panel]:
            for i in range(panel.tab_widget.count()):
                tab_widget = panel.tab_widget.widget(i)
                if tab_widget:
                    tab_widget.sort_column = column
                    tab_widget.sort_reverse = (
                        False  # Сбрасываем направление при смене столбца
                    )

        self.refresh_panels()

        # Показываем информацию о смене сортировки
        column_names = ["имени", "расширению", "размеру", "дате"]
        if column < len(column_names):
            self.status_bar.showMessage(
                f"🚩 Сортировка установлена по {column_names[column]}", 5000
            )

    def copy_file(self, source_panel, target_panel=None):
        """Копировать файл(ы)"""
        if target_panel is None:
            source_panel, target_panel = self.get_active_panel()

        selected_paths = source_panel.get_selected_paths()
        if not selected_paths:
            QMessageBox.information(
                self, "Информация", "Выберите файл(ы) для копирования"
            )
            return

        # Если выбран один файл
        if len(selected_paths) == 1:
            selected_path = selected_paths[0]
            target_path = target_panel.current_path / selected_path.name

            # Подтверждение копирования с указанием путей
            file_type = "папку" if selected_path.is_dir() else "файл"
            message = f"Копировать {file_type}:\n\nИз: {selected_path}\nВ: {target_path}\n\nПродолжить?"

            reply = QMessageBox.question(
                self,
                "Подтверждение копирования",
                message,
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            )
            if reply != QMessageBox.StandardButton.Yes:
                return

            if target_path.exists():
                replace_message = f"{file_type.capitalize()} {selected_path.name} уже существует в папке назначения.\n\nЗаменить?"
                replace_reply = QMessageBox.question(
                    self,
                    "Файл существует",
                    replace_message,
                    QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                )
                if replace_reply != QMessageBox.StandardButton.Yes:
                    return

            self.perform_file_operation(
                "copy", selected_path, target_path, target_panel
            )

        # Если выбрано несколько файлов
        else:
            message = f"Копировать {len(selected_paths)} выбранных элементов в:\n{target_panel.current_path}\n\nПродолжить?"
            reply = QMessageBox.question(
                self,
                "Подтверждение копирования",
                message,
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            )
            if reply != QMessageBox.StandardButton.Yes:
                return

            # Копируем файлы по одному
            self.perform_multiple_file_operations(
                "copy", selected_paths, target_panel, source_panel
            )

    def move_file(self, source_panel, target_panel=None):
        """Переместить файл(ы)"""
        if target_panel is None:
            source_panel, target_panel = self.get_active_panel()

        selected_paths = source_panel.get_selected_paths()
        if not selected_paths:
            QMessageBox.information(
                self, "Информация", "Выберите файл(ы) для перемещения"
            )
            return

        # Если выбран один файл
        if len(selected_paths) == 1:
            selected_path = selected_paths[0]
            target_path = target_panel.current_path / selected_path.name

            # Подтверждение перемещения с указанием путей
            file_type = "папку" if selected_path.is_dir() else "файл"
            message = f"Переместить {file_type}:\n\nИз: {selected_path}\nВ: {target_path}\n\nПродолжить?"

            reply = QMessageBox.question(
                self,
                "Подтверждение перемещения",
                message,
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            )
            if reply != QMessageBox.StandardButton.Yes:
                return

            if target_path.exists():
                replace_message = f"{file_type.capitalize()} {selected_path.name} уже существует в папке назначения.\n\nЗаменить?"
                replace_reply = QMessageBox.question(
                    self,
                    "Файл существует",
                    replace_message,
                    QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                )
                if replace_reply != QMessageBox.StandardButton.Yes:
                    return

            self.perform_file_operation(
                "move", selected_path, target_path, target_panel, source_panel
            )

        # Если выбрано несколько файлов
        else:
            message = f"Переместить {len(selected_paths)} выбранных элементов в:\n{target_panel.current_path}\n\nПродолжить?"
            reply = QMessageBox.question(
                self,
                "Подтверждение перемещения",
                message,
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            )
            if reply != QMessageBox.StandardButton.Yes:
                return

            # Перемещаем файлы по одному
            self.perform_multiple_file_operations(
                "move", selected_paths, target_panel, source_panel
            )

    def delete_file(self, source_panel):
        """Удалить файл(ы)"""
        selected_paths = source_panel.get_selected_paths()
        if not selected_paths:
            QMessageBox.information(self, "Информация", "Выберите файл(ы) для удаления")
            return

        # Если выбран один файл
        if len(selected_paths) == 1:
            selected_path = selected_paths[0]
            reply = QMessageBox.question(
                self, "Подтверждение", f"Удалить {selected_path.name}?"
            )
            if reply == QMessageBox.StandardButton.Yes:
                self.perform_file_operation(
                    "delete", selected_path, None, None, source_panel
                )

        # Если выбрано несколько файлов
        else:
            reply = QMessageBox.question(
                self,
                "Подтверждение",
                f"Удалить {len(selected_paths)} выбранных элементов?",
            )
            if reply == QMessageBox.StandardButton.Yes:
                self.perform_multiple_file_operations(
                    "delete", selected_paths, None, source_panel
                )

    def perform_file_operation(
        self, operation, source, destination, target_panel=None, source_panel=None
    ):
        """Выполнить операцию с файлом в отдельном потоке"""
        # Останавливаем предыдущий поток если он еще работает
        if (
            hasattr(self, "file_thread")
            and self.file_thread
            and self.file_thread.isRunning()
        ):
            self.file_thread.requestInterruption()
            self.file_thread.wait(1000)

        self.progress_bar.setVisible(True)
        self.progress_label.setVisible(True)
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setValue(0)

        self.file_thread = FileOperationThread(
            operation, str(source), str(destination) if destination else None
        )
        self.file_thread.progress.connect(self.progress_bar.setValue)
        self.file_thread.progress_text.connect(self.progress_label.setText)
        self.file_thread.finished.connect(
            lambda success, message: self.operation_finished(
                success, message, target_panel, source_panel
            )
        )

        # Обеспечиваем правильную очистку потока при завершении
        self.file_thread.finished.connect(self.file_thread.deleteLater)

        self.file_thread.start()

        operation_names = {
            "copy": "копирование",
            "move": "перемещение",
            "delete": "удаление",
        }
        self.status_bar.showMessage(
            f"⏳ Выполняется {operation_names.get(operation, operation)}..."
        )

    def operation_finished(self, success, message, target_panel, source_panel):
        """Обработка завершения операции с файлом"""
        self.progress_bar.setVisible(False)
        self.progress_label.setVisible(False)
        self.progress_bar.setValue(0)

        # Очищаем ссылку на поток
        if hasattr(self, "file_thread"):
            self.file_thread = None

        if success:
            self.status_bar.showMessage(message, 5000)
            if target_panel:
                target_panel.refresh()
            if source_panel:
                source_panel.refresh()
        else:
            QMessageBox.critical(self, "Ошибка", f"Ошибка операции: {message}")
            self.status_bar.showMessage("Ошибка операции", 3000)

    def perform_multiple_file_operations(
        self, operation, file_paths, target_panel, source_panel
    ):
        """Выполнить операции с несколькими файлами в одном потоке"""
        # Останавливаем любые активные потоки
        self.stop_all_threads()

        # Для операций копирования и перемещения проверяем конфликты заранее
        if operation in ["copy", "move"] and target_panel:
            conflicts = []
            non_conflicts = []

            # Проверяем каждый файл на конфликты
            for file_path in file_paths:
                target_path = target_panel.current_path / file_path.name

                # Проверяем, не пытаемся ли скопировать файл сам в себя
                try:
                    if file_path.resolve() == target_path.resolve():
                        logger.warning(
                            f"Пропускаем файл {file_path.name} (операция сам в себя)"
                        )
                        continue
                except OSError:
                    pass

                if target_path.exists():
                    conflicts.append((file_path, target_path))
                else:
                    non_conflicts.append(file_path)

            # Если есть конфликты, показываем диалог
            if conflicts:
                conflict_action = self.show_multiple_conflicts_dialog(
                    operation, conflicts
                )

                if conflict_action == "cancel":
                    logger.info("Операция отменена пользователем")
                    return
                elif conflict_action == "skip_all":
                    # Обрабатываем только файлы без конфликтов
                    file_paths = non_conflicts
                    logger.info(f"Пропускаем {len(conflicts)} существующих файлов")
                elif conflict_action == "replace_all":
                    # Обрабатываем все файлы (конфликтные будут заменены)
                    file_paths = file_paths  # Оставляем все как есть
                    logger.info(f"Заменяем {len(conflicts)} существующих файлов")
                elif conflict_action == "ask_each":
                    # Обрабатываем конфликты по одному
                    processed_files = []
                    processed_files.extend(
                        non_conflicts
                    )  # Добавляем файлы без конфликтов

                    for source_file, target_file in conflicts:
                        individual_action = self.show_individual_conflict_dialog(
                            operation, source_file, target_file
                        )

                        if individual_action == "cancel":
                            logger.info("Операция отменена пользователем")
                            return
                        elif individual_action == "replace":
                            processed_files.append(source_file)
                            logger.debug(f"Файл {source_file.name} будет заменен")
                        elif individual_action == "skip":
                            logger.debug(f"Файл {source_file.name} пропущен")
                            continue

                    file_paths = processed_files

            # Если после обработки конфликтов не осталось файлов для операции
            if not file_paths:
                QMessageBox.information(self, "Информация", "Нет файлов для обработки")
                return

        self.progress_bar.setVisible(True)
        self.progress_label.setVisible(True)
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setValue(0)

        # Создаем единый поток для множественных операций
        self.file_thread = MultipleFileOperationThread(
            operation, file_paths, target_panel.current_path if target_panel else None
        )

        self.file_thread.progress.connect(self.progress_bar.setValue)
        self.file_thread.progress_text.connect(self.progress_label.setText)
        self.file_thread.finished.connect(
            lambda success, message: self.multiple_operation_finished(
                success, message, target_panel, source_panel
            )
        )

        # Обеспечиваем правильную очистку потока при завершении
        self.file_thread.finished.connect(self.file_thread.deleteLater)

        self.file_thread.start()

        operation_names = {
            "copy": "копирование",
            "move": "перемещение",
            "delete": "удаление",
        }
        self.status_bar.showMessage(
            f"Выполняется {operation_names.get(operation, operation)} {len(file_paths)} файлов..."
        )

    def multiple_operation_finished(self, success, message, target_panel, source_panel):
        """Обработка завершения множественной операции"""
        self.progress_bar.setVisible(False)
        self.progress_label.setVisible(False)
        self.progress_bar.setValue(0)

        # Очищаем ссылку на поток
        if hasattr(self, "file_thread"):
            self.file_thread = None

        if success:
            self.status_bar.showMessage(message, 5000)
            if target_panel:
                target_panel.refresh()
            if source_panel:
                source_panel.refresh()
        else:
            QMessageBox.critical(self, "Ошибка", f"Ошибка операции: {message}")
            self.status_bar.showMessage("🆘 Ошибка операции", 3000)

    def show_multiple_conflicts_dialog(self, operation, conflicts):
        """Показать диалог для обработки множественных конфликтов файлов"""
        operation_text = "копировании" if operation == "copy" else "перемещении"

        conflict_message = f"При {operation_text} найдены существующие файлы:\n\n"

        # Показываем первые несколько конфликтных файлов
        for i, (source_file, target_file) in enumerate(conflicts[:5]):
            conflict_message += f"• {source_file.name}\n"

        if len(conflicts) > 5:
            conflict_message += f"... и еще {len(conflicts) - 5} файлов\n"

        conflict_message += f"\nВсего файлов: {len(conflicts)}\n\nВыберите действие:"

        # Создаем кастомный диалог с несколькими кнопками
        msg_box = QMessageBox(self)
        msg_box.setWindowTitle("Файлы существуют")
        msg_box.setText(conflict_message)
        msg_box.setIcon(QMessageBox.Icon.Question)

        # Добавляем кнопки с понятными названиями
        replace_all_btn = msg_box.addButton(
            "Заменить все", QMessageBox.ButtonRole.YesRole
        )
        skip_all_btn = msg_box.addButton(
            "Пропустить все", QMessageBox.ButtonRole.NoRole
        )
        ask_each_btn = msg_box.addButton(
            "Спрашивать для каждого", QMessageBox.ButtonRole.ActionRole
        )
        cancel_btn = msg_box.addButton("Отмена", QMessageBox.ButtonRole.RejectRole)

        msg_box.setDefaultButton(skip_all_btn)

        result = msg_box.exec()
        clicked_button = msg_box.clickedButton()

        if clicked_button == replace_all_btn:
            return "replace_all"
        elif clicked_button == skip_all_btn:
            return "skip_all"
        elif clicked_button == ask_each_btn:
            return "ask_each"
        else:  # cancel_btn или закрытие диалога
            return "cancel"

    def show_individual_conflict_dialog(self, operation, source_file, target_file):
        """Показать диалог для обработки индивидуального конфликта файла"""
        operation_text = "копировании" if operation == "copy" else "перемещении"

        try:
            # Получаем информацию о файлах
            source_stat = source_file.stat()
            target_stat = target_file.stat()

            from datetime import datetime

            source_date = datetime.fromtimestamp(source_stat.st_mtime).strftime(
                "%d.%m.%Y %H:%M:%S"
            )
            target_date = datetime.fromtimestamp(target_stat.st_mtime).strftime(
                "%d.%m.%Y %H:%M:%S"
            )

            source_size = self.format_size(source_stat.st_size)
            target_size = self.format_size(target_stat.st_size)

            conflict_message = f"Конфликт при {operation_text} файла:\n\n"
            conflict_message += f"📄 Файл: {source_file.name}\n\n"
            conflict_message += f"🔹 Исходный файл:\n"
            conflict_message += f"     Размер: {source_size}\n"
            conflict_message += f"     Дата: {source_date}\n"
            conflict_message += f"     Путь: {source_file.parent}\n\n"
            conflict_message += f"🔸 Существующий файл:\n"
            conflict_message += f"     Размер: {target_size}\n"
            conflict_message += f"     Дата: {target_date}\n"
            conflict_message += f"     Путь: {target_file.parent}\n\n"
            conflict_message += f"Что делать с этим файлом?"

        except (OSError, PermissionError):
            # Если не удается получить информацию о файлах
            conflict_message = f"Конфликт при {operation_text} файла:\n\n"
            conflict_message += f"📄 Файл: {source_file.name}\n\n"
            conflict_message += f"Файл уже существует в папке назначения.\n"
            conflict_message += f"Что делать с этим файлом?"

        # Создаем кастомный диалог
        msg_box = QMessageBox(self)
        msg_box.setWindowTitle(f"Файл существует: {source_file.name}")
        msg_box.setText(conflict_message)
        msg_box.setIcon(QMessageBox.Icon.Question)

        # Добавляем кнопки
        replace_btn = msg_box.addButton("Заменить", QMessageBox.ButtonRole.YesRole)
        skip_btn = msg_box.addButton("Пропустить", QMessageBox.ButtonRole.NoRole)
        cancel_btn = msg_box.addButton("Отмена", QMessageBox.ButtonRole.RejectRole)

        msg_box.setDefaultButton(skip_btn)

        result = msg_box.exec()
        clicked_button = msg_box.clickedButton()

        if clicked_button == replace_btn:
            return "replace"
        elif clicked_button == skip_btn:
            return "skip"
        else:  # cancel_btn или закрытие диалога
            return "cancel"

    def format_size(self, size):
        """Форматировать размер файла"""
        for unit in ["Б", "КБ", "МБ", "ГБ"]:
            if size < 1024:
                return f"{size:.1f} {unit}"
            size /= 1024
        return f"{size:.1f} ТБ"

    def new_tab_in_active_panel(self):
        """Создать новую вкладку в активной панели"""
        active_panel, _ = self.get_active_panel()
        active_panel.add_new_tab()

    def close_active_tab(self):
        """Закрыть активную вкладку"""
        active_panel, _ = self.get_active_panel()
        current_index = active_panel.tab_widget.currentIndex()
        active_panel.close_tab(current_index)

    def duplicate_active_tab(self):
        """Дублировать активную вкладку"""
        active_panel, _ = self.get_active_panel()
        current_index = active_panel.tab_widget.currentIndex()
        active_panel.duplicate_tab(current_index)

    def switch_panel(self):
        """Переключиться между левой и правой панелями"""
        logger.debug("switch_panel вызван")

        # Определяем текущую активную панель
        if self.active_panel == self.left_panel:
            # Переключаемся на правую панель
            target_panel = self.right_panel
            logger.debug("Переключение на ПРАВУЮ панель")
        else:
            # Переключаемся на левую панель
            target_panel = self.left_panel
            logger.debug("Переключение на ЛЕВУЮ панель")

        # Устанавливаем фокус на целевую панель
        target_tab = target_panel.get_current_tab()
        if target_tab and target_tab.file_list:
            target_tab.file_list.setFocus()
            # Активная панель будет установлена автоматически через on_focus_in

    def activate_left_panel(self):
        """Активировать левую панель"""
        logger.debug("Принудительная активация ЛЕВОЙ панели")
        left_tab = self.left_panel.get_current_tab()
        if left_tab and left_tab.file_list:
            left_tab.file_list.setFocus()

    def activate_right_panel(self):
        """Активировать правую панель"""
        logger.debug("Принудительная активация ПРАВОЙ панели")
        right_tab = self.right_panel.get_current_tab()
        if right_tab and right_tab.file_list:
            right_tab.file_list.setFocus()

    def prev_tab_in_active_panel(self):
        """Переключиться на предыдущую вкладку в активной панели"""
        active_panel, _ = self.get_active_panel()
        current_index = active_panel.tab_widget.currentIndex()
        if current_index > 0:
            active_panel.tab_widget.setCurrentIndex(current_index - 1)
            new_tab = active_panel.get_current_tab()
            if new_tab and new_tab.file_list:
                new_tab.file_list.setFocus()

    def next_tab_in_active_panel(self):
        """Переключиться на следующую вкладку в активной панели"""
        active_panel, _ = self.get_active_panel()
        current_index = active_panel.tab_widget.currentIndex()
        if current_index < active_panel.tab_widget.count() - 1:
            active_panel.tab_widget.setCurrentIndex(current_index + 1)
            new_tab = active_panel.get_current_tab()
            if new_tab and new_tab.file_list:
                new_tab.file_list.setFocus()

    def restore_settings(self):
        """Восстановить настройки приложения"""
        try:
            # Устанавливаем флаг восстановления настроек
            self._restoring_settings = True
            logger.info("Начало восстановления настроек")

            # Восстанавливаем геометрию окна
            geometry = self.settings.get("window_geometry", [100, 100, 1200, 800])
            is_maximized = self.settings.get("window_maximized", False)

            # Сначала устанавливаем обычную геометрию
            self.setGeometry(*geometry)

            # Затем максимизируем, если было максимизировано
            if is_maximized:
                self.showMaximized()

            # Восстанавливаем размеры разделителя
            splitter_sizes = self.settings.get("splitter_sizes", [600, 600])
            self.splitter.setSizes(splitter_sizes)

            # Обновляем состояние чекбокса цветовой схемы (настройки уже загружены в __init__)
            if hasattr(self, "toggle_colors_action"):
                self.toggle_colors_action.setChecked(self.color_scheme_enabled)

            # Восстанавливаем вкладки левой панели
            left_tabs = self.settings.get(
                "left_panel_tabs", [{"path": "C:\\", "name": "C:\\"}]
            )
            self.restore_panel_tabs(self.left_panel, left_tabs)
            left_active_tab = self.settings.get("left_panel_active_tab", 0)
            if 0 <= left_active_tab < self.left_panel.tab_widget.count():
                self.left_panel.tab_widget.setCurrentIndex(left_active_tab)

            # Восстанавливаем вкладки правой панели
            right_tabs = self.settings.get(
                "right_panel_tabs", [{"path": "C:\\", "name": "C:\\"}]
            )
            self.restore_panel_tabs(self.right_panel, right_tabs)
            right_active_tab = self.settings.get("right_panel_active_tab", 0)
            if 0 <= right_active_tab < self.right_panel.tab_widget.count():
                self.right_panel.tab_widget.setCurrentIndex(right_active_tab)

            # Применяем настройки к панелям
            self.left_panel.color_scheme_enabled = self.color_scheme_enabled
            self.right_panel.color_scheme_enabled = self.color_scheme_enabled
            self.left_panel.sort_column = self.sort_column
            self.right_panel.sort_column = self.sort_column

            # Снимаем флаг восстановления настроек
            self._restoring_settings = False
            logger.info("Восстановление настроек завершено")

        except Exception as e:
            logger.error(f"Ошибка восстановления настроек: {e}")
            # Снимаем флаг даже при ошибке
            self._restoring_settings = False
            # В случае ошибки создаем хотя бы одну вкладку в каждой панели
            if self.left_panel.tab_widget.count() == 0:
                self.left_panel.add_new_tab()
            if self.right_panel.tab_widget.count() == 0:
                self.right_panel.add_new_tab()

    def restore_panel_tabs(self, panel, tabs_data):
        """Восстановить вкладки для панели"""
        try:
            for i, tab_data in enumerate(tabs_data):
                path_str = tab_data.get("path", "C:\\")
                path = Path(path_str)

                # Проверяем, существует ли путь
                if not path.exists():
                    path = Path("C:\\")  # Если путь не существует, используем C:\

                logger.debug(f"Восстанавливаем вкладку {i + 1}: {path}")

                # Создаем вкладку с правильным путем
                tab_index = panel.add_new_tab(path)

                # Принудительно устанавливаем правильный путь после создания
                if tab_index is not None:
                    tab_widget = panel.tab_widget.widget(tab_index)
                    if tab_widget:
                        tab_widget.current_path = path
                        panel.current_path = path  # Также обновляем текущий путь панели
                        logger.debug(
                            f"Путь установлен для вкладки {tab_index}: {tab_widget.current_path}"
                        )

                        # Обновляем метку пути
                        if hasattr(tab_widget, "path_label"):
                            tab_widget.path_label.setText(str(path))

                        # Обновляем название вкладки
                        tab_name = path.name if path.name else path.as_posix()
                        if not tab_name or tab_name == ".":
                            tab_name = (
                                str(path)[:3] if len(str(path)) >= 3 else str(path)
                            )
                        panel.tab_widget.setTabText(tab_index, tab_name)

        except Exception as e:
            logger.error(f"Ошибка восстановления вкладок: {e}")
            # В случае ошибки создаем хотя бы одну вкладку по умолчанию
            if panel.tab_widget.count() == 0:
                panel.add_new_tab()

    def save_current_settings(self):
        """Сохранить текущие настройки"""
        try:
            # Сохраняем состояние максимизации
            self.settings["window_maximized"] = self.isMaximized()

            # Сохраняем геометрию окна (но только если окно не максимизировано)
            if not self.isMaximized():
                geometry = self.geometry()
                self.settings["window_geometry"] = [
                    geometry.x(),
                    geometry.y(),
                    geometry.width(),
                    geometry.height(),
                ]

            # Сохраняем размеры разделителя
            self.settings["splitter_sizes"] = self.splitter.sizes()

            # Сохраняем настройки цветовой схемы и сортировки
            self.settings["color_scheme_enabled"] = self.color_scheme_enabled
            self.settings["sort_column"] = self.sort_column

            # Сохраняем вкладки левой панели
            self.settings["left_panel_tabs"] = self.get_panel_tabs_data(self.left_panel)
            self.settings["left_panel_active_tab"] = (
                self.left_panel.tab_widget.currentIndex()
            )

            # Сохраняем вкладки правой панели
            self.settings["right_panel_tabs"] = self.get_panel_tabs_data(
                self.right_panel
            )
            self.settings["right_panel_active_tab"] = (
                self.right_panel.tab_widget.currentIndex()
            )

            # Сохраняем в файл
            self.settings_manager.save_settings(self.settings)

        except Exception as e:
            logger.error(f"🆘 Ошибка сохранения настроек: {e}")

    def setup_tab_order(self):
        """Настройка порядка табуляции"""
        # Отключаем стандартную табуляцию для большинства элементов
        # Оставляем только для списков файлов в панелях

        # Для левой панели
        left_tab = self.left_panel.get_current_tab()
        if left_tab:
            left_tab.file_list.setFocusPolicy(Qt.FocusPolicy.StrongFocus)

        # Для правой панели
        right_tab = self.right_panel.get_current_tab()
        if right_tab:
            right_tab.file_list.setFocusPolicy(Qt.FocusPolicy.StrongFocus)

        # Отключаем фокус для кнопок (чтобы Tab их пропускал)
        buttons = [
            self.copy_button,
            self.move_button,
            self.delete_button,
            self.refresh_button,
            self.view_button,
            self.edit_button,
            self.mkdir_button,
        ]

        for button in buttons:
            button.setFocusPolicy(Qt.FocusPolicy.NoFocus)

        # Также отключаем фокус для элементов вкладок
        self.left_panel.tab_widget.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self.right_panel.tab_widget.setFocusPolicy(Qt.FocusPolicy.NoFocus)

        # Отключаем фокус для кнопок управления вкладками
        if hasattr(self.left_panel, "new_tab_button"):
            self.left_panel.new_tab_button.setFocusPolicy(Qt.FocusPolicy.NoFocus)
            self.left_panel.select_mask_button.setFocusPolicy(Qt.FocusPolicy.NoFocus)

        if hasattr(self.right_panel, "new_tab_button"):
            self.right_panel.new_tab_button.setFocusPolicy(Qt.FocusPolicy.NoFocus)
            self.right_panel.select_mask_button.setFocusPolicy(Qt.FocusPolicy.NoFocus)

    def get_panel_tabs_data(self, panel):
        """Получить данные о вкладках панели"""
        tabs_data = []
        try:
            for i in range(panel.tab_widget.count()):
                tab_widget = panel.tab_widget.widget(i)
                if tab_widget and hasattr(tab_widget, "current_path"):
                    path_str = str(tab_widget.current_path)
                    tab_name = panel.tab_widget.tabText(i)
                    tabs_data.append({"path": path_str, "name": tab_name})
        except Exception as e:
            logger.error(f"Ошибка получения данных вкладок: {e}")

        # Если нет вкладок, добавляем хотя бы одну по умолчанию
        if not tabs_data:
            tabs_data.append({"path": "C:\\", "name": "C:\\"})

        return tabs_data

    def toggle_fullscreen(self):
        """Переключение полноэкранного режима"""
        if self.isFullScreen():
            self.showNormal()
            self.status_bar.showMessage("🚩 Полноэкранный режим отключен", 3000)
        else:
            self.showFullScreen()
            self.status_bar.showMessage(
                "🚩 Полноэкранный режим включен (F11 для выхода)", 5000
            )

    def toggle_maximize(self):
        """Переключение максимизации окна"""
        if self.isMaximized():
            self.showNormal()
            self.status_bar.showMessage("🚩 Окно восстановлено", 3000)
        else:
            self.showMaximized()
            self.status_bar.showMessage("🚩 Окно максимизировано", 3000)

    def export_selected_via_drag(self):
        """Экспорт выбранного файла через drag-and-drop"""
        active_panel, _ = self.get_active_panel()
        selected_path = active_panel.get_selected_path()

        if not selected_path or selected_path.name == "..":
            QMessageBox.information(self, "Информация", "Выберите файл для экспорта")
            return

        # Запускаем drag операцию
        active_tab = active_panel.get_current_tab()
        if active_tab and active_tab.file_list:
            active_panel.start_manual_drag(selected_path)

    def select_all_in_active_panel(self):
        """Выбрать все файлы в активной панели"""
        active_panel, _ = self.get_active_panel()
        active_tab = active_panel.get_current_tab()

        if not active_tab or not active_tab.file_list:
            return

        # Выбираем все элементы, кроме ".."
        file_list = active_tab.file_list
        selected_count = 0

        for i in range(file_list.topLevelItemCount()):
            item = file_list.topLevelItem(i)
            path = item.data(0, Qt.ItemDataRole.UserRole)

            if path and path.name != "..":
                item.setSelected(True)
                selected_count += 1
            else:
                item.setSelected(False)

        self.status_bar.showMessage(f"🚩 Выбрано всех файлов: {selected_count}", 3000)

    def show_search_dialog(self):
        """Показать диалог поиска файлов"""
        active_panel, _ = self.get_active_panel()
        current_path = active_panel.current_path

        search_dialog = SearchDialog(current_path, self)
        search_dialog.exec()

    def changeEvent(self, event):
        """Обработка изменения состояния окна"""
        if event.type() == event.Type.WindowStateChange:
            # Проверяем, было ли окно свернуто
            if self.windowState() & Qt.WindowState.WindowMinimized:
                self.was_minimized = True
                logger.debug("Окно свернуто")
            else:
                # Окно развернуто из свернутого состояния
                if self.was_minimized:
                    logger.info(
                        "Окно развернуто из свернутого состояния - обновляем панели"
                    )
                    self.refresh_panels_auto("Развернуто из свернутого состояния")
                    self.was_minimized = False

        super().changeEvent(event)

    def focusInEvent(self, event):
        """Обработка получения фокуса главным окном"""
        # Окно стало активным
        if self.was_inactive:
            logger.info("Главное окно получило фокус - обновляем панели")
            self.refresh_panels_auto("Окно получило фокус")
            self.was_inactive = False

        super().focusInEvent(event)

    def focusOutEvent(self, event):
        """Обработка потери фокуса главным окном"""
        # Окно стало неактивным
        self.was_inactive = True
        logger.debug("Главное окно потеряло фокус")
        super().focusOutEvent(event)

    def activationChange(self, active):
        """Дополнительная обработка активации окна (для старых версий Qt)"""
        if active and self.was_inactive:
            logger.info("Главное окно активировано - обновляем панели")
            self.refresh_panels_auto("Окно активировано")
            self.was_inactive = False
        elif not active:
            self.was_inactive = True

    def refresh_panels_auto(self, reason=""):
        """Автоматическое обновление панелей с логированием причины"""
        try:
            logger.info(f"Автообновление панелей: {reason}")
            self.left_panel.refresh()
            self.right_panel.refresh()
            self.status_bar.showMessage(
                f"Панели обновлены автоматически: {reason}", 3000
            )
            logger.debug(f"Панели обновлены автоматически: {reason}")
        except Exception as e:
            logger.error(f"Ошибка автообновления панелей: {e}")

    def showEvent(self, event):
        """Обработка события показа окна"""
        super().showEvent(event)
        # При первом показе окна также обновляем панели
        if hasattr(self, "left_panel"):
            self.refresh_panels_auto("Окно показано")

    def show_drag_help(self):
        """Показать справку по drag-and-drop"""
        help_text = """
<h3>📋 Справка по Drag & Drop</h3>

<h4>🔄 Перетаскивание файлов между панелями:</h4>
<ul>
<li><b>Обычное перетаскивание</b> - копирование файлов</li>
<li><b>Ctrl + перетаскивание</b> - принудительное копирование</li>
<li><b>Shift + перетаскивание</b> - перемещение файлов</li>
</ul>

<h4>🖱️ Выбор файлов:</h4>
<ul>
<li><b>Одиночный клик</b> - выбрать один файл</li>
<li><b>Ctrl + клик</b> - добавить/убрать файл из выбора (множественный выбор)</li>
<li><b>Shift + клик</b> - выбрать диапазон файлов</li>
<li><b>Ctrl + A</b> - выбрать все файлы</li>
</ul>

<h4>🚀 Экспорт в другие приложения:</h4>
<ul>
<li>Перетащите файлы из менеджера в другие программы</li>
<li>Поддерживается перетаскивание в текстовые редакторы, браузеры, и др.</li>
<li><b>Ctrl+Shift+D</b> - запустить drag для выбранного файла</li>
</ul>

<h4>📥 Импорт из других приложений:</h4>
<ul>
<li>Перетащите файлы из проводника Windows в любую панель</li>
<li>Перетащите файлы из браузера, почтовых клиентов</li>
<li>Поддерживается перетаскивание на заголовок окна</li>
</ul>

<h4>💡 Подсказки:</h4>
<ul>
<li>Индикатор в статус-баре показывает тип операции</li>
<li>Можно перетаскивать как отдельные файлы, так и группы</li>
<li>Папки также поддерживают drag & drop</li>
<li><b>Важно:</b> Ctrl+клик для выбора НЕ запускает drag операцию</li>
</ul>
        """

        msg = QMessageBox(self)
        msg.setWindowTitle("Справка по Drag & Drop")
        msg.setTextFormat(Qt.TextFormat.RichText)
        msg.setText(help_text)
        msg.setStandardButtons(QMessageBox.StandardButton.Ok)
        msg.exec()

    def show_shortcuts_help(self):
        """Показать справку по горячим клавишам"""
        help_text = """
<h3>⌨️ Горячие клавиши</h3>

<h4>🗂️ Основные операции:</h4>
<ul>
<li><b>F2</b> - Обновить панели</li>
<li><b>F3</b> - Просмотр файла</li>
<li><b>F4</b> - Редактировать файл</li>
<li><b>F5</b> - Копировать файлы</li>
<li><b>F6</b> - Переместить файлы</li>
<li><b>F7</b> - Создать папку</li>
<li><b>F8</b> - Удалить файлы</li>
</ul>

<h4>🔄 Навигация:</h4>
<ul>
<li><b>Tab</b> - Переключение между панелями</li>
<li><b>Ctrl+1/2</b> - Активировать левую/правую панель</li>
<li><b>Ctrl+Left/Right</b> - Переключение между вкладками</li>
</ul>

<h4>📑 Вкладки:</h4>
<ul>
<li><b>Ctrl+T</b> - Новая вкладка</li>
<li><b>Ctrl+W</b> - Закрыть вкладку</li>
<li><b>Ctrl+D</b> - Дублировать вкладку</li>
</ul>

<h4>🚀 Drag & Drop:</h4>
<ul>
<li><b>Ctrl+Shift+D</b> - Экспорт через drag & drop</li>
</ul>

<h4>🪟 Окно:</h4>
<ul>
<li><b>F11</b> - Полноэкранный режим</li>
<li><b>Alt+Enter</b> - Максимизировать/восстановить</li>
<li><b>Ctrl+Q</b> - Выход</li>
</ul>
        """

        msg = QMessageBox(self)
        msg.setWindowTitle("Горячие клавиши")
        msg.setTextFormat(Qt.TextFormat.RichText)
        msg.setText(help_text)
        msg.setStandardButtons(QMessageBox.StandardButton.Ok)
        msg.exec()

    def closeEvent(self, event):
        """Обработка закрытия приложения"""
        # Останавливаем все активные потоки
        self.stop_all_threads()
        self.save_current_settings()
        event.accept()

    def stop_all_threads(self):
        """Остановить все активные потоки"""
        if (
            hasattr(self, "file_thread")
            and self.file_thread
            and self.file_thread.isRunning()
        ):
            logger.info("Остановка файлового потока...")
            self.file_thread.requestInterruption()
            if not self.file_thread.wait(3000):  # Ждем 3 секунды
                logger.warning("Принудительное завершение файлового потока")
                self.file_thread.terminate()
                self.file_thread.wait(1000)

    def dragEnterEvent(self, event):
        """Обработка drag объектов в главное окно"""
        logger.debug("Главное окно: dragEnterEvent")

        if event.mimeData().hasUrls():
            urls = event.mimeData().urls()
            # Проверяем, есть ли локальные файлы
            for url in urls:
                if url.isLocalFile() and Path(url.toLocalFile()).exists():
                    event.acceptProposedAction()
                    logger.debug("Главное окно: drag данные приняты")
                    return

        event.ignore()
        logger.debug("Главное окно: drag данные отклонены")

    def dragMoveEvent(self, event):
        """Обработка движения drag объекта над главным окном"""
        if event.mimeData().hasUrls():
            event.acceptProposedAction()
        else:
            event.ignore()

    def dropEvent(self, event):
        """Обработка drop в главное окно"""
        logger.info("Главное окно: dropEvent")

        try:
            if not event.mimeData().hasUrls():
                event.ignore()
                return

            # Определяем активную панель как целевую
            active_panel, _ = self.get_active_panel()

            # Получаем координаты drop
            drop_pos = event.position().toPoint()

            # Определяем, на какую панель был сделан drop
            left_geometry = self.left_panel.geometry()
            right_geometry = self.right_panel.geometry()

            target_panel = None

            if left_geometry.contains(drop_pos):
                target_panel = self.left_panel
                logger.debug("Drop на левую панель")
            elif right_geometry.contains(drop_pos):
                target_panel = self.right_panel
                logger.debug("Drop на правую панель")
            else:
                # По умолчанию используем активную панель
                target_panel = active_panel
                logger.debug("Drop на активную панель (по умолчанию)")

            if not target_panel:
                logger.warning("Не удалось определить целевую панель")
                event.ignore()
                return

            # Передаем обработку drop соответствующей панели
            target_tab = target_panel.get_current_tab()
            if target_tab and target_tab.file_list:
                # Создаем искусственное drop событие для панели
                panel_pos = target_panel.mapFromGlobal(self.mapToGlobal(drop_pos))
                list_pos = target_tab.file_list.mapFromParent(panel_pos)

                # Создаем новое событие с локальными координатами
                new_event = event
                new_event.setDropAction(event.proposedAction())

                # Вызываем dropEvent панели напрямую
                target_tab.file_list.dropEvent(new_event)

                if new_event.isAccepted():
                    event.acceptProposedAction()
                    logger.info("Drop передан панели и принят")
                else:
                    event.ignore()
                    logger.warning("Drop отклонен панелью")
            else:
                event.ignore()
                logger.warning("Нет активной вкладки в целевой панели")

        except Exception as e:
            logger.error(f"Ошибка drop в главном окне: {e}", exc_info=True)
            event.ignore()


def main():
    try:
        app = QApplication(sys.argv)

        # Инициализируем логирование
        # main_logger = setup_logging()
        logger.info("=== Запуск приложения File Manager ===")

        # Установка стиля приложения
        app.setStyle("Fusion")

        # Создание главного окна
        window = DualPanelFileManager()
        window.show()
        logger.info("Главное окно отображено")

        # Запуск главного цикла приложения
        exit_code = app.exec()
        logger.info(f"Приложение завершено с кодом: {exit_code}")
        sys.exit(exit_code)

    except Exception as e:
        try:
            logger.critical(
                f"Критическая ошибка при запуске приложения: {e}", exc_info=True
            )
        except:
            # Если логгер недоступен, выводим в консоль
            print(f"КРИТИЧЕСКАЯ ОШИБКА: {e}")
            import traceback

            traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
