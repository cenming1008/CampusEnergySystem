"""
预测API端点
提供负荷预测和风光预测接口
支持简单算法和LSTM深度学习模型
"""
from typing import List, Optional, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, Query, Body
from sqlmodel import Session
from datetime import datetime

from app.core.database import get_session
from app.core.response import success_response
from app.models.tables import Prediction

# 导入统一的预测适配器
try:
    from app.services.forecast_adapter import ForecastAdapter
    FORECAST_AVAILABLE = True
    # 检查LSTM是否可用
    from lstm_forecast import LSTM_AVAILABLE
except ImportError:
    FORECAST_AVAILABLE = False
    LSTM_AVAILABLE = False

router = APIRouter()


@router.post("/load")
def forecast_load(
    device_id: Optional[int] = Query(None, description="设备ID，不提供则预测系统总负荷"),
    hours: int = Query(24, ge=1, le=168, description="预测时间范围（小时），1-168"),
    algorithm: Optional[str] = Query(None, description="预测算法：lstm, moving_average, linear_regression"),
    session: Session = Depends(get_session)
):
    """
    负荷预测
    
    根据历史数据预测未来负荷
    支持LSTM深度学习模型和简单统计方法
    """
    try:
        adapter = ForecastAdapter()
        predictions = adapter.forecast_load(
            session=session,
            device_id=device_id,
            hours=hours,
            algorithm=algorithm
        )
        
        return success_response(
            data={
                "device_id": device_id,
                "predictions": predictions,
                "forecast_hours": hours,
                "algorithm": algorithm or "default",
                "count": len(predictions)
            },
            message=f"成功生成 {len(predictions)} 个预测点"
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"负荷预测失败: {str(e)}")


@router.post("/renewable/{prediction_type}")
def forecast_renewable(
    prediction_type: str,
    device_id: Optional[int] = Query(None, description="设备ID，不提供则预测系统总量"),
    hours: int = Query(24, ge=1, le=168, description="预测时间范围（小时）"),
    algorithm: Optional[str] = Query(None, description="预测算法"),
    session: Session = Depends(get_session)
):
    """
    风光预测
    
    Args:
        prediction_type: 预测类型（solar-光伏, wind-风电）
    """
    if prediction_type not in ["solar", "wind"]:
        raise HTTPException(
            status_code=400,
            detail="prediction_type 必须是 'solar' 或 'wind'"
        )
    
    try:
        adapter = ForecastAdapter()
        # 注意：forecast_renewable 需要单独实现或使用 forecast_load
        # 这里暂时使用 forecast_load，后续可以扩展
        predictions = adapter.forecast_load(
            session=session,
            device_id=device_id,
            hours=hours,
            algorithm=algorithm
        )
        
        type_name = "光伏" if prediction_type == "solar" else "风电"
        return success_response(
            data={
                "prediction_type": prediction_type,
                "device_id": device_id,
                "predictions": predictions,
                "forecast_hours": hours,
                "count": len(predictions)
            },
            message=f"成功生成 {type_name} {len(predictions)} 个预测点"
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"{prediction_type}预测失败: {str(e)}")


@router.get("/latest/{prediction_type}")
def get_latest_predictions(
    prediction_type: str,
    device_id: Optional[int] = Query(None, description="设备ID"),
    limit: int = Query(24, ge=1, le=168, description="返回数量"),
    session: Session = Depends(get_session)
):
    """
    获取最新的预测结果
    
    Args:
        prediction_type: 预测类型（load, solar, wind）
    """
    if prediction_type not in ["load", "solar", "wind"]:
        raise HTTPException(
            status_code=400,
            detail="prediction_type 必须是 'load', 'solar' 或 'wind'"
        )
    
    # 注意：这个方法需要在 ForecastAdapter 中实现，或者直接查询数据库
    # 暂时保留原有逻辑，直接查询数据库
    from sqlmodel import select
    statement = (
        select(Prediction)
        .where(Prediction.prediction_type == prediction_type)
    )
    if device_id:
        statement = statement.where(Prediction.device_id == device_id)
    statement = statement.order_by(Prediction.created_at.desc()).limit(limit)
    
    predictions = list(session.exec(statement).all())
    
    # 转换为字典列表
    result = [{
        "forecast_time": p.forecast_time,
        "predicted_value": p.predicted_value,
        "confidence": p.confidence,
        "algorithm": p.algorithm
    } for p in predictions]
    
    return success_response(
        data={"predictions": result, "count": len(result)}
    )


@router.get("/accuracy/{prediction_type}")
def get_prediction_accuracy(
    prediction_type: str,
    device_id: Optional[int] = Query(None, description="设备ID"),
    days: int = Query(7, ge=1, le=30, description="评估天数"),
    session: Session = Depends(get_session)
):
    """
    获取预测准确性评估
    
    对比预测值和实际值，计算误差指标
    """
    if prediction_type not in ["load", "solar", "wind"]:
        raise HTTPException(
            status_code=400,
            detail="prediction_type 必须是 'load', 'solar' 或 'wind'"
        )
    
    accuracy = ForecastService.evaluate_prediction_accuracy(
        session=session,
        prediction_type=prediction_type,
        device_id=device_id,
        days=days
    )
    
    return success_response(
        data=accuracy,
        message="预测准确性评估"
    )


