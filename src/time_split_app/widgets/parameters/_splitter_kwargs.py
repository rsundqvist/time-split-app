from dataclasses import dataclass, field

from time_split.types import DatetimeIndexSplitterKwargs

from ._expand_limits import ExpandLimitsWidget
from ._schedule import ScheduleWidget
from ._span import SpanWidget, select_spans


@dataclass(frozen=True)
class SplitterKwargsWidget:
    schedule_widget: ScheduleWidget = field(default_factory=ScheduleWidget)
    before_widget: SpanWidget = field(default_factory=lambda: SpanWidget("before"))
    after_widget: SpanWidget = field(default_factory=lambda: SpanWidget("after"))
    limits_widget: ExpandLimitsWidget = field(default_factory=ExpandLimitsWidget)

    def select_params(self) -> DatetimeIndexSplitterKwargs:
        schedule, filters = self.schedule_widget.get_schedule()
        before, after = select_spans(self.before_widget, after=self.after_widget)
        expand_limits = self.limits_widget.select()

        return DatetimeIndexSplitterKwargs(
            schedule=schedule,
            before=before,
            after=after,
            step=filters.step,
            n_splits=filters.limit,
            expand_limits=expand_limits,
        )
