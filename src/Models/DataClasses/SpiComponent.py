from dataclasses import dataclass

@dataclass
class SpiComponent:
    pad_id: int
    component_id: str
    component_type: str
    size_min: float
    size_max: float
    volume: float
    real_vol: int
    area: float
    real_area: int
    pos_x: float
    pos_y: float
    canvas_pos_x: int = -1
    canvas_pos_y: int = -1

    @property
    def size(self) -> str:
        return f"{self.size_min}x{self.size_max}"