@router.get("/history/{prediction_type}")
def get_prediction_history(
    prediction_type: str,
    device_id: Optional[int] = Query(None, description="设备ID"),
    start_time: Optional[datetime] = Query(None, description="开始时间"),
    end_time: Optional[datetime] = Query(None, description="结束时间"),
    limit: int = Query(100, ge=1, le=1000, description="返回数量"),
    session: Session = Depends(get_session)
):
    """
    获取历史预测记录
    """
    from sqlmodel import select
    
    statement = select(Prediction).where(
        Prediction.prediction_type == prediction_type
    )
    
    if device_id is not None:
        statement = statement.where(Prediction.device_id == device_id)
    
    if start_time:
        statement = statement.where(Prediction.created_at >= start_time)
    
    if end_time:
        statement = statement.where(Prediction.created_at <= end_time)
    
    statement = statement.order_by(Prediction.created_at.desc()).limit(limit)
    
    predictions = list(session.exec(statement).all())
    
    return success_response(
        data={
            "predictions": [
                {
                    "id": p.id,
                    "device_id": p.device_id,
                    "forecast_time": p.forecast_time,
                    "predicted_value": p.predicted_value,
                    "actual_value": p.actual_value,
                    "confidence": p.confidence,
                    "algorithm": p.algorithm,
                    "created_at": p.created_at
                }
                for p in predictions
            ],
            "count": len(predictions)
        }
    )


@router.post("/lstm/train")
def train_lstm_model(
    prediction_type: str = Body(..., description="预测类型：load/solar/wind"),
    device_id: Optional[int] = Body(None, description="设备ID"),
    days: int = Body(60, ge=30, le=365, description="训练数据天数"),
    params: Optional[Dict[str, Any]] = Body(None, description="LSTM超参数"),
    retrain: bool = Body(False, description="是否强制重新训练"),
    use_multivariate: bool = Body(False, description="是否使用多变量预测（电压、电流、功率）"),
    version: Optional[str] = Body(None, description="版本号（如v1.0.0），不提供则自动生成"),
    session: Session = Depends(get_session)
):
    """
    训练LSTM模型
    
    需要安装TensorFlow: pip install tensorflow scikit-learn
    """
    if not LSTM_AVAILABLE:
        raise HTTPException(
            status_code=503,
            detail="LSTM功能不可用，请安装TensorFlow: pip install tensorflow scikit-learn"
        )
    
    if prediction_type not in ["load", "solar", "wind"]:
        raise HTTPException(
            status_code=400,
            detail="prediction_type 必须是 'load', 'solar' 或 'wind'"
        )
    
    try:
        adapter = ForecastAdapter()
        
        # 如果没有提供版本号，自动生成
        if not version:
            from datetime import datetime
            version = f"v{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        result = adapter.train_lstm_model(
            session=session,
            prediction_type=prediction_type,
            device_id=device_id,
            days=days,
            params=params,
            retrain=retrain,
            use_multivariate=use_multivariate,
            version=version
        )
        
        return success_response(
            data=result,
            message="LSTM模型训练完成"
        )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"LSTM模型训练失败: {str(e)}"
        )


@router.get("/lstm/evaluate/{prediction_type}")
def evaluate_lstm_model(
    prediction_type: str,
    device_id: Optional[int] = Query(None, description="设备ID"),
    test_days: int = Query(7, ge=1, le=30, description="测试数据天数"),
    session: Session = Depends(get_session)
):
    """
    评估LSTM模型性能
    """
    if not LSTM_AVAILABLE:
        raise HTTPException(
            status_code=503,
            detail="LSTM功能不可用"
        )
    
    if prediction_type not in ["load", "solar", "wind"]:
        raise HTTPException(
            status_code=400,
            detail="prediction_type 必须是 'load', 'solar' 或 'wind'"
        )
    
    try:
        adapter = ForecastAdapter()
        evaluation = adapter.evaluate_lstm_model(
            session=session,
            prediction_type=prediction_type,
            device_id=device_id,
            test_days=test_days
        )
        
        return success_response(
            data=evaluation,
            message="LSTM模型评估完成"
        )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"LSTM模型评估失败: {str(e)}"
        )


@router.get("/lstm/versions/{prediction_type}")
def list_model_versions(
    prediction_type: str,
    device_id: Optional[int] = Query(None, description="设备ID"),
    session: Session = Depends(get_session)
):
    """
    列出所有模型版本
    """
    if not LSTM_AVAILABLE:
        raise HTTPException(
            status_code=503,
            detail="LSTM功能不可用"
        )
    
    try:
        adapter = ForecastAdapter()
        versions = adapter.list_versions(prediction_type, device_id)
        
        return success_response(
            data={
                "versions": versions,
                "count": len(versions)
            }
        )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"获取版本列表失败: {str(e)}"
        )


