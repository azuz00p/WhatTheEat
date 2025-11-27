import sys
import os
import sqlite3
import random
from PyQt6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout,
                             QHBoxLayout, QPushButton, QListWidget, QListWidgetItem,
                             QTextEdit, QLineEdit, QLabel, QMessageBox, QSplitter,
                             QFormLayout, QSpinBox, QComboBox, QFileDialog, QDialog,
                             QDialogButtonBox)
from PyQt6.QtGui import QAction, QFont
from PyQt6.QtCore import Qt, QSettings

translate = False


class CategoryDialog(QDialog):
    def __init__(self, categories, parent=None):
        super().__init__(parent)
        self.categories = categories
        self.setModal(True)
        self.setFixedSize(300, 200)
        layout = QVBoxLayout(self)
        self.label = QLabel()
        layout.addWidget(self.label)
        self.category_combo = QComboBox()
        layout.addWidget(self.category_combo)
        buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)
        self.update_ui()

    def update_ui(self):
        if translate:
            self.setWindowTitle("WhatTheEat™")
            self.label.setText("Select category for random recipe:")
            self.category_combo.clear()
            self.category_combo.addItems(["Random"] + self.categories)
        else:
            self.setWindowTitle("ЧёПоесть™")
            self.label.setText("Выберите категорию для случайного рецепта:")
            self.category_combo.clear()
            self.category_combo.addItems(["Случайная"] + self.categories)

    def get_selected_category(self):
        return self.category_combo.currentText()


