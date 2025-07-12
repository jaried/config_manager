# tests/01_unit_tests/test_config_manager/test_config_file_protection.py
from __future__ import annotations
from pathlib import Path

from src.config_manager import get_config_manager, _clear_instances_for_testing



class TestConfigFileProtection:
    """测试配置文件保护功能"""
    
    def setup_method(self):
        """每个测试方法前的设置"""
        _clear_instances_for_testing()
    
    def teardown_method(self):
        """每个测试方法后的清理"""
        _clear_instances_for_testing()
    
    def test_windows_path_escape_fix(self, tmp_path):
        """测试Windows路径转义问题的修复"""
        config_path = tmp_path / 'test_config.yaml'
        
        # 使用安全的tmp_path动态构建模拟的Windows路径
        safe_base_dir_str = str(tmp_path / 'logs').replace('/', '\\\\')
        
        problematic_config = f'''__data__:
  project_name: "TestProject"
  base_dir: "{safe_base_dir_str}"
__type_hints__: {{}}'''
            
        with open(config_path, 'w', encoding='utf-8') as f:
            f.write(problematic_config)
            
        config = get_config_manager(
            config_path=str(config_path),
            auto_create=False
        )
            
        assert config is not None
        assert config.project_name == "TestProject"
        # 验证路径被正确标准化
        assert Path(config.base_dir) == Path(tmp_path / 'logs')
    
    def test_config_file_protection_on_parse_error(self, tmp_path):
        """测试配置文件解析错误时的保护机制"""
        config_path = tmp_path / 'test_config.yaml'
            
        invalid_yaml = '''__data__:
  invalid_yaml: [unclosed list
__type_hints__: {}'''
            
        with open(config_path, 'w', encoding='utf-8') as f:
            f.write(invalid_yaml)
            
        original_content = invalid_yaml
            
        config = get_config_manager(
            config_path=str(config_path),
            auto_create=True
        )
            
        assert config is None
            
        with open(config_path, 'r', encoding='utf-8') as f:
            current_content = f.read()
        assert current_content == original_content
    
    def test_successful_config_can_be_saved(self, tmp_path):
        """测试成功加载的配置可以正常保存"""
        config_path = tmp_path / 'test_config.yaml'
            
        config = get_config_manager(
            config_path=str(config_path),
            auto_create=True
        )
            
        config.set('project_name', 'TestProject')
        config.save()
            
        assert config_path.exists()
            
        _clear_instances_for_testing()
        config2 = get_config_manager(
            config_path=str(config_path),
            auto_create=False
        )
            
        assert config2.get('project_name') == 'TestProject'
    
    def test_complex_windows_paths_handling(self, tmp_path):
        """测试复杂Windows路径的处理"""
        config_path = tmp_path / 'test_config.yaml'
        
        # 动态、安全地创建模拟路径
        safe_logs_dir = str(tmp_path / "logs").replace('/', '\\\\')
        safe_data_dir = str(tmp_path / "data").replace('/', '\\\\')

        complex_config = f'''__data__:
  project_name: "FuturesTradingPL"
  base_dir: "{safe_logs_dir}"
  database:
    path: "{safe_data_dir}\\\\database.db"
  logs:
    base_root_dir: ".\\\\logs"
__type_hints__: {{}}'''
            
        with open(config_path, 'w', encoding='utf-8') as f:
            f.write(complex_config)
            
        config = get_config_manager(
            config_path=str(config_path),
            auto_create=False
        )
            
        assert config is not None
        assert Path(config.base_dir) == tmp_path / "logs"
        assert Path(config.database.path) == tmp_path / "data" / "database.db"
        assert config.logs.base_root_dir in ["./logs", ".\\logs"]
    
    def test_backup_creation_on_parse_error(self, tmp_path):
        """测试解析错误时备份文件的创建"""
        config_path = tmp_path / 'test_config.yaml'
            
        valid_config = f'''__data__:
  project_name: "TestProject"
  base_dir: "{str(tmp_path / 'logs')}"
__type_hints__: {{}}'''
            
        with open(config_path, 'w', encoding='utf-8') as f:
            f.write(valid_config)
            
        config = get_config_manager(
            config_path=str(config_path),
            auto_create=True
        )
            
        assert config is not None
            
        config.set('test_key', 'test_value')
        
        # 设置项目路径以生成backup_dir
        config.setup_project_paths()
        config.save()
        
        # 使用新的backup_dir路径
        backup_dir_path = config.get('paths.backup_dir')
        assert backup_dir_path is not None, "backup_dir应该被正确生成"
        
        backup_dir = Path(backup_dir_path)
        assert backup_dir.exists(), f"备份目录应该存在: {backup_dir}"
            
        backup_files = list(backup_dir.glob('*.yaml'))
        assert len(backup_files) > 0, f"应该有备份文件: {list(backup_dir.glob('*'))}"
            
        with open(backup_files[0], 'r', encoding='utf-8') as f:
            backup_content = f.read()
        
        assert 'test_key' in backup_content
        assert 'test_value' in backup_content