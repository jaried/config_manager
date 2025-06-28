class ConfigNode:
    """配置节点类，支持点操作访问"""

    def __init__(self, *args, **kwargs):
        """初始化配置节点"""
        super().__setattr__('_data', {})
        super().__setattr__('_root', kwargs.get('_root', None))
        if args or kwargs:
            self.update(*args, **kwargs)

    def __dir__(self) -> Iterable[str]:
        return self._data.keys()

    def __getattr__(self, name: str) -> Any:
        # ... (implementation remains the same)

    def __setattr__(self, name: str, value: Any):
        """通过属性设置值"""
        if name.startswith('_'):
            super().__setattr__(name, value)
            return

        self._data[name] = self.build(value)
        
        root = getattr(self, '_root', None) or (self if isinstance(self, ConfigManagerCore) else None)
        if root and hasattr(root, '_schedule_autosave'):
            root._schedule_autosave()

    def __delattr__(self, name: str):
        del self._data[name]

    def __getitem__(self, key: str) -> Any:
        """获取一个键的值"""
        # 当一个值被设置时，它可能会影响路径配置。
        # 我们将字典转换为ConfigNode以便进行属性访问。
        return self._data[key]

    def __setitem__(self, key: str, value: Any) -> None:
        """设置一个键值对"""
        self._data[key] = self.build(value)

    def __delitem__(self, key: str) -> None:
        del self._data[key]

    def update(self, *args, **kwargs):
        """更新节点内容"""
        if args:
            updates = dict(*args, **kwargs)
        else:
            updates = kwargs

        for key, value in updates.items():
            self[key] = value

    def build(self, obj: Any) -> Any:
        """构建对象，递归转换嵌套结构"""
        root = getattr(self, '_root', None) or (self if isinstance(self, ConfigManagerCore) else None)
        
        if isinstance(obj, ConfigNode):
            return obj
        if isinstance(obj, Mapping):
            return self.__class__(obj, _root=root)
        if not isinstance(obj, str) and isinstance(obj, Iterable):
            return obj.__class__(self.build(item) for item in obj)
        return obj

    def resolve_templates(self, context=None):
        # ... (existing code ...)
        # ... (existing code ...)
        # ... (existing code ...)

class ConfigManagerCore(ConfigNode):
    """配置管理器核心类"""

    def __init__(self):
        # 正确初始化ConfigNode，确保_data属性存在
        super().__init__(_root=self) # 设置自己为root

        # 初始化组件（延迟初始化）
        # ... (existing code ...)

    def _load(self):
        # ... (inside the loop `for key, value in raw_data.items():`)
        self._data[key] = self.build(value)

    def set(self, key: str, value: Any, autosave: bool = True, type_hint: Type = None):
        # ... (logic for debug_mode, first_start_time, base_dir conversion)

        keys = key.split('.')
        current = self
        for k in keys[:-1]:
            if k not in current or not isinstance(current[k], ConfigNode):
                current[k] = ConfigNode(_root=self) # 显式传递root
            current = current[k]
        
        current[keys[-1]] = value
        
        if type_hint:
            self.set_type_hint(key, type_hint)
        
        if autosave:
            self._schedule_autosave()

    def _setup_first_start_time(self, first_start_time: datetime = None):
        # ... (existing code ...)

        # ... (existing code ...) 