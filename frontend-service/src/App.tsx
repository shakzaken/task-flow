import HomePage from "./pages/HomePage";

interface AppProps {
  pollingIntervalMs?: number;
}

export default function App({ pollingIntervalMs }: AppProps) {
  return <HomePage pollingIntervalMs={pollingIntervalMs} />;
}