class WhatTheEat(QMainWindow):
    def __init__(self):
        super().__init__()
        self.current_db_path = None
        self.conn = None
        self.current_recipe_id = None
        self.categories_ru = ['Завтрак', 'Обед', 'Ужин', 'Десерт', 'Напиток', 'Другое']
        self.categories_en = ['Breakfast', 'Lunch', 'Dinner', 'Dessert', 'Drink', 'Other']
        self.category_id_map = {}
        self.initUI()
        self.load_last_database()

    def initUI(self):
        self.setWindowTitle('ЧёПоесть - Ваша кулинарная книга')
        self.setGeometry(100, 100, 900, 600)
        self.create_menu()
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)
        top_layout = QHBoxLayout()
        top_layout.addStretch()
        self.language_button = QPushButton('RU')
        self.language_button.setFixedSize(50, 30)
        self.language_button.clicked.connect(self.toggle_language)
        top_layout.addWidget(self.language_button)
        main_layout.addLayout(top_layout)
        content_layout = QHBoxLayout()
        splitter = QSplitter(Qt.Orientation.Horizontal)
        self.left_panel = self.create_recipe_list_panel()
        self.right_panel = self.create_recipe_detail_panel()
        splitter.addWidget(self.left_panel)
        splitter.addWidget(self.right_panel)
        splitter.setSizes([300, 600])
        content_layout.addWidget(splitter)
        main_layout.addLayout(content_layout)
        bottom_layout = QHBoxLayout()
        bottom_layout.addStretch()
        self.random_recipe_button = QPushButton('ЧёПоесть™')
        self.random_recipe_button.setFixedSize(120, 30)
        self.random_recipe_button.clicked.connect(self.show_random_recipe)
        bottom_layout.addWidget(self.random_recipe_button)
        main_layout.addLayout(bottom_layout)

    def toggle_language(self):
        global translate
        translate = not translate
        self.retranslate_ui()

    def retranslate_ui(self):
        self.language_button.setText('EN' if translate else 'RU')
        self.update_window_title()
        self.update_menu()
        self.update_main_ui()

    def update_window_title(self):
        if translate:
            if self.current_db_path:
                db_name = os.path.basename(self.current_db_path)
                self.setWindowTitle(f'WhatTheEat - {db_name}')
            else:
                self.setWindowTitle('WhatToEat - Your Cookbook')
        else:
            if self.current_db_path:
                db_name = os.path.basename(self.current_db_path)
                self.setWindowTitle(f'ЧёПоесть - {db_name}')
            else:
                self.setWindowTitle('ЧёПоесть - Ваша кулинарная книга')

    def update_menu(self):
        menubar = self.menuBar()
        file_menu = menubar.actions()[0].menu()
        if translate:
            file_menu.setTitle('File')
            file_menu.actions()[0].setText('New Database')
            file_menu.actions()[1].setText('Open Database')
            file_menu.actions()[3].setText('New Recipe')
            file_menu.actions()[4].setText('Save Recipe')
            file_menu.actions()[6].setText('Exit')
        else:
            file_menu.setTitle('Файл')
            file_menu.actions()[0].setText('Новая база данных')
            file_menu.actions()[1].setText('Открыть базу данных')
            file_menu.actions()[3].setText('Новый рецепт')
            file_menu.actions()[4].setText('Сохранить рецепт')
            file_menu.actions()[6].setText('Выход')
        db_menu = menubar.actions()[1].menu()
        if translate:
            db_menu.setTitle('Database')
            db_menu.actions()[0].setText('Database Info')
        else:
            db_menu.setTitle('База данных')
            db_menu.actions()[0].setText('Информация о базе')
        help_menu = menubar.actions()[2].menu()
        if translate:
            help_menu.setTitle('Help')
            help_menu.actions()[0].setText('About')
        else:
            help_menu.setTitle('Помощь')
            help_menu.actions()[0].setText('О программе')

    def update_main_ui(self):
        self.update_database_info()
        if translate:
            self.recipes_title.setText('My Recipes')
            self.search_input.setPlaceholderText('Search recipes...')
            self.add_button.setText('Add Recipe')
            self.delete_button.setText('Delete Recipe')
            self.filter_combo.clear()
            self.filter_combo.addItems(['All', 'Breakfast', 'Lunch', 'Dinner', 'Dessert', 'Drink', 'Other'])
        else:
            self.recipes_title.setText('Мои рецепты')
            self.search_input.setPlaceholderText('Поиск рецептов...')
            self.add_button.setText('Добавить рецепт')
            self.delete_button.setText('Удалить рецепт')
            self.filter_combo.clear()
            self.filter_combo.addItems(['Все', 'Завтрак', 'Обед', 'Ужин', 'Десерт', 'Напиток', 'Другое'])
        if self.current_recipe_id is None:
            if translate:
                self.detail_title.setText('Select Recipe')
            else:
                self.detail_title.setText('Выберите рецепт')
        if translate:
            self.name_input.setPlaceholderText('Enter recipe name')
            self.category_combo.clear()
            self.category_combo.addItems(self.categories_en)
            self.ingredients_input.setPlaceholderText('Enter ingredients (each on new line)')
            self.instructions_input.setPlaceholderText('Enter cooking instructions')
            self.save_button.setText('Save Recipe')
            self.cancel_button.setText('Cancel')
            self.export_button.setText('Export to TXT')
            self.name_label.setText('Name:')
            self.category_label.setText('Category:')
            self.time_label.setText('Time:')
            self.ingredients_label.setText('Ingredients:')
            self.instructions_label.setText('Instructions:')
        else:
            self.name_input.setPlaceholderText('Введите название рецепта')
            self.category_combo.clear()
            self.category_combo.addItems(self.categories_ru)
            self.ingredients_input.setPlaceholderText('Введите ингредиенты (каждый с новой строки)')
            self.instructions_input.setPlaceholderText('Введите инструкции по приготовлению')
            self.save_button.setText('Сохранить рецепт')
            self.cancel_button.setText('Отменить')
            self.export_button.setText('Экспорт в TXT')
            self.name_label.setText('Название:')
            self.category_label.setText('Категория:')
            self.time_label.setText('Время:')
            self.ingredients_label.setText('Ингредиенты:')
            self.instructions_label.setText('Инструкции:')
        if translate:
            self.random_recipe_button.setText('WhatTheEat™')
        else:
            self.random_recipe_button.setText('ЧёПоесть™')

    def create_menu(self):
        menubar = self.menuBar()
        file_menu = menubar.addMenu('Файл')
        new_db_action = QAction('Новая база данных', self)
        new_db_action.setShortcut('Ctrl+N')
        new_db_action.triggered.connect(self.create_new_database)
        file_menu.addAction(new_db_action)
        open_db_action = QAction('Открыть базу данных', self)
        open_db_action.setShortcut('Ctrl+O')
        open_db_action.triggered.connect(self.open_database)
        file_menu.addAction(open_db_action)
        file_menu.addSeparator()
        new_recipe_action = QAction('Новый рецепт', self)
        new_recipe_action.setShortcut('Ctrl+R')
        new_recipe_action.triggered.connect(self.add_recipe)
        file_menu.addAction(new_recipe_action)
        save_action = QAction('Сохранить рецепт', self)
        save_action.setShortcut('Ctrl+S')
        save_action.triggered.connect(self.save_recipe)
        file_menu.addAction(save_action)
        export_action = QAction('Экспорт рецепта в TXT', self)
        export_action.setShortcut('Ctrl+E')
        export_action.triggered.connect(self.export_recipe_to_txt)
        file_menu.addAction(export_action)
        file_menu.addSeparator()
        exit_action = QAction('Выход', self)
        exit_action.setShortcut('Ctrl+Q')
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)
        db_menu = menubar.addMenu('База данных')
        info_action = QAction('Информация о базе', self)
        info_action.triggered.connect(self.show_database_info)
        db_menu.addAction(info_action)
        help_menu = menubar.addMenu('Помощь')
        about_action = QAction('О программе', self)
        about_action.triggered.connect(self.show_about)
        help_menu.addAction(about_action)

    def create_recipe_list_panel(self):
        panel = QWidget()
        layout = QVBoxLayout(panel)
        self.db_info_label = QLabel('База данных не выбрана')
        self.db_info_label.setFont(QFont('Arial', 10))
        self.db_info_label.setStyleSheet('color: gray;')
        layout.addWidget(self.db_info_label)
        self.recipes_title = QLabel('Мои рецепты')
        self.recipes_title.setFont(QFont('Arial', 14, QFont.Weight.Bold))
        layout.addWidget(self.recipes_title)
        search_filter_layout = QHBoxLayout()
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText('Поиск рецептов...')
        self.search_input.textChanged.connect(self.search_recipes)
        search_filter_layout.addWidget(self.search_input)
        self.filter_combo = QComboBox()
        self.filter_combo.addItems(['Все', 'Завтрак', 'Обед', 'Ужин', 'Десерт', 'Напиток', 'Другое'])
        self.filter_combo.currentTextChanged.connect(self.filter_recipes)
        search_filter_layout.addWidget(self.filter_combo)
        layout.addLayout(search_filter_layout)
        self.recipe_list = QListWidget()
        self.recipe_list.itemClicked.connect(self.on_recipe_selected)
        layout.addWidget(self.recipe_list)
        button_layout = QHBoxLayout()
        self.add_button = QPushButton('Добавить рецепт')
        self.add_button.clicked.connect(self.add_recipe)
        self.delete_button = QPushButton('Удалить рецепт')
        self.delete_button.clicked.connect(self.delete_recipe)
        button_layout.addWidget(self.add_button)
        button_layout.addWidget(self.delete_button)
        layout.addLayout(button_layout)
        return panel

    def create_recipe_detail_panel(self):
        panel = QWidget()
        layout = QVBoxLayout(panel)
        self.detail_title = QLabel('Выберите рецепт')
        self.detail_title.setFont(QFont('Arial', 16, QFont.Weight.Bold))
        layout.addWidget(self.detail_title)
        form_layout = QFormLayout()
        self.name_label = QLabel('Название:')
        self.name_input = QLineEdit()
        self.name_input.setPlaceholderText('Введите название рецепта')
        form_layout.addRow(self.name_label, self.name_input)
        self.category_label = QLabel('Категория:')
        self.category_combo = QComboBox()
        self.category_combo.addItems(self.categories_ru)
        form_layout.addRow(self.category_label, self.category_combo)
        time_widget = QWidget()
        time_layout = QHBoxLayout(time_widget)
        self.time_label = QLabel('Время:')
        self.prep_time = QSpinBox()
        self.prep_time.setRange(1, 600)
        self.prep_time.setSuffix(' мин')
        time_layout.addWidget(self.time_label)
        time_layout.addWidget(self.prep_time)
        time_layout.addStretch()
        form_layout.addRow(time_widget)
        self.ingredients_label = QLabel('Ингредиенты:')
        self.ingredients_input = QTextEdit()
        self.ingredients_input.setPlaceholderText('Введите ингредиенты (каждый с новой строки)')
        self.ingredients_input.setMaximumHeight(150)
        form_layout.addRow(self.ingredients_label, self.ingredients_input)
        self.instructions_label = QLabel('Инструкции:')
        self.instructions_input = QTextEdit()
        self.instructions_input.setPlaceholderText('Введите инструкции по приготовлению')
        self.instructions_input.setMinimumHeight(200)
        form_layout.addRow(self.instructions_label, self.instructions_input)
        layout.addLayout(form_layout)
        button_layout = QHBoxLayout()
        self.save_button = QPushButton('Сохранить рецепт')
        self.save_button.clicked.connect(self.save_recipe)
        self.cancel_button = QPushButton('Отменить')
        self.cancel_button.clicked.connect(self.cancel_edit)
        self.export_button = QPushButton('Экспорт в TXT')
        self.export_button.clicked.connect(self.export_recipe_to_txt)
        button_layout.addWidget(self.save_button)
        button_layout.addWidget(self.cancel_button)
        button_layout.addWidget(self.export_button)
        button_layout.addStretch()
        layout.addLayout(button_layout)
        layout.addStretch()
        return panel

    def filter_recipes(self):
        if not self.conn:
            return
        selected_filter = self.filter_combo.currentText()
        search_text = self.search_input.text().lower()
        try:
            cursor = self.conn.cursor()
            if translate:
                if selected_filter == 'All':
                    cursor.execute('''
                        SELECT r.id, r.name, r.category_id, r.prep_time, r.ingredients, r.instructions, c.name as category_name 
                        FROM recipes r 
                        JOIN categories c ON r.category_id = c.id 
                        ORDER BY r.name
                    ''')
                else:
                    category_map = {
                        'Breakfast': 'Завтрак',
                        'Lunch': 'Обед',
                        'Dinner': 'Ужин',
                        'Dessert': 'Десерт',
                        'Drink': 'Напиток',
                        'Other': 'Другое'
                    }
                    db_category = category_map.get(selected_filter, selected_filter)
                    cursor.execute('''
                        SELECT r.id, r.name, r.category_id, r.prep_time, r.ingredients, r.instructions, c.name as category_name 
                        FROM recipes r 
                        JOIN categories c ON r.category_id = c.id 
                        WHERE c.name = ? 
                        ORDER BY r.name
                    ''', (db_category,))
            else:
                if selected_filter == 'Все':
                    cursor.execute('''
                        SELECT r.id, r.name, r.category_id, r.prep_time, r.ingredients, r.instructions, c.name as category_name 
                        FROM recipes r 
                        JOIN categories c ON r.category_id = c.id 
                        ORDER BY r.name
                    ''')
                else:
                    cursor.execute('''
                        SELECT r.id, r.name, r.category_id, r.prep_time, r.ingredients, r.instructions, c.name as category_name 
                        FROM recipes r 
                        JOIN categories c ON r.category_id = c.id 
                        WHERE c.name = ? 
                        ORDER BY r.name
                    ''', (selected_filter,))
            recipes = cursor.fetchall()
            self.recipe_list.clear()
            for recipe in recipes:
                recipe_name = recipe[1].lower()
                if search_text and search_text not in recipe_name:
                    continue
                item = QListWidgetItem(recipe[1])
                item.setData(Qt.ItemDataRole.UserRole, {
                    'id': recipe[0],
                    'name': recipe[1],
                    'category_id': recipe[2],
                    'category': recipe[6],
                    'prep_time': recipe[3],
                    'ingredients': recipe[4].split('\n') if recipe[4] else [],
                    'instructions': recipe[5]
                })
                self.recipe_list.addItem(item)
        except Exception as e:
            self.show_error('Failed to filter recipes' if translate else 'Не удалось отфильтровать рецепты', str(e))

    def search_recipes(self):
        self.filter_recipes()

    def export_recipe_to_txt(self):
        if not self.current_recipe_id:
            if translate:
                self.show_warning('Error', 'No recipe selected for export')
            else:
                self.show_warning('Ошибка', 'Не выбран рецепт для экспорта')
            return
        name = self.name_input.text().strip()
        if not name:
            if translate:
                self.show_warning('Error', 'Recipe name is empty')
            else:
                self.show_warning('Ошибка', 'Название рецепта пустое')
            return
        if translate:
            file_path, _ = QFileDialog.getSaveFileName(
                self, 'Export Recipe to TXT',
                f'{name}.txt', 'Text Files (*.txt)')
        else:
            file_path, _ = QFileDialog.getSaveFileName(
                self, 'Экспорт рецепта в TXT',
                f'{name}.txt', 'Text Files (*.txt)')
        if not file_path:
            return
        try:
            category = self.category_combo.currentText()
            prep_time = self.prep_time.value()
            ingredients = self.ingredients_input.toPlainText().strip()
            instructions = self.instructions_input.toPlainText().strip()
            if translate:
                category_map = {
                    'Breakfast': 'Завтрак',
                    'Lunch': 'Обед',
                    'Dinner': 'Ужин',
                    'Dessert': 'Десерт',
                    'Drink': 'Напиток',
                    'Other': 'Другое'
                }
                save_category = category_map.get(category, category)
            else:
                save_category = category
            content = []
            if translate:
                content.append("=" * 50)
                content.append(f"RECIPE: {name}")
                content.append("=" * 50)
                content.append(f"Category: {save_category}")
                content.append(f"Preparation time: {prep_time} minutes")
                content.append("")
                content.append("INGREDIENTS:")
                content.append("-" * 20)
                content.append(ingredients)
                content.append("")
                content.append("COOKING INSTRUCTIONS:")
                content.append("-" * 30)
                content.append(instructions)
                content.append("")
                content.append(f"Exported from WhatTheEat: https://github.com/azuz00p/WhatTheEat")
            else:
                content.append("=" * 50)
                content.append(f"РЕЦЕПТ: {name}")
                content.append("=" * 50)
                content.append(f"Категория: {save_category}")
                content.append(f"Время приготовления: {prep_time} минут")
                content.append("")
                content.append("ИНГРЕДИЕНТЫ:")
                content.append("-" * 20)
                content.append(ingredients)
                content.append("")
                content.append("ИНСТРУКЦИЯ ПРИГОТОВЛЕНИЯ:")
                content.append("-" * 30)
                content.append(instructions)
                content.append("")
                content.append(f"Экспортировано из ЧёПоесть: https://github.com/azuz00p/WhatTheEat")
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write('\n'.join(content))
            if translate:
                self.show_info('Success', f'Recipe "{name}" successfully exported to:\n{file_path}')
            else:
                self.show_info('Успех', f'Рецепт "{name}" успешно экспортирован в:\n{file_path}')
        except Exception as e:
            self.show_error('Export failed' if translate else 'Ошибка экспорта', str(e))

    def create_database(self, db_path):
        try:
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS categories (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT NOT NULL UNIQUE
                )
            ''')
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS recipes (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT NOT NULL,
                    category_id INTEGER NOT NULL,
                    prep_time INTEGER NOT NULL,
                    ingredients TEXT NOT NULL,
                    instructions TEXT NOT NULL,
                    FOREIGN KEY (category_id) REFERENCES categories (id)
                )
            ''')
            categories_to_insert = self.categories_ru
            for category in categories_to_insert:
                try:
                    cursor.execute('INSERT OR IGNORE INTO categories (name) VALUES (?)', (category,))
                except:
                    pass

            conn.commit()
            conn.close()
            return True
        except Exception as e:
            self.show_error('Failed to create database' if translate else 'Не удалось создать базу данных', str(e))
            return False

    def connect_to_database(self, db_path):
        try:
            if self.conn:
                self.conn.close()
            self.conn = sqlite3.connect(db_path)
            self.current_db_path = db_path
            self.save_last_database(db_path)
            self.load_category_map()
            self.update_database_info()
            self.load_recipes()
            return True
        except Exception as e:
            self.show_error('Failed to connect to database' if translate else 'Не удалось подключиться к базе данных',
                            str(e))
            return False

    def load_category_map(self):
        if not self.conn:
            return
        try:
            cursor = self.conn.cursor()
            cursor.execute('SELECT id, name FROM categories')
            categories = cursor.fetchall()
            self.category_id_map = {}
            for category_id, category_name in categories:
                self.category_id_map[category_name] = category_id
        except Exception as e:
            self.show_error('Failed to load categories' if translate else 'Не удалось загрузить категории', str(e))

    def save_last_database(self, db_path):
        settings = QSettings('ЧёПоесть', 'WhatTheEat')
        settings.setValue('last_database', db_path)

    def load_last_database(self):
        settings = QSettings('ЧёПоесть', 'WhatTheEat')
        last_db = settings.value('last_database', '')
        if last_db and os.path.exists(last_db):
            self.connect_to_database(last_db)

    def show_error(self, title, message):
        QMessageBox.critical(self, title, message)

    def show_info(self, title, message):
        QMessageBox.information(self, title, message)

    def show_warning(self, title, message):
        QMessageBox.warning(self, title, message)

    def create_new_database(self):
        if translate:
            file_path, _ = QFileDialog.getSaveFileName(
                self, 'Create New Database',
                'recipes.db', 'Database Files (*.db)')
        else:
            file_path, _ = QFileDialog.getSaveFileName(
                self, 'Создать новую базу данных',
                'recipes.db', 'Database Files (*.db)')
        if file_path:
            if self.create_database(file_path):
                if self.connect_to_database(file_path):
                    if translate:
                        self.show_info('Success', 'New database created and connected!')
                    else:
                        self.show_info('Успех', 'Новая база данных создана и подключена!')
                    return True
                else:
                    if translate:
                        self.show_warning('Warning', 'Database created but failed to connect')
                    else:
                        self.show_warning('Предупреждение', 'База данных создана, но не удалось подключиться')
                    return False
            else:
                return False
        else:
            return False

    def open_database(self):
        if translate:
            file_path, _ = QFileDialog.getOpenFileName(
                self, 'Open Database',
                '', 'Database Files (*.db)')
        else:
            file_path, _ = QFileDialog.getOpenFileName(
                self, 'Открыть базу данных',
                '', 'Database Files (*.db)')
        if file_path:
            if self.connect_to_database(file_path):
                if translate:
                    self.show_info('Success', 'Database opened successfully!')
                else:
                    self.show_info('Успех', 'База данных успешно открыта!')
                return True
            else:
                return False
        else:
            return False

    def update_database_info(self):
        if self.current_db_path:
            db_name = os.path.basename(self.current_db_path)
            db_dir = os.path.dirname(self.current_db_path)
            if translate:
                self.db_info_label.setText(f'Database: {db_name} | Folder: {db_dir}')
            else:
                self.db_info_label.setText(f'База: {db_name} | Папка: {db_dir}')
            self.db_info_label.setStyleSheet('color: green;')
        else:
            if translate:
                self.db_info_label.setText('Database not selected')
            else:
                self.db_info_label.setText('База данных не выбрана')
            self.db_info_label.setStyleSheet('color: gray;')
        self.update_window_title()

    def load_recipes(self):
        if not self.conn:
            return
        try:
            cursor = self.conn.cursor()
            cursor.execute('''
                SELECT r.id, r.name, r.category_id, r.prep_time, r.ingredients, r.instructions, c.name as category_name 
                FROM recipes r 
                JOIN categories c ON r.category_id = c.id 
                ORDER BY r.name
            ''')
            recipes = cursor.fetchall()
            self.recipe_list.clear()
            for recipe in recipes:
                item = QListWidgetItem(recipe[1])
                item.setData(Qt.ItemDataRole.UserRole, {
                    'id': recipe[0],
                    'name': recipe[1],
                    'category_id': recipe[2],
                    'category': recipe[6],
                    'prep_time': recipe[3],
                    'ingredients': recipe[4].split('\n') if recipe[4] else [],
                    'instructions': recipe[5]
                })
                self.recipe_list.addItem(item)
        except Exception as e:
            self.show_error('Failed to load recipes' if translate else 'Не удалось загрузить рецепты', str(e))

    def on_recipe_selected(self, item):
        recipe_data = item.data(Qt.ItemDataRole.UserRole)
        if recipe_data:
            self.current_recipe_id = recipe_data['id']
            self.display_recipe(recipe_data)

    def display_recipe(self, recipe):
        self.name_input.setText(recipe.get('name', ''))
        category = recipe.get('category', 'Другое')
        if translate:
            category_map = {
                'Завтрак': 'Breakfast',
                'Обед': 'Lunch',
                'Ужин': 'Dinner',
                'Десерт': 'Dessert',
                'Напиток': 'Drink',
                'Другое': 'Other'
            }
            display_category = category_map.get(category, category)
        else:
            display_category = category
        index = self.category_combo.findText(display_category)
        if index >= 0:
            self.category_combo.setCurrentIndex(index)
        self.prep_time.setValue(recipe.get('prep_time', 30))
        ingredients_text = '\n'.join(recipe.get('ingredients', []))
        self.ingredients_input.setPlainText(ingredients_text)
        self.instructions_input.setPlainText(recipe.get('instructions', ''))
        self.detail_title.setText(recipe.get('name', 'Recipe' if translate else 'Рецепт'))

    def add_recipe(self):
        if not self.conn:
            if translate:
                self.show_warning('Error', 'First open or create a database')
            else:
                self.show_warning('Ошибка', 'Сначала откройте или создайте базу данных')
            return
        self.clear_form()
        self.current_recipe_id = None
        self.recipe_list.clearSelection()
        if translate:
            self.detail_title.setText('New Recipe')
        else:
            self.detail_title.setText('Новый рецепт')
        self.name_input.setFocus()

    def delete_recipe(self):
        if not self.conn:
            if translate:
                self.show_warning('Error', 'First open or create a database')
            else:
                self.show_warning('Ошибка', 'Сначала откройте или создайте базу данных')
            return
        current_item = self.recipe_list.currentItem()
        if not current_item:
            if translate:
                self.show_warning('Error', 'Select a recipe to delete')
            else:
                self.show_warning('Ошибка', 'Выберите рецепт для удаления')
            return
        recipe_data = current_item.data(Qt.ItemDataRole.UserRole)
        recipe_name = recipe_data.get('name', '')
        if translate:
            reply = QMessageBox.question(self, 'Confirmation',
                                         f'Are you sure you want to delete recipe "{recipe_name}"?',
                                         QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
        else:
            reply = QMessageBox.question(self, 'Подтверждение',
                                         f'Вы уверены, что хотите удалить рецепт "{recipe_name}"?',
                                         QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
        if reply == QMessageBox.StandardButton.Yes:
            try:
                cursor = self.conn.cursor()
                cursor.execute('DELETE FROM recipes WHERE id = ?', (recipe_data['id'],))
                self.conn.commit()
                row = self.recipe_list.row(current_item)
                self.recipe_list.takeItem(row)
                self.clear_form()
                self.current_recipe_id = None
                if translate:
                    self.detail_title.setText('Select Recipe')
                else:
                    self.detail_title.setText('Выберите рецепт')
                self.filter_recipes()
            except Exception as e:
                self.show_error('Failed to delete recipe' if translate else 'Не удалось удалить рецепт', str(e))

    def save_recipe(self):
        if not self.conn:
            if translate:
                self.show_warning('Error', 'First open or create a database')
            else:
                self.show_warning('Ошибка', 'Сначала откройте или создайте базу данных')
            return
        name = self.name_input.text().strip()
        if not name:
            if translate:
                self.show_warning('Error', 'Enter recipe name')
            else:
                self.show_warning('Ошибка', 'Введите название рецепта')
            return
        category = self.category_combo.currentText()
        if translate:
            category_map = {
                'Breakfast': 'Завтрак',
                'Lunch': 'Обед',
                'Dinner': 'Ужин',
                'Dessert': 'Десерт',
                'Drink': 'Напиток',
                'Other': 'Другое'
            }
            save_category = category_map.get(category, category)
        else:
            save_category = category
        category_id = self.category_id_map.get(save_category)
        if category_id is None:
            if translate:
                self.show_warning('Error', f'Category "{save_category}" not found in database')
            else:
                self.show_warning('Ошибка', f'Категория "{save_category}" не найдена в базе данных')
            return

        ingredients_text = self.ingredients_input.toPlainText().strip()
        recipe_data = {
            'name': name,
            'category_id': category_id,
            'prep_time': self.prep_time.value(),
            'ingredients': ingredients_text,
            'instructions': self.instructions_input.toPlainText().strip()
        }
        try:
            cursor = self.conn.cursor()
            if self.current_recipe_id is not None:
                cursor.execute('''
                    UPDATE recipes 
                    SET name = ?, category_id = ?, prep_time = ?, ingredients = ?, instructions = ?, modified_date = CURRENT_TIMESTAMP
                    WHERE id = ?
                ''', (recipe_data['name'], recipe_data['category_id'], recipe_data['prep_time'],
                      recipe_data['ingredients'], recipe_data['instructions'], self.current_recipe_id))
                current_items = self.recipe_list.findItems(name, Qt.MatchFlag.MatchExactly)
                if current_items:
                    item = current_items[0]
                    item.setText(recipe_data['name'])
                    item.setData(Qt.ItemDataRole.UserRole, {
                        'id': self.current_recipe_id,
                        'name': recipe_data['name'],
                        'category_id': recipe_data['category_id'],
                        'category': save_category,
                        'prep_time': recipe_data['prep_time'],
                        'ingredients': recipe_data['ingredients'].split('\n') if recipe_data['ingredients'] else [],
                        'instructions': recipe_data['instructions']
                    })
            else:
                cursor.execute('''
                    INSERT INTO recipes (name, category_id, prep_time, ingredients, instructions)
                    VALUES (?, ?, ?, ?, ?)
                ''', (recipe_data['name'], recipe_data['category_id'], recipe_data['prep_time'],
                      recipe_data['ingredients'], recipe_data['instructions']))
                new_id = cursor.lastrowid
                item = QListWidgetItem(recipe_data['name'])
                item.setData(Qt.ItemDataRole.UserRole, {
                    'id': new_id,
                    'name': recipe_data['name'],
                    'category_id': recipe_data['category_id'],
                    'category': save_category,
                    'prep_time': recipe_data['prep_time'],
                    'ingredients': recipe_data['ingredients'].split('\n') if recipe_data['ingredients'] else [],
                    'instructions': recipe_data['instructions']
                })
                self.recipe_list.addItem(item)
                self.current_recipe_id = new_id
            self.conn.commit()
            if translate:
                self.show_info('Success', 'Recipe saved!')
            else:
                self.show_info('Успех', 'Рецепт сохранен!')
            self.filter_recipes()
        except Exception as e:
            self.show_error('Failed to save recipe' if translate else 'Не удалось сохранить рецепт', str(e))

    def cancel_edit(self):
        if self.current_recipe_id is not None:
            current_items = self.recipe_list.selectedItems()
            if current_items:
                recipe_data = current_items[0].data(Qt.ItemDataRole.UserRole)
                self.display_recipe(recipe_data)
        else:
            self.clear_form()
            if translate:
                self.detail_title.setText('Select Recipe')
            else:
                self.detail_title.setText('Выберите рецепт')

    def clear_form(self):
        self.name_input.clear()
        self.category_combo.setCurrentIndex(0)
        self.prep_time.setValue(30)
        self.ingredients_input.clear()
        self.instructions_input.clear()
        self.recipe_list.clearSelection()
        self.current_recipe_id = None

    def show_database_info(self):
        if not self.conn:
            if translate:
                self.show_info('Information', 'Database not selected')
            else:
                self.show_info('Информация', 'База данных не выбрана')
            return
        try:
            cursor = self.conn.cursor()
            cursor.execute('SELECT COUNT(*) FROM recipes')
            count = cursor.fetchone()[0]
            cursor.execute('SELECT COUNT(*) FROM categories')
            categories_count = cursor.fetchone()[0]
            if translate:
                info_text = f"""Database Information:
File: {os.path.basename(self.current_db_path)}
Path: {self.current_db_path}
Total recipes: {count}
Number of categories: {categories_count}"""
                self.show_info('Database Information', info_text)
            else:
                info_text = f"""Информация о базе данных:
Файл: {os.path.basename(self.current_db_path)}
Путь: {self.current_db_path}
Всего рецептов: {count}
Количество категорий: {categories_count}"""
                self.show_info('Информация о базе данных', info_text)
        except Exception as e:
            self.show_error('Failed to get information' if translate else 'Не удалось получить информацию', str(e))

    def show_random_recipe(self):
        if not self.conn:
            if translate:
                self.show_warning('Error', 'First open or create a database')
            else:
                self.show_warning('Ошибка', 'Сначала откройте или создайте базу данных')
            return
        try:
            cursor = self.conn.cursor()
            cursor.execute('SELECT DISTINCT c.name FROM categories c JOIN recipes r ON c.id = r.category_id')
            categories = [row[0] for row in cursor.fetchall()]
            if not categories:
                if translate:
                    self.show_info('Information', 'No recipes in database')
                else:
                    self.show_info('Информация', 'В базе данных нет рецептов')
                return
            dialog = CategoryDialog(categories, self)
            if dialog.exec() == QDialog.DialogCode.Accepted:
                selected_category = dialog.get_selected_category()
                if (selected_category == "Случайная" or
                        (translate and selected_category == "Random")):
                    cursor.execute('''
                        SELECT r.id, r.name, r.category_id, r.prep_time, r.ingredients, r.instructions, c.name as category_name 
                        FROM recipes r 
                        JOIN categories c ON r.category_id = c.id 
                        ORDER BY RANDOM() LIMIT 1
                    ''')
                else:
                    search_category = selected_category
                    if translate:
                        category_map = {
                            'Breakfast': 'Завтрак',
                            'Lunch': 'Обед',
                            'Dinner': 'Ужин',
                            'Dessert': 'Десерт',
                            'Drink': 'Напиток',
                            'Other': 'Другое'
                        }
                        search_category = category_map.get(selected_category, selected_category)
                    cursor.execute('''
                        SELECT r.id, r.name, r.category_id, r.prep_time, r.ingredients, r.instructions, c.name as category_name 
                        FROM recipes r 
                        JOIN categories c ON r.category_id = c.id 
                        WHERE c.name = ? 
                        ORDER BY RANDOM() LIMIT 1
                    ''', (search_category,))
                recipe = cursor.fetchone()
                if recipe:
                    recipe_data = {
                        'id': recipe[0],
                        'name': recipe[1],
                        'category_id': recipe[2],
                        'category': recipe[6],
                        'prep_time': recipe[3],
                        'ingredients': recipe[4].split('\n') if recipe[4] else [],
                        'instructions': recipe[5]
                    }
                    self.display_recipe(recipe_data)
                    self.current_recipe_id = recipe_data['id']
                    items = self.recipe_list.findItems(recipe_data['name'], Qt.MatchFlag.MatchExactly)
                    if items:
                        self.recipe_list.setCurrentItem(items[0])
                    display_category = recipe_data["category"]
                    if translate:
                        category_map = {
                            'Завтрак': 'Breakfast',
                            'Обед': 'Lunch',
                            'Ужин': 'Dinner',
                            'Десерт': 'Dessert',
                            'Напиток': 'Drink',
                            'Другое': 'Other'
                        }
                        display_category = category_map.get(display_category, display_category)
                    if translate:
                        self.show_info('WhatTheEat™',
                                       f'Random recipe: {recipe_data["name"]}\n'
                                       f'Category: {display_category}\n'
                                       f'Preparation time: {recipe_data["prep_time"]} minutes')
                    else:
                        self.show_info('ЧёПоесть™',
                                       f'Случайный рецепт: {recipe_data["name"]}\n'
                                       f'Категория: {display_category}\n'
                                       f'Время приготовления: {recipe_data["prep_time"]} минут')
                else:
                    if translate:
                        self.show_info('Information',
                                       f'No recipes in category "{selected_category}"')
                    else:
                        self.show_info('Информация',
                                       f'В категории "{selected_category}" нет рецептов')
        except Exception as e:
            self.show_error('Failed to get random recipe' if translate else 'Не удалось получить случайный рецепт',
                            str(e))

    def show_about(self):
        if translate:
            QMessageBox.about(self, 'About WhatTheEat',
                              'WhatToEat Alpha\n\n'
                              'Your personal electronic cookbook.\n\n'
                              'Features:\n'
                              '• Create and edit recipes\n'
                              '• Work with multiple databases\n'
                              '• Search recipes\n'
                              '• Dish categorization\n'
                              '• And one surprise ;P')
        else:
            QMessageBox.about(self, 'О программе ЧёПоесть',
                              'ЧёПоесть Alpha\n\n'
                              'Ваша персональная электронная кулинарная книга.\n\n'
                              'Возможности:\n'
                              '• Создание и редактирование рецептов\n'
                              '• Работа с несколькими базами данных\n'
                              '• Поиск по рецептам\n'
                              '• Категоризация блюд\n'
                              '• И один сюрприз ;P')

    def closeEvent(self, event):
        if self.conn:
            self.conn.close()
        event.accept()


if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = WhatTheEat()
    window.show()
    sys.exit(app.exec())