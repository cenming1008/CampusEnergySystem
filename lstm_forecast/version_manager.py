"""
模型版本管理服务
管理LSTM模型的多个版本，支持版本对比和回滚
"""
import json
from pathlib import Path
from typing import List, Dict, Any, Optional
from datetime import datetime


class ModelVersionService:
    """模型版本管理服务"""
    
    VERSION_DIR = Path("models/versions")
    VERSION_METADATA_FILE = Path("models/versions_metadata.json")
    
    def __init__(self):
        self.VERSION_DIR.mkdir(parents=True, exist_ok=True)
        self._load_metadata()
    
    def _load_metadata(self) -> Dict[str, Any]:
        """加载版本元数据"""
        if self.VERSION_METADATA_FILE.exists():
            try:
                with open(self.VERSION_METADATA_FILE, 'r') as f:
                    return json.load(f)
            except Exception:
                return {}
        return {}
    
    def _save_metadata(self, metadata: Dict[str, Any], logger: Optional[Any] = None):
        """保存版本元数据"""
        try:
            with open(self.VERSION_METADATA_FILE, 'w') as f:
                json.dump(metadata, f, indent=2)
        except Exception as e:
            if logger:
                logger.error(f"保存版本元数据失败: {e}")
    
    def list_versions(
        self,
        prediction_type: str,
        device_id: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """列出所有模型版本"""
        metadata = self._load_metadata()
        key = f"{prediction_type}_{device_id or 'system'}"
        
        versions = metadata.get(key, {}).get("versions", [])
        versions.sort(key=lambda x: x.get("created_at", ""), reverse=True)
        
        return versions
    
    def get_version_info(
        self,
        prediction_type: str,
        device_id: Optional[int],
        version: str
    ) -> Optional[Dict[str, Any]]:
        """获取指定版本的详细信息"""
        versions = self.list_versions(prediction_type, device_id)
        
        for v in versions:
            if v.get("version") == version:
                return v
        
        return None
    
    def create_version(
        self,
        prediction_type: str,
        device_id: Optional[int],
        version: str,
        model_path: str,
        metadata_path: str,
        metrics: Dict[str, float],
        logger: Optional[Any] = None
    ) -> Dict[str, Any]:
        """创建新版本记录"""
        metadata = self._load_metadata()
        key = f"{prediction_type}_{device_id or 'system'}"
        
        if key not in metadata:
            metadata[key] = {"versions": []}
        
        version_info = {
            "version": version,
            "prediction_type": prediction_type,
            "device_id": device_id,
            "model_path": model_path,
            "metadata_path": metadata_path,
            "metrics": metrics,
            "created_at": datetime.now().isoformat(),
            "is_active": False
        }
        
        metadata[key]["versions"].append(version_info)
        
        if not metadata[key].get("current_version"):
            metadata[key]["current_version"] = version
            version_info["is_active"] = True
        
        self._save_metadata(metadata, logger)
        
        if logger:
            logger.info(f"创建模型版本: {key} v{version}")
        return version_info
    
    def set_active_version(
        self,
        prediction_type: str,
        device_id: Optional[int],
        version: str,
        logger: Optional[Any] = None
    ) -> bool:
        """设置活动版本"""
        metadata = self._load_metadata()
        key = f"{prediction_type}_{device_id or 'system'}"
        
        if key not in metadata:
            return False
        
        version_exists = any(
            v.get("version") == version
            for v in metadata[key]["versions"]
        )
        
        if not version_exists:
            return False
        
        for v in metadata[key]["versions"]:
            v["is_active"] = (v.get("version") == version)
        
        metadata[key]["current_version"] = version
        self._save_metadata(metadata, logger)
        
        if logger:
            logger.info(f"设置活动版本: {key} v{version}")
        return True
    
    def get_active_version(
        self,
        prediction_type: str,
        device_id: Optional[int]
    ) -> Optional[str]:
        """获取当前活动版本"""
        metadata = self._load_metadata()
        key = f"{prediction_type}_{device_id or 'system'}"
        
        return metadata.get(key, {}).get("current_version")
    
    def compare_versions(
        self,
        prediction_type: str,
        device_id: Optional[int],
        version1: str,
        version2: str
    ) -> Dict[str, Any]:
        """对比两个版本的性能"""
        v1_info = self.get_version_info(prediction_type, device_id, version1)
        v2_info = self.get_version_info(prediction_type, device_id, version2)
        
        if not v1_info or not v2_info:
            raise ValueError("版本不存在")
        
        metrics1 = v1_info.get("metrics", {})
        metrics2 = v2_info.get("metrics", {})
        
        comparison = {
            "version1": {
                "version": version1,
                "metrics": metrics1,
                "created_at": v1_info.get("created_at")
            },
            "version2": {
                "version": version2,
                "metrics": metrics2,
                "created_at": v2_info.get("created_at")
            },
            "improvements": {}
        }
        
        # 计算改进（越小越好）
        for metric in ["mae", "mape", "rmse"]:
            if metric in metrics1 and metric in metrics2:
                improvement = ((metrics1[metric] - metrics2[metric]) / metrics1[metric]) * 100
                comparison["improvements"][metric] = round(improvement, 2)
        
        return comparison
    
    def delete_version(
        self,
        prediction_type: str,
        device_id: Optional[int],
        version: str,
        logger: Optional[Any] = None
    ) -> bool:
        """删除模型版本（不删除文件，只删除记录）"""
        metadata = self._load_metadata()
        key = f"{prediction_type}_{device_id or 'system'}"
        
        if key not in metadata:
            return False
        
        if metadata[key].get("current_version") == version:
            raise ValueError("不能删除活动版本，请先切换到其他版本")
        
        metadata[key]["versions"] = [
            v for v in metadata[key]["versions"]
            if v.get("version") != version
        ]
        
        self._save_metadata(metadata, logger)
        
        if logger:
            logger.info(f"删除模型版本: {key} v{version}")
        return True
