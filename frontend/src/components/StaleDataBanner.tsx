type Props = {
  message: string;
};

export function StaleDataBanner({ message }: Props) {
  return <div className="banner">{message}</div>;
}
