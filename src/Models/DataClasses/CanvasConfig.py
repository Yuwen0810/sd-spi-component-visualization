from dataclasses import dataclass


@dataclass
class CanvasConfig:
    # Fixed Attributes
    canvas_size: tuple[int, int] = (10000, 10000, 3)
    margin: int = 100
    background_color: tuple[int, int, int] = (84, 1, 68)
    component_radius: int = 10

    # Dynamic Attributes
    component_x_min: int = -1
    component_x_max: int = -1
    component_y_min: int = -1
    component_y_max: int = -1

    @property
    def available_size(self) -> tuple[int, int]:
        return (
            self.canvas_size[0] - 2 * self.margin,
            self.canvas_size[1] - 2 * self.margin,
        )

    @property
    def scaling_ratio(self) -> float:
        available_h, available_w = self.available_size
        return min(
            available_h / (self.component_y_max - self.component_y_min),
            available_w / (self.component_x_max - self.component_x_min),
        )

    @property
    def offset_to_center(self) -> tuple[int, int]:
        available_h, available_w = self.available_size
        scaling_ratio = self.scaling_ratio
        scaled_height = (self.component_y_max - self.component_y_min) * scaling_ratio
        scaled_width = (self.component_x_max - self.component_x_min) * scaling_ratio
        offset_y = (available_h - scaled_height) / 2
        offset_x = (available_w - scaled_width) / 2
        return int(offset_y), int(offset_x)


