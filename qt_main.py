#!/usr/bin/env python3
"""FitnessToolbox — Qt6 版本（示例）

运行: python3 qt_main.py

依赖: PySide6
"""
from math import pi
import sys
import json
import os

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QApplication,
    QCheckBox,
    QFormLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QListWidget,
    QMessageBox,
    QPushButton,
    QTabWidget,
    QVBoxLayout,
    QWidget,
    QTableWidget,
    QTableWidgetItem,
    QGroupBox,
    QSplitter,
    QScrollArea,
    QSizePolicy,
    QHeaderView,
    QSpinBox,
    QMenu,
)


def to_float(s):
    try:
        s = s.strip()
        if s == "":
            return None
        return float(s)
    except Exception:
        return None


class TreadmillTab(QWidget):
    """跑步机选项卡 — 支持单级或二级传动，界面左侧输入、右侧结果与型号管理。"""

    def __init__(self, parent=None):
        super().__init__(parent)
        # models persistence
        self.models = {}
        self.models_path = os.path.join(os.path.dirname(__file__), 'models.json')
        self.fields = []
        self.fields_path = os.path.join(os.path.dirname(__file__), 'fields.json')
        self.load_models()
        self.load_fields()
        self.init_ui()

    def init_ui(self):
        # 左侧输入表单
        form = QFormLayout()
        # 所有标签与控件靠右排列，使输入区更紧凑
        form.setLabelAlignment(Qt.AlignRight)
        form.setFormAlignment(Qt.AlignRight | Qt.AlignTop)
        # 标签右对齐，使输入区更靠右、更紧凑
        form.setLabelAlignment(Qt.AlignRight)
        self.motor_power_edit = QLineEdit()
        self.motor_rpm_edit = QLineEdit()
        self.motor_pulley_d_edit = QLineEdit()  # mm
        self.roller_pulley_d_edit = QLineEdit()  # mm
        self.roller_diameter_edit = QLineEdit()  # mm
        self.belt_speed_edit = QLineEdit()  # km/h
        # 统一缩小输入宽度并右对齐文本
        for edt in (self.motor_power_edit, self.motor_rpm_edit, self.motor_pulley_d_edit,
                    self.roller_pulley_d_edit, self.roller_diameter_edit, self.belt_speed_edit):
            try:
                edt.setMaximumWidth(180)
                edt.setAlignment(Qt.AlignRight)
            except Exception:
                pass

        form.addRow(QLabel('<b>电机功率 (W)</b>'), self.motor_power_edit)
        form.addRow('电机转速 (RPM)', self.motor_rpm_edit)
        form.addRow('电机带轮直径 (mm)', self.motor_pulley_d_edit)

        # 二级传动
        self.use_secondary_chk = QCheckBox('使用二级传动轮')
        self.sec1_d_edit = QLineEdit()
        self.sec2_d_edit = QLineEdit()
        for edt in (self.sec1_d_edit, self.sec2_d_edit):
            try:
                edt.setMaximumWidth(180)
                edt.setAlignment(Qt.AlignRight)
            except Exception:
                pass
        # 将二级传动项直接加入主表单，紧跟电机带轮之后，提升界面连贯性
        form.addRow(self.use_secondary_chk)
        form.addRow('二级带轮（电机侧）直径 (mm)', self.sec1_d_edit)
        form.addRow('二级带轮（滚筒侧）直径 (mm)', self.sec2_d_edit)

        form.addRow(QLabel('<b>滚筒带轮直径 (mm)</b>'), self.roller_pulley_d_edit)
        form.addRow('滚筒直径 (mm)', self.roller_diameter_edit)
        form.addRow('跑带时速 (km/h)', self.belt_speed_edit)

        btn_compute = QPushButton('计算（当且仅当有且只有一项为空时）')
        btn_compute.clicked.connect(self.compute_missing)

        left_v = QVBoxLayout()
        left_v.addLayout(form)
        # form layout to contain custom fields (initialized before scroll area)
        self.custom_fields_form = QFormLayout()

        # 不在左侧显示自定义字段输入（字段只在表格中可见）

        # 计算按钮放底部
        btn_box = QHBoxLayout()
        btn_box.addStretch(1)
        btn_box.addWidget(btn_compute)
        btn_box.addStretch(1)
        left_v.addLayout(btn_box)

        # 右侧结果与型号管理
        self.lbl_roller_rpm = QLabel('-')
        self.lbl_motor_rpm = QLabel('-')
        self.lbl_belt_kmh = QLabel('-')
        self.lbl_gear_ratio = QLabel('-')
        self.lbl_sec1 = QLabel('-')
        self.lbl_sec2 = QLabel('-')
        self.lbl_roller_diameter = QLabel('-')

        res_form = QFormLayout()
        res_form.addRow('<b>计算结果</b>', QLabel(''))
        res_form.addRow('滚筒转速 (RPM)', self.lbl_roller_rpm)
        res_form.addRow('电机转速 (RPM)', self.lbl_motor_rpm)
        res_form.addRow('跑带时速 (km/h)', self.lbl_belt_kmh)
        res_form.addRow('总传动比 (motor->roller)', self.lbl_gear_ratio)
        res_form.addRow('二级带轮（电机侧）(mm)', self.lbl_sec1)
        res_form.addRow('二级带轮（滚筒侧）(mm)', self.lbl_sec2)
        res_form.addRow('滚筒直径 (mm)', self.lbl_roller_diameter)

        model_h = QHBoxLayout()
        self.model_name_edit = QLineEdit()
        self.model_name_edit.setPlaceholderText('输入产品型号名称')
        self.btn_save_model = QPushButton('保存为产品型号')
        self.btn_save_model.clicked.connect(self.save_model)
        model_h.addWidget(self.model_name_edit)
        model_h.addWidget(self.btn_save_model)

        # model table (像 Excel 的表格视图)
        self.model_table = QTableWidget()
        self.model_table.setColumnCount(2 + len(self.fields))
        headers = ['#', '型号'] + list(self.fields)
        self.model_table.setHorizontalHeaderLabels(headers)
        # 允许通过点击表头排序
        try:
            self.model_table.setSortingEnabled(True)
        except Exception:
            pass
        self.model_table.cellClicked.connect(lambda r, c: self.on_table_clicked(r, c))
        # 右键菜单：在表格行上右键可删除该型号
        try:
            self.model_table.setContextMenuPolicy(Qt.CustomContextMenu)
            self.model_table.customContextMenuRequested.connect(self.on_model_table_context_menu)
        except Exception:
            pass
        # 字段管理现在移动到设置选项卡（不在此显示）
        field_h = QHBoxLayout()

        # 型号详情与行内参数编辑已移除（表格足够展示字段）

        # 结果区包装
        result_box = QGroupBox('计算结果')
        result_box.setLayout(res_form)

        # 型号管理包装
        self.model_box = QGroupBox('产品型号管理')
        model_box_layout = QVBoxLayout()
        model_box_layout.addLayout(model_h)
        model_box_layout.addLayout(field_h)
        model_box_layout.addWidget(self.model_table)
        # 删除操作已移至表格右键菜单（避免界面冗余按钮）
        self.model_box.setLayout(model_box_layout)

        # 上方：参数输入 与 计算结果 并排
        left_group = QGroupBox('参数输入')
        outer_h = QHBoxLayout()
        outer_h.addStretch(1)
        outer_h.addLayout(left_v)
        left_group.setLayout(outer_h)
        left_group.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Expanding)
        left_group.setMaximumWidth(420)

        result_group = QGroupBox('计算结果')
        result_group.setLayout(res_form)

        top_h = QHBoxLayout()
        top_h.addWidget(left_group)
        top_h.addWidget(result_group)

        # 主布局：上方并排（参数+结果），下方型号管理
        main_layout = QVBoxLayout()
        main_layout.addLayout(top_h)
        # 将 model_box 拖动到底部（主窗口将负责复用显示）
        main_layout.addWidget(self.model_box)
        main_layout.setContentsMargins(8, 8, 8, 8)
        main_layout.setSpacing(10)
        self.setLayout(main_layout)

        # 美化与表格布局调整
        try:
            self.model_table.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
            self.model_table.setMinimumHeight(300)
            header = self.model_table.horizontalHeader()
            # 允许用户通过鼠标拖拽调整列宽
            header.setSectionResizeMode(QHeaderView.Interactive)
            # 允许通过垂直表头拖拽调整行高
            try:
                vh = self.model_table.verticalHeader()
                vh.setSectionResizeMode(QHeaderView.Interactive)
            except Exception:
                pass
        except Exception:
            pass

        # UI 偏好文件路径
        self.prefs_path = os.path.join(os.path.dirname(__file__), 'ui_prefs.json')
        try:
            self.load_ui_prefs()
        except Exception:
            pass

        # 刷新已保存模型列表（不创建左侧自定义输入）
        self.refresh_model_list()

    def format_gear_ratio(self, ratio):
        """格式化传动比为 N:1 或 1:N 形式，保留最多 3 位小数并去除多余零。"""
        if ratio is None:
            return '-'
        try:
            r = float(ratio)
        except Exception:
            return str(ratio)
        if r == 0:
            return '0:1'
        if r >= 1.0:
            s = f"{r:.3f}".rstrip('0').rstrip('.')
            return f"{s}:1"
        else:
            inv = 1.0 / r
            s = f"{inv:.3f}".rstrip('0').rstrip('.')
            return f"1:{s}"

    def compute_missing(self):
        motor_power = to_float(self.motor_power_edit.text())
        motor_rpm = to_float(self.motor_rpm_edit.text())
        motor_pulley_d = to_float(self.motor_pulley_d_edit.text())
        roller_pulley_d = to_float(self.roller_pulley_d_edit.text())
        roller_diameter = to_float(self.roller_diameter_edit.text())
        belt_kmh = to_float(self.belt_speed_edit.text())

        use_secondary = self.use_secondary_chk.isChecked()
        sec1 = to_float(self.sec1_d_edit.text())
        sec2 = to_float(self.sec2_d_edit.text())

        # helper funcs
        def compute_roller_rpm_from_belt_kmh(kmh, roller_d_mm):
            v = kmh / 3.6
            if roller_d_mm is None or roller_d_mm <= 0:
                return None
            return v * 60.0 / (pi * (roller_d_mm / 1000.0))

        def compute_belt_kmh_from_roller_rpm(roller_rpm, roller_d_mm):
            if roller_d_mm is None:
                return None
            v = (pi * (roller_d_mm / 1000.0) * roller_rpm) / 60.0
            return v * 3.6

        def gear_ratio_total(motor_pulley, roller_pulley, use_sec, s1, s2):
            if use_sec:
                if None in (motor_pulley, s1, s2, roller_pulley):
                    return None
                return (motor_pulley / s1) * (s2 / roller_pulley)
            else:
                if None in (motor_pulley, roller_pulley):
                    return None
                return (motor_pulley / roller_pulley)

        # Try compute roller_rpm from belt if possible
        roller_rpm = None
        if belt_kmh is not None and roller_diameter is not None:
            roller_rpm = compute_roller_rpm_from_belt_kmh(belt_kmh, roller_diameter)

        # If secondary enabled and exactly one sec missing, try compute it using rpm ratio
        if use_secondary:
            sec_missing = None
            if sec1 is None and sec2 is not None:
                sec_missing = 'sec1'
            if sec2 is None and sec1 is not None:
                sec_missing = 'sec2'
            if sec_missing is not None and motor_rpm is not None and (roller_rpm is not None or belt_kmh is not None):
                # ensure roller_rpm is available
                if roller_rpm is None and belt_kmh is not None and roller_diameter is not None:
                    roller_rpm = compute_roller_rpm_from_belt_kmh(belt_kmh, roller_diameter)
                if roller_rpm is not None and motor_rpm != 0:
                    ratio_total = roller_rpm / motor_rpm
                    if sec_missing == 'sec1':
                        # sec1 = motor_pulley * (sec2 / roller_pulley) / ratio_total
                        if None not in (motor_pulley_d, sec2, roller_pulley_d) and ratio_total != 0:
                            val = motor_pulley_d * (sec2 / roller_pulley_d) / ratio_total
                            self.lbl_sec1.setText(f"{val:.3f}")
                    else:
                        # sec2 = ratio_total * (sec1 * roller_pulley) / motor_pulley
                        if None not in (motor_pulley_d, sec1, roller_pulley_d):
                            val = ratio_total * (sec1 * roller_pulley_d) / motor_pulley_d
                            self.lbl_sec2.setText(f"{val:.3f}")

        # Count empties among core fields for main calculation
        core = {
            'motor_power': motor_power,
            'motor_rpm': motor_rpm,
            'motor_pulley_d': motor_pulley_d,
            'roller_pulley_d': roller_pulley_d,
            'roller_diameter': roller_diameter,
            'belt_kmh': belt_kmh,
        }
        empty_keys = [k for k, v in core.items() if v is None]
        if len(empty_keys) == 0:
            QMessageBox.information(self, '信息', '没有留空项 — 无需计算。')
            return
        if len(empty_keys) > 1:
            QMessageBox.warning(self, '错误', '请只留空一项以便计算。')
            return

        missing = empty_keys[0]

        try:
            if missing == 'belt_kmh':
                if roller_diameter is None:
                    QMessageBox.warning(self, '错误', '计算跑带时速需要已知滚筒直径。')
                    return
                if motor_rpm is not None:
                    ratio = gear_ratio_total(motor_pulley_d, roller_pulley_d, use_secondary, sec1, sec2)
                    if ratio is None:
                        QMessageBox.warning(self, '错误', '需要完整的带轮尺寸以计算。')
                        return
                    roller_rpm = motor_rpm * ratio
                    belt_kmh = compute_belt_kmh_from_roller_rpm(roller_rpm, roller_diameter)
                    # 只在结果标签显示，不写回输入框（保持原始留空）
                    self.lbl_roller_rpm.setText(f"{roller_rpm:.3f}")
                    self.lbl_motor_rpm.setText(f"{motor_rpm:.3f}")
                    self.lbl_belt_kmh.setText(f"{belt_kmh:.3f}")
                    self.lbl_gear_ratio.setText(self.format_gear_ratio(ratio))
                    return
                QMessageBox.warning(self, '错误', '缺少电机转速或带轮信息，无法计算时速。')
                return

            if missing == 'motor_rpm':
                if belt_kmh is None:
                    QMessageBox.warning(self, '错误', '计算电机转速需要已知跑带时速或滚筒转速。')
                    return
                if roller_diameter is None:
                    QMessageBox.warning(self, '错误', '计算电机转速需要滚筒直径。')
                    return
                roller_rpm = compute_roller_rpm_from_belt_kmh(belt_kmh, roller_diameter)
                ratio = gear_ratio_total(motor_pulley_d, roller_pulley_d, use_secondary, sec1, sec2)
                if ratio is None or ratio == 0:
                    QMessageBox.warning(self, '错误', '需要完整的带轮尺寸以计算电机转速。')
                    return
                motor_rpm = roller_rpm / ratio
                # 只显示在结果标签（保持输入框留空）
                self.lbl_roller_rpm.setText(f"{roller_rpm:.3f}")
                self.lbl_motor_rpm.setText(f"{motor_rpm:.3f}")
                self.lbl_belt_kmh.setText(f"{belt_kmh:.3f}")
                self.lbl_gear_ratio.setText(self.format_gear_ratio(ratio))
                return

            if missing == 'roller_diameter':
                if belt_kmh is None and motor_rpm is None:
                    QMessageBox.warning(self, '错误', '计算滚筒直径需要已知跑带时速或电机转速。')
                    return
                if motor_rpm is not None and (motor_pulley_d is None or roller_pulley_d is None):
                    QMessageBox.warning(self, '错误', '计算滚筒直径需要带轮直径信息。')
                    return
                if belt_kmh is not None and motor_rpm is None:
                    QMessageBox.warning(self, '错误', '无法仅用时速反推滚筒直径，请提供电机转速或带轮比例。')
                    return
                ratio = gear_ratio_total(motor_pulley_d, roller_pulley_d, use_secondary, sec1, sec2)
                if ratio is None or ratio == 0:
                    QMessageBox.warning(self, '错误', '需要带轮完整信息以计算滚筒直径。')
                    return
                roller_rpm = motor_rpm * ratio
                if belt_kmh is None:
                    QMessageBox.warning(self, '错误', '计算滚筒直径需要目标跑带时速（km/h）。')
                    return
                v = belt_kmh / 3.6
                D_m = v * 60.0 / (pi * roller_rpm)
                D_mm = D_m * 1000.0
                self.lbl_roller_rpm.setText(f"{roller_rpm:.3f}")
                self.lbl_motor_rpm.setText(f"{motor_rpm:.3f}")
                self.lbl_belt_kmh.setText(f"{belt_kmh:.3f}")
                self.lbl_gear_ratio.setText(self.format_gear_ratio(ratio))
                self.lbl_sec1.setText(self.lbl_sec1.text())
                self.lbl_sec2.setText(self.lbl_sec2.text())
                # 显示计算得到的滚筒直径（在结果区显示，不写回输入）
                self.lbl_roller_diameter.setText(f"{D_mm:.3f}")
                return

            if missing in ('motor_pulley_d', 'roller_pulley_d'):
                QMessageBox.information(self, '提示', '电机带轮或滚筒带轮的直径通常由机械结构决定，请手动填写其中一个以便计算。')
                return

            if missing == 'motor_power':
                QMessageBox.information(self, '提示', '电机功率需基于负载或扭矩估算，目前无法仅用带轮/转速计算。')
                return

        except Exception as e:
            QMessageBox.critical(self, '异常', f'计算时发生异常: {e}')

    # ----------------- model save/load / custom params -----------------
    def save_model(self):
        name = self.model_name_edit.text().strip()
        if not name:
            QMessageBox.warning(self, '错误', '请输入产品型号名称')
            return
        extras = self.models.get(name, {}).get('extras', {})
        # collect field values (if left-side custom edits exist — otherwise preserve existing)
        fields_values = {}
        cf = getattr(self, 'custom_field_edits', {})
        if cf:
            for f, edt in cf.items():
                fields_values[f] = edt.text().strip()
        else:
            fields_values = self.models.get(name, {}).get('fields', {})
        data = {
            'motor_power': self.motor_power_edit.text().strip(),
            'motor_rpm': self.motor_rpm_edit.text().strip(),
            'motor_pulley_d': self.motor_pulley_d_edit.text().strip(),
            'use_secondary': self.use_secondary_chk.isChecked(),
            'sec1': self.sec1_d_edit.text().strip(),
            'sec2': self.sec2_d_edit.text().strip(),
            'roller_pulley_d': self.roller_pulley_d_edit.text().strip(),
            'roller_diameter': self.roller_diameter_edit.text().strip(),
            'belt_kmh': self.belt_speed_edit.text().strip(),
            'computed': {
                'roller_rpm': self.lbl_roller_rpm.text(),
                'motor_rpm': self.lbl_motor_rpm.text(),
                'belt_kmh': self.lbl_belt_kmh.text(),
                'gear_ratio': self.lbl_gear_ratio.text(),
                'sec1': self.lbl_sec1.text(),
                'sec2': self.lbl_sec2.text(),
                'roller_diameter': self.lbl_roller_diameter.text(),
            },
            'extras': extras,
            'fields': fields_values,
        }
        self.models[name] = data
        self.persist_models()
        self.refresh_model_list()
        QMessageBox.information(self, '保存', f'已保存型号：{name}')

    def load_model_from_item(self, item):
        # compatibility: if table clicked, item may be QTableWidgetItem
        name = item.text() if hasattr(item, 'text') else str(item)
        self.load_model(name)

    def on_table_clicked(self, row, col):
        # load model by row
        it = self.model_table.item(row, 1)
        if it:
            name = it.text()
            self.load_model(name)

    def load_model(self, name):
        data = self.models.get(name)
        if not data:
            return
        self.model_name_edit.setText(name)
        self.motor_power_edit.setText(data.get('motor_power', ''))
        self.motor_rpm_edit.setText(data.get('motor_rpm', ''))
        self.motor_pulley_d_edit.setText(data.get('motor_pulley_d', ''))
        self.use_secondary_chk.setChecked(bool(data.get('use_secondary', False)))
        self.sec1_d_edit.setText(data.get('sec1', ''))
        self.sec2_d_edit.setText(data.get('sec2', ''))
        self.roller_pulley_d_edit.setText(data.get('roller_pulley_d', ''))
        self.roller_diameter_edit.setText(data.get('roller_diameter', ''))
        self.belt_speed_edit.setText(data.get('belt_kmh', ''))
        comp = data.get('computed', {})
        self.lbl_roller_rpm.setText(comp.get('roller_rpm', '-'))
        self.lbl_motor_rpm.setText(comp.get('motor_rpm', '-'))
        self.lbl_belt_kmh.setText(comp.get('belt_kmh', '-'))
        # 如果存储的是数字字符串或数值，则格式化为 N:1 风格，否则原样显示
        gr = comp.get('gear_ratio', '-')
        gr_float = to_float(str(gr))
        if gr_float is not None:
            self.lbl_gear_ratio.setText(self.format_gear_ratio(gr_float))
        else:
            self.lbl_gear_ratio.setText(str(gr))
        self.lbl_sec1.setText(comp.get('sec1', '-'))
        self.lbl_sec2.setText(comp.get('sec2', '-'))
        # extras previously shown in details; now omitted (table suffices)
        # load fields values into custom_field_edits
        fields_vals = data.get('fields', {})
        # if left-side edits exist, populate them; otherwise ignore (fields are displayed in table)
        for f, edt in getattr(self, 'custom_field_edits', {}).items():
            edt.setText(fields_vals.get(f, ''))

    # inline parameter editing removed — 使用设置页与表格管理字段和值

    def persist_models(self):
        try:
            with open(self.models_path, 'w', encoding='utf-8') as f:
                json.dump(self.models, f, ensure_ascii=False, indent=2)
        except Exception:
            pass

    def persist_fields(self):
        try:
            with open(self.fields_path, 'w', encoding='utf-8') as f:
                json.dump(self.fields, f, ensure_ascii=False, indent=2)
        except Exception:
            pass

    def load_models(self):
        try:
            if os.path.exists(self.models_path):
                with open(self.models_path, 'r', encoding='utf-8') as f:
                    self.models = json.load(f)
        except Exception:
            self.models = {}

    def load_fields(self):
        try:
            if os.path.exists(self.fields_path):
                with open(self.fields_path, 'r', encoding='utf-8') as f:
                    # preserve legacy simple-list format
                    raw = json.load(f)
                    if isinstance(raw, list) and raw and isinstance(raw[0], dict):
                        # new format list of dicts
                        self.fields = [it.get('name') for it in raw]
                    else:
                        self.fields = raw
        except Exception:
            self.fields = []

    def refresh_model_list(self):
        # refresh table view
        self.refresh_table()

    def refresh_table(self):
        names = sorted(self.models.keys())
        cols = ['#', '型号'] + list(self.fields)
        self.model_table.clear()
        self.model_table.setColumnCount(len(cols))
        self.model_table.setHorizontalHeaderLabels(cols)
        self.model_table.setRowCount(len(names))
        for r, name in enumerate(names):
            self.model_table.setItem(r, 0, QTableWidgetItem(str(r+1)))
            self.model_table.setItem(r, 1, QTableWidgetItem(name))
            data = self.models.get(name, {})
            fvals = data.get('fields', {})
            for c, fld in enumerate(self.fields, start=2):
                self.model_table.setItem(r, c, QTableWidgetItem(str(fvals.get(fld, ''))))
        # resize columns to contents
        try:
            self.model_table.resizeColumnsToContents()
        except Exception:
            pass

    def delete_selected_model(self):
        sel = self.model_table.currentRow()
        if sel < 0:
            QMessageBox.information(self, '提示', '请先选择一行要删除的型号')
            return
        it = self.model_table.item(sel, 1)
        if not it:
            QMessageBox.warning(self, '错误', '无法识别选中型号')
            return
        name = it.text()
        ok = QMessageBox.question(self, '确认', f'确认删除型号：{name} ?')
        if ok != QMessageBox.Yes:
            return
        if name in self.models:
            del self.models[name]
            self.persist_models()
            self.refresh_table()
            QMessageBox.information(self, '已删除', f'已删除型号：{name}')

    # expose a helper for MainWindow to reparent the model_box
    def take_model_box(self):
        # remove from current layout
        try:
            parent = self.model_box.parent()
            if parent and hasattr(parent, 'layout'):
                try:
                    parent.layout().removeWidget(self.model_box)
                except Exception:
                    pass
            self.model_box.setParent(None)
        except Exception:
            pass
        return self.model_box

    def on_model_table_context_menu(self, pos):
        idx = self.model_table.indexAt(pos)
        if not idx.isValid():
            return
        menu = QMenu(self)
        act_copy = menu.addAction('复制此行（含字段）')
        act_sort_asc = menu.addAction('按此列升序排序')
        act_sort_desc = menu.addAction('按此列降序排序')
        menu.addSeparator()
        act_delete = menu.addAction('删除所选型号')
        action = menu.exec(self.model_table.viewport().mapToGlobal(pos))
        row = idx.row()
        col = idx.column()
        if action == act_copy:
            try:
                cols = self.model_table.columnCount()
                headers = [self.model_table.horizontalHeaderItem(c).text() if self.model_table.horizontalHeaderItem(c) else '' for c in range(cols)]
                vals = [self.model_table.item(row, c).text() if self.model_table.item(row, c) else '' for c in range(cols)]
                parts = [f"{h}:{v}" if h else v for h, v in zip(headers, vals)]
                text = '\t'.join(parts)
                QApplication.clipboard().setText(text)
                QMessageBox.information(self, '已复制', '已将当前行复制到剪贴板（含字段）')
            except Exception:
                pass
        elif action == act_sort_asc:
            try:
                self.model_table.sortItems(col, Qt.AscendingOrder)
            except Exception:
                pass
        elif action == act_sort_desc:
            try:
                self.model_table.sortItems(col, Qt.DescendingOrder)
            except Exception:
                pass
        elif action == act_delete:
            # set current row and call delete
            self.model_table.selectRow(row)
            self.delete_selected_model()

    # ---------------- UI prefs: 保存/加载列宽与行高与锁定 ----------------
    def apply_ui_prefs(self, prefs: dict):
        if not prefs:
            return
        # apply column widths
        cols = self.model_table.columnCount()
        cw = prefs.get('col_widths', [])
        for i in range(min(cols, len(cw))):
            try:
                self.model_table.setColumnWidth(i, int(cw[i]))
            except Exception:
                pass
        # apply row heights
        rows = self.model_table.rowCount()
        rh = prefs.get('row_heights', [])
        for r in range(min(rows, len(rh))):
            try:
                self.model_table.setRowHeight(r, int(rh[r]))
            except Exception:
                pass
        # apply locked state
        locked = prefs.get('locked', False)
        header = self.model_table.horizontalHeader()
        vh = self.model_table.verticalHeader()
        if locked:
            try:
                header.setSectionResizeMode(QHeaderView.Fixed)
                vh.setSectionResizeMode(QHeaderView.Fixed)
                header.setSectionsMovable(False)
                header.setSectionsClickable(False)
            except Exception:
                pass
        else:
            try:
                header.setSectionResizeMode(QHeaderView.Interactive)
                vh.setSectionResizeMode(QHeaderView.Interactive)
                header.setSectionsMovable(True)
                header.setSectionsClickable(True)
            except Exception:
                pass

    def load_ui_prefs(self):
        try:
            if os.path.exists(self.prefs_path):
                with open(self.prefs_path, 'r', encoding='utf-8') as f:
                    prefs = json.load(f)
                    # apply saved field row height to settings tree later handled by SettingsTab
                    self.apply_ui_prefs(prefs)
        except Exception:
            pass

    def create_custom_field_inputs(self):
        # rebuild left-side inputs for each custom field
        # delete old widgets safely
        try:
            for edt in list(self.custom_field_edits.values()):
                try:
                    edt.deleteLater()
                except Exception:
                    pass
        except Exception:
            pass
        self.custom_field_edits = {}
        # remove all rows from the form
        try:
            while self.custom_fields_form.rowCount() > 0:
                self.custom_fields_form.removeRow(0)
        except Exception:
            pass
        # create new edits
        new_edits = {}
        for fld in self.fields:
            edt = QLineEdit()
            edt.setPlaceholderText(fld)
            self.custom_fields_form.addRow(fld, edt)
            new_edits[fld] = edt
        self.custom_field_edits = new_edits

    def add_field(self):
        name = self.new_field_edit.text().strip()
        if not name:
            QMessageBox.warning(self, '错误', '请输入字段名称')
            return
        if name in self.fields:
            QMessageBox.information(self, '信息', '字段已存在')
            return
        self.fields.append(name)
        self.persist_fields()
        self.create_custom_field_inputs()
        self.refresh_table()
        self.new_field_edit.clear()


