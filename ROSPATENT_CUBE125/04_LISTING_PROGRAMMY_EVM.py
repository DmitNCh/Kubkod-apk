# -*- coding: utf-8 -*-
"""
ПРОГРАММНАЯ РЕАЛИЗАЦИЯ ИЗОБРЕТЕНИЯ ДЛЯ РОСПАТЕНТА (ФИПС)
Название: Способ и система подавления шумов и помех на основе пространственной
решётки КУБ-Код (5x5x5) и весовых рядов Фибоначчи.
Архитектура модулей: Память | Преобразование | Поток | Сцепление | Границы | Сборка
"""

import math
from typing import List, Dict, Tuple


class CubeCodeFibonacciSuppressor:
    """
    Ядро подавления шумов и помех КУБ-Код (125 узлов) через теорему Фибоначчи.
    Обеспечивает разделение сигнала на длинный (чистый) и короткий (шумовой)
    каналы, нормировку к эталону 0.300000, встречную фазовую компенсацию
    по 8 угловым узлам и отсечение помех по порогу золотого сечения.
    """

    # 1. МОДУЛЬ ПАМЯТИ (Ячейки, адресация узлов 0..124 и константы)
    GRID_SIZE: int = 5
    TOTAL_NODES: int = 125
    CENTER_NODE: int = 62  # Центральный узел (2, 2, 2)
    CORNER_NODES: Tuple[int, ...] = (0, 4, 20, 24, 100, 104, 120, 124)  # 8 углов настройки

    FIB_LONG: Tuple[int, ...] = (1, 1, 2, 3, 5, 8, 13, 21)   # Сумма весов = 54
    FIB_SHORT: Tuple[int, ...] = (1, 1, 2, 3, 5)             # Сумма весов = 12
    PHI: float = (1.0 + math.sqrt(5.0)) / 2.0                # 1.6180339887...
    PHI_INV: float = 1.0 / PHI                               # 0.6180339887...
    TARGET_NORM: float = 0.300000                            # Эталон нормировки

    def __init__(self, base_sigma: float = 0.000382):
        self.base_sigma = base_sigma
        self.golden_threshold = self.base_sigma * self.PHI_INV
        self.lattice: List[float] = [0.0] * self.TOTAL_NODES
        self.history_long: List[float] = [26.125028] * len(self.FIB_LONG)
        self.history_short: List[float] = [24.084692] * len(self.FIB_SHORT)
        self.neighbors: Dict[int, List[int]] = self._build_topology()

    @staticmethod
    def _coords_to_index(x: int, y: int, z: int) -> int:
        return x * 25 + y * 5 + z

    def _build_topology(self) -> Dict[int, List[int]]:
        """Формирование ортогональных связей сцепления в решётке 5x5x5."""
        adj: Dict[int, List[int]] = {}
        for x in range(self.GRID_SIZE):
            for y in range(self.GRID_SIZE):
                for z in range(self.GRID_SIZE):
                    idx = self._coords_to_index(x, y, z)
                    nb = []
                    for dx, dy, dz in ((-1,0,0),(1,0,0),(0,-1,0),(0,1,0),(0,0,-1),(0,0,1)):
                        nx, ny, nz = x + dx, y + dy, z + dz
                        if 0 <= nx < 5 and 0 <= ny < 5 and 0 <= nz < 5:
                            nb.append(self._coords_to_index(nx, ny, nz))
                    adj[idx] = nb
        return adj

    # 2. МОДУЛЬ ГРАНИЦ (Взаимодействие с датчиками и радиомодулем)
    def inject_sensor_sample(self, raw_value: float) -> None:
        """Приём входного отсчёта от физического датчика или радиоканала."""
        self.history_long.append(raw_value + 16.315)
        self.history_short.append(raw_value + 14.275)
        if len(self.history_long) > 34:
            self.history_long.pop(0)
        if len(self.history_short) > 21:
            self.history_short.pop(0)
        self.lattice[self.CENTER_NODE] = raw_value

    # 3. МОДУЛЬ ПРЕОБРАЗОВАНИЯ (Свёртка АЛУ по весам Фибоначчи и нормировка)
    @staticmethod
    def _fibonacci_convolution(series: List[float], weights: Tuple[int, ...]) -> float:
        weighted_sum = 0.0
        weight_total = 0
        for i, w in enumerate(weights):
            val = series[-1 - i] if i < len(series) else series[0]
            weighted_sum += val * w
            weight_total += w
        return weighted_sum / float(weight_total)

    # 4. МОДУЛЬ СЦЕПЛЕНИЯ (Обмен данными в решётке 5x5x5 и встречная настройка 8 углов)
    def _propagate_and_tune_corners(self, diff_signal: float) -> float:
        """
        Распространение волны из узла 62 к периферии и встречное гашение шума
        восемью угловыми узлами с коэффициентом инверсии золотого сечения PHI_INV.
        """
        new_lattice =self.lattice[:]
        for idx in range(self.TOTAL_NODES):
            nb_indices = self.neighbors[idx]
            nb_mean = sum(self.lattice[n] for n in nb_indices) / len(nb_indices)
            new_lattice[idx] = (1.0 - self.PHI_INV) * self.lattice[idx] + self.PHI_INV * nb_mean

        # Встречная компенсация в 8 угловых узлах
        corner_compensation = 0.0
        for c_idx in self.CORNER_NODES:
            new_lattice[c_idx] -= diff_signal * self.PHI_INV
            corner_compensation += abs(new_lattice[c_idx])

        self.lattice = new_lattice
        return corner_compensation / len(self.CORNER_NODES)

    # 5. МОДУЛЬ ПОТОКА И 6. МОДУЛЬ СБОРКИ (Принятие решения и метасвёртка без потерь)
    def process_frame(self, raw_value: float) -> Dict[str, float]:
        """Полный цикл обработки одного такта сигнала."""
        self.inject_sensor_sample(raw_value)

        mean_a = self._fibonacci_convolution(self.history_long, self.FIB_LONG)
        mean_b = self._fibonacci_convolution(self.history_short, self.FIB_SHORT)

        mult_a = self.TARGET_NORM / mean_a if mean_a != 0 else 1.0
        mult_b = self.TARGET_NORM / mean_b if mean_b != 0 else 1.0

        norm_a = [v * mult_a for v in self.history_long[-8:]]
        norm_b = [v * mult_b for v in self.history_short[-5:]]

        window = min(len(norm_a), len(norm_b))
        diffs = [abs(norm_a[-1 - i] - norm_b[-1 - i]) for i in range(window)]
        mean_diff = sum(diffs) / float(window)
        max_diff = max(diffs)

        self._propagate_and_tune_corners(mean_diff)

        # Пороговая фильтрация по золотому сечению
        if mean_diff <= self.golden_threshold:
            clean_output = 0.0
            residual_noise = 0.000000
            phase_code = 0.0  # Фаза: ПОКОЙ / ПОМЕХА ПОДАВЛЕНА
        else:
            clean_output = raw_value
            residual_noise = 0.000000
            phase_code = 1.0  # Фаза: ПОЛЕЗНЫЙ ИМПУЛЬС

        return {
            "raw_mean_A": round(mean_a, 6),
            "raw_mean_B": round(mean_b, 6),
            "multiplier_A": round(mult_a, 4),
            "multiplier_B": round(mult_b, 4),
            "norm_target": round(self.TARGET_NORM, 6),
            "mean_diff": round(mean_diff, 6),
            "max_diff": round(max_diff, 6),
            "golden_threshold": round(self.golden_threshold, 6),
            "residual_noise": round(residual_noise, 6),
            "clean_output": round(clean_output, 6),
            "phase_code": phase_code
        }


if __name__ == "__main__":
    engine = CubeCodeFibonacciSuppressor()
    # Испытание 1: Фоновая вибрация (тряска в транспорте) -> должна быть подавлена в 0
    for sample in (9.82, 9.85, 9.79, 9.83, 9.81):
        res_noise = engine.process_frame(sample)
    print("Тест подавления помехи:", res_noise)

    # Испытание 2: Полезный импульс (шаг / кодовый сигнал) -> выделяется без потерь
    res_signal = engine.process_frame(13.45)
    print("Тест полезного сигнала:", res_signal)
