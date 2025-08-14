"""pip install PyQt6 Pillow numpy opencv-python"""

import sys
import os
from PyQt6.QtWidgets import (
    QApplication,
    QMainWindow,
    QVBoxLayout,
    QHBoxLayout,
    QWidget,
    QPushButton,
    QLabel,
    QSlider,
    QColorDialog,
    QFileDialog,
    QListWidget,
    QListWidgetItem,
    QTextEdit,
    QSpinBox,
    QGroupBox,
    QSplitter,
    QScrollArea,
    QLineEdit,
    QComboBox,
    QMessageBox,
    QProgressBar,
    QCheckBox,
    QStatusBar,
    QMenuBar,
    QToolBar,
    QTabWidget,
    QSpacerItem,
    QSizePolicy,
    QFrame,
    QGridLayout,
    QButtonGroup,
    QDialog,
    QDialogButtonBox,
    QSlider,
    QSpinBox,
)
from PyQt6.QtCore import Qt, QPoint, QRect, QSize, QThread, pyqtSignal, QTimer
from PyQt6.QtGui import (
    QPainter,
    QPen,
    QBrush,
    QColor,
    QPixmap,
    QImage,
    QFont,
    QIcon,
    QPalette,
    QAction,
    QTransform,
    QKeySequence,
    QCursor,
    QWheelEvent,
    QMouseEvent,
    QPaintEvent,
    QClipboard,
    QLinearGradient,
)
from PIL import Image, ImageEnhance, ImageFilter, ImageDraw, ImageFont, ImageOps
import numpy as np
import cv2


