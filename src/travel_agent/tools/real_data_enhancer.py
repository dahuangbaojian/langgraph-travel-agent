"""真实数据增强工具 - 智能融合真实数据和AI建议"""

import pandas as pd
import json
import logging
from pathlib import Path
from typing import Dict, Any, List, Optional
from langchain_core.messages import HumanMessage

logger = logging.getLogger(__name__)


class RealDataEnhancer:
    """真实数据增强器 - 智能融合真实数据和AI建议"""

    def __init__(self, data_dir: str = "travel_data"):
        self.data_dir = Path(data_dir)
        self.data_dir.mkdir(exist_ok=True)
        self.real_data = {}

    def load_real_data(self) -> Dict[str, Any]:
        """加载所有真实数据文件"""
        try:
            # 查找所有Excel文件
            excel_files = list(self.data_dir.glob("*.xlsx"))

            for file_path in excel_files:
                file_name = file_path.stem
                logger.info(f"加载真实数据: {file_name}")

                try:
                    df = pd.read_excel(file_path)
                    self.real_data[file_name] = {
                        "data": df.to_dict("records"),
                        "columns": list(df.columns),
                        "row_count": len(df),
                        "file_size": file_path.stat().st_size,
                    }
                    logger.info(f"成功加载 {file_name}: {len(df)} 行数据")
                except Exception as e:
                    logger.error(f"加载 {file_name} 失败: {e}")
                    self.real_data[file_name] = {"error": str(e)}

        except Exception as e:
            logger.error(f"加载真实数据失败: {e}")

        return self.real_data

    def get_destination_specific_data(self, destination: str) -> Dict[str, Any]:
        """获取特定目的地的真实数据"""
        destination_data = {}

        for file_name, data in self.real_data.items():
            if "error" in data:
                continue

            # 查找包含目的地信息的数据
            records = data["data"]
            destination_records = []

            for record in records:
                # 检查记录中是否包含目的地信息
                if self._contains_destination(record, destination):
                    destination_records.append(record)

            if destination_records:
                destination_data[file_name] = {
                    "data": destination_records,
                    "columns": data["columns"],
                    "count": len(destination_records),
                }
                logger.info(
                    f"找到 {destination} 的 {file_name} 数据: {len(destination_records)} 条"
                )

        return destination_data

    def _contains_destination(self, record: Dict[str, Any], destination: str) -> bool:
        """检查记录是否包含目的地信息"""
        destination_lower = destination.lower()

        for value in record.values():
            if isinstance(value, str) and destination_lower in value.lower():
                return True
            elif isinstance(value, (int, float)) and str(value) == destination:
                return True

        return False

    def enhance_travel_plan_with_real_data(
        self, travel_plan: Dict[str, Any], destination: str, llm
    ) -> Dict[str, Any]:
        """使用真实数据增强旅行计划"""
        try:
            # 获取目的地特定数据
            destination_data = self.get_destination_specific_data(destination)

            if not destination_data:
                logger.info(f"未找到 {destination} 的真实数据")
                return travel_plan

            # 使用LLM智能融合真实数据和AI建议
            enhancement_prompt = self._create_enhancement_prompt(
                travel_plan, destination_data
            )

            response = llm.invoke([HumanMessage(content=enhancement_prompt)])
            enhanced_plan = json.loads(response.content.strip())

            logger.info(f"成功使用真实数据增强 {destination} 的旅行计划")
            return enhanced_plan

        except Exception as e:
            logger.error(f"使用真实数据增强失败: {e}")
            return travel_plan

    def _create_enhancement_prompt(
        self, travel_plan: Dict[str, Any], destination_data: Dict[str, Any]
    ) -> str:
        """创建数据增强prompt"""

        prompt = f"""你是一个专业的旅行规划专家。请基于以下真实数据和AI生成的旅行计划，创建一个增强版的旅行计划：

## AI生成的原始计划
{json.dumps(travel_plan, ensure_ascii=False, indent=2)}

## 真实数据信息
"""

        for data_type, data in destination_data.items():
            prompt += f"\n### {data_type} 数据 ({data['count']} 条记录)\n"
            prompt += f"列名: {', '.join(data['columns'])}\n"
            prompt += f"示例数据:\n"

            # 显示前3条数据作为示例
            for i, record in enumerate(data["data"][:3]):
                prompt += f"  {i+1}. {json.dumps(record, ensure_ascii=False)}\n"

        prompt += """

## 任务要求
请基于真实数据，优化AI生成的旅行计划，包括：

1. **住宿建议** - 基于真实酒店数据推荐
2. **景点安排** - 基于真实景点数据优化行程
3. **餐饮推荐** - 基于真实餐厅数据建议
4. **交通方案** - 基于真实交通数据规划
5. **预算调整** - 基于真实价格数据优化预算

## 输出格式
请返回JSON格式的增强版旅行计划，保持原有结构，但增加真实数据支持：

{
    "enhanced_plan": "增强后的旅行计划",
    "real_data_usage": "使用了哪些真实数据",
    "improvements": ["具体改进点"],
    "confidence_level": "数据可靠性评分",
    "data_sources": ["数据来源"]
}

注意：如果真实数据不足，请说明并保持AI建议的合理性。"""

        return prompt

    def get_data_summary(self) -> Dict[str, Any]:
        """获取数据摘要"""
        summary = {
            "total_files": len(self.real_data),
            "file_details": {},
            "total_records": 0,
        }

        for file_name, data in self.real_data.items():
            if "error" not in data:
                summary["file_details"][file_name] = {
                    "records": data["row_count"],
                    "columns": data["columns"],
                    "size_kb": data["file_size"] / 1024,
                }
                summary["total_records"] += data["row_count"]
            else:
                summary["file_details"][file_name] = {"error": data["error"]}

        return summary


# 全局实例
real_data_enhancer = RealDataEnhancer()
