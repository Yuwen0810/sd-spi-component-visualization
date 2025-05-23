import re
from collections import defaultdict
from itertools import chain
from typing import Generator, Iterator

from src.Models.DataClasses.SpiComponent import SpiComponent


class SpiComponentManager:
    def __init__(self):
        self._component_size_dict = defaultdict(lambda: defaultdict(list))
        self._component_id_dict = defaultdict(lambda: defaultdict(list))
        self._component_list: list[SpiComponent] = []
        self._line_id_list: list[str] = []
        self._panel_id_list: list[str] = []
        self._count = 0
        self._idno: int = -1
        self._product_name: str = ""

    def set_idno(self, idno: str | int):
        self._idno = int(idno)

    def get_idno(self) -> int:
        return self._idno

    def set_product_name(self, product_name: str):
        self._product_name = product_name

    def get_product_name(self) -> str:
        return self._product_name

    def set_line_id_list(self, *args):
        self._line_id_list.extend(args)

    def get_line_id_list(self) -> list[str]:
        return self._line_id_list

    def set_panel_id_list(self, *args):
        self._panel_id_list.extend(args)

    def get_panel_id_list(self) -> list[str]:
        return self._panel_id_list

    def add_component(self, component):
        self._component_size_dict[component.component_type][component.size].append(component)
        self._component_id_dict[component.component_type][component.component_id].append(component)
        self._component_list.append(component)
        self._count += 1

    def clear(self):
        self._component_size_dict.clear()
        self._component_id_dict.clear()
        self._component_list.clear()
        self._line_id_list.clear()
        self._panel_id_list.clear()
        self._count = 0
        self._idno: int = -1

    def iter_components_by_size(self) -> Iterator[tuple[str, str, list[SpiComponent]]]:
        for component_type, d in self._component_size_dict.items():
            for size, components in d.items():
                yield component_type, size, components

    def iter_components_by_id(self) -> Iterator[tuple[str, str, list[SpiComponent]]]:
        for component_type, d in self._component_id_dict.items():
            for component_id, components in d.items():
                yield component_type, component_id, components

    def get_components_by_size(self, component_type, size: str = None) -> list[SpiComponent]:
        if size:
            return self._component_size_dict[component_type][size]
        else:
            return list(chain.from_iterable(self._component_size_dict[component_type].values()))

    def get_components_by_id(self, component_id):
        component_size = component_id[0]
        return self._component_id_dict[component_size][component_id]

    def get_component_size_structure(self) -> list:
        res = []
        for component_type, d in self._component_size_dict.items():
            for size, components in d.items():
                res.append([component_type, size, len(components)])

        return sorted(res, key=lambda item: (item[0], item[1]))

    def get_component_id_structure(self) -> list:
        res = []
        for component_type, d in self._component_id_dict.items():
            for component_id, components in d.items():
                res.append([component_type, component_id, len(components)])

        return sorted(res, key=self.component_id_sort_key)

    def __iter__(self):
        return iter(self._component_list)

    def __len__(self):
        return self._count

    @staticmethod
    # 定義排序鍵函數
    def component_id_sort_key(item):
        # 分離 item[1] 的字母和數字部分
        match = re.match(r'([A-Za-z]*)(\d*)', item[1])
        if match:
            letters, numbers = match.groups()
            # 轉換數字字串為整數（如果為空則預設為0）
            number_val = int(numbers) if numbers else 0
            return (item[0], letters, number_val)
        return (item[0], item[1], 0)