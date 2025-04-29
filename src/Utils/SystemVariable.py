from typing import Any, Callable


class ObservableProperty:
    # Initialize the ObservableProperty with an object name
    def __init__(self, obj_name: str):
        self.obj_name = obj_name
        self.__value = ""
        self.default_value = ""
        self.callbacks = []
        self.signals_blocked = False

    # Get the current value
    def get_value(self):
        return self.__value

    # Set a new value and execute callbacks if the value changes
    def set_value(self, new_value: Any):
        if self.__value != new_value:
            self.__value = new_value
            self._execute_callbacks(new_value)

    # Set the default value
    def set_default_value(self, default_value: Any):
        self.default_value = default_value

    # Reset the value to the default value
    def reset_to_default(self):
        self.set_value(self.default_value)

    # Return the object name (compatible with PyQt)
    def objectName(self):
        # To be compatible with pyqt object name
        return self.obj_name

    # Execute all registered callbacks with the new value
    def _execute_callbacks(self, new_value: Any):
        if not self.signals_blocked:  # 只有當信號未被阻止時執行回調
            for callback in self.callbacks:
                callback(new_value)

    # Connect a new callback to be executed when the value changes
    def connect(self, callback: callable):
        self.callbacks.append(callback)

    def blockSignals(self, block: bool):
        """
        控制信號是否被阻止。
        :param block: True 表示阻止信號，False 表示允許信號。
        """
        self.signals_blocked = block

class SystemVariable:
    _instance = None

    def __new__(cls, *args, **kwargs):
        if cls._instance is None:
            cls._instance = super(SystemVariable, cls).__new__(cls)
        return cls._instance

    def __init__(self):
        if getattr(self, '_initialized', False):
            return
        self._callbacks: dict[str, Callable] = {}
        self.CANVAS_COLOR = ObservableProperty("CANVAS_COLOR")
        self.CANVAS_COLOR_DIALOG_TEMP = ObservableProperty("CANVAS_COLOR_DIALOG_TEMP")
        self._initialized = True

    def __getitem__(self, key) -> Any:
        if key in self.__dict__:
            return self.__dict__[key].get_value()
        else:
            return None

    def __repr__(self):
        return f"<SystemVariable: {list(self.__dict__.keys())}>"
