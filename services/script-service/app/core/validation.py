import re
from typing import Tuple, List

class InputValidator:
    DANGEROUS_PATTERNS = [
        (r'\brm\s+-rf\s+/', "Recursive deletion of root"),
        (r'\bdd\s+if=/dev/', "Direct disk access"),
        (r':()\{\s*:\|\:&\s*\};:', "Fork bomb"),
    ]
    
    @classmethod
    def validate_script_content(
        cls,
        content: str,
        script_type: str,
        max_size: int = 1_000_000
    ) -> Tuple[bool, List[str]]:
        errors = []
        
        if len(content) > max_size:
            errors.append(f"Script exceeds max size ({max_size} bytes)")
        
        for pattern, desc in cls.DANGEROUS_PATTERNS:
            if re.search(pattern, content, re.IGNORECASE):
                errors.append(f"Dangerous pattern: {desc}")
        
        return len(errors) == 0, errors