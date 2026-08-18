from dataclasses import dataclass, fields, is_dataclass
from enum import Enum
from typing import Any


class ContractValidationError(ValueError):
    """Raised when structured agent data violates its contract."""


def _required(value: str, field_name: str) -> str:
    if type(value) is not str:
        raise ContractValidationError(f"{field_name} must be a string.")
    value = value.strip()
    if not value:
        raise ContractValidationError(f"{field_name} is required.")
    return value


def _positive_integer(value: int, field_name: str) -> int:
    if type(value) is not int or value < 1:
        raise ContractValidationError(f"{field_name} must be a positive integer.")
    return value


def _contract_tuple(value: tuple[Any, ...], field_name: str, element_type: type) -> tuple[Any, ...]:
    if type(value) is not tuple:
        raise ContractValidationError(f"{field_name} must be a tuple.")
    if any(type(item) is not element_type for item in value):
        raise ContractValidationError(f"{field_name} contains an invalid item type.")
    return value


def _serializable(value: Any) -> Any:
    if isinstance(value, Enum):
        return value.value
    if is_dataclass(value):
        return {field.name: _serializable(getattr(value, field.name)) for field in fields(value)}
    if isinstance(value, tuple):
        return [_serializable(item) for item in value]
    return value


class SerializableContract:
    def to_dict(self) -> dict[str, Any]:
        return _serializable(self)


@dataclass(frozen=True)
class PlannerMilestone(SerializableContract):
    milestone_id: str
    order: int
    title: str
    start_week: int
    end_week: int

    def __post_init__(self):
        object.__setattr__(self, "milestone_id", _required(self.milestone_id, "milestone_id"))
        object.__setattr__(self, "title", _required(self.title, "title"))
        _positive_integer(self.order, "milestone order")
        _positive_integer(self.start_week, "milestone start_week")
        _positive_integer(self.end_week, "milestone end_week")
        if self.end_week < self.start_week:
            raise ContractValidationError("Milestone week boundaries are invalid.")


@dataclass(frozen=True)
class PlannerOutput(SerializableContract):
    milestones: tuple[PlannerMilestone, ...]

    def __post_init__(self):
        _contract_tuple(self.milestones, "milestones", PlannerMilestone)
        if not self.milestones:
            raise ContractValidationError("Planner output requires at least one milestone.")
        ids = [item.milestone_id for item in self.milestones]
        orders = [item.order for item in self.milestones]
        titles = [item.title.casefold() for item in self.milestones]
        if len(ids) != len(set(ids)) or len(orders) != len(set(orders)):
            raise ContractValidationError("Planner milestones must have unique identities and ordering.")
        if len(titles) != len(set(titles)):
            raise ContractValidationError("Planner milestones must not be duplicated.")
        if orders != sorted(orders):
            raise ContractValidationError("Planner milestones must be ordered.")


@dataclass(frozen=True)
class GeneratedTask(SerializableContract):
    task_id: str
    milestone_id: str
    order: int
    week: int
    title: str
    description: str
    objective: str
    techniques: tuple[str, ...]
    revision_checkpoint: bool = False

    def __post_init__(self):
        for field_name in ("task_id", "milestone_id", "title", "description", "objective"):
            object.__setattr__(self, field_name, _required(getattr(self, field_name), field_name))
        _positive_integer(self.order, "task order")
        _positive_integer(self.week, "task week")
        if type(self.revision_checkpoint) is not bool:
            raise ContractValidationError("revision_checkpoint must be a boolean.")
        if type(self.techniques) is not tuple:
            raise ContractValidationError("techniques must be a tuple.")
        cleaned = tuple(_required(item, "technique") for item in self.techniques)
        if not cleaned:
            raise ContractValidationError("A generated task requires at least one study technique.")
        object.__setattr__(self, "techniques", cleaned)


@dataclass(frozen=True)
class ContentGenerationOutput(SerializableContract):
    summary: str
    tasks: tuple[GeneratedTask, ...]

    def __post_init__(self):
        object.__setattr__(self, "summary", _required(self.summary, "summary"))
        _contract_tuple(self.tasks, "tasks", GeneratedTask)
        if not self.tasks:
            raise ContractValidationError("Content output requires at least one task.")
        task_ids = [item.task_id for item in self.tasks]
        orders = [item.order for item in self.tasks]
        if len(task_ids) != len(set(task_ids)) or len(orders) != len(set(orders)) or orders != sorted(orders):
            raise ContractValidationError("Generated tasks must have unique identities and ordered positions.")


class EvaluationStatus(str, Enum):
    VALID = "valid"
    INVALID = "invalid"


@dataclass(frozen=True)
class EvaluationResult(SerializableContract):
    status: EvaluationStatus
    issues: tuple[str, ...] = ()

    def __post_init__(self):
        if type(self.status) is not EvaluationStatus:
            raise ContractValidationError("status must be an EvaluationStatus value.")
        if type(self.issues) is not tuple:
            raise ContractValidationError("issues must be a tuple.")
        cleaned = tuple(_required(issue, "evaluation issue") for issue in self.issues)
        object.__setattr__(self, "issues", cleaned)
        if self.status == EvaluationStatus.VALID and cleaned:
            raise ContractValidationError("A valid evaluation cannot contain issues.")
        if self.status == EvaluationStatus.INVALID and not cleaned:
            raise ContractValidationError("An invalid evaluation must explain its issues.")


@dataclass(frozen=True)
class AggregatedTask(SerializableContract):
    task_id: str
    week: int
    title: str
    description: str
    method: str
    objective: str
    revision_checkpoint: bool

    def __post_init__(self):
        _positive_integer(self.week, "aggregated task week")
        if type(self.revision_checkpoint) is not bool:
            raise ContractValidationError("revision_checkpoint must be a boolean.")
        for field_name in ("task_id", "title", "description", "method", "objective"):
            object.__setattr__(self, field_name, _required(getattr(self, field_name), field_name))


@dataclass(frozen=True)
class AggregatedPlan(SerializableContract):
    summary: str
    tasks: tuple[AggregatedTask, ...]

    def __post_init__(self):
        object.__setattr__(self, "summary", _required(self.summary, "summary"))
        _contract_tuple(self.tasks, "tasks", AggregatedTask)
        if not self.tasks:
            raise ContractValidationError("An aggregated plan requires at least one task.")
        task_ids = [item.task_id for item in self.tasks]
        if len(task_ids) != len(set(task_ids)):
            raise ContractValidationError("Aggregated tasks must have unique identities.")