class SettingsTab(QWidget):
    """设置：管理自定义字段，仅通过此面板修改字段列表。
    负责保存 UI 偏好到 `ui_prefs.json`（列宽、行高、锁定、字段行高、深色主题）。
    """

    def __init__(self, treadmill=None, parent=None):
        super().__init__(parent)
        self.treadmill = treadmill
        self.fields_path = os.path.join(os.path.dirname(__file__), 'fields.json')
        self.prefs_path = os.path.join(os.path.dirname(__file__), 'ui_prefs.json')
        self.fields = []
        self.load_fields()
        self.init_ui()
        # 尝试加载并应用 ui prefs（但表格可能尚未就绪）
        try:
            self.load_ui_prefs()
        except Exception:
            pass

    def init_ui(self):
        layout = QVBoxLayout()
        self.list = QListWidget()
        self.refresh_list()

        h = QHBoxLayout()
        self.new_field = QLineEdit()
        self.new_field.setPlaceholderText('字段名称，例如：跑带宽度')
        self.btn_add = QPushButton('添加')
        self.btn_remove = QPushButton('删除所选')
        self.btn_add.clicked.connect(self.add_field)
        self.btn_remove.clicked.connect(self.remove_selected)
        h.addWidget(self.new_field)
        h.addWidget(self.btn_add)
        h.addWidget(self.btn_remove)
        layout.addWidget(QLabel('自定义字段（仅显示于型号表）'))
        layout.addWidget(self.list)
        layout.addLayout(h)
        # 表格尺寸保存/锁定控制
        ctrl_h = QHBoxLayout()
        self.btn_save_lock = QPushButton('保存并锁定表格尺寸')
        self.btn_unlock = QPushButton('解锁表格尺寸')
        self.chk_apply_on_start = QCheckBox('启动时应用已保存尺寸')
        self.btn_save_lock.clicked.connect(self.save_and_lock_table_prefs)
        self.btn_unlock.clicked.connect(self.unlock_table_prefs)
        ctrl_h.addWidget(self.btn_save_lock)
        ctrl_h.addWidget(self.btn_unlock)
        ctrl_h.addWidget(self.chk_apply_on_start)
        layout.addLayout(ctrl_h)

        # 主题控制
        theme_h = QHBoxLayout()
        self.chk_dark = QCheckBox('启用深色主题')
        self.chk_dark.stateChanged.connect(self.on_dark_toggle)
        theme_h.addWidget(self.chk_dark)
        layout.addLayout(theme_h)

        self.setLayout(layout)

    def load_fields(self):
        try:
            if os.path.exists(self.fields_path):
                with open(self.fields_path, 'r', encoding='utf-8') as f:
                    self.fields = json.load(f)
        except Exception:
            self.fields = []

    def persist_fields(self):
        try:
            with open(self.fields_path, 'w', encoding='utf-8') as f:
                json.dump(self.fields, f, ensure_ascii=False, indent=2)
        except Exception:
            pass

    def refresh_list(self):
        self.list.clear()
        for f in self.fields:
            self.list.addItem(f)

    # ---------------- UI prefs persistence ----------------
    def save_ui_prefs(self, prefs: dict):
        try:
            with open(self.prefs_path, 'w', encoding='utf-8') as f:
                json.dump(prefs, f, ensure_ascii=False, indent=2)
        except Exception:
            pass

    def load_ui_prefs(self):
        try:
            if os.path.exists(self.prefs_path):
                with open(self.prefs_path, 'r', encoding='utf-8') as f:
                    prefs = json.load(f)
                    # (no field row height control anymore)
                    # apply dark theme
                    if prefs.get('dark_theme'):
                        self.chk_dark.setChecked(True)
                        self.apply_dark_theme(True)
                    # if apply_on_start and treadmill exists, apply table prefs
                    if prefs.get('apply_on_start') and self.treadmill:
                        try:
                            self.treadmill.apply_ui_prefs(prefs)
                        except Exception:
                            pass
                    # set checkbox state
                    self.chk_apply_on_start.setChecked(bool(prefs.get('apply_on_start', False)))
        except Exception:
            pass

    def add_field(self):
        name = self.new_field.text().strip()
        if not name:
            QMessageBox.warning(self, '错误', '请输入字段名称')
            return
        if name in self.fields:
            QMessageBox.information(self, '信息', '字段已存在')
            return
        self.fields.append(name)
        self.persist_fields()
        self.refresh_list()
        # 更新 treadmill tab 的字段并刷新表格头
        try:
            if self.treadmill:
                self.treadmill.load_fields()
                self.treadmill.refresh_table()
        except Exception:
            pass
        self.new_field.clear()

    def remove_selected(self):
        it = self.list.currentItem()
        if not it:
            return
        name = it.text()
        if name in self.fields:
            self.fields.remove(name)
            self.persist_fields()
            self.refresh_list()
            try:
                if self.treadmill:
                    self.treadmill.load_fields()
                    self.treadmill.refresh_table()
            except Exception:
                pass

    def on_row_height_changed(self, val):
        # removed: no-op since row-height control was deleted
        return

    def save_and_lock_table_prefs(self):
        if not self.treadmill:
            QMessageBox.warning(self, '错误', '找不到表格控件')
            return
        tbl = self.treadmill.model_table
        prefs = {}
        prefs['col_widths'] = [tbl.columnWidth(i) for i in range(tbl.columnCount())]
        prefs['row_heights'] = [tbl.rowHeight(r) for r in range(tbl.rowCount())]
        prefs['locked'] = True
        prefs['dark_theme'] = bool(self.chk_dark.isChecked())
        prefs['apply_on_start'] = bool(self.chk_apply_on_start.isChecked())
        self.save_ui_prefs(prefs)
        # apply and lock
        try:
            self.treadmill.apply_ui_prefs(prefs)
            QMessageBox.information(self, '保存', '表格尺寸已保存并锁定')
        except Exception:
            pass

    def unlock_table_prefs(self):
        # load existing prefs, clear locked flag
        prefs = {}
        try:
            if os.path.exists(self.prefs_path):
                with open(self.prefs_path, 'r', encoding='utf-8') as f:
                    prefs = json.load(f)
        except Exception:
            prefs = {}
        prefs['locked'] = False
        self.save_ui_prefs(prefs)
        if self.treadmill:
            try:
                self.treadmill.apply_ui_prefs(prefs)
            except Exception:
                pass
        QMessageBox.information(self, '解锁', '表格尺寸已解锁，可手动调整')

    def on_dark_toggle(self, state):
        enabled = bool(state)
        self.apply_dark_theme(enabled)
        # persist change
        try:
            prefs = {}
            if os.path.exists(self.prefs_path):
                with open(self.prefs_path, 'r', encoding='utf-8') as f:
                    prefs = json.load(f)
        except Exception:
            prefs = {}
        prefs['dark_theme'] = enabled
        self.save_ui_prefs(prefs)

    def apply_dark_theme(self, enabled: bool):
        if enabled:
            dark = '''
            QWidget { background: #1e1e1e; color: #d4d4d4; }
            QTableWidget, QListWidget { background: #252526; color: #d4d4d4; }
            QHeaderView::section { background: #2d2d30; color: #d4d4d4; }
            QPushButton { background: #0e639c; color: #fff; }
            QLineEdit { background: #2d2d30; color: #d4d4d4; }
            '''
            QApplication.instance().setStyleSheet(dark)
        else:
            QApplication.instance().setStyleSheet('')



class MainWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle('FitnessToolbox (Qt6)')
        self.resize(900, 600)
        tabs = QTabWidget()
        # 创建实例以便后续刷新
        self.treadmill_tab = TreadmillTab()
        tabs.addTab(self.treadmill_tab, '跑步机')

        # 为其它选项卡创建带顶层占位内容的容器（产品型号管理会在切换时复用显示）
        def make_tab_placeholder(title):
            w = QWidget()
            l = QVBoxLayout()
            l.addWidget(QLabel(f'{title} 内容占位'))
            l.addStretch(1)
            w.setLayout(l)
            return w

        tabs.addTab(make_tab_placeholder('电机'), '电机')
        tabs.addTab(make_tab_placeholder('划船器'), '划船器')
        tabs.addTab(make_tab_placeholder('抖抖机'), '抖抖机')
        tabs.addTab(make_tab_placeholder('力量'), '力量')
        tabs.addTab(make_tab_placeholder('健身车'), '健身车')
        tabs.addTab(make_tab_placeholder('筋膜枪'), '筋膜枪')

        # 设置选项卡：字段管理
        self.settings_tab = SettingsTab(self.treadmill_tab)
        tabs.addTab(self.settings_tab, '设置')

        # 将 treadmill 的 model_box 提取到主窗口下方，作为共享区域（保证跨标签大小一致）
        try:
            shared_box = self.treadmill_tab.take_model_box()
            shared_box.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
        except Exception:
            shared_box = None

        layout = QVBoxLayout()
        layout.addWidget(tabs)
        if shared_box is not None:
            layout.addWidget(shared_box)
        self.setLayout(layout)
        # 简洁样式：更现代、更整齐的间距与表格显示
        self.setStyleSheet('''
        QWidget { font-family: -apple-system, system-ui, "Segoe UI", Roboto, "Helvetica Neue", Arial; font-size: 13px; }
        QGroupBox { font-weight: 600; margin-top: 6px; }
        QGroupBox::title { subcontrol-origin: margin; left: 8px; padding: 2px 6px; }
        QTableWidget { gridline-color: #e6e6e6; }
        QHeaderView::section { background: #f3f4f6; padding: 6px; border: 1px solid #e6e6e6; }
        QPushButton { padding: 6px 10px; }
        QLineEdit { padding: 4px 6px; }
        ''')


def main():
    app = QApplication(sys.argv)
    w = MainWindow()
    w.show()
    sys.exit(app.exec())


if __name__ == '__main__':
    main()
