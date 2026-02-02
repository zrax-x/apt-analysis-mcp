"""
YARA规则Hash查询工具
根据rule和namespace查询对应的样本SHA256 hash
"""
import csv
import os
from typing import List, Optional, Tuple


class RuleHashQuery:
    """YARA规则Hash查询类"""
    
    def __init__(self, mapping_file: str = None):
        """
        初始化查询器
        
        Args:
            mapping_file: 规则Hash映射文件路径
                         如果为None，将尝试从环境变量或使用默认路径
        """
        if mapping_file is None:
            # 默认使用项目根目录的映射文件
            project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
            mapping_file = os.path.join(project_root, "Rule_Hash_Mapping.csv")
        
        self.mapping_file = mapping_file
        self.mapping = {}
        self._load_mapping()
    
    def _load_mapping(self):
        """加载规则Hash映射表"""
        if not os.path.exists(self.mapping_file):
            raise FileNotFoundError(
                f"映射文件不存在: {self.mapping_file}\n"
                f"请先运行 'python3 build_rule_hash_mapping.py' 生成映射表"
            )
        
        try:
            with open(self.mapping_file, 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                for row in reader:
                    rule = row['rule']
                    namespace = row['namespace']
                    sha256_list = row.get('sha256List', '')
                    
                    key = (rule, namespace)
                    self.mapping[key] = sha256_list
        except Exception as e:
            raise Exception(f"读取映射文件失败: {e}")
    
    def query(
        self,
        rule: str,
        namespace: Optional[str] = None
    ) -> List[Tuple[str, str, List[str]]]:
        """
        查询规则对应的SHA256 hash
        
        Args:
            rule: 规则名称
            namespace: 命名空间（可选）
            
        Returns:
            list: 匹配的结果列表 [(rule, namespace, [sha256_list])]
        """
        results = []
        
        if namespace:
            # 精确查询
            key = (rule, namespace)
            if key in self.mapping:
                sha256_str = self.mapping[key]
                sha256_list = [h.strip() for h in sha256_str.split(',') if h.strip()]
                results.append((rule, namespace, sha256_list))
        else:
            # 只根据规则名查询
            for (r, ns), sha256_str in self.mapping.items():
                if r == rule:
                    sha256_list = [h.strip() for h in sha256_str.split(',') if h.strip()]
                    results.append((r, ns, sha256_list))
        
        return results
    
    def get_sha256_list(
        self,
        rule: str,
        namespace: Optional[str] = None
    ) -> List[str]:
        """
        获取规则对应的SHA256 hash列表（扁平化，去重）
        
        Args:
            rule: 规则名称
            namespace: 命名空间（可选）
            
        Returns:
            list: SHA256 hash列表
        """
        results = self.query(rule, namespace)
        all_sha256 = []
        
        for _, _, sha256_list in results:
            all_sha256.extend(sha256_list)
        
        # 去重
        return list(set(all_sha256))


if __name__ == "__main__":
    # 测试
    query = RuleHashQuery()