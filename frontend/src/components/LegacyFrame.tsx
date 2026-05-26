import { BACKEND_URL } from "@/constants/config";

type LegacyFrameProps = {
  title: string;
  path: string;
};

export function LegacyFrame({ title, path }: LegacyFrameProps) {
  return (
    <main className="legacy-frame-page">
      <iframe
        title={title}
        src={`${BACKEND_URL}${path}`}
        className="legacy-frame"
        allow="camera; microphone; autoplay; clipboard-read; clipboard-write"
      />
    </main>
  );
}
