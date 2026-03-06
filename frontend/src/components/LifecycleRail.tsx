type Props = {
  status?: string;
};

const STEPS = ["queued", "claimed", "running", "evaluated", "merged"];
const BRANCH_STATES = new Set(["blocked", "retry_pending", "failed"]);

export function LifecycleRail({ status }: Props) {
  const currentIndex = status ? STEPS.indexOf(status) : -1;
  const branch = status && BRANCH_STATES.has(status) ? status : null;

  return (
    <div className="lifecycle">
      {STEPS.map((step, index) => {
        const completed = currentIndex > index;
        const active = currentIndex === index;
        return (
          <div className="lifecycle-step" key={step}>
            <div className={`lifecycle-node ${completed ? "done" : ""} ${active ? "active" : ""}`}>
              {step}
            </div>
            {index < STEPS.length - 1 ? <div className={`lifecycle-connector ${completed ? "done" : ""}`} /> : null}
          </div>
        );
      })}
      {branch ? <div className="lifecycle-node branch">{branch}</div> : null}
    </div>
  );
}
