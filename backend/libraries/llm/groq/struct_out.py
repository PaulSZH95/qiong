from langchain_core.pydantic_v1 import BaseModel, Field
from enum import Enum, IntEnum
from typing import List


class Section(str, Enum):
    business = "business"
    risks = "risks"
    fin_data = "fin_data"
    discussions_and_analyst = "discussions_and_analyst"
    fin_statements_and_supplementary_data = "fin_statements_and_supplementary_data"
    corporate_governance = "corporate_governance"
    executive_compensation = "executive_compensation"
    security_ownership_of_priviledged_holders_related_matters = (
        "security_ownership_of_priviledged_holders_related_matters"
    )
    matters_pertaining_executive_and_staff = "matters_pertaining_executive_and_staff"
    declaration_of_relationships_related_transactions_and_independence = (
        "declaration_of_relationships_related_transactions_and_independence"
    )


class SectionTags(BaseModel):
    """
    This class is used to store list of tags
    """

    tags: List[Section] = Field(
        description="Carefully analyse and determine any number of suitable tags for this excerpt extracted from a financial document"
    )
