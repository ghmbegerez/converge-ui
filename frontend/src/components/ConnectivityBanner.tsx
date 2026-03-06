type ServiceStatus = {
  reachable: boolean;
  mode?: string;
};

type Props = {
  orchestrator?: ServiceStatus;
  converge?: ServiceStatus;
};

export function ConnectivityBanner({ orchestrator, converge }: Props) {
  const issues = [];
  if (orchestrator && !orchestrator.reachable) {
    issues.push("orchestrator");
  }
  if (converge && !converge.reachable) {
    issues.push("converge");
  }

  if (issues.length === 0) {
    return null;
  }

  return (
    <div className="banner banner-danger" role="alert">
      Connectivity degraded: {issues.join(" + ")} unavailable. The control plane may be working from partial or cached data.
    </div>
  );
}
