# Path: config/config_handler.py
import json
import os
import logging
from typing import Dict, Any, Optional
from pathlib import Path


class ConfigHandler:
    """Enhanced configuration handler with GPU settings support"""
    
    def __init__(self, config_file: str, gpu_config_file: Optional[str] = None):
        self.config_file = config_file
        self.gpu_config_file = gpu_config_file or self._get_default_gpu_config_path()
        self.config = self.load_configuration()
        self.gpu_config = self.load_gpu_configuration()
        
        # Initialize GPU if enabled
        self.gpu_status = self._initialize_gpu()

    def _get_default_gpu_config_path(self) -> str:
        """Get default GPU config path relative to main config"""
        config_dir = os.path.dirname(self.config_file)
        return os.path.join(config_dir, 'gpu_config.json')

    def load_configuration(self) -> Dict[str, Any]:
        """Load main configuration with error handling"""
        try:
            with open(self.config_file, 'r') as file:
                configuration = json.load(file)
            logging.info(f"Loaded configuration from {self.config_file}")
            return configuration
        except FileNotFoundError:
            logging.error(f"Configuration file not found: {self.config_file}")
            return {}
        except json.JSONDecodeError as e:
            logging.error(f"Invalid JSON in configuration file: {e}")
            return {}
        except Exception as e:
            logging.error(f"Error loading configuration: {e}")
            return {}

    def load_gpu_configuration(self) -> Dict[str, Any]:
        """Load GPU configuration with fallback defaults"""
        try:
            if os.path.exists(self.gpu_config_file):
                with open(self.gpu_config_file, 'r') as file:
                    gpu_config = json.load(file)
                logging.info(f"Loaded GPU configuration from {self.gpu_config_file}")
                return gpu_config
            else:
                logging.warning(f"GPU config file not found: {self.gpu_config_file}")
                return self._get_default_gpu_config()
        except json.JSONDecodeError as e:
            logging.error(f"Invalid JSON in GPU configuration file: {e}")
            return self._get_default_gpu_config()
        except Exception as e:
            logging.error(f"Error loading GPU configuration: {e}")
            return self._get_default_gpu_config()

    def _get_default_gpu_config(self) -> Dict[str, Any]:
        """Get default GPU configuration"""
        return {
            "gpu_acceleration": {
                "enable_gpu": True,
                "backend": "auto",
                "memory_mode": "balanced",
                "fallback_to_cpu": True,
                "run_initial_benchmark": True,
                "max_gpu_memory_usage": 0.8
            },
            "file_hashing": {
                "enable_gpu_hashing": True,
                "chunk_size_mb": 64,
                "max_concurrent_files": 4,
                "gpu_memory_limit_mb": 512,
                "min_file_size_for_gpu": 1048576
            },
            "image_processing": {
                "enable_gpu_processing": True,
                "max_concurrent_images": 4,
                "gpu_memory_limit_mb": 1024,
                "min_image_size_for_gpu": 524288
            },
            "batch_processing": {
                "enable_batch_gpu": True,
                "max_batch_size": 100,
                "batch_memory_limit_mb": 2048
            }
        }

    def _initialize_gpu(self) -> Dict[str, Any]:
        """Initialize GPU acceleration if enabled"""
        gpu_status = {
            'enabled': False,
            'available': False,
            'backend': 'none',
            'device_name': 'none',
            'error': None
        }
        
        # Check if GPU is enabled in config
        if not self.gpu_config.get('gpu_acceleration', {}).get('enable_gpu', False):
            gpu_status['error'] = 'GPU acceleration disabled in configuration'
            return gpu_status
        
        try:
            # Try to import and initialize GPU modules
            from ..file_handler.gpu_acceleration import initialize_gpu_acceleration, get_gpu_accelerator
            
            # Initialize GPU
            if initialize_gpu_acceleration(self.gpu_config.get('gpu_acceleration', {})):
                gpu_accelerator = get_gpu_accelerator()
                device = gpu_accelerator.get_device_info()
                
                gpu_status.update({
                    'enabled': True,
                    'available': True,
                    'backend': device.backend.value,
                    'device_name': device.name,
                    'memory_total': device.memory_total,
                    'memory_available': device.memory_available
                })
                
                logging.info(f"GPU acceleration initialized: {device.name} ({device.backend.value.upper()})")
            else:
                gpu_status['error'] = 'GPU initialization failed'
                logging.warning("GPU initialization failed, using CPU fallback")
                
        except ImportError as e:
            gpu_status['error'] = f'GPU libraries not available: {e}'
            logging.info("GPU libraries not installed, using CPU processing")
        except Exception as e:
            gpu_status['error'] = f'GPU initialization error: {e}'
            logging.warning(f"GPU initialization error: {e}")
        
        return gpu_status

    def get_config(self, key: str, default: Any = None) -> Any:
        """Get configuration value with default fallback"""
        return self.config.get(key, default)

    def get_gpu_config(self, section: str = None, key: str = None, default: Any = None) -> Any:
        """
        Get GPU configuration value
        
        Args:
            section: Config section (e.g., 'gpu_acceleration', 'file_hashing')
            key: Specific key within section
            default: Default value if not found
        
        Returns:
            Configuration value or default
        """
        if section is None:
            return self.gpu_config
        
        section_config = self.gpu_config.get(section, {})
        
        if key is None:
            return section_config
        
        return section_config.get(key, default)

    def is_gpu_enabled(self) -> bool:
        """Check if GPU acceleration is enabled and available"""
        return self.gpu_status.get('available', False)

    def get_gpu_status(self) -> Dict[str, Any]:
        """Get current GPU status"""
        return self.gpu_status.copy()

    def get_performance_settings(self) -> Dict[str, Any]:
        """Get performance-related settings for GPU acceleration"""
        gpu_accel = self.gpu_config.get('gpu_acceleration', {})
        file_hash = self.gpu_config.get('file_hashing', {})
        img_proc = self.gpu_config.get('image_processing', {})
        batch_proc = self.gpu_config.get('batch_processing', {})
        
        return {
            # GPU general settings
            'gpu_enabled': self.is_gpu_enabled(),
            'gpu_backend': self.gpu_status.get('backend', 'none'),
            'gpu_memory_mode': gpu_accel.get('memory_mode', 'balanced'),
            'max_gpu_memory_usage': gpu_accel.get('max_gpu_memory_usage', 0.8),
            
            # File hashing settings
            'hash_chunk_size_mb': file_hash.get('chunk_size_mb', 64),
            'max_concurrent_files': file_hash.get('max_concurrent_files', 4),
            'hash_gpu_memory_limit_mb': file_hash.get('gpu_memory_limit_mb', 512),
            'min_file_size_for_gpu': file_hash.get('min_file_size_for_gpu', 1048576),
            
            # Image processing settings
            'max_concurrent_images': img_proc.get('max_concurrent_images', 4),
            'image_gpu_memory_limit_mb': img_proc.get('gpu_memory_limit_mb', 1024),
            'min_image_size_for_gpu': img_proc.get('min_image_size_for_gpu', 524288),
            
            # Batch processing settings
            'batch_gpu_enabled': batch_proc.get('enable_batch_gpu', True),
            'max_batch_size': batch_proc.get('max_batch_size', 100),
            'batch_memory_limit_mb': batch_proc.get('batch_memory_limit_mb', 2048),
        }

    def save_gpu_config(self, updated_config: Dict[str, Any] = None):
        """Save GPU configuration to file"""
        try:
            config_to_save = updated_config or self.gpu_config
            
            with open(self.gpu_config_file, 'w') as file:
                json.dump(config_to_save, file, indent=2)
            
            if updated_config:
                self.gpu_config = updated_config
            
            logging.info(f"GPU configuration saved to {self.gpu_config_file}")
            
        except Exception as e:
            logging.error(f"Error saving GPU configuration: {e}")
            raise

    def validate_configuration(self) -> Dict[str, Any]:
        """Validate both main and GPU configurations"""
        validation_results = {
            'main_config_valid': True,
            'gpu_config_valid': True,
            'errors': [],
            'warnings': []
        }
        
        # Validate main configuration
        required_main_keys = ["file_categories", "subfolders", "default_duplicate_action"]
        for key in required_main_keys:
            if key not in self.config:
                validation_results['main_config_valid'] = False
                validation_results['errors'].append(f"Missing required main config key: {key}")
        
        # Validate GPU configuration structure
        required_gpu_sections = ["gpu_acceleration", "file_hashing", "image_processing"]
        for section in required_gpu_sections:
            if section not in self.gpu_config:
                validation_results['gpu_config_valid'] = False
                validation_results['errors'].append(f"Missing GPU config section: {section}")
        
        # Validate GPU settings
        gpu_accel = self.gpu_config.get('gpu_acceleration', {})
        if gpu_accel.get('enable_gpu') and not self.gpu_status.get('available'):
            validation_results['warnings'].append(
                f"GPU acceleration enabled but not available: {self.gpu_status.get('error', 'Unknown error')}"
            )
        
        # Check memory limits
        file_hash_mem = self.gpu_config.get('file_hashing', {}).get('gpu_memory_limit_mb', 0)
        image_proc_mem = self.gpu_config.get('image_processing', {}).get('gpu_memory_limit_mb', 0)
        total_gpu_memory = file_hash_mem + image_proc_mem
        
        if self.gpu_status.get('available') and total_gpu_memory > self.gpu_status.get('memory_total', 0):
            validation_results['warnings'].append(
                f"Total GPU memory allocation ({total_gpu_memory}MB) exceeds available memory "
                f"({self.gpu_status.get('memory_total', 0)}MB)"
            )
        
        return validation_results

    def get_optimized_settings_for_system(self) -> Dict[str, Any]:
        """Get optimized settings based on available hardware"""
        optimized = {}
        
        if not self.gpu_status.get('available'):
            # CPU-only optimizations
            optimized = {
                'max_concurrent_files': min(8, os.cpu_count() or 4),
                'chunk_size_mb': 32,
                'use_gpu': False,
                'batch_size': 50
            }
        else:
            # GPU-accelerated optimizations
            gpu_memory_mb = self.gpu_status.get('memory_total', 1024)
            
            # Scale settings based on GPU memory
            if gpu_memory_mb >= 8192:  # 8GB+ GPU
                optimized = {
                    'max_concurrent_files': 8,
                    'max_concurrent_images': 6,
                    'chunk_size_mb': 128,
                    'batch_size': 200,
                    'gpu_memory_limit_mb': min(2048, gpu_memory_mb // 4)
                }
            elif gpu_memory_mb >= 4096:  # 4GB+ GPU
                optimized = {
                    'max_concurrent_files': 6,
                    'max_concurrent_images': 4,
                    'chunk_size_mb': 64,
                    'batch_size': 100,
                    'gpu_memory_limit_mb': min(1024, gpu_memory_mb // 4)
                }
            else:  # <4GB GPU
                optimized = {
                    'max_concurrent_files': 4,
                    'max_concurrent_images': 2,
                    'chunk_size_mb': 32,
                    'batch_size': 50,
                    'gpu_memory_limit_mb': min(512, gpu_memory_mb // 4)
                }
            
            optimized['use_gpu'] = True
        
        return optimized

    def update_config(self, key: str, value: Any):
        """Update main configuration value"""
        self.config[key] = value

    def update_gpu_config(self, section: str, key: str, value: Any):
        """Update GPU configuration value"""
        if section not in self.gpu_config:
            self.gpu_config[section] = {}
        self.gpu_config[section][key] = value
