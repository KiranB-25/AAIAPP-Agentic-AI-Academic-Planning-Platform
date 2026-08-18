import { useState, type FormEvent } from "react";

import type { AcademicGoal, GoalCreateRequest } from "../../types/goals";

interface GoalFormProps {
  goal?: AcademicGoal;
  isSubmitting: boolean;
  serverErrors?: Record<string, string[]>;
  onCancel: () => void;
  onSubmit: (goal: GoalCreateRequest) => Promise<void>;
}

export function GoalForm({ goal, isSubmitting, serverErrors, onCancel, onSubmit }: GoalFormProps) {
  const [subject, setSubject] = useState(goal?.subject ?? "");
  const [description, setDescription] = useState(goal?.description ?? "");
  const [duration, setDuration] = useState(goal ? String(goal.duration) : "");
  const [intensity, setIntensity] = useState(goal?.intensity ?? "");
  const [errors, setErrors] = useState<Record<string, string>>({});

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const nextErrors: Record<string, string> = {};
    const numericDuration = Number(duration);
    if (!subject.trim()) nextErrors.subject = "Subject is required.";
    if (!description.trim()) nextErrors.description = "Objective or description is required.";
    if (!duration) nextErrors.duration = "Duration is required.";
    else if (!Number.isInteger(numericDuration) || numericDuration < 1 || numericDuration > 16) {
      nextErrors.duration = "Duration must be between 1 and 16 weeks.";
    }
    setErrors(nextErrors);
    if (Object.keys(nextErrors).length) return;
    await onSubmit({
      subject: subject.trim(),
      description: description.trim(),
      duration: numericDuration,
      intensity: intensity.trim(),
    });
  }

  const errorFor = (field: string) => errors[field] ?? serverErrors?.[field]?.[0];

  return (
    <form className="space-y-5" onSubmit={handleSubmit} noValidate>
      <div>
        <label className="block text-sm font-medium" htmlFor="goal-subject">Subject</label>
        <input id="goal-subject" className="mt-1.5 w-full rounded-lg border border-border bg-background px-3 py-2.5" value={subject} onChange={(event) => setSubject(event.target.value)} disabled={isSubmitting} maxLength={200} />
        {errorFor("subject") && <p className="mt-1 text-sm text-destructive" role="alert">{errorFor("subject")}</p>}
      </div>
      <div>
        <label className="block text-sm font-medium" htmlFor="goal-description">Objective or description</label>
        <textarea id="goal-description" className="mt-1.5 min-h-32 w-full rounded-lg border border-border bg-background px-3 py-2.5" value={description} onChange={(event) => setDescription(event.target.value)} disabled={isSubmitting} />
        {errorFor("description") && <p className="mt-1 text-sm text-destructive" role="alert">{errorFor("description")}</p>}
      </div>
      <div className="grid gap-5 sm:grid-cols-2">
        <div>
          <label className="block text-sm font-medium" htmlFor="goal-duration">Duration in weeks</label>
          <input id="goal-duration" className="mt-1.5 w-full rounded-lg border border-border bg-background px-3 py-2.5" type="number" min="1" max="16" value={duration} onChange={(event) => setDuration(event.target.value)} disabled={isSubmitting} />
          <p className="mt-1 text-xs text-muted-foreground">Choose between 1 and 16 weeks.</p>
          {errorFor("duration") && <p className="mt-1 text-sm text-destructive" role="alert">{errorFor("duration")}</p>}
        </div>
        <div>
          <label className="block text-sm font-medium" htmlFor="goal-intensity">Study intensity <span className="text-muted-foreground">(optional)</span></label>
          <input id="goal-intensity" className="mt-1.5 w-full rounded-lg border border-border bg-background px-3 py-2.5" value={intensity} onChange={(event) => setIntensity(event.target.value)} disabled={isSubmitting} maxLength={50} placeholder="e.g. Moderate" />
        </div>
      </div>
      <div className="flex flex-wrap justify-end gap-3 border-t border-border pt-5">
        <button className="rounded-lg border border-border px-4 py-2 text-sm font-medium" type="button" onClick={onCancel} disabled={isSubmitting}>Cancel</button>
        <button className="rounded-lg bg-primary px-4 py-2 text-sm font-semibold text-primary-foreground disabled:opacity-60" type="submit" disabled={isSubmitting}>{isSubmitting ? "Saving…" : goal ? "Save changes" : "Create goal"}</button>
      </div>
    </form>
  );
}