@router.post("/lstm/versions/{prediction_type}/activate")
def activate_model_version(
    prediction_type: str,
    version: str = Body(..., description="版本号"),
    device_id: Optional[int] = Body(None, description="设备ID"),
    session: Session = Depends(get_session)
):
    """
    激活指定版本的模型
    """
    if not LSTM_AVAILABLE:
        raise HTTPException(
            status_code=503,
            detail="LSTM功能不可用"
        )
    
    try:
        adapter = ForecastAdapter()
        success = adapter.set_active_version(prediction_type, device_id, version)
        
        if not success:
            raise HTTPException(
                status_code=404,
                detail="版本不存在"
            )
        
        return success_response(
            data={"version": version, "is_active": True},
            message=f"已激活版本 {version}"
        )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"激活版本失败: {str(e)}"
        )


@router.get("/lstm/versions/{prediction_type}/compare")
def compare_model_versions(
    prediction_type: str,
    version1: str = Query(..., description="版本1"),
    version2: str = Query(..., description="版本2"),
    device_id: Optional[int] = Query(None, description="设备ID"),
    session: Session = Depends(get_session)
):
    """
    对比两个模型版本的性能
    """
    if not LSTM_AVAILABLE:
        raise HTTPException(
            status_code=503,
            detail="LSTM功能不可用"
        )
    
    try:
        adapter = ForecastAdapter()
        comparison = adapter.compare_versions(
            prediction_type, device_id, version1, version2
        )
        
        return success_response(
            data=comparison,
            message="版本对比完成"
        )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"版本对比失败: {str(e)}"
        )


@router.get("/scheduler/jobs")
def get_scheduler_jobs(session: Session = Depends(get_session)):
    """
    获取所有定时任务列表
    """
    try:
        from app.services.scheduler_service import get_jobs
        jobs = get_jobs()
        
        return success_response(
            data={"jobs": jobs, "count": len(jobs)},
            message="获取定时任务列表成功"
        )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"获取定时任务失败: {str(e)}"
        )


@router.post("/lstm/hyperparameter-search")
def hyperparameter_search(
    prediction_type: str = Body(..., description="预测类型"),
    device_id: Optional[int] = Body(None, description="设备ID"),
    days: int = Body(60, description="训练数据天数"),
    session: Session = Depends(get_session)
):
    """
    超参数搜索（网格搜索）
    
    尝试不同的超参数组合，找到最佳配置
    """
    if not LSTM_AVAILABLE:
        raise HTTPException(
            status_code=503,
            detail="LSTM功能不可用"
        )
    
    if prediction_type not in ["load", "solar", "wind"]:
        raise HTTPException(
            status_code=400,
            detail="prediction_type 必须是 'load', 'solar' 或 'wind'"
        )
    
    try:
        adapter = ForecastAdapter()
        
        best_params = None
        best_score = float('inf')
        results = []
        
        # 简化版网格搜索（限制组合数量）
        from itertools import product
        
        # 限制搜索空间，避免组合过多
        sequence_lengths = [24, 48]
        lstm_units_list = [[64, 32], [128, 64]]
        dropout_rates = [0.2, 0.3]
        epochs_list = [30, 50]
        
        total_combinations = len(sequence_lengths) * len(lstm_units_list) * len(dropout_rates) * len(epochs_list)
        logger.info(f"开始超参数搜索，共 {total_combinations} 种组合")
        
        for seq_len, units, dropout, epochs in product(
            sequence_lengths, lstm_units_list, dropout_rates, epochs_list
        ):
            params = {
                "sequence_length": seq_len,
                "lstm_units": units,
                "dropout_rate": dropout,
                "epochs": epochs,
                "batch_size": 32,
                "validation_split": 0.2,
                "patience": 10
            }
            
            try:
                # 训练模型
                result = adapter.train_lstm_model(
                    session=session,
                    prediction_type=prediction_type,
                    device_id=device_id,
                    days=days,
                    params=params,
                    retrain=True,
                    version=f"search_{seq_len}_{units[0]}_{dropout}_{epochs}"
                )
                
                if result.get("status") == "success":
                    val_loss = result.get("val_loss", float('inf'))
                    
                    results.append({
                        "params": params,
                        "val_loss": val_loss,
                        "train_loss": result.get("train_loss"),
                        "epochs_trained": result.get("epochs_trained")
                    })
                    
                    if val_loss < best_score:
                        best_score = val_loss
                        best_params = params
                
            except Exception as e:
                logger.warning(f"超参数组合训练失败: {params}, 错误: {e}")
                continue
        
        # 按验证损失排序
        results.sort(key=lambda x: x.get("val_loss", float('inf')))
        
        return success_response(
            data={
                "best_params": best_params,
                "best_score": best_score,
                "all_results": results[:10],  # 返回前10个最佳结果
                "total_tested": len(results)
            },
            message="超参数搜索完成"
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"超参数搜索失败: {str(e)}"
        )