class ImageProcessor(QThread):
    """Поток для обработки изображений"""

    finished = pyqtSignal(QPixmap)
    progress = pyqtSignal(int)
    error = pyqtSignal(str)

    def __init__(self, image_path=None, image_data=None, operation="load", **kwargs):
        super().__init__()
        self.image_path = image_path
        self.image_data = image_data
        self.operation = operation
        self.kwargs = kwargs

    def run(self):
        try:
            if self.operation == "load":
                self.load_image()
            elif self.operation == "filters":
                self.apply_filters()
            elif self.operation == "remove_background":
                self.remove_background()
            elif self.operation == "blur":
                self.apply_blur()
            elif self.operation == "sharpen":
                self.apply_sharpen()
            elif self.operation == "unsharp_mask":
                self.apply_unsharp_mask()
            elif self.operation == "noise_reduction":
                self.apply_noise_reduction()
            elif self.operation == "grayscale":
                self.apply_grayscale()
            elif self.operation == "noise":
                self.apply_noise()
            elif self.operation == "sketch_effect":
                self.apply_sketch_effect()
            elif self.operation == "glass_effect":
                self.apply_glass_effect()
            elif self.operation == "wave_effect":
                self.apply_wave_effect()
            elif self.operation == "glow_effect":
                self.apply_glow_effect()
            elif self.operation == "shadow_effect":
                self.apply_shadow_effect()
            elif self.operation == "auto_levels":
                self.apply_auto_levels()
            elif self.operation == "auto_contrast":
                self.apply_auto_contrast()
            elif self.operation == "color_balance":
                self.apply_color_balance()

        except Exception as e:
            self.error.emit(str(e))

    def load_image(self):
        img = Image.open(self.image_path)
        self.progress.emit(50)
        pixmap = self.pil_to_pixmap(img)
        self.progress.emit(100)
        self.finished.emit(pixmap)

    def apply_filters(self):
        brightness = self.kwargs.get("brightness", 1.0)
        contrast = self.kwargs.get("contrast", 1.0)
        saturation = self.kwargs.get("saturation", 1.0)

        img = Image.open(self.image_path)
        self.progress.emit(25)

        if brightness != 1.0:
            enhancer = ImageEnhance.Brightness(img)
            img = enhancer.enhance(brightness)
        self.progress.emit(50)

        if contrast != 1.0:
            enhancer = ImageEnhance.Contrast(img)
            img = enhancer.enhance(contrast)
        self.progress.emit(75)

        if saturation != 1.0:
            enhancer = ImageEnhance.Color(img)
            img = enhancer.enhance(saturation)
        self.progress.emit(90)

        pixmap = self.pil_to_pixmap(img)
        self.progress.emit(100)
        self.finished.emit(pixmap)

    def remove_background(self):
        img = Image.open(self.image_path)
        self.progress.emit(30)

        #*  Конвертируем в RGBA
        img = img.convert("RGBA")
        data = img.getdata()

        self.progress.emit(60)

        new_data = []
        threshold = self.kwargs.get("threshold", 240)

        for item in data:
            # Делаем белые пиксели прозрачными
            if item[0] > threshold and item[1] > threshold and item[2] > threshold:
                new_data.append((255, 255, 255, 0))
            else:
                new_data.append(item)

        img.putdata(new_data)
        self.progress.emit(90)

        pixmap = self.pil_to_pixmap(img)
        self.progress.emit(100)
        self.finished.emit(pixmap)

    def apply_blur(self):
        img = Image.open(self.image_path)
        radius = self.kwargs.get("radius", 2)

        self.progress.emit(50)
        img = img.filter(ImageFilter.GaussianBlur(radius=radius))
        self.progress.emit(90)

        pixmap = self.pil_to_pixmap(img)
        self.progress.emit(100)
        self.finished.emit(pixmap)

    def apply_sharpen(self):
        img = Image.open(self.image_path)
        self.progress.emit(50)

        img = img.filter(ImageFilter.SHARPEN)
        self.progress.emit(90)

        pixmap = self.pil_to_pixmap(img)
        self.progress.emit(100)
        self.finished.emit(pixmap)

    def apply_unsharp_mask(self):
        """Увеличение резкости с помощью маски нерезкости"""
        img = Image.open(self.image_path)
        self.progress.emit(30)

        img = img.filter(ImageFilter.UnsharpMask(radius=2, percent=150, threshold=3))
        self.progress.emit(90)

        pixmap = self.pil_to_pixmap(img)
        self.progress.emit(100)
        self.finished.emit(pixmap)

    def apply_noise_reduction(self):
        """Шумоподавление"""
        img = Image.open(self.image_path)
        self.progress.emit(30)

        # Применяем медианный фильтр для уменьшения шума
        img = img.filter(ImageFilter.MedianFilter(size=3))
        self.progress.emit(90)

        pixmap = self.pil_to_pixmap(img)
        self.progress.emit(100)
        self.finished.emit(pixmap)

    def apply_grayscale(self):
        """Преобразование в черно-белое"""
        img = Image.open(self.image_path)
        self.progress.emit(50)

        img = img.convert("L").convert("RGB")
        self.progress.emit(90)

        pixmap = self.pil_to_pixmap(img)
        self.progress.emit(100)
        self.finished.emit(pixmap)

    def apply_noise(self):
        """Добавление шума"""
        img = Image.open(self.image_path)
        img_array = np.array(img)
        self.progress.emit(30)

        # Добавляем случайный шум
        noise = np.random.normal(0, 25, img_array.shape).astype(np.uint8)
        noisy_img = np.clip(img_array.astype(np.int16) + noise, 0, 255).astype(np.uint8)

        self.progress.emit(70)

        img = Image.fromarray(noisy_img)
        pixmap = self.pil_to_pixmap(img)
        self.progress.emit(100)
        self.finished.emit(pixmap)

    def apply_sketch_effect(self):
        """Эффект рисунка"""
        img = Image.open(self.image_path)
        self.progress.emit(30)

        # Преобразуем в оттенки серого
        img_gray = img.convert("L")

        # Инвертируем изображение
        img_inverted = ImageOps.invert(img_gray)

        # Применяем размытие
        img_blur = img_inverted.filter(ImageFilter.GaussianBlur(radius=21))

        # Создаем эффект карандашного рисунка
        def dodge(front, back):
            # Избегаем деления на ноль
            back_safe = np.where(back == 255, 254, back)
            result = front * 255.0 / (255 - back_safe)
            result = np.clip(result, 0, 255)
            return result.astype(np.uint8)

        front = np.array(img_gray)
        back = np.array(img_blur)

        try:
            sketch = dodge(front, back)
            # Убеждаемся, что результат корректный
            if sketch.min() < 0 or sketch.max() > 255:
                # Если что-то пошло не так, применяем простой эффект
                sketch = np.clip(front + (255 - back) // 2, 0, 255).astype(np.uint8)
        except:
            # Резервный вариант - простое инвертирование
            sketch = 255 - np.array(img_gray)

        self.progress.emit(90)

        img = Image.fromarray(sketch, mode="L").convert("RGB")
        pixmap = self.pil_to_pixmap(img)
        self.progress.emit(100)
        self.finished.emit(pixmap)

    def apply_glass_effect(self):
        """Эффект стекла"""
        img = Image.open(self.image_path)
        img_array = np.array(img)
        self.progress.emit(30)

        # Создаем искажение для эффекта стекла
        height, width = img_array.shape[:2]

        # Генерируем случайные смещения
        displacement_x = np.random.randint(-5, 6, (height, width))
        displacement_y = np.random.randint(-5, 6, (height, width))

        # Применяем искажение
        y_indices, x_indices = np.meshgrid(
            np.arange(height), np.arange(width), indexing="ij"
        )
        new_x = np.clip(x_indices + displacement_x, 0, width - 1)
        new_y = np.clip(y_indices + displacement_y, 0, height - 1)

        if len(img_array.shape) == 3:
            glass_img = img_array[new_y, new_x]
        else:
            glass_img = img_array[new_y, new_x]

        self.progress.emit(90)

        img = Image.fromarray(glass_img)
        pixmap = self.pil_to_pixmap(img)
        self.progress.emit(100)
        self.finished.emit(pixmap)

    def apply_wave_effect(self):
        """Эффект волн"""
        img = Image.open(self.image_path)
        img_array = np.array(img)
        self.progress.emit(30)

        height, width = img_array.shape[:2]

        # Создаем волновые искажения
        y_indices, x_indices = np.meshgrid(
            np.arange(height), np.arange(width), indexing="ij"
        )

        # Параметры волн
        amplitude = 20
        frequency = 0.05

        # Применяем синусоидальные искажения
        new_x = x_indices + amplitude * np.sin(frequency * y_indices)
        new_y = y_indices + amplitude * np.sin(frequency * x_indices)

        # Обрезаем значения по границам
        new_x = np.clip(new_x, 0, width - 1).astype(int)
        new_y = np.clip(new_y, 0, height - 1).astype(int)

        if len(img_array.shape) == 3:
            wave_img = img_array[new_y, new_x]
        else:
            wave_img = img_array[new_y, new_x]

        self.progress.emit(90)

        img = Image.fromarray(wave_img)
        pixmap = self.pil_to_pixmap(img)
        self.progress.emit(100)
        self.finished.emit(pixmap)

    def apply_glow_effect(self):
        """Эффект свечения"""
        img = Image.open(self.image_path)
        self.progress.emit(30)

        # Создаем копию для свечения
        glow = img.filter(ImageFilter.GaussianBlur(radius=15))

        # Усиливаем яркость для свечения
        enhancer = ImageEnhance.Brightness(glow)
        glow = enhancer.enhance(1.5)

        # Смешиваем оригинал со свечением
        result = Image.blend(img, glow, 0.3)

        self.progress.emit(90)

        pixmap = self.pil_to_pixmap(result)
        self.progress.emit(100)
        self.finished.emit(pixmap)

    def apply_auto_levels(self):
        """Автоматическая коррекция уровней"""
        img = Image.open(self.image_path)
        self.progress.emit(50)

        img = ImageOps.autocontrast(img)
        self.progress.emit(90)

        pixmap = self.pil_to_pixmap(img)
        self.progress.emit(100)
        self.finished.emit(pixmap)

    def apply_auto_contrast(self):
        """Автоматическая коррекция контраста"""
        img = Image.open(self.image_path)
        self.progress.emit(50)

        img = ImageOps.autocontrast(img, cutoff=1)
        self.progress.emit(90)

        pixmap = self.pil_to_pixmap(img)
        self.progress.emit(100)
        self.finished.emit(pixmap)

    def apply_color_balance(self):
        """Коррекция цветового баланса"""
        img = Image.open(self.image_path)
        img_array = np.array(img)
        self.progress.emit(30)

        # Получаем значения коррекции
        red_cyan = self.kwargs.get("red_cyan", 0)
        green_magenta = self.kwargs.get("green_magenta", 0)
        blue_yellow = self.kwargs.get("blue_yellow", 0)

        # Применяем коррекцию к каждому каналу
        if len(img_array.shape) == 3:
            # Красный-Голубой
            img_array[:, :, 0] = np.clip(img_array[:, :, 0] + red_cyan * 2.55, 0, 255)
            # Зеленый-Пурпурный
            img_array[:, :, 1] = np.clip(
                img_array[:, :, 1] + green_magenta * 2.55, 0, 255
            )
            # Синий-Желтый
            img_array[:, :, 2] = np.clip(
                img_array[:, :, 2] + blue_yellow * 2.55, 0, 255
            )

        self.progress.emit(90)

        img = Image.fromarray(img_array.astype(np.uint8))
        pixmap = self.pil_to_pixmap(img)
        self.progress.emit(100)
        self.finished.emit(pixmap)

    def apply_shadow_effect(self):
        """Эффект теней"""
        img = Image.open(self.image_path)
        self.progress.emit(30)

        # Создаем тень
        shadow = img.convert("RGBA")

        # Создаем черную тень
        shadow_data = []
        for pixel in shadow.getdata():
            # Делаем пиксель темнее для тени
            shadow_data.append(
                (0, 0, 0, int(pixel[3] * 0.5) if len(pixel) == 4 else 128)
            )

        shadow.putdata(shadow_data)

        # Размываем тень
        shadow = shadow.filter(ImageFilter.GaussianBlur(radius=5))

        # Создаем новое изображение с тенью
        result = Image.new(
            "RGBA", (img.width + 10, img.height + 10), (255, 255, 255, 0)
        )
        result.paste(shadow, (5, 5))  # Смещение тени
        result.paste(img, (0, 0))  # Оригинальное изображение сверху

        self.progress.emit(90)

        pixmap = self.pil_to_pixmap(result)
        self.progress.emit(100)
        self.finished.emit(pixmap)

    def pil_to_pixmap(self, img):
        """Конвертирует PIL изображение в QPixmap"""
        if img.mode == "RGBA":
            img_rgb = img
            h, w, ch = np.array(img_rgb).shape
            bytes_per_line = ch * w
            qt_image = QImage(
                np.array(img_rgb).data,
                w,
                h,
                bytes_per_line,
                QImage.Format.Format_RGBA8888,
            )
        else:
            img_rgb = img.convert("RGB")
            h, w, ch = np.array(img_rgb).shape
            bytes_per_line = ch * w
            qt_image = QImage(
                np.array(img_rgb).data,
                w,
                h,
                bytes_per_line,
                QImage.Format.Format_RGB888,
            )

        return QPixmap.fromImage(qt_image)


class DrawingCanvas(QLabel):
    """Холст для рисования и редактирования изображений"""

    def __init__(self):
        super().__init__()
        self.setMinimumSize(600, 450)
        #self.setMinimumWidth(800)
        self.setStyleSheet("border: 2px solid #cccccc; background-color: white;")
        self.setAlignment(Qt.AlignmentFlag.AlignCenter)

        # Состояние рисования
        self.drawing = False
        self.brush_size = 5
        self.brush_color = QColor(Qt.GlobalColor.black)
        self.last_point = QPoint()
        self.current_tool = "none"
        self.zoom_factor = 1.0

        # Дополнительные инструменты
        self.fill_color = QColor(Qt.GlobalColor.white)
        self.gradient_start_color = QColor(Qt.GlobalColor.black)
        self.gradient_end_color = QColor(Qt.GlobalColor.white)
        self.clone_source_point = None
        self.clone_offset = QPoint(0, 0)
        self.stamp_pattern = None

        # История изменений
        self.history = []
        self.history_index = -1
        self.max_history_size = 20

        # Изображение
        self.image = QPixmap(600, 450)
        self.image.fill(Qt.GlobalColor.white)
        self.original_image = None
        self.backup_image = None
        self.actual_size_mode = False

        # Текст
        self.text_font = QFont("Arial", 20)
        self.text_position = QPoint(50, 50)

        # Для перетаскивания
        self.dragging = False
        self.drag_start_position = QPoint()

        # Выделение области
        self.selecting = False
        self.selection_start = QPoint()
        self.selection_rect = QRect()
        self.selected_area = None

        # Обрезка
        self.cropping = False
        self.crop_start = QPoint()
        self.crop_rect = QRect()
        self.crop_area = None

        # Буфер обмена и вставка
        self.clipboard_data = None
        self.pasted_fragment = None
        self.fragment_position = QPoint(50, 50)
        self.dragging_fragment = False

        self.setPixmap(self.image)

    def set_image(self, pixmap):
        """Устанавливает изображение на холст"""
        self.original_image = pixmap.copy()
        self.image = pixmap.copy()
        self.backup_image = pixmap.copy()

        # Сбрасываем историю
        self.history = [pixmap.copy()]
        self.history_index = 0

        # Обновляем отображение
        self.update_display()

    def set_brush_size(self, size):
        self.brush_size = size

    def set_brush_color(self, color):
        self.brush_color = color

    def set_tool(self, tool):
        self.current_tool = tool
        if tool == "brush":
            self.setCursor(QCursor(Qt.CursorShape.CrossCursor))
        elif tool == "pencil":
            self.setCursor(QCursor(Qt.CursorShape.CrossCursor))
        elif tool == "eraser":
            self.setCursor(QCursor(Qt.CursorShape.CrossCursor))
        elif tool == "fill":
            self.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        elif tool == "gradient":
            self.setCursor(QCursor(Qt.CursorShape.CrossCursor))
        elif tool == "clone":
            self.setCursor(QCursor(Qt.CursorShape.CrossCursor))
        elif tool == "stamp":
            self.setCursor(QCursor(Qt.CursorShape.CrossCursor))
        elif tool == "text":
            self.setCursor(QCursor(Qt.CursorShape.IBeamCursor))
        elif tool == "drag":
            self.setCursor(QCursor(Qt.CursorShape.OpenHandCursor))
        elif tool == "select":
            self.setCursor(QCursor(Qt.CursorShape.CrossCursor))
        elif tool == "move":
            self.setCursor(QCursor(Qt.CursorShape.SizeAllCursor))
        elif tool == "crop":
            self.setCursor(QCursor(Qt.CursorShape.CrossCursor))
        else:
            self.setCursor(QCursor(Qt.CursorShape.ArrowCursor))

    def backup_current_state(self):
        """Создает резервную копию текущего состояния"""
        self.backup_image = self.image.copy()

    def add_to_history(self):
        """Добавляет текущее состояние в историю"""
        if not self.image:
            return

        # Удаляем все записи после текущего индекса (если мы отменили некоторые действия)
        self.history = self.history[: self.history_index + 1]

        # Добавляем новое состояние
        self.history.append(self.image.copy())
        self.history_index += 1

        # Ограничиваем размер истории
        if len(self.history) > self.max_history_size:
            self.history.pop(0)
            self.history_index -= 1

        # Обновляем интерфейс истории
        if hasattr(self.parent(), "update_history_ui"):
            self.parent().update_history_ui()

    def can_undo(self):
        """Проверяет, можно ли отменить действие"""
        return self.history_index > 0

    def can_redo(self):
        """Проверяет, можно ли повторить действие"""
        return self.history_index < len(self.history) - 1

    def undo_action(self):
        """Отменяет последнее действие"""
        if self.can_undo():
            self.history_index -= 1
            self.image = self.history[self.history_index].copy()
            self.update_display()

            # Очищаем состояние вставленного фрагмента при отмене
            if self.pasted_fragment:
                self.pasted_fragment = None
                self.current_tool = "none"
                self.setCursor(QCursor(Qt.CursorShape.ArrowCursor))

            # Обновляем интерфейс истории
            if hasattr(self.parent(), "update_history_ui"):
                self.parent().update_history_ui()
            return True
        return False

    def redo_action(self):
        """Повторяет отмененное действие"""
        if self.can_redo():
            self.history_index += 1
            self.image = self.history[self.history_index].copy()
            self.update_display()

            # Обновляем интерфейс истории
            if hasattr(self.parent(), "update_history_ui"):
                self.parent().update_history_ui()
            return True
        return False

    def restore_backup(self):
        """Восстанавливает из резервной копии"""
        if self.backup_image:
            self.image = self.backup_image.copy()
            self.update_display()

    def update_display(self):
        """Обновляет отображение изображения"""
        if not self.image:
            return

        if self.actual_size_mode:
            # Показываем в реальном размере с учетом масштаба
            new_width = int(self.image.width() * self.zoom_factor)
            new_height = int(self.image.height() * self.zoom_factor)
            display_pixmap = self.image.scaled(
                QSize(new_width, new_height),
                Qt.AspectRatioMode.IgnoreAspectRatio,
                Qt.TransformationMode.SmoothTransformation,
            )
        else:
            # Обычный режим - масштабируем под размер виджета с учетом zoom_factor
            widget_size = self.size()
            # Оставляем небольшие отступы
            target_size = QSize(widget_size.width() - 20, widget_size.height() - 20)

            # Сначала подгоняем под размер виджета, сохраняя пропорции
            fitted_pixmap = self.image.scaled(
                target_size,
                Qt.AspectRatioMode.KeepAspectRatio,
                Qt.TransformationMode.SmoothTransformation,
            )

            # Затем применяем zoom_factor
            zoomed_width = int(fitted_pixmap.width() * self.zoom_factor)
            zoomed_height = int(fitted_pixmap.height() * self.zoom_factor)

            display_pixmap = fitted_pixmap.scaled(
                QSize(zoomed_width, zoomed_height),
                Qt.AspectRatioMode.IgnoreAspectRatio,
                Qt.TransformationMode.SmoothTransformation,
            )

        self.setPixmap(display_pixmap)
        self.update()  # Принудительно обновляем виджет для перерисовки наложений

    def add_text(self, text, position=None):
        """Добавляет текст на изображение"""
        if not text:
            return

        self.add_to_history()

        painter = QPainter(self.image)
        painter.setPen(QPen(self.brush_color, 2))
        painter.setFont(self.text_font)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        # Используем позицию, установленную при клике мыши
        text_pos = position if position else self.text_position

        # Добавляем высоту шрифта к Y-координате для правильного позиционирования
        adjusted_y = text_pos.y() + self.text_font.pointSize()
        adjusted_pos = QPoint(text_pos.x(), adjusted_y)

        # Убеждаемся, что позиция находится в пределах изображения
        if (
            adjusted_pos.x() >= 0
            and adjusted_pos.x() < self.image.width()
            and adjusted_pos.y() >= 0
            and adjusted_pos.y() < self.image.height()
        ):
            painter.drawText(adjusted_pos, text)
        else:
            # Если позиция вне изображения, размещаем в безопасном месте
            safe_pos = QPoint(50, 50 + self.text_font.pointSize())
            painter.drawText(safe_pos, text)

        painter.end()
        self.update_display()

    def remove_background(self, threshold=240):
        """Упрощенное удаление фона"""
        if self.original_image is None:
            return

        self.add_to_history()

        # Конвертируем в PIL Image для обработки
        qimg = self.image.toImage()
        buffer = qimg.bits().asstring(qimg.sizeInBytes())

        if qimg.format() == QImage.Format.Format_RGB888:
            pil_img = Image.frombuffer(
                "RGB", (qimg.width(), qimg.height()), buffer, "raw", "RGB", 0, 1
            )
        else:
            pil_img = Image.frombuffer(
                "RGBA", (qimg.width(), qimg.height()), buffer, "raw", "RGBA", 0, 1
            )

        # Конвертируем в RGBA для прозрачности
        pil_img = pil_img.convert("RGBA")
        data = pil_img.getdata()

        new_data = []
        for item in data:
            # Делаем белые пиксели прозрачными
            if item[0] > threshold and item[1] > threshold and item[2] > threshold:
                new_data.append((255, 255, 255, 0))
            else:
                new_data.append(item)

        pil_img.putdata(new_data)

        # Конвертируем обратно в QPixmap
        img_array = np.array(pil_img)
        h, w, ch = img_array.shape
        bytes_per_line = ch * w
        qt_image = QImage(
            img_array.data, w, h, bytes_per_line, QImage.Format.Format_RGBA8888
        )
        self.image = QPixmap.fromImage(qt_image)

        self.update_display()

    def reset_image(self):
        """Сбрасывает изображение к оригиналу"""
        if self.original_image:
            self.image = self.original_image.copy()
            self.update_display()

    def crop_image(self, rect):
        """Обрезает изображение"""
        if rect.isValid():
            self.add_to_history()
            cropped = self.image.copy(rect)
            self.image = cropped
            self.update_display()

    def rotate_image(self, angle):
        """Поворачивает изображение"""
        if not self.image:
            return
        self.add_to_history()
        transform = QTransform()
        transform.rotate(angle)
        self.image = self.image.transformed(
            transform, Qt.TransformationMode.SmoothTransformation
        )
        self.update_display()

    def flip_image(self, horizontal=True):
        """Отражает изображение"""
        if not self.image:
            return
        self.add_to_history()
        if horizontal:
            self.image = self.image.transformed(QTransform().scale(-1, 1))
        else:
            self.image = self.image.transformed(QTransform().scale(1, -1))
        self.update_display()

    def resize_image(self, size):
        """Изменяет размер изображения"""
        if not self.image:
            return
        self.add_to_history()
        self.image = self.image.scaled(
            size,
            Qt.AspectRatioMode.KeepAspectRatio,
            Qt.TransformationMode.SmoothTransformation,
        )
        self.update_display()

    def copy_selected_area(self):
        """Копирует выделенную область в буфер обмена"""
        if not self.selected_area:
            return False

        # Нормализуем координаты выделения
        x = max(0, min(self.selected_area.x(), self.image.width()))
        y = max(0, min(self.selected_area.y(), self.image.height()))
        width = min(self.selected_area.width(), self.image.width() - x)
        height = min(self.selected_area.height(), self.image.height() - y)

        # Проверяем, что область валидна
        if width <= 0 or height <= 0:
            return False

        # Создаем нормализованный прямоугольник
        normalized_rect = QRect(x, y, width, height)

        # Копируем область из изображения
        copied_pixmap = self.image.copy(normalized_rect)

        # Сохраняем во внутренний буфер
        self.clipboard_data = copied_pixmap

        # Копируем в системный буфер обмена
        clipboard = QApplication.clipboard()
        clipboard.setPixmap(copied_pixmap)

        self.selected_area = None  # Убираем выделение
        self.update()
        return True

    def paste_from_clipboard(self):
        """Вставляет данные из буфера обмена (включая системный)"""
        # Сначала пытаемся получить данные из системного буфера обмена
        clipboard = QApplication.clipboard()

        # Проверяем, есть ли изображение в системном буфере
        if clipboard.mimeData().hasImage():
            # Получаем изображение из системного буфера
            image_data = clipboard.mimeData().imageData()
            if image_data:
                # Преобразуем QImage в QPixmap
                if isinstance(image_data, QImage):
                    system_pixmap = QPixmap.fromImage(image_data)
                else:
                    system_pixmap = QPixmap(image_data)

                if not system_pixmap.isNull():
                    # Используем изображение из системного буфера
                    self.pasted_fragment = system_pixmap
                    self.fragment_position = QPoint(50, 50)
                    self.current_tool = "move"
                    self.setCursor(QCursor(Qt.CursorShape.SizeAllCursor))
                    self.update()
                    return True

        # Если в системном буфере нет изображения, проверяем внутренний буфер
        if self.clipboard_data:
            self.pasted_fragment = self.clipboard_data
            self.fragment_position = QPoint(50, 50)
            self.current_tool = "move"
            self.setCursor(QCursor(Qt.CursorShape.SizeAllCursor))
            self.update()
            return True

        return False

    def apply_fragment_to_canvas(self):
        """Применяет вставленный фрагмент к основному изображению"""
        if not self.pasted_fragment:
            return

        # Добавляем в историю перед применением фрагмента
        self.add_to_history()

        painter = QPainter(self.image)
        painter.drawPixmap(self.fragment_position, self.pasted_fragment)
        painter.end()

        # Очищаем вставленный фрагмент
        self.pasted_fragment = None
        self.update_display()

        # Обновляем историю после применения
        if hasattr(self.parent(), "update_history_ui"):
            self.parent().update_history_ui()

    def flood_fill(self, start_point):
        """Заливка области одним цветом"""
        if not self.image:
            return

        # Конвертируем в QImage для работы с пикселями
        img = self.image.toImage()
        target_color = img.pixelColor(start_point)

        if target_color == self.fill_color:
            return  # Цвет уже такой же

        # Простой алгоритм заливки
        stack = [start_point]
        visited = set()

        while stack:
            point = stack.pop()

            if (
                point.x() < 0
                or point.x() >= img.width()
                or point.y() < 0
                or point.y() >= img.height()
            ):
                continue

            if (point.x(), point.y()) in visited:
                continue

            current_color = img.pixelColor(point)
            if current_color != target_color:
                continue

            img.setPixelColor(point, self.fill_color)
            visited.add((point.x(), point.y()))

            # Добавляем соседние пиксели
            stack.extend(
                [
                    QPoint(point.x() + 1, point.y()),
                    QPoint(point.x() - 1, point.y()),
                    QPoint(point.x(), point.y() + 1),
                    QPoint(point.x(), point.y() - 1),
                ]
            )

        self.image = QPixmap.fromImage(img)
        self.update_display()

    def apply_gradient(self, start_point, end_point):
        """Применяет градиент между двумя точками"""
        if not self.image:
            return

        painter = QPainter(self.image)

        # Создаем линейный градиент с float координатами
        gradient = QLinearGradient(
            float(start_point.x()),
            float(start_point.y()),
            float(end_point.x()),
            float(end_point.y()),
        )
        gradient.setColorAt(0, self.gradient_start_color)
        gradient.setColorAt(1, self.gradient_end_color)

        painter.setBrush(QBrush(gradient))
        painter.setPen(Qt.PenStyle.NoPen)
        painter.drawRect(self.image.rect())
        painter.end()

        self.update_display()

    def apply_clone(self, target_point):
        """Применяет клонирование"""
        if not self.clone_source_point or not self.image:
            return

        # Вычисляем смещение
        offset = target_point - self.last_point if self.last_point else QPoint(0, 0)
        source_point = self.clone_source_point + offset

        # Проверяем границы
        if (
            source_point.x() < 0
            or source_point.x() >= self.image.width()
            or source_point.y() < 0
            or source_point.y() >= self.image.height()
        ):
            return

        painter = QPainter(self.image)

        # Копируем область
        brush_rect = QRect(
            source_point.x() - self.brush_size // 2,
            source_point.y() - self.brush_size // 2,
            self.brush_size,
            self.brush_size,
        )

        target_rect = QRect(
            target_point.x() - self.brush_size // 2,
            target_point.y() - self.brush_size // 2,
            self.brush_size,
            self.brush_size,
        )

        painter.drawPixmap(target_rect, self.image, brush_rect)
        painter.end()

        self.update_display()

    def apply_stamp(self, position):
        """Применяет штамп"""
        if not self.stamp_pattern or not self.image:
            return

        painter = QPainter(self.image)
        painter.setOpacity(0.7)

        # Центрируем штамп
        stamp_rect = QRect(
            position.x() - self.stamp_pattern.width() // 2,
            position.y() - self.stamp_pattern.height() // 2,
            self.stamp_pattern.width(),
            self.stamp_pattern.height(),
        )

        painter.drawPixmap(stamp_rect, self.stamp_pattern)
        painter.end()

        self.update_display()

    def set_fill_color(self, color):
        """Устанавливает цвет заливки"""
        self.fill_color = color

    def set_gradient_colors(self, start_color, end_color):
        """Устанавливает цвета градиента"""
        self.gradient_start_color = start_color
        self.gradient_end_color = end_color

    def set_stamp_pattern(self, pattern):
        """Устанавливает паттерн штампа"""
        self.stamp_pattern = pattern

    def apply_crop(self):
        """Применяет обрезку к изображению"""
        if not self.crop_area or not self.image:
            return

        # Нормализуем координаты обрезки
        x = max(0, min(self.crop_area.x(), self.image.width()))
        y = max(0, min(self.crop_area.y(), self.image.height()))
        width = min(self.crop_area.width(), self.image.width() - x)
        height = min(self.crop_area.height(), self.image.height() - y)

        # Проверяем, что область валидна
        if width <= 0 or height <= 0:
            return

        # Создаем нормализованный прямоугольник
        normalized_rect = QRect(x, y, width, height)

        # Добавляем в историю
        self.add_to_history()

        # Обрезаем изображение
        self.image = self.image.copy(normalized_rect)

        # Обновляем отображение
        self.update_display()

        # Сбрасываем область обрезки
        self.crop_area = None

        # Обновляем историю в интерфейсе
        if hasattr(self.parent(), "update_history_ui"):
            self.parent().update_history_ui()

    def get_canvas_position(self, widget_pos):
        """Преобразует позицию в виджете в позицию на изображении с учетом масштабирования"""
        if not self.pixmap():
            return widget_pos

        # Получаем размеры виджета и отображаемого pixmap
        widget_size = self.size()
        displayed_pixmap = self.pixmap()
        actual_image_size = self.image.size()

        # Вычисляем коэффициент масштабирования между отображаемым изображением и реальным
        scale_x = actual_image_size.width() / displayed_pixmap.width()
        scale_y = actual_image_size.height() / displayed_pixmap.height()

        # Вычисляем позицию отображаемого изображения в виджете (центрированное)
        offset_x = (widget_size.width() - displayed_pixmap.width()) // 2
        offset_y = (widget_size.height() - displayed_pixmap.height()) // 2

        # Преобразуем координаты виджета в координаты отображаемого изображения
        displayed_x = widget_pos.x() - offset_x
        displayed_y = widget_pos.y() - offset_y

        # Проверяем, что клик внутри отображаемого изображения
        if (
            displayed_x < 0
            or displayed_x >= displayed_pixmap.width()
            or displayed_y < 0
            or displayed_y >= displayed_pixmap.height()
        ):
            return QPoint(50, 50)  # Возвращаем безопасную позицию

        # Преобразуем в координаты реального изображения
        real_x = int(displayed_x * scale_x)
        real_y = int(displayed_y * scale_y)

        # Ограничиваем координаты размерами реального изображения
        real_x = max(0, min(real_x, actual_image_size.width() - 1))
        real_y = max(0, min(real_y, actual_image_size.height() - 1))

        return QPoint(real_x, real_y)

    def dragEnterEvent(self, event):
        """Обработчик входа перетаскиваемых данных в canvas"""
        if event.mimeData().hasUrls():
            urls = event.mimeData().urls()
            # Проверяем, есть ли среди перетаскиваемых файлов изображения
            for url in urls:
                file_path = url.toLocalFile()
                if file_path.lower().endswith(
                    (".png", ".jpg", ".jpeg", ".bmp", ".gif", ".tiff", ".webp", ".ico")
                ):
                    event.accept()
                    return
            event.ignore()
        else:
            event.ignore()

    def dropEvent(self, event):
        """Обработчик сброса перетаскиваемых файлов в canvas"""
        if event.mimeData().hasUrls():
            urls = event.mimeData().urls()
            for url in urls:
                file_path = url.toLocalFile()
                if file_path.lower().endswith(
                    (".png", ".jpg", ".jpeg", ".bmp", ".gif", ".tiff", ".webp", ".ico")
                ):
                    # Загружаем первое найденное изображение через главное окно
                    if hasattr(self.parent(), "load_image_from_path"):
                        self.parent().load_image_from_path(file_path)
                    event.accept()
                    return
            event.ignore()
        else:
            event.ignore()

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            widget_pos = event.position().toPoint()
            canvas_pos = self.get_canvas_position(widget_pos)

            if self.current_tool == "brush":
                self.drawing = True
                self.last_point = canvas_pos
                self.add_to_history()
            elif self.current_tool == "pencil":
                self.drawing = True
                self.last_point = canvas_pos
                self.add_to_history()
            elif self.current_tool == "eraser":
                self.drawing = True
                self.last_point = canvas_pos
                self.add_to_history()
            elif self.current_tool == "fill":
                self.add_to_history()
                self.flood_fill(canvas_pos)
            elif self.current_tool == "gradient":
                self.drawing = True
                self.last_point = canvas_pos
                self.add_to_history()
            elif self.current_tool == "clone":
                if event.modifiers() & Qt.KeyboardModifier.ControlModifier:
                    # Ctrl+Click устанавливает источник клонирования
                    self.clone_source_point = canvas_pos
                    self.setCursor(QCursor(Qt.CursorShape.CrossCursor))
                elif self.clone_source_point:
                    self.drawing = True
                    self.last_point = canvas_pos
                    self.add_to_history()
            elif self.current_tool == "stamp":
                if self.stamp_pattern:
                    self.add_to_history()
                    self.apply_stamp(canvas_pos)
            elif self.current_tool == "text":
                self.text_position = canvas_pos
                # При клике мышью добавляем текст, если он есть
                if (
                    hasattr(self.parent(), "text_input")
                    and self.parent().text_input.text().strip()
                ):
                    text = self.parent().text_input.text().strip()
                    self.add_text(text, canvas_pos)
                    self.parent().text_input.clear()
                    self.parent().status_bar.showMessage("Текст добавлен")
            elif self.current_tool == "drag":
                self.dragging = True
                self.drag_start_position = widget_pos
                self.setCursor(QCursor(Qt.CursorShape.ClosedHandCursor))
            elif self.current_tool == "select":
                self.selecting = True
                self.selection_start = canvas_pos
                self.selection_rect = QRect(canvas_pos, canvas_pos)
                self.selected_area = None
            elif self.current_tool == "move" and self.pasted_fragment:
                # Проверяем, находится ли курсор над вставленным фрагментом
                frag_rect = QRect(self.fragment_position, self.pasted_fragment.size())
                if frag_rect.contains(canvas_pos):
                    self.dragging_fragment = True
            elif self.current_tool == "crop":
                self.cropping = True
                self.crop_start = canvas_pos
                self.crop_rect = QRect(canvas_pos, canvas_pos)
                self.crop_area = None

    def mouseMoveEvent(self, event):
        widget_pos = event.position().toPoint()
        canvas_pos = self.get_canvas_position(widget_pos)

        if (
            self.current_tool == "brush"
            and self.drawing
            and event.buttons() & Qt.MouseButton.LeftButton
        ):
            painter = QPainter(self.image)
            painter.setPen(
                QPen(
                    self.brush_color,
                    self.brush_size,
                    Qt.PenStyle.SolidLine,
                    Qt.PenCapStyle.RoundCap,
                    Qt.PenJoinStyle.RoundJoin,
                )
            )
            painter.setRenderHint(QPainter.RenderHint.Antialiasing)
            painter.drawLine(self.last_point, canvas_pos)
            painter.end()

            self.last_point = canvas_pos
            self.update_display()
        elif (
            self.current_tool == "pencil"
            and self.drawing
            and event.buttons() & Qt.MouseButton.LeftButton
        ):
            painter = QPainter(self.image)
            painter.setPen(
                QPen(
                    self.brush_color,
                    1,
                    Qt.PenStyle.SolidLine,
                    Qt.PenCapStyle.SquareCap,
                    Qt.PenJoinStyle.MiterJoin,
                )
            )
            painter.drawLine(self.last_point, canvas_pos)
            painter.end()

            self.last_point = canvas_pos
            self.update_display()
        elif (
            self.current_tool == "eraser"
            and self.drawing
            and event.buttons() & Qt.MouseButton.LeftButton
        ):
            painter = QPainter(self.image)
            # Правильный способ стирания - рисуем белым цветом или прозрачным
            if self.image.hasAlphaChannel():
                painter.setCompositionMode(
                    QPainter.CompositionMode.CompositionMode_Clear
                )
                painter.setPen(
                    QPen(
                        QColor(0, 0, 0, 0),
                        self.brush_size,
                        Qt.PenStyle.SolidLine,
                        Qt.PenCapStyle.RoundCap,
                        Qt.PenJoinStyle.RoundJoin,
                    )
                )
            else:
                painter.setPen(
                    QPen(
                        QColor(Qt.GlobalColor.white),
                        self.brush_size,
                        Qt.PenStyle.SolidLine,
                        Qt.PenCapStyle.RoundCap,
                        Qt.PenJoinStyle.RoundJoin,
                    )
                )
            painter.setRenderHint(QPainter.RenderHint.Antialiasing)
            painter.drawLine(self.last_point, canvas_pos)
            painter.end()

            self.last_point = canvas_pos
            self.update_display()
        elif (
            self.current_tool == "clone"
            and self.drawing
            and event.buttons() & Qt.MouseButton.LeftButton
            and self.clone_source_point
        ):
            self.apply_clone(canvas_pos)
            self.last_point = canvas_pos
        elif (
            self.current_tool == "gradient"
            and self.drawing
            and event.buttons() & Qt.MouseButton.LeftButton
        ):
            # Предварительный просмотр градиента
            pass
        elif self.current_tool == "select" and self.selecting:
            self.selection_rect = QRect(self.selection_start, canvas_pos).normalized()
            self.update()
        elif (
            self.current_tool == "move"
            and self.dragging_fragment
            and self.pasted_fragment
        ):
            self.fragment_position = canvas_pos
            self.update()
        elif self.current_tool == "crop" and self.cropping:
            self.crop_rect = QRect(self.crop_start, canvas_pos).normalized()
            self.update()

    def mouseReleaseEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            widget_pos = event.position().toPoint()
            canvas_pos = self.get_canvas_position(widget_pos)

            if self.current_tool == "gradient" and self.drawing:
                # Применяем градиент от начальной до конечной точки
                self.apply_gradient(self.last_point, canvas_pos)

            # Сбрасываем состояние рисования только после завершения действия
            if self.drawing:
                self.drawing = False
                # Обновляем историю в интерфейсе после завершения рисования
                if hasattr(self.parent(), "update_history_ui"):
                    self.parent().update_history_ui()

            if self.current_tool == "drag":
                self.dragging = False
                self.setCursor(QCursor(Qt.CursorShape.OpenHandCursor))
            elif self.current_tool == "select" and self.selecting:
                self.selecting = False
                if (
                    self.selection_rect.width() > 10
                    and self.selection_rect.height() > 10
                ):
                    self.selected_area = self.selection_rect
                self.selection_rect = QRect()
                self.update()
            elif self.current_tool == "move" and self.dragging_fragment:
                self.dragging_fragment = False
                # Применяем фрагмент к изображению
                self.apply_fragment_to_canvas()
            elif self.current_tool == "crop" and self.cropping:
                self.cropping = False
                if self.crop_rect.width() > 10 and self.crop_rect.height() > 10:
                    self.crop_area = self.crop_rect
                    # Автоматически применяем обрезку
                    self.apply_crop()
                self.crop_rect = QRect()

    def wheelEvent(self, event):
        """Масштабирование колесиком мыши"""
        if event.modifiers() & Qt.KeyboardModifier.ControlModifier:
            delta = event.angleDelta().y()
            if delta > 0:
                self.zoom_factor *= 1.1
            else:
                self.zoom_factor /= 1.1

            self.zoom_factor = max(0.1, min(5.0, self.zoom_factor))
            self.update_display()

            # Обновляем слайдер масштаба в главном окне
            if hasattr(self.parent(), "zoom_slider"):
                zoom_percent = int(self.zoom_factor * 100)
                self.parent().zoom_slider.blockSignals(True)
                self.parent().zoom_slider.setValue(zoom_percent)
                self.parent().zoom_label.setText(f"{zoom_percent}%")
                self.parent().zoom_status.setText(f"Масштаб: {zoom_percent}%")
                self.parent().zoom_slider.blockSignals(False)

    def get_widget_position(self, canvas_pos):
        """Преобразует позицию на изображении в позицию в виджете с учетом масштабирования"""
        if not self.pixmap():
            return canvas_pos

        # Получаем размеры виджета и отображаемого pixmap
        widget_size = self.size()
        displayed_pixmap = self.pixmap()
        actual_image_size = self.image.size()

        # Вычисляем коэффициент масштабирования между реальным и отображаемым изображением
        scale_x = displayed_pixmap.width() / actual_image_size.width()
        scale_y = displayed_pixmap.height() / actual_image_size.height()

        # Преобразуем координаты реального изображения в координаты отображаемого
        displayed_x = int(canvas_pos.x() * scale_x)
        displayed_y = int(canvas_pos.y() * scale_y)

        # Вычисляем смещение для центрирования отображаемого изображения в виджете
        offset_x = (widget_size.width() - displayed_pixmap.width()) // 2
        offset_y = (widget_size.height() - displayed_pixmap.height()) // 2

        # Преобразуем в координаты виджета
        widget_x = displayed_x + offset_x
        widget_y = displayed_y + offset_y

        return QPoint(widget_x, widget_y)

    def get_widget_rect(self, canvas_rect):
        """Преобразует прямоугольник на canvas в прямоугольник в виджете"""
        top_left = self.get_widget_position(canvas_rect.topLeft())
        bottom_right = self.get_widget_position(canvas_rect.bottomRight())
        return QRect(top_left, bottom_right)

    def paintEvent(self, event):
        """Переопределяем paintEvent для рисования выделения и фрагментов"""
        super().paintEvent(event)

        painter = QPainter(self)

        # Рисуем выделение в процессе
        if self.selecting and not self.selection_rect.isEmpty():
            pen = QPen(QColor(0, 123, 255), 2, Qt.PenStyle.DashLine)
            painter.setPen(pen)
            painter.setBrush(QBrush())
            widget_rect = self.get_widget_rect(self.selection_rect)
            painter.drawRect(widget_rect)

        # Рисуем завершенное выделение
        if self.selected_area and not self.selected_area.isEmpty():
            pen = QPen(QColor(0, 123, 255), 2, Qt.PenStyle.DashLine)
            painter.setPen(pen)
            painter.setBrush(QBrush())
            widget_rect = self.get_widget_rect(self.selected_area)
            painter.drawRect(widget_rect)

        # Рисуем область обрезки в процессе
        if self.cropping and not self.crop_rect.isEmpty():
            pen = QPen(QColor(255, 0, 0), 3, Qt.PenStyle.SolidLine)
            painter.setPen(pen)
            painter.setBrush(QBrush())
            widget_rect = self.get_widget_rect(self.crop_rect)
            painter.drawRect(widget_rect)

            # Затемняем области, которые будут обрезаны
            painter.setBrush(QBrush(QColor(0, 0, 0, 100)))
            painter.setPen(Qt.PenStyle.NoPen)

            # Получаем границы изображения в координатах виджета
            image_widget_rect = self.get_widget_rect(
                QRect(0, 0, self.image.width(), self.image.height())
            )

            # Рисуем затемненные области вокруг области обрезки
            # Верхняя область
            if widget_rect.top() > image_widget_rect.top():
                painter.drawRect(
                    image_widget_rect.left(),
                    image_widget_rect.top(),
                    image_widget_rect.width(),
                    widget_rect.top() - image_widget_rect.top(),
                )

            # Нижняя область
            if widget_rect.bottom() < image_widget_rect.bottom():
                painter.drawRect(
                    image_widget_rect.left(),
                    widget_rect.bottom(),
                    image_widget_rect.width(),
                    image_widget_rect.bottom() - widget_rect.bottom(),
                )

            # Левая область
            if widget_rect.left() > image_widget_rect.left():
                painter.drawRect(
                    image_widget_rect.left(),
                    widget_rect.top(),
                    widget_rect.left() - image_widget_rect.left(),
                    widget_rect.height(),
                )

            # Правая область
            if widget_rect.right() < image_widget_rect.right():
                painter.drawRect(
                    widget_rect.right(),
                    widget_rect.top(),
                    image_widget_rect.right() - widget_rect.right(),
                    widget_rect.height(),
                )

        # Рисуем вставленный фрагмент
        if self.pasted_fragment:
            # Получаем позицию фрагмента в координатах виджета
            widget_pos = self.get_widget_position(self.fragment_position)

            # Вычисляем масштаб для отображения фрагмента
            if self.pixmap():
                displayed_pixmap = self.pixmap()
                actual_image_size = self.image.size()

                # Коэффициент масштабирования
                scale_x = displayed_pixmap.width() / actual_image_size.width()
                scale_y = displayed_pixmap.height() / actual_image_size.height()

                # Масштабируем фрагмент
                scaled_width = int(self.pasted_fragment.width() * scale_x)
                scaled_height = int(self.pasted_fragment.height() * scale_y)

                scaled_fragment = self.pasted_fragment.scaled(
                    scaled_width,
                    scaled_height,
                    Qt.AspectRatioMode.IgnoreAspectRatio,
                    Qt.TransformationMode.SmoothTransformation,
                )

                painter.drawPixmap(widget_pos, scaled_fragment)

                # Рисуем рамку вокруг фрагмента
                pen = QPen(QColor(40, 167, 69), 2, Qt.PenStyle.DashLine)
                painter.setPen(pen)
                painter.setBrush(QBrush())
                frag_rect = QRect(widget_pos, scaled_fragment.size())
                painter.drawRect(frag_rect)


class ResizeDialog(QDialog):
    """Диалог изменения размера изображения"""

    def __init__(self, current_size, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Изменить размер")
        self.setModal(True)
        self.current_size = current_size

        layout = QVBoxLayout()

        # Поля для ввода размеров
        size_layout = QGridLayout()

        size_layout.addWidget(QLabel("Ширина:"), 0, 0)
        self.width_spin = QSpinBox()
        self.width_spin.setRange(1, 10000)
        self.width_spin.setValue(current_size.width())
        size_layout.addWidget(self.width_spin, 0, 1)

        size_layout.addWidget(QLabel("Высота:"), 1, 0)
        self.height_spin = QSpinBox()
        self.height_spin.setRange(1, 10000)
        self.height_spin.setValue(current_size.height())
        size_layout.addWidget(self.height_spin, 1, 1)

        # Чекбокс для сохранения пропорций
        self.keep_ratio_check = QCheckBox("Сохранить пропорции")
        self.keep_ratio_check.setChecked(True)

        layout.addLayout(size_layout)
        layout.addWidget(self.keep_ratio_check)

        # Кнопки
        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

        self.setLayout(layout)

        # Связываем изменения размеров
        self.width_spin.valueChanged.connect(self.on_width_changed)
        self.height_spin.valueChanged.connect(self.on_height_changed)

    def on_width_changed(self, value):
        if self.keep_ratio_check.isChecked():
            ratio = self.current_size.height() / self.current_size.width()
            self.height_spin.blockSignals(True)
            self.height_spin.setValue(int(value * ratio))
            self.height_spin.blockSignals(False)

    def on_height_changed(self, value):
        if self.keep_ratio_check.isChecked():
            ratio = self.current_size.width() / self.current_size.height()
            self.width_spin.blockSignals(True)
            self.width_spin.setValue(int(value * ratio))
            self.width_spin.blockSignals(False)

    def get_size(self):
        return QSize(self.width_spin.value(), self.height_spin.value())


class IconSizeDialog(QDialog):
    """Диалог выбора размеров для ICO файла"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Выберите размеры иконок")
        self.setModal(True)
        self.setFixedSize(400, 500)

        layout = QVBoxLayout()

        # Заголовок
        title = QLabel("Выберите размеры иконок для ICO файла:")
        title.setFont(QFont("Arial", 12, QFont.Weight.Bold))
        layout.addWidget(title)

        # Описание
        description = QLabel(
            "ICO файл может содержать несколько размеров иконок.\n"
            "Рекомендуется включить стандартные размеры для лучшей совместимости."
        )
        description.setWordWrap(True)
        description.setStyleSheet("color: #666; margin: 10px 0;")
        layout.addWidget(description)

        # Стандартные размеры иконок
        standard_sizes = [16, 24, 32, 48, 64, 96, 128, 256]
        self.size_checkboxes = {}

        # Группа стандартных размеров
        standard_group = QGroupBox("Стандартные размеры")
        standard_layout = QGridLayout(standard_group)

        row, col = 0, 0
        for size in standard_sizes:
            checkbox = QCheckBox(f"{size}×{size} пикселей")

            # Отмечаем наиболее популярные размеры по умолчанию
            if size in [16, 32, 48, 256]:
                checkbox.setChecked(True)

            # Добавляем описание для некоторых размеров
            if size == 16:
                checkbox.setToolTip("Маленькие иконки в проводнике, панель задач")
            elif size == 32:
                checkbox.setToolTip("Средние иконки в проводнике")
            elif size == 48:
                checkbox.setToolTip("Большие иконки в проводнике")
            elif size == 256:
                checkbox.setToolTip("Очень большие иконки, Windows Vista+")

            self.size_checkboxes[size] = checkbox
            standard_layout.addWidget(checkbox, row, col)

            col += 1
            if col >= 2:
                col = 0
                row += 1

        layout.addWidget(standard_group)

        # Пользовательский размер
        custom_group = QGroupBox("Пользовательский размер")
        custom_layout = QHBoxLayout(custom_group)

        self.custom_size_spin = QSpinBox()
        self.custom_size_spin.setRange(8, 512)
        self.custom_size_spin.setValue(64)
        self.custom_size_spin.setSuffix(" пикселей")

        self.custom_checkbox = QCheckBox("Включить пользовательский размер:")
        custom_layout.addWidget(self.custom_checkbox)
        custom_layout.addWidget(self.custom_size_spin)

        layout.addWidget(custom_group)

        # Кнопки быстрого выбора
        quick_select_group = QGroupBox("Быстрый выбор")
        quick_layout = QHBoxLayout(quick_select_group)

        btn_all = QPushButton("Выбрать все")
        btn_all.clicked.connect(self.select_all)
        quick_layout.addWidget(btn_all)

        btn_recommended = QPushButton("Рекомендуемые")
        btn_recommended.clicked.connect(self.select_recommended)
        quick_layout.addWidget(btn_recommended)

        btn_clear = QPushButton("Очистить все")
        btn_clear.clicked.connect(self.clear_all)
        quick_layout.addWidget(btn_clear)

        layout.addWidget(quick_select_group)

        # Предварительный просмотр
        preview_label = QLabel("Будут созданы иконки следующих размеров:")
        preview_label.setFont(QFont("Arial", 10, QFont.Weight.Bold))
        layout.addWidget(preview_label)

        self.preview_text = QLabel()
        self.preview_text.setStyleSheet(
            "background-color: #f0f0f0; padding: 8px; border-radius: 4px;"
        )
        self.preview_text.setWordWrap(True)
        layout.addWidget(self.preview_text)

        # Обновляем предварительный просмотр при изменении выбора
        for checkbox in self.size_checkboxes.values():
            checkbox.toggled.connect(self.update_preview)
        self.custom_checkbox.toggled.connect(self.update_preview)
        self.custom_size_spin.valueChanged.connect(self.update_preview)

        # Изначальное обновление предварительного просмотра
        self.update_preview()

        # Кнопки диалога
        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

        self.setLayout(layout)

    def select_all(self):
        """Выбирает все размеры"""
        for checkbox in self.size_checkboxes.values():
            checkbox.setChecked(True)
        self.custom_checkbox.setChecked(True)

    def select_recommended(self):
        """Выбирает рекомендуемые размеры"""
        recommended = [16, 32, 48, 256]
        for size, checkbox in self.size_checkboxes.items():
            checkbox.setChecked(size in recommended)
        self.custom_checkbox.setChecked(False)

    def clear_all(self):
        """Очищает все выборы"""
        for checkbox in self.size_checkboxes.values():
            checkbox.setChecked(False)
        self.custom_checkbox.setChecked(False)

    def update_preview(self):
        """Обновляет предварительный просмотр выбранных размеров"""
        selected_sizes = self.get_selected_sizes()

        if selected_sizes:
            size_strings = [f"{size}×{size}" for size in selected_sizes]
            preview_text = f"Размеры: {', '.join(size_strings)}\nОбщее количество: {len(selected_sizes)} иконок"

            # Добавляем информацию о размере файла (приблизительно)
            estimated_size = len(selected_sizes) * 2  # Примерно 2КБ на иконку
            preview_text += f"\nПримерный размер файла: ~{estimated_size}КБ"
        else:
            preview_text = "Не выбрано ни одного размера"

        self.preview_text.setText(preview_text)

    def accept(self):
        """Переопределяем accept для проверки выбора"""
        selected_sizes = self.get_selected_sizes()
        if not selected_sizes:
            QMessageBox.warning(
                self,
                "Предупреждение",
                "Выберите хотя бы один размер иконки.\n"
                "Рекомендуется выбрать стандартные размеры: 16×16, 32×32, 48×48, 256×256",
            )
            return
        super().accept()

    def get_selected_sizes(self):
        """Возвращает список выбранных размеров"""
        selected_sizes = []

        # Добавляем стандартные размеры
        for size, checkbox in self.size_checkboxes.items():
            if checkbox.isChecked():
                selected_sizes.append(size)

        # Добавляем пользовательский размер
        if self.custom_checkbox.isChecked():
            custom_size = self.custom_size_spin.value()
            if custom_size not in selected_sizes:
                selected_sizes.append(custom_size)

        # Сортируем размеры
        selected_sizes.sort()
        return selected_sizes


class GraphicsEditor(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Редактор графических файлов v1.0")
        self.setWindowIcon(QIcon("img0.png"))
        #self.setMinimumSize(1000, 800)
        #self.resize(1200, 800)
        self.setGeometry(50, 50, 1400, 900)

        # Текущие параметры
        self.current_image_path = None
        self.brightness = 1.0
        self.contrast = 1.0
        self.saturation = 1.0
        self.recent_files = []

        # Настройки приложения
        self.settings = {"auto_save": False, "backup_count": 5, "default_format": "PNG"}

        self.init_ui()
        self.init_menu()
        self.init_toolbar()
        self.init_status_bar()

        # Таймер для автосохранения
        self.auto_save_timer = QTimer()
        self.auto_save_timer.timeout.connect(self.auto_save)

        # Таймер для проверки буфера обмена
        self.clipboard_timer = QTimer()
        self.clipboard_timer.timeout.connect(self.check_clipboard_status)
        self.clipboard_timer.start(2000)  # Проверяем каждые 2 секунды

        # Добавляем обработчик клавиш для основного окна
        self.installEventFilter(self)

        # Включаем поддержку drag&drop
        self.setAcceptDrops(True)
        self.canvas.setAcceptDrops(True)

    def init_ui(self):
        """Инициализация интерфейса"""
        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        # Основной лейаут
        main_layout = QHBoxLayout(central_widget)

        # Создаем сплиттер для панелей
        splitter = QSplitter(Qt.Orientation.Horizontal)
        main_layout.addWidget(splitter)

        # Панель файлового менеджера
        file_panel = self.create_file_panel()
        file_panel.setFixedWidth(250)
        file_panel.setMinimumWidth(250)
        file_panel.setMaximumWidth(250)
        splitter.addWidget(file_panel)

        # Центральная область редактирования
        edit_area = self.create_edit_area()
        splitter.addWidget(edit_area)

        # Панель настроек
        settings_panel = self.create_settings_panel()
        settings_panel.setFixedWidth(300)
        settings_panel.setMinimumWidth(300)
        settings_panel.setMaximumWidth(300)
        splitter.addWidget(settings_panel)

        # Устанавливаем пропорции панелей
        splitter.setSizes([100, 1300, 200])

    def create_file_panel(self):
        """Создает панель файлового менеджера"""
        panel = QWidget()
        layout = QVBoxLayout(panel)
        layout.setContentsMargins(8, 8, 8, 8)
        layout.setSpacing(6)

        # Заголовок
        title = QLabel("📁 Файловый менеджер")
        title.setFont(QFont("Arial", 12, QFont.Weight.Bold))
        title.setStyleSheet(
            "background-color: #e9ecef; padding: 6px; color: #495057; border: 1px solid #ced4da; border-radius: 7px;"
        )
        layout.addWidget(title)

        # Кнопки управления файлами
        btn_layout = QVBoxLayout()

        btn_load = QPushButton("🔍 Загрузить изображение")
        btn_load.setMaximumWidth(250)
        btn_load.clicked.connect(self.load_image)
        btn_load.setStyleSheet("""
            QPushButton { 
                padding: 8px; 
                background-color: #28a745; 
                color: white; 
                border-radius: 5px; 
                font-size: 11px;
                font-weight: bold;
            }
            QPushButton:hover { background-color: #218838; }
        """)
        btn_layout.addWidget(btn_load)

        btn_refresh = QPushButton("🔄 Обновить список")
        btn_refresh.setMaximumWidth(250)
        btn_refresh.clicked.connect(self.refresh_file_list)
        btn_refresh.setStyleSheet("""
            QPushButton { 
                padding: 8px; 
                background-color: #007bff; 
                color: white; 
                border-radius: 5px; 
                font-size: 11px;
                font-weight: bold;
            }
            QPushButton:hover { background-color: #0056b3; }
        """)
        btn_layout.addWidget(btn_refresh)

        btn_open_folder = QPushButton("📂 Открыть папку")
        btn_open_folder.setMaximumWidth(250)
        btn_open_folder.setToolTip("Открыть текущую папку в проводнике")
        btn_open_folder.clicked.connect(self.open_folder)
        btn_open_folder.setStyleSheet("""
            QPushButton { 
                padding: 8px; 
                background-color: #fd7e14; 
                color: white; 
                border-radius: 5px; 
                font-size: 11px;
                font-weight: bold;
            }
            QPushButton:hover { background-color: #e85d04; }
        """)
        btn_layout.addWidget(btn_open_folder)

        layout.addLayout(btn_layout)

        # Список файлов
        self.file_list = QListWidget()
        self.file_list.setMaximumWidth(300)
        self.file_list.itemClicked.connect(self.select_file)
        self.file_list.setStyleSheet("""
            QListWidget { 
                border: 1px solid #ced4da; 
                border-radius: 10px; 
                background-color: white;
                font-size: 11px;
            }
            QListWidget::item {
                padding: 4px;
            }
            QListWidget::item:selected {
                background-color: #007bff;
                color: white;
            }
            QListWidget::item:hover {
                background-color: #e3f2fd;
            }
        """)
        layout.addWidget(self.file_list)

        # Информация о текущей папке
        self.folder_info = QLabel("Папка: не выбрана")
        self.folder_info.setStyleSheet("color: #6c757d; font-size: 10px;")
        layout.addWidget(self.folder_info)

        # Загружаем начальный список файлов
        self.refresh_file_list()

        return panel

    def create_edit_area(self):
        """Создает область редактирования"""
        panel = QWidget()
        layout = QVBoxLayout(panel)
        layout.setContentsMargins(4, 4, 4, 4)
        layout.setSpacing(4)

        # Панель инструментов редактирования (только основные инструменты)
        toolbar = self.create_edit_toolbar()
        layout.addWidget(toolbar)

        # Холст для рисования в скролл-области
        scroll_area = QScrollArea()
        scroll_area.setStyleSheet(
            "QScrollArea { color: #495057; border: 1px solid #ced4da; border-radius: 7px; }"
        )

        self.canvas = DrawingCanvas()
        scroll_area.setWidget(self.canvas)
        scroll_area.setWidgetResizable(True)
        layout.addWidget(scroll_area)

        # Панель масштабирования
        zoom_layout = QHBoxLayout()
        zoom_layout.addWidget(QLabel("Масштаб:"))

        self.zoom_slider = QSlider(Qt.Orientation.Horizontal)
        self.zoom_slider.setRange(10, 500)  # От 10% до 500%
        self.zoom_slider.setValue(100)
        self.zoom_slider.valueChanged.connect(self.on_zoom_changed)
        self.zoom_slider.setToolTip("Перетащите для изменения масштаба (10%-500%)")
        zoom_layout.addWidget(self.zoom_slider)

        self.zoom_label = QLabel("100%")
        self.zoom_label.setMinimumWidth(50)
        zoom_layout.addWidget(self.zoom_label)

        # Кнопки быстрого масштабирования
        zoom_50_btn = QPushButton("50%")
        zoom_50_btn.clicked.connect(lambda: self.set_zoom(50))
        zoom_50_btn.setMaximumWidth(50)
        zoom_layout.addWidget(zoom_50_btn)

        zoom_100_btn = QPushButton("100%")
        zoom_100_btn.clicked.connect(lambda: self.set_zoom(100))
        zoom_100_btn.setMaximumWidth(50)
        zoom_layout.addWidget(zoom_100_btn)

        zoom_200_btn = QPushButton("200%")
        zoom_200_btn.clicked.connect(lambda: self.set_zoom(200))
        zoom_200_btn.setMaximumWidth(50)
        zoom_layout.addWidget(zoom_200_btn)

        layout.addLayout(zoom_layout)

        return panel

    def create_edit_toolbar(self):
        """Создает панель инструментов редактирования"""
        toolbar = QWidget()
        layout = QHBoxLayout(toolbar)
        layout.setContentsMargins(4, 4, 4, 4)
        layout.setSpacing(2)
        toolbar.setStyleSheet(
            "QWidget { background-color: #f0f0f0; border: 1px solid #ced4da; border-radius: 7px; padding: 3px; }"
        )

        # Группа кнопок инструментов
        self.tool_group = QButtonGroup()

        # Компактные кнопки инструментов
        tools = [
            ("cursor.png", "none", "Выбор"),
            ("brush_.png", "brush", "Кисть"),
            ("pen_.png", "pencil", "Карандаш"),
            ("eraser_.png", "eraser", "Ластик"),
            ("fill.png", "fill", "Заливка"),
            ("gradient.png", "gradient", "Градиент"),
            ("clone_.png", "clone", "Клон"),
            ("stamp.png", "stamp", "Штамп"),
            ("text_.png", "text", "Текст"),
            ("hand.png", "drag", "Перетаскивание"),
            ("rect.png", "select", "Выделить"),
            ("paste.png", "move", "Переместить"),
            ("scis.png", "crop", "Обрезка"),
        ]

        for icon, tool_name, tooltip in tools:
            btn = QPushButton("")
            btn.setIcon(QIcon(os.path.join("image", icon)))
            btn.setCheckable(True)
            btn.setChecked(tool_name == "none")
            btn.clicked.connect(lambda checked, t=tool_name: self.set_tool(t))
            btn.setToolTip(tooltip)
            btn.setMinimumWidth(32)
            btn.setMinimumHeight(32)
            btn.setMaximumWidth(40)
            btn.setMaximumHeight(40)
            btn.setStyleSheet("""
                QPushButton { 
                    padding: 2px; 
                    font-size: 12px; 
                    border: 1px solid #ced4da;
                    border-radius: 2px;
                    background-color: #f8f9fa;
                }
                QPushButton:checked { 
                    background-color: silver; 
                    color: white; 
                }
                QPushButton:hover { background-color: #e9ecef; }
                QPushButton:checked:hover { background-color: #0056b3; }
            """)
            self.tool_group.addButton(btn)
            layout.addWidget(btn)

        layout.addStretch()

        return toolbar

    def create_settings_panel(self):
        """Создает панель настроек"""
        panel = QWidget()
        layout = QVBoxLayout(panel)
        layout.setContentsMargins(8, 8, 8, 8)
        layout.setSpacing(6)

        # Заголовок
        title = QLabel("⚙️ Настройки")
        title.setFont(QFont("Arial", 12, QFont.Weight.Bold))
        title.setStyleSheet(
            "background-color: #f0f0f0; padding: 5px; border: 1px solid #ced4da; border-radius: 7px;"
        )
        layout.addWidget(title)

        # Вкладки настроек
        tabs = QTabWidget()

        # Вкладка "Инструменты"
        tools_tab = QWidget()
        tabs.setStyleSheet("""
            QTabWidget::pane { border: 1px solid #ced4da; border-radius: 10px; background-color: white; }
            QTabBar::tab { 
                padding: 4px 8px; 
                font-size: 11px;
                font-weight: bold; 
                background-color: #f8f9fa;
                border: 1px solid #ced4da;
                margin-right: 1px;
            }
            QTabBar::tab:selected { 
                background-color: #ced4da; 
                color: blue; 
            }
        """)
        tools_layout = QVBoxLayout(tools_tab)

        # Настройки кисти
        brush_group = QGroupBox("🖌️ Кисть")
        brush_layout = QVBoxLayout(brush_group)

        brush_layout.addWidget(QLabel("Размер кисти:"))
        self.brush_size_slider = QSlider(Qt.Orientation.Horizontal)
        self.brush_size_slider.setRange(1, 100)
        self.brush_size_slider.setValue(5)
        self.brush_size_slider.valueChanged.connect(self.change_brush_size)
        brush_layout.addWidget(self.brush_size_slider)

        self.brush_size_label = QLabel("5 px")
        brush_layout.addWidget(self.brush_size_label)

        btn_color = QPushButton("🎨 Выбрать цвет")
        btn_color.clicked.connect(self.choose_color)
        brush_layout.addWidget(btn_color)

        self.color_preview = QLabel()
        self.color_preview.setFixedSize(100, 30)
        self.color_preview.setStyleSheet(
            "background-color: black; border: 1px solid gray;"
        )
        brush_layout.addWidget(self.color_preview)

        tools_layout.addWidget(brush_group)

        # Настройки текста
        text_group = QGroupBox("📝 Текст")
        text_layout = QVBoxLayout(text_group)

        text_layout.addWidget(QLabel("Введите текст:"))
        self.text_input = QLineEdit()
        self.text_input.setPlaceholderText("Введите текст здесь...")
        text_layout.addWidget(self.text_input)

        btn_add_text = QPushButton("➕ Добавить текст")
        btn_add_text.clicked.connect(self.add_text)
        text_layout.addWidget(btn_add_text)

        text_layout.addWidget(QLabel("Размер шрифта:"))
        self.font_size_spin = QSpinBox()
        self.font_size_spin.setRange(8, 72)
        self.font_size_spin.setValue(20)
        self.font_size_spin.valueChanged.connect(self.change_font_size)
        text_layout.addWidget(self.font_size_spin)

        tools_layout.addWidget(text_group)

        # Настройки дополнительных инструментов
        advanced_tools_group = QGroupBox("🔧 Дополнительные инструменты")
        advanced_layout = QVBoxLayout(advanced_tools_group)

        # Настройки заливки
        advanced_layout.addWidget(QLabel("Цвет заливки:"))
        btn_fill_color = QPushButton("🎨 Выбрать цвет заливки")
        btn_fill_color.clicked.connect(self.choose_fill_color)
        advanced_layout.addWidget(btn_fill_color)

        self.fill_color_preview = QLabel()
        self.fill_color_preview.setFixedSize(100, 30)
        self.fill_color_preview.setStyleSheet(
            "background-color: white; border: 1px solid gray;"
        )
        advanced_layout.addWidget(self.fill_color_preview)

        # Настройки градиента
        advanced_layout.addWidget(QLabel("Градиент:"))
        btn_gradient_start = QPushButton("🌈 Начальный цвет")
        btn_gradient_start.clicked.connect(self.choose_gradient_start_color)
        advanced_layout.addWidget(btn_gradient_start)

        btn_gradient_end = QPushButton("🌈 Конечный цвет")
        btn_gradient_end.clicked.connect(self.choose_gradient_end_color)
        advanced_layout.addWidget(btn_gradient_end)

        # Настройки штампа
        advanced_layout.addWidget(QLabel("Штамп:"))
        btn_load_stamp = QPushButton("📁 Загрузить штамп")
        btn_load_stamp.clicked.connect(self.load_stamp_pattern)
        advanced_layout.addWidget(btn_load_stamp)

        tools_layout.addWidget(advanced_tools_group)
        tools_layout.addStretch()

        tabs.addTab(tools_tab, "Инструменты")

        # Вкладка "Фильтры"
        filters_tab = QWidget()
        filters_layout = QVBoxLayout(filters_tab)

        filters_group = QGroupBox("🎭 Базовые фильтры")
        filters_group_layout = QVBoxLayout(filters_group)

        # Яркость
        filters_group_layout.addWidget(QLabel("☀️ Яркость:"))
        self.brightness_slider = QSlider(Qt.Orientation.Horizontal)
        self.brightness_slider.setRange(0, 200)
        self.brightness_slider.setValue(100)
        self.brightness_slider.valueChanged.connect(self.change_brightness)
        filters_group_layout.addWidget(self.brightness_slider)

        self.brightness_label = QLabel("100%")
        filters_group_layout.addWidget(self.brightness_label)

        # Контрастность
        filters_group_layout.addWidget(QLabel("🌓 Контрастность:"))
        self.contrast_slider = QSlider(Qt.Orientation.Horizontal)
        self.contrast_slider.setRange(0, 200)
        self.contrast_slider.setValue(100)
        self.contrast_slider.valueChanged.connect(self.change_contrast)
        filters_group_layout.addWidget(self.contrast_slider)

        self.contrast_label = QLabel("100%")
        filters_group_layout.addWidget(self.contrast_label)

        # Насыщенность
        filters_group_layout.addWidget(QLabel("🎨 Насыщенность:"))
        self.saturation_slider = QSlider(Qt.Orientation.Horizontal)
        self.saturation_slider.setRange(0, 200)
        self.saturation_slider.setValue(100)
        self.saturation_slider.valueChanged.connect(self.change_saturation)
        filters_group_layout.addWidget(self.saturation_slider)

        self.saturation_label = QLabel("100%")
        filters_group_layout.addWidget(self.saturation_label)

        # Кнопка применения фильтров
        btn_apply_filters = QPushButton("✨ Применить фильтры")
        btn_apply_filters.clicked.connect(self.apply_filters)
        
        filters_group_layout.addWidget(btn_apply_filters)

        filters_layout.addWidget(filters_group)

        # Дополнительные фильтры
        advanced_filters_group = QGroupBox("🔍 Дополнительные фильтры")
        advanced_filters_layout = QVBoxLayout(advanced_filters_group)

        btn_unsharp_mask = QPushButton("⚡ Увеличение резкости")
        btn_unsharp_mask.clicked.connect(self.apply_unsharp_mask)
        advanced_filters_layout.addWidget(btn_unsharp_mask)

        btn_noise_reduction = QPushButton("🔇 Шумоподавление")
        btn_noise_reduction.clicked.connect(self.apply_noise_reduction)
        advanced_filters_layout.addWidget(btn_noise_reduction)

        btn_grayscale = QPushButton("⚫ Черно-белый")
        btn_grayscale.clicked.connect(self.apply_grayscale)
        advanced_filters_layout.addWidget(btn_grayscale)

        btn_add_noise = QPushButton("📡 Добавить шум")
        btn_add_noise.clicked.connect(self.apply_noise_filter)
        advanced_filters_layout.addWidget(btn_add_noise)

        btn_blur = QPushButton("🌫️ Размытие")
        btn_blur.clicked.connect(self.apply_blur)
        advanced_filters_layout.addWidget(btn_blur)

        btn_sharpen = QPushButton("🔍 Резкость")
        btn_sharpen.clicked.connect(self.apply_sharpen)
        advanced_filters_layout.addWidget(btn_sharpen)

        filters_layout.addWidget(advanced_filters_group)
        filters_layout.addStretch()

        tabs.addTab(filters_tab, "Фильтры")

        # Вкладка "Эффекты"
        effects_tab = QWidget()
        effects_layout = QVBoxLayout(effects_tab)

        # Художественные эффекты
        artistic_effects_group = QGroupBox("🎨 Художественные эффекты")
        artistic_layout = QVBoxLayout(artistic_effects_group)

        btn_sketch = QPushButton("✏️ Рисунок")
        btn_sketch.clicked.connect(self.apply_sketch_effect)
        artistic_layout.addWidget(btn_sketch)

        btn_glass = QPushButton("🪟 Стекло")
        btn_glass.clicked.connect(self.apply_glass_effect)
        artistic_layout.addWidget(btn_glass)

        btn_waves = QPushButton("🌊 Волны")
        btn_waves.clicked.connect(self.apply_wave_effect)
        artistic_layout.addWidget(btn_waves)

        btn_glow = QPushButton("✨ Свечение")
        btn_glow.clicked.connect(self.apply_glow_effect)
        artistic_layout.addWidget(btn_glow)

        btn_shadow = QPushButton("🌑 Тени")
        btn_shadow.clicked.connect(self.apply_shadow_effect)
        artistic_layout.addWidget(btn_shadow)

        effects_layout.addWidget(artistic_effects_group)

        # Коррекция цвета
        color_correction_group = QGroupBox("🎨 Коррекция цвета")
        color_layout = QVBoxLayout(color_correction_group)

        # Автоуровни
        btn_auto_levels = QPushButton("📊 Автоуровни")
        btn_auto_levels.clicked.connect(self.apply_auto_levels)
        color_layout.addWidget(btn_auto_levels)

        # Автоконтраст
        btn_auto_contrast = QPushButton("📈 Автоконтраст")
        btn_auto_contrast.clicked.connect(self.apply_auto_contrast)
        color_layout.addWidget(btn_auto_contrast)

        # Цветовой баланс
        color_layout.addWidget(QLabel("Баланс цветов:"))

        # Красный-Голубой
        color_layout.addWidget(QLabel("Красный-Голубой:"))
        self.red_cyan_slider = QSlider(Qt.Orientation.Horizontal)
        self.red_cyan_slider.setRange(-100, 100)
        self.red_cyan_slider.setValue(0)
        color_layout.addWidget(self.red_cyan_slider)

        # Зеленый-Пурпурный
        color_layout.addWidget(QLabel("Зеленый-Пурпурный:"))
        self.green_magenta_slider = QSlider(Qt.Orientation.Horizontal)
        self.green_magenta_slider.setRange(-100, 100)
        self.green_magenta_slider.setValue(0)
        color_layout.addWidget(self.green_magenta_slider)

        # Синий-Желтый
        color_layout.addWidget(QLabel("Синий-Желтый:"))
        self.blue_yellow_slider = QSlider(Qt.Orientation.Horizontal)
        self.blue_yellow_slider.setRange(-100, 100)
        self.blue_yellow_slider.setValue(0)
        color_layout.addWidget(self.blue_yellow_slider)

        btn_apply_color_balance = QPushButton("✨ Применить цветовой баланс")
        btn_apply_color_balance.clicked.connect(self.apply_color_balance)
        color_layout.addWidget(btn_apply_color_balance)

        effects_layout.addWidget(color_correction_group)

        # Специальные эффекты
        special_effects_group = QGroupBox("🎪 Специальные эффекты")
        special_layout = QVBoxLayout(special_effects_group)

        btn_remove_bg = QPushButton("🗑️ Убрать фон")
        btn_remove_bg.clicked.connect(self.remove_background)
        special_layout.addWidget(btn_remove_bg)

        effects_layout.addWidget(special_effects_group)

        # Конвертация форматов
        conversion_group = QGroupBox("🔄 Конвертация форматов")
        conversion_layout = QVBoxLayout(conversion_group)

        btn_convert_ico = QPushButton("🖼️ Конвертировать в ICO")
        btn_convert_ico.clicked.connect(self.convert_to_ico)
        conversion_layout.addWidget(btn_convert_ico)

        btn_convert_png = QPushButton("🖼️ Конвертировать в PNG")
        btn_convert_png.clicked.connect(self.convert_to_png)
        conversion_layout.addWidget(btn_convert_png)

        btn_convert_jpg = QPushButton("🖼️ Конвертировать в JPEG")
        btn_convert_jpg.clicked.connect(self.convert_to_jpg)
        conversion_layout.addWidget(btn_convert_jpg)

        effects_layout.addWidget(conversion_group)
        effects_layout.addStretch()

        tabs.addTab(effects_tab, "Эффекты")

        # Вкладка "Информация"
        info_tab = QWidget()
        info_layout = QVBoxLayout(info_tab)

        self.file_info = QGroupBox("📊 Информация о файле")
        file_info_layout = QVBoxLayout(self.file_info)

        self.file_name_label = QLabel("Файл: не выбран")
        self.file_size_label = QLabel("Размер: —")
        self.file_format_label = QLabel("Формат: —")
        self.file_dimensions_label = QLabel("Разрешение: —")

        file_info_layout.addWidget(self.file_name_label)
        file_info_layout.addWidget(self.file_size_label)
        file_info_layout.addWidget(self.file_format_label)
        file_info_layout.addWidget(self.file_dimensions_label)

        info_layout.addWidget(self.file_info)

        # Статус инструментов
        self.tools_status = QGroupBox("🛠️ Статус инструментов")
        status_layout = QVBoxLayout(self.tools_status)

        self.current_tool_label = QLabel("Инструмент: не выбран")
        self.selection_status_label = QLabel("Выделение: нет")
        self.clipboard_status_label = QLabel("Буфер обмена: пуст")
        self.fragment_status_label = QLabel("Фрагмент: нет")

        status_layout.addWidget(self.current_tool_label)
        status_layout.addWidget(self.selection_status_label)
        status_layout.addWidget(self.clipboard_status_label)
        status_layout.addWidget(self.fragment_status_label)

        info_layout.addWidget(self.tools_status)

        # История изменений
        self.history_group = QGroupBox("📖 История изменений")
        history_layout = QVBoxLayout(self.history_group)

        self.history_label = QLabel("Шагов в истории: 0")
        self.history_position_label = QLabel("Текущая позиция: 0")

        history_layout.addWidget(self.history_label)
        history_layout.addWidget(self.history_position_label)

        # Кнопки для работы с историей
        history_buttons_layout = QHBoxLayout()

        self.btn_undo = QPushButton(QIcon(os.path.join("image", "arrowleft.png")), "Отменить")
        self.btn_undo.clicked.connect(self.undo)
        self.btn_undo.setEnabled(False)
        history_buttons_layout.addWidget(self.btn_undo)

        self.btn_redo = QPushButton(QIcon(os.path.join("image", "arrowright.png")), "Повторить")
        self.btn_redo.clicked.connect(self.redo)
        self.btn_redo.setEnabled(False)
        history_buttons_layout.addWidget(self.btn_redo)

        history_layout.addLayout(history_buttons_layout)

        info_layout.addWidget(self.history_group)
        info_layout.addStretch()

        tabs.addTab(info_tab, "Информация")

        layout.addWidget(tabs)

        return panel

    def init_menu(self):
        """Инициализация меню"""
        menubar = self.menuBar()

        # Меню "Файл"
        file_menu = menubar.addMenu("Файл")

        new_action = QAction(
            QIcon(os.path.join("image", "editfile.png")), "Создать", self
        )
        new_action.setShortcut(QKeySequence.StandardKey.New)
        new_action.triggered.connect(self.new_image)
        file_menu.addAction(new_action)

        open_action = QAction(
            QIcon(os.path.join("image", "folder.png")), "Открыть", self
        )
        open_action.setShortcut(QKeySequence.StandardKey.Open)
        open_action.triggered.connect(self.load_image)
        file_menu.addAction(open_action)

        file_menu.addSeparator()

        save_action = QAction(
            QIcon(os.path.join("image", "save.png")), "Сохранить", self
        )
        save_action.setShortcut(QKeySequence.StandardKey.Save)
        save_action.triggered.connect(self.save_image)
        file_menu.addAction(save_action)

        save_as_action = QAction(
            QIcon(os.path.join("image", "saveas.png")), "Сохранить как...", self
        )
        save_as_action.setShortcut(QKeySequence.StandardKey.SaveAs)
        save_as_action.triggered.connect(self.save_image_as)
        file_menu.addAction(save_as_action)

        file_menu.addSeparator()

        exit_action = QAction(
            QIcon(os.path.join("image", "exit.png")), "Выход", self
        )
        exit_action.setShortcut(QKeySequence.StandardKey.Quit)
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)

        # Меню "Редактирование"
        edit_menu = menubar.addMenu("Редактирование")

        undo_action = QAction(
            QIcon(os.path.join("image", "arrowleft.png")), "Отменить", self
        )
        undo_action.setShortcut(QKeySequence.StandardKey.Undo)
        undo_action.triggered.connect(self.undo)
        edit_menu.addAction(undo_action)

        redo_action = QAction(
            QIcon(os.path.join("image", "arrowright.png")), "Повторить", self
        )
        redo_action.setShortcut(QKeySequence.StandardKey.Redo)
        redo_action.triggered.connect(self.redo)
        edit_menu.addAction(redo_action)

        edit_menu.addSeparator()

        copy_action = QAction(
            QIcon(os.path.join("image", "copyimage.png")),
            "Копировать выделенную область",
            self,
        )
        copy_action.setShortcut("Ctrl+Shift+C")  # Изменили на уникальное сочетание
        copy_action.triggered.connect(self.copy_selection)
        edit_menu.addAction(copy_action)

        paste_action = QAction(
            QIcon(os.path.join("image", "paste.png")),
            "Вставить из буфера обмена",
            self,
        )
        paste_action.setShortcut("Ctrl+Shift+V")  # Изменили на уникальное сочетание
        paste_action.triggered.connect(self.paste_from_clipboard)
        edit_menu.addAction(paste_action)

        edit_menu.addSeparator()

        reset_action = QAction(
            QIcon(os.path.join("image", "cancel.png")), "Сбросить изменения", self
        )
        reset_action.setShortcut("Ctrl+R")
        reset_action.triggered.connect(self.reset_image)
        edit_menu.addAction(reset_action)

        # Меню "Изображение"
        image_menu = menubar.addMenu("Изображение")

        resize_action = QAction(
            QIcon(os.path.join("image", "remsize.png")), "Изменить размер", self
        )
        resize_action.triggered.connect(self.resize_image)
        image_menu.addAction(resize_action)

        actual_size_action = QAction(
            QIcon(os.path.join("image", "originalsize.png")), "Показать реальный размер", self
        )
        actual_size_action.setShortcut("Ctrl+1")
        actual_size_action.triggered.connect(self.show_actual_size)
        image_menu.addAction(actual_size_action)

        image_menu.addSeparator()

        # Подменю конвертации
        convert_menu = image_menu.addMenu(
            QIcon(os.path.join("image", "imageconv.png")), "Конвертирование"
        )

        convert_to_ico_action = QAction(QIcon(os.path.join("image", "ico.png")), "Конвертировать в ICO", self)
        convert_to_ico_action.triggered.connect(self.convert_to_ico)
        convert_menu.addAction(convert_to_ico_action)

        convert_to_png_action = QAction(QIcon(os.path.join("image", "png.png")), "Конвертировать в PNG", self)
        convert_to_png_action.triggered.connect(self.convert_to_png)
        convert_menu.addAction(convert_to_png_action)

        convert_to_jpg_action = QAction(QIcon(os.path.join("image", "jpg.png")), "Конвертировать в JPEG", self)
        convert_to_jpg_action.triggered.connect(self.convert_to_jpg)
        convert_menu.addAction(convert_to_jpg_action)

        rotate_menu = image_menu.addMenu(
            QIcon(os.path.join("image", "turn.png")), "Поворот"
        )

        rotate_90_action = QAction(
            QIcon(os.path.join("image", "rotate.png")), "90° по часовой", self
        )
        rotate_90_action.triggered.connect(lambda: self.rotate_image(90))
        rotate_menu.addAction(rotate_90_action)

        rotate_180_action = QAction(
            QIcon(os.path.join("image", "rotate.png")), "180° по часовой", self
        )
        rotate_180_action.triggered.connect(lambda: self.rotate_image(180))
        rotate_menu.addAction(rotate_180_action)

        rotate_270_action = QAction(
            QIcon(os.path.join("image", "rotate.png")), "270° по часовой", self
        )
        rotate_270_action.triggered.connect(lambda: self.rotate_image(270))
        rotate_menu.addAction(rotate_270_action)

        flip_menu = image_menu.addMenu(
            QIcon(os.path.join("image", "mirror.png")), "Отражение"
        )

        flip_h_action = QAction(
            QIcon(os.path.join("image", "flip1.png")), "Горизонтально", self
        )
        flip_h_action.triggered.connect(lambda: self.flip_image(True))
        flip_menu.addAction(flip_h_action)

        flip_v_action = QAction(
            QIcon(os.path.join("image", "flip2.png")), "Вертикально", self
        )
        flip_v_action.triggered.connect(lambda: self.flip_image(False))
        flip_menu.addAction(flip_v_action)

        # Меню "Инструменты"
        tools_menu = menubar.addMenu("Инструменты")

        brush_action = QAction(
            QIcon(os.path.join("image", "brush_.png")), "Кисть", self
        )
        brush_action.setShortcut("B")
        brush_action.triggered.connect(lambda: self.set_tool("brush"))
        tools_menu.addAction(brush_action)

        pencil_action = QAction(
            QIcon(os.path.join("image", "pen_.png")), "Карандаш", self
        )
        pencil_action.setShortcut("P")
        pencil_action.triggered.connect(lambda: self.set_tool("pencil"))
        tools_menu.addAction(pencil_action)

        text_action = QAction(
            QIcon(os.path.join("image", "text_.png")), "Текст", self
        )
        text_action.setShortcut("T")
        text_action.triggered.connect(lambda: self.set_tool("text"))
        tools_menu.addAction(text_action)

        crop_tool_action = QAction(
            QIcon(os.path.join("image", "scis.png")), "Обрезка", self
        )
        crop_tool_action.setShortcut("C")
        crop_tool_action.triggered.connect(lambda: self.set_tool("crop"))
        tools_menu.addAction(crop_tool_action)

        # Меню "Помощь"
        help_menu = menubar.addMenu("Помощь")

        about_action = QAction(
            QIcon(os.path.join("image", "info.png")), "О программе", self
        )
        about_action.triggered.connect(self.show_about)
        help_menu.addAction(about_action)

        help_action = QAction(
            QIcon(os.path.join("image", "help.png")), "Справка", self
        )
        help_action.setShortcut(QKeySequence.StandardKey.HelpContents)
        help_action.triggered.connect(self.show_help)
        help_menu.addAction(help_action)

    def init_toolbar(self):
        """Инициализация панели инструментов"""
        toolbar = self.addToolBar("Главная")
        toolbar.setToolButtonStyle(Qt.ToolButtonStyle.ToolButtonTextBesideIcon)
        toolbar.setIconSize(QSize(20, 20))

        # Файловые операции
        new_action = QAction(QIcon(os.path.join("image", "editfile.png")), "", self)
        new_action.setToolTip("Создать новое изображение")
        new_action.triggered.connect(self.new_image)
        toolbar.addAction(new_action)

        open_action = QAction(QIcon(os.path.join("image", "folder.png")), "", self)
        open_action.setToolTip("Открыть изображение")
        open_action.triggered.connect(self.load_image)
        toolbar.addAction(open_action)

        save_action = QAction(QIcon(os.path.join("image", "save.png")), "", self)
        save_action.setToolTip("Сохранить изображение")
        save_action.triggered.connect(self.save_image)
        toolbar.addAction(save_action)

        toolbar.addSeparator()

        # История действий
        self.toolbar_undo_action = QAction(
            QIcon(os.path.join("image", "arrowleft.png")), "", self
        )
        self.toolbar_undo_action.setToolTip("Отменить")
        self.toolbar_undo_action.triggered.connect(self.undo)
        self.toolbar_undo_action.setEnabled(False)
        toolbar.addAction(self.toolbar_undo_action)

        self.toolbar_redo_action = QAction(
            QIcon(os.path.join("image", "arrowright.png")), "", self
        )
        self.toolbar_redo_action.setToolTip("Повторить")
        self.toolbar_redo_action.triggered.connect(self.redo)
        self.toolbar_redo_action.setEnabled(False)
        toolbar.addAction(self.toolbar_redo_action)

        toolbar.addSeparator()

        # Буфер обмена
        copy_action = QAction(QIcon(os.path.join("image", "copy.png")), "", self)
        copy_action.setToolTip("Копировать выделенную область (Ctrl+Shift+C)")
        copy_action.setShortcut("Ctrl+Shift+C")
        copy_action.triggered.connect(self.copy_selection)
        toolbar.addAction(copy_action)

        paste_action = QAction(QIcon(os.path.join("image", "paste.png")), "", self)
        paste_action.setToolTip("Вставить из буфера обмена (Ctrl+Shift+V)")
        paste_action.setShortcut("Ctrl+Shift+V")
        paste_action.triggered.connect(self.paste_from_clipboard)
        toolbar.addAction(paste_action)

        toolbar.addSeparator()

        # Быстрые инструменты
        brush_action = QAction(QIcon(os.path.join("image", "brush_.png")), "", self)
        brush_action.setToolTip("Кисть")
        brush_action.triggered.connect(lambda: self.set_tool("brush"))
        toolbar.addAction(brush_action)

        pencil_action = QAction(QIcon(os.path.join("image", "pen_.png")), "", self)
        pencil_action.setToolTip("Карандаш")
        pencil_action.triggered.connect(lambda: self.set_tool("pencil"))
        toolbar.addAction(pencil_action)

        text_action = QAction(QIcon(os.path.join("image", "text_.png")), "", self)
        text_action.setToolTip("Текст")
        text_action.triggered.connect(lambda: self.set_tool("text"))
        toolbar.addAction(text_action)

        select_action = QAction(QIcon(os.path.join("image", "rect.png")), "", self)
        select_action.setToolTip("Выделение")
        select_action.triggered.connect(lambda: self.set_tool("select"))
        toolbar.addAction(select_action)

        crop_action = QAction(QIcon(os.path.join("image", "scis.png")), "", self)
        crop_action.setToolTip("Обрезка (C)")
        crop_action.triggered.connect(lambda: self.set_tool("crop"))
        toolbar.addAction(crop_action)

        toolbar.addSeparator()

        # Быстрые эффекты
        blur_action = QAction(QIcon(os.path.join("image", "blur.png")), "", self)
        blur_action.setToolTip("Размытие")
        blur_action.triggered.connect(self.apply_blur)
        toolbar.addAction(blur_action)

        sharpen_action = QAction(QIcon(os.path.join("image", "shapes.png")), "", self)
        sharpen_action.setToolTip("Резкость")
        sharpen_action.triggered.connect(self.apply_sharpen)
        toolbar.addAction(sharpen_action)

        rotate_action = QAction(QIcon(os.path.join("image", "90.png")), "", self)
        rotate_action.setToolTip("Повернуть на 90°")
        rotate_action.triggered.connect(lambda: self.rotate_image(90))
        toolbar.addAction(rotate_action)

        toolbar.addSeparator()

        # Конвертация форматов
        ico_action = QAction(QIcon(os.path.join("image", "ico.png")), "", self)
        ico_action.setToolTip("Конвертировать в ICO")
        ico_action.triggered.connect(self.convert_to_ico)
        toolbar.addAction(ico_action)

    def init_status_bar(self):
        """Инициализация статусной строки"""
        self.status_bar = self.statusBar()
        self.status_bar.showMessage("Готов к работе")

        # Прогресс-бар
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        self.progress_bar.setMaximumWidth(200)
        self.status_bar.addPermanentWidget(self.progress_bar)

        # Информация о масштабе
        self.zoom_status = QLabel("Масштаб: 100%")
        self.status_bar.addPermanentWidget(self.zoom_status)

        # Координаты мыши
        self.mouse_pos_label = QLabel("Позиция: —")
        self.status_bar.addPermanentWidget(self.mouse_pos_label)

    def refresh_file_list(self):
        """Обновляет список файлов"""
        self.file_list.clear()

        # Получаем текущую директорию
        current_dir = os.getcwd()

        # Поддерживаемые форматы
        supported_formats = [
            ".jpg",
            ".jpeg",
            ".png",
            ".bmp",
            ".gif",
            ".tiff",
            ".webp",
            ".ico",
        ]

        try:
            files = []
            for filename in os.listdir(current_dir):
                if any(filename.lower().endswith(ext) for ext in supported_formats):
                    files.append(filename)

            # Сортируем файлы по имени
            files.sort()

            for filename in files:
                item = QListWidgetItem(f"🖼️ {filename}")
                item.setData(
                    Qt.ItemDataRole.UserRole, os.path.join(current_dir, filename)
                )
                self.file_list.addItem(item)

            self.folder_info.setText(f"Папка: {current_dir} ({len(files)} файлов)")

        except Exception as e:
            self.status_bar.showMessage(f"Ошибка чтения директории: {e}")

    def open_folder(self):
        """Открывает диалог выбора папки"""
        folder = QFileDialog.getExistingDirectory(
            self, "Выберите папку с изображениями"
        )
        if folder:
            os.chdir(folder)
            self.refresh_file_list()

    def select_file(self, item):
        """Выбирает файл из списка"""
        file_path = item.data(Qt.ItemDataRole.UserRole)
        self.load_image_from_path(file_path)

    def new_image(self):
        """Создает новое изображение"""
        # Диалог для выбора размера нового изображения
        dialog = ResizeDialog(QSize(800, 600), self)
        dialog.setWindowTitle("Создать новое изображение")

        if dialog.exec() == QDialog.DialogCode.Accepted:
            size = dialog.get_size()

            # Создаем новое изображение
            new_image = QPixmap(size)
            new_image.fill(Qt.GlobalColor.white)

            self.canvas.set_image(new_image)
            self.current_image_path = None

            # Сбрасываем слайдеры
            self.reset_sliders()

            # Обновляем информацию о файле
            self.update_file_info("Новое изображение", size)

            # Обновляем историю
            self.update_history_ui()

            self.status_bar.showMessage("Создано новое изображение")

    def load_image(self):
        """Загружает изображение из диалога"""
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Выберите изображение",
            "",
            "Изображения (*.png *.jpg *.jpeg *.bmp *.gif *.tiff *.webp *.ico);;Все файлы (*.*)",
        )

        if file_path:
            self.load_image_from_path(file_path)

    def load_image_from_path(self, file_path):
        """Загружает изображение по пути"""
        try:
            # Показываем прогресс
            self.progress_bar.setVisible(True)
            self.progress_bar.setValue(0)

            # Создаем поток для загрузки
            self.processor = ImageProcessor(file_path, operation="load")
            self.processor.progress.connect(self.progress_bar.setValue)
            self.processor.finished.connect(self.on_image_loaded)
            self.processor.error.connect(self.on_processing_error)
            self.processor.start()

            self.current_image_path = file_path

            # Добавляем файл в список, если его там нет
            filename = os.path.basename(file_path)
            file_exists = False
            for item_index in range(self.file_list.count()):
                item = self.file_list.item(item_index)
                if item.data(Qt.ItemDataRole.UserRole) == file_path:
                    file_exists = True
                    # Выделяем существующий файл
                    self.file_list.setCurrentItem(item)
                    break

            if not file_exists:
                # Добавляем новый файл в список
                item = QListWidgetItem(f"🖼️ {filename}")
                item.setData(Qt.ItemDataRole.UserRole, file_path)
                self.file_list.addItem(item)
                self.file_list.setCurrentItem(item)
                self.status_bar.showMessage(f"Файл добавлен в список: {filename}")

        except Exception as e:
            QMessageBox.critical(self, "Ошибка", f"Ошибка загрузки изображения: {e}")

    def on_image_loaded(self, pixmap):
        """Обработчик успешной загрузки изображения"""
        self.canvas.set_image(pixmap)

        # Сбрасываем слайдеры
        self.reset_sliders()

        # Обновляем информацию о файле
        if self.current_image_path:
            self.update_file_info_from_path(self.current_image_path)

        # Обновляем историю
        self.update_history_ui()

        self.progress_bar.setVisible(False)
        self.status_bar.showMessage(
            f"Загружено: {os.path.basename(self.current_image_path)}"
        )

    def on_processing_error(self, error_msg):
        """Обработчик ошибок при обработке изображения"""
        self.progress_bar.setVisible(False)
        QMessageBox.critical(
            self, "Ошибка", f"Ошибка обработки изображения: {error_msg}"
        )

    def update_file_info_from_path(self, file_path):
        """Обновляет информацию о файле по пути"""
        try:
            file_info = os.stat(file_path)
            file_size = file_info.st_size / (1024 * 1024)  # В мегабайтах

            # Получаем размеры изображения
            with Image.open(file_path) as img:
                width, height = img.size

            self.update_file_info(
                os.path.basename(file_path), QSize(width, height), file_size
            )

        except Exception as e:
            print(f"Ошибка получения информации о файле: {e}")

    def update_file_info(self, filename, size, file_size_mb=None):
        """Обновляет информацию о файле"""
        self.file_name_label.setText(f"Файл: {filename}")
        self.file_dimensions_label.setText(
            f"Разрешение: {size.width()}×{size.height()}"
        )

        if file_size_mb is not None:
            self.file_size_label.setText(f"Размер: {file_size_mb:.2f} МБ")

        if self.current_image_path:
            ext = os.path.splitext(self.current_image_path)[1].upper()
            self.file_format_label.setText(f"Формат: {ext}")

    def save_image(self):
        """Сохраняет изображение"""
        if not self.canvas.image:
            QMessageBox.warning(
                self, "Предупреждение", "Нет изображения для сохранения"
            )
            return

        if self.current_image_path:
            # Сохраняем в тот же файл
            try:
                self.canvas.image.save(self.current_image_path)
                self.status_bar.showMessage(
                    f"Сохранено: {os.path.basename(self.current_image_path)}"
                )
                QMessageBox.information(self, "Успех", "Изображение успешно сохранено")
            except Exception as e:
                QMessageBox.critical(self, "Ошибка", f"Ошибка сохранения: {e}")
        else:
            # Если файл новый, вызываем "Сохранить как"
            self.save_image_as()

    def save_image_as(self):
        """Сохраняет изображение с выбором имени"""
        if not self.canvas.image:
            QMessageBox.warning(
                self, "Предупреждение", "Нет изображения для сохранения"
            )
            return

        file_path, _ = QFileDialog.getSaveFileName(
            self,
            "Сохранить изображение",
            "",
            "PNG (*.png);;JPEG (*.jpg);;BMP (*.bmp);;TIFF (*.tiff);;Все файлы (*.*)",
        )

        if file_path:
            try:
                self.canvas.image.save(file_path)
                self.current_image_path = file_path
                self.status_bar.showMessage(f"Сохранено: {os.path.basename(file_path)}")
                QMessageBox.information(self, "Успех", "Изображение успешно сохранено")

                # Обновляем информацию о файле
                self.update_file_info_from_path(file_path)

            except Exception as e:
                QMessageBox.critical(self, "Ошибка", f"Ошибка сохранения: {e}")

    def auto_save(self):
        """Автоматическое сохранение"""
        if self.settings["auto_save"] and self.current_image_path:
            backup_path = self.current_image_path + ".backup"
            try:
                self.canvas.image.save(backup_path)
                self.status_bar.showMessage("Автосохранение выполнено", 2000)
            except Exception as e:
                print(f"Ошибка автосохранения: {e}")

    def set_tool(self, tool):
        """Устанавливает текущий инструмент"""
        self.canvas.set_tool(tool)
        tool_names = {
            "none": "Выбор",
            "brush": "Кисть",
            "pencil": "Карандаш",
            "eraser": "Ластик",
            "fill": "Заливка",
            "gradient": "Градиент",
            "clone": "Клонирование",
            "stamp": "Штамп",
            "text": "Текст",
            "drag": "Перетаскивание",
            "select": "Выделение",
            "move": "Перемещение",
            "crop": "Обрезка",
        }
        tool_name = tool_names.get(tool, tool)
        self.status_bar.showMessage(f"Выбран инструмент: {tool_name}")
        self.current_tool_label.setText(f"Инструмент: {tool_name}")

    def copy_selection(self):
        """Копирует выделенную область"""
        if self.canvas.copy_selected_area():
            self.status_bar.showMessage(
                "Область скопирована в буфер обмена (системный и внутренний)"
            )
            self.clipboard_status_label.setText("Буфер обмена: есть данные")
            self.selection_status_label.setText("Выделение: нет")
        else:
            QMessageBox.warning(
                self,
                "Предупреждение",
                "Сначала выделите область для копирования.\n\n"
                "Для выделения:\n"
                "1. Выберите инструмент 'Выделить'\n"
                "2. Кликните и перетащите мышь по изображению\n"
                "3. Отпустите кнопку мыши\n"
                "4. Нажмите 'Копировать' или Ctrl+Shift+C",
            )

    def paste_from_clipboard(self):
        """Вставляет из буфера обмена"""
        if self.canvas.paste_from_clipboard():
            self.status_bar.showMessage("Изображение вставлено из буфера обмена")
            self.fragment_status_label.setText("Фрагмент: вставлен")
            self.current_tool_label.setText("Инструмент: Перемещение")
            # Переключаем инструмент на перемещение в интерфейсе
            self.set_tool("move")
        else:
            QMessageBox.warning(
                self,
                "Предупреждение",
                "В буфере обмена нет изображения.\n\n"
                "Для вставки:\n"
                "1. Скопируйте изображение в другой программе (Ctrl+C)\n"
                "2. Или выделите и скопируйте область в этом редакторе (Ctrl+Shift+C)\n"
                "3. Затем используйте 'Вставить' или Ctrl+Shift+V",
            )

    def update_history_ui(self):
        """Обновляет интерфейс истории"""
        total_steps = len(self.canvas.history)
        current_pos = self.canvas.history_index + 1

        self.history_label.setText(f"Шагов в истории: {total_steps}")
        self.history_position_label.setText(f"Текущая позиция: {current_pos}")

        # Обновляем состояние кнопок
        can_undo = self.canvas.can_undo()
        can_redo = self.canvas.can_redo()

        self.btn_undo.setEnabled(can_undo)
        self.btn_redo.setEnabled(can_redo)

        # Обновляем кнопки на панели инструментов
        self.toolbar_undo_action.setEnabled(can_undo)
        self.toolbar_redo_action.setEnabled(can_redo)

    def change_brush_size(self, value):
        """Изменяет размер кисти"""
        self.canvas.set_brush_size(value)
        self.brush_size_label.setText(f"{value} px")

    def choose_color(self):
        """Выбирает цвет кисти"""
        color = QColorDialog.getColor()
        if color.isValid():
            self.canvas.set_brush_color(color)
            self.color_preview.setStyleSheet(
                f"background-color: {color.name()}; border: 1px solid gray;"
            )

    def choose_fill_color(self):
        """Выбирает цвет заливки"""
        color = QColorDialog.getColor()
        if color.isValid():
            self.canvas.set_fill_color(color)
            self.fill_color_preview.setStyleSheet(
                f"background-color: {color.name()}; border: 1px solid gray;"
            )

    def choose_gradient_start_color(self):
        """Выбирает начальный цвет градиента"""
        color = QColorDialog.getColor()
        if color.isValid():
            self.canvas.gradient_start_color = color

    def choose_gradient_end_color(self):
        """Выбирает конечный цвет градиента"""
        color = QColorDialog.getColor()
        if color.isValid():
            self.canvas.gradient_end_color = color

    def load_stamp_pattern(self):
        """Загружает паттерн для штампа"""
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Выберите изображение для штампа",
            "",
            "Изображения (*.png *.jpg *.jpeg *.bmp *.gif);;Все файлы (*.*)",
        )

        if file_path:
            try:
                stamp_pixmap = QPixmap(file_path)
                # Масштабируем штамп до разумного размера
                if stamp_pixmap.width() > 100 or stamp_pixmap.height() > 100:
                    stamp_pixmap = stamp_pixmap.scaled(
                        100,
                        100,
                        Qt.AspectRatioMode.KeepAspectRatio,
                        Qt.TransformationMode.SmoothTransformation,
                    )
                self.canvas.set_stamp_pattern(stamp_pixmap)
                self.status_bar.showMessage("Штамп загружен")
            except Exception as e:
                QMessageBox.critical(self, "Ошибка", f"Ошибка загрузки штампа: {e}")

    def change_font_size(self, value):
        """Изменяет размер шрифта"""
        self.canvas.text_font.setPointSize(value)

    def add_text(self):
        """Добавляет текст на изображение"""
        text = self.text_input.text()
        if text and self.canvas.image:
            # Добавляем текст в центр изображения, если инструмент не активен
            if self.canvas.current_tool != "text":
                center_pos = QPoint(
                    self.canvas.image.width() // 2, self.canvas.image.height() // 2
                )
                self.canvas.add_text(text, center_pos)
            else:
                # Если инструмент текста активен, добавляем в последнюю установленную позицию
                self.canvas.add_text(text)
            self.text_input.clear()
            self.status_bar.showMessage("Текст добавлен")
        elif not self.canvas.image:
            QMessageBox.warning(self, "Предупреждение", "Сначала загрузите изображение")
        else:
            QMessageBox.warning(self, "Предупреждение", "Введите текст для добавления")

    def change_brightness(self, value):
        """Изменяет яркость"""
        self.brightness = value / 100.0
        self.brightness_label.setText(f"{value}%")

    def change_contrast(self, value):
        """Изменяет контрастность"""
        self.contrast = value / 100.0
        self.contrast_label.setText(f"{value}%")

    def change_saturation(self, value):
        """Изменяет насыщенность"""
        self.saturation = value / 100.0
        self.saturation_label.setText(f"{value}%")

    def apply_filters(self):
        """Применяет фильтры к изображению"""
        if not self.canvas.image:
            QMessageBox.warning(self, "Предупреждение", "Сначала загрузите изображение")
            return

        if not self.current_image_path:
            QMessageBox.warning(
                self, "Предупреждение", "Нет пути к изображению для применения фильтров"
            )
            return

        # Показываем прогресс-бар
        self.progress_bar.setVisible(True)
        self.progress_bar.setValue(0)

        # Создаем и запускаем поток обработки
        self.processor = ImageProcessor(
            self.current_image_path,
            operation="filters",
            brightness=self.brightness,
            contrast=self.contrast,
            saturation=self.saturation,
        )
        self.processor.progress.connect(self.progress_bar.setValue)
        self.processor.finished.connect(self.on_filters_applied)
        self.processor.error.connect(self.on_processing_error)
        self.processor.start()

    def on_filters_applied(self, pixmap):
        """Обработчик завершения применения фильтров"""
        if not self.canvas.image:
            return
        self.canvas.add_to_history()
        self.canvas.image = pixmap
        self.canvas.update_display()
        self.progress_bar.setVisible(False)
        self.status_bar.showMessage("Фильтры применены")
        self.update_history_ui()

    def apply_blur(self):
        """Применяет размытие"""
        if not self.current_image_path:
            QMessageBox.warning(self, "Предупреждение", "Сначала загрузите изображение")
            return

        self.progress_bar.setVisible(True)
        self.processor = ImageProcessor(
            self.current_image_path, operation="blur", radius=2
        )
        self.processor.progress.connect(self.progress_bar.setValue)
        self.processor.finished.connect(self.on_effect_applied)
        self.processor.error.connect(self.on_processing_error)
        self.processor.start()

    def apply_sharpen(self):
        """Применяет резкость"""
        if not self.current_image_path:
            QMessageBox.warning(self, "Предупреждение", "Сначала загрузите изображение")
            return

        self.progress_bar.setVisible(True)
        self.processor = ImageProcessor(self.current_image_path, operation="sharpen")
        self.processor.progress.connect(self.progress_bar.setValue)
        self.processor.finished.connect(self.on_effect_applied)
        self.processor.error.connect(self.on_processing_error)
        self.processor.start()

    def on_effect_applied(self, pixmap):
        """Обработчик завершения применения эффекта"""
        if not self.canvas.image:
            return
        self.canvas.add_to_history()
        self.canvas.image = pixmap
        self.canvas.update_display()
        self.progress_bar.setVisible(False)
        self.status_bar.showMessage("Эффект применен")
        self.update_history_ui()

    def remove_background(self):
        """Удаляет фон"""
        if not self.canvas.image:
            QMessageBox.warning(self, "Предупреждение", "Сначала загрузите изображение")
            return

        # Если есть путь к файлу, используем поток обработки
        if self.current_image_path:
            self.progress_bar.setVisible(True)
            self.processor = ImageProcessor(
                self.current_image_path, operation="remove_background"
            )
            self.processor.progress.connect(self.progress_bar.setValue)
            self.processor.finished.connect(self.on_background_removed)
            self.processor.error.connect(self.on_processing_error)
            self.processor.start()
        else:
            # Если нет пути, применяем удаление фона к текущему изображению
            self.canvas.remove_background()
            self.update_history_ui()

    def on_background_removed(self, pixmap):
        """Обработчик завершения удаления фона"""
        if not self.canvas.image:
            return
        self.canvas.add_to_history()
        self.canvas.image = pixmap
        self.canvas.update_display()
        self.progress_bar.setVisible(False)
        self.status_bar.showMessage("Фон удален")
        self.update_history_ui()

    def apply_unsharp_mask(self):
        """Применяет увеличение резкости"""
        if not self.current_image_path:
            QMessageBox.warning(self, "Предупреждение", "Сначала загрузите изображение")
            return

        self.progress_bar.setVisible(True)
        self.processor = ImageProcessor(
            self.current_image_path, operation="unsharp_mask"
        )
        self.processor.progress.connect(self.progress_bar.setValue)
        self.processor.finished.connect(self.on_effect_applied)
        self.processor.error.connect(self.on_processing_error)
        self.processor.start()

    def apply_noise_reduction(self):
        """Применяет шумоподавление"""
        if not self.current_image_path:
            QMessageBox.warning(self, "Предупреждение", "Сначала загрузите изображение")
            return

        self.progress_bar.setVisible(True)
        self.processor = ImageProcessor(
            self.current_image_path, operation="noise_reduction"
        )
        self.processor.progress.connect(self.progress_bar.setValue)
        self.processor.finished.connect(self.on_effect_applied)
        self.processor.error.connect(self.on_processing_error)
        self.processor.start()

    def apply_grayscale(self):
        """Применяет черно-белый фильтр"""
        if not self.current_image_path:
            QMessageBox.warning(self, "Предупреждение", "Сначала загрузите изображение")
            return

        self.progress_bar.setVisible(True)
        self.processor = ImageProcessor(self.current_image_path, operation="grayscale")
        self.processor.progress.connect(self.progress_bar.setValue)
        self.processor.finished.connect(self.on_effect_applied)
        self.processor.error.connect(self.on_processing_error)
        self.processor.start()

    def apply_noise_filter(self):
        """Применяет добавление шума"""
        if not self.current_image_path:
            QMessageBox.warning(self, "Предупреждение", "Сначала загрузите изображение")
            return

        self.progress_bar.setVisible(True)
        self.processor = ImageProcessor(self.current_image_path, operation="noise")
        self.processor.progress.connect(self.progress_bar.setValue)
        self.processor.finished.connect(self.on_effect_applied)
        self.processor.error.connect(self.on_processing_error)
        self.processor.start()

    def apply_sketch_effect(self):
        """Применяет эффект рисунка"""
        if not self.current_image_path:
            QMessageBox.warning(self, "Предупреждение", "Сначала загрузите изображение")
            return

        self.progress_bar.setVisible(True)
        self.processor = ImageProcessor(
            self.current_image_path, operation="sketch_effect"
        )
        self.processor.progress.connect(self.progress_bar.setValue)
        self.processor.finished.connect(self.on_effect_applied)
        self.processor.error.connect(self.on_processing_error)
        self.processor.start()

    def apply_glass_effect(self):
        """Применяет эффект стекла"""
        if not self.current_image_path:
            QMessageBox.warning(self, "Предупреждение", "Сначала загрузите изображение")
            return

        self.progress_bar.setVisible(True)
        self.processor = ImageProcessor(
            self.current_image_path, operation="glass_effect"
        )
        self.processor.progress.connect(self.progress_bar.setValue)
        self.processor.finished.connect(self.on_effect_applied)
        self.processor.error.connect(self.on_processing_error)
        self.processor.start()

    def apply_wave_effect(self):
        """Применяет эффект волн"""
        if not self.current_image_path:
            QMessageBox.warning(self, "Предупреждение", "Сначала загрузите изображение")
            return

        self.progress_bar.setVisible(True)
        self.processor = ImageProcessor(
            self.current_image_path, operation="wave_effect"
        )
        self.processor.progress.connect(self.progress_bar.setValue)
        self.processor.finished.connect(self.on_effect_applied)
        self.processor.error.connect(self.on_processing_error)
        self.processor.start()

    def apply_glow_effect(self):
        """Применяет эффект свечения"""
        if not self.current_image_path:
            QMessageBox.warning(self, "Предупреждение", "Сначала загрузите изображение")
            return

        self.progress_bar.setVisible(True)
        self.processor = ImageProcessor(
            self.current_image_path, operation="glow_effect"
        )
        self.processor.progress.connect(self.progress_bar.setValue)
        self.processor.finished.connect(self.on_effect_applied)
        self.processor.error.connect(self.on_processing_error)
        self.processor.start()

    def apply_shadow_effect(self):
        """Применяет эффект теней"""
        if not self.current_image_path:
            QMessageBox.warning(self, "Предупреждение", "Сначала загрузите изображение")
            return

        self.progress_bar.setVisible(True)
        self.processor = ImageProcessor(
            self.current_image_path, operation="shadow_effect"
        )
        self.processor.progress.connect(self.progress_bar.setValue)
        self.processor.finished.connect(self.on_effect_applied)
        self.processor.error.connect(self.on_processing_error)
        self.processor.start()

    def apply_auto_levels(self):
        """Применяет автоуровни"""
        if not self.current_image_path:
            QMessageBox.warning(self, "Предупреждение", "Сначала загрузите изображение")
            return

        self.progress_bar.setVisible(True)
        self.processor = ImageProcessor(
            self.current_image_path, operation="auto_levels"
        )
        self.processor.progress.connect(self.progress_bar.setValue)
        self.processor.finished.connect(self.on_effect_applied)
        self.processor.error.connect(self.on_processing_error)
        self.processor.start()

    def apply_auto_contrast(self):
        """Применяет автоконтраст"""
        if not self.current_image_path:
            QMessageBox.warning(self, "Предупреждение", "Сначала загрузите изображение")
            return

        self.progress_bar.setVisible(True)
        self.processor = ImageProcessor(
            self.current_image_path, operation="auto_contrast"
        )
        self.processor.progress.connect(self.progress_bar.setValue)
        self.processor.finished.connect(self.on_effect_applied)
        self.processor.error.connect(self.on_processing_error)
        self.processor.start()

    def apply_color_balance(self):
        """Применяет цветовой баланс"""
        if not self.current_image_path:
            QMessageBox.warning(self, "Предупреждение", "Сначала загрузите изображение")
            return

        red_cyan = self.red_cyan_slider.value()
        green_magenta = self.green_magenta_slider.value()
        blue_yellow = self.blue_yellow_slider.value()

        self.progress_bar.setVisible(True)
        self.processor = ImageProcessor(
            self.current_image_path,
            operation="color_balance",
            red_cyan=red_cyan,
            green_magenta=green_magenta,
            blue_yellow=blue_yellow,
        )
        self.processor.progress.connect(self.progress_bar.setValue)
        self.processor.finished.connect(self.on_effect_applied)
        self.processor.error.connect(self.on_processing_error)
        self.processor.start()

    def reset_image(self):
        """Сбрасывает изображение"""
        self.canvas.reset_image()
        self.reset_sliders()
        self.status_bar.showMessage("Изображение сброшено")

    def reset_sliders(self):
        """Сбрасывает слайдеры к значениям по умолчанию"""
        self.brightness_slider.setValue(100)
        self.contrast_slider.setValue(100)
        self.saturation_slider.setValue(100)

    def resize_image(self):
        """Изменяет размер изображения"""
        if not self.canvas.image:
            QMessageBox.warning(self, "Предупреждение", "Сначала загрузите изображение")
            return

        current_size = self.canvas.image.size()
        dialog = ResizeDialog(current_size, self)

        if dialog.exec() == QDialog.DialogCode.Accepted:
            new_size = dialog.get_size()
            self.canvas.resize_image(new_size)
            self.status_bar.showMessage(
                f"Размер изменен на {new_size.width()}×{new_size.height()}"
            )

    def rotate_image(self, angle):
        """Поворачивает изображение"""
        if not self.canvas.image:
            QMessageBox.warning(self, "Предупреждение", "Сначала загрузите изображение")
            return

        self.canvas.rotate_image(angle)
        self.status_bar.showMessage(f"Изображение повернуто на {angle}°")

    def flip_image(self, horizontal):
        """Отражает изображение"""
        if not self.canvas.image:
            QMessageBox.warning(self, "Предупреждение", "Сначала загрузите изображение")
            return

        self.canvas.flip_image(horizontal)
        direction = "горизонтально" if horizontal else "вертикально"
        self.status_bar.showMessage(f"Изображение отражено {direction}")

    def show_actual_size(self):
        """Переключает режим показа в реальном размере"""
        if not self.canvas.image:
            QMessageBox.warning(self, "Предупреждение", "Сначала загрузите изображение")
            return

        self.canvas.actual_size_mode = not self.canvas.actual_size_mode
        self.canvas.update_display()

        if self.canvas.actual_size_mode:
            self.status_bar.showMessage("Режим реального размера включен")
        else:
            self.status_bar.showMessage("Режим реального размера выключен")

    def on_zoom_changed(self, value):
        """Обработчик изменения масштаба"""
        self.canvas.zoom_factor = value / 100.0
        self.zoom_label.setText(f"{value}%")
        self.zoom_status.setText(f"Масштаб: {value}%")
        self.canvas.update_display()

    def set_zoom(self, percent):
        """Устанавливает масштаб в процентах"""
        self.zoom_slider.setValue(percent)
        # Обработчик on_zoom_changed вызовется автоматически

    def undo(self):
        """Отменяет последнее действие"""
        if self.canvas.undo_action():
            self.status_bar.showMessage("Действие отменено")
            self.update_history_ui()
        else:
            self.status_bar.showMessage("Нечего отменять")

    def redo(self):
        """Повторяет отмененное действие"""
        if self.canvas.redo_action():
            self.status_bar.showMessage("Действие повторено")
            self.update_history_ui()
        else:
            self.status_bar.showMessage("Нечего повторять")

    def show_about(self):
        """Показывает окно 'О программе'"""
        QMessageBox.about(
            self,
            "О программе",
            "🎨 Редактор графических файлов\n\n"
            "Версия 1.0\n"
            "Создан с использованием Python и PyQt6\n\n"
            "Возможности:\n"
            "• Загрузка и сохранение изображений\n"
            "• Рисование кистью с настройкой размера и цвета\n"
            "• Добавление текста с настройкой шрифта\n"
            "• Применение фильтров (яркость, контрастность, насыщенность)\n"
            "• Эффекты (размытие, резкость)\n"
            "• Удаление фона\n"
            "• Изменение размера и поворот\n"
            "• Отражение изображений\n"
            "• Масштабирование и навигация\n"
            "• Файловый менеджер\n"
            "• Горячие клавиши\n\n"
            "Автор: AI Assistant\n"
            "© 2024",
        )

    def show_help(self):
        """Показывает справку"""
        help_text = """
        <h3>Справка по использованию</h3>
        
        <h4>Основные функции:</h4>
        <ul>
        <li><b>Ctrl+N</b> - Создать новое изображение</li>
        <li><b>Ctrl+O</b> - Открыть изображение</li>
        <li><b>Ctrl+S</b> - Сохранить изображение</li>
        <li><b>Ctrl+Z</b> - Отменить действие</li>
        <li><b>Ctrl+Y</b> - Повторить действие</li>
        <li><b>Ctrl+R</b> - Сбросить изменения</li>
        <li><b>Ctrl+Shift+C</b> - Копировать выделенную область</li>
        <li><b>Ctrl+Shift+V</b> - Вставить из буфера обмена</li>
        </ul>
        
        <h4>Инструменты:</h4>
        <ul>
        <li><b>B</b> - Выбрать кисть</li>
        <li><b>T</b> - Выбрать инструмент текста</li>
        <li><b>C</b> - Выбрать инструмент обрезки</li>
        <li><b>Ctrl+колесо мыши</b> - Масштабирование</li>
        </ul>
        
        <h4>Конвертация форматов:</h4>
        <ul>
        <li><b>ICO</b> - Создание иконок с несколькими размерами (16x16, 32x32, 48x48, 256x256)</li>
        <li><b>PNG</b> - Формат с поддержкой прозрачности</li>
        <li><b>JPEG</b> - Сжатый формат с настройкой качества</li>
        <li>Автоматическая подгонка размеров для иконок</li>
        <li>Сохранение пропорций при конвертации</li>
        </ul>
        
        <h4>Работа с изображениями:</h4>
        <ul>
        <li>Выберите изображение в файловом менеджере</li>
        <li>Используйте инструменты для редактирования</li>
        <li>Применяйте фильтры и эффекты</li>
        <li>Конвертируйте в нужный формат</li>
        <li>Сохраняйте результат</li>
        </ul>
        """

        msg = QMessageBox()
        msg.setWindowTitle("Справка")
        msg.setTextFormat(Qt.TextFormat.RichText)
        msg.setText(help_text)
        msg.exec()

    def check_clipboard_status(self):
        """Проверяет состояние системного буфера обмена"""
        clipboard = QApplication.clipboard()

        has_system_image = clipboard.mimeData().hasImage()
        has_internal_data = self.canvas.clipboard_data is not None

        if has_system_image or has_internal_data:
            status_text = "Буфер обмена: "
            if has_system_image and has_internal_data:
                status_text += "системный + внутренний"
            elif has_system_image:
                status_text += "системный"
            elif has_internal_data:
                status_text += "внутренний"

            self.clipboard_status_label.setText(status_text)
        else:
            self.clipboard_status_label.setText("Буфер обмена: пуст")

    def eventFilter(self, source, event):
        """Обработчик событий для горячих клавиш"""
        if event.type() == event.Type.KeyPress:
            # Ctrl+Shift+C для копирования
            if (
                event.modifiers()
                == (
                    Qt.KeyboardModifier.ControlModifier
                    | Qt.KeyboardModifier.ShiftModifier
                )
                and event.key() == Qt.Key.Key_C
            ):
                self.copy_selection()
                return True
            # Ctrl+Shift+V для вставки
            elif (
                event.modifiers()
                == (
                    Qt.KeyboardModifier.ControlModifier
                    | Qt.KeyboardModifier.ShiftModifier
                )
                and event.key() == Qt.Key.Key_V
            ):
                self.paste_from_clipboard()
                return True

        return super().eventFilter(source, event)

    def convert_to_ico(self):
        """Конвертирует изображение в ICO формат с высоким качеством"""
        if not self.canvas.image:
            QMessageBox.warning(self, "Предупреждение", "Сначала загрузите изображение")
            return

        # Диалог выбора размеров иконок
        sizes_dialog = IconSizeDialog(self)
        if sizes_dialog.exec() != QDialog.DialogCode.Accepted:
            return

        selected_sizes = sizes_dialog.get_selected_sizes()
        if not selected_sizes:
            QMessageBox.warning(
                self, "Предупреждение", "Выберите хотя бы один размер иконки"
            )
            return

        # Выбираем файл для сохранения
        file_path, _ = QFileDialog.getSaveFileName(
            self, "Сохранить как ICO", "", "Файлы иконок (*.ico);;Все файлы (*.*)"
        )

        if file_path:
            try:
                # Показываем прогресс
                self.progress_bar.setVisible(True)
                self.progress_bar.setValue(0)

                # Конвертируем QPixmap в высококачественный PIL Image
                qimg = self.canvas.image.toImage()

                # Конвертируем в формат RGB или RGBA с правильным порядком байтов
                if qimg.hasAlphaChannel():
                    # Конвертируем в RGBA
                    qimg = qimg.convertToFormat(QImage.Format.Format_RGBA8888)
                    width, height = qimg.width(), qimg.height()
                    ptr = qimg.bits()
                    ptr.setsize(qimg.sizeInBytes())
                    arr = np.array(ptr).reshape(height, width, 4)
                    pil_img = Image.fromarray(arr, "RGBA")
                else:
                    # Конвертируем в RGB
                    qimg = qimg.convertToFormat(QImage.Format.Format_RGB888)
                    width, height = qimg.width(), qimg.height()
                    ptr = qimg.bits()
                    ptr.setsize(qimg.sizeInBytes())
                    arr = np.array(ptr).reshape(height, width, 3)
                    pil_img = Image.fromarray(arr, "RGB")
                    # Добавляем альфа-канал для лучшей совместимости
                    pil_img = pil_img.convert("RGBA")

                self.progress_bar.setValue(20)

                # Создаем список изображений разных размеров с высоким качеством
                icon_images = []
                total_sizes = len(selected_sizes)

                for i, size in enumerate(selected_sizes):
                    # Вычисляем наилучший метод масштабирования
                    if size <= 48:
                        # Для маленьких иконок используем более четкий алгоритм
                        resample = (
                            Image.Resampling.NEAREST
                            if size <= 16
                            else Image.Resampling.BOX
                        )
                    else:
                        # Для больших иконок используем качественное масштабирование
                        resample = Image.Resampling.LANCZOS

                    # Изменяем размер с сохранением пропорций и качества
                    if pil_img.width != pil_img.height:
                        # Если изображение не квадратное, сначала подгоняем под квадрат
                        max_side = max(pil_img.width, pil_img.height)

                        # Создаем квадратное изображение с прозрачным фоном
                        square_img = Image.new(
                            "RGBA", (max_side, max_side), (0, 0, 0, 0)
                        )

                        # Вычисляем позицию для центрирования
                        paste_x = (max_side - pil_img.width) // 2
                        paste_y = (max_side - pil_img.height) // 2

                        # Вставляем оригинальное изображение в центр
                        square_img.paste(
                            pil_img,
                            (paste_x, paste_y),
                            pil_img if pil_img.mode == "RGBA" else None,
                        )

                        # Теперь масштабируем квадратное изображение
                        resized_img = square_img.resize((size, size), resample)
                    else:
                        # Изображение уже квадратное
                        resized_img = pil_img.resize((size, size), resample)

                    # Оптимизируем цветовую палитру для маленьких иконок
                    if size <= 48 and resized_img.mode == "RGBA":
                        # Для маленьких иконок квантуем цвета для лучшего отображения
                        # Конвертируем в P режим с альфой для лучшего сжатия
                        try:
                            # Создаем оптимизированную палитру
                            alpha = resized_img.split()[-1]  # Извлекаем альфа-канал
                            rgb_img = resized_img.convert("RGB")
                            # Квантуем до 255 цветов, оставляя место для прозрачности
                            quantized = rgb_img.quantize(
                                colors=255, method=Image.Quantize.MEDIANCUT
                            )
                            quantized = quantized.convert("RGBA")
                            # Применяем альфа-канал обратно
                            quantized.putalpha(alpha)
                            resized_img = quantized
                        except:
                            # Если квантизация не удалась, оставляем как есть
                            pass

                    icon_images.append(resized_img)

                    # Обновляем прогресс
                    progress = 20 + (60 * (i + 1) // total_sizes)
                    self.progress_bar.setValue(progress)

                self.progress_bar.setValue(85)

                # Сохраняем как ICO файл с максимальным качеством
                save_kwargs = {
                    "format": "ICO",
                    "sizes": [(img.width, img.height) for img in icon_images],
                }

                # Добавляем дополнительные изображения только если их больше одного
                if len(icon_images) > 1:
                    save_kwargs["append_images"] = icon_images[1:]

                # Сохраняем с оптимальными настройками
                icon_images[0].save(file_path, **save_kwargs)

                self.progress_bar.setValue(100)

                self.status_bar.showMessage(
                    f"ICO файл сохранен: {os.path.basename(file_path)}"
                )
                QMessageBox.information(
                    self,
                    "Успех",
                    f"Изображение успешно конвертировано в ICO формат высокого качества!\n"
                    f"Размеры иконок: {', '.join(f'{s}×{s}' for s in selected_sizes)}\n"
                    f"Алгоритм: адаптивное масштабирование с сохранением цветов\n"
                    f"Файл: {os.path.basename(file_path)}",
                )

                self.progress_bar.setVisible(False)

            except Exception as e:
                self.progress_bar.setVisible(False)
                QMessageBox.critical(self, "Ошибка", f"Ошибка конвертации в ICO: {e}")

    def convert_to_png(self):
        """Конвертирует изображение в PNG формат"""
        if not self.canvas.image:
            QMessageBox.warning(self, "Предупреждение", "Сначала загрузите изображение")
            return

        file_path, _ = QFileDialog.getSaveFileName(
            self, "Сохранить как PNG", "", "PNG файлы (*.png);;Все файлы (*.*)"
        )

        if file_path:
            try:
                self.canvas.image.save(file_path, "PNG")
                self.status_bar.showMessage(
                    f"PNG файл сохранен: {os.path.basename(file_path)}"
                )
                QMessageBox.information(
                    self, "Успех", "Изображение успешно конвертировано в PNG формат!"
                )
            except Exception as e:
                QMessageBox.critical(self, "Ошибка", f"Ошибка конвертации в PNG: {e}")

    def convert_to_jpg(self):
        """Конвертирует изображение в JPEG формат"""
        if not self.canvas.image:
            QMessageBox.warning(self, "Предупреждение", "Сначала загрузите изображение")
            return

        # Диалог настроек JPEG
        quality, ok = QSpinBox().value(), True
        quality_dialog = QDialog(self)
        quality_dialog.setWindowTitle("Настройки JPEG")
        quality_dialog.setModal(True)

        layout = QVBoxLayout(quality_dialog)
        layout.addWidget(QLabel("Качество JPEG (1-100):"))

        quality_spin = QSpinBox()
        quality_spin.setRange(1, 100)
        quality_spin.setValue(90)
        layout.addWidget(quality_spin)

        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        buttons.accepted.connect(quality_dialog.accept)
        buttons.rejected.connect(quality_dialog.reject)
        layout.addWidget(buttons)

        if quality_dialog.exec() != QDialog.DialogCode.Accepted:
            return

        quality = quality_spin.value()

        file_path, _ = QFileDialog.getSaveFileName(
            self, "Сохранить как JPEG", "", "JPEG файлы (*.jpg *.jpeg);;Все файлы (*.*)"
        )

        if file_path:
            try:
                # Конвертируем в RGB если есть альфа-канал
                qimg = self.canvas.image.toImage()
                if qimg.hasAlphaChannel():
                    # Создаем белый фон для JPEG
                    rgb_image = QImage(qimg.size(), QImage.Format.Format_RGB888)
                    rgb_image.fill(Qt.GlobalColor.white)

                    painter = QPainter(rgb_image)
                    painter.drawImage(0, 0, qimg)
                    painter.end()

                    pixmap = QPixmap.fromImage(rgb_image)
                else:
                    pixmap = self.canvas.image

                pixmap.save(file_path, "JPEG", quality)
                self.status_bar.showMessage(
                    f"JPEG файл сохранен: {os.path.basename(file_path)}"
                )
                QMessageBox.information(
                    self,
                    "Успех",
                    f"Изображение успешно конвертировано в JPEG формат!\nКачество: {quality}%",
                )
            except Exception as e:
                QMessageBox.critical(self, "Ошибка", f"Ошибка конвертации в JPEG: {e}")

    def dragEnterEvent(self, event):
        """Обработчик входа перетаскиваемых данных в главное окно"""
        if event.mimeData().hasUrls():
            urls = event.mimeData().urls()
            # Проверяем, есть ли среди перетаскиваемых файлов изображения
            for url in urls:
                file_path = url.toLocalFile()
                if file_path.lower().endswith(
                    (".png", ".jpg", ".jpeg", ".bmp", ".gif", ".tiff", ".webp", ".ico")
                ):
                    event.accept()
                    return
            event.ignore()
        else:
            event.ignore()

    def dropEvent(self, event):
        """Обработчик сброса перетаскиваемых файлов в главное окно"""
        if event.mimeData().hasUrls():
            urls = event.mimeData().urls()
            for url in urls:
                file_path = url.toLocalFile()
                if file_path.lower().endswith(
                    (".png", ".jpg", ".jpeg", ".bmp", ".gif", ".tiff", ".webp", ".ico")
                ):
                    # Загружаем первое найденное изображение
                    self.load_image_from_path(file_path)
                    event.accept()
                    return
            event.ignore()
        else:
            event.ignore()

    def closeEvent(self, event):
        """Обработчик закрытия приложения"""
        if self.canvas.image and self.canvas.image != self.canvas.original_image:
            reply = QMessageBox.question(
                self,
                "Сохранить изменения?",
                "У вас есть несохраненные изменения. Сохранить их?",
                QMessageBox.StandardButton.Yes
                | QMessageBox.StandardButton.No
                | QMessageBox.StandardButton.Cancel,
            )

            if reply == QMessageBox.StandardButton.Yes:
                self.save_image()
                event.accept()
            elif reply == QMessageBox.StandardButton.No:
                event.accept()
            else:
                event.ignore()
                return

        event.accept()


def main():
    app = QApplication(sys.argv)

    # Устанавливаем стиль приложения
    app.setStyle("Fusion")

    # Настройка темы
    palette = QPalette()
    palette.setColor(QPalette.ColorRole.Window, QColor(240, 240, 240))
    palette.setColor(QPalette.ColorRole.WindowText, QColor(0, 0, 0))
    palette.setColor(QPalette.ColorRole.Base, QColor(255, 255, 255))
    palette.setColor(QPalette.ColorRole.AlternateBase, QColor(245, 245, 245))
    palette.setColor(QPalette.ColorRole.ToolTipBase, QColor(255, 255, 220))
    palette.setColor(QPalette.ColorRole.ToolTipText, QColor(0, 0, 0))
    palette.setColor(QPalette.ColorRole.Text, QColor(0, 0, 0))
    palette.setColor(QPalette.ColorRole.Button, QColor(240, 240, 240))
    palette.setColor(QPalette.ColorRole.ButtonText, QColor(0, 0, 0))
    palette.setColor(QPalette.ColorRole.BrightText, QColor(255, 0, 0))
    palette.setColor(QPalette.ColorRole.Link, QColor(42, 130, 218))
    palette.setColor(QPalette.ColorRole.Highlight, QColor(42, 130, 218))
    palette.setColor(QPalette.ColorRole.HighlightedText, QColor(255, 255, 255))
    app.setPalette(palette)

    # Создаем главное окно
    window = GraphicsEditor()
    window.showMaximized()

    # Запускаем приложение
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
